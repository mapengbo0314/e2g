# Codebase Index: e-2-g

> Generated: 2026-05-08 19:45:03 UTC | Files: 85 | Lines: 8268
> Languages: JSON (3), Markdown (71), Python (8), Shell (1), TOML (1), YAML (1)

## Directory Structure

```
e-2-g/
  ARCHITECTURE.md
  GEMINI.md
  INDEX.md
  ONBOARDING_GUIDE.md
  _agents/
    GEMINI.md
    agents/
      adversary.md
      architect.md
      codesigner.md
      config-schema.md
      designdoc-drafter.md
      implementer.md
      planner.md
      reviewer.md
      verifier.md
    agents.json
    reload_agents.py
    rules/
      orchestrator.md
      phases/
        phase_1_design_discussion.md
        phase_2_design_doc.md
        phase_3_goldfish_protocol.md
        phase_4_implementation.md
    skills/
      adk_document_structurer/
        EVAL.yaml
        SKILL.md
        TEST.md
      repo_migration_planner/
        SKILL.md
        references/
          expected_modifications.md
        scripts/
          detect_drift.py
    skills.json
  artifacts/
    agent_format_reference.md
    agent_migration_plan.md
    final_adversarial_report.md
    implementation_plan.md
    implementation_report.md
    implementation_report_v2.md
    verification_report.md
    verification_report_v2.md
  boilerplate-agent/
    AGENTS.md
    agent.json
    agents/
      adversary.md
      architect.md
      codesigner.md
      designdoc-drafter.md
      feature-fetcher.md
      implementer.md
      linter-agent.md
      performance-profiler.md
      planner.md
      refactorer.md
      reviewer.md
      security-auditor.md
      verifier.md
    orchestrator.md
    rules/
      dispatch_rules.md
      unified_superpower_workflow.md
    skills/
      grill-me.md
      grill-with-docs.md
      improve-codebase-architecture.md
  docs/
    superpowers/
      plans/
        2023-10-25-ast-grounded-enrichment.md
        2026-05-06-active-agent-grounding-plan.md
        2026-05-06-harness-redesign.md
        2026-05-06-llm-integration.md
        2026-05-06-skill-enhancement.md
        2026-05-07-harness-pointer-architecture.md
        2026-05-07-integration-fixes-plan.md
        2026-05-07-omni-compatible-finalization-plan.md
        2026-05-07-omni-compatible-refactor-plan.md
        ddd-agent-discovery-plan.md
      specs/
        2024-05-20-sequential-prompter-refactor-design.md
        2024-05-24-tree-sitter-integration-design.md
        2025-05-14-deterministic-grounding-design.md
        2026-05-06-active-agent-grounding-design.md
        2026-05-06-ddd-agent-factory-design.md
        2026-05-06-harness-dynamic-discovery-design.md
        2026-05-06-harness-init-cli-design.md
        2026-05-07-omni-compatible-refactor-design.md
    walkthrough/
      agentic_harness_lifecycle.md
  harness/
    cli.py
    discovery_engine.py
    minting_engine.py
  pyproject.toml
  tests/
    buglogger.md
    test_cli_cleanup.py
    test_discovery_engine.py
    test_minting_engine.py
  update_wiki.sh
```

---

## Public API Surface

**ARCHITECTURE.md**
- `# Superpowers Agentic Harness: Architecture & Workflow`

**INDEX.md**
- `# Codebase Index: e-2-g`

**ONBOARDING_GUIDE.md**
- `# User Guide: Onboarding a New Repository with Harness-WF`
- `# 1. Navigate to your project`
- `# 2. Set your LLM API Key (Indxr uses this to process the code)`
- `# 3. Generate the wiki bundle`
- `# Initialize the harness using Gemini as the orchestrating LLM`
- `# and the existing index for context`

**_agents/GEMINI.md**
- `# General Agent Rules`

