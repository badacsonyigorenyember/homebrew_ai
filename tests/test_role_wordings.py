"""The role measurement set: shape, counts and labels (m2-adjunct-role Task 1)."""

import re
import tomllib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORDINGS = tomllib.loads((ROOT / "evals" / "role_wordings.toml").read_text(encoding="utf-8"))["wording"]
BRIEFS = {
    b["id"]: b["request"]
    for b in tomllib.loads((ROOT / "evals" / "recipe_briefs.toml").read_text(encoding="utf-8"))["brief"]
}
FIELDS = {"id", "set", "adjunct", "expected", "source", "request"}


def _of(set_name):
    return [w for w in WORDINGS if w["set"] == set_name]


def test_every_wording_has_exactly_the_fields():
    for w in WORDINGS:
        assert set(w) == FIELDS, w["id"]
        assert w["request"].strip(), w["id"]


def test_ids_are_unique():
    ids = [w["id"] for w in WORDINGS]
    assert len(ids) == len(set(ids))


def test_counts():
    assert len(WORDINGS) == 34
    clear = _of("clear")
    assert Counter(w["expected"] for w in clear) == {"feature": 14, "background": 7}
    ambiguous = _of("ambiguous")
    assert len(ambiguous) == 3
    assert all(w["expected"] == "" for w in ambiguous)
    held = _of("held_out")
    assert Counter(w["expected"] for w in held) == {"feature": 5, "background": 5}


def test_sets_and_expected_values_are_known():
    for w in WORDINGS:
        assert w["set"] in {"clear", "ambiguous", "held_out"}, w["id"]
        assert w["expected"] in {"feature", "background", ""}, w["id"]


def test_adjunct_is_a_whole_word_in_the_request():
    for w in WORDINGS:
        text = w["request"].lower().replace("-", " ")
        assert re.search(rf"\b{re.escape(w['adjunct'].lower())}\b", text), w["id"]


def test_r01_and_r15_are_b12_and_b19():
    by_id = {w["id"]: w for w in WORDINGS}
    assert by_id["r01"]["request"] == BRIEFS["b12"]
    assert by_id["r15"]["request"] == BRIEFS["b19"]


def test_held_out_set_covers_molasses_and_non_specialty_adjuncts():
    held = _of("held_out")
    adjuncts = {w["adjunct"] for w in held}
    assert "molasses" in adjuncts
    assert len(adjuncts - {"honey"}) >= 3
