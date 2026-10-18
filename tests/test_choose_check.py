"""The steps 6-9 proposal check (db/043_choose_check.sql).

Acceptance A1-A7 of docs/work/m5-choose-ingredients/brief.md. A helper builds a good proposal from
a candidate table; each rule test makes the smallest change to a good proposal and expects the
error of that rule, starting with the step number.
"""

import copy
import json

import pytest

from loaders.db import connect
from tests.test_choose_table import BRIEFS, build, ids_named, ids_of_word, rows_of, table_of
from tests.test_step4 import sql

pytestmark = pytest.mark.stack

GOOD = ("required", "typical", "allowed")
CONTRACT = json.loads(
    (__import__("pathlib").Path(__file__).resolve().parent.parent / "shared" / "contracts"
     / "choose.proposal.schema.json").read_text())


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def purpose():
    return "test"


def usable(r, tbl):
    """The row fits the recipe: a good level (guidance on), the yeast rules."""
    if tbl["guidance"] and r["best_level"] not in GOOD:
        return False
    if r["kind"] == "yeast":
        rules = tbl["yeast_rules"]
        if r["type"] == "lacto":
            return False
        if rules["lager"] and r["type"] != "lager":
            return False
        if any(f not in r["family"] for f in rules["families"]):
            return False
        if r["overlaps_band"] is False:
            return False
    return True


def choice_of(r, tbl, prefer=("mash", "boil 30 min", "boil", "secondary")):
    """A choice label of the row: one that keeps the best level when wanted, else a good level."""
    levels = r["levels"]
    if r.get("keeps_best"):
        return next(c for c in levels if c["choice"] in r["keeps_best"])
    for c in levels:
        if not tbl["guidance"] or c["level"] in GOOD:
            return c
    return levels[0]


def good_proposal(tbl):
    """First in-style rows, wanted and inventory ids, shares adding up to 100."""
    marked = lambda r: bool(r["inventory"]) or bool(r["wanted"])
    # yeast: an inventory yeast first, then a wanted one, else the first usable
    yeasts = [r for r in tbl["yeasts"] if r["type"] != "lacto"]
    fits = {i for w in tbl["inventory_words"] if w["kind"] == "yeast" and w["fits"] for i in w["ids"]}
    main = next((r for r in yeasts if r["ingredient_id"] in fits and usable(r, tbl)), None) \
        or next(r for r in yeasts if usable(r, tbl))
    souring = None
    if tbl["yeast_rules"]["souring"]:
        souring = next(r for r in tbl["yeasts"] if r["type"] == "lacto")
    yeast = {"main": {"ingredient_id": main["ingredient_id"], "purpose": purpose()},
             "souring": None if souring is None else {"ingredient_id": souring["ingredient_id"], "purpose": purpose()}}

    def required(kind):
        ids = []
        for s in tbl["slots"]:
            if s["kind"] == kind and s["ids"]:
                ids.append(s["ids"][0])
        for w in tbl["inventory_words"]:
            if w["kind"] == kind and w["fits"] and w["ids"] and not set(w["ids"]) & set(ids):
                rows = {r["ingredient_id"]: r for r in rows_of(tbl)}
                ids.append(next(i for i in w["ids"] if usable(rows[i], tbl)))
        return list(dict.fromkeys(ids))

    rows = {r["ingredient_id"]: r for r in rows_of(tbl)}
    # fermentables: the required ones at a small share, a base for the rest
    picks = required("fermentable")
    small = 5.0
    ferm = []
    for i in picks:
        r = rows[i]
        pct = min(small, float(r["max_pct"])) if r["max_pct"] else small
        ferm.append({"ingredient_id": i, "usage": choice_of(r, tbl)["usage"], "pct": pct, "purpose": purpose()})
    base = next(r for r in tbl["fermentables"] if r["role"] == "base" and r["max_pct"] in (None, 100)
                and usable(r, tbl) and r["ingredient_id"] not in picks)
    ferm.append({"ingredient_id": base["ingredient_id"], "usage": "mash", "pct": round(100 - sum(f["pct"] for f in ferm), 2),
                 "purpose": purpose()})

    # hops: the required ones, then in-style boil hops; shares add up to 100
    picks = required("hop")
    hops = []
    for i in picks:
        c = choice_of(rows[i], tbl)
        hops.append({"ingredient_id": i, "usage": c["usage"], "minutes": c["minutes"] or 0, "purpose": purpose()})
    if (tbl["targets"]["ibu"] or 0) > 0:
        boil = next(r for r in tbl["hops"] if r["ingredient_id"] not in picks and usable(r, tbl)
                    and any(c["choice"] == "boil 30 min" and c["level"] in GOOD for c in r["levels"]))
        hops.append({"ingredient_id": boil["ingredient_id"], "usage": "boil", "minutes": 60, "purpose": purpose()})
    for h in hops:
        h["share_pct"] = round(100 / len(hops), 2)
    if hops:
        hops[-1]["share_pct"] = round(100 - sum(h["share_pct"] for h in hops[:-1]), 2)

    extras = []
    for i in required("misc"):
        c = choice_of(rows[i], tbl)
        extras.append({"ingredient_id": i, "usage": c["usage"], "purpose": purpose()})
    return {"yeast": yeast, "fermentables": ferm, "hops": hops, "extras": extras}


