# Codex Support Implementation Plan (Revised v2)

This plan outlines the steps to add support for the **Codex** platform in the Agentic Harness, based on the specific `AGENTS.md` and Subagent specifications found in the OpenAI Codex documentation (`https://developers.openai.com/codex/subagents`).

## Goal
Enable the Harness to mint a single-file agent manifest (`AGENTS.md`) and configuration files optimized for Codex's explicit delegation model.

## Key Technical Specifications
- **Single Manifest**: All specialized agents will be consolidated into a root-level `AGENTS.md` file.
- **H2 Identification**: Codex uses `## agent-name` headers to identify subagents.
- **YAML Metadata**: Each agent entry requires a YAML block immediately following the H2 for `description`, `model`, and `sandbox_mode`.
- **Explicit Delegation**: Our Orchestrator instructions must be updated to use explicit hand-off language (e.g., "Hand over to `reviewer`") to trigger Codex's native spawning logic.

## Proposed Changes

### 1. CLI Integration (`harness/cli.py`)
- [ ] **Add Platform Option**: Include "Codex" in the `platform_selection` menu.
- [ ] **Harness Pathing**: Set the `harness_folder` to the root directory (`.`) specifically for the `AGENTS.md` file, while potentially keeping rules in a `.codex/` or `.agents/` folder.

### 2. Minting Engine Support (`harness/minting_engine.py`)
- [ ] **Consolidated AGENTS.md Generator**: Implement a new function to iterate through `selected_agents` and format them as H2 sections in a single `AGENTS.md` file.
- [ ] **Metadata Mapping**: Map our agent definitions to the Codex YAML fields:
    - `name` -> `## [name]`
    - `role` -> `description`
    - `type` -> `model` selection logic
    - `zone` -> `sandbox_mode` mapping (e.g., `infra` -> `workspace-write`, `logic` -> `workspace-write`, others -> `read-only`).
- [ ] **Rules Conversion**: Translate the `dispatch_rules.md` into a Codex-compatible instructions block for the primary Orchestrator (likely defined as the root instructions in a config file or as the first agent in `AGENTS.md`).

### 3. Template Updates (`boilerplate-agent/`)
- [ ] **Prompt Syntax Injection**: Update `{{SUBAGENT_SYNTAX}}` for Codex to use phrases like "Hand over to `[agent-name]`" or "Have `[agent-name]` do X".
- [ ] **MCP Mapping**: Ensure `mcp_servers` are listed in the YAML metadata for each relevant agent in `AGENTS.md`.

## Execution Strategy
1. **Remediation**: First, fix the hardcoded pathing and parsing issues identified in the [Verification Remediation Plan](file:///Users/pengbolicious/pengbo-apps/e-2-g/artifacts/verification_remediation_plan.md) to ensure the engine is stable.
2. **Implementation**: Build the `CodexManifestGenerator` in `minting_engine.py`.
3. **Verification**: Run a "Codex" mode install and verify the resulting `AGENTS.md` matches the official OpenAI spec exactly.
