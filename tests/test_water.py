"""Water maths for step 12 (db/050_water.sql); docs/work/m7-process Task 3.

The expected figures are the worked examples of doc-calc.md §1, §2, §6 and §7 (Water ch. 4-7,
How to Brew ch. 21), computed there from the book's own numbers.
"""

import copy
import json
import re
from pathlib import Path

import pytest

from loaders.db import connect
from tests.test_compute import compute, step10_input
from tests.test_contracts import errors

pytestmark = pytest.mark.stack

def sql(conn, fn, *args):
    """select app.<fn>(args): dicts and lists go as jsonb, numbers as numeric, text lists as text[]."""
    marks, params = [], []
    for a in args:
        if isinstance(a, (dict,)) or (isinstance(a, list) and a and isinstance(a[0], dict)) or (isinstance(a, list) and not a and fn != "water_aim"):
            marks.append("%s::jsonb")
            params.append(json.dumps(a))
        elif isinstance(a, list):
            marks.append("%s::text[]")
            params.append(a)
        elif isinstance(a, (int, float)) and not isinstance(a, bool):
            marks.append("%s::numeric")
            params.append(a)
        else:
            marks.append("%s")
            params.append(a)
    return conn.execute(f"select app.{fn}({', '.join(marks)})", params).fetchone()[0]


DISTILLED = {"ca": 0, "mg": 0, "na": 0, "so4": 0, "cl": 0, "hco3": 0}


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    connection.autocommit = True
    yield connection
    connection.close()


@pytest.fixture(scope="module")
def ids(conn):
    rows = conn.execute("select name, id from ref.ingredient where name = any(%s)",
                        (["gypsum", "calcium chloride", "baking soda", "slaked lime", "Brown Candi Sugar"],)).fetchall()
    return dict(rows)


# Grist items as app.mashed_grist gives them: Pilsen malt (about 1.5 degL), Caramel 60L (61 degL = 120 EBC)
# and a roast malt, so Table 21.4's rows are the ones doc-calc §7 works with.
def pilsen(kg):
    return {"name": "Pilsen", "kg": kg, "role": "base", "ebc": 3}


def caramel60(kg):
    return {"name": "Caramel 60L", "kg": kg, "role": "crystal", "ebc": 120.17}


def roast(kg):
    return {"name": "Roast", "kg": kg, "role": "roast", "ebc": 1000}


def ions_of(**kw):
    return {**DISTILLED, **kw}


# ---- the book's worked examples ----

def test_table17_per_gallon(conn, ids):
    """doc-calc §1: the stored mg/L per g/L reproduce Water's Table 17 per gallon (3.785 L)."""
    gypsum = sql(conn, "salt_ions", [{"ingredient_id": ids["gypsum"], "g": 1}], 3.785)
    assert gypsum["ca"] == pytest.approx(61.5, abs=0.1) and gypsum["so4"] == pytest.approx(147.4, abs=0.1)
    cacl = sql(conn, "salt_ions", [{"ingredient_id": ids["calcium chloride"], "g": 1}], 3.785)
    assert cacl["ca"] == pytest.approx(72.0, abs=0.1) and cacl["cl"] == pytest.approx(127.4, abs=0.1)
    lime = sql(conn, "salt_ions", [{"ingredient_id": ids["slaked lime"], "g": 1}], 3.785)
    assert lime["ca"] == pytest.approx(143, abs=0.2) and lime["oh"] == pytest.approx(121, abs=0.3)


def test_pilsner_example(conn, ids):
    """Water ch. 7 p. 129: 30 mg/L Ca from calcium chloride in 10 gal (37.854 L) is 4.17 g; 4.2 g gives 53.5 mg/L Cl."""
    ca_per_g_l = sql(conn, "salt_ions", [{"ingredient_id": ids["calcium chloride"], "g": 1}], 1)["ca"]
    assert 30 * 37.854 / ca_per_g_l == pytest.approx(4.17, abs=0.02)
    ions = sql(conn, "salt_ions", [{"ingredient_id": ids["calcium chloride"], "g": 4.2}], 37.854)
    assert ions["cl"] == pytest.approx(53.5, abs=0.2)


