"""app.recipe_deviation takes every kind of step 3 deviation (db/045_recipe_deviation_kind.sql).

R7, A8 of docs/work/m6-compute-validate/brief.md. Every insert is rolled back.
"""

import psycopg
import pytest

from loaders.db import connect
from tests.test_step4 import BRIEFS, brief_of, sql

pytestmark = pytest.mark.stack


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


@pytest.fixture
def recipe_id(conn):
    """A throwaway brief and recipe, rolled back after the test."""
    brief_id = conn.execute(
        "insert into app.brief (request_text, brief) values ('test', '{}'::jsonb) returning id"
    ).fetchone()[0]
    style_id = conn.execute("select id from ref.beer_style limit 1").fetchone()[0]
    rid = conn.execute(
        "insert into app.recipe (brief_id, style_id, batch_l, efficiency_pct, targets, calc_version) "
        "values (%s, %s, 20, 70, '{}'::jsonb, 'test') returning id",
        [brief_id, style_id],
    ).fetchone()[0]
    yield rid
    conn.rollback()


def deviations_of(conn, bid):
    b = BRIEFS[bid]
    brief = brief_of(b)
    style = sql(conn, "step2_best_style", brief, b["request"], None)
    return sql(conn, "step3_deviations", brief, style)["deviations"]


def insert(conn, recipe_id, d):
    conn.execute(
        "insert into app.recipe_deviation (recipe_id, kind, subject, level, requested_by, note) "
        "values (%s, %s, %s, %s, %s, %s)",
        [recipe_id, d["kind"], d["subject"], d.get("level"), d["requested_by"], d["because"]],
    )


def test_deviation_takes_every_step3_kind(conn, recipe_id):
    """One row per kind, as step 3 gives it: b05 mismatch, b08 number, b11 conflict, b16 ingredient."""
    seen = set()
    for bid, kind in [("b05", "mismatch"), ("b08", "number"), ("b11", "conflict"), ("b16", "ingredient")]:
        found = [d for d in deviations_of(conn, bid) if d["kind"] == kind]
        assert found, f"{bid} has no {kind} deviation"
        insert(conn, recipe_id, found[0])
        seen.add(kind)
    assert seen == {"mismatch", "number", "conflict", "ingredient"}
    assert conn.execute("select count(*) from app.recipe_deviation where recipe_id = %s", [recipe_id]).fetchone()[0] == 4


def test_ingredient_deviation_needs_a_level(conn, recipe_id):
    with pytest.raises(psycopg.errors.CheckViolation):
        insert(conn, recipe_id, {"kind": "ingredient", "subject": "rice", "level": None,
                                 "requested_by": "user", "because": "x"})


def test_number_deviation_has_no_level(conn, recipe_id):
    with pytest.raises(psycopg.errors.CheckViolation):
        insert(conn, recipe_id, {"kind": "number", "subject": "IBU 50", "level": "out_of_style",
                                 "requested_by": "user", "because": "x"})
