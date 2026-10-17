"""Tags and flagged ingredients (s3-style-fit): the schema (Task 2), the vocabulary and the
automatic tagging (Task 3)."""

import psycopg
import pytest

from loaders import tags
from loaders.db import connect


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


@pytest.fixture(scope="module")
def vocab():
    return tags.read_vocab()


def ingredient_id(conn, name, kind):
    return conn.execute(
        "select id from ref.ingredient where kind = %s and name = %s order by id limit 1", (kind, name)
    ).fetchone()[0]


def tag_names(conn, iid, facet):
    return {
        r[0]
        for r in conn.execute(
            "select t.name from ref.ingredient_tag it join ref.tag t on t.id = it.tag_id "
            "where it.ingredient_id = %s and t.facet = %s",
            (iid, facet),
        )
    }


@pytest.mark.stack
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
    ingredient = conn.execute("select id from ref.ingredient limit 1").fetchone()[0]
    try:
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(
                "insert into ref.style_ingredient (style_id, role, ingredient_id, quote) "
                "values (%s, 'adjunct', %s, 'x')",
                (style_id, ingredient),
            )
    finally:
        conn.rollback()


def test_split_words():
    # Hungarian list, "és" and "and", mixed case, stray spaces
    assert tags.split_words("Citrusos,  Virágos és Fenyős") == ["citrusos", "virágos", "fenyős"]
    assert tags.split_words("mangó és ananász, körte , dinnye") == ["mangó", "ananász", "körte", "dinnye"]
    assert tags.split_words("fruity and spicy") == ["fruity", "spicy"]
    # a word with "és" inside it is not split
    assert tags.split_words("észteres") == ["észteres"]
    # empty, unknown-marker and None give nothing
    assert tags.split_words("") == []
    assert tags.split_words("???") == []
    assert tags.split_words(None) == []
    # filler words at either end of a phrase are dropped
    assert tags.split_words("ananászos jegyekkel, erősen gyümölcsös", filler={"jegyekkel", "erősen"}) == [
        "ananászos",
        "gyümölcsös",
    ]


def test_hop_words_prefers_aroma_line():
    sku = {
        "spec": "Alfa-sav 10-15 % Felhasználás: IPA Aroma : Citrus, grapefruit, lime, trópusi gyümölcsök",
        "params": {"Komló aroma": "Trópusi gyümölcsös, Citrusos, Édes gyümölcsös, Virágos"},
    }
    assert tags.hop_words({"hopline-hops": {"1": sku}}) == ["citrus", "grapefruit", "lime", "trópusi gyümölcsök"]
    # no usable line (missing, empty or ???) -> the "Komló aroma" list
    for spec in ("Alfa-sav 10-15 %", "Aroma : ???", "Aroma :"):
        raw = {"hopline-hops": {"1": {"spec": spec, "params": {"Komló aroma": "Citrusos, Virágos"}}}}
        assert tags.hop_words(raw) == ["citrusos", "virágos"]
    # nothing at all
    assert tags.hop_words({"hopline-hops": {"1": {"spec": "Aroma : ???", "params": {}}}}) == []


def test_yeast_words_structured_then_spec():
    raw = {"hopline-yeasts": {"1": {"params": {"Aroma": "Gyümölcsös, Semleges"}, "spec": "x"}}}
    assert tags.yeast_words(raw) == ["gyümölcsös", "semleges"]
    raw = {"hopline-yeasts": {"1": {"params": {}, "table": {"Aroma": "ribizli"}, "spec": None}}}
    assert tags.yeast_words(raw) == ["ribizli"]
    assert tags.yeast_words({"hopline-yeasts": {"1": {"params": {}, "spec": "Stílus Hőmérséklet"}}}) == []