def test_pale_ale_option_1(conn):
    """Water ch. 7 p. 124-125: alkalinity 125, Mg 15: RA 44 at Ca 101 and 9 at Ca 150."""
    hco3 = 125 * 61.017 / 50
    at_101 = sql(conn, "residual_alkalinity", {"ca": 101, "mg": 15, "hco3": hco3})
    at_150 = sql(conn, "residual_alkalinity", {"ca": 150, "mg": 15, "hco3": hco3})
    assert at_101["alkalinity_ppm"] == pytest.approx(125, abs=0.01)
    assert at_101["ra_ppm"] == pytest.approx(44, abs=1)
    assert at_150["ra_ppm"] == pytest.approx(9, abs=1)
    assert at_150["ra_meq_l"] == pytest.approx(at_150["ra_ppm"] / 50)


def test_foreign_extra_stout_lime(conn, ids):
    """Water ch. 7 p. 131: raising RA by 1.68 mEq/L takes 0.087 g/L slaked lime."""
    effect = sql(conn, "residual_alkalinity",
                 sql(conn, "salt_ions", [{"ingredient_id": ids["slaked lime"], "g": 1}], 1))["ra_meq_l"]
    assert effect == pytest.approx(19.3, abs=0.1)
    assert 1.68 / effect == pytest.approx(0.087, abs=0.002)


def test_salt_ions_rejects_bad_input(conn, ids):
    with pytest.raises(Exception, match="not a water salt"):
        sql(conn, "salt_ions", [{"ingredient_id": 1, "g": 1}], 10)
    with pytest.raises(Exception, match="above 0"):
        sql(conn, "salt_ions", [{"ingredient_id": ids["gypsum"], "g": 1}], 0)


# ---- volumes ----

def test_volumes_add_up(conn, ids):
    """A12: b01's step 10 on the default profile: strike + sparge = total = pre-boil + kg x 1.0; sugars count in none."""
    inp = step10_input(conn, "b01")
    step10 = compute(conn, inp)
    v = sql(conn, "water_volumes", inp["profile"], step10)
    kg = sum(f["kg"] for f in step10["fermentables"])
    preboil = conn.execute("select app.preboil_volume(%s::numeric, %s::numeric, %s::numeric, %s::numeric)",
                           (step10["batch"]["volume_l"], step10["boil"]["boil_min"],
                            step10["batch"]["boil_off_l_h"], step10["batch"]["losses_l"])).fetchone()[0]
    assert v["grist_kg"] == pytest.approx(kg)
    assert v["total_l"] == pytest.approx(float(preboil) + kg * 1.0, abs=0.01)
    assert v["strike_l"] == pytest.approx(kg * v["ratio_l_kg"], abs=0.01)
    assert v["strike_l"] + v["sparge_l"] == pytest.approx(v["total_l"])
    assert v["ratio_l_kg"] == 3 and v["sparge_l"] > 0
    with_sugar = copy.deepcopy(step10)
    with_sugar["fermentables"].append({"ingredient_id": ids["Brown Candi Sugar"], "name": "Brown Candi Sugar",
                                       "kg": 1.0, "pct": 15, "usage": "boil"})
    assert sql(conn, "water_volumes", inp["profile"], with_sugar) == v
    # a high-gravity case: ten times the grist, strike would exceed the total
    big = copy.deepcopy(step10)
    for f in big["fermentables"]:
        f["kg"] = f["kg"] * 10
    bv = sql(conn, "water_volumes", inp["profile"], big)
    assert bv["strike_l"] == bv["total_l"] and bv["sparge_l"] == 0
    assert "no sparge" in bv["because"]


# ---- aim, salts ----

ROW = "ale-medium-pale-assertive"   # sulfate [100,400], chloride [0,100], calcium from 50


