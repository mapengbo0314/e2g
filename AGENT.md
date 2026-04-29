# Agent Workspace

This repository now uses a single `_agents/` workspace for both lightweight
workflow assets and the more formal multi-agent registry modeled after your
reference screenshots.

The naming here is intentionally general. Even when source material says
"Gemini agent," this workspace treats the system as a broader agent platform.

## Primary goals

1. Keep the indexing reference focused on the essential Python core.
2. Accept videos, screenshots, and walkthroughs as structured source inputs.
3. Route extracted information into the correct repository files.
4. Prepare the codebase for an eventual staged migration from Python to Kotlin
   or Java.

## Workspace layout

- `indexing-reference/`: Essential indexing and summarization scaffold kept as reference material.
- `_agents/agents/`: Formal role-based agent definitions with `agent.json` and `config.yaml`.
- `_agents/rules/`: Shared operating rules for orchestration and media transcription.
- `_agents/skills/`: Reusable structured skills and lightweight routing helpers.
- `_agents/mcps/`: MCP registry notes and connector expectations.
- `_agents/sub_agents/`: Focused worker roles for transcription and file writing.
- `_agents/workflows/`: End-to-end workflows the harness can run.
- `_agents/templates/`: Output templates for transcript-to-file conversion.

## Formal agent roles

- `planner`: breaks work into bounded tasks and routes incoming evidence.
- `architect`: designs system structure and migration sequencing.
- `codesigner`: shapes interfaces, prompts, and reusable patterns.
- `implementer`: applies concrete repository changes.
- `designdoc_drafter`: turns architecture and media findings into docs.
- `reviewer`: checks correctness, coherence, and maintainability.
- `verifier`: runs final QA and robustness checks.

## Current workflow direction

The first operational workflow remains `video_transcriber`. Its job is to:

1. Accept a video or extracted frames.
2. Pull visible text, spoken explanation, filenames, and directory hints.
3. Match that information to the right path in this workspace.
4. Convert the content into project-specific source or notes.
5. Stage the result in the corresponding file for review.

## Migration direction

Python is still the execution language for this scaffold today. The agent
system should preserve that while steadily collecting the design knowledge
needed to port stable subsystems into Kotlin or Java later.
