# Phase 3: The "Goldfish" Review Protocol

**Goal**: Verify the design doc is complete and hallucination-free by testing it against a "fresh" AI memory.

## Step 6: The Comprehension Test
- **Action**: Simulate a brand new session (or actually open one if possible).
- **Roles**: `Goldfish` (Fresh Agent Persona).
- **Prompt**: "Hey, nice to meet you, Goldfish. Read this document. Read all the files referenced in it. Tell me what you think it's trying to accomplish. Then, tell me how my system currently works as it relates to this feature."
- **Fail Condition**: If the agent cannot explain the system based *only* on the doc and referenced files, the doc is missing context. Add missing details and repeat.

## Step 7: The Critic Review (Adversarial Mode)
- **Action**: Assume the role of an expert technical reviewer.
- **Roles**: `Adversarial Verifier`.
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