**_agents/agents/adversary.md**
- `# Core Mandates`
- `# Core Mandates (Universal Subagent Context)`
- `# Role: Adversary`
- `# Adversary Instructions`
- `# Output Format`

**_agents/agents/architect.md**
- `# Core Mandates`
- `# Core Mandates (Universal Subagent Context)`
- `# Workspace Guidelines`
- `# Skill: Repo Migration Planner`
- `# Role: Architect`
- `# Architect Instructions`
- `# Architect Constraints`
- `# Scratchpad Template`
- `# Scratchpad`
- `# Tool Usage Constraints`
- `# Output Format`

**_agents/agents/codesigner.md**
- `# Core Mandates`
- `# Core Mandates (Universal Subagent Context)`
- `# Role: Codesigner`
- `# Codesigner Instructions`
- `# Tool Usage Constraints`

**_agents/agents/config-schema.md**
- `# Agent Config Schema`

**_agents/agents/designdoc-drafter.md**
- `# Core Mandates`
- `# Core Mandates (Universal Subagent Context)`
- `# Skill: ADK Document Structurer`
- `# Role: Design Doc Drafter`
- `# Design Doc Drafter Instructions`
- `# Design Doc Drafter Constraints`
- `# Examples`
- `# Tool Usage Constraints`

**_agents/agents/implementer.md**
- `# Core Mandates`
- `# Core Mandates (Universal Subagent Context)`
- `# Workspace Guidelines`
- `# Role: Implementer`
- `# Implementer Instructions`
- `# Implementer Constraints`
- `# Scratchpad Template`
- `# Tool Usage Constraints`
- `# Output Format`

**_agents/agents/planner.md**
- `# Core Mandates`
- `# Core Mandates (Universal Subagent Context)`
- `# Workspace Guidelines`
- `# Skill: Repo Migration Planner`
- `# Role: Planner`
- `# Mandates`
- `# Planner Instructions`
- `# Planner Constraints`
- `# Scratchpad Template`
- `# Tool Usage Constraints`
- `# Output Format`

**_agents/agents/reviewer.md**
- `# Core Mandates`
- `# Core Mandates (Universal Subagent Context)`
- `# Workspace Guidelines`
- `# Role: Reviewer`
- `# Reviewer Instructions`
- `# Reviewer Constraints`
- `# Scratchpad Template`
- `# Tool Usage Constraints`
- `# Output Format`

**_agents/agents/verifier.md**
- `# Core Mandates`
- `# Core Mandates (Universal Subagent Context)`
- `# Role: Verifier`
- `# Verifier Goals`
- `# Verifier Constraints`
- `# Verification Focus`
- `# Output Format`

**_agents/agents.json**
- `"defaultAgent": "planner"`
- `"agents": [`

**_agents/reload_agents.py**
- `def reload_agents()`

**_agents/rules/orchestrator.md**
- `# Orchestrator Rules`
- `# Primary Workflows (The Superpower Workflow)`

**_agents/rules/phases/phase_1_design_discussion.md**
- `# Phase 1: The Design Discussion (No Code Yet)`

**_agents/rules/phases/phase_2_design_doc.md**
- `# Phase 2: Writing the Design Doc`

**_agents/rules/phases/phase_3_goldfish_protocol.md**
- `# Phase 3: The "Goldfish" Review Protocol`

**_agents/rules/phases/phase_4_implementation.md**
- `# Phase 4: Implementation & Mean Review`

**_agents/skills/adk_document_structurer/EVAL.yaml**
- `name:`
- `eval_targets:`

**_agents/skills/adk_document_structurer/SKILL.md**
- `# Skill: ADK Document Structurer`

**_agents/skills/adk_document_structurer/TEST.md**
- `# Test Notes`

**_agents/skills/repo_migration_planner/SKILL.md**
- `# Skill: Repo Migration Planner`

**_agents/skills/repo_migration_planner/references/expected_modifications.md**
- `# Expected Modifications`

