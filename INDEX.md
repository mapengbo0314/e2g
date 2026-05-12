# Codebase Index: e-2-g

> Generated: 2026-05-12 00:35:11 UTC | Files: 117 | Lines: 13962
> Languages: JSON (4), Markdown (92), Python (20), TOML (1)

## Directory Structure

```
e-2-g/
  ARCHITECTURE.md
  GEMINI.md
  INDEX.md
  ONBOARDING_GUIDE.md
  artifacts/
    agent_format_reference.md
    agent_migration_plan.md
    codex_cli_support_plan.md
    final_adversarial_report.md
    implementation_plan.md
    implementation_report.md
    implementation_report_v2.md
    implementation_report_v3.md
    qa_report.md
    tasks.md
    token_optimization_guide.md
    token_optimization_report.md
    tool_injection_plan.md
    tool_registry_expansion_design.md
    tool_registry_expansion_plan.md
    verification_remediation_plan.md
    verification_report.md
    verification_report_v2.md
  boilerplate-agent/
    AGENTS.md
    agent.json
    agents/
      adversary.md
      architect.md
      feature-fetcher.md
      implementer.md
      linter-agent.md
      performance-profiler.md
      planner.md
      refactorer.md
      reviewer.md
      security-auditor.md
      verifier.md
    onboarding/
      tools.json
    orchestrator.md
    rules/
      core_mandates.md
      dispatch_rules.md
    scripts/
      benchmark_efficiency_test.py
    skills/
      ddd-alignment/
        SKILL.md
      fastapi/
        SKILL.md
      grill-me/
        SKILL.md
      grill-with-docs/
        ADR-FORMAT.md
        CONTEXT-FORMAT.md
        SKILL.md
      improve-codebase-architecture/
        INTERFACE-DESIGN.md
        LANGUAGE.md
        SKILL.md
      meta-learning/
        SKILL.md
      nextjs/
        SKILL.md
    skills.json
  docs/
    superpowers/
      plans/
        2023-10-25-ast-grounded-enrichment.md
        2025-01-24-prune-logs-refactor.md
        2026-05-06-active-agent-grounding-plan.md
        2026-05-06-harness-redesign.md
        2026-05-06-llm-integration.md
        2026-05-06-skill-enhancement.md
        2026-05-07-harness-pointer-architecture.md
        2026-05-07-integration-fixes-plan.md
        2026-05-07-omni-compatible-finalization-plan.md
        2026-05-07-omni-compatible-refactor-plan.md
        2026-05-08-benchmark-efficiency-plan.md
        2026-05-08-context-intake-implementation.md
        2026-05-08-enhanced-ddd-discovery.md
        2026-05-08-token-optimization-plan.md
        2026-05-08-token-optimizer-implementation.md
        2026-05-09-bundle-fallback-plan.md
        2026-05-09-ddd-dispatch-rules-injection.md
        2026-05-09-setup-harness-automation-plan.md
        2026-05-10-minting-fixes.md
        2026-05-10-onboarding-reliability-fix.md
        2026-05-10-phased-onboarding-plan.md
        2026-05-10-tool-discovery-plan.md
        2026-05-11-deterministic-tool-onboarding-plan.md
        2026-05-13-create-pruning-utility.md
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
        2026-05-08-benchmark-efficiency-design.md
        2026-05-08-context-intake-design.md
        2026-05-08-token-optimization-design.md
        2026-05-08-token-optimizer-agent-design.md
        2026-05-09-bundle-fallback-design.md
        2026-05-09-setup-harness-automation-design.md
        2026-05-10-phased-onboarding-sme-design.md
        2026-05-10-tool-discovery-design.md
        2026-05-11-deterministic-tool-onboarding-design.md
    walkthrough/
      agentic_harness_lifecycle.md
  harness/
    cli.py
    discovery_engine.py
    minting_engine.py
  pyproject.toml
  run_debug.py
  scripts/
    benchmark_gate.py
    benchmark_hub_vs_spoke.py
    efficiency_suite.py
  skills-lock.json
  tests/
    buglogger.md
    test_cli.py
    test_cli_edge_cases.py
    test_codex_minting.py
    test_core_mandates_presence.py
    test_discovery_engine.py
    test_e2e_flow.py
    test_forced_injection.py
    test_mcp_config.py
    test_minting_engine.py
    test_platform_awareness.py
    test_platform_coexistence.py
    test_strict_generation.py
```

---

## Public API Surface

**ARCHITECTURE.md**
- `# Superpowers Agentic Harness: Architecture & Workflow`

**GEMINI.md**
- `# Agentic Harness`

**INDEX.md**
- `# Codebase Index: e-2-g`

**ONBOARDING_GUIDE.md**
- `# User Guide: Onboarding a New Repository with Harness-WF`
- `# 1. Navigate to your project`
- `# 2. Set your LLM API Key (Indxr uses this to process the code)`
- `# 3. Generate the wiki bundle`
- `# Initialize the harness using Gemini as the orchestrating LLM`
- `# and the existing index for context`

**artifacts/agent_format_reference.md**
- `# Agent Format Reference`
- `# Core Mandates`

