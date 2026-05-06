"""Local reconstruction of bundle_pb2 for ProjectBundle configuration."""

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class InputDirectory:
    directory: str = ""
    research_guidance: str = ""

@dataclass
class CustomSection:
    title: str = ""
    prompt: str = ""

@dataclass
class GitRepository:
    owner: str = ""
    name: str = ""
    repository_url: str = ""

@dataclass
class GitInput:
    @dataclass
    class Versioning:
        commit_shas: List[str] = field(default_factory=list)

    repository_input: List[GitRepository] = field(default_factory=list)
    versioning: Optional[Versioning] = None

@dataclass
class CustomOutput:
    output_directory: str = ""

@dataclass
class InterleavedOutput:
    rootmap_output_directory: str = ""

@dataclass
class Metadata:
    issue_tracker_ids: List[int] = field(default_factory=list)
    team_ids: List[int] = field(default_factory=list)
    managers: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

@dataclass
class ProjectBundle:
    bundle_name: str = ""
    input: List[InputDirectory] = field(default_factory=list)
    exclude_pattern: List[str] = field(default_factory=list)
    include_pattern: List[str] = field(default_factory=list)
    additional_extensions: List[str] = field(default_factory=list)
    git_input: GitInput = field(default_factory=GitInput)
    custom_sections: List[CustomSection] = field(default_factory=list)
    metadata: Metadata = field(default_factory=Metadata)
    custom_output: Optional[CustomOutput] = None
    interleaved_output: Optional[InterleavedOutput] = None
    indexer_config: Optional[object] = None
