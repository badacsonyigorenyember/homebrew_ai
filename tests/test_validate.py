"""Step 11: validation and what to retry (Task 5 of docs/work/m6-compute-validate, db/047_validate.sql).

Inputs are the ones Task 4 builds: step 4, steps 6-9 from the first good proposal, step 10.
"""

import copy
import re
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
    assert f["subject"] == "srm" and f["limit"] == 2 and f["value"] is not None and f["ban"] is None
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


def test_mash_move_lets_rule_10_pass(conn):
    """Task 9b: b09's G6 picks fail rule 10 at the 66.5 C mash; with the mash move step 11 passes."""
    from tests.test_compute import b09_picks
    inp = b09_picks(conn)
    out = compute(conn, inp)
    assert out["mash_c"] > 68.3
    picks = [{"ingredient_id": f["ingredient_id"], "name": f["name"], "self_picked": False}
             for f in out["fermentables"]]
    v = validate(conn, out, inp, picks, frame_of(conn, inp))
    assert v["passed"] is True, v["failures"]
    # the same grist at the unmoved mash is the failure G6 saw
    inp["targets"]["mash_c"]["from"] = "hint"
    stays = compute(conn, inp)
    v = validate(conn, stays, inp, picks, frame_of(conn, inp))
    assert v["passed"] is False and any("Rule 10" in f["text"] for f in v["failures"])


# --- Task 9c: a failed try tells the retry what to change (app.step11_fix, app.attenuation_for_fg) ---

from tests import test_compute as tc  # noqa: E402

MUNICH1 = ("Weyermann", "Munich Malt Type 1")
CARAAMBER = ("Weyermann", "Caraamber")
GOLDEN = ("Simpsons Malt", "Finest Pale Ale Golden Promise")
RICE = ("", "Flaked Rice")
CARAMEL100 = ("Viking Malt", "Caramel 100 Malt")
CARAMEL300 = ("Viking Malt", "Caramel 300 Malt")


# b07's grist is 1.09 SRM too dark, which SRM +- 2 now accepts (Task 10b): its target moves to 2.0 so the case still fails
SRM_TARGET = {"b07": 2.0}


def fix_case(conn, bid, fermentables, yeast):
    """Step 10 and step 11 of a brief on G6's picks: (inp, out, validation)."""
    inp = tc.with_picks(conn, bid, fermentables, yeast)
    if bid in SRM_TARGET:
        inp["targets"]["targets"]["srm"]["value"] = SRM_TARGET[bid]
    out = compute(conn, inp)
    picks = [{"ingredient_id": f["ingredient_id"], "name": f["name"], "self_picked": False}
             for f in out["fermentables"]]
    return inp, out, validate(conn, out, inp, picks, frame_of(conn, inp))


def fix_of(v, subject):
    """(failure, its To fix text or None) for the failure with this subject."""
    for f, line in zip(v["failures"], v["feedback"]):
        if f["subject"] == subject:
            assert line.startswith(f["text"])
            return f, (line.split(" To fix: ", 1)[1] if " To fix: " in line else None)
    pytest.fail(f"no failure {subject}: {[f['subject'] for f in v['failures']]}")


def test_fix_lighter_base(conn):
    """b07: Pale Ale Malt 80 and Flaked Corn 20 are too dark and the base malt is the only mover."""
    _, _, v = fix_case(conn, "b07", [(tc.PALE_ALE_W, 80), (tc.CORN, 20)], tc.US05_YEAST)
    f, fix = fix_of(v, "srm")
    assert fix == "use a lighter base malt than Pale Ale Malt (6.5 EBC)."
    assert v["feedback"][v["failures"].index(f)].endswith(" To fix: " + fix)


def test_fix_add_base(conn):
    """b10's try-1 grist has no base malt."""
    _, _, v = fix_case(conn, "b10", [(MUNICH1, 50), (tc.ABBEY, 20), (CARAAMBER, 10), (tc.CANDI, 20)],
                       ("Lallemand", "Abbaye"))
    assert fix_of(v, "srm")[1] == "add a base malt: no other fermentable can take up the colour change."


def test_fix_lower_crystal(conn):
    """b19's try-3 grist: too dark with one base malt and 15 % Caramel 150 Malt."""
    _, _, v = fix_case(conn, "b19", [(GOLDEN, 75), (tc.CARAMEL150, 15), (tc.HONEY, 10)], ("Lallemand", "Nottingham"))
    assert fix_of(v, "srm")[1] == ("lower the crystal share (Caramel 150 Malt 15 %): "
                                   "the colour adjustment never moves a crystal.")


