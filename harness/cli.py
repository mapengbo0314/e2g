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
    from harness.indexer_wrapper import acquire_context
    index_path = acquire_context(args.project_path, args.bundle)
    print(f"Context acquired at: {index_path}")
    
    import json
    from harness.discovery_engine import discover_agents
    
    try:
        with open(index_path, 'r') as f:
            index_data = json.load(f)
    except Exception as e:
        print(f"ERROR: Could not read index JSON at {index_path}: {e}")
        sys.exit(1)
        
    print(f"Discovering agents via {args.llm}...")
    recommended_agents = discover_agents(index_data, args.llm, api_key)
    print(f"Found {len(recommended_agents)} recommendations.")

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
    if not platform_choice:
        platform_choice = "1"
        
    print(f"\nProceeding to mint {len(selected_agents)} agents for platform {platform_choice}...")
    
    from harness.minting_engine import mint_workspace
    target_dir = os.path.join(args.project_path, ".agents")
    mint_workspace(target_dir, selected_agents, args.project_path, platform_choice)

if __name__ == "__main__":
    main()
