## Section Zero: The Problem

Modern engineering teams often inherit large, messy, partially documented
codebases that are difficult to understand quickly. This creates friction for
nearly everyone involved in building or planning product work: software
engineers trying to implement features safely, technical leads estimating
scope, product managers evaluating feasibility, and other technical
stakeholders who need reliable answers about how a system actually works.

Today, understanding an unfamiliar codebase usually requires a slow and
expensive process. A person has to manually read many files, chase dependencies
across directories, infer architecture from implementation details, and piece
together system behavior from incomplete docs or tribal knowledge. In older or
fast-moving systems, that knowledge is often fragmented, outdated, or locked in
the heads of a few experienced engineers. As a result, teams lose time, make
riskier decisions, duplicate investigation work, and struggle to use AI tools
effectively because the AI lacks trustworthy, repo-specific context.

The problem we are solving is not just "searching code better." The deeper
problem is that teams do not have a durable, structured, high-quality knowledge
layer for their codebase. Without that layer, both humans and AI agents are
forced to repeatedly rediscover the same system understanding from raw source
code.

However, a generated knowledge layer is only useful if it is trustworthy. An
inaccurate index is often worse than no index at all, because engineers and AI
agents may rely on it without realizing that parts of it are stale, incomplete,
or wrong. A summary that confidently misstates a dependency, expands an acronym
incorrectly, overstates a directory's responsibilities, or misses an important
shared abstraction can mislead downstream design work, implementation work, and
future automated reasoning. The core challenge is not merely compressing a
codebase into summaries. The core challenge is producing a compressed mental
model that remains grounded in the actual repository and communicates useful
understanding without inventing facts.

This project solves that by turning a codebase into a recursively generated set
of structured knowledge artifacts that are designed for trust as much as for
coverage. Instead of requiring every engineer or agent to start from scratch,
the system will analyze the repository, summarize it directory by directory,
preserve important technical details in a consistent structure, and generate a
top-level root map that explains the system as a whole. Just as importantly,
the system will treat accuracy, grounding, and change-awareness as first-class
requirements so that the resulting artifacts can be reused safely.

In plain English: we want to make an existing codebase understandable on
demand, at scale, in a way that is persistent, structured, and trustworthy for
both people and AI.

## Section One: The Technical Plan

The system will be built as a command-line indexing engine that takes one code
repository, walks through it directory by directory, and produces a persistent
bundle of knowledge files. The bundle will contain detailed summaries for each
indexed directory, repository-level root-map files, canonical structured JSON
artifacts, and structured state files that allow the system to rerun later
without starting from zero. Unlike a simple report generator, this system is
specifically designed to produce knowledge artifacts that are grounded in source
material and safe for future human and agent consumption.

This design implements a robust system for bundle definitions, bundle
verification, work-unit persistence, CLI wrappers, and multiple storage
backends. The `indexing-reference/` directory provides a baseline scaffold
that preserves the important module boundaries we intend to implement locally.
This design therefore describes how to build the `indexing/` package from
that scaffold while extending it with artifact-level trust controls.

The first major component is the input and configuration layer. In MVP, the
system remains CLI-first operationally, but the canonical indexing contract is
not raw flags alone. It is defined by `ProjectBundle` bundle definitions
declared as textprotos. Those bundles specify what directories or repositories
are indexed, which filters apply, what custom sections are requested, and how
output should be organized. CLI flags then select bundles, control runtime
behavior, and choose operational settings such as output destinations or
verification strictness. This distinction matters because configuration is part
of the trust model, not just a convenience interface.

The second major component is the configuration verification layer. Before the
system ever attempts indexing, bundle definitions must pass blocking validation.
That includes basic structural checks such as bundle naming rules, input-path
sanity checks, limits on research-guidance length and custom-section prompts,
and policy enforcement for `git_input` bundles. It also includes bundle-size
denial based on estimated lines of code so obviously unbounded bundles are
rejected before they can consume excessive model context or indexing budget.
This layer is a first-class pre-run gate.

The third major component is the source preparation and file access layer. Its
job is to normalize the repository into a consistent local working shape. If
the user provides a local path, the system reads from that path directly. If
the user provides a git source, the system clones it into a temporary
workspace. After that, the rest of the pipeline works against a stable
directory tree and does not need to care where the code originally came from.

