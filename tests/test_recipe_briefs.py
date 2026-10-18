"""Shape and coverage checks for the 24 recipe test briefs in evals/recipe_briefs.toml.

Requirements R1-R3 and R5-R11 of docs/work/test-briefs/brief.md. Each coverage test fails
with the measured count in its message. `pytest -s` prints the whole coverage dict.
test_style_codes_exist_in_ref reads the live DB and is skipped when the stack is not running.
"""

import re
import tomllib
from pathlib import Path

import pytest

from loaders.db import connect

BRIEFS_FILE = Path(__file__).resolve().parent.parent / "evals" / "recipe_briefs.toml"
with BRIEFS_FILE.open("rb") as f:
    BRIEFS = tomllib.load(f)["brief"]

# The R2 field list. No other key is allowed, so style ranges cannot sneak in (R4).
FIELDS = {
    "id", "request", "named", "why", "style", "alt_styles", "deviations", "stated", "hints",
    "wanted", "excluded", "inventory", "guidance", "needs",
}
STATED_KEYS = {"batch_l", "abv", "og", "ibu", "srm"}
NEEDS_KEYS = {"fermentables", "hops", "yeast", "water_salts", "misc"}
DEVIATION_KINDS = {"ingredient", "number", "mismatch", "conflict"}

# Style buckets for R5, as BJCP 2021 codes. A brief counts by its `style`, not its alt_styles.
LAGERS = {
    "1A", "1B", "2A", "2B", "2C", "3A", "3B", "3C", "3D", "4A", "4B", "4C", "5A", "5C", "5D",
    "6A", "6B", "6C", "7A", "8A", "8B", "9A", "9B", "9C", "27F",
}
BELGIAN = {"24A", "24B", "24C", "25A", "25B", "25C", "26A", "26B", "26C", "26D"}
WHEAT_OR_SOUR = {
    "1D", "10A", "10B", "10C", "22D", "24A", "27E",                     # wheat
    "23A", "23B", "23C", "23D", "23E", "23F", "23G", "27C", "28B", "28D",  # sour
}
HOP_FORWARD = {"12C", "18B", "21A", "21B", "21C", "22A"}
STOUT_OR_PORTER = {
    "9C", "13C", "15B", "15C", "16A", "16B", "16C", "16D", "20A", "20B", "20C", "27G",
}

# The six adjunct fermentables (R6), exactly as they are written in needs.fermentables.
ADJUNCTS = ["flaked oats", "candi sugar", "flaked corn", "flaked rice", "lactose", "honey"]

# The seven rows of RECIPE-ROADMAP §7 (R9); a row is used when a brief has any of its words.
HINT_ROWS = {
    "bitter": {"bitter"},
    "hoppy/juicy": {"hoppy", "juicy"},
    "dry/crisp": {"dry", "crisp"},
    "full/chewy": {"full", "chewy"},
    "malty": {"malty"},
    "darker": {"darker"},
    "stronger/session": {"stronger", "session"},
}

# Words that mean fruit or an extra without gravity (R11). Not "chocolate": that is a malt.
# b01-b22 use none; b23 and b24 are the briefs with extras (s9) and are not counted.
EXTRAS_BRIEFS = {"b23", "b24"}
NON_GRAVITY_WORDS = {
    "fruit", "fruity", "apple", "apricot", "banana", "blackberry", "blueberry", "cherry",
    "grape", "grapefruit", "lemon", "lime", "mango", "orange", "peach", "pineapple", "plum",
    "raspberry", "strawberry", "raisin",
    "spice", "spiced", "cinnamon", "coriander", "clove", "herb", "herbs", "coffee", "vanilla",
    "cacao", "cocoa", "oak", "wood", "barrel",
}


def sentence_count(text: str) -> int:
    """Sentences end in . ! or ? followed by a space or the end; '6.5' is not an end."""
    return len(re.findall(r"[.!?]+(?:\s|$)", text.strip()))


def words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower()))


