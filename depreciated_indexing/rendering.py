"""Logic for rendering structured IndexDocument artifacts to Markdown.

Separates presentation logic from the data models defined in schema.py.
"""

from __future__ import annotations

import re
from typing import Optional

from indexing import schema
from indexing import section_registry


def sanitize_unicode(text: str) -> str:
    """Removes control characters and replaces invalid UTF-8 characters."""
    # Eliminate non-printable control characters from the text stream.
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)
    text = text.encode("utf-8", errors="replace").decode("utf-8")
    return text


def render_section(section: schema.Section) -> Optional[str]:
    """Renders a single schema section to Markdown."""
    return section_registry.render_section(section)


def to_markdown(doc: schema.IndexDocument) -> str:
    """Converts an IndexDocument to a formatted Markdown string."""
    output = []
    # Iterate through the ordered sections and render them if present.
    for field_name in section_registry.ordered_section_ids():
        section = getattr(doc, field_name)
        if section:
            md = render_section(section)
            if md:
                output.append(md.strip())

    for custom_section in doc.custom_sections:
        md = render_section(custom_section)
        if md:
            output.append(md.strip())

    if doc.verification_notes:
        notes = "\n".join([f"- {note}" for note in doc.verification_notes])
        output.append(f"# Verification Notes\n\n> [!NOTE]\n> These are informational findings from the verifier (e.g., documented claims not yet found in the code).\n\n{notes}")

    # Add verification footer for auditability.
    if doc.verification_state and doc.verification_state.verified:
        vs = doc.verification_state
        model_str = f" by {vs.verification_model}" if vs.verification_model else ""
        time_str = f" at {vs.verified_at}" if vs.verified_at else ""
        
        footer_parts = [f"*Verified{model_str}{time_str} (Confidence: {vs.confidence:.2f})*"]
        
        if doc.generation_metadata and doc.generation_metadata.cost_report:
            cr = doc.generation_metadata.cost_report
            models = ", ".join(cr.model_breakdown.keys())
            footer_parts.append(f"*Usage ({models}): {cr.total_input_tokens:,} in / {cr.total_output_tokens:,} out tokens across {cr.total_calls} calls ({cr.total_latency_ms}ms)*")
            
        output.append("---\n" + "\n".join(footer_parts))

    result = "\n\n".join(output)
    return sanitize_unicode(result)