**artifacts/agent_migration_plan.md**
- `# Agent Migration Plan`

**artifacts/codex_cli_support_plan.md**
- `# Codex Support Implementation Plan (Revised v2)`

**artifacts/final_adversarial_report.md**
- `# Final Adversarial Report: Installation Failures Diagnosis`

**artifacts/implementation_plan.md**
- `# Implementation Plan: Fix Skill Installation Failures`

**artifacts/implementation_report.md**
- `# Implementation Report`

**artifacts/implementation_report_v2.md**
- `# Implementation Report v2: Agent Schema Migration Fixes`

**artifacts/implementation_report_v3.md**
- `# Codex Support Implementation Report (v3)`

**artifacts/qa_report.md**
- `# QA Report: Onboarding Enhancement Project (`harness/cli.py`)`

**artifacts/tasks.md**
- `# Implementation Tasks: Hardened Context Intake Gate`

**artifacts/token_optimization_guide.md**
- `# Agentic Harness Token Optimization Guide`

**artifacts/token_optimization_report.md**
- `# Token Optimization Report: Agentic Harness CLI`

**artifacts/tool_injection_plan.md**
- `# Deterministic Onboarding Tool Injection Implementation Plan`

**artifacts/tool_registry_expansion_design.md**
- `# Design Spec: Tool Registry Expansion`

**artifacts/tool_registry_expansion_plan.md**
- `# Tool Registry Expansion Implementation Plan`

**artifacts/verification_remediation_plan.md**
- `# Verification & Remediation Report: Discovery & Minting Alignment`

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
- `# Scratchpad`

**boilerplate-agent/agents/refactorer.md**
- `# Refactorer`

**boilerplate-agent/agents/reviewer.md**
- `# Reviewer`
- `# Scratchpad`

**boilerplate-agent/agents/security-auditor.md**
- `# Security Auditor`

**boilerplate-agent/agents/verifier.md**
- `# Verifier`

**boilerplate-agent/onboarding/tools.json**
- `"categories": {`

**boilerplate-agent/orchestrator.md**
- `# Orchestrator`

**boilerplate-agent/rules/core_mandates.md**
- `# Core Mandates (Universal Subagent Context)`

**boilerplate-agent/rules/dispatch_rules.md**
- `# Dispatch Rules`
- `# Primary Workflows (The Phased Goldfish Protocol + Superpowers)`

**boilerplate-agent/scripts/benchmark_efficiency_test.py**
- `def get_client(api_key: str) -> genai.Client`
- `def count_tokens(text: str, model: str = "gemini-1.5-flash") -> int`
- `class CLIRunnerError(Exception)`
- `def run_cli_command(cli_binary: str, args: list[str]) -> str`
- `BASELINE_SINGLE = "Generate a JSON with 10 user objects (id, name, age). Filter those > 18. Output the result."`
- `BASELINE_MULTI = [ "Read the repository and generate a JSON array of 10 mock user objects (id, name, age, active). Return only the JSON.", "Filter the generated users to only include those where age > 18 and active is true.", "Add a new field 'role: admin' to the first two filtered users, and 'role: user' to the rest.", "Format the final processed list into a neat markdown table and write it to output.md." ]`
- `def run_multi_benchmark(tasks: list[str], rules_content: str, harness_dir: Path)`
- `def run_monolith_benchmark(task_prompt: str, rules_content: str, cli_tool: str = "gemini")`
- `def run_harness_benchmark(task_prompt: str, harness_dir: Path, cli_tool: str = "gemini")`
- `def main()`

**boilerplate-agent/skills/ddd-alignment/SKILL.md**
- `# Deterministic DDD Framework`

**boilerplate-agent/skills/fastapi/SKILL.md**
- `# Python FastAPI .cursorrules`
- `# FastAPI best practices`
- `# Folder structure`
- `# Additional instructions`

**boilerplate-agent/skills/grill-with-docs/ADR-FORMAT.md**
- `# ADR Format`
- `# {Short title of the decision}`

**boilerplate-agent/skills/grill-with-docs/CONTEXT-FORMAT.md**
- `# CONTEXT.md Format`
- `# {Context Name}`
- `# Context Map`

**boilerplate-agent/skills/grill-with-docs/SKILL.md**
- `## Domain awareness`
- `## During the session`

**boilerplate-agent/skills/improve-codebase-architecture/INTERFACE-DESIGN.md**
- `# Interface Design`

**boilerplate-agent/skills/improve-codebase-architecture/LANGUAGE.md**
- `# Language`

**boilerplate-agent/skills/improve-codebase-architecture/SKILL.md**
- `# Improve Codebase Architecture`

**boilerplate-agent/skills/meta-learning/SKILL.md**
- `# Meta-Learning Framework`

**boilerplate-agent/skills/nextjs/SKILL.md**
- `# System Prompt: Next.js 14 and Tailwind CSS Code Generation with TypeScript`

**boilerplate-agent/skills.json**
- `"skills": {`

**docs/superpowers/plans/2023-10-25-ast-grounded-enrichment.md**
- `# AST-Grounded Enrichment Pipeline Implementation Plan`
- `# tests/test_schema.py`
- `# tests/test_ast_extractor.py`
- `# tests/test_ast_merger.py`

