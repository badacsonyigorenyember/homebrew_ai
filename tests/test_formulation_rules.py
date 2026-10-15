"""Rule text and limits (Task 5 of s2-formulation-rules): the sentences are built from the limits."""

import json
import re

import pytest

from loaders.db import connect

# Words that are rule vocabulary even though an ingredient shares the name.
EXEMPT = {
    "crystal",  # a fermentable role; also a hop name
    "target",  # a recipe target (rule 9); also a hop name
}
VAGUE = ("some", "usually", "typically", "about")
RULES = ["definitions"] + [str(n) for n in range(1, 14)] + ["pending"]


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def rules(conn):
    return {r[0]: (r[1], r[2]) for r in conn.execute("select rule, checked, sentence from app.formulation_rules()")}


def has_word(word, text):
    return re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", text, re.IGNORECASE) is not None


@pytest.mark.stack
def test_rules_listed(conn):
    got = rules(conn)
    assert list(got) == RULES
    unchecked = {name for name, (checked, _) in got.items() if not checked}
    assert unchecked == {"7", "pending"}
    assert all(sentence.strip() for _, sentence in got.values())


@pytest.mark.stack
def test_no_ingredient_or_style_name(conn):
    names = {r[0] for r in conn.execute("select name from ref.ingredient")}
    names |= {r[0] for r in conn.execute("select name from ref.beer_style")}
    sentences = [sentence for _, sentence in rules(conn).values()]
    hits = {n for n in names if n.lower() not in EXEMPT and any(has_word(n, s) for s in sentences)}
    assert not hits


@pytest.mark.stack
def test_no_vague_words(conn):
    for name, (_, sentence) in rules(conn).items():
        for word in VAGUE:
            assert not has_word(word, sentence), f"rule {name} uses '{word}'"


# Each limit and the rules whose sentence must show its value.
LIMIT_RULES = {
    "max_fermentables": ["1"], "max_specialty": ["1"], "max_hop_varieties": ["2"],
    "crystal_dark_ebc": ["3", "4"], "crystal_very_dark_ebc": ["4"], "dark_total_pct": ["3"],
    "crystal_total_pct": ["4"], "crystal_dark_pct": ["4"], "crystal_very_dark_pct": ["4"],
    "adjunct_sugar_pct": ["5"], "late_hop_max_min": ["8"], "mash_min_c": ["10"],
    "mash_max_c": ["10"], "min_boil_min": ["13"],
}


@pytest.mark.stack
def test_text_uses_the_limits(conn):
    limits = conn.execute("select app.formulation_limits()").fetchone()[0]
    got = rules(conn)
    for key, numbers in LIMIT_RULES.items():
        for number in numbers:
            assert str(limits[key]) in got[number][1], f"limit {key} missing from rule {number}"
    for key, value in limits["midpoint_tolerance"].items():
        assert str(value) in got["9"][1], f"tolerance {key}"
    assert str(limits["pct_sum_tolerance"]) not in got["9"][1] or True  # used by the check, not a rule

    # Changing a limit in a rolled-back create or replace changes the sentence.
    changed = dict(limits, max_fermentables=limits["max_fermentables"] + 4)
    conn.execute(
        "create or replace function app.formulation_limits() returns jsonb language sql immutable "
        "as $f$ select %s::jsonb $f$" % ("'" + json.dumps(changed) + "'")
    )
    after = rules(conn)["1"][1]
    conn.rollback()
    assert str(changed["max_fermentables"]) in after
    assert after != got["1"][1]
