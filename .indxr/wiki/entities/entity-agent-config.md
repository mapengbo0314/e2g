---
id: entity-agent-config
title: Agent Configuration Schema
page_type: entity
source_files:
- _agents/agents/config-schema.md
- _agents/GEMINI.md
generated_at_ref: f1af3b2fa46c98c92658d870947ac03b9020de8a
generated_at: 2026-05-08T19:40:40Z
links_to:
- harnessdiscovery_enginepy
- mod-harness-core
- topic-workflow-orchestration
- mod-skills
covers:
- heading:Agent Config Schema
- heading:General Agent Rules
contradictions:
- description: Wiki described JSON/YAML dual-format configuration system but code now uses markdown-based configuration files
  source: _agents/agents/config-schema.md
  detected_at: 2026-05-08T19:40:40Z
---

# Agent Configuration Schema

The agent configuration schema defines the standardized structure for configuring AI agents within the E2G harness system. This schema has evolved from a complex JSON-based format to a simplified markdown-based configuration system that prioritizes clarity and maintainability.

## Current Configuration Format

The system has transitioned from the previous JSON/YAML dual-format approach to a **unified markdown-based configuration system**. Agent configurations are now defined as structured markdown documents located in `_agents/agents/` directories, with each agent having its own `.md` file containing both configuration and documentation.

**New Structure**: Each agent configuration follows a standardized markdown format that combines:
- Agent metadata and capabilities
- Behavioral instructions and constraints  
- Integration specifications with other system components
- Human-readable documentation within the same file

This represents a significant departure from the previous layered approach of separate JSON schema files, YAML configurations, and external documentation.

## Schema Design Evolution

The schema design has shifted from **composability over inheritance** to **documentation-driven configuration**. The new approach embeds configuration directly within markdown documentation, making agent behavior and capabilities self-documenting.

**Simplified Structure**: The complex three-layer system (Identity, Capabilities, Runtime) has been replaced with a more streamlined approach where agent definitions are human-readable markdown that can be directly processed by LLMs without intermediate parsing layers.

**Type Safety**: Instead of using `agent_type` discriminators and complex validation rules, the system now relies on consistent markdown formatting and agent discovery mechanisms that can dynamically understand agent capabilities from their documentation.

## Configuration Discovery and Validation

The new system employs **dynamic discovery** rather than static schema validation:

- Agent configurations are discovered through filesystem scanning of markdown files
- Capabilities are inferred from the markdown content structure
- Integration points are established through cross-references within the documentation
- Domain-Driven Design (DDD) context influences agent discovery and configuration

The [[harness/discovery_engine.py]] module now handles `discover_ddd_context()` and `discover_custom_agent()` functions that can dynamically generate agent configurations based on project context rather than requiring pre-defined schemas.

## Integration Points

Agent configurations integrate with system components differently than before:

- **Discovery Engine** ([[mod-harness-core]]): Uses markdown parsing and LLM analysis to understand agent capabilities
- **Minting Engine**: Generates workspace configurations from discovered agent specifications
- **Workflow Engine** ([[topic-workflow-orchestration]]): Consumes agent metadata directly from markdown documentation
- **Skills System** ([[mod-skills]]): References skills through markdown cross-links rather than registry lookups

The configuration system now serves as a **living documentation contract** that combines human-readable specifications with machine-processable agent definitions, enabling more flexible and maintainable agent lifecycle management.
