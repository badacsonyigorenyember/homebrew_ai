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


def citra_with_alias(conn, alias):
    """Insert a temporary alias for Citra; the caller rolls back."""
    citra = conn.execute(
        "select id from ref.ingredient where kind = 'hop' and name = 'Citra'"
    ).fetchone()[0]
    conn.execute(
        "insert into ref.ingredient_alias (ingredient_id, alias) values (%s, %s)", (citra, alias)
    )
    return citra


@pytest.mark.stack
def test_alias_finds_only_its_product(conn):
    try:
        citra = citra_with_alias(conn, "zz test alias")
        assert [(r[0], r[2], r[3]) for r in resolve(conn, "zz test alias")] == [
            (citra, "Citra", "alias")]
    finally:
        conn.rollback()


@pytest.mark.stack
def test_alias_with_kind_word(conn):
    try:
        citra = citra_with_alias(conn, "zz test alias")
        assert [(r[0], r[3]) for r in resolve(conn, "zz test alias hop")] == [(citra, "alias")]
        assert [r for r in resolve(conn, "zz test alias malt") if r[3] == "alias"] == []
    finally:
        conn.rollback()


@pytest.mark.stack
def test_by_name_ignores_aliases(conn):
    try:
        citra_with_alias(conn, "zz test alias")
        rows = conn.execute(
            "select * from app.resolve_ingredient_by_name('zz test alias')").fetchall()
        assert rows == []
    finally:
        conn.rollback()


@pytest.mark.stack
def test_misc_kind_words_leave_brief_words_alone(conn):
    # every wanted word of b01-b22 must find the same products with the misc kind words as without
    # them: the "without" run swaps in the three-word kind list (rolled back). b23, b24 want misc.
    words = [w["item"] for b in BRIEFS if b["id"] not in ("b23", "b24") for w in b["wanted"]]
    try:
        with_misc = {w: sorted(r[0] for r in resolve(conn, w)) for w in words}
        conn.execute("""create or replace function app.ingredient_kind_word()
            returns table (word text, kind text) language sql immutable as
            $$ values ('malt', 'fermentable'), ('hop', 'hop'), ('yeast', 'yeast') $$""")
        without_misc = {w: sorted(r[0] for r in resolve(conn, w)) for w in words}
    finally:
        conn.rollback()
    assert with_misc == without_misc
    rows = resolve(conn, "smoked malt cherry wood")
    assert rows and {r[1] for r in rows} == {"fermentable"}
