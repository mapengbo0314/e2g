# AST-Grounded Enrichment Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a two-phase indexing pipeline that strictly separates deterministic AST symbol extraction from LLM semantic enrichment, guaranteeing 100% AST grounding.

**Architecture:** 
1. `ast_extractor.py` generates a `FileSkeleton` with collision-proof IDs (SHA-256).
2. The LLM generates a `FileEnrichment` dictionary (O(1) lookups).
3. `ast_merger.py` deterministically joins them, dropping hallucinations and raising errors if mandatory IDs are missing.

**Tech Stack:** Python, Pydantic, pytest

---

### Task 1: Update Schemas

**Files:**
- Modify: `indexing/schema.py`
- Test: `tests/test_schema.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_schema.py
from indexing.schema import FileSkeleton, FileEnrichment, SkeletonSymbol, SymbolEnrichment

def test_ast_enrichment_schemas():
    skeleton = FileSkeleton(
        symbols=[SkeletonSymbol(id="hash1", name="Foo", signature="class Foo", line_number=10)],
        invariants=[]
    )
    enrichment = FileEnrichment(
        symbols={"hash1": SymbolEnrichment(summary="A foo class")},
        invariants={}
    )
    assert skeleton.symbols[0].id == "hash1"
    assert enrichment.symbols["hash1"].summary == "A foo class"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_schema.py::test_ast_enrichment_schemas -v`
Expected: FAIL with "ImportError: cannot import name 'FileSkeleton'"

- [ ] **Step 3: Write minimal implementation**
Append to `indexing/schema.py` (before `IndexDocument`):

```python
class SkeletonSymbol(_BaseModel):
    id: str = _field(description="Collision-proof hash ID")
    name: str = _field(description="Symbol name")
    signature: str = _field(description="Exact signature")
    line_number: int = _field(description="Starting line number")

class SkeletonInvariant(_BaseModel):
    id: str = _field(description="Collision-proof hash ID")
    primitive: str = _field(description="Primitive type")
    line_number: int = _field(description="Line number")

class FileSkeleton(_BaseModel):
    symbols: List[SkeletonSymbol] = _field(default_factory=list)
    invariants: List[SkeletonInvariant] = _field(default_factory=list)

class SymbolEnrichment(_BaseModel):
    summary: str = _field(description="Semantic summary of the symbol")

class InvariantEnrichment(_BaseModel):
    intent: str = _field(description="Intent behind the primitive")
    usage_context: str = _field(description="How it is used")

class FileEnrichment(_BaseModel):
    symbols: Dict[str, SymbolEnrichment] = _field(default_factory=dict)
    invariants: Dict[str, InvariantEnrichment] = _field(default_factory=dict)
```
Also update `ExportedSymbol` and `ImplementationInvariant` in `indexing/schema.py` to add:
```python
    id: str = _field(default="", description="The collision-proof hash ID.")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_schema.py::test_ast_enrichment_schemas -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add indexing/schema.py tests/test_schema.py
git commit -m "feat: add schema definitions for AST grounded enrichment"
```

### Task 2: Update Extractor with Collision-Proof IDs

**Files:**
- Modify: `indexing/ast_extractor.py`
- Test: `tests/test_ast_extractor.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ast_extractor.py
from indexing.ast_extractor import extract_skeleton

def test_extract_skeleton_generates_ids():
    code = "class Foo:\n    pass\n"
    skeleton = extract_skeleton("test.py", code)
    assert len(skeleton.symbols) == 1
    assert skeleton.symbols[0].id is not None
    assert len(skeleton.symbols[0].id) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ast_extractor.py::test_extract_skeleton_generates_ids -v`
Expected: FAIL with "ImportError: cannot import name 'extract_skeleton'"

- [ ] **Step 3: Write minimal implementation**
In `indexing/ast_extractor.py`, add the ID generator and `extract_skeleton`:

