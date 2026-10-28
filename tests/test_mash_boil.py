"""Step 13: mash steps, strike temperature, volumes and boil schedule (db/051_mash_boil.sql);
docs/work/m7-process Task 5. The expected figures are doc-calc.md §8 and §9 (How to Brew ch. 16-17)."""

import copy

import pytest

from loaders.db import connect
from tests.test_compute import compute, step10_input
from tests.test_contracts import errors
from tests.test_water import sql

pytestmark = pytest.mark.stack

BRIEFS = ["b01", "b02", "b08", "b13", "b14", "b23", "b24"]


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    connection.autocommit = True
    yield connection
    connection.close()


@pytest.fixture(scope="module")
def step13(conn):
    cache = {}

    def run(bid):
        if bid not in cache:
            inp = step10_input(conn, bid)
            i = {"run_id": 0, "profile": inp["profile"], "targets": inp["targets"], "step10": compute(conn, inp)}
            cache[bid] = (i, sql(conn, "step13_mash_boil", i["profile"], i["targets"], i["step10"]))
        return copy.deepcopy(cache[bid])
    return run


def grist(adjunct_pct):
    return [{"name": "Pale Ale Malt", "kg": 100 - adjunct_pct, "role": "base", "ebc": 6},
            {"name": "Flaked Oats", "kg": adjunct_pct, "role": "adjunct", "ebc": 2}]


def by_name(steps):
    return {s["name"]: s for s in steps}


@pytest.mark.parametrize("bid", ["b01", "b08", "b14"])
def test_mash_and_boil_are_step10s(step13, bid):
    """A7: the saccharification rest and the boil time are step 10's."""
    i, out = step13(bid)
    sacch = by_name(out["mash"]["steps"])["saccharification rest"]
    assert sacch["temp_c"] == pytest.approx(i["step10"]["mash_c"])
    assert out["mash"]["mash_c"] == pytest.approx(i["step10"]["mash_c"])
    assert out["boil"]["boil_min"] == i["step10"]["boil"]["boil_min"]
    assert out["boil"]["because"] == i["step10"]["boil"]["because"]


@pytest.mark.parametrize("bid", BRIEFS)
def test_rests_are_neutral_and_sourced(step13, bid):
    """A11: every step but the saccharification rest is below the starch range or the mash-out, and has a source."""
    _, out = step13(bid)
    for s in out["mash"]["steps"]:
        assert s["source"] and s["why"], s
        if s["name"] not in ("saccharification rest", "mash-out"):
            assert s["temp_c"] < 55, s
    assert out["mash"]["steps"][-1]["name"] == "mash-out" and out["mash"]["steps"][-1]["temp_c"] == 77


def test_weizen_gets_ferulic_rest(step13):
    i, out = step13("b13")
    assert i["targets"]["style"]["code"] in ("10A", "10B", "10C")
    rest = by_name(out["mash"]["steps"])["ferulic acid rest"]
    assert (rest["temp_c"], rest["minutes"]) == (40, 30)
    assert out["mash"]["steps"][0]["name"] == "ferulic acid rest"


def test_flaked_over_20_gets_beta_glucan_rest(conn):
    over = by_name(sql(conn, "mash_rests", "18A", grist(25), 66))
    assert (over["beta-glucan rest"]["temp_c"], over["beta-glucan rest"]["minutes"]) == (45, 20)
    assert "beta-glucan rest" not in by_name(sql(conn, "mash_rests", "18A", grist(15), 66))
    both = sql(conn, "mash_rests", "10A", grist(25), 66)
    assert [s["name"] for s in both] == ["ferulic acid rest", "saccharification rest", "mash-out"]


def test_single_infusion_otherwise(step13):
    _, out = step13("b01")
    assert [s["name"] for s in out["mash"]["steps"]] == ["saccharification rest", "mash-out"]