The fourth major component is the planning layer. This is the part that scans
the repository, filters out files that should not be indexed, groups related
files into manageable work units, and decides what needs to be processed in the
current run. This matters because a large codebase cannot simply be dumped into
one model call. The planner breaks the system into smaller units that are large
enough to be meaningful, but small enough to be processed reliably. This layer
also defines what the system can and cannot claim to know, because excluded
files, chunk boundaries, work-unit boundaries, and large-file skips all
directly affect summary quality.

The fifth major component is the indexing layer. For each planned work unit,
the system loads the relevant files, gathers useful context from child
directories or previous passes, and asks the model to generate a structured
understanding of that part of the codebase. If the directory is small enough,
it can be summarized directly. If it is too large, the system splits it into
chunks, summarizes each chunk, and then merges the chunk summaries into one
final directory-level result. This stage must be treated as grounded
generation, not open-ended prose writing. The system should instruct the model
to skip unknown information rather than guess, and to describe only what can be
supported by the files and context it actually received.

The sixth major component is the schema and rendering layer. The model output
is not treated as loose text. Instead, it is shaped into a consistent
structure with sections such as overview, deep dive, important components,
important interfaces, dependencies, testing strategy, and configuration notes.
That structured representation is the canonical artifact. In local MVP, it will
be persisted as JSON on disk. Markdown is then rendered from the canonical JSON
for humans to read. This distinction matters because downstream validation,
comparison, and future agent use should rely on the structured form rather than
parsing prose back out of markdown.

The seventh major component is the root map layer. After directory summaries
are produced, the system collects the high-level overview from each one and
combines them into a repository-wide map. This root map acts as the top-level
mental model of the codebase. In the multi-epoch architecture, later passes may
use the earlier root map as context so the model can improve summaries with a
better understanding of how distant parts of the system relate to one another.
However, the root map is also a lossy compression step, so the design must
treat it carefully. It is helpful global context, but it is not automatically
ground truth. Later passes should use it to improve contextualization and spot
likely inaccuracies, not to freely rewrite local summaries without checking
them against the directory's source material. The root map itself should also
gain structured-artifact parity rather than existing only as markdown.

The eighth major component is the artifact verification layer. This layer
exists because schema validation and careful prompting are not enough to
guarantee accuracy. The system should perform lightweight, LLM-based checks on
generated artifacts to catch likely unsupported claims, chunk-merging
distortions, stale references, and low-quality rewrites introduced by later
epochs. For MVP, this verification can remain intentionally simple. It does not
need to be a full evaluation platform. But it must be blocking. A work unit
that fails artifact verification must not be published as a final artifact.
Here, publication means writing the final canonical JSON and final markdown
rendering into the bundle output as trusted outputs consumable by humans or
downstream agents. The system may retain failed or degraded drafts internally
for debugging, but those drafts are not treated as published outputs.

The ninth major component is the state and persistence layer. The system needs
to remember what it indexed, what outputs were created, and what version of the
source tree those outputs correspond to. It will store work-unit manifests,
root maps, and per-directory outputs in a bundle directory. However, the
persistence story is broader than filesystem markdown. The system
treats work units and summaries as structured persistence concepts with
multiple backend flavors, including filesystem persistence, shadow
primary/secondary reads and writes. The local MVP
does not need to implement every backend, but it should preserve that shape:
structured manifests and artifacts are canonical, markdown is derivative, and
storage abstractions must be designed so they can support richer backends later.

The tenth major component is change detection and rerun support. Since the
product is meant to help with real engineering workflows, it cannot behave like
a one-time report generator. It needs to detect what changed between runs and
update only the affected parts where possible. For MVP, the design should
support both full reruns and change-aware reindexing, with enough stored
metadata to identify changed work units and regenerate the parent summaries
that depend on them. The current evidence supports structural invalidation
driven by work-unit manifests, file changes, and version-control lineage. The
long-term design should still acknowledge semantic invalidation as part of the
real problem, but MVP should begin with structural invalidation and explicit
extension points for richer dependency reasoning later.

All of these parts fit together as one trust-oriented pipeline. The user starts
the tool from the command line. The system loads bundle configuration, verifies
that configuration, loads the source, builds a plan, generates structured
summaries for each work unit, verifies those artifacts, publishes only the
artifacts that pass verification, produces the root map, and writes out the
final bundle. The end result is not just one summary file, but a reusable
knowledge package for that repository.

