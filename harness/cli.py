import argparse
import sys
import getpass
import os
import tempfile
import subprocess
import shutil
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Initialize a new Harness agent workspace.")
    parser.add_argument("command", choices=["init"], help="Command to run")
    parser.add_argument("--project-path", required=True, help="Path to the repository")
    parser.add_argument("--llm", required=True, choices=["gemini", "openai", "anthropic"], help="LLM provider")
    parser.add_argument("--model", help="Optional specific model to use (e.g., gemini-3.1-pro-preview, claude-3-5-sonnet-20241022)")
    parser.add_argument("--bundle", help="Optional path to an existing .indxr directory or wiki")
    parser.add_argument("--ddd", action="store_true", help="Enable DDD Onboarding sequence")
    parser.add_argument("--detailed", action="store_true", help="Include all wiki files for deeper context acquisition")
    return parser.parse_args()

def run_ddd_grill(ddd_context: dict) -> dict:
    """Interactively grill the user with alignment questions."""
    print("\n=== DDD Alignment Grill ===")
    questions = ddd_context.get("questions", [])
    answers = {}
    
    if not questions:
        print("No alignment questions generated.")
    else:
        for i, q in enumerate(questions):
            print(f"\n[{i+1}/{len(questions)}] {q}")
            ans = input("> ").strip()
            answers[q] = ans
            
    # Enhancement: Extra question for general domain knowledge
    print("\n[Extra] Are there any other domain specific knowledge you would like to pass in?")
    extra_knowledge = input("> ").strip()
    if extra_knowledge:
        answers["__additional_domain_knowledge__"] = extra_knowledge
        
    return answers

