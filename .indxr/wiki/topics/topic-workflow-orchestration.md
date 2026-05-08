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
generated_at_ref: f1af3b2fa46c98c92658d870947ac03b9020de8a
generated_at: 2026-05-08T19:40:40Z
links_to: []
covers:
- heading:Orchestrator Rules
- heading:Primary Workflows (The Superpower Workflow)
- 'heading:Phase 1: The Design Discussion (No Code Yet)'
- 'heading:Phase 2: Writing the Design Doc'
- 'heading:Phase 3: The "Goldfish" Review Protocol'
- 'heading:Phase 4: Implementation & Mean Review'
- heading:The Universal Agentic Harness Protocol
---

# E2G Harness: Workflow Orchestration System

The E2G harness implements a sophisticated multi-phase workflow orchestration system designed to guide AI agents through complex software development tasks. The system enforces structured progression through clearly defined phases, each with specific objectives and validation criteria.

## Core Orchestration Pattern

The orchestration follows a **phased goldfish protocol** that treats each phase as an independent unit requiring fresh context loading. This design prevents context drift and ensures consistent quality across long-running workflows.

The master orchestrator (`_agents/rules/orchestrator.md`) defines the primary workflow structure, while individual phase specifications (`_agents/rules/phases/`) provide detailed execution rules. The boilerplate agent system (`boilerplate-agent/`) implements a parallel **Universal Agentic Harness Protocol** with its own state machine.

## Phase Structure and Flow

### Phase 1: Design Discussion (`phase_1_design_discussion.md`)
- **Objective**: Feature exploration without implementation
- **Key Constraint**: Absolute prohibition on code generation
- **Process**: Context loading → Feature description → Adversarial challenge → Technical proposal
- **Output**: Validated feature requirements and high-level approach

### Phase 2: Design Documentation (`phase_2_design_doc.md`)
- **Objective**: Create comprehensive technical specification
- **Structure**: Five mandatory sections (Business Problem, Technical Plan, Alternatives, Implementation, Sphinch Marks)
- **Quality Gate**: Sphinch Marks (SM-1 through SM-N) provide readiness assertions
- **Output**: Implementation-ready design document serving as source of truth

### Phase 3: Goldfish Protocol (`phase_3_goldfish_protocol.md`)
- **Objective**: Validation through fresh perspective simulation
- **Core Mechanism**: Agent must demonstrate understanding as if seeing the project for the first time
- **Validation Steps**: Comprehension test → Sphinch Mark verification → Implementation readiness assessment
- **Fallback**: Legacy open-ended critic review if goldfish protocol insufficient

### Phase 4: Implementation (`phase_4_implementation.md`)
- **Objective**: Code generation with adversarial review
- **Process**: Coding with guardrails → "Mean" adversarial code review
- **Quality Control**: Aggressive criticism to identify defects before human review

## State Machine Architecture (Boilerplate Agent)

The boilerplate agent implements a complementary **Universal Agentic Harness Protocol** (`unified_superpower_workflow.md`) with six discrete states:

- **State 0**: Bootstrap & Factory Minting - Initial setup and capability discovery
- **State 1**: Feature Refinement - Requirements clarification and scope definition  
- **State 2**: Planning - Architecture design and implementation strategy
- **State 3**: Execution & Testing - Code generation with continuous validation
- **State 4**: Adversarial Verification - Aggressive quality assurance
- **State 5**: Wrap-up & Review - Final validation and documentation

### Domain-Driven Design Integration

The boilerplate agent workflow now includes a **Domain-Driven Design (DDD) mandate** that provides specialized context analysis and domain modeling capabilities. This enhancement enables agents to better understand project structure, domain boundaries, and architectural patterns before engaging in implementation work.

## Agent Architecture Evolution

### Centralized Agent Management

The system has migrated from distributed agent configurations to centralized management:

- **Main Harness**: Agents consolidated in `_agents/agents/` as markdown specifications (replacing JSON-based configs)
- **Boilerplate System**: Agents standardized in `boilerplate-agent/agents/` with consistent markdown format
- **Discovery Engine**: Enhanced with DDD context analysis, custom agent discovery, and remote skill fetching
- **Minting Engine**: Extended with model choice options, bundle overrides, and DDD context integration

### Specialized Agent Roles

The agent ecosystem includes specialized roles:
- **Core Workflow Agents**: Architect, Implementer, Reviewer, Verifier
- **Specialized Agents**: Security Auditor, Performance Profiler, Linter Agent, Refactorer
- **Discovery Agents**: Feature Fetcher for dynamic capability identification
- **Documentation Agents**: Design Doc Drafter for technical specification generation

## Enhanced Discovery and Context Management

### DDD Context Analysis
The discovery engine now includes domain-driven design analysis capabilities that extract and model domain concepts, boundaries, and relationships from project contexts. This provides agents with richer architectural understanding before task execution.

### Remote Skill Integration
The system supports fetching remote skills dynamically, enabling agents to acquire new capabilities from external repositories during workflow execution.

### Custom Agent Discovery
Agents can be discovered and configured dynamically based on project-specific requirements, moving beyond static predefined roles to adaptive capability matching.

## Design Principles

**Phase Isolation**: Each phase operates independently with explicit context loading to prevent information decay across long sessions.

**Adversarial Validation**: Multiple phases incorporate adversarial review (Phase 1 challenge, Phase 3 goldfish test, Phase 4 mean review) to stress-test decisions before human involvement.

**Sphinch Mark System**: Quantified readiness assertions replace subjective quality gates, providing concrete validation criteria for phase transitions.

**Superpower Integration**: The state machine explicitly invokes superpower skills at appropriate phases, ensuring agents leverage their full capability spectrum.

**Domain-Aware Processing**: DDD context analysis provides architectural intelligence that informs agent decision-making throughout the workflow.

## Orchestration Invariants

1. **No Phase Skipping**: Each phase must complete successfully before progression
2. **Context Refresh**: Agents must reload context at phase boundaries to simulate fresh perspective
3. **Validation Gates**: Sphinch Marks and adversarial reviews must pass before implementation
4. **Documentation Primacy**: Phase 2 design document serves as authoritative specification for all subsequent phases
5. **DDD Context Grounding**: Domain analysis must inform architectural decisions across all phases

The dual orchestration systems (main harness + boilerplate agent) provide redundancy and specialization - the main system handles general workflows while the boilerplate agent optimizes for rapid prototyping, skill demonstration, and domain-driven development scenarios.
