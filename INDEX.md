# Codebase Index: e-2-g

> Generated: 2026-05-06 20:59:19 UTC | Files: 78 | Lines: 6042
> Languages: JSON (20), Markdown (23), Python (12), Shell (4), YAML (19)

## Directory Structure

```
e-2-g/
  INDEX.md
  _agents/
    GEMINI.md
    agents/
      CONFIG_SCHEMA.md
      adversary/
        agent.json
        config.yaml
      architect/
        agent.json
        config.yaml
      codesigner/
        agent.json
        config.yaml
      designdoc_drafter/
        agent.json
        config.yaml
      implementer/
        agent.json
        config.yaml
      planner/
        agent.json
        config.yaml
      reviewer/
        agent.json
        config.yaml
      verifier/
        agent.json
        config.yaml
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
  boilerplate-agent/
    agent.json
    agents/
      core/
        implementer/
          agent.json
          config.yaml
        planner/
          agent.json
          config.yaml
        reviewer/
          agent.json
          config.yaml
        verifier/
          agent.json
          config.yaml
      discovery/
        adversary/
          agent.json
          config.yaml
        architect/
          agent.json
          config.yaml
        codesigner/
          agent.json
          config.yaml
        designdoc_drafter/
          agent.json
          config.yaml
        feature-fetcher/
          agent.json
          config.yaml
    config.yaml
    demo_feature_fetcher.sh
    rules/
      orchestrator.md
      unified_superpower_workflow.md
    scripts/
      clone_harness.py
      clone_harness.sh
      setup_harness.sh
    skills/
      harness-workflow/
        SKILL.md
        verify_tdd_gate.sh
  docs/
    superpowers/
      plans/
        2023-10-25-ast-grounded-enrichment.md
        2026-05-06-harness-init-cli-plan.md
      specs/
        2024-05-20-sequential-prompter-refactor-design.md
        2024-05-24-tree-sitter-integration-design.md
        2025-05-14-deterministic-grounding-design.md
        2026-05-06-harness-init-cli-design.md
    walkthrough/
      agentic_harness_lifecycle.md
  harness/
    cli.py
    discovery_engine.py
    indexer_wrapper.py
    indexing/
      main.py
    minting_engine.py
  test_freshness.py
  tests/
    buglogger.md
    test_cli_preflight.py
    test_context_acquisition.py
    test_discovery_engine.py
```

---

## Public API Surface

**INDEX.md**
- `# Codebase Index: e-2-g`

**_agents/GEMINI.md**
- `# General Agent Rules`

**_agents/agents/CONFIG_SCHEMA.md**
- `# Agent Config Schema`

**_agents/agents/adversary/agent.json**
- `"name": "adversary"`
- `"description": "An adversarial agent that is hyper-skeptical, factual, and strictly avoids hallucination or flattery."`

**_agents/agents/adversary/config.yaml**
- `coding_agent:`
- `agentic_mode:`
- `prompt_section_customization:`
- `customization_config:`

**_agents/agents/architect/agent.json**
- `"name": "architect"`
- `"description": "The specialized tool for codebase analysis, architectural mapping, and understanding system-wide dependencies. Invoke this tool for tasks like vague requests, bug root-cause analysis, system refactoring, comprehensive feature implementation, or to answer questions about the codebase that require investigation."`
- `"configPath": {`

**_agents/agents/architect/config.yaml**
- `coding_agent:`
- `agentic_mode:`
- `prompt_section_customization:`
- `customization_config:`

**_agents/agents/codesigner/agent.json**
- `"name": "codesigner"`
- `"description": "Specialized sub-agent that acts as an adversarial design partner to harden technical approaches and generate a design handoff."`
- `"configPath": {`

**_agents/agents/codesigner/config.yaml**
- `coding_agent:`
- `agentic_mode:`
- `prompt_section_customization:`
- `customization_config:`

