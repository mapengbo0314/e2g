import argparse
import sys
import getpass
import os

def parse_args():
    parser = argparse.ArgumentParser(description="Initialize a new Harness agent workspace.")
    parser.add_argument("command", choices=["init"], help="Command to run")
    parser.add_argument("--project-path", required=True, help="Path to the repository")
    parser.add_argument("--llm", required=True, choices=["gemini", "openai", "anthropic"], help="LLM provider")
    parser.add_argument("--model", help="Optional specific model to use (e.g., gemini-2.5-flash, claude-3-5-sonnet-20241022)")
    parser.add_argument("--bundle", help="Optional path to an existing indxr JSON bundle")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Secure Credential Check
    api_key_env_var = f"{args.llm.upper()}_API_KEY"
    api_key = os.environ.get(api_key_env_var)
    if not api_key:
        print(f"Environment variable {api_key_env_var} not found.")
        api_key = getpass.getpass(prompt=f"Enter your {args.llm} API Key: ")
        
    print("Pre-flight checks passed.")
    
    index_data = {}
    
    import json
    from harness.discovery_engine import discover_agents
    
    print(f"Discovering agents via {args.llm}...")
    recommended_agents = discover_agents(index_data, args.llm, api_key, args.model)
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
    print("3. Copilot CLI")
    print("4. Cursor")
    print("5. Generic / Custom")
    platform_choice = input("Select target platform [1-5]: ").strip()
    if not platform_choice:
        platform_choice = "1"
        
    print(f"\nProceeding to mint {len(selected_agents)} agents for platform {platform_choice}...")

    from harness.minting_engine import mint_workspace
    target_dir = os.path.join(args.project_path, ".agents")
    mint_workspace(target_dir, selected_agents, args.project_path, platform_choice, args.model, args.bundle)

if __name__ == "__main__":
    main()
