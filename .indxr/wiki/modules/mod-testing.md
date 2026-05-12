---
id: mod-testing
title: Testing Infrastructure
page_type: module
source_files:
- tests/buglogger.md
- tests/test_cli_preflight.py
- tests/test_context_acquisition.py
- tests/test_discovery_engine.py
generated_at_ref: b341f91c9dedfba9ea77683443093879cad39600
generated_at: 2026-05-12T23:04:50Z
links_to:
- mod-harness-core
- mod-documentation
- architecture
covers:
- heading:E2G Indexing Pipeline Bug Log
- fn:test_discover_agents
- fn:test_discover_agents_with_ddd_context
- fn:test_discover_custom_agent
- fn:test_discover_ddd_context
- fn:test_acquire_mcp_context_with_bundle
- fn:test_acquire_mcp_context_no_wiki
- fn:test_acquire_mcp_context_bundle_indxr_path
- fn:test_generate_onboarding_domain_doc
- fn:test_generate_onboarding_domain_doc_with_tools
- fn:test_generate_onboarding_domain_doc_forced_injection
contradictions:
- description: Wiki stated CLI Cleanup Tests (test_cli_cleanup.py) ensures proper cleanup, but the file has been removed and cleanup logic has been refactored or deleted.
  source: tests/test_cli_cleanup.py
  detected_at: 2026-05-12T23:04:50Z
---

# Testing Infrastructure

The testing infrastructure provides automated validation and bug tracking for the E2G harness system, focusing on critical integration points like CLI operations, context acquisition, and agent discovery.

## Test Organization

The test suite is organized around key validation areas and lifecycle phases:
- **Discovery Engine Tests** (`test_discovery_engine.py`) - Verifies LLM-based agent discovery, DDD context extraction, and MCP context acquisition.
- **Minting Engine Tests** (`test_minting_engine.py`) - Validates workspace generation, remote tool installation, and SME agent synthesis.
- **CLI and E2E Validation** (`test_cli.py`, `test_e2e_flow.py`) - Ensures the command-line interface handles operations and edge cases across the full system lifecycle.
- **Platform & Config Validation** (`test_platform_awareness.py`, `test_mcp_config.py`) - Validates behavior across different operating systems and MCP configurations.
- **Core Mandates Tests** (`test_core_mandates_presence.py`) - Validates presence and integrity of mandatory configuration files.

Each test module targets specific components from [[mod-harness-core]] and uses extensive mocking to isolate system dependencies.

## Enhanced Discovery Engine Testing

The discovery engine tests have been expanded to support broader context acquisition and procedural documentation:

### DDD Context Discovery
The `test_discover_ddd_context()` validates Domain-Driven Design context extraction from project metadata, ensuring the system can analyze project structure and extract domain concepts for contextual agent selection.

### MCP Context Acquisition
New tests validate the ability to acquire structural context via the `indxr` MCP server:
- `test_acquire_mcp_context_with_bundle()` ensures context can be retrieved using pre-indexed bundles.
- `test_acquire_mcp_context_no_wiki()` verifies fallback behavior when repository documentation is missing.

### Custom Agent Discovery
The `test_discover_custom_agent()` validates on-demand agent creation based on specific requirements, supporting dynamic agent generation beyond pre-defined types.

### Procedural Onboarding
`test_generate_onboarding_domain_doc()` ensures that the system correctly generates `ONBOARDING_DOMAIN.md` files, including tool checklists and domain-specific guidance.

## Minting and Workspace Synthesis Testing

The `minting_engine.py` tests now cover the complex setup process for new agentic workspaces:

### Workspace Tool Installation
`test_install_workspace_tools()` verifies that the harness correctly fetches remote skills and injects MCP configurations into the generated workspace.

### Dynamic Rules Injection
`test_patch_orchestrator_rules()` validates that the system dynamically updates `dispatch_rules.md` to include newly discovered DDD agents, ensuring the Orchestrator can route tasks to them immediately.

### SME Agent Synthesis
`test_synthesize_domain_sme_agent()` validates the creation of specialized Subject Matter Expert agents based on the project's discovered domain content.

## Bug Tracking System

The `buglogger.md` maintains a structured incident log for the indexing pipeline with standardized fields:
- **Description** - Observable symptoms and error conditions
- **Status** - Current resolution state with timestamps
- **Root Cause** - Technical analysis of underlying issues
- **Resolution** - Specific code changes or configuration fixes
- **Verified By** - Confirmation of fix effectiveness

All tracked bugs relate to Pydantic validation failures during document processing (e.g., `verify_artifact`, `OverviewDocument`), indicating tight coupling between the testing system and [[mod-documentation]] schema validation.

## Test Design Patterns

### Subprocess Mocking
The testing infrastructure uses subprocess mocking to simulate external tool execution and CLI calls. This isolates the harness from toolchain availability while validating JSON parsing and file system operations.

### LLM Integration Testing
Multiple test functions validate LLM integration through mocked responses, ensuring discovery engines can parse structured outputs without live API calls. This extends to agent discovery, DDD extraction, and custom agent specification.

### Remote Resource Mocking
Tests utilize `mock.patch("urllib.request.urlopen")` and `mock.patch("harness.discovery_engine.fetch_remote_skill")` to validate the fetching of external skills and tools without network dependencies.

## Integration Points

The test infrastructure validates critical handoff points between harness components:
- **CLI → Discovery Engine** - Validates DDD discovery and enhanced context acquisition (including MCP).
- **Discovery Engine → MCP Server** - Extraction of structural metadata from indexed codebases.
- **Minting Engine → Workspace Generation** - Template instantiation with tool installation and rules injection.
- **Remote Skills → Local Integration** - Incorporation of external skills into agent workflows.

These tests serve as integration contracts, ensuring that changes to [[mod-harness-core]] components don't break the lifecycle phases described in [[architecture]].
