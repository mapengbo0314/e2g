---
name: design-as-code
description: High-rigor, text-only architectural design workflow. Supplements standard planning by enforcing strict "No Code" phases, indxr-based context loading, iterative doc generation, and Goldfish subagent validation.
---

# Design as the New Code Workflow

This skill supplements the standard `brainstorming` and planning workflows by providing a highly rigorous, text-only architectural design pipeline. It completely bypasses visual tools and UI companions, focusing on deep technical planning, iterative markdown generation, and strict context isolation using subagents. 

Use this skill when tackling complex architectural changes, backend services, or when the user explicitly requests a highly critical design partner.

## Rules & Invariants
- **NO CODE GENERATION:** During phases 1-3, you are strictly forbidden from writing functional code. Write prose, pseudocode, or mermaid diagrams only.
- **NO VISUALS:** Do not offer the visual companion or UI mockups.
- **ONE SECTION AT A TIME:** When drafting the design doc, ask for approval after EVERY section before moving to the next.

## The Workflow

You must guide the user through the following state machine sequentially:

### Phase 1: Context Loading & Understanding (`01_design_load_context`)
1. Use the `mcp_indxr` tools (e.g., `mcp_indxr_wiki_search`, `mcp_indxr_summarize`, `mcp_indxr_explain_symbol`, `mcp_indxr_get_dependency_graph`) to build a "peanuts and hay" mental model of the relevant feature area.
2. Write a high-level summary of your understanding of the current system and its components back to the user.
3. Wait for the user to correct your understanding before proceeding.

### Phase 2: Design Discussion (`02_design_start_discussion` to `04_design_first_proposal`)
1. Act as a critical design partner. Your highest and best use is to point out flaws, suggest alternatives, and challenge assumptions (`03_design_challenge`). Do not easily agree.
2. Ask clarifying questions one at a time.
3. Once the requirements are clear, provide a "First Draft Technical Proposal" (`04`). This must be in prose/diagrams only. NO CODE.

### Phase 3: Iterative Document Generation (`05_design_doc` to `08_design_doc_implementation`)
Draft the design document section-by-section. *Wait for user approval after each section.*
- **Section 1: The Problem** (`05`): Plain English description of the business/technical problem.
- **Section 2: Technical Plan** (`06`): Plain English description of big components and ecosystem fit. Minimal jargon.
- **Section 3: Alternatives Considered** (`07`): What was ruled out and why.
- **Section 4: Detailed Implementation** (`08`): Enumerate EVERY file to be changed/created and WHY. No code yet.
- *Action:* Save the compiled document to `docs/superpowers/specs/YYYY-MM-DD-<FEATURE_NAME>-design.md` using the `write_file` tool.

### Phase 4: Goldfish Protocol Validation (`09_goldfish` to `11_goldfish`)
Leverage Gemini CLI's native subagents to test the document in isolated context windows. Dispatch these using the `invoke_agent` tool (or `@agent_name` syntax).
1. **Comprehension Test** (`09`): Dispatch `@generalist` to read the doc and explain the system back.
2. **Critic Review** (`10`): Dispatch `@adversary` (or `@reviewer`) to tear the design doc apart and find missing edge cases or faulty assumptions.
3. **Implementation Readiness** (`11`): Dispatch `@verifier` to confirm if the document has *absolutely all* the information required to successfully implement the feature in the first pass without asking clarifying questions.

### Phase 5: Implementation & Mean Review (`12_impl` to `13_mean_review`)
1. **Implementation** (`12`): Dispatch `@implementer` with the finalized design doc. Instruct it: "Implement exactly as described. Follow the plan and file change list precisely."
2. **Mean Code Review** (`13`): Dispatch `@reviewer` to heavily critique the implemented code. Instruct it to "tear it to shreds," flag any 10+ lines of code missing comments, and enforce extreme readability standards.

---

## Drift Detect All (Utility Workflow)
If the user requests `drift_detect_all` or a drift report:
1. Identify all files in `docs/superpowers/specs/` (or the requested documentation directory).
2. For each doc, dispatch a subagent (e.g., `@generalist` or `@architect`) to `grep` or read the referenced source files.
3. Compare design vs. reality. Look for:
   - Missing Features
   - Incomplete Models/Schemas
   - Logic Shortcuts (e.g., hardcoded values vs. dynamic logic)
   - Architectural Divergence
4. Compile an `Implementation Drift Report` showing ONLY the differences.
5. Save it to `artifacts/_DRIFT_REPORT.md`.