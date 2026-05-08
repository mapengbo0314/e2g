# Refactor prune_logs.py and enhance tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `scripts/prune_logs.py` for efficiency and better structure, and enhance `tests/test_prune_logs.py` with direct function testing and edge cases.

**Architecture:** 
1.  Move patterns and keywords to module-level constants.
2.  Compile vendor patterns into a single regex for efficiency.
3.  Add type hints to the `prune_logs` function.
4.  Update tests to import and test `prune_logs` directly.
5.  Add edge case tests (empty input, no errors).

**Tech Stack:** Python, pytest

---

### Task 1: Refactor `scripts/prune_logs.py`

**Files:**
- Modify: `scripts/prune_logs.py`

- [ ] **Step 1: Define constants and compile regex**

```python
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
```

- [ ] **Step 2: Update `prune_logs` with constants and type hints**

```python
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
```

- [ ] **Step 3: Verify the script still works as a CLI**

Run: `echo "test" | python3 scripts/prune_logs.py`
Expected: `test`

### Task 2: Enhance `tests/test_prune_logs.py`

**Files:**
- Modify: `tests/test_prune_logs.py`

- [ ] **Step 1: Import `prune_logs` directly**

```python
from scripts.prune_logs import prune_logs
```

- [ ] **Step 2: Add direct function tests**

```python
def test_prune_logs_function_directly():
    input_text = "line1\nnode_modules/lib.js\nError: boom\nvenv/lib.py"
    expected = "line1\nnode_modules/lib.js\nError: boom"
    assert prune_logs(input_text) == expected
```

- [ ] **Step 3: Add edge case tests**

```python
def test_prune_logs_empty_input():
    assert prune_logs("") == ""

def test_prune_logs_no_errors():
    input_text = "line1\nnode_modules/lib.js\nline2"
    # Without an error, vendor frames are kept
    assert prune_logs(input_text) == input_text
```

- [ ] **Step 4: Run all tests**

Run: `pytest tests/test_prune_logs.py`
Expected: ALL PASS

### Task 3: Final Verification and Commit

- [ ] **Step 1: Run full test suite**

Run: `pytest`

- [ ] **Step 2: Commit changes**

```bash
git add scripts/prune_logs.py tests/test_prune_logs.py
git commit -m "refactor: optimize prune_logs and enhance testing"
```
