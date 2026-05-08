---
name: context-intake
description: Use when distilling raw user inputs, especially large stack traces or CI logs, into a structured diagnostic summary.
---

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
