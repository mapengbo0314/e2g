# Harness Onboarding Reliability Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the `harness-wf init` onboarding flow to be reliable and deterministic by using a boilerplate template for `ONBOARDING_DOMAIN.md` and a `tools.json` registry for skill/MCP recommendations, resolving 404 errors and poor LLM generation.

**Architecture:** We are shifting the onboarding discovery phase from generating raw strings via LLM to populating a predefined template (`ONBOARDING_DOMAIN.md.template`) and selecting tools from a verified registry (`tools.json`). The registry will categorize tools (frontend, backend, database) to make tech-stack-based mapping easier.

**Tech Stack:** Python, `harness/discovery_engine.py`, `harness/minting_engine.py`

---

### Task 1: Create the Boilerplate Assets

**Files:**
- Create: `boilerplate-agent/onboarding/ONBOARDING_DOMAIN.md.template`
- Create: `boilerplate-agent/onboarding/tools.json`

- [ ] **Step 1: Write `tools.json`**

```bash
cat << 'EOF' > boilerplate-agent/onboarding/tools.json
{
  "categories": {
    "frontend": [
      {
        "name": "nextjs",
        "url": "https://raw.githubusercontent.com/PatrickJS/awesome-cline-prompts/main/prompts/nextjs.md",
        "keywords": ["react", "nextjs", "next.js", "frontend"]
      },
      {
         "name": "playwright",
         "command": "npx -y @modelcontextprotocol/server-playwright",
         "type": "mcp",
         "keywords": ["react", "nextjs", "frontend", "vue", "svelte"]
      }
    ],
    "backend": [
      {
        "name": "fastapi",
        "url": "https://raw.githubusercontent.com/PatrickJS/awesome-cline-prompts/main/prompts/fastapi.md",
        "keywords": ["fastapi", "python backend"]
      },
      {
        "name": "fetch",
        "command": "npx -y @modelcontextprotocol/server-fetch",
        "type": "mcp",
        "keywords": ["api", "rest", "graphql"]
      }
    ],
    "database": [
      {
        "name": "postgres",
        "command": "npx -y @modelcontextprotocol/server-postgres postgresql://postgres:postgres@localhost:5432/postgres",
        "type": "mcp",
        "keywords": ["postgresql", "postgres", "sql"]
      }
    ]
  }
}
EOF
```

- [ ] **Step 2: Write `ONBOARDING_DOMAIN.md.template`**

```bash
cat << 'EOF' > boilerplate-agent/onboarding/ONBOARDING_DOMAIN.md.template
# Project Onboarding Domain

**Detected Tech Stack:** {{TECH_STACK}}

Based on the codebase scan, I have identified **{{DOMAIN_SUMMARY}}** as a core complex domain. I propose creating a dedicated agent to protect this logic.

## Proposed Domain SME Agent

**Proposed Agent Name:** `@{{SME_NAME}}`
*(Edit the name above if incorrect. Must be lowercase.)*

**Domain Invariants (The absolute rules this agent must enforce):**
{{INVARIANTS}}

**Ubiquitous Language (Key terms to define):**
{{GLOSSARY}}

## Proposed Skills
*(Delete the line of any skill you do NOT want installed)*
{{SKILLS_MD}}

## Proposed MCP Tools
*(Delete the line of any MCP you do NOT want installed)*
{{MCPS_MD}}

*(When you have finished editing this file, return to the terminal and press ENTER to continue minting)*
EOF
```

- [ ] **Step 3: Commit**

```bash
git add boilerplate-agent/onboarding/tools.json boilerplate-agent/onboarding/ONBOARDING_DOMAIN.md.template
git commit -m "feat(onboarding): add templates and verified tools registry"
```

### Task 2: Update `discovery_engine.py` to use Templates and Registry

**Files:**
- Modify: `harness/discovery_engine.py`

- [ ] **Step 1: Write the updated `generate_onboarding_domain_doc` function**

Edit `harness/discovery_engine.py` to replace the `generate_onboarding_domain_doc` function with the following:

