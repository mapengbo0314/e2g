# First Draft Technical Proposal

## Goal

Build an MVP indexing engine that can take a single existing codebase, recursively analyze it, and produce a persistent, structured knowledge artifact for later human and agent use.

For MVP, the product is not “a chat app about code.” The product is the indexing pipeline itself.

The concrete output of MVP is:

- per-directory `llm_index_v{epoch}.md` files
- top-level `root_map_v{epoch}.md`
- persisted work-unit metadata for re-runs and change-aware updates

This gives us the durable “mental model” layer that later systems can consume:
- harness engineering
- design generation
- agent context bootstrapping
- future Q&A / deep research

---

## Product Shape

I think the system should be implemented as a batch indexing engine with a narrow interface:

### Inputs
- local repo path or git URL
- bundle/config describing what to include and exclude
- output bundle directory
- model/runtime settings

### Outputs
- structured bundle directory containing:
  - `work_units.json`
  - directory-level index markdown files
  - root map markdown files
  - optional run metadata

### Non-goals for MVP
- UI
- MCP server
- live question answering
- multi-repo composition
- continuous background indexing service

Those should remain explicit future layers, not hidden MVP scope.

---

## Proposed Architecture

I would implement the project as six major layers.

### 1. Source Ingestion Layer

This layer normalizes where code comes from.

Responsibilities:
- accept a local repo path
- optionally clone a git repo into a temporary workspace
- canonicalize paths so output artifacts use stable relative paths
- expose a filesystem abstraction for downstream components

Why this matters:
The rest of the system should not care whether the source came from a checked-out local repo or a cloned repo. It should just operate on normalized root directories.

### 2. Planning Layer

This layer determines what the system should index and at what granularity.

Responsibilities:
- walk the source tree
- apply include/exclude filtering
- collect per-directory direct-file stats
- skip files above hard size limits
- aggregate small directories upward into `WorkUnit`s
- produce an `IndexPlan`

This is one of the most important parts of the design. The planner is not just a scanner. It is the layer that compresses a raw tree into LLM-friendly indexing units.

Conceptually:

```text
repo tree
  -> filtered directories/files
  -> DirectoryStats
  -> aggregated WorkUnits
  -> IndexPlan
```

The work-unit abstraction is the right boundary because it gives us:
- bounded LLM context
- stable reindex units
- a durable manifest for incremental runs

### 3. State and Manifest Layer

This layer persists what we indexed and what state the index is in.

Responsibilities:
- write/read per-directory index files
- write/read root map files
- write/read `work_units.json`
- expose latest-epoch lookup
- support deletion of stale outputs
- support comparison between current and prior runs

This layer is the foundation for resumability and incremental behavior. Without it, we only have a one-off summarizer. With it, we have maintained code intelligence.

I would preserve the current separation between:
- content state: markdown index artifacts and root maps
- execution state: work-unit manifest and last indexed info

### 4. Index Generation Layer

This layer generates the actual content for a work unit.

Responsibilities:
- load files from a work unit
- fetch child/subdirectory indexes when available
- read prior epoch index when available
- choose between:
  - direct summarization
  - chunked summarization + merge
- emit a structured `IndexDocument`
- render it to markdown

This layer should preserve the multi-stage prompting model:

- research-oriented analysis of files / code contents
- synthesis-oriented merging into structured section output

At a high level:

```text
WorkUnit
  -> load files
  -> gather context
  -> if small:
       generate IndexDocument
     else:
       chunk
       generate partial IndexDocuments
       merge partials
  -> render markdown
```

This is the real core of the product.

### 5. Root Map Synthesis Layer

This layer turns all directory-level indexes into a top-level codebase map.

Responsibilities:
- collect `Overview` sections from generated index docs
- concatenate them in stable path order
- generate a concise executive/root summary
- persist `root_map_v{epoch}.md`

This is important because per-directory summaries alone are not enough for fast global understanding. The root map is the cross-directory compression artifact.

For MVP, I think the root map should remain simple and deterministic:
- gather overviews
- synthesize one top summary
- append the underlying directory overviews

That is enough to support later agent bootstrap.

### 6. Orchestration Layer

This layer runs the indexing job end to end.

Responsibilities:
- initialize all components
- compute the plan
- run work units in bottom-up order
- run epoch loops
- regenerate root map after each epoch
- persist manifests and metadata
- handle failures and retries

This is where the whole system becomes a product instead of a library.

At a high level:

```text
load config
  -> resolve repo input
  -> create planner/state/indexer/merger/prompter
  -> plan work
  -> optionally diff against previous manifest
  -> run work units
  -> write index docs
  -> synthesize root map
  -> persist manifest
```

---

## Why I Think This Structure Fits Your System

Your broader vision is not just indexing for its own sake. It is indexing as infrastructure.

That means the MVP should optimize for:
- durable outputs
- deterministic artifact layout
- resumability
- enough structure that future agents can consume the output programmatically

That is why I think these pieces should stay:

