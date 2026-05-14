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
generated_at_ref: f1af3b2fa46c98c92658d870947ac03b9020de8a
generated_at: 2026-05-08T19:40:40Z
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
- heading:Sequential LLM Prompter Refactor Design
- heading:Tree-sitter Integration and Private Symbol Indexing Design
- heading:Deterministic Injection and Metadata Extraction Design
- 'heading:Design Document: Harness Initialization CLI (`harness init`)'
---

# Updated Wiki Page Content

This module contains technical documentation, design specifications, and implementation plans that guide the development and evolution of the E2G Agentic Harness. The documentation serves as both architectural guidance and task tracking for complex system improvements.

## Document Categories

The documentation is organized into three main categories:

**Plans** (`docs/superpowers/plans/`): Implementation plans with specific tasks, test files, and acceptance criteria. These now include:

- The AST-Grounded Enrichment Pipeline plan
- **NEW**: Active Agent Grounding Plan (2026-05-06) for dynamic agent context integration
- **NEW**: Harness Redesign Plan (2026-05-06) covering system architecture evolution
- **NEW**: LLM Integration Plan (2026-05-06) for enhanced language model capabilities
- **NEW**: Skill Enhancement Plan (2026-05-06) for expanding agent skills
- **NEW**: Harness Pointer Architecture Plan (2026-05-07) for reference management
- **NEW**: Integration Fixes Plan (2026-05-07) for cross-component compatibility
- **NEW**: Omni-Compatible Finalization and Refactor Plans (2026-05-07) for universal compatibility
- **NEW**: Token Optimization Plan (2026-05-08) for performance improvements
- **NEW**: DDD Agent Discovery Plan for domain-driven design integration

**Specifications** (`docs/superpowers/specs/`): Design documents that define system behavior, architectural decisions, and component interfaces. Key specs now cover:

- Sequential LLM Prompter refactor
- Tree-sitter integration  
- Deterministic grounding design
- Harness Init CLI design
- **NEW**: Active Agent Grounding Design (2026-05-06) for runtime agent discovery
- **NEW**: DDD Agent Factory Design (2026-05-06) for domain-driven agent creation
- **NEW**: Harness Dynamic Discovery Design (2026-05-06) for automated component discovery
- **NEW**: Omni-Compatible Refactor Design (2026-05-07) for cross-platform compatibility
- **NEW**: Token Optimization Design (2026-05-08) for efficient resource utilization

**Sphinch Mark Seeds**: Several documents include "Sphinch Mark Seeds" sections that appear to be design consensus checkpoints or readiness assertions for implementation phases.

## Key Design Patterns

The documentation reveals several critical system design patterns:

**Deterministic ID Generation**: Multiple documents emphasize collision-proof, deterministic ID generation for AST nodes and symbols (`docs/superpowers/specs/2025-05-14-deterministic-grounding-design.md`). This enables stable cross-session symbol references.

**Tree-sitter Integration**: The system integrates tree-sitter parsers for multi-language AST extraction and private symbol indexing (`docs/superpowers/specs/2024-05-24-tree-sitter-integration-design.md`). The design includes schema mapping from tree-sitter nodes to `ExportedSymbol` format.

**AST Merger Architecture**: Plans detail an AST merger component that combines parsed AST data with existing artifacts, handling source kind fallbacks and maintaining referential integrity.

**Domain-Driven Design (DDD) Integration**: **NEW** — The 2026 specifications introduce comprehensive DDD support with agent factory patterns, dynamic discovery mechanisms, and context-aware agent grounding. This represents a significant architectural evolution toward more intelligent, self-organizing agent systems.

**Active Agent Grounding**: **NEW** — The system now supports runtime agent discovery and grounding based on project context, enabling adaptive agent selection and configuration based on actual codebase characteristics.

**Token Optimization**: **NEW** — Advanced token management and optimization strategies are being implemented to improve performance and reduce resource consumption across the system.

## CLI Evolution

The Harness Init CLI represents a significant system capability expansion. The design (`docs/superpowers/specs/2026-05-06-harness-init-cli-design.md`) describes a discovery-driven workflow that:

1. Performs pre-flight checks and API key validation
2. Uses an `indxr` wrapper for context acquisition
3. Implements a discovery engine for codebase analysis
4. Provides a human-in-the-loop TUI for workspace configuration
5. Handles workspace minting and prerequisite injection

The CLI integrates with the [[mod-harness-core]] system and coordinates with [[mod-agents]] for workspace setup. **NEW**: Recent enhancements include DDD context discovery, custom agent creation capabilities, and improved model selection options.

## Verification and Testing Strategy

The documentation emphasizes test-driven development with specific test file requirements for each implementation task. The AST-Grounded Enrichment plan includes detailed test scenarios for schema updates, extractor collision-proofing, AST merger functionality, and verifier updates.

The deterministic grounding design includes explicit verification plans that test extraction consistency, injection determinism, and metadata accuracy across multiple runs.

**NEW**: The 2026 plans introduce comprehensive testing strategies for agent discovery, DDD integration, and token optimization, ensuring that new architectural patterns maintain system reliability.

## Integration Points

These documentation artifacts inform several other system components:

- **[[mod-skills]]**: Tree-sitter integration, symbol extraction capabilities, and **NEW** enhanced skill discovery and remote skill fetching
- **[[mod-harness-core]]**: CLI initialization, workspace management, and **NEW** dynamic discovery engine integration
- **[[mod-agents]]**: Agent configuration during workspace setup and **NEW** DDD-driven agent factory patterns
- **[[topic-workflow-orchestration]]**: Sequential prompter refactoring, workflow management, and **NEW** omni-compatible orchestration patterns

The documentation maintains traceability between design decisions and implementation tasks, ensuring that architectural intentions are preserved during development. **NEW**: The 2026 documentation cycle introduces significant architectural evolution with DDD principles, active grounding, and token optimization representing major system capability expansions.

## Recent Architectural Evolution (2026)

The substantial addition of 2026-dated plans and specifications indicates a major architectural evolution phase focusing on:

- **Dynamic Discovery**: Moving from static configuration to runtime discovery of agents, skills, and context
- **Domain-Driven Design**: Integrating DDD principles for more coherent agent organization and behavior
- **Universal Compatibility**: Omni-compatible refactoring for cross-platform and cross-model support
- **Performance Optimization**: Token-aware optimization strategies for improved resource efficiency
- **Active Grounding**: Real-time context-aware agent selection and configuration

This represents a significant maturation of the system from a primarily configuration-driven approach to an intelligent, adaptive platform capable of self-organization and optimization.



