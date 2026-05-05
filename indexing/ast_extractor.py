"""AST-based extraction of symbols and invariants for deterministic grounding.

This module provides deterministic parsing of source files to extract symbols
(classes, functions) and implementation invariants (e.g., locks, threading primitives).
This serves as the "ground truth" that the LLM will enrich rather than discover.
"""

import ast
import os
import re
from typing import List, Tuple

from indexing.schema import ExportedSymbol, ImplementationInvariant

def _extract_signature(node: ast.AST, source_lines: List[str]) -> str:
    """Extracts a simple signature string from an AST node."""
    if isinstance(node, ast.ClassDef):
        bases = ", ".join([ast.unparse(b) for b in node.bases])
        sig = f"class {node.name}"
        if bases:
            sig += f"({bases})"
        return sig
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        # For simplicity, we just take the first line of the definition
        # which usually contains the signature. A full unparse could lose formatting
        # or we can use ast.unparse for the arguments.
        # Let's use ast.unparse for clean signatures in Python 3.9+
        args = ast.unparse(node.args)
        returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
        prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
        return f"{prefix}{node.name}({args}){returns}"
    return "unknown"

def extract_from_python(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    """Extracts symbols and invariants from a Python source file using the built-in ast module."""
    try:
        tree = ast.parse(source_code, filename=file_path)
    except SyntaxError:
        return [], []

    source_lines = source_code.splitlines()
    symbols: List[ExportedSymbol] = []
    invariants: List[ImplementationInvariant] = []

    # Known primitives to track for invariants
    known_primitives = {"Lock", "RLock", "Semaphore", "Condition", "Event", "flock", "lockf"}

    for node in ast.walk(tree):
        # Extract Exported Symbols
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            # Skip private symbols
            if node.name.startswith('_') and not node.name.startswith('__'):
                continue
                
            docstring = ast.get_docstring(node) or ""
            summary = docstring.split('\n')[0] if docstring else ""
            
            symbols.append(
                ExportedSymbol(
                    name=node.name,
                    signature=_extract_signature(node, source_lines),
                    summary=summary,
                    file_path=file_path,
                    line_number=node.lineno,
                    end_line_number=getattr(node, "end_lineno", node.lineno),
                    source_kind="ast"
                )
            )
            
        # Extract Implementation Invariants (heuristic-based primitive matching)
        elif isinstance(node, ast.Call):
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
                
            if func_name in known_primitives:
                invariants.append(
                    ImplementationInvariant(
                        primitive=func_name,
                        intent="[AST Discovered - LLM must enrich intent]",
                        usage_context="[AST Discovered - LLM must enrich usage context]",
                        file_path=file_path,
                        line_number=node.lineno,
                        end_line_number=getattr(node, "end_lineno", node.lineno),
                        evidence_origin="ast"
                    )
                )

    # Sort by line number
    symbols.sort(key=lambda x: x.line_number or 0)
    invariants.sort(key=lambda x: x.line_number or 0)
    
    return symbols, invariants

def extract_from_typescript_javascript(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
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
            source_kind="ast"
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
            source_kind="ast"
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
            source_kind="ast"
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
            evidence_origin="ast"
        ))

    # Sort by line number
    symbols.sort(key=lambda x: x.line_number or 0)
    invariants.sort(key=lambda x: x.line_number or 0)

    return symbols, invariants

def extract_from_go(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    """Regex-based extraction for Go as a fallback for full AST parsing."""
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
            source_kind="ast"
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
            source_kind="ast"
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
            source_kind="ast"
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
            evidence_origin="ast"
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
