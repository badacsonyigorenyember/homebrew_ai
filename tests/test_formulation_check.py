"""The recipe check (Tasks 6 and 7 of s2-formulation-rules): inputs, numbers and rules 1-6, 8-13."""

import json
import re

import pytest

from loaders.db import connect

CONTRACTS = "shared/contracts/formulation_check.%s.schema.json"
EXEMPT = {"crystal", "target"}  # rule vocabulary that is also a hop name (as in test_formulation_rules)

# producer, name for each fermentable the tests use
PILSNER = ("Weyermann", "Pilsner Malt")
VIENNA = ("Weyermann", "Vienna Malt")
PALE = ("Weyermann", "Pale Ale Malt")
WHEAT = ("Weyermann", "Wheat Malt Pale")
RYE = ("Weyermann", "Rye Malt Pale")
SPELT = ("Weyermann", "Spelt Malt")
CARAHELL = ("Weyermann", "Carahell")
CARARED = ("Weyermann", "Carared")
CARAAMBER = ("Weyermann", "Caraamber")
CARAMUNICH1 = ("Weyermann", "Caramunich Type 1")
CARAMUNICH2 = ("Weyermann", "Caramunich Type 2")
CARAAROMA = ("Weyermann", "Caraaroma")
MUNICH1 = ("Weyermann", "Munich Malt Type 1")
MUNICH2 = ("Weyermann", "Munich Malt Type 2")
CHOC_LIGHT = ("Viking Malt", "Chocolate Light Malt")
CARAFA1 = ("Weyermann", "Carafa Type 1")
CARAFA2 = ("Weyermann", "Carafa Type 2")
RICE = ("", "Flaked Rice")
CORN = ("", "Flaked Corn")
LACTOSE = ("", "Lactose")
US05 = ("Fermentis", "SafAle US-05")


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def ing(conn, kind, producer_name):
    producer, name = producer_name
    row = conn.execute(
        "select id from ref.ingredient where kind = %s and producer = %s and name = %s",
        (kind, producer, name),
    ).fetchone()
    assert row, f"{producer} {name} not in ref.ingredient"
    return row[0]


def recipe(conn, fermentables, hops=("Magnum", "Saaz"), boil_min=90, **over):
    """A recipe with the base settings; `fermentables` is a list of ((producer, name), pct)."""
    hop_items = []
    for i, name in enumerate(hops):
        hop_items.append({
            "ingredient_id": hop_id(conn, name),
            "usage": "boil", "minutes": boil_min if i == 0 else 10, "purpose": "bittering" if i == 0 else "flavour",
            "g": 20,
        })
    base = {
        "style_code": "18A", "guidance": True, "stated": {},
        "targets": {"og": 1.046, "fg": 1.0105, "abv": 4.65, "ibu": 21.5, "srm": 4.5},  # 18A midpoints
        "batch": {"volume_l": 20, "efficiency_pct": 72, "boil_off_l_h": 4, "losses_l": 2},
        "mash_c": 66.5, "boil_min": boil_min,
        "fermentables": [
            {"ingredient_id": ing(conn, "fermentable", pn), "pct": pct, "purpose": "grist"}
            for pn, pct in fermentables
        ],
        "hops": hop_items,
        "yeast": {"ingredient_id": ing(conn, "yeast", US05), "ferm_c": 19, "purpose": "clean fermentation"},
    }
    base.update(over)
    return base


def hop_id(conn, name):
    return conn.execute("select id from ref.ingredient where kind = 'hop' and name = %s", (name,)).fetchone()[0]


def check(conn, recipe_json):
    return conn.execute("select app.check_recipe(%s::jsonb)", (json.dumps(recipe_json),)).fetchone()[0]


def result(out, rule):
    return next(r for r in out["results"] if r["rule"] == rule)


RULES = [1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13]
BASE = [(PILSNER, 85), (CARAHELL, 10), (MUNICH1, 5)]

