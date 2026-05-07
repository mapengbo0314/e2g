---
id: mod-harness-core
title: Core Harness Components
page_type: module
source_files:
- harness/cli.py
- harness/discovery_engine.py
- harness/indexer_wrapper.py
- harness/indexing/main.py
- harness/minting_engine.py
generated_at_ref: 703d472a00754a21da89f8b7ca2cde038b89e5b3
generated_at: 2026-05-06T21:04:02Z
links_to: []
covers:
- fn:parse_args
- fn:main
- fn:query_llm
- fn:prune_context
- fn:discover_agents
- fn:check_indxr_installed
- fn:acquire_context
- fn:run_reindex
- fn:mint_workspace
---

The core harness components form the operational backbone of the E2G system, orchestrating the discovery-to-deployment pipeline through five specialized modules that handle CLI interaction, codebase analysis, agent discovery, workspace generation, and indexing operations.

## Command Line Interface (cli.py)

The CLI serves as the primary entry point, parsing user arguments and delegating to the appropriate subsystems. `parse_args()` returns an `argparse.Namespace` with fields for project path, output directory, and optional bundle override. The design assumes users will provide either a local project path or a pre-generated indxr bundle, with the CLI validating indxr availability before proceeding.

`main()` orchestrates the full pipeline: acquire context → discover agents → mint workspace. It terminates early if indxr is unavailable, ensuring the indexing dependency is satisfied before expensive operations.

## Discovery Engine (discovery_engine.py)

The discovery engine bridges codebase analysis with LLM-based agent recommendations. `prune_context(index_data: dict) -> dict` strips implementation details from the full indxr output, retaining only structural information (file declarations, imports, relationships) to minimize context window usage while preserving architectural insights.

`discover_agents()` sends the pruned context to the LLM with a prompt requesting agent recommendations. The LLM returns a JSON array of agent specifications, each containing fields expected by the minting engine. The `query_llm()` function is currently stubbed but designed to accept provider-agnostic parameters (llm_provider, api_key).

**Key invariant**: The pruned context must retain enough structural information for meaningful agent discovery while staying within typical LLM context limits (~8K tokens).

## Indexing Integration (indexer_wrapper.py)

This module encapsulates the dependency on the external `indxr` tool, providing fallback mechanisms and error handling. `check_indxr_installed()` uses `shutil.which()` to verify indxr availability, enabling graceful degradation when the tool is missing.

`acquire_context()` implements a two-path strategy: if `bundle_override` is provided, it returns that directly; otherwise, it spawns `indxr` as a subprocess to generate fresh index data. The subprocess execution captures both stdout (index JSON) and stderr (diagnostic output), with timeout handling to prevent hanging on large codebases.

**Design decision**: The wrapper maintains separation between harness logic and indxr implementation details, enabling future migration to alternative indexing tools.

## Workspace Generation (minting_engine.py)

The minting engine materializes discovered agents into executable workspace configurations. `mint_workspace()` performs three critical operations:

1. **Template cloning**: Copies the boilerplate agent structure from `agents/boilerplate-agent/` to the target directory
2. **Configuration injection**: Writes agent-specific configs, including MCP (Model Context Protocol) server definitions and skill mappings
3. **Platform setup**: Generates platform-specific setup files (package.json for Node.js, requirements.txt for Python)

The engine writes a `agents.json` manifest containing the selected agent configurations, enabling downstream tools to understand the workspace structure. Each agent config includes fields for name, description, skills, and platform requirements.

**Key invariant**: The generated workspace must be immediately executable without additional configuration, assuming the target platform runtime is available.

## Indexing Orchestration (indexing/main.py)

The internal indexing module provides an alternative to external indxr dependency through `run_reindex()`. This function coordinates several specialized components:

- **State management**: Tracks indexing progress and handles incremental updates
- **Work unit planning**: Breaks large codebases into manageable chunks
- **LLM integration**: Uses `UniversalLlmPrompter` for provider-agnostic LLM access
- **File system abstraction**: `RealFsManager` provides testable FS operations

The orchestrator implements a work-stealing scheduler that distributes indexing tasks across available resources, with the `planner` module determining optimal work unit boundaries based on file dependencies and size heuristics.

## Module Interactions

The core components follow a strict data flow: CLI → indexer_wrapper → discovery_engine → minting_engine. Each stage transforms the data format:

1. **Raw project** → **Index JSON** (indxr/indexing)
2. **Index JSON** → **Pruned context** (discovery_engine)
3. **Pruned context** → **Agent recommendations** (LLM via discovery_engine)
4. **Agent recommendations** → **Executable workspace** (minting_engine)

Error handling propagates upward, with each module returning structured error responses rather than raising exceptions. This enables the CLI to provide actionable error messages and continue partial operations where possible.

The architecture separates concerns cleanly: indexing focuses on code analysis, discovery handles AI reasoning, and minting manages workspace materialization. This separation enables independent testing and future enhancement of each subsystem.
