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
        "select app.boil_gravity(1.050, 0, 6)",
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


@pytest.mark.stack
def test_boil_gravity_takes_postboil_volume(conn):
    # HTB p. 291 divides by the post-boil volume: 20 L batch + 2 L losses = 22 L, 25 L pre-boil.
    sql = "select app.boil_gravity(og => 1.060, postboil_l => 22, preboil_l => 25)"
    assert one(conn, sql) == pytest.approx(1.0528, abs=0.0001)


@pytest.mark.stack
def test_null_fields_and_arrays_raise(conn):
    grist = '[{"kg":1,"extract_pct":80,"mashed":%s,"fermentability":"normal"}]'
    hops = '[{"g":10,"alpha_pct":10,"minutes":60,"usage":"boil"}]'
    pct_grist = '[{"pct":%s,"extract_pct":80,"mashed":true}]'
    share_hops = '[{"share_pct":%s,"alpha_pct":10,"minutes":60,"usage":"boil"}]'
    for sql in (
        f"select app.og('{grist % 'null'}'::jsonb, 50, 10)",
        f"select app.fg('{grist % 'null'}'::jsonb, 50, 10, 75)",
        f"select app.ibu('{hops.replace('10,', 'null,', 1)}'::jsonb, 1.050, 20)",
        "select app.grist_mcu('[{\"kg\":1,\"ebc\":null}]'::jsonb, 20)",
        f"select app.solve_grist(1.050, '{pct_grist % 'null'}'::jsonb, 75, 20)",
        f"select app.solve_hops(50, '{share_hops % 'null'}'::jsonb, 1.050, 20)",
        "select app.og('null'::jsonb, 75, 10)",
        "select app.og(null, 75, 10)",
        "select app.fg('null'::jsonb, 75, 10, 75)",
        "select app.ibu('null'::jsonb, 1.050, 20)",
        "select app.ibu(null, 1.050, 20)",
        "select app.grist_mcu('null'::jsonb, 20)",
        "select app.solve_grist(1.050, 'null'::jsonb, 75, 20)",
        "select app.solve_hops(50, 'null'::jsonb, 1.050, 20)",
    ):
        with pytest.raises(psycopg.Error):
            conn.execute(sql)
        conn.rollback()


# HTB table 9.1, p. 150 (typed from the book, doc-calc section 5).
ABV_TABLE_OGS = (1.030, 1.035, 1.040, 1.045, 1.050, 1.055, 1.060, 1.065, 1.070, 1.075)
ABV_TABLE_9_1 = {  # FG -> printed ABV at each OG above (HTB p. 150)
    0.998: (4.1, 4.8, 5.4, 6.1, 6.8, 7.4, 8.1, 8.7, 9.4, 10.1),
    1.000: (3.9, 4.5, 5.2, 5.8, 6.5, 7.1, 7.8, 8.5, 9.1, 9.8),
    1.002: (3.6, 4.2, 4.9, 5.6, 6.2, 6.9, 7.5, 8.2, 8.9, 9.5),
    1.004: (3.3, 4.0, 4.6, 5.3, 5.9, 6.6, 7.3, 7.9, 8.6, 9.3),
    1.006: (3.1, 3.7, 4.4, 5.0, 5.7, 6.3, 7.0, 7.7, 8.3, 9.0),
    1.008: (2.8, 3.5, 4.1, 4.8, 5.4, 6.1, 6.7, 7.4, 8.0, 8.7),
    1.010: (2.6, 3.2, 3.8, 4.5, 5.1, 5.8, 6.5, 7.1, 7.8, 8.4),
    1.012: (2.3, 2.9, 3.6, 4.2, 4.9, 5.5, 6.2, 6.8, 7.5, 8.2),
    1.014: (2.0, 2.7, 3.3, 4.0, 4.6, 5.3, 5.9, 6.6, 7.2, 7.9),
    1.016: (1.8, 2.4, 3.1, 3.7, 4.4, 5.0, 5.7, 6.3, 7.0, 7.6),
    1.018: (1.5, 2.2, 2.8, 3.4, 4.1, 4.7, 5.4, 6.0, 6.7, 7.3),
    1.020: (1.3, 1.9, 2.5, 3.2, 3.8, 4.5, 5.1, 5.8, 6.4, 7.1),
    1.022: (1.0, 1.6, 2.3, 2.9, 3.6, 4.2, 4.9, 5.5, 6.2, 6.8),
    1.024: (0.8, 1.4, 2.0, 2.7, 3.3, 4.0, 4.6, 5.2, 5.9, 6.5),
}

