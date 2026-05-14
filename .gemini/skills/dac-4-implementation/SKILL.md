# Design-as-Code: Phase 4 (Mean Implementation)

**Goal:** Execute the validated plan using subagent delegations with zero tolerance for sloppy code.

## Instructions
1. **Subagent-Driven:** Use this skill alongside `subagent-driven-development`.
2. **Implementation Handoff:** Dispatch `@implementer` to work on independent tasks defined in the plan.
   - **Instruction:** "Implement exactly as described. Follow the file change list precisely. Use TDD."
3. **Mean Code Review:** For every completed task, dispatch the `@reviewer` subagent.
   - **Instruction:** "Perform a 'Mean Code Review'. Tear the implemented code to shreds. Flag any 10+ lines of code missing comments. Enforce extreme readability standards and ensure it matches the design doc perfectly."
4. **Completion:** Only declare a component complete when it passes the Mean Code Review.