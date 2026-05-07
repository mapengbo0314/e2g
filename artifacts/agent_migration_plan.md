# Agent Migration Plan

**Goal:** Automate the migration of agent definition files in `/Users/pengbolicious/pengbo-apps/depreciated_indexing/.gemini/agents/` to adhere strictly to the Gemini CLI schema.

**Target Fixes:**
1. Convert `name` fields to valid URL-safe slugs (e.g., `ArchitectureDeepener` -> `architecture-deepener`).
2. Remove unrecognized keys (`skills`, `related_agents`) from the YAML frontmatter.
3. Append extracted unrecognized keys into the Markdown body under a `## Metadata` heading.

## Execution Script

Save the following Python script (e.g., `migrate_agents.py`) and run it.

*Requirement: You will need the `pyyaml` package installed (`pip install pyyaml`).*

```python
#!/usr/bin/env python3
import os
import re
import yaml

TARGET_DIR = "/Users/pengbolicious/pengbo-apps/depreciated_indexing/.gemini/agents/"

def to_slug(text):
    """Converts CamelCase/PascalCase and spaces to lowercase kebab-case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', text)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()
    # Replace spaces or underscores with hyphens
    s3 = re.sub(r'[\s_]+', '-', s2)
    # Remove any non-alphanumeric characters (except hyphens)
    return re.sub(r'[^a-z0-9-]', '', s3)

def migrate_agent_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Match the frontmatter block
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if not match:
        print(f"Skipping {filepath}: No YAML frontmatter found.")
        return

    frontmatter_str = match.group(1)
    body = match.group(2)

    try:
        data = yaml.safe_load(frontmatter_str)
    except yaml.YAMLError as e:
        print(f"Skipping {filepath}: YAML parsing error - {e}")
        return

    if not isinstance(data, dict):
        return

    # Extract invalid keys to move to the body
    skills = data.pop('skills', None)
    related_agents = data.pop('related_agents', None)
    
    # Fix the name to be a valid slug
    original_name = data.get('name', '')
    if original_name:
        data['name'] = to_slug(original_name)

    # Re-serialize frontmatter, explicitly keeping only allowed keys
    new_data = {}
    if 'name' in data: new_data['name'] = data['name']
    if 'description' in data: new_data['description'] = data['description']
    if 'tools' in data: new_data['tools'] = data['tools']

    new_frontmatter = yaml.dump(new_data, sort_keys=False, default_flow_style=False).strip()

    # Prepare the metadata section to append to the Markdown body
    metadata_lines = []
    if skills or related_agents:
        metadata_lines.append("## Metadata")
        if skills:
            if isinstance(skills, list):
                skills_str = ", ".join(skills)
            else:
                skills_str = str(skills)
            metadata_lines.append(f"**Skills:** {skills_str}")
            
        if related_agents:
            if isinstance(related_agents, list):
                agents_str = ", ".join(related_agents)
            else:
                agents_str = str(related_agents)
            metadata_lines.append(f"**Related Agents:** {agents_str}")
        metadata_lines.append("") # Trailing newline for spacing

    # Append metadata to the bottom of the document if we removed any from frontmatter
    new_body = body
    if metadata_lines:
        if not new_body.endswith('\n'):
            new_body += '\n'
        new_body += '\n' + '\n'.join(metadata_lines)

    # Reassemble and write back the file
    new_content = f"---\n{new_frontmatter}\n---{new_body}"
    with open(filepath, 'w') as f:
        f.write(new_content)
    
    print(f"Migrated: {filepath}")

def main():
    if not os.path.isdir(TARGET_DIR):
        print(f"Error: Target directory {TARGET_DIR} does not exist.")
        return
        
    for filename in os.listdir(TARGET_DIR):
        if filename.endswith('.md'):
            migrate_agent_file(os.path.join(TARGET_DIR, filename))
            
    print("Migration complete.")

if __name__ == '__main__':
    main()
```
