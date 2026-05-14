---
id: index
title: Wiki Index
page_type: index
source_files: []
generated_at_ref: b29a3ffd2cf37a1a0c14e3c142224bee9fdd325d
generated_at: 2026-05-14T04:26:21Z
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
- [[architecture]] — High-level overview of the e-2-g codebase index and the Universal Agentic Harness Lifecycle.

## Modules
- [[mod-agents]] — Configuration system for managing and defining agent behavior.
- [[mod-boilerplate-agent]] — Standardized metadata and property definitions (skills, entrypoints) for boilerplate agents.
- [[mod-documentation]] — Technical specs for AST-grounded enrichment, Tree-sitter integration, and the `harness init` CLI.
- [[mod-harness-core]] — Core implementation of CLI parsing, agent/DDD discovery, and workspace minting.
- [[mod-skills]] — System for fetching and managing remote and local skills.
- [[mod-testing]] — Testing infrastructure, unit tests for the discovery engine, and indexing pipeline bug logs.

## Topics
- [[topic-workflow-orchestration]] — Deep dive into phase management and the orchestration of agent workflows.

---

## Quick Reference
- **To understand the system lifecycle or main entry point** → [[architecture]]
- **To modify CLI arguments or agent discovery logic** → [[mod-harness-core]]
- **To adjust agent metadata or boilerplate structures** → [[mod-boilerplate-agent]]
- **To research technical designs (AST, Tree-sitter, Injection)** → [[mod-documentation]]
- **To debug orchestration phases or workflow transitions** → [[topic-workflow-orchestration]]
- **To view known bugs or unit test coverage** → [[mod-testing]]
