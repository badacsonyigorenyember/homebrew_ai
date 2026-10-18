"""Step 0 (db/038_step0.sql): the stored brewer profile, called directly (no pipeline).

Acceptance A7 of docs/work/m4-targets-blueprint/brief.md.
"""

import json
from pathlib import Path

import pytest

from loaders.db import connect

ROOT = Path(__file__).resolve().parent.parent
SQL_FILE = ROOT / "db" / "038_step0.sql"
CONTRACT = ROOT / "shared" / "contracts" / "step0.output.schema.json"


@pytest.fixture
def conn():
    connection = connect()
    yield connection
    connection.rollback()
    connection.close()


def step0(conn, profile_id=None):
    return conn.execute("select app.step0_profile(%s)", (profile_id,)).fetchone()[0]


@pytest.mark.stack
def test_default_profile(conn):
    got = step0(conn)
    assert (got["batch_l"], got["efficiency_pct"], got["boil_off_l_h"], got["losses_l"],
            got["grain_abs_l_kg"]) == (20, 72, 4, 2, 1.0)
    assert got["water"] == {k: 0 for k in ("ca", "mg", "na", "so4", "cl", "hco3")}
    assert got["units"] == "metric"
    assert got["inventory"] == []


@pytest.mark.stack
def test_output_meets_contract(conn):
    errs = conn.execute(
        "select coalesce(extensions.jsonschema_validation_errors(%s::json, %s::json), '{}')",
        (CONTRACT.read_text(), json.dumps(step0(conn))),
    ).fetchone()[0]
    assert errs == []


@pytest.mark.stack
def test_profile_by_id(conn):
    pid = conn.execute(
        "insert into app.brewer_profile (name, batch_l, efficiency_pct, boil_off_l_h, losses_l, ca_mg_l, mg_mg_l)"
        " values ('t', 10, 65, 3, 1, 50, 5) returning id").fetchone()[0]
    conn.execute("insert into app.inventory (profile_id, raw_name, amount, unit) values (%s, 'mystery malt', 1, 'kg')", (pid,))
    got = step0(conn, pid)
    assert got["batch_l"] == 10 and got["water"]["ca"] == 50 and got["water"]["na"] is None
    assert got["inventory"] == [{"raw_name": "mystery malt", "ingredient_id": None, "amount": 1, "unit": "kg"}]


@pytest.mark.stack
def test_unknown_id_raises(conn):
    with pytest.raises(Exception, match="step 0: no brewer profile"):
        step0(conn, -1)


@pytest.mark.stack
def test_rerun_keeps_user_values(conn):
    conn.execute("update app.brewer_profile set ca_mg_l = 50 where name = 'default'")
    text = SQL_FILE.read_text()
    start = text.index("insert into app.brewer_profile")
    conn.execute(text[start:text.index(";", start) + 1])
    assert conn.execute("select ca_mg_l from app.brewer_profile where name = 'default'").fetchone()[0] == 50


def test_sql_cites_water_source():
    text = SQL_FILE.read_text()
    for needle in ("brunwater-water-knowledge", "4.2.1", "placeholder"):
        assert needle in text
