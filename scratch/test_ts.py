import tree_sitter_languages
try:
    parser = tree_sitter_languages.get_parser('javascript')
    tree = parser.parse(b"function foo() {}")
    print(tree.root_node.type)
except Exception as e:
    print(e)
