"""Prompts for Merger and Indexer Agents."""

from __future__ import annotations

import abc
from collections.abc import Sequence
import copy
import json
import textwrap
from typing import Final

import pydantic

from indexing import schema


# Local replacement for bundle_pb2.ProjectBundle.CustomSection
from dataclasses import dataclass as _dataclass


@_dataclass
class _CustomSection:
    """Stand-in for the upstream proto CustomSection."""
    title: str = ""
    prompt: str = ""


class _ProjectBundle:
    CustomSection = _CustomSection


class bundle_pb2:  # noqa: N801
    ProjectBundle = _ProjectBundle


MAX_CODE_SEARCH_QUERIES: Final[int] = 5
MAX_READ_FILE_QUERIES: Final[int] = 5

SEARCH_REFERENCE: Final[str] = textwrap.dedent("""\
Common Search Qualifiers (GitHub / Commercial Search Style)

* **Repository & Path**
  * `repo:OWNER/NAME`: Search within a specific repository.
  * `org:ORGNAME`: Search across all repositories in an organization.
  * `path:PATH/TO/DIR`: Restrict search to a specific path or directory.
  * `filename:FILENAME`: Search for a specific file by name.
  * `extension:EXT`: Filter by file extension (e.g., `extension:py`).

* **Content & Symbols**
  * `language:LANG`: Filter by programming language (e.g., `language:typescript`).
  * `symbol:NAME`: Search for symbol definitions (supported by some commercial indexers like Sourcegraph).
  * `content:QUERY`: Search for text within file contents (usually the default).
  * `NOT term`: Exclude results containing a specific term.
  * `term1 AND term2`: Find files containing both terms.
  * `term1 OR term2`: Find files containing either term.

* **Metadata & History**
  * `user:USERNAME`: Find repositories owned by a user or files modified by them.
  * `created:YYYY-MM-DD`: Filter by creation date.
  * `pushed:YYYY-MM-DD`: Filter by last push date.
  * `stars:>100`: Filter by repository popularity.
  * `fork:true|false`: Include or exclude forks.

* **Advanced Operators**
  * `"phrase"`: Search for an exact phrase.
  * `*`: Wildcard for matching parts of words.
  * `regex:PATTERN`: Some tools support PCRE or RE2 regular expressions for content or path filtering.
""")

CLOUD_CONTEXT: Final[str] = textwrap.dedent("""\
This project utilizes modern, industry-standard cloud-native infrastructure and DevOps practices.
**1. Infrastructure & Orchestration**
* **Containerization (Docker):** Standard unit of software that packages up code and all its dependencies.
* **Orchestration (Kubernetes / K8s):** The system for automating deployment, scaling, and management of containerized applications.
* **Nodes & Clusters:** A cluster consists of a set of worker machines, called nodes, that run containerized applications.
* **Pods:** The smallest deployable units of computing that you can create and manage in Kubernetes.

**2. Storage & Databases**
* **Object Storage (S3 / GCS / Azure Blob):** Scalable storage for unstructured data (images, logs, backups).
* **Managed Databases (RDS / Cloud SQL / Neon):** Fully managed relational database services (PostgreSQL, MySQL).
* **NoSQL (DynamoDB / CosmosDB / MongoDB):** Distributed, non-relational database systems for high-scale applications.
* **Distributed Locking (Redis / Etcd):** Services used for distributed coordination and state management.

**3. Development Workflow & CI/CD**
* **Version Control (GitHub / GitLab / Bitbucket):** Distributed version control systems for tracking changes in source code.
* **Pull Requests (PR) / Merge Requests (MR):** Proposals to merge code changes into a main branch, including peer review.
* **CI/CD Pipelines (GitHub Actions / Jenkins / CircleCI):** Automated workflows for building, testing, and deploying code.
* **Monorepo vs. Polyrepo:** Strategy of keeping all code in one repository versus splitting it across multiple repos.

**4. Observability & Reliability**
* **Logging (ELK / Splunk / Datadog):** Centralized systems for collecting and analyzing application logs.
* **Metrics (Prometheus / Grafana):** Monitoring systems for tracking performance and health metrics.
* **Tracing (Jaeger / OpenTelemetry):** Distributed tracing for debugging request flows across microservices.
* **Site Reliability Engineering (SRE):** The discipline that incorporates aspects of software engineering and applies them to infrastructure and operations problems.
""")



