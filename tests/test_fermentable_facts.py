"""Fermentable facts: schema (Task 2), loader and data (Tasks 3-4) of s2-formulation-rules."""

import psycopg
import pytest

from loaders.db import connect


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


@pytest.mark.stack
def test_schema(conn):
    columns = {
        r[0]
        for r in conn.execute(
            "select column_name from information_schema.columns "
            "where table_schema = 'ref' and table_name = 'fermentable'"
        )
    }
    assert {"enzyme_activity", "min_boil_min", "description", "description_ref"} <= columns

    # The check constraints reject bad values; the transaction is rolled back each time.
    for column, bad in (("enzyme_activity", "'medium'"), ("min_boil_min", "30")):
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(
                f"update ref.fermentable set {column} = {bad} "
                "where ingredient_id = (select min(ingredient_id) from ref.fermentable)"
            )
        conn.rollback()

    owners = {
        r[0]: r[1]
        for r in conn.execute(
            "select c.relname, pg_get_userbyid(c.relowner) from pg_class c "
            "join pg_namespace n on n.oid = c.relnamespace "
            "where n.nspname = 'ref' and c.relname in "
            "('fermentable_substitute', 'fermentable_substitutes', 'fermentable_style')"
        )
    }
    assert owners == {
        "fermentable_substitute": "postgres",
        "fermentable_substitutes": "postgres",
        "fermentable_style": "postgres",
    }
    kinds = dict(
        conn.execute(
            "select c.relname, c.relkind from pg_class c join pg_namespace n on n.oid = c.relnamespace "
            "where n.nspname = 'ref' and c.relname like 'fermentable_%'"
        ).fetchall()
    )
    assert kinds["fermentable_substitutes"] == "v"

    row = conn.execute(
        "select title, edition, publisher from ref.source where slug = 'malt-substitution-2025'"
    ).fetchone()
    assert row == ("PrimeTime Malt Substitution Chart", "2025 (short)", "Hops Shop BG")