**docs/superpowers/plans/2025-01-24-prune-logs-refactor.md**
- `# Refactor prune_logs.py and enhance tests Implementation Plan`

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

**docs/superpowers/plans/2026-05-08-benchmark-efficiency-plan.md**
- `# Token Efficiency Benchmark Implementation Plan`

**docs/superpowers/plans/2026-05-08-context-intake-implementation.md**
- `# Hardened Context Intake Gate Implementation Plan`
- `# Context Intake`
- `# In harness/minting_engine.py`
- `# Ensure the skills directory includes context-intake`

**docs/superpowers/plans/2026-05-08-enhanced-ddd-discovery.md**
- `# Enhanced DDD Agent Discovery Implementation Plan`

**docs/superpowers/plans/2026-05-08-token-optimization-plan.md**
- `# Token Optimization via Prompt Deduplication and Context Intake Implementation Plan`
- `# Core Mandates (Universal Subagent Context)`
- `# Workspace Guidelines`

**docs/superpowers/plans/2026-05-08-token-optimizer-implementation.md**
- `# Token Optimizer Agent Implementation Plan`
- `# Token Optimizer Agent`

**docs/superpowers/plans/2026-05-09-bundle-fallback-plan.md**
- `# Bundle Fallback and Generation Implementation Plan`
- `# test_discovery_engine.py (concept, assuming we have tests for this)`

**docs/superpowers/plans/2026-05-09-ddd-dispatch-rules-injection.md**
- `# Implementation Plan: Dynamic Dispatch Rules for DDD Agents`

**docs/superpowers/plans/2026-05-09-setup-harness-automation-plan.md**
- `# Setup Harness Automation Implementation Plan`

**docs/superpowers/plans/2026-05-10-minting-fixes.md**
- `# Tool Minting Fix Implementation Plan`

**docs/superpowers/plans/2026-05-10-onboarding-reliability-fix.md**
- `# Harness Onboarding Reliability Fix Implementation Plan`
- `# Project Onboarding Domain`
- `# Role: Domain Subject Matter Expert`
- `# Core Mandates`
- `# Domain-Specific Invariants (The MOAT)`
- `# Ubiquitous Language (Glossary)`
- `# Operational Instructions`

**docs/superpowers/plans/2026-05-10-phased-onboarding-plan.md**
- `# Phased Onboarding & Domain SME Synthesis Implementation Plan`
- `# In tests/test_discovery_engine.py`
- `# In harness/discovery_engine.py (add to the end of the file)`
- `# In tests/test_minting_engine.py`
- `# In harness/minting_engine.py (add near the top or a suitable location)`
- `# In tests/test_minting_engine.py`
- `# In harness/minting_engine.py`
- `# In tests/test_minting_engine.py`
- `# In harness/minting_engine.py`
- `# In tests/test_cli_flow.py (create if needed)`
- `# Assuming you have an entrypoint function like run_onboarding`
- `# from harness.cli import run_onboarding`
- `# (This test is conceptual and requires knowing the exact cli.py structure.`
- `# The goal is to assert that generate_onboarding -> wait -> synthesize -> patch are called in order).`
- `# In harness/cli.py`
- `# Import the new functions`
- `# from harness.discovery_engine import generate_onboarding_domain_doc`
- `# from harness.minting_engine import wait_for_user_review_and_read_domain, synthesize_domain_sme_agent, patch_orchestrator_rules`
- `# Inside the main flow logic (e.g., after initial discovery, before final minting):`
- `# 1. generate_onboarding_domain_doc(project_path, llm_discovery_summary)`
- `# 2. domain_content = wait_for_user_review_and_read_domain(project_path)`
- `# 3. Proceed with standard minting (copying boilerplate, etc.)`
- `# 4. agent_name = synthesize_domain_sme_agent(target_dir, domain_content, query_llm, llm_provider, api_key)`
- `# 5. patch_orchestrator_rules(target_dir, agent_name)`

**docs/superpowers/plans/2026-05-10-tool-discovery-plan.md**
- `# Workspace-Level Skill & MCP Discovery Implementation Plan`
- `# In tests/test_discovery_engine.py`
- `# In harness/discovery_engine.py`
- `# In tests/test_minting_engine.py`
- `# In harness/minting_engine.py`
- `# In tests/test_minting_engine.py`
- `# In harness/minting_engine.py`
- `# In harness/cli.py`
- `# Import the new functions`
- `# Inside main(), update the generation and minting flow:`

**docs/superpowers/plans/2026-05-11-deterministic-tool-onboarding-plan.md**
- `# Deterministic Onboarding Tool Injection Implementation Plan`

**docs/superpowers/plans/2026-05-13-create-pruning-utility.md**
- `# Create Pruning Utility Implementation Plan`

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

**docs/superpowers/specs/2026-05-08-benchmark-efficiency-design.md**
- `# Token Efficiency Benchmark Utility Design`

**docs/superpowers/specs/2026-05-08-context-intake-design.md**
- `# Design Doc: Hardened Context Intake Gate (In-Memory Compression)`

