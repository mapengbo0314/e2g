"""AST-based extraction of symbols and invariants for deterministic grounding.

This module provides deterministic parsing of source files to extract symbols
(classes, functions) and implementation invariants (e.g., locks, threading primitives).
This serves as the "ground truth" that the LLM will enrich rather than discover.
"""

import ast
import os
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
                    end_line_number=node.end_lineno,
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
                        end_line_number=node.end_lineno,
                        evidence_origin="ast"
                    )
                )

    # Sort by line number
    symbols.sort(key=lambda x: x.line_number or 0)
    invariants.sort(key=lambda x: x.line_number or 0)
    
    return symbols, invariants

def extract_ast_grounding(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    """Entry point for AST extraction. Dispatches to the appropriate parser based on file extension."""
    _, ext = os.path.splitext(file_path)
    
    if ext == '.py':
        return extract_from_python(file_path, source_code)
    
    # Fallback for unsupported languages: return empty lists. 
    # Can be extended with tree-sitter for other languages.
    return [], []
