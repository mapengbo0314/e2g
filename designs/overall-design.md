
Really repo specific, or a bunch of microservices is that fine?
—--------------
Based on the provided documentation (go/Recursive-Index), here are the key features of Recursive-Index and examples of their usage:
Codebase Indexing & Summarization:
Feature: Recursive-Index's core capability is to process a configured codebase (a "bundle") and create a hierarchical index of LLM-generated Markdown summaries. This index represents a "Mental Model" of the codebase.
Usage: This is mostly an automated backend process configured via bundle files in monorepo/coresystems/data/excellence/applications/indexing/config/.
Web UI for Q&A (go/Recursive-Index-ui):
Feature: An interactive web interface to ask natural language questions about an indexed codebase.
Usage:Navigate to go/Recursive-Index-ui.
Select the desired bundle (e.g., gmscore_cli, alloydb) from the dropdown.
Type a question in the input box, e.g., "How does the authentication module handle token renewal?" or "What are the main dependencies of the FooBar service?"
Recursive-Index will perform "deep research" using the index and provide a synthesized answer.
Specific bundle UI: go/Recursive-Index-ui/<YOUR_BUNDLE> (e.g., go/Recursive-Index-ui/alloydb).
Recursive-Index CLI (ask_Recursive-Index.sh):
Feature: A command-line tool for interactive Q&A sessions with Recursive-Index.
Setup: alias Recursive-Index='coresystems/data/excellence/applications/indexing/index_expert/ask_Recursive-Index.sh'
Usage:
BASH
# Basic query
Recursive-Index --bundle_names=my_bundle# Inside the CLI, ask questions:
> How is data cached in this system?
Adding Extra Context (CLI):
Feature: The CLI allows providing additional context like design docs, CLs, or local files to the agent using the --extra_context flag.
Usage:
BASH
Recursive-Index --bundle_names=my_bundle \
--extra_context=go/my-design-doc \
--extra_context=cl/123456789 \
--extra_context=./local_notes.md# Ask questions related to the bundle AND the extra context:
> Based on the design doc, what parts of the codebase need changes?
Controlling Runtime (CLI):
Feature: Adjust the time Recursive-Index spends on research using --target_runtime_seconds.
Usage:
BASH
# Allow more time for complex questions
Recursive-Index --bundle_names=my_bundle --target_runtime_seconds=120
MCP Server for Agent Integration:
Feature: Recursive-Index runs an MCP server, allowing other AI agents and tools like Jetski, Cider Agent, and Gemini CLI to query its "Index Expert" and leverage its codebase understanding.
Usage: This is configured within the respective agent/tool settings:Jetski: Install the "Recursive-Index" MCP Server from Jetski's settings.
Cider Agent: Install the "Recursive-Index MCP Server" extension in Cider.
Gemini CLI: Link the Recursive-Index extension (gemini extensions link /google/src/files/head/depot/monorepo/coresystems/data/excellence/applications/indexing/gemini_cli/).
Agents can then use tools like Recursive-Index.query_codebase_expert(question="...", bundle_names=["..."]).
Deep Codebase Understanding & Research:
Feature: When queried, Recursive-Index doesn't just return static summaries. Its "Index Expert" agent performs multi-step research, potentially reading index files, fetching live code, and calling CodeSearch to answer complex questions.
Usage: This is the core of the Q&A in the UI, CLI, and when called by other agents. Example questions:"Trace the data flow for a user login."
"What happens if the database connection fails during order processing?"
"Where is the error handling for API endpoint X implemented?"
Querying Across Multiple Bundles:
Feature: Recursive-Index can reason across more than one indexed bundle at a time.
Usage: Specify multiple bundle names in the UI or CLI.BASH
Recursive-Index --bundle_names=frontend_bundle,backend_bundle# Ask questions spanning both:
> How does the frontend authenticate with the backend API?
Bundle Onboarding & Configuration:
Feature: Flexible system for defining what code to index using .textproto files. Supports inclusion/exclusion patterns, Git repositories, and repository directories.
Usage: Create/edit files in monorepo/coresystems/data/excellence/applications/indexing/config/.
Manual Indexing / Re-indexing:
Feature: Ability to manually trigger the indexing process for a bundle.
Usage:
BASH
export GEMINI_API_KEY="<YOUR_KEY>"
blaze build //coresystems/data/excellence/applications/indexing:generate_bundles
./blaze-bin/coresystems/data/excellence/applications/indexing/generate_bundles --bundle_names="<BUNDLE_NAME>"
These features work together to provide AI agents and developers with a powerful way to understand and interact with large codebases.



