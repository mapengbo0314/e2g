---
name: context-intake
description: Use when distilling raw user inputs, especially large stack traces or CI logs, into a structured diagnostic summary.
---

# Context Intake

Use this skill to distill raw user inputs, especially large stack traces or CI logs, into a structured diagnostic summary.

## The Goal
Reduce 1,000+ tokens of raw logs into a < 500 token summary that pinpoints the error and repo location.

## Instructions
1. **Analyze the Raw Logs**: Read the raw error logs provided by the Orchestrator. 
2. **Filter Noise**: Mentally discard all "Vendor Frames" (e.g., `node_modules`, `venv`, `site-packages`, standard libraries) unless the error explicitly states a missing package. Focus entirely on "Repo Frames"—code written by us.
3. **Pinpoint the Error**: Extract the exact Exception type and the core error message.
4. **Ground the Symbols**: 
   - Identify the primary application file and line number where the error occurred.
   - Use `grep_search` or `indxr` tools (like `explain_symbol` or `find`) to verify that the file exists in the current workspace and retrieve the specific code block causing the issue.
5. **Distill Evidence**: Extract a minimal 3-5 line snippet of the offending code. Do NOT copy the entire file.
6. **Suggest Next Step**:
   - If it's a bug: "Next Process: Use superpowers:diagnose starting at Phase 1 (Build a feedback loop)."
   - If it's a feature/architecture issue: "Next Process: Proceed to Brainstorming."

## Output Format
Produce a concise markdown summary with these sections:
- **Intent**: ...
- **Error**: ...
- **Primary Location**: `file:line`
- **Distilled Evidence**: ...
- **Next Process**: ...
