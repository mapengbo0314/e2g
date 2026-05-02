"""Pydantic schemas for LLM indexer output.

This is the canonical structured artifact schema for the trust-oriented
indexing pipeline. It defines the JSON contract that all generated
artifacts must conform to. Optional fields use `None` to represent
concepts not present in the source code, preventing the LLM from
hallucinating missing information.
"""

# Standard library imports for schema validation and serialization.
from __future__ import annotations
import abc
import datetime
import json
import re
from typing import Any, Dict, List, Optional

# Conditional import for Pydantic to support restricted environments.
try:
    import pydantic
except ImportError:  # pragma: no cover
    pydantic = None


if pydantic is None:  # pragma: no cover
    # Provide a minimal fallback for environments without Pydantic.
    class _BaseModel:
        def __init__(self, **kwargs):
            # Initialize fields from keyword arguments.
            for key, value in kwargs.items():
                setattr(self, key, value)

        def model_dump(self):
            # Convert attributes to a dictionary.
            return dict(self.__dict__)

        def model_dump_json(self, indent: int | None = None):
            # Serialize model data to JSON.
            return json.dumps(self.model_dump(), indent=indent, default=str)

    def _field(default=None, default_factory=None, description: str = ""):
        # Minimal Field stand-in.
        if default_factory is not None:
            return default_factory()
        return default

    # Define a custom validator decorator stand-in.

else:
    # Use real Pydantic if available.
    _BaseModel = pydantic.BaseModel
    _field = pydantic.Field


# ---------------------------------------------------------------------------
# Component-level models
# ---------------------------------------------------------------------------

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
    # The detailed description explains the abstraction's purpose and usage patterns.
    description: str = _field(
        description=(
            "A description of what the interface does, what abstraction it represents, "
            "and how it is intended to be used by consumers."
        )
    )


# ---------------------------------------------------------------------------
# High-level relational models for tracking project architecture.
# ---------------------------------------------------------------------------