**_agents/skills/repo_migration_planner/scripts/detect_drift.py**
- `def detect_drift(current_summary: str, target_summary: str) -> bool`

**_agents/skills.json**
- `"skills": [`

**artifacts/agent_format_reference.md**
- `# Agent Format Reference`
- `# Core Mandates`

**artifacts/agent_migration_plan.md**
- `# Agent Migration Plan`

**artifacts/final_adversarial_report.md**
- `# Final Adversarial Verification Report`

**artifacts/implementation_plan.md**
- `# Agent Schema Migration & Cleanup Implementation Plan`
- `# Mocking the cleanup directly for the test`

**artifacts/implementation_report.md**
- `# Implementation Report`

**artifacts/implementation_report_v2.md**
- `# Implementation Report v2: Agent Schema Migration Fixes`

**artifacts/verification_report.md**
- `# Verification Report: Phase 4 Implementation`

**artifacts/verification_report_v2.md**
- `# Verification Report v2: Agent Schema Migration Fixes`

**boilerplate-agent/AGENTS.md**
- `# Agentic Harness Rules`

**boilerplate-agent/agent.json**
- `"name": "orchestrator"`
- `"description": "Senior Project Manager & Router that manages the Hub-and-Spoke model."`
- `"type": "router"`
- `"version": "1.0"`
- `"entrypoint": "rules/dispatch_rules.md"`
- `"skills": [`
- `"related_agents": [`

**boilerplate-agent/agents/adversary.md**
- `# Adversary`

**boilerplate-agent/agents/architect.md**
- `# Architect`
- `# Scratchpad`

**boilerplate-agent/agents/codesigner.md**
- `# Codesigner`

**boilerplate-agent/agents/designdoc-drafter.md**
- `# Design Doc Drafter`

**boilerplate-agent/agents/feature-fetcher.md**
- `# Feature Fetcher`

**boilerplate-agent/agents/implementer.md**
- `# Implementer`

**boilerplate-agent/agents/linter-agent.md**
- `# Linter Agent`

**boilerplate-agent/agents/performance-profiler.md**
- `# Performance Profiler`

**boilerplate-agent/agents/planner.md**
- `# Planner`

**boilerplate-agent/agents/refactorer.md**
- `# Refactorer`

**boilerplate-agent/agents/reviewer.md**
- `# Reviewer`

**boilerplate-agent/agents/security-auditor.md**
- `# Security Auditor`

**boilerplate-agent/agents/verifier.md**
- `# Verifier`

**boilerplate-agent/orchestrator.md**
- `# Orchestrator`

**boilerplate-agent/rules/dispatch_rules.md**
- `# Dispatch Rules`
- `# Primary Workflows (The Phased Goldfish Protocol + Superpowers)`

**boilerplate-agent/rules/unified_superpower_workflow.md**
- `# The Universal Agentic Harness Protocol`

**boilerplate-agent/skills/grill-with-docs.md**
- `## Domain awareness`
- `## During the session`

**boilerplate-agent/skills/improve-codebase-architecture.md**
- `# Improve Codebase Architecture`

**docs/superpowers/plans/2023-10-25-ast-grounded-enrichment.md**
- `# AST-Grounded Enrichment Pipeline Implementation Plan`
- `# tests/test_schema.py`
- `# tests/test_ast_extractor.py`
- `# tests/test_ast_merger.py`

**docs/superpowers/plans/2026-05-06-active-agent-grounding-plan.md**
- `# Active Agent Grounding Implementation Plan`
- `# OLD`
- `# Load the full brain from the generated markdown file`
- `# NEW`
- `# Load the full brain from the generated markdown file`
- `# OLD`
- `# NEW`

**docs/superpowers/plans/2026-05-06-harness-redesign.md**
- `# Harness Dynamic Discovery Redesign Implementation Plan`
- `# 1. Platform Specific Extension/Skill Installation`
- `# 2. Install indxr MCP Server`
- `# 3. Existing Wiki Detected`
- `# 3. Generate initial Codebase Wiki`