# (rule, label, fermentables, hops) - each fails exactly its own rule among rules 1-6
FAILING = [
    (1, "six fermentables",
     [(PILSNER, 25), (VIENNA, 25), (PALE, 20), (WHEAT, 10), (RYE, 10), (SPELT, 10)], ("Magnum", "Saaz")),
    (1, "four specialty",
     [(PILSNER, 80), (CARAHELL, 5), (CARARED, 5), (MUNICH1, 5), (MUNICH2, 5)], ("Magnum", "Saaz")),
    (2, "four hops", BASE, ("Magnum", "Saaz", "Cascade", "Citra")),
    (3, "roast 20 %", [(PILSNER, 80), (CHOC_LIGHT, 10), (CARAFA1, 5), (CARAFA2, 5)], ("Magnum", "Saaz")),
    (4, "crystal 30 %", [(PILSNER, 70), (CARAHELL, 15), (CARARED, 15)], ("Magnum", "Saaz")),
    (4, "crystal above 60 EBC 11 %", [(PILSNER, 89), (CARAMUNICH1, 5.5), (CARAMUNICH2, 5.5)], ("Magnum", "Saaz")),
    (4, "crystal above 160 EBC 6 %", [(PILSNER, 94), (CARAAROMA, 6)], ("Magnum", "Saaz")),
    (5, "adjunct and sugar 45 %", [(PILSNER, 55), (RICE, 25), (CORN, 20)], ("Magnum", "Saaz")),
    (6, "Carahell 20 % against max 15", [(PILSNER, 80), (CARAHELL, 20)], ("Magnum", "Saaz")),
]
PASSING = [
    (1, "five fermentables, three specialty",
     [(PILSNER, 60), (VIENNA, 20), (CARAHELL, 10), (CARARED, 5), (MUNICH1, 5)], ("Magnum", "Saaz", "Cascade")),
    (3, "roast at 15 %", [(PILSNER, 85), (CHOC_LIGHT, 10), (CARAFA1, 5)], ("Magnum", "Saaz")),
    (4, "crystal at 25 %", [(PILSNER, 75), (CARAHELL, 15), (CARARED, 10)], ("Magnum", "Saaz")),
    (4, "crystal above 60 EBC at 10 %", [(PILSNER, 90), (CARAMUNICH2, 10)], ("Magnum", "Saaz")),
    (5, "adjunct and sugar at 40 %", [(PILSNER, 60), (RICE, 40)], ("Magnum", "Saaz")),
    (6, "Carahell at its max_pct", [(PILSNER, 85), (CARAHELL, 15)], ("Magnum", "Saaz")),
]


@pytest.mark.stack
def test_base_recipe_passes_all_rules(conn):
    out = check(conn, recipe(conn, BASE))
    assert [r["rule"] for r in out["results"]] == RULES
    assert [r["status"] for r in out["results"]] == ["pass"] * 12
    assert out["calc_version"] == conn.execute("select app.calc_version()").fetchone()[0]


@pytest.mark.stack
@pytest.mark.parametrize("rule,label,ferm,hops", FAILING, ids=[f"{r}-{l}" for r, l, _, _ in FAILING])
def test_rule_fails_alone(conn, rule, label, ferm, hops):
    out = check(conn, recipe(conn, ferm, hops))
    statuses = {r["rule"]: r["status"] for r in out["results"]}
    assert statuses[rule] == "fail"
    assert {k: v for k, v in statuses.items() if k != rule} == {k: "pass" for k in statuses if k != rule}


@pytest.mark.stack
@pytest.mark.parametrize("rule,label,ferm,hops", PASSING, ids=[f"{r}-{l}" for r, l, _, _ in PASSING])
def test_rule_passes_at_its_limit(conn, rule, label, ferm, hops):
    out = check(conn, recipe(conn, ferm, hops))
    assert [r["status"] for r in out["results"]] == ["pass"] * 12, label


@pytest.mark.stack
def test_just_above_the_crystal_limit_fails(conn):
    out = check(conn, recipe(conn, [(PILSNER, 74.5), (CARAHELL, 15), (CARARED, 10.5)]))
    assert result(out, 4)["status"] == "fail"