class Dependency(_BaseModel):
    """Represents a dependency of a directory."""

    name: str = _field(
        description='The name of the dependency, e.g. "Spanner" or "//path:target".'
    )
    usage_description: str = _field(
        default="",
        description="A description of how this dependency is used by the code.",
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
    # Comments are optional and provide extra context for configuration nuances.
    comments: str = _field(
        default="",
        description="Additional comments, such as typical values or caveats.",
    )


# ---------------------------------------------------------------------------
# Section models
# ---------------------------------------------------------------------------

class Section(_BaseModel, abc.ABC):
    """Base class for all sections."""


class Overview(Section):
    """Conceptual overview of the directory."""

    content: str = _field(
        description="A high-level overview of the directory and what it provides."
    )


class DeepDive(Section):
    """Deep dive into the contents of a directory."""

    content: Optional[str] = _field(
        default=None,
        description="A detailed explanation of important behavior and structure. Use null if not applicable.",
    )


class KeyIndividualComponents(Section):
    """Key individual components of the directory."""

    components: Optional[List[Component]] = _field(
        default_factory=list,
        description="Important files and subdirectories, with their responsibilities. Use null or empty list if none.",
    )


class KeyInterfaces(Section):
    """Key interfaces exported by the directory."""

    interfaces: Optional[List[Interface]] = _field(
        default_factory=list,
        description="Key classes, functions, or APIs exported by this directory. Use null or empty list if none.",
    )


class KeyDependencies(Section):
    """Key dependencies of the code in this directory."""

    dependencies: Optional[List[Dependency]] = _field(
        default_factory=list,
        description="External systems, libraries, or codebase areas this code depends on. Use null or empty list if none.",
    )


class ArchitecturalPatternsAndGotchas(Section):
    """Key architectural patterns, design decisions, or gotchas."""

    content: Optional[str] = _field(
        default=None,
        description="Important design decisions, order-of-operations rules, and pitfalls. Use null if not applicable.",
    )


class TestingStrategy(Section):
    """Testing strategy for the code in this directory."""

    content: Optional[str] = _field(
        default=None,
        description="Describe the testing strategy for the code in this directory. Use null if not applicable.",
    )


class Configurations(Section):
    """Configurations and flags that control behavior."""

    configurations: Optional[List[ConfigurationItem]] = _field(
        default_factory=list,
        description="Important configuration items and how they are used. Use null or empty list if none.",
    )


class CustomSectionData(Section):
    """Output of a custom section requested by the user."""

    title: str = _field(description="The header title for the section.")
    content: str = _field(
        description="The generated markdown content for this section."
    )


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
            # Check for duplicate titles to prevent ambiguous section rendering.
            if len(titles) != len(set(titles)):
                raise ValueError("Custom section titles must be unique.")
            # Return the validated instance if all titles are unique.
            return self


class KeyComponentsDocument(_BaseModel):
    # Aggregation of key components for the generator agent.
    key_individual_components: Optional[KeyIndividualComponents] = None
    key_interfaces: Optional[KeyInterfaces] = None
    # Aggregation of key dependencies for the generator agent.
    key_dependencies: Optional[KeyDependencies] = None
    architectural_patterns_and_gotchas: Optional[ArchitecturalPatternsAndGotchas] = None
    # Aggregation of testing and configuration for the generator agent.
    testing_strategy: Optional[TestingStrategy] = None
    configurations: Optional[Configurations] = None


class DeepDiveDocument(_BaseModel):
    """Output of the Deep Dive agent."""

    # Wrapper for the core deep dive section.
    deep_dive: DeepDive

    # Optional fields to capture 'leaky' LLM responses from weaker models.
    overview: Optional[Overview] = None
    key_individual_components: Optional[KeyIndividualComponents] = None
    key_interfaces: Optional[KeyInterfaces] = None
    key_dependencies: Optional[KeyDependencies] = None
    architectural_patterns_and_gotchas: Optional[ArchitecturalPatternsAndGotchas] = None
    testing_strategy: Optional[TestingStrategy] = None
    configurations: Optional[Configurations] = None


class OverviewDocument(_BaseModel):
    """Output of the Overview agent."""

    overview: Overview

    # Optional fields to capture 'leaky' LLM responses.
    deep_dive: Optional[DeepDive] = None
    key_individual_components: Optional[KeyIndividualComponents] = None
    key_interfaces: Optional[KeyInterfaces] = None
    key_dependencies: Optional[KeyDependencies] = None
    architectural_patterns_and_gotchas: Optional[ArchitecturalPatternsAndGotchas] = None
    testing_strategy: Optional[TestingStrategy] = None
    configurations: Optional[Configurations] = None


# ---------------------------------------------------------------------------
# Trust metadata
# ---------------------------------------------------------------------------

class GenerationMetadata(_BaseModel):
    """Metadata about how an artifact was generated."""

    # Model and epoch information.
    model_name: Optional[str] = _field(
        default=None,
        description="The model used for generation.",
    )
    epoch: int = _field(
        default=0,
        description="The epoch during which this artifact was generated.",
    )
    # Timestamps and processing details.
    generated_at: Optional[str] = _field(
        default=None,
        description="ISO timestamp of when generation completed.",
    )
    chunk_count: int = _field(
        default=1,
        description="Number of chunks used (1 = direct, >1 = chunked + merged).",
    )
    # Tracking retries for trust auditing.
    retry_count: int = _field(
        default=0,
        description="Number of verification retries before this version was accepted.",
    )


class VerificationState(_BaseModel):
    """Records the verification status of an artifact."""

    # Core verification status.
    verified: bool = _field(
        default=False,
        description="Whether this artifact has passed verification.",
    )
    verification_model: Optional[str] = _field(
        default=None,
        description="The model used for semantic verification.",
    )
    # Timing and scoring metadata.
    verified_at: Optional[str] = _field(
        default=None,
        description="ISO timestamp of when verification completed.",
    )
    confidence: float = _field(
        default=0.0,
        description="The confidence score from the verifier (0.0-1.0).",
    )
    # Detailed issue list if verification failed.
    issues: List[str] = _field(
        default_factory=list,
        description="Issues found during verification (empty if passed).",
    )
    is_empty_bypass: bool = _field(
        default=False,
        description="True if this index bypassed LLM generation because the directory was empty.",
    )


# ---------------------------------------------------------------------------
# Top-level document
# ---------------------------------------------------------------------------

class IndexDocument(_BaseModel):
    """The top-level model for the LLM indexer output.

    This is the canonical JSON artifact. Fields use Optional types so
    the LLM can return null when source code lacks the corresponding
    concept, rather than being pressured to hallucinate.
    """

    # Core content sections.
    overview: Overview
    key_individual_components: Optional[KeyIndividualComponents] = None
    deep_dive: Optional[DeepDive] = None
    # Detailed patterns and interfaces.
    architectural_patterns_and_gotchas: Optional[
        ArchitecturalPatternsAndGotchas
    ] = None
    key_interfaces: Optional[KeyInterfaces] = None
    # Dependencies and configurations.
    key_dependencies: Optional[KeyDependencies] = None
    configurations: Optional[Configurations] = None
    testing_strategy: Optional[TestingStrategy] = None
    # Extensions and metadata.
    custom_sections: List[CustomSectionData] = _field(default_factory=list)

    # Trust metadata (populated by the pipeline).
    generation_metadata: Optional[GenerationMetadata] = _field(
        default=None,
        description="Metadata about how this artifact was generated.",
    )
    # Verification audit trail.
    verification_state: Optional[VerificationState] = _field(
        default=None,
        description="The verification status of this artifact.",
    )


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def to_json(doc: IndexDocument, indent: int = 2) -> str:
    """Serializes an IndexDocument to a canonical JSON string."""
    return doc.model_dump_json(indent=indent)


def from_json(json_str: str) -> IndexDocument:
    """Deserializes an IndexDocument from a JSON string."""
    data = json.loads(json_str)
    if pydantic is not None:
        # Use Pydantic's strict validation if available.
        return IndexDocument.model_validate(data)
    # Fallback to direct instantiation in restricted environments.
    return IndexDocument(**data)
