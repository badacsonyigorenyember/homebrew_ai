"""Step 15: carbonation and priming sugar (db/053_package.sql); docs/work/m7-process Task 7.
The expected figures are doc-calc.md §14 (How to Brew ch. 10, Table 10.1 p. 158, Table 10.3 p. 161)."""

import copy

import pytest

from loaders.db import connect
from tests.test_compute import compute, step10_input
from tests.test_contracts import errors
from tests.test_ferment import yeast_id  # noqa: F401  (keeps the fixture helpers in one place)
from tests.test_water import sql

pytestmark = pytest.mark.stack

# Table 10.3, doc-calc.md §14: temperature C -> (gas volume L/mol, residual CO2 volumes)
TABLE_10_3 = {
    5: (23.1, 1.32), 6: (23.2, 1.27), 7: (23.3, 1.23), 8: (23.4, 1.19), 9: (23.5, 1.16), 10: (23.5, 1.12),
    11: (23.6, 1.08), 12: (23.7, 1.05), 13: (23.8, 1.02), 14: (23.9, 0.99), 15: (24.0, 0.96), 16: (24.0, 0.93),
    17: (24.1, 0.90), 18: (24.2, 0.87), 19: (24.3, 0.84), 20: (24.4, 0.82), 21: (24.5, 0.80), 22: (24.5, 0.77),
    23: (24.6, 0.75), 24: (24.7, 0.73), 25: (24.8, 0.72), 26: (24.9, 0.70), 27: (25.0, 0.68), 28: (25.0, 0.67),
    29: (25.1, 0.65), 30: (25.2, 0.64),
}


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    connection.autocommit = True
    yield connection
    connection.close()


@pytest.fixture(scope="module")
def step15(conn):
    cache = {}

    def run(bid):
        if bid not in cache:
            inp = step10_input(conn, bid)
            s10 = compute(conn, inp)
            s14 = sql(conn, "step14_ferment", inp["targets"], s10)
            cache[bid] = ({"run_id": 0, "targets": inp["targets"], "step10": s10, "step14": s14},
                          sql(conn, "step15_package", inp["targets"], s10, s14))
        return copy.deepcopy(cache[bid])
    return run


def priming(conn, vol, temp, litres):
    return float(conn.execute("select app.priming_sugar_g(%s::numeric, %s::numeric, %s::numeric)", (vol, temp, litres)).fetchone()[0])


def test_palmer_cane_sugar(conn):
    """A5: 2.5 volumes, 19 L, 21 C is Table 10.1's 113 g of cane sugar, within 5 %."""
    assert priming(conn, 2.5, 21, 19) == pytest.approx(113, rel=0.05)


def test_table_10_3_cells(conn):
    """Table 10.3's g/L: 5 C 2.5 volumes 4.4, 21 C 2.5 volumes 6.0, 30 C 4.5 volumes 13.1."""
    for vol, temp, g_per_l in [(2.5, 5, 4.4), (2.5, 21, 6.0), (4.5, 30, 13.1)]:
        assert priming(conn, vol, temp, 1) == pytest.approx(g_per_l, abs=0.1)


def test_residual_rows(conn):
    for temp, (gas, resid) in TABLE_10_3.items():
        got = conn.execute("select app.residual_co2(%s::numeric)", (temp,)).fetchone()[0]
        assert (float(got["gas_l_mol"]), float(got["residual_vol"]), float(got["temp_c"])) == (gas, resid, temp)
    assert float(conn.execute("select app.residual_co2(20.6::numeric)").fetchone()[0]["temp_c"]) == 21
    for out_of_range in (4, 31):
        with pytest.raises(Exception, match="residual_co2"):
            conn.execute("select app.residual_co2(%s::numeric)", (out_of_range,))


def test_priming_uses_max_temp(step15):
    """b08: the priming temperature is step 14's highest ferment or rest temperature."""
    i, out = step15("b08")
    assert out["priming"]["temp_c"] == i["step14"]["max_temp_c"]


def test_co2_from_style(step15):
    """b13 (10A) sits in the German wheat family, b05 (15B) in porter and stout; volumes are the middle of the range."""
    _, wheat = step15("b13")
    assert wheat["co2"]["family"] == "german-wheat" and wheat["co2"]["from"] == "style"
    assert wheat["co2"]["range"] == [3.3, 4.5] and wheat["co2"]["volumes"] == 3.9 and wheat["co2"]["basis"] == "listed"
    _, stout = step15("b05")
    assert stout["co2"]["family"] == "porter-stout" and stout["co2"]["range"] == [1.7, 2.3] and stout["co2"]["volumes"] == 2.0


def test_default_co2(conn, step15):
    """Decision Q1: a style without volumes gets 2.5, from the default."""
    i, _ = step15("b01")
    targets = copy.deepcopy(i["targets"])
    targets["style"]["code"] = "specialty-honey-beer"
    out = sql(conn, "step15_package", targets, i["step10"], i["step14"])
    assert out["co2"]["volumes"] == 2.5 and out["co2"]["from"] == "default"
    assert out["co2"]["range"] is None and out["co2"]["family"] is None and out["co2"]["basis"] is None
    assert "p. 155" in out["co2"]["source"]


def test_priming_block(step15):
    i, out = step15("b01")
    p = out["priming"]
    litres = i["step10"]["batch"]["volume_l"]
    assert p["sugar"] == "table sugar (sucrose)" and p["volume_l"] == litres
    assert p["g"] == round(p["g"]) and p["g_per_l"] == pytest.approx(p["g"] / litres, abs=0.1)
    assert p["g"] > 0 and p["residual_vol"] > 0


def test_packaging_extras(step15):
    """b23: the cold brew coffee goes in at packaging, and only that one."""
    i, out = step15("b23")
    cold = next(e for e in i["step10"]["extras"] if e["usage"] == "package")
    assert out["extras"] == [{"ingredient_id": cold["ingredient_id"], "name": cold["name"], "g": cold["g"]}]
    _, plain = step15("b01")
    assert plain["extras"] == []


def test_step15_meets_contract(conn, step15):
    for bid in ("b01", "b05", "b13", "b23"):
        i, out = step15(bid)
        assert errors(conn, "step15.input", i) == [], bid
        assert errors(conn, "step15.output", out) == [], bid