def check(conn, bid, proposal):
    tbl = table_of(conn, bid)
    return sql(conn, "choose_check", tbl, proposal)


def errors_of(conn, bid, proposal, step=None):
    errs = check(conn, bid, proposal)
    assert all(e.startswith("step ") for e in errs), errs
    return errs if step is None else [e for e in errs if e.startswith(f"step {step}: ")]


def good(conn, bid):
    return good_proposal(table_of(conn, bid))


@pytest.mark.parametrize("bid", ["b01", "b08", "b10", "b14", "b15", "b16", "b23"])
def test_good_proposals_pass(conn, bid):
    proposal = good(conn, bid)
    assert errors_of(conn, bid, proposal) == []
    tbl = table_of(conn, bid)
    contract = json.dumps(CONTRACT)
    got = conn.execute("select proposal, errors from app.choose_read_answer(%s, %s::json, %s::jsonb)",
                       (json.dumps(proposal), contract, json.dumps(tbl))).fetchone()
    assert got[1] == [] and got[0] == proposal


def test_not_json_and_contract_errors(conn):
    tbl = table_of(conn, "b01")
    read = lambda text: conn.execute("select errors from app.choose_read_answer(%s, %s::json, %s::jsonb)",
                                     (text, json.dumps(CONTRACT), json.dumps(tbl))).fetchone()[0]
    assert read("not json")[0].startswith("answer is not JSON")
    errs = read(json.dumps({"yeast": 1}))
    assert errs and all(e.startswith("contract: ") for e in errs)


def test_invented_id(conn):
    """A1: an id that is not in the table, in each of the four steps."""
    p = good(conn, "b01")
    p["yeast"]["main"]["ingredient_id"] = 999999999
    p["fermentables"][0]["ingredient_id"] = 999999998
    p["hops"][0]["ingredient_id"] = 999999997
    p["extras"] = [{"ingredient_id": 999999996, "usage": "boil", "purpose": "x"}]
    errs = errors_of(conn, "b01", p)
    for n, i in ((6, 999999999), (7, 999999998), (8, 999999997), (9, 999999996)):
        assert f"step {n}: id {i} is not in the candidate table" in errs


def test_excluded_products(conn):
    """A2: Saaz in b08, Citra LUPOMAX in b16, each with its own message."""
    p = good(conn, "b08")
    saaz = next(iter(ids_named(conn, "hop", "Saaz")))
    p["hops"][-1]["ingredient_id"] = saaz
    errs = errors_of(conn, "b08", p, 8)
    assert any("Saaz" in e and "is excluded" in e for e in errs), errs

    p = good(conn, "b16")
    lupomax = next(iter(ids_named(conn, "hop", "Citra LUPOMAX")))
    p["hops"][-1]["ingredient_id"] = lupomax
    errs = errors_of(conn, "b16", p, 8)
    assert any("Citra LUPOMAX" in e and "sibling of Citra" in e for e in errs), errs


