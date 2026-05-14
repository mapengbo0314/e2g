---
id: topic-workflow-orchestration
title: Workflow Orchestration and Phase Management
page_type: topic
source_files:
- _agents/rules/orchestrator.md
- _agents/rules/phases/phase_1_design_discussion.md
- _agents/rules/phases/phase_2_design_doc.md
- _agents/rules/phases/phase_3_goldfish_protocol.md
- _agents/rules/phases/phase_4_implementation.md
- boilerplate-agent/rules/orchestrator.md
- boilerplate-agent/rules/unified_superpower_workflow.md
generated_at_ref: b341f91c9dedfba9ea77683443093879cad39600
generated_at: 2026-05-12T23:04:50Z
links_to: []
covers: []
contradictions:
- description: Wiki stated Phase 1 is 'Design Discussion' and Phase 2 is 'Design Documentation', but code/dispatch rules now define them as 'Discovery & Design Challenge' and 'Planning & Design Doc'.
  source: boilerplate-agent/rules/dispatch_rules.md
  detected_at: 2026-05-12T23:04:50Z
- description: Wiki described a 6-state machine in 'unified_superpower_workflow.md', but that file has been removed in favor of a phase-based system in 'dispatch_rules.md'.
  source: boilerplate-agent/rules/dispatch_rules.md
  detected_at: 2026-05-12T23:04:50Z
---

# E2G Harness: Workflow Orchestration System

The E2G harness implements a sophisticated multi-phase workflow orchestration system designed to guide AI agents through complex software development tasks. The system enforces structured progression through clearly defined phases, each with specific objectives and validation criteria.

## Core Orchestration Pattern

The orchestration follows a **Hub-and-Spoke model** managed by a Senior Project Manager (Orchestrator). The system has transitioned from distributed configurations in `_agents/` to a centralized structure within the `.gemini/` directory.

The master orchestrator (`.gemini/orchestrator.md`) defines the primary workflow, utilizing the **Indexer MCP Integration** to maintain codebase awareness without context bloat. Individual phase execution is guided by `dispatch_rules.md`.

### Key Orchestration Mandates
- **Zero Work Rule**: The Orchestrator is forbidden from modifying code directly; it must delegate to specialized subagents.
- **Artifact-Driven Communication**: Detailed plans and reports are stored in `artifacts/` to keep session histories lean.
- **Wiki-First Indexing**: Reliance on the `indxr` MCP server for verified structural context.

## Phase Structure and Flow

The workflow has been streamlined into distinct lifecycle phases managed via `dispatch_rules.md`.

### Phase 1: Discovery & Design Challenge (No Code)
- **Objective**: Feature exploration and adversarial validation without implementation.
- **Key Constraint**: Absolute prohibition on code generation.
- **Process**: Context loading → Feature description → Adversarial challenge → Technical proposal.
- **Output**: Validated requirements and a high-level architectural approach.

### Phase 2: Planning & Design Doc (The Source of Truth)
- **Objective**: Create a comprehensive technical specification.
- **Structure**: Mandatory sections including Business Problem, Technical Plan, and Alternatives.
- **Quality Gate**: **Sphinch Marks** provide readiness assertions before implementation begins.
- **Output**: `implementation_plan.md` and `task.md` artifacts.

### Execution & Verification
Following the design phases, the system moves through:
- **TDD Implementation**: Subagents (e.g., `@implementer`) write production code strictly using Test-Driven Development.
- **Adversarial Review**: The `@reviewer` and `@adversary` agents perform "mean" reviews to identify defects.
- **QA & Verification**: The `@verifier` agent performs final robustness checks.

## Agent Architecture and Minting

### Specialized Agent Roles
The ecosystem has evolved into a standardized set of markdown specifications:
- **Core Workflow**: Architect, Planner, Implementer, Reviewer, Verifier.
- **Specialized**: Security Auditor, Performance Profiler, Linter Agent, Refactorer.
- **Dynamic SMEs**: The system can now synthesize **Domain SME Agents** specifically tailored to the project's tech stack and domain concepts.

### Discovery & Minting Engines
The harness includes advanced automation for workspace setup:
- **Tech Stack Detection**: Automatically identifies project technologies to inform agent configuration.
- **Dynamic SME Synthesis**: `synthesize_domain_sme_agent` creates specialized agents based on domain analysis.
- **Dynamic Dispatch Injection**: The `minting_engine` automatically injects newly discovered DDD agents into the workspace's `dispatch_rules.md` during generation.
- **Remote Skill Fetching**: Capabilities can be acquired dynamically from external repositories.

## Design Principles

**Phase Isolation**: Each phase operates with explicit context loading to prevent information decay.

**Adversarial Validation**: Multiple phases incorporate adversarial review to stress-test decisions before code is written.

**Sphinch Mark System**: Quantified readiness assertions replace subjective quality gates.

**Domain-Aware Processing**: Domain-Driven Design (DDD) analysis provides architectural intelligence that informs agent decision-making throughout the workflow.

**Tool Orchestration**: Automated installation of workspace tools, skills, and MCP configurations during the minting process.