**_agents/agents/designdoc_drafter/agent.json**
- `"name": "designdoc_drafter"`
- `"description": "Specialized sub-agent that documents technical designs and performs an impact audit.\n"`
- `"configPath": {`

**_agents/agents/designdoc_drafter/config.yaml**
- `coding_agent:`
- `agentic_mode:`
- `prompt_section_customization:`
- `customization_config:`

**_agents/agents/implementer/agent.json**
- `"name": "implementer"`
- `"description": "The specialized tool for TDD execution and production code changes. Delegate to this sub-agent for implementation tasks."`
- `"configPath": {`

**_agents/agents/implementer/config.yaml**
- `coding_agent:`
- `agentic_mode:`
- `prompt_section_customization:`
- `customization_config:`

**_agents/agents/planner/agent.json**
- `"name": "planner"`
- `"description": "The specialized tool for breaking down a design into a detailed, step-by-step plan before execution."`
- `"configPath": {`

**_agents/agents/planner/config.yaml**
- `coding_agent:`
- `agentic_mode:`
- `prompt_section_customization:`
- `customization_config:`

**_agents/agents/reviewer/agent.json**
- `"name": "reviewer"`
- `"description": "Senior Software Engineer for identifying issues and ensuring high standards in the codebase."`
- `"configPath": {`

**_agents/agents/reviewer/config.yaml**
- `coding_agent:`
- `agentic_mode:`
- `prompt_section_customization:`
- `customization_config:`

**_agents/agents/verifier/agent.json**
- `"name": "verifier"`
- `"description": "The specialized tool for final QA, edge-case testing, transcript fidelity checks, and robustness verification."`
- `"configPath": {`

**_agents/agents/verifier/config.yaml**
- `coding_agent:`
- `agentic_mode:`
- `prompt_section_customization:`
- `customization_config:`

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

**boilerplate-agent/agent.json**
- `"name": "orchestrator"`
- `"description": "Senior Project Manager & Router that manages the Hub-and-Spoke model."`
- `"type": "router"`
- `"version": "1.0"`
- `"entrypoint": "config.yaml"`

**boilerplate-agent/agents/core/implementer/agent.json**
- `"name": "implementer"`
- `"description": "The specialized tool for TDD execution and production code changes. Delegate to this sub-agent for implementation tasks."`
- `"configPath": {`

**boilerplate-agent/agents/core/implementer/config.yaml**
- `coding_agent:`
- `agentic_mode:`
- `prompt_section_customization:`
- `customization_config:`

**boilerplate-agent/agents/core/planner/agent.json**
- `"name": "planner"`
- `"description": "The specialized tool for breaking down a design into a detailed, step-by-step plan before execution."`
- `"configPath": {`

**boilerplate-agent/agents/core/planner/config.yaml**
- `coding_agent:`
- `agentic_mode:`
- `prompt_section_customization:`
- `customization_config:`

**boilerplate-agent/agents/core/reviewer/agent.json**
- `"name": "reviewer"`
- `"description": "Senior Software Engineer for identifying issues and ensuring high standards in the codebase."`
- `"configPath": {`

**boilerplate-agent/agents/core/reviewer/config.yaml**
- `coding_agent:`
- `agentic_mode:`
- `prompt_section_customization:`
- `customization_config:`

**boilerplate-agent/agents/core/verifier/agent.json**
- `"name": "verifier"`
- `"description": "The specialized tool for final QA, edge-case testing, transcript fidelity checks, and robustness verification."`
- `"configPath": {`

**boilerplate-agent/agents/core/verifier/config.yaml**
- `coding_agent:`
- `agentic_mode:`
- `prompt_section_customization:`
- `customization_config:`

**boilerplate-agent/agents/discovery/adversary/agent.json**
- `"name": "adversary"`
- `"description": "An adversarial agent that is hyper-skeptical, factual, and strictly avoids hallucination or flattery."`

**boilerplate-agent/agents/discovery/adversary/config.yaml**
- `coding_agent:`
- `agentic_mode:`
- `prompt_section_customization:`
- `customization_config:`

