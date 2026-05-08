---
id: architecture
title: Architecture Overview
page_type: architecture
source_files:
- INDEX.md
- docs/walkthrough/agentic_harness_lifecycle.md
- harness/cli.py
- harness/discovery_engine.py
- harness/indexer_wrapper.py
- harness/minting_engine.py
generated_at_ref: f1af3b2fa46c98c92658d870947ac03b9020de8a
generated_at: 2026-05-08T19:40:40Z
links_to:
- topic-workflow-orchestration
- mod-agents
covers:
- 'heading:Codebase Index: e-2-g'
- heading:The Universal Agentic Harness Lifecycle
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
- description: 'Wiki stated agents use ''dual-format approach: JSON files define metadata and capabilities, while YAML files specify behavioral parameters'' but code now uses Markdown-based agent definitions'
  source: _agents/agents/*.md and boilerplate-agent/agents/*.md
  detected_at: 2026-05-08T19:40:40Z
- description: 'Wiki stated ''The system maintains two configuration hierarchies: core/ agents (universal) and discovery/ agents (project-discovery phase)'' but the hierarchical structure has been flattened'
  source: boilerplate-agent/agents/
  detected_at: 2026-05-08T19:40:40Z
- description: Wiki mentioned indexer_wrapper.py and prune_context() function but these have been removed from the codebase
  source: harness/indexer_wrapper.py
  detected_at: 2026-05-08T19:40:40Z
- description: Wiki stated 'Uses context pruning via prune_context() to fit structural data within LLM context windows' but this function no longer exists
  source: harness/discovery_engine.py
  detected_at: 2026-05-08T19:40:40Z
---

# Architecture Overview

E2G Agentic Harness employs a three-layer architecture that separates concerns between workspace bootstrapping, agent orchestration, and skill execution. The system follows a "factory pattern" where specialized components handle different phases of the agentic development lifecycle.

## Core Architecture Layers

### Bootstrap Layer (Stage 0)
The bootstrap layer (`harness/`) contains stateless utilities that analyze codebases and mint agent workspaces. This layer operates independently of any specific project and produces reproducible outputs:

- **Discovery Engine** (`harness/discovery_engine.py`): Interfaces with LLMs to analyze project structure and recommend agent configurations. Features new capabilities for Domain Driven Design (DDD) context extraction via `discover_ddd_context()` and custom agent generation through `discover_custom_agent()`. Uses lightweight context acquisition via `acquire_mcp_context()` to fit structural data within LLM context windows, replacing the previous heavy indexing approach.
- **Minting Engine** (`harness/minting_engine.py`): Templates and configures workspaces via `mint_workspace()`. Clones the boilerplate structure and injects project-specific agent configurations using MCP (Model Context Protocol). Now supports DDD context injection and model-specific configurations.

### Agent Configuration Layer
The agent configuration system has undergone a **major architectural transformation**. The previous dual-format approach (JSON + YAML files in nested directory structures) has been completely replaced with a **Markdown-based agent definition system**:

- **Project-Specific Agents** (`_agents/agents/`): Now uses standalone Markdown files (e.g., `adversary.md`, `architect.md`) instead of the previous `agent.json`/`config.yaml` pairs in subdirectories.
- **Boilerplate Template** (`boilerplate-agent/agents/`): The hierarchical `core/` and `discovery/` structure has been flattened to direct Markdown agent definitions. The template no longer maintains separate configuration hierarchies.
- **Orchestration Rules**: Centralized in `boilerplate-agent/rules/` with `core_mandates.md`, `dispatch_rules.md`, and enhanced workflow definitions including DDD mandates.

### Execution Layer (Skills + Orchestration)
Skills have been enhanced with new capabilities and remote skill fetching:

- **Remote Skills**: The discovery engine now supports `fetch_remote_skill()` for dynamic skill acquisition from external repositories.
- **Enhanced Skills**: New skills like `grill-me.md`, `grill-with-docs.md`, and `improve-codebase-architecture.md` in the boilerplate template.
- **DDD Integration**: Skills now integrate with Domain Driven Design context for more targeted architectural improvements.

## Data Flow Architecture

The system follows a streamlined data flow with significant changes to context handling:

1. **Lightweight Context Acquisition**: `harness/discovery_engine.py` now uses `acquire_mcp_context()` instead of heavy structural indexing
2. **DDD Context Discovery**: New `discover_ddd_context()` extracts domain-specific context for better agent configuration
3. **Agent Discovery**: Enhanced `discover_agents()` with DDD context integration and feature-fetcher YAML path support
4. **Workspace Minting**: `mint_workspace()` now supports model-specific configurations, DDD context injection, and flexible boilerplate directory handling

## Configuration Contract

The configuration system has been **fundamentally redesigned**:

- **Markdown-First Approach**: Agent configurations are now defined in human-readable Markdown files instead of JSON/YAML pairs
- **Simplified Structure**: Eliminated the complex nested directory hierarchies in favor of flat Markdown-based definitions
- **Enhanced Context Injection**: DDD context and model-specific parameters are injected during minting for better project alignment

## Key Design Invariants

- **Stateless Bootstrap**: All `harness/` components remain pure functions, now enhanced with DDD context capabilities
- **Template Evolution**: The `boilerplate-agent/` template has been significantly restructured but maintains immutability during minting
- **Phase Isolation**: Each orchestration phase operates independently with explicit handoff points, now enhanced with DDD-aware workflows
- **Skill Atomicity**: Individual skills remain self-contained and composable, with new remote skill capabilities

## Major Architectural Changes

**⚠️ BREAKING CHANGES ALERT**

1. **Agent Configuration Format**: Complete migration from JSON/YAML to Markdown-based definitions
2. **Directory Structure**: Flattened agent hierarchy, eliminated `core/` and `discovery/` subdirectories
3. **Context Handling**: Replaced heavy indexing with lightweight MCP context acquisition
4. **DDD Integration**: New domain-driven design context throughout the system
5. **Model Flexibility**: Enhanced support for different LLM models and configurations

This architecture continues to enable bootstrapping agent workspaces for arbitrary codebases while maintaining consistency and reproducibility, now with enhanced domain awareness and simplified configuration management. See [[topic-workflow-orchestration]] for details on phase management and [[mod-agents]] for the new agent configuration specifics.
