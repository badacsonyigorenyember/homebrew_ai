"""Step 10: the colour solver (Task 3 of docs/work/m6-compute-validate, db/046_compute.sql)."""

import copy
import json
import re

import pytest

from loaders.db import connect
from tests.test_choose_check import good
from tests.test_choose_table import table_of
from tests.test_contracts import errors as contract_errors
from tests.test_step4 import BRIEFS, brief_of, sql, step4

pytestmark = pytest.mark.stack

MARIS = ("Simpsons Malt", "Finest Pale Ale Maris Otter")
CRYSTAL_T50 = ("Simpsons Malt", "Crystal T50")
BLACK = ("Viking Malt", "Black Malt")
ROASTED_BARLEY = ("Viking Malt", "Roasted Barley")
PALE_ALE = ("Viking Malt", "Pale Ale Malt")
MUNICH2 = ("Weyermann", "Munich Malt Type 2")
LACTOSE = ("", "Lactose")
CHOCOLATE = ("Viking Malt", "Chocolate Dark Malt")
CARAMEL150 = ("Viking Malt", "Caramel 150 Malt")
CARAMEL50 = ("Viking Malt", "Caramel 50 Malt")
OATS = ("", "Flaked Oats")
CORN = ("", "Flaked Corn")
CANDI = ("", "Brown Candi Sugar")
ABBEY = ("Weyermann", "Abbey Malt")
PILSNER = ("Weyermann", "Pilsner Malt")
PALE_ALE_W = ("Weyermann", "Pale Ale Malt")
HONEY = ("", "Honey")
MELANOIDIN = ("Weyermann", "Melanoidin Malt")

OG, EFFICIENCY, VOLUME = 1.050, 70, 20


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def item(conn, who, pct):
    """A grist item for a ref fermentable, with the colour as its middle, as step 10 gives it."""
    producer, name = who
    row = conn.execute(
        "select i.id, i.name, f.role, f.extract_dbfg_pct, app.ebc_mid(f.ebc), f.max_pct "
        "from ref.fermentable f join ref.ingredient i on i.id = f.ingredient_id "
        "where i.producer = %s and i.name = %s",
        who,
    ).fetchone()
    assert row, f"{who} not in ref"
    return {
        "ingredient_id": row[0], "name": row[1], "role": row[2], "pct": pct,
        "extract_pct": float(row[3]), "mashed": row[2] != "sugar",
        "ebc": None if row[4] is None else float(row[4]), "max_pct": float(row[5]),
    }


def colour(conn, target, grist, og=OG):
    return conn.execute(
        "select app.solve_colour(%s::numeric, %s::jsonb, %s::numeric, %s::numeric, %s::numeric)",
        [target, json.dumps(grist), og, EFFICIENCY, VOLUME],
    ).fetchone()[0]


def srm_of(conn, grist, og=OG):
    return float(conn.execute(
        "select app.srm(app.grist_mcu(app.solve_grist(%s::numeric, %s::jsonb, %s::numeric, %s::numeric), %s::numeric))",
        [og, json.dumps(grist), EFFICIENCY, VOLUME, VOLUME],
    ).fetchone()[0])


def shares(result):
    return {g["name"]: float(g["pct"]) for g in result["grist"]}


def test_colour_moves_only_darkest_and_base(conn):
    """A6: b15's G5 grist, Maris Otter 88, Crystal T50 10, Black Malt 2, target 12."""
    grist = [item(conn, MARIS, 88), item(conn, CRYSTAL_T50, 10), item(conn, BLACK, 2)]
    before = srm_of(conn, grist)
    assert abs(before - 12) > 1, "the test needs a grist that misses the target"
    r = colour(conn, 12, grist)
    assert r["adjusted"] and r["reached"]
    s = shares(r)
    assert s["Crystal T50"] == 10
    assert s["Black Malt"] != 2 and s["Finest Pale Ale Maris Otter"] != 88
    assert abs(sum(s.values()) - 100) < 1e-9
    assert abs(float(r["srm"]) - 12) < 0.01
    assert r["darkest"]["name"] == "Black Malt" and r["absorber"]["name"] == "Finest Pale Ale Maris Otter"
    assert float(r["from_pct"]) == 2 and float(r["to_pct"]) == s["Black Malt"]


