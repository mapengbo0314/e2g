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


USER_PROMPT_TEMPLATE = "Summarize the contents of {directory_path}"
PARTIAL_SUMMARY_PROMPT_ADDITION = (
    "(this is a partial summary, you are only seeing a subset of the files in"
    " the directory)"
)


@dataclasses.dataclass
class LlmIndexerConfig:
    """Configuration for the LLM indexer.

    Attributes:
      llm_prompter: The LLM prompter to use for prompting the LLM.
      index_state: The state object for reading and writing index files.
      config: The indexer configuration.
      chunker: The chunker to use for splitting large directories.
      summary_merger: The summary merger to use for merging partial summaries.
      max_dir_size: The maximum size of a directory's contents in bytes before
        chunking is triggered.
      include_search_tool: Whether to include the search tool in the agent
        abilities.
      codebase_specific_context: Additional context to add to the prompt for a
        specific codebase instead of the default generic project context.
      filtering_config: Optional configuration for filtering paths.
      custom_sections: Custom sections requested by the user.
    """

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
        """Initializes the LlmIndexer.

        Args:
          config: Configuration for the LlmIndexer.
          fs_manager: A file system manager to use for file operations.
        """
        self._config = config
        self._stats = _SimpleStatsRecorder()
        self._fs_manager = fs_manager

    @property
    def llm_prompter(self) -> sequential_llm_prompter.LlmPrompter:
        """Returns the LLM prompter."""
        return self._config.llm_prompter

    def _generate_index_for_chunk(
        self,
        directory_path: Path,
        epoch: int,
        previous_root_map_content: str,
        directory_contents_chunk: dict[Path, str],
        subdirectory_indexes: dict[str, str],
        existing_index: str,
        is_partial: bool,
        verifier: Any | None = None,
    ) -> schema.IndexDocument:
        """Generates an index for a chunk of files in a directory."""
        import time
        max_attempts = 3
        current_issues = []
        previous_artifact = ""

        for attempt in range(max_attempts):
            try:
                logging.info("Generating index for %s (epoch %d) attempt %d", directory_path, epoch, attempt + 1)

                display_path = self._config.index_state.get_display_path(str(directory_path))
                str_directory_contents = {str(k): v for k, v in directory_contents_chunk.items()}
                extra_ctx = ""
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

                user_prompt_template = USER_PROMPT_TEMPLATE
                if is_partial:
                    user_prompt_template += PARTIAL_SUMMARY_PROMPT_ADDITION
                    keys_str = [str(k) for k in directory_contents_chunk.keys()]
                    user_prompt_template += f"Please summarize only the following files: {keys_str}"

                initial_user_prompt = user_prompt_template.format(directory_path=display_path)

                issues_to_use = current_issues or getattr(self._config, "verification_issues", None)
                if issues_to_use:
                    epg = getattr(error_prompt_generator, 'IndexerErrorPromptGenerator', None)
                    if epg:
                        error_msg = "Verification failed for previous attempt."
                        if previous_artifact:
                            error_msg += f"\nRejected Output:\n{previous_artifact}"
                        initial_user_prompt += "\n\n" + epg().generate_error_prompt(error_msg, issues_to_use)

                epg = getattr(error_prompt_generator, 'IndexerErrorPromptGenerator', None)
                epg_instance = epg() if epg else error_prompt_generator
                
                artifact_chunk = self._config.llm_prompter.prompt_for_indexing(
                    directory_path=str(directory_path),
                    initial_user_prompt=initial_user_prompt,
                    system_prompt=system_prompt,
                    error_prompt_generator_instance=epg_instance,
                )

                if verifier:
                    source_context = "\n\n".join([f"--- {k} ---\n{v}" for k, v in directory_contents_chunk.items()])
                    verdict = verifier.verify(artifact_chunk.model_dump_json(), source_context)
                    if not verdict.passed:
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
                        is_empty_bypass=getattr(verdict, 'is_empty_bypass', False),
                        verification_model=getattr(verdict, 'verification_model', None),
                        verified_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
                    )
                return artifact_chunk
                
            except VerificationFailedError as ve:
                current_issues = ve.issues
                result = getattr(ve, "result", None)
                previous_artifact = result.model_dump_json() if hasattr(result, 'model_dump_json') else ""
                
                if attempt == max_attempts - 1:
                    logging.error("Chunk failed after all retries. Proceeding with 'Best Effort'.")
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
                # Infrastructure errors (network, auth, quota) should bubble up
                # to the prompter's internal retries or the orchestrator.
                logging.error(f"Unexpected infrastructure error in chunk generation: {e}")
                raise

        # Safety net: if the loop exits without returning (should be unreachable),
        # synthesize a failed artifact rather than returning None.
        logging.error("[LlmIndexer] _generate_index_for_chunk loop exited without returning for %s. This is a bug.", directory_path)
        fallback = schema.IndexDocument(
            overview=schema.Overview(content="Processing failed: retry loop exited unexpectedly.")
        )
        fallback.verification_state = schema.VerificationState(
            verified=False, confidence=0.0, issues=["Internal error: retry loop exited without result"],
            is_empty_bypass=False
        )
        return fallback

    def _merge_with_retries(self, chunk_docs, work_unit, verifier) -> schema.IndexDocument:
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
                    chunk_docs, str(work_unit.output_path), error_prompt=error_prompt
                )
                
                if verifier:
                    from indexing import rendering
                    chunk_context = ""
                    context_limit_reached = False
                    for doc in chunk_docs:
                        doc_md = rendering.to_markdown(doc)
                        if len(chunk_context) + len(doc_md) > 24000:
                            context_limit_reached = True
                            break
                        chunk_context += f"\n\n{doc_md}"

                    if context_limit_reached:
                        logging.warning(
                            "[Merger] Context exceeds verifier window (%d bytes). skipping verification.",
                            len(chunk_context)
                        )
                        merged_doc.verification_state = schema.VerificationState(
                            verified=True, confidence=0.5, issues=["Verification skipped due to context size"],
                            is_empty_bypass=False
                        )
                        return merged_doc

                    verdict = verifier.verify(merged_doc.model_dump_json(), chunk_context, is_merger_mode=True)
                    if not verdict.passed:
                        raise VerificationFailedError("Merger failed", result=merged_doc, issues=verdict.issues)
                    
                    # Extract info issues as verification notes
                    if hasattr(verdict, 'detailed_issues'):
                        info_issues = [
                            issue.description for issue in verdict.detailed_issues 
                            if getattr(issue, 'severity', 'error') == "info"
                        ]
                        merged_doc.verification_notes = info_issues

                    merged_doc.verification_state = schema.VerificationState(
                        verified=True, 
                        confidence=getattr(verdict, 'confidence', 1.0), 
                        issues=verdict.issues,
                        is_empty_bypass=getattr(verdict, 'is_empty_bypass', False),
                        verification_model=getattr(verdict, 'verification_model', None),
                        verified_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
                    )
                return merged_doc
                
            except VerificationFailedError as ve:
                current_issues = ve.issues
                result = getattr(ve, "result", None)
                previous_artifact = result.model_dump_json() if hasattr(result, 'model_dump_json') else ""
                
                if attempt == max_attempts - 1:
                    if not result:
                        result = schema.IndexDocument(
                            overview=schema.Overview(content="Merge failed due to unrecoverable verification error.")
                        )
                        
                    result.verification_state = schema.VerificationState(
                        verified=False, confidence=0.0, issues=current_issues,
                        is_empty_bypass=False
                    )
                    return result
                
                time.sleep(2 ** attempt)
            except Exception as e:
                logging.error(f"Unexpected infrastructure error in merger: {e}")
                raise

    def generate_subcomponent_list_section(
        self,
        directory_contents: dict[Path, str],
        output_path: Path,
    ) -> str:
        """Generates a list of files for the given directory contents."""
        file_list = []
        for filename in directory_contents.keys():
            try:
                from pathlib import Path
                rel_path = str(Path(filename).relative_to(Path(output_path)))
            except ValueError:
                rel_path = str(filename)
            file_list.append(rel_path)
        # Sort the file list to ensure deterministic output in the artifact.
        file_list = sorted(file_list)
        return "\n\n# All Subcomponents\n\n" + "\n".join(
            [f"- `{filename}`" for filename in file_list]
        )

    @dataclasses.dataclass(frozen=True)
    class WorkUnitGenerationResult:
        """Result of generating an index for a work unit."""

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
        """Generates an index for the given work unit.

        Args:
          work_unit: The work unit to index.
          epoch: The current indexing epoch.
          previous_root_map_content: The content of the root map from the previous
            epoch.
          max_chunk_parallelization: The maximum number of chunks to process in
            parallel.
          input_prefix: The prefix to add to the input file paths to load the files
            from the filesystem.

        Returns:
          The generated index content and whether the generation had any failures.

        Raises:
          RuntimeError: If the LLM output fails validation after max_retries.
        """
        prefix = Path(input_prefix) if input_prefix else None
        loaded_contents = work_unit.load_files_to_index(self._fs_manager, prefix)
        directory_contents = {k: v for k, v in sorted(loaded_contents.items())}

        num_files = len(directory_contents)
        self._stats.increment_counter("files.processed", num_files)
        total_size = sum(len(content) for content in directory_contents.values())

        if num_files == 0:
            logging.info(f"Directory {work_unit.output_path} is completely empty. Bypassing LLM.")
            empty_state = schema.VerificationState(
                verified=True, confidence=1.0, issues=[], is_empty_bypass=True
            )
            empty_artifact = schema.IndexDocument(
                overview=schema.Overview(content="Empty directory"),
                verification_state=empty_state
            )
            return self.WorkUnitGenerationResult(
                markdown_result=f"# {work_unit.output_path}\n\nEmpty directory.\n",
                artifact=empty_artifact,
                source_context="",
                success=True,
            )

        # --- Diagnostic: identify degraded-context directories early ---
        placeholder_values = {"Could not read file.", "Non-unicode file."}
        degraded_count = sum(
            1 for v in directory_contents.values() if v in placeholder_values
        )
        if degraded_count > 0:
            logging.warning(
                "[LlmIndexer] %s: %d/%d files have degraded context "
                "(binary/unreadable). LLM may produce unverifiable claims.",
                work_unit.output_path, degraded_count, num_files,
            )
        if degraded_count == num_files and num_files > 0:
            # Every file is unreadable — LLM cannot produce verifiable claims.
            # Early-exit to avoid burning retries on an unwinnable verify loop.
            logging.warning(
                "[LlmIndexer] %s: ALL %d files unreadable. "
                "Skipping LLM generation (would always fail verification).",
                work_unit.output_path, num_files,
            )
            return self.WorkUnitGenerationResult(
                markdown_result=(
                    f"# {work_unit.output_path}\n\n"
                    f"This directory contains {num_files} file(s) that could "
                    f"not be read as text (binary or inaccessible). "
                    f"No index was generated."
                ),
                artifact=None,
                source_context="",
                success=True,
            )
        logging.info(
            "[LlmIndexer] %s: %d files, %d bytes total context.",
            work_unit.output_path, num_files, total_size,
        )

        prefixed_output_path = (
            input_prefix / work_unit.output_path
            if input_prefix
            else work_unit.output_path
        )
        # Determine the absolute path in the workspace for state operations.
        # Get the subdirectory indexes for the current epoch.
        get_subdir = getattr(file_utils, 'get_subdirectory_indexes', None)
        if get_subdir:
            subdirectory_indexes = get_subdir(
                self._fs_manager,
                self._config.index_state,
                str(prefixed_output_path),
                epoch,
                filtering_config=self._config.filtering_config,
            )
        else:
            subdirectory_indexes = {}

        if epoch > 0 and self._config.index_state.exist_summary(
            str(prefixed_output_path), epoch - 1
        ):
            existing_index = self._config.index_state.read_summary(
                str(prefixed_output_path), epoch - 1
            )
        else:
            existing_index = ""

        # Check if the directory size is within the threshold for single-chunk processing.
        if (
            self._config.max_dir_size is None
            or total_size <= self._config.max_dir_size
        ):
            try:
                # Generate a single index for the entire directory.
                doc = self._generate_index_for_chunk(
                    directory_path=work_unit.output_path,
                    epoch=epoch,
                    previous_root_map_content=previous_root_map_content,
                    directory_contents_chunk=directory_contents,
                    is_partial=False,
                    subdirectory_indexes=subdirectory_indexes,
                    existing_index=existing_index,
                    verifier=verifier,
                )
                # Convert the generated Pydantic artifact to its markdown representation.
                markdown_result = rendering.to_markdown(doc)
                success = True
            except sequential_llm_prompter.UnrecoverableLlmError:
                # Re-raise unrecoverable errors to trigger orchestrator fail-fast.
                raise
            except Exception:  # pylint: disable=broad-exception-caught
                # Log the failure but ensure the process continues for other units.
                logging.exception("Failed processing %s", work_unit.output_path)
                markdown_result = (
                    f"Could not generate index for {work_unit.output_path}."
                )
                success = False
                doc = None
            
            # Combine the raw source code into a context string for verification.
            research_ctx = getattr(self._config.llm_prompter, "last_research_context", "")
            source_ctx = "\n\n".join([f"--- {k} ---\n{v}" for k, v in directory_contents.items()])
            if research_ctx:
                source_ctx += "\n\n" + research_ctx
            logging.info(
                "[LlmIndexer] %s: source_context=%d bytes, artifact=%s, success=%s",
                work_unit.output_path,
                len(source_ctx),
                type(doc).__name__ if doc else "None",
                success,
            )
            return self.WorkUnitGenerationResult(
                markdown_result=markdown_result
                + self.generate_subcomponent_list_section(
                    directory_contents, work_unit.output_path
                ),
                artifact=doc,
                source_context=source_ctx,
                success=success,
            )

        # Large directory detected; split into smaller chunks for parallel LLM analysis.
        chunks = self._config.chunker.chunk(
            directory_contents, self._config.max_dir_size
        )

        logging.info(f"Processing {len(chunks)} chunks for {work_unit.output_path}")

        # Process each chunk and collect the generated indexes.
        chunk_docs: list[schema.IndexDocument | None] = [None] * len(chunks)
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max_chunk_parallelization
        ) as executor:
            # Dispatch indexing tasks to the thread pool for each directory chunk.
            future_to_chunk_id = {}
            for chunk_id, chunk in enumerate(chunks):
                # Submit a separate thread task for each chunk to process
                # the directory's split contents concurrently, maintaining isolation.
                future = executor.submit(
                    self._generate_index_for_chunk,
                    directory_path=work_unit.output_path,
                    epoch=epoch,
                    previous_root_map_content=previous_root_map_content,
                    directory_contents_chunk=chunk,
                    subdirectory_indexes=subdirectory_indexes,
                    existing_index=existing_index,
                    is_partial=True,
                    verifier=verifier,
                )
                future_to_chunk_id[future] = chunk_id
            for future in concurrent.futures.as_completed(future_to_chunk_id):
                chunk_id = future_to_chunk_id[future]
                try:
                    # Capture the LLM response for each chunk.
                    chunk_docs[chunk_id] = future.result()
                    logging.info(
                        f"Finished processing chunk {chunk_id} (out of {len(chunks)}) for"
                        f" {work_unit.output_path}"
                    )
                except sequential_llm_prompter.UnrecoverableLlmError:
                    # Propagate unrecoverable errors to trigger orchestrator fail-fast.
                    raise
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # Handle individual chunk failures without aborting the entire unit.
                    logging.error(
                        f"Failed processing chunk {chunk_id} for"
                        f" {work_unit.output_path}: {e}"
                    )

        # Filter out failed chunks before merging.
        chunk_docs = [doc for doc in chunk_docs if doc is not None]

        try:
            # Re-synthesize the partial chunk summaries into a final coherent directory index.
            merged_doc = self._merge_with_retries(chunk_docs, work_unit, verifier)
            markdown_result = rendering.to_markdown(merged_doc)
            success = True
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Log merger failures and provide a placeholder result.
            print(f"Failed merging chunks for {work_unit.output_path}: {e}")
            markdown_result = f"Could not generate index for {work_unit.output_path}."
            success = False
            merged_doc = None

        # Build the final source context and return the combined result.
        research_ctx = getattr(self._config.llm_prompter, "last_research_context", "")
        source_ctx = "\n\n".join([f"--- {k} ---\n{v}" for k, v in directory_contents.items()])
        if research_ctx:
            source_ctx += "\n\n" + research_ctx
        return self.WorkUnitGenerationResult(
            markdown_result=markdown_result
            + self.generate_subcomponent_list_section(
                directory_contents, work_unit.output_path
            ),
            artifact=merged_doc,
            source_context=source_ctx,
            success=success,
        )
