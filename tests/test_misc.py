"""Misc extras (s9-misc-extras). Stack tests roll back; nothing is left in the database."""

import psycopg
import pytest

from loaders.db import connect

pytestmark = pytest.mark.stack

FLAVOUR = ("spice", "herb", "fruit", "wood", "coffee", "cacao", "vanilla", "smoke", "other")
PROCESS = ("fining", "nutrient", "enzyme", "acid", "other-process")


@pytest.fixture
def conn():
    connection = connect()
    yield connection
    connection.rollback()
    connection.close()


def new_ingredient(conn, name):
    source_id = conn.execute("select min(id) from ref.source").fetchone()[0]
    return conn.execute(
        "insert into ref.ingredient (kind, name, name_key, source_id, raw)"
        " values ('misc', %s, %s, %s, '{}') returning id",
        (name, name, source_id),
    ).fetchone()[0]


def insert_misc(conn, ingredient_id, purpose, category, usages):
    conn.execute(
        "insert into ref.misc (ingredient_id, purpose, category, usages) values (%s, %s, %s, %s)",
        (ingredient_id, purpose, category, usages),
    )


def test_misc_columns_and_checks(conn):
    columns = dict(conn.execute(
        "select column_name, data_type from information_schema.columns"
        " where table_schema = 'ref' and table_name = 'misc'"
    ).fetchall())
    assert columns == {
        "ingredient_id": "bigint", "category": "text", "purpose": "text", "usages": "ARRAY",
        "time_min": "integer", "dose_g_per_l": "numrange", "description": "text",
        "field_source": "jsonb",
    }
    owner = conn.execute("select tableowner from pg_tables where schemaname = 'ref' and tablename = 'misc'").fetchone()[0]
    assert owner == "postgres"

    # every category under its own purpose is accepted
    for number, (purpose, categories) in enumerate((("flavour", FLAVOUR), ("process", PROCESS))):
        for category in categories:
            insert_misc(conn, new_ingredient(conn, f"ok {number} {category}"), purpose, category, ["boil"])

    bad = [
        ("flavour category under process", "process", "spice", ["boil"]),
        ("process category under flavour", "flavour", "enzyme", ["boil"]),
        ("fining under flavour", "flavour", "fining", ["boil"]),
        ("unknown usage", "flavour", "spice", ["dry-hop"]),
        ("empty usages", "flavour", "spice", []),
        ("unknown purpose", "taste", "spice", ["boil"]),
    ]
    for label, purpose, category, usages in bad:
        conn.execute("savepoint s")
        with pytest.raises(psycopg.errors.CheckViolation):
            insert_misc(conn, new_ingredient(conn, label), purpose, category, usages)
        conn.execute("rollback to savepoint s")

    for label, column, value in (("negative time", "time_min", -1), ("negative dose", "dose_g_per_l", "[-1,2]")):
        conn.execute("savepoint s")
        with pytest.raises(psycopg.errors.CheckViolation):
            ingredient_id = new_ingredient(conn, label)
            conn.execute(
                f"insert into ref.misc (ingredient_id, purpose, category, usages, {column})"
                " values (%s, 'flavour', 'spice', array['boil'], %s)",
                (ingredient_id, value),
            )
        conn.execute("rollback to savepoint s")


# ---------------------------------------------------------------- resolver (Task 5)

from pathlib import Path  # noqa: E402

from tests.test_extra_ingredients import load_fixtures  # noqa: E402


def resolve(conn, word):
    return conn.execute(
        "select ingredient_id, kind, name, rule from app.resolve_ingredient(%s)", (word,)
    ).fetchall()


def test_misc_kind_words_find_misc_products(conn):
    load_fixtures(conn)
    assert [(r[1], r[2]) for r in resolve(conn, "Fixture Spice")] == [("misc", "Fixture Spice")]
    assert [(r[1], r[2]) for r in resolve(conn, "fixture spice seed")] == [("misc", "Fixture Spice")]
    assert [(r[1], r[2]) for r in resolve(conn, "herb fixture no dose")] == [("misc", "Fixture No Dose")]
    # a misc kind word restricts to misc, so another kind's name finds nothing
    assert resolve(conn, "herb Citra") == []