def test_colour_never_moves_crystal(conn):
    """A grist whose darkest fermentable is a crystal: the darkest non-crystal moves."""
    grist = [item(conn, MARIS, 80), item(conn, CRYSTAL_T50, 15), item(conn, MUNICH2, 5)]
    r = colour(conn, 20, grist)
    assert r["darkest"]["name"] == "Munich Malt Type 2"
    s = shares(r)
    assert s["Crystal T50"] == 15
    assert s["Munich Malt Type 2"] != 5


def test_colour_reports_unreachable(conn):
    """Roasted Barley sits at its max_pct 2 and the target is far above: share stays, reached false."""
    grist = [item(conn, MARIS, 98), item(conn, ROASTED_BARLEY, 2)]
    r = colour(conn, 40, grist)
    assert r["reached"] is False
    assert shares(r)["Roasted Barley"] == 2
    assert r["adjusted"] is False
    assert "limit" in r["because"] or "stay" in r["because"] or "away" in r["because"]


def test_colour_needs_a_base(conn):
    """One base malt that is the darkest: nothing can take up the change."""
    grist = [item(conn, PALE_ALE, 90), item(conn, CRYSTAL_T50, 10)]
    r = colour(conn, 3, grist)
    assert r["adjusted"] is False
    assert r["absorber"] is None
    assert "no other base malt" in r["because"]
    assert shares(r) == {"Pale Ale Malt": 90, "Crystal T50": 10}


def test_colour_within_tolerance_is_left_alone(conn):
    grist = [item(conn, MARIS, 88), item(conn, CRYSTAL_T50, 10), item(conn, BLACK, 2)]
    target = srm_of(conn, grist) + 0.5
    r = colour(conn, target, grist)
    assert r["adjusted"] is False and r["reached"] is True
    assert shares(r) == {"Finest Pale Ale Maris Otter": 88, "Crystal T50": 10, "Black Malt": 2}
    assert "within" in r["because"]


def test_colour_matches_s1(conn):
    """The returned SRM is s1's SRM of the returned shares."""
    grist = [item(conn, MARIS, 88), item(conn, CRYSTAL_T50, 10), item(conn, BLACK, 2)]
    r = colour(conn, 12, grist)
    again = srm_of(conn, r["grist"])
    assert abs(again - float(r["srm"])) < 1e-9


def test_colour_no_colour_counts_as_zero(conn):
    """Lactose has no colour: it enters as 0 EBC and the solver still runs."""
    grist = [item(conn, MARIS, 85), item(conn, LACTOSE, 5), item(conn, BLACK, 1.5), item(conn, CRYSTAL_T50, 8.5)]
    r = colour(conn, 12, grist)
    assert r["reached"] is True


# ---- Task 9b: the second colour pass ----

def dark_total(conn, result):
    """Rule 3's total of a solved grist (roast, and crystal above 60 EBC), read by app.check_rule_3."""
    ferm = [{"role": role, "ebc_mid": None if ebc is None else float(ebc), "pct": g["pct"]}
            for g in result["grist"]
            for role, ebc in [conn.execute(
                "select f.role, app.ebc_mid(f.ebc) from ref.fermentable f where f.ingredient_id = %s",
                (g["ingredient_id"],)).fetchone()]]
    check = conn.execute("select app.check_rule_3(%s::jsonb)", [json.dumps({"fermentables": ferm})]).fetchone()[0]
    return check, sum(f["pct"] for f in ferm if f["role"] == "roast" or (f["role"] == "crystal" and f["ebc_mid"] > 60))


