#!/bin/bash

# Exit on error
set -e

# Help message
if [ "$1" == "-h" ] || [ "$1" == "--help" ] || [ -z "$1" ]; then
    echo "Usage: $0 <target_directory_name>"
    echo "Example: $0 index-agents"
    exit 1
fi

TARGET_NAME=$1

# Get the absolute path of the source directory (parent of this script's directory)
SOURCE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
PARENT_DIR="$( dirname "$SOURCE_DIR" )"
TARGET_DIR="$PARENT_DIR/$TARGET_NAME"

echo "=== Cloning Boilerplate Agent Harness ==="
echo "Source: $SOURCE_DIR"
echo "Target: $TARGET_DIR"

if [ -d "$TARGET_DIR" ]; then
    echo "Error: Target directory '$TARGET_DIR' already exists."
    exit 1
fi

# Ensure parent directory of target exists
mkdir -p "$PARENT_DIR"

# Perform the copy using rsync for robust exclusion handling
# -a: archive mode
# -v: verbose
# --exclude='workspace/artifacts/*': keep the directory but exclude contents
# --exclude='__pycache__/': exclude python cache
# --exclude='*.log': exclude log files
if command -v rsync >/dev/null 2>&1; then
    rsync -av "$SOURCE_DIR/" "$TARGET_DIR/" \
        --exclude='workspace/artifacts/*' \
        --exclude='__pycache__/' \
        --exclude='*.log' \
        --exclude='.git/' \
        --exclude='.DS_Store'
else
    echo "rsync not found, falling back to cp (exclusions may be less precise)..."
    cp -R "$SOURCE_DIR" "$TARGET_DIR"
    # Clean up excluded patterns manually
    find "$TARGET_DIR" -name "__pycache__" -type d -exec rm -rf {} +
    find "$TARGET_DIR" -name "*.log" -type f -delete
    rm -rf "$TARGET_DIR/workspace/artifacts/"*
    rm -rf "$TARGET_DIR/.git"
fi

# Ensure workspace/artifacts exists even if it was empty or not copied
mkdir -p "$TARGET_DIR/workspace/artifacts"

echo "------------------------------------------"
echo "SUCCESS: Harness cloned to $TARGET_DIR"
echo "Note: workspace/artifacts/ has been initialized as an empty directory."
