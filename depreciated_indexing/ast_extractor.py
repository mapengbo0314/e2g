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


import sys

def _extract_signature(node: ast.AST) -> str:
    """Extracts a simple signature string from an AST node."""
    if isinstance(node, ast.ClassDef):
        if sys.version_info >= (3, 9):
            bases = ", ".join([ast.unparse(b) for b in node.bases])
        else:
            bases = ", ".join([getattr(b, 'id', getattr(b, 'name', 'unknown')) for b in node.bases])
        sig = f"class {node.name}"
        if bases:
            sig += f"({bases})"
        return sig
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        # Use ast.unparse for clean signatures in Python 3.9+
        if sys.version_info >= (3, 9):
            args = ast.unparse(node.args)
            returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
        else:
            args = ", ".join([getattr(a, 'arg', 'unknown') for a in getattr(node.args, 'args', [])])
            returns = ""
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
        is_private = node.name.startswith('_') and not node.name.startswith('__')

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
                source_kind="ast",
                is_private=is_private
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
    extractor = TreeSitterExtractor(file_path, source_code, 'typescript')
    symbols, invariants = extractor.extract()
    if not symbols and not invariants:
        return _extract_ts_js_heuristic(file_path, source_code)
    return symbols, invariants


class TreeSitterExtractor:
    """Tree-sitter based extraction for multiple languages."""
    def __init__(self, file_path: str, source_code: str, language: str):
        self.file_path = file_path
        self.source_code = source_code.encode('utf-8')
        self.language = language
        self.symbols: List[ExportedSymbol] = []
        self.invariants: List[ImplementationInvariant] = []

    def extract(self) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
        try:
            import tree_sitter_languages
            parser = tree_sitter_languages.get_parser(self.language)
            tree = parser.parse(self.source_code)
            self._walk(tree.root_node)
        except Exception:
            # Fallback to empty if tree-sitter fails
            pass
        return self.symbols, self.invariants

    def _walk(self, node):
        # Extract based on common node types across languages
        # This is a simplified version that catches typical declarations
        node_type = node.type
        
        name = None
        is_symbol = False
        kind = "ast"

        # Language-specific mapping
        if self.language in ('typescript', 'tsx', 'javascript'):
            if node_type in ('function_declaration', 'class_declaration', 'method_definition'):
                is_symbol = True
                # Try to find 'name' or 'identifier' child
                for child in node.children:
                    if child.type in ('identifier', 'property_identifier'):
                        name = self.source_code[child.start_byte:child.end_byte].decode('utf-8')
                        break
        elif self.language == 'go':
            if node_type in ('function_declaration', 'method_declaration', 'type_declaration'):
                is_symbol = True
                for child in node.children:
                    if child.type in ('identifier', 'type_identifier'):
                        name = self.source_code[child.start_byte:child.end_byte].decode('utf-8')
                        break
        elif self.language in ('java', 'kotlin'):
            if node_type in ('class_declaration', 'method_declaration', 'function_declaration'):
                is_symbol = True
                for child in node.children:
                    if child.type == 'identifier':
                        name = self.source_code[child.start_byte:child.end_byte].decode('utf-8')
                        break

        if is_symbol and name:
            # Basic signature extraction
            sig = self.source_code[node.start_byte:node.end_byte].decode('utf-8').split('{')[0].strip()
            self.symbols.append(ExportedSymbol(
                name=name,
                signature=sig,
                summary="",
                file_path=self.file_path,
                line_number=node.start_point[0] + 1,
                end_line_number=node.end_point[0] + 1,
                source_kind=kind
            ))

        for child in node.children:
            self._walk(child)