**docs/superpowers/specs/2026-05-08-token-optimization-design.md**
- `# Token Optimization via Prompt Deduplication and Context Intake`

**docs/superpowers/specs/2026-05-08-token-optimizer-agent-design.md**
- `# Token Optimizer Agent Design`

**docs/superpowers/specs/2026-05-09-bundle-fallback-design.md**
- `# Bundle Fallback and Generation Design`

**docs/superpowers/specs/2026-05-09-setup-harness-automation-design.md**
- `# Setup Harness Automation Design`

**docs/superpowers/specs/2026-05-10-phased-onboarding-sme-design.md**
- `# Design Doc: Phased Onboarding & Domain SME Synthesis`

**docs/superpowers/specs/2026-05-10-tool-discovery-design.md**
- `# Design Doc: Workspace-Level Skill & MCP Discovery`

**docs/superpowers/specs/2026-05-11-deterministic-tool-onboarding-design.md**
- `# Design Spec: Deterministic Onboarding Tool Injection`

**docs/walkthrough/agentic_harness_lifecycle.md**
- `# The Universal Agentic Harness Lifecycle`

**harness/cli.py**
- `def parse_args()`
- `def run_ddd_grill(ddd_context: dict) -> dict`
- `def main()`

**harness/discovery_engine.py**
- `def acquire_mcp_context(project_path: str, bundle_path: str = None, detailed: bool = False) -> str`
- `def fetch_remote_skill(skill_url: str) -> str`
- `def fetch_skill(skill_name: str, remote_url: str) -> str`
- `def query_llm(prompt: str, llm_provider: str, api_key: str, model: str = None) -> str`
- `def discover_agents(context_str: str, feature_fetcher_yaml_path: str, llm_provider: str, api_key: str, model: str = None, ddd_context: dict = None) -> list[dict]`
- `def discover_ddd_context(context_str: str, llm_provider: str, api_key: str, model: str = None) -> dict`
- `def discover_custom_agent(name: str, specs: str, context_str: str, ddd_context: dict, llm_provider: str, api_key: str, model: str = None) -> dict`
- `def detect_tech_stack(project_path: str) -> str`
- `def generate_onboarding_domain_doc(project_path: str, domain_summary: str, query_llm_fn=None, llm_provider=None, api_key=None, context_str="", boilerplate_dir: str = None)`

**harness/minting_engine.py**
- `def parse_tool_checklists(domain_content: str) -> tuple[list[dict], list[dict]]`
- `def wait_for_user_review_and_read_domain(project_path: str) -> str`
- `def process_includes(content: str, current_file_path: str, target_root: Path, tool_replacements: dict, target_dir_name: str, visited: set = None) -> str`
- `def mint_workspace(target_dir: str, selected_agents: list[dict], project_path: str, platform_choice: str, model_choice: str = None, bundle_override: str = None, boilerplate_dir: str = None, ddd_context: dict = None)`
- `def synthesize_domain_sme_agent(target_dir: str, domain_content: str, harness_folder_name: str, platform_choice: str = "1", model_choice: str = None)`
- `def patch_orchestrator_rules(target_dir: str, agent_name: str, harness_folder_name: str, target_syntax: str = "@")`
- `def install_workspace_tools(target_dir: str, harness_folder_name: str, skills: list[dict], mcps: list[dict])`

**pyproject.toml**
- `[build-system]`
- `[project]`
- `[project.scripts]`
- `[tool.setuptools.packages.find]`

**scripts/benchmark_gate.py**
- `def generate_mock_stack_trace()`
- `def get_token_count(text)`
- `def simulate_workflow(use_gate=False)`

**scripts/benchmark_hub_vs_spoke.py**
- `def get_token_count(text)`
- `def simulate_repo_iteration()`

**scripts/efficiency_suite.py**
- `FALLBACK_CHARS_PER_TOKEN = 4`
- `MIN_OVERLAP_LINE_LENGTH = 20`
- `def count_tokens(text: str, model: str = "gemini-1.5-flash") -> int`
- `def test_static(target_dir: Path)`
- `def test_goldfish(doc_path: Path)`

**skills-lock.json**
- `"version": 1`
- `"skills": {`

**tests/buglogger.md**
- `# E2G Indexing Pipeline Bug Log`

**tests/test_cli.py**
- `@patch('subprocess.run') @patch('builtins.print') def test_cli_indexer_failure_aborts(mock_print, mock_subprocess_run)`

**tests/test_cli_edge_cases.py**
- `@patch('urllib.request.urlopen') def test_install_workspace_tools_guarantees_superpowers(mock_urlopen, tmp_path)`

**tests/test_codex_minting.py**
- `def test_mint_workspace_codex_manifest()`

**tests/test_core_mandates_presence.py**
- `def test_core_mandates_file_exists()`

