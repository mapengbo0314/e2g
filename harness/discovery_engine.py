import json
import subprocess
import time
import urllib.request
import os

def acquire_mcp_context(project_path: str, bundle_path: str = None, detailed: bool = False) -> str:
    """Acquires project context from the core wiki files. Detailed mode reads everything."""

    # Check bundle path first if provided
    if bundle_path:
        bundle_wiki_path = os.path.join(bundle_path, "wiki") if not bundle_path.endswith("wiki") else bundle_path
        # If the user passed the path to the indxr folder itself
        if not os.path.exists(bundle_wiki_path) and os.path.basename(bundle_path) == ".indxr":
            bundle_wiki_path = os.path.join(bundle_path, "wiki")
        elif not os.path.exists(bundle_wiki_path):
             bundle_wiki_path = os.path.join(bundle_path, ".indxr", "wiki")

        if os.path.exists(bundle_wiki_path):
            wiki_path = bundle_wiki_path
            print(f"Found existing wiki in bundle at {wiki_path}. Reading core architecture...")
        else:
            wiki_path = os.path.join(project_path, ".indxr", "wiki")
    else:
        wiki_path = os.path.join(project_path, ".indxr", "wiki")

    context_parts = []

    if os.path.exists(wiki_path):
        if not bundle_path or wiki_path == os.path.join(project_path, ".indxr/wiki"):
             print(f"Found existing .indxr/wiki at {wiki_path}. Reading context...")

        # Read ONLY the index and architecture by default to avoid token explosion
        # Detailed mode reads everything in the wiki
        if detailed:
            for root, _, files in os.walk(wiki_path):
                for file in files:
                    if file.endswith(".md"):
                        p = os.path.join(root, file)
                        with open(p, 'r') as f:
                            context_parts.append(f"=== {file.upper()} ===\n" + f.read())
        else:
            for core_file in ["index.md", "architecture.md"]:
                p = os.path.join(wiki_path, core_file)
                if os.path.exists(p):
                    with open(p, 'r') as f:
                        context_parts.append(f"=== {core_file.upper()} ===\n" + f.read())

        if context_parts:
            return "\n\n".join(context_parts)

    # Return None instead of a string if no wiki is found so caller can handle fallback
    return None


def fetch_remote_skill(skill_url: str) -> str:
    """Fetches a skill definition from a raw GitHub URL."""
    try:
        req = urllib.request.Request(skill_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"WARNING: Failed to fetch skill from {skill_url}")
        print(f"Details: {e}")
        return None # Graceful fallback

def fetch_skill(skill_name: str, remote_url: str) -> str:
    """Fetches a skill definition from remote URL or fallback to local storage."""
    content = fetch_remote_skill(remote_url)
    if content:
        return content
        
    print(f"Attempting to load skill {skill_name} from local fallback...")
    home = os.path.expanduser("~")
    local_paths = [
        os.path.join(home, ".agents", "skills", skill_name, "SKILL.md"),
        os.path.join(home, ".gemini", "extensions", "superpowers", "skills", skill_name, "SKILL.md"),
        os.path.join(".agents", "skills", skill_name, "SKILL.md")
    ]
    
    for p in local_paths:
        if os.path.exists(p):
            try:
                with open(p, 'r') as f:
                    return f.read()
            except Exception:
                continue

    return None

