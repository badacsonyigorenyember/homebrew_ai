"""A validated recipe is saved as rows (Task 6 of docs/work/m6-compute-validate, db/048_save_recipe.sql).

The step 10 and 11 outputs are the ones tests/test_validate.py builds. Every insert is rolled back.
"""

import copy
import json

import psycopg
import pytest

from loaders.db import connect
from tests.test_compute import step10_input
from tests.test_step4 import BRIEFS, brief_of, sql
from tests.test_validate import case, validate

pytestmark = pytest.mark.stack

# A5: how far a recomputation from the saved rows may be from the saved numbers.
RECOMPUTE_TOLERANCES = {"og": 0.001, "ibu": 1, "srm": 1}


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


@pytest.fixture(autouse=True)
def rolled_back(conn):
    yield
    conn.rollback()


def step3_of(conn, bid):
    b = BRIEFS[bid]
    brief = brief_of(b)
    style = sql(conn, "step2_best_style", brief, b["request"], None)
    return sql(conn, "step3_deviations", brief, style)


def new_run(conn):
    brief_id = conn.execute(
        "insert into app.brief (request_text, brief) values ('test', '{}'::jsonb) returning id").fetchone()[0]
    run_id = conn.execute("insert into app.run (brief_id, model) values (%s, 'test') returning id",
                          [brief_id]).fetchone()[0]
    return brief_id, run_id


def saved(conn, bid, step3_bid=None, passed_override=None, step11=None):
    """Validate brief `bid` (it passes), then save it. The step 3 deviations may come from another
    brief, to test every kind. Returns (recipe id, run id, step 10, step 11)."""
    inp, out, picks, frame = case(conn, bid)
    v = step11 or validate(conn, out, inp, picks, frame)
    _, run_id = new_run(conn)
    step3 = step3_of(conn, step3_bid or bid)
    rid = sql(conn, "save_recipe", run_id, step3, inp["targets"], out, v)
    return rid, run_id, out, v


def items_of(conn, rid):
    return conn.execute("select ingredient_id, raw_name, usage, time_min, pct, amount, unit "
                        "from app.recipe_item where recipe_id = %s order by id", [rid]).fetchall()


def test_rows_match_step10(conn):
    """b23: one item per fermentable, hop, yeast and extra; amounts as step 10 gave them (A7: coffee
    is its dose times 20 L). b23's first good proposal does not pass step 11, and what is saved is
    under test here, so a passed step 11 is given."""
    rid, _, out, _ = saved(conn, "b23", step11={"passed": True, "model_deviations": []})
    rows = items_of(conn, rid)
    assert len(rows) == (len(out["fermentables"]) + len(out["hops"]) + len(out["yeasts"]) + len(out["extras"]))
    by_id = {}
    for r in rows:
        by_id.setdefault(r[0], []).append(r)
    for f in out["fermentables"]:
        r = by_id[f["ingredient_id"]][0]
        assert r[6] == "kg" and abs(float(r[5]) - f["kg"]) < 0.0006 and abs(float(r[4]) - float(f["pct"])) < 0.006
        assert r[2] == f["usage"] and r[1] == f["name"] and r[3] is None
    for h in out["hops"]:
        r = by_id[h["ingredient_id"]][0]
        assert r[6] == "g" and abs(float(r[5]) - h["g"]) < 0.0006 and r[3] == h["minutes"]
        assert abs(float(r[4]) - float(h["share_pct"])) < 0.006 and r[2] == h["usage"]
    for y in out["yeasts"]:
        r = by_id[y["ingredient_id"]][0]
        assert (r[6], float(r[5]), r[2]) == ("pack", 1.0, "ferment")
    for e in out["extras"]:
        r = by_id[e["ingredient_id"]][0]
        assert (r[6], r[2]) == ("g", e["usage"]) and abs(float(r[5]) - e["dose_g_per_l"] * 20) < 0.0006
    assert all(r[0] is not None for r in rows)


def hop_alpha(conn, ingredient_id):
    lo, hi = conn.execute("select lower(alpha_pct), upper(alpha_pct) from ref.hop where ingredient_id = %s",
                          [ingredient_id]).fetchone()
    return float((lo + hi) / 2) if hi is not None and lo is not None else float(lo if lo is not None else hi)


def recompute(conn, rid):
    """A5: OG, IBU and SRM from the saved recipe_item rows with s1's functions and the ref values.
    Reused by tests/test_pipeline.py."""
    recipe_batch, eff = conn.execute("select batch_l, efficiency_pct from app.recipe where id = %s", [rid]).fetchone()
    profile = sql(conn, "step0_profile", None)
    volume, eff = float(recipe_batch), float(eff)
    grist, hops = [], []
    for ing, _name, usage, minutes, _pct, amount, unit in items_of(conn, rid):
        f = conn.execute("select extract_dbfg_pct, app.ebc_mid(ebc), role from ref.fermentable where ingredient_id = %s",
                         [ing]).fetchone()
        if f is not None and unit == "kg":
            grist.append({"kg": float(amount), "extract_pct": float(f[0]), "ebc": float(f[1] or 0),
                          "mashed": f[2] != "sugar"})
        elif unit == "g" and conn.execute("select 1 from ref.hop where ingredient_id = %s", [ing]).fetchone():
            hops.append({"g": float(amount), "alpha_pct": hop_alpha(conn, ing), "minutes": float(minutes or 0),
                         "usage": usage})
    boil = max([h["minutes"] for h in hops if h["usage"] == "boil"] or [60])
    losses = float(profile["losses_l"])

    def calc(expr, *args):
        return float(conn.execute(f"select {expr}", [json.dumps(a) if isinstance(a, list) else a for a in args]).fetchone()[0])

    og = calc("app.og(%s::jsonb, %s::numeric, %s::numeric)", grist, eff, volume)
    preboil = calc("app.preboil_volume(%s::numeric, %s::numeric, %s::numeric, %s::numeric)",
                   volume, boil, float(profile["boil_off_l_h"]), losses)
    boil_sg = calc("app.boil_gravity(%s::numeric, %s::numeric, %s::numeric)", og, volume + losses, preboil)
    ibu = calc("app.ibu(%s::jsonb, %s::numeric, %s::numeric)", hops, boil_sg, volume)
    srm = calc("app.srm(app.grist_mcu(%s::jsonb, %s::numeric))", grist, volume)
    return {"og": og, "ibu": ibu, "srm": srm}


