# Design Document: AST-Grounded Enrichment Pipeline

## 1. Problem Statement

The current indexing pipeline relies on the LLM to both discover symbols in source code and describe them simultaneously. While we enforce a `BLUEPRINT FIDELITY MANDATE` to try and force the LLM to include every symbol from a pre-extracted AST list, this approach regularly fails. The LLM often omits symbols, hallucinates signatures, misidentifies private symbols as public, or fails to properly link implementation invariants to their specific code locations. These failures lead to "AST Grounding failures" where the Verifier rightly rejects the LLM's output because it has strayed from the deterministic ground truth of the AST. We need a pipeline that is structurally guaranteed to be grounded in the AST, moving the LLM from a "discovery" role to a pure "enrichment" role.

## 2. Proposed Design

The "AST-Grounded Enrichment Pipeline" splits the indexing of a file into two distinct, strictly separated phases joined by deterministic identifiers.

**Phase 1: Deterministic AST Extraction**
A language-specific parser (using `ast` for Python, `tree-sitter` or heuristics for Go/JS/TS) extracts the deterministic "skeleton" of the file. This `FileSkeleton` contains the definitive list of symbols and invariants, their exact signatures, and their exact line numbers.

**Phase 2: LLM Enrichment**
The LLM is provided with the source code AND the extracted `FileSkeleton`. Instead of generating the full index, the LLM's task is strictly constrained to producing a `FileEnrichment` object. This object provides the semantic "meat" (summaries, intents, usage contexts) for each identifier provided in the skeleton.

**The Join Strategy (Hybrid FQN IDs)**
The critical link between these two phases is the **Hybrid Fully Qualified Name (FQN) ID**.
- For standalone functions: `function_name`
- For methods: `ClassName.method_name`
- For nested classes: `OuterClass.InnerClass`
- For invariants: `PrimitiveName:LineNumber` (e.g., `Lock:142`)

A deterministic `Merger` script then joins the `FileSkeleton` and `FileEnrichment` on these IDs to produce the final `IndexDocument`.

**Merge Logic & Strict Discard:**
- If the LLM provides enrichment for an ID that *does not exist* in the `FileSkeleton`, it is considered a hallucination and is **strictly discarded**.
- If the `FileSkeleton` contains an ID that the LLM *failed* to enrich, we apply a **Fallback Strategy** (e.g., parsing the docstring directly).
- **Retry Strategy**: If the missing coverage (IDs in skeleton missing from enrichment) exceeds a threshold of **20%**, the pipeline triggers a retry for that file.

## 3. Architecture Diagram

```ascii
+-------------------+       +-------------------+       +-------------------+
|   Source File     | ----> |   AST Extractor   | ----> |   FileSkeleton    |
| (Python, Go, TS)  |       | (Deterministic)   |       | (IDs, Signatures) |
+-------------------+       +-------------------+       +-------------------+
        |                                                         |
        |                                                         v
        |           +-------------------+               +-------------------+
        +---------> |   LLM Prompter    | <------------ |   Prompt Engine   |
                    |   (Instructor)    |               +-------------------+
                    +-------------------+                         |
                              |                                   |
                              v                                   |
                    +-------------------+                         |
                    |  FileEnrichment   |                         |
                    | (Summaries, Int.) |                         |
                    +-------------------+                         |
                              |                                   |
                              v                                   v
                    +-------------------------------------------------------+
                    |                       AST Merger                      |
                    |       (Join on Hybrid FQN IDs, Discard Halluc.)       |
                    +-------------------------------------------------------+
                                              |
                                              v
                                    +-------------------+
                                    |   IndexDocument   |
                                    | (100% Grounded)   |
                                    +-------------------+
```

## 4. Alternatives Considered

- **Strict Prompting (Status Quo)**: Relying on the LLM to follow the `BLUEPRINT FIDELITY MANDATE` perfectly. Rejected because it is non-deterministic, fails frequently at scale, and wastes tokens/compute on retries.
- **Post-hoc Correction / Fuzzy Matching**: Letting the LLM generate whatever it wants and attempting to "fuzzy match" hallucinated names back to the real AST names. Rejected because mapping incorrect names back to truth is brittle, error-prone, and adds unnecessary complexity.
- **AST-Only Indexing**: Completely removing the LLM from the symbol indexing process. Rejected because ASTs alone cannot provide the high-level semantic summaries, business logic intents, and usage contexts that make the resulting index valuable to downstream autonomous agents.

