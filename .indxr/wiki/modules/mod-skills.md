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
generated_at_ref: 703d472a00754a21da89f8b7ca2cde038b89e5b3
generated_at: 2026-05-06T21:04:02Z
links_to:
- mod-agents
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
- heading:Harness Workflow
---

The Skills System is the core competency framework that defines reusable agent capabilities across the harness. Skills are modular, testable units that encapsulate domain-specific knowledge and workflows, organized in a hierarchical directory structure with standardized documentation and evaluation patterns.

## Architecture

Skills follow a standardized structure with three required components:
- `SKILL.md`: Defines purpose, use cases, and behavioral contracts
- `EVAL.yaml`: Specifies evaluation targets and success criteria  
- Supporting files: Scripts, references, and test materials

The system maintains a registry at `_agents/skills.json` that indexes available skills, enabling dynamic discovery and composition by the [[mod-agents]] system.

## Skill Categories

### System Skills
**harness-workflow** (`boilerplate-agent/skills/harness-workflow/SKILL.md:1`) implements the core 5-phase execution model:
1. CLI Bootstrapping (human-driven setup)
2. Agent Factory (feature extraction via `feature-fetcher`)
3. Deterministic Execution (LangGraph orchestration)
4. Agent Arena evaluation
5. Wrap-up and PR generation

This skill enforces strict TDD gates via `verify_tdd_gate.sh` that validates test coverage before phase transitions.

### Domain Skills
**adk_document_structurer** focuses on technical documentation parsing and structuring, particularly for ADK-style specifications. Evaluation targets include structural accuracy and completeness metrics.

**repo_migration_planner** handles repository transformation workflows, with drift detection capabilities via `detect_drift.py`. The skill maintains expected modification patterns in `references/expected_modifications.md` for validation.

## Integration Patterns

Skills integrate with the harness through three mechanisms:

1. **Agent Composition**: The [[mod-agents]] system dynamically loads skills based on agent configurations, allowing per-agent skill specialization
2. **Workflow Orchestration**: The [[topic-workflow-orchestration]] system uses skills as execution units within phase-based workflows
3. **Evaluation Framework**: Skills expose evaluation targets that integrate with the testing infrastructure in [[mod-testing]]

## Design Invariants

Skills maintain strict separation between specification (`SKILL.md`) and evaluation (`EVAL.yaml`), enabling independent evolution of capability definitions and success criteria. The standardized structure allows the harness to treat skills as black boxes while maintaining discoverability and composability.

The system assumes skills are stateless and idempotent - they operate on input data and produce deterministic outputs without side effects beyond their defined scope. This enables safe parallel execution and reproducible results across multiple harness runs.