Setup
Setup for customer the basic repo (find out whats the most common) for the service we are hosting
Then create bundles for them then just use the service to update the bundles



Tools available
CLI, UI, MCP, Extension




"responseMarkdown": "You are right to ask for a deeper walkthrough; the process is complex, and \"Recursive-Index\" is indeed the name of this AI codebase indexer. Let's clarify the \"deep research\" aspect and walk through the process from invocation to the generation of the index files, which includes the summaries that function as the root map.\n\n### Clarification on \"Deep Research\"\n\nThe term \"deep research\" doesn't refer to a special mode that Recursive-Index enters, but rather to the *way* the LLM is used. When  is called, it initializes a `GeminiLlmPrompter` with configuration for both a `synthesis_gemini_model` and a `research_gemini_model`. In the current code, both are set to the same model specified by `--gemini_model`.\n\nThe distinction lies in the *type of prompts* sent to the LLM:\n\n1.  **Code Analysis (Research):** This is when Recursive-Index sends file contents or code chunks to the LLM and asks it to analyze the code and produce an initial summary. This is the \"code -> summary\" step.\n2.  **Summary Synthesis (Merging):** This is when Recursive-Index has already generated summaries for several files and subdirectories within a directory, and it sends *those summaries* to the LLM, asking it to synthesize them into a single, higher-level summary for the parent directory. This is the \"summaries -> summary\" step.\n\nSo, the LLM is used for both analyzing raw code and synthesizing summaries from other summaries. Both use the same underlying Gemini model.\n\n---\n\n### Detailed Walkthrough: From Invocation to Index Generation\n\nHere is the step-by-step process of how Recursive-Index generates an index bundle (e.g., the contents of `root_map_dir`, including summaries and metadata) when you run :\n\n#### Phase 1: Initialization\n\n1.  **`main()` Starts:** The script begins execution in the  function.\n2.  **File System and Bundle Storage:** It initializes `factory.make_fs_manager()` to get an object that knows how to read files (from repository or locally) and `bundle_storage.BundleStorage` to read bundle configuration files (`*.textproto`) and determine input/output directories.\n3.  **Find Bundles:** `bundle_storage_impl.get_bundles()` reads the `.textproto` configurations for the bundles specified by `--bundle_names` (or all bundles).\n4.  **Setup Parallelism:** It creates a `ThreadPoolExecutor` to process multiple bundles in parallel, configured by `--max_parallel_bundles`.\n5.  **Create LLM Interface:** For *each* bundle, it calls `create_llm_prompter()` to create a `GeminiLlmPrompter` instance. This object is responsible for all communication with the Gemini API for that bundle and shares the `throttling_strategy` to manage API limits across bundles.\n6.  **Create State Storage:** For *each* bundle, it creates a `work_unit.FsWorkUnitStorage` instance. This object handles reading and writing metadata about the indexing job, such as `last_indexed.json`, which tracks the CL or commit SHA of the last successful run.\n7.  **Submit to Executor:** Each bundle, along with its dedicated `llm_prompter` and `work_unit_storage`, is submitted to the thread pool by calling .\n\n#### Phase 2: Per-Bundle Setup\n\n8.  **`generate_bundle()`:** This function runs in a separate thread for each bundle.\n    *   It reads the specific bundle configuration and merges it with default settings.\n    *   It determines if the bundle is repository-based (has `input` paths) or Git-based (has `git_input`).\n9.  **Git Cloning (If Applicable):** If it's a Git bundle,  is called. It uses `github_cloner.clone_repository` to clone the repository code into a temporary directory (e.g., `/tmp/mybundle_ab/myrepo`).\n10. **Call `_execute_indexing()`:**  (via  or ) calls  with the appropriate source code paths (repository paths or temporary Git paths).\n\n#### Phase 3: Core Indexing Setup ()\n\nThis is where all the main components are assembled.\n\n11. **`state.LocalState`:** An instance of `LocalState` is created. This object is crucial: it manages the reading and writing of *individual summaries* and *chunk data* to the bundle's output directory (e.g., `output_dir/summaries/path/to/file.json`, `output_dir/chunks/...`).\n12. **Change Detection:** A `repositoryChangeDetectionStrategy` or `GitChangeDetectionStrategy` is created to determine the current CL number or commit SHA.\n13. **Differ (If Re-indexing):** If `--reindex=True`, `reindexing.IndexDiffer` is created. It reads `last_indexed.json` (via `work_unit_storage`), scans the filesystem for all files matching the bundle's patterns, and compares this to the list of files indexed in the previous run. It produces a list of added, deleted, and modified files.\n14. **Component Initialization:** `Chunker`, `SummaryMerger`, `LlmIndexer`, `Planner`, and `Orchestrator` are instantiated, wiring all the dependencies together (LLM prompter, state manager, filesystem manager, etc.).\n\n#### Phase 4: The Indexing Loop (`orchestrator.run()`)\n\nThis is the heart of Recursive-Index, where summaries are generated layer by layer.\n\n15. **Orchestrator Runs:** `indexer_orchestrator.run()` is called and begins executing.\n16. **Epochs:** The orchestrator runs in loops called \"epochs\" (typically 5-10). Summaries must be generated \"bottom-up\": a directory summary can only be generated *after* all its children (files and subdirs) have been summarized. Epochs enable this:\n    *   **Epoch 1:** Summarizes all files and directories that contain *only* files.\n    *   **Epoch 2:** Summarizes directories whose children were summarized in Epoch 1.\n    *   ... and so on, until all directories up to the root are summarized.\n17. **Planning:** In each epoch, the orchestrator asks `planner_instance.get_work_units()`: \"What needs to be indexed now?\"\n    *   The `Planner` scans the source directories. It skips files/dirs that don't match `include/exclude` patterns.\n    *   It checks `index_state` to see if a file/dir already has a summary.\n    *   If `--reindex=True`, it consults the `IndexDiffer` and forces re-indexing of any files/dirs marked as changed, added, or modified.\n    *   It returns a list of files/directories ready to be indexed in this epoch.\n18. **Indexing:** The `Orchestrator` takes the list from the `Planner` and uses a thread pool (`--max_workers`) to call `indexer.index(work_unit)` for each file or directory.\n19. **Inside `indexer.index(path)`:**\n    *   **If `path` is a FILE:**\n        *   The file content is read via `fs_manager`.\n        *   If the file is large, `chunker.chunk_file()` splits it into chunks.\n        *   `llm_prompter.summarize_chunk()` is called for each chunk (Code Analysis).\n        *   `llm_prompter.summarize_file_from_chunks()` is called to synthesize chunk summaries into a file summary (Summary Synthesis).\n        *   If the file is small, `llm_prompter.summarize_file()` is called directly (Code Analysis).\n        *   The resulting summary is saved via **`index_state.save_summary(path, summary)`**, which writes it to a file like `output_dir/summaries/path/to/file.json`.\n    *   **If `path` is a DIRECTORY:**\n        *   `summary_merger.merge_summaries(path)` is called.\n        *   The merger asks `index_state.get_summary()` for all children of `path`.\n        *   **If any child summary is missing**, the merger reports failure for this directory *in this epoch*. It will be retried in the next epoch.\n        *   **If all child summaries are present**, `llm_prompter.summarize_directory(child_summaries)` is called to synthesize them into a directory summary (Summary Synthesis).\n        *   The resulting summary is saved via **`index_state.save_summary(path, summary)`**, writing it to `output_dir/summaries/path/to/directory.json`.\n\n#### Phase 5: Finalization\n\n20. **Epochs Complete:** After all epochs are finished, or no more progress can be made, the `orchestrator.run()` loop finishes.\n21. **Write Metadata:** The orchestrator calls **`work_unit_storage.write()`**, which saves the outcome of the indexing run—including the CL number or commit SHA(s) that were indexed, timestamps, and statistics—to **`output_dir/last_indexed.json`**.\n22. **Bundle Complete:** Control returns to , which prints a success message.\n\n### Output: The `root_map_v0/v1`\n\nThe output of this process is not a single file named `root_map_v0.json` or `root_map_v1.json`. Instead, the entire structure under `output_dir` constitutes the generated index, and the entry point—or \"root map\"—is the summary file corresponding to the top-level input directory or directories.\n\nFor example, if your bundle input was `monorepo/my/project`, the generated index consists of:\n\n*   `output_dir/last_indexed.json` (Metadata: indexed at CL 12345)\n*   `output_dir/summaries/my/project.json` (**This is the root map/entry point for this path**)\n*   `output_dir/summaries/my/project/sub_dir.json`\n*   `output_dir/summaries/my/project/sub_dir/file.py.json`\n*   ... and so on for all files and directories.\n\n"
      }
    }
  }
]


