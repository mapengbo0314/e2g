"""Single registration point for structured index sections.

The published artifact is still ``schema.IndexDocument``. This registry keeps
the current section contract in one place so coercion, assembly, and markdown
rendering stop drifting independently.
"""

from __future__ import annotations

from collections.abc import Callable
import dataclasses
from typing import Any

from indexing import schema


@dataclasses.dataclass(frozen=True)
class SectionSpec:
    """Metadata for one published index section."""

    section_id: str
    payload_model: type[Any]
    render_order: int
    producer_wrapper: str | None = None
    list_field: str | None = None
    item_model_name: str | None = None
    content_field: str | None = None
    field_defaults: dict[str, Any] = dataclasses.field(default_factory=dict)
    producer_agent: str = ""
    verification_policy: str = "optional"
    merge_strategy: str = "llm_synthesized"
    summary_projection: str = "full"
    render_fn: Callable[[Any], str | None] | None = None


import re

def _get_anchor_name(item: Any) -> str:
    """Generates a stable, unique markdown-safe anchor name for an item."""
    if hasattr(item, "file_path") and hasattr(item, "name"):
        safe_path = re.sub(r'[^a-zA-Z0-9]', '_', item.file_path)
        return f"sym_{safe_path}_{item.name}"
    if hasattr(item, "file_path") and hasattr(item, "primitive"):
         safe_path = re.sub(r'[^a-zA-Z0-9]', '_', item.file_path)
         safe_primitive = re.sub(r'[^a-zA-Z0-9]', '_', item.primitive)
         line = getattr(item, "line_number", 0)
         return f"inv_{safe_path}_{safe_primitive}_{line}"
    return ""


def _render_overview(section: schema.Overview) -> str | None:
    return f"# Overview\n\n{section.content}" if section.content else None


def _render_deep_dive(section: schema.DeepDive) -> str | None:
    return f"# Deep Dive\n\n{section.content}" if section.content else None


def _render_key_individual_components(
    section: schema.KeyIndividualComponents,
) -> str | None:
    if not section.components:
        return None
    items = []
    for component in section.components:
        anchor = _get_anchor_name(component)
        anchor_tag = f"<a name=\"{anchor}\"></a>" if anchor else ""
        items.append(f"- **{component.name}**: {component.description} {anchor_tag}")
    return f"# Key Individual Components\n\n" + "\n".join(items)


def _render_key_interfaces(section: schema.KeyInterfaces) -> str | None:
    if not section.interfaces:
        return None
    items = []
    for interface in section.interfaces:
        anchor = _get_anchor_name(interface)
        anchor_tag = f"<a name=\"{anchor}\"></a>" if anchor else ""
        items.append(f"- **{interface.name}**: {interface.description} {anchor_tag}")
    return f"# Key Interfaces\n\n" + "\n".join(items)


def _render_key_dependencies(section: schema.KeyDependencies) -> str | None:
    if not section.dependencies:
        return None
    items = []
    for dependency in section.dependencies:
        type_label = ""
        if getattr(dependency, "dependency_type", "internal") != "internal":
            type_label = f" *[{dependency.dependency_type}]*"
        items.append(
            f"- **{dependency.name}**{type_label}: {dependency.usage_description}"
        )
    return f"# Key Dependencies\n\n" + "\n".join(items)


def _render_architectural_patterns_and_gotchas(
    section: schema.ArchitecturalPatternsAndGotchas,
) -> str | None:
    return (
        f"# Architectural Patterns and Gotchas\n\n{section.content}"
        if section.content
        else None
    )


def _render_testing_strategy(section: schema.TestingStrategy) -> str | None:
    return f"# Testing Strategy\n\n{section.content}" if section.content else None


def _render_configurations(section: schema.Configurations) -> str | None:
    if not section.configurations:
        return None
    items = "\n".join(
        [
            f"- **{config.name}**: {config.description} "
            f"(Defined in: {config.definition_link})"
            f"{' Comments: ' + config.comments if config.comments else ''}"
            for config in section.configurations
        ]
    )
    return f"# Configuration and flags\n\n{items}"


def _render_implementation_invariants(
    section: schema.ImplementationInvariants,
) -> str | None:
    if not section.invariants:
        return None
    items = []
    for invariant in section.invariants:
        anchor = _get_anchor_name(invariant)
        anchor_tag = f"<a name=\"{anchor}\"></a>" if anchor else ""
        items.append(f"- **{invariant.primitive}**: {invariant.intent} ({invariant.usage_context}) {anchor_tag}")
    return f"# Implementation Invariants\n\n" + "\n".join(items)


def _render_blueprint(section: schema.Blueprint) -> str | None:
    if not section.symbols:
        return None
    items = []
    for symbol in section.symbols:
        anchor = _get_anchor_name(symbol)
        anchor_tag = f"<a name=\"{anchor}\"></a>" if anchor else ""
        items.append(f"- {anchor_tag}`{symbol.signature}`: {symbol.summary}")
    return f"# Blueprint\n\n" + "\n".join(items)