**tests/test_discovery_engine.py**
- `@mock.patch("harness.discovery_engine.fetch_remote_skill") @mock.patch("harness.discovery_engine.query_llm") def test_discover_agents(mock_query_llm, mock_fetch_skill)`
- `@mock.patch("harness.discovery_engine.fetch_remote_skill") @mock.patch("harness.discovery_engine.query_llm") def test_discover_agents_with_ddd_context(mock_query_llm, mock_fetch_skill)`
- `@mock.patch("harness.discovery_engine.query_llm") def test_discover_custom_agent(mock_query_llm)`
- `@mock.patch("harness.discovery_engine.fetch_remote_skill") @mock.patch("harness.discovery_engine.query_llm") def test_discover_ddd_context(mock_query_llm, mock_fetch_skill)`
- `def test_acquire_mcp_context_with_bundle()`
- `def test_acquire_mcp_context_no_wiki()`
- `def test_acquire_mcp_context_bundle_indxr_path()`
- `def test_generate_onboarding_domain_doc(tmp_path)`
- `@mock.patch('harness.discovery_engine.query_llm') def test_generate_onboarding_domain_doc_with_tools(mock_query_llm, tmp_path)`
- `@mock.patch('harness.discovery_engine.query_llm') def test_generate_onboarding_domain_doc_forced_injection(mock_query_llm, tmp_path)`

**tests/test_e2e_flow.py**
- `def setup_dummy_wiki(project_path)`
- `@pytest.fixture def temp_project()`
- `@patch('subprocess.run') @patch('getpass.getpass') @patch('builtins.input') @patch('harness.discovery_engine.query_llm') @patch('harness.discovery_engine.fetch_remote_skill') @patch('harness.minting_engine.urllib.request.urlopen') @patch('shutil.which') def test_e2e_init_flow(
    mock_shutil_which,
    mock_urlopen,
    mock_fetch_remote_skill,
    mock_query_llm,
    mock_input,
    mock_getpass,
    mock_subprocess_run,
    temp_project
)`

**tests/test_forced_injection.py**
- `@mock.patch('harness.discovery_engine.query_llm') def test_generate_onboarding_domain_doc_forced_injection(mock_query_llm, tmp_path)`

**tests/test_mcp_config.py**
- `def test_mcp_config_filename_gemini()`
- `def test_mcp_config_filename_claude()`
- `def test_setup_harness_contains_mcp_instructions_claude()`
- `def test_setup_harness_contains_mcp_instructions_gemini()`

**tests/test_minting_engine.py**
- `def test_parse_tool_checklists()`
- `def test_patch_orchestrator_rules(tmp_path)`
- `def test_mint_workspace_agent_naming()`
- `@patch('builtins.input', return_value='') def test_wait_for_user_review_and_read_domain(mock_input, tmp_path)`
- `def test_synthesize_domain_sme_agent(tmp_path)`
- `@patch('urllib.request.urlopen') def test_install_workspace_tools(mock_urlopen, tmp_path)`

**tests/test_platform_awareness.py**
- `def test_platform_awareness_gemini()`
- `def test_platform_awareness_claude()`
- `def test_platform_awareness_cursor()`
- `def test_platform_awareness_agents()`

**tests/test_platform_coexistence.py**
- `def test_platform_coexistence()`

**tests/test_strict_generation.py**
- `def test_strict_generation()`

---

## ARCHITECTURE.md

**Language:** Markdown | **Size:** 4.6 KB | **Lines:** 70

**Declarations:**

---

## GEMINI.md

**Language:** Markdown | **Size:** 267 B | **Lines:** 7

**Declarations:**

---

## INDEX.md

**Language:** Markdown | **Size:** 25.5 KB | **Lines:** 1201

**Declarations:**

---

## ONBOARDING_GUIDE.md

**Language:** Markdown | **Size:** 4.9 KB | **Lines:** 103

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

## artifacts/codex_cli_support_plan.md

**Language:** Markdown | **Size:** 2.8 KB | **Lines:** 36

**Declarations:**

---

## artifacts/final_adversarial_report.md

**Language:** Markdown | **Size:** 2.4 KB | **Lines:** 43

**Declarations:**

---

## artifacts/implementation_plan.md

**Language:** Markdown | **Size:** 1.8 KB | **Lines:** 30

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

## artifacts/implementation_report_v3.md

**Language:** Markdown | **Size:** 2.2 KB | **Lines:** 44

**Declarations:**

---

## artifacts/qa_report.md

**Language:** Markdown | **Size:** 2.8 KB | **Lines:** 32

**Declarations:**

---

## artifacts/tasks.md

**Language:** Markdown | **Size:** 514 B | **Lines:** 8

**Declarations:**

---

## artifacts/token_optimization_guide.md

**Language:** Markdown | **Size:** 7.2 KB | **Lines:** 74

**Declarations:**

---

## artifacts/token_optimization_report.md

**Language:** Markdown | **Size:** 3.8 KB | **Lines:** 30

**Declarations:**

---

## artifacts/tool_injection_plan.md

**Language:** Markdown | **Size:** 1.9 KB | **Lines:** 54

**Declarations:**

---

## artifacts/tool_registry_expansion_design.md

**Language:** Markdown | **Size:** 1.4 KB | **Lines:** 35

**Declarations:**

---

## artifacts/tool_registry_expansion_plan.md

**Language:** Markdown | **Size:** 2.2 KB | **Lines:** 77

**Declarations:**

---

## artifacts/verification_remediation_plan.md

**Language:** Markdown | **Size:** 2.3 KB | **Lines:** 35

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

