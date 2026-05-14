# Engineering Requirements for Long-Running (10+ Hour) Autonomous Agents

## Overview
This document defines the strict engineering standards and architectural patterns required to build a resilient agent harness capable of sustained execution (10+ hours). It is designed to mitigate the systemic failure modes identified in the Adversary Analysis (e.g., state decay, trajectory drift, and environmental instability).

---

## 1. State Persistence and Memory Architecture (The "State Decay" Mitigation)
**Problem**: Context window exhaustion and lossy summarization lead to "semantic entropy" and mission amnesia.

### Standards:
- **Requirement 1.1: Immutable Event Sourcing**: The harness must maintain an immutable, append-only log of every tool invocation, observation, and internal thought (the "Timeline"). This log serves as the absolute source of truth, independent of the LLM's current context window.
- **Requirement 1.2: Structured State Reification**: Every $N$ turns, the harness must trigger a "State Extraction" process. This process distills the raw timeline into a structured "World Model" (e.g., current file structure, known variables, task status). This structured model is injected into the prompt as a fixed reference, preventing the "summary of a summary" degradation.
- **Requirement 1.3: Tiered Memory Management**:
    - **Active Context**: Current sub-task details + Mission Profile.
    - **Working Memory**: Recent timeline events (sliding window).
    - **Semantic Archive**: RAG-based lookup into the full 10-hour history for historical discovery retrieval.
- **Requirement 1.4: "North Star" Persistence**: The original user prompt and high-level mission constraints must be pinned (immutable) in the system prompt. They are exempt from any truncation or summarization logic.

---

## 2. Verification Gates and Trajectory Control (The "Drift" Mitigation)
**Problem**: Small errors compound into global failure without independent, non-probabilistic validation.

### Standards:
- **Requirement 2.1: Deterministic Verification Gates**: High-risk transitions (e.g., "Implementation complete", "Refactor finished") MUST pass a suite of non-LLM validators (Unit tests, Linters, Type-checkers, File-existence checks) before the agent can proceed to the next milestone.
- **Requirement 2.2: Checkpoint & Rollback Protocol**: The harness must implement a "Git-like" state management system for the workspace. If the Verification Gate fails $X$ times, the harness must force a "Rollback" to the last known-good state (checkpoint) rather than allowing the agent to attempt recursive "fixes" on corrupted code.
- **Requirement 2.3: Anomaly Detection (Loop Breaking)**: The harness must monitor for "circular reasoning" or "repetitive tool-calling" patterns. If an agent repeats the same tool/argument pair three times with no state change, the harness must interrupt the loop and force a "Strategy Pivot" (e.g., clearing the working memory or escalating to HITL).
- **Requirement 2.4: External Supervisor Layer**: A secondary, low-cost model or rule-based engine should monitor the agent's progress against the "Goal Tree" to detect semantic drift early.

---

## 3. Resilience and Resource Management (The "Environmental Friction" Mitigation)
**Problem**: 10-hour runs are statistically guaranteed to hit transient failures and resource limits.

### Standards:
- **Requirement 3.1: Full Serialization (Hydration/Dehydration)**: The entire harness state (Task DAG, Event Log, World Model, Token Usage) must be serializable to persistent storage (e.g., JSON/SQLite). The harness must be capable of "resuming" from a file after a host reboot or process crash.
- **Requirement 3.2: Tool Idempotency**: All side-effecting tools (Write, Edit, Delete, Run Command) must be implemented with idempotency guards. For example, a "Create Directory" tool must check if the directory exists and is writable before attempting the operation.
- **Requirement 3.3: Exponential Backoff & Jitter**: All external API calls (LLM, Web Search, etc.) must utilize standard resilience patterns for 429 (Rate Limit) and 5xx (Server Error) responses to survive transient outages.
- **Requirement 3.4: Budget Circuit Breakers**: The harness must enforce hard caps on:
    - **Total Token Count** (Input/Output).
    - **Financial Cost** (USD).
    - **Wall-clock Time**.
    When a limit is reached, the harness must "Dehydrate" state and pause execution, requiring explicit human authorization to resume.

---

## 4. Objective Completion and Termination Semantics (The "Infinite Loop" Mitigation)
**Problem**: Agents lack an internal "Stop" signal rooted in objective success, leading to infinite refinement.

### Standards:
- **Requirement 4.1: Goal Tree Decomposition**: The mission must be decomposed into a Directed Acyclic Graph (DAG) of sub-tasks. Each sub-task must have an explicit "Definition of Done" (DoD).
- **Requirement 4.2: Machine-Verifiable DoD**: Completion criteria must be expressed as verifiable predicates (e.g., `file_exists(PATH) AND exit_code(TEST_CMD) == 0`). The agent is not "done" until the harness verifies these predicates.
- **Requirement 4.3: Hard Termination Conditions**: Every task must have a "Max Turn" limit. If the limit is reached without the DoD being met, the task is marked as "FAILED" and the agent must move to a contingency plan or stop.
- **Requirement 4.4: Artifact Handoff Validation**: Before termination, the agent must generate a "Final Report" artifact that maps original requirements to verified results. The harness must verify that all artifacts mentioned in the report actually exist on disk.

---

## Summary of Architectural Shift
To survive 10+ hours, the system must shift from a **"Loop-driven LLM"** to an **"Orchestrated State Machine"** where the LLM is merely a reasoning engine used by a robust, deterministic supervisor. The supervisor manages the memory, verifies the work, and ensures the environment remains viable.
