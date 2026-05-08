# Hardened Context Intake Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a mandatory in-memory compression gate for non-trivial inputs to protect subagents from token bloat.

**Architecture:** A universal routing gate triggered by the Orchestrator on inputs > 2000 chars or containing logs. It delegates to a `context-intake` skill to produce a distilled summary used for all downstream work.

**Tech Stack:** Markdown (Prompts/Skills), Python (Harness logic).

---

### Task 0: Create Pruning Utility

**Files:**
- Create: `scripts/prune_logs.py`

- [ ] **Step 1: Implement `scripts/prune_logs.py`**

```python
import sys
import re

def prune_logs(input_text):
    lines = input_text.splitlines()
    pruned = []
    
    # Common vendor/noise patterns
    vendor_patterns = [
        r"node_modules/",
        r"venv/",
        r"site-packages/",
        r"/lib/python",
        r"/usr/lib/",
        r"external/"
    ]
    
    error_found = False
    for line in lines:
        # Always keep error messages and exceptions
        if any(kw in line for kw in ["Exception", "Error:", "Traceback", "FAILED", "AssertionError"]):
            pruned.append(line)
            error_found = True
            continue
            
        # Keep lines that look like repo frames (assuming no vendor patterns)
        if any(pat in line for pat in vendor_patterns):
            # Only keep vendor frame if we haven't found an error yet (might be part of the header)
            if not error_found:
                pruned.append(line)
            continue
            
        # Keep everything else (likely repo frames or context)
        pruned.append(line)
        
    return "\n".join(pruned)

if __name__ == "__main__":
    raw_input = sys.stdin.read()
    print(prune_logs(raw_input))
```

- [ ] **Step 2: Commit**

```bash
git add scripts/prune_logs.py
git commit -m "feat(scripts): add prune_logs.py utility for local log compression"
```

### Task 1: Create the `context-intake` Skill

**Files:**
- Create: `boilerplate-agent/skills/context-intake/SKILL.md`

- [ ] **Step 1: Write the `context-intake` skill content**

```markdown
# Context Intake

Use this skill to distill raw user inputs, especially large stack traces or CI logs, into a structured diagnostic summary.

## The Goal
Reduce 1,000+ tokens of raw logs into a < 500 token summary that pinpoints the error and repo location.

## Instructions
1. **Identify the Intent**: What is the user trying to do? (e.g., "Fix a failing test", "Debug a timeout").
2. **Pinpoint the Error**: Extract the exact Exception type and message.
3. **Isolate Repo Frames**: 
   - Search the stack trace for files within the current repository.
   - Use `grep_search` to verify the file and line number exist.
   - Ignore "Vendor Frames" (e.g., `node_modules`, `venv`, system libraries) unless the error message originates there.
4. **Distill Evidence**: Extract 3-5 lines of context around the failure point.
5. **Suggest Next Step**:
   - If it's a bug: "Next Process: Use superpowers:diagnose starting at Phase 1."
   - If it's a feature request: "Next Process: Proceed to Brainstorming."

## Output Format
Produce a concise markdown summary with these sections:
- **Intent**: ...
- **Error**: ...
- **Primary Location**: `file:line`
- **Distilled Evidence**: ...
- **Next Process**: ...
```

- [ ] **Step 2: Commit**

```bash
git add boilerplate-agent/skills/context-intake/SKILL.md
git commit -m "feat(skills): add context-intake skill for log compression"
```

---

### Task 2: Update Orchestrator Dispatch Rules

**Files:**
- Modify: `boilerplate-agent/rules/dispatch_rules.md`
- Modify: `boilerplate-agent/rules/unified_superpower_workflow.md`

- [ ] **Step 1: Update `dispatch_rules.md` with the Intake Gate**

Insert at the top of the `<orchestration_hierarchy>` section:

```markdown
- **Context Intake Gate (MANDATORY)**: 
  - **Trigger**: If input > 2000 characters OR contains log patterns (`Traceback`, `at `, `Exception`, `Error: `).
  - **Action**: You MUST delegate to `@generalist` with the `context-intake` skill to produce a `SUMMARY`.
  - **Delegation**: Use the resulting `SUMMARY` as the primary context for all subsequent subagent calls. DO NOT pass the raw logs to downstream agents.
```

- [ ] **Step 2: Update `unified_superpower_workflow.md` with State 0.5**

Insert before `State 1: Design Discussion`:

```markdown
### State 0.5: Context Intake (Gating)
- **Trigger**: Large input or logs detected.
- **Goal**: Distill raw input into a bounded summary.
- **Exit Condition**: `context_intake_summary` produced and verified.
```

- [ ] **Step 3: Commit**

```bash
git add boilerplate-agent/rules/dispatch_rules.md boilerplate-agent/rules/unified_superpower_workflow.md
git commit -m "feat(rules): enforce mandatory context intake gate"
```

---

### Task 3: Update Orchestrator and Core Mandates

**Files:**
- Modify: `boilerplate-agent/orchestrator.md`
- Modify: `boilerplate-agent/rules/core_mandates.md`

- [ ] **Step 1: Add `context-intake` to Orchestrator skills**

```markdown
- Skills:
  - context-intake
  - grill-me
  ...
```

- [ ] **Step 2: Update `core_mandates.md` with Context Efficiency**

Add to the "Context Efficiency" section:

```markdown
6. **Intake Awareness**: If you are a subagent (Implementer, Planner, etc.), you should prioritize the distilled summary provided in your prompt over any raw logs. If you detect raw logs were leaked to you without an intake summary, flag this as a workflow violation.
```

- [ ] **Step 3: Commit**

```bash
git add boilerplate-agent/orchestrator.md boilerplate-agent/rules/core_mandates.md
git commit -m "feat(orchestrator): register context-intake skill and update mandates"
```

---

### Task 4: Update Minting Engine

**Files:**
- Modify: `harness/minting_engine.py`

- [ ] **Step 1: Ensure `context-intake` skill is bundled during minting**

Update `minting_engine.py` to copy the `context-intake` skill folder/file into the new workspace.

```python
# In harness/minting_engine.py
# Ensure the skills directory includes context-intake
```

- [ ] **Step 2: Commit**

```bash
git add harness/minting_engine.py
git commit -m "feat(harness): bundle context-intake skill in minted workspaces"
```

---

### Task 5: Final Verification

- [ ] **Step 1: Verify the Gate manually**
Perform a dry-run check: If a user provided a 3000-character stack trace, would the Orchestrator follow Task 2's rules?
Expected: Yes.

- [ ] **Step 2: Verify `context-intake` skill logic**
Read the skill file one last time to ensure it mentions `grep_search`.
Expected: Yes.
