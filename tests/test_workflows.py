from pathlib import Path

import pytest

from evals import workflows

REPO_DIR = Path(__file__).resolve().parent.parent / "n8n" / "workflows"


def test_shape_drops_volatile_fields():
    wf = {
        "id": "abc",
        "name": "Demo",
        "nodes": [{"name": "A"}],
        "connections": {},
        "settings": {"executionOrder": "v1"},
        "createdAt": "2026-10-12",
        "updatedAt": "2026-10-12",
        "versionId": "v1",
        "shared": [{"role": "owner"}],
        "pinData": {"A": []},
    }
    assert workflows.shape(wf) == {
        "id": "abc",
        "name": "Demo",
        "nodes": [{"name": "A"}],
        "connections": {},
        "settings": {"executionOrder": "v1"},
    }


def test_file_name():
    assert workflows.file_name("Step 1 · read request") == "step-1-read-request.json"
    assert workflows.file_name("  Recipe pipeline!! ") == "recipe-pipeline.json"


@pytest.mark.stack
def test_repo_files_match_n8n():
    import json

    in_n8n = {workflows.file_name(w["name"]): w for w in workflows.export_all()}
    in_repo = {p.name: p for p in REPO_DIR.glob("*.json")} if REPO_DIR.exists() else {}
    assert set(in_n8n) == set(in_repo), "run python -m evals.workflows"
    for name, wf in in_n8n.items():
        repo_wf = json.loads(in_repo[name].read_text())
        assert workflows.node_graph(repo_wf) == workflows.node_graph(wf), name