**docs/superpowers/plans/2026-05-06-llm-integration.md**
- `# Real LLM Integration & DDD Alignment Plan`

**docs/superpowers/plans/2026-05-06-skill-enhancement.md**
- `# Engineering Skills Integration Plan`

**docs/superpowers/plans/2026-05-07-harness-pointer-architecture.md**
- `# Harness Pointer Architecture Implementation Plan`
- `# Agentic Harness Rules`
- `# Replace the old logic in harness/minting_engine.py (around lines 193-211)`
- `# Pattern to remove the entire block related to urllib and downloading skills`
- `# Create a python script to do the string replacement safely`
- `# Pattern to find the old rules generation block`
- `# The new logic generating the pointer`
- `# Create a python script to safely update the setup_content string in minting_engine.py`
- `# Find the end of the existing setup script generation block`
- `# The new logic to append to the setup script`
- `# 4. Generate Native Skill Pointers`
- `# Source skills directory`

**docs/superpowers/plans/2026-05-07-integration-fixes-plan.md**
- `# Integration Fixes Implementation Plan`
- `# Replace _agents/skills with the dynamic target path name`
- `# Replace the agent loading loop`

**docs/superpowers/plans/2026-05-07-omni-compatible-finalization-plan.md**
- `# Omni-Compatible Finalization Plan`
- `# Replace everything from setup_script_path = ... down to os.chmod`
- `# MCP Configuration for Claude`
- `# Replace the loop under `# Generate Specialized Agents``

**docs/superpowers/plans/2026-05-07-omni-compatible-refactor-plan.md**
- `# Omni-Compatible Refactor Implementation Plan`

**docs/superpowers/plans/ddd-agent-discovery-plan.md**
- `# DDD Agent Discovery Integration Plan`

**docs/superpowers/specs/2024-05-20-sequential-prompter-refactor-design.md**
- `# Sequential LLM Prompter Refactor Design`

**docs/superpowers/specs/2024-05-24-tree-sitter-integration-design.md**
- `# Tree-sitter Integration and Private Symbol Indexing Design`

**docs/superpowers/specs/2025-05-14-deterministic-grounding-design.md**
- `# Deterministic Injection and Metadata Extraction Design`

**docs/superpowers/specs/2026-05-06-active-agent-grounding-design.md**
- `# Design Document: Active Agent Grounding`

**docs/superpowers/specs/2026-05-06-ddd-agent-factory-design.md**
- `# Design Document: DDD Agent Factory Integration (`harness init --ddd`)`

**docs/superpowers/specs/2026-05-06-harness-dynamic-discovery-design.md**
- `# Design Document: Harness Initialization & Dynamic Discovery Redesign`

**docs/superpowers/specs/2026-05-06-harness-init-cli-design.md**
- `# Design Document: Harness Initialization CLI (`harness init`)`

**docs/superpowers/specs/2026-05-07-omni-compatible-refactor-design.md**
- `# Omni-Compatible Refactor Design Spec`

**docs/walkthrough/agentic_harness_lifecycle.md**
- `# The Universal Agentic Harness Lifecycle`

**harness/cli.py**
- `def parse_args()`
- `def run_ddd_grill(ddd_context: dict) -> dict`
- `def main()`

**harness/discovery_engine.py**
- `def acquire_mcp_context(project_path: str) -> str`
- `def fetch_remote_skill(skill_url: str) -> str`
- `def query_llm(prompt: str, llm_provider: str, api_key: str, model: str = None) -> str`
- `def discover_agents(context_str: str, feature_fetcher_yaml_path: str, llm_provider: str, api_key: str, model: str = None, ddd_context: dict = None) -> list[dict]`
- `def discover_ddd_context(context_str: str, llm_provider: str, api_key: str, model: str = None) -> dict`

