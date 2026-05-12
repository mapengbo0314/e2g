---
id: entity-agent-config
title: Agent Configuration Schema
page_type: entity
source_files:
- _agents/agents/config-schema.md
- _agents/GEMINI.md
generated_at_ref: b341f91c9dedfba9ea77683443093879cad39600
generated_at: 2026-05-12T23:04:50Z
links_to:
- harnessdiscovery_enginepy
- harnessminting_enginepy
covers: []
contradictions:
- description: Wiki stated agent configurations are located in _agents/agents/ but the directory has been removed and replaced by boilerplate-agent/ templates and minted .gemini/ locations.
  source: 'Structural Diff: Removed Files / _agents/agents/'
  detected_at: 2026-05-12T23:04:50Z
- description: Wiki claimed a transition to a 'unified markdown-based system' replacing JSON, but the system now uses boilerplate-agent/skills.json and boilerplate-agent/onboarding/tools.json for metadata.
  source: 'Structural Diff: Added Files / boilerplate-agent/skills.json'
  detected_at: 2026-05-12T23:04:50Z
---

# Agent Configuration Schema

The agent configuration schema defines the standardized structure for configuring AI agents within the E2G harness system. This schema has evolved from a complex JSON-based format to a hybrid system that combines markdown-based behavioral instructions with JSON-based capability registries, prioritizing both human readability and automated discovery.

## Current Configuration Format

The system utilizes a **hybrid markdown and JSON configuration system**. Agent behaviors and identity are defined in structured markdown documents, while metadata and tool registries are managed via JSON.

**New Structure**: Agent templates are primarily located in `boilerplate-agent/agents/` and are minted into the project's active agent directory (typically `.gemini/agents/`) during workspace setup. Each agent definition combines:
- **Markdown behavioral instructions**: Behavioral mandates, constraints, and personas.
- **JSON Metadata**: Capability registries like `skills.json` and `tools.json` (located in `boilerplate-agent/`) that define the available toolsets and skills for the agents.
- **Dynamic Routing**: Integration rules injected directly into `dispatch_rules.md` during the minting process.

This represents a shift from the temporary `_agents/` directory (now removed) to a more permanent template-to-workspace minting lifecycle.

## Schema Design Evolution

The schema design has transitioned from **composability over inheritance** to **synthesis-driven configuration**. 

**Synthesized Agents**: The system now supports the dynamic creation of **Domain SME Agents**. Using the [[harness/discovery_engine.py]] and [[harness/minting_engine.py]], the harness can analyze project context to synthesize specialized agents that didn't exist in the templates.

**Type Safety and Routing**: The system has moved away from static `agent_type` discriminators. Instead, the [[harness/minting_engine.py]] uses `patch_orchestrator_rules()` to dynamically inject "Domain Specific Routing" instructions into the workspace's dispatch rules, enabling the Orchestrator to route tasks to these newly minted agents based on their documented mandates.

## Configuration Discovery and Validation

The configuration lifecycle now involves several automated phases:

- **Discovery**: `discover_custom_agent()` uses LLM-based analysis to identify required specialized roles based on project context.
- **Synthesis**: `synthesize_domain_sme_agent()` generates the necessary markdown and metadata for these roles.
- **Tool Mapping**: `parse_tool_checklists()` extracts required tools and skills from domain documentation to populate the agent's environment.
- **Injection**: The Minting Engine automatically updates `dispatch_rules.md` to include routing for synthesized agents, ensuring they are active participants in the Hub-and-Spoke model.

## Integration Points

Agent configurations are tightly integrated into the workspace via the following mechanisms:

- **Minting Engine**: Handles `install_workspace_tools()` to provision the agent's environment based on discovered needs.
- **Orchestrator Rules**: The `patch_orchestrator_rules()` function ensures that any minted or synthesized agent is properly registered in the central `dispatch_rules.md`.
- **Skills & Tools Registry**: `skills.json` and `tools.json` provide a structured manifest of capabilities that agents can invoke, bridging the gap between markdown instructions and executable code.

The configuration system now acts as a **dynamic contract** that is generated and updated as the project's Domain-Driven Design (DDD) context evolves.
