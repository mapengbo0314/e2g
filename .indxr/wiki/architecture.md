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
generated_at_ref: 77df166158f6da25c1fb0e84492b38d646ca42f3
generated_at: 2026-05-14T18:56:52Z
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
---

# Architecture Overview

E2G Agentic Harness employs a three-layer architecture that separates concerns between workspace bootstrapping, agent orchestration, and skill execution. The system follows a "factory pattern" where specialized components handle different phases of the agentic development lifecycle, integrated with Domain Driven Design (DDD) principles.

## Core Architecture Layers

### Bootstrap Layer (Stage 0)
The bootstrap layer (`harness/`) contains stateless utilities that analyze codebases and mint agent workspaces. This layer operates independently of any specific project and produces reproducible, project-aligned outputs:

- **Discovery Engine** (`harness/discovery_engine.py`): Interfaces with LLMs to analyze project structure and recommend agent configurations. 
    - **Tech Stack Detection**: Uses `detect_tech_stack()` to heuristically identify languages and frameworks.
    - **DDD Extraction**: Extracts Domain Driven Design context via `discover_ddd_context()`.
    - **Onboarding Profiling**: Generates `ONBOARDING_DOMAIN.md` via `generate_onboarding_domain_doc()`, creating a template for users to define domain-specific expertise and select tools.
    - **Custom Agent Generation**: Supports generating specialized agents through `discover_custom_agent()`.
    - **Lightweight Context**: Uses `acquire_mcp_context()` to fetch structural data from existing indexes (like the `indxr` MCP) to fit within LLM context windows.
- **Minting Engine** (`harness/minting_engine.py`): Templates and configures workspaces via `mint_workspace()`. 
    - **Domain SME Synthesis**: `synthesize_domain_sme_agent()` creates a deterministic Domain SME agent based on the user's completed onboarding doc.
    - **Dynamic Rule Patching**: `patch_orchestrator_rules()` injects new agents into the Orchestrator's `dispatch_rules.md`.
    - **DDD Agent Injection**: During `mint_workspace`, the engine dynamically injects routing rules for discovered DDD agents into `dispatch_rules.md` just before the negative routing section.
    - **Tool Installation**: `install_workspace_tools()` downloads remote skills and configures MCPs.
    - **Recursive Includes**: Uses `process_includes()` to resolve ` @path` directives within templates, supporting placeholder replacements.
- **CLI Orchestrator** (`harness/cli.py`): Manages the interactive flow between discovery and minting, including the `run_ddd_grill()` phase and path normalization logic to prevent nesting when running the harness inside a `.gemini` folder.

### Agent Configuration Layer
The agent configuration system uses a **Markdown-based definition system**, prioritizing human readability and ease of modification:

- **Project-Specific Agents** (`.gemini/agents/`): Standalone Markdown files (e.g., `adversary.md`, `architect.md`) contain the full system prompts and mandates for subagents.
- **Boilerplate Template** (`boilerplate-agent/agents/`): A flattened directory of agent definitions used as the source for new workspaces.
- **Orchestration Rules**: Centralized in `boilerplate-agent/rules/`. Governance is split into modular mandates to ensure granular control over agent behavior:
    - `core_mandates.md`: High-level system constraints.
    - `base_mandate.md`: General operational standards.
    - `coding_mandate.md`: Development, typing, and TDD standards.
    - `indexer_mandate.md`: MCP and indexing usage rules.
    - `dispatch_rules.md`: Governs the Hub-and-Spoke interaction and phase transitions.

### Execution Layer (Skills + Orchestration)
The execution layer supports dynamic extension and domain-aware workflows:

- **Remote Skills**: Dynamic skill acquisition from external repositories via `fetch_skill()` and `fetch_remote_skill()`.
- **Domain SME Integration**: A dedicated Domain SME subagent is minted for every workspace.
- **Publishing & Notifications**: External communication support, such as the `SlackPublisher` (`chat/publishers/slack_publisher.py`).
- **DDD-Aware Workflows**: Orchestration rules enforce a lifecycle (Brainstorming -> Planning -> TDD -> Implementation) that integrates DDD context at every gate.
- **Verification & Governance**: Includes scripts like `gatekeeper.py` (`boilerplate-agent/scripts/gatekeeper.py`) to enforce mandates during the agentic lifecycle.

