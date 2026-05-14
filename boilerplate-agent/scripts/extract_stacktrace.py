#!/usr/bin/env python3
import sys
import re

def extract_trace(log_content):
    # Heuristic for finding common stack trace patterns
    patterns = [
        r"Traceback \(most recent call last\):", # Python
        r"Error: .*?\n\s+at ",                 # Node
        r"panic: ",                            # Go
        r"AssertionError"                      # Generic
    ]
    
    lines = log_content.splitlines()
    for idx, line in enumerate(lines):
        if any(re.search(p, line) for p in patterns):
            # Capture from start of trace to the end of the log (or next block)
            # This ensures we get the full error context
            return "\n".join(lines[idx:idx+100]) # Cap at 100 lines
            
    return "\n".join(lines[-40:]) # Fallback to tail

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    with open(sys.argv[1], 'r') as f:
        print(extract_trace(f.read()))
