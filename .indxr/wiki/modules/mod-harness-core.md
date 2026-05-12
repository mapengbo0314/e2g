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
generated_at_ref: b341f91c9dedfba9ea77683443093879cad39600
generated_at: 2026-05-12T23:04:50Z
links_to: []
covers:
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

# Core Harness Components

The core harness components form the operational backbone of the E2G system, orchestrating the discovery-to-deployment pipeline through specialized modules that handle CLI interaction, agent discovery, and workspace generation. The system has evolved from a traditional indexing-based approach to a dynamic, onboarding-centric architecture focused on Domain-Driven Design (DDD) principles and interactive refinement.

## Command Line Interface (cli.py)

The CLI serves as the primary entry point, parsing user arguments and delegating to the appropriate subsystems. `parse_args()` returns an `argparse.Namespace` with fields for project path, output directory, and optional bundle override.

`main()` orchestrates the pipeline, which now includes an interactive DDD context grilling phase. `run_ddd_grill()` engages users with alignment questions to better understand project requirements and domain context. This human-in-the-loop approach ensures the generated agents are grounded in the specific needs of the project.

## Discovery Engine (discovery_engine.py)

The discovery engine focuses on lightweight context acquisition and tech-stack profiling to drive agent recommendations. Key functions include:

- **`acquire_mcp_context()`** - Acquires project context from core wiki files. It supports a `detailed` mode for exhaustive reads and allows specifying a `bundle_path` to target specific documentation sets or indices.
- **`detect_tech_stack()`** - Performs heuristic detection of the project's technology stack by searching up to 2 levels deep for configuration files (e.g., `package.json`, `pyproject.toml`).
- **`discover_ddd_context()`** - Extracts Domain-Driven Design context using remote skills and deterministic questions, establishing the architectural foundation for the workspace.
- **`discover_agents()`** - Recommends specialized agents based on the project context, feature fetcher specifications, and DDD insights.
- **`generate_onboarding_domain_doc()`** - A critical new component that generates an `ONBOARDING_DOMAIN.md` template using LLM profiling. This document serves as the bridge between discovery and minting, allowing users to verify discovered tools and domain concepts before they are baked into the workspace.

The engine integrates with remote skills through `fetch_skill()`, which retrieves definitions from remote URLs or falls back to local storage, enabling dynamic capability enhancement.

## Workspace Generation (minting_engine.py)

The minting engine transforms discovered context and user-validated plans into a functional workspace. It has been significantly expanded to handle dynamic tool installation and SME (Subject Matter Expert) synthesis.

- **`mint_workspace()`** - Copies boilerplate templates and injects configurations. It now includes logic to dynamically inject DDD agents into the `dispatch_rules.md` of the generated workspace, ensuring the Orchestrator can route tasks to them immediately.
- **`process_includes()`** - Recursively resolves `@path` includes at the start of lines in template files, applying placeholders and enabling modular, reusable configuration.
- **`synthesize_domain_sme_agent()`** - Generates a specialized domain SME agent deterministically based on the content of the user-reviewed `ONBOARDING_DOMAIN.md`.
- **`patch_orchestrator_rules()`** - Injects the newly synthesized SME agent into the Orchestrator's dispatch rules within the target workspace.
- **`install_workspace_tools()`** - Automates workspace setup by downloading remote skills and configuring MCPs locally based on the tool checklists parsed from the onboarding document.

The engine uses `wait_for_user_review_and_read_domain()` to pause execution, allowing the user to edit and approve the generated domain document before final synthesis and tool installation proceed.

## Module Interactions

The redesigned data flow emphasizes context efficiency and user-driven refinement:

1. **Tech Stack Detection** (`detect_tech_stack`) → Identifies core technologies and languages.
2. **Context Acquisition** (`acquire_mcp_context`) → Gathers lightweight project metadata and wiki content.
3. **DDD Discovery** (`discover_ddd_context`) → Establishes the domain foundation and ubiquitous language.
4. **Onboarding Generation** (`generate_onboarding_domain_doc`) → Creates a reviewable domain manifest and tool checklist.
5. **User Review** (`wait_for_user_review_and_read_domain`) → Human-in-the-loop validation of discovered tools and domain concepts.
6. **SME Synthesis & Tooling** (`synthesize_domain_sme_agent` + `install_workspace_tools`) → Creates custom domain agents and installs selected skills/MCPs.
7. **Workspace Minting** (`mint_workspace`) → Final assembly, template cloning, and configuration injection (including dynamic dispatch rule updates).

**Removed Components**: The `indexer_wrapper.py` and `indexing/main.py` modules have been eliminated, reflecting the shift away from heavy indexing toward lightweight, wiki-based context acquisition and interactive profiling. This reduces external dependencies and simplifies the operational model.