**Language:** Markdown | **Size:** 1.6 KB | **Lines:** 24

**Declarations:**

---

## boilerplate-agent/agent.json

**Language:** JSON | **Size:** 559 B | **Lines:** 26

**Declarations:**

---

## boilerplate-agent/agents/adversary.md

**Language:** Markdown | **Size:** 2.3 KB | **Lines:** 63

**Declarations:**

---

## boilerplate-agent/agents/architect.md

**Language:** Markdown | **Size:** 4.4 KB | **Lines:** 101

**Declarations:**

---

## boilerplate-agent/agents/feature-fetcher.md

**Language:** Markdown | **Size:** 2.5 KB | **Lines:** 55

**Declarations:**

---

## boilerplate-agent/agents/implementer.md

**Language:** Markdown | **Size:** 4.1 KB | **Lines:** 112

**Declarations:**

---

## boilerplate-agent/agents/linter-agent.md

**Language:** Markdown | **Size:** 1.6 KB | **Lines:** 51

**Declarations:**

---

## boilerplate-agent/agents/performance-profiler.md

**Language:** Markdown | **Size:** 1.7 KB | **Lines:** 53

**Declarations:**

---

## boilerplate-agent/agents/planner.md

**Language:** Markdown | **Size:** 5.6 KB | **Lines:** 145

**Declarations:**

---

## boilerplate-agent/agents/refactorer.md

**Language:** Markdown | **Size:** 1.9 KB | **Lines:** 59

**Declarations:**

---

## boilerplate-agent/agents/reviewer.md

**Language:** Markdown | **Size:** 3.6 KB | **Lines:** 110

**Declarations:**

---

## boilerplate-agent/agents/security-auditor.md

**Language:** Markdown | **Size:** 1.7 KB | **Lines:** 54

**Declarations:**

---

## boilerplate-agent/agents/verifier.md

**Language:** Markdown | **Size:** 2.3 KB | **Lines:** 75

**Declarations:**

---

## boilerplate-agent/onboarding/tools.json

**Language:** JSON | **Size:** 1.8 KB | **Lines:** 54

**Declarations:**

---

## boilerplate-agent/orchestrator.md

**Language:** Markdown | **Size:** 3.8 KB | **Lines:** 57

**Declarations:**

---

## boilerplate-agent/rules/core_mandates.md

**Language:** Markdown | **Size:** 2.5 KB | **Lines:** 25

**Declarations:**

---

## boilerplate-agent/rules/dispatch_rules.md

**Language:** Markdown | **Size:** 11.3 KB | **Lines:** 147

**Declarations:**

---

## boilerplate-agent/scripts/benchmark_efficiency_test.py

**Language:** Python | **Size:** 13.4 KB | **Lines:** 320

**Imports:**
- `import os`
- `import argparse`
- `import sys`
- `import subprocess`
- `from pathlib import Path`
- `from google import genai`

**Declarations:**

`_CLIENT_CACHE = {}`

---

## boilerplate-agent/skills/ddd-alignment/SKILL.md

**Language:** Markdown | **Size:** 1.5 KB | **Lines:** 22

**Declarations:**

---

## boilerplate-agent/skills/fastapi/SKILL.md

**Language:** Markdown | **Size:** 1006 B | **Lines:** 38

**Declarations:**

---

## boilerplate-agent/skills/grill-me/SKILL.md

**Language:** Markdown | **Size:** 635 B | **Lines:** 10

---

## boilerplate-agent/skills/grill-with-docs/ADR-FORMAT.md

**Language:** Markdown | **Size:** 2.7 KB | **Lines:** 47

**Declarations:**

---

## boilerplate-agent/skills/grill-with-docs/CONTEXT-FORMAT.md

**Language:** Markdown | **Size:** 3.1 KB | **Lines:** 77

**Declarations:**

---

## boilerplate-agent/skills/grill-with-docs/SKILL.md

**Language:** Markdown | **Size:** 3.5 KB | **Lines:** 88

**Declarations:**

---

## boilerplate-agent/skills/improve-codebase-architecture/INTERFACE-DESIGN.md

**Language:** Markdown | **Size:** 2.7 KB | **Lines:** 44

**Declarations:**

---

## boilerplate-agent/skills/improve-codebase-architecture/LANGUAGE.md

**Language:** Markdown | **Size:** 3.7 KB | **Lines:** 53

**Declarations:**

---

## boilerplate-agent/skills/improve-codebase-architecture/SKILL.md

**Language:** Markdown | **Size:** 5.0 KB | **Lines:** 71

**Declarations:**

---

## boilerplate-agent/skills/meta-learning/SKILL.md

**Language:** Markdown | **Size:** 4.2 KB | **Lines:** 67

**Declarations:**

---

## boilerplate-agent/skills/nextjs/SKILL.md

**Language:** Markdown | **Size:** 5.5 KB | **Lines:** 126

**Declarations:**

---

## boilerplate-agent/skills.json

**Language:** JSON | **Size:** 392 B | **Lines:** 19

**Declarations:**

---

## docs/superpowers/plans/2023-10-25-ast-grounded-enrichment.md

**Language:** Markdown | **Size:** 9.7 KB | **Lines:** 270