OUTPUT_GOALS: Final[str] = textwrap.dedent("""\
Create overviews of a particular codebase with this output. Engineers and agents
use these summaries. They have access to the underlying codebase.
Write the summaries with the following goals:

## Content Goals

1. **Accuracy: CRITICAL GOAL** Ensure the summaries are free of errors.
Skip unknown information rather than providing incorrect information. Consumers
can reference the code to find missing information. Consumers may not realize
incorrect information in the summary is wrong. For example, do not guess acronym
meanings. Leave unresolved acronyms alone if you do not know the answer. Do not
expand acronyms unless the provided code context explicitly states the expansion.
2. **Completeness: CRITICAL GOAL** Include or point to all information
necessary to understand the code. Treat the summaries as a “map” of the codebase.
Do not explain every detail. Provide enough information to help a user quickly
find the right place to start reading code.

3. **Usefulness: CRITICAL GOAL** Make the summaries useful. Help a skilled
engineer understand the codebase. Ensure they know where to look for more detail
in as few steps as possible.
4. **Mechanical Grounding: NEW CRITICAL GOAL** Identify the underlying technical primitives that ensure reliability (e.g., locking, atomicity, concurrency models). This prevents agents from breaking mechanical contracts.
5. **Blueprint Fidelity: NEW CRITICAL GOAL** Extract exact structural signatures (type hints, arguments) for public symbols. For class methods, use the `ClassName.methodName` naming convention to ensure uniqueness. This enables "Zero-Discovery" implementation.
6. **Targeted Detail: Important Goal** Provide an appropriate level of detail
for each directory and component. Tune the level of detail based on complexity
and importance. Write very brief explanations of purpose for trivial files and
directories. A single sentence description suffices for simple utility classes.
Write detailed summaries for more complex files and directories. Explain the why
and how of the code in those summaries. For complex components, prioritize
explaining the core logic, key data structures, and interactions over listing

all public methods.

## Style Goals

1. **Objective Voice: CRITICAL GOAL** Write summaries in a neutral, objective
voice. Make them impersonal. Do not reflect the author’s point of view. Do not
waste words praising or criticizing the code. This wastes text.
2. **Code Excerpts: Important Goal** Do not include code excerpts within the
summaries. The consuming agent will have access to the codebase. It can get code
references itself. Direct code might confuse the agent. It might make the agent
think it has already inspected the codebase directly.
""")


def _output_format(schema_cls: type[pydantic.BaseModel]) -> str:
    """Returns the schema fields text for the indexer."""
    schema_str = json.dumps(schema_cls.model_json_schema(), indent=2)
    return textwrap.dedent("""\
CRITICAL:

Provide only a summary of the directory and its contents. Follow the
schema below exactly. Do not include any other information. Do not respond
multiple times. Do not ask clarifying questions.

Output ONLY the JSON data. Do NOT include the "$defs" or "definitions"
section in your output. Only output the actual field values.

{schema_str}

Avoid these common failure modes:
- Return a single object, not a list of objects.
- Do not include markdown formatting (like ```json ... ```) around the JSON.
- Do not add explanatory text before or after the JSON.
- DO NOT INCLUDE THE SCHEMA DEFINITIONS ($defs) IN YOUR RESPONSE.
""").format(schema_str=schema_str)


