"""Step 11: validation and what to retry (Task 5 of docs/work/m6-compute-validate, db/047_validate.sql).

Inputs are the ones Task 4 builds: step 4, steps 6-9 from the first good proposal, step 10.
"""

import copy
import json

import pytest

from loaders.db import connect
from tests.test_choose_check import good_proposal
from tests.test_choose_table import rows_of, table_of
from tests.test_compute import compute, step10_input
from tests.test_contracts import errors as contract_errors
from tests.test_step4 import BRIEFS, brief_of, sql

pytestmark = pytest.mark.stack

CACHE: dict = {}


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def frame_of(conn, inp):
    return sql(conn, "step5_frame", inp["brief"], inp["profile"], inp["targets"])


def picks_of(tbl):
    """Every row of the table, self-picked when it is neither wanted nor inventory."""
    return [{"ingredient_id": r["ingredient_id"], "name": r["name"],
             "self_picked": not (r["wanted"] or r["inventory"])} for r in rows_of(tbl)]


def validate(conn, out, inp, picks, frame=None, brief=None, targets=None):
    return sql(conn, "step11_validate", out, brief or inp["brief"], targets or inp["targets"],
               frame if frame is not None else frame_of(conn, inp), picks)


def case(conn, bid):
    """(step 10 input, step 10 output, picks, frame) of one brief."""
    if bid not in CACHE:
        inp = step10_input(conn, bid)
        CACHE[bid] = (inp, compute(conn, inp), picks_of(table_of(conn, bid)), frame_of(conn, inp))
    inp, out, picks, frame = CACHE[bid]
    return copy.deepcopy(inp), copy.deepcopy(out), copy.deepcopy(picks), copy.deepcopy(frame)


def kinds(v):
    return sorted(f["kind"] for f in v["failures"])


@pytest.mark.parametrize("bid", ["b08", "b14"])
def test_good_recipe_passes(conn, bid):
    inp, out, picks, frame = case(conn, bid)
    v = validate(conn, out, inp, picks, frame)
    assert v["passed"] is True and v["failures"] == [] and v["feedback"] == [] and v["banned"] == []
    assert all(t["met"] for t in v["targets"])


def test_target_miss_is_a_numbers_failure(conn):
    inp, out, picks, frame = case(conn, "b08")
    targets = copy.deepcopy(inp["targets"])
    targets["targets"]["srm"]["value"] = float(targets["targets"]["srm"]["value"]) + 3
    v = validate(conn, out, inp, picks, frame, targets=targets)
    assert v["passed"] is False and kinds(v) == ["numbers"]
    f = v["failures"][0]
    assert f["subject"] == "srm" and f["limit"] == 1 and f["value"] is not None and f["ban"] is None
    assert "SRM" in f["text"] and v["feedback"] == [f["text"]] and v["banned"] == []
    assert [t["met"] for t in v["targets"] if t["key"] == "srm"] == [False]


def test_unreached_colour_is_named_in_the_srm_text(conn):
    inp, out, picks, frame = case(conn, "b08")
    out["colour"] = {**out["colour"], "reached": False, "because": "the dark malt is at its limit"}
    targets = copy.deepcopy(inp["targets"])
    targets["targets"]["srm"]["value"] = float(targets["targets"]["srm"]["value"]) + 3
    v = validate(conn, out, inp, picks, frame, targets=targets)
    assert "the dark malt is at its limit" in v["failures"][0]["text"]


def test_stated_numbers(conn):
    inp, out, picks, frame = case(conn, "b08")  # stated batch 10 L and 50 IBU
    v = validate(conn, out, inp, picks, frame)
    assert {s["key"]: s["met"] for s in v["stated"]} == {"batch_l": True, "ibu": True}
    # a stated ABV the recipe does not give: one numbers failure, named as stated
    brief = copy.deepcopy(inp["brief"])
    brief["stated"]["abv"] = round(float(out["numbers"]["abv"]) + 1, 2)
    v = validate(conn, out, inp, picks, frame, brief=brief)
    assert [f["subject"] for f in v["failures"]] == ["stated abv"] and v["failures"][0]["kind"] == "numbers"
    # and one it does give
    brief["stated"]["abv"] = round(float(out["numbers"]["abv"]), 1)
    assert validate(conn, out, inp, picks, frame, brief=brief)["passed"] is True
    # a batch that is not the stated one
    brief = copy.deepcopy(inp["brief"])
    brief["stated"]["batch_l"] = 23
    v = validate(conn, out, inp, picks, frame, brief=brief)
    assert [f["subject"] for f in v["failures"]] == ["stated batch_l"]
    assert [s["met"] for s in v["stated"] if s["key"] == "batch_l"] == [False]


def test_target_that_is_stated_fails_once(conn):
    inp, out, picks, frame = case(conn, "b08")
    out["numbers"]["ibu"] = float(out["numbers"]["ibu"]) + 10
    v = validate(conn, out, inp, picks, frame)
    assert [f["subject"] for f in v["failures"]] == ["ibu"]
    assert [s["met"] for s in v["stated"] if s["key"] == "ibu"] == [False]


