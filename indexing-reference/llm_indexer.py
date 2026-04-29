"""Directory indexing orchestrated through an LLM prompt layer.

This module preserves a more literal transcription of the visible
`llm_indexer.py` span from `reference-photos/IMG_1655.HEIC`. That screenshot
shows roughly lines 79-178 of the original file, including the constructor,
the `llm_prompter` property, and most of `_generate_index_for_chunk()`.
"""

try:
    from indexing.prompt_templates import directory_prompt
except ImportError:
    def directory_prompt(directory_name: str, file_count: int) -> str:
        return f"Index {directory_name} with {file_count} files."

try:
    from indexing.sequential_llm_prompter import SequentialLlmPrompter
except ImportError:
    from sequential_llm_prompter import SequentialLlmPrompter


REFERENCE_EXCERPT = """\
class LlmIndexer:
  def __init__(
      self,
      config: Configuration,
      fs_manager,
      llm_prompter: sequential_llm_prompter.LlmPrompter,
  ) -> None:
    \"\"\"Initialize the LlmIndexer.

    Args:
      config: Configuration for the LlmIndexer.
      fs_manager: A file system manager to use for file operations.
    \"\"\"
    self._config = config
    self._stats = stat_recorder.get_instance()
    self._fs_manager = fs_manager

  @property
  def llm_prompter(self) -> sequential_llm_prompter.LlmPrompter:
    \"\"\"Returns the LLM prompter.\"\"\"
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
    \"\"\"Generates an index for a chunk of files in a directory.

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
    \"\"\"
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
"""


class LlmIndexer:
    def __init__(self, prompter: SequentialLlmPrompter | None = None) -> None:
        self.prompter = prompter or SequentialLlmPrompter()

    def plan_messages(self, directory_name: str, file_count: int) -> list[dict[str, str]]:
        prompt = directory_prompt(directory_name, file_count)
        return self.prompter.build_messages(prompt)