class IndexerPrompt(abc.ABC):
    """Base class for the indexer prompts.

    Note that the indexer works in a sequential manner, first performing
    the code search, then reading the files, and then answering the final
    prompt.
    """
    def __init__(
        self,
        *,
        epoch: int,
        previous_epoch_str: str,
        directory_path: str,
        directory_contents: str,
        subdirectory_indexes: str,
        index_file_name: str,
        codebase_specific_context: str,
        custom_sections: Sequence[bundle_pb2.ProjectBundle.CustomSection],
        extra_context: str = "",
        repo_root: str | None = None,
    ):
        self._epoch = epoch
        self._previous_epoch_str = previous_epoch_str
        self._directory_path = directory_path
        self._directory_contents = directory_contents
        self._subdirectory_indexes = subdirectory_indexes
        self._index_file_name = index_file_name
        self._codebase_specific_context = codebase_specific_context or CLOUD_CONTEXT
        self._repo_root = repo_root
        
        self._custom_sections = custom_sections
        self._extra_context = extra_context

    @abc.abstractmethod
    def role_description(self) -> str:
        raise NotImplementedError

    def prompt_context(self) -> str:
        return textwrap.dedent("""\
Current directory:
<DIRECTORY_PATH>
{directory_path}
</DIRECTORY_PATH>

Immediate directory contents:
<DIRECTORY_CONTENTS>
{directory_contents}
</DIRECTORY_CONTENTS>

Summaries of immediate subdirectories from this epoch:
<SUBDIRECTORY_INDEXES>
{subdirectory_indexes}
</SUBDIRECTORY_INDEXES>

Previous epoch state (if any):
<PREVIOUS_EPOCH_STATE>
{previous_epoch_str}
</PREVIOUS_EPOCH_STATE>

The index file name pattern for other directories is:
<INDEX_FILE_NAME>
{index_file_name}
</INDEX_FILE_NAME>

Repository root (search here for manifests):
<REPOSITORY_ROOT>
{repo_root}
</REPOSITORY_ROOT>
""").format(
            epoch=self._epoch,
            previous_epoch_str=self._previous_epoch_str,
            directory_path=self._directory_path,
            directory_contents=self._directory_contents,
            subdirectory_indexes=self._subdirectory_indexes,
            index_file_name=self._index_file_name,
            repo_root=self._repo_root or "Unknown",
        )


    def epoch(self) -> int:
        """Returns the epoch of the prompt."""
        return self._epoch

    def custom_sections(self) -> Sequence[bundle_pb2.ProjectBundle.CustomSection]:
        """Returns the custom sections of the prompt."""
        return self._custom_sections

    def research_planner_instruction(self) -> str:
        """Returns the instruction for the research planner agent."""
        agent_role = textwrap.dedent("""\
Your Role: You act as a researcher. You plan codebase searches to document a
directory's contents. You are a senior architect who knows that the best documentation
comes from ground-truth manifests and verified usage.
""")

        ability = textwrap.dedent("""\
Code search: You cannot perform code searches directly. You generate queries
for the code search tool. You can plan at most {max_code_search_queries} queries.
The system discards any extra queries. Use this language reference for the
code search query syntax:
<SEARCH_REFERENCE>
{search_reference}
</SEARCH_REFERENCE>
""").format(
            search_reference=SEARCH_REFERENCE,
            max_code_search_queries=MAX_CODE_SEARCH_QUERIES,
        )

        task = textwrap.dedent("""\
Your task:

1. Inspect the directory contents and any subdirectory summaries.
2. Create a research plan. Decide what information you need to gather via code
search to better understand the directory's code.

### Manifest Discovery Mandate:
Look for dependency manifest files that define the project's external environment. You are indexing a subdirectory, but manifest files are often at the REPOSITORY ROOT. You MUST search the ENTIRE repository for these manifests if they are not in your current directory.

### Mechanical & Signature Mandate:
You MUST search for:
1. **Critical Primitives**: Look for `fcntl`, `flock`, `threading`, `asyncio.Lock`, `tempfile`, `os.rename` (atomic), `multiprocessing`.
2. **Structural Signatures**: Identify all public-facing functions and classes. Your research plan MUST include reading the definitions of these symbols to extract their exact signatures.
3. **Implicit Dependencies**: Search for usage of environment variables (`os.environ`, `getenv`) or external service calls that aren't in manifests.
4. **Workflow State Machines**: Look for LangGraph `StateGraph`, Temporal `Workflow`, or custom orchestration logic that dictates system behavior.

If you see signs of a specific ecosystem, search for:
- **Node/JS**: `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `deno.json`
- **Python**: `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`, `poetry.lock`
- **Go**: `go.mod`, `go.sum`
- **Rust**: `Cargo.toml`, `Cargo.lock`
- **Java/Kotlin**: `pom.xml`, `build.gradle`, `build.gradle.kts`
- **Ruby**: `Gemfile`, `Gemfile.lock`
- **C#/.NET**: `*.csproj`, `packages.config`
- **C/C++**: `CMakeLists.txt`, `Makefile`, `vcpkg.json`
- **Swift**: `Package.swift`, `Podfile`
- **Dart**: `pubspec.yaml`
- **Infrastructure**: `Dockerfile`, `docker-compose.yml`, `earthly.sh`

### Dependency Classification Rules:
- **Internal**: Any component, interface, or library that exists WITHIN this repository.
- **External**: Any third-party library, managed service (S3, Cloud SQL, etc.), or system dependency installed via a package manager.

IMPORTANT: format your output as a JSON object with a "queries" list field.
Example: {"queries": ["filename:package.json", "path:src/auth symbol:login"]}
""")

        return textwrap.dedent("""\
{codebase_context}
{prompt_context}
{role_description}
{ability}
{task}""").format(
            role_description=agent_role,
            codebase_context=self._codebase_specific_context,
            ability=ability,
            prompt_context=self.prompt_context(),
            task=task,
        )

    def read_files_planner_instruction(
        self,
        *,
        code_search_output: str,
    ) -> str:
        """Returns the instruction for the read files planner agent."""
        agent_role = textwrap.dedent("""\
Your Role: You act as a researcher. You plan file reading to document a
directory's contents. You focus on extracting dependency data from manifests
and verifying their usage in actual source code.
""")

        ability = textwrap.dedent("""\
Read files: You cannot read files directly. You generate a list of files for
the read files tool. You can plan to read at most {max_read_file_queries} files.
The system discards any extra files.
""").format(max_read_file_queries=MAX_READ_FILE_QUERIES)

        previous_context = textwrap.dedent("""\
Code search results:
<CODE_SEARCH_OUTPUT>
{code_search_output}
</CODE_SEARCH_OUTPUT>
""").format(
            code_search_output=code_search_output,
        )

        task = textwrap.dedent("""\
Your task:

Create a plan to read files to help summarize the directory.

1. Inspect the directory contents, subdirectory summaries, and code search
additional information.
2. Create a research plan. Decide what additional information you need to
gather by reading files.

### Manifest Reading Mandate:
Always prioritize reading any manifest files (e.g., `package.json`, `go.mod`, `requirements.txt`, `pyproject.toml`) found by the research agent. These are essential for identifying external dependencies and their roles.

### Usage Verification Mandate:
For every dependency found in a manifest, you MUST identify at least one file that uses it (e.g. via an `import` or `require` statement) to confirm its role and provided a high-quality `usage_description`.

Use workspace-relative paths (e.g., 'foo/bar.py'). 

IMPORTANT: format your output as a JSON object with a "files" list field.
Example: {"files": ["package.json", "src/index.ts"]}
""")

        return textwrap.dedent("""\
{codebase_context}
{prompt_context}
{previous_context}
{role_description}
{ability}
{task}""").format(
            role_description=agent_role,
            codebase_context=self._codebase_specific_context,
            ability=ability,
            prompt_context=self.prompt_context(),
            previous_context=previous_context,
            task=task,
        )

    def custom_sections_instruction(
        self,
        *,
        code_search_output: str,
        read_files_output: str,
        key_components_output: str,
        deep_dive_output: str,
    ) -> str:
        """Returns the instruction for the custom sections agent.

        Args:
          code_search_output: The output from the initial code search.
          read_files_output: The output from reading the files.
          key_components_output: The summary of key components.
          deep_dive_output: The Deep dive summary.
        """
        previous_context = textwrap.dedent("""\
Code search results:
<CODE_SEARCH_OUTPUT>
{code_search_output}
</CODE_SEARCH_OUTPUT>

Read files results:
<READ_FILES_OUTPUT>
{read_files_output}
</READ_FILES_OUTPUT>

Key components summary:
<KEY_COMPONENTS_SUMMARY>
{key_components_output}
</KEY_COMPONENTS_SUMMARY>

Deep dive summary:
<DEEP_DIVE_SUMMARY>
{deep_dive_output}
</DEEP_DIVE_SUMMARY>
""").format(
            code_search_output=code_search_output,
            read_files_output=read_files_output,
            key_components_output=key_components_output,
            deep_dive_output=deep_dive_output,
        )

        agent_role = textwrap.dedent("""\
Your Role: You are **Architect**, a senior staff-level AI agent specialized in reverse-engineering and understanding this codebase. You focus on synthesizing both general research and your targeted specialized research to produce deep, domain-specific analysis for the codebase.
""")

        task_instructions = [
            "Your task:",
            "",
            "1. Inspect the directory contents and any subdirectory summaries.",
            "2. Inspect the additional context from the previous research.",
            (
                "3. Generate the specific analysis sections requested by the user. "
                "For each section, generate a title and the full markdown content "
                "based on the provided instructions."
            ),
        
        ]

        if self._custom_sections:
            task_instructions.append(
                "4. You MUST generate the following requested sections based on the"
                " instructions:"
            )
        for section in self._custom_sections:
            task_instructions.append(
                f"*  - Title: {section.title}\n"
                f"      Instructions: {section.prompt}"
            
            )
        
        task = "\n".join(task_instructions)

        return textwrap.dedent("""\
{codebase_context}
{prompt_context}
{previous_context}
{role_description}
{output_goals}
{output_format}
{task}
""").format(
            role_description=agent_role,
            output_goals=OUTPUT_GOALS,
            output_format=_output_format(schema.CustomSectionsDocument),
            codebase_context=self._codebase_specific_context,
            task=task,
            prompt_context=self.prompt_context(),
            previous_context=previous_context,
        )

    def key_components_instruction(
        self,
        *,
        code_search_output: str,
        read_files_output: str,
    ) -> str:
        """Returns the instruction for the key components summary agent."""
        previous_context = textwrap.dedent("""\
Code search results:
<CODE_SEARCH_OUTPUT>
{code_search_output}
</CODE_SEARCH_OUTPUT>

Read files results:
<READ_FILES_OUTPUT>
{read_files_output}
</READ_FILES_OUTPUT>
""").format(
            code_search_output=code_search_output,
            read_files_output=read_files_output,
        )

        task = textwrap.dedent("""\
 Your task:
 
 1. Inspect the directory contents and any subdirectory summaries.
 2. Inspect the additional context from the previous research.
 3. Summarize the following sections for the directory: 
    - **Key Components**: Files and Subdirectories.
    - **Key Interfaces (MANDATORY if code present)**: Conceptual abstractions and public-facing APIs.
    - **Key Dependencies**: Internal vs External.
    - **Configuration and Flags**: System controls.
    - **Implementation Invariants (MANDATORY if code present)**: Mechanical primitives (locking, atomicity, concurrency, resource management) that define the system's reliability.
    - **Blueprint (MANDATORY if code present)**: Exact structural signatures (e.g., `def foo(a: int) -> str`) for all public symbols. **IMPORTANT: Use the format `ClassName.methodName` for all class methods (including `__init__`) to avoid name collisions in files with multiple classes.**
    - **Workflow Patterns**: Orchestration flows, LangGraph nodes/edges, or Temporal state machines.
 
 4. **BLUEPRINT FIDELITY MANDATE**: If the `extra_context` section contains "AST Deterministic Grounding", you MUST include every symbol listed there in your `blueprint` section. Copy signatures exactly. Do NOT omit them. This is the source of truth for coding agents.
 5. **INVARIANT MANDATE**: If the `extra_context` contains "AST Discovered Invariants", you MUST enrich these primitives with their intent and usage context in the `implementation_invariants` section.

""")
        return textwrap.dedent("""\
{codebase_context}
{prompt_context}
{previous_context}
{role_description}
{output_goals}
{output_format}
{task}
{extra_context}
""").format(
            role_description=textwrap.dedent("""\
Your Role: You are **Architect**, a senior staff-level AI agent specialized in reverse-engineering and understanding this codebase. Your mission is to build a comprehensive mental model of the code and foresee architectural consequences of changes. You follow elite engineering standards, prioritize context efficiency, and provide deep, technical insights that go beyond surface-level summaries.
"""),
            codebase_context=self._codebase_specific_context,
            output_goals=OUTPUT_GOALS,
            prompt_context=self.prompt_context(),
            previous_context=previous_context,
            output_format=_output_format(schema.KeyComponentsDocument),
            task=task,
            extra_context=self._extra_context,
        )

    def deep_dive_instruction(
        
        self,
        *,
        code_search_output: str,
        read_files_output: str,
        key_components_output: str,
    ) -> str:
        """Returns the instruction for the deep dive summary agent."""
        previous_context = textwrap.dedent("""\
Code search results:
<CODE_SEARCH_OUTPUT>
{code_search_output}
</CODE_SEARCH_OUTPUT>

Read files results:
<READ_FILES_OUTPUT>
{read_files_output}
</READ_FILES_OUTPUT>

Key components summary:

<KEY_COMPONENTS_SUMMARY>
{key_components_output}
</KEY_COMPONENTS_SUMMARY>
""").format(
            code_search_output=code_search_output,
            read_files_output=read_files_output,
            key_components_output=key_components_output,
        )

        task = textwrap.dedent("""\
Your task:

1. Inspect the directory contents and any subdirectory summaries.
2. Inspect the additional context from the previous research.
3. Inspect the key components summary.
4. Write the Deep Dive section for the directory. Focus on the core logic, motivations, and technical details.

IMPORTANT: DO NOT repeat the information found in key components summary.
IMPORTANT: format your output as a JSON object with a "deep_dive" field containing a "content" field.
Example: {"deep_dive": {"content": "Your detailed explanation here."}}
""")
        return textwrap.dedent("""\
{codebase_context}
{prompt_context}
{previous_context}
{role_description}
{output_goals}
{output_format}
{task}
{extra_context}
""").format(
            role_description=textwrap.dedent("""\
Your Role: You are **Architect**, a senior staff-level AI agent specialized in reverse-engineering and understanding this codebase. Your mission is to build a comprehensive mental model of the code and foresee architectural consequences of changes. You follow elite engineering standards, prioritize context efficiency, and provide deep, technical insights that go beyond surface-level summaries.
"""),
            codebase_context=self._codebase_specific_context,
            output_goals=OUTPUT_GOALS,
            output_format=_output_format(schema.DeepDiveDocument),
            prompt_context=self.prompt_context(),
            previous_context=previous_context,
            task=task,
            extra_context=self._extra_context,
        )

    def overview_instruction(
        self,
        *,
        code_search_output: str,
        read_files_output: str,
        key_components_output: str,
        deep_dive_output: str,
    ) -> str:
        """Returns the instruction for the final overview agent."""
        previous_context = textwrap.dedent("""\
Code search results:
<CODE_SEARCH_OUTPUT>
{code_search_output}
</CODE_SEARCH_OUTPUT>

Read files results:
<READ_FILES_OUTPUT>
{read_files_output}
</READ_FILES_OUTPUT>

Key components summary:
<KEY_COMPONENTS_SUMMARY>
{key_components_output}
</KEY_COMPONENTS_SUMMARY>

Deep dive summary:
<DEEP_DIVE_SUMMARY>
{deep_dive_output}
</DEEP_DIVE_SUMMARY>
""").format(
            code_search_output=code_search_output,
            read_files_output=read_files_output,
            key_components_output=key_components_output,
            deep_dive_output=deep_dive_output,
        )

        task = textwrap.dedent("""\
Your task:

1. Inspect the directory contents and any subdirectory summaries. Synthesize the
subdirectory information. Explain how subdirectories collectively contributes to
the current directory's overall purpose.

2. Inspect the additional context from the previous research, the key components summary, and the Deep Dive summary.
3. Provide the final response according to the output goals and format. Do not repeat the previous summaries. Focus
on synthesizing a higher-level overview.

CRITICAL MANDATE: You MUST include the `overview` section in your final output. It is a strictly required field.
IMPORTANT: keep the overview under 2 paragraphs (1000 words) and do not include any extra markdown formatting.
""")
        return textwrap.dedent("""\
{codebase_context}
{prompt_context}
{previous_context}
{role_description}
{output_goals}
{output_format}
{task}
{extra_context}
""").format(
            role_description=textwrap.dedent("""\
Your Role: You are **Architect**, a senior staff-level AI agent specialized in reverse-engineering and understanding this codebase. Your mission is to build a comprehensive mental model of the code and foresee architectural consequences of changes. You follow elite engineering standards, prioritize context efficiency, and provide deep, technical insights that go beyond surface-level summaries.
"""),
            codebase_context=self._codebase_specific_context,
            output_goals=OUTPUT_GOALS,
            output_format=_output_format(schema.OverviewDocument),
            prompt_context=self.prompt_context(),
            previous_context=previous_context,
            task=task,
            extra_context=self._extra_context,
        )

    def verifier_agent_instruction(
        self,
        *,
        artifact_json: str,
        source_context: str,
        is_merger_mode: bool = False,
    ) -> str:
        """Returns the instruction for the verifier agent."""
        agent_role = textwrap.dedent("""\
Your Role: You are **Verifier**, a specialized quality assurance agent. Your mission is to perform final QA and edge-case checks on generated artifacts.

### Adversarial Verification Mandates:
1. **Ground Truth Priority**: The source code's usage ALWAYS takes precedence over manifest files (package.json/requirements.txt).
2. **Ghost Dependencies**: Look for dependencies mentioned in manifest files that are NOT actually used in the code. Flag these as `found_in_config`.
3. **Implicit Dependencies**: Identify dependencies used in code (via imports or service calls) that are NOT declared in manifest files.
4. **Blueprint Integrity**: Ensure that the `blueprint` signatures match the source code character-for-character (including type hints). Verify that class methods use the `ClassName.methodName` naming convention.
5. **Shadow Tech Debt**: Identify naming slop, redundant aliases (multiple names for the same instance), and "Zombie APIs" (exported but never consumed). Document these in the `tech_debt` section.
6. **Mechanical Fragility**: Flag any place where a critical primitive (like a lock) is used inconsistently (e.g., used in write but not in read).

You report failures with concrete evidence.
""")

        return textwrap.dedent("""\
{role_description}
{task}
""").format(
            role_description=agent_role,
            task=create_verifier_prompt(artifact_json, source_context),
        )


