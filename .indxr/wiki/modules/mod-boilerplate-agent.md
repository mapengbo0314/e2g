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
generated_at_ref: f1af3b2fa46c98c92658d870947ac03b9020de8a
generated_at: 2026-05-08T19:40:40Z
links_to:
- mod-harness-core
- topic-workflow-orchestration
covers:
- key:name
- key:description
- key:type
- key:version
- key:entrypoint
- key:skills
- key:related_agents
contradictions:
- description: Wiki stated agents were organized into core/ and discovery/ domains with JSON configs, but agents are now stored as Markdown files in a flat structure
  source: boilerplate-agent/agents/*.md
  detected_at: 2026-05-08T19:40:40Z
- description: 'Wiki stated router uses ''type: router'' to indicate orchestration role, but now uses ''entrypoint: rules/dispatch_rules.md'' for rule-based dispatch'
  source: boilerplate-agent/agent.json:5
  detected_at: 2026-05-08T19:40:40Z
- description: 'Wiki stated core agents use ''coding_agent: true'' in config files, but these config files no longer exist'
  source: boilerplate-agent/agents/core/*/config.yaml removed
  detected_at: 2026-05-08T19:40:40Z
- description: Wiki stated deployment scripts were in scripts/ directory, but these have been removed
  source: boilerplate-agent/scripts/ removed
  detected_at: 2026-05-08T19:40:40Z
---

# Boilerplate Agent System

The Boilerplate Agent System provides a reference implementation of a hierarchical agent orchestration pattern using the [[mod-harness-core]] framework. This system demonstrates the hub-and-spoke architecture where a router agent coordinates specialized sub-agents.

## Architecture

The system has undergone a **major architectural transformation** from the traditional hierarchical agent structure to a dynamic, Domain-Driven Design (DDD) approach:

### New Dynamic Architecture

1. **Router Layer**: The `orchestrator` agent (`agent.json:2`) acts as the entry point, managing delegation based on dispatch rules
2. **Dynamic Discovery**: Agents are now discovered and minted on-demand using DDD principles and contextual analysis
3. **Rule-Based Dispatch**: The router uses `"entrypoint": "rules/dispatch_rules.md"` (`agent.json:5`) instead of static domain organization

### Agent Discovery and Minting

The system now features:
- **DDD Context Discovery**: Automatic analysis of project domains using `discover_ddd_context()` (`discovery_engine.py:65`)
- **Custom Agent Generation**: Dynamic agent creation via `discover_custom_agent()` (`discovery_engine.py:43`) 
- **Remote Skills Integration**: Dynamic skill fetching with `fetch_remote_skill()` (`discovery_engine.py:23`)
- **Enhanced Minting**: Workspace creation with DDD context integration (`minting_engine.py:7`)

## Agent Definitions

Agents are now defined as Markdown documentation rather than JSON configurations:

### Core Execution Agents
- **planner**: Strategic planning and task breakdown (`boilerplate-agent/agents/planner.md`)
- **implementer**: Code generation and modification (`boilerplate-agent/agents/implementer.md`)
- **reviewer**: Code quality assessment (`boilerplate-agent/agents/reviewer.md`)
- **verifier**: QA and testing validation (`boilerplate-agent/agents/verifier.md`)

### Discovery and Analysis Agents
- **architect**: Codebase analysis and system design (`boilerplate-agent/agents/architect.md`)
- **codesigner**: Collaborative design partner (`boilerplate-agent/agents/codesigner.md`)
- **designdoc-drafter**: Technical documentation (`boilerplate-agent/agents/designdoc-drafter.md`)
- **adversary**: Critical validation and skeptical review (`boilerplate-agent/agents/adversary.md`)

### Specialized Domain Agents
- **feature-fetcher**: Dynamic agent discovery and proposal (`boilerplate-agent/agents/feature-fetcher.md`)
- **linter-agent**: Code quality enforcement (`boilerplate-agent/agents/linter-agent.md`)
- **security-auditor**: Security analysis (`boilerplate-agent/agents/security-auditor.md`)
- **performance-profiler**: Performance optimization (`boilerplate-agent/agents/performance-profiler.md`)
- **refactorer**: Code restructuring (`boilerplate-agent/agents/refactorer.md`)

## Configuration System

The configuration approach has been completely redesigned:

### Rule-Based Configuration
- **Core Mandates**: Fundamental operational rules (`boilerplate-agent/rules/core_mandates.md`)
- **Dispatch Rules**: Agent routing and delegation logic (`boilerplate-agent/rules/dispatch_rules.md`)
- **Unified Workflows**: Comprehensive workflow patterns with DDD integration (`boilerplate-agent/rules/unified_superpower_workflow.md:44`)

### Skills Integration
The system now includes sophisticated skill modules:
- **grill-me**: Interactive validation (`boilerplate-agent/skills/grill-me.md`)
- **grill-with-docs**: Documentation-aware analysis (`boilerplate-agent/skills/grill-with-docs.md`)
- **improve-codebase-architecture**: Architectural enhancement (`boilerplate-agent/skills/improve-codebase-architecture.md`)

## Enhanced Discovery Engine

The discovery system has been significantly enhanced:

- **Context Acquisition**: MCP-based context gathering (`discovery_engine.py:35`)
- **Model Flexibility**: Support for multiple LLM models (`discovery_engine.py:76`)
- **DDD Grilling**: Interactive domain analysis via CLI (`cli.py:45`)

## Design Principles

The evolved system emphasizes:

1. **Dynamic Adaptation**: Agents are discovered and created based on actual project needs
2. **Domain-Driven Organization**: Structure follows business domains rather than technical layers
3. **Rule-Based Orchestration**: Behavior is governed by explicit rules rather than hardcoded logic
4. **Skills Modularity**: Reusable capabilities that can be combined dynamically
5. **Context Awareness**: Deep integration with project context and documentation

This transformation represents a shift from static agent hierarchies to a dynamic, context-aware orchestration system that adapts to project requirements in real-time. See [[topic-workflow-orchestration]] for details on how the new rule-based system coordinates agent interactions.