# HTB table 4.3, p. 55: FG at "75 % fermentability" for each OG.
FG_TABLE_4_3 = {1.030: 1.007, 1.040: 1.010, 1.050: 1.012, 1.060: 1.015, 1.070: 1.018,
                1.080: 1.020, 1.090: 1.022}


def fg(conn, grist, efficiency, volume_l, attenuation):
    return one(conn, "select app.fg(%s::jsonb, %s, %s, %s)", json.dumps(grist), efficiency,
               volume_l, attenuation)


def sugar(kg, fermentability, extract_pct=100):
    return {"kg": kg, "extract_pct": extract_pct, "mashed": False,
            "fermentability": fermentability}


@pytest.mark.stack
@pytest.mark.parametrize("target_og,printed_fg", FG_TABLE_4_3.items())
def test_fg_table_4_3(conn, target_og, printed_fg):
    # Unmashed sugar sized to hit the OG in 10 L: kg = points x L / 384.
    kg = (target_og - 1) * 1000 * 10 / 384
    grist = [sugar(kg, "normal")]
    assert og(conn, grist, 75, 10) == pytest.approx(target_og)
    assert fg(conn, grist, 75, 10, 75) == pytest.approx(printed_fg, abs=0.002)


@pytest.mark.stack
@pytest.mark.parametrize("fg_key", ABV_TABLE_9_1)
def test_abv_table_9_1(conn, fg_key):
    for table_og, printed in zip(ABV_TABLE_OGS, ABV_TABLE_9_1[fg_key]):
        value = one(conn, "select app.abv(%s, %s)", table_og, fg_key)
        assert value == pytest.approx(printed, abs=0.1), (table_og, fg_key)


@pytest.mark.stack
def test_fg_all_candi_is_one(conn):
    assert fg(conn, [sugar(2, "full")], 75, 10, 75) == pytest.approx(1.000)


@pytest.mark.stack
def test_fg_lactose_only_is_og(conn):
    grist = [sugar(2, "none", extract_pct=100)]
    assert fg(conn, grist, 75, 10, 75) == pytest.approx(og(conn, grist, 75, 10))


@pytest.mark.stack
def test_fg_unknown_fermentability_raises(conn):
    with pytest.raises(psycopg.Error):
        fg(conn, [sugar(1, "sometimes")], 75, 10, 75)
    conn.rollback()


