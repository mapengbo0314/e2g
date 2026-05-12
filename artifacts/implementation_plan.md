# Implementation Plan: Fix Skill Installation Failures

## Goal
Fix incorrect URLs and installation logic to ensure skills and extensions are correctly installed without conflicts or 404s.

## Proposed Changes

### 1. `boilerplate-agent/onboarding/tools.json`
- Update `playwright-interactive` URL: `https://raw.githubusercontent.com/openai/skills/main/skills/.curated/playwright-interactive/SKILL.md`
- Update `nextjs` URL: `https://raw.githubusercontent.com/PatrickJS/awesome-cursorrules/main/rules/nextjs-14-cursorrules-prompt-file/.cursorrules`
- Update `fastapi` URL: `https://raw.githubusercontent.com/PatrickJS/awesome-cursorrules/main/rules/python-fastapi-cursorrules-prompt-file/.cursorrules`

### 2. `harness/discovery_engine.py`
- Update hardcoded URLs in `discover_agents` and `discover_ddd_context` to use `raw.githubusercontent.com`:
  - `agentic-eval`: `https://raw.githubusercontent.com/github/awesome-copilot/main/skills/agentic-eval/SKILL.md`
  - `prompt-engineer`: `https://raw.githubusercontent.com/Jeffallan/claude-skills/main/skills/prompt-engineer/SKILL.md`

### 3. `harness/minting_engine.py`
- Refactor `install_workspace_tools`:
  - Ensure it respects the `type` field if available.
- Refactor `mint_workspace` (setup script generation):
  - In `scripts_to_generate["gemini"]`, filter `selected_skills` to only install those with `type: "extension"`.
  - Do NOT install Markdown skills via `gemini extensions install`.
  - Fix the redundant `using-superpowers` installation.

## Verification Tasks
- [ ] Run `python harness/cli.py init --project-path . --llm gemini --model gemini-3.1-pro-preview` (use a temp directory if possible).
- [ ] Check `ONBOARDING_DOMAIN.md` for correct URLs.
- [ ] Check `.gemini/scripts/setup_harness.sh` for correct installation commands.
- [ ] Run `sh .gemini/scripts/setup_harness.sh` and verify no errors.
