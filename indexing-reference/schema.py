"""Pydantic schemas for LLM indexer output.

This is a local, screenshot-backed reconstruction of the main schema contract
used by the indexer. It preserves the important section models and markdown
rendering flow while staying lightweight enough for this reference repo.
"""

from __future__ import annotations

import abc
import re
from typing import List, Optional

try:
    import pydantic
except ImportError:  # pragma: no cover
    pydantic = None


if pydantic is None:  # pragma: no cover
    class _BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def model_dump(self):
            return dict(self.__dict__)

        def model_dump_json(self, indent: int | None = None):
            import json
            return json.dumps(self.model_dump(), indent=indent, default=str)

    def _field(default=None, default_factory=None, description: str = ""):
        if default_factory is not None:
            return default_factory()
        return default

else:
    _BaseModel = pydantic.BaseModel
    _field = pydantic.Field


class Component(_BaseModel):
    """Represents a file or subdirectory component."""

    name: str = _field(description="The file name or subdirectory name.")
    description: str = _field(
        description="A brief description of the component's purpose or content."
    )


class Interface(_BaseModel):
    """Represents an interface exported by a directory."""

    name: str = _field(
        description=(
            "The name or signature of the interface, API, or conceptual abstraction."
        )
    )
    description: str = _field(
        description=(
            "A description of what the interface does, what abstraction it represents, "
            "and how it is intended to be used by consumers."
        )
    )


class Dependency(_BaseModel):
    """Represents a dependency of a directory."""

    name: str = _field(
        description='The name of the dependency, e.g. "Spanner" or "//path:target".'
    )
    usage_description: str = _field(
        description="A description of how this dependency is used by the code."
    )


class ConfigurationItem(_BaseModel):
    """Represents a configuration item, like a flag or config bundle."""

    name: str = _field(
        description="The name of the flag, configuration field, or bundle."
    )
    definition_link: str = _field(
        description="A link to where the item is defined or bundle is constructed."
    )
    description: str = _field(
        description="A description of how the item is used or configured."
    )
    comments: str = _field(
        default="",
        description="Additional comments, such as typical values or caveats.",
    )


class Section(_BaseModel, abc.ABC):
    """Base class for all sections."""

    @abc.abstractmethod
    def to_markdown(self) -> Optional[str]:
        """Renders the section to markdown, or None if the section is empty."""


class Overview(Section):
    """Conceptual overview of the directory."""

    content: str = _field(
        description="A high-level overview of the directory and what it provides."
    )

    def to_markdown(self) -> Optional[str]:
        return f"# Overview\n\n{self.content}" if self.content else None


class DeepDive(Section):
    """Deep dive into the contents of a directory."""

    content: str = _field(
        description="A detailed explanation of important behavior and structure."
    )

    def to_markdown(self) -> Optional[str]:
        return f"# Deep Dive\n\n{self.content}" if self.content else None


class KeyIndividualComponents(Section):
    """Key individual components of the directory."""

    components: List[Component] = _field(
        default_factory=list,
        description="Important files and subdirectories, with their responsibilities.",
    )

    def to_markdown(self) -> Optional[str]:
        if not self.components:
            return None
        items = "\n".join(
            [f"- **{component.name}**: {component.description}" for component in self.components]
        )
        return f"# Key Individual Components\n\n{items}"


class KeyInterfaces(Section):
    """Key interfaces exported by the directory."""

    interfaces: List[Interface] = _field(
        default_factory=list,
        description="Key classes, functions, or APIs exported by this directory.",
    )

    def to_markdown(self) -> Optional[str]:
        if not self.interfaces:
            return None
        items = "\n".join(
            [f"- **{interface.name}**: {interface.description}" for interface in self.interfaces]
        )
        return f"# Key Interfaces\n\n{items}"


class KeyDependencies(Section):
    """Key dependencies of the code in this directory."""

    dependencies: List[Dependency] = _field(
        default_factory=list,
        description="External systems, libraries, or codebase areas this code depends on.",
    )

    def to_markdown(self) -> Optional[str]:
        if not self.dependencies:
            return None
        items = "\n".join(
            [f"- **{dependency.name}**: {dependency.usage_description}" for dependency in self.dependencies]
        )
        return f"# Key Dependencies\n\n{items}"