## 5. Implementation Phases

**Phase 1: Infrastructure & Data Contracts**
Define the precise Pydantic schemas for the data contracts.

```python
from pydantic import BaseModel
from typing import List, Optional

# Skeleton Contract (Phase 1)
class SkeletonSymbol(BaseModel):
    id: str  # Hybrid FQN
    signature: str
    line_number: int

class SkeletonInvariant(BaseModel):
    id: str  # Primitive:LineNumber
    primitive: str
    line_number: int

class FileSkeleton(BaseModel):
    symbols: List[SkeletonSymbol]
    invariants: List[SkeletonInvariant]

# Enrichment Contract (Phase 2)
class SymbolEnrichment(BaseModel):
    id: str  # Must match a SkeletonSymbol.id
    summary: str

class InvariantEnrichment(BaseModel):
    id: str  # Must match a SkeletonInvariant.id
    intent: str
    usage_context: str

class FileEnrichment(BaseModel):
    symbols: List[SymbolEnrichment]
    invariants: List[InvariantEnrichment]
```

**Phase 2: Prompter Updates**
Update `indexing/prompter.py` (or `sequential_llm_prompter.py`) to use `instructor` to enforce the `FileEnrichment` schema. Create a new prompt template that clearly injects the `FileSkeleton` as the required workload.

**Phase 3: Merger Implementation**
Create the merge logic that performs the deterministic join. It must loop through the `FileSkeleton`, look up the corresponding enrichment in `FileEnrichment`, and construct the final `ExportedSymbol` and `ImplementationInvariant` objects for the `IndexDocument`. Implement the 20% retry threshold logic here.

**Phase 4: Verifier Updates**
Update `indexing/verification.py`. The "Stage 1.6: AST Grounding Enforcement" can be vastly simplified or removed entirely for file-level indices, as the output of the Merger is guaranteed by construction to be 100% AST-grounded.

## 6. Impact Audit

- **Expected Reduction in AST Grounding Failures**: ~95% reduction. The LLM is structurally prevented from introducing non-grounded symbols into the final document.
- **Token Impact**:
    - *Input*: Slight increase due to providing the `FileSkeleton` in the prompt.
    - *Output*: Significant decrease. The LLM no longer needs to write out full signatures or reproduce the AST structure; it only outputs IDs and text summaries.
- **Latency/Cost**: Expected to decrease overall due to the reduction in validation-triggered retries.

## 7. Sphinch Marks

<!-- consistency-fqn -->
- [ ] Hybrid FQN IDs generated by `ast_extractor.py` exactly match the format expected by the LLM prompt and the `ASTMerger`.
<!-- consistency-schemas -->
- [ ] Field names in `FileEnrichment` schema align with the terminology used in `prompt_templates.py`.

<!-- interface-merger -->
- [ ] `ASTMerger.merge()` successfully accepts a valid `FileSkeleton` and `FileEnrichment` and returns a valid `schema.IndexDocument` containing `ExportedSymbol`s.
<!-- interface-extractor -->
- [ ] Language parsers in `ast_extractor.py` uniformly implement the `Symbol` interface (Python, Go, JS, TS) to generate the `FileSkeleton`.

<!-- state-retry -->
- [ ] The pipeline correctly triggers a retry if the LLM fails to enrich >20% of the IDs present in the `FileSkeleton`.
<!-- state-fallback -->
- [ ] The Merger correctly falls back to source code docstrings when an LLM enrichment is missing (and below the retry threshold).

<!-- failure-hallucination -->
- [ ] The Merger strictly discards and logs any `SymbolEnrichment` whose `id` is not present in the `FileSkeleton`.
<!-- failure-schema -->
- [ ] Pydantic/Instructor validation failures on the `FileEnrichment` output trigger standard prompt-level retries.

<!-- deps-pydantic -->
- [ ] Pydantic v2 features are utilized for the new `FileEnrichment` and `FileSkeleton` schemas.
<!-- deps-ast -->
- [ ] Python's built-in `ast` module and `tree-sitter` (when available) are utilized as the authoritative extraction engines.
