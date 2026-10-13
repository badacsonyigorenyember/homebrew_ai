"""Step 2 picking function app.step2_best_style in db/022_step2.sql, called directly (no pipeline).

Acceptance A1 (SQL level), A2, A3, A4, A5 of docs/work/m2-best-fit-style/brief.md.
"""

import json
import tomllib
from pathlib import Path

import pytest

from loaders.db import connect

ROOT = Path(__file__).resolve().parent.parent
BRIEFS = {b["id"]: b for b in tomllib.loads((ROOT / "evals" / "recipe_briefs.toml").read_text())["brief"]}
CONTRACT = json.loads((ROOT / "shared" / "contracts" / "step2.output.schema.json").read_text())


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def brief_of(b):
    """A step 1 brief built from the expected fields of a test brief."""
    return {
        "named": b["named"] or None, "stated": b["stated"], "hints": b["hints"], "wanted": b["wanted"],
        "excluded": b["excluded"], "inventory": b["inventory"], "unknown": [], "guidance": b["guidance"],
    }


def run(conn, brief, request, guide=None):
    return conn.execute(
        "select app.step2_best_style(%s::jsonb, %s, %s)", (json.dumps(brief), request, guide)
    ).fetchone()[0]


def pick(conn, b, guide=None, request=None):
    return run(conn, brief_of(b), request if request is not None else b["request"], guide)


@pytest.mark.stack
def test_b05_irish_stout_with_mismatch(conn):
    out = pick(conn, BRIEFS["b05"])
    assert out["style"]["code"] == "15B"
    assert out["mismatch"]["chosen"].startswith("15B")
    assert out["mismatch"]["named"].startswith("20C")
    assert "ABV 8.0–12.0" in out["mismatch"]["range"]


@pytest.mark.stack
def test_sweet_words_move_the_pick_to_16a(conn):
    """Same numbers as b05, but the flavour words 'sweet' and 'lactose' make it a Sweet Stout."""
    brief = {**brief_of(BRIEFS["b05"]), "unknown": ["sweet", "lactose"]}
    out = run(conn, brief, "I'd like a sweet 4 % imperial stout with lactose.")
    assert out["style"]["code"] == "16A"


@pytest.mark.stack
def test_b12_honey_forward_is_a_honey_specialty(conn):
    out = pick(conn, BRIEFS["b12"])
    assert out["style"]["code"] in ("31B", "specialty-honey-beer")
    assert out["alt_styles"][0] == "18A"


@pytest.mark.stack
def test_pastry_stout_keeps_the_ba_style(conn):
    """A BA style paired with a BJCP catch-all (30D) is not swapped."""
    brief = {"named": "pastry stout", "stated": {"abv": 10}, "hints": [], "wanted": ["vanilla", "tonka bean", "lactose"],
             "excluded": [], "inventory": [], "unknown": [], "guidance": True}
    out = run(conn, brief, "A strong 10 % ABV pastry stout with vanilla and tonka bean and lots of lactose.")
    assert out["style"]["code"] == "dessert-stout-or-pastry-beer"
    assert "30D" in out["reason"]


@pytest.mark.stack
def test_koelsch_request_still_returns_5b(conn):
    brief = {**brief_of(BRIEFS["b01"]), "named": "Koelsch", "stated": {}, "hints": []}
    assert run(conn, brief, "A Koelsch please.")["style"]["code"] == "5B"


@pytest.mark.stack
def test_b19_some_honey_keeps_wee_heavy(conn):
    out = pick(conn, BRIEFS["b19"])
    assert out["style"]["code"] == "17C"
    assert "31B" not in [out["style"]["code"], *out["alt_styles"]]


@pytest.mark.stack
def test_b17_number_outside_is_not_a_mismatch(conn):
    out = pick(conn, BRIEFS["b17"])
    assert out["style"]["code"] == "8B"
    assert out["mismatch"] is None


@pytest.mark.stack
def test_briefs_reach_the_bar(conn):
    misses, passed = [], 0
    for b in BRIEFS.values():
        out = pick(conn, b)
        got = [out["style"]["code"], *out["alt_styles"]] if out["style"] else []
        ok = b["style"] in got if b["id"] <= "b20" else (out["style"] or {}).get("code") == b["style"]
        passed += ok and b["id"] <= "b20"
        if not ok:
            misses.append(f"{b['id']} wants {b['style']}, got {got}, top 3 {out['candidates'][:3]}")
    assert passed >= 18 and not [m for m in misses if m[:3] in ("b21", "b22")], "\n".join(misses)
    assert passed >= 18, "\n".join(misses)


@pytest.mark.stack
def test_same_input_same_output(conn):
    for b in BRIEFS.values():
        assert pick(conn, b) == pick(conn, b), b["id"]


@pytest.mark.stack
def test_ba_only_field_b01(conn):
    out = pick(conn, BRIEFS["b01"], guide="ba")
    assert out["style"]["guide"] == "BA"
    assert "webhook" in out["guide_reason"]


@pytest.mark.stack
def test_ba_only_from_request_b01(conn):
    out = pick(conn, BRIEFS["b01"], request=BRIEFS["b01"]["request"] + " Use a BA style.")
    assert out["style"]["guide"] == "BA"
    assert "request" in out["guide_reason"]


@pytest.mark.stack
def test_field_beats_request_text(conn):
    out = pick(conn, BRIEFS["b01"], guide="any", request=BRIEFS["b01"]["request"] + " Use a BA style.")
    assert out["style"]["code"] == "21A"


@pytest.mark.stack
def test_bjcp_only_b21(conn):
    assert pick(conn, BRIEFS["b21"], guide="bjcp")["style"]["guide"] == "BJCP"


@pytest.mark.stack
def test_ba_winner_with_pair_returns_bjcp(conn):
    brief = {**brief_of(BRIEFS["b01"]), "named": "German-Style Koelsch", "stated": {}, "hints": []}
    out = run(conn, brief, "A German-Style Koelsch please.")
    assert out["style"]["code"] == "5B"
    assert "style pair" in out["guide_reason"]
    assert run(conn, brief, "A German-Style Koelsch please.", "ba")["style"]["code"] == "german-style-koelsch"


@pytest.mark.stack
def test_equal_names_go_to_bjcp(conn):
    assert pick(conn, BRIEFS["b03"])["style"]["code"] == "16B"


@pytest.mark.stack
def test_no_beer_is_unknown(conn):
    brief = {"named": None, "stated": {}, "hints": [], "wanted": [], "excluded": [], "inventory": [],
             "unknown": [], "guidance": True}
    out = run(conn, brief, "something nice")
    assert out["style"] is None
    assert out["unknown_reason"]


@pytest.mark.stack
def test_output_meets_contract(conn):
    brief = {"named": None, "stated": {}, "hints": [], "wanted": [], "excluded": [], "inventory": [],
             "unknown": [], "guidance": True}
    outs = [pick(conn, b) for b in BRIEFS.values()] + [run(conn, brief, "something nice")]
    for out in outs:
        errs = conn.execute(
            "select coalesce(extensions.jsonschema_validation_errors(%s::json, %s::json), '{}')",
            (json.dumps(CONTRACT), json.dumps(out)),
        ).fetchone()[0]
        assert errs == [], (out, errs)
