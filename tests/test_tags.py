"""Tags and flagged ingredients (s3-style-fit). Task 2 holds the schema test."""

import psycopg
import pytest

from loaders.db import connect

pytestmark = pytest.mark.stack


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def test_schema(conn):
    tables = {
        r[0]
        for r in conn.execute(
            "select tablename from pg_tables where schemaname = 'ref' "
            "and tablename in ('style_ingredient', 'ingredient_review')"
        )
    }
    assert tables == {"style_ingredient", "ingredient_review"}

    style_id = conn.execute("select id from ref.beer_style limit 1").fetchone()[0]
    ingredient_id = conn.execute("select id from ref.ingredient limit 1").fetchone()[0]
    try:
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(
                "insert into ref.style_ingredient (style_id, role, ingredient_id, quote) "
                "values (%s, 'adjunct', %s, 'x')",
                (style_id, ingredient_id),
            )
    finally:
        conn.rollback()