- `WorkUnit`
- `Planner`
- `State`
- `Schema`
- `SummaryMerger`
- `RootMap`
- `Orchestrator`

Even in a simplified clone, these are not incidental details. They are the architecture that makes the outputs reusable.

---

## MVP Output Layout

I would recommend a bundle layout like this:

```text
bundles/
  <bundle_name>/
    work_units.json
    root_map_v0.md
    root_map_v1.md
    <relative/path/to/dir>/llm_index_v0.md
    <relative/path/to/dir>/llm_index_v1.md
```

This is good because:
- it keeps all artifacts together
- it mirrors the source tree
- it supports epoch evolution
- it is easy for future tooling to traverse

If you want a simpler MVP, we can do only `v0` first and add multiple epochs after the first working end-to-end version.

---

## My Recommendation on Epochs

This is the one place I would suggest a deliberate simplification.

I think we should architect for multi-epoch refinement, but possibly implement MVP in two phases:

### MVP-A
- one indexing epoch
- per-directory index generation
- root map generation
- full rerun support
- manifest persistence

### MVP-B
- add epoch-aware reindexing
- add use of previous root map as context
- add improved refinement loop

Why I’m suggesting this:
multi-epoch refinement is valuable, but it also complicates debugging. If we do one good pass first, we can validate the entire artifact chain before adding cross-epoch feedback.

If you strongly want epochs from day one, the architecture already supports it, but I would still keep the first implementation path narrow.

---

## Incremental Reindexing Proposal

You said you want weekly or change-aware updates. I think the right MVP approach is:

### Phase 1
- always support full reindex
- persist work-unit manifests and last indexed info

### Phase 2
- add change-detection-based selective reindex
- compare old and new manifests
- mark changed paths for reindex
- propagate invalidation upward to parents
- delete stale paths removed from the source tree

This fits the `IndexDiffer` design very naturally.

The key idea is:
we should diff work units, not just files.

That gives us stable operational behavior and preserves alignment with output artifacts.

---

## LLM Strategy

I think the system should keep the distinction between:
- research-oriented prompt steps
- synthesis-oriented prompt steps

Even if both use the same base model initially, the workflow should preserve different prompt roles:
- read/analyze code
- synthesize key components
- deep dive
- overview
- merge
- root summary

This matters because your desired outputs are not plain summaries. They are structured technical documents.

I would also recommend two runtime modes:

### 1. Fake mode
- deterministic stub outputs
- useful for pipeline testing
- no provider dependency

### 2. Real mode
- actual LLM calls
- provider-backed indexing
- used for real artifact generation

This will make the MVP much easier to debug and demo.

---

## Proposed MVP Execution Flow

```text
User runs index command
  -> load config
  -> resolve repo source
  -> create bundle output directory
  -> build planner
  -> generate WorkUnits
  -> load prior manifest if present
  -> diff for reindex if enabled
  -> for each work unit in bottom-up order:
       load files
       fetch subdirectory summaries
       generate directory index
       persist markdown
  -> collect overviews
  -> generate root map
  -> persist manifest
  -> print output bundle location
```

---

## What I Would Build First

If we were implementing this in order, I would do:

1. Stable core data model
- config
- work units
- manifests
- state interfaces

2. Planner and bundle output layout
- filesystem walk
- filtering
- work-unit aggregation
- persistence

3. Schema and markdown rendering
- structured section output
- markdown serializer

4. Fake LLM indexer path
- generate placeholder `IndexDocument`s
- validate end-to-end flow

5. Real prompter integration
- staged prompting
- chunking
- merging

6. Root map generation
- overview extraction
- top summary

7. Reindex/diff support
- selective re-run
- stale deletion

That ordering reduces risk because it proves the pipeline before provider complexity gets involved.

---

## Open Technical Choices

There are a few choices I think we should settle before implementation:

### 1. Config shape
Do we want:
- a structured bundle config file
or
- a simpler CLI-first config for MVP?

My recommendation:
start CLI-first, but design the internal config model so it can later be loaded from a file.

### 2. Epoch model
Do we want:
- single epoch first
or
- multi-epoch immediately?

My recommendation:
single epoch first, architect for multi-epoch.

### 3. Storage format
Do we want:
- markdown only
or
- markdown plus raw JSON model snapshots?

My recommendation:
write markdown as the primary artifact, but optionally persist JSON alongside it for future tooling.

### 4. Provider integration
Do we want:
- fake mode first
or
- real LLM immediately?

My recommendation:
support both, with fake mode available from day one.

---

## Final Recommendation

I think the right MVP is:

- single repo
- batch indexing
- bundle output directory
- planner + work units
- schema-based directory index generation
- root map generation
- manifest persistence
- basic rerun support
- optional selective reindex structure

And I think the right philosophy is:

build the indexing engine as durable infrastructure first, then layer deep research, harness integration, and agent-serving on top of it.

That gives you a product foundation instead of a demo.

If you want, the next step should be turning this into the first actual MVP design doc sections:
- Problem
- Technical Plan
- Alternatives Considered
- Detailed Implementation