import os
import shutil
import json
from pathlib import Path

def mint_workspace(target_dir: str, selected_agents: list[dict], project_path: str, platform_choice: str, model_choice: str = None, bundle_override: str = None, boilerplate_dir: str = None, ddd_context: dict = None):
    """Copies boilerplate, injects styled configs, and writes setup prerequisites."""
    target_path = Path(target_dir)
    
    if target_path.exists():
        print(f"Warning: Target directory {target_dir} already exists. Minting may overwrite files.")
        
    def ignore_patterns(dir_path, contents):
        ignored = ['.git', '__pycache__', '.DS_Store']
        return [i for i in contents if i in ignored or i.endswith('.log')]
        
    if boilerplate_dir and os.path.exists(boilerplate_dir):
        shutil.copytree(boilerplate_dir, target_path, ignore=ignore_patterns, dirs_exist_ok=True)
    else:
        print("Error: Boilerplate directory not found.")
        return

    # Save DDD context if provided
    if ddd_context:
        print(f"Saving DDD context to {target_path / 'ddd_context.json'}")
        with open(target_path / "ddd_context.json", "w") as f:
            json.dump(ddd_context, f, indent=2)

        # Write DDD markdown files
        ddd_dir = target_path / "ddd"
        ddd_dir.mkdir(parents=True, exist_ok=True)
        
        if "ubiquitous_language" in ddd_context:
            with open(ddd_dir / "context.md", "w") as f:
                f.write(ddd_context["ubiquitous_language"])
        
        if "translation_map" in ddd_context:
            with open(ddd_dir / "translation_map.json", "w") as f:
                json.dump(ddd_context["translation_map"], f, indent=2)

    # Handle existing bundle / wiki migration
    existing_wiki = False
    if bundle_override:
        # Determine where the .indxr folder is located based on the bundle argument
        if os.path.isdir(bundle_override) and os.path.basename(bundle_override) == ".indxr":
            source_indxr = bundle_override
        elif os.path.isdir(bundle_override):
            source_indxr = os.path.join(bundle_override, ".indxr")
        else:
            source_indxr = os.path.join(os.path.dirname(bundle_override), ".indxr")
            
        target_indxr = os.path.join(project_path, ".indxr")
        
        if os.path.exists(source_indxr) and os.path.abspath(source_indxr) != os.path.abspath(target_indxr):
            print(f"Migrating existing wiki database from {source_indxr} to {target_indxr}...")
            if os.path.exists(target_indxr):
                shutil.rmtree(target_indxr)
            shutil.copytree(source_indxr, target_indxr)
            
        if os.path.exists(os.path.join(target_indxr, "wiki")):
            existing_wiki = True
            
    # Generate specialized setup_harness.sh (Prerequisites)
        # Generate Segregated Setup Scripts
    project_root = Path(project_path)
    escaped_project_path = os.path.abspath(project_path).replace("'", "'\\''")
    scripts_to_generate = {
        ".gemini": f"""#!/usr/bin/env bash
set -e
echo "=== Setting up Superpowers for Gemini CLI ==="
if command -v gemini &> /dev/null; then
    gemini extensions install https://github.com/obra/superpowers || true
    gemini extensions install https://github.com/mattpocock/skills || true
else
    echo "Warning: gemini command not found."
fi

""",
        ".claude": f"""#!/usr/bin/env bash
set -e
echo "=== Setting up Superpowers for Claude Code ==="
echo "To install Superpowers and Skills for Claude Code, run these commands inside the Claude Code interface:"
echo "  /plugin install superpowers@claude-plugins-official"
echo "  /plugin install skills@mattpocock"

# MCP Configuration for Claude
if command -v claude &> /dev/null; then
    echo "Adding indxr to Claude Code global MCP configuration..."
    indxr_serve_args_str="serve --watch --wiki-auto-update"
    claude mcp add indxr -- bash -c "cd '{escaped_project_path}' && indxr $indxr_serve_args_str" || true
fi
""",
        ".cursor": f"""#!/usr/bin/env bash
set -e
echo "=== Setting up Superpowers for Cursor ==="
echo "To install Superpowers and Skills for Cursor, run these commands inside the Cursor Agent chat:"
echo "  /add-plugin superpowers"
echo "  /add-plugin mattpocock/skills"
"""
    }

    for platform_dir, script_content in scripts_to_generate.items():
        script_dir = project_root / platform_dir / "scripts"
        script_dir.mkdir(parents=True, exist_ok=True)
        script_path = script_dir / "setup_harness.sh"
        with open(script_path, "w") as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        
    print("\nTo install skills & MCPs, run the setup_harness.sh script inside your platform's hidden folder (e.g. `sh .gemini/scripts/setup_harness.sh`).")

    # Create an MCP config that points to the indxr server running in the project root
    indxr_serve_args = ["serve", "--watch", "--wiki-auto-update"]
    if model_choice:
        indxr_serve_args.extend(["--wiki-model", model_choice])
    
    indxr_serve_cmd = " ".join(indxr_serve_args)
    # Securely quote the path for bash -c to prevent command injection
    escaped_project_path = os.path.abspath(project_path).replace("'", "'\\''")

    mcp_config = {
        "mcpServers": {
            "indxr": {
                "command": "bash",
                "args": ["-c", f"cd '{escaped_project_path}' && indxr {indxr_serve_cmd}"],
                "env": {
                    "GEMINI_API_KEY": "$GEMINI_API_KEY",
                    "ANTHROPIC_API_KEY": "$ANTHROPIC_API_KEY",
                    "OPENAI_API_KEY": "$OPENAI_API_KEY"
                }
            }
        }
    }
    
    mcp_path = target_path / "mcp.json"
    with open(mcp_path, 'w') as f:
         json.dump(mcp_config, f, indent=2)
         
    # Cursor Multi-Platform Parity
    cursor_dir = project_root / ".cursor"
    cursor_dir.mkdir(exist_ok=True)
    with open(cursor_dir / "mcp.json", 'w') as f:
        json.dump(mcp_config, f, indent=2)
         
    # Generate Specialized Agents
    specialized_dir = target_path / "agents" / "specialized"
    specialized_dir.mkdir(exist_ok=True, parents=True)
    
    for agent in selected_agents:
        safe_name = agent["name"].lower().replace(" ", "-")
        agent_dir = specialized_dir / safe_name
        agent_dir.mkdir(exist_ok=True, parents=True)
        
        agent_file_path = agent_dir / f"{safe_name}.md"
        
        frontmatter = f"""---
name: {agent["name"]}
description: {agent["role"]}
coding_agent: true
agentic_mode: true
---
"""
        system_prompt = agent.get("system_prompt", f"# {agent['name']}\n\n{agent['role']}")
        
        # Append DDD logic
        ddd_section = ""
        if ddd_context:
            ddd_section = f"""
## Domain-Driven Design (DDD) Context
This project uses Domain-Driven Design principles.
At the beginning of any new session or task involving domain logic, you MUST use the `read_file` tool to load `{target_path.name}/ddd/context.md`.

You MUST refer to the following DDD documentation:
- `context.md`: Defines the core domain terms and their meanings.
- `translation_map.json`: Maps domain concepts to implementation details.

Ensure your implementation aligns with these definitions.
"""

        core_mandates = f"""
## Core Mandates
You are a specialized subagent operating within this repository's agent ecosystem.
You have been delegated a specific task by the Orchestrator.
1. Security & System Integrity: Protect secrets.
2. Context Efficiency: Be strategic in tool usage.
3. Superpower Workflows: You MUST utilize installed Superpower skills. If your platform supports a native skill tool (e.g. `activate_skill`, `skill`), use it. Otherwise, read the `.md` files located in `{target_path.name}/skills/`.

## Indexer MCP Integration
You have access to the codebase index via the `indxr` MCP server.
- Strategic Fetching: Use `find`, `summarize`, `get_file_summary` via MCP.
"""

        final_content = frontmatter + system_prompt + "\n" + core_mandates + "\n" + ddd_section
        
        with open(agent_file_path, 'w') as f:
            f.write(final_content)
            
    print(f"Successfully minted workspace at {target_dir}")
    print("\nNext Steps:")
    print(f"1. cd {target_dir}")
    print("2. ./scripts/setup_harness.sh (Install prerequisites)")
    print("3. Activate your environment and Launch AI")