## Data Flow Architecture

The system follows a streamlined data flow from raw codebase to fully functional agentic workspace:

1. **Lightweight Context Acquisition**: `acquire_mcp_context()` gathers structural data.
2. **DDD Context Discovery**: `discover_ddd_context()` identifies domain boundaries.
3. **Onboarding Generation**: The system creates a project profile (`ONBOARDING_DOMAIN.md`).
4. **User Alignment**: User fills the onboarding doc and may undergo a "grilling" session via the CLI.
5. **Workspace Minting**: `mint_workspace()` copies boilerplate and injects synthesized agents.
6. **Rule Injection**: The Minting Engine patches `dispatch_rules.md` to include both the Domain SME and any project-specific DDD agents discovered during Phase 2.

## Configuration Contract

- **Markdown-First**: All agent definitions and rules are Markdown files.
- **Flat Hierarchy**: Simplified directory structures for lower context usage.
- **Dynamic Routing**: The Orchestrator uses explicit ` @agent` mentions in dispatch rules to manage the subagent lifecycle.

## Key Design Invariants

- **Stateless Bootstrap**: `harness/` components remain pure functions.
- **Template Immutability**: The `boilerplate-agent/` directory is treated as a read-only template.
- **Verification Gates**: The architecture mandates TDD and verification phases.

## Major Architectural Changes

**⚠️ BREAKING CHANGES ALERT**

1. **Agent Format**: Full migration from JSON/YAML configurations to Markdown files in `.gemini/agents/`.
2. **Dispatch Rule Injection**: The system now dynamically modifies `dispatch_rules.md` to register discovered DDD agents during the minting process.
3. **Modular Mandates**: Governance rules have been split into domain-specific files (`base`, `coding`, `indexer`) to improve maintainability and granularity of agent constraints.
4. **Documentation Consolidation**: Removed the internal `.indxr/wiki/` directory in favor of project-root documentation (e.g., `ARCHITECTURE.md`, `INDEX.md`).
5. **Removed Legacy Files**: Removed `.gemini/orchestrator.md` and `.gemini/rules/dispatch_rules.md` from the root in favor of the `boilerplate-agent/` template structure.
6. **Indexing Decoupling**: The harness no longer includes its own indexing engine, instead consuming index data via MCP.
7. **Stacktrace Extraction**: The `extract_stacktrace.py` utility has moved to a test-focused location, with corresponding unit tests added.

# Structural Changes

## Changes as of May 14, 2026

### Added Files
- `boilerplate-agent/rules/base_mandate.md`
- `boilerplate-agent/rules/coding_mandate.md`
- `boilerplate-agent/rules/indexer_mandate.md`
- `boilerplate-agent/scripts/gatekeeper.py`

### Removed Files
- Entire `.indxr/wiki/` directory (consolidated into root docs).

## Changes as of May 10, 2026

### Added Files
- `boilerplate-agent/scripts/update_index.sh`
- `chat/publishers/slack_publisher.py`
- `chat/tests/test_slack_publisher.py`
- `tests/test_extract_stacktrace.py`

### Modified Files

#### chat/fetchers/ai_usage.py
~ `def fetch_openai_usage(api_key: Optional[str]) -> dict` (api_key is now optional)

#### harness/minting_engine.py
+ Logic in `mint_workspace` to inject DDD agents into `dispatch_rules.md`.
~ `process_includes` updated to handle ` @path` directives and placeholder replacements.

#### harness/cli.py
+ Added path normalization logic to prevent nesting when running the harness inside a `.gemini` folder.

# Project Documentation
- `ARCHITECTURE.md` — This document
- `INDEX.md` — Comprehensive Codebase Index and API Surface
- `GEMINI.md` — Agentic Harness instructions and routing rules
- `ONBOARDING_GUIDE.md` — Guide for setting up new projects with the harness