@pytest.mark.stack
def test_rules_3_and_4_agree_on_caraamber(conn):
    """Caraamber [60,80] has colour 70, above 60; Carared [40,60] has 50, not above."""
    amber = check(conn, recipe(conn, [(PILSNER, 89), (CARAAMBER, 6), (CARAMUNICH1, 5)]))
    carared = check(conn, recipe(conn, [(PILSNER, 89), (CARARED, 6), (CARAMUNICH1, 5)]))
    assert result(amber, 4)["status"] == "fail"  # 6 + 5 = 11 above 60 EBC
    assert result(carared, 4)["status"] == "pass"  # only the 5 counts


@pytest.mark.stack
def test_failure_names_rule_items_value_limit(conn):
    out = check(conn, recipe(conn, [(PILSNER, 80), (CHOC_LIGHT, 10), (CARAFA1, 5), (CARAFA2, 5)]))
    r = result(out, 3)
    assert r["message"].startswith("Rule 3:")
    for text in ("Chocolate Light Malt 10 %", "Carafa Type 1 5 %", "Carafa Type 2 5 %", "20 %", "15 %"):
        assert text in r["message"]
    failure = r["failures"][0]
    assert failure["value"] == 20 and failure["limit"] == 15
    assert {i["name"] for i in failure["items"]} == {"Chocolate Light Malt", "Carafa Type 1", "Carafa Type 2"}
    assert all(isinstance(i["ingredient_id"], int) for i in failure["items"])

    six = result(check(conn, recipe(conn, FAILING[0][2])), 1)
    assert "6" in six["message"] and "limit is 5" in six["message"]


@pytest.mark.stack
def test_failure_names_no_other_ingredient(conn):
    names = {r[0] for r in conn.execute("select name from ref.ingredient")}
    names |= {r[0] for r in conn.execute("select name from ref.beer_style")}
    for rule, label, ferm, hops in FAILING:
        rec = recipe(conn, ferm, hops)
        in_recipe = {
            conn.execute("select name from ref.ingredient where id = %s", (i["ingredient_id"],)).fetchone()[0]
            for i in rec["fermentables"] + rec["hops"] + [rec["yeast"]]
        }
        for r in check(conn, rec)["results"]:
            message = r["message"]
            for own in sorted(in_recipe, key=len, reverse=True):  # "Rye Malt Pale" must not hit "Rye Malt"
                message = message.replace(own, "")
            for name in {n for n in names - in_recipe if n.lower() not in EXEMPT}:
                found = re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", message, re.IGNORECASE)
                assert not found, f"{label}: rule {r['rule']} message names {name}"


@pytest.mark.stack
def test_unknown_when_a_field_is_missing(conn):
    ferm = {"ingredient_id": 1, "name": "X", "pct": 10, "role": "crystal", "ebc_mid": None, "max_pct": None}
    items = {"fermentables": [ferm], "hops": []}
    six = conn.execute("select app.check_rule_6(%s::jsonb)", (json.dumps(items),)).fetchone()[0]
    assert six["status"] == "unknown" and "ref.fermentable.max_pct" in six["message"]
    for n in (3, 4):
        r = conn.execute(f"select app.check_rule_{n}(%s::jsonb)", (json.dumps(items),)).fetchone()[0]
        assert r["status"] == "unknown" and r["missing"] == ["ref.fermentable.ebc"]


