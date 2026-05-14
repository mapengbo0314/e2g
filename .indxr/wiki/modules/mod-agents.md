---
id: mod-agents
title: Agent Configuration System
page_type: module
source_files:
- _agents/agents/config-schema.md
- _agents/agents.json
- _agents/reload_agents.py
- _agents/agents/adversary/agent.json
- _agents/agents/adversary/config.yaml
- _agents/agents/architect/agent.json
- _agents/agents/architect/config.yaml
- _agents/agents/designdoc_drafter/agent.json
- _agents/agents/designdoc_drafter/config.yaml
- _agents/agents/implementer/agent.json
- _agents/agents/implementer/config.yaml
- _agents/agents/planner/agent.json
- _agents/agents/planner/config.yaml
- _agents/agents/reviewer/agent.json
- _agents/agents/reviewer/config.yaml
- _agents/agents/verifier/agent.json
- _agents/agents/verifier/config.yaml
generated_at_ref: b341f91c9dedfba9ea77683443093879cad39600
generated_at: 2026-05-12T23:04:50Z
links_to:
- mod-harness-core
- topic-workflow-orchestration
covers: []
contradictions:
- description: Wiki stated agent configurations are stored in _agents/agents/, but the directory has been removed and they are now in .gemini/agents/.
  source: 'Structural Diff: Removed _agents/'
  detected_at: 2026-05-12T23:04:50Z
- description: Wiki referenced reload_agents() in _agents/reload_agents.py, but this file has been removed.
  source: 'Structural Diff: Removed _agents/reload_agents.py'
  detected_at: 2026-05-12T23:04:50Z
- description: Wiki referenced _agents/agents.json for registry structure, but this file has been removed.
  source: 'Structural Diff: Removed _agents/agents.json'
  detected_at: 2026-05-12T23:04:50Z
---

# Agent Configuration System

The agent configuration system provides a centralized mechanism for defining specialized AI agents with distinct roles, capabilities, and behavioral configurations. This system enables workflow orchestration by allowing the harness to dynamically select, configure, and synthesize agents based on task requirements.

## Configuration Architecture

**MAJOR ARCHITECTURAL CHANGE**: The system has transitioned from a centralized `_agents/` directory to a project-local configuration stored within the `.gemini/` directory of the workspace. This shift supports the "Minting" lifecycle, where agents are tailored to the specific domain of the codebase during setup.

### Agent Definition Format

Agent configurations are stored as standalone Markdown files in `.gemini/agents/`. Each agent is defined in a single `.md` file (e.g., `planner.md`, `architect.md`) containing:
- **Metadata**: Name, Description, Type, Version.
- **Skills**: A list of associated superpower skills.
- **System Prompt**: The persona and behavioral instructions.

### Discovery and Synthesis (DDD Alignment)

The system now features a dynamic **Domain-Driven Design (DDD) Discovery** phase. 
- **Custom Agent Discovery**: `harness/discovery_engine.py` can discover or propose custom agents based on the project's tech stack and domain summary.
- **SME Synthesis**: `harness/minting_engine.py` can synthesize a "Domain SME" (Subject Matter Expert) agent (`synthesize_domain_sme_agent`) specifically for the project, which is then minted into the workspace.

## Agent Registry and Orchestration

The previous `reload_agents.py` and `agents.json` registry have been replaced by the **Orchestrator** model. 

- **Entrypoint**: The primary orchestration entry point is defined in `.gemini/orchestrator.md`.
- **Dynamic Routing**: During the minting process, `minting_engine.py` patches the workspace's `dispatch_rules.md` to inject routing rules for newly discovered DDD agents. This allows the Orchestrator to delegate tasks to these specialized agents automatically.

## Specialized Agent Roles

The system utilizes a variety of specialized roles, defined in Markdown format within the workspace:

- **Planner**: Primary orchestration agent for task decomposition and workflow coordination.
- **Architect**: Deep codebase analysis and system-wide dependency mapping.
- **Implementer**: TDD execution and production code changes.
- **Reviewer**: Code quality assessment and standards enforcement.
- **Verifier**: Final QA, edge-case testing, and robustness verification.
- **Adversary**: Hyper-skeptical validation agent for critical path verification.
- **Refactorer**: Specialized in structural refactoring and technical debt reduction.
- **Linter-agent**: Specialized in fixing lint, type errors, and formatting.
- **Security-auditor**: Performs security audits and vulnerability scanning.
- **Performance-profiler**: Identifies performance bottlenecks.

## Integration with Core Harness

The configuration system integrates with [[mod-harness-core]] through the `minting_engine`. The migration to workspace-local `.gemini/` definitions ensures that agent behavior is portable and grounded in the project's specific context.

## Boilerplate Integration

The `boilerplate-agent/` directory provides the source templates for all standard agents and rules.
- **Template Agents**: Located in `boilerplate-agent/agents/`.
- **Tool Checklists**: `boilerplate-agent/onboarding/tools.json` provides a registry of installable tools and skills that can be added to the workspace during minting.
- **Skills System**: A rich set of skills (e.g., `ddd-alignment`, `grill-me`, `improve-codebase-architecture`) is bundled in `boilerplate-agent/skills/` and mapped via `boilerplate-agent/skills.json`.

## Cross-Agent Communication Protocol

Agent configurations include communication protocols that enable the [[topic-workflow-orchestration]] system. The Orchestrator uses the `@agent` syntax defined in `.gemini/rules/dispatch_rules.md` to handle handoffs, context preservation via artifacts in `workspace/artifacts/`, and result validation.





