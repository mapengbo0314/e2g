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
generated_at_ref: 77df166158f6da25c1fb0e84492b38d646ca42f3
generated_at: 2026-05-14T18:56:52Z
links_to:
- architecture
- onboardingindxr-ci-automation
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
contradictions:
- description: Wiki stated process_includes resolves @path includes, but code documentation indicates it specifically resolves @tests/test_path_normalization.py includes
  source: harness/minting_engine.py
  detected_at: 2026-05-14T18:56:52Z
---

# Core Harness Components

The core harness components form the operational backbone of the E2G system, orchestrating the discovery-to-deployment pipeline through specialized modules that handle CLI interaction, agent discovery, and workspace generation. The system has moved away from heavy indexing-based approaches toward a dynamic, onboarding-centric architecture focused on Domain-Driven Design (DDD) principles and interactive refinement.

## Command Line Interface (cli.py)

The CLI serves as the primary entry point, parsing user arguments and delegating to the appropriate subsystems. `parse_args()` returns an `argparse.Namespace` with fields for project path, output directory, and optional bundle override.

`main()` orchestrates the pipeline and includes **Path Normalization** logic to ensure consistency. If a user provides a path directly to a `.gemini` folder, the CLI automatically backtracks to the project root for discovery while maintaining the `.gemini` folder as the target for workspace minting.

The pipeline includes an interactive DDD context grilling phase via `run_ddd_grill()`, which engages users with alignment questions to better ground the generated agents in the specific needs of the project.

## Discovery Engine (discovery_engine.py)

The discovery engine focuses on lightweight context acquisition and tech-stack profiling. Key functions include:

- **`acquire_mcp_context()`** - Acquires project context from core wiki files. It supports a `detailed` mode for exhaustive reads.
- **`fetch_remote_skill()`** - Fetches a skill definition directly from a raw GitHub URL.
- **`fetch_skill()`** - Retrieves definitions from remote URLs or falls back to local storage.
- **`query_llm()`** - Dispatches standardized prompts to supported LLM providers (Gemini, OpenAI, etc.).
- **`detect_tech_stack()`** - Performs heuristic detection of the technology stack by searching up to 2 levels deep for configuration files (e.g., `package.json`, `pyproject.toml`).
- **`discover_ddd_context()`** - Extracts Domain-Driven Design context using remote skills and deterministic questions.
- **`discover_agents()`** - Recommends specialized agents based on project context and DDD insights.
- **`discover_custom_agent()`** - Generates system prompts for custom, user-defined agents based on specific names and specifications.
- **`generate_onboarding_domain_doc()`** - Generates an `ONBOARDING_DOMAIN.md` template using LLM profiling and verified tools.

## Workspace Generation (minting_engine.py)

The minting engine transforms discovered context and user-validated plans into a functional workspace.

- **`parse_tool_checklists()`** - Extracts selected skills and MCPs from the `ONBOARDING_DOMAIN.md` content for installation.
- **`mint_workspace()`** - Copies boilerplate templates and injects configurations. It features **Dynamic Dispatch Injection**, automatically injecting discovered DDD agents into the `dispatch_rules.md` of the generated workspace.
- **`process_includes()`** - Recursively resolves `@` includes at the start of lines in template files, enabling modular configuration.
- **`synthesize_domain_sme_agent()`** - Generates a specialized domain SME agent deterministically based on the content of the user-reviewed `ONBOARDING_DOMAIN.md`.
- **`patch_orchestrator_rules()`** - Injects the newly synthesized SME agent into the Orchestrator's dispatch rules.
- **`install_workspace_tools()`** - Automates workspace setup by downloading remote skills and configuring MCPs locally based on the tool checklists.

The engine uses `wait_for_user_review_and_read_domain()` to pause execution, allowing the user to approve the domain manifest before final synthesis and tool installation proceed.

## Module Interactions

The redesigned data flow emphasizes context efficiency:

1. **Tech Stack Detection** (`detect_tech_stack`) → Identifies core technologies.
2. **Context Acquisition** (`acquire_mcp_context`) → Gathers lightweight metadata.
3. **DDD Discovery** (`discover_ddd_context`) → Establishes the domain foundation.
4. **Onboarding Generation** (`generate_onboarding_domain_doc`) → Creates a reviewable domain manifest.
5. **User Review** (`wait_for_user_review_and_read_domain`) → Human-in-the-loop validation.
6. **SME Synthesis & Tooling** (`synthesize_domain_sme_agent` + `install_workspace_tools`) → Creates custom agents and installs skills/MCPs.
7. **Workspace Minting** (`mint_workspace`) → Final assembly, including **Dynamic Dispatch Rule** updates to route tasks to new DDD agents.

**Removed Components**: The `indexer_wrapper.py` and `indexing/main.py` modules, along with the associated `.indxr/wiki` documentation, have been fully eliminated. The system now relies entirely on interactive profiling and lightweight wiki acquisition rather than heavy pre-indexing.

## Significant Architectural Changes: Boilerplate Mandates
The boilerplate system now includes a set of core mandates located in `boilerplate-agent/rules/`, including `base_mandate.md`, `coding_mandate.md`, and `indexer_mandate.md`. These are enforced by a new `gatekeeper.py` script to ensure compliance across generated workspaces.

## Other Wiki Pages
- [[architecture]] — Architecture Overview
- [[onboarding/indxr-ci-automation]] — CI Automation and LLM Provider configuration.