def s1_numbers(conn, rec):
    """OG, FG, ABV, SRM, IBU from direct calls of the s1 functions on the same inputs."""
    grist = []
    for f in rec["fermentables"]:
        role, extract, ferment, ebc = conn.execute(
            "select role, extract_dbfg_pct, fermentability, app.ebc_mid(ebc) "
            "from ref.fermentable where ingredient_id = %s", (f["ingredient_id"],)).fetchone()
        grist.append({"pct": f["pct"], "extract_pct": float(extract), "mashed": role != "sugar",
                      "fermentability": ferment, "ebc": float(ebc)})
    b = rec["batch"]
    solved = conn.execute("select app.solve_grist(%s::numeric, %s::jsonb, %s::numeric, %s::numeric)",
                          (rec["targets"]["og"], json.dumps(grist), b["efficiency_pct"], b["volume_l"])).fetchone()[0]
    attenuation = 80  # SafAle US-05 [78,82] at 66.5 C: the middle of the range
    og = conn.execute("select app.og(%s::jsonb, %s::numeric, %s::numeric)", (json.dumps(solved), b["efficiency_pct"], b["volume_l"])).fetchone()[0]
    fg = conn.execute("select app.fg(%s::jsonb, %s::numeric, %s::numeric, %s::numeric)",
                      (json.dumps(solved), b["efficiency_pct"], b["volume_l"], attenuation)).fetchone()[0]
    abv = conn.execute("select app.abv(%s::numeric, %s::numeric)", (og, fg)).fetchone()[0]
    srm = conn.execute("select app.srm(app.grist_mcu(%s::jsonb, %s::numeric))", (json.dumps(solved), b["volume_l"])).fetchone()[0]
    preboil = conn.execute("select app.preboil_volume(%s::numeric, %s::numeric, %s::numeric, %s::numeric)",
                           (b["volume_l"], rec["boil_min"], b["boil_off_l_h"], b["losses_l"])).fetchone()[0]
    boil_sg = conn.execute("select app.boil_gravity(%s::numeric, %s::numeric, %s::numeric)", (og, b["volume_l"] + b["losses_l"], preboil)).fetchone()[0]
    hops = []
    for h in rec["hops"]:
        alpha = conn.execute("select app.ebc_mid(alpha_pct) from ref.hop where ingredient_id = %s",
                             (h["ingredient_id"],)).fetchone()[0]
        hops.append({"g": h["g"], "alpha_pct": float(alpha), "minutes": h["minutes"], "usage": h["usage"]})
    ibu = conn.execute("select app.ibu(%s::jsonb, %s::numeric, %s::numeric)", (json.dumps(hops), boil_sg, b["volume_l"])).fetchone()[0]
    return {"og": og, "fg": fg, "abv": abv, "srm": srm, "ibu": ibu}


@pytest.mark.stack
def test_numbers_equal_s1(conn):
    rec = recipe(conn, [(PILSNER, 80), (CARAHELL, 10), (CARAMUNICH1, 5), (CHOC_LIGHT, 5)])
    numbers = check(conn, rec)["numbers"]
    expected = s1_numbers(conn, rec)
    for key, value in expected.items():
        assert numbers[key] == pytest.approx(float(value), rel=1e-9), key
    assert numbers["og"] == pytest.approx(1.046, abs=0.001)
    assert numbers["attenuation_pct"] == pytest.approx(80)
    assert numbers["missing"] == []


@pytest.mark.stack
def test_lactose_raises_fg(conn):
    plain = check(conn, recipe(conn, [(PILSNER, 100)]))["numbers"]["fg"]
    lactose = check(conn, recipe(conn, [(PILSNER, 92), (LACTOSE, 8)]))["numbers"]["fg"]
    assert lactose > plain


@pytest.mark.stack
def test_missing_inputs_give_null_numbers(conn):
    rec = recipe(conn, BASE)
    for h in rec["hops"]:
        del h["g"]
    numbers = check(conn, rec)["numbers"]
    assert numbers["ibu"] is None and "hops.g" in numbers["missing"]
    gozdawa = conn.execute(
        "select id from ref.ingredient where kind = 'yeast' and producer = 'Gozdawa' and name = 'W-34/70'").fetchone()[0]
    rec["yeast"]["ingredient_id"] = gozdawa
    numbers = check(conn, rec)["numbers"]
    assert numbers["fg"] is None and numbers["abv"] is None
    assert "ref.yeast.attenuation_pct" in numbers["missing"]
    # a fermentable with no colour leaves SRM null (Flaked Rice has no ebc)
    numbers = check(conn, recipe(conn, [(PILSNER, 70), (RICE, 30)]))["numbers"]
    assert numbers["srm"] is None and "ref.fermentable.ebc" in numbers["missing"]


def schema_errors(conn, name, value):
    schema = open(CONTRACTS % name).read()
    return conn.execute(
        "select coalesce(extensions.jsonschema_validation_errors(%s::json, %s::json), '{}')",
        (schema, json.dumps(value))).fetchone()[0]


