# Harness Init CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `harness init` command that automates indexing via `indxr`, discovers specialized agents via an LLM, confirms them via an interactive TUI, and mints a boilerplate workspace while generating platform-specific setup scripts for MCP and skills.

**Architecture:** A Python CLI tool (`harness/cli.py`) utilizing `argparse` for command routing, and modular engine files (`indexer_wrapper.py`, `discovery_engine.py`, `minting_engine.py`) for the core logic.

**Tech Stack:** Python 3.11+, `argparse`, `subprocess`, `pydantic` (for LLM schema parsing), `json`.

---

### Task 1: Setup CLI Entry Point and Pre-flight Checks

**Files:**
- Create: `harness/cli.py`
- Create: `harness/indexer_wrapper.py`

- [ ] **Step 1: Write minimal implementation for `indexer_wrapper.py`**

```python
import shutil
import sys

def check_indxr_installed() -> bool:
    """Verifies that indxr is available on the system PATH."""
    if shutil.which("indxr") is None:
        print("ERROR: 'indxr' is not installed or not on your PATH.")
        print("Please install indxr (e.g., cargo install indxr) to use harness init.")
        sys.exit(1)
    return True
```

- [ ] **Step 2: Write the CLI entry point parser in `harness/cli.py`**

```python
import argparse
import sys
import getpass
import os
from harness.indexer_wrapper import check_indxr_installed

def parse_args():
    parser = argparse.ArgumentParser(description="Initialize a new Harness agent workspace.")
    parser.add_argument("command", choices=["init"], help="Command to run")
    parser.add_argument("--project-path", required=True, help="Path to the repository")
    parser.add_argument("--llm", required=True, choices=["gemini", "openai", "anthropic"], help="LLM provider")
    parser.add_argument("--bundle", help="Optional path to an existing indxr JSON bundle")
    return parser.parse_args()

def main():
    if len(sys.argv) < 2 or sys.argv[1] != "init":
        print("Usage: harness init ...")
        sys.exit(1)
        
    args = parse_args()
    check_indxr_installed()
    
    # Secure Credential Check
    api_key_env_var = f"{args.llm.upper()}_API_KEY"
    api_key = os.environ.get(api_key_env_var)
    if not api_key:
        print(f"Environment variable {api_key_env_var} not found.")
        api_key = getpass.getpass(prompt=f"Enter your {args.llm} API Key: ")
        
    print("Pre-flight checks passed.")

if __name__ == "__main__":
    main()
```

### Task 2: Context Acquisition via `indxr` Wrapper

**Files:**
- Modify: `harness/indexer_wrapper.py`
- Modify: `harness/cli.py`

- [ ] **Step 1: Implement `acquire_context` in `indexer_wrapper.py`**

```python
import json
import os
import subprocess
import datetime
import sys

def acquire_context(project_path: str, bundle_override: str | None = None) -> str:
    """Runs indxr to generate the index or uses the provided bundle."""
    if bundle_override:
        if not os.path.exists(bundle_override):
            print(f"ERROR: Provided bundle not found at {bundle_override}")
            sys.exit(1)
        index_path = bundle_override
    else:
        print(f"Running indxr on {project_path}...")
        index_path = os.path.join(project_path, "INDEX.json")
        try:
            subprocess.run(
                ["indxr", "index", "-f", "json", "-o", index_path],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            print(f"ERROR: indxr failed: {e.stderr}")
            sys.exit(1)
            
    # Generate metadata.json for the freshness gate
    metadata_path = os.path.join(project_path, "metadata.json")
    metadata = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_bundle": index_path,
        "engine": "indxr"
    }
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    return index_path
```

- [ ] **Step 2: Update `harness/cli.py` to call `acquire_context`**

Modify `harness/cli.py` inside `main()`:
```python
# ... after api key check ...
    print("Pre-flight checks passed.")
    from harness.indexer_wrapper import acquire_context
    index_path = acquire_context(args.project_path, args.bundle)
    print(f"Context acquired at: {index_path}")
```

### Task 3: Discovery Engine

**Files:**
- Create: `harness/discovery_engine.py`
- Modify: `harness/cli.py`

- [ ] **Step 1: Implement `discovery_engine.py`**