Phase 1: Initialization (main)
Goal: Read command-line flags, identify which bundles to process, and set up the parallel execution framework.
Implementation: The main function serves as the entry point.
Setup & Data Flow:
Flag Parsing: absl.flags are parsed. Key flags include --bundle_names, --bundle_config_dir, --bundle_output_dir, --max_parallel_bundles, --gemini_model, --reindex, and --llm_throttling_strategy.
FileSystemManager: factory.make_fs_manager() creates a manager for file operations.
BundleStorage: bundle_storage.BundleStorage(fs_manager, ...) is created. This object knows how to find bundle configurations (*.textproto files in --bundle_config_dir) and determine their input and output directories based on convention or configuration.
Bundle Discovery: bundle_storage_impl.get_bundles() reads all *.textproto files in the config directory, parses them into ProjectBundle protos, and filters them based on --bundle_names. If --unindexed_bundles_only=True, it uses bundle_storage_impl.is_bundle_indexed(b) to check for the existence of <bundle_output_dir>/last_indexed.json for each bundle, skipping those that have already been indexed.
Throttling: create_throttling_strategy() creates a single instance of SemaphoreAdapter or TokenCountThrottler based on --llm_throttling_strategy. This instance will be shared by all LLM prompters to ensure the overall rate of API calls doesn't exceed limits.
ThreadPool: A concurrent.futures.ThreadPoolExecutor is created with --max_parallel_bundles workers. This pool will run the generate_bundle function for different bundles in parallel.
Task Submission: The code iterates through the list of ProjectBundle protos to be processed. For each bundle, it:
Instantiates work_unit.FsWorkUnitStorage, telling it where to find/write last_indexed.json by calling bundle_storage_impl.get_bundle_output_dir(bundle_config).
Calls create_llm_prompter(), passing it the bundle config and the shared throttling_strategy, to create a GeminiLlmPrompter. This object encapsulates all settings for calling the Gemini API (model, retry logic, etc.) for this specific bundle.
Submits a new task to the executor: executor.submit(generate_bundle, ...), passing the bundle, fs_manager, llm_prompter, work_unit_storage, and bundle_storage_impl as arguments.
Output: The main thread waits for all futures in the ThreadPoolExecutor to complete.
Phase 2: Per-Bundle Setup (generate_bundle, _generate_..._bundle)
Goal: For a single bundle, determine its type (Git), prepare its source code for indexing, and call the core indexing logic.
Implementation: generate_bundle and its helpers _generate_github_bundle and _generate_regular_bundle. This phase runs in a worker thread from Phase 1's thread pool.
Setup & Data Flow:
Config Loading: generate_bundle receives its specific bundle, llm_prompter, etc. It loads the default indexer configuration and merges it with any overrides in bundle.indexer_config.
Type Check: It checks if bundle.HasField("git_input").
If Git: _generate_github_bundle is called.
It creates a temporary directory like /tmp/my_bundle_xy/.
It iterates through bundle.git_input.repository_input, calling github_cloner.clone_repository for each. This function likely uses git command-line tools to clone the specified repository (at a specific commit or HEAD) into the temporary directory. If there are multiple repositories, they are cloned into subdirectories within /tmp/my_bundle_xy/.
It collects the list of directories containing the cloned code (e.g., [/tmp/my_bundle_xy/repo1, /tmp/my_bundle_xy/repo2]) and the exact commit SHA that was checked out for each.
It updates the indexer config via dataclasses.replace to set input_prefix_to_strip to the temporary directory path (e.g., /tmp/my_bundle_xy/). This is critical for ensuring that summaries are stored with relative paths like repo1/src/main.c.json instead of /tmp/my_bundle_xy/repo1/src/main.c.json.
It calls _execute_indexing, passing the list of cloned repo directories as input_directories
Output: A call to _execute_indexing with fully resolved inputs.
Phase 3: Core Indexing Setup (_execute_indexing)
Goal: Instantiate and wire together all the components needed for indexing: State, Change Detection, Differ, Planner, Indexer, Merger, Chunker, and Orchestrator.
Implementation: The first part of _execute_indexing.
Setup & Data Flow:
State: state.LocalState is instantiated. It receives the output_dir for the bundle and input_prefix_to_strip. Its methods like save_summary(path, data) will automatically strip the prefix from path and write data to <output_dir>/summaries/<relative_path>.json.
Change Detection:
If Git: work_unit_storage.read() is called to get last_indexed_info.commit_identifier (SHAs from the previous run). GitChangeDetectionStrategy is instantiated with the old and new commit SHAs.
Differ: If reindex=True, reindexing.IndexDiffer(..., work_unit_storage=work_unit_storage, ...) is instantiated. It reads last_indexed.json via work_unit_storage to get the list of files processed in the last run, and it has access to fs_manager to scan the current filesystem state.
Filtering: bundle.include_pattern and bundle.exclude_pattern are passed to re.compile() and then stored in a PathFilteringConfig object.
Component Wiring:
Chunker() is created.
SummaryMerger is created, receiving the llm_prompter, index_state, fs_manager, and filtering_config.
LlmIndexer is created, receiving the llm_prompter, index_state, chunker, summary_merger, fs_manager, and filtering_config.
Planner is created, receiving fs_manager, input_directories, filtering_config, and the index_differ if it exists.
Orchestrator is created, receiving the planner, indexer, index_state, work_unit_storage, fs_manager, and change_detection_strategy.
Output: A fully configured Orchestrator instance.
Phase 4: The Indexing Loop (Orchestrator.run())
Goal: Iteratively generate summaries for all files and directories, from the leaves of the file tree up to the roots.
Implementation: This logic resides within the orchestrator.Orchestrator.run() method, called at the end of _execute_indexing.
Setup & Data Flow:
Epoch Loop: run() starts a loop: for i in range(_NUM_EPOCHS.value):.
Planning: Inside the loop, self.planner_instance.get_work_units(self.index_state) is called.
The Planner uses fs_manager.walk() to traverse directories, applying filtering_config to skip files/dirs.
For each path, it asks index_state.has_summary(path) to see if it's already done.
If reindex=True, it checks self.index_differ.is_path_changed(path).
Crucially, for a directory to be added to the work list, the Planner must check index_state.has_summary() for all its children first. If any child is missing a summary, the directory cannot be processed in this epoch.
get_work_units returns a list of paths (files or directories) that are ready to be processed now.
Indexing: The Orchestrator uses another ThreadPoolExecutor (with --max_workers) to parallelize calls to self.indexer.index(path) for each path returned by the Planner.
indexer.index(path):
If FILE: It reads file content via fs_manager.read_file(). It chunks if needed (chunker.chunk_file()), then calls llm_prompter.summarize_chunk() or llm_prompter.summarize_file(). These methods call the Gemini API, get a response, and return a summary string. The indexer then calls self.index_state.save_summary(path, summary) to persist the result to <output_dir>/summaries/path/to/file.json.
If DIRECTORY: It calls self.summary_merger.merge_summaries(path). The merger reads child summaries using self.index_state.get_summary(), and if all are available, it calls self.llm_prompter_instance.summarize_directory() with the text of all child summaries. This method calls the Gemini API to synthesize them into a directory-level summary. The indexer then calls self.index_state.save_summary(path, dir_summary) to persist it to <output_dir>/summaries/path/to/dir.json.
Check Convergence: At the end of an epoch, if no new summaries were successfully generated (i.e., get_work_units returned items but indexer.index failed for all of them, or get_work_units returned nothing), the Orchestrator breaks out of the epoch loop early.
Output: JSON summary files populated in <output_dir>/summaries/.
Phase 5: Finalization (Orchestrator.run() completion)
Goal: Record the result of the indexing run (the CL or commit SHA indexed) to metadata for future runs.
Implementation: The end of orchestrator.Orchestrator.run().
Setup & Data Flow:
After the epoch loop finishes, run() calls self.change_detection_strategy.get_commit_identifier() to get the CL number or list of commit SHAs that this index corresponds to.
It creates an IndexedState object containing this identifier and other metadata like timestamps.
It calls self.work_unit_storage.write(IndexedState(...)).
FsWorkUnitStorage.write() serializes the IndexedState object to JSON and overwrites the file <output_dir>/last_indexed.json.
Output: The file <output_dir>/last_indexed.json is created or updated.

