# Platform-Aware Scaffolding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modify the Agentic Harness file generation logic to only create the specific root pointer file and configuration structure for the user's selected platform, while ensuring correct subagent invocation syntax in the templates.

**Architecture:** We will update `harness/minting_engine.py` to map the `active_platform` to its specific root pointer file and clean up any pre-existing pointer files for other platforms. We will also update `boilerplate-agent/orchestrator.md` and `boilerplate-agent/AGENTS.md` to use placeholder syntax that will be injected by the minting engine based on the platform.

**Tech Stack:** Python

---

### Task 1: Update Platform-Specific Tooling & Include Syntax in boilerplate-agent

**Files:**
- Modify: `boilerplate-agent/orchestrator.md`

- [ ] **Step 1: Replace hardcoded platform tools in `orchestrator.md`**

In `boilerplate-agent/orchestrator.md`, under `ROUTING INSTRUCTIONS:`, replace the hardcoded `@agent` syntax with a placeholder `{{SUBAGENT_SYNTAX}}` to allow the minting engine to inject the correct syntax.

- [ ] **Step 2: Commit changes**

### Task 2: Refactor `minting_engine.py` for Platform Awareness

**Files:**
- Modify: `harness/minting_engine.py`

- [ ] **Step 1: Define Platform File Maps & Clean up old files**
Update `minting_engine.py` to remove any existing root pointer files (`GEMINI.md`, `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`) to avoid pollution.

- [ ] **Step 2: Generate the correct Root Pointer File**
Only write the pointer file that corresponds to the `active_platform`.

- [ ] **Step 3: Inject `{{SUBAGENT_SYNTAX}}` replacement**
Add `{{SUBAGENT_SYNTAX}}` to the replacements logic based on the platform (e.g., `"@"` for Gemini, `"Task tool: "` for Claude).

- [ ] **Step 4: Commit changes**

### Task 3: Test and Verify

**Files:**
- Modify: `tests/test_cli_cleanup.py` (or create a new test file)

- [ ] **Step 1: Add a test case to ensure platform specific file generation**
Write a simple test that runs the minting engine and asserts that only the correct files are generated for a given platform.