def coverage(briefs: list[dict]) -> dict[str, int]:
    """The R5-R11 counts for a list of briefs."""
    styles = [b["style"] for b in briefs]
    kinds = [d["kind"] for b in briefs for d in b["deviations"]]
    batch_sizes = {b["stated"]["batch_l"] for b in briefs if "batch_l" in b["stated"]}
    non_gravity = 0
    for b in briefs:
        if b["id"] in EXTRAS_BRIEFS:
            continue
        texts = [b["request"], *(w["item"] for w in b["wanted"]), *(item for v in b["needs"].values() for item in v)]
        non_gravity += sum(len(words(t) & NON_GRAVITY_WORDS) for t in texts)

    c = {
        "briefs": len(briefs),
        "categories": len({re.sub(r"[A-Z]+$", "", s) for s in styles}),
        "stouts_porters": sum(s in STOUT_OR_PORTER for s in styles),
        "lagers": sum(s in LAGERS for s in styles),
        "belgian": sum(s in BELGIAN for s in styles),
        "wheat_sour": sum(s in WHEAT_OR_SOUR for s in styles),
        "hop_forward": sum(s in HOP_FORWARD for s in styles),
    }
    for adjunct in ADJUNCTS:
        c[f"adjunct: {adjunct}"] = sum(adjunct in b["needs"]["fermentables"] for b in briefs)
    for kind in sorted(DEVIATION_KINDS):
        c[f"deviation: {kind}"] = kinds.count(kind)
    c["guidance_off"] = sum(not b["guidance"] for b in briefs)
    c["exclusions"] = sum(bool(b["excluded"]) for b in briefs)
    c["inventories"] = sum(bool(b["inventory"]) for b in briefs)
    for row, row_words in HINT_ROWS.items():
        c[f"hint: {row}"] = sum(bool(set(b["hints"]) & row_words) for b in briefs)
    c["batch_sizes"] = len(batch_sizes)
    c["batch_sizes_not_20"] = len(batch_sizes - {20})
    c["non_gravity_words"] = non_gravity
    return c


def at_least(c: dict[str, int], key: str, minimum: int) -> None:
    assert c[key] >= minimum, f"{key}: {c[key]} (need >= {minimum})"


def test_briefs_with_every_field():
    assert len(BRIEFS) == 24, f"briefs: {len(BRIEFS)} (need exactly 24)"
    ids = [b.get("id") for b in BRIEFS]
    assert len(set(ids)) == 24, f"duplicate ids: {sorted(i for i in set(ids) if ids.count(i) > 1)}"
    hint_words = set().union(*HINT_ROWS.values())
    for b in BRIEFS:
        bid = b.get("id")
        assert set(b) == FIELDS, f"{bid}: missing {FIELDS - set(b)}, extra {set(b) - FIELDS}"
        assert re.fullmatch(r"b\d\d", b["id"]), f"{bid}: id"
        for key in ("request", "named", "why", "style"):
            assert isinstance(b[key], str) and b[key].strip(), f"{bid}: {key} empty"
        n = sentence_count(b["request"])
        assert 1 <= n <= 3, f"{bid}: request has {n} sentences (need 1 to 3)"
        assert isinstance(b["guidance"], bool), f"{bid}: guidance is not a bool"
        for key in ("alt_styles", "hints", "wanted", "excluded", "inventory"):
            assert isinstance(b[key], list), f"{bid}: {key} is not a list"
            if key == "wanted":
                continue
            assert all(isinstance(x, str) and x for x in b[key]), f"{bid}: {key} item"
        for w in b["wanted"]:
            assert isinstance(w, dict) and set(w) == {"item", "role"}, f"{bid}: wanted item {w!r}"
            assert isinstance(w["item"], str) and w["item"], f"{bid}: wanted item word"
            assert w["role"] in ("feature", "background"), f"{bid}: wanted role {w['role']!r}"
        assert set(b["hints"]) <= hint_words, f"{bid}: unknown hints {set(b['hints']) - hint_words}"
        assert set(b["stated"]) <= STATED_KEYS, f"{bid}: stated keys {set(b['stated']) - STATED_KEYS}"
        for key, value in b["stated"].items():
            assert isinstance(value, (int, float)), f"{bid}: stated {key} is not a number"
        assert set(b["needs"]) <= NEEDS_KEYS, f"{bid}: needs keys {set(b['needs']) - NEEDS_KEYS}"
        for key, items in b["needs"].items():
            assert isinstance(items, list) and all(isinstance(x, str) and x for x in items), (
                f"{bid}: needs {key}"
            )
        assert isinstance(b["deviations"], list), f"{bid}: deviations is not a list"
        for d in b["deviations"]:
            assert set(d) == {"kind", "what", "from"}, f"{bid}: deviation keys {set(d)}"
            assert d["kind"] in DEVIATION_KINDS, f"{bid}: deviation kind {d['kind']!r}"
            assert d["what"].strip() and d["from"].strip(), f"{bid}: deviation without what/from"


