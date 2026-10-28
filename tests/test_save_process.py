"""The process is saved with the recipe (Task 8 of docs/work/m7-process, db/048_save_recipe.sql).
Steps 12-15 are run on the step 10 output the validate tests build. Every insert is rolled back."""

import copy

import psycopg
import pytest

from loaders.db import connect
from tests.test_contracts import errors
from tests.test_save_recipe import new_run, step3_of
from tests.test_step4 import sql
from tests.test_validate import case, validate

pytestmark = pytest.mark.stack


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


@pytest.fixture(autouse=True)
def rolled_back(conn):
    yield
    conn.rollback()


STEPS = {}


def steps_of(conn, bid):
    """(step 10 input, step 10, step 12, 13, 14, 15, step 11) of one brief. b23's first good proposal does
    not pass step 11 (see test_save_recipe), nor does b01's: a passed step 11 is given for those, as
    only what is saved is under test."""
    if bid not in STEPS:
        inp, out, picks, frame = case(conn, bid)
        v = validate(conn, out, inp, picks, frame)
        if not v["passed"]:
            v = {"passed": True, "model_deviations": []}
        s12 = sql(conn, "step12_water", inp["profile"], inp["targets"], inp["brief"], out)
        s13 = sql(conn, "step13_mash_boil", inp["profile"], inp["targets"], out)
        s14 = sql(conn, "step14_ferment", inp["targets"], out)
        s15 = sql(conn, "step15_package", inp["targets"], out, s14)
        STEPS[bid] = (inp, out, s12, s13, s14, s15, v)
    return copy.deepcopy(STEPS[bid])


def process_of(conn, bid):
    inp, out, s12, s13, s14, s15, v = steps_of(conn, bid)
    return sql(conn, "recipe_process", out, s12, s13, s14, s15)


def save(conn, bid, process="given"):
    inp, out, s12, s13, s14, s15, v = steps_of(conn, bid)
    if process == "given":
        process = sql(conn, "recipe_process", out, s12, s13, s14, s15)
    _, run_id = new_run(conn)
    step3 = step3_of(conn, bid)
    if process is None:
        return sql(conn, "save_recipe", run_id, step3, inp["targets"], out, v), out
    return sql(conn, "save_recipe", run_id, step3, inp["targets"], out, v, process), out


def yeast_rows(conn, rid):
    return {r[0]: r[1:] for r in conn.execute(
        "select ingredient_id, raw_name, amount, unit from app.recipe_item where recipe_id = %s and usage = 'ferment'",
        [rid]).fetchall()}


def test_process_saved(conn):
    """b23: the saved process is valid against process.output and holds the step outputs."""
    rid, _ = save(conn, "b23")
    _, _, s12, s13, s14, s15, _ = steps_of(conn, "b23")
    p = conn.execute("select process from app.recipe where id = %s", [rid]).fetchone()[0]
    assert errors(conn, "process.output", p) == []
    assert p["water"] == s12 and p["mash"] == s13["mash"] and p["boil"] == s13["boil"]
    assert p["fermentation"] == s14 and p["packaging"] == s15


@pytest.mark.parametrize("bid", ["b01", "b14"])
def test_mash_and_boil_match_step10(conn, bid):
    """A7, on the saved row."""
    rid, out = save(conn, bid)
    p = conn.execute("select process from app.recipe where id = %s", [rid]).fetchone()[0]
    assert float(p["mash"]["mash_c"]) == float(out["mash_c"])
    assert float(p["boil"]["boil_min"]) == float(out["boil"]["boil_min"])
    assert p["boil"]["because"] == out["boil"]["because"]


def test_yeast_rows_from_pitch(conn):
    """A7: b01's yeast row is step 14's amount; b14's souring row has step 14's packs, and the because is in the process."""
    rid, _ = save(conn, "b01")
    _, _, _, _, s14, _, _ = steps_of(conn, "b01")
    rows = yeast_rows(conn, rid)
    assert len(rows) == len(s14["pitch"])
    for x in s14["pitch"]:
        _, amount, unit = rows[x["ingredient_id"]]
        assert (float(amount), unit) == (float(x["amount"]), x["unit"])
    assert any(unit == "g" for _, _, unit in rows.values())

    rid, _ = save(conn, "b14")
    _, _, _, _, s14, _, _ = steps_of(conn, "b14")
    rows = yeast_rows(conn, rid)
    souring = [x for x in s14["pitch"] if x["role"] == "souring"]
    assert souring and all(x["because"] for x in souring)
    for x in s14["pitch"]:
        _, amount, unit = rows[x["ingredient_id"]]
        assert (float(amount), unit) == (float(x["amount"]), x["unit"])
    p = conn.execute("select process from app.recipe where id = %s", [rid]).fetchone()[0]
    assert [x["because"] for x in p["fermentation"]["pitch"] if x["role"] == "souring"] == [x["because"] for x in souring]


@pytest.mark.parametrize("bid", ["b01", "b14"])
def test_fg_unchanged(conn, bid):
    """A11: the saved fg is step 10's."""
    rid, out = save(conn, bid)
    fg = conn.execute("select fg from app.recipe where id = %s", [rid]).fetchone()[0]
    assert float(fg) == pytest.approx(out["numbers"]["fg"], abs=0.00005)


def test_recipe_process_refuses_other_mash(conn):
    inp, out, s12, s13, s14, s15, _ = steps_of(conn, "b01")
    s13["mash"]["mash_c"] = float(out["mash_c"]) + 1
    with pytest.raises(psycopg.errors.RaiseException, match="recipe_process: mash"):
        sql(conn, "recipe_process", out, s12, s13, s14, s15)
    conn.rollback()
    inp, out, s12, s13, s14, s15, _ = steps_of(conn, "b01")
    s13["boil"]["boil_min"] = float(out["boil"]["boil_min"]) + 5
    with pytest.raises(psycopg.errors.RaiseException, match="recipe_process: boil"):
        sql(conn, "recipe_process", out, s12, s13, s14, s15)


def test_yeast_missing_from_pitch_raises(conn):
    inp, out, s12, s13, s14, s15, v = steps_of(conn, "b01")
    process = sql(conn, "recipe_process", out, s12, s13, s14, s15)
    process["fermentation"]["pitch"] = []
    _, run_id = new_run(conn)
    with pytest.raises(psycopg.errors.RaiseException, match="save_recipe: .*pitch"):
        sql(conn, "save_recipe", run_id, step3_of(conn, "b01"), inp["targets"], out, v, process)


def test_save_without_process_still_works(conn):
    """The stage D callers pass five arguments: no process, one pack per yeast as before."""
    rid, out = save(conn, "b01", process=None)
    assert conn.execute("select process from app.recipe where id = %s", [rid]).fetchone()[0] is None
    for ing, (_, amount, unit) in yeast_rows(conn, rid).items():
        assert (float(amount), unit) == (1.0, "pack")