def test_inventory_left_out(conn):
    """A3: b10 without Brown Candi Sugar, b15 without East Kent Goldings."""
    p = good(conn, "b10")
    candi = next(iter(ids_named(conn, "fermentable", "Brown Candi Sugar")))
    assert any(f["ingredient_id"] == candi for f in p["fermentables"])
    p["fermentables"] = [f for f in p["fermentables"] if f["ingredient_id"] != candi]
    p["fermentables"][-1]["pct"] = round(100 - sum(f["pct"] for f in p["fermentables"][:-1]), 2)
    errs = errors_of(conn, "b10", p)
    assert errs == [e for e in errs if e.startswith("step 7: the inventory \"dark candi sugar\"")] and len(errs) == 1, errs

    p = good(conn, "b15")
    kent = ids_of_word(conn, "East Kent Golding")
    assert len(kent) == 1
    p["hops"] = [h for h in p["hops"] if h["ingredient_id"] not in kent]
    p["hops"][0]["share_pct"] = 100
    errs = errors_of(conn, "b15", p)
    assert len(errs) == 1 and errs[0].startswith("step 8: the inventory \"East Kent Golding"), errs

    # a yeast in stock: one is enough, but none is not
    p = good(conn, "b10")
    stock = {i for w in table_of(conn, "b10")["inventory_words"] if w["kind"] == "yeast" for i in w["ids"]}
    other = next(r for r in table_of(conn, "b10")["yeasts"] if r["ingredient_id"] not in stock and usable(r, table_of(conn, "b10")))
    p["yeast"]["main"]["ingredient_id"] = other["ingredient_id"]
    errs = errors_of(conn, "b10", p, 6)
    assert any("inventory has a yeast that fits" in e for e in errs), errs


def test_levels_and_wanted(conn):
    """A4: an out-of-style pipeline pick, and a wanted pick off keeps_best."""
    tbl = table_of(conn, "b01")
    bad = next(r for r in tbl["hops"] if r["inventory"] is None
               and any(c["level"] in ("out_of_style", "changes_style") for c in r["levels"]))
    bad_choice = next(c for c in bad["levels"] if c["level"] in ("out_of_style", "changes_style"))
    p = good(conn, "b01")
    p["hops"][0].update(ingredient_id=bad["ingredient_id"], usage=bad_choice["usage"], minutes=bad_choice["minutes"] or 0)
    errs = errors_of(conn, "b01", p, 8)
    assert any(bad["name"] in e and "in 21A" in e for e in errs), errs

    # a wanted pick: b01 with Cascade wanted; its boil 30 min is "allowed", below the best "typical"
    b = copy.deepcopy(BRIEFS["b01"])
    b["wanted"] = b["wanted"] + [{"item": "Cascade", "role": "background"}]
    tbl, _ = build(conn, b)
    cascade = next(r for r in tbl["hops"] if r["name"] == "Cascade")
    assert "boil 30 min" not in cascade["keeps_best"]
    p = good_proposal(tbl)
    assert sql(conn, "choose_check", tbl, p) == []
    wanted_hop = next(h for h in p["hops"] if h["ingredient_id"] == cascade["ingredient_id"])
    wanted_hop.update(usage="boil", minutes=60)
    errs = sql(conn, "choose_check", tbl, p)
    assert len(errs) == 1 and errs[0].startswith("step 8: Cascade is wanted as \"Cascade\", and boil 30 min does not keep"), errs


def test_yeast_rules(conn):
    """A5: an ale yeast in lager b08, an ale-family yeast in b13, and a lacto culture as main."""
    tbl = table_of(conn, "b08")
    ale = next(r for r in tbl["yeasts"] if r["type"] == "ale")
    p = good(conn, "b08")
    p["yeast"]["main"]["ingredient_id"] = ale["ingredient_id"]
    errs = errors_of(conn, "b08", p, 6)
    assert any("is not a lager yeast" in e for e in errs), errs

    tbl = table_of(conn, "b13")
    non_wheat = next(r for r in tbl["yeasts"] if r["type"] == "ale" and "wheat" not in r["family"] and r["overlaps_band"])
    p = good(conn, "b13")
    p["yeast"]["main"]["ingredient_id"] = non_wheat["ingredient_id"]
    errs = errors_of(conn, "b13", p, 6)
    assert any("yeast family wheat" in e for e in errs), errs

    tbl = table_of(conn, "b14")
    lacto = next(r for r in tbl["yeasts"] if r["type"] == "lacto")
    p = good(conn, "b14")
    p["yeast"]["main"]["ingredient_id"] = lacto["ingredient_id"]
    assert any("is a lacto culture" in e for e in errors_of(conn, "b14", p, 6))


