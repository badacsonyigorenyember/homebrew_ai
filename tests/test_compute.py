"""Step 10: the colour solver (Task 3 of docs/work/m6-compute-validate, db/046_compute.sql)."""

import json

import pytest

from loaders.db import connect

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
