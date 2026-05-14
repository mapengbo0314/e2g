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
generated_at_ref: b341f91c9dedfba9ea77683443093879cad39600
generated_at: 2026-05-12T23:04:50Z
links_to:
- mod-agents
- mod-harness-core
covers: []
contradictions:
- description: Wiki stated the registry is at _agents/skills.json, but that directory was removed and replaced by boilerplate-agent/skills.json
  source: boilerplate-agent/skills.json
  detected_at: 2026-05-12T23:04:50Z
- description: Wiki listed adk_document_structurer and repo_migration_planner as examples, but these were deleted from the codebase.
  source: _agents/skills/
  detected_at: 2026-05-12T23:04:50Z
---

The Skills System is the core competency framework that defines reusable agent capabilities across the harness. Skills are modular, testable units that encapsulate domain-specific knowledge and workflows, organized in a hierarchical directory structure with standardized documentation and evaluation patterns.

## Architecture

Skills follow a standardized structure centered around:
- `SKILL.md`: Defines purpose, use cases, and behavioral contracts.
- **Supporting files**: Checklists, templates (e.g., `ADR-FORMAT.md`), and configuration.

The system maintains a registry at `boilerplate-agent/skills.json` (formerly `_agents/skills.json`) that indexes available skills, enabling dynamic discovery and composition by the [[mod-agents]] system. A `skills-lock.json` file is used to manage and lock skill versions.

## Skill Categories

### Domain & Workflow Skills
The harness now prioritizes architectural and alignment-focused skills:

- **ddd-alignment**: Ensures implementations stay consistent with Domain-Driven Design principles.
- **grill-me / grill-with-docs**: Interview-based skills for stress-testing plans against domain models and existing documentation.
- **improve-codebase-architecture**: Identifies refactoring and deepening opportunities within the codebase.
- **meta-learning**: Facilitates deep understanding of new, complex subjects.
- **fastapi / nextjs**: Technical stack-specific skills for standardizing implementation patterns.

### Skill Evolution
The system has fully transitioned from fixed, phase-gated models (like the legacy `harness-workflow`) to a highly dynamic, discovery-driven architecture. Skills are no longer just local files but can be fetched and installed on-demand based on the project's detected technology stack and DDD context.

## Integration Patterns

Skills integrate with the harness through several updated mechanisms:

1.  **Dynamic Discovery & Fetching**: The [[mod-harness-core]] discovery engine utilizes `fetch_skill(skill_name, remote_url)` to retrieve capabilities from remote sources, allowing for a distributed ecosystem of skills.
2.  **Automated Installation**: During workspace generation, the `minting_engine.py` uses `install_workspace_tools()` to inject selected skills and MCP configurations directly into the target environment.
3.  **DDD Context Awareness**: Skills are selected and configured via `discover_ddd_context()`, ensuring the agent's capabilities are relevant to the specific business domain.
4.  **Agent Composition**: The [[mod-agents]] system dynamically loads skills based on agent configurations (managed in `.gemini/agents/`), allowing per-agent skill specialization.

## Enhanced Discovery Capabilities

The skills system supports:
- **Remote Skill Fetching**: Skills can be loaded from external sources via URL.
- **DDD Context Awareness**: Skills are selected and configured based on domain-driven design contexts.
- **Custom Agent Generation**: Skills are dynamically composed into custom agents through `discover_custom_agent()`.

## Design Invariants

Skills maintain strict specification in `SKILL.md`. The standardized structure allows the harness to treat skills as black boxes while maintaining discoverability and composability.

The system assumes skills are stateless and idempotent - they operate on input data and produce deterministic outputs without side effects beyond their defined scope. This enables safe parallel execution and reproducible results across multiple harness runs.




