# Agentic Harness Improvements: Stack Trace Extraction & Bug Routing

## 1. Overview
This document outlines the design for two critical optimizations to the Agentic Harness, aimed at reducing context bloat and improving bug resolution speed:
1.  **"Ask First" Bug Routing Protocol:** A deterministic gate in the Orchestrator to bypass heavy architectural reviews for simple fixes.
2.  **Intelligent Stack Trace Hook:** A polyglot error extraction script (inspired by `ultimate_bug_scanner`) that condenses massive log files into actionable contexts before ingestion by the LLM.

## 2. "Ask First" Bug Routing Protocol

### Problem
Currently, all bug reports are routed to the `@architect` for Phase 0 (Diagnosis), followed by the `@planner` and finally the `@implementer`. For a simple typo, this incurs a massive "Routing Tax" (~15,000 tokens) before a single line of code is written.

### Solution
Update the Orchestrator's `<tool_delegation_policy>` in `dispatch_rules.md` to introduce a deterministic triage flow:

1.  **Initial Assessment (Auto-Fast Path):** If the user's prompt explicitly provides the exact file/line to fix, or explicitly requests a "quick fix", the Orchestrator routes the task immediately to the `@implementer`.
2.  **The "Ask First" Gate:** If the prompt is a pasted log, stack trace, or a vague failure report, the Orchestrator MUST use the `ask_user` tool:
    *   **Question:** "Should I route this as a quick, localized fix, or run a deep architectural diagnosis?"
    *   **Options:** `["Quick Fix (Fast Path)", "Deep Diagnosis (Standard Path)"]`
3.  **Fallback Mechanism:** If the `ask_user` tool is unavailable or the user delegates the decision to the agent, default to the **Fast Path** (`@implementer`).
4.  **Escalation Loop:** If the `@implementer` fails to resolve the bug on the Fast Path, they report the failure. The Orchestrator intercepts this failure and automatically escalates the issue to the **Standard Path** (`@architect` -> `diagnose` -> `@planner`).

## 3. Intelligent Stack Trace Extraction Hook

### Problem
When tests fail, agents often use `read_file` to ingest the entire test output log. This consumes thousands of tokens on irrelevant setup logs and dependency warnings, increasing costs and triggering the "lost in the middle" effect where the model misses the actual assertion error.

### Solution
Introduce a dedicated Python script, `extract_stacktrace.py`, deployed into the `boilerplate-agent/scripts` directory during minting.

#### Implementation Details
*   **Location:** `boilerplate-agent/scripts/extract_stacktrace.py`
*   **Behavior:** The script reads a log file or standard input.
*   **Heuristics (Inspired by `ultimate_bug_scanner`):**
    *   Detects the language environment based on regex patterns (e.g., Python's `Traceback (most recent call last):`, Node's `Error: ... at ...`).
    *   Traces the stack frames backwards to find the *last frame belonging to user code* (ignoring `/node_modules/`, `/usr/lib/`, or standard library paths).
    *   Extracts the specific error message, the file path, the line number, and ~5-10 lines of surrounding code context.
*   **Agent Integration:**
    *   Update the `diagnose` skill instructions to mandate: *"When analyzing test failures or logs, you MUST run `run_shell_command("python <harness_dir>/scripts/extract_stacktrace.py <logfile>")` before attempting to read the raw log file."*
    *   Update the `@implementer` prompt with the same mandate.

## 4. Rollout Strategy
1.  **Script Creation:** Write the `extract_stacktrace.py` script and place it in the core `boilerplate-agent/scripts/` repository.
2.  **Rules Update:** Modify `boilerplate-agent/rules/dispatch_rules.md` to encode the "Ask First" protocol.
3.  **Skill Update:** Update the `diagnose` skill template (and any internal testing/debugging skills) to enforce the usage of the new stack trace hook.
4.  **Testing:** Mint a new test harness, trigger a failing test, and verify that the Orchestrator correctly triages the bug and the `@implementer` utilizes the extraction hook.