def test_colour_second_dark_grain(conn):
    """b23's G6 grist: Black Malt goes to its 0.01 % floor and is still too dark, so Chocolate Dark
    Malt moves in a second pass; the crystal stays (replay at the real efficiency: Chocolate 7.48 %, SRM 35.0)."""
    grist = [item(conn, PALE_ALE, 83), item(conn, CHOCOLATE, 10), item(conn, CARAMEL150, 5), item(conn, BLACK, 2)]
    r = colour(conn, 35, grist, og=1.0625)
    assert r["reached"] and r["adjusted"]
    s = shares(r)
    assert s["Black Malt"] == pytest.approx(0.01) and r["darkest"]["name"] == "Black Malt"
    assert r["second"]["darkest"]["name"] == "Chocolate Dark Malt"
    assert r["second"]["absorber"]["name"] == "Pale Ale Malt"
    assert float(r["second"]["from_pct"]) == 10 and float(r["second"]["to_pct"]) == pytest.approx(s["Chocolate Dark Malt"])
    assert s["Chocolate Dark Malt"] == pytest.approx(7.48, abs=0.3)  # step 10 runs it at 72 % efficiency: 7.48
    assert s["Caramel 150 Malt"] == 5
    assert abs(float(r["srm"]) - 35) <= 1
    assert "Black Malt" in r["because"] and "Chocolate Dark Malt" in r["because"]


def test_colour_one_pass_has_no_second(conn):
    grist = [item(conn, MARIS, 88), item(conn, CRYSTAL_T50, 10), item(conn, BLACK, 2)]
    assert colour(conn, 12, grist)["second"] is None


def test_colour_keeps_rule_3(conn):
    """b03's G6 try-3 grist: Chocolate Dark Malt stops at the room left under the 15 % dark total
    (replay: SRM 30.5)."""
    grist = [item(conn, MARIS, 73.92), item(conn, OATS, 15), item(conn, CARAMEL150, 8.92), item(conn, CHOCOLATE, 2.16)]
    r = colour(conn, 31, grist, og=1.055)  # the colour is reached below the limit
    assert r["reached"] and shares(r)["Chocolate Dark Malt"] < 15 - 8.92
    r = colour(conn, 34, grist, og=1.055)  # a darker target would need more than the room left
    assert shares(r)["Chocolate Dark Malt"] == pytest.approx(15 - 8.92, abs=1e-9)
    check, total = dark_total(conn, r)
    assert check["status"] == "pass" and total <= 15 + 1e-9
    assert r["reached"] is False and "away" in r["because"]


def test_colour_keeps_rule_5(conn):
    """A sugar mover next to adjuncts: it stops at the room left under the 40 % adjunct and sugar total."""
    grist = [item(conn, PALE_ALE, 64), item(conn, CORN, 18), item(conn, OATS, 15), item(conn, CANDI, 3)]
    r = colour(conn, 30, grist)  # a dark target needs more sugar than the 7 points left
    s = shares(r)
    assert s["Brown Candi Sugar"] == pytest.approx(40 - 18 - 15, abs=1e-9)
    assert s["Flaked Corn"] == 18 and s["Flaked Oats"] == 15


def test_colour_next_base_takes_up(conn):
    """The largest base malt reaches 0.01 % first: the next-largest base malt takes up the rest."""
    grist = [item(conn, ABBEY, 30), item(conn, CORN, 20), item(conn, OATS, 30), item(conn, MARIS, 12), item(conn, PALE_ALE, 8)]
    r = colour(conn, 20, grist)
    assert r["absorber"]["name"] == "Finest Pale Ale Maris Otter"
    assert r["second"] is not None and r["second"]["absorber"]["name"] == "Pale Ale Malt"
    assert r["second"]["darkest"]["name"] == "Abbey Malt"
    s = shares(r)
    assert s["Finest Pale Ale Maris Otter"] == pytest.approx(0.01)
    assert abs(sum(s.values()) - 100) < 1e-9


