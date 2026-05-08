---
id: mod-skills
title: Skills System
page_type: module
source_files:
- _agents/skills.json
- _agents/skills/adk_document_structurer/EVAL.yaml
- _agents/skills/adk_document_structurer/SKILL.md
- _agents/skills/adk_document_structurer/TEST.md
- _agents/skills/repo_migration_planner/SKILL.md
- _agents/skills/repo_migration_planner/references/expected_modifications.md
- _agents/skills/repo_migration_planner/scripts/detect_drift.py
- boilerplate-agent/skills/harness-workflow/SKILL.md
- boilerplate-agent/skills/harness-workflow/verify_tdd_gate.sh
generated_at_ref: f1af3b2fa46c98c92658d870947ac03b9020de8a
generated_at: 2026-05-08T19:40:40Z
links_to:
- mod-agents
- mod-harness-core
- topic-workflow-orchestration
- mod-testing
covers:
- key:skills
- key:name
- key:eval_targets
- 'heading:Skill: ADK Document Structurer'
- heading:Test Notes
- 'heading:Skill: Repo Migration Planner'
- heading:Expected Modifications
- fn:detect_drift
contradictions:
- description: Wiki stated harness-workflow skill exists with 5-phase execution model and TDD gates, but this skill has been removed from the codebase
  source: boilerplate-agent/skills/harness-workflow/SKILL.md
  detected_at: 2026-05-08T19:40:40Z
---

The Skills System is the core competency framework that defines reusable agent capabilities across the harness. Skills are modular, testable units that encapsulate domain-specific knowledge and workflows, organized in a hierarchical directory structure with standardized documentation and evaluation patterns.

## Architecture

Skills follow a standardized structure with three required components:
- `SKILL.md`: Defines purpose, use cases, and behavioral contracts
- `EVAL.yaml`: Specifies evaluation targets and success criteria  
- Supporting files: Scripts, references, and test materials

The system maintains a registry at `_agents/skills.json` that indexes available skills, enabling dynamic discovery and composition by the [[mod-agents]] system.

## Skill Categories

### Domain Skills
**adk_document_structurer** focuses on technical documentation parsing and structuring, particularly for ADK-style specifications. Evaluation targets include structural accuracy and completeness metrics.

**repo_migration_planner** handles repository transformation workflows, with drift detection capabilities via `detect_drift.py`. The skill maintains expected modification patterns in `references/expected_modifications.md` for validation.

### Skill Evolution

The skill system has evolved from its original architecture where system skills like **harness-workflow** provided core 5-phase execution models with TDD gates. The system has shifted toward a more flexible, agent-driven approach where skills are dynamically discovered and composed through the enhanced discovery engine.

## Integration Patterns

Skills integrate with the harness through several mechanisms:

1. **Dynamic Discovery**: The [[mod-harness-core]] discovery engine can now fetch remote skills via `fetch_remote_skill()`, enabling distributed skill repositories and dynamic capability expansion

2. **Agent Composition**: The [[mod-agents]] system dynamically loads skills based on agent configurations, allowing per-agent skill specialization

3. **Workflow Orchestration**: The [[topic-workflow-orchestration]] system uses skills as execution units within phase-based workflows

4. **Evaluation Framework**: Skills expose evaluation targets that integrate with the testing infrastructure in [[mod-testing]]

5. **Domain-Driven Design (DDD) Integration**: Skills now support DDD contexts through the discovery engine's `discover_ddd_context()` function, enabling contextual skill selection and composition

## Enhanced Discovery Capabilities

The skills system now supports:
- **Remote Skill Fetching**: Skills can be loaded from external sources via URL
- **DDD Context Awareness**: Skills can be selected and configured based on domain-driven design contexts
- **Custom Agent Generation**: Skills can be dynamically composed into custom agents through `discover_custom_agent()`

## Design Invariants

Skills maintain strict separation between specification (`SKILL.md`) and evaluation (`EVAL.yaml`), enabling independent evolution of capability definitions and success criteria. The standardized structure allows the harness to treat skills as black boxes while maintaining discoverability and composability.

The system assumes skills are stateless and idempotent - they operate on input data and produce deterministic outputs without side effects beyond their defined scope. This enables safe parallel execution and reproducible results across multiple harness runs.
