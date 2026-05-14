# Adversary Review: Harness Improvements Implementation Plan

**Reviewer:** Adversary
**Date:** 2026-05-13
**Subject:** Rigorous "Goldfish" validation of the "Ask First" routing and Stack Trace extraction plan.

## 1. Premise Analysis
The proposal attempts to solve "Routing Tax" (token bloat) by:
1. Introducing an "Ask First" gate (via `ask_user`) to choose between a "Fast Path" (@implementer) and "Standard Path" (@architect -> @planner).
2. Forcing the use of a Python script (`extract_stacktrace.py`) to prune logs before LLM ingestion.

## 2. Architectural Reality vs. Proposed Ideal

### Conflict: Redundancy with "Phase 0: Diagnosis"
The existing `dispatch_rules.md` already contains a structured `Phase 0: Diagnosis` branch. 
- **Existing Rule:** "If the user reports a bug... you MUST halt... and delegate to the `@architect`."
- **Proposed Rule:** "If the prompt is a pasted log... you MUST use the `ask_user` tool... [to choose] Quick Fix or Deep Diagnosis."

**Logical Friction:** We are creating two parallel triage systems. One is based on the *nature* of the input (Bug vs. Feature), and the other is based on a *user prompt* (Quick vs. Deep). This creates a logical collision. If a user provides a bug report, does the Orchestrator follow the "Bug Fixes Only" Phase 0 mandate, or the "Complexity Assessment" mandate? 

### Conflict: Complexity Assessment vs. "Fast Path"
The existing `Complexity Assessment & Routing` section already defines a "Low Complexity (Fast Path)". 
- **Existing Fast Path:** Isolated bug fixes or minor tweaks.
- **Proposed Fast Path:** "Ask First" gate + "Auto-Fast Path" for explicitly clear fixes.

**Critique:** The proposed Task 2 rewrite is not a surgical edit; it's a replacement that shifts the logic from "Agent Assessment" to "User Choice". This introduces human error (users will almost always choose "Quick Fix") and bypasses the `diagnose` skill, which is critical for preventing "guess-and-check" loops that ultimately waste more tokens.

## 3. Variables and Friction (Failure Points)

- **The Escalation Loop is Naive:** Task 2 proposes an "Escalation Loop" where the Orchestrator catches `@implementer` failures. In a multi-turn session, `@implementer` failures often look like "The test still fails," which the Orchestrator might interpret as the agent still "working" rather than a signal to escalate.
- **Tool Availability:** The plan relies on `ask_user`. In non-interactive CI/CD environments or certain headless integrations, `ask_user` will fail or hang. The "Fallback" to Fast Path is a risky default that prioritizes speed over correctness.
- **Script Dependency:** Forcing `extract_stacktrace.py` usage in the `@implementer` prompt creates a hard dependency on the harness directory structure (`{{HARNESS_DIR}}`). If the agent is in a sub-directory or a different repo context, this command will fail.

## 4. Logical Conclusion & Recommendation

The proposed implementation of Task 2 is **architecturally messy** and **redundant**. It attempts to fix a policy problem (Routing Tax) by adding more policy layers instead of refining the existing ones.

**Strict Recommendations:**
1. **Discard the `ask_user` gate for bugs.** The Orchestrator should be intelligent enough to see a 50-line stack trace and know it needs diagnosis. If the fix is "Quick," the existing Low Complexity Fast Path already covers it.
2. **Surgical Edit only:** Instead of rewriting the entire Complexity section, add a single bullet to the existing "Low Complexity" rule: *"If a bug report includes a clear stack trace and a single-file context, prefer the Fast Path."*
3. **Fix the Escalation:** The escalation should be triggered by the `@implementer` explicitly saying "I cannot find the root cause," not by the Orchestrator guessing based on tool output.
4. **Environment Variables:** The `extract_stacktrace.py` path should be passed via an environment variable or a known alias, not a hardcoded `{{HARNESS_DIR}}` which might not resolve.

**Status:** The plan is **NOT IMPLEMENTATION READY**. It requires a rewrite of Task 2 to avoid logic collisions with the existing `Phase 0` rules.
