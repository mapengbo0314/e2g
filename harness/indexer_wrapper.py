import shutil
import sys
import json
import os
import subprocess
import datetime

def check_indxr_installed() -> bool:
    """Verifies that indxr is available on the system PATH."""
    if shutil.which("indxr") is None:
        print("ERROR: 'indxr' is not installed or not on your PATH.")
        print("Please install indxr (e.g., cargo install indxr) to use harness init.")
        sys.exit(1)
    return True

def acquire_context(project_path: str, bundle_override: str | None = None) -> str:
    """Runs indxr to generate the index or uses the provided bundle."""
    if bundle_override:
        if not os.path.exists(bundle_override):
            print(f"ERROR: Provided bundle not found at {bundle_override}")
            sys.exit(1)
        index_path = bundle_override
    else:
        print(f"Running indxr on {project_path}...")
        index_path = os.path.join(project_path, "INDEX.json")
        try:
            subprocess.run(
                ["indxr", "index", "-f", "json", "-o", index_path],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            print(f"ERROR: indxr failed: {e.stderr}")
            sys.exit(1)
            
    # Generate metadata.json for the freshness gate
    metadata_path = os.path.join(project_path, "metadata.json")
    metadata = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_bundle": index_path,
        "engine": "indxr"
    }
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    return index_path
