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
        "named": b["named"] or None, "stated": b["stated"], "hints": b["hints"], "wanted": [dict(w) for w in b["wanted"]],
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
def test_smoke_porter_keeps_the_ba_style(conn):
    """A BA style paired with a BJCP catch-all (smoke-porter, 32A) is not swapped."""
    brief = {"named": "smoke porter", "stated": {}, "hints": [], "wanted": [{"item": "smoked malt", "role": "background"}],
             "excluded": [], "inventory": [], "unknown": [], "guidance": True}
    out = run(conn, brief, "A smoke porter with smoked malt.")
    assert out["style"]["code"] == "smoke-porter"
    assert "32A" in out["reason"]


@pytest.mark.stack
def test_b05_picks_15b_and_lists_no_pale_lager(conn):
    """Step 1's real b05 brief also carries the hint 'session' (from 'a few pints'). The pick is
    15B and a stout request must not list pale lagers (3A, 1A) as alternatives."""
    brief = {**brief_of(BRIEFS["b05"]), "hints": ["session"]}
    out = run(conn, brief, BRIEFS["b05"]["request"])
    assert out["style"]["code"] == "15B"
    assert not {"3A", "1A"} & set(out["alt_styles"])
    assert out["alt_styles"]


@pytest.mark.stack
@pytest.mark.parametrize(
    "named, stated, request_text, mismatch_word",
    [
        ("barleywine", {"abv": 5}, "a 5% barleywine", "Barleywine"),
        ("tripel", {"abv": 4}, "a 4% tripel", "Tripel"),
        ("kolsch", {"abv": 8}, "an 8% kolsch", "Kolsch"),
        ("doppelbock", {"abv": 4}, "a 4% doppelbock", "Doppelbock"),
        ("berliner weisse", {"abv": 8}, "an 8% berliner weisse", "Berliner Weisse"),
    ],
)
def test_number_that_rules_out_the_named_style_gives_a_pick_and_a_mismatch(
        conn, named, stated, request_text, mismatch_word):
    """The fitting style often shares no word with the named one; it must still be picked."""
    brief = {"named": named, "stated": stated, "hints": [], "wanted": [], "excluded": [],
             "inventory": [], "unknown": [], "guidance": True}
    out = run(conn, brief, request_text)
    assert out["style"] is not None
    assert mismatch_word in out["mismatch"]["named"]


@pytest.mark.stack
def test_unnamed_style_is_not_a_mismatch(conn):
    """b21 with BJCP only: nobody names English IPA, so the mismatch must not name it."""
    out = pick(conn, BRIEFS["b21"], guide="bjcp")
    assert out["mismatch"] is None or "12C" not in out["mismatch"]["named"]


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
    """Same check as the G2 grader: the picked style (not an alternative) is the brief's style or
    one of its accepted alt_styles."""
    misses, passed = [], 0
    for b in BRIEFS.values():
        out = pick(conn, b)
        got = (out["style"] or {}).get("code")
        ok = got in [b["style"], *b["alt_styles"]]
        passed += ok and b["id"] <= "b20"
        if not ok:
            misses.append(f"{b['id']} wants {b['style']} {b['alt_styles']}, got {got}, top 3 {out['candidates'][:3]}")
    assert passed >= 18 and not [m for m in misses if m[:3] in ("b21", "b22")], "\n".join(misses)


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
