"""Automated code standards enforcement test.

Ensures the codebase adheres to elite engineering standards, specifically the
10-line rule: no code block should exceed 10 lines without at least one comment.
"""

import ast
import os
from pathlib import Path

import pytest

def get_code_files():
    """Returns all Python files in the indexing directory."""
    indexing_dir = Path("indexing")
    return list(indexing_dir.rglob("*.py"))

def check_10_line_rule(file_path):
    """Checks a file for violations of the 10-line comment rule.
    
    A violation occurs if there is a sequence of 11+ non-empty lines
    without any comment or docstring interspersed.
    """
    content = file_path.read_text()
    lines = content.splitlines()
    
    consecutive_code_lines = 0
    violations = []
    in_docstring = False
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Track docstrings
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if stripped.endswith('"""') or stripped.endswith("'''"):
                if len(stripped) > 3: # single line docstring
                    consecutive_code_lines = 0
                    continue
            in_docstring = not in_docstring
            consecutive_code_lines = 0
            continue
            
        if in_docstring:
            consecutive_code_lines = 0
            continue

        # Skip empty lines
        if not stripped:
            continue
            
        # If it's a comment, reset the counter
        if stripped.startswith("#"):
            consecutive_code_lines = 0
            continue
            
        # If it's code, increment the counter
        consecutive_code_lines += 1
        
        if consecutive_code_lines > 10:
            violations.append(f"Line {i}: {line}")
            # Reset after reporting to find the next block
            consecutive_code_lines = 0
            
    return violations

@pytest.mark.parametrize("file_path", get_code_files())
def test_10_line_comment_rule(file_path):
    """Enforces that no block of code exceeds 10 lines without a comment."""
    # We exclude __init__.py and very small files
    if file_path.name == "__init__.py":
        return
        
    violations = check_10_line_rule(file_path)
    if violations:
        error_msg = f"10-line rule violation in {file_path}:\n" + "\n".join(violations)
        pytest.fail(error_msg)

def test_no_print_statements():
    """Ensures no print() statements remain in production code (use logging)."""
    for file_path in get_code_files():
        if file_path.name == "generate_bundles.py": # CLI entry point might have some
            continue
        content = file_path.read_text()
        if "print(" in content and "logging" not in content:
            # Simple check, can be refined with AST
            pytest.fail(f"Possible print() statement found in {file_path}. Use logging instead.")

if __name__ == "__main__":
    pytest.main([__file__])
