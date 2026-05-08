---
id: mod-testing
title: Testing Infrastructure
page_type: module
source_files:
- tests/buglogger.md
- tests/test_cli_preflight.py
- tests/test_context_acquisition.py
- tests/test_discovery_engine.py
generated_at_ref: f1af3b2fa46c98c92658d870947ac03b9020de8a
generated_at: 2026-05-08T19:40:40Z
links_to:
- mod-harness-core
- mod-documentation
- topic-workflow-orchestration
covers:
- heading:E2G Indexing Pipeline Bug Log
- fn:test_discover_agents
- fn:test_discover_agents_with_ddd_context
- fn:test_discover_custom_agent
- fn:test_discover_ddd_context
contradictions:
- description: Wiki mentioned CLI Preflight Tests and Context Acquisition Tests but these test files were removed from the codebase
  source: tests/test_cli_preflight.py, tests/test_context_acquisition.py
  detected_at: 2026-05-08T19:40:40Z
---

# Testing Infrastructure

The testing infrastructure provides automated validation and bug tracking for the E2G harness system, focusing on critical integration points like CLI operations, context acquisition, and agent discovery.

## Test Organization

The test suite is organized around key validation areas:
- **Discovery Engine Tests** (`test_discovery_engine.py`) - Verifies LLM-based agent discovery functionality including DDD context extraction
- **Minting Engine Tests** (`test_minting_engine.py`) - Validates workspace generation and agent instantiation
- **CLI Cleanup Tests** (`test_cli_cleanup.py`) - Ensures proper cleanup of temporary resources
- **Core Mandates Tests** (`test_core_mandates_presence.py`) - Validates presence of mandatory configuration files

Each test module targets specific components from [[mod-harness-core]] and uses mocking to isolate system dependencies.

## Enhanced Discovery Engine Testing

The discovery engine tests have been significantly expanded to support new agent discovery patterns:

### DDD Context Discovery
The `test_discover_ddd_context()` validates Domain-Driven Design context extraction from project metadata:

```python
@mock.patch("harness.discovery_engine.fetch_remote_skill")
@mock.patch("harness.discovery_engine.query_llm")
def test_discover_ddd_context(mock_query_llm, mock_fetch_skill):
```

This test ensures the system can analyze project structure and extract domain concepts for contextual agent selection.

### Custom Agent Discovery
The `test_discover_custom_agent()` validates on-demand agent creation based on specific requirements:

```python
@mock.patch("harness.discovery_engine.query_llm")
def test_discover_custom_agent(mock_query_llm):
```

This supports dynamic agent generation beyond pre-defined agent types, enabling project-specific tooling.

### Enhanced Agent Discovery
The core `test_discover_agents()` now supports DDD context integration and remote skill fetching:

```python
@mock.patch("harness.discovery_engine.fetch_remote_skill")
@mock.patch("harness.discovery_engine.query_llm") 
def test_discover_agents_with_ddd_context(mock_query_llm, mock_fetch_skill):
```

## Bug Tracking System

The `buglogger.md` maintains a structured incident log for the indexing pipeline with standardized fields:
- **Description** - Observable symptoms and error conditions
- **Status** - Current resolution state with timestamps
- **Root Cause** - Technical analysis of underlying issues
- **Resolution** - Specific code changes or configuration fixes
- **Verified By** - Confirmation of fix effectiveness

All tracked bugs relate to Pydantic validation failures during document processing, indicating tight coupling between the testing system and [[mod-documentation]] schema validation.

## Test Design Patterns

### Subprocess Mocking
The testing infrastructure uses subprocess mocking to simulate external tool execution without system dependencies, isolating the harness from toolchain availability while validating JSON parsing and file system operations.

### LLM Integration Testing
Multiple test functions validate LLM integration through mocked responses, ensuring discovery engines can parse structured outputs without live API calls. The pattern extends to:
- Agent discovery with contextual information
- DDD context extraction from project metadata
- Custom agent specification processing
- Remote skill fetching validation

### Remote Resource Mocking
New tests include `@mock.patch("harness.discovery_engine.fetch_remote_skill")` to validate external skill integration without network dependencies.

## Integration Points

The test infrastructure validates critical handoff points between harness components:
- **CLI → Discovery Engine** - Validates new DDD grilling functionality and enhanced agent discovery
- **Discovery Engine → LLM Provider** - Agent configuration extraction with contextual awareness
- **Minting Engine → Workspace Generation** - Template instantiation with enhanced configuration options
- **Remote Skills → Local Integration** - External skill incorporation into agent workflows

These tests serve as integration contracts, ensuring that changes to [[mod-harness-core]] components don't break the workflow orchestration described in [[topic-workflow-orchestration]].

## Bug Pattern Analysis

The bug log reveals recurring Pydantic validation issues, particularly around document structure expectations. Common patterns include:
- Missing required fields in generated documents
- Nested dictionary structures not matching schema expectations
- Type mismatches between generated content and schema definitions

These patterns suggest that document generation logic requires tighter coupling to schema validation during development, not just at runtime.
