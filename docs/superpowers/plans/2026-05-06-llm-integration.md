# Real LLM Integration & DDD Alignment Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Replace LLM stubs with real API calls, fetch required skills remotely during init, and ensure DDD alignment works with the true project context.

**Architecture:** 
1. `discovery_engine.py` will fetch `SKILL.md` from `mattpocock/skills` repository over HTTP. It will fail hard if the network request fails.
2. A unified `query_llm` function will dispatch to OpenAI, Anthropic, or Gemini APIs using standard libraries/REST to avoid heavy SDK bloat.
3. `cli.py` will acquire the MCP context *once* and pass it to both the Agent Discovery and DDD Alignment phases.
4. `minting_engine.py` will save the DDD artifacts to the `.agents/ddd/` (or `.gemini/ddd/`) directory and add the `mattpocock/skills` install command to the setup script.

---

### Task 1: Remote Skill Fetching & Unified LLM Client

**Files:**
- Modify: `harness/discovery_engine.py`

- [ ] **Step 1: Implement unified LLM client and remote fetcher**

Replace the `query_llm` stub and add the fetcher:

```python
import json
import subprocess
import urllib.request
import os

def fetch_remote_skill(skill_url: str) -> str:
    """Fetches a skill definition from a raw GitHub URL."""
    try:
        req = urllib.request.Request(skill_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to fetch required skill from {skill_url}")
        print(f"Details: {e}")
        import sys
        sys.exit(1) # Fail hard as requested

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
        use_model = model or "gemini-2.5-flash"
        response = client.models.generate_content(
            model=use_model,
            contents=prompt
        )
        return response.text
        
    raise ValueError(f"Unsupported LLM provider: {llm_provider}")
```

- [ ] **Step 2: Update discovery functions to accept context**

```python
def discover_agents(context_str: str, feature_fetcher_yaml_path: str, llm_provider: str, api_key: str, model: str = None) -> list[dict]:
    """Loads the system prompt and queries the LLM."""
    system_prompt = "You are the Feature Fetcher."
    try:
        import yaml
        with open(feature_fetcher_yaml_path, 'r') as f:
            config = yaml.safe_load(f)
            if "system_prompt" in config:
                system_prompt = config["system_prompt"]
    except Exception as e:
        print(f"Warning: Could not load feature-fetcher prompt: {e}")

    full_prompt = f"{system_prompt}\n\nPROJECT CONTEXT:\n{context_str}\n\nBased on the mandate above, output the required JSON."
    
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
    """Extracts DDD context using remote skills."""
    print("Fetching remote skills for DDD alignment...")
    grill_me_skill = fetch_remote_skill("https://raw.githubusercontent.com/mattpocock/skills/main/skills/productivity/grill-me/SKILL.md")
    grill_with_docs_skill = fetch_remote_skill("https://raw.githubusercontent.com/mattpocock/skills/main/skills/engineering/grill-with-docs.md")
    
    prompt = (
        "You are a strict Domain-Driven Design architect. Analyze the following project context and execute the provided skills.\n\n"
        "=== GRILL-WITH-DOCS SKILL ===\n"
        f"{grill_with_docs_skill}\n\n"
        "=== GRILL-ME SKILL ===\n"
        f"{grill_me_skill}\n\n"
        "Your task:\n"
        "1. Draft a context definition (context.md style) based on the codebase.\n"
        "2. Identify ambiguities or missing domain definitions.\n"
        "3. Use the 'grill-me' approach to generate 3-5 sharp, critical questions to align the user on these ambiguities.\n\n"
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
```

- [ ] **Step 3: Commit discovery changes**

```bash
git add harness/discovery_engine.py
git commit -m "feat(llm): implement real API clients and remote skill fetching for DDD"
```

---

### Task 2: Fix Orchestration Context Flow

**Files:**
- Modify: `harness/cli.py`

- [ ] **Step 1: Fetch context once and pass it to both discovery functions**

```python
        print("Stage 2: Dynamic Context Acquisition")
        from harness.discovery_engine import discover_agents, discover_ddd_context, acquire_mcp_context
        
        # Acquire context once
        context_str = acquire_mcp_context(args.project_path)
        
        print("Discovering specialized agents...")
        recommended_agents = discover_agents(context_str, feature_fetcher_yaml, args.llm, api_key, args.model)
        
        print(f"Found {len(recommended_agents)} recommendations.")
        selected_agents = []
        # ... (keep existing print and selection loop) ...
                
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
```

- [ ] **Step 2: Commit CLI refactor**

```bash
git add harness/cli.py
git commit -m "refactor(cli): pass mcp context correctly to discovery phases"
```

---

### Task 3: Update Setup Script for Matt Pocock Skills

**Files:**
- Modify: `harness/minting_engine.py`

- [ ] **Step 1: Add mattpocock/skills to the generated installation block**

In `minting_engine.py`, update the `setup_content` blocks to install both skill repositories:

For Gemini:
```python
    if platform_choice == "1": # Gemini
        setup_content += """
echo "Installing Superpowers and Skills for Gemini CLI..."
if command -v gemini &> /dev/null; then
    gemini extensions install https://github.com/obra/superpowers || true
    gemini extensions install https://github.com/mattpocock/skills || true
else
    echo "Warning: gemini command not found."
fi
"""
```

For Claude:
```python
    elif platform_choice == "2": # Claude
        setup_content += """
echo "To install Superpowers and Skills for Claude Code, run these commands inside the Claude Code interface:"
echo "  /plugin install superpowers@claude-plugins-official"
echo "  /plugin install skills@mattpocock"
"""
```

For Copilot:
```python
    elif platform_choice == "3": # Copilot
        setup_content += """
echo "Installing Superpowers and Skills for Copilot CLI..."
if command -v copilot &> /dev/null; then
    copilot plugin marketplace add obra/superpowers-marketplace || true
    copilot plugin install superpowers@superpowers-marketplace || true
    copilot plugin marketplace add mattpocock/skills-marketplace || true
    copilot plugin install skills@skills-marketplace || true
else
    echo "Warning: copilot command not found."
fi
"""
```

For Cursor:
```python
    elif platform_choice == "4": # Cursor
        setup_content += """
echo "To install Superpowers and Skills for Cursor, run these commands inside the Cursor Agent chat:"
echo "  /add-plugin superpowers"
echo "  /add-plugin mattpocock/skills"
"""
```

- [ ] **Step 2: Commit minting engine changes**

```bash
git add harness/minting_engine.py
git commit -m "feat(setup): add mattpocock skills repo to generated setup script"
```