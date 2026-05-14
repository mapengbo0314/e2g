# Design-as-Code: Phase 3 (Goldfish Validation)

**Goal:** Leverage isolated subagents to test the written implementation plan for gaps and assumptions.

## Instructions
1. **Prerequisite:** Run this alongside the `verification-before-completion` skill *after* the implementation plan has been written but *before* writing any code.
2. **The Gauntlet:** Dispatch the following native subagents in sequence using the `invoke_agent` tool. Pass them ONLY the path to the written plan.
   - **Comprehension Test:** Dispatch `@generalist`. Prompt: "Read this spec and explain the system architecture back to me. Do not write code."
   - **Critic Review:** Dispatch `@adversary`. Prompt: "Tear this plan apart. Find missing edge cases, faulty assumptions, or ambiguous logic."
   - **Implementation Readiness:** Dispatch `@verifier`. Prompt: "Confirm if this document has *absolutely all* the information required to successfully implement the feature without asking clarifying questions."
3. **Synthesis & Recommendation:** Synthesize the feedback from the subagents. Present the user with a summary of what needs to be fixed and your recommendations.
4. **Apply & Re-verify:** Apply the approved fixes to the plan. If major changes were made, re-verify readiness.
5. **Transition:** Once finalized, transition to implementation.