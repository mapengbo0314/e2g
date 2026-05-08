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
generated_at_ref: f1af3b2fa46c98c92658d870947ac03b9020de8a
generated_at: 2026-05-08T19:40:40Z
links_to:
- entity-agent-config
- mod-harness-core
- topic-workflow-orchestration
covers:
- heading:Agent Config Schema
- key:defaultAgent
- key:agents
- fn:reload_agents
contradictions:
- description: Wiki previously described a two-layer JSON/YAML configuration structure (agent.json + config.yaml) but the system has migrated to single Markdown files
  source: _agents/agents/config-schema.md
  detected_at: 2026-05-08T19:40:40Z
- description: Wiki stated configurations follow a specific YAML schema but agents are now defined in Markdown format
  source: _agents/agents/*.md files
  detected_at: 2026-05-08T19:40:40Z
---

# Agent Configuration System

The agent configuration system provides a centralized mechanism for defining specialized AI agents with distinct roles, capabilities, and behavioral configurations. This system enables workflow orchestration by allowing the harness to dynamically select and configure agents based on task requirements.

## Configuration Architecture

**MAJOR ARCHITECTURAL CHANGE**: The system has migrated from a two-layer JSON/YAML configuration structure to a Markdown-based agent definition format. This represents a fundamental shift in how agents are configured and managed.

### New Agent Definition Format

Agent configurations are now stored as standalone Markdown files in `_agents/agents/`, replacing the previous `agent.json` + `config.yaml` pattern. Each agent is defined in a single `.md` file (e.g., `planner.md`, `architect.md`) that contains structured agent specifications in a human-readable format.

### Registry Structure

The `_agents/agents.json` file continues to specify `"defaultAgent": "planner"`, establishing the planner as the primary orchestration entry point, but now references the new Markdown-based agent definitions.

## Agent Registry and Reload System

The `reload_agents()` function in `_agents/reload_agents.py` has been updated to handle the new Markdown-based configuration format. This build-time configuration compilation process transforms the source agent definitions into the runtime format expected by the harness, maintaining the ability to apply configuration changes without system restart.

The function now processes Markdown agent definitions instead of JSON/YAML configurations, enabling more flexible and maintainable agent specifications while preserving the separation between development-time configuration and runtime agent instantiation.

## Specialized Agent Roles

The system maintains the same specialized agent roles, now defined in Markdown format:

- **Planner**: Primary orchestration agent for task decomposition and workflow coordination
- **Architect**: Deep codebase analysis and system-wide dependency mapping
- **Codesigner**: Adversarial design validation and technical approach hardening  
- **Implementer**: TDD execution and production code changes
- **Reviewer**: Code quality assessment and standards enforcement
- **Verifier**: Final QA, edge-case testing, and robustness verification
- **Adversary**: Hyper-skeptical validation agent for critical path verification
- **Designdoc-drafter**: Documentation and specification generation (new addition)

This role specialization continues to prevent capability dilution and ensures each agent's prompt engineering is optimized for its specific function in the development pipeline.

## Configuration Schema Structure

The new configuration schema is documented in [[entity-agent-config]] and follows a Markdown-based structure that replaces the previous YAML format:

- Agent metadata and behavioral settings are embedded within structured Markdown
- Prompt customizations are integrated directly into the agent definition
- Role-specific behavior tuning is handled through the Markdown specification format

The schema documentation in `_agents/agents/config-schema.md` explains the rationale: "Why it looks like this" - indicating the new format was designed for improved maintainability and human readability compared to the previous JSON/YAML approach.

## Integration with Core Harness

The configuration system continues to integrate with [[mod-harness-core]] through the agent factory pattern, with configurations lazy-loaded during agent instantiation. The migration to Markdown-based definitions maintains the reduced memory footprint and configuration hot-reloading capabilities while improving the developer experience for agent configuration management.

## Boilerplate Integration

A new boilerplate agent system has been introduced in `boilerplate-agent/`, providing template configurations and standardized agent definitions that can be used as starting points for custom agent development. This includes comprehensive agent templates and supporting infrastructure.

## Cross-Agent Communication Protocol

Agent configurations continue to include communication protocols that enable the [[topic-workflow-orchestration]] system to coordinate multi-agent workflows. The new Markdown format preserves the ability to specify how agents handle handoffs, context preservation, and result validation when participating in multi-step processes.