**boilerplate-agent/agents/discovery/architect/agent.json**
- `"name": "architect"`
- `"description": "The specialized tool for codebase analysis, architectural mapping, and understanding system-wide dependencies. Invoke this tool for tasks like vague requests, bug root-cause analysis, system refactoring, comprehensive feature implementation, or to answer questions about the codebase that require investigation."`
- `"configPath": {`

**boilerplate-agent/agents/discovery/architect/config.yaml**
- `coding_agent:`
- `agentic_mode:`
- `prompt_section_customization:`
- `customization_config:`

**boilerplate-agent/agents/discovery/codesigner/agent.json**
- `"name": "codesigner"`
- `"description": "Specialized sub-agent that acts as an adversarial design partner to harden technical approaches and generate a design handoff."`
- `"configPath": {`

**boilerplate-agent/agents/discovery/codesigner/config.yaml**
- `coding_agent:`
- `agentic_mode:`
- `prompt_section_customization:`
- `customization_config:`

**boilerplate-agent/agents/discovery/designdoc_drafter/agent.json**
- `"name": "designdoc_drafter"`
- `"description": "Specialized sub-agent that documents technical designs and performs an impact audit.\n"`
- `"configPath": {`

**boilerplate-agent/agents/discovery/designdoc_drafter/config.yaml**
- `coding_agent:`
- `agentic_mode:`
- `prompt_section_customization:`
- `customization_config:`

**boilerplate-agent/agents/discovery/feature-fetcher/agent.json**
- `"name": "feature-fetcher"`
- `"description": "The Agent Factory: Analyzes indices and proposes specialized domain agents for SME approval."`
- `"type": "discovery"`
- `"version": "1.0"`
- `"entrypoint": "config.yaml"`

**boilerplate-agent/agents/discovery/feature-fetcher/config.yaml**
- `system_prompt:`

**boilerplate-agent/config.yaml**
- `system_prompt:`

**boilerplate-agent/rules/orchestrator.md**
- `# Orchestrator Rules`
- `# Primary Workflows (The Phased Goldfish Protocol + Superpowers)`

**boilerplate-agent/rules/unified_superpower_workflow.md**
- `# The Universal Agentic Harness Protocol`

**boilerplate-agent/scripts/clone_harness.py**
- `def main()`

**boilerplate-agent/skills/harness-workflow/SKILL.md**
- `# Harness Workflow`

**docs/superpowers/plans/2023-10-25-ast-grounded-enrichment.md**
- `# AST-Grounded Enrichment Pipeline Implementation Plan`
- `# tests/test_schema.py`
- `# tests/test_ast_extractor.py`
- `# tests/test_ast_merger.py`

**docs/superpowers/plans/2026-05-06-harness-init-cli-plan.md**
- `# Harness Init CLI Implementation Plan`
- `# ... after api key check ...`
- `# ... after context acquisition ...`
- `# ... after discovery ...`
- `# 1. Platform Specific Extension/Skill Installation`
- `# 2. Install indxr MCP Server`
- `# ... after HITL selection ...`

**docs/superpowers/specs/2024-05-20-sequential-prompter-refactor-design.md**
- `# Sequential LLM Prompter Refactor Design`

**docs/superpowers/specs/2024-05-24-tree-sitter-integration-design.md**
- `# Tree-sitter Integration and Private Symbol Indexing Design`

**docs/superpowers/specs/2025-05-14-deterministic-grounding-design.md**
- `# Deterministic Injection and Metadata Extraction Design`

**docs/superpowers/specs/2026-05-06-harness-init-cli-design.md**
- `# Design Document: Harness Initialization CLI (`harness init`)`

**docs/walkthrough/agentic_harness_lifecycle.md**
- `# The Universal Agentic Harness Lifecycle`

**harness/cli.py**
- `def parse_args()`
- `def main()`