class InitialIndexerPrompt(IndexerPrompt):
    """Initial indexer prompt."""

    def role_description(self) -> str:
        """Returns the role description for the architect agent."""
        return textwrap.dedent("""\
Your Role: You are **Architect**, a senior staff-level AI agent specialized in reverse-engineering and understanding this codebase. Your mission is to build a comprehensive mental model of the code and foresee architectural consequences of changes. You follow elite engineering standards, prioritize context efficiency, and provide deep, technical insights that go beyond surface-level summaries.
""")


class IndexImproverPrompt(IndexerPrompt):
    """Index improver prompt."""

    def role_description(self) -> str:
        del self  # Unused.
        return textwrap.dedent("""\
Your Role: You act as a technical writer on a team summarizing a large codebase.
Improve the summary of a particular directory. Improve the summary along one
of the dimensions from the output goals.

Cross-reference the 'existing_index' with the 'previous_root_map'. Identify
missing connections or contextual information.

Example improvements:

Make any improvements you see fit. Consider these impactful improvements:
- Correct inaccuracies. This provides the most impact. Fix any errors you spot.
- Add context about the directory's place in the larger project. Prior
iterations likely lacked this context.
- Improve tone, clarity, and flow.
- Improve usability. Engineers use the summary for context, background, and
navigating deeper information. Make the summary more scannable. Provide clearer
pointers to other interesting codebase areas.
- Make the summary concise without losing important information.
- Improve contextualization. The summary may inaccurately portray the directory's
role. It might claim this directory is the only solution, when others exist.
It might claim this directory solves a problem entirely, when it only provides
a partial solution.

Always improve! Look for opportunities to improve accuracy if you get stuck.
Find potentially wrong summary sections. Double check them against the code.
Identify and fix inaccuracies.
""")


