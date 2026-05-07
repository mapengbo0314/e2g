import os
import json
import yaml

def reload_agents():
    """Regenerates .gemini/agents/*.md from _agents/agents/*/ config files."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    agents_src_dir = os.path.join(base_dir, "_agents", "agents")
    output_dir = os.path.join(base_dir, ".gemini", "agents")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Reloading agents from {agents_src_dir} to {output_dir}...")
    
    updated_count = 0
    import glob
    import shutil

    # Recursively find all agents (handling subdirectories like core/ and discovery/ and specialized/)
    # We look for agent.json (legacy) and .md files (new flattened)
    agent_candidates = []
    
    # Search for legacy agent.json bundles
    for root, dirs, files in os.walk(agents_src_dir):
        if "agent.json" in files:
            agent_candidates.append(("legacy", root, os.path.basename(root)))
            
    # Search for flattened .md agents
    for root, dirs, files in os.walk(agents_src_dir):
        for file in files:
            if file.endswith(".md"):
                # Ensure it has yaml frontmatter to avoid picking up random READMEs
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    first_line = f.readline().strip()
                    if first_line == "---":
                        agent_candidates.append(("flat", root, file))

    for agent_type, root_dir, agent_identifier in agent_candidates:
        if agent_type == "legacy":
            agent_name = agent_identifier
            agent_json_path = os.path.join(root_dir, "agent.json")
            config_yaml_path = os.path.join(root_dir, "config.yaml")
            
            with open(agent_json_path, "r") as f:
                agent_data = json.load(f)
                
            config_data = {}
            if os.path.exists(config_yaml_path):
                with open(config_yaml_path, "r") as f:
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
                    markdown_content.append(f"# {title}\n")
                    markdown_content.append(content_text.strip() + "\n")
            
            # Sections from instructions schema
            instr = config_data.get('instructions', {})
            if instr:
                if 'goals' in instr:
                    markdown_content.append("# Goals\n")
                    for goal in instr['goals']:
                        markdown_content.append(f"- {goal}")
                    markdown_content.append("")
                if 'constraints' in instr:
                    markdown_content.append("# Constraints\n")
                    for constraint in instr['constraints']:
                        markdown_content.append(f"- {constraint}")
                    markdown_content.append("")
                    
            # Capabilities
            caps = config_data.get('capabilities', {})
            if caps:
                markdown_content.append("# Capabilities\n")
                for cap_name, cap_list in caps.items():
                    markdown_content.append(f"## {cap_name.replace('_', ' ').title()}")
                    if isinstance(cap_list, list):
                        for item in cap_list:
                            markdown_content.append(f"- {item}")
                    else:
                        markdown_content.append(str(cap_list))
                    markdown_content.append("")
                    
            output_file = os.path.join(output_dir, f"{agent_name}.md")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(markdown_content))
            print(f"  [+] {agent_name} -> {output_file}")
            updated_count += 1
            
        elif agent_type == "flat":
            agent_file_path = os.path.join(root_dir, agent_identifier)
            output_file = os.path.join(output_dir, agent_identifier)
            shutil.copy2(agent_file_path, output_file)
            print(f"  [+] {agent_identifier.replace('.md', '')} (Flat) -> {output_file}")
            updated_count += 1

    print(f"\nSuccessfully reloaded {updated_count} agents.")

if __name__ == "__main__":
    reload_agents()