**harness/minting_engine.py**
- `def mint_workspace(target_dir: str, selected_agents: list[dict], project_path: str, platform_choice: str, model_choice: str = None, bundle_override: str = None, boilerplate_dir: str = None, ddd_context: dict = None)`

**pyproject.toml**
- `[build-system]`
- `[project]`
- `[project.scripts]`
- `[tool.setuptools.packages.find]`

**tests/buglogger.md**
- `# E2G Indexing Pipeline Bug Log`

**tests/test_cli_cleanup.py**
- `def cleanup_other_platforms(project_path, chosen_platform)`
- `def test_cleanup_other_platforms()`

**tests/test_discovery_engine.py**
- `@mock.patch("harness.discovery_engine.fetch_remote_skill") @mock.patch("harness.discovery_engine.query_llm") def test_discover_agents(mock_query_llm, mock_fetch_skill)`
- `@mock.patch("harness.discovery_engine.fetch_remote_skill") @mock.patch("harness.discovery_engine.query_llm") def test_discover_agents_with_ddd_context(mock_query_llm, mock_fetch_skill)`
- `@mock.patch("harness.discovery_engine.fetch_remote_skill") @mock.patch("harness.discovery_engine.query_llm") def test_discover_ddd_context(mock_query_llm, mock_fetch_skill)`

**tests/test_minting_engine.py**
- `def test_mint_workspace_agent_naming()`

**update_wiki.sh**
- `export ANTHROPIC_API_KEY="$1"`

---

## ARCHITECTURE.md

**Language:** Markdown | **Size:** 3.8 KB | **Lines:** 69

**Declarations:**

---

## GEMINI.md

**Language:** Markdown | **Size:** 16 B | **Lines:** 1

---

## INDEX.md

**Language:** Markdown | **Size:** 24.4 KB | **Lines:** 1140

**Declarations:**

---

## ONBOARDING_GUIDE.md

**Language:** Markdown | **Size:** 4.9 KB | **Lines:** 103

**Declarations:**

---

## _agents/GEMINI.md

**Language:** Markdown | **Size:** 1.7 KB | **Lines:** 44

**Declarations:**

---

## _agents/agents/adversary.md

**Language:** Markdown | **Size:** 2.2 KB | **Lines:** 36

**Declarations:**

---

## _agents/agents/architect.md

**Language:** Markdown | **Size:** 6.1 KB | **Lines:** 99

**Declarations:**

---

## _agents/agents/codesigner.md

**Language:** Markdown | **Size:** 4.1 KB | **Lines:** 40

**Declarations:**

---

## _agents/agents/config-schema.md

**Language:** Markdown | **Size:** 1.0 KB | **Lines:** 50

**Declarations:**

---

## _agents/agents/designdoc-drafter.md

**Language:** Markdown | **Size:** 5.3 KB | **Lines:** 70

**Declarations:**

---

## _agents/agents/implementer.md

**Language:** Markdown | **Size:** 4.4 KB | **Lines:** 77

**Declarations:**

---

## _agents/agents/planner.md

**Language:** Markdown | **Size:** 5.2 KB | **Lines:** 109

**Declarations:**

---

## _agents/agents/reviewer.md

**Language:** Markdown | **Size:** 4.5 KB | **Lines:** 87

**Declarations:**

---

## _agents/agents/verifier.md

**Language:** Markdown | **Size:** 2.2 KB | **Lines:** 39

**Declarations:**

---

## _agents/agents.json

**Language:** JSON | **Size:** 176 B | **Lines:** 12

**Declarations:**

---

## _agents/reload_agents.py

**Language:** Python | **Size:** 5.0 KB | **Lines:** 115

**Imports:**
- `import os`
- `import json`
- `import yaml`

**Declarations:**

---

## _agents/rules/orchestrator.md

**Language:** Markdown | **Size:** 9.4 KB | **Lines:** 120

**Declarations:**