**Declarations:**

---

## docs/superpowers/plans/2025-01-24-prune-logs-refactor.md

**Language:** Markdown | **Size:** 3.4 KB | **Lines:** 126

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

## docs/superpowers/plans/2026-05-08-benchmark-efficiency-plan.md

**Language:** Markdown | **Size:** 7.1 KB | **Lines:** 231

**Declarations:**

---

## docs/superpowers/plans/2026-05-08-context-intake-implementation.md

**Language:** Markdown | **Size:** 6.6 KB | **Lines:** 215

**Declarations:**

---

## docs/superpowers/plans/2026-05-08-enhanced-ddd-discovery.md

**Language:** Markdown | **Size:** 6.9 KB | **Lines:** 191

**Declarations:**

---

## docs/superpowers/plans/2026-05-08-token-optimization-plan.md

**Language:** Markdown | **Size:** 6.7 KB | **Lines:** 142

**Declarations:**

---

## docs/superpowers/plans/2026-05-08-token-optimizer-implementation.md

**Language:** Markdown | **Size:** 4.6 KB | **Lines:** 137

**Declarations:**

---

## docs/superpowers/plans/2026-05-09-bundle-fallback-plan.md

**Language:** Markdown | **Size:** 10.0 KB | **Lines:** 236

**Declarations:**

---

## docs/superpowers/plans/2026-05-09-ddd-dispatch-rules-injection.md

**Language:** Markdown | **Size:** 2.6 KB | **Lines:** 46

**Declarations:**

---

## docs/superpowers/plans/2026-05-09-setup-harness-automation-plan.md

**Language:** Markdown | **Size:** 2.3 KB | **Lines:** 43

**Declarations:**

---

## docs/superpowers/plans/2026-05-10-minting-fixes.md

**Language:** Markdown | **Size:** 7.8 KB | **Lines:** 205

**Declarations:**

---

## docs/superpowers/plans/2026-05-10-onboarding-reliability-fix.md

**Language:** Markdown | **Size:** 14.3 KB | **Lines:** 361

**Declarations:**

---

## docs/superpowers/plans/2026-05-10-phased-onboarding-plan.md

**Language:** Markdown | **Size:** 15.9 KB | **Lines:** 446

**Declarations:**

---

## docs/superpowers/plans/2026-05-10-tool-discovery-plan.md

**Language:** Markdown | **Size:** 14.9 KB | **Lines:** 417

**Declarations:**

---

## docs/superpowers/plans/2026-05-11-deterministic-tool-onboarding-plan.md

**Language:** Markdown | **Size:** 4.3 KB | **Lines:** 124

**Declarations:**

---

## docs/superpowers/plans/2026-05-13-create-pruning-utility.md

**Language:** Markdown | **Size:** 4.8 KB | **Lines:** 169

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

**Language:** Markdown | **Size:** 3.2 KB | **Lines:** 51

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

## docs/superpowers/specs/2026-05-08-benchmark-efficiency-design.md

**Language:** Markdown | **Size:** 3.1 KB | **Lines:** 59

**Declarations:**

---

## docs/superpowers/specs/2026-05-08-context-intake-design.md

**Language:** Markdown | **Size:** 3.7 KB | **Lines:** 53

**Declarations:**

---

## docs/superpowers/specs/2026-05-08-token-optimization-design.md

**Language:** Markdown | **Size:** 3.8 KB | **Lines:** 41

**Declarations:**

---

## docs/superpowers/specs/2026-05-08-token-optimizer-agent-design.md

**Language:** Markdown | **Size:** 2.7 KB | **Lines:** 39

**Declarations:**

---

## docs/superpowers/specs/2026-05-09-bundle-fallback-design.md

**Language:** Markdown | **Size:** 2.1 KB | **Lines:** 33

**Declarations:**

---

## docs/superpowers/specs/2026-05-09-setup-harness-automation-design.md

**Language:** Markdown | **Size:** 1.3 KB | **Lines:** 18

**Declarations:**

---

## docs/superpowers/specs/2026-05-10-phased-onboarding-sme-design.md

**Language:** Markdown | **Size:** 3.2 KB | **Lines:** 50

**Declarations:**

---

## docs/superpowers/specs/2026-05-10-tool-discovery-design.md

**Language:** Markdown | **Size:** 3.1 KB | **Lines:** 43

**Declarations:**

---

## docs/superpowers/specs/2026-05-11-deterministic-tool-onboarding-design.md

**Language:** Markdown | **Size:** 1.3 KB | **Lines:** 26

**Declarations:**

---

## docs/walkthrough/agentic_harness_lifecycle.md

**Language:** Markdown | **Size:** 8.4 KB | **Lines:** 144

**Declarations:**

---

## harness/cli.py

**Language:** Python | **Size:** 12.9 KB | **Lines:** 293

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

**Language:** Python | **Size:** 24.7 KB | **Lines:** 532

**Imports:**
- `import json`
- `import subprocess`
- `import time`
- `import urllib.request`
- `import os`

**Declarations:**

---

## harness/minting_engine.py

**Language:** Python | **Size:** 36.5 KB | **Lines:** 839

