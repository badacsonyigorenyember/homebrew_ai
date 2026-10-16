"""The style-neighbour check set (evals/style_neighbours.toml): the 91 study-guide triples and the 83 briefs."""

import json
import re
import tomllib
import unicodedata
from pathlib import Path

import pytest

from loaders.db import connect

ROOT = Path(__file__).resolve().parent.parent
DATA = tomllib.loads((ROOT / "evals" / "style_neighbours.toml").read_text())
TRIPLES = DATA["triple"]
BRIEFS = DATA.get("brief", [])

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


# ---- the 83 briefs -------------------------------------------------------------------------------

HINT_WORDS = {"bitter", "hoppy", "juicy", "dry", "crisp", "full", "chewy", "malty", "darker", "stronger", "session"}
STATED_COLUMNS = {"abv": "abv", "og": "og", "ibu": "ibu", "srm": "srm"}
# Words that would give a style away in a request (R1). Style names and aliases are read from the
# database in the stack test; these are the single words a name or family is known by.
NAMING_WORDS = [
    "stout", "porter", "bock", "lager", "ale", "ipa", "pils", "pilsner", "weisse", "weissbier", "weizen",
    "lambic", "gueuze", "barleywine", "saison", "kolsch", "helles", "dunkel", "marzen", "festbier", "wheat",
]
SCORED_TEXT = (
    "overallimpression", "aroma", "appearance", "flavor", "mouthfeel", "comments", "stylecomparison",
    "characteristicingredients",
)


def step1_brief(b):
    """The step 1 brief a user's sentence should produce (named stays empty: Run A)."""
    return {
        "named": None, "stated": dict(b["stated"]), "hints": list(b["hints"]), "wanted": [], "excluded": [],
        "inventory": [], "unknown": list(b["unknown"]), "guidance": True,
    }


def partners_of(code):
    return sorted({c for t in TRIPLES if code in t["codes"] for c in t["codes"] if c != code})


def word_in(word, text):
    return re.search(rf"(?<![a-z]){re.escape(word)}(?![a-z])", text.lower()) is not None


@pytest.mark.parametrize("b", BRIEFS, ids=lambda b: b["code"])
def test_brief_has_a_request(b):
    assert isinstance(b["request"], str) and b["request"].strip().endswith((".", "?"))


def test_one_brief_per_triple_style():
    codes = [b["code"] for b in BRIEFS]
    assert len(codes) == len(set(codes))
    assert set(codes) == {c for t in TRIPLES for c in t["codes"]}
    assert len(codes) == 83


def test_briefs_ordered_by_code():
    key = lambda c: (int(c[:-1]), c[-1])
    codes = [b["code"] for b in BRIEFS]
    assert codes == sorted(codes, key=key)


def test_partners_match_triples():
    assert BRIEFS
    for b in BRIEFS:
        assert b["partners"] == partners_of(b["code"]), b["code"]


def test_brief_shape():
    assert BRIEFS
    for b in BRIEFS:
        code = b["code"]
        assert b["named"] == "", code
        assert 1 <= len(b["stated"]) <= 2 and set(b["stated"]) <= set(STATED_COLUMNS), code
        assert set(b["hints"]) <= HINT_WORDS, code
        words = b["hints"] + b["unknown"]
        assert 2 <= len(words) <= 4 and len(set(words)) == len(words), code
        for w in words:
            assert re.fullmatch(r"[a-z][a-z-]*", w), (code, w)
        for w in b["unknown"]:
            assert len(w) >= 4, (code, w)
        for w in words:
            assert word_in(w, b["request"]), (code, w)
        for key, v in b["stated"].items():
            assert f"{v:g}" in b["request"], (code, key, v)


@pytest.mark.stack
def test_stated_numbers_in_2021_range(conn):
    assert BRIEFS
    for b in BRIEFS:
        for key, v in b["stated"].items():
            (ok,) = conn.execute(
                f"select %s::numeric <@ b.{STATED_COLUMNS[key]} from ref.beer_style b "
                "join ref.source s on s.id = b.source_id where s.slug = 'bjcp-2021' and b.code = %s",
                (v, b["code"]),
            ).fetchone()
            assert ok, (b["code"], key, v)


@pytest.mark.stack
def test_words_from_2021_entry(conn):
    assert BRIEFS
    for b in BRIEFS:
        (raw,) = conn.execute(
            "select b.raw from ref.beer_style b join ref.source s on s.id = b.source_id "
            "where s.slug = 'bjcp-2021' and b.code = %s", (b["code"],)
        ).fetchone()
        text = " ".join(raw.get(k) or "" for k in SCORED_TEXT)
        for field, words in (("hints", b["hints"]), ("unknown", b["unknown"])):
            for w in words:
                # the word as step 2 reads it (brief_words renames some hints and drops short words)
                (read,) = conn.execute("select app.brief_words(%s::jsonb)", (json.dumps({field: [w]}),)).fetchone()
                (tags,) = conn.execute("select app.style_tags(%s::jsonb)", (json.dumps(raw),)).fetchone()
                (score,) = conn.execute("select app.style_word_score(%s, %s, %s)", (read, tags, text)).fetchone()
                assert score > 0, (b["code"], field, w)


@pytest.mark.stack
def test_no_style_name_in_request(conn):
    assert BRIEFS
    rows = conn.execute(
        "select b.code, b.name from ref.beer_style b join ref.source s on s.id = b.source_id "
        "where s.slug = 'bjcp-2021'"
    ).fetchall()
    phrases = [fold(name) for _, name in rows]
    phrases += [fold(a) for (a,) in conn.execute("select alias from app.style_alias()").fetchall()]
    own = {t_code: names for t in TRIPLES for t_code, names in zip(t["codes"], t["names"])}
    for b in BRIEFS:
        text = fold(b["request"])
        own_name = fold(own[b["code"]])
        for phrase in phrases + [own_name]:
            assert not re.search(rf"(?<![a-z]){re.escape(phrase)}(?![a-z])", text), (b["code"], phrase)
        for word in NAMING_WORDS:
            assert not re.search(rf"(?<![a-z]){word}(?![a-z])", text), (b["code"], word)


@pytest.mark.stack
def test_briefs_fit_step1_contract(conn):
    assert BRIEFS
    schema = json.loads((ROOT / "shared" / "contracts" / "step1.output.schema.json").read_text())
    for b in BRIEFS:
        (errs,) = conn.execute(
            "select coalesce(extensions.jsonschema_validation_errors(%s::json, %s::json), '{}')",
            (json.dumps(schema), json.dumps(step1_brief(b))),
        ).fetchone()
        assert errs == [], (b["code"], errs)