---

## _agents/rules/phases/phase_1_design_discussion.md

**Language:** Markdown | **Size:** 1.8 KB | **Lines:** 28

**Declarations:**

---

## _agents/rules/phases/phase_2_design_doc.md

**Language:** Markdown | **Size:** 3.5 KB | **Lines:** 66

**Declarations:**

---

## _agents/rules/phases/phase_3_goldfish_protocol.md

**Language:** Markdown | **Size:** 3.6 KB | **Lines:** 52

**Declarations:**

---

## _agents/rules/phases/phase_4_implementation.md

**Language:** Markdown | **Size:** 889 B | **Lines:** 15

**Declarations:**

---

## _agents/skills/adk_document_structurer/EVAL.yaml

**Language:** YAML | **Size:** 142 B | **Lines:** 5

**Declarations:**

---

## _agents/skills/adk_document_structurer/SKILL.md

**Language:** Markdown | **Size:** 232 B | **Lines:** 13

**Declarations:**

---

## _agents/skills/adk_document_structurer/TEST.md

**Language:** Markdown | **Size:** 189 B | **Lines:** 8

**Declarations:**

---

## _agents/skills/repo_migration_planner/SKILL.md

**Language:** Markdown | **Size:** 261 B | **Lines:** 13

**Declarations:**

---

## _agents/skills/repo_migration_planner/references/expected_modifications.md

**Language:** Markdown | **Size:** 204 B | **Lines:** 6

**Declarations:**

---

## _agents/skills/repo_migration_planner/scripts/detect_drift.py

**Language:** Python | **Size:** 199 B | **Lines:** 5

**Declarations:**

---

## _agents/skills.json

**Language:** JSON | **Size:** 82 B | **Lines:** 6

**Declarations:**

---

## artifacts/agent_format_reference.md

**Language:** Markdown | **Size:** 1.9 KB | **Lines:** 42

**Declarations:**

---

## artifacts/agent_migration_plan.md

**Language:** Markdown | **Size:** 4.0 KB | **Lines:** 118

**Declarations:**

---

## artifacts/final_adversarial_report.md

**Language:** Markdown | **Size:** 1.7 KB | **Lines:** 31

**Declarations:**

---

## artifacts/implementation_plan.md

**Language:** Markdown | **Size:** 7.4 KB | **Lines:** 231

**Declarations:**

---

## artifacts/implementation_report.md

**Language:** Markdown | **Size:** 1.8 KB | **Lines:** 23

**Declarations:**

---

## artifacts/implementation_report_v2.md

**Language:** Markdown | **Size:** 2.7 KB | **Lines:** 30

**Declarations:**

---

## artifacts/verification_report.md

**Language:** Markdown | **Size:** 2.0 KB | **Lines:** 22

**Declarations:**

---

## artifacts/verification_report_v2.md

**Language:** Markdown | **Size:** 2.5 KB | **Lines:** 31

**Declarations:**

---

## boilerplate-agent/AGENTS.md

**Language:** Markdown | **Size:** 1.7 KB | **Lines:** 27

**Declarations:**

---

## boilerplate-agent/agent.json

**Language:** JSON | **Size:** 536 B | **Lines:** 25

**Declarations:**

---

## boilerplate-agent/agents/adversary.md

**Language:** Markdown | **Size:** 3.6 KB | **Lines:** 69

**Declarations:**

---

## boilerplate-agent/agents/architect.md

**Language:** Markdown | **Size:** 6.4 KB | **Lines:** 110

**Declarations:**

---

## boilerplate-agent/agents/codesigner.md

**Language:** Markdown | **Size:** 5.5 KB | **Lines:** 76

**Declarations:**

---

## boilerplate-agent/agents/designdoc-drafter.md

**Language:** Markdown | **Size:** 6.1 KB | **Lines:** 99

**Declarations:**

---

## boilerplate-agent/agents/feature-fetcher.md