# HTB table 5.5, p. 81 (typed from the book, doc-calc section 6): utilisation by boil time (rows)
# and boil gravity (columns).
TINSETH_GRAVITIES = (1.030, 1.040, 1.050, 1.060, 1.070, 1.080, 1.090, 1.100, 1.110, 1.120)
TINSETH_TABLE_5_5 = {  # minutes -> printed utilisation at each gravity above
    0: (0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000),
    5: (0.055, 0.050, 0.046, 0.042, 0.038, 0.035, 0.032, 0.029, 0.027, 0.025),
    10: (0.100, 0.091, 0.084, 0.076, 0.070, 0.064, 0.058, 0.053, 0.049, 0.045),
    15: (0.137, 0.125, 0.114, 0.105, 0.096, 0.087, 0.080, 0.073, 0.067, 0.061),
    20: (0.167, 0.153, 0.140, 0.128, 0.117, 0.107, 0.098, 0.089, 0.081, 0.074),
    25: (0.192, 0.175, 0.160, 0.147, 0.134, 0.122, 0.112, 0.102, 0.094, 0.085),
    30: (0.212, 0.194, 0.177, 0.162, 0.148, 0.135, 0.124, 0.113, 0.103, 0.094),
    35: (0.229, 0.209, 0.191, 0.175, 0.160, 0.146, 0.133, 0.122, 0.111, 0.102),
    40: (0.242, 0.221, 0.202, 0.185, 0.169, 0.155, 0.141, 0.129, 0.118, 0.108),
    45: (0.253, 0.232, 0.212, 0.194, 0.177, 0.162, 0.148, 0.135, 0.123, 0.113),
    50: (0.263, 0.240, 0.219, 0.200, 0.183, 0.168, 0.153, 0.140, 0.128, 0.117),
    55: (0.270, 0.247, 0.226, 0.206, 0.188, 0.172, 0.157, 0.144, 0.132, 0.120),
    60: (0.276, 0.252, 0.231, 0.211, 0.193, 0.176, 0.161, 0.147, 0.135, 0.123),
    70: (0.285, 0.261, 0.238, 0.218, 0.199, 0.182, 0.166, 0.152, 0.139, 0.127),
    80: (0.291, 0.266, 0.243, 0.222, 0.203, 0.186, 0.170, 0.155, 0.142, 0.130),
    90: (0.295, 0.270, 0.247, 0.226, 0.206, 0.188, 0.172, 0.157, 0.144, 0.132),
}


def hop(g, alpha_pct, minutes, usage="boil"):
    return {"g": g, "alpha_pct": alpha_pct, "minutes": minutes, "usage": usage}


def ibu(conn, hops, boil_sg, volume_l):
    return one(conn, "select app.ibu(%s::jsonb, %s, %s)", json.dumps(hops), boil_sg, volume_l)


@pytest.mark.stack
@pytest.mark.parametrize("minutes", TINSETH_TABLE_5_5)
def test_tinseth_table_5_5(conn, minutes):
    for gravity, printed in zip(TINSETH_GRAVITIES, TINSETH_TABLE_5_5[minutes]):
        value = one(conn, "select app.tinseth_utilisation(%s, %s)", gravity, minutes)
        assert value == pytest.approx(printed, abs=0.001), (minutes, gravity)


# Joe Ale (HTB p. 78-79): the metric sum uses 28 g and 42 g, not the 30 g / 45 g in the header.
JOE_ALE_METRIC = [hop(28, 8, 60), hop(42, 4, 15)]


@pytest.mark.stack
def test_ibu_joe_ale_metric(conn):
    assert ibu(conn, [JOE_ALE_METRIC[0]], 1.038, 19) == pytest.approx(30.3, abs=1)
    assert ibu(conn, [JOE_ALE_METRIC[1]], 1.038, 19) == pytest.approx(11.2, abs=1)
    assert ibu(conn, JOE_ALE_METRIC, 1.038, 19) == pytest.approx(41.5, abs=1)


@pytest.mark.stack
def test_ibu_joe_ale_us(conn):
    oz = 28.349523125
    assert ibu(conn, [hop(1 * oz, 8, 60)], 1.038, 5 * GAL) == pytest.approx(30.8, abs=1)
    assert ibu(conn, [hop(1.5 * oz, 4, 15)], 1.038, 5 * GAL) == pytest.approx(11.4, abs=1)


@pytest.mark.stack
def test_ibu_no_hops_is_zero(conn):
    assert ibu(conn, [], 1.050, 20) == 0


@pytest.mark.stack
def test_whirlpool_and_dry_hop_add_no_ibu(conn):
    extra = [hop(50, 12, 20, "whirlpool"), hop(100, 12, 0, "dry_hop")]
    assert ibu(conn, JOE_ALE_METRIC + extra, 1.038, 19) == pytest.approx(
        ibu(conn, JOE_ALE_METRIC, 1.038, 19))


