# Integration Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the pathing of `AGENTS.md`, update bash script paths, fix the specialized agent instructions, and upgrade `reload_agents.py` to support Markdown agents.

**Architecture:** 
1. `AGENTS.md` will be moved from `.agents/AGENTS.md` to `<project_root>/AGENTS.md` during minting.
2. `setup_harness.sh` paths will be updated to point to `.agents/skills/*.md` instead of `_agents/skills/*.md`.
3. Specialized agent prompt templates will be updated to tell agents to list `.gemini/skills/` (or platform equivalent) rather than manually checking the source directory.
4. `_agents/reload_agents.py` will be refactored to parse either `agent.json`/`config.yaml` bundles OR standalone `.md` files with YAML frontmatter.

**Tech Stack:** Python.

---

### Task 1: Fix Root Placement of `AGENTS.md`

**Files:**
- Modify: `harness/minting_engine.py`

- [ ] **Step 1: Move `AGENTS.md` to the root after copying the boilerplate**
In `harness/minting_engine.py`, find where the boilerplate is copied (around line 20). Add logic to move `AGENTS.md` from `target_path` to `project_path`.

```python
import re
with open("harness/minting_engine.py", "r") as f:
    content = f.read()

pattern = r"(if boilerplate_dir and os\.path\.exists\(boilerplate_dir\):\n\s+shutil\.copytree.*?else:\n\s+print\(\"Error: Boilerplate directory not found\.\"\)\n\s+return)"

new_logic = """\\1

    # Move AGENTS.md to the project root
    agents_md_src = target_path / "AGENTS.md"
    agents_md_dest = Path(project_path) / "AGENTS.md"
    if agents_md_src.exists():
        shutil.move(str(agents_md_src), str(agents_md_dest))
"""
new_content = re.sub(pattern, new_logic, content)
with open("harness/minting_engine.py", "w") as f:
    f.write(new_content)
```

- [ ] **Step 2: Commit**
```bash
git add harness/minting_engine.py
git commit -m "fix: move AGENTS.md to project root during minting"
```

### Task 2: Fix Bash Script Paths & Specialized Prompt

**Files:**
- Modify: `harness/minting_engine.py`

- [ ] **Step 1: Update skill source path in the bash script generation**
Find the bash script templates (around line 110) where it says `for skill_file in _agents/skills/*.md; do`. Change it to use `target_path.name`.

```python
import re
with open("harness/minting_engine.py", "r") as f:
    content = f.read()

# Replace _agents/skills with the dynamic target path name
content = content.replace("for skill_file in _agents/skills/*.md; do", 
                          f"for skill_file in {{target_path.name}}/skills/*.md; do")

with open("harness/minting_engine.py", "w") as f:
    f.write(content)
```

- [ ] **Step 2: Fix the specialized agent `core_mandates` string**
Find the `core_mandates` variable definition (around line 200). Change the instruction from running `list_directory` on the raw folder to using native tools or platform folders.

```python
with open("harness/minting_engine.py", "r") as f:
    content = f.read()

old_mandate = "3. Superpower Workflows: You MUST run `list_directory` on `{target_path.name}/skills/` at the start of your session to discover available local skills."
new_mandate = "3. Superpower Workflows: You MUST utilize installed Superpower skills. If your platform supports a skill tool (e.g. `activate_skill`, `skill`), use it. Otherwise, read the `.md` files located in `{target_path.name}/skills/`."

content = content.replace(old_mandate, new_mandate)

with open("harness/minting_engine.py", "w") as f:
    f.write(content)
```

- [ ] **Step 3: Commit**
```bash
git add harness/minting_engine.py
git commit -m "fix: correct skill paths and specialized agent prompt"
```

### Task 3: Upgrade `reload_agents.py` to Support Markdown Agents

**Files:**
- Modify: `_agents/reload_agents.py`

