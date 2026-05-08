---
name: context-intake
description: Use when distilling raw user inputs, especially large stack traces or CI logs, into a structured diagnostic summary.
---

# Context Intake

Use this skill to distill raw user inputs, especially large stack traces or CI logs, into a structured diagnostic summary.

## The Goal
Reduce 1,000+ tokens of raw logs into a < 500 token summary that pinpoints the error and repo location.

## Instructions
1. **Automated Pruning**: 
   - Write the raw user stack trace/logs to a temporary file: `artifacts/temp_raw_logs.txt`.
   - Run a deterministic bash filter to strip vendor noise:
     `grep -v "node_modules\|venv\|site-packages\|/lib/python\|/usr/lib/\|external/" artifacts/temp_raw_logs.txt > artifacts/pruned_logs.txt`
   - Read `artifacts/pruned_logs.txt`. This is your clean working context.
2. **Identify the Intent**: What is the user trying to do? (e.g., "Fix a failing test", "Debug a timeout").
3. **Pinpoint the Error**: Extract the exact Exception type and message from the pruned output.
4. **Isolate Repo Frames**: 
   - Review the pruned stack trace for files within the current repository.
   - Use `grep_search` to verify the file and line number exist.
5. **Distill Evidence**: Extract 3-5 lines of context around the failure point.
6. **Suggest Next Step**:
   - If it's a bug: "Next Process: Use superpowers:diagnose starting at Phase 1 (Build a feedback loop)."
   - If it's a feature request: "Next Process: Proceed to Brainstorming."

## Output Format
Produce a concise markdown summary with these sections:
- **Intent**: ...
- **Error**: ...
- **Primary Location**: `file:line`
- **Distilled Evidence**: ...
- **Next Process**: ...
