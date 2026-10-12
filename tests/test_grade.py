"""Grader unit tests (no stack). Briefs come from evals/recipe_briefs.toml."""

import copy
import tomllib
from pathlib import Path

from evals import grade

FILE = Path(__file__).resolve().parent.parent / "evals" / "recipe_briefs.toml"
with FILE.open("rb") as f:
    BRIEFS = {b["id"]: b for b in tomllib.load(f)["brief"]}


def right_step1(b):
    return {"named": None, "stated": dict(b["stated"]), "hints": list(b["hints"]),
            "wanted": list(b["wanted"]), "excluded": list(b["excluded"]),
            "inventory": list(b["inventory"]), "unknown": [], "guidance": b["guidance"]}


def style(code):
    return {"style": {"id": 1, "guide": "bjcp", "code": code, "name": "x"}}


def dev(kind, subject):
    return {"kind": kind, "subject": subject, "from": "x", "level": None,
            "requested_by": "user", "because": "x"}


def test_step1_all_fields_right():
    b = BRIEFS["b08"]
    assert grade.grade_step1(b, right_step1(b)) == {f: True for f in grade.STEP1_FIELDS}


def test_step1_each_field_can_fail():
    b = BRIEFS["b08"]
    wrong = {
        "stated": {"batch_l": 10},
        "hints": [],
        "wanted": ["x"],
        "excluded": [],
        "inventory": ["x"],
        "guidance": False,
    }
    for field, value in wrong.items():
        out = right_step1(b)
        out[field] = value
        result = grade.grade_step1(b, out)
        assert [f for f, ok in result.items() if not ok] == [field]


def test_step1_order_and_case_ignored():
    b = BRIEFS["b16"]
    out = right_step1(b)
    out["excluded"] = [" mosaic", "CITRA "]
    assert grade.grade_step1(b, out)["excluded"] is True


def test_step1_missing_output_fails_every_field():
    assert grade.grade_step1(BRIEFS["b01"], None) == {f: False for f in grade.STEP1_FIELDS}


def test_step2_expected_style_passes():
    assert grade.grade_step2(BRIEFS["b01"], style("21A"))


def test_step2_alternative_style_passes():
    assert grade.grade_step2(BRIEFS["b05"], style("20C"))


def test_step2_other_style_fails():
    assert not grade.grade_step2(BRIEFS["b01"], style("21B"))


def test_step2_unknown_style_fails():
    assert not grade.grade_step2(BRIEFS["b01"], {"style": None})
    assert not grade.grade_step2(BRIEFS["b01"], None)


def test_same_kind_other_subject_does_not_match():
    expected = BRIEFS["b08"]["deviations"][0]
    assert not grade.deviation_matches(expected, dev("number", "ABV 7"))
    assert grade.deviation_matches(expected, dev("number", "IBU 50 is above the range"))


def test_other_kind_same_subject_does_not_match():
    expected = BRIEFS["b08"]["deviations"][0]
    assert not grade.deviation_matches(expected, dev("mismatch", "IBU 50"))


def test_ingredient_word_inside_subject_matches():
    expected = BRIEFS["b16"]["deviations"][0]
    assert grade.deviation_matches(expected, dev("ingredient", "flaked rice"))
    assert not grade.deviation_matches(expected, dev("ingredient", "licorice"))


def test_conflict_subject_is_hint_rows():
    expected = BRIEFS["b11"]["deviations"][0]
    assert grade.subject_key("conflict", expected["what"]) == frozenset({"dry/crisp", "full/chewy"})
    assert grade.deviation_matches(expected, dev("conflict", "dry vs chewy"))
    assert not grade.deviation_matches(expected, dev("conflict", "bitter vs malty"))


def test_step3_extra_deviation_fails():
    b = BRIEFS["b08"]
    out = {"deviations": [dev("number", "IBU"), dev("number", "OG")]}
    assert not grade.grade_step3(b, out)


def test_step3_missing_deviation_fails():
    assert not grade.grade_step3(BRIEFS["b08"], {"deviations": []})
    assert not grade.grade_step3(BRIEFS["b08"], None)


def test_step3_none_expected_none_found_passes():
    assert grade.grade_step3(BRIEFS["b01"], {"deviations": []})


def test_grade_run_combines_steps():
    b = BRIEFS["b01"]
    steps = {1: right_step1(b), 2: style("21A"), 3: {"deviations": []}}
    assert grade.grade_run(copy.deepcopy(b), steps)["passed"] is True
    assert grade.grade_run(b, {1: right_step1(b)})["passed"] is False