def create_merger_prompt() -> str:
    return textwrap.dedent("""\
You act as a technical writer. Consolidate multiple partial directory summaries
into a single, coherent summary.

The system generated each partial summary from a subset of the files in the directory.
Merge them. Ensure the final output accurately reflects the combined content of all
partial summaries. Do not mention the partial summaries in the final summary.

{output_format}
""").format(output_format=_output_format(schema.IndexDocument))


VERIFIER_SYSTEM_PROMPT: Final[str] = textwrap.dedent("""\
You are an expert factual verifier for a codebase indexing system.
Your job is to read the generated artifact JSON and verify that EVERY claim made in it is explicitly supported by the source code context provided.

Rule 1: If the artifact claims a dependency, interface, or component exists, it SHOULD be visible in the source context.
Rule 2: If the artifact makes a claim about how something works, it MUST be supported by the code or comments in the source context.
Rule 3: You must NOT verify if the JSON structure is valid. Assume it is syntactically correct. Your job is ONLY semantic factual verification.
Rule 4: If you find a dependency or configuration that is documented in a README/MD file but not found in the actual source code, do NOT mark `passed` as false. Instead, mark it as an `info` severity issue with category `unsupported_claim`.
Rule 5: Distinguish between Hallucinations (things that don't exist anywhere) and Documentation Claims (things documented but not yet implemented/visible in code). Only Hallucinations should block publication.
Rule 6: If the source context was truncated, do NOT fail verification just because a claimed file is not visible. Only fail if a claim directly contradicts what IS visible.
Rule 7: Large external libraries (e.g., react, vite, tailwind) found in package.json/lock files are 'external' dependencies. Do not flag them as issues if they are listed as such.
Rule 8: The provided source context includes both the immediate directory contents and 'RESEARCH CONTEXT' gathered from across the codebase. Use both as valid grounds for verification.

Return your verdict in the requested JSON format (VerificationVerdict).
If there are unverified documentation claims, set `passed=True` but list them in `detailed_issues` with `severity='info'`.
""")


