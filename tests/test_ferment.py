"""Step 14: the pitch rate, the fermentation schedule, dry hops and secondary extras (db/052_ferment.sql);
docs/work/m7-process Task 6. The expected figures are doc-calc.md §10-§13 (How to Brew ch. 6-7, Table 6.2, p. 206)."""

import copy
import json
import math

import pytest

from loaders.db import connect
from tests.test_compute import compute, step10_input
from tests.test_contracts import errors
from tests.test_water import sql

pytestmark = pytest.mark.stack

BRIEFS = ["b01", "b02", "b03", "b08", "b13", "b14", "b23"]
OG_12P = 1.0486  # about 12 degP
GRAVITY = "2-5 points of FG"


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    connection.autocommit = True
    yield connection
    connection.close()


@pytest.fixture(scope="module")
def step14(conn):
    cache = {}

    def run(bid):
        if bid not in cache:
            inp = step10_input(conn, bid)
            s10 = compute(conn, inp)
            cache[bid] = ({"run_id": 0, "targets": inp["targets"], "step10": s10},
                          sql(conn, "step14_ferment", inp["targets"], s10))
        return copy.deepcopy(cache[bid])
    return run


def yeast_id(conn, product_id):
    return conn.execute("select ingredient_id from ref.yeast where product_id = %s", (product_id,)).fetchone()[0]


def phases(steps, phase):
    return [s for s in steps if s["phase"] == phase]


def schedule(conn, yid, ferm_c, sid=None, dry_hop=False):
    main = {"ingredient_id": yid}
    souring = {"ingredient_id": sid} if sid else None
    return conn.execute("select app.ferment_schedule(%s::jsonb, %s::jsonb, %s::numeric, %s)",
                        (json.dumps(main), None if souring is None else json.dumps(souring), ferm_c, dry_hop)).fetchone()[0]


def pitch(conn, yid, og, litres):
    return conn.execute("select app.pitch_rate(%s::bigint, %s::numeric, %s::numeric)", (yid, og, litres)).fetchone()[0]


def test_yeast_book_example(conn):
    """A8, HTB Table 7.1: an ale at 0.75 billion cells/L/degP, 20 L of 12 degP is 180 billion cells; a lager at 1.5, 360."""
    ale = pitch(conn, yeast_id(conn, "US-05"), OG_12P, 20)
    lager = pitch(conn, conn.execute("select ingredient_id from ref.yeast where type = 'lager' and form = 'dry' limit 1").fetchone()[0], OG_12P, 20)
    assert ale["rate_m_per_ml_p"] == 0.75
    assert ale["cells_billion"] == pytest.approx(180, abs=2)
    assert lager["rate_m_per_ml_p"] == 1.5
    assert lager["cells_billion"] == pytest.approx(360, abs=4)


def test_dry_yeast_in_grams(conn, step14):
    """Dry yeast: grams = cells / 10 billion per gram, rounded up (HTB p. 108); b01's BRY-97 through the step."""
    out = pitch(conn, yeast_id(conn, "US-05"), OG_12P, 20)
    assert (out["amount"], out["unit"]) == (math.ceil(out["cells_billion"] / 10), "g")
    i, s14 = step14("b01")
    p = s14["pitch"][0]
    og = i["step10"]["numbers"]["og"]
    assert p["unit"] == "g" and p["amount"] == math.ceil(p["cells_billion"] / 10)
    assert p["cells_billion"] == pytest.approx(0.75 * i["step10"]["batch"]["volume_l"] * float(sql(conn, "sg_to_plato", og)), abs=0.1)


def test_liquid_yeast_in_packs(conn):
    """A liquid ale: packs = cells / 100 billion, rounded up."""
    liquid = conn.execute("select ingredient_id from ref.yeast where type = 'ale' and form = 'liquid' limit 1").fetchone()[0]
    out = pitch(conn, liquid, OG_12P, 20)
    assert (out["amount"], out["unit"]) == (math.ceil(out["cells_billion"] / 100), "pack") == (2, "pack")


def test_no_sourced_rate_is_one_pack(conn):
    """A yeast whose amount cannot be computed keeps one pack and says so."""
    out = pitch(conn, yeast_id(conn, "US-05"), None, 20)
    assert (out["amount"], out["unit"], out["cells_billion"]) == (1, "pack", None)
    assert "no sourced pitch rate" in out["because"]