@pytest.mark.stack
def test_input_and_output_match_schemas(conn):
    rec = recipe(conn, BASE)
    assert schema_errors(conn, "input", rec) == []
    assert schema_errors(conn, "output", check(conn, rec)) == []
    rec["yeast"]["ingredient_id"] = ing(conn, "yeast", ("Gozdawa", "W-34/70"))
    assert schema_errors(conn, "output", check(conn, rec)) == []  # nulls and missing[] are allowed


@pytest.mark.stack
def test_ebc_mid(conn):
    def mid(range_text):
        return conn.execute("select app.ebc_mid(%s::numrange)", (range_text,)).fetchone()[0]

    assert float(mid("[60,80]")) == 70  # above 60 EBC
    assert float(mid("[40,60]")) == 50  # not above 60 EBC
    assert float(mid("(,8]")) == 8
    assert float(mid("[350,)")) == 350
    assert mid(None) is None


@pytest.mark.stack
def test_bad_input_raises(conn):
    import psycopg

    def raises(rec, text):
        with pytest.raises(psycopg.errors.RaiseException, match=text):
            check(conn, rec)
        conn.rollback()

    good = recipe(conn, BASE)
    raises({**good, "fermentables": [{**good["fermentables"][0], "ingredient_id": -1}] + good["fermentables"][1:]},
           "not a fermentable")
    hop = hop_id(conn, "Magnum")
    raises({**good, "fermentables": [{**good["fermentables"][0], "ingredient_id": hop}] + good["fermentables"][1:]},
           "not a fermentable")
    raises(recipe(conn, [(PILSNER, 85), (CARAHELL, 10)]),
           "add up to 95")
    raises({**good, "style_code": "99Z"}, "not in ref.beer_style")
    raises(recipe(conn, [(PILSNER, 50), (PILSNER, 50)]), "appears twice")
    raises({**good, "hops": [{**good["hops"][0], "ingredient_id": good["fermentables"][0]["ingredient_id"]}]},
           "not a hop")


# --- Task 7: rules 8-13 ------------------------------------------------------------------------

def hop(conn, name, usage, minutes, purpose="hop", g=20):
    return {"ingredient_id": hop_id(conn, name), "usage": usage, "minutes": minutes, "purpose": purpose, "g": g}


def statuses(out):
    return {r["rule"]: r["status"] for r in out["results"]}


def only_rule_differs(out, rule, status):
    got = statuses(out)
    assert got[rule] == status, out["results"]
    assert {k: v for k, v in got.items() if k != rule} == {k: "pass" for k in got if k != rule}


@pytest.mark.stack
def test_results_cover_checked_rules(conn):
    out = check(conn, recipe(conn, BASE))
    assert [r["rule"] for r in out["results"]] == RULES and len(out["results"]) == 12


@pytest.mark.stack
def test_rule_8(conn):
    mag, saaz = "Magnum", "Saaz"
    two_bitter = [hop(conn, mag, "boil", 90), hop(conn, saaz, "boil", 90)]
    none = [hop(conn, saaz, "boil", 10)]
    mid = [hop(conn, mag, "boil", 90), hop(conn, saaz, "boil", 30)]
    late = [hop(conn, mag, "boil", 90), hop(conn, saaz, "boil", 15), hop(conn, saaz, "whirlpool", 20),
            hop(conn, saaz, "dry_hop", 4320)]
    for hops, status in ((two_bitter, "fail"), (none, "fail"), (mid, "fail"), (late, "pass")):
        out = check(conn, recipe(conn, BASE, hops=(), **{}) | {"hops": hops})
        only_rule_differs(out, 8, status)
    # the 60-minute hop in a 90-minute boil is not the bittering addition
    out = check(conn, recipe(conn, BASE) | {"hops": [hop(conn, mag, "boil", 60)]})
    assert statuses(out)[8] == "fail"