**harness/discovery_engine.py**
- `def query_llm(prompt: str, llm_provider: str, api_key: str) -> str`
- `def prune_context(index_data: dict) -> dict`
- `def discover_agents(index_data: dict, llm_provider: str, api_key: str) -> list[dict]`

**harness/indexer_wrapper.py**
- `def check_indxr_installed() -> bool`
- `def acquire_context(project_path: str, bundle_override: str | None = None) -> str`

**harness/indexing/main.py**
- `def run_reindex(index_dir: str)`

**harness/minting_engine.py**
- `def mint_workspace(target_dir: str, selected_agents: list[dict], project_path: str, platform_choice: str)`

**tests/buglogger.md**
- `# E2G Indexing Pipeline Bug Log`

**tests/test_cli_preflight.py**
- `def test_check_indxr_installed_fails_when_missing()`
- `def test_check_indxr_installed_passes_when_present()`

**tests/test_context_acquisition.py**
- `@mock.patch("subprocess.run") def test_acquire_context_generates_metadata(mock_run, tmp_path)`

**tests/test_discovery_engine.py**
- `@mock.patch("harness.discovery_engine.query_llm") def test_discover_agents(mock_query_llm)`

---

## INDEX.md

**Language:** Markdown | **Size:** 24.3 KB | **Lines:** 1128

**Declarations:**

---

## _agents/GEMINI.md

**Language:** Markdown | **Size:** 1.7 KB | **Lines:** 44

**Declarations:**

---

## _agents/agents/CONFIG_SCHEMA.md

**Language:** Markdown | **Size:** 1.0 KB | **Lines:** 50

**Declarations:**

---

## _agents/agents/adversary/agent.json

**Language:** JSON | **Size:** 148 B | **Lines:** 4

**Declarations:**

---

## _agents/agents/adversary/config.yaml

**Language:** YAML | **Size:** 2.9 KB | **Lines:** 51

**Declarations:**

---

## _agents/agents/architect/agent.json

**Language:** JSON | **Size:** 423 B | **Lines:** 7

**Declarations:**

---

## _agents/agents/architect/config.yaml

**Language:** YAML | **Size:** 7.5 KB | **Lines:** 122

**Declarations:**

---

## _agents/agents/codesigner/agent.json

**Language:** JSON | **Size:** 239 B | **Lines:** 7

**Declarations:**

---

## _agents/agents/codesigner/config.yaml

**Language:** YAML | **Size:** 4.8 KB | **Lines:** 55

**Declarations:**

---

## _agents/agents/designdoc_drafter/agent.json

**Language:** JSON | **Size:** 206 B | **Lines:** 7

**Declarations:**

---

## _agents/agents/designdoc_drafter/config.yaml

**Language:** YAML | **Size:** 6.5 KB | **Lines:** 91

**Declarations:**

---

## _agents/agents/implementer/agent.json

**Language:** JSON | **Size:** 234 B | **Lines:** 7

**Declarations:**

---

## _agents/agents/implementer/config.yaml

**Language:** YAML | **Size:** 5.8 KB | **Lines:** 100

**Declarations:**

---

## _agents/agents/planner/agent.json

**Language:** JSON | **Size:** 210 B | **Lines:** 7

**Declarations:**

---

## _agents/agents/planner/config.yaml

**Language:** YAML | **Size:** 7.0 KB | **Lines:** 136

**Declarations:**

---

## _agents/agents/reviewer/agent.json

**Language:** JSON | **Size:** 203 B | **Lines:** 7

**Declarations:**

---

## _agents/agents/reviewer/config.yaml

**Language:** YAML | **Size:** 5.9 KB | **Lines:** 110

**Declarations:**

---

## _agents/agents/verifier/agent.json

**Language:** JSON | **Size:** 221 B | **Lines:** 7

**Declarations:**

---

## _agents/agents/verifier/config.yaml

**Language:** YAML | **Size:** 3.0 KB | **Lines:** 58

**Declarations:**

---

## _agents/agents.json

**Language:** JSON | **Size:** 176 B | **Lines:** 12

**Declarations:**

---