def test_a_number_that_cannot_be_computed_fails(conn):
    inp, out, picks, frame = case(conn, "b08")
    out["numbers"].update(abv=None, fg=None, attenuation_pct=None)
    v = validate(conn, out, inp, picks, frame)
    f = next(f for f in v["failures"] if f["subject"] == "abv")
    assert f["value"] is None and "cannot be computed" in f["text"] and "attenuation" in f["text"]


def pale_and_roast(conn):
    return [r[0] for r in conn.execute(
        "select i.id from ref.ingredient i where (i.producer, i.name) in "
        "(('Viking Malt', 'Pale Ale Malt'), ('Viking Malt', 'Black Malt')) order by i.name desc")]


def test_rule_failure_names_rule_value_limit(conn):
    """A grist with 20 % roast fails rule 3; it is a rule failure and bans nothing."""
    inp, out, picks, frame = case(conn, "b08")
    pale, black = pale_and_roast(conn)
    out["recipe"]["fermentables"] = [
        {"ingredient_id": pale, "pct": 80, "purpose": "base"}, {"ingredient_id": black, "pct": 20, "purpose": "colour"}]
    v = validate(conn, out, inp, picks, frame)
    rule3 = [f for f in v["failures"] if f["kind"] == "rule" and f["subject"] == "rule 3"]
    assert rule3 and rule3[0]["text"].startswith("Rule 3") and rule3[0]["value"] is not None
    assert rule3[0]["limit"] is not None and rule3[0]["ban"] is None


def test_rule_9_og_and_abv_lines_are_skipped_when_og_moved(conn):
    """Step 10 moves OG on purpose, so rule 9's lines on the OG and ABV targets do not fail a recipe."""
    inp, out, picks, frame = case(conn, "b08")
    raw = sql(conn, "check_recipe", {**out["recipe"], "targets": {**out["recipe"]["targets"], "og": 1.040}})
    assert any(r["rule"] == 9 and r["status"] == "fail" for r in raw["results"])
    out["recipe"]["targets"]["og"] = 1.040
    v = validate(conn, out, inp, picks, frame)
    assert not [f for f in v["failures"] if f["subject"] == "rule 9"]


def out_of_style_pick(conn, out, inp):
    """A fermentable that step 11's style rating (totals off) calls out_of_style in this recipe,
    swapped in for the first one. No hop is out_of_style in the styles tried: hops are rated by
    their totals, which step 11 leaves out."""
    for (fid,) in conn.execute("select ingredient_id from ref.fermentable order by ingredient_id").fetchall():
        recipe = copy.deepcopy(out["recipe"])
        recipe["fermentables"][0]["ingredient_id"] = fid
        try:
            fit = sql(conn, "style_fit_recipe", recipe, None, False)
        except Exception:
            conn.execute("rollback")
            continue
        line = next(l for l in fit["lines"] if l["ingredient_id"] == fid)
        if line["level"] in ("out_of_style", "changes_style"):
            return fid, recipe, line
    pytest.fail("no out-of-style fermentable found")


def test_self_pick_out_of_style_is_banned(conn):
    inp, out, picks, frame = case(conn, "b08")
    hop, recipe, line = out_of_style_pick(conn, out, inp)
    out["recipe"] = recipe
    picks.append({"ingredient_id": hop, "name": line["name"], "self_picked": True})
    v = validate(conn, out, inp, picks, frame)
    fails = [f for f in v["failures"] if f["kind"] == "pick"]
    assert [f["ban"] for f in fails] == [hop] and line["name"] in fails[0]["text"]
    assert [b["ingredient_id"] for b in v["banned"]] == [hop] and v["banned"][0]["why"]
    assert v["feedback"][v["failures"].index(fails[0])].endswith("(banned for the next try)")


def test_unrated_style_bans_nothing(conn):
    """A style with no reviewed envelope rates no line (level null): no pick failure, no ban (found in the pipeline run)."""
    inp, out, picks, frame = case(conn, "b08")
    out["recipe"]["style_code"] = "session-beer"
    v = validate(conn, out, inp, picks, frame)
    assert all(ln["level"] is None for ln in v["style_fit"]["lines"])
    assert [f for f in v["failures"] if f["kind"] == "pick"] == [] and v["banned"] == []
    assert contract_errors(conn, "step11.output", v) == []


def test_wanted_pick_is_never_banned(conn):
    inp, out, picks, frame = case(conn, "b08")
    hop, recipe, line = out_of_style_pick(conn, out, inp)
    out["recipe"] = recipe
    picks.append({"ingredient_id": hop, "name": line["name"], "self_picked": False})
    v = validate(conn, out, inp, picks, frame)
    assert not [f for f in v["failures"] if f["kind"] == "pick"] and v["banned"] == []


