"""The user-approved golden set run against app.style_level (Task 8 of s3-style-fit; A4, A5, A8)."""

import tomllib
from pathlib import Path

import pytest
from psycopg.types.json import Jsonb

from loaders.db import connect

GOLDEN = Path(__file__).parent / "fixtures" / "style_fit_golden.toml"
CASES = tomllib.loads(GOLDEN.read_text(encoding="utf-8"))["case"]
CITRA_IDS = ["c01", "c02", "c03", "c04", "c05", "c06"]


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def run_case(conn, case):
    row = conn.execute(
        "select id from ref.ingredient where kind = %s and producer = %s and name = %s",
        (case["kind"], case["producer"], case["name"]),
    ).fetchone()
    assert row, f"{case['id']}: no ingredient {case['name']!r}"
    result = conn.execute(
        "select app.style_level(%s, %s, %s, %s)",
        (case["style"], row[0], case["usage"], Jsonb(case["dose"])),
    ).fetchone()[0]
    conn.rollback()
    return result


@pytest.mark.stack
@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_golden_case(conn, case):
    result = run_case(conn, case)
    assert result["level"] == case.get("level"), f"{case['note']} | because: {result['because']}"
    assert result["because"]


@pytest.mark.stack
def test_citra_table(conn):
    """A4: the six Citra cases come out exactly as approved."""
    by_id = {c["id"]: c for c in CASES}
    got = {i: run_case(conn, by_id[i])["level"] for i in CITRA_IDS}
    assert got == {
        "c01": "allowed", "c02": "out_of_style", "c03": "out_of_style",
        "c04": "allowed", "c05": "typical", "c06": "out_of_style",
    }


@pytest.mark.stack
def test_m3_cases_have_no_rule(conn):
    """R8: the M3 ingredient cases are decided by the general rule, not by a style_rule row."""
    ids = [c for c in CASES if c["id"].startswith("m0") and c["id"] != "m08"]
    assert len(ids) == 7
    count = conn.execute(
        """select count(*) from ref.style_rule r
           join ref.beer_style b on b.id = r.style_id
           join ref.ingredient i on i.id = r.ingredient_id
           where (b.code, i.name) in (('18B','Flaked Rice'),('17C','Honey'),('19C','Lactose'),
                 ('21C','Flaked Oats'),('1B','Flaked Rice'),('1C','Flaked Corn'),('31B','Honey'),
                 ('16A','Lactose'))"""
    ).fetchone()[0]
    assert count == 0