def _render_workflow_patterns(section: schema.WorkflowPatterns) -> str | None:
    if not section.patterns:
        return None
    items = []
    for pattern in section.patterns:
        flow = " -> ".join(pattern.edges) if pattern.edges else "Single Node"
        items.append(
            f"- **{pattern.name}** ({pattern.framework}): {pattern.summary}\n"
            f"  - Flow: `{flow}`\n"
            f"  - Entry: `{pattern.entry_point}`"
        )
    return f"# Workflow Patterns\n\n" + "\n".join(items)


def _render_tech_debt(section: schema.TechDebt) -> str | None:
    if not section.notes:
        return None
    items = "\n".join(
        [
            f"- **{note.category}**: {note.description} *Impact: {note.impact}*"
            for note in section.notes
        ]
    )
    return f"# Tech Debt\n\n{items}"


def _render_custom_section(section: schema.CustomSectionData) -> str | None:
    return f"# {section.title}\n\n{section.content}" if section.content else None


SECTION_SPECS: tuple[SectionSpec, ...] = (
    SectionSpec("overview", schema.Overview, 10, content_field="content", render_fn=_render_overview),
    SectionSpec("deep_dive", schema.DeepDive, 20, content_field="content", render_fn=_render_deep_dive),
    SectionSpec(
        "architectural_patterns_and_gotchas",
        schema.ArchitecturalPatternsAndGotchas,
        30,
        content_field="content",
        producer_wrapper="architectural_patterns_and_gotchas",
        producer_agent="key_components_agent",
        render_fn=_render_architectural_patterns_and_gotchas,
    ),
    SectionSpec(
        "key_individual_components",
        schema.KeyIndividualComponents,
        40,
        producer_wrapper="key_individual_components",
        list_field="components",
        item_model_name="Component",
        field_defaults={"description": ""},
        producer_agent="key_components_agent",
        merge_strategy="deterministic_union",
        render_fn=_render_key_individual_components,
    ),
    SectionSpec(
        "key_interfaces",
        schema.KeyInterfaces,
        50,
        producer_wrapper="key_interfaces",
        list_field="interfaces",
        item_model_name="Interface",
        field_defaults={"description": ""},
        producer_agent="key_components_agent",
        merge_strategy="deterministic_union",
        verification_policy="required_for_code",
        render_fn=_render_key_interfaces,
    ),
    SectionSpec(
        "blueprint",
        schema.Blueprint,
        60,
        producer_wrapper="blueprint",
        list_field="symbols",
        item_model_name="ExportedSymbol",
        field_defaults={"name": "", "signature": "", "summary": ""},
        producer_agent="key_components_agent",
        merge_strategy="deterministic_union",
        verification_policy="required_for_code",
        render_fn=_render_blueprint,
    ),
    SectionSpec(
        "workflow_patterns",
        schema.WorkflowPatterns,
        70,
        producer_wrapper="workflow_patterns",
        list_field="patterns",
        item_model_name="WorkflowPattern",
        field_defaults={
            "name": "",
            "framework": "",
            "summary": "",
            "nodes": [],
            "edges": [],
            "entry_point": "",
        },
        producer_agent="key_components_agent",
        merge_strategy="deterministic_union",
        render_fn=_render_workflow_patterns,
    ),
    SectionSpec(
        "key_dependencies",
        schema.KeyDependencies,
        80,
        producer_wrapper="key_dependencies",
        list_field="dependencies",
        item_model_name="Dependency",
        field_defaults={"usage_description": ""},
        producer_agent="key_components_agent",
        merge_strategy="deterministic_union",
        render_fn=_render_key_dependencies,
    ),
    SectionSpec(
        "implementation_invariants",
        schema.ImplementationInvariants,
        90,
        producer_wrapper="implementation_invariants",
        list_field="invariants",
        item_model_name="ImplementationInvariant",
        field_defaults={"primitive": "", "intent": "", "usage_context": ""},
        producer_agent="key_components_agent",
        merge_strategy="deterministic_union",
        verification_policy="required_for_code",
        render_fn=_render_implementation_invariants,
    ),
    SectionSpec(
        "configurations",
        schema.Configurations,
        100,
        producer_wrapper="configurations",
        list_field="configurations",
        item_model_name="ConfigurationItem",
        field_defaults={"definition_link": "", "description": ""},
        producer_agent="key_components_agent",
        merge_strategy="deterministic_union",
        render_fn=_render_configurations,
    ),
    SectionSpec(
        "testing_strategy",
        schema.TestingStrategy,
        110,
        content_field="content",
        producer_wrapper="testing_strategy",
        producer_agent="key_components_agent",
        render_fn=_render_testing_strategy,
    ),
    SectionSpec(
        "tech_debt",
        schema.TechDebt,
        120,
        producer_wrapper="tech_debt",
        list_field="notes",
        item_model_name="TechDebtNote",
        field_defaults={"category": "", "description": "", "impact": ""},
        producer_agent="key_components_agent",
        merge_strategy="accumulate",
        render_fn=_render_tech_debt,
    ),
)


