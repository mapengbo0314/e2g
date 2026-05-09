# Setup Harness Automation Design

## Goal
Automate the installation of the 'superpowers' extension and 'mattpocock/skills' within the `setup_harness.sh` script, ensuring non-interactive execution and prioritizing local (workspace) scope where applicable.

## Approach
Update `.gemini/scripts/setup_harness.sh` to use the appropriate Gemini CLI installation commands with the `--consent` flag to bypass security prompts.

1.  **Superpowers (Extension):** Extensions in Gemini CLI are installed globally. We will automate this using `gemini extensions install https://github.com/obra/superpowers --consent`.
2.  **Matt Pocock Skills (Skill):** Skills can be scoped locally. We will automate this using `gemini skills install https://github.com/mattpocock/skills --scope workspace --consent`. This places the skills inside the project's `.gemini/skills/` directory.

## File Changes
*   **File:** `.gemini/scripts/setup_harness.sh`
*   **Change:** Replace the existing `gemini extensions install` commands with the automated commands detailed above. Ensure the commands are suffixed with `|| true` to prevent the script from failing if the user is offline or the installation encounters a non-critical error.

## Dependencies
*   Requires `gemini` CLI to be available in the user's `$PATH`.
*   Requires internet access for the initial git cloning/fetching.
