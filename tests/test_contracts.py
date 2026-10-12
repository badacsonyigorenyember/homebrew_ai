"""Step contracts: the JSON Schema files in shared/contracts/ (R5)."""

import json
from pathlib import Path

import pytest

from loaders.db import connect

CONTRACTS = Path(__file__).resolve().parent.parent / "shared" / "contracts"
NAMES = [f"step{n}.{side}" for n in range(4) for side in ("input", "output")]

# Each output's slot for absent / unknown / conflict: (property, how the schema must allow it).
# "null" = the property's type allows null; "array" = it is an array; "enum:<v>" = enum holds <v>.
ABSENT_SLOTS = {
    "step0.output": [("water.ca", "null"), ("inventory.ingredient_id", "null")],
    "step1.output": [("named", "null"), ("unknown", "array")],
    "step2.output": [("style", "null"), ("unknown_reason", "null"), ("mismatch", "null")],
    "step3.output": [("deviations.kind", "enum:conflict"), ("unrated", "array")],
}


def load(name: str) -> dict:
    return json.loads((CONTRACTS / f"{name}.schema.json").read_text())


def _walk(schema: dict, path: str) -> dict:
    """Find a property by dotted path; an array is entered through its `items`."""
    node = schema
    for part in path.split("."):
        if node.get("type") == "array":
            node = node["items"]
        node = node["properties"][part]
    return node


def _allows_null(node: dict) -> bool:
    t = node.get("type")
    return t == "null" or (isinstance(t, list) and "null" in t)


def test_contract_files_complete():
    assert sorted(p.name for p in CONTRACTS.glob("*.json")) == sorted(
        f"{n}.schema.json" for n in NAMES
    )
    for name in NAMES:
        schema = load(name)
        for key in ("$schema", "title", "description"):
            assert schema.get(key), f"{name}: {key} missing"
        assert schema["type"] == "object"
        assert set(schema["required"]) == set(schema["properties"]), name
        assert schema["additionalProperties"] is False, name
        if name.endswith(".input"):
            assert "run_id" in schema["required"], name


def test_every_output_has_an_absent_slot():
    assert set(ABSENT_SLOTS) == {n for n in NAMES if n.endswith(".output")}
    for name, slots in ABSENT_SLOTS.items():
        schema = load(name)
        for path, how in slots:
            node = _walk(schema, path)
            if how == "null":
                assert _allows_null(node), f"{name}: {path} must allow null"
            elif how == "array":
                assert node["type"] == "array", f"{name}: {path} must be an array"
            else:
                assert how.split(":", 1)[1] in node["enum"], f"{name}: {path}"


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def errors(conn, name: str, value) -> list:
    return conn.execute(
        "select coalesce(extensions.jsonschema_validation_errors(%s::json, %s::json), '{}')",
        (json.dumps(load(name)), json.dumps(value)),
    ).fetchone()[0]


@pytest.mark.stack
def test_schemas_valid(conn):
    for name in NAMES:
        ok = conn.execute(
            "select extensions.jsonschema_is_valid(%s::json)", (json.dumps(load(name)),)
        ).fetchone()[0]
        assert ok, name


BRIEF = {
    "named": None, "stated": {}, "hints": [], "wanted": ["rice"], "excluded": [],
    "inventory": [], "unknown": ["xyzzy"], "guidance": True,
}
STYLE = {"id": 1, "guide": "bjcp", "code": "1A", "name": "American Light Lager"}
STEP2_OUT = {
    "style": None, "unknown_reason": "no style fits", "alt_styles": [], "candidates": [],
    "scores": {"hint:dry": 0.5}, "mismatch": None, "guide_reason": "no signal",
}
GOOD = {
    "step0.input": {"run_id": 1, "profile_id": None},
    "step0.output": {
        "batch_l": 20, "efficiency_pct": 72, "boil_off_l_h": 3.5, "losses_l": 2,
        "grain_abs_l_kg": 1.0,
        "water": {"ca": None, "mg": 5, "na": None, "so4": None, "cl": None, "hco3": 40},
        "units": "metric",
        "inventory": [{"raw_name": "mystery malt", "ingredient_id": None, "amount": 1, "unit": "kg"}],
    },
    "step1.input": {"run_id": 1, "request": "a dry stout"},
    "step1.output": BRIEF,
    "step2.input": {"run_id": 1, "brief": BRIEF, "guide_preference": "any"},
    "step2.output": STEP2_OUT,
    "step3.input": {"run_id": 1, "brief": BRIEF, "style": STEP2_OUT},
    "step3.output": {
        "deviations": [{
            "kind": "conflict", "subject": "dry vs full", "from": "bone dry vs chewy",
            "level": None, "requested_by": "user", "because": "hints disagree",
        }],
        "unrated": ["mystery malt"], "guidance": False,
    },
}
BAD = [
    ("step1.input", {"run_id": 1, "request": ""}),
    ("step1.output", {**BRIEF, "hints": ["funky"]}),
    ("step1.output", {**BRIEF, "stated": {"abv": 45}}),
    ("step1.output", {**BRIEF, "wanted": ["oats", "oats"]}),
    ("step2.output", {k: v for k, v in STEP2_OUT.items() if k != "unknown_reason"}),
    ("step3.output", {**GOOD["step3.output"], "deviations": [
        {**GOOD["step3.output"]["deviations"][0], "kind": "typo"}]}),
]


@pytest.mark.stack
@pytest.mark.parametrize("name", NAMES)
def test_good_examples(conn, name):
    assert errors(conn, name, GOOD[name]) == []


@pytest.mark.stack
@pytest.mark.parametrize("name,value", BAD, ids=[f"{n}-{i}" for i, (n, _) in enumerate(BAD)])
def test_bad_examples(conn, name, value):
    assert len(errors(conn, name, value)) >= 1