def test_attenuation_band(conn):
    """R5: a yeast whose range misses the band is refused when another reaches it."""
    tbl = table_of(conn, "b01")
    miss = next(r for r in tbl["yeasts"] if r["overlaps_band"] is False and r["best_level"] in GOOD and r["inventory"] is None)
    p = good(conn, "b01")
    p["yeast"]["main"]["ingredient_id"] = miss["ingredient_id"]
    errs = errors_of(conn, "b01", p, 6)
    assert len(errs) == 1 and "does not reach the band" in errs[0], errs


def test_souring(conn):
    """A5: b14 without a souring culture, and a souring culture where none is asked for."""
    p = good(conn, "b14")
    assert p["yeast"]["souring"]
    p["yeast"]["souring"] = None
    assert errors_of(conn, "b14", p) == ["step 6: the style is sour: add a souring culture (type lacto) in souring"]

    p = good(conn, "b14")
    p["yeast"]["souring"]["ingredient_id"] = p["yeast"]["main"]["ingredient_id"]
    assert any("not a lacto culture" in e for e in errors_of(conn, "b14", p, 6))

    lacto = next(r for r in table_of(conn, "b14")["yeasts"] if r["type"] == "lacto")
    p = good(conn, "b01")
    tbl = table_of(conn, "b01")
    row = next((r for r in tbl["yeasts"] if r["type"] == "lacto"), None)
    if row is not None:  # b01 lists no lacto culture: the id is then simply not in its table
        p["yeast"]["souring"] = {"ingredient_id": row["ingredient_id"], "purpose": "x"}
        assert any("none was asked for" in e for e in errors_of(conn, "b01", p, 6))
    else:
        p["yeast"]["souring"] = {"ingredient_id": lacto["ingredient_id"], "purpose": "x"}
        assert errors_of(conn, "b01", p, 6)


def test_fermentable_shares(conn):
    """A6: shares not 100, a share above max_pct, a product twice."""
    p = good(conn, "b01")
    p["fermentables"][-1]["pct"] -= 1
    errs = errors_of(conn, "b01", p)
    assert errs == ["step 7: the fermentable shares add up to 99, not 100"]

    tbl = table_of(conn, "b01")
    limited = next(r for r in tbl["fermentables"] if r["max_pct"] and r["max_pct"] < 20 and r["best_level"] in GOOD
                   and r["ingredient_id"] != p["fermentables"][-1]["ingredient_id"])
    p = good(conn, "b01")
    p["fermentables"].insert(0, {"ingredient_id": limited["ingredient_id"], "usage": "mash",
                                 "pct": limited["max_pct"] + 5, "purpose": "x"})
    p["fermentables"][-1]["pct"] = round(100 - sum(f["pct"] for f in p["fermentables"][:-1]), 2)
    errs = errors_of(conn, "b01", p, 7)
    assert len(errs) == 1 and "above its maximum" in errs[0], errs

    p = good(conn, "b01")
    p["fermentables"].append(dict(p["fermentables"][-1], pct=0.05))
    p["fermentables"][0]["pct"] -= 0.05
    assert any("picked more than once" in e for e in errors_of(conn, "b01", p, 7))


