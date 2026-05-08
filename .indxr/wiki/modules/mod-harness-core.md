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
generated_at_ref: f1af3b2fa46c98c92658d870947ac03b9020de8a
generated_at: 2026-05-08T19:40:40Z
links_to: []
covers:
- fn:parse_args
- fn:run_ddd_grill
- fn:main
- fn:acquire_mcp_context
- fn:fetch_remote_skill
- fn:query_llm
- fn:discover_agents
- fn:discover_ddd_context
- fn:discover_custom_agent
- fn:mint_workspace
contradictions:
- description: Wiki stated the system requires indxr indexing tool but code has removed indexer_wrapper.py and indexing components
  source: harness/indexer_wrapper.py
  detected_at: 2026-05-08T19:40:40Z
---

# Core Harness Components

The core harness components form the operational backbone of the E2G system, orchestrating the discovery-to-deployment pipeline through specialized modules that handle CLI interaction, agent discovery, and workspace generation. The system has evolved from a traditional indexing-based approach to a more lightweight, context-aware architecture focused on Domain-Driven Design (DDD) principles.

## Command Line Interface (cli.py)

The CLI serves as the primary entry point, parsing user arguments and delegating to the appropriate subsystems. `parse_args()` returns an `argparse.Namespace` with fields for project path, output directory, and optional bundle override. The system now emphasizes DDD-driven agent discovery over traditional code indexing.

`main()` orchestrates the pipeline with optional DDD context grilling, where `run_ddd_grill()` interactively engages users with alignment questions to better understand project requirements and domain context. This human-in-the-loop approach replaces the previous automatic indexing dependency, making the system more accessible and context-aware.

## Discovery Engine (discovery_engine.py)

The discovery engine has been redesigned around lightweight context acquisition and DDD principles. Key functions include:

- **`acquire_mcp_context()`** - Provides lightweight project context from core wiki files, avoiding the token explosion issues of full codebase indexing
- **`discover_ddd_context()`** - Extracts Domain-Driven Design context using remote skills, establishing the architectural foundation for agent recommendations
- **`discover_agents()`** - Now accepts a context string and feature fetcher YAML path rather than full index data, with optional DDD context for enhanced recommendations
- **`discover_custom_agent()`** - Generates custom user-defined agents based on specifications and project context

The engine integrates with remote skills through `fetch_remote_skill()`, enabling dynamic capability enhancement. The `query_llm()` function now supports model selection, providing flexibility across different LLM providers and capabilities.

**Key architectural shift**: The system moved from heavy indexing to lightweight, wiki-based context acquisition, reducing complexity while improving usability.

## Workspace Generation (minting_engine.py)

The minting engine has been enhanced to support the new DDD-aware architecture. `mint_workspace()` now accepts additional parameters including model choice, bundle override, custom boilerplate directory, and DDD context. This enables more flexible workspace generation that can incorporate domain-specific insights into the agent configuration.

The engine continues to perform its core operations:
1. **Template cloning** from configurable boilerplate directories
2. **Configuration injection** with DDD context integration
3. **Platform setup** with model-aware configurations

The generated workspace maintains immediate executability while incorporating the richer context provided by the DDD discovery process.

## Module Interactions

The redesigned data flow emphasizes context efficiency and user interaction: CLI → lightweight context acquisition → DDD discovery → agent recommendations → workspace generation. Each stage has been optimized:

1. **Raw project** → **Lightweight context** (acquire_mcp_context)
2. **Project context** → **DDD context** (discover_ddd_context) 
3. **DDD context + User input** → **Agent recommendations** (discover_agents)
4. **Agent recommendations** → **Executable workspace** (minting_engine)

The architecture maintains clean separation of concerns while adding DDD-driven intelligence and user interaction capabilities. Error handling continues to propagate upward with structured responses, enabling graceful degradation and informative user feedback.

**Removed Components**: The indexer_wrapper.py and indexing/main.py modules have been eliminated, reflecting the shift away from heavy indexing toward lightweight, wiki-based context acquisition. This reduces external dependencies and simplifies the operational model.
