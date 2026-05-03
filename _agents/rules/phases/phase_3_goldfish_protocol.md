# Phase 3: The "Goldfish" Review Protocol

**Goal**: Verify the design doc is complete and hallucination-free by testing it against a "fresh" AI memory. **Terminates when all sphinch marks pass.**

## Step 6: The Comprehension Test
- **Action**: Simulate a brand new session (or actually open one if possible).
- **Roles**: `Goldfish` (Fresh Agent Persona).
- **Prompt**: "Hey, nice to meet you, Goldfish. Read this document. Read all the files referenced in it. Tell me what you think it's trying to accomplish. Then, tell me how my system currently works as it relates to this feature."
- **Fail Condition**: If the agent cannot explain the system based *only* on the doc and referenced files, the doc is missing context. Add missing details and repeat.

## Step 7: Sphinch Mark Verification (Replaces Open-Ended Critic Review)

> **CRITICAL:** This step does NOT run an open-ended adversarial review.
> That approach is non-convergent (each pass finds different issues based on
> attention). Instead, the reviewer mechanically verifies the sphinch marks.

- **Action**: Locate the `## Sphinch Marks` section in the design document.
- **Roles**: `Adversarial Verifier`.
- **Protocol**:
  1. **Verify each sphinch mark** — For each `- [ ]` item, perform the specific
     verification described (read a section, compare field names, trace a path,
     grep for a reference). Mark `[x]` if it passes.
  2. **Fix failures** — For each `- [ ]` that fails, update the design doc to
     resolve the issue. Then re-verify ONLY the fixed items.
  3. **No new marks** — Do NOT add new sphinch marks during verification. If a
     genuine new issue is discovered that doesn't map to any existing mark, log
     it as a "Phase 4 implementation note" in the doc, NOT as a new mark.
  4. **Delta-check** — Verify that no change claims credit for pre-existing
     codebase functionality. The existing system state is not new progress.
- **Termination Condition**: All sphinch marks are either `[x]` or `🔵 DEFERRED`
  (max 5 deferred items with rationale). When this condition is met, the doc
  is implementation-ready.
- **Fail Condition**: If the reviewer cannot verify a mark because the
  specification is ambiguous or incomplete, that is a legitimate failure. Fix
  the spec, not the mark.

### Legacy Fallback: Open-Ended Critic Review
If the design doc does NOT contain a sphinch marks section (legacy docs), fall
back to the original open-ended review:
- **Prompt**: "Assume the role of an expert technical reviewer. Tell me all the things I missed, all the faulty assumptions, all the edge cases I'm missing, and things I should have considered but did not. **Crucially, perform a delta-check: what specifically changed in the last user edit versus the existing codebase? Do not attribute existing system state as new progress.**"
- **Fail Condition**: If the agent praises a feature that was already present in the previous version of the document or codebase, it has failed the mandate.
- **Action**: Update the design doc based on valid critiques.

## Step 8: The Implementation Readiness Test
- **Action**: Simulate an experienced SWE.
- **Roles**: `Architect`.
- **Prompt**: "You are an experienced SWE experienced with our codebase. Read this document and tell me: Does it absolutely have all the information you would require to successfully implement this feature in your first pass?"
- **Action**: Resolve ambiguities and update the doc.

## Step 9: Human Review
- **Action**: Share the design doc with relevant humans for feedback.
- **Note**: Do not involve AI in this step. Update the doc based on human feedback and gain approvals.
