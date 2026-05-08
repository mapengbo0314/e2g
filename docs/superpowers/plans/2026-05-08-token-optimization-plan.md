# Token Optimization via Prompt Deduplication and Context Intake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce token bloat by extracting common agent mandates into a shared file and establishing a pre-delegation stack-trace compression layer using `token-optimizer` and `stack-trace-decoder`.

**Architecture:** 
1. `boilerplate-agent/rules/core_mandates.md` will hold the shared system prompt.
2. `harness/minting_engine.py` will inject `@.gemini/rules/core_mandates.md` (or equivalent) instead of duplicating the string into agent files.
3. `minting_engine.py` will update setup scripts to install `token-optimizer` and `stack-trace-decoder`.
4. `boilerplate-agent/rules/dispatch_rules.md` will receive updated routing instructions mandating triage via `architect` before delegating bugs to `implementer`.

**Tech Stack:** Python (Minting Engine), Markdown (Prompts), npm (Skills).

---

### Task 1: Create Shared Mandates File

**Files:**
- Create: `boilerplate-agent/rules/core_mandates.md`
- Create: `tests/test_core_mandates_presence.py`

- [ ] **Step 1: Write the failing test**

```python
import os

def test_core_mandates_file_exists():
    assert os.path.exists("boilerplate-agent/rules/core_mandates.md"), "Core mandates file is missing"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_core_mandates_presence.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

Write the shared mandates content to `boilerplate-agent/rules/core_mandates.md`:

```markdown
# Core Mandates (Universal Subagent Context)

You are a specialized subagent operating within this repository's agent ecosystem. You have been delegated a specific task by the Orchestrator (the main agent).

1. **Security & System Integrity:** Never log, print, or commit secrets, API keys, or sensitive credentials. Rigorously protect `.env` files, `.git`, and system configuration folders. Do not stage or commit changes unless specifically requested by the user.
2. **Context Efficiency:** Your context window is isolated to save tokens. Be strategic in your use of tools. Combine turns whenever possible. Prefer targeted search before reading entire files.
3. **Engineering Standards:** Follow established workspace conventions for naming, formatting, typing, and commenting, but do not blindly replicate poor quality patterns. If existing code violates readability standards, produce high-quality idiomatic code for your changes rather than matching surrounding anti-patterns. Never assume a library or framework is available without verifying its usage in the project.
4. **Contextual Precedence & Clashes:** Project-specific instructions found in the loaded context, including `AGENT.md` and role-level instructions within this workspace, are foundational mandates and take precedence over your default workflows. If you detect a severe conflict between these instructions and sound engineering practice, pause and ask the user for clarification rather than acting on contradictory rules.
5. **No Chitchat:** Avoid conversational filler. Focus exclusively on intent and technical rationale. Do not narrate your tool usage.

# Workspace Guidelines

## Language stance
- The current service is Python-first.
- New agent outputs should preserve working Python unless the task explicitly asks for a migration artifact.
- A strategic project goal is to progressively translate stable Python modules into Kotlin or Java once the behavior is fully understood.

## Kotlin and Java migration guidance
- Treat Kotlin as the default JVM landing zone unless Java is requested.
- Preserve behavior before optimizing structure.
- Migrate one bounded subsystem at a time.
- Generate design notes before large language migrations.
- Keep test fixtures and example inputs aligned across source and target implementations.

## Documentation expectations
- Every new workflow should state its inputs, outputs, and failure modes.
- Media-derived code reference source evidence when possible.
- Migration plans should note what is preserved, what is re-modeled, and what remains unknown.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_core_mandates_presence.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

Run:
```bash
git add tests/test_core_mandates_presence.py boilerplate-agent/rules/core_mandates.md
git commit -m "feat(harness): extract shared core mandates to rules directory"
```

---

### Task 2: Update Minting Engine (Platform-Aware Deduplication & Tooling)

**Files:**
- Modify: `harness/minting_engine.py`

- [ ] **Step 1: Write minimal implementation**

Update `minting_engine.py` using `sed` or Python scripting to replace the hardcoded `core_mandates` injection and update the `setup_harness.sh` scripts.

1.  Find the `scripts_to_generate` dictionary in `harness/minting_engine.py`.
2.  Update the `"claude"` and `"cursor"` values to include:
    ```bash
    echo "Installing stack-trace-decoder..."
    npx skills add latestaiagents/agent-skills@stack-trace-decoder -y || true
    ```
3.  Update the `"gemini"` value to include:
    ```bash
    echo "Installing stack-trace-decoder..."
    gemini extensions install https://github.com/latestaiagents/agent-skills@stack-trace-decoder || true
    ```
4.  Find the loop `for agent in selected_agents:` near the end of the file.
5.  Remove the `core_mandates = f"""..."""` block.
6.  Replace the `final_content` construction with platform-aware logic:

```python
        # Determine the correct include syntax based on platform
        include_pointer = ""
        if active_platform == "gemini":
            include_pointer = f"@.{active_platform}/rules/core_mandates.md\\n\\n"
        elif active_platform == "claude":
            include_pointer = f"@.{active_platform}/rules/core_mandates.md\\n\\n"
        else:
            # Fallback for cursor/agents where include syntax might not be natively supported
            include_pointer = "<!-- Core Mandates should be read from rules/core_mandates.md -->\\n\\n"

        final_content = frontmatter + include_pointer + system_prompt + "\\n" + ddd_section
```

- [ ] **Step 2: Commit**

Run:
```bash
git add harness/minting_engine.py
git commit -m "feat(harness): implement platform-aware prompt deduplication and inject token optimization tools"
```

---

### Task 3: Update Orchestrator Routing Rules

**Files:**
- Modify: `boilerplate-agent/rules/dispatch_rules.md`
- Modify: `boilerplate-agent/orchestrator.md`

- [ ] **Step 1: Write minimal implementation (dispatch_rules.md)**

Using an exact replace, insert the new mandate into `boilerplate-agent/rules/dispatch_rules.md` inside the `<orchestration_hierarchy>` section, right below the Adversarial Verification bullet.

```markdown
- **Failure Context Triage (MANDATORY)**: If the user input contains a raw stack trace, CI failure, or explicitly requests a bug fix, DO NOT read the logs directly. You MUST delegate to a triage agent (e.g., `architect` or `@generalist`) and instruct them to use the `stack-trace-decoder` skill. They must write a compressed artifact to `workspace/artifacts/triage.md`. When delegating to the `implementer` to fix the bug, pass `artifacts/triage.md` as the primary diagnostic frame, but **always include the original user prompt** in the delegation message to preserve intent.
```

- [ ] **Step 2: Write minimal implementation (orchestrator.md)**

Using an exact replace, add `stack-trace-decoder` to the `Skills:` list in the Metadata header of `boilerplate-agent/orchestrator.md`.

```markdown
## Metadata
- Name: orchestrator
- Description: Senior Project Manager & Router that manages the Hub-and-Spoke model.
- Type: router
- Version: 1.0
- Entrypoint: orchestrator.md
- Skills:
  - grill-me
  - grill-with-docs
  - improve-coding-architecture
  - ddd-alignment
  - stack-trace-decoder
```

- [ ] **Step 3: Commit**

Run:
```bash
git add boilerplate-agent/rules/dispatch_rules.md boilerplate-agent/orchestrator.md
git commit -m "feat(orchestrator): mandate pre-delegation failure triage"
```