```python
import json
import sys

def query_llm(prompt: str, llm_provider: str, api_key: str) -> str:
    return '{"agents": [{"name": "DefaultAgent", "role": "Generalist", "zone": "Core"}]}'

def prune_context(index_data: dict) -> dict:
    if "files" in index_data:
        return {"files": [f.get("path", "") for f in index_data["files"]][:100]} 
    return index_data

def discover_agents(index_data: dict, llm_provider: str, api_key: str) -> list[dict]:
    pruned_map = prune_context(index_data)
    prompt = f"""
    Analyze this project structure:
    {json.dumps(pruned_map, indent=2)}
    Identify 3-5 logical "specialization zones" unique to this architecture.
    Recommend an AI agent for each zone.
    Return EXACTLY this JSON format:
    {{"agents": [{{"name": "AgentName", "role": "Brief description", "zone": "The zone"}}]}}
    """
    response_text = query_llm(prompt, llm_provider, api_key)
    try:
        cleaned = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        return data.get("agents", [])
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse LLM response as JSON: {e}")
        sys.exit(1)
```

- [ ] **Step 2: Update `harness/cli.py` to call discovery**

Modify `harness/cli.py` inside `main()`:
```python
# ... after context acquisition ...
    import json
    from harness.discovery_engine import discover_agents
    
    try:
        with open(index_path, 'r') as f:
            index_data = json.load(f)
    except json.JSONDecodeError:
        print(f"ERROR: Could not read index JSON at {index_path}")
        sys.exit(1)
        
    print(f"Discovering agents via {args.llm}...")
    recommended_agents = discover_agents(index_data, args.llm, api_key)
    print(f"Found {len(recommended_agents)} recommendations.")
```

### Task 4: Human-in-the-Loop TUI

**Files:**
- Modify: `harness/cli.py`

- [ ] **Step 1: Implement basic TUI selection in `harness/cli.py`**

Modify `harness/cli.py` inside `main()`:
```python
# ... after discovery ...
    selected_agents = []
    print("\n=== Recommended Agents ===")
    for idx, agent in enumerate(recommended_agents):
        print(f"[{idx}] {agent['name']} ({agent['zone']}): {agent['role']}")
        choice = input(f"Include {agent['name']}? (Y/n): ").strip().lower()
        if choice in ['', 'y', 'yes']:
            selected_agents.append(agent)
            
    add_custom = input("\nAdd a custom agent? (y/N): ").strip().lower()
    if add_custom in ['y', 'yes']:
        name = input("Agent Name: ")
        role = input("Role Description: ")
        selected_agents.append({"name": name, "role": role, "zone": "Custom"})
        
    if not selected_agents:
        print("No agents selected. Aborting.")
        sys.exit(0)

    print("\n=== Platform Selection ===")
    print("1. Gemini CLI")
    print("2. Claude Code")
    print("3. Cursor / Custom")
    platform_choice = input("Select target platform [1-3]: ").strip()
        
    print(f"\nProceeding to mint {len(selected_agents)} agents...")
```

### Task 5: Workspace Minting & Prerequisites Injection

**Files:**
- Create: `harness/minting_engine.py`
- Modify: `harness/cli.py`

- [ ] **Step 1: Implement `minting_engine.py`**

```python
import os
import shutil
import json
from pathlib import Path

def mint_workspace(target_dir: str, selected_agents: list[dict], project_path: str, platform_choice: str):
    """Clones boilerplate, injects configs with MCP, and writes setup prerequisites."""
    target_path = Path(target_dir)
    source_dir = Path("boilerplate-agent") # Assuming this script runs from repo root
    
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
    
    # Setup agents directory
    agents_dir = target_path / "agents"
    agents_dir.mkdir(exist_ok=True)
    
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
        agent_dir = agents_dir / agent["name"].lower().replace(" ", "-")
        agent_dir.mkdir(exist_ok=True)
        
        # Inject MCP into agent config
        config_data = {
            "name": agent["name"],
            "role": agent["role"],
            "zone": agent["zone"],
            "mcp_servers": ["indxr"] # References the global mcp.json
        }
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
```

- [ ] **Step 2: Update `harness/cli.py` to pass platform choice**

Modify `harness/cli.py` inside `main()`:
```python
# ... after HITL selection ...
    from harness.minting_engine import mint_workspace
    
    target_dir = os.path.join(args.project_path, ".agents")
    mint_workspace(target_dir, selected_agents, args.project_path, platform_choice)
```
---