---
id: mod-demos
title: Demo Scripts and Examples
page_type: module
source_files:
- boilerplate-agent/demo_feature_fetcher.sh
generated_at_ref: f1af3b2fa46c98c92658d870947ac03b9020de8a
generated_at: 2026-05-08T19:40:40Z
links_to:
- mod-documentation
- mod-testing
- entity-agent-config
covers: []
contradictions:
- description: Wiki stated demo scripts were shell-based located in boilerplate-agent/demo_feature_fetcher.sh, but this file has been removed
  source: boilerplate-agent/demo_feature_fetcher.sh
  detected_at: 2026-05-08T19:40:40Z
---

# Demo Scripts and Examples

The demos module provides practical examples and testing scripts for validating E2G system functionality through real-world scenarios. These scripts serve as both integration tests and reference implementations for common agentic workflows.

## Agent Configuration Repository

The module now contains comprehensive agent configuration files in Markdown format, located in `boilerplate-agent/agents/`. These configurations define specialized agents for different aspects of software development:

### Core Development Agents
- **feature-fetcher**: Analyzes codebases and extracts feature requirements
- **implementer**: Handles code implementation tasks
- **planner**: Creates development plans and task breakdowns  
- **reviewer**: Performs code reviews and quality assessments
- **verifier**: Validates implementations against requirements

### Architecture and Design Agents
- **architect**: Designs system architecture and technical specifications
- **designdoc-drafter**: Creates comprehensive design documentation

### Quality Assurance Agents
- **adversary**: Performs adversarial testing and edge case analysis
- **linter-agent**: Enforces code style and quality standards
- **security-auditor**: Conducts security assessments
- **performance-profiler**: Analyzes and optimizes performance
- **refactorer**: Handles code refactoring and improvements

## Orchestration and Skills Framework

### Central Orchestrator
The `boilerplate-agent/orchestrator.md` defines the central coordination logic for multi-agent workflows, managing agent dispatch and task coordination.

### Core Mandates and Rules
- **Core Mandates** (`boilerplate-agent/rules/core_mandates.md`): Fundamental operational principles
- **Dispatch Rules** (`boilerplate-agent/rules/dispatch_rules.md`): Agent selection and task routing logic

### Specialized Skills
- **grill-me**: Interactive questioning and requirement gathering
- **grill-with-docs**: Documentation-assisted requirement analysis  
- **improve-codebase-architecture**: Architectural improvement workflows

## Domain-Driven Design Integration

The system now includes comprehensive Domain-Driven Design (DDD) capabilities through:

### Enhanced Discovery Engine
- **DDD Context Discovery**: `discover_ddd_context()` function extracts domain models and bounded contexts
- **Custom Agent Discovery**: `discover_custom_agent()` creates specialized agents based on domain requirements
- **MCP Context Acquisition**: `acquire_mcp_context()` integrates with Model Context Protocol

### CLI Integration
- **DDD Grilling**: `run_ddd_grill()` function enables interactive domain analysis sessions
- Enhanced agent discovery with domain context awareness

## Advanced Configuration System

### Flexible Agent Definitions
Agent configurations have migrated from JSON/YAML to Markdown format, providing:
- Human-readable specifications
- Rich documentation capabilities
- Version control friendly format
- Easier collaborative editing

### Dynamic Workspace Minting
The minting engine now supports:
- Model choice selection
- Bundle overrides for custom configurations
- Boilerplate directory customization
- Domain context integration

## Testing and Validation Infrastructure

### Comprehensive Test Coverage
New test modules validate:
- **CLI Cleanup**: `test_cli_cleanup.py` ensures proper resource cleanup
- **Core Mandates**: `test_core_mandates_presence.py` validates rule presence
- **Minting Engine**: `test_minting_engine.py` tests workspace generation

### Enhanced Discovery Testing
Discovery engine tests now cover:
- DDD context discovery workflows
- Custom agent creation scenarios
- Remote skill fetching capabilities
- Integration with domain models

## Integration with Core Systems

The demo system maintains its integration patterns while adding new capabilities:

- **Agent Configuration**: Now uses Markdown-based definitions for improved maintainability
- **Workflow Orchestration**: Enhanced with DDD-aware dispatch rules and domain context
- **Skills Integration**: Expanded with specialized domain analysis capabilities
- **Documentation System**: Agent specifications serve as living documentation

### Relationship to Other Components

The demos continue to serve as living documentation for the [[mod-documentation]] system while adding domain-driven examples. They complement the [[mod-testing]] infrastructure with new integration tests for DDD workflows and custom agent discovery.

The enhanced agent configurations demonstrate advanced [[entity-agent-config]] patterns, showing how domain context influences agent behavior and specialization.
