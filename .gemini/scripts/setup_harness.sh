#!/usr/bin/env bash
set -e

# Check for indxr API keys
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: indxr requires an ANTHROPIC_API_KEY or OPENAI_API_KEY for background wiki updates."
    echo "Background auto-indexing will be disabled until a key is exported in your terminal."
    echo "Example: export ANTHROPIC_API_KEY='sk-ant-...' "
    echo ""
fi

echo "=== Setting up Superpowers for Gemini CLI ==="
if command -v gemini &> /dev/null; then
    echo "Installing Superpowers extension..."
    gemini extensions install https://github.com/obra/superpowers --consent || true
    
    echo "Installing Matt Pocock skills..."
    # The mattpocock/skills repository contains multiple nested skills.
    # We must clone it temporarily and install each valid skill directory individually.
    TEMP_DIR=$(mktemp -d)
    git clone --depth 1 https://github.com/mattpocock/skills "$TEMP_DIR" &> /dev/null
    
    # Find all directories containing a SKILL.md (excluding deprecated ones to save time/space)
    find "$TEMP_DIR" -type f -name "SKILL.md" | grep -v "/deprecated/" | while read -r skill_file; do
        skill_dir=$(dirname "$skill_file")
        echo "Installing skill from $(basename "$skill_dir")..."
        gemini skills install "$skill_dir" --scope workspace --consent || true
    done
    
    rm -rf "$TEMP_DIR"
    
    echo "Adding indxr to Gemini CLI project MCP configuration..."
    indxr_serve_args_str="serve --watch --wiki-auto-update --all-tools"
    gemini mcp add indxr bash -c "cd '/Users/pengbolicious/pengbo-apps/e-2-g' && indxr $indxr_serve_args_str" -e GEMINI_API_KEY=\$GEMINI_API_KEY -e ANTHROPIC_API_KEY=\$ANTHROPIC_API_KEY -e OPENAI_API_KEY=\$OPENAI_API_KEY || true
else
    echo "Warning: gemini command not found."
fi

echo "To activate it, run Gemini from the project root and use '/mcp reload'."