def test_aim_moves_with_hints(conn):
    none = sql(conn, "water_aim", ROW, [])
    bitter = sql(conn, "water_aim", ROW, ["bitter"])
    malty = sql(conn, "water_aim", ROW, ["malty"])
    both = sql(conn, "water_aim", ROW, ["bitter", "malty"])
    assert (none["so4"], none["cl"]) == (250, 50)
    assert (bitter["so4"], bitter["cl"]) == (362.5, 12.5)
    assert (malty["so4"], malty["cl"]) == (137.5, 87.5)
    assert (both["so4"], both["cl"]) == (250, 50)
    assert any("together" in m for m in both["moved_by"]) and bitter["moved_by"] and not none["moved_by"]
    assert sql(conn, "water_aim", ROW, ["darker", "session"])["so4"] == 250   # hints that do not move the ions
    assert none["ca"] == 50 and none["alkalinity"] == {"low": 40, "high": 120} and none["ra"] == {"low": -30, "high": 30}


def test_aims_stay_under_the_caps(conn):
    """HTB p. 135: sulfate <= 400, chloride <= 150, together <= 500, for every row at both hint extremes."""
    for (code,) in conn.execute("select code from ref.water_profile").fetchall():
        for hints in (["bitter"], ["malty"], []):
            aim = sql(conn, "water_aim", code, hints)
            assert aim["so4"] <= 400 and aim["cl"] <= 150 and aim["so4"] + aim["cl"] <= 500, (code, hints)


def test_salts_never_negative(conn):
    """A source water above every aim gets no salt."""
    aim = sql(conn, "water_aim", ROW, [])
    out = sql(conn, "salt_additions", ions_of(ca=80, so4=900, cl=900), aim, ROW, 15, 15)
    assert out["salts"] == [] and out["none_needed"] is True
    assert out["strike_water"]["ions"]["so4"] == pytest.approx(900)
    # only one side needed: chloride from the source, sulfate added
    one = sql(conn, "salt_additions", ions_of(ca=80, cl=900), aim, ROW, 15, 15)
    assert [s["name"] for s in one["salts"]] == ["gypsum"] and one["none_needed"] is False


def test_salts_reach_the_aim_in_both_waters(conn):
    aim = sql(conn, "water_aim", ROW, [])
    out = sql(conn, "salt_additions", DISTILLED, aim, ROW, 17, 16)
    for water in ("strike_water", "sparge_water"):
        assert out[water]["ions"]["so4"] == pytest.approx(250, abs=2)
        assert out[water]["ions"]["cl"] == pytest.approx(50, abs=2)
    for s in out["salts"]:
        assert s["strike_g"] * 10 == pytest.approx(round(s["strike_g"] * 10)) and s["total_g"] == pytest.approx(s["strike_g"] + s["sparge_g"])
    # no sparge: the sparge water is just the source water
    none = sql(conn, "salt_additions", DISTILLED, aim, ROW, 17, 0)
    assert all(s["sparge_g"] == 0 for s in none["salts"]) and none["sparge_water"]["ions"]["so4"] == 0


def test_calcium_brought_to_minimum(conn):
    row = "ale-medium-pale-soft"   # calcium from 50, sulfate [0,50], chloride [0,100]; the middle aims give Ca about 39
    aim = sql(conn, "water_aim", row, [])
    out = sql(conn, "salt_additions", DISTILLED, aim, row, 100, 0)
    ions = out["strike_water"]["ions"]
    assert ions["ca"] == pytest.approx(50, abs=1) and ions["so4"] > 25 and ions["cl"] > 50
    assert ions["so4"] <= 50 and ions["cl"] <= 100
    assert any("raised" in n for n in out["notes"])
    # sulfate and chloride reach the row's maximum first: calcium stays below and says so
    low = sql(conn, "salt_additions", DISTILLED, {**aim, "so4": 5, "cl": 5}, row, 100, 0)
    assert low["strike_water"]["ions"]["so4"] <= 50.5 and low["strike_water"]["ions"]["ca"] < 50
    assert any("calcium below the row" in n for n in low["notes"])