In the broader ecosystem, this feature is the foundation layer. It is the step
that turns raw source code into structured context. Later systems such as
harness engineering, design generation, code understanding workflows, deep
research agents, and expert-querying surfaces can all build on top of these
outputs. In other words, this indexing engine is not the final user experience
by itself. It is the infrastructure that makes better AI-assisted engineering
possible, and it only fulfills that role if its outputs are trustworthy enough
to reuse.

## Section Two: Alternatives Considered

One alternative was to start by building the full end-to-end product all at
once, including the indexing engine, deep research workflows, harness
integration, and user-facing serving layers such as MCP or interactive
question-answering. We ruled that out for the first version because it mixes
too many problems together. The indexing engine is the foundation for
everything else, so it is safer and more practical to make that layer solid
first before adding more agent behavior on top of it.

Another alternative was to make the MVP a chat or research product instead of
an indexing product. In that version, the system would focus first on answering
questions about a repo and only later worry about durable recursive summaries.
We ruled that out because the core business value here comes from creating a
persistent knowledge layer that both humans and future AI systems can rely on.
Without that layer, every later tool would still be forced to start from raw
source code and would repeat the same expensive discovery work.

We also considered simplifying the system into a one-pass summarizer that would
generate only a single repository-level summary. That approach would be faster
to build, but it would not preserve enough detail to be useful for real
engineering work. It would also make reruns, partial updates, and downstream
agent usage much weaker, because the output would not reflect the structure of
the codebase. We chose recursive per-directory indexing instead because it
creates a reusable map of the system rather than a single disposable report.

Another alternative was to rely primarily on prompt quality and schema
validation to handle accuracy. In that version, the system would instruct the
model to avoid hallucinating, validate the output format, and assume that this
was enough to make the generated artifacts trustworthy. We ruled that out
because format correctness is not the same as factual correctness. A summary
can be perfectly well-structured and still be misleading or wrong. Since users
may trust the generated index, the architecture needs at least a minimal
artifact verification story rather than treating accuracy as an emergent side
effect of good prompts.

We also considered a markdown-only design where the generated output would be
stored mainly as prose files and any structured information would be secondary
or omitted. We ruled that out because prose alone is hard to validate, diff,
compare, and reuse programmatically. A structured JSON artifact gives the
system a better foundation for consistency, downstream agent use, and future
trust mechanisms, while markdown remains valuable as the human-readable
rendering.

Another option was to delay multi-epoch refinement and start with only a single
indexing pass. That would reduce early implementation complexity, and it
remains a reasonable fallback if epoch-based refinement proves too noisy. We
kept multi-epoch indexing in the architecture because later passes can improve
cross-directory contextualization, but we are changing the rationale slightly.
Later epochs should not be assumed to improve truth automatically. They are
valuable because they can help correct framing mistakes and connect distant
parts of the system, but they must be used conservatively and any rewritten
outputs must pass verification before publication.

We also considered starting with a large, formal evaluation platform in the
MVP, including broad benchmark suites, rubric-heavy grading, and sophisticated
scoring infrastructure. We ruled that out for the first version because it
would expand scope too aggressively before the core indexing pipeline is proven.
However, we also rejected the opposite extreme of shipping with no verification
at all. The MVP should include a lightweight trust bar, such as basic artifact
verification checks and a small set of acceptance-style tests, even if the more
comprehensive evaluation ecosystem comes later.

We also considered starting with fake or stubbed model behavior only, and
adding the real language model integration later. We did decide that fake mode
should exist for testing, but we ruled out fake-only MVP because the product is
meant to deliver real technical understanding from real repositories. That
means the MVP needs genuine model-backed indexing, even if we keep a test mode
for local development and pipeline validation.

Another alternative was to begin with a file-based configuration format as the
main user interface. Instead, we chose a CLI-first operational approach for
the MVP while retaining bundle textprotos as the canonical configuration
contract. This gives us a fast path for local runs without discarding the real
configuration model used by the system.

We also considered designing for multi-repo indexing from the start. That is
part of the long-term direction, especially for systems made of many services,
but we ruled it out for the MVP because it would make planning, storage,
diffing, and summarization much more complicated before the single-repo engine
is proven. Starting with one repository gives us a narrower and more reliable
first target.

## Section Three: Detailed Implementation

