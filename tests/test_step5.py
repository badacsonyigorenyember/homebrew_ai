"""Step 5 (design frame) in db/041_step5.sql.

Acceptance A8, A9, A10 of docs/work/m4-targets-blueprint/brief.md, at SQL level.
"""

import json
from pathlib import Path

import pytest

from loaders.db import connect
from tests.test_step4 import BRIEFS, brief_of, sql, step4

ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.stack


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def step5(conn, b):
    """Step 1's expected brief through steps 2, 3, 0, 4 and 5."""
    s4 = step4(conn, b)
    profile = sql(conn, "step0_profile", None)
    return sql(conn, "step5_frame", brief_of(b), profile, s4)


@pytest.fixture(scope="module")
def step4s(conn):
    return {bid: step4(conn, b) for bid, b in BRIEFS.items()}


@pytest.fixture(scope="module")
def frames(conn):
    return {bid: step5(conn, b) for bid, b in BRIEFS.items()}


def names(refs):
    return [(r["name"], r["role"], None if r["max_pct"] is None else float(r["max_pct"])) for r in refs]


def slot(frame, item):
    return next(s for s in frame["slots"] if s["item"] == item)


def test_slots(frames):
    """A8: each wanted word has a slot with its products, role and max_pct."""
    cases = {
        "b02": ("oats", ("Flaked Oats", "adjunct", 30)),
        "b06": ("rice", ("Flaked Rice", "adjunct", 40)),
        "b16": ("rice", ("Flaked Rice", "adjunct", 40)),
        "b07": ("corn", ("Flaked Corn", "adjunct", 20)),
        "b12": ("honey", ("Honey", "sugar", 20)),
        "b19": ("honey", ("Honey", "sugar", 20)),
        "b20": ("lactose", ("Lactose", "sugar", 10)),
    }
    for bid, (item, expected) in cases.items():
        got = names(slot(frames[bid], item)["refs"])
        assert expected in got, (bid, item, got)
    for bid, frame in frames.items():
        assert [(s["item"], s["wanted_role"]) for s in frame["slots"]] == [
            (w["item"], w["role"]) for w in BRIEFS[bid]["wanted"]], bid


def test_excluded_and_inventory(frames):
    assert [(e["word"], names(e["refs"])[0][0]) for e in frames["b08"]["excluded"]] == [("Saaz", "Saaz")]
    got = {e["word"]: e for e in frames["b16"]["excluded"]}
    assert {"Citra", "Mosaic"} <= set(got)
    assert all(e["refs"] and e["refs"][0]["kind"] == "hop" for e in got.values())
    for bid in ("b10", "b15"):
        assert [i["word"] for i in frames[bid]["inventory"]] == BRIEFS[bid]["inventory"], bid
    candi = next(i for i in frames["b10"]["inventory"] if i["word"] == "dark candi sugar")
    assert candi["refs"] == [] and candi["from"] == "not in the catalogue"
    assert all(i["from"] == "request" for i in frames["b15"]["inventory"])
    assert all(i["refs"] for i in frames["b15"]["inventory"])


def test_profile_inventory_joins_the_frame(conn):
    """Profile inventory rows follow the brief's words, refs from the row's ingredient_id."""
    b = BRIEFS["b02"]
    profile = sql(conn, "step0_profile", None)
    profile["inventory"] = [
        {"raw_name": "my oats", "ingredient_id": 3393, "amount": 1, "unit": "kg"},
        {"raw_name": "mystery malt", "ingredient_id": None, "amount": 2, "unit": "kg"},
    ]
    frame = sql(conn, "step5_frame", brief_of(b), profile, step4(conn, b))
    assert [(i["word"], i["from"]) for i in frame["inventory"]] == [("my oats", "profile"), ("mystery malt", "profile")]
    assert names(frame["inventory"][0]["refs"]) == [("Flaked Oats", "adjunct", 30)]
    assert frame["inventory"][1]["refs"] == []


def intents(frame):
    return " | ".join(i["intent"] for i in frame["intents"])


