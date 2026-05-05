"""AST-based extraction of symbols and invariants for deterministic grounding.

This module provides deterministic parsing of source files to extract symbols
(classes, functions) and implementation invariants (e.g., locks, threading primitives).
This serves as the "ground truth" that the LLM will enrich rather than discover.
"""

import ast
import os
import re
import hashlib
from typing import List, Tuple, Optional

from indexing.schema import (
    ExportedSymbol,
    ImplementationInvariant,
    FileSkeleton,
    SkeletonSymbol,
    SkeletonInvariant
)


def _extract_signature(node: ast.AST) -> str:
    """Extracts a simple signature string from an AST node."""
    if isinstance(node, ast.ClassDef):
        bases = ", ".join([ast.unparse(b) for b in node.bases])
        sig = f"class {node.name}"
        if bases:
            sig += f"({bases})"
        return sig
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        # Use ast.unparse for clean signatures in Python 3.9+
        args = ast.unparse(node.args)
        returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
        prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
        return f"{prefix}{node.name}({args}){returns}"
    return "unknown"

class PythonSymbolExtractor(ast.NodeVisitor):
    """Visitor to extract symbols and invariants with class-awareness."""
    
    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.symbols: List[ExportedSymbol] = []
        self.invariants: List[ImplementationInvariant] = []
        self.current_class: Optional[str] = None
        self.known_primitives = {"Lock", "RLock", "Semaphore", "Condition", "Event", "flock", "lockf"}

    def visit_ClassDef(self, node: ast.ClassDef):
        # Extract the class itself
        if not node.name.startswith('_') or node.name.startswith('__'):
            docstring = ast.get_docstring(node) or ""
            summary = docstring.split('\n')[0] if docstring else ""
            self.symbols.append(
                ExportedSymbol(
                    name=node.name,
                    signature=_extract_signature(node),
                    summary=summary,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    end_line_number=getattr(node, "end_lineno", node.lineno),
                    source_kind="ast"
                )
            )
        
        # Track class context for methods (support nesting)
        old_class = self.current_class
        if self.current_class:
            self.current_class = f"{self.current_class}.{node.name}"
        else:
            self.current_class = node.name
        
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visit_function(node)

    def _visit_function(self, node: ast.AST):
        # Skip private symbols, but keep dunder methods
        if node.name.startswith('_') and not node.name.startswith('__'):
            return

        name = f"{self.current_class}.{node.name}" if self.current_class else node.name
        docstring = ast.get_docstring(node) or ""
        summary = docstring.split('\n')[0] if docstring else ""
        
        self.symbols.append(
            ExportedSymbol(
                name=name,
                signature=_extract_signature(node),
                summary=summary,
                file_path=self.file_path,
                line_number=node.lineno,
                end_line_number=getattr(node, "end_lineno", node.lineno),
                source_kind="ast"
            )
        )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            
        if func_name in self.known_primitives:
            self.invariants.append(
                ImplementationInvariant(
                    primitive=func_name,
                    intent="[AST Discovered - LLM must enrich intent]",
                    usage_context="[AST Discovered - LLM must enrich usage context]",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    end_line_number=getattr(node, "end_lineno", node.lineno),
                    evidence_origin="ast"
                )
            )
        self.generic_visit(node)

