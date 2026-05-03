# Agent Config Schema

The agents follow a consistent per-agent structure:

- `BUILD`
- `agent.json`
- `config.yaml`

This repository uses a shared schema that keeps a consistent pattern while remaining easy to refine.

## Shape

```yaml
version: 1
agent:
  name: planner
  role: workflow_planning
  owner: _agents/agents/planner
runtime:
  primary_language: markdown
instructions:
  system_rules:
    - ../../../AGENT.md
    - ../../rules/orchestrator.md
  skills:
    - ../../skills/example/SKILL.md
  goals:
    - describe the agent's objectives
  constraints:
    - describe the agent's limits
capabilities:
  inputs:
    - user request
  outputs:
    - execution plan
handoff:
  upstream:
    - architect
  downstream:
    - implementer
success_criteria:
  - optional validation targets
```

## Why it looks like this

- `agent.json` stays minimal, just like your screenshot.
- `config.yaml` carries behavior, routing, and role-level instructions.
- shared rules and skills are referenced by path so future updates stay local
  and composable.