**Language:** Markdown | **Size:** 2.2 KB | **Lines:** 48

**Declarations:**

---

## boilerplate-agent/agents/implementer.md

**Language:** Markdown | **Size:** 5.9 KB | **Lines:** 121

**Declarations:**

---

## boilerplate-agent/agents/linter-agent.md

**Language:** Markdown | **Size:** 1.3 KB | **Lines:** 40

**Declarations:**

---

## boilerplate-agent/agents/performance-profiler.md

**Language:** Markdown | **Size:** 1.5 KB | **Lines:** 42

**Declarations:**

---

## boilerplate-agent/agents/planner.md

**Language:** Markdown | **Size:** 6.5 KB | **Lines:** 147

**Declarations:**

---

## boilerplate-agent/agents/refactorer.md

**Language:** Markdown | **Size:** 1.6 KB | **Lines:** 48

**Declarations:**

---

## boilerplate-agent/agents/reviewer.md

**Language:** Markdown | **Size:** 5.3 KB | **Lines:** 118

**Declarations:**

---

## boilerplate-agent/agents/security-auditor.md

**Language:** Markdown | **Size:** 1.5 KB | **Lines:** 44

**Declarations:**

---

## boilerplate-agent/agents/verifier.md

**Language:** Markdown | **Size:** 3.4 KB | **Lines:** 75

**Declarations:**

---

## boilerplate-agent/orchestrator.md

**Language:** Markdown | **Size:** 3.1 KB | **Lines:** 57

**Declarations:**

---

## boilerplate-agent/rules/dispatch_rules.md

**Language:** Markdown | **Size:** 10.6 KB | **Lines:** 142

**Declarations:**

---

## boilerplate-agent/rules/unified_superpower_workflow.md

**Language:** Markdown | **Size:** 5.2 KB | **Lines:** 77

**Declarations:**

---

## boilerplate-agent/skills/grill-me.md

**Language:** Markdown | **Size:** 635 B | **Lines:** 10

---

## boilerplate-agent/skills/grill-with-docs.md

**Language:** Markdown | **Size:** 3.5 KB | **Lines:** 88

**Declarations:**

---

## boilerplate-agent/skills/improve-codebase-architecture.md

**Language:** Markdown | **Size:** 5.0 KB | **Lines:** 71

**Declarations:**

---

## docs/superpowers/plans/2023-10-25-ast-grounded-enrichment.md

**Language:** Markdown | **Size:** 9.7 KB | **Lines:** 270

**Declarations:**

---

## docs/superpowers/plans/2026-05-06-active-agent-grounding-plan.md

**Language:** Markdown | **Size:** 4.6 KB | **Lines:** 131

**Declarations:**

---

## docs/superpowers/plans/2026-05-06-harness-redesign.md

**Language:** Markdown | **Size:** 20.9 KB | **Lines:** 572

**Declarations:**

---

## docs/superpowers/plans/2026-05-06-llm-integration.md

**Language:** Markdown | **Size:** 10.5 KB | **Lines:** 280

**Declarations:**

---

## docs/superpowers/plans/2026-05-06-skill-enhancement.md

**Language:** Markdown | **Size:** 6.1 KB | **Lines:** 142

**Declarations:**

---

## docs/superpowers/plans/2026-05-07-harness-pointer-architecture.md

**Language:** Markdown | **Size:** 9.4 KB | **Lines:** 247

**Declarations:**

---

## docs/superpowers/plans/2026-05-07-integration-fixes-plan.md

**Language:** Markdown | **Size:** 8.4 KB | **Lines:** 202

**Declarations:**

---

## docs/superpowers/plans/2026-05-07-omni-compatible-finalization-plan.md

**Language:** Markdown | **Size:** 8.5 KB | **Lines:** 233

**Declarations:**

---

## docs/superpowers/plans/2026-05-07-omni-compatible-refactor-plan.md

