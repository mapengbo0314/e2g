# Orchestrator Rules

The orchestrator coordinates agent roles for planning, implementation,
review, verification, and media-driven repository population.

## Flow

1. Route incoming work to `planner` first when scope is unclear.
2. Use `architect` for system structure or migration strategy.
3. Use `implementer` for concrete file changes.
4. Use `reviewer` before large merges or major workflow shifts.
5. Use `verifier` for final QA, edge cases, and robustness checks.

## Media ingestion rule

When the source is a video, first extract transcript and visible file hints,
then map content to repository paths before generating edits.
