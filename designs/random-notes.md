
Product Requirements Document (PRD): Glimpse
1. Product Overview & Purpose
Glimpse (Generative Language Interface for Massive Project Source Exploration) is an AI-powered platform designed to construct hierarchical "mental models" of massive codebases (like google3). Large Language Models (LLMs) inherently struggle with multi-million line codebases due to context window constraints. Glimpse solves this by intelligently partitioning, researching, and summarizing the repository into a structured architectural map, providing highly accurate, grounded context for downstream agentic tasks, developer Q&A, and IDE auto-completion.
2. Target Audience
Software Engineers: Developers looking to understand complex, undocumented, or unfamiliar code boundaries via the Web UI or CLI.
AI Agents & Workbenches: Autonomous systems (like Bug Agents, Code Reviewers, or the Deep Thinker agent) that need API-level access to codebase intelligence.
IDE Integrations: Developers using Cider or the Gemini CLI who consume Glimpse's mental model via the Model Context Protocol (MCP).
3. Core Capabilities & Features
Multi-Epoch Contextualization: Summarizes code bottom-up. Epoch 0 creates isolated local summaries. Epoch 1+ uses a global "Root Map" to rewrite summaries so they reflect cross-directory architectural dependencies.
Intelligent WorkUnit Aggregation: Uses a Union-Find algorithm to cluster small directories into optimized WorkUnit blocks, preventing massive LLM token overhead while staying within context limits.
Distributed Continuous Indexing: Automatically synchronizes with Piper/Git activity. A Controller-Worker architecture orchestrates task shards in Cloud Spanner to ensure exactly-once processing.
Agentic Q&A (Index Expert): A "Research Team" workflow (Director + parallel Researchers) that queries CodeSearch, Kythe, and Moma to synthesize deep, heavily grounded technical answers.
Strict Security & Silo Awareness: Integrates deeply with srcprotect to enforce read permissions at the RPC Gateway level, and respects OWNERS_METADATA during the indexing planning phase.
4. System Constraints
Bundle Size Limits: Configurations (ProjectBundles) are strictly limited to < 10 Million Lines of Code (LoC) per bundle.
File Size Limits: Files larger than 1 MiB are excluded from the index.
Latency & Throttling: Respects Gemini/Vertex AI burst limits via token-bucket rate limiting (estimating 3 characters per token) to prevent global quota exhaustion.

Exact System Architecture & Data Flow
Glimpse operates in two primary lifecycle phases: Phase 1: Index Generation (generate_bundle pipeline) and Phase 2: Codebase Expert Reasoning (User UI/MCP to Deep Research).
Architecture Diagram: Overall System

Initiation (controller.py / generate_bundle.py): The system queries F1 metadata (codesize_prod.dir_summaries) to gather precise line-of-code counts for the target depot path.
Planning & Aggregation (Planner):
A bottom-up traversal (tree_sizer.py) maps the codebase.
A Union-Find algorithm greedily clusters small leaf directories into their parent directories. Merging continues until the unit reaches max_work_unit_size_bytes (default 500KB).
Files > 1MiB and directories violating OWNERS_METADATA silos are excluded.
This outputs an IndexPlan (WorkUnits).
Queueing & Sharding (shard_storage.py): If a directory is too massive (e.g., >10M LoC), it is split into "Direct Files" shards and "Subtree" shards. Tasks are queued into the G3WorkShards Spanner table. A rule ensures a parent's summary cannot be generated until all child shards are COMPLETED.
Execution (Orchestrator & LlmIndexer): Workers claim shards transactionally. For each WorkUnit, sequential_llm_prompter.py initiates a simulated 5-stage human research process using Gemini:
CodeSearch Planning: Agent runs RE2 regex queries to find external implementations.
File Reading: Identifies and reads critical config/base files.
Key Component Analysis: Analyzes internal interfaces.
Deep Dive: Focuses on architectural motivations.
Synthesis: Unifies data into a markdown summary.
Multi-Epoch Pass: Epoch 0 builds local summaries. Epoch 1+ passes the global "Root Map" (an aggregate of all Epoch 0 overviews) back to the LLM, rewriting local summaries to reflect cross-directory dependencies.

Detailed Data Flow 2: Answering Deep Research Questions
This flow describes how a user leverages the UI to trigger the Agentic Reasoning Engine (index_expert).
User Invocation: A user asks a question via the Angular Web UI, the glimpse CLI, or an IDE extension connected via the Model Context Protocol (mcp/ directory).
RPC Gateway & Security (glimpse_gateway.py): The request hits the GlimpseGateway. Before any indexed data is returned, an embedded srcprotect check validates the user's MDB (identity) credentials against the requested //depot/ Piper paths to guarantee they have read access.
Agent Orchestration (ExpertAgentWorkflow): The question is passed to the reasoning engine (agent.py). Internal links (Docs, critique CLs) are automatically expanded into text context.
Collaborative Multi-Agent Research (research_team_flow.py):
The Director: Analyzes the prompt and breaks it into high-level ResearchTopics.
The Researchers: Parallel workers spin up to gather data.
knowledge_base_researcher writes ZetaSQL queries against Kythe graph data in Spanner for structural relationships.
codesearch_researcher runs textual queries.
file_read_researcher pulls exact source code via SrcFS or GitFS.
Trimming & Merging (Context Optimization):
Trimming Agent: Because raw search output is huge, a specialized LLM call identifies and extracts only the relevant line ranges from the raw retrieval data.
Snippet Merging: Inside SharedResearchState, a thread-safe union-interval algorithm merges overlapping/adjacent line ranges (e.g., lines 1-5 and 4-10 become 1-10) into contiguous blocks.
Final Synthesis & Review: Once the Director concludes enough context has been gathered, the LLM initiates a two-step answer sequence: generating an outline/skeleton first, then filling in technical details. A background reviewer agent (if configured) double-checks for hallucinations purely against the retrieved context before streaming the markdown response back to the UI.