- [ ] **Step 1: Update script to parse `.md` files with frontmatter**
Rewrite the loop in `reload_agents()` to check if an entry is a directory (legacy bundle) OR a file ending in `.md` (new specialized agent).

```python
import re
with open("_agents/reload_agents.py", "r") as f:
    content = f.read()

# Replace the agent loading loop
pattern = r"for agent_name in sorted\(os\.listdir\(agents_src_dir\)\):.*?(?=print\(f\"\\nSuccessfully reloaded {updated_count} agents\.\"\))"

new_logic = """for agent_name in sorted(os.listdir(agents_src_dir)):
        agent_path = os.path.join(agents_src_dir, agent_name)
        
        # 1. Handle Legacy Folders (agent.json + config.yaml)
        if os.path.isdir(agent_path):
            agent_json_path = os.path.join(agent_path, "agent.json")
            config_yaml_path = os.path.join(agent_path, "config.yaml")
            
            if not os.path.exists(agent_json_path):
                continue
                
            with open(agent_json_path, 'r') as f:
                agent_data = json.load(f)
                
            config_data = {}
            if os.path.exists(config_yaml_path):
                with open(config_yaml_path, 'r') as f:
                    config_data = yaml.safe_load(f) or {}
            
            markdown_content = []
            
            # Frontmatter
            markdown_content.append("---")
            markdown_content.append(f"name: {agent_data.get('name', agent_name)}")
            markdown_content.append(f"description: {agent_data.get('description', '').strip()}")
            markdown_content.append("---")
            
            # Sections from prompt_section_customization
            sections = config_data.get('prompt_section_customization', {}).get('add_prompt_sections', [])
            for section_wrapper in sections:
                section = section_wrapper.get('prompt_section', {})
                title = section.get('title')
                content_text = section.get('content')
                if title and content_text:
                    markdown_content.append(f"# {title}\\n")
                    markdown_content.append(content_text.strip() + "\\n")
            
            # Sections from instructions schema
            instr = config_data.get('instructions', {})
            if instr:
                if 'goals' in instr:
                    markdown_content.append("# Goals\\n")
                    for goal in instr['goals']:
                        markdown_content.append(f"- {goal}")
                    markdown_content.append("")
                if 'constraints' in instr:
                    markdown_content.append("# Constraints\\n")
                    for constraint in instr['constraints']:
                        markdown_content.append(f"- {constraint}")
                    markdown_content.append("")
                    
            # Capabilities
            caps = config_data.get('capabilities', {})
            if caps:
                markdown_content.append("# Capabilities\\n")
                for cap_name, cap_list in caps.items():
                    markdown_content.append(f"## {cap_name.replace('_', ' ').title()}")
                    if isinstance(cap_list, list):
                        for item in cap_list:
                            markdown_content.append(f"- {item}")
                    else:
                        markdown_content.append(str(cap_list))
                    markdown_content.append("")
                    
            output_file = os.path.join(output_dir, f"{agent_name}.md")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("\\n".join(markdown_content))
            print(f"  [+] {agent_name} -> {output_file}")
            updated_count += 1
            
        # 2. Handle New Flattened Markdown Agents (.md)
        elif os.path.isfile(agent_path) and agent_name.endswith('.md'):
            # Just copy the flat markdown file directly to the output directory
            output_file = os.path.join(output_dir, agent_name)
            shutil.copy2(agent_path, output_file)
            print(f"  [+] {agent_name.replace('.md', '')} (Flat) -> {output_file}")
            updated_count += 1

    """

new_content = re.sub(pattern, new_logic, content, flags=re.DOTALL)
with open("_agents/reload_agents.py", "w") as f:
    f.write(new_content)
```

- [ ] **Step 2: Ensure `shutil` is imported**
Run `grep "import shutil" _agents/reload_agents.py`. If not found, add it to the top.

- [ ] **Step 3: Commit**
```bash
git add _agents/reload_agents.py
git commit -m "feat: upgrade reload_agents.py to support flat markdown agents"
```