def test_colour_never_more_than_two_passes(conn):
    """b18's grist: Roasted Barley sits at its limit, no other fermentable can move, the crystal stays."""
    grist = [item(conn, PALE_ALE, 88), item(conn, CARAMEL50, 10), item(conn, ROASTED_BARLEY, 2)]
    r = colour(conn, 20, grist)
    assert r["reached"] is False and r["second"] is None
    assert shares(r)["Caramel 50 Malt"] == 10
    assert "limit" in r["because"] or "away" in r["because"]


# ---- Task 4: step 10 computes amounts and numbers ----

STEP10_IDS = ["b01", "b08", "b10", "b14", "b16", "b23", "b24"]
INPUTS: dict = {}


def step10_input(conn, bid):
    """What the pipeline gives step 10 for one brief: steps 6-9 from the first good proposal."""
    if bid not in INPUTS:
        out = sql(conn, "choose_outputs", table_of(conn, bid), good(conn, bid))
        INPUTS[bid] = {
            "run_id": 0, "try": 1, "brief": brief_of(BRIEFS[bid]),
            "profile": sql(conn, "step0_profile", None), "targets": step4(conn, BRIEFS[bid]),
            "step6": out["step6"], "step7": out["step7"], "step8": out["step8"], "step9": out["step9"],
        }
    return copy.deepcopy(INPUTS[bid])


def compute(conn, inp):
    return sql(conn, "step10_compute", inp["profile"], inp["targets"], inp["step6"], inp["step7"],
               inp["step8"], inp["step9"], inp["brief"])


@pytest.fixture(scope="module")
def computed(conn):
    return {bid: compute(conn, step10_input(conn, bid)) for bid in STEP10_IDS}


def target(inp, key):
    return float(inp["targets"]["targets"][key]["value"])


@pytest.mark.parametrize("bid", STEP10_IDS)
def test_amounts_hit_the_targets(conn, computed, bid):
    inp, out = step10_input(conn, bid), computed[bid]
    n = out["numbers"]
    assert abs(float(n["og"]) - target(inp, "og")) <= 0.002 + 1e-12
    assert abs(float(n["ibu"]) - target(inp, "ibu")) <= 2 + 1e-9
    assert all(float(f["kg"]) > 0 for f in out["fermentables"])
    assert all(float(h["g"]) >= 0 for h in out["hops"])
    assert sum(float(h["g"]) for h in out["hops"]) > 0
    moved = {out["colour"]["darkest"]["ingredient_id"], out["colour"]["absorber"]["ingredient_id"]} \
        if out["colour"]["adjusted"] else set()
    if out["colour"]["second"]:
        moved |= {out["colour"]["second"]["darkest"]["ingredient_id"], out["colour"]["second"]["absorber"]["ingredient_id"]}
    proposed = {f["ingredient_id"]: float(f["pct"]) for f in inp["step7"]["fermentables"]}
    total_kg = sum(float(f["kg"]) for f in out["fermentables"])
    for f in out["fermentables"]:
        if f["ingredient_id"] not in moved:  # rounding moves a share by at most one step of the total
            assert abs(float(f["pct"]) - proposed[f["ingredient_id"]]) <= 0.05 / total_kg * 100 + 1e-9, f["name"]
    assert abs(sum(float(f["pct"]) for f in out["fermentables"]) - 100) < 1e-9
    assert out["batch"]["volume_l"] == inp["targets"]["batch_l"]["value"]


@pytest.mark.parametrize("bid", STEP10_IDS)
def test_numbers_are_what_check_recipe_computes(conn, computed, bid):
    """A5 (SQL half): the check recomputes the numbers of step 10 from its recipe object."""
    out = computed[bid]
    check = sql(conn, "check_recipe", out["recipe"])["numbers"]
    for k in ("og", "fg", "abv", "ibu", "attenuation_pct"):
        if out["numbers"][k] is None:  # a yeast with no attenuation figure (b10's abbey yeast)
            assert check[k] is None, k
        else:
            assert abs(float(check[k]) - float(out["numbers"][k])) < 1e-9, k
    if not out["numbers"]["srm_lower_bound"]:
        assert abs(float(check["srm"]) - float(out["numbers"]["srm"])) < 1e-9
    else:
        assert check["srm"] is None


