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
    assert abs(float(n["ibu"]) - target(inp, "ibu")) < 0.01
    assert all(float(f["kg"]) > 0 for f in out["fermentables"])
    assert all(float(h["g"]) >= 0 for h in out["hops"])
    assert sum(float(h["g"]) for h in out["hops"]) > 0
    moved = {out["colour"]["darkest"]["ingredient_id"], out["colour"]["absorber"]["ingredient_id"]} \
        if out["colour"]["adjusted"] else set()
    proposed = {f["ingredient_id"]: float(f["pct"]) for f in inp["step7"]["fermentables"]}
    for f in out["fermentables"]:
        if f["ingredient_id"] not in moved:
            assert float(f["pct"]) == proposed[f["ingredient_id"]], f["name"]
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
    """A7: every extra is its dose g/L x 20 L (b23 vanilla 1 g, b24 orange peel 52.8 g); no number moves."""
    for bid in ("b23", "b24"):
        out = computed[bid]
        doses = {e["ingredient_id"]: float(e["dose_g_per_l"]) for e in step10_input(conn, bid)["step9"]["extras"]}
        assert doses and {e["ingredient_id"] for e in out["extras"]} == set(doses)
        for e in out["extras"]:
            assert abs(float(e["g"]) - doses[e["ingredient_id"]] * 20) < 1e-9, e["name"]
        assert [e["ingredient_id"] for e in out["recipe"]["extras"]] == [e["ingredient_id"] for e in out["extras"]]
        without = copy.deepcopy(out["recipe"])
        without["extras"] = []
        assert sql(conn, "check_recipe", without)["numbers"] == sql(conn, "check_recipe", out["recipe"])["numbers"]
    grams = {e["name"]: float(e["g"]) for bid in ("b23", "b24") for e in computed[bid]["extras"]}
    assert grams["Vanilla bean"] == 1 and abs(grams["Orange peel"] - 52.8) < 1e-9
    # packaging is saved as package, the recipe object keeps the check's word
    cold = next(e for e in computed["b23"]["extras"] if e["name"] == "Coffee, cold brew")
    assert cold["usage"] == "package"
    assert next(e for e in computed["b23"]["recipe"]["extras"] if e["ingredient_id"] == cold["ingredient_id"])["usage"] == "packaging"


def test_values_used_named(computed):
    """R1: each value picked from a range has its line."""
    for out in computed.values():
        assert {v["what"] for v in out["values_used"]} == {
            "colour", "alpha", "attenuation", "ferm_c", "boil", "yeast amount"}
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
    assert moved["recipe"]["targets"]["og"] == moved["og_used"]["value"]


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
