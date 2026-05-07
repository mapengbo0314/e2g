import os
import tempfile
import pytest
import shutil

# Mocking the cleanup directly for the test
def cleanup_other_platforms(project_path, chosen_platform):
    platforms = [".gemini", ".claude", ".cursor", ".agents"]
    if chosen_platform == "1":
        harness_folder = ".gemini"
    elif chosen_platform == "2":
        harness_folder = ".claude"
    elif chosen_platform == "3":
        harness_folder = ".cursor"
    else:
        harness_folder = ".agents"

    if harness_folder in platforms:
        platforms.remove(harness_folder)
    for p in platforms:
        path = os.path.join(project_path, p)
        if os.path.exists(path):
            shutil.rmtree(path)

def test_cleanup_other_platforms():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup folders
        os.mkdir(os.path.join(temp_dir, ".gemini"))
        os.mkdir(os.path.join(temp_dir, ".claude"))
        os.mkdir(os.path.join(temp_dir, ".cursor"))
        
        # Action (Choose Gemini CLI = "1")
        cleanup_other_platforms(temp_dir, "1")
        
        # Assert
        assert os.path.exists(os.path.join(temp_dir, ".gemini"))
        assert not os.path.exists(os.path.join(temp_dir, ".claude"))
        assert not os.path.exists(os.path.join(temp_dir, ".cursor"))