@pytest.mark.parametrize("bid", ["b08", "b14"])
def test_recompute_from_saved_rows(conn, bid):
    rid, _, out, _ = saved(conn, bid)
    og, ibu, srm = conn.execute("select og, ibu, srm from app.recipe where id = %s", [rid]).fetchone()
    mine = recompute(conn, rid)
    assert abs(mine["og"] - float(og)) <= RECOMPUTE_TOLERANCES["og"]
    assert abs(mine["ibu"] - float(ibu)) <= RECOMPUTE_TOLERANCES["ibu"]
    assert abs(mine["srm"] - float(srm)) <= RECOMPUTE_TOLERANCES["srm"]
    assert abs(float(ibu) - out["numbers"]["ibu"]) <= 0.05 and abs(float(og) - out["numbers"]["og"]) <= 0.00005


def deviations(conn, rid):
    return conn.execute("select kind, subject, level, requested_by, note from app.recipe_deviation "
                        "where recipe_id = %s order by id", [rid]).fetchall()


@pytest.mark.parametrize("bid, kind", [("b05", "mismatch"), ("b11", "conflict"), ("b08", "number"),
                                       ("b16", "ingredient")])
def test_every_step3_deviation_saved(conn, bid, kind):
    """A8: each step 3 deviation of the brief is a user row; a level only on an ingredient one.
    The recipe is b08's; only the deviation rows are under test."""
    rid, *_ = saved(conn, "b08", step3_bid=bid)
    expected = step3_of(conn, bid)["deviations"]
    got = deviations(conn, rid)
    assert len(got) == len(expected) and kind in {g[0] for g in got}
    for d, g in zip(expected, got):
        assert (g[0], g[1], g[2], g[3], g[4]) == (d["kind"], d["subject"], d.get("level"), "user", d["because"])
        assert (g[2] is not None) == (g[0] == "ingredient")


def test_model_deviation_saved(conn):
    inp, out, picks, frame = case(conn, "b08")
    v = validate(conn, out, inp, picks, frame)
    v["model_deviations"] = [{"subject": "Black Malt", "level": "changes_style", "note": "the pick darkens it"}]
    rid, *_ = saved(conn, "b08", step11=v)
    rows = [d for d in deviations(conn, rid) if d[3] == "model"]
    assert rows == [("ingredient", "Black Malt", "changes_style", "model", "the pick darkens it")]


def test_refuses_a_failed_validation(conn):
    inp, out, picks, frame = case(conn, "b08")
    v = validate(conn, out, inp, picks, frame)
    v["passed"] = False
    before = conn.execute("select count(*) from app.recipe").fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException, match="did not pass"):
        saved(conn, "b08", step11=v)
    conn.rollback()
    assert conn.execute("select count(*) from app.recipe").fetchone()[0] == before


def test_refuses_a_run_without_a_brief(conn):
    inp, out, picks, frame = case(conn, "b08")
    v = validate(conn, out, inp, picks, frame)
    run_id = conn.execute("insert into app.run (model) values ('test') returning id").fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException, match="no brief"):
        sql(conn, "save_recipe", run_id, step3_of(conn, "b08"), inp["targets"], out, v)


def test_run_points_to_recipe(conn):
    rid, run_id, *_ = saved(conn, "b08")
    assert conn.execute("select recipe_id from app.run where id = %s", [run_id]).fetchone()[0] == rid


def test_snapshot_fields(conn):
    rid, run_id, out, _ = saved(conn, "b08")
    inp = step10_input(conn, "b08")
    row = conn.execute("select brief_id, style_id, status, batch_l, efficiency_pct, targets, og, fg, abv, ibu, srm, "
                       "calc_version from app.recipe where id = %s", [rid]).fetchone()
    brief_id = conn.execute("select brief_id from app.run where id = %s", [run_id]).fetchone()[0]
    code = conn.execute("select code from ref.beer_style where id = %s", [row[1]]).fetchone()[0]
    assert row[0] == brief_id and code == inp["targets"]["style"]["code"] and row[2] == "draft"
    assert float(row[3]) == out["batch"]["volume_l"] and float(row[4]) == out["batch"]["efficiency_pct"]
    assert row[5] == inp["targets"] and row[11] == "maths-1"
    assert abs(float(row[6]) - out["numbers"]["og"]) < 0.00006 and abs(float(row[9]) - out["numbers"]["ibu"]) < 0.06
