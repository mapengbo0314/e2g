import subprocess
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "boilerplate-agent", "scripts"))
from prune_logs import prune_logs

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
        [sys.executable, "boilerplate-agent/scripts/prune_logs.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate(input=input_text)
    
    assert "venv/" not in stdout
    assert "Error: Something went wrong" in stdout
    assert "some/path/to/repo/file.py" in stdout

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
        [sys.executable, "boilerplate-agent/scripts/prune_logs.py"],
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
    assert "Exception" in stdout

def test_prune_logs_function_directly():
    input_text = "line1\nnode_modules/lib.js\nError: boom\nvenv/lib.py"
    expected = "line1\nnode_modules/lib.js\nError: boom"
    assert prune_logs(input_text) == expected

def test_prune_logs_empty_input():
    assert prune_logs("") == ""

def test_prune_logs_no_errors():
    input_text = "line1\nnode_modules/lib.js\nline2"
    # Without an error, vendor frames are kept
    assert prune_logs(input_text) == input_text
