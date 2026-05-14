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
generated_at_ref: b341f91c9dedfba9ea77683443093879cad39600
generated_at: 2026-05-12T23:04:50Z
links_to: []
covers:
- 'heading:Codebase Index: e-2-g'
- heading:The Universal Agentic Harness Lifecycle
- fn:parse_args
- fn:run_ddd_grill
- fn:main
- fn:acquire_mcp_context
- fn:fetch_remote_skill
- fn:fetch_skill
- fn:query_llm
- fn:discover_agents
- fn:discover_ddd_context
- fn:discover_custom_agent
- fn:detect_tech_stack
- fn:generate_onboarding_domain_doc
- fn:parse_tool_checklists
- fn:wait_for_user_review_and_read_domain
- fn:process_includes
- fn:mint_workspace
- fn:synthesize_domain_sme_agent
- fn:patch_orchestrator_rules
- fn:install_workspace_tools
contradictions:
- description: Wiki stated Project-Specific Agents are in _agents/agents/ but code and current structure use .gemini/agents/
  source: .gemini/orchestrator.md
  detected_at: 2026-05-12T23:04:50Z
---

# Architecture Overview

E2G Agentic Harness employs a three-layer architecture that separates concerns between workspace bootstrapping, agent orchestration, and skill execution. The system follows a "factory pattern" where specialized components handle different phases of the agentic development lifecycle, now heavily integrated with Domain Driven Design (DDD) principles.

## Core Architecture Layers

### Bootstrap Layer (Stage 0)
The bootstrap layer (`harness/`) contains stateless utilities that analyze codebases and mint agent workspaces. This layer operates independently of any specific project and produces reproducible, project-aligned outputs:

- **Discovery Engine** (`harness/discovery_engine.py`): Interfaces with LLMs to analyze project structure and recommend agent configurations. 
    - **Tech Stack Detection**: Uses `detect_tech_stack()` to heuristically identify languages and frameworks.
    - **DDD Extraction**: Extracts Domain Driven Design context via `discover_ddd_context()`.
    - **Onboarding Profiling**: Generates `ONBOARDING_DOMAIN.md` via `generate_onboarding_domain_doc()`, creating a template for users to define domain-specific expertise and select tools.
    - **Custom Agent Generation**: Supports generating specialized agents through `discover_custom_agent()`.
    - **Lightweight Context**: Replaced internal heavy indexing with `acquire_mcp_context()`, which fetches structural data from existing indexes (like the `indxr` MCP) to fit within LLM context windows.
- **Minting Engine** (`harness/minting_engine.py`): Templates and configures workspaces via `mint_workspace()`. 
    - **Domain SME Synthesis**: `synthesize_domain_sme_agent()` creates a deterministic Domain SME agent based on the user's completed onboarding doc.
    - **Dynamic Rule Patching**: `patch_orchestrator_rules()` injects new agents into the Orchestrator's `dispatch_rules.md` to enable the Hub-and-Spoke routing model.
    - **Tool Installation**: `install_workspace_tools()` dynamically downloads remote skills and configures MCPs for the target workspace.
    - **Recursive Includes**: Uses `process_includes()` to resolve `@path` directives within templates.
- **CLI Orchestrator** (`harness/cli.py`): Manages the interactive flow between discovery and minting, including the `run_ddd_grill()` phase to align the harness with user architectural goals.

### Agent Configuration Layer
The agent configuration system uses a **Markdown-based definition system**, prioritizing human readability and ease of modification:

- **Project-Specific Agents** (`.gemini/agents/`): Standalone Markdown files (e.g., `adversary.md`, `architect.md`) contain the full system prompts and mandates for subagents.
- **Boilerplate Template** (`boilerplate-agent/agents/`): A flattened directory of agent definitions that no longer relies on complex nested hierarchies.
- **Orchestration Rules**: Centralized in `boilerplate-agent/rules/`, defining the `core_mandates.md` and the `dispatch_rules.md` that govern the Hub-and-Spoke interaction.

### Execution Layer (Skills + Orchestration)
The execution layer has been enhanced to support dynamic extension and domain-aware workflows:

- **Remote Skills**: The system supports dynamic skill acquisition from external repositories via `fetch_skill()` and `fetch_remote_skill()`.
- **Domain SME Integration**: A dedicated Domain SME subagent is minted for every workspace, acting as the primary source of truth for project-specific business logic.
- **DDD-Aware Workflows**: Orchestration rules enforce a lifecycle (Brainstorming -> Planning -> TDD -> Implementation) that integrates DDD context at every gate.

## Data Flow Architecture

The system follows a streamlined data flow from raw codebase to fully functional agentic workspace:

1. **Lightweight Context Acquisition**: `acquire_mcp_context()` gathers structural data without heavy local re-indexing.
2. **DDD Context Discovery**: `discover_ddd_context()` identifies domain boundaries and ubiquitous language.
3. **Onboarding Generation**: The system creates a project profile (`ONBOARDING_DOMAIN.md`) for user review.
4. **User Alignment**: The user fills the onboarding doc and may undergo a "grilling" session via the CLI for deeper alignment.
5. **Workspace Minting**: `mint_workspace()` copies the boilerplate and injects the synthesized Domain SME and project-specific agents.
6. **Rule Injection**: The Minting Engine patches `dispatch_rules.md` to ensure the Orchestrator can route tasks to newly created domain agents.

## Configuration Contract

- **Markdown-First**: All agent definitions and rules are Markdown files.
- **Flat Hierarchy**: Simplified directory structures for easier navigation and lower context usage.
- **Dynamic Routing**: The Orchestrator uses explicit `@agent` mentions in dispatch rules to manage the subagent lifecycle.

## Key Design Invariants

- **Stateless Bootstrap**: `harness/` components remain pure functions that do not maintain state between runs.
- **Template Immutability**: The `boilerplate-agent/` directory is treated as a read-only template during the minting process.
- **Verification Gates**: The architecture mandates TDD and verification phases, enforced by the minted subagent prompts.

## Major Architectural Changes

**⚠️ BREAKING CHANGES ALERT**

1. **Agent Format**: Full migration from JSON/YAML configurations to Markdown files in `.gemini/agents/`.
2. **Onboarding Flow**: Introduction of the mandatory `ONBOARDING_DOMAIN.md` phase for tool selection and SME profiling.
3. **Dynamic Routing**: The Minting Engine now actively modifies `dispatch_rules.md` to inject project-specific agents.
4. **Indexing Decoupling**: The harness no longer includes its own indexing engine, instead consuming index data via MCP or `acquire_mcp_context()`.
5. **Flattened Structure**: Removal of `core/` and `discovery/` subdirectories in the agent configuration hierarchy.