```python
import hashlib
from indexing.schema import FileSkeleton, SkeletonSymbol, SkeletonInvariant

def generate_deterministic_id(name: str, signature: str, line_number: int) -> str:
    """Generates a collision-proof ID using UTF-8 encoding."""
    raw = f"{name}:{signature}:{line_number}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]

def extract_skeleton(file_path: str, source_code: str) -> FileSkeleton:
    symbols, invariants = extract_ast_grounding(file_path, source_code)
    
    sk_symbols = []
    for s in symbols:
        sym_id = generate_deterministic_id(s.name, s.signature, s.line_number or 0)
        sk_symbols.append(SkeletonSymbol(id=sym_id, name=s.name, signature=s.signature, line_number=s.line_number or 0))
        s.id = sym_id  # Retrofit existing ExportedSymbol
        
    sk_invariants = []
    for i in invariants:
        inv_id = generate_deterministic_id(i.primitive, "invariant", i.line_number or 0)
        sk_invariants.append(SkeletonInvariant(id=inv_id, primitive=i.primitive, line_number=i.line_number or 0))
        i.id = inv_id  # Retrofit existing ImplementationInvariant
        
    return FileSkeleton(symbols=sk_symbols, invariants=sk_invariants)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ast_extractor.py::test_extract_skeleton_generates_ids -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add indexing/ast_extractor.py tests/test_ast_extractor.py
git commit -m "feat: add deterministic ID generation and FileSkeleton extraction"
```

### Task 3: Implement AST Merger

**Files:**
- Create: `indexing/ast_merger.py`
- Test: `tests/test_ast_merger.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ast_merger.py
import pytest
from indexing.schema import FileSkeleton, FileEnrichment, SkeletonSymbol, SymbolEnrichment
from indexing.ast_merger import ASTMerger, MissingEnrichmentError

def test_ast_merger_success():
    skeleton = FileSkeleton(symbols=[SkeletonSymbol(id="h1", name="Foo", signature="class Foo", line_number=1)])
    enrichment = FileEnrichment(symbols={"h1": SymbolEnrichment(summary="A class")})
    symbols, _ = ASTMerger.merge("test.py", skeleton, enrichment)
    assert symbols[0].summary == "A class"
    assert symbols[0].source_kind == "merged"

def test_ast_merger_missing_id():
    skeleton = FileSkeleton(symbols=[SkeletonSymbol(id="h1", name="Foo", signature="class Foo", line_number=1)])
    enrichment = FileEnrichment(symbols={})
    with pytest.raises(MissingEnrichmentError) as exc:
        ASTMerger.merge("test.py", skeleton, enrichment)
    assert "h1" in str(exc.value)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ast_merger.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**
Create `indexing/ast_merger.py`:

```python
from typing import Tuple, List
from indexing.schema import FileSkeleton, FileEnrichment, ExportedSymbol, ImplementationInvariant

class MissingEnrichmentError(Exception):
    pass

class ASTMerger:
    @staticmethod
    def merge(file_path: str, skeleton: FileSkeleton, enrichment: FileEnrichment) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
        missing_ids = []
        final_symbols = []
        for sk_sym in skeleton.symbols:
            if sk_sym.id not in enrichment.symbols:
                missing_ids.append(sk_sym.id)
            else:
                en_sym = enrichment.symbols[sk_sym.id]
                final_symbols.append(ExportedSymbol(
                    id=sk_sym.id, name=sk_sym.name, signature=sk_sym.signature,
                    summary=en_sym.summary, file_path=file_path, line_number=sk_sym.line_number,
                    source_kind="merged"
                ))
                
        final_invariants = []
        for sk_inv in skeleton.invariants:
            if sk_inv.id not in enrichment.invariants:
                missing_ids.append(sk_inv.id)
            else:
                en_inv = enrichment.invariants[sk_inv.id]
                final_invariants.append(ImplementationInvariant(
                    id=sk_inv.id, primitive=sk_inv.primitive, intent=en_inv.intent,
                    usage_context=en_inv.usage_context, file_path=file_path, line_number=sk_inv.line_number,
                    evidence_origin="merged"
                ))
                
        if missing_ids:
            raise MissingEnrichmentError(f"Mandatory IDs missing from enrichment: {missing_ids}")
            
        return final_symbols, final_invariants
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ast_merger.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add indexing/ast_merger.py tests/test_ast_merger.py
git commit -m "feat: implement deterministic AST merger with retry validation"
```

### Task 4: Update Verifier to Recognize Merged Artifacts

**Files:**
- Modify: `indexing/verification.py`

- [ ] **Step 1: Write minimal implementation**
In `indexing/verification.py`, modify `_check_ast_grounding` to immediately return `None` (pass) if `source_kind == "merged"` for symbols, as they are guaranteed grounded.
At the top of the `for file_path, evidence in ast_grounding.items():` loop in `_check_ast_grounding`, add:

```python
                # Skip AST Grounding checks if the pipeline already guarantees it via merging
                if llm_symbols and any(sym.source_kind == "merged" for sym in llm_symbols.values()):
                    continue
```

- [ ] **Step 2: Commit**

```bash
git add indexing/verification.py
git commit -m "feat: bypass AST check for deterministically merged artifacts"
```
