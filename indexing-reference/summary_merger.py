"""Merge chunk-level summaries into a directory-level result."""


class SummaryMerger:
    def merge(self, summaries: list[str]) -> str:
        cleaned = [summary.strip() for summary in summaries if summary.strip()]
        return "\n\n".join(cleaned)