_SECTION_BY_ID = {spec.section_id: spec for spec in SECTION_SPECS}
_SECTION_BY_MODEL = {
    spec.payload_model: spec for spec in SECTION_SPECS if spec.render_fn is not None
}
_CUSTOM_SECTION_SPEC = SectionSpec(
    "custom_sections",
    schema.CustomSectionData,
    10_000,
    render_fn=_render_custom_section,
)


def ordered_section_ids() -> list[str]:
    """Returns published section ids in markdown render order."""
    return [spec.section_id for spec in sorted(SECTION_SPECS, key=lambda s: s.render_order)]


def list_field_map() -> dict[str, tuple[str, str]]:
    """Returns wrapper -> (list field, item model name) for list-like sections."""
    return {
        spec.section_id: (spec.list_field, spec.item_model_name)
        for spec in SECTION_SPECS
        if spec.list_field and spec.item_model_name
    }


def field_defaults() -> dict[str, dict[str, Any]]:
    """Returns item model defaults used by LLM output coercion."""
    return {
        spec.item_model_name: dict(spec.field_defaults)
        for spec in SECTION_SPECS
        if spec.item_model_name and spec.field_defaults
    }


def content_field_map() -> dict[str, str]:
    """Returns wrapper -> content field name for text-heavy sections."""
    return {
        spec.section_id: spec.content_field
        for spec in SECTION_SPECS
        if spec.content_field
    }


def key_components_section_ids() -> list[str]:
    """Returns IndexDocument fields produced by KeyComponentsDocument."""
    return [
        spec.section_id
        for spec in SECTION_SPECS
        if spec.producer_agent == "key_components_agent"
    ]


def key_components_payloads(key_components_doc: schema.KeyComponentsDocument) -> dict[str, Any]:
    """Extracts registered key-components sections for final IndexDocument assembly."""
    return {
        section_id: getattr(key_components_doc, section_id)
        for section_id in key_components_section_ids()
    }


def render_section(section: Any) -> str | None:
    """Renders a registered section instance to markdown."""
    if isinstance(section, schema.CustomSectionData):
        return _CUSTOM_SECTION_SPEC.render_fn(section)

    spec = _SECTION_BY_MODEL.get(type(section))
    if spec and spec.render_fn:
        return spec.render_fn(section)
    return None


def get_section_spec(section_id: str) -> SectionSpec:
    """Returns the spec for a registered published section."""
    return _SECTION_BY_ID[section_id]


def is_section_empty(section_id: str, section_instance: Any) -> bool:
    """Returns True if the section is missing or its primary payload is empty."""
    if section_instance is None:
        return True
    
    if section_id not in _SECTION_BY_ID:
        # Unknown sections are considered empty if not present
        return True

    spec = _SECTION_BY_ID[section_id]
    if spec.list_field:
        items = getattr(section_instance, spec.list_field, None)
        return not bool(items)
    if spec.content_field:
        content = getattr(section_instance, spec.content_field, None)
        return not bool(content)
    
    return False


def get_mandatory_sections() -> list[str]:
    """Returns a list of section IDs that are required for directories containing code."""
    return [
        spec.section_id
        for spec in SECTION_SPECS
        if spec.verification_policy == "required_for_code"
    ]


def merge_sections(section_id: str, instances: list[Any]) -> Any:
    """Merges multiple instances of a section based on its registered strategy.

    This implements programmatic merges for 'deterministic_union' and 'accumulate'
    strategies, reducing LLM token usage and improving structural reliability.
    """
    spec = _SECTION_BY_ID.get(section_id)
    if not spec:
        return instances[0] if instances else None

    # Filter out None instances and empty sections
    instances = [i for i in instances if i is not None and not is_section_empty(section_id, i)]
    if not instances:
        return None
    if len(instances) == 1:
        return instances[0]

    if spec.merge_strategy == "deterministic_union" and spec.list_field:
        # Union of items, deduplicating by a stable key (usually 'name' or 'primitive').
        all_items = []
        seen_keys = set()
        
        for inst in instances:
            items = getattr(inst, spec.list_field, [])
            for item in items:
                # Determine the primary key for deduplication.
                # ExportedSymbol uses (name, signature, file_path) for maximum precision.
                if isinstance(item, schema.ExportedSymbol):
                    key = (item.name, item.signature, item.file_path)
                else:
                    key = getattr(item, "name", getattr(item, "primitive", None))
                
                if key not in seen_keys:
                    all_items.append(item)
                    seen_keys.add(key)
        
        # Return a new instance of the payload model with the merged items.
        return spec.payload_model(**{spec.list_field: all_items})

    if spec.merge_strategy == "accumulate" and spec.list_field:
        # Simple concatenation for sections where all evidence is additive (e.g. tech debt).
        all_items = []
        for inst in instances:
            all_items.extend(getattr(inst, spec.list_field, []))
        return spec.payload_model(**{spec.list_field: all_items})

    # For 'llm_synthesized' or unknown strategies, we return the first one.
    # The caller (SummaryMerger) is responsible for coordinating LLM-based merges.
    return instances[0]


def get_deterministic_section_ids() -> list[str]:
    """Returns section IDs that can be merged programmatically."""
    return [
        spec.section_id
        for spec in SECTION_SPECS
        if spec.merge_strategy in ("deterministic_union", "accumulate")
    ]
