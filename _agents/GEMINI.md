# General Agent Rules

The following rules apply to agent behavior, coding style guidance, review
quality, and migration planning for this workspace.

## Language stance

- The current service is Python-first.
- New agent outputs should preserve working Python unless the task explicitly
  asks for a migration artifact.
- A strategic project goal is to progressively translate stable Python modules
  into Kotlin or Java once the behavior is fully understood.

## Python coding style

- Use clear module boundaries and small, composable functions.
- Prefer dataclasses and typed interfaces for structured state.
- Keep imports explicit and grouped consistently.
- Use docstrings for public classes, workflows, and non-obvious modules.
- Favor deterministic transforms over hidden side effects.

## Kotlin and Java migration guidance

- Treat Kotlin as the default JVM landing zone unless Java is requested.
- Preserve behavior before optimizing structure.
- Migrate one bounded subsystem at a time.
- Generate design notes before large language migrations.
- Keep test fixtures and example inputs aligned across source and target
  implementations.

## Testing and verification

- Planner output should define expected behavior before implementation.
- Reviewer output should focus on correctness, maintainability, and migration
  risk.
- Verifier output should check edge cases, parsing fidelity, and workflow
  robustness.

## Documentation expectations

- Every new workflow should state its inputs, outputs, and failure modes.
- Media-derived code should reference source evidence when possible.
- Migration plans should note what is preserved, what is re-modeled, and what
  remains unknown.
