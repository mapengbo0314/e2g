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
                results[path] = "No indexed summary available for this path."
        return results

    def get_verified_context(self, path: str) -> VerifiedContextItem:
        """Tool 2: Fetches detailed context, enforcing Waterfall Budgeting Algorithm."""
        # 1. Fetch Source Code from Disk / Overlay
        source_code = ""
        full_path = os.path.join(self.workspace_root, path)
        try:
            if os.path.isdir(full_path):
                # For directories, we list children if no index exists
                children = os.listdir(full_path)
                source_code = f"Directory contents: {', '.join(children)}"
            elif os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    source_code = f.read()
            else:
                source_code = ""
        except Exception as e:
            import logging
            logging.error(f"Error reading path {full_path}: {e}")
            source_code = f"Error reading file: {str(e)}"
            
        # If there are active changes in the session, show them as diff
        active_diffs = getattr(self.overlay_state, "active_diffs", {})
        if path in active_diffs:
            if source_code:
                source_code += f"\n\n--- UNCOMMITTED CHANGES (DIFF) ---\n{active_diffs[path]}"
            else:
                source_code = active_diffs[path]

        # 2. Fetch Index Data
        try:
            artifact_json = None
            current_path = path
            
            # Try to find an artifact for the exact path, or traverse up to find a directory artifact
            while current_path and current_path != ".":
                try:
                    artifact_json = self.overlay_state.read_artifact(current_path)
                    if artifact_json:
                        break
                except FileNotFoundError:
                    # Move up one directory level
                    parent = os.path.dirname(current_path)
                    if parent == current_path:
                        break
                    current_path = parent
            
            if not artifact_json:
                raise FileNotFoundError(f"No artifact found for {path} or its parents.")

            doc = IndexDocument.model_validate_json(artifact_json)
            
            content_parts = []
            doc_dict = doc.model_dump()
            
            # Base Layer: Overview
            overview = doc_dict.get("overview", {})
            if overview and overview.get("content"):
                content_parts.append(f"Semantic Overview:\n{overview['content']}")
                
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
                return {"path": path, "summary": f"Unindexed file context.\n\nSource Code:\n```\n{source_code}\n```"}
            return {"path": path, "summary": "New file. No verified context available."}
