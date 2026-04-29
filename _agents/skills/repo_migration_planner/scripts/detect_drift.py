"""Placeholder drift detector for migration planning artifacts."""


def detect_drift(current_summary: str, target_summary: str) -> bool:
    return current_summary.strip() != target_summary.strip()
