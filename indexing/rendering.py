"""Logic for rendering structured IndexDocument artifacts to Markdown.

Separates presentation logic from the data models defined in schema.py.
"""

from __future__ import annotations

import re
from typing import Optional

from indexing import schema


def sanitize_unicode(text: str) -> str:
    """Removes control characters and replaces invalid UTF-8 characters."""
    # Eliminate non-printable control characters from the text stream.
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)
    text = text.encode("utf-8", errors="replace").decode("utf-8")
    return text


def render_section(section: schema.Section) -> Optional[str]:
    """Renders a single schema section to Markdown."""
    if isinstance(section, schema.Overview):
        return f"# Overview\n\n{section.content}" if section.content else None
    
    if isinstance(section, schema.DeepDive):
        return f"# Deep Dive\n\n{section.content}" if section.content else None
    
    if isinstance(section, schema.KeyIndividualComponents):
        if not section.components:
            return None
        # Format each component as a bullet point with bolded name labels.
        items = "\n".join(
            [f"- **{c.name}**: {c.description}" for c in section.components]
        )
        return f"# Key Individual Components\n\n{items}"
    
    if isinstance(section, schema.KeyInterfaces):
        if not section.interfaces:
            return None
        # Aggregate interface definitions into a structured list of descriptions.
        items = "\n".join(
            [f"- **{i.name}**: {i.description}" for i in section.interfaces]
        )
        return f"# Key Interfaces\n\n{items}"
    
    if isinstance(section, schema.KeyDependencies):
        if not section.dependencies:
            return None
        # Map each dependency to its respective usage description string.
        # Include type indicator for external/unverified dependencies.
        items = []
        for d in section.dependencies:
            type_label = ""
            if getattr(d, "dependency_type", "internal") != "internal":
                type_label = f" *[{d.dependency_type}]*"
            items.append(f"- **{d.name}**{type_label}: {d.usage_description}")
        
        return f"# Key Dependencies\n\n" + "\n".join(items)
    
    if isinstance(section, schema.ArchitecturalPatternsAndGotchas):
        return (
            f"# Architectural Patterns and Gotchas\n\n{section.content}"
            if section.content
            else None
        )
    
    if isinstance(section, schema.TestingStrategy):
        return f"# Testing Strategy\n\n{section.content}" if section.content else None
    
    if isinstance(section, schema.Configurations):
        if not section.configurations:
            return None
        # Construct a detailed list of configuration flags with definition links.
        items = "\n".join(
            [
                f"- **{config.name}**: {config.description} "
                f"(Defined in: {config.definition_link})"
                f"{' Comments: ' + config.comments if config.comments else ''}"
                for config in section.configurations
            ]
        )
        return f"# Configuration and flags\n\n{items}"
    
    if isinstance(section, schema.CustomSectionData):
        return f"# {section.title}\n\n{section.content}" if section.content else None
    
    return None


def to_markdown(doc: schema.IndexDocument) -> str:
    """Converts an IndexDocument to a formatted Markdown string."""
    output = []
    # Define the canonical ordering for sections in the final markdown document.
    section_order = [
        "overview",
        "deep_dive",
        "architectural_patterns_and_gotchas",
        "key_individual_components",
        "key_interfaces",
        "key_dependencies",
        "configurations",
        "testing_strategy",
    ]

    # Iterate through the ordered sections and render them if present.
    for field_name in section_order:
        section = getattr(doc, field_name)
        if section and isinstance(section, schema.Section):
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
        output.append(f"---\n*Verified{model_str}{time_str} (Confidence: {vs.confidence:.2f})*")

    result = "\n\n".join(output)
    return sanitize_unicode(result)
