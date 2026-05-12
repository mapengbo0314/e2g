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

# Run the update
echo "Executing indxr with INDXR_LLM_COMMAND='gemini -p \"\"'"
export INDXR_LLM_COMMAND="gemini -p \"\""
indxr wiki update

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