def query_llm(prompt: str, llm_provider: str, api_key: str, model: str = None) -> str:
    """Dispatches to the real LLM providers."""
    if llm_provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        use_model = model or "gpt-4o"
        response = client.chat.completions.create(
            model=use_model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
        
    elif llm_provider == "anthropic":
        import urllib.request
        import json
        use_model = model or "claude-3-5-sonnet-20241022"
        data = {
            "model": use_model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}]
        }
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(data).encode("utf-8"),
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["content"][0]["text"]
            
    elif llm_provider == "gemini":
        from google import genai
        client = genai.Client(api_key=api_key)
        # Fix model name format: Gemini SDK often expects 'gemini-3.1-pro-preview' without 'models/' prefix 
        # but depending on the SDK version, it might require it. Let's ensure it's robust.
        use_model = model or "gemini-3.1-pro-preview"
        
        try:
            # We are using generate_content, which is synchronous. It might take 10-20 seconds.
            response = client.models.generate_content(
                model=use_model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini API call failed: {e}")
        
    raise ValueError(f"Unsupported LLM provider: {llm_provider}")

def discover_agents(context_str: str, feature_fetcher_yaml_path: str, llm_provider: str, api_key: str, model: str = None, ddd_context: dict = None) -> list[dict]:
    """Loads the system prompt and queries the LLM."""
    system_prompt = "You are the Feature Fetcher."
    try:
        import yaml
        with open(feature_fetcher_yaml_path, 'r') as f:
            config = next(yaml.safe_load_all(f), {})
            if config and isinstance(config, dict) and "system_prompt" in config:
                system_prompt = config["system_prompt"]
    except Exception as e:
        print(f"Warning: Could not load feature-fetcher prompt: {e}")

    print("Loading skills for Agent Discovery...")
    arch_skill = fetch_skill("improve-codebase-architecture", "https://raw.githubusercontent.com/mattpocock/skills/main/skills/engineering/improve-codebase-architecture/SKILL.md")
    grill_docs_skill = fetch_skill("grill-with-docs", "https://raw.githubusercontent.com/mattpocock/skills/main/skills/engineering/grill-with-docs/SKILL.md")
    agentic_eval_skill = fetch_skill("agentic-eval", "https://raw.githubusercontent.com/github/awesome-copilot/main/skills/agentic-eval/SKILL.md")
    prompt_engineer_skill = fetch_skill("prompt-engineer", "https://raw.githubusercontent.com/Jeffallan/claude-skills/main/skills/prompt-engineer/SKILL.md")

    ddd_prompt_section = ""
    if ddd_context:
        ddd_prompt_section = (
            "=== DOMAIN-DRIVEN DESIGN (DDD) CONTEXT ===\n"
            "The following domain knowledge and user alignment answers MUST be intrinsically woven into each agent's identity and responsibilities:\n"
            f"Ubiquitous Language: {ddd_context.get('ubiquitous_language', 'None provided')}\n"
            f"Translation Map (User Answers): {json.dumps(ddd_context.get('translation_map', {}))}\n"
            f"Legacy Hints: {json.dumps(ddd_context.get('legacy_hints', {}))}\n"
            f"Additional Knowledge: {ddd_context.get('additional_domain_knowledge', 'None provided')}\n\n"
            "Ensure the agents' system prompts incorporate this domain-specific knowledge intrinsically. Do not just append it; use it to specialize their roles.\n"
            "Specifically, you MUST use the Translation Map to bridge legacy terms with the Ubiquitous Language, and define their responsibilities based on the boundaries identified in these DDD concepts.\n\n"
        )

    full_prompt = (
        f"{system_prompt}\n\n"
        "You must utilize the principles from the following skills to guide your agent recommendations:\n\n"
        "=== IMPROVE CODEBASE ARCHITECTURE ===\n"
        f"{arch_skill}\n\n"
        "=== GRILL WITH DOCS ===\n"
        f"{grill_docs_skill}\n\n"
        "PROJECT CONTEXT:\n"
        f"{context_str}\n\n"
        f"{ddd_prompt_section}"
        "TASK:\n"
        "Recommend 3-5 specialized agents. For EACH agent, you MUST provide:\n"
        "1. 'name': Concise name.\n"
        "2. 'role': Brief responsibility summary.\n"
        "3. 'zone': (Domain/Data/Handler/Core).\n"
        "4. 'system_prompt': A comprehensive, 300-500 word Markdown system prompt. This prompt MUST:\n"
        "   - Define their specific expertise relative to the project files.\n"
        "   - Enforce the use of 'indxr' MCP tools and local skills.\n"
        "   - Define their 'Goldfish' phase responsibilities.\n\n"
        "Return as JSON: {'agents': [{'name': '...', 'role': '...', 'zone': '...', 'system_prompt': '...'}]}"
    )
    
    print(f"Querying {llm_provider} for specialized agents...")
    response_text = query_llm(full_prompt, llm_provider, api_key, model)
    
    try:
        cleaned = response_text.replace("```json", "").replace("```", "").strip()
        # Find JSON boundaries if LLM included conversational text
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}") + 1
        if start_idx != -1 and end_idx != 0:
            cleaned = cleaned[start_idx:end_idx]
            
        data = json.loads(cleaned)
        return data.get("agents", [])
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse LLM response as JSON: {e}\nResponse:\n{response_text}")
        return [{"name": "Architect", "role": "General architecture and design", "zone": "Core"}]