def test_calcium_above_the_row_is_reported_not_corrected(conn):
    row = "lager-medium-pale"   # calcium [50,75]; bitter aims sulfate 137.5, chloride 56.25 give Ca about 89
    aim = sql(conn, "water_aim", row, ["bitter"])
    out = sql(conn, "salt_additions", DISTILLED, aim, row, 100, 0)
    assert out["strike_water"]["ions"]["ca"] > 75
    assert any(n.startswith("outside_row: calcium") for n in out["notes"])
    assert out["strike_water"]["ions"]["so4"] == pytest.approx(137.5, abs=1)


# ---- alkalinity ----

def test_alkalinity_follows_grist(conn, ids):
    """doc-calc §6: 4 kg Pilsen + 1 kg Caramel 60L + 1 kg roast in 18 L of distilled water needs
    0.2314 g/L baking soda (4.2 g), after which the estimate reads 5.400; a pale grist needs none."""
    grist = [pilsen(4), caramel60(1), roast(1)]
    dose = sql(conn, "alkalinity_dose", grist, DISTILLED, 18, 5.4)
    assert dose["ra_needed_meq_l"] == pytest.approx(2.754, abs=0.005)
    assert [(s["name"], s["strike_g"]) for s in dose["salts"]] == [("baking soda", 4.2)]
    dosed = sql(conn, "salt_ions", [{"ingredient_id": s["ingredient_id"], "g": s["strike_g"]} for s in dose["salts"]], 18)
    assert dosed["na"] == pytest.approx(63.3, abs=1.5)
    after = sql(conn, "mash_ph_estimate", grist, dosed, 18, "brown/black")
    assert after["ph"] == pytest.approx(5.4, abs=0.01)
    pale = sql(conn, "alkalinity_dose", [pilsen(4)], DISTILLED, 12, 5.2)
    assert pale["salts"] == [] and pale["ra_needed_meq_l"] == 0 and "already" in pale["because"]


def test_alkalinity_soda_then_lime(conn, ids):
    """A need above the 100 mg/L sodium cap: soda up to the cap, slaked lime for the rest."""
    grist = [pilsen(4), roast(3)]
    dose = sql(conn, "alkalinity_dose", grist, DISTILLED, 18, 5.4)
    by_name = {s["name"]: s["strike_g"] for s in dose["salts"]}
    assert set(by_name) == {"baking soda", "slaked lime"}
    dosed = sql(conn, "salt_ions", [{"ingredient_id": s["ingredient_id"], "g": s["strike_g"]} for s in dose["salts"]], 18)
    assert dosed["na"] <= 100 and dosed["na"] > 95
    after = sql(conn, "mash_ph_estimate", grist, dosed, 18, "brown/black")
    assert after["ph"] == pytest.approx(5.4, abs=0.01)
    # the source water's own sodium counts toward the cap
    salty = sql(conn, "alkalinity_dose", grist, ions_of(na=100), 18, 5.4)
    assert [s["name"] for s in salty["salts"]] == ["slaked lime"]


def test_alkalinity_only_in_strike(conn, ids):
    """Dark grist on distilled water: the dose names strike grams only, and the flavour salts add no alkalinity."""
    grist = [pilsen(4), roast(3)]
    dose = sql(conn, "alkalinity_dose", grist, DISTILLED, 18, 5.4)
    assert all(set(s) == {"ingredient_id", "name", "strike_g"} for s in dose["salts"])
    aim = sql(conn, "water_aim", "ale-medium-brown-black", [])
    out = sql(conn, "salt_additions", DISTILLED, aim, "ale-medium-brown-black", 18, 15)
    assert out["sparge_water"]["ions"]["hco3"] == 0 and out["sparge_water"]["alkalinity_ppm"] == 0
    assert out["strike_water"]["ions"]["hco3"] == 0 and out["strike_water"]["ions"]["na"] == 0


