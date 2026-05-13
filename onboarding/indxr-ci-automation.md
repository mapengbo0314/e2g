# Setting up Automated Indxr Updates via CI/CD

When onboarding a new repository, follow these steps to ensure the `indxr` codebase wiki automatically updates on every Pull Request.

## Step 1: Create the Helper Script

Create a script at `scripts/update_index.sh` to handle the execution and commit logic. This script is designed to handle Gemini (via CLI) or Anthropic/OpenAI (native).

```bash
#!/usr/bin/env bash
set -e

# Ensure we are in the project root
cd "$(dirname "$0")/.."

echo "=== Running indxr wiki update ==="

# Check for LLM API keys
if [ -z "$GEMINI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: No LLM API key found in environment."
    exit 1
fi

# Configuration for Gemini (requires INDXR_LLM_COMMAND bypass)
if [ -n "$GEMINI_API_KEY" ]; then
    echo "Using Gemini CLI as the LLM backend..."
    export GEMINI_CLI_TRUST_WORKSPACE=true
    export INDXR_LLM_COMMAND="gemini --skip-trust -p \"\""
fi

# Run the update
indxr wiki update

echo "=== Checking for index changes ==="

if git status --porcelain .indxr/ | grep -q "^"; then
    echo "Changes detected in .indxr/. Proceeding to commit."
    
    # Configure git bot user
    git config --local user.email "41898282+github-actions[bot]@users.noreply.github.com"
    git config --local user.name "github-actions[bot]"
    
    # Stage and commit
    git add .indxr/
    git commit -m "chore(docs): auto-update indxr wiki [skip ci]"
    
    # Pull with rebase to avoid conflicts, then push
    git pull --rebase origin $(git rev-parse --abbrev-ref HEAD)
    git push origin HEAD
    
    echo "Successfully updated and committed the index."
else
    echo "No changes detected in the index. Exiting."
fi
```

Make it executable:
```bash
chmod +x scripts/update_index.sh
```

## Step 2: Add the GitHub Action

Create the workflow file at `.github/workflows/update-indexer.yml`.

```yaml
name: Update Codebase Index

on:
  pull_request:
    types: [opened, synchronize, reopened]
    branches:
      - main
      - master

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  update-index:
    runs-on: ubuntu-latest
    permissions:
      contents: write # Required to push commits
      pull-requests: write

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.ref }}
          fetch-depth: 0

      - name: Setup Rust and Install indxr
        run: |
          cargo install indxr --features wiki

      - name: Setup Node.js (for Gemini CLI)
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Gemini CLI (Only needed for Gemini)
        run: |
          npm install -g @google/gemini-cli

      - name: Run Indexer Update Script
        env:
          # Inject whichever keys are configured in your repository secrets
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: ./scripts/update_index.sh
```

## Step 3: Configure GitHub Secrets

1. Go to **Settings > Secrets and variables > Actions** in the GitHub repository.
2. Add your provider's key as a secret:
   - **Gemini:** `GEMINI_API_KEY`
   - **Claude:** `ANTHROPIC_API_KEY`
   - **OpenAI:** `OPENAI_API_KEY`

## Why Gemini requires more setup
`indxr` is a Rust binary that natively understands `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`. To use Gemini, we use the `@google/gemini-cli` as a "shim" by setting the `INDXR_LLM_COMMAND`. The script handles this automatically if it detects a `GEMINI_API_KEY`.