@pytest.mark.parametrize("bid", ["b01", "b14"])
def test_pitch_is_labelled_as_an_estimate(step14, bid):
    """Generic How to Brew cell counts are said to be estimates, not the maker's spec (dry, liquid culture, main after souring)."""
    _, out = step14(bid)
    for p in out["pitch"]:
        assert "generic" in p["because"] and "not the maker" in p["because"], p["name"]


def test_liquid_pitch_is_labelled_as_an_estimate(conn):
    liquid = conn.execute("select ingredient_id from ref.yeast where type = 'ale' and form = 'liquid' limit 1").fetchone()[0]
    because = pitch(conn, liquid, OG_12P, 20)["because"]
    assert "generic" in because and "not the maker" in because


def all_schedules(conn, types):
    rows = conn.execute(
        "select y.ingredient_id, y.type, y.temp_c, (c.dose ->> 'ferm_c')::numeric, "
        "       app.ferment_schedule(jsonb_build_object('ingredient_id', y.ingredient_id), null, (c.dose ->> 'ferm_c')::numeric) "
        "from ref.yeast y cross join lateral app.ingredient_choices(y.ingredient_id, 'main') c "
        "where c.usage = 'ferment' and y.type = any(%s)", (types,)).fetchall()
    assert rows
    return rows


def test_every_ferment_temp_in_range(conn):
    """A4: every souring, ferment and rest step of every ale, kveik and lager yeast, at each ferment option, is inside its range."""
    for yid, typ, rng, ferm_c, steps in all_schedules(conn, ["ale", "kveik", "lager"]):
        for s in steps:
            if s["phase"] in ("souring", "ferment", "rest"):
                assert rng.lower <= s["temp_c"] <= rng.upper, (yid, ferm_c, s)


def test_every_lager_has_diacetyl_rest(conn):
    for yid, typ, rng, ferm_c, steps in all_schedules(conn, ["lager"]):
        rest = phases(steps, "rest")
        assert len(rest) == 1 and rest[0]["days"] == 6, (yid, ferm_c)
        assert rest[0]["temp_c"] >= phases(steps, "ferment")[0]["temp_c"]
        assert phases(steps, "lager")[0]["temp_c"] == 2


def test_ramp_shape(conn):
    """Ale: start < main <= rest; lager: start = main. S-04 (15-20) at step 6's 15 C starts at 15 and holds at 16."""
    steps = schedule(conn, yeast_id(conn, "S-04"), 15)
    start, main = phases(steps, "ferment")
    rest = phases(steps, "rest")[0]
    assert (start["temp_c"], main["temp_c"], rest["temp_c"]) == (15, 16, 19)
    for yid, typ, rng, ferm_c, s in all_schedules(conn, ["ale", "kveik"]):
        a, b = phases(s, "ferment")
        assert a["temp_c"] < b["temp_c"] <= phases(s, "rest")[0]["temp_c"], (yid, ferm_c)
        assert rng.lower <= a["temp_c"]
    for yid, typ, rng, ferm_c, s in all_schedules(conn, ["lager"]):
        assert len(phases(s, "ferment")) == 1


def test_gravity_trigger_on_the_rest(conn):
    """HTB Table 6.2: the rest starts at 2-5 gravity points from FG; the days are only a minimum."""
    for yid, typ, rng, ferm_c, steps in all_schedules(conn, ["ale", "lager"]):
        rest = phases(steps, "rest")[0]
        assert GRAVITY in rest["move_on"] and "at least" in rest["move_on"] and "FG" in rest["move_on"]
        hold = phases(steps, "ferment")[-1]
        assert GRAVITY in hold["move_on"] and "at least" in hold["move_on"]
        assert hold["days"] > 0 and rest["days"] > 0


def test_b13_weizen_schedule(step14):
    """Munich Classic (17-22 C) at 17: start 17, hold 18, rest 21, cold conditioning 10."""
    _, out = step14("b13")
    assert [(s["phase"], s["temp_c"], s["days"]) for s in out["steps"]] == [
        ("ferment", 17, 1), ("ferment", 18, 2), ("rest", 21, 4), ("crash", 10, 7)]