This section describes the concrete implementation plan for the accuracy-focused
MVP. The goal of this work is to evolve the indexing system from a recursive
summary generator into a trust-oriented indexing pipeline that produces
structured, grounded, and minimally verified knowledge artifacts. The
`indexing-reference/` directory gives us a reliable baseline scaffold
for the intended module layout. The implementation below assumes we will build
the real system under `indexing/` using that structure as a literal starting
point, while updating some boundaries to reflect artifact-level verification and
canonical JSON persistence.

The work is organized around the files we will change or create under
`indexing/`. Every file listed below is included because it is necessary to
make accuracy, grounding, and verification first-class parts of the indexing
pipeline rather than treating them as prompt-level best-effort behavior.

### Files To Modify

#### `indexing/config/bundle.proto`

This file defines the canonical indexing contract for bundles. It should be
carried forward explicitly into the local implementation because bundle
definitions are part of the trust boundary, not just operational convenience.
The rationale for including this file is that the MVP should preserve the real
configuration contract rather than replacing it with ad hoc CLI-only behavior.

#### `indexing/scripts/bundle_verifier.py`

This file is the configuration verification layer. It captures
rules around bundle naming, input path validation, prompt-size limits, custom
section counts, and bundle-size enforcement. It should be updated only as
needed to align with the local package shape, but it must remain a blocking
pre-run gate. The rationale for including this file is that config verification
is a core part of the end-to-end trust story.

#### `indexing/schema.py`

This file will define the canonical structured artifact produced by indexing.
It must be updated so the structured representation can carry the trust-related
metadata needed by the MVP design. Crucially, to prevent infinite retry loops where the LLM is pressured to hallucinate missing information, the schema must explicitly support fallbacks. We will use `Optional[str]` and `Optional[List[str]]` in Pydantic, and explicitly instruct the LLM to return `null` if the code lacks a concept (e.g., no "Key Interfaces"). The verifier will treat this as a valid, non-hallucinated state. In addition to the existing section-based summary fields, this file should grow the fields needed to represent verification status, generation metadata, and the JSON form that will be persisted on disk.

#### `indexing/prompt_templates.py`

This file will be updated so accuracy rules are encoded directly in the system prompts used for indexing, improving, merging, and root map generation. Specifically, this file will introduce the **Retry Prompt Mechanics**. When a work unit fails verification, the recovery prompt will explicitly inject the Verifier's structured feedback (`issues: List[str]`) directly into the generator's context window (e.g., *"The verifier failed your previous attempt because you claimed X was used, but it is not in the source. Try again."*). The prompts should make unsupported inference explicitly disallowed, reinforce that unknown information must be skipped rather than guessed (`null`), and add new prompt templates for granular section-by-section verifier flows.

#### `indexing/sequential_llm_prompter.py`

This file will be extended to support explicit verification interactions in
addition to summary generation and merging. It should expose methods for
running verifier prompts, parsing verifier outputs, and returning structured
verification results to callers. **Additionally, it will implement a Factory Pattern to support multiple LLM providers (`GoogleAiConversation`, `OpenAiConversation`, `AnthropicConversation`, and `OllamaConversation`), allowing the pipeline to be vendor-agnostic and run entirely locally when needed.** The rationale for this change is that the rest
of the system needs a stable programmatic interface for trust checks rather
than reusing generation APIs for unrelated validation behavior, and it must support flexible, multi-provider execution environments.

#### `indexing/llm_indexer.py`

This file will be modified to make structured artifact generation the primary
output of indexing and to route generated summaries through verification before
they are treated as complete. It should preserve the right generation metadata,
handle chunked indexing with stricter caution, and treat chunk summary merging
as a high-risk area for factual drift. The rationale for this change is that
`llm_indexer.py` is the main place where factual errors, omission errors, and
overconfident phrasing are introduced into the system.

#### `indexing/summary_merger.py`

This file will be updated so partial-summary merging is no longer a simple
synthesis step. It should incorporate stricter merge behavior, preserve enough
merge context for downstream verification, and connect the merged result to the
verification subsystem before it is finalized. The rationale for this change is
that combining partial summaries is one of the easiest places for the system to
invent false unifications, lose important caveats, or overstate what the source
files collectively prove.

#### `indexing/root_map.py`