@pytest.mark.stack
def test_ibu_unknown_usage_raises(conn):
    with pytest.raises(psycopg.Error):
        ibu(conn, [hop(28, 8, 60, "mash")], 1.038, 19)
    conn.rollback()


# Colour. Inputs are given in °L and converted to EBC (x 1.97, HTB p. 469).
def malt(lb, lovibond):
    return {"kg": lb * LB, "ebc": lovibond * 1.97}


def grist_mcu(conn, grist, gallons):
    return one(conn, "select app.grist_mcu(%s::jsonb, %s)", json.dumps(grist), gallons * GAL)


def srm(conn, mcu):
    return one(conn, "select app.srm(%s)", mcu)


@pytest.mark.stack
def test_mcu_palmer_simple(conn):
    assert grist_mcu(conn, [malt(8, 2), malt(2, 4)], 5) == pytest.approx(4.8, abs=0.01)


@pytest.mark.stack
def test_srm_shay_steam(conn):
    assert srm(conn, 12) == pytest.approx(8, abs=1)


@pytest.mark.stack
def test_srm_port_o_palmer(conn):
    assert srm(conn, 72) == pytest.approx(28, abs=1)


@pytest.mark.stack
def test_srm_port_o_palmer_more_chocolate(conn):
    assert srm(conn, 107) == pytest.approx(37, abs=1)


@pytest.mark.stack
def test_mcu_obc_pils(conn):
    mcu = grist_mcu(conn, [malt(8, 2), malt(1, 4)], 5)
    assert mcu == pytest.approx(4.0, abs=0.01)
    assert srm(conn, mcu) == pytest.approx(4, abs=1)


@pytest.mark.stack
def test_mcu_obc_dubbel(conn):
    # The book prints 43 MCU; its own rows add up to 40.5 (doc-calc section 7).
    rows = [(4.75, 3), (4.75, 2), (1.25, 8), (0.75, 75), (0.75, 120), (0.75, 30)]
    grist = [malt(lb, lov) for lb, lov in rows]
    assert grist_mcu(conn, grist, 5) == pytest.approx(40.5, abs=0.01)


@pytest.mark.stack
def test_ebc_srm_round_trip(conn):
    back = one(conn, "select app.ebc_from_srm(app.srm_from_ebc(%s))", 37.9)
    assert back == pytest.approx(37.9)


@pytest.mark.stack
def test_colour_missing_ebc_raises(conn):
    with pytest.raises(psycopg.Error):
        grist_mcu(conn, [{"kg": 1}], 5)
    conn.rollback()


# Solvers (R4, R6, A3, A4): each one inverts the forward function it mirrors.
def solve_grist(conn, target_og, grist, efficiency, volume_l):
    return conn.execute("select app.solve_grist(%s, %s::jsonb, %s, %s)",
                        [Decimal(str(target_og)), json.dumps(grist), Decimal(str(efficiency)),
                         Decimal(str(volume_l))]).fetchone()[0]


def solve_hops(conn, target_ibu, hops, boil_sg, volume_l):
    return conn.execute("select app.solve_hops(%s, %s::jsonb, %s, %s)",
                        [Decimal(str(target_ibu)), json.dumps(hops), Decimal(str(boil_sg)),
                         Decimal(str(volume_l))]).fetchone()[0]


def share(pct, extract_pct, mashed=True, fermentability="normal"):
    return {"pct": pct, "extract_pct": extract_pct, "mashed": mashed,
            "fermentability": fermentability}