def extract_from_python(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    """Extracts symbols and invariants from a Python source file using a NodeVisitor."""
    try:
        tree = ast.parse(source_code, filename=file_path)
    except SyntaxError:
        return [], []

    extractor = PythonSymbolExtractor(file_path, source_code)
    extractor.visit(tree)

    # Sort by line number
    extractor.symbols.sort(key=lambda x: x.line_number or 0)
    extractor.invariants.sort(key=lambda x: x.line_number or 0)
    
    return extractor.symbols, extractor.invariants

def extract_from_typescript_javascript(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    """Attempts tree-sitter extraction for TS/JS, falling back to regex if unavailable."""
    try:
        # Attempt to use tree-sitter if available in the environment
        import tree_sitter_languages
        from tree_sitter import Parser
        
        # Placeholder for actual tree-sitter logic. 
        # For now, we still fall back to heuristic but the structure is ready.
        # Real implementation would involve parser.set_language(...) and tree traversal.
        return _extract_ts_js_heuristic(file_path, source_code)
    except (ImportError, Exception):
        return _extract_ts_js_heuristic(file_path, source_code)

def _extract_ts_js_heuristic(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    """Regex-based extraction for TS/JS as a fallback for full AST parsing."""
    symbols: List[ExportedSymbol] = []
    invariants: List[ImplementationInvariant] = []
    
    # 1. Classes: class Name { ... }
    class_pattern = re.compile(r'^[ \t]*(?:export\s+)?class\s+([a-zA-Z0-9_$]+)(?:\s+extends\s+[^{]+)?\s*\{', re.MULTILINE)
    for match in class_pattern.finditer(source_code):
        name = match.group(1)
        symbols.append(ExportedSymbol(
            name=name,
            signature=f"class {name}",
            summary="",
            file_path=file_path,
            line_number=source_code.count('\n', 0, match.start()) + 1,
            source_kind="heuristic_ast"
        ))
        
    # 2. Functions: function Name(...) { ... }
    func_pattern = re.compile(r'^[ \t]*(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\(([^)]*)\)', re.MULTILINE)
    for match in func_pattern.finditer(source_code):
        name = match.group(1)
        args = match.group(2).replace('\n', ' ').strip()
        symbols.append(ExportedSymbol(
            name=name,
            signature=f"function {name}({args})",
            summary="",
            file_path=file_path,
            line_number=source_code.count('\n', 0, match.start()) + 1,
            source_kind="heuristic_ast"
        ))
        
    # 3. Arrow functions assigned to const: const Name = (...) => { ... }
    arrow_pattern = re.compile(r'^[ \t]*(?:export\s+)?const\s+([a-zA-Z0-9_$]+)\s*=\s*(?:\([^)]*\)|[a-zA-Z0-9_$]+)\s*=>', re.MULTILINE)
    for match in arrow_pattern.finditer(source_code):
        name = match.group(1)
        symbols.append(ExportedSymbol(
            name=name,
            signature=f"const {name} = ...",
            summary="",
            file_path=file_path,
            line_number=source_code.count('\n', 0, match.start()) + 1,
            source_kind="heuristic_ast"
        ))
        
    # 4. Invariants (heuristics for Mutex, Lock, etc.)
    invariant_pattern = re.compile(r'(?:new\s+)?(Mutex|Lock|Semaphore|flock|lockf)\(', re.IGNORECASE)
    for match in invariant_pattern.finditer(source_code):
        primitive = match.group(1)
        invariants.append(ImplementationInvariant(
            primitive=primitive,
            intent="[AST Discovered - LLM must enrich intent]",
            usage_context="[AST Discovered - LLM must enrich usage context]",
            file_path=file_path,
            line_number=source_code.count('\n', 0, match.start()) + 1,
            evidence_origin="heuristic_ast"
        ))

    # Sort by line number
    symbols.sort(key=lambda x: x.line_number or 0)
    invariants.sort(key=lambda x: x.line_number or 0)

    return symbols, invariants

def extract_from_go(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    """Regex-based extraction for Go (marked as heuristic_ast)."""
    symbols: List[ExportedSymbol] = []
    invariants: List[ImplementationInvariant] = []
    
    # 1. Functions: func Name(...) { ... } or func (r *Receiver) Name(...) { ... }
    # Note: In Go, exported symbols start with an uppercase letter.
    # We allow optional [ \t]* at start of line and optional receiver.
    func_pattern = re.compile(r'^[ \t]*func\s+(?:\([^)]+\)\s+)?([A-Z][a-zA-Z0-9_]*)\s*\(([^)]*)\)', re.MULTILINE)
    for match in func_pattern.finditer(source_code):
        name = match.group(1)
        args = match.group(2).replace('\n', ' ').strip()
        symbols.append(ExportedSymbol(
            name=name,
            signature=f"func {name}({args})",
            summary="",
            file_path=file_path,
            line_number=source_code.count('\n', 0, match.start()) + 1,
            source_kind="heuristic_ast"
        ))
        
    # 2. Structs: type Name struct { ... }
    struct_pattern = re.compile(r'^[ \t]*type\s+([A-Z][a-zA-Z0-9_]*)\s+struct', re.MULTILINE)
    for match in struct_pattern.finditer(source_code):
        name = match.group(1)
        symbols.append(ExportedSymbol(
            name=name,
            signature=f"type {name} struct",
            summary="",
            file_path=file_path,
            line_number=source_code.count('\n', 0, match.start()) + 1,
            source_kind="heuristic_ast"
        ))
        
    # 3. Interfaces: type Name interface { ... }
    interface_pattern = re.compile(r'^[ \t]*type\s+([A-Z][a-zA-Z0-9_]*)\s+interface', re.MULTILINE)
    for match in interface_pattern.finditer(source_code):
        name = match.group(1)
        symbols.append(ExportedSymbol(
            name=name,
            signature=f"type {name} interface",
            summary="",
            file_path=file_path,
            line_number=source_code.count('\n', 0, match.start()) + 1,
            source_kind="heuristic_ast"
        ))
        
    # 4. Invariants (Go sync primitives)
    # sync.Mutex, sync.RWMutex, etc.
    invariant_pattern = re.compile(r'(sync\.(?:Mutex|RWMutex|WaitGroup|Cond|Pool))', re.IGNORECASE)
    for match in invariant_pattern.finditer(source_code):
        primitive = match.group(1)
        invariants.append(ImplementationInvariant(
            primitive=primitive,
            intent="[AST Discovered - LLM must enrich intent]",
            usage_context="[AST Discovered - LLM must enrich usage context]",
            file_path=file_path,
            line_number=source_code.count('\n', 0, match.start()) + 1,
            evidence_origin="heuristic_ast"
        ))

    # Sort by line number
    symbols.sort(key=lambda x: x.line_number or 0)
    invariants.sort(key=lambda x: x.line_number or 0)

    return symbols, invariants

def extract_ast_grounding(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    """Entry point for AST extraction. Dispatches to the appropriate parser based on file extension."""
    _, ext = os.path.splitext(file_path)
    
    if ext == '.py':
        return extract_from_python(file_path, source_code)
    elif ext in ('.ts', '.tsx', '.js', '.jsx'):
        return extract_from_typescript_javascript(file_path, source_code)
    elif ext == '.go':
        return extract_from_go(file_path, source_code)
    
    # Fallback for unsupported languages: return empty lists. 
    return [], []

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