def main():
    args = parse_args()
    
    api_key_env_var = f"{args.llm.upper()}_API_KEY"
    api_key = os.environ.get(api_key_env_var)
    
    # Fallback for Gemini
    if not api_key and args.llm == "gemini":
        api_key = os.environ.get("GOOGLE_API_KEY")
        
    if not api_key:
        print(f"Environment variable {api_key_env_var} not found.")
        api_key = getpass.getpass(prompt=f"Enter your {args.llm} API Key: ")
        
    print("Pre-flight checks passed.")
    
    # --- New: Fast Path Bundle Resolution & Fallback ---
    resolved_bundle_path = None
    if args.bundle:
        resolved_bundle_path = os.path.abspath(args.bundle)

    # Check for index existence
    index_found = False
    
    # 1. Check bundle if provided
    if resolved_bundle_path:
        base_name = os.path.basename(resolved_bundle_path)
        if base_name == "wiki":
            if os.path.exists(os.path.join(resolved_bundle_path, "index.md")):
                index_found = True
        elif base_name == ".indxr":
            if os.path.exists(os.path.join(resolved_bundle_path, "INDEX.md")) or os.path.exists(os.path.join(resolved_bundle_path, "wiki", "index.md")):
                index_found = True
        else:
            bundle_indxr = os.path.join(resolved_bundle_path, ".indxr")
            if os.path.exists(os.path.join(bundle_indxr, "INDEX.md")) or os.path.exists(os.path.join(bundle_indxr, "wiki", "index.md")):
                index_found = True
            elif os.path.exists(os.path.join(resolved_bundle_path, "INDEX.md")):
                index_found = True

    # 2. Check project path
    project_indxr = os.path.join(args.project_path, ".indxr")
    if not index_found and (os.path.exists(os.path.join(project_indxr, "INDEX.md")) or os.path.exists(os.path.join(project_indxr, "wiki", "index.md"))):
        index_found = True

    if not index_found:
        print("\nNo existing indxr database found.")
        choice = input("Would you like to generate one now using 'indxr wiki generate'? (Y/n): ").strip().lower()
        if choice in ['', 'y', 'yes']:
            print("Generating indxr wiki...")
            
            # Prepare environment variables for indxr
            env = os.environ.copy()
            if args.llm == "anthropic":
                env["ANTHROPIC_API_KEY"] = api_key
            elif args.llm == "openai":
                env["OPENAI_API_KEY"] = api_key
            elif args.llm == "gemini":
                 # Pass GOOGLE_API_KEY to the indexer as it might support it now.
                 env["GOOGLE_API_KEY"] = api_key
                 # Clarify the warning: indexer performs best with Anthropic or OpenAI
                 if not env.get("ANTHROPIC_API_KEY") and not env.get("OPENAI_API_KEY"):
                      print("Notice: 'indxr' performs best with ANTHROPIC_API_KEY or OPENAI_API_KEY for wiki generation.")
                      print("Attempting with GOOGLE_API_KEY...")
            
            # Execute indxr in the project directory
            os.makedirs(args.project_path, exist_ok=True)
            try:
                if shutil.which("npx"):
                    result = subprocess.run(
                        ["npx", "--yes", "indxr", "wiki", "generate"], 
                        cwd=args.project_path, 
                        env=env,
                        check=False
                    )
                    if result.returncode != 0:
                        print("npx failed, attempting global indxr...")
                        subprocess.run(
                            ["indxr", "wiki", "generate"], 
                            cwd=args.project_path, 
                            env=env,
                            check=True
                        )
                else:
                    subprocess.run(
                        ["indxr", "wiki", "generate"], 
                        cwd=args.project_path, 
                        env=env,
                        check=True
                    )
            except subprocess.CalledProcessError as e:
                print(f"\nFailed to generate indxr wiki: {e}")
                print("\033[91mWARNING: Index generation failed. Proceeding without a codebase index will lead to hallucinated workspace context.\033[0m")
                choice = input("Do you want to continue anyway? (y/N): ").strip().lower()
                if choice != 'y':
                    print("Aborting.")
                    sys.exit(1)
            except FileNotFoundError:
                print(f"\nError: Neither 'npx' nor 'indxr' command found.")
                print("\033[91mWARNING: Index generation failed. Proceeding without a codebase index will lead to hallucinated workspace context.\033[0m")
                choice = input("Do you want to continue anyway? (y/N): ").strip().lower()
                if choice != 'y':
                    print("Aborting.")
                    sys.exit(1)
            except Exception as e:
                print(f"\nError running indexer: {e}")
                print("\033[91mWARNING: Index generation failed. Proceeding without a codebase index will lead to hallucinated workspace context.\033[0m")
                choice = input("Do you want to continue anyway? (y/N): ").strip().lower()
                if choice != 'y':
                    print("Aborting.")
                    sys.exit(1)
        else:
             print("Proceeding without codebase index. Architecture context will be severely limited.")
    # --- End Fast Path ---

    print("Stage 1: Cloning boilerplate for discovery...")
    repo_url = "https://github.com/mapengbo0314/e2g.git"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to clone boilerplate repository: {e.stderr.decode() if e.stderr else str(e)}")
            sys.exit(1)
        except FileNotFoundError:
            print("Error: 'git' command not found. Please install Git.")
            sys.exit(1)
            
        boilerplate_dir = os.path.join(temp_dir, "boilerplate-agent")
        
        print("Stage 2: Dynamic Context Acquisition")
        from harness.discovery_engine import discover_ddd_context, acquire_mcp_context, generate_onboarding_domain_doc
        
        # Acquire context once
        context_str = acquire_mcp_context(args.project_path, bundle_path=resolved_bundle_path, detailed=args.detailed)
        if context_str is None:
             context_str = "No codebase wiki found. Architecture unknown."
             print("No usable .indxr/wiki found. Proceeding with empty context.")
        
        final_ddd_context = None
        if args.ddd:
            print("\nStage 2.5: DDD Onboarding Context Extraction")
            ddd_context_raw = discover_ddd_context(context_str, args.llm, api_key, args.model)
            grill_answers = run_ddd_grill(ddd_context_raw)
            
            final_ddd_context = {
                "ubiquitous_language": ddd_context_raw.get("context_draft", ""),
                "translation_map": grill_answers,
                "legacy_hints": ddd_context_raw.get("legacy_hints", {}),
                "additional_domain_knowledge": grill_answers.get("__additional_domain_knowledge__", "")
            }

        selected_agents = []

        print("\n=== Platform Selection ===")
        print("1. Gemini CLI")
        print("2. Claude Code")
        print("3. Cursor")
        print("4. Generic / Custom")
        print("5. Codex")
        platform_choice = input("Select target platform [1-5]: ").strip()
        if not platform_choice:
            platform_choice = "1"
        
        if platform_choice == "1":
            harness_folder = ".gemini"
        elif platform_choice == "2":
            harness_folder = ".claude"
        elif platform_choice == "3":
            harness_folder = ".cursor"
        elif platform_choice == "5":
            harness_folder = ".codex"
        else:
            harness_folder = ".agents"

        # Normalize project_path to avoid nesting if the user points directly to the harness folder
        # We check against ALL common harness folder names to be safe
        possible_harness_folders = [".gemini", ".claude", ".cursor", ".codex", ".agents"]
        abs_project_path = os.path.abspath(args.project_path)
        path_parts = Path(abs_project_path).parts
        if path_parts and path_parts[-1] in possible_harness_folders:
            print(f"Notice: You pointed to a harness folder '{path_parts[-1]}'. Backtracking to project root: {os.path.dirname(abs_project_path)}")
            args.project_path = os.path.dirname(abs_project_path)

        target_dir = os.path.join(args.project_path, harness_folder)
        
        from harness.minting_engine import (
            mint_workspace,
            wait_for_user_review_and_read_domain,
            synthesize_domain_sme_agent,
            patch_orchestrator_rules,
            parse_tool_checklists,
            install_workspace_tools
        )

        print("\nStage 2.7: Phased Onboarding & Domain SME Discovery")
        from harness.discovery_engine import query_llm
        generate_onboarding_domain_doc(
            args.project_path, 
            "Analyzed Codebase Context", 
            query_llm, 
            args.llm, 
            api_key, 
            context_str,
            boilerplate_dir
        )
        domain_content = wait_for_user_review_and_read_domain(args.project_path)

        # Parse tools
        skills_to_install, mcps_to_install = parse_tool_checklists(domain_content)

        # We pass the cloned boilerplate_dir so minting engine doesn't have to clone again
        mint_workspace(target_dir, selected_agents, args.project_path, platform_choice, args.model, resolved_bundle_path, boilerplate_dir, ddd_context=final_ddd_context)

        # Install tools
        install_workspace_tools(args.project_path, harness_folder, skills_to_install, mcps_to_install)

        # Determine subagent syntax for rule patching
        target_syntax = "@"
        if platform_choice == "2": # Claude
            target_syntax = "Task tool: "
        elif platform_choice == "5": # Codex
            target_syntax = "Hand off to "

        sme_agent_name = synthesize_domain_sme_agent(args.project_path, domain_content, harness_folder, platform_choice=platform_choice, model_choice=args.model)
        patch_orchestrator_rules(args.project_path, sme_agent_name, harness_folder, target_syntax=target_syntax)

        print(f"\n{'='*60}")
        print("🚀 ONBOARDING COMPLETE")
        print(f"{'='*60}")
        
        counter = 1
        print(f"\n{counter}. Workspace Minted: {target_dir}")
        counter += 1
        
        if sme_agent_name:
            print(f"{counter}. Domain SME Created: @{sme_agent_name}")
            counter += 1
        
        if skills_to_install:
            print(f"{counter}. Local Skills Installed: {', '.join([s['name'] for s in skills_to_install])}")
            counter += 1
        
        if mcps_to_install:
            print(f"{counter}. MCP Tools Configured: {', '.join([m['name'] for m in mcps_to_install])}")
            print("\n[ACTION REQUIRED] MCP Authorization:")
            if platform_choice == "1":
                print("   - In Gemini CLI, you will be prompted to 'Allow' each tool on first use.")
            elif platform_choice == "2":
                print("   - In Claude Code, ensure you restart your session to load the new mcp.json.")
            print("   - Review your workspace mcp.json to verify the command paths.")
            counter += 1

        print(f"\n{counter}. [ACTION REQUIRED] Context Automation:")
        print("   - The indxr GitHub Action (.github/workflows/update-indexer.yml) has been generated.")
        print("   - To enable automated context updates on PRs, configure the following GitHub Secrets:")
        print("     - GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY")
        counter += 1

        if sme_agent_name:
            print(f"\n{counter}. Context: The @{sme_agent_name} is now the gateway for all planning.")
            print(f"   Dispatch rules in {harness_folder}/rules/dispatch_rules.md have been updated.")
            
        print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