def test_misc_grams_are_dose_times_batch(conn, computed):
    """A7: every extra is its dose g/L x 20 L to the gram (b23 coffee 120 g, vanilla 1 g, b24 orange peel 52.8 -> 53 g); no number moves."""
    for bid in ("b23", "b24"):
        out = computed[bid]
        doses = {e["ingredient_id"]: float(e["dose_g_per_l"]) for e in step10_input(conn, bid)["step9"]["extras"]}
        assert doses and {e["ingredient_id"] for e in out["extras"]} == set(doses)
        for e in out["extras"]:
            assert float(e["g"]) == max(round(doses[e["ingredient_id"]] * 20 + 1e-9), 1), e["name"]
        assert [e["ingredient_id"] for e in out["recipe"]["extras"]] == [e["ingredient_id"] for e in out["extras"]]
        without = copy.deepcopy(out["recipe"])
        without["extras"] = []
        assert sql(conn, "check_recipe", without)["numbers"] == sql(conn, "check_recipe", out["recipe"])["numbers"]
    grams = {e["name"]: float(e["g"]) for bid in ("b23", "b24") for e in computed[bid]["extras"]}
    assert grams["Vanilla bean"] == 1 and grams["Orange peel"] == 53 and grams["Coffee, cold brew"] == 120  # dose 6 g/L x 20 L
    # packaging is saved as package, the recipe object keeps the check's word
    cold = next(e for e in computed["b23"]["extras"] if e["name"] == "Coffee, cold brew")
    assert cold["usage"] == "package"
    assert next(e for e in computed["b23"]["recipe"]["extras"] if e["ingredient_id"] == cold["ingredient_id"])["usage"] == "packaging"


def test_values_used_named(computed):
    """R1: each value picked from a range has its line."""
    for out in computed.values():
        assert {v["what"] for v in out["values_used"]} == {
            "colour", "alpha", "attenuation", "ferm_c", "boil", "mash", "yeast amount"}
        assert all(v["because"] for v in out["values_used"])


def test_boil_covers_grist_and_hops(conn, computed):
    """Rule 8 and 13: the boil is the largest of 60, the grist's need and the longest boil addition."""
    for bid, out in computed.items():
        need = conn.execute("select coalesce(max(min_boil_min), 0) from ref.fermentable where ingredient_id = any(%s)",
                            ([f["ingredient_id"] for f in out["fermentables"]],)).fetchone()[0]
        boil = out["boil"]["boil_min"]
        assert boil == max(60, need), bid
        assert out["recipe"]["boil_min"] == boil
        boil_hops = [h for h in out["hops"] if h["usage"] == "boil"]
        assert max(float(h["minutes"]) for h in boil_hops) == boil, bid
    # Pilsner malt needs 90 min and the proposal's bittering hop is at 60: the hop follows the boil
    b08 = computed["b08"]
    assert b08["boil"]["boil_min"] == 90 and b08["boil"]["because"].startswith("90 min")
    asked = step10_input(conn, "b08")["step8"]["hops"]
    assert max(float(h["minutes"]) for h in asked if h["usage"] == "boil") == 60
    # a 60 min malt: the boil stays at 60
    inp = step10_input(conn, "b01")
    pale, = conn.execute("select i.id from ref.ingredient i where i.producer = 'Viking Malt' and i.name = 'Pale Ale Malt'").fetchone()
    inp["step7"]["fermentables"][-1].update(ingredient_id=pale, name="Pale Ale Malt")
    assert compute(conn, inp)["boil"]["boil_min"] == 60