A. The Programmatic RPC Gateway
To interact with Glimpse's pre-computed "mental models" over a network without spinning up heavy LLM agents, you connect to the GlimpseGateway.
Protobuf Interface: Located in gateway/proto/glimpse_gateway.proto, it exposes RPCs like GetDirectorySummary, GetRootSummary, and GetDynamicRootSummary.
GatewayState Abstraction: Glimpse decouples storage backends via the State protocol. Your harness can initialize GatewayState(bundle_name, server_address). This object makes the remote Spanner database feel like a local, read-only file system. When your harness calls state.read_summary(), it transparently translates the call into a Stubby RPC to the Gateway.
Security Propagation (SrcProtect): You don't need to manually pass permissions. The glimpse_gateway_client determines your environment (pyborgletinfo.RunningUnderBorglet()) and propagates the caller's context (rpc_authority.FromContext()). On the server side, Glimpse extracts the caller's MDB identity and passes it through a srcprotect wrapper to verify they have Piper read permissions for the requested //depot/ path before returning data.


The accuracy of Glimpse bundles—and the agents that rely on them to understand massive codebases—is understood and assured through a sophisticated, multi-layered evaluation and validation ecosystem. 

This system guarantees accuracy through four primary mechanisms: **Rubric-Based Expert Evaluations**, **"Haystack" Retrieval Benchmarks**, **Pre-computation Bundle Validation**, and **Semantic Integration Testing**.

### 1. Rubric-Based Expert Evaluations (`evals/expert`)
To understand how accurately the Index Expert agent reasons over a bundle, Glimpse uses a structured, LLM-driven evaluation framework that moves beyond simple string matching. 
* **Demerit-Based Scoring:** Instead of just comparing to a "golden answer," an evaluator agent assesses the generated response against a specific benchmark rubric (categorized into tiers like Focused, Detailed, and Comprehensive). It issues demerits for **Omissions** (missing facts), **Inaccuracies** (incorrect facts), and **Formatting** issues.
* **Strict Hallucination Checking:** To assure that the agent isn't just relying on its internal LLM weights, a dedicated `hallucination_agent` performs a strict factual verification. It compares the agent's final answer *exclusively* against the `research_context` (the raw source information the agent gathered during its execution). Any claim not explicitly supported by this localized context is flagged as a major hallucination demerit.
* **Automated Semantic Similarity:** The framework calculates BERT scores (Precision, Recall, and F1) to provide an automated, mathematical measure of how well the agent's response semantically aligns with the required rubric criteria.

### 2. "Needle in a Haystack" Benchmarks (`evals/haystack`)
Glimpse assures that its hierarchical indexing strategy actually works for deep retrieval by using a specialized "Haystack" evaluation suite.
* **Conceptual File Retrieval:** This framework quantitatively measures an agent's ability to locate the exact file implementing a specific functionality. An automated generator creates unambiguous, conceptual questions about a file's purpose (e.g., "Where is the functionality for aggregating various signals implemented?").
* **Strict Success Criteria:** The evaluation uses a strict suffix-matching rule. The agent's final response must end *exactly* with the expected relative file path to pass.
* **Index-Augmented Baseline Comparisons:** The accuracy of Glimpse bundles is proven by comparing baseline agents (using raw code search) against "index-augmented" agents (which are primed with the bundle's `root_map_v1.md` and a tool to fetch directory summaries). This proves how much the pre-computed directory metadata reduces the search space and improves retrieval reliability.

### 3. Build-Time Bundle Validation (`build_defs` & `scripts/bundle_verifier.py`)
Accuracy degrades if an LLM is overwhelmed by too much context. Glimpse assures the operational integrity and boundaries of a bundle before it is ever indexed.
* **Resource Governance (LOC Limits):** A dedicated `bundle_verifier.py` library intercepts bundle configurations during the Guitar presubmit phase (`config_size_presubmit_test.py`). It performs a live SQL query against the `zahlen` codesize database (hosted in F1) to estimate the total Lines of Code (LOC) covered by the bundle. By enforcing a standard 10-million-LOC limit, it prevents indexing bloat and ensures the resulting summaries remain focused and within the model's context window constraints.
* **Structural Checks:** It also enforces structural validity, checking for proper regex inclusions/exclusions, ensuring that custom prompts/guidance do not exceed character limits, and preventing overlapping configurations.

### 4. End-to-End Integration Testing (`integration_tests`)
Glimpse utilizes non-hermetic integration tests (e.g., `glimpse_integration_test.py`) that integrate with actual persistent storage, Piper, and Vertex AI. 
* **Semantic Verification:** These tests actually generate bundles on the fly and prompt the Expert Agent to answer specific questions (e.g., "What is the magic word in glimpse_integration_test_file.md?"). The tests assert that the agent can successfully retrieve specific architectural details and correct answers from the generated hierarchical summaries, ensuring the mental model is fundamentally sound.
* **Structural Verification:** The tests also guarantee that features like "sparse tree" aggregation (combining small directories) and chunking of massive flat directories are reliably producing the required Markdown indices and `work_units.json` manifests.




