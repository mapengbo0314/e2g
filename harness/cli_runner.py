import subprocess
import sys

class CLIRunnerError(Exception):
    """Exception raised when a CLI command fails."""
    pass

def run_gemini_command(args: list[str]) -> str:
    """
    Executes a gemini command and returns the STDOUT.
    
    Raises:
        CLIRunnerError: If the command fails or the executable is not found.
    """
    cmd = ["gemini"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except FileNotFoundError:
        error_msg = "The 'gemini' executable was not found in the system PATH."
        print(error_msg, file=sys.stderr)
        raise CLIRunnerError(error_msg)
    except subprocess.CalledProcessError as e:
        error_msg = f"Command '{' '.join(cmd)}' failed with exit code {e.returncode}: {e.stderr.strip()}"
        print(error_msg, file=sys.stderr)
        raise CLIRunnerError(error_msg) from e