def test_fix_darker_malt_at_limit(conn):
    """b18: Roasted Barley sits at its 2 % limit and the beer is still too light."""
    _, out, v = fix_case(conn, "b18", [(tc.PALE_ALE_W, 88), (tc.CARAMEL50, 10), (tc.ROASTED_BARLEY, 2)],
                         ("Brewline", "British Ale"))
    assert float(out["colour"]["srm"]) < 20 - 1
    assert fix_of(v, "srm")[1] == "Roasted Barley is at its 2 % limit: add a second dark malt (role roast or kilned)."


def test_fix_less_attenuative_yeast(conn):
    """b12: US-05 gives 78 % at 69 C and the grist needs about 77 % for FG 1.0080; Honey ferments out."""
    _, out, v = fix_case(conn, "b12", [(tc.PALE_ALE_W, 85), (tc.HONEY, 15)], tc.US05_YEAST)
    fix = fix_of(v, "rule 10")[1]
    m = re.fullmatch(r"pick a less attenuative yeast: SafAle US-05 gives 78 % here \(mash 69 °C\) and this grist "
                     r"needs about ([\d.]+) % for FG 1\.0080, or lower Honey 15 %, which ferment out\.", fix)
    assert m and 75 < float(m.group(1)) < 78, fix


def test_fix_more_attenuative_yeast(conn):
    inp = tc.step10_input(conn, "b01")
    inp["brief"]["stated"]["fg"] = 1.003
    inp["targets"]["targets"]["fg"]["value"] = 1.003
    out = compute(conn, inp)
    picks = picks_of(table_of(conn, "b01"))
    v = validate(conn, out, inp, picks, frame_of(conn, inp))
    fix = fix_of(v, "rule 10")[1]
    assert re.fullmatch(r"pick a more attenuative yeast: about [\d.]+ %\.", fix), fix


def test_fix_abv_yeast(conn):
    """b23: ABV 6.25 against 5.99 with US-05 at 80 %; about 77 % is needed (replay figure, unverified)."""
    _, out, v = fix_case(conn, "b23", [(tc.PALE_ALE_W, 83), (tc.CHOCOLATE, 10), (tc.CARAMEL150, 5), (tc.BLACK, 2)],
                         tc.US05_YEAST)
    fix = fix_of(v, "abv")[1]
    m = re.fullmatch(r"pick a yeast attenuating about ([\d.]+) % \(SafAle US-05 gives 80 %\)\.", fix)
    assert m and 75 < float(m.group(1)) < 79, fix


def test_fix_abv_without_attenuation_figure(conn):
    inp, out, picks, frame = case(conn, "b08")
    out["numbers"].update(abv=None, fg=None, attenuation_pct=None)
    v = validate(conn, out, inp, picks, frame)
    assert fix_of(v, "abv")[1] == "pick a yeast with an attenuation figure."


def test_fix_rule_4_points(conn):
    """b22's try-1 grist: 15 % Caraamber against a limit of 10 %."""
    _, _, v = fix_case(conn, "b22", [(tc.PILSNER, 60), (RICE, 20), (CARAAMBER, 15), (tc.MELANOIDIN, 5)],
                       ("Lallemand", "Diamond"))
    f, fix = fix_of(v, "rule 4")
    assert fix == "take at least 4.77 points off Caraamber 14.8 %."


def test_fix_rule_3_points(conn):
    _, _, v = fix_case(conn, "b19", [(GOLDEN, 70), (CARAMEL100, 15), (CARAMEL300, 10), (tc.HONEY, 5)],
                       ("Gozdawa", "Real Scotland"))
    f, fix = fix_of(v, "rule 3")
    assert fix == "take at least 9.26 points off Caramel 100 Malt 14.8 %, Caramel 300 Malt 9.5 %."


def test_fix_rule_11_tolerance(conn):
    _, _, v = fix_case(conn, "b19", [(GOLDEN, 70), (CARAMEL100, 15), (CARAMEL300, 10), (tc.HONEY, 5)],
                       ("Gozdawa", "Real Scotland"))
    f, fix = fix_of(v, "rule 11")
    assert fix == f"pick a yeast with an alcohol tolerance of at least {round(float(f['value']), 2):g} %."


