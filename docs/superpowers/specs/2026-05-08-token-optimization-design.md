# Token Optimization via Prompt Deduplication and Context Intake

## 1. Problem
The current Agentic Harness suffers from severe token bloat in two primary areas:
1.  **Agent Prompt Bloat (The Boilerplate Tax):** Every specialized agent (e.g., `implementer.md`, `architect.md`) contains an identical ~1,500-token block of "Core Mandates" and "Workspace Guidelines". When workflows involve multiple agents in a chain, this redundant context compounds, wasting tokens and increasing latency.
2.  **Raw Log Context Bloat:** When a user pastes a massive stack trace or CI failure, the Orchestrator (and subsequently, every delegated subagent) receives the raw, uncompressed text. This violates the Orchestrator's "Zero Work Rule" by forcing it to process raw diagnostic data and floods the context window with vendor frames and repetitive noise.

## 2. Plan

We will resolve this through a two-part architectural update: **Platform-Aware Deduplication** and **Failure Context Triage**.

### Part 1: Platform-Aware Agent Prompt Deduplication
Extract the duplicated rules into a shared file to drastically shrink individual agent prompts.

1.  **Extract Shared Mandates:** 
    *   Create `boilerplate-agent/rules/core_mandates.md` containing the "Core Mandates" and "Workspace Guidelines".
2.  **Update `minting_engine.py`:**
    *   Remove the hardcoded `core_mandates` string generation.
    *   Introduce platform-aware injection logic when generating agent markdown files:
        *   If `platform == gemini`: Prepend `@.gemini/rules/core_mandates.md`
        *   If `platform == claude`: Prepend `@.claude/rules/core_mandates.md`
        *   If `platform == cursor` (or custom): Fallback to injecting the raw text inline (as Cursor lacks a robust file-inclusion syntax for system prompts).

### Part 2: The Triage Delegation (Stack Trace Intake)
Introduce a mandatory compression step before debugging tasks.
### 2. Pre-Delegation Triage Layer (The "Spoke" Guardrail)
1.  **Install Compression Skill:**
    *   Update the `setup_harness.sh` script templates in `minting_engine.py` to automatically install the `token-optimizer` skill during onboarding.
2.  **Update Orchestrator Routing Rules:**
    *   Modify `boilerplate-agent/rules/dispatch_rules.md` (and related Orchestrator instructions) to include a strict pre-delegation mandate:
        *   *"If the user input contains a raw stack trace, CI failure, or explicitly requests a bug fix, DO NOT read the logs directly. Delegate to a triage agent (e.g., `architect` or `@generalist`) and instruct them to write a compressed artifact to `artifacts/triage.md`. When delegating to the `implementer`, pass `artifacts/triage.md` as the primary diagnostic frame, but always include the original user prompt to preserve intent."*

## 3. Alternatives Considered
*   **Orchestrator Prepending Mandates Runtime:** We considered keeping agents lean but having the Orchestrator inject the rules dynamically into the delegation prompt. *Rejected:* This bloats the Orchestrator's own context window, defeating the token-saving goal.
*   **`@include` for all platforms:** We considered using `@include` blindly. *Rejected:* Goldfish review identified this would break Claude Code and Cursor.
*   **Orchestrator Running the Decoder Skill:** We considered having the Orchestrator run the stack trace compression itself. *Rejected:* Violates the "Zero Work Rule" and still forces the large raw trace into the Hub's context window.

## 4. Sphinch Marks
- [ ] Verify `boilerplate-agent/rules/core_mandates.md` exists and contains the "Core Mandates" and "Workspace Guidelines".
- [ ] Verify `harness/minting_engine.py` generates agent files using `@` inclusion for `gemini` and `claude` platforms pointing to `rules/core_mandates.md`.
- [ ] Verify `boilerplate-agent/rules/dispatch_rules.md` contains the new mandatory Failure Context Triage routing rule.
