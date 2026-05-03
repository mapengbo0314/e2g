# Phase 4: Implementation & Mean Review

**Goal**: Generate code with minimal "slop" and bugs.

## Step 10: Coding with Guardrails
- **Action**: Use the finalized Design Doc as the prompt for coding.
- **Roles**: `Implementer`.
- **Mandate**: "Read this design doc. Implement the feature as described. Follow the plan exactly."
- **Recovery**: If the agent "spins out", restart a session and feed the Design Doc again to restore context.

## Step 11: The "Mean" Code Review (Adversarial Mode)
- **Action**: Critique the generated code strictly.
- **Roles**: `Adversarial Verifier`.
- **Prompt**: "Tell me all the ways in which this code is terrible. Tell me any place in this CL where we've gone 10 lines of code or more without a comment. Tell me all the places it doesn't pass readability."
- **Strict Rule**: **Zero warnings**. Strict readability. Focus on complexity and logic errors.
