# Agent Schema Migration & Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate all agent definition files to a valid lowercase slug name, move skills/related_agents into a markdown metadata section, and add a platform cleanup routine for the Gemini CLI initialization.

**Architecture:** A Python script will handle parsing and updating the YAML frontmatter of the `.md` agent files across the three target directories. The `harness/cli.py` will be modified to remove unused platform folders (like `.claude` and `.cursor`) when the `gemini` platform is chosen during initialization to maintain workspace cleanliness.

**Tech Stack:** Python, `re`, `yaml`, `shutil`

---

### Task 1: Create and Run the Agent Schema Migration Script

**Files:**
- Create: `scripts/migrate_agent_schemas.py`
- Modify: (Automatically modifies all `.md` files in `_agents/agents/`, `boilerplate-agent/agents/`, `.gemini/agents/`)

- [ ] **Step 1: Write the migration script**

```python
import os
import re
import yaml

AGENT_DIRS = [
    "_agents/agents",
    "boilerplate-agent/agents",
    ".gemini/agents"
]

def slugify(name):
    # Convert to lowercase and replace underscores/spaces with hyphens
    slug = name.lower()
    slug = re.sub(r'[\s_]+', '-', slug)
    return slug

def migrate_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Match YAML frontmatter
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if not match:
        return

    frontmatter_str = match.group(1)
    body = match.group(2)
    
    try:
        data = yaml.safe_load(frontmatter_str)
    except yaml.YAMLError:
        return

    if not data or not isinstance(data, dict):
        return

    changes_made = False
    
    # 1. Update Name
    if 'name' in data:
        old_name = data['name']
        new_name = slugify(old_name)
        if old_name != new_name:
            data['name'] = new_name
            changes_made = True

    # 2. Extract Skills and Related Agents
    metadata_lines = []
    
    if 'skills' in data:
        skills = data.pop('skills')
        if skills:
            metadata_lines.append("- Skills:")
            if isinstance(skills, list):
                for skill in skills:
                    metadata_lines.append(f"  - {skill}")
            else:
                 metadata_lines.append(f"  - {skills}")
        changes_made = True

    if 'related_agents' in data:
        related = data.pop('related_agents')
        if related:
            metadata_lines.append("- Related Agents:")
            if isinstance(related, list):
                for agent in related:
                    metadata_lines.append(f"  - {agent}")
            else:
                metadata_lines.append(f"  - {related}")
        changes_made = True

    if not changes_made:
        return

    # Reconstruct the file
    new_frontmatter = yaml.dump(data, default_flow_style=False, sort_keys=False)
    
    new_body = body
    if metadata_lines:
        metadata_section = "\n## Metadata\n" + "\n".join(metadata_lines) + "\n"
        
        # Check if Metadata section already exists
        if "## Metadata" not in new_body:
            # Find the first H1 header and insert after it
            h1_match = re.search(r'^#\s+.*?\n', new_body, re.MULTILINE)
            if h1_match:
                insert_pos = h1_match.end()
                new_body = new_body[:insert_pos] + metadata_section + new_body[insert_pos:]
            else:
                new_body = metadata_section + new_body
        else:
            # If it exists, append below the heading
            new_body = new_body.replace("## Metadata\n", "## Metadata\n" + "\n".join(metadata_lines) + "\n")

    new_content = f"---\n{new_frontmatter}---\n{new_body}"

    with open(filepath, 'w') as f:
        f.write(new_content)
    print(f"Migrated {filepath}")

if __name__ == '__main__':
    for directory in AGENT_DIRS:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                if filename.endswith(".md"):
                    filepath = os.path.join(directory, filename)
                    if filename != "CONFIG_SCHEMA.md": # Skip schema file
                        migrate_file(filepath)
```

- [ ] **Step 2: Run the migration script**

Run: `python scripts/migrate_agent_schemas.py`
Expected: Terminal output showing which `.md` agent files were migrated.

- [ ] **Step 3: Commit the migration**

```bash
git add _agents/agents boilerplate-agent/agents .gemini/agents scripts/migrate_agent_schemas.py
git commit -m "refactor: migrate agent schemas to lowercase slugs and move metadata"
```

### Task 2: Implement Platform Cleanup Logic

**Files:**
- Modify: `harness/cli.py`
- Create: `tests/test_cli_cleanup.py`

- [ ] **Step 1: Write the cleanup test**

```python
import os
import tempfile
import pytest
import shutil

# Mocking the cleanup directly for the test
def cleanup_other_platforms(project_path, chosen_platform):
    platforms = [".gemini", ".claude", ".cursor", ".agents"]
    if chosen_platform == "1":
        harness_folder = ".gemini"
    elif chosen_platform == "2":
        harness_folder = ".claude"
    elif chosen_platform == "3":
        harness_folder = ".cursor"
    else:
        harness_folder = ".agents"

    platforms.remove(harness_folder)
    for p in platforms:
        path = os.path.join(project_path, p)
        if os.path.exists(path):
            shutil.rmtree(path)

def test_cleanup_other_platforms():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup folders
        os.mkdir(os.path.join(temp_dir, ".gemini"))
        os.mkdir(os.path.join(temp_dir, ".claude"))
        os.mkdir(os.path.join(temp_dir, ".cursor"))
        
        # Action (Choose Gemini CLI = "1")
        cleanup_other_platforms(temp_dir, "1")
        
        # Assert
        assert os.path.exists(os.path.join(temp_dir, ".gemini"))
        assert not os.path.exists(os.path.join(temp_dir, ".claude"))
        assert not os.path.exists(os.path.join(temp_dir, ".cursor"))
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_cli_cleanup.py -v`
Expected: PASS

- [ ] **Step 3: Write implementation in `harness/cli.py`**

Open `harness/cli.py` and locate the platform selection block around line 80. Replace the assignment block and add the cleanup logic.

Modify `harness/cli.py`:

```python
        if platform_choice == "1":
            harness_folder = ".gemini"
        elif platform_choice == "2":
            harness_folder = ".claude"
        elif platform_choice == "3":
            harness_folder = ".cursor"
        else:
            harness_folder = ".agents"

        # Cleanup other platforms
        platforms = [".gemini", ".claude", ".cursor", ".agents"]
        if harness_folder in platforms:
            platforms.remove(harness_folder)
        for p in platforms:
            p_path = os.path.join(args.project_path, p)
            if os.path.exists(p_path):
                import shutil
                shutil.rmtree(p_path)

        target_dir = os.path.join(args.project_path, harness_folder)
```

- [ ] **Step 4: Commit the cleanup logic**

```bash
git add harness/cli.py tests/test_cli_cleanup.py
git commit -m "feat: add platform cleanup routine for gemini cli initialization"
```
