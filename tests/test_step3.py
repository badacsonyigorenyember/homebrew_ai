"""Step 3 rules in db/037_step3.sql, called directly (no pipeline).

Acceptance A2 (b05, b08, b11, b17, b18) and A6 (conflict tests) of docs/work/m3-deviations/brief.md.
"""

import json
import tomllib
from pathlib import Path

import pytest

from evals.grade import deviation_matches
from loaders.db import connect

ROOT = Path(__file__).resolve().parent.parent
BRIEFS = {b["id"]: b for b in tomllib.loads((ROOT / "evals" / "recipe_briefs.toml").read_text())["brief"]}


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


def sql(conn, fn, *args):
    """Call app.<fn>; dict and list arguments go in as jsonb."""
    marks = ", ".join("%s::jsonb" if isinstance(a, (dict, list)) else "%s" for a in args)
    params = [json.dumps(a) if isinstance(a, (dict, list)) else a for a in args]
    return conn.execute(f"select app.{fn}({marks})", params).fetchone()[0]


def numbers(conn, stated, code):
    return sql(conn, "step3_numbers", stated, code)


def conflicts(conn, hints):
    return sql(conn, "step3_conflicts", hints)


@pytest.mark.stack
def test_number_outside_is_a_deviation(conn):
    for bid, code, subject, range_text in [("b08", "5D", "IBU 50", "22–40"), ("b17", "8B", "ABV 7", ""),
                                           ("b18", "15A", "SRM 20", "")]:
        got = numbers(conn, BRIEFS[bid]["stated"], code)
        assert len(got) == 1, (bid, got)
        assert got[0]["kind"] == "number" and got[0]["subject"] == subject
        assert got[0]["from"].startswith(code) and range_text in got[0]["from"]
        assert got[0]["level"] is None and got[0]["requested_by"] == "user"
        assert deviation_matches(BRIEFS[bid]["deviations"][0], got[0])
    assert "above German Pils (5D)'s IBU range 22–40" in numbers(conn, {"ibu": 50}, "5D")[0]["because"]
    assert " below " in numbers(conn, {"ibu": 10}, "5D")[0]["because"]


@pytest.mark.stack
def test_number_inside_or_on_edge_is_not(conn):
    for bid, code in [("b01", "21A"), ("b05", "15B"), ("b14", "23A"), ("b21", "session-india-pale-ale")]:
        assert numbers(conn, BRIEFS[bid]["stated"], code) == [], bid
    assert numbers(conn, {"abv": 5.5}, "21A") == []
    assert numbers(conn, {"abv": 7.5}, "21A") == []


@pytest.mark.stack
def test_batch_is_never_a_deviation(conn):
    assert numbers(conn, {"batch_l": 500}, "21A") == []


@pytest.mark.stack
def test_style_without_range_gives_none(conn):
    assert numbers(conn, {"abv": 12}, "31B") == []


@pytest.mark.stack
def test_mismatch_carried(conn):
    from_step2 = sql(conn, "step2_best_style", brief_of(BRIEFS["b05"]), BRIEFS["b05"]["request"], None)
    got = sql(conn, "step3_mismatch", BRIEFS["b05"]["stated"], from_step2["mismatch"])
    assert len(got) == 1
    assert got[0]["kind"] == "mismatch" and "20C" in got[0]["subject"] and "ABV 4" in got[0]["subject"]
    assert deviation_matches(BRIEFS["b05"]["deviations"][0], got[0])
    assert sql(conn, "step3_mismatch", {"abv": 4}, None) == []


@pytest.mark.stack
def test_dry_vs_full_chewy_is_one_conflict(conn):
    got = conflicts(conn, BRIEFS["b11"]["hints"])
    assert len(got) == 1
    assert got[0]["kind"] == "conflict" and got[0]["subject"] == "dry vs full, chewy"
    assert got[0]["level"] is None and got[0]["requested_by"] == "user"
    assert "dry lowers mash temperature and raises attenuation" in got[0]["because"]
    assert deviation_matches(BRIEFS["b11"]["deviations"][0], got[0])


@pytest.mark.stack
def test_bitter_vs_malty(conn):
    got = conflicts(conn, ["bitter", "malty"])
    assert [d["subject"] for d in got] == ["bitter vs malty"]
    assert "BU:GU" in got[0]["because"]


@pytest.mark.stack
def test_stronger_vs_session(conn):
    got = conflicts(conn, ["stronger", "session"])
    assert [d["subject"] for d in got] == ["stronger vs session"]


@pytest.mark.stack
def test_same_side_never_conflicts(conn):
    for hints in (["dry", "crisp"], ["full", "chewy"], ["hoppy", "juicy"]):
        assert conflicts(conn, hints) == [], hints


@pytest.mark.stack
def test_unrelated_hints_do_not_conflict(conn):
    assert conflicts(conn, BRIEFS["b19"]["hints"]) == []
    assert conflicts(conn, BRIEFS["b21"]["hints"]) == []
    assert conflicts(conn, []) == []


def rate(conn, code, item, role="background"):
    return sql(conn, "rate_wanted", code, item, role)


@pytest.mark.stack
def test_out_of_style_words(conn):
    for code, item in [("18B", "rice"), ("17C", "honey"), ("19C", "lactose")]:
        assert rate(conn, code, item)["level"] == "out_of_style", (code, item)


@pytest.mark.stack
def test_in_style_words(conn):
    for code, item in [("21C", "oats"), ("1B", "rice"), ("1C", "corn"), ("31B", "honey")]:
        assert rate(conn, code, item)["level"] == "typical", (code, item)


@pytest.mark.stack
def test_best_over_products(conn):
    got = rate(conn, "26B", "abbey yeast")
    assert got["name"] == "Abbaye" and got["level"] == "typical", got


@pytest.mark.stack
def test_yeast_best_over_its_temperature_range(conn):
    got = rate(conn, "26B", "Abbey Monk Ale")
    assert got["level"] == "allowed", got
    assert any(f"{t} °C" in got["choice"] for t in range(22, 27)), got
    assert rate(conn, "26B", "M47 Belgian Abbey")["level"] == "out_of_style"


@pytest.mark.stack
def test_feature_hop_rated_late_only(conn):
    feature = rate(conn, "15B", "Citra", "feature")
    assert feature["level"] == "out_of_style" and ("whirlpool" in feature["choice"] or "dry hop" in feature["choice"]), feature
    background = rate(conn, "15B", "Citra", "background")
    assert background["level"] == "allowed" and "boil" in background["choice"], background


@pytest.mark.stack
def test_unresolved_word_is_unrated(conn):
    got = rate(conn, "21A", "unicorn tears")
    assert got["level"] is None and got["reason"]


@pytest.mark.stack
def test_style_without_envelope_is_unrated(conn):
    code = conn.execute(
        "select b.code from ref.beer_style b"
        " where not exists (select 1 from ref.style_sensory x where x.style_id = b.id and x.reviewed)"
        " and not exists (select 1 from ref.style_ingredient x where x.style_id = b.id and x.reviewed)"
        " order by b.code limit 1"
    ).fetchone()
    assert code, "no style without an envelope found"
    got = rate(conn, code[0], "rice")
    assert got["level"] is None and "envelope" in got["reason"], got