def discover_ddd_context(context_str: str, llm_provider: str, api_key: str, model: str = None) -> dict:
    """Extracts DDD context using remote skills and deterministic questions."""
    print("Loading skills for DDD alignment...")
    grill_me_skill = fetch_skill("grill-me", "https://raw.githubusercontent.com/mattpocock/skills/main/skills/productivity/grill-me/SKILL.md")
    grill_with_docs_skill = fetch_skill("grill-with-docs", "https://raw.githubusercontent.com/mattpocock/skills/main/skills/engineering/grill-with-docs/SKILL.md")
    agentic_eval_skill = fetch_skill("agentic-eval", "https://raw.githubusercontent.com/github/awesome-copilot/main/skills/agentic-eval/SKILL.md")
    prompt_engineer_skill = fetch_skill("prompt-engineer", "https://raw.githubusercontent.com/Jeffallan/claude-skills/main/skills/prompt-engineer/SKILL.md")

    prompt = (
        "You are a strict Domain-Driven Design architect. Analyze the project context and execute the provided skills.\n\n"
        "AVOID TECHNICAL PEDANTRY: Do not ask about technical naming (e.g., 'spend vs cost') or implementation details (e.g., 'dataframe skeletons') unless they represent a fundamental business misunderstanding.\n\n"
        "=== DETERMINISTIC DDD FRAMEWORK ===\n"
        "Focus your analysis and questions on these 5 core areas:\n"
        "1. UBIQUITOUS LANGUAGE: What is the exact vocabulary business experts use? Are there overloaded terms across contexts?\n"
        "2. CORE DOMAIN: What is the single core capability that provides primary value/competitive advantage?\n"
        "3. AGGREGATES & INVARIANTS: What data MUST be updated together in a single transaction to maintain business rules?\n"
        "4. DOMAIN EVENTS: Who needs to know when a significant action is completed? (Eventual consistency needs)\n"
        "5. CONTEXT MAPPING: Who dictates the shape of the data contract when interacting with external/other systems?\n\n"
        "Apply the 'agentic-eval' and 'prompt-engineer' skills to self-critique your domain definitions.\n\n"
        "=== GRILL-WITH-DOCS SKILL ===\n"
        f"{grill_with_docs_skill}\n\n"
        "=== GRILL-ME SKILL ===\n"
        f"{grill_me_skill}\n\n"
        "Your task:\n"
        "1. Draft a context definition (context.md style) structured by the 5 Deterministic DDD areas.\n"
        "2. Identify genuine domain ambiguities that cannot be resolved by reading the code.\n"
        "3. Generate 3-5 sharp questions that force the user to define business boundaries, NOT implementation details.\n\n"
        "Your response MUST be in JSON format with exactly these keys:\n"
        "- 'context_draft': A string containing the drafted domain context.\n"
        "- 'questions': A list of strings representing alignment questions.\n"
        "- 'legacy_hints': A dictionary containing hints about legacy components.\n\n"
        f"PROJECT CONTEXT:\n{context_str}"
    )    
    response_text = query_llm(prompt, llm_provider, api_key, model)

    
    try:
        cleaned = response_text.replace("```json", "").replace("```", "").strip()
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}") + 1
        if start_idx != -1 and end_idx != 0:
            cleaned = cleaned[start_idx:end_idx]
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse DDD LLM response as JSON: {e}")
        return {"context_draft": "", "questions": [], "legacy_hints": {}}