@pytest.mark.stack
def test_style_codes_exist_in_ref():
    with connect() as conn:
        rows = conn.execute(
            "select b.code from ref.beer_style b join ref.source s on s.id = b.source_id"
            " where s.slug in ('bjcp-2021', 'ba-2026')"
        ).fetchall()
    known = {code for (code,) in rows}
    used = {b["style"] for b in BRIEFS} | {code for b in BRIEFS for code in b["alt_styles"]}
    assert used - known == set(), f"codes not in ref.beer_style (bjcp-2021, ba-2026): {sorted(used - known)}"


@pytest.mark.stack
def test_ba_briefs():
    with connect() as conn:
        rows = conn.execute(
            "select b.code from ref.beer_style b join ref.source s on s.id = b.source_id"
            " where s.slug = 'ba-2026'"
        ).fetchall()
    ba_codes = {code for (code,) in rows}
    expect_ba = {b["id"] for b in BRIEFS if b["style"] in ba_codes}
    assert expect_ba == {"b21", "b22"}, f"briefs expecting a ba-2026 code: {sorted(expect_ba)}"


def test_style_spread():
    c = coverage(BRIEFS)
    at_least(c, "categories", 8)
    assert c["stouts_porters"] <= 3, f"stouts_porters: {c['stouts_porters']} (need <= 3)"
    at_least(c, "lagers", 3)
    at_least(c, "belgian", 2)
    at_least(c, "wheat_sour", 2)
    at_least(c, "hop_forward", 3)


def test_adjuncts_needed():
    c = coverage(BRIEFS)
    for adjunct in ADJUNCTS:
        at_least(c, f"adjunct: {adjunct}", 1)


def test_guidance_cases():
    c = coverage(BRIEFS)
    at_least(c, "deviation: ingredient", 3)
    at_least(c, "deviation: number", 2)
    at_least(c, "deviation: mismatch", 1)
    at_least(c, "guidance_off", 1)
    at_least(c, "deviation: conflict", 1)


def test_constraint_cases():
    c = coverage(BRIEFS)
    at_least(c, "exclusions", 2)
    at_least(c, "inventories", 2)


def test_hint_rows():
    c = coverage(BRIEFS)
    for row in HINT_ROWS:
        at_least(c, f"hint: {row}", 1)


def test_batch_sizes():
    c = coverage(BRIEFS)
    at_least(c, "batch_sizes", 3)
    at_least(c, "batch_sizes_not_20", 1)


def test_no_fruit_or_non_gravity_extras():
    c = coverage(BRIEFS)
    assert c["non_gravity_words"] == 0, f"non_gravity_words: {c['non_gravity_words']} (need 0)"
    for b in BRIEFS:
        needed = {item for items in b["needs"].values() for item in items}
        missing = {
            w["item"] for w in b["wanted"]
            if not any(re.search(rf"\b{re.escape(w['item'])}\b", item) for item in needed)
        }
        assert not missing, f"{b['id']}: wanted but not in needs: {sorted(missing)}"


def test_words_are_the_users():
    for b in BRIEFS:
        request = b["request"].lower()
        for key in ("named", "wanted", "excluded", "inventory"):
            items = [b[key]] if key == "named" else b[key]
            if key == "wanted":
                items = [w["item"] for w in items]
            for item in items:
                assert item.lower() in request, f"{b['id']}: {key} {item!r} is not in the request"


def test_print_coverage():
    for key, value in coverage(BRIEFS).items():
        print(f"{key}: {value}")
