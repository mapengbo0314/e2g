# 10+ Hour Long-Running Agent Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a comprehensive analysis report on the systemic requirements for 10+ hour long-running agent harnesses, utilizing the `@adversary` and `@reviewer` subagents.

**Architecture:** Sequential agent dispatch. `@adversary` generates the failure modes, which are saved to an intermediate artifact. `@reviewer` then consumes that artifact and generates the success criteria and architectural requirements. Finally, a synthesis task combines them.

**Tech Stack:** `invoke_agent` tool, markdown artifacts.

---

### Task 1: Generate Adversarial Failure Modes

**Files:**
- Create: `artifacts/adversary_long_running_analysis.md`

- [ ] **Step 1: Dispatch @adversary**

Use the `invoke_agent` tool to dispatch the `@adversary` subagent.

**Agent:** `adversary`
**Prompt:**
```markdown
Read the design spec at `docs/superpowers/specs/2026-05-11-long-running-agent-analysis-design.md`.

Your task is to generate the "Adversary Output" for the four Core Analysis Areas defined in the spec. You must dismantle the premise of a naive 10+ hour agent run and detail the precise mathematical, logical, and environmental points of failure.

Write your complete analysis to `artifacts/adversary_long_running_analysis.md`.
```

- [ ] **Step 2: Verify Artifact Creation**

Run: `cat artifacts/adversary_long_running_analysis.md`
Expected: The file exists and contains the @adversary's analysis.

### Task 2: Generate Reviewer Success Criteria

**Files:**
- Create: `artifacts/reviewer_long_running_requirements.md`

- [ ] **Step 1: Dispatch @reviewer**

Use the `invoke_agent` tool to dispatch the `@reviewer` subagent.

**Agent:** `reviewer`
**Prompt:**
```markdown
Read the design spec at `docs/superpowers/specs/2026-05-11-long-running-agent-analysis-design.md`.
Read the adversary's failure analysis at `artifacts/adversary_long_running_analysis.md`.

Your task is to generate the "Reviewer Output" for the four Core Analysis Areas defined in the spec. You must define the strict engineering standards, architectural patterns, and systemic infrastructure required to survive the failure modes identified by the adversary.

Write your complete requirements specification to `artifacts/reviewer_long_running_requirements.md`. Do NOT use the wiki tools, just write the markdown file.
```

- [ ] **Step 2: Verify Artifact Creation**

Run: `cat artifacts/reviewer_long_running_requirements.md`
Expected: The file exists and contains the @reviewer's requirements.

### Task 3: Synthesize Final Report

**Files:**
- Create: `artifacts/long_running_agent_framework.md`

- [ ] **Step 1: Dispatch Generalist to Synthesize**

Use the `invoke_agent` tool to dispatch the `@generalist` subagent to synthesize the final report.

**Agent:** `generalist`
**Prompt:**
```markdown
Read the adversary's analysis at `artifacts/adversary_long_running_analysis.md`.
Read the reviewer's requirements at `artifacts/reviewer_long_running_requirements.md`.

Your task is to synthesize these two documents into a single, cohesive, high-quality markdown report titled `artifacts/long_running_agent_framework.md`. 

The report should be structured around the four core areas from the original design spec:
1. State Decay, Context Bloat, and Amnesia
2. Compounding Failure and Trajectory Drift
3. Environmental Friction and Resource Exhaustion
4. Goal Coherence and Completion Semantics

For each area, present the Adversary's failure modes followed by the Reviewer's required architectural solutions. Add a brief executive summary at the beginning.
```

- [ ] **Step 2: Verify Final Artifact**

Run: `ls -la artifacts/long_running_agent_framework.md`
Expected: The file exists.
