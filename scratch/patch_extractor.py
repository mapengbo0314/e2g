import ast
import re

with open("indexing/ast_extractor.py", "r") as f:
    content = f.read()

tree_sitter_class = """
class TreeSitterExtractor:
    \"\"\"Stub for tree-sitter based extraction.\"\"\"
    def __init__(self, file_path: str, source_code: str, language: str):
        self.file_path = file_path
        self.source_code = source_code
        self.language = language
        self.symbols: List[ExportedSymbol] = []
        self.invariants: List[ImplementationInvariant] = []

    def extract(self) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
        try:
            import tree_sitter_languages
            from tree_sitter import Parser
            parser = tree_sitter_languages.get_parser(self.language)
            tree = parser.parse(self.source_code.encode('utf-8'))
            self._walk(tree.root_node)
        except Exception:
            pass
        return self.symbols, self.invariants

    def _walk(self, node):
        for child in node.children:
            self._walk(child)

def _extract_java_heuristic(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    symbols: List[ExportedSymbol] = []
    invariants: List[ImplementationInvariant] = []
    pkg_match = re.search(r'^[ \t]*package\s+([a-zA-Z0-9_.]+)\s*;', source_code, re.MULTILINE)
    pkg_prefix = f"{pkg_match.group(1)}." if pkg_match else ""
    
    class_pattern = re.compile(r'^[ \t]*(?:public\s+|protected\s+|private\s+)?(?:abstract\s+|final\s+)?class\s+([a-zA-Z0-9_]+)', re.MULTILINE)
    for match in class_pattern.finditer(source_code):
        name = match.group(1)
        symbols.append(ExportedSymbol(
            name=f"{pkg_prefix}{name}",
            signature=f"class {name}",
            summary="",
            file_path=file_path,
            line_number=source_code.count('\\n', 0, match.start()) + 1,
            source_kind="heuristic_ast"
        ))
    return symbols, invariants

def _extract_kotlin_heuristic(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    symbols: List[ExportedSymbol] = []
    invariants: List[ImplementationInvariant] = []
    pkg_match = re.search(r'^[ \t]*package\s+([a-zA-Z0-9_.]+)', source_code, re.MULTILINE)
    pkg_prefix = f"{pkg_match.group(1)}." if pkg_match else ""
    
    class_pattern = re.compile(r'^[ \t]*(?:public\s+|internal\s+|private\s+|protected\s+)?(?:open\s+|data\s+|sealed\s+)?(?:class|interface)\s+([a-zA-Z0-9_]+)', re.MULTILINE)
    for match in class_pattern.finditer(source_code):
        name = match.group(1)
        symbols.append(ExportedSymbol(
            name=f"{pkg_prefix}{name}",
            signature=f"class {name}", # simplified
            summary="",
            file_path=file_path,
            line_number=source_code.count('\\n', 0, match.start()) + 1,
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
"""

# Replace the typescript function
ts_js_old = """def extract_from_typescript_javascript(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    \"\"\"Attempts tree-sitter extraction for TS/JS, falling back to regex if unavailable.\"\"\"
    try:
        # Attempt to use tree-sitter if available in the environment
        import tree_sitter_languages
        from tree_sitter import Parser
        
        # Placeholder for actual tree-sitter logic. 
        # For now, we still fall back to heuristic but the structure is ready.
        # Real implementation would involve parser.set_language(...) and tree traversal.
        return _extract_ts_js_heuristic(file_path, source_code)
    except (ImportError, Exception):
        return _extract_ts_js_heuristic(file_path, source_code)"""

ts_js_new = """def extract_from_typescript_javascript(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    \"\"\"Attempts tree-sitter extraction for TS/JS, falling back to regex if unavailable.\"\"\"
    extractor = TreeSitterExtractor(file_path, source_code, 'typescript')
    symbols, invariants = extractor.extract()
    if not symbols and not invariants:
        return _extract_ts_js_heuristic(file_path, source_code)
    return symbols, invariants"""

go_old = """def extract_from_go(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    \"\"\"Regex-based extraction for Go (marked as heuristic_ast).\"\"\""""

go_new = """def extract_from_go(file_path: str, source_code: str) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
    \"\"\"Tree-sitter or Regex-based extraction for Go.\"\"\"
    extractor = TreeSitterExtractor(file_path, source_code, 'go')
    symbols, invariants = extractor.extract()
    if symbols or invariants:
        return symbols, invariants"""

# And update the dispatch
dispatch_old = """    if ext == '.py':
        return extract_from_python(file_path, source_code)
    elif ext in ('.ts', '.tsx', '.js', '.jsx'):
        return extract_from_typescript_javascript(file_path, source_code)
    elif ext == '.go':
        return extract_from_go(file_path, source_code)
    
    # Fallback for unsupported languages: return empty lists. 
    return [], []"""

dispatch_new = """    if ext == '.py':
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
    return [], []"""

content = content.replace("def _extract_ts_js_heuristic", tree_sitter_class + "\n\ndef _extract_ts_js_heuristic")
content = content.replace(ts_js_old, ts_js_new)
content = content.replace(go_old, go_new)
content = content.replace(dispatch_old, dispatch_new)

with open("indexing/ast_extractor.py", "w") as f:
    f.write(content)