This file will be modified to treat root-map generation as a lossy but useful
global-context artifact rather than as automatic truth. It should continue to
collect directory overviews and synthesize a top-level map, but it should also
preserve enough structure and metadata to distinguish local grounded summaries
from globally synthesized framing. It should also integrate with lightweight
root-map verification and structured root-map persistence. The rationale for
this change is that later epochs will depend on the root map, so a low-quality
root map can amplify inaccuracies across the entire bundle.

#### `indexing/orchestrator.py`

This file will be updated to insert verification into the normal indexing lifecycle. The orchestrator should run the following stages in order: configuration already verified, structured generation, artifact verification, publication/persistence, and root-map regeneration. Because multi-epoch, multi-pass generation dramatically multiplies LLM API calls, the orchestrator will integrate the `tenacity` library to implement robust exponential backoff handling for `429 Too Many Requests` rate limits seamlessly. It will also define how the system behaves when verification fails (retrying up to 3 times before failing the unit). In MVP, failed work units must not be published as final artifacts.

#### `indexing/state.py`

This file will be modified so persistence includes not just rendered markdown
summaries but also the canonical structured artifact and verification metadata
for each indexed path and epoch. It should also support reading that data back
for later epochs, trust audits, and future agent consumers. The rationale for
this change is that a trust-oriented indexing system needs more durable state
than "markdown exists for this path."

#### `indexing/work_unit.py`

This file will be updated so work-unit manifests can carry the metadata needed
for trust-aware reruns and auditability. In practice this file sits on the
persistence boundary of the system, not just the planning layer. It may need to
record whether a work unit failed verification, whether its last output was
degraded, and whether it should be revisited because of invalidation logic
beyond direct file diffs. The rationale for this change is that work-unit
manifests are the natural place to record indexing outcomes and later rerun
decisions.

#### `indexing/reindexing.py`

This file will be modified to add the first version of trust-aware invalidation
behavior. MVP does not need full semantic dependency analysis, but this module
should at least establish the mechanism for reindexing because a shared schema,
config, or interface changed, not just because the files inside a directory
changed. The rationale for this change is that stale summaries are one of the
main ways an index becomes untrustworthy over time.

#### `indexing/planner/planner.py`

This file will be updated so the planning phase exposes the coverage decisions
that materially affect trust. That includes exclusions, large-file skips,
aggregation boundaries, and other planning decisions that shape what a summary
can honestly claim to represent. The rationale for this change is that planning
is part of the accuracy story, because an omitted or split context can create
misleading summaries even when the model behaves perfectly.

#### `indexing/file_utils.py`

This file will be modified to improve the loading and normalization of file and
subdirectory context used by both generation and verification. It should help
package source inputs consistently so later stages can reason about what the
model actually saw. The rationale for this change is that grounded generation
and trust checks both depend on stable, explicit context assembly.

#### `indexing/context.py`

This file will be updated so prompt context is constructed in a clearer and
more explicit way. It should separate direct file contents, child summaries,
previous-epoch summaries, root-map context, and any extra context added by the
bundle. The rationale for this change is that once accuracy becomes central, we
need to be precise about the difference between direct evidence and inherited
context.

#### `indexing/constants.py`

This file will be modified to define the constants used by the trust pipeline,
such as verification modes, retry behavior, severity levels, publication
states, or other cross-module policy values. The rationale for this change is
to keep these rules centralized rather than scattering trust-related policy
decisions across multiple modules.

#### `indexing/error_prompt_generator.py`

This file will be updated so retry and recovery prompts understand
verification-oriented failure modes. It should support cases such as malformed
verifier output, unsupported claims flagged during checking, or a need to
regenerate an index more conservatively. The rationale for this change is that
error recovery must align with the new trust contract rather than acting as a
generic retry mechanism.

#### `indexing/generate_bundles.py`

This file will be modified to wire the new trust-oriented components together
at the top level. It should create and configure the verification subsystem,
connect it to the indexer and orchestrator, and ensure bundle generation
persists the richer output state. The rationale for this change is that
`generate_bundles.py` is the entry point that assembles the full indexing
pipeline.

#### `indexing/shared_flags.py`

This file will be updated to add configuration knobs for verification behavior,
strictness, retries, and any lightweight MVP trust controls we want to expose.
The rationale for this change is that the new trust behavior needs to be
observable and configurable during development, testing, and rollout.

#### `indexing/README.md`

This file will be updated to document the new architecture, especially the fact
that the system now produces canonical structured JSON artifacts, performs
artifact verification, preserves bundle-based configuration, and treats the
root map as global context rather than automatic ground truth. The rationale
for this change is that the implementation model is changing substantially
enough that the module documentation must evolve with it.