def test_og_moves_only_inside_tolerance(conn):
    inp = step10_input(conn, "b01")
    base = compute(conn, inp)
    abv_at_target = float(sql(conn, "check_recipe", {**base["recipe"], "targets": {
        **base["recipe"]["targets"], "og": target(inp, "og")}})["numbers"]["abv"])
    # in tolerance at the target OG: it stays
    inp["targets"]["targets"]["abv"]["value"] = round(abv_at_target + 0.1, 2)
    kept = compute(conn, inp)
    assert kept["og_used"]["moved"] is False and float(kept["og_used"]["value"]) == target(inp, "og")
    # 0.35 below the ABV the grist gives: the OG moves down, by at most 0.002, and ABV gets nearer
    wanted = abv_at_target - 0.35
    inp["targets"]["targets"]["abv"]["value"] = wanted
    moved = compute(conn, inp)
    assert moved["og_used"]["moved"] is True
    assert abs(float(moved["og_used"]["value"]) - target(inp, "og")) <= 0.002 + 1e-12
    assert float(moved["og_used"]["value"]) < target(inp, "og")
    assert abs(float(moved["numbers"]["abv"]) - wanted) < abs(abv_at_target - wanted)
    assert moved["recipe"]["targets"]["og"] == moved["numbers"]["og"]  # the rounded OG; og_used is before rounding
    assert abs(float(moved["numbers"]["og"]) - float(moved["og_used"]["value"])) < 0.001


def test_lower_bound_named(conn):
    """A fermentable with no colour counts as 0 EBC and is named."""
    out = compute(conn, step10_input(conn, "b20"))
    expected = sorted(r[0] for r in conn.execute(
        "select i.name from ref.fermentable f join ref.ingredient i on i.id = f.ingredient_id "
        "where f.ebc is null and f.ingredient_id = any(%s)", ([f["ingredient_id"] for f in out["fermentables"]],)))
    assert expected and sorted(out["numbers"]["srm_lower_bound"]) == expected
    assert out["numbers"]["srm"] is not None


def test_ferm_c_from_choice(conn, computed):
    for bid, out in computed.items():
        choice = step10_input(conn, bid)["step6"]["yeast"]["choice"]
        assert float(out["ferm_c"]) == float(re.search(r"ferment at ([\d.]+)", choice).group(1)), bid
        assert out["recipe"]["yeast"]["ferm_c"] == out["ferm_c"]


def test_ferm_c_without_a_choice_is_the_range_middle(conn):
    """Step 6 may pick a yeast with no choice: the middle of its temperature range stands in (found in the pipeline run)."""
    inp = step10_input(conn, "b01")
    inp["step6"]["yeast"]["choice"] = None
    inp["step6"]["yeast"]["temp_c"] = {"low": 12, "high": 15}
    out = compute(conn, inp)
    assert float(out["ferm_c"]) == 13.5
    line = next(v for v in out["values_used"] if v["what"] == "ferm_c")
    assert "13.5" in line["because"] and "no choice" in line["because"]
    inp["step6"]["yeast"]["temp_c"] = None
    with pytest.raises(Exception, match="step 10: the yeast .* has no fermentation temperature"):
        compute(conn, inp)
    conn.execute("rollback")


def test_a_missing_dose_raises(conn):
    inp = step10_input(conn, "b23")
    inp["step9"]["extras"][0]["dose_g_per_l"] = None
    with pytest.raises(Exception, match="step 10: no dose for"):
        compute(conn, inp)
    conn.execute("rollback")


@pytest.mark.parametrize("bid", STEP10_IDS)
def test_output_meets_contract(conn, computed, bid):
    assert contract_errors(conn, "step10.input", step10_input(conn, bid)) == []
    assert contract_errors(conn, "step10.output", computed[bid]) == []


def test_same_input_same_output(conn, computed):
    assert compute(conn, step10_input(conn, "b16")) == computed["b16"]


# ---- Task 9b: the mash moves for a low FG ----

US05_YEAST = ("Fermentis", "SafAle US-05")