def create_verifier_prompt(artifact_json: str, source_context: str) -> str:
    # Safety cap to avoid exceeding model context limits.  Gemma 4 supports
    # ~200K tokens; 400K chars is approximately 100K tokens which fits
    # comfortably.  Only truncates truly massive directories.
    max_context_chars = 400_000
    if len(source_context) > max_context_chars:
        half = max_context_chars // 2
        truncated_context = (
            source_context[:half]
            + f"\n\n... [TRUNCATED {len(source_context) - max_context_chars:,} chars] ...\n\n"
            + source_context[-half:]
        )
    else:
        truncated_context = source_context

    return textwrap.dedent(f"""\
=== SOURCE CONTEXT ===
{truncated_context}

=== GENERATED ARTIFACT ===
{artifact_json}

Please verify the artifact against the source context and provide your structured verdict.
""")


def create_root_map_prompt(root_map_content: str) -> str:
    """Creates the senior architect prompt for root map synthesis."""
    return textwrap.dedent(f"""\
        You are a senior software architect creating a high-level "Map" of a large codebase.
        Your goal is to synthesize multiple directory overviews into a single, cohesive architectural summary of the project.
        
        ### Instructions:
        1. Identify the core purpose and architectural themes of the project.
        2. Group related directories into logical components or layers (e.g., Infrastructure, API, Core Logic, UI).
        3. Explain the data flow or interaction patterns between these components.
        4. Focus on the "Big Picture". Avoid listing every single directory; instead, explain the system's design.
        5. If the input is already a collection of summaries, further synthesize them into a higher-level abstraction.
        
        ### Input Context (Overviews/Summaries):
        {root_map_content}
        
        Write a professional, neutral, and highly useful summary for other engineers and autonomous agents.
    """)

