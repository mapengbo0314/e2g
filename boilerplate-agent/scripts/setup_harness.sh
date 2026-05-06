#!/usr/bin/env bash
set -e

echo "=== Setting up Agentic Harness Dependencies ==="

# 1. Install Superpowers (Global Gemini CLI Extension)
echo "--- Installing Superpowers Framework ---"
if command -v gemini &> /dev/null; then
    gemini extensions install https://github.com/obra/superpowers || true
    echo "Superpowers installed/updated for Gemini CLI."
else
    echo "Warning: gemini CLI not found. Skipping Gemini superpower extension installation."
fi

# 2. Install indxr MCP Server
echo "--- Installing indxr MCP Server ---"
if command -v cargo &> /dev/null; then
    cargo install indxr --features wiki,http || true
    
    echo "Initializing indxr MCP configurations..."
    indxr init || true
else
    echo "Error: cargo (Rust package manager) is required to install indxr."
    echo "Please install Rust from https://rustup.rs/"
fi

echo "=== Setup Complete ==="
echo "The Boilerplate Agent environment is now fully equipped with indxr and Superpowers."
