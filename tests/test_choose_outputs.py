"""The steps 6-9 outputs (db/044_choose_outputs.sql) and their contracts.

Acceptance A1, A7, A8, A9, A16 of docs/work/m5-choose-ingredients/brief.md. The good proposals are
the ones of test_choose_check.py.
"""

import copy
import json

import psycopg
import pytest

from loaders.db import connect
from tests.test_choose_check import good_proposal, good
from tests.test_choose_table import BRIEFS, build, ids_of, table_of
from tests.test_contracts import errors as contract_errors
from tests.test_step4 import sql

pytestmark = pytest.mark.stack

BIDS = ["b01", "b08", "b10", "b14", "b15", "b16", "b23"]
KINDS = {6: "yeasts", 7: "fermentables", 8: "hops", 9: "misc"}


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def outputs(conn, tbl, proposal):
    return sql(conn, "choose_outputs", tbl, proposal)


def step_inputs(tbl):
    """What the pipeline logs as each step's input: that kind's rows and the frame parts."""
    common = {"run_id": 0, "style_used": tbl["style_used"], "wanted_style": tbl["wanted_style"],
              "guidance": tbl["guidance"], "slots": tbl["slots"], "inventory_words": tbl["inventory_words"],
              "excluded": tbl["excluded"]}
    out = {n: {**common, "candidates": tbl[key]} for n, key in KINDS.items()}
    out[6].update(band=tbl["band"], targets=tbl["targets"], yeast_rules=tbl["yeast_rules"])
    out[8].update(targets=tbl["targets"])
    return out


def picks_of(out):
    yield out["step6"]["yeast"]
    if out["step6"]["souring"]:
        yield out["step6"]["souring"]
    yield from out["step7"]["fermentables"]
    yield from out["step8"]["hops"]
    yield from out["step9"]["extras"]


@pytest.mark.parametrize("bid", BIDS)
def test_outputs_use_table_rows_only(conn, bid):
    """A1/R1: every output id is a table row and its facts equal the ref row."""
    tbl = table_of(conn, bid)
    out = outputs(conn, tbl, good(conn, bid))
    assert all(p["ingredient_id"] in ids_of(tbl) for p in picks_of(out))
    for p in picks_of(out):
        name, = conn.execute("select name from ref.ingredient where id = %s", (p["ingredient_id"],)).fetchone()
        assert p["name"] == name
    for h in out["step8"]["hops"]:
        lo, hi = conn.execute("select lower(alpha_pct), upper(alpha_pct) from ref.hop where ingredient_id = %s",
                              (h["ingredient_id"],)).fetchone()
        assert (h["alpha"]["low"], h["alpha"]["high"]) == (float(lo), float(hi))
        assert float(h["alpha_pct"]) == float(lo + hi) / 2
    for f in out["step7"]["fermentables"]:
        lo, hi = conn.execute("select lower(ebc), upper(ebc) from ref.fermentable where ingredient_id = %s",
                              (f["ingredient_id"],)).fetchone()
        assert (f["ebc"]["low"], f["ebc"]["high"]) == (float(lo), float(hi))


def test_output_refuses_an_id_outside_the_table(conn):
    tbl = table_of(conn, "b01")
    outside, = conn.execute("select max(id) + 1 from ref.ingredient").fetchone()
    for key, step, fn in (("fermentables", 7, None), ("hops", 8, None), ("extras", 9, None)):
        p = good(conn, "b01")
        if not p[key]:
            continue
        p[key] = [dict(p[key][0], ingredient_id=outside)] + p[key][1:]
        with pytest.raises(psycopg.errors.RaiseException, match=f"step {step}: id {outside} is not in the candidate table"):
            outputs(conn, tbl, p)
        conn.execute("rollback")
    p = good(conn, "b01")
    p["yeast"]["main"]["ingredient_id"] = outside
    with pytest.raises(psycopg.errors.RaiseException, match=f"step 6: id {outside} is not in the candidate table"):
        outputs(conn, tbl, p)
    conn.execute("rollback")
    # a row of the wrong kind raises too
    p = good(conn, "b01")
    p["yeast"]["main"]["ingredient_id"] = tbl["hops"][0]["ingredient_id"]
    with pytest.raises(psycopg.errors.RaiseException, match="step 6: id .* is a hop, not a yeast"):
        outputs(conn, tbl, p)
    conn.execute("rollback")


@pytest.mark.parametrize("bid", BIDS)
def test_outputs_meet_contracts(conn, bid):
    tbl = table_of(conn, bid)
    out = outputs(conn, tbl, good(conn, bid))
    ins = step_inputs(tbl)
    for n in (6, 7, 8, 9):
        assert contract_errors(conn, f"step{n}.output", out[f"step{n}"]) == [], n
        assert contract_errors(conn, f"step{n}.input", ins[n]) == [], n


