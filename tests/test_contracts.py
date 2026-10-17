"""Step contracts: the JSON Schema files in shared/contracts/ (R5)."""

import json
from pathlib import Path

import pytest

from loaders.db import connect

CONTRACTS = Path(__file__).resolve().parent.parent / "shared" / "contracts"
NAMES = [f"step{n}.{side}" for n in range(5) for side in ("input", "output")]
NAMES += [f"formulation_check.{side}" for side in ("input", "output")]

# Each output's slot for absent / unknown / conflict: (property, how the schema must allow it).
# "null" = the property's type allows null; "array" = it is an array; "enum:<v>" = enum holds <v>.
ABSENT_SLOTS = {
    "step0.output": [("water.ca", "null"), ("inventory.ingredient_id", "null")],
    "step1.output": [("named", "null"), ("unknown", "array")],
    "step2.output": [("style", "null"), ("unknown_reason", "null"), ("mismatch", "null")],
    "step3.output": [("deviations.kind", "enum:conflict"), ("unrated", "array")],
    "step4.output": [("targets.og.value", "null"), ("conflicts", "array")],
    "formulation_check.output": [("results.status", "enum:unknown"), ("numbers.fg", "null")],
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
        optional = {"temperature", "seed"} if name == "step1.input" else set()
        assert set(schema["required"]) == set(schema["properties"]) - optional, name
        assert schema["additionalProperties"] is False, name
        if name.startswith("step") and name.endswith(".input"):
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
    "named": None, "stated": {}, "hints": [], "wanted": [{"item": "rice", "role": "background"}], "excluded": [],
    "inventory": [], "unknown": ["xyzzy"], "guidance": True,
}
STYLE = {"id": 1, "guide": "BJCP", "code": "1A", "name": "American Light Lager"}
STEP2_OUT = {
    "style": None, "unknown_reason": "no style fits", "alt_styles": [], "candidates": [],
    "scores": {"hint:dry": 0.5}, "mismatch": None, "guide_reason": "no signal", "reason": "no style fits",
}
CHECK_IN = {
    "style_code": "18A", "guidance": True, "stated": {"abv": 5.2},
    "targets": {"og": 1.050, "fg": 1.011, "abv": 5.2, "ibu": 30, "srm": 5},
    "batch": {"volume_l": 20, "efficiency_pct": 72, "boil_off_l_h": 4, "losses_l": 2},
    "mash_c": 66, "boil_min": 60,
    "fermentables": [{"ingredient_id": 1, "pct": 100, "purpose": "base malt"}],
    "hops": [{"ingredient_id": 2, "usage": "boil", "minutes": 60, "purpose": "bittering", "g": 20}],
    "yeast": {"ingredient_id": 3, "ferm_c": 18, "purpose": "clean fermentation"},
}
CHECK_OUT = {
    "calc_version": "maths-1",
    "numbers": {"og": 1.05, "fg": None, "abv": None, "srm": 4.1, "ibu": None,
                "attenuation_pct": None, "missing": ["ref.yeast.attenuation_pct"]},
    "results": [{
        "rule": 10, "status": "unknown", "message": "Rule 10: not checked, missing ref.yeast.attenuation_pct.",
        "failures": [], "missing": ["ref.yeast.attenuation_pct"],
    }, {
        "rule": 3, "status": "fail", "message": "Rule 3: too dark.",
        "failures": [{"text": "Rule 3: too dark.", "items": [{"ingredient_id": 7, "name": "Black Malt"}],
                      "value": 18, "limit": 15}],
        "missing": [],
    }],
}
GOOD_PROFILE = {
    "batch_l": 20, "efficiency_pct": 72, "boil_off_l_h": 3.5, "losses_l": 2,
    "grain_abs_l_kg": 1.0,
    "water": {"ca": None, "mg": 5, "na": None, "so4": None, "cl": None, "hco3": 40},
    "units": "metric",
    "inventory": [{"raw_name": "mystery malt", "ingredient_id": None, "amount": 1, "unit": "kg"}],
}


def _value(v, frm, because="because"):
    return {"value": v, "from": frm, "because": because}


