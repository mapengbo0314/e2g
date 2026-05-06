#!/usr/bin/env python3
import os
import sys
import json
import datetime
from pathlib import Path

# Threshold in days for an index to be considered stale
STALE_THRESHOLD_DAYS = 7

def main():
    script_dir = Path(__file__).parent.resolve()
    # Assuming script is in <harness>/scripts/, the harness is in repo root
    # Go up two levels to find the repo root
    repo_root = script_dir.parent.parent.resolve()
    metadata_path = repo_root / "metadata.json"

    print("=== Checking Index Freshness ===")
    
    if not metadata_path.exists():
        print(f"WARNING: metadata.json not found at {metadata_path}.")
        print("Cannot verify index freshness. Assuming fresh for now, but please run the indexer.")
        sys.exit(0)

    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    except Exception as e:
        print(f"ERROR: Could not parse metadata.json: {e}")
        sys.exit(1)

    # Support 'timestamp' (ISO 8601 or similar) or 'run_date'
    timestamp_str = metadata.get('timestamp') or metadata.get('run_date')
    if not timestamp_str:
        print("WARNING: 'timestamp' or 'run_date' field missing in metadata.json. Cannot verify freshness.")
        sys.exit(0)

    try:
        # Simple ISO parse, handles standard formats
        # E.g., '2023-10-25T14:30:00Z' or '2023-10-25'
        # Strip 'Z' for python fromisoformat compatibility in <3.11
        clean_ts = timestamp_str.replace('Z', '+00:00')
        index_date = datetime.datetime.fromisoformat(clean_ts)
        
        # Make timezone naive for easy delta comparison if needed, or just compare UTC
        now = datetime.datetime.now(datetime.timezone.utc)
        if index_date.tzinfo is None:
             now = datetime.datetime.now()
             
        delta = now - index_date
        
        if delta.days > STALE_THRESHOLD_DAYS:
            print(f"ERROR [Stale Index Gate Failed]: The indexing bundle is {delta.days} days old.")
            print(f"It was generated on {timestamp_str}.")
            print(f"I cannot safely generate or operate agents on a codebase index older than {STALE_THRESHOLD_DAYS} days.")
            print("Please re-run the indexer and try again.")
            sys.exit(1)
        else:
            print(f"SUCCESS: Index is fresh ({delta.days} days old).")
            sys.exit(0)
            
    except ValueError as e:
        print(f"WARNING: Could not parse date format in metadata.json '{timestamp_str}': {e}")
        sys.exit(0)

if __name__ == "__main__":
    main()
