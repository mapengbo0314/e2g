# Agents Workspace

This directory is the single home for the repository's agent system.

## Structure

- `agents/`: formal role definitions with `agent.json` and `config.yaml`
- `rules/`: orchestration and media-transcription rules
- `skills/`: reusable agent capabilities
- `mcps/`: MCP registry notes
- `sub_agents/`: focused worker roles
- `workflows/`: end-to-end workflows
- `templates/`: output templates for structured generation

## Current emphasis

The active flow is still video-driven repository population:

1. read media
2. extract transcript and visible file context
3. route content to the right path
4. draft repository updates
5. verify fidelity before finalizing
