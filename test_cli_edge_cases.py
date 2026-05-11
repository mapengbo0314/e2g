import subprocess
import os

def test_cli():
    env = os.environ.copy()
    env["GEMINI_API_KEY"] = "dummy_key"
    env["PYTHONPATH"] = "."
    
    # We will pass 'n\n' multiple times to answer Prompts.
    process = subprocess.Popen(
        ["python3", "harness/cli.py", "init", "--project-path", "./dummy_project_2", "--llm", "gemini"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True
    )
    
    # Supply some 'n's
    inputs = "n\n" * 10
    stdout, stderr = process.communicate(input=inputs)
    
    print("STDOUT:")
    print(stdout)
    print("STDERR:")
    print(stderr)
    print(f"Exit code: {process.returncode}")

test_cli()
