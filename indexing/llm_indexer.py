"""Indexer for a single directory using an LLM.

This collects context about a given directory and uses Gemini to produce a
summary.

Does not handle recursive indexing; walking a directory tree is the
responsibility of the caller.
"""

from collections.abc import Sequence
import concurrent.futures
import dataclasses
import datetime
import logging
from pathlib import Path
from typing import Any

from indexing import chunker as chunker_lib
from indexing import error_prompt_generator
from indexing import file_utils
from indexing import prompt_templates
from indexing import rendering
from indexing import schema
from indexing import sequential_llm_prompter
from indexing import state
from indexing import summary_merger as summary_merger_lib
from indexing import work_unit as work_unit_lib

class VerificationFailedError(Exception):
    def __init__(self, message: str, result: Any, issues: list[str]):
        super().__init__(message)
        self.result = result
        self.issues = issues


class _SimpleStatsRecorder:
    """Internal helper to track indexing throughput and success rates."""
    def __init__(self) -> None:
        self.counters: dict[str, int] = {}
    def increment_counter(self, name: str, value: int = 1) -> None:
        # Atomically increment the named counter for reporting.
        self.counters[name] = self.counters.get(name, 0) + value


def get_index_file_name(epoch: int) -> str:
    """Returns the index file name for the given epoch."""
    return f"llm_index_v{epoch}.md"


def _optional_str_attr(obj: Any, name: str) -> str | None:
    value = getattr(obj, name, None)
    return value if isinstance(value, str) else None


def _bool_attr(obj: Any, name: str) -> bool:
    value = getattr(obj, name, False)
    return value if isinstance(value, bool) else False


USER_PROMPT_TEMPLATE = "Summarize the contents of {directory_path}"
PARTIAL_SUMMARY_PROMPT_ADDITION = (
    "(this is a partial summary, you are only seeing a subset of the files in"
    " the directory)"
)


@dataclasses.dataclass
class LlmIndexerConfig:
    """Configuration for the LLM indexer."""

    llm_prompter: sequential_llm_prompter.LlmPrompter
    index_state: state.State
    chunker: chunker_lib.Chunker
    summary_merger: summary_merger_lib.SummaryMerger
    config: Any = None
    max_dir_size: int | None = None
    include_search_tool: bool = True
    codebase_specific_context: str | None = None
    filtering_config: Any = None
    custom_sections: Sequence[Any] | None = None