def test_user_ibu_does_not_ban_hops(conn):
    """b08 states 50 IBU, which rates its hops out_of_style with the totals left in."""
    inp, out, picks, frame = case(conn, "b08")
    assert float(inp["targets"]["targets"]["ibu"]["value"]) == 50
    v = validate(conn, out, inp, picks, frame)
    assert not [f for f in v["failures"] if f["kind"] == "pick"] and v["banned"] == []


def test_excluded_product_fails(conn):
    inp, out, picks, frame = case(conn, "b16")
    lupomax, = conn.execute(
        "select id from ref.ingredient where kind = 'hop' and name ilike 'Citra%LUPOMAX%' order by id limit 1").fetchone()
    out["recipe"]["hops"][0]["ingredient_id"] = lupomax
    picks.append({"ingredient_id": lupomax, "name": "Citra LUPOMAX", "self_picked": True})
    v = validate(conn, out, inp, picks, frame)
    fails = [f for f in v["failures"] if f["kind"] == "pick" and f["ban"] == lupomax]
    assert fails and "excluded" in fails[0]["text"]
    assert lupomax in [b["ingredient_id"] for b in v["banned"]]
    # the brewer's own pick is not banned
    picks[-1]["self_picked"] = False
    v = validate(conn, out, inp, picks, frame)
    assert [f for f in v["failures"] if f["kind"] == "pick"] and v["banned"] == []


def test_impossible_target_cannot_pass(conn):
    """A4 (SQL half): OG 1.080 at 2 % ABV is met by no yeast in the table."""
    b = {"request": "A blonde ale at OG 1.080 and only 2 % ABV, 20 litres.", "named": "blonde ale",
         "stated": {"batch_l": 20, "og": 1.08, "abv": 2}, "hints": [], "wanted": [], "excluded": [],
         "inventory": [], "guidance": True}
    brief = brief_of(b)
    style = sql(conn, "step2_best_style", brief, b["request"], None)
    profile = sql(conn, "step0_profile", None)
    targets = sql(conn, "step4_targets", brief, style, profile, sql(conn, "step3_deviations", brief, style))
    frame = sql(conn, "step5_frame", brief, profile, targets)
    tbl = sql(conn, "choose_table", brief, style, targets, frame)
    # the style it lands in has no envelope, so no row has a level: rate them all typical to pick by
    rated = copy.deepcopy(tbl)
    for r in rows_of(rated):
        r["best_level"] = r["best_level"] or "typical"
        for c in r.get("levels") or []:
            c["level"] = c["level"] or "typical"
    steps = sql(conn, "choose_outputs", tbl, good_proposal(rated))
    picks = picks_of(tbl)
    tried = 0
    for y in tbl["yeasts"]:
        if y["type"] not in ("ale", "lager", "kveik"):
            continue
        choice = conn.execute("select label from app.ingredient_choices(%s, null) where dose ? 'ferm_c' limit 1",
                              [y["ingredient_id"]]).fetchone()
        if choice is None:
            continue
        step6 = copy.deepcopy(steps["step6"])
        step6["yeast"].update(ingredient_id=y["ingredient_id"], name=y["name"], choice=choice[0])
        out = sql(conn, "step10_compute", profile, targets, step6, steps["step7"], steps["step8"],
                  steps["step9"], brief)
        v = sql(conn, "step11_validate", out, brief, targets, frame, picks)
        assert v["passed"] is False, y["name"]
        subjects = {f["subject"] for f in v["failures"]}
        assert "abv" in subjects or "stated abv" in subjects, y["name"]
        assert out["numbers"]["attenuation_pct"] is None or "rule 10" in subjects, y["name"]
        tried += 1
    assert tried > 5


def test_guidance_off_gives_model_deviations(conn):
    """b18 has style guidance off: a self-picked out_of_style line is a deviation, not a failure."""
    inp, out, picks, frame = case(conn, "b18")
    assert inp["targets"]["guidance"] is False
    hop, recipe, line = out_of_style_pick(conn, out, inp)
    out["recipe"] = recipe
    picks.append({"ingredient_id": hop, "name": line["name"], "self_picked": True})
    v = validate(conn, out, inp, picks, frame)
    assert not [f for f in v["failures"] if f["kind"] == "pick"] and v["banned"] == []
    dev = [d for d in v["model_deviations"] if d["subject"] == line["name"]]
    assert dev and dev[0]["level"] == line["level"] and dev[0]["note"]


@pytest.mark.parametrize("bid", ["b08", "b14"])
def test_output_meets_contract(conn, bid):
    inp, out, picks, frame = case(conn, bid)
    step11_in = {"run_id": 0, "try": 1, "brief": inp["brief"], "targets": inp["targets"], "frame": frame,
                 "picks": picks, "step10": out}
    assert contract_errors(conn, "step11.input", step11_in) == []
    assert contract_errors(conn, "step11.output", validate(conn, out, inp, picks, frame)) == []
    # a failing one meets it too
    out["numbers"]["abv"] = None
    assert contract_errors(conn, "step11.output", validate(conn, out, inp, picks, frame)) == []