**Imports:**
- `import os`
- `import re`
- `import shutil`
- `import json`
- `import urllib.request`
- `from pathlib import Path`

**Declarations:**

---

## pyproject.toml

**Language:** TOML | **Size:** 412 B | **Lines:** 20

**Declarations:**

---

## run_debug.py

**Language:** Python | **Size:** 307 B | **Lines:** 9

**Imports:**
- `from harness.discovery_engine import detect_tech_stack`
- `import os`
- `import tempfile`

---

## scripts/benchmark_gate.py

**Language:** Python | **Size:** 4.4 KB | **Lines:** 93

**Imports:**
- `import subprocess`
- `import json`
- `import time`

**Declarations:**

---

## scripts/benchmark_hub_vs_spoke.py

**Language:** Python | **Size:** 5.8 KB | **Lines:** 137

**Imports:**
- `import sys`

**Declarations:**

---

## scripts/efficiency_suite.py

**Language:** Python | **Size:** 2.8 KB | **Lines:** 77

**Imports:**
- `import os`
- `import argparse`
- `import re`
- `from pathlib import Path`
- `from collections import defaultdict`
- `from google import genai`

**Declarations:**

---

## skills-lock.json

**Language:** JSON | **Size:** 3.2 KB | **Lines:** 83

**Declarations:**

---

## tests/buglogger.md

**Language:** Markdown | **Size:** 7.4 KB | **Lines:** 94

**Declarations:**

---

## tests/test_cli.py

**Language:** Python | **Size:** 863 B | **Lines:** 24

**Imports:**
- `import pytest`
- `from unittest.mock import patch`
- `import subprocess`
- `import os`
- `from harness.cli import main`

**Declarations:**

---

## tests/test_cli_edge_cases.py

**Language:** Python | **Size:** 1.2 KB | **Lines:** 31

**Imports:**
- `from unittest.mock import patch`
- `import json`
- `import os`
- `from pathlib import Path`
- `import pytest`

**Declarations:**

---

## tests/test_codex_minting.py

**Language:** Python | **Size:** 2.1 KB | **Lines:** 61

**Imports:**
- `import tempfile`
- `from pathlib import Path`
- `from harness.minting_engine import mint_workspace`

**Declarations:**

---

## tests/test_core_mandates_presence.py

**Language:** Python | **Size:** 152 B | **Lines:** 4

**Imports:**
- `import os`

**Declarations:**

---

## tests/test_discovery_engine.py

**Language:** Python | **Size:** 7.7 KB | **Lines:** 206

**Imports:**
- `import os`
- `import tempfile`
- `from harness.discovery_engine import acquire_mcp_context`
- `import pytest`
- `from unittest import mock`
- `from harness.discovery_engine import discover_agents, discover_ddd_context, discover_custom_agent, generate_onboarding_domain_doc`

**Declarations:**

---

## tests/test_e2e_flow.py

**Language:** Python | **Size:** 6.7 KB | **Lines:** 182

**Imports:**
- `import pytest`
- `import os`
- `import json`
- `import shutil`
- `import subprocess`
- `import tempfile`
- `from unittest.mock import patch, MagicMock`
- `from pathlib import Path`
- `from harness.cli import main`

**Declarations:**

---

## tests/test_forced_injection.py

**Language:** Python | **Size:** 2.1 KB | **Lines:** 64

**Imports:**
- `import os`
- `import json`
- `from unittest import mock`
- `from harness.discovery_engine import generate_onboarding_domain_doc`

**Declarations:**

---

## tests/test_mcp_config.py

**Language:** Python | **Size:** 3.7 KB | **Lines:** 101

**Imports:**
- `import pytest`
- `from pathlib import Path`
- `import tempfile`
- `import json`
- `import shutil`
- `from harness.minting_engine import mint_workspace`

**Declarations:**

---

## tests/test_minting_engine.py

**Language:** Python | **Size:** 5.9 KB | **Lines:** 171

**Imports:**
- `import pytest`
- `import shutil`
- `import tempfile`
- `import json`
- `from pathlib import Path`
- `import os`
- `from unittest.mock import patch`
- `from harness.minting_engine import (
    mint_workspace,
    wait_for_user_review_and_read_domain,
    patch_orchestrator_rules,
    parse_tool_checklists,
)`

**Declarations:**

---

## tests/test_platform_awareness.py

**Language:** Python | **Size:** 4.3 KB | **Lines:** 123

**Imports:**
- `import pytest`
- `import shutil`
- `import tempfile`
- `from pathlib import Path`
- `import os`
- `from harness.minting_engine import mint_workspace`

**Declarations:**

---

## tests/test_platform_coexistence.py

**Language:** Python | **Size:** 2.4 KB | **Lines:** 61

**Imports:**
- `import os`
- `import shutil`
- `import tempfile`
- `from pathlib import Path`
- `from harness.minting_engine import mint_workspace`

**Declarations:**

---

## tests/test_strict_generation.py

**Language:** Python | **Size:** 1.4 KB | **Lines:** 33

**Imports:**
- `import os`
- `import tempfile`
- `from pathlib import Path`
- `from harness.minting_engine import mint_workspace`

**Declarations:**