@pytest.mark.stack
def test_every_hop_tagged_or_flagged(conn):
    rows = conn.execute(
        """
        select i.name,
               exists (select 1 from ref.ingredient_tag it join ref.tag t on t.id = it.tag_id
                       where it.ingredient_id = i.id and t.facet = 'character') as tagged,
               exists (select 1 from ref.ingredient_review r where r.ingredient_id = i.id) as flagged
        from ref.ingredient i where i.kind = 'hop'
        """
    ).fetchall()
    assert len(rows) == 89  # Sterling removed (db/035_drop_sterling.sql, user 2026-10-15)
    assert [r[0] for r in rows if not (r[1] or r[2])] == []


@pytest.mark.stack
def test_retag_is_identical(conn, vocab):
    def snapshot():
        return sorted(conn.execute("select ingredient_id, tag_id, reviewed from ref.ingredient_tag").fetchall()), sorted(
            conn.execute("select ingredient_id, reason from ref.ingredient_review").fetchall()
        )

    try:
        before = snapshot()
        tags.derive_tags(conn, vocab)
        tags.derive_tags(conn, vocab)
        assert snapshot() == before
        assert before[0], "no ingredient_tag rows: run python -m loaders.tags first"
    finally:
        conn.rollback()


@pytest.mark.stack
def test_new_synonym_retags(conn, vocab):
    """A word without a synonym flags the hop; adding the synonym tags it and drops the flag."""
    try:
        amarillo = ingredient_id(conn, "Amarillo", "hop")
        tag_id, word = conn.execute(
            "select tag_id, word from ref.tag_synonym where word = 'grapefruitos'"
        ).fetchone()
        conn.execute("delete from ref.tag_synonym where word = %s", (word,))
        tags.derive_tags(conn, vocab)
        reason = conn.execute("select reason from ref.ingredient_review where ingredient_id = %s", (amarillo,)).fetchone()
        assert reason is not None and word in reason[0]
        assert "grapefruit" not in tag_names(conn, amarillo, "character")

        conn.execute("insert into ref.tag_synonym (word, tag_id) values (%s, %s)", (word, tag_id))
        tags.derive_tags(conn, vocab)
        assert "grapefruit" in tag_names(conn, amarillo, "character")
        assert conn.execute("select 1 from ref.ingredient_review where ingredient_id = %s", (amarillo,)).fetchone() is None
    finally:
        conn.rollback()


@pytest.mark.stack
def test_citra_tags(conn):
    citra = ingredient_id(conn, "Citra", "hop")
    assert tag_names(conn, citra, "origin") == {"US"}
    characters = tag_names(conn, citra, "character")
    assert {"citrus", "tropical"} <= characters
    assert "floral" not in characters


@pytest.mark.stack
def test_yeast_families(conn):
    us05 = ingredient_id(conn, "SafAle US-05", "yeast")
    assert tag_names(conn, us05, "family") == {"american-ale"}
    assert tag_names(conn, us05, "character") == set()
    brett = ingredient_id(conn, "SafBrew BR-8", "yeast")
    assert "brett" in tag_names(conn, brett, "family")
    sour = ingredient_id(conn, "Philly Sour", "yeast")
    assert "sour" in tag_names(conn, sour, "family")
    assert tag_names(conn, ingredient_id(conn, "German Lager", "yeast"), "family") == {"lager"}


@pytest.mark.stack
def test_fermentable_tags(conn):
    roast = ingredient_id(conn, "Carafa Type 1", "fermentable")
    assert tag_names(conn, roast, "family") == {"roast"}
    assert "coffee" in tag_names(conn, roast, "character")
    smoked = ingredient_id(conn, "Beech Smoked Barley Malt", "fermentable")
    assert "smoke" in tag_names(conn, smoked, "character")
    assert tag_names(conn, ingredient_id(conn, "Lactose", "fermentable"), "family") == {"sugar"}


def test_descriptor_tag(vocab):
    synonyms = vocab["synonyms"]
    characters = {t["name"] for t in vocab["tag"] if t["facet"] == "character"}
    assert tags.descriptor_tag("dried-fruit", synonyms, characters) == "dried-fruit"  # a tag name
    assert tags.descriptor_tag("Citrusos", synonyms, characters) == "citrus"  # a synonym, name_key compared
    assert tags.descriptor_tag("zzword", synonyms, characters) is None