Details

Recursive-Index

What will happen if my system sees a request of type foo?
I'm encountering this unexplained bug: where should I look to figure out its source?
Ok, can you look there and find the issue for me?
How does feature X interact with feature Y?
What are all the dependencies of my system?
I need to integrate feature Z; what parts of the system do I need to touch?
Design a new feature for the system
And produce a detailed implementation plan, broken into logically reviewable chunks

Based on the provided codebase, here is the precise technical breakdown of the bundle generation process, tracing the execution path from `generate_bundles.py` down to the creation of the multi-epoch root maps (`root_map_v0.md`, `root_map_v1.md`, etc.).
### 1. Entry Point and Initialization (`generate_bundles.py`)
The pipeline begins in `generate_bundles.py`, which is the main entry point for running the AI Codebase Indexer.
*   **Bundle Discovery:** The `main()` function uses `BundleStorage` to read `ProjectBundle` `.textproto` configuration files from the disk.
*   **Parallel Execution:** It spins up a `concurrent.futures.ThreadPoolExecutor` (based on the `MAX_PARALLEL_BUNDLES` flag) to process multiple bundles concurrently by calling `generate_bundle()`.
*   **Setup:** `generate_bundle()` determines if the bundle is a standard or Git-based repository, then calls `_execute_indexing()`.
*   **Component Instantiation:** `_execute_indexing()` wires together the core components. It initializes the `State` (for storage), `Chunker`, `SummaryMerger`, `LlmIndexer`, and the `Planner`. Finally, it initializes the `Orchestrator` (passing in `_NUM_EPOCHS`, which defaults to 2) and invokes `indexer_orchestrator.run()`.
### 2. Planning and Work Unit Aggregation (`planner/planner.py`)
Before any LLM is called, the `Orchestrator` asks the `Planner` for an `IndexPlan`.
*   **Discovery & Filtering:** The planner uses `tree_sizer.py` to traverse the directory structure from the bottom up, calculating byte sizes and filtering out excluded paths/silos.
*   **Union-Find Aggregation:** To avoid wasting LLM tokens on tiny directories, the planner uses a Union-Find algorithm (`_aggregate_small_work_units`). It merges small leaf directories into their parent directories to form consolidated `WorkUnit` objects, provided the combined size stays under `max_work_unit_size_bytes` (default 500 KB).
*   **Diffing:** It compares these units against the previous run's metadata (via `IndexDiffer`) to determine which `WorkUnit`s actually need re-indexing.
### 3. The Multi-Epoch Orchestration (`orchestrator.py`)
The `Orchestrator.run()` method drives the iterative refinement process. It loops over the number of epochs (e.g., `for epoch in range(self._num_epochs):`). 
*   **Epoch 0 (Isolated Discovery):** The indexer processes files strictly based on local file contents and immediate subdirectory summaries.
*   **Epoch 1+ (Global Context):** For any epoch > 0, the `Orchestrator` reads the previous epoch's root map (e.g., `root_map_v0.md`) from disk and passes its content down to the indexer as `previous_root_map_content`.
*   **Bottom-Up Execution:** During `_run_epoch()`, work units are grouped by path depth and processed deepest-first using a `ThreadPoolExecutor`. This ensures that a parent directory is only summarized *after* its subdirectories have been summarized, allowing the parent to ingest its children's context.
### 4. Work Unit Indexing (`llm_indexer.py` & `sequential_llm_prompter.py`)
For each `WorkUnit` during an epoch, `Orchestrator` calls `_process_work_unit()`, which hands off to `LlmIndexer.generate_index_for_work_unit()`.
*   **Prompt Selection:** `LlmIndexer` selects a prompt template. Epoch 0 uses `InitialIndexerPrompt`. Epochs > 0 use `IndexImproverPrompt`, injecting the `previous_root_map` to give the LLM cross-directory architectural context.
*   **Agentic Research Loop:** The `GeminiLlmPrompter` executes a sequential 5-stage chain-of-thought:
    1.  *CodeSearch Planner:* Generates RE2 queries to find external implementations/consumers.
    2.  *Read Files Planner:* Selects exact files to read based on search results.
    3.  *Key Components Agent:* Analyzes internal interfaces, dependencies, and configs.
    4.  *Deep Dive Agent:* Focuses on "how/why" implementation motivations.
    5.  *Overview Agent:* Synthesizes all findings and immediate subdirectory summaries.
