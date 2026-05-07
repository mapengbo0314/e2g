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
- boilerplate-agent/agents/discovery/codesigner/agent.json
- boilerplate-agent/agents/discovery/codesigner/config.yaml
- boilerplate-agent/agents/discovery/designdoc_drafter/agent.json
- boilerplate-agent/agents/discovery/designdoc_drafter/config.yaml
- boilerplate-agent/agents/discovery/feature-fetcher/agent.json
- boilerplate-agent/agents/discovery/feature-fetcher/config.yaml
- boilerplate-agent/scripts/clone_harness.py
- boilerplate-agent/scripts/clone_harness.sh
- boilerplate-agent/scripts/setup_harness.sh
generated_at_ref: 703d472a00754a21da89f8b7ca2cde038b89e5b3
generated_at: 2026-05-06T21:04:02Z
links_to:
- mod-harness-core
- topic-workflow-orchestration
covers:
- key:name
- key:description
- key:type
- key:version
- key:entrypoint
- key:system_prompt
- key:name
- key:description
- key:configPath
- key:coding_agent
- key:agentic_mode
- key:prompt_section_customization
- key:customization_config
- key:name
- key:description
- key:configPath
- key:coding_agent
- key:agentic_mode
- key:prompt_section_customization
- key:customization_config
- key:name
- key:description
- key:configPath
- key:coding_agent
- key:agentic_mode
- key:prompt_section_customization
- key:customization_config
- key:name
- key:description
- key:configPath
- key:coding_agent
- key:agentic_mode
- key:prompt_section_customization
- key:customization_config
- key:name
- key:description
- key:coding_agent
- key:agentic_mode
- key:prompt_section_customization
- key:customization_config
- key:name
- key:description
- key:configPath
- key:coding_agent
- key:agentic_mode
- key:prompt_section_customization
- key:customization_config
- key:name
- key:description
- key:configPath
- key:coding_agent
- key:agentic_mode
- key:prompt_section_customization
- key:customization_config
- key:name
- key:description
- key:configPath
- key:coding_agent
- key:agentic_mode
- key:prompt_section_customization
- key:customization_config
- key:name
- key:description
- key:type
- key:version
- key:entrypoint
- key:system_prompt
- fn:main
---

The Boilerplate Agent System provides a reference implementation of a hierarchical agent orchestration pattern using the [[mod-harness-core]] framework. This system demonstrates the hub-and-spoke architecture where a router agent coordinates specialized sub-agents organized into functional domains.

## Architecture

The system implements a three-tier hierarchy:

1. **Router Layer**: The `orchestrator` agent (`agent.json:2`) acts as the entry point, managing delegation to sub-agents based on task requirements
2. **Domain Layer**: Agents are grouped into `core/` (execution-focused) and `discovery/` (analysis-focused) domains
3. **Specialization Layer**: Each domain contains specialized agents with specific responsibilities

The router uses `"type": "router"` (`agent.json:4`) to indicate its orchestration role, while sub-agents use domain-specific types or default to execution agents.

## Core Domain Agents

The `core/` domain implements a TDD-style workflow pipeline:

- **planner**: Breaks down requirements into detailed execution steps (`planner/agent.json:3`)
- **implementer**: Handles code generation and modification (`implementer/agent.json:3`)
- **reviewer**: Performs code quality assessment (`reviewer/agent.json:3`)
- **verifier**: Conducts final QA and edge-case testing (`verifier/agent.json:3`)

Each core agent uses `coding_agent: true` in their config files, enabling code-generation capabilities through the [[mod-harness-core]] framework.

## Discovery Domain Agents

The `discovery/` domain handles analysis and design activities:

- **architect**: Performs codebase analysis and dependency mapping (`architect/agent.json:3`)
- **codesigner**: Acts as adversarial design partner (`codesigner/agent.json:3`)
- **designdoc_drafter**: Documents technical designs and impact analysis (`designdoc_drafter/agent.json:3`)
- **adversary**: Provides skeptical validation (`adversary/agent.json:2`)
- **feature-fetcher**: Proposes specialized domain agents (`feature-fetcher/agent.json:2`)

## Configuration Pattern

All agents follow a consistent configuration structure:

1. **Agent Metadata**: `agent.json` files define name, description, and config path using `"configPath": {"relativePathToConfig": "config.yaml"}` pattern
2. **Behavioral Config**: `config.yaml` files contain `prompt_section_customization` and `customization_config` sections that specialize agent behavior
3. **Mode Configuration**: The `agentic_mode` setting controls autonomous operation vs. guided execution

## Deployment Infrastructure

The system includes deployment scripts that integrate with [[mod-harness-core]]:

- `clone_harness.py` (`scripts/clone_harness.py:86`): Programmatic setup for agent environments
- `clone_harness.sh` and `setup_harness.sh`: Shell-based deployment automation

These scripts handle the initialization of agent workspaces and ensure proper integration with the harness framework.

## Design Principles

The boilerplate demonstrates several key patterns:

1. **Separation of Concerns**: Each agent has a single, well-defined responsibility
2. **Hierarchical Delegation**: The router maintains workflow context while delegating specialized tasks
3. **Configuration Inheritance**: Common patterns are shared while allowing agent-specific customization
4. **Domain Segregation**: Core execution agents are separated from discovery/analysis agents

This structure provides a template for implementing complex multi-agent workflows while maintaining clear boundaries and predictable interaction patterns. See [[topic-workflow-orchestration]] for details on how these agents coordinate during execution.