class LlmIndexer:
    """Class to generate an index for a directory using an LLM."""

    def __init__(
        self,
        config: LlmIndexerConfig,
        fs_manager: Any = None,
    ) -> None:
        self._config = config
        self._stats = _SimpleStatsRecorder()
        self._fs_manager = fs_manager

    @property
    def llm_prompter(self) -> sequential_llm_prompter.LlmPrompter:
        return self._config.llm_prompter

    def _generate_index_for_chunk(
        self,
        directory_path: Path,
        epoch: int = 0,
        previous_root_map_content: str = "",
        directory_contents_chunk: dict[Path, str] = None,
        subdirectory_indexes: dict[str, str] = None,
        existing_index: str = "",
        is_partial: bool = False,
        verifier: Any | None = None,
    ) -> schema.IndexDocument:
        """Generates an index for a chunk of files in a directory."""
        import time
        max_attempts = 3
        current_issues = []
        previous_artifact_str = ""
        previous_artifact_doc: schema.IndexDocument | None = None
        previous_verdict: Any | None = None

        for attempt in range(max_attempts):
            try:
                logging.info("Generating index for %s (epoch %d) attempt %d", directory_path, epoch, attempt + 1)

                display_path = self._config.index_state.get_display_path(str(directory_path))
                str_directory_contents = {str(k): v for k, v in directory_contents_chunk.items()}
                extra_ctx = ""
                
                # --- AST Grounding Phase ---
                ast_grounding_cache = {}
                try:
                    from indexing import ast_extractor
                    ast_context_lines = []
                    for filepath, content in directory_contents_chunk.items():
                        symbols, invariants = ast_extractor.extract_ast_grounding(str(filepath), content)
                        if symbols or invariants:
                            ast_grounding_cache[str(filepath)] = {"symbols": symbols, "invariants": invariants}
                            ast_context_lines.append(f"AST Deterministic Grounding for {filepath}:")
                            if symbols:
                                ast_context_lines.append("  Exported Symbols (Mandatory to include in blueprint with matching provenance):")
                                for sym in symbols:
                                    ast_context_lines.append(f"  - name: {sym.name}, signature: {sym.signature}, lines: {sym.line_number}-{sym.end_line_number}")
                            if invariants:
                                ast_context_lines.append("  Implementation Invariants (Mandatory to enrich in blueprint with matching provenance):")
                                for inv in invariants:
                                    ast_context_lines.append(f"  - primitive: {inv.primitive}, lines: {inv.line_number}-{inv.end_line_number}")
                            ast_context_lines.append("")
                    if ast_context_lines:
                        extra_ctx += "\n".join(ast_context_lines) + "\n"
                except Exception as e:
                    logging.warning(f"AST extraction failed: {e}")

                if existing_index:
                    extra_ctx += f"existing_index:\n{existing_index}\n"

                if epoch > 0:
                    system_prompt = prompt_templates.IndexImproverPrompt(
                        directory_path=str(display_path),
                        epoch=epoch,
                        directory_contents=repr(str_directory_contents),
                        subdirectory_indexes=repr(subdirectory_indexes),
                        extra_context=extra_ctx,
                        previous_epoch_str=previous_root_map_content or "",
                        index_file_name=get_index_file_name(epoch),
                        codebase_specific_context=self._config.codebase_specific_context,
                        custom_sections=self._config.custom_sections,
                        repo_root=self._config.llm_prompter.repo_root,
                    )
                else:
                    system_prompt = prompt_templates.InitialIndexerPrompt(
                        directory_path=str(display_path),
                        epoch=epoch,
                        directory_contents=repr(str_directory_contents),
                        subdirectory_indexes=repr(subdirectory_indexes),
                        extra_context=extra_ctx,
                        previous_epoch_str=previous_root_map_content or "",
                        index_file_name=get_index_file_name(epoch),
                        codebase_specific_context=self._config.codebase_specific_context,
                        custom_sections=self._config.custom_sections,
                        repo_root=self._config.llm_prompter.repo_root,
                    )
                
                # Inject AST cache into system prompt so prompter can use it
                system_prompt._ast_grounding_cache = ast_grounding_cache

                user_prompt_template = USER_PROMPT_TEMPLATE
                if is_partial:
                    user_prompt_template += PARTIAL_SUMMARY_PROMPT_ADDITION
                    keys_str = [str(k) for k in directory_contents_chunk.keys()]
                    user_prompt_template += f"Please summarize only the following files: {keys_str}"

                initial_user_prompt = user_prompt_template.format(directory_path=display_path)

                if current_issues:
                    epg = getattr(error_prompt_generator, 'IndexerErrorPromptGenerator', None)
                    if epg:
                        error_msg = "Verification failed for previous attempt."
                        if previous_artifact_str:
                            error_msg += f"\nRejected Output:\n{previous_artifact_str}"
                        initial_user_prompt += "\n\n" + epg().generate_error_prompt(error_msg, current_issues)

                epg = getattr(error_prompt_generator, 'IndexerErrorPromptGenerator', None)
                epg_instance = epg() if epg else error_prompt_generator
                
                artifact_chunk = self._config.llm_prompter.prompt_for_indexing(
                    directory_path=str(directory_path),
                    initial_user_prompt=initial_user_prompt,
                    system_prompt=system_prompt,
                    error_prompt_generator_instance=epg_instance,
                    verifier=verifier,
                    directory_files=[str(k) for k in directory_contents_chunk.keys()],
                    previous_artifact=previous_artifact_doc,
                    previous_verdict=previous_verdict
                )

                if verifier:
                    source_context = "\n\n".join([f"--- {k} ---\n{v}" for k, v in directory_contents_chunk.items()])
                    verdict = verifier.verify(
                        artifact_chunk.model_dump_json(), 
                        source_context, 
                        directory_files=[str(k) for k in directory_contents_chunk.keys()],
                        ast_grounding=ast_grounding_cache
                    )
                    if not verdict.passed:
                        previous_artifact_doc = artifact_chunk
                        previous_artifact_str = artifact_chunk.model_dump_json() if hasattr(artifact_chunk, 'model_dump_json') else ""
                        previous_verdict = verdict
                        raise VerificationFailedError("Chunk failed", result=artifact_chunk, issues=verdict.issues)
                    
                    # Extract info issues as verification notes
                    if hasattr(verdict, 'detailed_issues'):
                        info_issues = [
                            issue.description for issue in verdict.detailed_issues 
                            if getattr(issue, 'severity', 'error') == "info"
                        ]
                        artifact_chunk.verification_notes = info_issues
                    
                    artifact_chunk.verification_state = schema.VerificationState(
                        verified=True, 
                        confidence=getattr(verdict, 'confidence', 1.0), 
                        issues=verdict.issues,
                        is_empty_bypass=_bool_attr(verdict, 'is_empty_bypass'),
                        is_infrastructure_bypass=_bool_attr(verdict, 'is_infrastructure_bypass'),
                        verification_model=_optional_str_attr(verdict, 'verification_model'),
                        verified_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
                    )
                return artifact_chunk
                
            except VerificationFailedError as ve:
                current_issues = ve.issues
                if attempt == max_attempts - 1:
                    logging.error("Chunk failed after all retries. Proceeding with 'Best Effort'.")
                    result = ve.result
                    if not result:
                        result = schema.IndexDocument(
                            overview=schema.Overview(content="Processing failed due to unrecoverable verification error.")
                        )
                    
                    result.verification_state = schema.VerificationState(
                        verified=False, confidence=0.0, issues=current_issues,
                        is_empty_bypass=False
                    )
                    return result
                
                time.sleep(2 ** attempt)
            except Exception as e:
                logging.error(f"Unexpected error in chunk generation: {e}")
                raise

        # Safety net
        fallback = schema.IndexDocument(overview=schema.Overview(content="Processing failed loop exit."))
        fallback.verification_state = schema.VerificationState(verified=False, confidence=0.0, issues=["Internal error"])
        return fallback

    def _merge_with_retries(self, chunk_docs, work_unit, verifier=None, epoch=0, directory_files: list[str] | None = None, ast_grounding: dict[str, Any] | None = None) -> schema.IndexDocument:
        import time
        max_attempts = 3
        current_issues = []
        previous_artifact = ""

        for attempt in range(max_attempts):
            try:
                error_prompt = ""
                if current_issues:
                    error_msg = f"Merger verification failed.\nRejected Output:\n{previous_artifact}\nIssues:\n{current_issues}"
                    error_prompt = error_msg
                
                merged_doc = self._config.summary_merger.merge(
                    chunk_docs, 
                    str(work_unit.output_path), 
                    epoch=epoch, 
                    error_prompt=error_prompt,
                    directory_files=directory_files
                )
                
                if verifier:
                    chunk_context = ""
                    context_limit_reached = False
                    for doc in chunk_docs:
                        doc_md = rendering.to_markdown(doc)
                        if len(chunk_context) + len(doc_md) > 24000:
                            context_limit_reached = True
                            break
                        chunk_context += f"\n\n{doc_md}"

                    if context_limit_reached:
                        merged_doc.verification_state = schema.VerificationState(
                            verified=True, confidence=0.5, issues=["Verification skipped due to context size"],
                            is_empty_bypass=False, is_infrastructure_bypass=True,
                            verified_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        )
                        return merged_doc

                    verdict = verifier.verify(
                        merged_doc.model_dump_json(), 
                        chunk_context, 
                        directory_files=directory_files,
                        is_merger_mode=True,
                        ast_grounding=ast_grounding
                    )
                    if not verdict.passed:
                        raise VerificationFailedError("Merger failed", result=merged_doc, issues=verdict.issues)
                    
                    if hasattr(verdict, 'detailed_issues'):
                        info_issues = [i.description for i in verdict.detailed_issues if getattr(i, 'severity', 'error') == "info"]
                        merged_doc.verification_notes = info_issues

                    merged_doc.verification_state = schema.VerificationState(
                        verified=True, confidence=getattr(verdict, 'confidence', 1.0), issues=verdict.issues,
                        is_empty_bypass=_bool_attr(verdict, 'is_empty_bypass'),
                        is_infrastructure_bypass=_bool_attr(verdict, 'is_infrastructure_bypass'),
                        verification_model=_optional_str_attr(verdict, 'verification_model'),
                        verified_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
                    )
                return merged_doc
                
            except VerificationFailedError as ve:
                current_issues = ve.issues
                previous_artifact = ve.result.model_dump_json() if hasattr(ve.result, 'model_dump_json') else ""
                if attempt == max_attempts - 1:
                    result = ve.result
                    result.verification_state = schema.VerificationState(verified=False, confidence=0.0, issues=current_issues)
                    return result
                time.sleep(2 ** attempt)
            except Exception as e:
                logging.error(f"Unexpected error in merger: {e}")
                raise
        return schema.IndexDocument(overview=schema.Overview(content="Merge failed loop exit."))

    def generate_subcomponent_list_section(self, directory_contents: dict[Path, str], output_path: Path) -> str:
        file_list = []
        for filename in directory_contents.keys():
            try: rel_path = str(Path(filename).relative_to(Path(output_path)))
            except ValueError: rel_path = str(filename)
            file_list.append(rel_path)
        file_list = sorted(file_list)
        return "\n\n# All Subcomponents\n\n" + "\n".join([f"- `{filename}`" for filename in file_list])

    @dataclasses.dataclass(frozen=True)
    class WorkUnitGenerationResult:
        markdown_result: str
        artifact: schema.IndexDocument | None = None
        source_context: str = ""
        success: bool = True

    def generate_index_for_work_unit(
        self,
        work_unit: work_unit_lib.WorkUnit,
        epoch: int,
        previous_root_map_content: str = "",
        max_chunk_parallelization: int | None = None,
        input_prefix: str | None = None,
        verifier: Any | None = None,
    ) -> WorkUnitGenerationResult:
        prefix = Path(input_prefix) if input_prefix else None
        loaded_contents = work_unit.load_files_to_index(self._fs_manager, prefix)
        directory_contents = {k: v for k, v in sorted(loaded_contents.items())}
        num_files = len(directory_contents)
        total_size = sum(len(content) for content in directory_contents.values())

        if num_files == 0:
            return self.WorkUnitGenerationResult(
                markdown_result=f"# {work_unit.output_path}\n\nEmpty directory.\n",
                artifact=schema.IndexDocument(overview=schema.Overview(content="Empty directory"), verification_state=schema.VerificationState(verified=True, confidence=1.0, issues=[], is_empty_bypass=True)),
                success=True,
            )

        prefixed_output_path = input_prefix / work_unit.output_path if input_prefix else work_unit.output_path
        get_subdir = getattr(file_utils, 'get_subdirectory_indexes', None)
        subdirectory_indexes = get_subdir(self._fs_manager, self._config.index_state, str(prefixed_output_path), epoch, filtering_config=self._config.filtering_config) if get_subdir else {}
        existing_index = self._config.index_state.read_summary(str(prefixed_output_path), epoch - 1) if epoch > 0 and self._config.index_state.exist_summary(str(prefixed_output_path), epoch - 1) else ""

        if self._config.max_dir_size is None or total_size <= self._config.max_dir_size:
            try:
                doc = self._generate_index_for_chunk(work_unit.output_path, epoch, previous_root_map_content, directory_contents, subdirectory_indexes, existing_index, False, verifier)
                markdown_result = rendering.to_markdown(doc)
                success = True
            except Exception:
                logging.exception("Failed processing %s", work_unit.output_path)
                markdown_result, success, doc = f"Could not generate index for {work_unit.output_path}.", False, None
            
            source_ctx = "\n\n".join([f"--- {k} ---\n{v}" for k, v in directory_contents.items()])
            return self.WorkUnitGenerationResult(markdown_result=markdown_result + self.generate_subcomponent_list_section(directory_contents, work_unit.output_path), artifact=doc, source_context=source_ctx, success=success)

        chunks = self._config.chunker.chunk(directory_contents, self._config.max_dir_size)
        chunk_docs: list[schema.IndexDocument | None] = [None] * len(chunks)
        
        # Accumulate AST grounding for merged verification
        all_ast_grounding = {}
        try:
            from indexing import ast_extractor
            for filepath, content in directory_contents.items():
                symbols, invariants = ast_extractor.extract_ast_grounding(str(filepath), content)
                if symbols or invariants:
                    all_ast_grounding[str(filepath)] = {"symbols": symbols, "invariants": invariants}
        except Exception as e:
            logging.warning(f"AST extraction failed for merge context: {e}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_chunk_parallelization) as executor:
            future_to_chunk_id = {executor.submit(self._generate_index_for_chunk, work_unit.output_path, epoch, previous_root_map_content, chunk, subdirectory_indexes, existing_index, True, verifier): i for i, chunk in enumerate(chunks)}
            for future in concurrent.futures.as_completed(future_to_chunk_id):
                try: chunk_docs[future_to_chunk_id[future]] = future.result()
                except Exception as e: logging.error(f"Failed chunk {future_to_chunk_id[future]}: {e}")

        chunk_docs = [doc for doc in chunk_docs if doc is not None]
        try:
            merged_doc = self._merge_with_retries(
                chunk_docs, 
                work_unit, 
                verifier,
                epoch=epoch, 
                directory_files=[str(k) for k in directory_contents.keys()],
                ast_grounding=all_ast_grounding
            )
            markdown_result, success = rendering.to_markdown(merged_doc), True
        except Exception as e:
            logging.error(f"Failed merge: {e}")
            markdown_result, success, merged_doc = f"Could not generate index for {work_unit.output_path}.", False, None

        source_ctx = "\n\n".join([f"--- {k} ---\n{v}" for k, v in directory_contents.items()])
        return self.WorkUnitGenerationResult(markdown_result=markdown_result + self.generate_subcomponent_list_section(directory_contents, work_unit.output_path), artifact=merged_doc, source_context=source_ctx, success=success)
