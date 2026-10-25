import json
import re
import tomllib
from pathlib import Path

import pytest

from evals import workflows

ROOT = Path(__file__).resolve().parent.parent
REPO_DIR = ROOT / "n8n" / "workflows"
CONTRACTS = ROOT / "shared" / "contracts"
with (ROOT / "evals" / "recipe_briefs.toml").open("rb") as _f:
    B01 = next(b for b in tomllib.load(_f)["brief"] if b["id"] == "b01")["request"]

MODEL = "hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K"

# The sample each workflow's `Test data` sticky note must carry (plan Task 8).
SAMPLES = {
    "recipe-pipeline.json": [{
        "headers": {"content-type": "application/json"}, "params": {}, "query": {},
        "body": {"request": B01, "brief_id": "editor-b01"},
    }],
    "step-1-read-request.json": [{"run_id": 0, "request": B01, "model": MODEL, "think": False}],
    "check-contract.json": [{
        "contract": "step1.input",
        "value": {"run_id": 0, "request": B01, "model": MODEL, "think": False},
    }],
}
STEP2_BRIEF = {
    "named": "West Coast IPA", "stated": {"batch_l": 20, "abv": 6.5}, "hints": ["bitter"],
    "wanted": [], "excluded": [], "inventory": [], "unknown": [], "guidance": True,
}
SAMPLES["step-2-best-fit-style.json"] = [
    {"run_id": 0, "brief": STEP2_BRIEF, "request": B01, "guide_preference": None}
]
STEP3_STYLE = json.loads((ROOT / "tests" / "step3_sample_style.json").read_text())
SAMPLES["step-3-deviations.json"] = [{"run_id": 0, "brief": STEP2_BRIEF, "style": STEP3_STYLE}]
FX = json.loads((ROOT / "tests" / "step45_sample.json").read_text())
SAMPLES["step-0-load-profile.json"] = [{"run_id": 0, "profile_id": 1}]
SAMPLES["step-4-targets.json"] = [{
    "run_id": 0, "brief": STEP2_BRIEF, "style": STEP3_STYLE,
    "profile": FX["profile"], "deviations": FX["deviations"],
}]
SAMPLES["step-5-design-frame.json"] = [{
    "run_id": 0, "brief": STEP2_BRIEF, "profile": FX["profile"], "targets": FX["targets"],
}]
STEP69 = json.loads((ROOT / "tests" / "step69_sample.json").read_text())
SAMPLES["steps-6-9-choose-ingredients.json"] = STEP69
SAMPLES["steps-10-11-compute-and-validate.json"] = json.loads(
    (ROOT / "tests" / "step1011_sample.json").read_text())
SAMPLES["steps-6-11-one-try.json"] = json.loads((ROOT / "tests" / "step611_sample.json").read_text())
# The input contract each sample is checked against.
CONTRACT_OF = {
    "recipe-pipeline.json": "step1.input",
    "step-1-read-request.json": "step1.input",
    "check-contract.json": "step1.input",
    "step-2-best-fit-style.json": "step2.input",
    "step-3-deviations.json": "step3.input",
    "step-0-load-profile.json": "step0.input",
    "step-4-targets.json": "step4.input",
    "step-5-design-frame.json": "step5.input",
    "steps-6-9-choose-ingredients.json": "choose.input",
    "steps-10-11-compute-and-validate.json": "step10.input",
    "steps-6-11-one-try.json": "try.input",
}
STEP1_INPUT = {
    "recipe-pipeline.json": lambda s: {
        "run_id": 0, "request": s[0]["body"]["request"], "model": MODEL, "think": False},
    "step-1-read-request.json": lambda s: s[0],
    "check-contract.json": lambda s: s[0]["value"],
    "step-2-best-fit-style.json": lambda s: s[0],
    "step-3-deviations.json": lambda s: s[0],
    "step-0-load-profile.json": lambda s: s[0],
    "step-4-targets.json": lambda s: s[0],
    "step-5-design-frame.json": lambda s: s[0],
    "steps-6-9-choose-ingredients.json": lambda s: {**s[0], "temperature": 0, "seed": 42},
    "steps-10-11-compute-and-validate.json": lambda s: {k: v for k, v in s[0].items() if k != "frame"},
    "steps-6-11-one-try.json": lambda s: s[0],
}


def _repo(name: str) -> dict:
    return json.loads((REPO_DIR / name).read_text())


def _sample_in_note(name: str):
    notes = [n for n in _repo(name)["nodes"] if n["name"] == "Test data"]
    assert len(notes) == 1, "exactly one node named Test data"
    assert notes[0]["type"] == "n8n-nodes-base.stickyNote"
    blocks = re.findall(r"```json\n(.*?)```", notes[0]["parameters"]["content"], re.S)
    assert len(blocks) == 1, "exactly one json fenced block"
    return json.loads(blocks[0])


@pytest.mark.parametrize("name", SAMPLES)
def test_test_data_notes(name):
    sample = _sample_in_note(name)
    assert sample == SAMPLES[name]
    trigger = _repo(name)["nodes"][0]
    if name == "recipe-pipeline.json":
        assert not {h.lower() for h in sample[0]["headers"]} & {"authorization", "cookie", "x-api-key"}
    else:
        declared = [v["name"] for v in trigger["parameters"]["workflowInputs"]["values"]]
        optional = {"temperature", "seed"}  # step 1 defaults them; the sample leaves them out
        assert set(sample[0]) == set(declared) - optional


@pytest.mark.stack
@pytest.mark.parametrize("name", SAMPLES)
def test_test_data_meets_contracts(name):
    from loaders.db import connect

    value = STEP1_INPUT[name](_sample_in_note(name))
    schema = (CONTRACTS / f"{CONTRACT_OF[name]}.schema.json").read_text(encoding="utf-8")
    with connect() as conn:
        errors = conn.execute(
            "select extensions.jsonschema_validation_errors(%s::json, %s::json)",
            (schema, json.dumps(value)),
        ).fetchone()[0]
    assert errors == []


def test_num_ctx_matches_benchmark():
    from evals import benchmark

    nodes = {n["name"]: n for n in _repo("step-1-read-request.json")["nodes"]}
    assert f"num_ctx: {benchmark.NUM_CTX}" in nodes["Build model request"]["parameters"]["jsonOutput"]


def test_choose_num_ctx_matches_fit_test():
    from evals import fit_test

    nodes = {n["name"]: n for n in _repo("steps-6-9-choose-ingredients.json")["nodes"]}
    assert f"num_ctx: {fit_test.CHOOSE_NUM_CTX}" in nodes["Build model request"]["parameters"]["jsonOutput"]


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
    in_n8n = {workflows.file_name(w["name"]): w for w in workflows.export_all()}
    in_repo = {p.name: p for p in REPO_DIR.glob("*.json")} if REPO_DIR.exists() else {}
    assert set(in_n8n) == set(in_repo), "run python -m evals.workflows"
    for name, wf in in_n8n.items():
        repo_wf = json.loads(in_repo[name].read_text())
        assert workflows.node_graph(repo_wf) == workflows.node_graph(wf), name
