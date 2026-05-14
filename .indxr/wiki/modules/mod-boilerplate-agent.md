---
id: mod-boilerplate-agent
title: Boilerplate Agent System
page_type: module
source_files:
- boilerplate-agent/agent.json
- boilerplate-agent/config.yaml
- boilerplate-agent/agents/core/implementer/agent.json
- boilerplate-agent/agents/core/implementer/config.yaml
- boilerplate-agent/agents/core/planner/agent.json
- boilerplate-agent/agents/core/planner/config.yaml
- boilerplate-agent/agents/core/reviewer/agent.json
- boilerplate-agent/agents/core/reviewer/config.yaml
- boilerplate-agent/agents/core/verifier/agent.json
- boilerplate-agent/agents/core/verifier/config.yaml
- boilerplate-agent/agents/discovery/adversary/agent.json
- boilerplate-agent/agents/discovery/adversary/config.yaml
- boilerplate-agent/agents/discovery/architect/agent.json
- boilerplate-agent/agents/discovery/architect/config.yaml
- boilerplate-agent/agents/discovery/designdoc_drafter/agent.json
- boilerplate-agent/agents/discovery/designdoc_drafter/config.yaml
- boilerplate-agent/agents/discovery/feature-fetcher/agent.json
- boilerplate-agent/agents/discovery/feature-fetcher/config.yaml
- boilerplate-agent/scripts/clone_harness.py
- boilerplate-agent/scripts/clone_harness.sh
- boilerplate-agent/scripts/setup_harness.sh
generated_at_ref: b29a3ffd2cf37a1a0c14e3c142224bee9fdd325d
generated_at: 2026-05-14T04:26:21Z
links_to:
- mod-harness-core
covers:
- key:name
- key:description
- key:type
- key:version
- key:entrypoint
- key:skills
- key:related_agents
contradictions:
- description: 'Wiki stated architecture is organized into three distinct lifecycle phases, but dispatch_rules.md now defines four phases starting with Phase 0: Diagnosis.'
  source: boilerplate-agent/rules/dispatch_rules.md
  detected_at: 2026-05-14T04:26:21Z
---

# Boilerplate Agent System

The Boilerplate Agent System provides a reference implementation of a hierarchical agent orchestration pattern using the [[mod-harness-core]] framework. This system demonstrates the hub-and-spoke architecture where a router agent coordinates specialized sub-agents through a rule-based lifecycle.

## Architecture

The system follows a dynamic, Domain-Driven Design (DDD) approach organized into four distinct lifecycle phases:

0.  **Phase 0: Diagnosis (BUG FIXES ONLY)**: Initial triage and root-cause analysis for reported defects before entering the planning stage.
1.  **Phase 1: Discovery & DDD Alignment**: Automatic analysis of project domains and technical stacks to establish the ubiquitous language and architectural boundaries.
2.  **Phase 2: Minting & Setup**: Dynamic creation of specialized agents and workspace configuration, including tool installation and rule injection.
3.  **Phase 3: Final User State**: The operational environment where the `orchestrator` manages execution via delegated sub-agents.

### Router Layer
The `orchestrator` agent (`boilerplate-agent/agent.json`) acts as the central router. It uses `boilerplate-agent/rules/dispatch_rules.md` to govern delegation, moving away from static hierarchies toward dynamic, context-aware routing.

### Agent Discovery and Minting
The system features an automated engine for workspace initialization:
- **Tech Stack Detection**: Automatic identification of project languages and frameworks via `detect_tech_stack()` (`discovery_engine.py:81`).
- **DDD Context Discovery**: Deep analysis of project domains using `discover_ddd_context()`.
- **Custom Agent Generation**: Dynamic creation of specialized agents tailored to the project's specific needs via `discover_custom_agent()`.
- **Workspace Tooling**: Automated installation of workspace-specific tools and MCP servers during minting (`minting_engine.py:112`).

## Agent Definitions

Agents are defined as Markdown documents, emphasizing clear mandates and operational "scratchpads":

### Core Execution Agents
- **planner**: Strategic planning, task breakdown, and design document management (`boilerplate-agent/agents/planner.md`).
- **implementer**: Code generation following strict TDD patterns (`boilerplate-agent/agents/implementer.md`).
- **reviewer**: Code quality assessment and architectural adherence (`boilerplate-agent/agents/reviewer.md`).
- **verifier**: QA, testing validation, and robustness checks (`boilerplate-agent/agents/verifier.md`).

### Discovery and Analysis Agents
- **architect**: Codebase mapping, system design, and root-cause analysis (`boilerplate-agent/agents/architect.md`).
- **adversary**: Critical validation and skeptical review of implementation strategies (`boilerplate-agent/agents/adversary.md`).

### Specialized Domain Agents
- **feature-fetcher**: Dynamic discovery and proposal of new capabilities (`boilerplate-agent/agents/feature-fetcher.md`).
- **linter-agent**: Automated fixing of linting and formatting issues (`boilerplate-agent/agents/linter-agent.md`).
- **security-auditor**: Deep security analysis and vulnerability scanning (`boilerplate-agent/agents/security-auditor.md`).
- **performance-profiler**: Identification of bottlenecks and optimization opportunities (`boilerplate-agent/agents/performance-profiler.md`).
- **refactorer**: Specialized in structural debt reduction and refactoring (`boilerplate-agent/agents/refactorer.md`).

## Configuration System

### Rule-Based Configuration
- **Core Mandates**: Fundamental rules including a **Wiki-First Indexer Integration** that prioritizes the codebase index for context (`boilerplate-agent/rules/core_mandates.md`).
- **Dispatch Rules**: Routing logic that enforces the transition between Diagnosis, Brainstorming, Planning, TDD, and Implementation (`boilerplate-agent/rules/dispatch_rules.md`).

### Skills Integration
The system utilizes a modular skills configuration (`boilerplate-agent/skills.json`) and supports dynamic skill fetching. Skills are now consolidated within the `boilerplate-agent/skills/` directory. Key skills include:
- **diagnose**: Specialized skill for bug triage and stacktrace extraction (utilizing `extract_stacktrace.py`).
- **grill-me**: Interactive validation of plans and designs.
- **grill-with-docs**: Documentation-aware analysis and ADR enforcement.
- **improve-codebase-architecture**: Proactive identification of refactoring opportunities.
- **meta-learning**: Deep-dive analysis for complex subjects.

## Enhanced Discovery Engine

The discovery system integrates with the project's environment to ensure high-fidelity context:
- **MCP-Based Context**: Gathering structural information via Indexer MCP, supporting specific bundle paths for localized analysis (`discovery_engine.py:35`).
- **Onboarding Automation**: Generation of domain-specific onboarding documentation to ground new agents (`discovery_engine.py:59`).
- **Interactive DDD Grilling**: CLI-driven domain analysis to refine the agentic workspace.

## Design Principles

1.  **Dynamic Adaptation**: Agents are discovered and created based on the detected tech stack and project needs.
2.  **Domain-Driven Organization**: The workspace structure follows business domains and architectural boundaries.
3.  **Rule-Based Orchestration**: Behavior is governed by explicit, versioned rules in Markdown rather than hardcoded logic.
4.  **Contextual Grounding**: Deep integration with the project index (via `indxr`) to maintain accuracy without token bloat.