### Files To Create

#### `indexing/config/*.textproto`

These example bundle definitions should be carried into the local implementation
as representative inputs. They are not code modules in the traditional sense,
but they are part of the real system boundary because `ProjectBundle`
textprotos are the operational declarations that drive indexing. The rationale
for creating or copying these files is to keep the MVP anchored to realistic
bundle usage.

#### `indexing/verification.py`

This new file will contain the main artifact verification subsystem. It will implement a two-stage verification pipeline: Stage 1 (Syntactic Validation) using deterministic Pydantic parsing to ensure valid JSON structure, and Stage 2 (Semantic Verification) using an LLM-based factual grounding check against the raw code. It will also implement an aggressive caching mechanism using a local `.verification_cache.json` file to track hashes of verified chunks, bypassing re-verification for unmodified chunks to save tokens and time. Furthermore, for large directories, merge verification will rely on a map-reduce strategy that avoids exceeding the context window of the verification model.

#### `indexing/verification_types.py`

This new file will define the structured types used by the verification subsystem. Crucially, it will define the `VerificationVerdict` Pydantic model containing: `passed: bool`, `confidence: float`, and `issues: List[str]`. This strict definition ensures the orchestrator can predictably route failures and the prompt generator can inject the specific `issues` strings back into the LLM context for retries. It will also define issue categories, severity levels, and publication decisions.

#### `indexing/rendering.py`

This new file will contain the rendering logic that turns canonical JSON
artifacts into markdown. The rationale for creating this file is that once JSON
becomes canonical, the render step deserves an explicit home rather than being
an implicit side effect scattered across schema or state modules.

#### `indexing/verification_test.py`

This new file will contain focused unit tests for the artifact verification
subsystem. It should cover structured parsing, verdict handling, failure
classification, and any policy logic used to decide whether an index passes or
requires regeneration. The rationale for creating this file is that the trust
layer must be tested directly rather than only through indirect integration
behavior.

#### `indexing/llm_indexer_test.py`

This new file will contain tests for the main generation-plus-verification
workflow. It should cover direct indexing, chunked indexing, conservative
handling of unknowns, and the persistence of structured artifacts after
verification. The rationale for creating this file is that `llm_indexer.py` is
the most important behavioral change point in the implementation.

#### `indexing/summary_merger_test.py`

This new file will contain tests for partial-summary merging and post-merge
verification. It should cover contradiction handling, omission handling, and
the interaction between merge output and the verification subsystem. The
rationale for creating this file is that chunked summarization is one of the
highest-risk accuracy paths in the system.

#### `indexing/root_map_test.py`

This new file will contain tests for root-map synthesis and any root-map
verification behavior included in MVP. It should cover root-map generation from
directory overviews, preservation of stable structure, and safe use of root-map
context across epochs. The rationale for creating this file is that root maps
will influence later rewrites, so they need dedicated coverage.

#### `indexing/reindexing_test.py`

This new file will contain tests for the updated invalidation logic. It should
cover ordinary file-level changes as well as the initial trust-aware triggers
that cause work units to be reindexed because shared abstractions or related
context changed. The rationale for creating this file is that stale summaries
are a core product risk and rerun logic must be validated directly.

#### `indexing/schema_test.py`

This new file will contain tests for the updated structured artifact schema and
any new trust-related fields it introduces. It should validate serialization,
deserialization, optional metadata handling, and markdown rendering behavior
where still applicable. The rationale for creating this file is that the schema
is the canonical contract for the whole system.

### Files Not Required In The First Pass

The following files do not need to change in the initial implementation unless
the real code path reveals a dependency we have not modeled yet:

- `indexing/chunker.py`
- `indexing/bundle_storage.py`
- `indexing/github_cloner.py`
- `indexing/multi_bundle_state.py`

These modules are adjacent to the trust pipeline, but they are not the primary
change points for the accuracy-focused MVP.

### Summary Of File Scope

The implementation scope for this design is now intentionally broad because it
needs to preserve both the real configuration contract and the new
artifact-verification flow. The exact count of modified and created files may
shift slightly as the local `indexing/` package is assembled from the scaffold,
but the major change points are now explicit enough that implementation can
proceed in a disciplined way without leaving major architectural decisions
unresolved.
