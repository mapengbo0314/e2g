import os
import shutil
import json
from pathlib import Path

def mint_workspace(target_dir: str, selected_agents: list[dict], project_path: str, platform_choice: str):
    """Clones boilerplate, injects configs with MCP, and writes setup prerequisites."""
    target_path = Path(target_dir)
    # The source is boilerplate-agent in the current workspace
    source_dir = Path("boilerplate-agent") 
    
    if target_path.exists():
        print(f"Warning: Target directory {target_dir} already exists. Minting may overwrite files.")
        
    def ignore_patterns(dir_path, contents):
        ignored = ['.git', '__pycache__', '.DS_Store']
        return [i for i in contents if i in ignored or i.endswith('.log')]
        
    shutil.copytree(source_dir, target_path, ignore=ignore_patterns, dirs_exist_ok=True)
    
    # Generate specialized setup_harness.sh (Prerequisites)
    platform_name = "Gemini CLI" if platform_choice == "1" else "Claude Code" if platform_choice == "2" else "Cursor"
    setup_script_path = target_path / "scripts" / "setup_harness.sh"
    setup_script_path.parent.mkdir(parents=True, exist_ok=True)
    
    setup_content = f"""#!/usr/bin/env bash
set -e
echo "=== Setting up Agentic Harness Prerequisites for {platform_name} ==="

# 1. Platform Specific Extension/Skill Installation
"""
    if platform_choice == "1": # Gemini
        setup_content += """
if command -v gemini &> /dev/null; then
    gemini extensions install https://github.com/obra/superpowers || true
fi
"""
    elif platform_choice == "2": # Claude
        setup_content += """
echo "Ensure your Claude Code environment has the Superpowers skills loaded."
"""

    setup_content += """
# 2. Install indxr MCP Server
if command -v cargo &> /dev/null; then
    cargo install indxr --features wiki,http || true
    indxr init || true
else
    echo "Error: cargo required to install indxr. Visit https://rustup.rs/"
fi
"""
    with open(setup_script_path, "w") as f:
        f.write(setup_content)
    os.chmod(setup_script_path, 0o755)
    
    # Generate Platform Rules file (GEMINI.md, CLAUDE.md, etc.)
    rules_file = "GEMINI.md" if platform_choice == "1" else "CLAUDE.md" if platform_choice == "2" else "RULES.md"
    rules_content = f"""# Agentic Harness Rules for {platform_name}

1. **Context First**: Always use the `indxr` MCP server to query the codebase before proposing changes.
2. **Strict Planning**: Never write production code without an approved plan in `workspace/artifacts/plan.md`.
3. **Verified Index**: Check `metadata.json` for index freshness (< 7 days).
"""
    with open(target_path / rules_file, "w") as f:
        f.write(rules_content)

    # Setup agents directory
    agents_dir = target_path / "_agents"
    agents_dir.mkdir(exist_ok=True, parents=True)
    
    # Create an MCP config that points to the indxr server running in the project root
    mcp_config = {
        "mcpServers": {
            "indxr": {
                "command": "indxr",
                "args": ["serve", "--stdio", "--project", os.path.abspath(project_path)],
                "env": {}
            }
        }
    }
    
    mcp_path = target_path / "mcp.json"
    with open(mcp_path, 'w') as f:
         json.dump(mcp_config, f, indent=2)
    
    for agent in selected_agents:
        agent_dir = agents_dir / "agents" / agent["name"].lower().replace(" ", "-")
        agent_dir.mkdir(exist_ok=True, parents=True)
        
        # Inject config.yaml
        with open(agent_dir / "config.yaml", 'w') as f:
            f.write(f"name: {agent['name']}\n")
            f.write(f"role: {agent['role']}\n")
            f.write(f"zone: {agent['zone']}\n")
            f.write(f"mcp_servers:\n  - indxr\n")
            
    print(f"Successfully minted workspace at {target_dir}")
    print("\nNext Steps:")
    print(f"1. cd {target_dir}")
    print("2. ./scripts/setup_harness.sh (Install prerequisites)")
    print("3. Activate your environment and Launch AI")
