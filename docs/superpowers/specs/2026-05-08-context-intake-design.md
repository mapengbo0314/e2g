# Design Doc: Hardened Context Intake Gate (In-Memory Compression)

## 1. Problem
Raw user inputs containing large stack traces, CI logs, or redundant diagnostic data cause severe token bloat. This bloat propagates through the "Hub-and-Spoke" delegation chain, wasting tokens and increasing latency. The Orchestrator currently lacks a formal contract for distilling this context before delegation.

## 2. Goals
- **Minimize Token Usage**: Reduce raw logs to essential diagnostic summaries (intent, error, repo location).
- **Hardened Routing**: Ensure every non-trivial input is distilled before reaching specialized subagents.
- **Workflow Synergy**: Seamlessly hand off distilled context to the `diagnose` skill for debugging.
- **Zero Work Rule**: Keep the Orchestrator lean by delegating the intake/compression task.

## 3. Proposed Solution

### A. The `context-intake` Skill
A new first-party skill in `boilerplate-agent/skills/context-intake/SKILL.md`.
**Responsibilities:**
- **Parse**: Extract error types and messages from raw logs.
- **Filter**: Distinguish Repo Frames from Vendor Frames.
- **Ground**: Use `grep_search` and `glob` to verify that the files and lines mentioned in the trace exist in the repository.
- **Distill**: Summarize the failure into a structured summary (approx. 200-500 tokens).

### B. Universal Routing Gate (Orchestrator Integration)
Update `boilerplate-agent/rules/dispatch_rules.md` to enforce the following hierarchy:
1. **Intake Check**: Triggered if input > 2000 characters OR contains log patterns (e.g., `Traceback`, `at `, `Exception`).
2. **Compression**: Delegate to `@generalist` with `context-intake` skill to produce a `SUMMARY`.
3. **Delegation**: Use the `SUMMARY` as the primary context for subagents. 

**Note on Token Architecture**: It is acknowledged that raw logs will remain in the Orchestrator's session history (The Token Fallacy). This is an accepted trade-off to avoid the friction of file-based intake. The primary benefit is **Subagent Protection**: ensuring the `implementer`, `planner`, and `verifier` receive only the distilled summary, preventing bloat in the Spoke-level context windows.

### C. Synergy with `diagnose` Skill
When `context-intake` identifies a bug, the resulting summary will include a section:
`**Next Process**: Use superpowers:diagnose starting at Phase 1 (Build a feedback loop).`

## 4. Implementation Details
- **Location**: `boilerplate-agent/skills/context-intake/SKILL.md`
- **Rules**: `boilerplate-agent/rules/dispatch_rules.md`, `boilerplate-agent/rules/unified_superpower_workflow.md`
- **Agent Updates**: `boilerplate-agent/orchestrator.md` will list `context-intake` as a skill.

## 5. Alternatives Considered
- **File-based Artifacts**: (Rejected by user) Storing to `workspace/artifacts/context_intake.md`. We will instead use in-memory summaries passed in delegation prompts.
- **Orchestrator Manual Compression**: (Rejected) Violates Zero Work Rule.

## 6. Success Criteria
- [ ] Raw stack traces are never passed directly to `implementer`.
- [ ] Subagent prompts are reduced by > 50% for diagnostic tasks.
- [ ] `diagnose` skill is triggered with high-quality, pre-filtered context.

## 7. Sphinch Marks
- [ ] Verify `boilerplate-agent/skills/context-intake/SKILL.md` exists and contains logic to distill logs via `grep_search`.
- [ ] Verify `boilerplate-agent/rules/dispatch_rules.md` has a mandatory "Intake Check" (2000 chars / log markers).
- [ ] Verify `boilerplate-agent/orchestrator.md` lists `context-intake` in its `Skills` section.
- [ ] Verify that `context-intake` output includes a recommendation for `superpowers:diagnose` when a bug is detected.
- [ ] Verify `boilerplate-agent/rules/unified_superpower_workflow.md` includes `State 0.5: Context Intake`.
