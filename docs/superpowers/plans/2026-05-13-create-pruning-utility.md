# Create Pruning Utility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a CLI utility `scripts/prune_logs.py` to prune vendor noise from logs while keeping error messages and repository-related frames.

**Architecture:** A Python script that reads from `stdin`, processes the text line-by-line using regex patterns to identify noise (e.g., `node_modules`, `venv`), and outputs the pruned text to `stdout`.

**Tech Stack:** Python 3, `pytest` for testing.

---

### Task 1: Setup and Basic Pruning Logic (TDD)

**Files:**
- Create: `scripts/prune_logs.py`
- Create: `tests/test_prune_logs.py`

- [ ] **Step 1: Write the failing test for basic pruning**

```python
import subprocess
import sys
import os

def test_prune_logs_basic():
    input_text = """
some/path/to/repo/file.py:10: in function
    code_here()
venv/lib/python3.9/site-packages/some_lib.py:20: in lib_func
    lib_code()
Error: Something went wrong
"""
    # Use the script as a CLI utility
    process = subprocess.Popen(
        [sys.executable, "scripts/prune_logs.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate(input=input_text)
    
    assert "venv/" not in stdout
    assert "Error: Something went wrong" in stdout
    assert "some/path/to/repo/file.py" in stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_prune_logs.py -v`
Expected: FAIL (File not found or script execution error)

- [ ] **Step 3: Implement `scripts/prune_logs.py`**

```python
import sys
import re

def prune_logs(input_text):
    lines = input_text.splitlines()
    pruned = []
    
    # Common vendor/noise patterns
    vendor_patterns = [
        r"node_modules/",
        r"venv/",
        r"site-packages/",
        r"/lib/python",
        r"/usr/lib/",
        r"external/"
    ]
    
    error_found = False
    for line in lines:
        # Always keep error messages and exceptions
        if any(kw in line for kw in ["Exception", "Error:", "Traceback", "FAILED", "AssertionError"]):
            pruned.append(line)
            error_found = True
            continue
            
        # Keep lines that look like repo frames (assuming no vendor patterns)
        is_vendor = any(re.search(pat, line) for pat in vendor_patterns)
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_prune_logs.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/prune_logs.py tests/test_prune_logs.py
git commit -m "feat(scripts): add prune_logs.py utility for local log compression"
```

---

### Task 2: Comprehensive Pruning Validation

**Files:**
- Modify: `tests/test_prune_logs.py`

- [ ] **Step 1: Add more comprehensive test cases**

```python
def test_prune_logs_comprehensive():
    input_text = """
Header line 1
Header line 2
node_modules/some-lib/index.js:5
  some code
some/repo/file.py:10
  repo code
Error: Failed here
venv/lib/python3.9/site-packages/other-lib/main.py:20
  ignored code
Traceback (most recent call last):
  File "some/repo/file.py", line 10, in <module>
    raise Exception("Boom")
"""
    process = subprocess.Popen(
        [sys.executable, "scripts/prune_logs.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate(input=input_text)
    
    # Should keep header vendor frames if before error
    assert "node_modules/some-lib/index.js:5" in stdout
    # Should keep repo frames
    assert "some/repo/file.py:10" in stdout
    # Should keep the error
    assert "Error: Failed here" in stdout
    # Should prune vendor frames after error
    assert "venv/lib/python3.9/site-packages/other-lib/main.py:20" not in stdout
    # Should keep traceback even if it looks like vendor (though here it's repo)
    assert "Traceback" in stdout
    assert "Exception: Boom" in stdout
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/test_prune_logs.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_prune_logs.py
git commit -m "test(scripts): add comprehensive tests for prune_logs.py"
```
