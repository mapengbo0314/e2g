---
id: mod-agents
title: Agent Configuration System
page_type: module
source_files:
- _agents/agents/CONFIG_SCHEMA.md
- _agents/agents.json
- _agents/reload_agents.py
- _agents/agents/adversary/agent.json
- _agents/agents/adversary/config.yaml
- _agents/agents/architect/agent.json
- _agents/agents/architect/config.yaml
- _agents/agents/codesigner/agent.json
- _agents/agents/codesigner/config.yaml
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
generated_at_ref: 703d472a00754a21da89f8b7ca2cde038b89e5b3
generated_at: 2026-05-06T21:04:02Z
links_to:
- topic-workflow-orchestration
- entity-agent-config
- mod-harness-core
covers:
- heading:Agent Config Schema
- key:defaultAgent
- key:agents
- fn:reload_agents
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
---

The agent configuration system provides a centralized mechanism for defining specialized AI agents with distinct roles, capabilities, and behavioral configurations. This system enables workflow orchestration by allowing the harness to dynamically select and configure agents based on task requirements.

## Configuration Architecture

The system uses a two-layer configuration structure:

1. **Agent Metadata** (`agent.json`): Defines agent identity, description, and configuration file references
2. **Behavioral Configuration** (`config.yaml`): Specifies detailed prompt customizations, coding behaviors, and agentic mode settings

This separation allows the harness to quickly enumerate available agents while deferring expensive configuration parsing until agent instantiation. The `_agents/agents.json` file specifies `"defaultAgent": "planner"`, establishing the planner as the primary orchestration entry point.

## Agent Registry and Reload System

The `reload_agents()` function in `_agents/reload_agents.py` implements a build-time configuration compilation process that transforms the source agent definitions into the runtime format expected by the harness. This enables configuration changes to be applied without system restart and maintains separation between development-time configuration and runtime agent instantiation.

The registry pattern in `_agents/agents.json` provides O(1) agent lookup and supports dynamic agent selection based on task characteristics, enabling the [[topic-workflow-orchestration]] system to dispatch work appropriately.

## Specialized Agent Roles

Each agent configuration defines a specific role in the development workflow:

- **Planner**: Primary orchestration agent for task decomposition and workflow coordination
- **Architect**: Deep codebase analysis and system-wide dependency mapping
- **Codesigner**: Adversarial design validation and technical approach hardening  
- **Implementer**: TDD execution and production code changes
- **Reviewer**: Code quality assessment and standards enforcement
- **Verifier**: Final QA, edge-case testing, and robustness verification
- **Adversary**: Hyper-skeptical validation agent for critical path verification

This role specialization prevents capability dilution and ensures each agent's prompt engineering is optimized for its specific function in the development pipeline.

## Configuration Schema Structure

Each `config.yaml` follows the schema documented in [[entity-agent-config]]:

```yaml
coding_agent: # Core behavioral settings
agentic_mode: # Autonomous operation parameters  
prompt_section_customization: # Context injection points
customization_config: # Role-specific behavior tuning
```

The `prompt_section_customization` key enables surgical modification of specific prompt sections without full prompt rewriting, while `customization_config` provides agent-specific behavioral parameters that influence decision-making heuristics.

## Integration with Core Harness

The configuration system integrates with [[mod-harness-core]] through the agent factory pattern, where configurations are lazy-loaded during agent instantiation rather than system startup. This design reduces memory footprint and enables configuration hot-reloading during development.

The `configPath.relativePathToConfig` pattern in agent metadata enables flexible configuration file organization while maintaining predictable resolution semantics for the harness loader.

## Cross-Agent Communication Protocol

Agent configurations include communication protocols that enable the [[topic-workflow-orchestration]] system to coordinate multi-agent workflows. The `agentic_mode` settings control how agents handle handoffs, context preservation, and result validation when participating in multi-step processes.
