"""A recipe can hold a sheet and be accepted (Task 1 of docs/work/m8-recipe-sheet-chat, db/054_recipe_sheet.sql).

Every insert is rolled back.
"""

import psycopg
import pytest

from loaders.db import connect
from tests.test_save_recipe import saved
from tests.test_step4 import sql

pytestmark = pytest.mark.stack


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


@pytest.fixture(autouse=True)
def rolled_back(conn):
    yield
    conn.rollback()


def row(conn, rid):
    return conn.execute("select status, sheet from app.recipe where id = %s", [rid]).fetchone()


def test_save_then_read_sheet(conn):
    rid = saved(conn, "b08")[0]
    assert row(conn, rid) == ("draft", None)
    assert sql(conn, "save_sheet", rid, "# Sheet\n\nbody") == rid
    assert row(conn, rid) == ("draft", "# Sheet\n\nbody")


def test_save_sheet_overwrites(conn):
    rid = saved(conn, "b08")[0]
    sql(conn, "save_sheet", rid, "first")
    sql(conn, "save_sheet", rid, "second")
    assert row(conn, rid)[1] == "second"


def test_save_sheet_rejects_empty_and_unknown(conn):
    rid = saved(conn, "b08")[0]
    for bad in ("", "   "):
        with pytest.raises(psycopg.errors.RaiseException, match="sheet is empty"):
            sql(conn, "save_sheet", rid, bad)
        conn.rollback()
        rid = saved(conn, "b08")[0]
    with pytest.raises(psycopg.errors.RaiseException, match="unknown recipe"):
        sql(conn, "save_sheet", -1, "x")


def test_accept_with_sheet_gives_final(conn):
    rid = saved(conn, "b08")[0]
    sql(conn, "save_sheet", rid, "sheet")
    assert sql(conn, "accept_recipe", rid) == "final"
    assert row(conn, rid)[0] == "final"
    assert sql(conn, "accept_recipe", rid) == "final"


def test_accept_without_sheet_raises_and_stays_draft(conn):
    rid = saved(conn, "b08")[0]
    with pytest.raises(psycopg.errors.RaiseException, match="no sheet"):
        sql(conn, "accept_recipe", rid)
    conn.rollback()
    rid = saved(conn, "b08")[0]
    assert row(conn, rid)[0] == "draft"


def test_brewed_stays_brewed(conn):
    rid = saved(conn, "b08")[0]
    sql(conn, "save_sheet", rid, "sheet")
    conn.execute("update app.recipe set status = 'brewed' where id = %s", [rid])
    assert sql(conn, "accept_recipe", rid) == "brewed"
    assert row(conn, rid)[0] == "brewed"
