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
generated_at_ref: 703d472a00754a21da89f8b7ca2cde038b89e5b3
generated_at: 2026-05-06T21:04:02Z
links_to:
- topic-workflow-orchestration
- mod-agents
covers:
- 'heading:Codebase Index: e-2-g'
- heading:The Universal Agentic Harness Lifecycle
- fn:parse_args
- fn:main
- fn:query_llm
- fn:prune_context
- fn:discover_agents
- fn:check_indxr_installed
- fn:acquire_context
- fn:mint_workspace
---

# Architecture Overview

E2G Agentic Harness employs a three-layer architecture that separates concerns between workspace bootstrapping, agent orchestration, and skill execution. The system follows a "factory pattern" where specialized components handle different phases of the agentic development lifecycle.

## Core Architecture Layers

### Bootstrap Layer (Stage 0)
The bootstrap layer (`harness/`) contains stateless utilities that analyze codebases and mint agent workspaces. This layer operates independently of any specific project and produces reproducible outputs:

- **Discovery Engine** (`harness/discovery_engine.py`): Interfaces with LLMs to analyze project structure and recommend agent configurations. Uses context pruning via `prune_context()` to fit structural data within LLM context windows.
- **Indexer Wrapper** (`harness/indexer_wrapper.py`): Abstracts the `indxr` binary dependency through `check_indxr_installed()` and `acquire_context()`. Provides fallback to pre-generated bundles when the indexer is unavailable.
- **Minting Engine** (`harness/minting_engine.py`): Templates and configures workspaces via `mint_workspace()`. Clones the boilerplate structure and injects project-specific agent configurations using MCP (Model Context Protocol).

### Agent Configuration Layer (`_agents/`, `boilerplate-agent/`)
This layer defines declarative agent configurations and orchestration rules. The system maintains two configuration hierarchies:

- **Project-Specific Agents** (`_agents/`): Configurations tailored for the current project, including specialized agents like `designdoc_drafter` and `architect`.
- **Boilerplate Template** (`boilerplate-agent/`): Generic agent templates that get instantiated during workspace minting. Contains both `core/` agents (universal) and `discovery/` agents (project-discovery phase).

Agent configurations use a dual-format approach: JSON files define metadata and capabilities, while YAML files specify behavioral parameters and constraints.

### Execution Layer (Skills + Orchestration)
Skills (`_agents/skills/`, `boilerplate-agent/skills/`) are executable capabilities that agents invoke. The orchestration system manages multi-agent workflows through phase-based state machines defined in `rules/phases/`.

## Data Flow Architecture

The system follows a unidirectional data flow:

1. **Index Generation**: `harness/indexer_wrapper.py` produces structural representations of codebases
2. **Agent Discovery**: `harness/discovery_engine.py` analyzes structure and recommends agent configurations  
3. **Workspace Minting**: `harness/minting_engine.py` instantiates configured workspace from templates
4. **Phase Execution**: Orchestration rules coordinate multi-agent workflows within minted workspaces

## Configuration Contract

The architecture enforces strict separation between configuration-time and runtime concerns. Agent configurations must be deterministically derivable from project structure alone, enabling reproducible workspace creation. The MCP injection pattern ensures that project-specific context propagates consistently across all agent instances.

## Key Design Invariants

- **Stateless Bootstrap**: All `harness/` components are pure functions that don't maintain state between invocations
- **Template Immutability**: The `boilerplate-agent/` template remains unchanged during minting; all customization happens via configuration injection
- **Phase Isolation**: Each orchestration phase operates independently with explicit handoff points defined in `rules/phases/`
- **Skill Atomicity**: Individual skills are self-contained and can be composed without side effects

This architecture enables the system to bootstrap agent workspaces for arbitrary codebases while maintaining consistency and reproducibility across different projects and development contexts. See [[topic-workflow-orchestration]] for details on phase management and [[mod-agents]] for agent configuration specifics.