STEP4_OUT = {
    "style": {"code": "18A", "name": "Blonde Ale", "from": "chosen", "because": "step 2's style"},
    "batch_l": _value(20, "profile"),
    "targets": {
        "og": _value(1.0475, "midpoint"), "fg": _value(1.0125, "midpoint"),
        "abv": _value(4.6, "derived"), "ibu": _value(None, "none"), "srm": _value(4.5, "hint"),
    },
    "mash_c": _value(66.5, "midpoint"),
    "knobs": [{"knob": "srm", "direction": 1, "hints": "darker", "intent": None, "source": "unsourced"}],
    "conflicts": [{
        "kind": "conflict", "subject": "dry vs full", "from": "bone dry vs chewy",
        "level": None, "requested_by": "user", "because": "hints disagree",
    }],
    "guidance": True,
}
GOOD = {
    "formulation_check.input": CHECK_IN,
    "formulation_check.output": CHECK_OUT,
    "step0.input": {"run_id": 1, "profile_id": None},
    "step0.output": GOOD_PROFILE,
    "step1.input": {"run_id": 1, "request": "a dry stout", "model": "gemma4:12b", "think": False},
    "step1.output": BRIEF,
    "step2.input": {"run_id": 1, "brief": BRIEF, "request": "a dry stout", "guide_preference": "any"},
    "step2.output": STEP2_OUT,
    "step3.input": {"run_id": 1, "brief": BRIEF, "style": STEP2_OUT},
    "step3.output": {
        "deviations": [{
            "kind": "conflict", "subject": "dry vs full", "from": "bone dry vs chewy",
            "level": None, "requested_by": "user", "because": "hints disagree",
        }],
        "unrated": ["mystery malt"], "guidance": False,
    },
    "step4.input": {"run_id": 1, "brief": BRIEF, "style": STEP2_OUT, "profile": GOOD_PROFILE, "deviations": {}},
    "step4.output": STEP4_OUT,
}
BAD = [
    ("formulation_check.input", {k: v for k, v in CHECK_IN.items() if k != "mash_c"}),
    ("formulation_check.input", {**CHECK_IN, "hops": [{**CHECK_IN["hops"][0], "usage": "mash"}]}),
    ("formulation_check.input", {**CHECK_IN, "stated": {"colour": 5}}),
    ("formulation_check.output", {**CHECK_OUT, "results": [{**CHECK_OUT["results"][0], "status": "maybe"}]}),
    ("formulation_check.output", {k: v for k, v in CHECK_OUT.items() if k != "numbers"}),
    ("step1.input", {"run_id": 1, "request": "", "model": "gemma4:12b", "think": False}),
    ("step1.input", {"run_id": 1, "request": "a dry stout", "model": "", "think": False}),
    ("step1.input", {"run_id": 1, "request": "a dry stout", "model": "gemma4:12b"}),
    ("step1.input", {"run_id": 1, "request": "a dry stout", "model": "gemma4:12b", "think": False, "seed": 1.5}),
    ("step1.output", {**BRIEF, "hints": ["funky"]}),
    ("step1.output", {**BRIEF, "stated": {"abv": 45}}),
    ("step1.output", {**BRIEF, "wanted": [{"item": "oats", "role": "background"}] * 2}),
    ("step1.output", {**BRIEF, "wanted": ["oats"]}),
    ("step1.output", {**BRIEF, "wanted": [{"item": "oats"}]}),
    ("step1.output", {**BRIEF, "wanted": [{"item": "oats", "role": "main"}]}),
    ("step1.output", {**BRIEF, "wanted": [{"item": "oats", "role": "feature", "why": "x"}]}),
    ("step2.input", {"run_id": 1, "brief": BRIEF, "guide_preference": "any"}),
    ("step2.input", {"run_id": 1, "brief": BRIEF, "request": "a dry stout", "guide_preference": "both"}),
    ("step2.output", {k: v for k, v in STEP2_OUT.items() if k != "unknown_reason"}),
    ("step3.output", {**GOOD["step3.output"], "deviations": [
        {**GOOD["step3.output"]["deviations"][0], "kind": "typo"}]}),
    ("step4.output", {**STEP4_OUT, "batch_l": _value(20, "guess")}),
    ("step4.output", {**STEP4_OUT, "mash_c": {"value": 66.5, "from": "midpoint"}}),
]


@pytest.mark.stack
@pytest.mark.parametrize("name", NAMES)
def test_good_examples(conn, name):
    assert errors(conn, name, GOOD[name]) == []


@pytest.mark.stack
@pytest.mark.parametrize("name,value", BAD, ids=[f"{n}-{i}" for i, (n, _) in enumerate(BAD)])
def test_bad_examples(conn, name, value):
    assert len(errors(conn, name, value)) >= 1


@pytest.mark.stack
def test_step2_input_allows_null_guide(conn):
    value = {**GOOD["step2.input"], "guide_preference": None}
    assert errors(conn, "step2.input", value) == []


@pytest.mark.stack
def test_step1_input_allows_temperature_and_seed(conn):
    value = {**GOOD["step1.input"], "temperature": 0.8, "seed": 1}
    assert errors(conn, "step1.input", value) == []
