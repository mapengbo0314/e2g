# User Guide: Onboarding a New Repository with Harness-WF

This guide explains how to ground a completely new project into the Superpowers Agentic Harness using an existing `indxr` bundle.

## Prerequisites
- `harness-wf` installed (`pip install -e .` from this repo root).
- `indxr` CLI installed and configured.
- Your project directory (e.g., `~/my-awesome-app`).

---

## Step 1: Pre-generate the Codebase Index (Indxr Bundle)
Before running the harness, we utilize the `indxr` tool to create a semantic map of your repository.

```bash
# 1. Navigate to your project
cd ~/my-awesome-app

# 2. Set your LLM API Key (Indxr uses this to process the code)
export ANTHROPIC_API_KEY="sk-..." 

# 3. Generate the wiki bundle
# Replace {my-awesome-app} with your project name or identifier
indxr wiki generate {my-awesome-app}
```

This creates a hidden `.indxr/` folder in your project root containing the full knowledge base of your codebase.

---

## Step 2: Initialize the Agentic Harness
Now, run the `harness-wf` tool to mint your agents and universal routing pointers. We use the `--bundle` flag to point to the existing index so the harness can instantly understand your repo.

```bash
# Initialize the harness using Gemini as the orchestrating LLM
# and the existing index for context
harness-wf init --project-path . --llm gemini --bundle .indxr --ddd
```

### What to expect:
- **DDD Alignment**: The CLI will ask you a series of Domain-Driven Design questions based on your code.
- **Agent Discovery**: It will recommend specialized agents (e.g., `trust-agent`, `auth-expert`) tailored to your project.
- **Omni-Compatibility**: It will drop `GEMINI.md`, `CLAUDE.md`, and `.cursorrules` pointers into your root.
- **Segregated Scripts**: Hidden platform folders (e.g., `.gemini/`, `.claude/`) will be created with their own setup scripts.

---

## Step 3: Platform Setup
Once the minting is finished, run the setup script for the specific tool you want to use for this project.

### If using Gemini CLI:
```bash
sh .gemini/scripts/setup_harness.sh
```

### If using Claude Code:
```bash
sh .claude/scripts/setup_harness.sh
```

### If using Cursor:
```bash
sh .cursor/scripts/setup_harness.sh
```

---

## Success!
Your repository is now fully grounded. You can now open your preferred AI client (Gemini, Claude, or Cursor), and it will automatically follow the pointers to `_agents/AGENTS.md`, assume the **Orchestrator** role, and follow the mandated Superpower workflows.
