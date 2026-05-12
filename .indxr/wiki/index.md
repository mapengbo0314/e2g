---
id: index
title: Wiki Index
page_type: index
source_files: []
generated_at_ref: b341f91c9dedfba9ea77683443093879cad39600
generated_at: 2026-05-12T23:04:50Z
links_to:
- architecture
- mod-agents
- mod-boilerplate-agent
- mod-harness-core
- mod-skills
- topic-workflow-orchestration
- mod-documentation
- mod-testing
covers: []
---

# Codebase Wiki Index

## Architecture
- [[architecture]] — Architecture Overview: Covers the Universal Agentic Harness Lifecycle, codebase indexing, and core execution flow.

## Modules
- [[mod-agents]] — Agent Configuration System: Details the configuration, discovery, and management of specialized agents.
- [[mod-boilerplate-agent]] — Boilerplate Agent System: Definitions for agent metadata including skills, types, and related agents.
- [[mod-harness-core]] — Core Harness Components: Implementation of discovery engines, tech stack detection, and workspace minting.
- [[mod-skills]] — Skills System: Infrastructure for loading and managing agent capabilities and remote skills.
- [[mod-documentation]] — Technical Documentation: Specifications for AST enrichment, Tree-sitter integration, and indexing pipelines.
- [[mod-testing]] — Testing Infrastructure: Test suites for discovery engines, MCP context acquisition, and harness lifecycle validation.

## Topics
- [[topic-workflow-orchestration]] — Workflow Orchestration: Management of execution phases and the Hub-and-Spoke orchestration model.

## Quick Reference
- **Understand the initialization & lifecycle** → [[architecture]]
- **Modify how agents are discovered** → [[mod-agents]] or [[mod-harness-core]]
- **Create a new agent template** → [[mod-boilerplate-agent]]
- **Develop or integrate new skills** → [[mod-skills]]
- **Review indexing or AST-extraction designs** → [[mod-documentation]]
- **Debug or add new test cases** → [[mod-testing]]
- **Understand phase management & routing** → [[topic-workflow-orchestration]]
