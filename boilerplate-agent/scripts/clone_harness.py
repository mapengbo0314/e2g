#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Clone the boilerplate agent harness into a new directory.")
    parser.add_argument("target_dir", help="Name of the target directory to create (e.g., index-agents)")
    args = parser.parse_args()

    source_dir = Path(__file__).parent.parent.resolve()
    parent_dir = source_dir.parent.resolve()
    target_dir = parent_dir / args.target_dir

    print("=== Cloning Boilerplate Agent Harness ===")
    print(f"Source: {source_dir}")
    print(f"Target: {target_dir}")

    if target_dir.exists():
        print(f"Error: Target directory '{target_dir}' already exists.")
        sys.exit(1)

    # Interactive Platform Selection
    print("\nWhich AI Platform are you using for this harness?")
    print(" [1] Gemini CLI")
    print(" [2] Claude Code")
    print(" [3] Copilot Workspace")
    print(" [4] Other / Custom MCP")
    try:
        platform_choice = input("Select [1-4]: ").strip()
    except EOFError:
        platform_choice = "1"

    platform_map = {"1": "Gemini CLI", "2": "Claude Code", "3": "Copilot Workspace", "4": "Custom"}
    selected_platform = platform_map.get(platform_choice, "Unknown")
    print(f"\nConfiguring setup reminders for {selected_platform}...\n")

    def ignore_patterns(dir_path, contents):
        # Ignore git, pycache, log files, and artifacts content
        ignored = []
        if '.git' in contents:
            ignored.append('.git')
        if '__pycache__' in contents:
            ignored.append('__pycache__')
        for item in contents:
            if item.endswith('.log') or item == '.DS_Store':
                ignored.append(item)
            if Path(dir_path).name == 'artifacts':
                ignored.append(item)
        return ignored

    try:
        shutil.copytree(source_dir, target_dir, ignore=ignore_patterns)
    except Exception as e:
        print(f"Error during cloning: {e}")
        sys.exit(1)

    # Ensure artifacts directory exists
    artifacts_dir = target_dir / "workspace" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Post-Clone Audit
    print("=== Post-Clone Environment Audit ===")
    has_reqs = (parent_dir / "requirements.txt").exists()
    has_package_json = (parent_dir / "package.json").exists()
    has_venv = (parent_dir / ".venv").exists()

    print(f"\nSUCCESS: Harness cloned to {target_dir}")
    print("\nNEXT STEPS:")
    print(f"1. cd {args.target_dir}")
    
    if has_venv:
        print("2. source ../.venv/bin/activate  (Recommended: Activate your Python environment)")
    elif has_reqs:
        print("2. Create and activate a Python virtual environment, then 'pip install -r ../requirements.txt'")
    elif has_package_json:
        print("2. npm install  (Ensure your node modules are installed)")
    else:
        print("2. Activate your project's runtime environment (e.g., venv, nvm) before running tests.")
    
    print(f"3. Start your {selected_platform} session!")

if __name__ == "__main__":
    main()
