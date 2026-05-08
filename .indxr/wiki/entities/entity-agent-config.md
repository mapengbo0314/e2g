---
id: entity-agent-config
title: Agent Configuration Schema
page_type: entity
source_files:
- _agents/agents/config-schema.md
- _agents/GEMINI.md
generated_at_ref: 703d472a00754a21da89f8b7ca2cde038b89e5b3
generated_at: 2026-05-06T21:04:02Z
links_to:
- mod-skills
- mod-agents
- topic-workflow-orchestration
- mod-documentation
covers:
- heading:Agent Config Schema
- heading:General Agent Rules
---

The agent configuration schema defines the standardized structure for configuring AI agents within the E2G harness system. This schema enforces consistency across all agent types while providing the flexibility needed for different agent specializations and use cases.

## Configuration Structure

The configuration schema follows a layered approach with three primary sections that separate concerns between identity, capabilities, and runtime behavior:

**Identity Layer** (`agent_type`, `name`, `description`): Defines what the agent is and its purpose within the system. The `agent_type` field determines which agent class will be instantiated, while `name` and `description` provide human-readable identification for logging and debugging.

**Capabilities Layer** (`skills`, `tools`, `knowledge_base`): Specifies what the agent can do. The `skills` array references entries from the [[mod-skills]] system, `tools` defines available external integrations, and `knowledge_base` points to specialized domain knowledge.

**Runtime Layer** (`config`, `environment`, `constraints`): Controls how the agent behaves during execution. This includes LLM parameters, resource limits, and behavioral constraints that govern the agent's decision-making process.

## Schema Design Rationale

The schema design prioritizes **composability over inheritance** to avoid the complexity of deeply nested configuration hierarchies. Each agent configuration is self-contained, making it easier to reason about agent behavior and troubleshoot issues in production.

**Type Safety**: The `agent_type` field serves as a discriminator that determines which configuration subset is valid. This prevents mismatched configurations where an agent receives parameters it cannot interpret.

**Environment Separation**: The `environment` section isolates deployment-specific settings (API keys, endpoints, resource limits) from logical configuration, enabling the same agent definition to work across development, staging, and production environments.

**Extensibility**: New agent types can be added without modifying existing configurations, as the schema uses a flexible key-value structure within each section while maintaining type safety at the agent level.

## Configuration Validation

The schema enforces several invariants that prevent common configuration errors:

- Required fields must be present for the specified `agent_type`
- Skill references must exist in the skills registry (validated by [[mod-skills]])
- Resource constraints must be positive values within system limits
- Tool configurations must match the expected interface contracts

## Integration Points

Agent configurations integrate with several system components:

- **Agent Factory** ([[mod-agents]]): Uses `agent_type` to instantiate the correct agent class
- **Skills System** ([[mod-skills]]): Validates and loads referenced skills
- **Workflow Engine** ([[topic-workflow-orchestration]]): Consumes agent metadata for task routing
- **Documentation System** ([[mod-documentation]]): Generates agent inventories from configuration metadata

The configuration schema serves as the contract between the declarative agent definitions and the runtime system, ensuring that agents are properly initialized with all required capabilities and constraints.
