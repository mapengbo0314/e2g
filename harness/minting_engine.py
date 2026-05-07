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

    # Remove internal discovery agents from the final workspace
    discovery_path = target_path / "agents" / "discovery"
    if discovery_path.exists():
        shutil.rmtree(discovery_path)

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
    indxr_init_flag = ""
    if platform_choice == "1":
        platform_name = "Gemini CLI"
    elif platform_choice == "2":
        platform_name = "Claude Code"
        indxr_init_flag = " --claude"
    elif platform_choice == "3":
        platform_name = "Copilot CLI"
    elif platform_choice == "4":
        platform_name = "Cursor"
        indxr_init_flag = " --cursor"
    else:
        platform_name = "Generic / Custom"

    setup_script_path = target_path / "scripts" / "setup_harness.sh"
    setup_script_path.parent.mkdir(parents=True, exist_ok=True)
    
    setup_content = f"""#!/usr/bin/env bash
set -e
echo "=== Setting up Agentic Harness Prerequisites for {platform_name} ==="

# 1. Platform Specific Extension/Skill Installation
"""
    if platform_choice == "1": # Gemini
        setup_content += """
echo "Installing Superpowers and Skills for Gemini CLI..."
if command -v gemini &> /dev/null; then
    gemini extensions install https://github.com/obra/superpowers || true
    gemini extensions install https://github.com/mattpocock/skills || true
else
    echo "Warning: gemini command not found."
fi
"""
    elif platform_choice == "2": # Claude
        setup_content += """
echo "To install Superpowers and Skills for Claude Code, run these commands inside the Claude Code interface:"
echo "  /plugin install superpowers@claude-plugins-official"
echo "  /plugin install skills@mattpocock"
"""
    elif platform_choice == "3": # Copilot
        setup_content += """
echo "Installing Superpowers and Skills for Copilot CLI..."
if command -v copilot &> /dev/null; then
    copilot plugin marketplace add obra/superpowers-marketplace || true
    copilot plugin install superpowers@superpowers-marketplace || true
    copilot plugin marketplace add mattpocock/skills-marketplace || true
    copilot plugin install skills@skills-marketplace || true
else
    echo "Warning: copilot command not found."
fi
"""
    elif platform_choice == "4": # Cursor
        setup_content += """
echo "To install Superpowers and Skills for Cursor, run these commands inside the Cursor Agent chat:"
echo "  /add-plugin superpowers"
echo "  /add-plugin mattpocock/skills"
"""
    else: # Generic fallback
        setup_content += """
echo "Please refer to https://github.com/obra/superpowers to manually install skills for your AI platform."
"""

    setup_content += f"""
# 2. Configure indxr MCP Server
echo "Configuring indxr MCP Server..."
if command -v indxr &> /dev/null; then
"""
    if indxr_init_flag:
        setup_content += f"""    indxr init{indxr_init_flag} || true"""
    else:
        setup_content += """    echo "indxr configured for Gemini CLI (skipping generic init)." """

    if platform_choice == "2":
        # Add Claude Code direct MCP configuration
        indxr_serve_args_str = " ".join(["serve", "--watch", "--wiki-auto-update"] + (["--wiki-model", model_choice] if model_choice else []))
        escaped_project_path = os.path.abspath(project_path).replace("'", "'\\''")
        setup_content += f"""
    if command -v claude &> /dev/null; then
        echo "Adding indxr to Claude Code global MCP configuration..."
        claude mcp add indxr bash -c "cd '{escaped_project_path}' && indxr {indxr_serve_args_str}" || true
    fi
"""

    setup_content += """
else
    echo "Error: indxr is not installed. This should have been caught during init."
fi
"""

    if existing_wiki:
        setup_content += """
# 3. Existing Wiki Detected
echo "Existing codebase wiki database detected. Skipping initial wiki generation."
"""
    else:
        setup_content += f"""
# 3. Generate initial Codebase Wiki
echo "Generating initial codebase wiki (this may take a moment)..."
(cd "{os.path.abspath(project_path)}" && indxr wiki generate{" --model " + model_choice if model_choice else ""}) || echo "Warning: Wiki generation failed. You may need to run it manually."
"""

    with open(setup_script_path, "w") as f:
        f.write(setup_content)
    os.chmod(setup_script_path, 0o755)
    
    # Generate Platform Rules file (GEMINI.md, CLAUDE.md, etc.) IN THE ROOT DIRECTORY
    project_root = Path(project_path)
    if platform_choice == "1":
        rules_file = "GEMINI.md"
    elif platform_choice == "2":
        rules_file = "CLAUDE.md"
    elif platform_choice == "3":
        rules_file = ".github/copilot-instructions.md"
        (project_root / ".github").mkdir(exist_ok=True)
    elif platform_choice == "4":
        rules_file = ".cursorrules"
    else:
        rules_file = "RULES.md"
    
    # Generate Platform Rules Pointer File
    pointer_content = f"""# Agentic Harness
    
Please read `AGENTS.md` for core repository instructions and routing rules.
"""
    with open(project_root / rules_file, "w") as f:
        f.write(pointer_content)

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
    if platform_choice == "4":
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
        
        # 1. Write the full SYSTEM_PROMPT.md
        system_prompt_path = agent_dir / "system_prompt.md"
        with open(system_prompt_path, 'w') as f:
            f.write(agent.get("system_prompt", f"# {agent['name']}\n\n{agent['role']}"))

        # 2. Inject agent.json
        agent_manifest = {
            "name": agent["name"],
            "description": agent["role"],
            "entrypoint": "config.yaml"
        }
        with open(agent_dir / "agent.json", 'w') as f:
            json.dump(agent_manifest, f, indent=2)
            
        # 3. Inject config.yaml (referencing the system_prompt.md)
        ddd_section = ""
        if ddd_context:
            ddd_section = f"""  - prompt_section:
      title: Domain-Driven Design (DDD) Context
      content: |
        This project uses Domain-Driven Design principles.
        At the beginning of any new session or task involving domain logic, you MUST use the `read_file` tool to load `{target_path.name}/ddd/context.md`.
        
        You MUST refer to the following DDD documentation:
        - `context.md`: Defines the core domain terms and their meanings.
        - `translation_map.json`: Maps domain concepts to implementation details.
        
        Ensure your implementation aligns with these definitions.
    insert_after_sections: Core Mandates"""

        config_yaml_content = f"""coding_agent: true
agentic_mode: true
# Load the full brain from the generated markdown file
system_prompt_file: system_prompt.md
prompt_section_customization:
  add_prompt_sections:
  - prompt_section:
      title: Core Mandates
      content: |
        You are a specialized subagent operating within this repository's agent ecosystem.
        You have been delegated a specific task by the Orchestrator.
        1. Security & System Integrity: Protect secrets.
        2. Context Efficiency: Be strategic in tool usage.
        3. Superpower Workflows: You MUST run `list_directory` on `{target_path.name}/skills/` at the start of your session to discover available local skills.
    insert_before_sections: artifacts
  - prompt_section:
      title: Indexer MCP Integration
      content: |
        You have access to the codebase index via the `indxr` MCP server.
        - Strategic Fetching: Use `find`, `summarize`, `get_file_summary` via MCP.
    insert_after_sections: Core Mandates
{ddd_section}
"""
        with open(agent_dir / "config.yaml", 'w') as f:
            f.write(config_yaml_content)
            
    print(f"Successfully minted workspace at {target_dir}")
    print("\nNext Steps:")
    print(f"1. cd {target_dir}")
    print("2. ./scripts/setup_harness.sh (Install prerequisites)")
    print("3. Activate your environment and Launch AI")
