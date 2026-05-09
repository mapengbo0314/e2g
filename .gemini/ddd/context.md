# E2G Agentic Harness - Core Domain Context

## Glossary

*   **Harness**: The overarching stateless utility system responsible for bootstrapping and analyzing codebases.
*   **Workspace**: A generated, project-specific environment created by the Minting Engine. *Ambiguity: Is this just a file directory artifact, or a runtime entity?*
*   **Agent**: An actor in the system, exclusively defined by a standalone Markdown document (e.g., `architect.md`). It encapsulates instructions and mandates but lacks native executable code.
*   **Skill**: An atomic, executable capability (e.g., `grill-me.md`) that an Agent can utilize. Can be local to the boilerplate or fetched dynamically (`fetch_remote_skill`).
*   **Discovery Engine**: The sub-domain responsible for analyzing external codebases to recommend Agent configurations and extract domain intelligence.
*   **Minting Engine**: The sub-domain responsible for projecting Discovery outputs and Boilerplate Templates into a concrete Workspace.
*   **Boilerplate Template**: The immutable source truth (`boilerplate-agent/`) used as the structural foundation during Minting.
*   **Context (WARNING: Overloaded)**: Currently used interchangeably to mean Domain-Driven Design context (`discover_ddd_context`), LLM context windows, and Model Context Protocol state (`acquire_mcp_context`).

## Key Relationships
*   A **Harness** uses a **Discovery Engine** to analyze a codebase.
*   A **Minting Engine** uses outputs from Discovery and a **Boilerplate Template** to generate a **Workspace**.
*   A **Workspace** contains **Agents** (Markdown) and centralized Orchestration Rules.
*   **Agents** invoke **Skills** during execution phases.