def test_row_ranges_are_references(conn):
    """A source water outside the row's alkalinity range is noted and nothing extra is dosed for it."""
    row = "lager-light-pale"   # alkalinity [0,40]
    hard = ions_of(ca=60, hco3=300)   # alkalinity 246 as CaCO3
    aim = sql(conn, "water_aim", row, [])
    out = sql(conn, "salt_additions", hard, aim, row, 12, 15)
    assert any(n.startswith("outside_row: alkalinity") for n in out["notes"])
    assert not any(s["name"] in ("baking soda", "slaked lime") for s in out["salts"])
    dose = sql(conn, "alkalinity_dose", [pilsen(4)], out["strike_water"]["ions"], 12, 5.2)
    assert dose["salts"] == []
    # a water inside the row has no such note
    soft = sql(conn, "salt_additions", ions_of(ca=60, hco3=20), aim, row, 12, 15)
    assert not any(n.startswith("outside_row: alkalinity") for n in soft["notes"])


# ---- mash pH ----

def test_pale_grist_needs_acid(conn, ids):
    """A10, doc-calc §7: 4.0 kg Pilsen, 12 L, light-lager aim (Ca 52.82, sulfate 25, chloride 75): pH 5.573, above the pale target."""
    ph = sql(conn, "mash_ph_estimate", [pilsen(4)], ions_of(ca=52.82, so4=25, cl=75), 12, "pale")
    assert ph["ph"] == pytest.approx(5.573, abs=0.02)
    assert ph["ph"] > ph["target_high"] == 5.4 and ph["target_low"] == 5.2


def test_dark_grist_on_distilled_is_low(conn):
    """doc-calc §7: 4 kg Pilsen + 1 kg Caramel 60L + 1 kg roast on distilled water: 5.193; the b05-style grist 5.30."""
    ph = sql(conn, "mash_ph_estimate", [pilsen(4), caramel60(1), roast(1)], DISTILLED, 18, "brown/black")
    assert ph["ph"] == pytest.approx(5.193, abs=0.01) and ph["ph"] < 5.4
    assert (ph["target_low"], ph["target_high"]) == (5.4, 5.6)
    b05 = sql(conn, "mash_ph_estimate", [pilsen(6.4), caramel60(0.8), roast(0.8)], ions_of(ca=60), 24, "brown/black")
    assert b05["ph"] == pytest.approx(5.30, abs=0.02)


def test_targets_by_colour(conn):
    targets = {c: sql(conn, "mash_ph_estimate", [pilsen(4)], DISTILLED, 12, c) for c in ("pale", "amber", "brown/black", None)}
    assert [(t["target_low"], t["target_high"]) for t in targets.values()] == [(5.2, 5.4), (5.3, 5.5), (5.4, 5.6), (5.2, 5.6)]
    with pytest.raises(Exception, match="unknown colour"):
        sql(conn, "mash_ph_estimate", [pilsen(4)], DISTILLED, 12, "green")


def test_ph_terms_add_up(conn):
    ph = sql(conn, "mash_ph_estimate", [pilsen(4), caramel60(1), roast(1)], ions_of(ca=50, hco3=80), 18, "amber")
    assert sum(t["meq"] for t in ph["terms"]) / sum(t["buffer"] for t in ph["terms"]) + 5.4 == pytest.approx(ph["ph"], abs=0.001)
    assert [t["what"] for t in ph["terms"]] == ["strike water", "Pilsen", "Caramel 60L", "Roast"]
    assert sum(t["buffer"] for t in ph["terms"]) == pytest.approx(40 * 6)


def test_malt_acidity_classes(conn):
    assert sql(conn, "malt_acidity", "base", 3)["meq_kg"] == 9.2                 # 1.5 degL: Pilsen Malt
    assert sql(conn, "malt_acidity", "kilned", 40 * 1.97)["class"] in ("Caramel 40L", "Special Roast")
    assert sql(conn, "malt_acidity", "crystal", 61 * 1.97)["meq_kg"] == -43.4
    assert sql(conn, "malt_acidity", "adjunct", 4)["meq_kg"] == 5.0              # flaked grain counts as base: Brewers Malt
    assert sql(conn, "malt_acidity", "roast", 600)["meq_kg"] == -42.98
    assert sql(conn, "malt_acidity", "sugar", None) == {"class": "sugar (not mashed)", "meq_kg": 0, "buffer": 0,
                                                         "page": "How to Brew Table 21.4, p. 351"}
    with pytest.raises(Exception, match="unknown role"):
        sql(conn, "malt_acidity", "hop", 3)


