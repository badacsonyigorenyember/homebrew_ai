"""Ingredient-word resolver app.resolve_ingredient in db/036_ingredient_resolver.sql.

Acceptance A7 of docs/work/m3-deviations/brief.md.
"""

import tomllib
from pathlib import Path

import pytest

from loaders.db import connect

ROOT = Path(__file__).resolve().parent.parent
BRIEFS = tomllib.loads((ROOT / "evals" / "recipe_briefs.toml").read_text())["brief"]
SQL_FILE = ROOT / "db" / "036_ingredient_resolver.sql"


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def resolve(conn, word):
    return conn.execute(
        "select ingredient_id, kind, name, rule from app.resolve_ingredient(%s)", (word,)
    ).fetchall()


def names(rows):
    return [r[2] for r in rows]


@pytest.mark.stack
def test_brief_wanted_words_resolve(conn):
    expected = {"oats": "Flaked Oats", "rice": "Flaked Rice", "corn": "Flaked Corn",
                "honey": "Honey", "lactose": "Lactose"}
    for word, name in expected.items():
        assert names(resolve(conn, word)) == [name], word
    for b in BRIEFS:
        for w in b["wanted"]:
            assert resolve(conn, w["item"]), f"{b['id']}: {w['item']} resolves to nothing"


@pytest.mark.stack
def test_crystal_malt_is_not_the_crystal_hop(conn):
    rows = resolve(conn, "crystal malt")
    assert {r[1] for r in rows} == {"fermentable"}
    assert "Crystal T50" in names(rows)


@pytest.mark.stack
def test_abbey_yeast_is_not_abbey_malt(conn):
    rows = resolve(conn, "abbey yeast")
    assert {r[1] for r in rows} == {"yeast"}
    assert names(rows) == ["Abbaye", "Abbey Monk Ale", "M47 Belgian Abbey"]


@pytest.mark.stack
def test_same_name_wins(conn):
    assert names(resolve(conn, "Citra")) == ["Citra"]
    assert names(resolve(conn, "Abbey Malt")) == ["Abbey Malt"]


@pytest.mark.stack
def test_case_plural_and_synonym(conn):
    assert names(resolve(conn, "Flaked OATS")) == ["Flaked Oats"]
    assert names(resolve(conn, "East Kent Goldings")) == ["East Kent Golding"]
    assert resolve(conn, "abbaye yeast") == resolve(conn, "abbey yeast")


@pytest.mark.stack
def test_unknown_word_resolves_to_nothing(conn):
    assert resolve(conn, "unicorn tears") == []


def test_resolver_reads_no_fixture():
    text = SQL_FILE.read_text()
    for forbidden in ("recipe_briefs", "evals", "SYNONYMS"):
        assert forbidden not in text.replace("never reads evals/", ""), forbidden
