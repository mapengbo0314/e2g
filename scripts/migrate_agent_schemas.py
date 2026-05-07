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
        return None

    frontmatter_str = match.group(1)
    body = match.group(2)
    
    try:
        data = yaml.safe_load(frontmatter_str)
    except yaml.YAMLError:
        return None

    if not data or not isinstance(data, dict):
        return None

    old_name = data.get('name', '')
    new_name = slugify(old_name) if old_name else old_name
    
    if 'name' in data and old_name != new_name:
        data['name'] = new_name
        
    skills = []
    related_agents = []
    
    fm_skills = data.pop('skills', [])
    if isinstance(fm_skills, str): fm_skills = [fm_skills]
    for s in fm_skills:
        if s not in skills:
            skills.append(s)
            
    fm_related = data.pop('related_agents', [])
    if isinstance(fm_related, str): fm_related = [fm_related]
    for a in fm_related:
        if a not in related_agents:
            related_agents.append(a)

    # Parse existing body for ## Metadata blocks
    metadata_pattern = r'## Metadata\n.*?(?=\n## |\Z)'
    for match_metadata in re.finditer(metadata_pattern, body, re.DOTALL):
        metadata_block = match_metadata.group(0)
        current_list = None
        for line in metadata_block.split('\n'):
            if line.startswith('- Skills:'):
                current_list = skills
            elif line.startswith('- Related Agents:'):
                current_list = related_agents
            elif line.startswith('- Name:') or line.startswith('- Description:'):
                current_list = None
            elif line.startswith('  - '):
                if current_list is not None:
                    item = line[4:].strip()
                    if item not in current_list:
                        current_list.append(item)
            elif line.strip() == '':
                continue
            elif line.startswith('-'):
                current_list = None

    # Remove all existing metadata blocks from body
    body_no_metadata = re.sub(metadata_pattern + r'\n?', '', body, flags=re.DOTALL)

    # Reconstruct Metadata block
    metadata_lines = []
    if skills:
        metadata_lines.append("- Skills:")
        for s in skills:
            metadata_lines.append(f"  - {s}")
    if related_agents:
        metadata_lines.append("- Related Agents:")
        for a in related_agents:
            metadata_lines.append(f"  - {a}")

    new_metadata_text = ""
    if metadata_lines:
        new_metadata_text = "## Metadata\n" + "\n".join(metadata_lines) + "\n"

    new_body = body_no_metadata
    if new_metadata_text:
        h1_match = re.search(r'^#\s+.*?\n', new_body, re.MULTILINE)
        if h1_match:
            insert_pos = h1_match.end()
            new_body = new_body[:insert_pos] + "\n" + new_metadata_text + new_body[insert_pos:]
        else:
            new_body = new_metadata_text + "\n" + new_body

    new_frontmatter = yaml.dump(data, default_flow_style=False, sort_keys=False)
    new_content = f"---\n{new_frontmatter}---\n{new_body}"

    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    
    new_filepath = filepath
    expected_filename = new_name + ".md" if new_name else filename
    
    if filename != expected_filename and 'name' in data:
        new_filepath = os.path.join(directory, expected_filename)

    with open(new_filepath, 'w') as f:
        f.write(new_content)
        
    if filepath != new_filepath:
        if os.path.exists(filepath):
            os.remove(filepath)
        print(f"Migrated and renamed {filepath} -> {new_filepath}")
    else:
        print(f"Migrated {filepath}")
        
    return new_filepath

if __name__ == '__main__':
    for directory in AGENT_DIRS:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                if filename.endswith(".md"):
                    filepath = os.path.join(directory, filename)
                    if filename != "config-schema.md": # Skip schema file
                        migrate_file(filepath)
