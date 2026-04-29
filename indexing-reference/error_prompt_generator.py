"""Helpers for generating repair or error-analysis prompts."""


def build_error_prompt(message: str, context: str = "") -> str:
    prefix = "Explain the failure and propose the next recovery step."
    if context:
        return f"{prefix}\n\nContext:\n{context}\n\nError:\n{message}"
    return f"{prefix}\n\nError:\n{message}"
