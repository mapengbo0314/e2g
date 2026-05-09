import os
import re
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
        
        # Tool mapping for specific platforms
        platform_map_normalized = {"1": "gemini", "2": "claude", "3": "cursor", "4": "agents"}
        current_platform = platform_map_normalized.get(platform_choice, platform_choice).lower()
        
        tool_replacements = {}
        if current_platform == "claude":
            tool_replacements = {
                "- read_file": "- Read",
                "- grep_search": "- Grep",
                "- replace": "- Edit",
                "- write_file": "- Write",
                "- run_shell_command": "- Bash",
                "- glob": "- Glob"
            }

        # Fix broken include pointers inside the copied files and map tool names
        target_dir_name = target_path.name
        for root, _, files in os.walk(target_path):
            for file in files:
                if file.endswith((".md", ".json", ".yaml", ".yml")):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r") as f:
                            content = f.read()
                            
                        new_content = content
                        if "@boilerplate-agent" in new_content:
                            new_content = new_content.replace("@boilerplate-agent", f"@{target_dir_name}")
                            
                        # Apply tool mappings if any
                        for old_tool, new_tool in tool_replacements.items():
                            new_content = new_content.replace(old_tool, new_tool)
                            
                        if new_content != content:
                            with open(filepath, "w") as f:
                                f.write(new_content)
                    except Exception as e:
                        print(f"Warning: Failed to process {filepath}: {e}")
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
    
    # Normalize platform choice
    platform_map = {
        "1": "gemini",
        "2": "claude",
        "3": "cursor",
        "4": "agents"
    }
    active_platform = platform_map.get(platform_choice, platform_choice).lower()

    escaped_project_path = os.path.abspath(project_path).replace("'", "'\\''")
    
    key_check_snippet = """
# Check for indxr API keys
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: indxr requires an ANTHROPIC_API_KEY or OPENAI_API_KEY for background wiki updates."
    echo "Background auto-indexing will be disabled until a key is exported in your terminal."
    echo "Example: export ANTHROPIC_API_KEY='sk-ant-...' "
    echo ""
fi
"""

    scripts_to_generate = {
        "gemini": f"""#!/usr/bin/env bash
set -e
{key_check_snippet}
echo "=== Setting up Superpowers for Gemini CLI ==="
if command -v gemini &> /dev/null; then
    gemini extensions install https://github.com/obra/superpowers || true
    gemini extensions install https://github.com/mattpocock/skills || true
    
    echo "Adding indxr to Gemini CLI project MCP configuration..."
    indxr_serve_args_str="serve --watch --wiki-auto-update --all-tools"
    gemini mcp add indxr bash -c "cd '{escaped_project_path}' && indxr $indxr_serve_args_str" -e GEMINI_API_KEY=\\$GEMINI_API_KEY -e ANTHROPIC_API_KEY=\\$ANTHROPIC_API_KEY -e OPENAI_API_KEY=\\$OPENAI_API_KEY || true
else
    echo "Warning: gemini command not found."
fi

echo "To activate it, run Gemini from the project root and use '/mcp reload'."
""",
        "claude": f"""#!/usr/bin/env bash
set -e
{key_check_snippet}
echo "=== Setting up Superpowers for Claude Code ==="
echo "To install Superpowers and Skills for Claude Code, run these commands inside the Claude Code interface:"
echo "  /plugin install superpowers@claude-plugins-official"
echo "  /plugin install skills@mattpocock"

# MCP Configuration for Claude
if command -v claude &> /dev/null; then
    echo "Adding indxr to Claude Code project MCP configuration..."
    indxr_serve_args_str="serve --watch --wiki-auto-update --all-tools"
    claude mcp add --scope project indxr --env GEMINI_API_KEY=\\$GEMINI_API_KEY --env ANTHROPIC_API_KEY=\\$ANTHROPIC_API_KEY --env OPENAI_API_KEY=\\$OPENAI_API_KEY -- bash -c "cd '{escaped_project_path}' && indxr $indxr_serve_args_str" || true
fi
""",
        "cursor": f"""#!/usr/bin/env bash
set -e
{key_check_snippet}
echo "=== Setting up Superpowers for Cursor ==="
echo "To install Superpowers and Skills for Cursor, run these commands inside the Cursor Agent chat:"
echo "  /add-plugin superpowers"
echo "  /add-plugin mattpocock/skills"
"""
    }

    # Write setup script
    if active_platform in scripts_to_generate:
        script_content = scripts_to_generate[active_platform]
        
        script_dir = project_root / f".{active_platform}" / "scripts"
        script_dir.mkdir(parents=True, exist_ok=True)
        script_path = script_dir / "setup_harness.sh"
        with open(script_path, "w") as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
    
    # Generate Platform Rules Pointers IN THE ROOT DIRECTORY
    harness_prefix = f".{active_platform}" if active_platform in ["gemini", "claude", "cursor"] else target_dir_name
    pointer_content = f"""# Agentic Harness
    
Please read `AGENTS.md` for core repository instructions and routing rules.
The Orchestrator agent and core rules are located in `{harness_prefix}/orchestrator.md`.
"""
    pointer_files = ["GEMINI.md", "CLAUDE.md", ".cursorrules"]
    for rules_file in pointer_files:
        with open(project_root / rules_file, "w") as f:
            f.write(pointer_content)
            
    copilot_dir = project_root / ".github"
    copilot_dir.mkdir(exist_ok=True)
    with open(copilot_dir / "copilot-instructions.md", "w") as f:
        f.write(pointer_content)
        
    print("\nTo install skills & MCPs, run the setup_harness.sh script inside your platform's hidden folder (e.g. `sh .gemini/scripts/setup_harness.sh`).")

    # Create an MCP config that points to the indxr server running in the project root
    indxr_serve_args = ["serve", "--watch", "--wiki-auto-update", "--all-tools"]
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
    
    # Generate mcp.json as a fallback/reference configuration
    mcp_path = target_path / "mcp.json"
    with open(mcp_path, 'w') as f:
         json.dump(mcp_config, f, indent=2)
         
    # Helper to generate a valid URL-safe slug
    def to_slug(text):
        # 1. Handle CamelCase (Insert hyphens between lower-to-upper transitions)
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', text)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()
        # 2. Replace any non-alphanumeric character (except hyphens) with a hyphen
        s3 = re.sub(r'[^a-z0-9]+', '-', s2)
        # 3. Clean up multiple hyphens and leading/trailing
        return re.sub(r'-+', '-', s3).strip('-')

    # Generate Specialized Agents
    for agent in selected_agents:
        safe_name = to_slug(agent["name"])
        
        agent_dir_path = target_path / "agents"
        agent_dir_path.mkdir(parents=True, exist_ok=True)
        agent_file_path = agent_dir_path / f"{safe_name}.md" 
        
        # Select base tools based on platform
        if active_platform == "claude":
            tools_list = """  - Read
  - Grep
  - Edit
  - Bash"""
        else:
            tools_list = """  - read_file
  - grep_search
  - replace
  - run_shell_command"""
        
        frontmatter = f"""---
name: {safe_name}
description: {agent["role"]}
tools:
{tools_list}
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

        # Determine the correct include syntax based on platform
        include_pointer = ""
        if active_platform in ["gemini", "claude"]:
            include_pointer = "@../rules/core_mandates.md\n\n"
        else:
            # Fallback for cursor/agents where include syntax might not be natively supported
            include_pointer = "<!-- Core Mandates should be read from ../rules/core_mandates.md -->\n\n"

        final_content = frontmatter + include_pointer + system_prompt + "\n" + ddd_section
        
        with open(agent_file_path, 'w') as f:
            f.write(final_content)
            
    print(f"Successfully minted workspace at {target_dir}")
    print("\nNext Steps:")
    print(f"1. cd {target_dir}")
    print("2. ./scripts/setup_harness.sh (Install prerequisites)")
    print("3. Activate your environment and Launch AI")
