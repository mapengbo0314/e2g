from indexing.orchestrator import _SimpleProgressManager, LocalFileSystemManager
pm = _SimpleProgressManager("./local_outputs/e2g_blueprint_gemini", LocalFileSystemManager())
f = pm.get_progress_file(0)
print(f"Path: {f}")
import os
print(f"Exists: {os.path.exists(f)}")