## _agents/reload_agents.py

**Language:** Python | **Size:** 3.5 KB | **Lines:** 90

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

## boilerplate-agent/agent.json

**Language:** JSON | **Size:** 189 B | **Lines:** 7

**Declarations:**

---

## boilerplate-agent/agents/core/implementer/agent.json

**Language:** JSON | **Size:** 234 B | **Lines:** 7

**Declarations:**

---

## boilerplate-agent/agents/core/implementer/config.yaml

**Language:** YAML | **Size:** 7.0 KB | **Lines:** 195

**Declarations:**

---

## boilerplate-agent/agents/core/planner/agent.json

**Language:** JSON | **Size:** 210 B | **Lines:** 7

**Declarations:**

---

## boilerplate-agent/agents/core/planner/config.yaml

**Language:** YAML | **Size:** 8.1 KB | **Lines:** 261

**Declarations:**

---

## boilerplate-agent/agents/core/reviewer/agent.json

**Language:** JSON | **Size:** 203 B | **Lines:** 7

**Declarations:**

---

## boilerplate-agent/agents/core/reviewer/config.yaml

**Language:** YAML | **Size:** 6.7 KB | **Lines:** 212

**Declarations:**

---

## boilerplate-agent/agents/core/verifier/agent.json

**Language:** JSON | **Size:** 221 B | **Lines:** 7

**Declarations:**

---

## boilerplate-agent/agents/core/verifier/config.yaml

**Language:** YAML | **Size:** 4.1 KB | **Lines:** 115

**Declarations:**

---

## boilerplate-agent/agents/discovery/adversary/agent.json

**Language:** JSON | **Size:** 148 B | **Lines:** 4

**Declarations:**

---

## boilerplate-agent/agents/discovery/adversary/config.yaml

**Language:** YAML | **Size:** 3.7 KB | **Lines:** 89

**Declarations:**

---

## boilerplate-agent/agents/discovery/architect/agent.json

**Language:** JSON | **Size:** 423 B | **Lines:** 7

**Declarations:**

---

## boilerplate-agent/agents/discovery/architect/config.yaml

**Language:** YAML | **Size:** 8.4 KB | **Lines:** 242

**Declarations:**

---

## boilerplate-agent/agents/discovery/codesigner/agent.json

**Language:** JSON | **Size:** 239 B | **Lines:** 7

**Declarations:**

---

## boilerplate-agent/agents/discovery/codesigner/config.yaml

**Language:** YAML | **Size:** 6.1 KB | **Lines:** 139

**Declarations:**

---

## boilerplate-agent/agents/discovery/designdoc_drafter/agent.json

**Language:** JSON | **Size:** 206 B | **Lines:** 7

**Declarations:**

---

## boilerplate-agent/agents/discovery/designdoc_drafter/config.yaml

**Language:** YAML | **Size:** 7.5 KB | **Lines:** 170

**Declarations:**

---

## boilerplate-agent/agents/discovery/feature-fetcher/agent.json

**Language:** JSON | **Size:** 218 B | **Lines:** 7

**Declarations:**

---

## boilerplate-agent/agents/discovery/feature-fetcher/config.yaml

**Language:** YAML | **Size:** 1.7 KB | **Lines:** 20

**Declarations:**

---

## boilerplate-agent/config.yaml

**Language:** YAML | **Size:** 1.5 KB | **Lines:** 18

**Declarations:**

---

## boilerplate-agent/demo_feature_fetcher.sh

**Language:** Shell | **Size:** 1.3 KB | **Lines:** 29

---

## boilerplate-agent/rules/orchestrator.md

**Language:** Markdown | **Size:** 10.8 KB | **Lines:** 142

**Declarations:**

---

## boilerplate-agent/rules/unified_superpower_workflow.md

**Language:** Markdown | **Size:** 4.9 KB | **Lines:** 74

**Declarations:**

---

## boilerplate-agent/scripts/clone_harness.py