```python
def generate_onboarding_domain_doc(project_path: str, domain_summary: str, query_llm_fn=None, llm_provider=None, api_key=None, context_str="", boilerplate_dir: str = None):
    """Generates the ONBOARDING_DOMAIN.md template using LLM profiling and verified tools."""
    doc_path = os.path.join(project_path, "ONBOARDING_DOMAIN.md")
    
    # 1. Detect Tech Stack
    tech_stack = detect_tech_stack(project_path)
    
    # 2. Load Tools Registry
    tools_registry = {}
    if boilerplate_dir:
        registry_path = os.path.join(boilerplate_dir, "onboarding", "tools.json")
        if os.path.exists(registry_path):
            try:
                import json
                with open(registry_path, "r") as f:
                    tools_registry = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load tools registry: {e}")

    # 3. Profile SME via LLM
    sme_name = "domain-sme"
    invariants = "1. [USER INPUT REQUIRED: Add your own unbreakable rule here]\n"
    glossary = "*   **[Term 1]**: [USER INPUT REQUIRED: Define this term]\n"
    recommended_skills = []
    recommended_mcps = []

    if query_llm_fn and llm_provider and api_key:
        prompt = f"""
        You are an Architect and Domain Modeler. Based on the following project context, you must define a 'Domain SME' agent to protect the core logic.
        
        Project Context:
        {context_str[:4000]}
        
        Available Verified Tools:
        {json.dumps(tools_registry)}
        
        Task:
        1. Propose a specific name for the Domain SME (e.g., 'billing-guardian', 'auth-sme').
        2. Propose 3-5 strict Domain Invariants (absolute rules it must enforce).
        3. Define 3-5 terms for the Ubiquitous Language.
        4. Select up to 3 relevant skills from the 'Available Verified Tools'. Return EXACTLY the JSON object for the tool.
        5. Select up to 2 relevant MCPs from the 'Available Verified Tools'. Return EXACTLY the JSON object for the tool.
        
        Return ONLY valid JSON in this format:
        {{
            "sme_name": "...",
            "invariants": ["...", "..."],
            "glossary": {{"term": "definition"}},
            "skills": [{{"name": "...", "url": "..."}}],
            "mcps": [{{"name": "...", "command": "...", "type": "mcp"}}]
        }}
        """
        try:
            res = query_llm_fn(prompt, llm_provider, api_key)
            import json
            cleaned = res.replace("```json", "").replace("```", "").strip()
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                cleaned = cleaned[start_idx:end_idx]
            data = json.loads(cleaned)
            
            if data.get("sme_name"): sme_name = data["sme_name"]
            if data.get("invariants"):
                invariants = "\n".join([f"{i+1}. {inv}" for i, inv in enumerate(data["invariants"])])
            if data.get("glossary"):
                glossary = "\n".join([f"*   **{k}**: {v}" for k, v in data["glossary"].items()])
            if data.get("skills"): recommended_skills = data["skills"]
            if data.get("mcps"): recommended_mcps = data["mcps"]
        except Exception as e:
            print(f"Warning: SME Profiling failed: {e}")

    # 4. Format Tools
    skills_md = "- [ ] No skills recommended"
    if recommended_skills:
        skills_md = "\n".join([f"- [x] {s['name']} ({s['url']})" for s in recommended_skills])
        
    mcps_md = "- [ ] No MCPs recommended"
    if recommended_mcps:
        mcps_md = "\n".join([f"- [x] {m['name']} ({m.get('command', '')})" for m in recommended_mcps])

    # 5. Populate Template
    template_str = ""
    if boilerplate_dir:
        template_path = os.path.join(boilerplate_dir, "onboarding", "ONBOARDING_DOMAIN.md.template")
        if os.path.exists(template_path):
            with open(template_path, "r") as f:
                 template_str = f.read()
    
    # Fallback if template missing
    if not template_str:
         template_str = "# Project Onboarding Domain\n\n**Detected Tech Stack:** {{TECH_STACK}}\n\nBased on the codebase scan, I have identified **{{DOMAIN_SUMMARY}}** as a core complex domain. I propose creating a dedicated agent to protect this logic.\n\n## Proposed Domain SME Agent\n\n**Proposed Agent Name:** `@{{SME_NAME}}`\n*(Edit the name above if incorrect. Must be lowercase.)*\n\n**Domain Invariants (The absolute rules this agent must enforce):**\n{{INVARIANTS}}\n\n**Ubiquitous Language (Key terms to define):**\n{{GLOSSARY}}\n\n## Proposed Skills\n*(Delete the line of any skill you do NOT want installed)*\n{{SKILLS_MD}}\n\n## Proposed MCP Tools\n*(Delete the line of any MCP you do NOT want installed)*\n{{MCPS_MD}}\n\n*(When you have finished editing this file, return to the terminal and press ENTER to continue minting)*\n"

    final_content = template_str.replace("{{TECH_STACK}}", tech_stack)
    final_content = final_content.replace("{{DOMAIN_SUMMARY}}", domain_summary)
    final_content = final_content.replace("{{SME_NAME}}", sme_name.lower())
    final_content = final_content.replace("{{INVARIANTS}}", invariants)
    final_content = final_content.replace("{{GLOSSARY}}", glossary)
    final_content = final_content.replace("{{SKILLS_MD}}", skills_md)
    final_content = final_content.replace("{{MCPS_MD}}", mcps_md)

    with open(doc_path, "w") as f:
        f.write(final_content)
    print(f"\n[HARNESS] Generated ONBOARDING_DOMAIN.md at {doc_path}")
```

