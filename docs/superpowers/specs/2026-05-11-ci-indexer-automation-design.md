# Automated Indexer Wiki Update via CI/CD

## 1. Overview
This design outlines a GitHub Actions workflow to automatically update the `indxr` wiki bundle whenever a Pull Request is submitted or updated. This ensures that the codebase index remains in sync with the latest code changes before they are merged into the main branch. The updated index is automatically committed directly back to the PR branch.

## 2. Architecture & Components

The solution consists of two primary components:

### 2.1. The Helper Script (`scripts/update_index.sh`)
A dedicated bash script responsible for the execution and version control logic.
*   **Execution:** Runs the `npx --yes indxr wiki update` command to process recent code changes.
*   **Detection:** Uses `git status` to detect if any files within the `.indxr/` directory were modified by the update process.
*   **Commit:** If changes are detected, it configures a bot git user, commits the changes with a standard message (e.g., `chore: auto-update indxr wiki`), and pushes the commit to the active branch.

### 2.2. The GitHub Action Workflow (`.github/workflows/update-indexer.yml`)
The orchestration layer that triggers the helper script in a secure CI environment.
*   **Triggers:** Runs on `pull_request` events.
*   **Environment Setup:** Checks out the repository and configures the Node.js environment required to run `npx indxr`.
*   **Security (API Key Handling):** The workflow securely passes the LLM API key (stored in GitHub Secrets) to the helper script via an environment variable (e.g., `GEMINI_API_KEY`). The key is never logged or exposed.
*   **Permissions:** Requires `contents: write` permissions to allow the default `GITHUB_TOKEN` to push commits back to the PR branch.

## 3. Data Flow
1.  A developer pushes new code to a PR branch.
2.  The GitHub Action triggers and sets up the environment, injecting the API key from Secrets.
3.  The workflow executes `scripts/update_index.sh`.
4.  The script runs the `indxr` CLI, which analyzes the diff and updates the `.indxr/wiki` bundle.
5.  The script detects the changes, commits them, and pushes them back to the PR.
6.  The PR now contains both the developer's code changes and the updated semantic index.

## 4. Error Handling & Edge Cases
*   **No Changes:** If the code changes do not result in index modifications, the script exits cleanly without creating an empty commit.
*   **API Key Missing:** The script should verify the presence of the necessary API key environment variable before attempting to run `indxr`, failing gracefully if it is missing.
*   **Concurrent Pushes:** While standard GitHub Action behavior handles this, the script should pull with rebase immediately before pushing to minimize conflict risk if the developer pushes simultaneously.

## 5. Security Considerations
*   The LLM API key MUST be stored in GitHub Secrets (e.g., `GEMINI_API_KEY`).
*   The action must only grant `contents: write` permissions necessary for the push, adhering to the principle of least privilege.