# ---- step 12 (Task 4) ----

STEP12_BRIEFS = ["b01", "b05", "b08", "b13", "b16"]


def step12_input(conn, bid):
    """The step12.input object for one brief: its step 10 output computed from the first good proposal."""
    inp = step10_input(conn, bid)
    return {"run_id": 0, "brief": inp["brief"], "profile": inp["profile"], "targets": inp["targets"],
            "step10": compute(conn, inp)}


@pytest.fixture(scope="module")
def step12(conn):
    cache = {}

    def run(bid):
        if bid not in cache:
            i = step12_input(conn, bid)
            cache[bid] = (i, sql(conn, "step12_water", i["profile"], i["targets"], i["brief"], i["step10"]))
        return copy.deepcopy(cache[bid])
    return run


@pytest.mark.parametrize("bid", STEP12_BRIEFS)
def test_step12_names_its_row(conn, step12, bid):
    """A9: the target row is the style's water_profile, with its page, basis and the references."""
    i, out = step12(bid)
    code = i["targets"]["style"]["code"]
    row, basis = conn.execute("select water_profile, water_basis from ref.beer_style where code = %s", (code,)).fetchone()
    assert row is not None, code
    t = out["target"]
    assert t["from"] == "style" and t["style_code"] == code and t["row"] == row and t["page"]
    assert t["basis"] == basis and t["fallback"] == (basis != "listed")
    assert set(t["ranges"]) == {"ca", "alkalinity", "so4", "cl", "ra"}
    assert t["ranges"]["so4"]["low"] is not None


@pytest.mark.parametrize("bid", ["b01", "b08", "b14"])
def test_step12_volumes_are_step13s(conn, step12, bid):
    """A12: step 12 doses for the volumes app.water_volumes gives (step 13 outputs the same function's)."""
    i, out = step12(bid)
    assert out["volumes"] == sql(conn, "water_volumes", i["profile"], i["step10"])
    for s in out["salts"]:
        assert s["total_g"] == pytest.approx(s["strike_g"] + s["sparge_g"])


def test_step12_b08_needs_acid(conn, step12):
    """A10 through the step: b08's pale grist on distilled water is above the pale target; the line says acid, no amount."""
    _, out = step12("b08")
    assert out["mash_ph"]["ph"] > out["mash_ph"]["target_high"]
    assert out["acid"]["needed"] is True
    assert "acid would be needed" in out["acid"]["text"] and str(round(out["mash_ph"]["ph"], 2)) in out["acid"]["text"]
    assert set(out["acid"]) == {"needed", "text", "acidify"}