def with_picks(conn, bid, fermentables, yeast):
    """The step 10 input of a brief with other steps 6-7 picks (a G6 grist and yeast), the rest as
    the first good proposal gave it."""
    inp = step10_input(conn, bid)
    ferms = []
    for who, pct in fermentables:
        fid, name = conn.execute("select id, name from ref.ingredient where producer = %s and name = %s", who).fetchone()
        ferms.append({"ingredient_id": fid, "name": name, "pct": pct, "usage": "mash", "purpose": "test"})
    inp["step7"]["fermentables"] = ferms
    yid, name, temp = conn.execute(
        "select i.id, i.name, y.temp_c from ref.yeast y join ref.ingredient i on i.id = y.ingredient_id "
        "where i.producer = %s and i.name = %s", yeast).fetchone()
    inp["step6"]["yeast"].update(ingredient_id=yid, name=name, choice=None,
                                 temp_c={"low": float(temp.lower), "high": float(temp.upper)})
    return inp


def b09_picks(conn):
    return with_picks(conn, "b09", [(MUNICH2, 70), (PILSNER, 25), (MELANOIDIN, 5)], ("Fermentis", "SafLager S-189"))


def fg_range(conn, out, inp):
    r = conn.execute("select app.rule10_fg_range(%s, %s::numeric, %s::jsonb)",
                     (out["recipe"]["style_code"], target(inp, "fg"), json.dumps(out["recipe"]["stated"]))).fetchone()[0]
    return float(r.lower), float(r.upper)


def mash_line(out):
    return next(v for v in out["values_used"] if v["what"] == "mash")["because"]


def test_mash_moves_for_low_fg(conn):
    """b09's G6 picks end below rule 10's FG range at 66.5 C: the mash goes up inside (68.3, 69]
    (replay: FG 1.0114 at 69 C)."""
    inp = b09_picks(conn)
    out = compute(conn, inp)
    lo, hi = fg_range(conn, out, inp)
    assert 68.3 < out["mash_c"] <= 69 and out["recipe"]["mash_c"] == out["mash_c"]
    assert lo <= float(out["numbers"]["fg"]) <= hi
    check = sql(conn, "check_recipe", out["recipe"])
    assert next(r for r in check["results"] if r["rule"] == 10)["status"] == "pass"
    assert "66.5" in mash_line(out) and "raised" in mash_line(out)
    # the attenuation line and every later number use the mash used
    assert str(round(out["mash_c"])) in next(v for v in out["values_used"] if v["what"] == "attenuation")["because"]
    inp["targets"]["mash_c"]["from"] = "hint"
    stays = compute(conn, inp)
    assert stays["mash_c"] == 66.5 and float(stays["numbers"]["fg"]) < lo


def test_mash_stays_in_range(conn):
    inp = step10_input(conn, "b01")
    out = compute(conn, inp)
    lo, hi = fg_range(conn, out, inp)
    assert out["mash_c"] == 66.5 and lo <= float(out["numbers"]["fg"]) <= hi
    assert "inside" in mash_line(out) and "stays" in mash_line(out)


def test_mash_hint_stays(conn):
    inp = b09_picks(conn)
    inp["targets"]["mash_c"].update({"from": "hint", "value": 66.5})
    out = compute(conn, inp)
    assert out["mash_c"] == 66.5
    assert "hint" in mash_line(out) and "stays" in mash_line(out)


def test_mash_cannot_raise_fg_above_range(conn):
    """An FG above the range cannot be helped by a lower mash: the curve is flat below 68.3 C."""
    inp = step10_input(conn, "b01")
    inp["brief"]["stated"]["fg"] = 1.003
    inp["targets"]["targets"]["fg"]["value"] = 1.003
    out = compute(conn, inp)
    lo, hi = fg_range(conn, out, inp)
    assert float(out["numbers"]["fg"]) > hi
    assert out["mash_c"] == 66.5
    assert "flat below 68.3" in mash_line(out)