@pytest.mark.stack
def test_rule_9(conn):
    out = check(conn, recipe(conn, BASE))
    only_rule_differs(out, 9, "pass")
    # a stated ABV above the range (b17-like): OG and FG count as stated, so they may sit anywhere
    strong = recipe(conn, BASE, stated={"abv": 8.0}, targets={"og": 1.075, "fg": 1.015, "abv": 8.0, "ibu": 21.5, "srm": 4.5})
    assert result(check(conn, strong), 9)["status"] == "pass"
    # an unstated IBU off the midpoint fails
    off = recipe(conn, BASE)
    off["targets"]["ibu"] = 35
    out = check(conn, off)
    only_rule_differs(out, 9, "fail")
    assert "IBU" in result(out, 9)["message"]
    # the same IBU stated passes
    off["stated"] = {"ibu": 35}
    only_rule_differs(check(conn, off), 9, "pass")
    # an out-of-range SRM with guidance off passes
    dark = recipe(conn, BASE, guidance=False)
    dark["targets"]["srm"] = 30
    only_rule_differs(check(conn, dark), 9, "pass")
    dark["guidance"] = True
    only_rule_differs(check(conn, dark), 9, "fail")
    # tolerance: OG 0.001 off passes, 0.002 off fails
    near = recipe(conn, BASE)
    near["targets"]["og"] = 1.047
    only_rule_differs(check(conn, near), 9, "pass")
    near["targets"]["og"] = 1.0485
    only_rule_differs(check(conn, near), 9, "fail")


@pytest.mark.stack
def test_rule_9_unknown_without_style_range(conn):
    code = conn.execute("select code from ref.beer_style where ibu is null limit 1").fetchone()
    if code is None:
        pytest.skip("every style has an IBU range")
    out = check(conn, recipe(conn, BASE, style_code=code[0]))
    assert result(out, 9)["status"] == "unknown"


@pytest.mark.stack
def test_rule_10(conn):
    only_rule_differs(check(conn, recipe(conn, BASE)), 10, "pass")
    # the mash limits themselves pass; one degree outside fails and names the limit it crossed
    for mash in (64, 69):
        only_rule_differs(check(conn, recipe(conn, BASE, mash_c=mash)), 10, "pass")
    for mash, limit in ((63, 64), (70, 69)):
        out = check(conn, recipe(conn, BASE, mash_c=mash))
        only_rule_differs(out, 10, "fail")
        assert "between 64 and 69" in result(out, 10)["message"]
        failure = result(out, 10)["failures"][0]
        assert (failure["value"], failure["limit"]) == (mash, limit)
    # predicted FG outside the style range: a strong wort at 80 % attenuation ends above 1.013
    high_fg = recipe(conn, BASE, stated={"og": 1.075}, targets={"og": 1.075, "fg": 1.0105, "abv": 4.65, "ibu": 21.5, "srm": 4.5})
    out = check(conn, high_fg)
    only_rule_differs(out, 10, "fail")
    assert "predicted FG" in result(out, 10)["message"]
    # stated FG: the range is the target FG +- 0.002
    # (OG, FG and ABV are all stated, so rule 9 has nothing to check)
    stated = recipe(conn, BASE, stated={"og": 1.046, "fg": 1.020, "abv": 3.4},
                    targets={"og": 1.046, "fg": 1.020, "abv": 3.4, "ibu": 21.5, "srm": 4.5})
    only_rule_differs(check(conn, stated), 10, "fail")
    stated = recipe(conn, BASE, stated={"og": 1.046, "fg": 1.009, "abv": 4.8},
                    targets={"og": 1.046, "fg": 1.009, "abv": 4.8, "ibu": 21.5, "srm": 4.5})
    only_rule_differs(check(conn, stated), 10, "pass")
    # the band is the midpoint_tolerance.fg limit, not a literal: widen it and the stated 1.020 passes
    limits = conn.execute("select app.formulation_limits()").fetchone()[0]
    limits["midpoint_tolerance"]["fg"] = 0.05
    conn.execute(
        "create or replace function app.formulation_limits() returns jsonb language sql immutable "
        "as $f$ select %s::jsonb $f$" % ("'" + json.dumps(limits) + "'"))
    wide = recipe(conn, BASE, stated={"og": 1.046, "fg": 1.020, "abv": 3.4},
                  targets={"og": 1.046, "fg": 1.020, "abv": 3.4, "ibu": 21.5, "srm": 4.5})
    status = result(check(conn, wide), 10)["status"]
    conn.rollback()
    assert status == "pass"


