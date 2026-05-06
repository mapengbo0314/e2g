# Tree-sitter Integration and Private Symbol Indexing Design

## 1. Overview
This design outlines the unification of our AST-based extraction pipeline by replacing fragile regex fallbacks with `tree-sitter` for TS, JS, Go, Java, Kotlin, and TSX. It also details how we will start including private symbols (e.g., `_my_func`) across all supported languages while strictly managing token volume in the resulting blueprint.

## 2. Library Management for Tree-sitter
Managing `.so`/`.dylib` grammar files manually is brittle and hard to scale across different OS environments (Linux/Mac/Windows). 

**Decision:** We will use the `tree-sitter-languages` Python package.
- It bundles pre-compiled grammars for a wide variety of languages (including TS, JS, Go, Java, Kotlin) and manages the platform-specific shared objects internally.
- **Action:** Add `tree-sitter` and `tree-sitter-languages` to `requirements.txt`.
- **Fallback:** If `tree-sitter-languages` fails to import, we will gracefully fall back to the existing regex heuristics to avoid breaking the pipeline on environments without compatible binaries.

## 3. Schema Mapping (Tree-sitter to ExportedSymbol)
Tree-sitter produces a concrete syntax tree (CST) which varies by language. We will unify this by using Tree-sitter's Query API rather than manual node traversal.

**Approach: Unified `TreeSitterExtractor`**
- We will define language-specific query strings for classes, functions, interfaces, and invariants.
- **Example Query (TS/JS):**
  ```scm
  (function_declaration 
    name: (identifier) @symbol.name) @symbol.node
  ```
- **Mapping logic:**
  - `name`: Extracted from the `@symbol.name` capture.
  - `signature`: Derived by taking the text of `@symbol.node` up to the opening brace `{`.
  - `line_number`: Extracted from `node.start_point[0] + 1` (Tree-sitter lines are 0-indexed; `schema.py` expects 1-indexed).
  - `source_kind`: Set to `"tree_sitter"`.

## 4. Including Private Symbols & Data Volume Strategy
Currently, `PythonSymbolExtractor` forcefully drops any symbol starting with `_` (unless it's a dunder method). We need to extract them, but prevent blueprint bloat.

**Design:**
1. **Update `ast_extractor.py`:** Remove the hardcoded `startswith('_')` dropping logic in `PythonSymbolExtractor` and ensure Tree-sitter queries also capture private symbols.
2. **Private Symbol Opt-in & Truncation:**
   - To prevent token explosion in the LLM context, private symbols will be explicitly tracked in the AST extraction phase but given a strict summarization rule.
   - We will add a flag (e.g., `include_private_symbols=False`) to the indexing config.
   - If enabled, private symbols are included but their `summary` will be aggressively capped (e.g., restricted to a 1-sentence max or a pure structural stub) so they act purely as a routing map without consuming deep reasoning tokens.
   - We can enforce this at the extraction layer: if `symbol.name.startswith('_')`, auto-stub its docstring extraction.

## 5. Stability of `generate_deterministic_id`
The current ID generation is: `hashlib.sha256(f"{name}:{signature}:{line_number}".encode('utf-8'))`.
- **Risk:** Tree-sitter vs. Regex vs. native `ast` might yield slightly different `line_number` values (e.g., counting decorators or docstrings).
- **Mitigation:**
  - We will rigorously map Tree-sitter's `start_point` to the exact keyword (e.g., `function` or `class`) rather than the start of the preceding decorator/comment. 
  - We will retain the exact 1-based indexing parity.

## 6. Implementation Boundaries
- **`requirements.txt`:** Add `tree-sitter`, `tree-sitter-languages`.
- **`indexing/ast_extractor.py`:**
  - Create `TreeSitterExtractor`.
  - Add language query definitions for Go, TS/JS, Java, Kotlin.
  - Update `PythonSymbolExtractor` to permit `_` symbols.
- **`indexing/schema.py`:** Add `is_private: bool = False` to `ExportedSymbol` (optional, for explicit downstream handling).

## Sphinch Mark Seeds (Design Consensus)
- [ ] `tree-sitter` and `tree-sitter-languages` are added to dependencies.
- [ ] `PythonSymbolExtractor` no longer drops `_` prefixed functions/classes.
- [ ] Tree-sitter lines are converted from 0-indexed to 1-indexed before ID generation.
- [ ] Extracted signatures for Tree-sitter nodes do not include the function body.
- [ ] Private symbols have their summaries capped or empty to limit token volume.
