import subprocess
import sys
import os

def test_prune_logs_basic():
    input_text = """
some/path/to/repo/file.py:10: in function
    code_here()
Error: Something went wrong
venv/lib/python3.9/site-packages/some_lib.py:20: in lib_func
    lib_code()
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