@pytest.mark.stack
def test_rule_10_unknown_without_attenuation(conn):
    rec = recipe(conn, BASE)
    rec["yeast"]["ingredient_id"] = ing(conn, "yeast", ("Gozdawa", "W-34/70"))
    rec["yeast"]["ferm_c"] = 13
    r = result(check(conn, rec), 10)
    assert r["status"] == "unknown" and "ref.yeast.attenuation_pct" in r["message"]
    assert result(check(conn, rec), 11)["status"] == "unknown"


@pytest.mark.stack
def test_mash_mapping(conn):
    def att(mash):
        return conn.execute("select app.mash_attenuation('[78,82]'::numrange, %s::numeric)", (mash,)).fetchone()[0]

    assert (float(att(64)), float(att(69)), float(att(66.5))) == (82, 78, 80)
    text = conn.execute("select sentence from app.formulation_rules() where rule = '10'").fetchone()[0]
    assert "uncited assumption" in text
    assert check(conn, recipe(conn, BASE, mash_c=64))["numbers"]["attenuation_pct"] == pytest.approx(82)


@pytest.mark.stack
def test_rule_11(conn):
    assert result(check(conn, recipe(conn, BASE)), 11)["status"] == "pass"
    only_rule_differs(check(conn, recipe(conn, BASE)), 11, "pass")
    cold = recipe(conn, BASE)
    cold["yeast"]["ferm_c"] = 10
    out = check(conn, cold)
    only_rule_differs(out, 11, "fail")
    assert "fermentation temperature" in result(out, 11)["message"]
    cold["yeast"]["ferm_c"] = 18
    only_rule_differs(check(conn, cold), 11, "pass")
    tolerance = conn.execute(
        "select alcohol_tolerance_pct from ref.yeast where ingredient_id = %s", (ing(conn, "yeast", US05),)).fetchone()[0]
    strong = recipe(conn, [(PILSNER, 70), (RICE, 30)], targets={"og": 1.120, "fg": 1.020, "abv": 13, "ibu": 21.5, "srm": 4.5},
                    stated={"abv": 13})
    # state the predicted FG as the target, so rule 10 passes and only rule 11 is left to fail
    strong["targets"]["fg"] = round(check(conn, strong)["numbers"]["fg"], 4)
    out = check(conn, strong)
    only_rule_differs(out, 11, "fail")
    assert f"{tolerance:.0f} %" in result(out, 11)["message"]


@pytest.mark.stack
def test_rule_12(conn):
    for where in ("fermentables", "hops", "yeast"):
        rec = recipe(conn, BASE)
        target = rec[where] if where == "yeast" else rec[where][0]
        target["purpose"] = "   "
        out = check(conn, rec)
        only_rule_differs(out, 12, "fail")
    rec = recipe(conn, BASE)
    del rec["hops"][1]["purpose"]
    assert result(check(conn, rec), 12)["status"] == "fail"


@pytest.mark.stack
def test_rule_13(conn):
    out = check(conn, recipe(conn, BASE, boil_min=60))
    only_rule_differs(out, 13, "fail")
    assert "Pilsner Malt needs at least 90 min" in result(out, 13)["message"]
    only_rule_differs(check(conn, recipe(conn, BASE, boil_min=90)), 13, "pass")
    no_pilsner = recipe(conn, [(VIENNA, 100)], boil_min=60)
    only_rule_differs(check(conn, no_pilsner), 13, "pass")
    below_floor = recipe(conn, [(VIENNA, 100)], boil_min=45)
    only_rule_differs(check(conn, below_floor), 13, "fail")
    items = {"fermentables": [{"ingredient_id": 1, "name": "X", "min_boil_min": None}], "hops": []}
    r = conn.execute("select app.check_rule_13(%s::jsonb, %s::jsonb)", (json.dumps(items), json.dumps({"boil_min": 60}))).fetchone()[0]
    assert r["status"] == "unknown" and r["missing"] == ["ref.fermentable.min_boil_min"]
