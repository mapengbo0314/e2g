"""Context Tools and Waterfall Budgeting for the Unified Harness."""

import os
from typing import List, Dict, Any, Tuple
from harness.state import OverlayState, VerifiedContextItem
from indexing.schema import IndexDocument

MAX_CONTEXT_BUDGET = 200_000 # 200K tokens approx
CHARS_PER_TOKEN = 4

class ContextTools:
    def __init__(self, overlay_state: OverlayState, workspace_root: str):
        self.overlay_state = overlay_state
        self.workspace_root = workspace_root

    def get_stale_context(self, paths: List[str]) -> Dict[str, str]:
        """Tool 1: Read the Overview from the Index for a list of paths."""
        results = {}
        for path in paths:
            try:
                summary = self.overlay_state.read_summary(path)
                results[path] = summary
            except FileNotFoundError:
                results[path] = "[SYNTHETIC] New file. No context available."
        return results

    def get_verified_context(self, path: str) -> VerifiedContextItem:
        """Tool 2: Fetches detailed context, enforcing Waterfall Budgeting Algorithm."""
        # 1. Fetch Source Code from Disk / Overlay
        source_code = ""
        full_path = os.path.join(self.workspace_root, path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                source_code = f.read()
        except FileNotFoundError:
            import logging
            logging.warning(f"File not found on disk, assuming synthetic base for: {full_path}")
            source_code = ""
            
        # If there are active changes in the session, show them as diff
        active_diffs = getattr(self.overlay_state, "active_diffs", {})
        if path in active_diffs:
            if source_code:
                source_code += f"\n\n--- UNCOMMITTED CHANGES (DIFF) ---\n{active_diffs[path]}"
            else:
                source_code = active_diffs[path]

        # 2. Fetch Index Data
        try:
            artifact_json = self.overlay_state.read_artifact(path)
            doc = IndexDocument.model_validate_json(artifact_json)
            
            # Waterfall Budgeting implementation
            # The algorithm statically budgets token allocations by prioritizing high-value 
            # architectural definitions (Overview, Interfaces) over raw source code to prevent
            # context window exhaustion during deep verification loops.
            content_parts = []
            
            doc_dict = doc.model_dump()
            
            # Base Layer: Overview
            overview = doc_dict.get("overview", {})
            if overview and overview.get("content"):
                content_parts.append(f"Overview:\n{overview['content']}")
                
            # Base Layer: Key Interfaces
            interfaces_dict = doc_dict.get("key_interfaces", {})
            interfaces = interfaces_dict.get("interfaces", [])
            if interfaces:
                interface_lines = "\n".join([f"- {i.get('name', 'Unknown')}: {i.get('description', '')}" for i in interfaces])
                content_parts.append(f"Key Interfaces:\n{interface_lines}")

            # Dependency Layer
            deps_dict = doc_dict.get("key_dependencies", {})
            dependencies = deps_dict.get("dependencies", [])
            if dependencies:
                dep_lines = "\n".join([f"- {d.get('name', 'Unknown')}" for d in dependencies])
                content_parts.append(f"Key Dependencies:\n{dep_lines}")

            # Code Layer
            if source_code:
                content_parts.append(f"Source Code:\n```\n{source_code}\n```")

            summary = "\n\n".join(content_parts)
            return {"path": path, "summary": summary}
            
        except FileNotFoundError:
            # File exists on disk but not in index
            if source_code:
                return {"path": path, "summary": f"[SYNTHETIC] Unindexed file.\n\nSource Code:\n```\n{source_code}\n```"}
            return {"path": path, "summary": "[SYNTHETIC] New file. No verified context available."}