def keys_of(value):
    """Every dict key in a JSON value, at any depth, with the string values beside it."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield k, v
            yield from keys_of(v)
    elif isinstance(value, list):
        for v in value:
            yield from keys_of(v)


@pytest.mark.parametrize("bid", STEP12_BRIEFS)
def test_no_acid_amount_anywhere(conn, step12, bid):
    """A10: no key named *acid*_g or *_ml, and no acid among the salts, in steps 12 and 13. (Steps 14-15 add theirs in Tasks 6-7.)"""
    i, out = step12(bid)
    out13 = sql(conn, "step13_mash_boil", i["profile"], i["targets"], i["step10"])
    for k, v in list(keys_of(out)) + list(keys_of(out13)):
        assert not re.search(r"acid.*_g$|_ml$", k), k
        if k == "name" and isinstance(v, str):
            assert "acid" not in v.lower() or v == "ferulic acid rest", v
    assert {s["name"] for s in out["salts"]} <= {"gypsum", "calcium chloride", "baking soda", "slaked lime"}


def bjcp_cities():
    """The 8-city table of the BJCP study guide (ppm), read from the file at test time and never stored."""
    text = (Path(__file__).resolve().parent.parent / "shared" / "rag-files" / "water" / "bjcp_study_guide_water.md").read_text()
    cities = {}
    for m in re.finditer(r"^\| (Plzen|Dortmund|Munich|Vienna|Burton|Dublin|Edinburgh|London) \|([^\n]*)$", text, re.M):
        ca, mg, na, so4, hco3, cl = (float(x) for x in m.group(2).strip().strip("|").split("|"))
        cities[m.group(1)] = {"ca": ca, "mg": mg, "so4": so4, "cl": cl,
                              "ra": hco3 * 50 / 61.017 - ca / 1.4 - mg / 1.7, "alk": hco3 * 50 / 61.017}
    assert len(cities) == 8
    return cities


def test_targets_agree_with_bjcp_cities(conn):
    """A9, doc-calc §15: comparisons between the mapped styles' rows and the famous brewing waters."""
    city = bjcp_cities()

    def row_of(code):
        return conn.execute("select water_profile from ref.beer_style where code = %s", (code,)).fetchone()[0]

    def aim(code):
        return sql(conn, "water_aim", row_of(code), [])

    def ra_mid(code):
        lo, hi = conn.execute("select lower(ra), upper(ra) from ref.water_profile where code = %s", (row_of(code),)).fetchone()
        return (lo + hi) / 2

    assert aim("3B")["so4"] < aim("21A")["so4"] and city["Plzen"]["so4"] < city["Burton"]["so4"]
    assert aim("5D")["so4"] > aim("5D")["cl"] and city["Dortmund"]["so4"] > city["Dortmund"]["cl"]
    assert aim("21A")["so4"] >= 4 * aim("21A")["cl"] and city["Burton"]["so4"] > 10 * city["Burton"]["cl"]
    assert city["Plzen"]["ra"] < city["Vienna"]["ra"] < city["Munich"]["ra"]
    assert ra_mid("3B") < ra_mid("6A") < ra_mid("8B")
    lo, hi = conn.execute("select lower(ra), upper(ra) from ref.water_profile where code = %s", (row_of("14B"),)).fetchone()
    assert lo <= city["Edinburgh"]["ra"] <= hi
    assert aim("13C")["so4"] < aim("21A")["so4"] and city["London"]["so4"] < city["Burton"]["so4"]


def test_unmapped_style_has_no_salts(conn):
    """Decision Q1: a style with no water row gets no salts; the waters are the source water and the pH is still estimated."""
    i = step12_input(conn, "b01")
    code = conn.execute("select code from ref.beer_style where water_profile is null and code = '1A'").fetchone()[0]
    i["targets"]["style"] = dict(i["targets"]["style"], code=code)
    out = sql(conn, "step12_water", i["profile"], i["targets"], i["brief"], i["step10"])
    assert out["target"]["from"] == "none" and out["target"]["row"] is None and out["target"]["style_code"] == code
    assert out["salts"] == [] and out["none_needed"] is True
    assert any("has no water row" in v["because"] for v in out["values_used"])
    assert out["strike_water"]["ions"] == out["sparge_water"]["ions"]
    assert {k: out["strike_water"]["ions"][k] for k in out["source_water"]["ions"]} == out["source_water"]["ions"]
    assert out["mash_ph"]["ph"] > 0 and out["acid"]["needed"] in (True, False)


@pytest.mark.parametrize("bid", STEP12_BRIEFS)
def test_step12_meets_contract(conn, step12, bid):
    i, out = step12(bid)
    assert errors(conn, "step12.input", i) == []
    assert errors(conn, "step12.output", out) == []


def test_step12_same_input_same_output(conn):
    i = step12_input(conn, "b05")
    a = sql(conn, "step12_water", i["profile"], i["targets"], i["brief"], i["step10"])
    b = sql(conn, "step12_water", i["profile"], i["targets"], i["brief"], i["step10"])
    assert a == b
