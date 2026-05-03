# Product Requirements Document (PRD): Recursive-Index

## 1. Product Overview & Purpose
Recursive-Index (Generative Language Interface for Massive Project Source Exploration) is an AI-powered platform designed to construct hierarchical "mental models" of massive codebases. Large Language Models (LLMs) inherently struggle with multi-million line codebases due to context window constraints. Recursive-Index solves this by intelligently partitioning, researching, and summarizing the repository into a structured architectural map, providing highly accurate, grounded context for downstream agentic tasks, developer Q&A, and IDE integration.

## 2. Target Audience
- **Software Engineers**: Developers looking to understand complex, undocumented, or unfamiliar code boundaries via a Web UI or CLI.
- **AI Agents & Workbenches**: Autonomous systems (like Bug Agents or Code Reviewers) that need API-level access to codebase intelligence.
- **IDE Integrations**: Developers using modern IDEs or CLI tools who consume the mental model via the Model Context Protocol (MCP).

## 3. Core Capabilities & Features
- **Multi-Epoch Contextualization**: Summarizes code bottom-up. Initial passes create isolated local summaries, while subsequent passes use a global "Root Map" to rewrite summaries so they reflect cross-directory architectural dependencies.
- **Intelligent WorkUnit Aggregation**: Clusters small directories into optimized WorkUnit blocks, preventing massive LLM token overhead while staying within context limits.
- **Distributed Continuous Indexing**: Automatically synchronizes with repository activity. A Controller-Worker architecture orchestrates task shards in a distributed database to ensure reliable processing.
- **Agentic Q&A (Index Expert)**: A "Research Team" workflow (Director + parallel Researchers) that queries search engines and structural metadata to synthesize deep, heavily grounded technical answers.
- **Security & Access Control**: Integrates with existing access control systems to enforce read permissions at the API level.

## 4. System Architecture & Data Flow
Recursive-Index operates in two primary lifecycle phases: **Index Generation** and **Codebase Expert Reasoning**.

### Phase 1: Index Generation
1.  **Initiation**: The system gathers line-of-code counts for the target paths.
2.  **Planning & Aggregation (Planner)**:
    - A bottom-up traversal maps the codebase.
    - Small leaf directories are greedily clustered into their parent directories to optimize LLM usage.
    - Large files and restricted directories are handled according to configuration.
    - This outputs an **IndexPlan** (WorkUnits).
3.  **Queueing & Sharding**: Tasks are queued and sharded. A parent's summary cannot be generated until all child shards are completed.
4.  **Execution (Orchestrator & LlmIndexer)**: Workers claim shards. For each WorkUnit, a simulated 5-stage research process is initiated:
    - **Planning**: Generates queries to find external implementations.
    - **File Reading**: Identifies and reads critical configuration files.
    - **Component Analysis**: Analyzes internal interfaces.
    - **Deep Dive**: Focuses on architectural motivations.
    - **Synthesis**: Unifies data into a markdown summary.
5.  **Multi-Epoch Pass**: Refines summaries to reflect cross-directory dependencies.

### Phase 2: Codebase Expert Reasoning
1.  **User Invocation**: A user asks a question via a Web UI, CLI, or IDE extension (MCP).
2.  **API Gateway & Security**: Validates user credentials and access rights.
3.  **Agent Orchestration**: The question is passed to the reasoning engine. Internal links are automatically expanded into text context.
4.  **Collaborative Multi-Agent Research**:
    - **The Director**: Analyzes the prompt and breaks it into ResearchTopics.
    - **The Researchers**: Parallel workers gather data from search, structural metadata, and source code.
5.  **Context Optimization**:
    - **Trimming Agent**: Identifies and extracts only the relevant line ranges from retrieval data.
    - **Snippet Merging**: Merges overlapping or adjacent line ranges into contiguous blocks.
6.  **Final Synthesis & Review**: Generates a detailed technical answer and double-checks for hallucinations against retrieved context.

## 5. Accuracy & Validation
The system guarantees accuracy through four primary mechanisms:
- **Rubric-Based Expert Evaluations**: LLM-driven assessment against specific technical rubrics.
- **"Haystack" Retrieval Benchmarks**: Measures the ability to locate specific implementation details in a massive search space.
- **Pre-computation Validation**: Enforces resource limits and structural validity before indexing.
- **End-to-End Integration Testing**: Verifies the entire pipeline against known architectural patterns and ground truth.
