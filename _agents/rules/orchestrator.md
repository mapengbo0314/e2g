---
trigger: always_on
---

# Orchestrator Rules

The orchestrator coordinates agent roles for planning, implementation, review, verification, and repository population.

## Core Flow

1.  **Route incoming work to `planner` first** when scope is unclear or a new feature is requested.
2.  **For non-trivial feature development**, follow the [Feature Development Lifecycle](#feature-development-lifecycle).
3.  Use **Architect** for system structure or migration strategy.
4.  Use **Implementer** for concrete file changes.
5.  Use **Adversarial Verifier** before large merges or major workflow shifts.
6.  Use **Verifier** for final QA, edge cases, and robustness checks.

## Feature Development Lifecycle

When building new features, the orchestrator MUST transition through these four mandatory phases. Each phase requires an **Adversarial Mandate** to challenge assumptions and prevent code slop.

### Phase 1: Design Discussion (No Code)
Focus: Co-design and grounding.
-   **Step**: Context Loading, "No Code" Interview, The Challenge, Technical Proposal.
-   **Roles**: Researcher, Architect, Adversarial Verifier.
-   **Detail**: [phase_1_design_discussion.md](file:///Users/pengbolicious/pengbo-apps/e-2-g/_agents/rules/phases/phase_1_design_discussion.md)

### Phase 2: Writing the Design Doc
Focus: Establishing the "Source of Truth" with embedded readiness assertions.
-   **Step**: Section-by-section generation (Problem, Plan, Alternatives, Detailed Implementation, **Sphinch Marks**).
-   **Roles**: Architect, Technical Writer.
-   **Detail**: [phase_2_design_doc.md](file:///Users/pengbolicious/pengbo-apps/e-2-g/_agents/rules/phases/phase_2_design_doc.md)

### Phase 3: The "Goldfish" Review Protocol
Focus: Convergent verification via sphinch mark pass/fail checks (replaces open-ended critique).
-   **Step**: Comprehension Test, **Sphinch Mark Verification**, Implementation Readiness.
-   **Roles**: Goldfish (Fresh Agent), Adversarial Verifier.
-   **Detail**: [phase_3_goldfish_protocol.md](file:///Users/pengbolicious/pengbo-apps/e-2-g/_agents/rules/phases/phase_3_goldfish_protocol.md)

### Phase 4: Implementation & Mean Review
Focus: High-fidelity coding and strict readability.
-   **Step**: Coding with Guardrails, "Mean" Code Review (10-line comment rule).
-   **Roles**: Implementer, Adversarial Verifier.
-   **Detail**: [phase_4_implementation.md](file:///Users/pengbolicious/pengbo-apps/e-2-g/_agents/rules/phases/phase_4_implementation.md)
