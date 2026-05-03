import os
import re

def check_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    executable_block_count = 0
    in_executable_block = False
    violations = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            if in_executable_block:
                if executable_block_count > 10:
                    violations.append((i - executable_block_count + 1, i, executable_block_count))
                executable_block_count = 0
                in_executable_block = False
            continue
        
        # This is a line of code
        in_executable_block = True
        executable_block_count += 1
        
        # Check if there's an inline comment
        if '#' in line:
            # If there's an inline comment, it counts as "having an explanatory comment" for the block?
            # Or maybe just resets the block?
            # "No block of executable code >10 lines exists without an explanatory comment."
            # Usually this means a comment *above* or *inside* the block.
            pass

    # Final block check
    if in_executable_block and executable_block_count > 10:
        violations.append((len(lines) - executable_block_count + 1, len(lines), executable_block_count))
        
    return violations

def main():
    indexing_dir = '/Users/pengbolicious/pengbo-apps/e-2-g/indexing'
    for root, dirs, files in os.walk(indexing_dir):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                violations = check_file(path)
                if violations:
                    print(f"Violations in {path}:")
                    for start, end, count in violations:
                        print(f"  Lines {start}-{end} ({count} lines)")

if __name__ == "__main__":
    main()
