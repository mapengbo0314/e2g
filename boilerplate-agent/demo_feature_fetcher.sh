#!/bin/bash

# demo_feature_fetcher.sh
# This script demonstrates how to invoke the Gemini CLI to pass an indexing bundle path
# to the 'feature-fetcher' agent to mint a new domain expert.

# 1. Define the path to the indexing bundle. 
# This bundle contains the AST and metadata needed by the agent to understand the codebase.
BUNDLE_PATH="./workspace/artifacts/indexing_bundle.json"

# 2. Define the target feature or domain expert we want to mint.
TARGET_FEATURE="Authentication Expert"

# 3. Construct the prompt for the Gemini CLI.
# We use the '@' syntax to target the specific 'feature-fetcher' agent.
# We explicitly provide the BUNDLE_PATH so the agent knows where to look for source context.
PROMPT="@feature-fetcher I need to mint a new domain expert for: $TARGET_FEATURE. 
Please analyze the codebase using the indexing bundle at $BUNDLE_PATH and 
generate the necessary configuration and agent rules to specialize in this domain."

# 4. Invoke the Gemini CLI.
# Ensure you have 'gemini-cli' installed and configured in your PATH.
echo "Invoking Gemini CLI for feature: $TARGET_FEATURE..."
echo "Using indexing bundle: $BUNDLE_PATH"

gemini-cli "$PROMPT"

# Note: The output will be streamed to the console. 
# The agent will typically generate new files in the appropriate _agents/ directory.