@pytest.mark.parametrize("bid", BIDS)
def test_every_pick_has_because_and_level(conn, bid):
    """A9: a level and a because sentence on every pick; the sentence names the product and purpose."""
    tbl = table_of(conn, bid)
    out = outputs(conn, tbl, good(conn, bid))
    for p in picks_of(out):
        assert p["level"] and p["level_because"] and p["choice"], p
        assert p["name"] in p["because"] and p["purpose"] in p["because"], p
        if p["inventory"]:
            assert p["inventory"] in p["because"]
        if p["wanted"]:
            assert p["wanted"]["item"] in p["because"]


def swap(proposal, name_ids, conn, name):
    """Replace the extra that sits in the same slot as `name` by that product."""
    wanted, = conn.execute("select id from ref.ingredient where name = %s and kind = 'misc'", (name,)).fetchone()
    for e in proposal["extras"]:
        if wanted in name_ids[e["ingredient_id"]]:
            e["ingredient_id"] = wanted
            return
    raise AssertionError(name)


def test_dose_set_by_code(conn):
    """A7, A16: b23 coffee whole beans 3.0 (feature), vanilla 0.05 (background); b24 orange peel 2.64."""
    tbl = table_of(conn, "b23")
    p = good(conn, "b23")
    swap(p, {i: s["ids"] for s in tbl["slots"] for i in s["ids"]}, conn, "Coffee, whole beans")
    extras = {e["name"]: e for e in outputs(conn, tbl, p)["step9"]["extras"]}
    assert float(extras["Coffee, whole beans"]["dose_g_per_l"]) == 3.0
    assert extras["Coffee, whole beans"]["dose_because"] == "one sourced dose"
    assert float(extras["Vanilla bean"]["dose_g_per_l"]) == 0.05
    assert "background" in extras["Vanilla bean"]["dose_because"]
    t24 = table_of(conn, "b24")
    peel = outputs(conn, t24, good(conn, "b24"))["step9"]["extras"]
    assert [(e["name"], float(e["dose_g_per_l"])) for e in peel] == [("Orange peel", 2.64)]


def test_dose_is_the_codes_not_the_proposals(conn):
    tbl = table_of(conn, "b24")
    p = good(conn, "b24")
    assert "dose_g_per_l" not in p["extras"][0]
    out = outputs(conn, tbl, p)
    assert out["step9"]["extras"][0]["dose_g_per_l"] == 2.64


def test_made_up_word_absent_rest_chosen(conn):
    """A8: a wanted word with no product is reported absent in step 9; the other picks stay."""
    b = copy.deepcopy(BRIEFS["b01"])
    b["wanted"] = b["wanted"] + [{"item": "unobtainium", "role": "background"}]
    tbl, _ = build(conn, b)
    p = good_proposal(tbl)
    assert sql(conn, "choose_check", tbl, p) == []
    out = outputs(conn, tbl, p)
    assert out["step9"]["absent"] == [{"word": "unobtainium", "kind": None,
                                       "reason": 'no product in the catalogue matches "unobtainium"'}]
    for n in (6, 7, 8):
        assert out[f"step{n}"]["absent"] == []
    assert out["step6"]["yeast"]["ingredient_id"] and out["step7"]["fermentables"] and out["step8"]["hops"]
    assert contract_errors(conn, "step9.output", out["step9"]) == []


def test_yeast_without_figure_reported(conn):
    """R5: a yeast with no attenuation figure reports overlaps null and that nothing is assumed."""
    tbl = table_of(conn, "b01")
    p = good(conn, "b01")
    row = copy.deepcopy(next(r for r in tbl["yeasts"] if r["ingredient_id"] == p["yeast"]["main"]["ingredient_id"]))
    t2 = copy.deepcopy(tbl)
    for r in t2["yeasts"]:
        if r["ingredient_id"] == row["ingredient_id"]:
            r["attenuation"] = None
            r["overlaps_band"] = None
    att = outputs(conn, t2, p)["step6"]["attenuation"]
    assert att["overlaps"] is None and att["yeast"] is None
    assert att["because"] == "no attenuation figure; not assumed"
    ok = outputs(conn, tbl, p)["step6"]["attenuation"]
    assert ok["overlaps"] is True and "reaches the band" in ok["because"]
    assert ok["band"] == {"low_pct": tbl["band"]["yeast_low_pct"], "high_pct": tbl["band"]["yeast_high_pct"]}


def test_unused_inventory_reported(conn):
    """An inventory yeast that was not used appears with why (b10 has several yeast words)."""
    tbl = table_of(conn, "b10")
    out = outputs(conn, tbl, good(conn, "b10"))
    words = {w["word"] for w in tbl["inventory_words"] if w["kind"] == "yeast" and w["fits"]}
    used = {out["step6"]["yeast"]["inventory"]}
    left = {u["word"] for u in out["step6"]["unused_inventory"]}
    assert left == words - used
