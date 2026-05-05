from pathlib import Path

from indexing.runtime_artifact_contract import RuntimeArtifactContract
from indexing.state import LocalState


def test_runtime_artifact_contract_uses_repo_relative_state_layout(tmp_path):
    state_dir = tmp_path / "state"
    index_state = LocalState(str(state_dir))

    index_state.write_summary("pkg/core", 3, "summary")
    index_state.write_artifact("pkg/core", 3, "{}")
    index_state.write_rootmap(3, "root map")

    contract = RuntimeArtifactContract.build(
        state_dir=state_dir,
        output_path=Path("pkg/core"),
        files_to_index=[Path("pkg/core/b.py"), Path("pkg/core/a.py")],
        epoch=3,
    )

    assert contract.output_path == "pkg/core"
    assert contract.files_to_index == ("pkg/core/a.py", "pkg/core/b.py")
    assert contract.epoch == 3
    assert contract.summary_path == str(state_dir / "pkg/core/llm_index_v3.md")
    assert contract.artifact_path == str(state_dir / "pkg/core/llm_index_v3.json")
    assert contract.root_map_path == str(state_dir / "root_map_v3.md")
    assert Path(contract.summary_path).read_text(encoding="utf-8") == "summary"
    assert Path(contract.artifact_path).read_text(encoding="utf-8") == "{}"
    assert Path(contract.root_map_path).read_text(encoding="utf-8") == "root map"


def test_runtime_artifact_contract_matches_prefix_stripped_local_state_paths(tmp_path):
    repo_root = tmp_path / "repo"
    output_path = repo_root / "pkg/core"
    state_dir = tmp_path / "state"
    index_state = LocalState(
        str(state_dir), input_prefix_to_strip=str(repo_root)
    )

    index_state.write_summary(str(output_path), 1, "summary")
    index_state.write_artifact(str(output_path), 1, "{}")
    index_state.write_rootmap(1, "root map")

    contract = RuntimeArtifactContract.build(
        state_dir=state_dir,
        output_path=output_path,
        epoch=1,
        input_prefix_to_strip=repo_root,
    )

    assert contract.output_path == "pkg/core"
    assert contract.summary_path == str(state_dir / "pkg/core/llm_index_v1.md")
    assert contract.artifact_path == str(state_dir / "pkg/core/llm_index_v1.json")
    assert contract.root_map_path == str(state_dir / "root_map_v1.md")
    assert index_state.read_summary(str(output_path), 1) == "summary"
    assert Path(contract.summary_path).exists()
    assert Path(contract.artifact_path).exists()
    assert Path(contract.root_map_path).exists()