def _extract_java_heuristic(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    symbols: List[ExportedSymbol] = []
    invariants: List[ImplementationInvariant] = []
    pkg_match = re.search(r'^[ 	]*package\s+([a-zA-Z0-9_.]+)\s*;', source_code, re.MULTILINE)
    pkg_prefix = f"{pkg_match.group(1)}." if pkg_match else ""
    
    class_pattern = re.compile(r'^[ 	]*(?:public\s+|protected\s+|private\s+)?(?:abstract\s+|final\s+)?class\s+([a-zA-Z0-9_]+)', re.MULTILINE)
    for match in class_pattern.finditer(source_code):
        name = match.group(1)
        symbols.append(ExportedSymbol(
            name=f"{pkg_prefix}{name}",
            signature=f"class {name}",
            summary="",
            file_path=file_path,
            line_number=source_code.count('\n', 0, match.start()) + 1,
            source_kind="heuristic_ast"
        ))
    return symbols, invariants

def _extract_kotlin_heuristic(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    symbols: List[ExportedSymbol] = []
    invariants: List[ImplementationInvariant] = []
    pkg_match = re.search(r'^[ 	]*package\s+([a-zA-Z0-9_.]+)', source_code, re.MULTILINE)
    pkg_prefix = f"{pkg_match.group(1)}." if pkg_match else ""
    
    class_pattern = re.compile(r'^[ 	]*(?:public\s+|internal\s+|private\s+|protected\s+)?(?:open\s+|data\s+|sealed\s+)?(?:class|interface)\s+([a-zA-Z0-9_]+)', re.MULTILINE)
    for match in class_pattern.finditer(source_code):
        name = match.group(1)
        symbols.append(ExportedSymbol(
            name=f"{pkg_prefix}{name}",
            signature=f"class {name}", # simplified
            summary="",
            file_path=file_path,
            line_number=source_code.count('\n', 0, match.start()) + 1,
            source_kind="heuristic_ast"
        ))
    return symbols, invariants

def extract_from_java(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    extractor = TreeSitterExtractor(file_path, source_code, 'java')
    symbols, invariants = extractor.extract()
    if not symbols and not invariants:
        return _extract_java_heuristic(file_path, source_code)
    return symbols, invariants

def extract_from_kotlin(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    extractor = TreeSitterExtractor(file_path, source_code, 'kotlin')
    symbols, invariants = extractor.extract()
    if not symbols and not invariants:
        return _extract_kotlin_heuristic(file_path, source_code)
    return symbols, invariants


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
    """Tree-sitter or Regex-based extraction for Go."""
    extractor = TreeSitterExtractor(file_path, source_code, 'go')
    symbols, invariants = extractor.extract()
    if symbols or invariants:
        return symbols, invariants
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
    elif ext == '.java':
        return extract_from_java(file_path, source_code)
    elif ext == '.kt':
        return extract_from_kotlin(file_path, source_code)
    
    # Fallback for unsupported languages: return empty lists. 
    return [], []

def generate_deterministic_id(file_path: str, name: str, signature: str) -> str:
    """Generates a collision-proof ID using UTF-8 encoding."""
    raw = f"{file_path}:{name}:{signature}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]

def extract_skeleton(file_path: str, source_code: str) -> FileSkeleton:
    symbols, invariants = extract_ast_grounding(file_path, source_code)
    
    sk_symbols = []
    for s in symbols:
        sym_id = generate_deterministic_id(file_path, s.name, s.signature)
        sk_symbols.append(SkeletonSymbol(id=sym_id, name=s.name, signature=s.signature, line_number=s.line_number or 0, is_private=s.is_private))
        s.id = sym_id  # Retrofit existing ExportedSymbol
        
    sk_invariants = []
    inv_counts = {}
    for i in invariants:
        inv_counts[i.primitive] = inv_counts.get(i.primitive, 0) + 1
        count = inv_counts[i.primitive]
        inv_id = generate_deterministic_id(file_path, i.primitive, f"invariant-{count}")
        sk_invariants.append(SkeletonInvariant(id=inv_id, primitive=i.primitive, line_number=i.line_number or 0))
        i.id = inv_id  # Retrofit existing ImplementationInvariant
        
    return FileSkeleton(symbols=sk_symbols, invariants=sk_invariants)