@pytest.mark.stack
def test_solve_grist_round_trip(conn):
    grist = [share(80, 80), share(10, 75), share(10, 74)]
    solved = solve_grist(conn, 1.060, grist, 75, 20)
    assert og(conn, solved, 75, 20) == pytest.approx(1.060, abs=0.001)
    # shares of mass are kept, and the extra keys come back
    total = sum(i["kg"] for i in solved)
    assert [i["kg"] / total * 100 for i in solved] == pytest.approx([80, 10, 10])
    assert solved[0]["fermentability"] == "normal"


@pytest.mark.stack
def test_solve_grist_normalises_pct(conn):
    a = solve_grist(conn, 1.050, [share(80, 80), share(20, 75)], 75, 20)
    b = solve_grist(conn, 1.050, [share(8, 80), share(2, 75)], 75, 20)
    assert [i["kg"] for i in a] == pytest.approx([i["kg"] for i in b])


@pytest.mark.stack
def test_solve_hops_round_trip(conn):
    batch, boil_min = 20, 60
    preboil = one(conn, "select app.preboil_volume(%s, %s, %s, %s)", batch, boil_min, 3, 2)
    boil_sg = one(conn, "select app.boil_gravity(%s, %s, %s)", 1.060, batch + 2, preboil)
    hops = [{"share_pct": 50, "alpha_pct": 12, "minutes": 60, "usage": "boil"},
            {"share_pct": 20, "alpha_pct": 6, "minutes": 15, "usage": "boil"},
            {"share_pct": 10, "alpha_pct": 6, "minutes": 0, "usage": "boil"},
            {"share_pct": 20, "alpha_pct": 6, "minutes": 0, "usage": "dry_hop"}]
    solved = solve_hops(conn, 50, hops, boil_sg, batch)
    assert ibu(conn, solved, boil_sg, batch) == pytest.approx(50, abs=1)
    total = sum(i["g"] for i in solved)
    assert [i["g"] / total * 100 for i in solved] == pytest.approx([50, 20, 10, 20])


@pytest.mark.stack
def test_lactose_raises_fg_candi_lowers_it(conn):
    pale = share(100, 80)

    def solved_fg(grist):
        solved = solve_grist(conn, 1.060, grist, 75, 20)
        assert og(conn, solved, 75, 20) == pytest.approx(1.060, abs=0.001)
        return fg(conn, solved, 75, 20, 75)

    only_pale = solved_fg([pale])
    with_lactose = solved_fg([share(90, 80), share(10, 100, False, "none")])
    with_candi = solved_fg([share(90, 80), share(10, 100, False, "full")])
    assert with_lactose > only_pale > with_candi


@pytest.mark.stack
@pytest.mark.parametrize("efficiency", [50, 75, 100])
def test_solve_grist_all_sugar(conn, efficiency):
    solved = solve_grist(conn, 1.050, [share(100, 100, False, "full")], efficiency, 20)
    assert og(conn, solved, efficiency, 20) == pytest.approx(1.050, abs=0.001)
    assert solved[0]["kg"] == pytest.approx(0.050 * 1000 * 20 / 384)


@pytest.mark.stack
def test_solve_hops_without_boil_addition_raises(conn):
    hops = [{"share_pct": 100, "alpha_pct": 12, "minutes": 0, "usage": "dry_hop"}]
    with pytest.raises(psycopg.Error):
        solve_hops(conn, 30, hops, 1.050, 20)
    conn.rollback()


@pytest.mark.stack
def test_solve_hops_zero_target(conn):
    hops = [{"share_pct": 70, "alpha_pct": 12, "minutes": 60, "usage": "boil"},
            {"share_pct": 30, "alpha_pct": 6, "minutes": 0, "usage": "dry_hop"}]
    assert [i["g"] for i in solve_hops(conn, 0, hops, 1.050, 20)] == [0, 0]
    # also with no boil addition at all
    only_dry = [{"share_pct": 100, "alpha_pct": 12, "minutes": 0, "usage": "dry_hop"}]
    assert solve_hops(conn, 0, only_dry, 1.050, 20)[0]["g"] == 0
