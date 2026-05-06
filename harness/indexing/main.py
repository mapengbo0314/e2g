"""Main entry point for re-indexing the codebase."""

import argparse
import logging
import os
import sys

from indexing import orchestrator
from indexing import llm_indexer
from indexing import planner
from indexing import state
from indexing import work_unit
from indexing.fs_manager import RealFsManager
from harness.prompter import UniversalLlmPrompter

def run_reindex(index_dir: str):
    logging.basicConfig(level=logging.INFO)
    
    fs_manager = RealFsManager()
    index_state = state.State(state_dir=index_dir, fs_manager=fs_manager)
    work_unit_storage = work_unit.LocalWorkUnitStorage(
        storage_dir=index_dir, fs_manager=fs_manager
    )
    
    # We use the UniversalLlmPrompter as the default for indexing
    # This expects GOOGLE_API_KEY to be set.
    prompter = UniversalLlmPrompter()
    indexer = llm_indexer.LlmIndexer(llm_prompter=prompter, index_state=index_state)
    
    # The default planner walks the directory tree
    plan_instance = planner.FileSystemPlanner(
        root_dir=".", # Start from current workspace root
        fs_manager=fs_manager
    )
    
    orch = orchestrator.Orchestrator(
        planner_instance=plan_instance,
        indexer=indexer,
        num_epochs=1, # Default to 1 epoch for quick re-indexing
        root_map_dir=index_dir,
        index_state=index_state,
        work_unit_storage=work_unit_storage,
        fs_manager=fs_manager,
        bundle_name="harness_reindex"
    )
    
    logging.info(f"Starting re-indexing for directory: . into {index_dir}")
    orch.run()
    logging.info("Re-indexing complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unified Harness Re-indexer")
    parser.add_argument("--index_dir", type=str, default=".index_state", help="Path to index directory")
    args = parser.parse_args()
    
    run_reindex(args.index_dir)
