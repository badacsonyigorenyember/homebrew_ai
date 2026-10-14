"""Brewing maths functions in db/030_maths.sql, each called with literal inputs.

Every expected number cites a row of docs/work/s1-maths/doc-calc.md (HTB = How to Brew, OBC =
Oregon Brew Crew Recipe Formulation). Requirements R1-R10, acceptance A2, A6, A7 of the brief.
"""

import json
from decimal import Decimal

import psycopg
import pytest

from loaders.db import connect

# Unit factors (HTB p. 469, p. 290; same PPG rule as loaders/adjuncts.py).
LB = 0.45359237  # kg
GAL = 3.785411784  # L


def ppg(points_per_lb_gal):
    """PPG (or 'points per lb per gal') to extract %: PPG / 46 x 100 (HTB p. 290)."""
    return points_per_lb_gal / 46 * 100


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def one(conn, sql, *params):
    """First value of a query. Numbers go in as exact decimals so numeric functions resolve."""
    params = [Decimal(str(p)) if isinstance(p, (int, float)) else p for p in params]
    return float(conn.execute(sql, params).fetchone()[0])


def og(conn, grist, efficiency, volume_l):
    return one(conn, "select app.og(%s::jsonb, %s, %s)", json.dumps(grist), efficiency, volume_l)


def item(lb, extract_pct, mashed=True):
    return {"kg": lb * LB, "extract_pct": extract_pct, "mashed": mashed}


SHORT_STOUT_YIELDS = (81, 75, 74, 74, 78)  # FGDB %, HTB table 18.4


def short_stout_us(lager_lb):
    pounds = (lager_lb, 0.5, 0.5, 0.5, 0.5)
    return [item(lb, y) for lb, y in zip(pounds, SHORT_STOUT_YIELDS)]


@pytest.mark.stack
@pytest.mark.parametrize("sg", [1.010, 1.050, 1.100])
def test_plato_round_trip(conn, sg):
    plato = one(conn, "select app.sg_to_plato(%s)", sg)
    assert one(conn, "select app.plato_to_sg(%s)", plato) == pytest.approx(sg, abs=0.001)


@pytest.mark.stack
def test_ebc_srm_helpers(conn):
    assert one(conn, "select app.ebc_from_srm(10)") == pytest.approx(19.7)
    assert one(conn, "select app.srm_from_ebc(19.7)") == pytest.approx(10)


@pytest.mark.stack
def test_preboil_volume_example(conn):
    assert one(conn, "select app.preboil_volume(20, 60, 3, 2)") == pytest.approx(25)


@pytest.mark.stack
def test_og_palmer_dme_example(conn):
    us = og(conn, [item(5, ppg(42), mashed=False)], 75, 3 * GAL)
    assert us == pytest.approx(1.070, abs=0.001)
    metric = og(conn, [{"kg": 2.27, "extract_pct": 350 / 384 * 100, "mashed": False}], 75, 11.4)
    assert metric == pytest.approx(1.070, abs=0.001)


@pytest.mark.stack
def test_og_palmer_short_stout_max_yield(conn):
    grist = short_stout_us(6.5)
    assert og(conn, grist, 100, 6 * GAL) == pytest.approx(1.052, abs=0.001)
    assert og(conn, grist, 73, 6 * GAL) == pytest.approx(1.038, abs=0.001)


@pytest.mark.stack
def test_og_palmer_short_stout_planned_us(conn):
    assert og(conn, short_stout_us(7), 75, 5 * GAL) == pytest.approx(1.050, abs=0.001)


@pytest.mark.stack
def test_og_palmer_short_stout_planned_metric(conn):
    grist = [{"kg": 3.5, "extract_pct": 80, "mashed": True}]
    grist += [{"kg": 0.225, "extract_pct": y, "mashed": True} for y in (75, 74, 74, 78)]
    assert og(conn, grist, 75, 20) == pytest.approx(1.050, abs=0.001)


@pytest.mark.stack
def test_boil_gravity_joe_ale(conn):
    grist = [{"kg": 2.5, "extract_pct": 91.3, "mashed": False}]
    assert og(conn, grist, 75, 23) == pytest.approx(1.038, abs=0.001)


@pytest.mark.stack
def test_boil_gravity_book_example(conn):
    # HTB p. 291: 5 gal at 1.050 boiled in 6 gal is 1.042, in 7 gal is 1.036.
    assert one(conn, "select app.boil_gravity(1.050, 5, 6)") == pytest.approx(1.042, abs=0.001)
    assert one(conn, "select app.boil_gravity(1.050, 5, 7)") == pytest.approx(1.036, abs=0.001)


@pytest.mark.stack
def test_og_obc_dubbel(conn):
    # OBC p. 2, 100 % column in points per lb per gal; candi sugar is not mashed.
    rows = [(4.75, 38), (4.75, 37), (1.25, 38), (0.75, 33), (0.75, 30)]
    grist = [item(lb, ppg(points)) for lb, points in rows]
    grist.append(item(0.75, ppg(47), mashed=False))
    assert og(conn, grist, 75, 5 * GAL) == pytest.approx(1.0745, abs=0.001)


@pytest.mark.stack
def test_og_obc_pils(conn):
    grist = [item(8, ppg(37)), item(1, ppg(37))]
    assert og(conn, grist, 75, 5 * GAL) == pytest.approx(1.0504, abs=0.001)


@pytest.mark.stack
def test_efficiency_skips_unmashed(conn):
    sugar = [item(1, 100, mashed=False)]
    assert og(conn, sugar, 50, 10) == pytest.approx(og(conn, sugar, 100, 10))
    malt = [item(1, 80)]
    assert og(conn, malt, 50, 10) < og(conn, malt, 100, 10)


@pytest.mark.stack
def test_calc_version_defined(conn):
    assert conn.execute("select app.calc_version()").fetchone()[0] == "maths-1"


@pytest.mark.stack
def test_bad_volume_raises(conn):
    for sql in (
        "select app.og('[{\"kg\":1,\"extract_pct\":80,\"mashed\":true}]'::jsonb, 75, 0)",
        "select app.gravity_points(1, 80, 75, -1)",
        "select app.boil_gravity(1.050, 5, 0)",
        "select app.preboil_volume(0, 60, 3, 2)",
    ):
        with pytest.raises(psycopg.Error):
            conn.execute(sql)
        conn.rollback()


@pytest.mark.stack
def test_og_missing_field_raises(conn):
    with pytest.raises(psycopg.Error):
        conn.execute("select app.og('[{\"kg\":1,\"mashed\":true}]'::jsonb, 75, 10)")
    conn.rollback()
