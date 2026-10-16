"""The style-neighbour check set (evals/style_neighbours.toml): the 91 study-guide triples."""

import re
import tomllib
import unicodedata
from pathlib import Path

import pytest

from loaders.db import connect

ROOT = Path(__file__).resolve().parent.parent
DATA = tomllib.loads((ROOT / "evals" / "style_neighbours.toml").read_text())
TRIPLES = DATA["triple"]

REMOVED_IDS = {8, 19, 20, 33, 36, 40, 43, 45, 55, 72, 83, *range(97, 105)}
HAND_MAPPED = {"Vienna": "7A", "English Barleywine": "17D", "Trappist Single": "26A", "Belgian IPA": "21B"}
FAMILY_WORDS = {"ale", "lager", "bock", "ipa", "porter", "stout", "wheat"}
# BJCP 2021 family tag (typos in the data folded away) -> the noun a user would write.
TAG_TO_NOUN = {
    "amber-ale": "ale", "brown-ale": "ale", "pale-ale": "ale", "strong-ale": "ale",
    "amber-lager": "lager", "dark-lager": "lager", "pale-lager": "lager", "pilsner": "lager",
    "bock": "bock", "ipa": "ipa", "porter": "porter", "stout": "stout", "wheat-beer": "wheat",
}


def fold(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def nouns_of(tags):
    """The family nouns a style's tags give (the 'family' suffix may or may not have a dash)."""
    return {TAG_TO_NOUN[t] for t in (re.sub(r"-?family$", "", t) for t in tags) if t in TAG_TO_NOUN}


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


@pytest.fixture(scope="module")
def styles(conn):
    """code -> (name, tags) for BJCP 2021."""
    rows = conn.execute(
        "select b.code, b.name, app.style_tags(b.raw) from ref.beer_style b "
        "join ref.source s on s.id = b.source_id where s.slug = 'bjcp-2021'"
    ).fetchall()
    return {code: (name, tags) for code, name, tags in rows}


def test_triples_are_the_91():
    assert len(TRIPLES) == 91
    ids = [t["id"] for t in TRIPLES]
    assert len(set(ids)) == 91
    assert not set(ids) & REMOVED_IDS
    for t in TRIPLES:
        assert len(t["names"]) == 3 and len(t["codes"]) == 3
        assert len(set(t["codes"])) == 3, t["id"]


def test_83_distinct_styles():
    # 84 printed names, but Vienna and Vienna Lager are both 7A.
    assert len({c for t in TRIPLES for c in t["codes"]}) == 83


@pytest.mark.stack
def test_triple_names_match_2021(styles):
    for t in TRIPLES:
        for name, code in zip(t["names"], t["codes"]):
            if name in HAND_MAPPED:
                assert code == HAND_MAPPED[name], (t["id"], name)
            else:
                assert fold(name) == fold(styles[code][0]), (t["id"], name, code)


@pytest.mark.stack
def test_triple_family_from_2021_tags(styles):
    single = 0
    for t in TRIPLES:
        shared = set.intersection(*[nouns_of(styles[c][1]) for c in t["codes"]])
        assert len(shared) <= 1, (t["id"], shared)
        assert t["family"] == (next(iter(shared)) if shared else ""), t["id"]
        single += bool(t["family"])
    assert (single, len(TRIPLES) - single) == (50, 41)


@pytest.mark.stack
def test_family_is_a_family_word_only(conn):
    assert {t["family"] for t in TRIPLES if t["family"]} <= FAMILY_WORDS
    names = [n for (n,) in conn.execute(
        "select b.name from ref.beer_style b join ref.source s on s.id = b.source_id where s.slug = 'bjcp-2021'"
    ).fetchall()]
    names += [a for (a,) in conn.execute("select alias from app.style_alias()").fetchall()]
    for word in FAMILY_WORDS:
        (word_list,) = conn.execute("select app.style_words(%s)", (word,)).fetchone()
        for name in names:
            (name_list,) = conn.execute("select app.style_words(%s)", (name,)).fetchone()
            assert word_list != name_list, (word, name)


def test_one_family_per_style():
    noun_of = {}
    for t in TRIPLES:
        if not t["family"]:
            continue
        for code in t["codes"]:
            assert noun_of.setdefault(code, t["family"]) == t["family"], code
