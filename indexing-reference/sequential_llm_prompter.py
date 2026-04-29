"""Sequential prompt runner used by the indexing pipeline.

No screenshot in the current verified pass has been confidently matched to
`sequential_llm_prompter.py`. The local stub stays importable, but its earlier
photo attribution has been removed until we verify the correct image span.
"""

try:
    from indexing.prompt_templates import system_prompt
except ImportError:
    def system_prompt() -> str:
        return "Reference system prompt placeholder."


REFERENCE_EXCERPT = """\
# No confirmed screenshot-backed excerpt yet for sequential_llm_prompter.py.
"""


class SequentialLlmPrompter:
    """Small executable stub with preserved reference text below."""

    def build_messages(self, prompt: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": system_prompt()},
            {"role": "user", "content": prompt},
        ]