*   **State Persistence:** The resulting markdown summary is written to Spanner or the local filesystem (`self._index_state.write_summary()`).
### 5. Root Map Generation (`root_map.py`)
At the very end of **each** epoch loop in `Orchestrator.run()`, the system calls `root_map.regenerate_root_map(...)` to build the overarching "Mental Model" for that epoch. Here is exactly how that is technically implemented:
1.  **Collection:** `regenerate_root_map` calls `collect_overviews()`. This function reads the newly generated summaries for *all* directories processed in the current epoch.
2.  **Extraction:** For each directory summary, it uses a utility function `file_utils.extract_markdown_section(content, "Overview")` to dynamically parse and slice out *only* the high-level `Overview` section of the document, stripping away the deeper code-level details.
3.  **Aggregation:** It concatenates all these extracted overviews into a massive single string, formatted with their canonicalized directory paths (e.g., `## path/to/dir \n\n <overview>`).
4.  **Flash Synthesis:** It passes this massive concatenated string to `llm_prompter.prompt_for_root_map_summary(overviews)`. This specifically triggers `flash_summarize.summarize()`, prompting a Gemini model to read the entire codebase's overviews and generate a dense 200-300 word executive "meta-summary."
5.  **File Creation:** Finally, the script stitches the generated meta-summary and the concatenated directory overviews together under the header `# Root Map - Epoch {epoch}`.
6.  **Persistence:** It writes this content to disk/state as `root_map_v{epoch}.md` (e.g., `root_map_v0.md` for Epoch 0, `root_map_v1.md` for Epoch 1).
By the end of the script, `root_map_v0.md` represents a localized mapping of the codebase, while `root_map_v1.md` represents an architecturally aware mapping, having used `root_map_v0.md` to spot distant dependencies during its generation phase.