def test_intents(frames):
    assert "late and dry hop share" in intents(frames["b02"])
    assert "lower-attenuation" in intents(frames["b03"]) and "oats" in intents(frames["b03"])
    assert "high-attenuation" in intents(frames["b06"]) and "sugar at most 10 %" in intents(frames["b06"])
    assert "kilned share" in intents(frames["b09"])
    assert "attenuation" not in " ".join(i["knob"] for i in frames["b11"]["intents"])
    for frame in frames.values():
        assert all(i["from"] == "hint" and i["source"] for i in frame["intents"])


def test_rules_equal_formulation_rules(conn, frames):
    rows = [{"rule": r, "checked": c, "sentence": s}
            for r, c, s in conn.execute("select rule, checked, sentence from app.formulation_rules()").fetchall()]
    limits = conn.execute("select app.formulation_limits()").fetchone()[0]
    for bid, frame in frames.items():
        assert frame["rules"]["rows"] == rows, bid
        assert frame["limits"]["values"] == limits, bid
        assert "db/031" in frame["rules"]["from"] and "db/031" in frame["limits"]["from"]


ALLOWED_NUMBERS = {"ingredient_id", "max_pct", "needed_pct", "low_pct", "high_pct", "mash_c",
                   "yeast_middle_pct", "yeast_low_pct", "yeast_high_pct"}


def numbers_outside(node, key=""):
    """Keys that hold a number but are not on the allowed list; `limits` is skipped (R10)."""
    found = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "limits":
                continue
            found += numbers_outside(v, k)
    elif isinstance(node, list):
        for v in node:
            found += numbers_outside(v, key)
    elif isinstance(node, (int, float)) and not isinstance(node, bool) and key not in ALLOWED_NUMBERS:
        found.append(key)
    return found


def test_no_ratio_numbers(frames):
    """A8: no grist, no percentages of the recipe, no split."""
    def keys(node):
        if isinstance(node, dict):
            for k, v in node.items():
                yield k
                yield from keys(v)
        elif isinstance(node, list):
            for v in node:
                yield from keys(v)
    for bid, frame in frames.items():
        assert numbers_outside(frame) == [], bid
        bad = [k for k in keys({k: v for k, v in frame.items() if k != "limits"})
               if k == "pct" or k == "grist" or "split" in k]
        assert bad == [], bid


def test_needed_attenuation(conn, frames, step4s):
    """A9: needed = 100 x (OG - FG)/(OG - 1); the yeast band, run through app.mash_attenuation, gives it back."""
    for bid, frame in frames.items():
        t = step4s[bid]["targets"]
        att = frame["attenuation"]
        og, fg = t["og"]["value"], t["fg"]["value"]
        if og is None or fg is None:
            assert att["needed_pct"] is None and att["from"] == "none", bid
            continue
        needed = 100 * (float(og) - float(fg)) / (float(og) - 1)
        assert abs(float(att["needed_pct"]) - needed) <= 0.01, bid
        mid = float(att["yeast_middle_pct"])
        back = conn.execute("select app.mash_attenuation(numrange(%s::numeric, %s::numeric), %s::numeric)",
                            [mid - 3, mid + 3, step4s[bid]["mash_c"]["value"]]).fetchone()[0]
        assert abs(float(back) - needed) <= 0.01, (bid, back, needed)
        assert float(att["low_pct"]) - 0.01 <= float(att["needed_pct"]) <= float(att["high_pct"]) + 0.01, bid
        assert att["from"] == "derived" and "Troester" in att["because"], bid


def test_every_value_has_from(frames):
    for bid, frame in frames.items():
        for key in ("slots", "excluded", "inventory", "intents"):
            for item in frame[key]:
                assert item["from"], (bid, key, item)
        assert frame["rules"]["from"] and frame["limits"]["from"] and frame["attenuation"]["from"], bid
        assert frame["attenuation"]["because"], bid


def test_same_input_same_output(conn, frames):
    for bid, b in BRIEFS.items():
        assert step5(conn, b) == frames[bid], bid


def test_output_meets_contract(conn, frames):
    schema = json.loads((ROOT / "shared" / "contracts" / "step5.output.schema.json").read_text())
    for bid, frame in frames.items():
        errs = conn.execute(
            "select coalesce(extensions.jsonschema_validation_errors(%s::json, %s::json), '{}')",
            (json.dumps(schema), json.dumps(frame))).fetchone()[0]
        assert errs == [], (bid, errs)