def discover_custom_agent(name: str, specs: str, context_str: str, ddd_context: dict, llm_provider: str, api_key: str, model: str = None) -> dict:
    """Generates a system prompt for a custom user-defined agent."""
    
    ddd_prompt_section = ""
    if ddd_context:
        ddd_prompt_section = (
            "=== DOMAIN-DRIVEN DESIGN (DDD) CONTEXT ===\n"
            f"Ubiquitous Language: {ddd_context.get('ubiquitous_language', 'None provided')}\n"
            f"Translation Map: {json.dumps(ddd_context.get('translation_map', {}))}\n"
            f"Additional Knowledge: {ddd_context.get('additional_domain_knowledge', 'None provided')}\n\n"
        )

    prompt = (
        "You are an Agent Architect. Your task is to generate a high-quality system prompt for a new specialized agent.\n\n"
        "=== PROJECT CONTEXT ===\n"
        f"{context_str}\n\n"
        f"{ddd_prompt_section}"
        "=== USER REQUEST ===\n"
        f"Agent Name: {name}\n"
        f"Agent Role/Specs: {specs}\n\n"
        "=== TASK ===\n"
        "Generate a comprehensive, 300-500 word Markdown system prompt for this agent. The prompt MUST:\n"
        "1. Define their specific expertise relative to the project files.\n"
        "2. Enforce the use of 'indxr' MCP tools and local skills.\n"
        "3. Define their role in the Goldfish Protocol (Phase 3) and Implementation (Phase 4).\n"
        "4. Incorporate the DDD context and ubiquitous language intrinsically.\n\n"
        "Return as JSON: {'name': '...', 'role': '...', 'zone': '...', 'system_prompt': '...'}"
    )
    
    print(f"Generating specialized prompt for custom agent: {name}...")
    response_text = query_llm(prompt, llm_provider, api_key, model)
    
    try:
        cleaned = response_text.replace("```json", "").replace("```", "").strip()
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}") + 1
        if start_idx != -1 and end_idx != 0:
            cleaned = cleaned[start_idx:end_idx]
            
        data = json.loads(cleaned)
        return data
    except Exception as e:
        print(f"Error generating custom agent: {e}")
        return {"name": name, "role": specs, "zone": "Core", "system_prompt": f"# {name}\n\n{specs}"}

def detect_tech_stack(project_path: str) -> str:
    """Heuristic detection of tech stack from project files, searching up to 2 levels deep."""
    stacks = set()
    
    # Files we are looking for
    markers = {
        "package.json": "Node.js/JavaScript",
        "tsconfig.json": "Node.js/TypeScript",
        "requirements.txt": "Python",
        "pyproject.toml": "Python",
        "Pipfile": "Python",
        "setup.py": "Python",
        "Cargo.toml": "Rust",
        "go.mod": "Go",
        "pom.xml": "JVM (Java/Kotlin)",
        "build.gradle": "JVM (Java/Kotlin)",
        "composer.json": "PHP"
    }

    # Walk directory structure, max 2 levels deep
    start_depth = project_path.rstrip(os.path.sep).count(os.path.sep)
    for root, dirs, files in os.walk(project_path):
        current_depth = root.count(os.path.sep)
        if current_depth - start_depth >= 2:
            dirs[:] = [] # Stop recursion
            continue
            
        for file in files:
            if file in markers:
                stacks.add(markers[file])

    # If TypeScript is found, prefer it over plain JavaScript
    if "Node.js/TypeScript" in stacks and "Node.js/JavaScript" in stacks:
        stacks.remove("Node.js/JavaScript")

    # Add Frontend marker for Node projects
    final_stacks = list(stacks)
    if any("Node.js" in s for s in final_stacks):
        final_stacks.append("Frontend")
        
    return ", ".join(sorted(final_stacks)) if final_stacks else "Unknown Stack"