def test_hop_rules(conn):
    """A6: no boil addition, a dry hop with minutes, a late boil, shares."""
    p = good(conn, "b01")
    for h in p["hops"]:
        h["usage"], h["minutes"] = "whirlpool", 20
    errs = errors_of(conn, "b01", p, 8)
    assert any("at least one hop is a boil addition" in e for e in errs), errs

    p = good(conn, "b01")
    p["hops"][-1].update(usage="dry_hop", minutes=3)
    errs = errors_of(conn, "b01", p, 8)
    assert any("dry hop addition has minutes 0" in e for e in errs), errs

    p = good(conn, "b01")
    p["hops"][-1]["minutes"] = 120
    assert any("longer than 90 min" in e for e in errors_of(conn, "b01", p, 8))

    p = good(conn, "b01")
    p["hops"][0]["share_pct"] += 5
    assert any("hop shares add up to" in e for e in errors_of(conn, "b01", p, 8))


def test_extras_rules(conn):
    """A7: a dose is refused by the contract; a usage the row does not have is refused by the check."""
    p = good(conn, "b23")
    assert len(p["extras"]) == 2  # coffee, vanilla
    contract = json.dumps(CONTRACT)
    tbl = json.dumps(table_of(conn, "b23"))
    with_dose = copy.deepcopy(p)
    with_dose["extras"][0]["dose_g_per_l"] = 3.0
    errs = conn.execute("select errors from app.choose_read_answer(%s, %s::json, %s::jsonb)",
                        (json.dumps(with_dose), contract, tbl)).fetchone()[0]
    assert errs and all(e.startswith("contract: ") for e in errs)

    bad = copy.deepcopy(p)
    bad["extras"][0]["usage"] = "whirlpool"
    assert any("cannot be used as \"whirlpool\"" in e for e in errors_of(conn, "b23", bad, 9))

    two = copy.deepcopy(p)
    other = next(s for s in table_of(conn, "b23")["slots"] if s["item"] == "coffee")["ids"]
    two["extras"].append({"ingredient_id": [i for i in other if i != two["extras"][0]["ingredient_id"]][0],
                          "usage": "packaging", "purpose": "x"})
    assert any("has 2 picks" in e for e in errors_of(conn, "b23", two, 9))

    missing = copy.deepcopy(p)
    missing["extras"] = missing["extras"][1:]
    assert any("has no pick" in e for e in errors_of(conn, "b23", missing, 9))


def test_misc_dose_rule(conn):
    """A16: one point as it is, feature the high end, background the low end, no range null."""
    dose = lambda name, role: conn.execute(
        "select app.misc_dose((select id from ref.ingredient where name = %s), %s)", (name, role)).fetchone()[0]
    assert float(dose("Coffee, whole beans", "feature")["g_per_l"]) == 3.0
    assert dose("Coffee, whole beans", "feature")["because"] == "one sourced dose"
    assert float(dose("Vanilla bean", "background")["g_per_l"]) == 0.05
    assert float(dose("Vanilla bean", "feature")["g_per_l"]) == 0.53
    assert float(dose("Vanilla bean", None)["g_per_l"]) == 0.05
    assert float(dose("Orange peel", "background")["g_per_l"]) == 2.64
    assert "low end" in dose("Vanilla bean", "background")["because"]
    assert "high end" in dose("Vanilla bean", "feature")["because"]
    # a misc without a sourced range: a fixture inside a rolled-back transaction
    conn.execute("begin")
    try:
        conn.execute("update ref.misc set dose_g_per_l = null where ingredient_id = (select id from ref.ingredient where name = 'Vanilla bean')")
        assert dose("Vanilla bean", "feature") == {"g_per_l": None, "because": "no sourced dose"}
    finally:
        conn.execute("rollback")


def test_guidance_off_allows_any_level(conn):
    """b18: no level, lager or family rule; an out-of-style product passes."""
    tbl = table_of(conn, "b18")
    assert tbl["guidance"] is False
    p = good_proposal(tbl)
    assert errors_of(conn, "b18", p) == []
    bad = next(r for r in tbl["fermentables"] if r["inventory"] is None and r["role"] == "base" and r["max_pct"] in (None, 100)
               and r["best_level"] not in GOOD and r["ingredient_id"] != p["fermentables"][-1]["ingredient_id"])
    p["fermentables"][-1]["ingredient_id"] = bad["ingredient_id"]
    assert errors_of(conn, "b18", p) == []
