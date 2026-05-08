import sys
import re
from typing import List

VENDOR_PATTERNS = [
    r"node_modules/",
    r"venv/",
    r"site-packages/",
    r"/lib/python",
    r"/usr/lib/",
    r"external/"
]

ERROR_KEYWORDS = ["Exception", "Error:", "Traceback", "FAILED", "AssertionError", "ERROR", "CRITICAL"]

VENDOR_REGEX = re.compile("|".join(VENDOR_PATTERNS))

def prune_logs(input_text: str) -> str:
    lines = input_text.splitlines()
    pruned = []
    
    error_found = False
    for line in lines:
        # Always keep error messages and exceptions
        if any(kw in line for kw in ERROR_KEYWORDS):
            pruned.append(line)
            error_found = True
            continue
            
        # Keep lines that look like repo frames (assuming no vendor patterns)
        is_vendor = VENDOR_REGEX.search(line)
        if is_vendor:
            # Only keep vendor frame if we haven't found an error yet (might be part of the header)
            if not error_found:
                pruned.append(line)
            continue
            
        # Keep everything else (likely repo frames or context)
        pruned.append(line)
        
    return "\n".join(pruned)

if __name__ == "__main__":
    raw_input = sys.stdin.read()
    print(prune_logs(raw_input))