def generate_onboarding_domain_doc(project_path: str, domain_summary: str, query_llm_fn=None, llm_provider=None, api_key=None, context_str="", boilerplate_dir: str = None):
    """Generates the ONBOARDING_DOMAIN.md template using LLM profiling and verified tools."""
    doc_path = os.path.join(project_path, "ONBOARDING_DOMAIN.md")
    
    # 1. Detect Tech Stack
    tech_stack = detect_tech_stack(project_path)
    
    # 2. Load and Flatten Tools Registry
    tools_registry = {}
    flattened_tools = []
    if boilerplate_dir:
        registry_path = os.path.join(boilerplate_dir, "onboarding", "tools.json")
        if os.path.exists(registry_path):
            try:
                with open(registry_path, "r") as f:
                    tools_registry = json.load(f)
                    # Flatten for LLM consumption
                    for cat, tools in tools_registry.get("categories", {}).items():
                        for t in tools:
                            t["category"] = cat
                            flattened_tools.append(t)
            except Exception as e:
                print(f"Warning: Could not load tools registry: {e}")

    # 3. Profile SME via LLM
    sme_name = "domain-sme"
    core_domain_value = "[USER INPUT REQUIRED]"
    invariants = "1. [USER INPUT REQUIRED: Add your own unbreakable rule here]\n"
    glossary = "*   **[Term 1]**: [USER INPUT REQUIRED: Define this term]\n"
    domain_events = "*   **[USER INPUT REQUIRED]**"
    recommended_skills = []
    recommended_mcps = []

    # Pre-populate with forced tools based on tech stack
    for tool in flattened_tools:
        if "force_if_keywords" in tool:
            for kw in tool["force_if_keywords"]:
                if kw.lower() in tech_stack.lower():
                    if tool.get("type") == "mcp":
                        if not any(m["name"] == tool["name"] for m in recommended_mcps):
                            recommended_mcps.append(tool)
                    else:
                        if not any(s["name"] == tool["name"] for s in recommended_skills):
                            recommended_skills.append(tool)
                    break

    if query_llm_fn and llm_provider and api_key:
        prompt = f"""
        You are a Senior Architect. Analyze the project context and recommend a 'Domain SME' agent.
        
        Detected Tech Stack:
        {tech_stack}
        
        Project Context:
        {context_str[:5000]}
        
        Verified Tool Inventory:
        {json.dumps(flattened_tools)}
        
        Task:
        1. Name the SME (e.g. 'marketing-guardian').
        2. Define the Core Domain Value (what is the competitive advantage?).
        3. List 4 strict Domain Invariants (rules to protect logic).
        4. Define 4 Ubiquitous Language terms.
        5. List 2 key Domain Events (what happens that others need to know about?).
        6. Select 2-3 most relevant skills from the Inventory based on the Detected Tech Stack.
        7. Select 1-2 most relevant MCPs from the Inventory based on the Detected Tech Stack.
        
        Return ONLY valid JSON:
        {{
            "sme_name": "...",
            "core_domain_value": "...",
            "invariants": ["...", "..."],
            "glossary": {{"term": "definition"}},
            "domain_events": ["...", "..."],
            "skills": [{{"name": "...", "url": "..."}}],
            "mcps": [{{"name": "...", "command": "...", "type": "mcp"}}]
        }}
        """
        try:
            res = query_llm_fn(prompt, llm_provider, api_key)
            cleaned = res.replace("```json", "").replace("```", "").strip()
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                cleaned = cleaned[start_idx:end_idx]
            data = json.loads(cleaned)
            
            if data.get("sme_name"): sme_name = data["sme_name"]
            core_domain_value = data.get("core_domain_value", "[USER INPUT REQUIRED]")
            if data.get("invariants"):
                invariants = "\n".join([f"{i+1}. {inv}" for i, inv in enumerate(data["invariants"])])
            if data.get("glossary"):
                glossary = "\n".join([f"*   **{k}**: {v}" for k, v in data["glossary"].items()])
            
            domain_events = "*   **[USER INPUT REQUIRED]**"
            if data.get("domain_events"):
                domain_events = "\n".join([f"*   **{e}**" for e in data["domain_events"]])
                
            if data.get("skills"): 
                for skill in data["skills"]:
                    if not any(s["name"] == skill["name"] for s in recommended_skills):
                        recommended_skills.append(skill)
            if data.get("mcps"): 
                for mcp in data["mcps"]:
                    if not any(m["name"] == mcp["name"] for m in recommended_mcps):
                        recommended_mcps.append(mcp)
        except Exception as e:
            print(f"Warning: SME Profiling failed: {e}")
            core_domain_value = "[USER INPUT REQUIRED]"
            domain_events = "*   **[USER INPUT REQUIRED]**"

    # 4. Format Tools for Markdown
    skills_md = "- [ ] No skills recommended"
    if recommended_skills:
        # Format as: - [x] Name (URL)
        skills_md = "\n".join([f"- [x] {s.get('name', 'Unknown')} ({s.get('url', '')})" for s in recommended_skills])
        
    mcps_md = "- [ ] No MCPs recommended"
    if recommended_mcps:
        # Format as: - [x] Name (Command)
        mcps_md = "\n".join([f"- [x] {m.get('name', 'Unknown')} ({m.get('command', '')})" for m in recommended_mcps])

    # 5. Populate Template
    template_str = ""
    if boilerplate_dir:
        template_path = os.path.join(boilerplate_dir, "onboarding", "ONBOARDING_DOMAIN.md.template")
        if os.path.exists(template_path):
            with open(template_path, "r") as f:
                 template_str = f.read()
    
    # Fallback if template missing
    if not template_str:
         template_str = """# Project Onboarding Domain

**Detected Tech Stack:** {{TECH_STACK}}

Based on the codebase scan, I have identified **{{DOMAIN_SUMMARY}}** as a core complex domain. I propose creating a dedicated agent to protect this logic.

## Proposed Domain SME Agent

**Proposed Agent Name:** `@{{SME_NAME}}`
*(Edit the name above if incorrect. Must be lowercase.)*

## Deterministic DDD Alignment

### 1. Ubiquitous Language (Glossary)
*Key terms defined by business experts:*
{{GLOSSARY}}

### 2. Core Domain (Value Proposition)
*The single core capability that provides primary value:*
*   **{{CORE_DOMAIN_VALUE}}**

### 3. Aggregates & Invariants (Transactional Boundaries)
*Data that must absolutely always be updated together:*
{{INVARIANTS}}

### 4. Domain Events & Coordination (Asynchrony)
*Significant actions that others need to know about:*
{{DOMAIN_EVENTS}}

### 5. Context Mapping (Contract Ownership)
*Who dictates the shape of external data contracts:*
*   **[USER INPUT REQUIRED]**: e.g., "We are a 'Conformist' to the Legacy API, but we use an 'Anti-Corruption Layer' for the CRM."

## Proposed Skills
*(Delete the line of any skill you do NOT want installed)*
{{SKILLS_MD}}

## Proposed MCP Tools
*(Delete the line of any MCP you do NOT want installed)*
{{MCPS_MD}}

*(When you have finished editing this file, return to the terminal and press ENTER to continue minting)*
"""

    final_content = template_str.replace("{{TECH_STACK}}", tech_stack)
    final_content = final_content.replace("{{DOMAIN_SUMMARY}}", domain_summary)
    final_content = final_content.replace("{{SME_NAME}}", str(sme_name).lower())
    final_content = final_content.replace("{{CORE_DOMAIN_VALUE}}", core_domain_value)
    final_content = final_content.replace("{{INVARIANTS}}", invariants)
    final_content = final_content.replace("{{GLOSSARY}}", glossary)
    final_content = final_content.replace("{{DOMAIN_EVENTS}}", domain_events)
    final_content = final_content.replace("{{SKILLS_MD}}", skills_md)
    final_content = final_content.replace("{{MCPS_MD}}", mcps_md)

    with open(doc_path, "w") as f:
        f.write(final_content)
    print(f"\n[HARNESS] Generated ONBOARDING_DOMAIN.md at {doc_path}")

