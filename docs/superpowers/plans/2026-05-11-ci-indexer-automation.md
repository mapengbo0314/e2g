# CI Indexer Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automate the `indxr` wiki generation on PR updates via a GitHub Action that commits changes directly back to the PR branch.

**Architecture:** A GitHub Action triggers on `pull_request` events, injecting a stored API key. It calls a local bash helper script (`scripts/update_index.sh`) which executes `npx --yes indxr wiki update`, checks for modified files in `.indxr/`, and commits them back to the active branch if changes occurred.

**Tech Stack:** GitHub Actions (YAML), Bash, `indxr` CLI.

---

### Task 1: Create the Helper Script

**Files:**
- Create: `scripts/update_index.sh`

- [ ] **Step 1: Write the helper script implementation**
Create `scripts/update_index.sh` with the following content:
```bash
#!/usr/bin/env bash
set -e

# Ensure we are in the project root
cd "$(dirname "$0")/.."

echo "=== Running indxr wiki update ==="

# Fallback to checking keys if needed
if [ -z "$GEMINI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: No LLM API key found in environment."
    echo "Please ensure GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY is set."
    exit 1
fi

# Run the update (assuming 'update' is the command to refresh an existing wiki)
# Using npx --yes to ensure it runs non-interactively
npx --yes indxr wiki update

echo "=== Checking for index changes ==="

# Check if anything in .indxr/ changed
if git status --porcelain .indxr/ | grep -q "^"; then
    echo "Changes detected in .indxr/. Proceeding to commit."
    
    # Configure git bot user
    git config --local user.email "41898282+github-actions[bot]@users.noreply.github.com"
    git config --local user.name "github-actions[bot]"
    
    # Stage the changes
    git add .indxr/
    
    # Commit
    git commit -m "chore(docs): auto-update indxr wiki [skip ci]"
    
    # Pull with rebase to avoid conflicts if the user pushed concurrently
    # Note: We expect the CI environment to be checked out to the PR HEAD
    git pull --rebase origin $(git rev-parse --abbrev-ref HEAD)
    
    # Push back to the current branch
    git push origin HEAD
    
    echo "Successfully updated and committed the index."
else
    echo "No changes detected in the index. Exiting."
fi
```

- [ ] **Step 2: Make the script executable**

Run: `chmod +x scripts/update_index.sh`
Expected: Command succeeds silently.

- [ ] **Step 3: Run the script locally (Validation)**

Run: `GEMINI_API_KEY="dummy" ./scripts/update_index.sh`
Expected: Should attempt to run `indxr`, likely failing due to the dummy key, but it proves the script runs and checks for the key. (If it passes, it proves no changes were needed).

- [ ] **Step 4: Commit**

```bash
git add scripts/update_index.sh
git commit -m "feat(ci): add helper script for index auto-updates"
```

---

### Task 2: Create the GitHub Action Workflow

**Files:**
- Create: `.github/workflows/update-indexer.yml`

- [ ] **Step 1: Write the workflow YAML**
Create `.github/workflows/update-indexer.yml` with the following content:
```yaml
name: Update Codebase Index

on:
  pull_request:
    types: [opened, synchronize, reopened]
    branches:
      - main
      - master

# Ensure only one run per PR at a time to prevent commit race conditions
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  update-index:
    runs-on: ubuntu-latest
    permissions:
      contents: write # Required to push commits to the PR branch
      pull-requests: write

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4
        with:
          # We need to checkout the actual branch HEAD, not the merge commit,
          # so we can push back to it.
          ref: ${{ github.event.pull_request.head.ref }}
          # Fetch full depth so we can push
          fetch-depth: 0

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Run Indexer Update Script
        env:
          # Assuming the user stores their key in a secret named GEMINI_API_KEY
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          # Provide fallbacks if they use other providers
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: ./scripts/update_index.sh
```

- [ ] **Step 2: Verify YAML syntax**

Run: `cat .github/workflows/update-indexer.yml`
Expected: Output matches the step above. No syntax errors visually apparent.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/update-indexer.yml
git commit -m "ci: add workflow to trigger indexer updates on PR"
```