def test_b14_souring_first(conn, step14):
    i, out = step14("b14")
    first, second = out["steps"][0], out["steps"][1]
    assert (first["phase"], first["yeast_id"], first["days"]) == ("souring", 1930, 1.5)
    assert 15 <= first["temp_c"] <= 35 and 32 <= first["temp_c"] <= 46
    assert "pH" in first["move_on"]
    assert second["phase"] == "ferment" and second["yeast_id"] == 1845


def test_souring_culture_pitch(step14):
    """b14: YF-998 at 150 billion per 19 L (20 L: 157.9 billion, 2 packs), the main yeast at 1.0 after souring."""
    i, out = step14("b14")
    sour, main = out["pitch"]
    assert sour["role"] == "souring" and sour["cells_billion"] == pytest.approx(150 * 20 / 19, abs=0.1)
    assert (sour["amount"], sour["unit"]) == (2, "pack")
    assert main["role"] == "main" and main["rate_m_per_ml_p"] == 1.0
    assert step14("b01")[1]["pitch"][0]["rate_m_per_ml_p"] == 0.75


def test_dry_hop_after_fermentation(conn, step14):
    """b02 with 30 g of dry hops: the day after the last ferment step, 14 C, 3 days of contact, step 10's grams."""
    i, _ = step14("b02")
    s10 = i["step10"]
    base = s10["hops"][0]
    s10["hops"] = s10["hops"] + [{**base, "usage": "dry_hop", "minutes": 0, "name": "Dry A", "g": 20},
                                 {**base, "usage": "dry_hop", "minutes": 0, "name": "Dry B", "g": 10}]
    out = sql(conn, "step14_ferment", i["targets"], s10)
    fermented = sum(s["days"] for s in out["steps"] if s["phase"] in ("souring", "ferment", "rest"))
    [group] = out["dry_hops"]
    assert (group["day"], group["temp_c"], group["contact_days"]) == (fermented, 14, 3)
    assert {h["name"]: h["g"] for h in group["hops"]} == {"Dry A": 20, "Dry B": 10}
    order = [s["phase"] for s in out["steps"]]
    assert order.index("dry_hop") == order.index("rest") + 1 and order[-1] == "crash"
    assert errors(conn, "step14.output", out) == []
    assert step14("b02")[1]["dry_hops"] == []


def test_secondary_extras(conn, step14):
    """b23 with coffee beans (time_min 2880) and vanilla: contact 2 days and none; the cold brew coffee is packaging."""
    i, real = step14("b23")
    assert all(e["name"] != "Coffee, cold brew" for e in real["secondary"])
    s10 = i["step10"]
    s10["extras"] = [{"ingredient_id": 26306, "name": "Coffee, whole beans", "usage": "secondary", "time_min": 2880,
                      "dose_g_per_l": 3, "g": 60, "purpose": "x"},
                     {"ingredient_id": 26308, "name": "Vanilla bean", "usage": "secondary", "time_min": None,
                      "dose_g_per_l": 0.05, "g": 1, "purpose": "x"}]
    out = sql(conn, "step14_ferment", i["targets"], s10)
    fermented = sum(s["days"] for s in out["steps"] if s["phase"] in ("souring", "ferment", "rest"))
    coffee, vanilla = sorted(out["secondary"], key=lambda e: e["name"])
    assert (coffee["g"], coffee["contact_days"], coffee["day"]) == (60, 2, fermented)
    assert (vanilla["g"], vanilla["contact_days"]) == (1, None)


def test_max_temp(step14):
    """b08: the highest fermentation temperature is its diacetyl rest; b14's souring step (35 C) does not count."""
    _, out = step14("b08")
    assert out["max_temp_c"] == phases(out["steps"], "rest")[0]["temp_c"] == 18
    _, sour = step14("b14")
    assert sour["max_temp_c"] == phases(sour["steps"], "rest")[0]["temp_c"] < 35


@pytest.mark.parametrize("bid", BRIEFS)
def test_step14_meets_contract(conn, step14, bid):
    i, out = step14(bid)
    assert errors(conn, "step14.input", i) == []
    assert errors(conn, "step14.output", out) == []
    assert [p["ingredient_id"] for p in out["pitch"]].sort() == [y["ingredient_id"] for y in i["step10"]["yeasts"]].sort()


def test_step14_same_input_same_output(conn, step14):
    i, out = step14("b14")
    assert sql(conn, "step14_ferment", i["targets"], i["step10"]) == out
