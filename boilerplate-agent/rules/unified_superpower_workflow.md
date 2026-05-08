# The Universal Agentic Harness Protocol

This document defines the strictly deterministic, filesystem-backed state machine for the Platform-Agnostic Agentic Harness. It integrates the Orchestrator Routing rules, the `using-superpowers` skill lifecycle, and the **`indxr` MCP** tools.

## Core Mandate: Superpower Skill Invocation
At each stage of this workflow, the Orchestrator or corresponding subagent **MUST** explicitly invoke the listed `Superpower Skill` using their AI's skill invocation tool.

## DOMAIN DRIVEN DESIGN (DDD) mandate:
- Use skills like `grill-me`, `grill-with-docs`, `improve-coding-architecture`, and `ddd-alignment` if you encounter domain conflicts, need to refine the ubiquitous language, or want to align implementation with architectural goals.

---

## The State Machine

> **COMPLEXITY BYPASS (FAST PATH)**: If the Orchestrator determines the user's request is of **Low Complexity** (e.g., a simple typo fix, single-file isolated change), it MUST bypass States 1 and 2 and jump directly to State 3 (Execution). The full State Machine is reserved for **High Complexity** features.

### State 0: Bootstrap & Factory Minting
*   **Action:** The user launches their chosen AI within the `boilerplate-agent` directory.
*   **Interaction:** The Orchestrator delegates to `feature-fetcher`. 
*   **MCP Integration:** `feature-fetcher` uses `indxr` MCP tools (`get_tree`, `get_public_api`, `get_health`) to understand the repository structure without reading raw files. It proposes specialized agents. 
*   **Handoff:** The user approves, the factory is minted, and the user restarts the AI in the new project directory.

### State 1: Feature Refinement
*   **Required Superpower Skill:** `brainstorming`
*   **Action:** The Orchestrator engages the user to define a feature or fix.
*   **Interaction:** The Orchestrator or specialized subagent MUST invoke the `brainstorming` skill to explore the project context and ask clarifying questions. 
*   **MCP Integration:** Before proposing approaches, the agent uses `indxr` tools (`find`, `search_relevant`, `summarize`, `get_health`) to verify its assumptions against the real codebase. 
*   **Handoff:** Requirements are finalized and written to a spec document (as dictated by the `brainstorming` skill).

### State 2: Planning
*   **Required Superpower Skill:** `writing-plans`
*   **Action:** The Orchestrator delegates to the `planner` agent.
*   **Interaction:** The `planner` agent MUST invoke the `writing-plans` skill to draft a deterministic execution plan.
*   **MCP Integration:** The `planner` uses `indxr` tools (`explain_symbol`, `get_dependency_graph`, `get_callers`) to map out exact interfaces and ensure the plan relies on existing architecture.
*   **Handoff:** The state is committed to disk at `workspace/artifacts/plan.md`.

### State 3: Execution & Testing
*   **Required Superpower Skills:** `test-driven-development` and `systematic-debugging`
*   **Action:** The Orchestrator delegates to the `implementer` (or specialized coding agent).
*   **Interaction:** The agent reads the plan. It MUST invoke `test-driven-development` to write failing tests first. If bugs occur, it MUST invoke `systematic-debugging` to trace root causes.
*   **MCP Integration:** During debugging, the agent queries `indxr` using `get_callers` or `get_type_flow` to understand how a changed symbol affects the rest of the application.
*   **Handoff:** The codebase is mutated, tests pass.

### State 4: Adversarial Verification
*   **Required Superpower Skill:** `verification-before-completion`
*   **Action:** The Orchestrator delegates to the `adversary` or `verifier` agent.
*   **Interaction:** The agent MUST invoke the `verification-before-completion` skill. It must ruthlessly challenge the implementer's success claims and demand empirical proof (test outputs).
*   **MCP Integration:** The `verifier` uses `indxr` (`get_diff_summary`, `get_public_api`) to ensure no new architectural violations were introduced.
*   **Handoff:** The state is physically committed to disk as a verification report.

### State 5: Wrap-up & Review
*   **Required Superpower Skills:** `finishing-a-development-branch` and `requesting-code-review`
*   **Action:** Control returns to the Orchestrator.
*   **Interaction:** The Orchestrator invokes `finishing-a-development-branch` to manage Git commit cleanup, and `requesting-code-review` to generate a PR description.
*   **Handoff:** Branch is ready for human review or merging.

---

## Quick Reference: Indxr MCP Tools
*   `find`: Find files/symbols by concept, name, callers, or signature pattern.
*   `summarize`: Understand files/symbols without reading source.
*   `explain_symbol`: Signature, doc comment, relationships, metadata.
*   `get_public_api`: Public declarations with signatures for a module.
*   `get_callers`: Find who references a symbol across all files.
*   `get_health`: Codebase health summary, and complexity metrics. (Index freshness is maintained automatically).
*   `get_diff_summary`: Structural changes since a git ref or GitHub PR.
*   `get_dependency_graph`: Map file and symbol dependencies.
*   `get_tree`: Directory/file tree.
*   `search_relevant`: Multi-signal relevance search.

## Quick Reference: Superpower Skills
*   `brainstorming`
*   `writing-plans`
*   `test-driven-development`
*   `systematic-debugging`
*   `verification-before-completion`
*   `finishing-a-development-branch`
*   `requesting-code-review`