**Language:** Python | **Size:** 3.0 KB | **Lines:** 86

**Imports:**
- `import os`
- `import sys`
- `import shutil`
- `import argparse`
- `from pathlib import Path`

**Declarations:**

---

## boilerplate-agent/scripts/clone_harness.sh

**Language:** Shell | **Size:** 1.9 KB | **Lines:** 60

---

## boilerplate-agent/scripts/setup_harness.sh

**Language:** Shell | **Size:** 967 B | **Lines:** 28

---

## boilerplate-agent/skills/harness-workflow/SKILL.md

**Language:** Markdown | **Size:** 3.0 KB | **Lines:** 62

**Declarations:**

---

## boilerplate-agent/skills/harness-workflow/verify_tdd_gate.sh

**Language:** Shell | **Size:** 1.6 KB | **Lines:** 41

---

## docs/superpowers/plans/2023-10-25-ast-grounded-enrichment.md

**Language:** Markdown | **Size:** 9.7 KB | **Lines:** 270

**Declarations:**

---

## docs/superpowers/plans/2026-05-06-harness-init-cli-plan.md

**Language:** Markdown | **Size:** 11.6 KB | **Lines:** 346

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

## docs/superpowers/specs/2026-05-06-harness-init-cli-design.md

**Language:** Markdown | **Size:** 3.6 KB | **Lines:** 61

**Declarations:**

---

## docs/walkthrough/agentic_harness_lifecycle.md

**Language:** Markdown | **Size:** 8.4 KB | **Lines:** 144

**Declarations:**

---

## harness/cli.py

**Language:** Python | **Size:** 3.1 KB | **Lines:** 84

**Imports:**
- `import argparse`
- `import sys`
- `import getpass`
- `import os`
- `from harness.indexer_wrapper import check_indxr_installed`

**Declarations:**

---

## harness/discovery_engine.py

**Language:** Python | **Size:** 2.1 KB | **Lines:** 48

**Imports:**
- `import json`
- `import sys`

**Declarations:**

---

## harness/indexer_wrapper.py

**Language:** Python | **Size:** 1.6 KB | **Lines:** 48

**Imports:**
- `import shutil`
- `import sys`
- `import json`
- `import os`
- `import subprocess`
- `import datetime`

**Declarations:**

---

## harness/indexing/main.py

**Language:** Python | **Size:** 1.8 KB | **Lines:** 56

**Imports:**
- `import argparse`
- `import logging`
- `import os`
- `import sys`
- `from indexing import orchestrator`
- `from indexing import llm_indexer`
- `from indexing import planner`
- `from indexing import state`
- `from indexing import work_unit`
- `from indexing.fs_manager import RealFsManager`
- *... and 1 more imports*

**Declarations:**

---

## harness/minting_engine.py

**Language:** Python | **Size:** 5.0 KB | **Lines:** 135

**Imports:**
- `import os`
- `import shutil`
- `import json`
- `from pathlib import Path`

**Declarations:**

---

## test_freshness.py

**Language:** Python | **Size:** 33 B | **Lines:** 2

---

## tests/buglogger.md

**Language:** Markdown | **Size:** 7.4 KB | **Lines:** 94

**Declarations:**

---

## tests/test_cli_preflight.py

**Language:** Python | **Size:** 465 B | **Lines:** 13

**Imports:**
- `import pytest`
- `from unittest import mock`
- `import sys`
- `from harness.indexer_wrapper import check_indxr_installed`

**Declarations:**

---

## tests/test_context_acquisition.py

**Language:** Python | **Size:** 728 B | **Lines:** 23

**Imports:**
- `import json`
- `import os`
- `import pytest`
- `from unittest import mock`
- `from harness.indexer_wrapper import acquire_context`

**Declarations:**

---

## tests/test_discovery_engine.py

**Language:** Python | **Size:** 639 B | **Lines:** 21

**Imports:**
- `import pytest`
- `from unittest import mock`
- `from harness.discovery_engine import discover_agents`

**Declarations:**