**Language:** Markdown | **Size:** 4.4 KB | **Lines:** 117

**Declarations:**

---

## docs/superpowers/plans/ddd-agent-discovery-plan.md

**Language:** Markdown | **Size:** 6.2 KB | **Lines:** 145

**Declarations:**

---

## docs/superpowers/specs/2024-05-20-sequential-prompter-refactor-design.md

**Language:** Markdown | **Size:** 5.4 KB | **Lines:** 82

**Declarations:**

---

## docs/superpowers/specs/2024-05-24-tree-sitter-integration-design.md

**Language:** Markdown | **Size:** 4.3 KB | **Lines:** 61

**Declarations:**

---

## docs/superpowers/specs/2025-05-14-deterministic-grounding-design.md

**Language:** Markdown | **Size:** 3.2 KB | **Lines:** 67

**Declarations:**

---

## docs/superpowers/specs/2026-05-06-active-agent-grounding-design.md

**Language:** Markdown | **Size:** 2.1 KB | **Lines:** 36

**Declarations:**

---

## docs/superpowers/specs/2026-05-06-ddd-agent-factory-design.md

**Language:** Markdown | **Size:** 3.4 KB | **Lines:** 53

**Declarations:**

---

## docs/superpowers/specs/2026-05-06-harness-dynamic-discovery-design.md

**Language:** Markdown | **Size:** 4.2 KB | **Lines:** 49

**Declarations:**

---

## docs/superpowers/specs/2026-05-06-harness-init-cli-design.md

**Language:** Markdown | **Size:** 3.6 KB | **Lines:** 61

**Declarations:**

---

## docs/superpowers/specs/2026-05-07-omni-compatible-refactor-design.md

**Language:** Markdown | **Size:** 3.1 KB | **Lines:** 45

**Declarations:**

---

## docs/walkthrough/agentic_harness_lifecycle.md

**Language:** Markdown | **Size:** 8.4 KB | **Lines:** 144

**Declarations:**

---

## harness/cli.py

**Language:** Python | **Size:** 5.1 KB | **Lines:** 127

**Imports:**
- `import argparse`
- `import sys`
- `import getpass`
- `import os`
- `import tempfile`
- `import subprocess`
- `import shutil`

**Declarations:**

---

## harness/discovery_engine.py

**Language:** Python | **Size:** 9.2 KB | **Lines:** 194

**Imports:**
- `import json`
- `import subprocess`
- `import time`
- `import urllib.request`
- `import os`

**Declarations:**

---

## harness/minting_engine.py

**Language:** Python | **Size:** 9.9 KB | **Lines:** 244

**Imports:**
- `import os`
- `import re`
- `import shutil`
- `import json`
- `from pathlib import Path`

**Declarations:**

---

## pyproject.toml

**Language:** TOML | **Size:** 412 B | **Lines:** 20

**Declarations:**

---

## tests/buglogger.md

**Language:** Markdown | **Size:** 7.4 KB | **Lines:** 94

**Declarations:**

---

## tests/test_cli_cleanup.py

**Language:** Python | **Size:** 1.2 KB | **Lines:** 38

**Imports:**
- `import os`
- `import tempfile`
- `import pytest`
- `import shutil`

**Declarations:**

---

## tests/test_discovery_engine.py

**Language:** Python | **Size:** 2.5 KB | **Lines:** 71

**Imports:**
- `import pytest`
- `from unittest import mock`
- `from harness.discovery_engine import discover_agents, discover_ddd_context`

**Declarations:**

---

## tests/test_minting_engine.py

**Language:** Python | **Size:** 1.6 KB | **Lines:** 49

**Imports:**
- `import pytest`
- `import shutil`
- `import tempfile`
- `from pathlib import Path`
- `import os`
- `from harness.minting_engine import mint_workspace`

**Declarations:**

---

## update_wiki.sh

**Language:** Shell | **Size:** 80 B | **Lines:** 4

**Declarations:**

