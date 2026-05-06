import tree_sitter_languages

source = b'''package com.example.app;

public class Main {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}'''

parser = tree_sitter_languages.get_parser("java")
tree = parser.parse(source)

def find_package(node):
    if node.type == 'program':
        for child in node.children:
            if child.type == 'package_declaration':
                for child2 in child.children:
                    if child2.type == 'scoped_identifier' or child2.type == 'identifier':
                        return source[child2.start_byte:child2.end_byte].decode('utf-8')
    return None

print(f"Package: {find_package(tree.root_node)}")
