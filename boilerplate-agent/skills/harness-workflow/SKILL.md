# Harness Workflow

## Purpose
This skill codifies the deterministic 5-phase workflow for the "Fluid Harness" architecture. It ensures a strict transition from human-led design to autonomous agent execution and finally to verified integration.

## Workflow Phases

### Phase 1: CLI Bootstrapping (Human + Superpowers)
**Goal:** Define the task and prepare the workspace.
- [ ] Invoke `brainstorming` skill to refine requirements.
- [ ] Create a design document (e.g., in `designs/`).
- [ ] Invoke `using-git-worktrees` to create an isolated environment for the harness to operate in.
- [ ] Verify the current directory is the new worktree.

<HARD-GATE>
Do not proceed until the design is approved by the user and a clean worktree is active.
</HARD-GATE>

### Phase 2: The Agent Factory (Harness: `feature-fetcher`)
**Goal:** Generate specialized agents based on the design.
- [ ] Dispatch `feature-fetcher` agent to analyze the codebase index (`local_outputs/e2g_blueprint_gemini_v1`).
- [ ] Identify necessary specialized agents (e.g., `feature-x-expert`).
- [ ] Create specialized agent configurations in `boilerplate-agent/agents/specialized/`.
- [ ] Inject relevant Superpower skills into the generated agent's prompt (e.g., `test-driven-development`).

<HARD-GATE>
Specialized agents must be instantiated with clear boundaries and assigned skills before execution.
</HARD-GATE>

### Phase 3: Deterministic Execution (Harness: LangGraph)
**Goal:** Execute the task using the hub-and-spoke graph.
- [ ] `Planner` creates a detailed implementation plan in `artifacts/plan.md`.
- [ ] Specialized agent (Implementer) writes code and tests following the plan.
- [ ] Ensure all implementation follows the `test-driven-development` skill.
- [ ] Verify artifacts are written to disk.

<HARD-GATE>
The graph must not progress if verifiable artifacts (code/tests) are missing or invalid.
</HARD-GATE>

### Phase 4: Agent Arena & Evaluation
**Goal:** Evaluate and refine agent outputs.
- [ ] (Optional) Compare multiple candidate agent outputs if variations were generated.
- [ ] `Verifier` runs tests and checks for compliance with the design.
- [ ] Orchestrator merges the best architectural and logic traits from candidates.

<HARD-GATE>
Only verified and merged code can proceed to the final phase.
</HARD-GATE>

### Phase 5: Wrap-up & PR (Human + Superpowers)
**Goal:** Finalize the work and return control to the user.
- [ ] Invoke `verification-before-completion` to run final tests.
- [ ] Invoke `requesting-code-review` to summarize changes.
- [ ] Invoke `finishing-a-development-branch` to commit and prepare a PR.
- [ ] Cleanup temporary artifacts in `boilerplate-agent/`.

## Strict Execution Rules
1. **No Skip:** Every phase must be completed in order.
2. **Isolation:** All harness execution MUST happen in the worktree created in Phase 1.
3. **Artifact-Driven:** Transitions between phases require physical artifacts on disk.
4. **Skill Chaining:** Always activate the skills mentioned in each phase when performing those actions.
