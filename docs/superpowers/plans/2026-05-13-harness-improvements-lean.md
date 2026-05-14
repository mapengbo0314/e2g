# Lean Harness Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the "Higher/Lower" model selection policy and the intelligent stack trace extraction hook for maximum token and cost efficiency.

**Architecture:** 
1.  **Model Selection Policy:** Update the Orchestrator's system prompt to explicitly mandate the use of "higher" models (reasoning) vs "lower" models (execution).
2.  **Stack Trace Hook:** Add a polyglot extraction script to the boilerplate scripts directory to condense log files before ingestion.

**Tech Stack:** Python, Markdown (Agent System Prompts)

---

### Task 1: Create the Stack Trace Extractor Hook

**Files:**
- Create: `boilerplate-agent/scripts/extract_stacktrace.py`
- Modify: `boilerplate-agent/agents/implementer.md`
- Modify: `boilerplate-agent/skills/diagnose/SKILL.md`

- [ ] **Step 1: Write the extractor implementation**

Create `boilerplate-agent/scripts/extract_stacktrace.py`:
```python
#!/usr/bin/env python3
import sys
import re

def extract_trace(log_content):
    # Heuristic for finding common stack trace patterns
    patterns = [
        r"Traceback \(most recent call last\):", # Python
        r"Error: .*?\n\s+at ",                 # Node
        r"panic: ",                            # Go
        r"AssertionError"                      # Generic
    ]
    
    lines = log_content.splitlines()
    for idx, line in enumerate(lines):
        if any(re.search(p, line) for p in patterns):
            # Capture from start of trace to the end of the log (or next block)
            # This ensures we get the full error context
            return "\n".join(lines[idx:idx+100]) # Cap at 100 lines
            
    return "\n".join(lines[-40:]) # Fallback to tail

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    with open(sys.argv[1], 'r') as f:
        print(extract_trace(f.read()))
```

- [ ] **Step 2: Mandate usage in agent prompts**

Modify `boilerplate-agent/agents/implementer.md` (Constraints):
- [ ] Add: `- **Stack Trace Hook**: Before reading large log files, you MUST run `run_shell_command("python {{HARNESS_DIR}}/scripts/extract_stacktrace.py <file>")` to minimize context usage.`

Modify `boilerplate-agent/skills/diagnose/SKILL.md` (Checklist):
- [ ] Add: `- Run the extraction hook: `python {{HARNESS_DIR}}/scripts/extract_stacktrace.py <logfile>` to isolate the error.`

- [ ] **Step 3: Commit**

```bash
chmod +x boilerplate-agent/scripts/extract_stacktrace.py
git add boilerplate-agent/scripts/extract_stacktrace.py boilerplate-agent/agents/implementer.md boilerplate-agent/skills/diagnose/SKILL.md
git commit -m "feat(hook): add stacktrace extraction script and mandate its use"
```

### Task 2: Implement "Higher/Lower" Model Selection

**Files:**
- Modify: `boilerplate-agent/rules/dispatch_rules.md`
- Modify: `boilerplate-agent/orchestrator.md`

- [ ] **Step 1: Update Model Selection Policy in Dispatch Rules**

In `boilerplate-agent/rules/dispatch_rules.md`, locate `<model_selection_policy>` and ensure it uses "higher/lower" terminology:
```markdown
<model_selection_policy>
When invoking sub-agents, you MUST select the appropriate model tier:
- **Use "higher" models** (e.g., Pro, Sonnet) for Reasoning, Planning, Architecture, and Review.
- **Use "lower" models** (e.g., Flash, Haiku) for Execution (Implementing), Typos, and simple fixes.
</model_selection_policy>
```

- [ ] **Step 2: Add Ambiguity Gate to Orchestrator**

In `boilerplate-agent/orchestrator.md`, add to the "SYSTEM PROMPT" section:
```markdown
- **Ambiguity Gate**: If a bug report is vague, use `ask_user` to check if the user wants a "Fast Path" (typo/simple fix) or "Standard Path" (deep diagnosis). Default to "higher" models for diagnosis and "lower" models for fast-path implementation.
```

- [ ] **Step 3: Commit**

```bash
git add boilerplate-agent/rules/dispatch_rules.md boilerplate-agent/orchestrator.md
git commit -m "feat(orchestrator): implement higher/lower model policy and ambiguity gate"
```