def test_no_fix_for_a_pick(conn):
    inp, out, picks, frame = case(conn, "b08")
    hop, recipe, line = out_of_style_pick(conn, out, inp)
    out["recipe"] = recipe
    picks.append({"ingredient_id": hop, "name": line["name"], "self_picked": True})
    v = validate(conn, out, inp, picks, frame)
    assert v["feedback"] and all("To fix" not in l for l in v["feedback"])
    # nor does a target miss no rule explains
    inp, out, picks, frame = case(conn, "b08")
    out["numbers"]["ibu"] = float(out["numbers"]["ibu"]) + 10
    assert all("To fix" not in l for l in validate(conn, out, inp, picks, frame)["feedback"])


def numeric_leaves(x):
    if isinstance(x, bool) or x is None:
        return
    if isinstance(x, (int, float)):
        yield float(x)
    elif isinstance(x, str):
        yield from (float(n) for n in re.findall(r"\d+(?:\.\d+)?", x))
    elif isinstance(x, dict):
        for v in x.values():
            yield from numeric_leaves(v)
    elif isinstance(x, list):
        for v in x:
            yield from numeric_leaves(v)


@pytest.mark.parametrize("bid,ferms,yeast", [
    ("b07", [(tc.PALE_ALE_W, 80), (tc.CORN, 20)], tc.US05_YEAST),
    ("b12", [(tc.PALE_ALE_W, 85), (tc.HONEY, 15)], tc.US05_YEAST),
    ("b18", [(tc.PALE_ALE_W, 88), (tc.CARAMEL50, 10), (tc.ROASTED_BARLEY, 2)], ("Brewline", "British Ale")),
    ("b19", [(GOLDEN, 70), (CARAMEL100, 15), (CARAMEL300, 10), (tc.HONEY, 5)], ("Gozdawa", "Real Scotland")),
    ("b22", [(tc.PILSNER, 60), (RICE, 20), (CARAAMBER, 15), (tc.MELANOIDIN, 5)], ("Lallemand", "Diamond")),
    ("b23", [(tc.PALE_ALE_W, 83), (tc.CHOCOLATE, 10), (tc.CARAMEL150, 5), (tc.BLACK, 2)], tc.US05_YEAST),
])
def test_fix_numbers_come_from_sql(conn, bid, ferms, yeast):
    """Every number in a fix is in the failure, in step 10's output, or is app.attenuation_for_fg's result as rounded."""
    inp, out, v = fix_case(conn, bid, ferms, yeast)
    colour = out["colour"]["grist"]
    og = float(out["og_used"]["value"])
    eff, vol = float(out["batch"]["efficiency_pct"]), float(out["batch"]["volume_l"])
    allowed = list(numeric_leaves(out)) + list(numeric_leaves(inp["targets"]))
    for f in v["failures"]:
        allowed += list(numeric_leaves(f))
    fixes = 0
    for f, line in zip(v["failures"], v["feedback"]):
        if " To fix: " not in line:
            continue
        fixes += 1
        fix = line.split(" To fix: ", 1)[1]
        extra = []
        for fg in re.findall(r"FG (1\.\d+)", fix) + [str(x) for x in (
                [conn.execute("select app.fg_for_abv(%s::numeric, %s::numeric)", [og, float(inp["targets"]["targets"]["abv"]["value"])]).fetchone()[0]] if f["subject"] == "abv" else [])]:
            extra.append(float(conn.execute(
                "select app.attenuation_for_fg(%s::jsonb, %s::numeric, %s::numeric, %s::numeric, %s::numeric)",
                [json.dumps(colour), og, eff, vol, fg]).fetchone()[0]))
        if f["subject"] == "rule 10":
            r = conn.execute("select app.rule10_fg_range(%s, %s::numeric, %s::jsonb)", [
                out["recipe"]["style_code"], out["recipe"]["targets"]["fg"], json.dumps(out["recipe"]["stated"])]).fetchone()[0]
            for bound in (r.lower, r.upper):
                extra.append(float(conn.execute(
                    "select app.attenuation_for_fg(%s::jsonb, %s::numeric, %s::numeric, %s::numeric, %s::numeric)",
                    [json.dumps(colour), og, eff, vol, bound]).fetchone()[0]))
                allowed.append(float(bound))
        if f["subject"] in ("rule 3", "rule 4"):
            allowed.append(float(f["value"]) - float(f["limit"]))
        for token in re.findall(r"\d+(?:\.\d+)?", fix):
            d = len(token.split(".")[1]) if "." in token else 0
            assert any(abs(round(a, d) - float(token)) < 1e-9 for a in allowed + extra), (fix, token)
    assert fixes >= 1, v["feedback"]


