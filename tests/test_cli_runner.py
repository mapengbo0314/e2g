import subprocess
import pytest
from unittest.mock import patch, MagicMock
from harness.cli_runner import run_gemini_command, CLIRunnerError

def test_run_gemini_command_success():
    """Tests successful command execution."""
    mock_stdout = "gemini version 1.0.0"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout=mock_stdout,
            returncode=0
        )
        
        result = run_gemini_command(["--version"])
        
        assert result == mock_stdout
        mock_run.assert_called_once_with(
            ["gemini", "--version"],
            capture_output=True,
            text=True,
            check=True
        )

def test_run_gemini_command_file_not_found():
    """Tests handling when the gemini executable is missing."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        
        with pytest.raises(CLIRunnerError) as excinfo:
            run_gemini_command(["--version"])
        
        assert "not found in the system PATH" in str(excinfo.value)

def test_run_gemini_command_error_return_code():
    """Tests handling when the command returns a non-zero exit code."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["gemini", "invalid"],
            stderr="Error: Invalid command"
        )
        
        with pytest.raises(CLIRunnerError) as excinfo:
            run_gemini_command(["invalid"])
        
        assert "failed with exit code 1" in str(excinfo.value)
        assert "Error: Invalid command" in str(excinfo.value)