- [ ] **Step 2: Commit**

```bash
git add harness/discovery_engine.py
git commit -m "feat(onboarding): update discovery engine to use template and registry"
```

### Task 3: Update `cli.py` to pass `boilerplate_dir` to `generate_onboarding_domain_doc`

**Files:**
- Modify: `harness/cli.py`

- [ ] **Step 1: Update the function call in `cli.py`**

In `harness/cli.py`, locate the call to `generate_onboarding_domain_doc` (around line 265). It needs to pass `boilerplate_dir` as the final argument.

```python
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
```

- [ ] **Step 2: Remove old Agent Loop**

In `harness/cli.py`, remove the `discover_agents` loop (around lines 192-233) that asks the user to include recommended agents and create custom agents. The entire block starting with `print("Discovering specialized agents...")` and ending before `print("\n=== Platform Selection ===")` should be deleted. 

We now only mint the boilerplate agents + the SME. Therefore, we should set `selected_agents = []` so `mint_workspace` doesn't try to mint hallucinated agents.

Replace that block with just:

```python
        selected_agents = []
```

- [ ] **Step 3: Commit**

```bash
git add harness/cli.py
git commit -m "refactor(onboarding): pass boilerplate dir to discovery and remove old agent loop"
```

### Task 4: Fix SME Synthesis Regex in `minting_engine.py`

**Files:**
- Modify: `harness/minting_engine.py`

- [ ] **Step 1: Fix regex in `synthesize_domain_sme_agent`**

In `harness/minting_engine.py` around line 620, the regex capturing invariants and glossary relies on the exact markdown formatting `**Domain Invariants` which might get mangled.

Update the `synthesize_domain_sme_agent` function to use a more robust split-based extraction:

```python
def synthesize_domain_sme_agent(target_dir: str, domain_content: str, harness_folder_name: str):
    """Generates the domain SME agent deterministically based on the filled doc."""
    if not domain_content:
        return None

    # Extract proposed name, fallback to domain-sme
    agent_name = "domain-sme"
    name_match = re.search(r'Proposed Agent Name:\s*`?@([a-zA-Z0-9_-]+)`?', domain_content)
    if name_match:
        agent_name = name_match.group(1).lower()
        
    # Extract sections using split
    invariants = "None provided."
    glossary = "None provided."
    
    parts = domain_content.split("Domain Invariants")
    if len(parts) > 1:
        after_invariants = parts[1]
        invariants_parts = after_invariants.split("Ubiquitous Language")
        if len(invariants_parts) > 1:
             invariants = invariants_parts[0].replace("(The absolute rules this agent must enforce):", "").replace("**:**", "").strip()
             glossary_parts = invariants_parts[1].split("## Proposed Skills")
             if len(glossary_parts) > 1:
                 glossary = glossary_parts[0].replace("(Key terms to define):", "").replace("**:**", "").strip()
             else:
                 glossary = invariants_parts[1].replace("(Key terms to define):", "").replace("**:**", "").strip()
        else:
             invariants = invariants_parts[0].replace("(The absolute rules this agent must enforce):", "").replace("**:**", "").strip()
             

    agent_markdown = f"""---
name: {agent_name}
description: Subject Matter Expert and Guardian. Consult this agent before modifying core logic.
type: architect_variant
---
# Role: Domain Subject Matter Expert
You are the definitive authority on the business logic, ubiquitous language, and architectural constraints.

# Core Mandates
1. **Security & System Integrity:** Never log, print, or commit secrets.
2. **Context Efficiency:** Your context window is isolated.
3. **No Chitchat:** Focus exclusively on intent and technical rationale.

# Domain-Specific Invariants (The MOAT)
<invariants>
{invariants}
</invariants>

# Ubiquitous Language (Glossary)
<glossary>
{glossary}
</glossary>

# Operational Instructions
1. **Audit:** Review proposed plans against your <invariants>. 
2. **Correct:** Identify any misuse of terms.
3. **Reject:** Reject plans that violate domain rules. Provide architectural corrections, NOT implementation code.
"""

    try:
        agents_dir = os.path.join(target_dir, harness_folder_name, "agents")
        os.makedirs(agents_dir, exist_ok=True)
        
        file_path = os.path.join(agents_dir, f"{agent_name}.md")
        with open(file_path, "w") as f:
            f.write(agent_markdown.strip() + "\n")
            
        print(f"[HARNESS] Synthesized {agent_name} at {file_path}")
        return agent_name
        
    except Exception as e:
        print(f"Error synthesizing domain agent: {e}")
        return None
```

- [ ] **Step 2: Commit**

```bash
git add harness/minting_engine.py
git commit -m "fix(onboarding): make SME synthesis extraction more robust"
```
