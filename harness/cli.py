import argparse
import sys
import getpass
import os
import tempfile
import subprocess
import shutil

def parse_args():
    parser = argparse.ArgumentParser(description="Initialize a new Harness agent workspace.")
    parser.add_argument("command", choices=["init"], help="Command to run")
    parser.add_argument("--project-path", required=True, help="Path to the repository")
    parser.add_argument("--llm", required=True, choices=["gemini", "openai", "anthropic"], help="LLM provider")
    parser.add_argument("--model", help="Optional specific model to use (e.g., gemini-2.5-flash, claude-3-5-sonnet-20241022)")
    parser.add_argument("--bundle", help="Optional path to an existing indxr JSON bundle")
    parser.add_argument("--ddd", action="store_true", help="Enable DDD Onboarding sequence")
    return parser.parse_args()

def run_ddd_grill(ddd_context: dict) -> dict:
    """Interactively grill the user with alignment questions."""
    print("\n=== DDD Alignment Grill ===")
    questions = ddd_context.get("questions", [])
    answers = {}
    
    if not questions:
        print("No alignment questions generated.")
        return answers

    for i, q in enumerate(questions):
        print(f"\n[{i+1}/{len(questions)}] {q}")
        ans = input("> ").strip()
        answers[q] = ans
        
    return answers

def main():
    args = parse_args()
    
    api_key_env_var = f"{args.llm.upper()}_API_KEY"
    api_key = os.environ.get(api_key_env_var)
    if not api_key:
        print(f"Environment variable {api_key_env_var} not found.")
        api_key = getpass.getpass(prompt=f"Enter your {args.llm} API Key: ")
        
    print("Pre-flight checks passed.")
    
    print("Stage 1: Cloning boilerplate for discovery...")
    repo_url = "https://github.com/mapengbo0314/e2g.git"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], check=True, capture_output=True)
        boilerplate_dir = os.path.join(temp_dir, "boilerplate-agent")
        
        feature_fetcher_yaml = os.path.join(boilerplate_dir, "agents", "discovery", "feature-fetcher", "config.yaml")
        
        print("Stage 2: Dynamic Context Acquisition")
        from harness.discovery_engine import discover_agents, discover_ddd_context, acquire_mcp_context
        
        # Acquire context once
        context_str = acquire_mcp_context(args.project_path)
        
        print("Discovering specialized agents...")
        recommended_agents = discover_agents(context_str, feature_fetcher_yaml, args.llm, api_key, args.model)
        
        print(f"Found {len(recommended_agents)} recommendations.")
        selected_agents = []
        print("\n=== Recommended Agents ===")
        for idx, agent in enumerate(recommended_agents):
            print(f"[{idx}] {agent['name']} ({agent['zone']}): {agent['role']}")
            choice = input(f"Include {agent['name']}? (Y/n): ").strip().lower()
            if choice in ['', 'y', 'yes']:
                selected_agents.append(agent)
                
        if not selected_agents:
            print("No agents selected. Aborting.")
            sys.exit(0)

        final_ddd_context = None
        if args.ddd:
            print("\nStage 2.5: DDD Onboarding Context Extraction")
            ddd_context = discover_ddd_context(context_str, args.llm, api_key, args.model)
            grill_answers = run_ddd_grill(ddd_context)
            
            final_ddd_context = {
                "ubiquitous_language": ddd_context.get("context_draft", ""),
                "translation_map": grill_answers,
                "legacy_hints": ddd_context.get("legacy_hints", {})
            }

        print("\n=== Platform Selection ===")
        print("1. Gemini CLI")
        print("2. Claude Code")
        print("3. Copilot CLI")
        print("4. Cursor")
        print("5. Generic / Custom")
        platform_choice = input("Select target platform [1-5]: ").strip()
        if not platform_choice:
            platform_choice = "1"
            
        print(f"\nStage 3: Proceeding to mint {len(selected_agents)} agents...")
        
        # Option B: Dynamic Target Directory based on platform
        harness_folder = ".gemini" if platform_choice == "1" else ".agents"
        target_dir = os.path.join(args.project_path, harness_folder)
        
        from harness.minting_engine import mint_workspace
        # We pass the cloned boilerplate_dir so minting engine doesn't have to clone again
        mint_workspace(target_dir, selected_agents, args.project_path, platform_choice, args.model, args.bundle, boilerplate_dir, ddd_context=final_ddd_context)

        print("\nStage 4: Executing Automated Setup...")
        setup_script = os.path.join(target_dir, "scripts", "setup_harness.sh")
        if os.path.exists(setup_script):
            try:
                # Run the setup script with the target_dir as the working directory
                subprocess.run([setup_script], cwd=target_dir, check=True)
                print(f"\n✅ Setup Complete! Your Agentic Workspace is ready at: {target_dir}")
                print("Launch your AI platform in that directory to begin.")
            except subprocess.CalledProcessError as e:
                print(f"\n❌ Error during automated setup (Exit Code: {e.returncode}).")
                print(f"You may need to manually run: cd {target_dir} && ./scripts/setup_harness.sh")
        else:
            print(f"\nWarning: Setup script not found at {setup_script}")

if __name__ == "__main__":
    main()