class ArchitecturalPatternsAndGotchas(Section):
    """Key architectural patterns, design decisions, or gotchas."""

    content: str = _field(
        description="Important design decisions, order-of-operations rules, and pitfalls."
    )

    def to_markdown(self) -> Optional[str]:
        return (
            f"# Architectural Patterns and Gotchas\n\n{self.content}"
            if self.content
            else None
        )


class TestingStrategy(Section):
    """Testing strategy for the code in this directory."""

    content: str = _field(
        description="Describe the testing strategy for the code in this directory."
    )

    def to_markdown(self) -> Optional[str]:
        return f"# Testing Strategy\n\n{self.content}" if self.content else None


class Configurations(Section):
    """Configurations and flags that control behavior."""

    configurations: List[ConfigurationItem] = _field(
        default_factory=list,
        description="Important configuration items and how they are used.",
    )

    def to_markdown(self) -> Optional[str]:
        if not self.configurations:
            return None
        items = "\n".join(
            [
                f"- **{config.name}**: {config.description} "
                f"(Defined in: {config.definition_link})"
                f"{' Comments: ' + config.comments if config.comments else ''}"
                for config in self.configurations
            ]
        )
        return f"# Configuration and flags\n\n{items}"


class CustomSectionData(Section):
    """Output of a custom section requested by the user."""

    title: str = _field(description="The header title for the section.")
    content: str = _field(
        description="The generated markdown content for this section."
    )

    def to_markdown(self) -> Optional[str]:
        return f"# {self.title}\n\n{self.content}" if self.content else None


class CustomSectionsDocument(_BaseModel):
    """Output of the Custom Sections agent."""

    custom_sections: List[CustomSectionData] = _field(
        default_factory=list,
        description="Custom sections requested by the user.",
    )

    if pydantic is not None:
        @pydantic.model_validator(mode="after")
        def check_unique_titles(self):
            titles = [section.title for section in self.custom_sections]
            if len(titles) != len(set(titles)):
                raise ValueError("Custom section titles must be unique.")
            return self


class KeyComponentsDocument(_BaseModel):
    key_individual_components: KeyIndividualComponents
    key_interfaces: KeyInterfaces
    key_dependencies: KeyDependencies
    architectural_patterns_and_gotchas: ArchitecturalPatternsAndGotchas
    testing_strategy: TestingStrategy
    configurations: Configurations


class DeepDiveDocument(_BaseModel):
    """Output of the Deep Dive agent."""

    deep_dive: DeepDive


class OverviewDocument(_BaseModel):
    """Output of the Overview agent."""

    overview: Overview


class IndexDocument(_BaseModel):
    """The top-level model for the LLM indexer output."""

    overview: Overview
    key_individual_components: KeyIndividualComponents
    deep_dive: Optional[DeepDive] = None
    architectural_patterns_and_gotchas: Optional[
        ArchitecturalPatternsAndGotchas
    ] = None
    key_interfaces: Optional[KeyInterfaces] = None
    key_dependencies: Optional[KeyDependencies] = None
    configurations: Optional[Configurations] = None
    testing_strategy: Optional[TestingStrategy] = None
    custom_sections: List[CustomSectionData] = _field(default_factory=list)


def sanitize_unicode(text: str) -> str:
    """Removes control characters and replaces invalid UTF-8 characters."""
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)
    text = text.encode("utf-8", errors="replace").decode("utf-8")
    return text


def to_markdown(doc: IndexDocument) -> str:
    """Converts an IndexDocument to a Markdown string."""
    output = []
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

    for field_name in section_order:
        section = getattr(doc, field_name)
        if section and isinstance(section, Section):
            md = section.to_markdown()
            if md:
                output.append(md.strip())

    for custom_section in doc.custom_sections:
        md = custom_section.to_markdown()
        if md:
            output.append(md.strip())

    output = "\n\n".join(output)
    return sanitize_unicode(output)