The accuracy of Recursive-Index bundles—and the agents that rely on them to understand massive codebases—is understood and assured through a sophisticated, multi-layered evaluation and validation ecosystem. 

This system guarantees accuracy through four primary mechanisms: **Rubric-Based Expert Evaluations**, **"Haystack" Retrieval Benchmarks**, **Pre-computation Bundle Validation**, and **Semantic Integration Testing**.

### 1. Rubric-Based Expert Evaluations (`evals/expert`)
To understand how accurately the Index Expert agent reasons over a bundle, Recursive-Index uses a structured, LLM-driven evaluation framework that moves beyond simple string matching. 
* **Demerit-Based Scoring:** Instead of just comparing to a "golden answer," an evaluator agent assesses the generated response against a specific benchmark rubric (categorized into tiers like Focused, Detailed, and Comprehensive). It issues demerits for **Omissions** (missing facts), **Inaccuracies** (incorrect facts), and **Formatting** issues.
* **Strict Hallucination Checking:** To assure that the agent isn't just relying on its internal LLM weights, a dedicated `hallucination_agent` performs a strict factual verification. It compares the agent's final answer *exclusively* against the `research_context` (the raw source information the agent gathered during its execution). Any claim not explicitly supported by this localized context is flagged as a major hallucination demerit.
* **Automated Semantic Similarity:** The framework calculates BERT scores (Precision, Recall, and F1) to provide an automated, mathematical measure of how well the agent's response semantically aligns with the required rubric criteria.