@pytest.mark.parametrize("bid", ["b01", "b08", "b14"])
def test_attenuation_for_fg_inverts_fg(conn, bid):
    inp, out, picks, frame = case(conn, bid)
    grist = json.dumps(out["colour"]["grist"])
    og = float(out["og_used"]["value"])
    eff, vol = float(out["batch"]["efficiency_pct"]), float(out["batch"]["volume_l"])
    for att in (65, 72, 80):
        fg = conn.execute("select app.fg(app.solve_grist(%s::numeric, %s::jsonb, %s::numeric, %s::numeric), %s::numeric, "
                          "%s::numeric, %s::numeric)", [og, grist, eff, vol, eff, vol, att]).fetchone()[0]
        got, back = conn.execute(
            "select a, app.fg(app.solve_grist(%s::numeric, %s::jsonb, %s::numeric, %s::numeric), %s::numeric, %s::numeric, a) "
            "from (select app.attenuation_for_fg(%s::jsonb, %s::numeric, %s::numeric, %s::numeric, %s::numeric) a) q",
            [og, grist, eff, vol, eff, vol, grist, og, eff, vol, fg]).fetchone()
        assert abs(float(back) - float(fg)) < 1e-6 and abs(float(got) - att) < 1e-4
    # clamped to [0, 100]
    assert float(conn.execute("select app.attenuation_for_fg(%s::jsonb, %s::numeric, %s::numeric, %s::numeric, 2.0)",
                              [grist, og, eff, vol]).fetchone()[0]) == 0
    assert float(conn.execute("select app.attenuation_for_fg(%s::jsonb, %s::numeric, %s::numeric, %s::numeric, 1.0)",
                              [grist, og, eff, vol]).fetchone()[0]) == 100


# ---- Task 10b: rounding to weighing steps ----

def rerun(conn, run_id):
    from evals import revalidate
    r = revalidate.revalidate_run(conn, run_id)
    conn.rollback()
    if r is None:
        pytest.skip(f"run {run_id} is not in this database")
    return r


def test_rounding_failure_says_rounding(conn):
    """b15's Black Malt floor of 50 g puts SRM out; step 11's SRM line ends with the rounding sentence."""
    r = rerun(conn, 4517)
    srm = next(t for t in r["failures"] if "SRM" in t)
    assert "It comes from rounding to weighing steps: " in srm
    assert srm.endswith(r["rounding"]["because"])


def test_srm_tolerance_is_two(conn):
    """b04's m6-9b grist rounded gives SRM 36.04 against 35: passes at 2; 2.5 away fails, stated or not."""
    from evals.revalidate import call
    row = conn.execute("select input from app.run_step where run_id = 4506 and step = 11 and ok "
                       "order by try desc limit 1").fetchone()
    in10 = conn.execute("select input from app.run_step where run_id = 4506 and step = 10 and ok "
                        "order by try desc limit 1").fetchone()[0]
    conn.rollback()
    in11 = row[0]
    out = compute(conn, in10)
    srm = float(out["numbers"]["srm"])
    ok = call(conn, "step11_validate", out, in11["brief"], in11["targets"], in11["frame"], in11["picks"])
    assert not any("SRM" in f["text"] for f in ok["failures"])
    targets = copy.deepcopy(in11["targets"])
    targets["targets"]["srm"]["value"] = srm - 2.5
    bad = call(conn, "step11_validate", out, in11["brief"], targets, in11["frame"], in11["picks"])
    text = next(f["text"] for f in bad["failures"] if f["subject"] == "srm")
    assert "limit +- 2)" in text
    brief = copy.deepcopy(in11["brief"])
    brief["stated"] = {**brief.get("stated", {}), "srm": srm + 2.5}
    stated = call(conn, "step11_validate", out, brief, in11["targets"], in11["frame"], in11["picks"])
    assert any(f["subject"] == "stated srm" and "limit +- 2)" in f["text"] for f in stated["failures"])


def test_rule_failures_unchanged(conn):
    """app.recipe_rule_failures gives step 11 the rule failures it always had, on every logged m6-9b
    step 11 (the rule 3, 4, 8 and 10 cases among them)."""
    rows = conn.execute("select run_id, output from app.run_step where step = 11 and run_id between 4503 and 4526 "
                        "and output is not null").fetchall()
    conn.rollback()
    if not rows:
        pytest.skip("the m6-9b runs are not in this database")
    rules = set()
    for run_id, output in rows:
        got = sql(conn, "recipe_rule_failures", output["check"])
        logged = [{"rule": int(f["subject"].split()[1]), "text": f["text"], "value": f["value"], "limit": f["limit"]}
                  for f in output["failures"] if f["kind"] == "rule"]
        assert got == logged, run_id
        rules |= {g["rule"] for g in got}
    assert {3, 4} <= rules
