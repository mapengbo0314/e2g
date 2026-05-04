import sqlite3
import json
import os

db_path = "/Users/pengbolicious/pengbo-apps/e-2-g/local_outputs/span_landing_index_v2/harness_checkpoints.sqlite"
thread_id = "84615e58-5662-4f66-b29e-e34ac04e0c36"

if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # LangGraph stores checkpoints in a table called 'checkpoints'
    # The schema might vary, but usually it has thread_id and checkpoint data.
    try:
        cursor.execute("SELECT thread_id, checkpoint FROM checkpoints WHERE thread_id = ?", (thread_id,))
        row = cursor.fetchone()
        if row:
            print(f"Task {thread_id} found in checkpointer.")
            # We could deserialize the checkpoint to get more info, but just knowing it exists is a start.
        else:
            print(f"Task {thread_id} NOT found in checkpointer.")
    except Exception as e:
        print(f"Error querying DB: {e}")
    conn.close()
