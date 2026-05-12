# Final Adversarial Report: Installation Failures Diagnosis

## Symptom Analysis
The following errors were observed during the `init` process and subsequent `setup_harness.sh` execution:
1. `playwright-interactive`: "Invalid GitHub repository source".
2. `nextjs`/`fastapi`: "HTTP Error 404: Not Found".
3. `superpowers`: "Extension already installed" conflict.
4. "Configuration file not found" for various skill URLs.

## Root Cause Analysis

### 1. Incorrect Skill URLs (tools.json & discovery_engine.py)
Many skills point to GitHub "blob" URLs (e.g., `https://github.com/.../SKILL.md`) instead of "raw" URLs (e.g., `https://raw.githubusercontent.com/.../SKILL.md`).
- `urllib.request.urlopen` fetches HTML instead of Markdown when using blob URLs.
- `gemini extensions install` expects a repository URI or a name, not a direct file link, and fails when it finds no `gemini-extension.json`.

Specific 404s:
- `nextjs` and `fastapi` URLs in `tools.json` point to a non-existent `awesome-cline-prompts` repo. The correct source is `PatrickJS/awesome-cursorrules` with a nested directory structure: `rules/<tech>-cursorrules-prompt-file/.cursorrules`.

### 2. Logic Error in `minting_engine.py` (Gemini CLI)
The `mint_workspace` function in `harness/minting_engine.py` generates `setup_harness.sh` by iterating over `selected_skills` and blindly adding `gemini extensions install <url>` for each.
- Skills (Markdown files) should be downloaded to the workspace's `skills/` directory (which `install_workspace_tools` already does).
- Only actual Extensions (Plugins/Repos) should be installed via `gemini extensions install`.

### 3. Redundant `superpowers` Installation
The `using-superpowers` skill is both downloaded to the workspace AND attempted as an extension install, causing conflicts if already present.

## Remediation Plan

### Phase 1: URL Correction
- Update `boilerplate-agent/onboarding/tools.json` with verified raw URLs.
- Update `harness/discovery_engine.py` hardcoded skill URLs to use raw content.

### Phase 2: Refactor Installation Logic
- Modify `harness/minting_engine.py`:
  - Add a check for `type: "extension"` or similar to distinguish from `type: "skill"`.
  - In `setup_harness.sh` generation, only include `gemini extensions install` for real extensions.
  - Fix the `using-superpowers` redundancy.

### Phase 3: Verification
- Run a trial `init` with the corrected URLs.
- Verify `setup_harness.sh` content.
- Ensure all skills are downloaded correctly as Markdown.
