---
id: mod-testing
title: Testing Infrastructure
page_type: module
source_files:
- tests/buglogger.md
- tests/test_cli_preflight.py
- tests/test_context_acquisition.py
- tests/test_discovery_engine.py
generated_at_ref: 703d472a00754a21da89f8b7ca2cde038b89e5b3
generated_at: 2026-05-06T21:04:02Z
links_to:
- mod-harness-core
- mod-documentation
- topic-workflow-orchestration
covers:
- heading:E2G Indexing Pipeline Bug Log
- fn:test_check_indxr_installed_fails_when_missing
- fn:test_check_indxr_installed_passes_when_present
- fn:test_acquire_context_generates_metadata
- fn:test_discover_agents
---

The testing infrastructure provides automated validation and bug tracking for the E2G harness system, focusing on critical integration points like CLI operations, context acquisition, and agent discovery.

## Test Organization

The test suite is organized around three core validation areas:
- **CLI Preflight Tests** (`test_cli_preflight.py`) - Validates tool availability before execution
- **Context Acquisition Tests** (`test_context_acquisition.py`) - Ensures proper metadata generation and subprocess interaction  
- **Discovery Engine Tests** (`test_discovery_engine.py`) - Verifies LLM-based agent discovery functionality

Each test module targets a specific component from [[mod-harness-core]] and uses mocking to isolate system dependencies.

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
The `test_acquire_context_generates_metadata()` function uses `@mock.patch("subprocess.run")` to simulate the `indxr` tool execution without system dependencies:

```python
def test_acquire_context_generates_metadata(mock_run, tmp_path):
    mock_run.return_value.stdout = json.dumps({...})
    metadata = acquire_context(str(tmp_path))
```

This pattern isolates the harness from external toolchain availability while validating JSON parsing and file system operations.

### LLM Integration Testing
The `test_discover_agents()` validates agent discovery through mocked LLM responses, ensuring the discovery engine can parse structured outputs without live API calls:

```python
@mock.patch("harness.discovery_engine.query_llm")
def test_discover_agents(mock_query_llm):
```

## Integration Points

The test infrastructure validates critical handoff points between harness components:
- **CLI → Indexer Wrapper** - Tool availability checks prevent runtime failures
- **Indexer Wrapper → Context System** - Metadata generation and JSON parsing
- **Discovery Engine → LLM Provider** - Agent configuration extraction from natural language

These tests serve as integration contracts, ensuring that changes to [[mod-harness-core]] components don't break the workflow orchestration described in [[topic-workflow-orchestration]].

## Bug Pattern Analysis

The bug log reveals recurring Pydantic validation issues, particularly around document structure expectations. Common patterns include:
- Missing required fields in generated documents
- Nested dictionary structures not matching schema expectations
- Type mismatches between generated content and schema definitions

These patterns suggest that document generation logic requires tighter coupling to schema validation during development, not just at runtime.
