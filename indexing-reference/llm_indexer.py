"""Indexer for a single directory using an LLM.

This collects context about a given directory and uses Gemini to produce a
summary.

Does not handle recursive indexing; walking a directory tree is the
responsibility of the caller.
"""

from collections.abc import Sequence
import concurrent.futures
import dataclasses

from absl import logging

from mono.coresystems.data.excellence.applications.indexing import chunker as chunker_lib
from mono.coresystems.data.excellence.applications.indexing import error_prompt_generator
from mono.coresystems.data.excellence.applications.indexing import file_utils
from mono.coresystems.data.excellence.applications.indexing import prompt_templates
from mono.coresystems.data.excellence.applications.indexing import schema
from mono.coresystems.data.excellence.applications.indexing import sequential_llm_prompter
from mono.coresystems.data.excellence.applications.indexing import state
from mono.coresystems.data.excellence.applications.indexing import summary_merger as summary_merger_lib
from mono.coresystems.data.excellence.applications.indexing import work_unit as work_unit_lib
from mono.coresystems.data.excellence.applications.indexing.config import bundle_pb2
from mono.coresystems.data.excellence.applications.indexing.config.indexer import indexer_config
from mono.coresystems.data.excellence.applications.indexing.filesystem import file_system_manager_base
from mono.coresystems.data.excellence.applications.indexing.indexer import path_filtering_config
from mono.coresystems.data.excellence.infra.utils import stat_recorder
from mono.pyglib.contrib.gpathlib import gpath


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
        specific codebase instead of the default generic mono context.
      filtering_config: Optional configuration for filtering paths.
      custom_sections: Custom sections requested by the user.
    """

    llm_prompter: sequential_llm_prompter.LlmPrompter
    index_state: state.State
    chunker: chunker_lib.Chunker
    summary_merger: summary_merger_lib.SummaryMerger
    config: indexer_config.IndexerConfig
    max_dir_size: int | None = None
    include_search_tool: bool = True
    codebase_specific_context: str | None = None
    filtering_config: path_filtering_config.PathFilteringConfig | None = None
    custom_sections: (
        Sequence[bundle_pb2.ProjectBundle.CustomSection] | None
    ) = None


class LlmIndexer:
    """Class to generate an index for a directory using an LLM."""

    def __init__(
        self,
        config: LlmIndexerConfig,
        fs_manager: file_system_manager_base.FileSystemManagerBase,
    ) -> None:
        """Initializes the LlmIndexer.

        Args:
          config: Configuration for the LlmIndexer.
          fs_manager: A file system manager to use for file operations.
        """
        self._config = config
        self._stats = stat_recorder.get_instance()
        self._fs_manager = fs_manager

    @property
    def llm_prompter(self) -> sequential_llm_prompter.LlmPrompter:
        """Returns the LLM prompter."""
        return self._config.llm_prompter

    def _generate_index_for_chunk(
        self,
        directory_path: gpath.GPath,
        epoch: int,
        previous_root_map_content: str,
        directory_contents_chunk: dict[gpath.GPath, str],
        subdirectory_indexes: dict[str, str],
        existing_index: str,
        is_partial: bool,
    ) -> schema.IndexDocument:
        """Generates an index for a chunk of files in a directory.

        Args:
          directory_path: The path to the directory to index.
          epoch: The current indexing epoch.
          previous_root_map_content: The content of the root map from the previous
            epoch.
          directory_contents_chunk: A dictionary of file names to their contents for
            the current chunk.
          subdirectory_indexes: A dictionary of subdirectory names to their content
            from the current epoch.
          existing_index: The existing index for the directory.
          is_partial: Whether this is a partial index for a chunk of the directory.

        Returns:
          The generated index content for the current chunk.

        Raises:
          RuntimeError: If the LLM output fails validation after max_retries.
        """
        logging.info("Generating index for %s (epoch %d)", directory_path, epoch)

        # Canonicalize the directory path for display in prompts
        display_path = self._config.index_state.get_display_path(
            str(directory_path)
        )

        str_directory_contents = {
            str(k): v for k, v in directory_contents_chunk.items()
        }
        if epoch > 0:
            system_prompt = prompt_templates.IndexImproverPrompt(
                directory_path=display_path,
                epoch=epoch,
                directory_contents=repr(str_directory_contents),
                subdirectory_indexes=repr(subdirectory_indexes),
                existing_index=existing_index,
                previous_root_map=previous_root_map_content,
                index_file_name=get_index_file_name(epoch),
                codebase_specific_context=self._config.codebase_specific_context,
                custom_sections=self._config.custom_sections,
            )
        else:
            system_prompt = prompt_templates.InitialIndexerPrompt(
                directory_path=display_path,
                epoch=epoch,
                directory_contents=repr(str_directory_contents),
                subdirectory_indexes=repr(subdirectory_indexes),
                existing_index=existing_index,
                previous_root_map=previous_root_map_content,
                index_file_name=get_index_file_name(epoch),
                codebase_specific_context=self._config.codebase_specific_context,
                custom_sections=self._config.custom_sections,
            )

        user_prompt_template = USER_PROMPT_TEMPLATE
        if is_partial:
            user_prompt_template += PARTIAL_SUMMARY_PROMPT_ADDITION
            # Without this explicit list of files to summarize, the LLM frequently
            # gets confused and summarizes the entire directory.
            keys_str = [str(k) for k in directory_contents_chunk.keys()]
            user_prompt_template += (
                f"Please summarize only the following files: {keys_str}"
            )

        initial_user_prompt = user_prompt_template.format(
            directory_path=display_path
        )

        logging.info(
            "Generating index for %s with prompt: %s",
            directory_path,
            initial_user_prompt,
        )

        return self._config.llm_prompter.prompt_for_indexing(
            directory_path=str(directory_path),
            initial_user_prompt=initial_user_prompt,
            system_prompt=system_prompt,
            error_prompt_generator_instance=error_prompt_generator.IndexerErrorPromptGenerator(),
        )

    def generate_subcomponent_list_section(
        self,
        directory_contents: dict[gpath.GPath, str],
        output_path: gpath.GPath,
    ) -> str:
        """Generates a list of files for the given directory contents."""
        file_list = []
        for filename in directory_contents.keys():
            try:
                rel_path = str(filename.relative_to(output_path))
            except ValueError:
                rel_path = str(filename)
            file_list.append(rel_path)
        file_list = sorted(file_list)
        return "\n\n# All Subcomponents\n\n" + "\n".join(
            [f"- `{filename}`" for filename in file_list]
        )

    @dataclasses.dataclass(frozen=True)
    class WorkUnitGenerationResult:
        """Result of generating an index for a work unit."""

        markdown_result: str
        success: bool = True

    def generate_index_for_work_unit(
        self,
        work_unit: work_unit_lib.WorkUnit,
        epoch: int,
        previous_root_map_content: str = "",
        max_chunk_parallelization: int | None = None,
        input_prefix: str | None = None,
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
        prefix = gpath.GPath(input_prefix) if input_prefix else None
        loaded_contents = work_unit.load_files_to_index(self._fs_manager, prefix)
        directory_contents = {k: v for k, v in sorted(loaded_contents.items())}

        num_files = len(directory_contents)
        self._stats.increment_counter("files.processed", num_files)

        total_size = sum(len(content) for content in directory_contents.values())

        prefixed_output_path = (
            input_prefix / work_unit.output_path
            if input_prefix
            else work_unit.output_path
        )
        # Get the subdirectory indexes for the current epoch.
        subdirectory_indexes = file_utils.get_subdirectory_indexes(
            self._fs_manager,
            self._config.index_state,
            str(prefixed_output_path),
            epoch,
            filtering_config=self._config.filtering_config,
        )

        if epoch > 0 and self._config.index_state.exist_summary(
            str(prefixed_output_path), epoch - 1
        ):
            existing_index = self._config.index_state.read_summary(
                str(prefixed_output_path), epoch - 1
            )
        else:
            existing_index = ""

        if (
            self._config.max_dir_size is None
            or total_size <= self._config.max_dir_size
        ):
            try:
                doc = self._generate_index_for_chunk(
                    directory_path=work_unit.output_path,
                    epoch=epoch,
                    previous_root_map_content=previous_root_map_content,
                    directory_contents_chunk=directory_contents,
                    is_partial=False,
                    subdirectory_indexes=subdirectory_indexes,
                    existing_index=existing_index,
                )
                markdown_result = schema.to_markdown(doc)
                success = True
            except Exception:  # pylint: disable=broad-exception-caught
                logging.exception("Failed processing %s", work_unit.output_path)
                markdown_result = (
                    f"Could not generate index for {work_unit.output_path}."
                )
                success = False
            return self.WorkUnitGenerationResult(
                markdown_result=markdown_result
                + self.generate_subcomponent_list_section(
                    directory_contents, work_unit.output_path
                ),
                success=success,
            )

        chunks = self._config.chunker.chunk(
            directory_contents, self._config.max_dir_size
        )

        print(f"Processing {len(chunks)} chunks for {work_unit.output_path}")

        # Process each chunk and collect the generated indexes.
        chunk_docs: list[schema.IndexDocument | None] = [None] * len(chunks)
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max_chunk_parallelization
        ) as executor:
            future_to_chunk_id = {
                executor.submit(
                    self._generate_index_for_chunk,
                    directory_path=work_unit.output_path,
                    epoch=epoch,
                    previous_root_map_content=previous_root_map_content,
                    directory_contents_chunk=chunk,
                    subdirectory_indexes=subdirectory_indexes,
                    existing_index=existing_index,
                    is_partial=True,
                ): chunk_id
                for chunk_id, chunk in enumerate(chunks)
            }

            for future in concurrent.futures.as_completed(future_to_chunk_id):
                chunk_id = future_to_chunk_id[future]
                try:
                    chunk_docs[chunk_id] = future.result()
                    print(
                        f"Finished processing chunk {chunk_id} (out of {len(chunks)}) for"
                        f" {work_unit.output_path}"
                    )
                except Exception as e:  # pylint: disable=broad-exception-caught
                    print(
                        f"Failed processing chunk {chunk_id} for"
                        f" {work_unit.output_path}: {e}"
                    )

        chunk_docs = [doc for doc in chunk_docs if doc is not None]

        try:
            merged_doc = self._config.summary_merger.merge(
                chunk_docs, str(work_unit.output_path)
            )
            markdown_result = schema.to_markdown(merged_doc)
            success = True
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Failed merging chunks for {work_unit.output_path}: {e}")
            markdown_result = f"Could not generate index for {work_unit.output_path}."
            success = False

        return self.WorkUnitGenerationResult(
            markdown_result=markdown_result
            + self.generate_subcomponent_list_section(
                directory_contents, work_unit.output_path
            ),
            success=success,
        )
