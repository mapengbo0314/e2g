---
id: mod-documentation
title: Technical Documentation and Specifications
page_type: module
source_files:
- docs/superpowers/plans/2023-10-25-ast-grounded-enrichment.md
- docs/superpowers/plans/2026-05-06-harness-init-cli-plan.md
- docs/superpowers/specs/2024-05-20-sequential-prompter-refactor-design.md
- docs/superpowers/specs/2024-05-24-tree-sitter-integration-design.md
- docs/superpowers/specs/2025-05-14-deterministic-grounding-design.md
- docs/superpowers/specs/2026-05-06-harness-init-cli-design.md
generated_at_ref: 703d472a00754a21da89f8b7ca2cde038b89e5b3
generated_at: 2026-05-06T21:04:02Z
links_to:
- mod-harness-core
- mod-agents
- mod-skills
- topic-workflow-orchestration
covers:
- heading:AST-Grounded Enrichment Pipeline Implementation Plan
- heading:tests/test_schema.py
- heading:tests/test_ast_extractor.py
- heading:tests/test_ast_merger.py
- heading:Harness Init CLI Implementation Plan
- heading:... after api key check ...
- heading:... after context acquisition ...
- heading:... after discovery ...
- heading:1. Platform Specific Extension/Skill Installation
- heading:2. Install indxr MCP Server
- heading:... after HITL selection ...
- heading:Sequential LLM Prompter Refactor Design
- heading:Tree-sitter Integration and Private Symbol Indexing Design
- heading:Deterministic Injection and Metadata Extraction Design
- 'heading:Design Document: Harness Initialization CLI (`harness init`)'
---

This module contains technical documentation, design specifications, and implementation plans that guide the development and evolution of the E2G Agentic Harness. The documentation serves as both architectural guidance and task tracking for complex system improvements.

## Document Categories

The documentation is organized into three main categories:

**Plans** (`docs/superpowers/plans/`): Implementation plans with specific tasks, test files, and acceptance criteria. These include the AST-Grounded Enrichment Pipeline plan and the Harness Init CLI Implementation plan.

**Specifications** (`docs/superpowers/specs/`): Design documents that define system behavior, architectural decisions, and component interfaces. Key specs cover the Sequential LLM Prompter refactor, Tree-sitter integration, deterministic grounding design, and the Harness Init CLI design.

**Sphinch Mark Seeds**: Several documents include "Sphinch Mark Seeds" sections that appear to be design consensus checkpoints or readiness assertions for implementation phases.

## Key Design Patterns

The documentation reveals several critical system design patterns:

**Deterministic ID Generation**: Multiple documents emphasize collision-proof, deterministic ID generation for AST nodes and symbols (`docs/superpowers/specs/2025-05-14-deterministic-grounding-design.md`). This enables stable cross-session symbol references.

**Tree-sitter Integration**: The system integrates tree-sitter parsers for multi-language AST extraction and private symbol indexing (`docs/superpowers/specs/2024-05-24-tree-sitter-integration-design.md`). The design includes schema mapping from tree-sitter nodes to `ExportedSymbol` format.

**AST Merger Architecture**: Plans detail an AST merger component that combines parsed AST data with existing artifacts, handling source kind fallbacks and maintaining referential integrity.

## CLI Evolution

The Harness Init CLI represents a significant system capability expansion. The design (`docs/superpowers/specs/2026-05-06-harness-init-cli-design.md`) describes a discovery-driven workflow that:

1. Performs pre-flight checks and API key validation
2. Uses an `indxr` wrapper for context acquisition
3. Implements a discovery engine for codebase analysis
4. Provides a human-in-the-loop TUI for workspace configuration
5. Handles workspace minting and prerequisite injection

The CLI integrates with the [[mod-harness-core]] system and likely coordinates with [[mod-agents]] for workspace setup.

## Verification and Testing Strategy

The documentation emphasizes test-driven development with specific test file requirements for each implementation task. The AST-Grounded Enrichment plan includes detailed test scenarios for schema updates, extractor collision-proofing, AST merger functionality, and verifier updates.

The deterministic grounding design includes explicit verification plans that test extraction consistency, injection determinism, and metadata accuracy across multiple runs.

## Integration Points

These documentation artifacts inform several other system components:

- **[[mod-skills]]**: Tree-sitter integration and symbol extraction capabilities
- **[[mod-harness-core]]**: CLI initialization and workspace management
- **[[mod-agents]]**: Agent configuration during workspace setup
- **[[topic-workflow-orchestration]]**: Sequential prompter refactoring and workflow management

The documentation maintains traceability between design decisions and implementation tasks, ensuring that architectural intentions are preserved during development.