def test_additions_in_time_order(conn, step13):
    """A boil with hops at 15, 60 and 5 minutes, a whirlpool hop and a boil extra: largest minute first, whirlpool apart."""
    i, _ = step13("b01")
    s10 = copy.deepcopy(i["step10"])
    base = s10["hops"][0]
    s10["hops"] = [
        {**base, "usage": "boil", "minutes": 15, "name": "Late", "g": 10},
        {**base, "usage": "boil", "minutes": 60, "name": "Early", "g": 20},
        {**base, "usage": "boil", "minutes": 5, "name": "Last", "g": 5},
        {**base, "usage": "whirlpool", "minutes": 20, "name": "Swirl", "g": 30},
        {**base, "usage": "dry_hop", "minutes": 0, "name": "Dry", "g": 40},
    ]
    s10["extras"] = [{"ingredient_id": 1, "name": "Peel", "usage": "whirlpool", "time_min": 10, "dose_g_per_l": 1, "g": 7, "purpose": "x"},
                     {"ingredient_id": 2, "name": "Moss", "usage": "boil", "time_min": 10, "dose_g_per_l": 1, "g": 3, "purpose": "x"}]
    out = sql(conn, "step13_mash_boil", i["profile"], i["targets"], s10)
    assert [(a["at_min"], a["name"]) for a in out["boil"]["additions"]] == [(60, "Early"), (15, "Late"), (10, "Moss"), (5, "Last")]
    assert [(w["minutes"], w["name"]) for w in out["boil"]["whirlpool"]] == [(20, "Swirl"), (10, "Peel")]
    assert errors(conn, "step13.output", out) == []
    _, orange = step13("b24")
    assert [(w["minutes"], w["name"], w["kind"]) for w in orange["boil"]["whirlpool"]] == [(15, "Orange peel", "extra")]


@pytest.mark.parametrize("bid", ["b02", "b23"])
def test_no_dry_hop_or_secondary_here(step13, bid):
    """Dry hops and package, secondary or ferment extras are step 14's and 15's, not step 13's."""
    i, out = step13(bid)
    here = [a["name"] for a in out["boil"]["additions"] + out["boil"]["whirlpool"] + out["mash"]["additions"]]
    for e in i["step10"]["extras"]:
        if e["usage"] in ("ferment", "secondary", "package"):
            assert e["name"] not in here
    assert len(here) == sum(1 for h in i["step10"]["hops"] if h["usage"] in ("boil", "whirlpool")) + \
        sum(1 for e in i["step10"]["extras"] if e["usage"] in ("mash", "boil", "whirlpool"))


def test_strike_temp_example(conn):
    """doc-calc §8: HTB ch. 17 p. 268, 4.54 kg at 3 L/kg, grain 21 C, mash 67 C gives 73.2 C."""
    assert float(sql(conn, "strike_temp", 3, 21, 67)) == pytest.approx(73.2, abs=0.5)
    with pytest.raises(Exception, match="above 0"):
        sql(conn, "strike_temp", 0, 21, 67)


@pytest.mark.parametrize("bid", ["b01", "b13"])
def test_strike_c_targets_first_step(conn, step13, bid):
    _, out = step13(bid)
    first = out["mash"]["steps"][0]["temp_c"]
    assert out["mash"]["grain_c"] == 21
    assert out["mash"]["strike_c"] == float(sql(conn, "strike_temp", out["mash"]["volumes"]["ratio_l_kg"], 21, first))
    assert out["mash"]["strike_c"] > first


@pytest.mark.parametrize("bid", ["b01", "b08", "b14"])
def test_volumes_equal_step12s(conn, step13, bid):
    """A12: step 13's volumes are the ones step 12 doses for."""
    i, out = step13(bid)
    step12 = sql(conn, "step12_water", i["profile"], i["targets"], step10_brief(conn, bid), i["step10"])
    assert out["mash"]["volumes"] == step12["volumes"] == sql(conn, "water_volumes", i["profile"], i["step10"])


def step10_brief(conn, bid):
    return step10_input(conn, bid)["brief"]


@pytest.mark.parametrize("bid", BRIEFS)
def test_step13_meets_contract(conn, step13, bid):
    i, out = step13(bid)
    assert errors(conn, "step13.input", i) == []
    assert errors(conn, "step13.output", out) == []