### 2. "Needle in a Haystack" Benchmarks (`evals/haystack`)
Recursive-Index assures that its hierarchical indexing strategy actually works for deep retrieval by using a specialized "Haystack" evaluation suite.
* **Conceptual File Retrieval:** This framework quantitatively measures an agent's ability to locate the exact file implementing a specific functionality. An automated generator creates unambiguous, conceptual questions about a file's purpose (e.g., "Where is the functionality for aggregating various signals implemented?").
* **Strict Success Criteria:** The evaluation uses a strict suffix-matching rule. The agent's final response must end *exactly* with the expected relative file path to pass.
* **Index-Augmented Baseline Comparisons:** The accuracy of Recursive-Index bundles is proven by comparing baseline agents (using raw code search) against "index-augmented" agents (which are primed with the bundle's `root_map_v1.md` and a tool to fetch directory summaries). This proves how much the pre-computed directory metadata reduces the search space and improves retrieval reliability.

### 3. Build-Time Bundle Validation (`build_defs` & `scripts/bundle_verifier.py`)
Accuracy degrades if an LLM is overwhelmed by too much context. Recursive-Index assures the operational integrity and boundaries of a bundle before it is ever indexed.
* **Resource Governance (LOC Limits):** A dedicated `bundle_verifier.py` library intercepts bundle configurations during the Guitar presubmit phase (`config_size_presubmit_test.py`). It performs a live SQL query against the `zahlen` codesize database (hosted in F1) to estimate the total Lines of Code (LOC) covered by the bundle. By enforcing a standard 10-million-LOC limit, it prevents indexing bloat and ensures the resulting summaries remain focused and within the model's context window constraints.
* **Structural Checks:** It also enforces structural validity, checking for proper regex inclusions/exclusions, ensuring that custom prompts/guidance do not exceed character limits, and preventing overlapping configurations.

### 4. End-to-End Integration Testing (`integration_tests`)
Recursive-Index utilizes non-hermetic integration tests (e.g., `Recursive-Index_integration_test.py`) that integrate with actual persistent storage, repository, and Vertex AI. 
* **Semantic Verification:** These tests actually generate bundles on the fly and prompt the Expert Agent to answer specific questions (e.g., "What is the magic word in Recursive-Index_integration_test_file.md?"). The tests assert that the agent can successfully retrieve specific architectural details and correct answers from the generated hierarchical summaries, ensuring the mental model is fundamentally sound.
* **Structural Verification:** The tests also guarantee that features like "sparse tree" aggregation (combining small directories) and chunking of massive flat directories are reliably producing the required Markdown indices and `work_units.json` manifests.