def test_mash_stops_at_69(conn):
    """b12's G6 picks: even at 69 C the FG stays below its range (replay: 1.0077 vs 1.0080)."""
    inp = with_picks(conn, "b12", [(PALE_ALE_W, 85), (HONEY, 15)], US05_YEAST)
    out = compute(conn, inp)
    lo, hi = fg_range(conn, out, inp)
    assert out["mash_c"] == 69 and float(out["numbers"]["fg"]) < lo
    check = sql(conn, "check_recipe", out["recipe"])
    assert next(r for r in check["results"] if r["rule"] == 10)["status"] == "fail"
    assert "69" in mash_line(out)


# ---- Task 10b: step 10 rounds amounts to what a brewer can weigh and order ----

def logged_input(conn, run_id):
    """The last try's step 10 input of a logged m6-9b run (its saved picks)."""
    row = conn.execute("select input from app.run_step where run_id = %s and step = 10 and ok "
                       "order by try desc limit 1", (run_id,)).fetchone()
    conn.rollback()
    if row is None:
        pytest.skip(f"run {run_id} is not in this database")
    return row[0]


def compute_logged(conn, run_id):
    inp = logged_input(conn, run_id)
    return compute(conn, inp)


def on_step(value, step):
    steps = round(float(value) / step)
    return steps >= 1 and abs(float(value) - steps * step) < 1e-9


def test_weighing_steps_as_decided(conn):
    assert sql(conn, "weighing_steps") == {"malt_kg": 0.05, "sugar_kg": 0.001, "hop_g": 1, "extra_g": 1}


@pytest.mark.parametrize("bid", ["b01", "b10", "b23", "b24"])
def test_amounts_on_weighing_steps(conn, computed_10b, bid):
    out = computed_10b[bid]
    roles = {r[0]: r[1] for r in conn.execute(
        "select ingredient_id, role from ref.fermentable where ingredient_id = any(%s)",
        ([f["ingredient_id"] for f in out["fermentables"]],))}
    total = sum(float(f["kg"]) for f in out["fermentables"])
    for f in out["fermentables"]:
        step = 0.001 if roles[f["ingredient_id"]] == "sugar" else 0.05
        assert on_step(f["kg"], step), (f["name"], f["kg"])
        assert abs(float(f["pct"]) - float(f["kg"]) / total * 100) < 1e-9, f["name"]
    hop_total = sum(float(h["g"]) for h in out["hops"])
    for h in out["hops"]:
        assert on_step(h["g"], 1), (h["name"], h["g"])
        assert abs(float(h["share_pct"]) - float(h["g"]) / hop_total * 100) < 1e-9
    for e in out["extras"]:
        assert on_step(e["g"], 1), (e["name"], e["g"])
    assert out["rounding"]["steps"] == {"malt_kg": 0.05, "sugar_kg": 0.001, "hop_g": 1, "extra_g": 1}
    assert out["recipe"]["fermentables"][0]["pct"] == out["fermentables"][0]["pct"]
    assert [h["g"] for h in out["recipe"]["hops"]] == [h["g"] for h in out["hops"]]


@pytest.fixture(scope="module")
def computed_10b(conn):
    return {bid: compute(conn, step10_input(conn, bid)) for bid in ("b01", "b10", "b23", "b24")}


def grist_of(conn, out, scale=1.0):
    """Step 10's solved grist for step10_round_grist, from an output's fermentables and the ref facts."""
    grist = grist_of(conn, out, 1.013)
    targets = {k: target(inp, k) for k in ("og", "abv", "srm")}
    r = sql(conn, "step10_round_grist", grist, recipe, targets, {}, 70, 20, out["numbers"]["attenuation_pct"])
    assert r["reached"] is True and "rule 8" not in r["added"]


def test_hops_rounded_inside_ibu(conn):
    """b08 at 10 L: IBU within 2 of 50; Magnum 13 g."""
    inp = step10_input(conn, "b08")
    inp["targets"]["batch_l"]["value"] = 10
    out = compute(conn, inp)
    assert abs(float(out["numbers"]["ibu"]) - target(inp, "ibu")) <= 2 + 1e-9
    assert all(on_step(h["g"], 1) for h in out["hops"])
