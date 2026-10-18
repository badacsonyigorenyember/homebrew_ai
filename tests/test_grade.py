"""Grader unit tests (no stack). Briefs come from evals/recipe_briefs.toml."""

import copy
import tomllib
from pathlib import Path

from evals import grade

FILE = Path(__file__).resolve().parent.parent / "evals" / "recipe_briefs.toml"
with FILE.open("rb") as f:
    BRIEFS = {b["id"]: b for b in tomllib.load(f)["brief"]}


def right_step1(b):
    return {"named": b["named"], "stated": dict(b["stated"]), "hints": list(b["hints"]),
            "wanted": [dict(w) for w in b["wanted"]], "excluded": list(b["excluded"]),
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
        "named": "x",
        "stated": {"batch_l": 10},
        "hints": [],
        "wanted": [{"item": "x", "role": "background"}],
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


def test_form_word_is_a_different_ingredient():
    b = BRIEFS["b16"]
    out = right_step1(b)
    out["wanted"] = [{"item": "flaked rice", "role": "background"}]
    assert grade.grade_step1(b, out)["wanted"] is False


def test_case_and_spacing_ignored():
    b = BRIEFS["b16"]
    out = right_step1(b)
    out["wanted"] = [{"item": "Flaked  Rice", "role": "background"}]
    b = {**b, "wanted": [{"item": "flaked rice", "role": "background"}]}
    assert grade.grade_step1(b, out)["wanted"] is True


def test_synonym_pair_counts_as_equal():
    b = {**BRIEFS["b16"], "wanted": [{"item": "crystal malt", "role": "background"}]}
    out = right_step1(b)
    out["wanted"] = [{"item": "caramel malt", "role": "background"}]
    assert grade.grade_step1(b, out)["wanted"] is True


def test_accents_ignored_in_named():
    b = {**BRIEFS["b09"], "named": "Märzen"}
    out = right_step1(b)
    out["named"] = "Marzen"
    assert grade.grade_step1(b, out)["named"] is True


def test_named_null_is_wrong():
    b = BRIEFS["b05"]
    out = right_step1(b)
    out["named"] = None
    result = grade.grade_step1(b, out)
    assert [f for f, ok in result.items() if not ok] == ["named"]


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


def val(value, source="midpoint"):
    return {"value": value, "from": source, "because": "x"}


RANGES_21A = {"og": [1.056, 1.070], "fg": [1.008, 1.014], "abv": [5.5, 7.5],
              "ibu": [40, 70], "srm": [6, 14]}


def right_step4_b01():
    """b01: 21A, ABV 6.5 stated, bitter; OG solved from the ABV."""
    return {"style": {"code": "21A", "name": "x", "from": "chosen", "because": "x"},
            "batch_l": val(20, "stated"), "mash_c": val(66.5),
            "targets": {"og": val(1.0613, "derived"), "fg": val(1.011), "abv": val(6.5, "stated"),
                        "ibu": val(66.25, "hint"), "srm": val(10.0)},
            "knobs": [], "conflicts": [], "guidance": True}


FACTS4 = {"ranges": RANGES_21A, "abv": 6.5}


def test_step4_right_passes():
    assert grade.grade_step4(BRIEFS["b01"], right_step4_b01(), FACTS4)
    assert not grade.grade_step4(BRIEFS["b01"], None, FACTS4)
    assert not grade.grade_step4(BRIEFS["b01"], right_step4_b01(), None)


def test_step4_hint_not_moved_fails():
    out = right_step4_b01()
    out["targets"]["ibu"] = val(55, "midpoint")
    assert not grade.grade_step4(BRIEFS["b01"], out, FACTS4)


def test_step4_out_of_range_fails():
    out = right_step4_b01()
    out["targets"]["srm"] = val(30)
    assert not grade.grade_step4(BRIEFS["b01"], out, FACTS4)
    out = right_step4_b01()
    out["targets"]["fg"] = val(1.030)
    assert not grade.grade_step4(BRIEFS["b01"], out, FACTS4)


def test_step4_stated_abv_og_outside_passes():
    """b17: ABV 7 stated; the OG solved from it is above the style's OG range and is accepted."""
    b = BRIEFS["b17"]
    out = {"style": {"code": "8B", "name": "x", "from": "chosen", "because": "x"},
           "batch_l": val(20, "profile"), "mash_c": val(66.5),
           "targets": {"og": val(1.0672, "derived"), "fg": val(1.012), "abv": val(7.0, "stated"),
                       "ibu": val(25), "srm": val(14)},
           "knobs": [], "conflicts": [], "guidance": True}
    ranges = {"og": [1.046, 1.052], "fg": [1.010, 1.014], "abv": [4.6, 5.5], "ibu": [20, 30], "srm": [9, 19]}
    assert b["stated"].get("abv") == 7
    assert grade.grade_step4(b, out, {"ranges": ranges, "abv": 7.0})
    out["targets"]["og"] = val(1.0672, "midpoint")
    assert not grade.grade_step4(b, out, {"ranges": ranges, "abv": 7.0})


def test_step4_conflict_missing_fails():
    b = BRIEFS["b11"]
    out = {"style": {"code": b["style"], "name": "x", "from": "chosen", "because": "x"},
           "batch_l": val(20, "profile"), "mash_c": val(66.5),
           "targets": {"og": val(1.0565), "fg": val(1.005), "abv": val(6.69, "derived"),
                       "ibu": val(27.5), "srm": val(13.5)},
           "knobs": [], "conflicts": [], "guidance": True}
    facts = {"ranges": {"og": [1.048, 1.065], "fg": [1.002, 1.008], "abv": [5, 8], "ibu": [20, 35], "srm": [5, 22]},
             "abv": 6.69}
    assert not grade.grade_step4(b, out, facts)
    out["conflicts"] = [dev("conflict", "dry vs full, chewy")]
    assert grade.grade_step4(b, out, facts)
    out["mash_c"] = val(64.5, "hint")
    assert not grade.grade_step4(b, out, facts)


def frame_b02():
    return {"style_code": "x",
            "rules": {"from": "x", "rows": [{"rule": "1", "checked": True, "sentence": "s"}]},
            "limits": {"from": "x", "values": {}},
            "slots": [{"item": "oats", "wanted_role": "background", "from": "x",
                       "refs": [{"ingredient_id": 1, "kind": "fermentable", "name": "Flaked Oats",
                                 "role": "adjunct", "max_pct": 30}]}],
            "excluded": [], "inventory": [],
            "intents": [{"hints": "hoppy, juicy", "knob": "late_hop_share", "intent": "x",
                         "source": "unsourced", "from": "hint"}],
            "attenuation": {"needed_pct": 75.0, "from": "derived", "because": "x"}, "guidance": True}


STEP4_B02 = {"targets": {"og": val(1.060), "fg": val(1.015)}}
FACTS5 = {"rules": [{"rule": "1", "checked": True, "sentence": "s"}], "band_attenuation": 75.0}


def test_step5_right_passes():
    b = BRIEFS["b02"]
    assert grade.grade_step5(b, frame_b02(), STEP4_B02, FACTS5)
    assert not grade.grade_step5(b, None, STEP4_B02, FACTS5)


def test_step5_missing_slot_fails():
    b = BRIEFS["b02"]
    out = frame_b02()
    out["slots"][0]["refs"] = []
    assert not grade.grade_step5(b, out, STEP4_B02, FACTS5)
    out = frame_b02()
    out["slots"] = []
    assert not grade.grade_step5(b, out, STEP4_B02, FACTS5)
    out = frame_b02()
    out["intents"] = []
    assert not grade.grade_step5(b, out, STEP4_B02, FACTS5)


def test_step5_wrong_attenuation_fails():
    b = BRIEFS["b02"]
    out = frame_b02()
    out["attenuation"]["needed_pct"] = 70.0
    assert not grade.grade_step5(b, out, STEP4_B02, FACTS5)
    assert not grade.grade_step5(b, frame_b02(), STEP4_B02, {**FACTS5, "band_attenuation": 76.0})


def unstated_abv_b01():
    """b01 with no stated ABV: OG and ABV are derived and must sit inside the style's ranges."""
    b = copy.deepcopy(BRIEFS["b01"])
    del b["stated"]["abv"]
    out = right_step4_b01()
    out["targets"]["og"] = val(1.0613)
    out["targets"]["abv"] = val(6.5, "derived")
    return b, out


def test_step4_unstated_abv_baseline_passes():
    b, out = unstated_abv_b01()
    assert grade.grade_step4(b, out, FACTS4)


def test_step4_derived_og_outside_range_fails_without_stated_abv():
    b, out = unstated_abv_b01()
    out["targets"]["og"] = val(1.080, "derived")
    assert not grade.grade_step4(b, out, FACTS4)


def test_step4_abv_must_agree_with_app_abv():
    assert not grade.grade_step4(BRIEFS["b01"], right_step4_b01(), {**FACTS4, "abv": 6.0})


def test_step4_abv_outside_range_fails_without_stated_abv():
    b, out = unstated_abv_b01()
    out["targets"]["abv"] = val(8.0, "derived")
    assert not grade.grade_step4(b, out, {**FACTS4, "abv": 8.0})


def test_step4_every_from_must_be_set():
    for target in ("ibu", "srm"):
        out = right_step4_b01()
        out["targets"][target]["from"] = ""
        assert not grade.grade_step4(BRIEFS["b01"], out, FACTS4)
    out = right_step4_b01()
    out["mash_c"]["from"] = None
    assert not grade.grade_step4(BRIEFS["b01"], out, FACTS4)


def test_step5_rules_must_equal_the_database_rules():
    b = BRIEFS["b02"]
    other = [{"rule": "1", "checked": False, "sentence": "s"}]
    assert not grade.grade_step5(b, frame_b02(), STEP4_B02, {**FACTS5, "rules": other})
    out = frame_b02()
    out["rules"]["rows"] = other
    assert not grade.grade_step5(b, out, STEP4_B02, FACTS5)


def test_grade_run_combines_steps():
    b = BRIEFS["b01"]
    steps = {1: right_step1(b), 2: style("21A"), 3: {"deviations": []}}
    graded = grade.grade_run(copy.deepcopy(b), steps)
    assert graded["step1"]["ok"] and graded["step2"] and graded["step3"]
    assert graded["step4"] is False and graded["step5"] is False and graded["passed"] is False
    assert grade.grade_run(b, {1: right_step1(b)})["passed"] is False
    steps[4] = right_step4_b01()
    graded = grade.grade_run(b, steps, {"step4": FACTS4})
    assert graded["step4"] is True and graded["step5"] is False and graded["passed"] is False


def test_wrong_role_fails_wanted():
    b = BRIEFS["b12"]
    out = right_step1(b)
    out["wanted"] = [{"item": "honey", "role": "background"}]
    assert grade.grade_step1(b, out)["wanted"] is False


def test_right_role_passes_wanted():
    b = BRIEFS["b12"]
    out = right_step1(b)
    out["wanted"] = [{"item": "Honey", "role": "feature"}]
    assert grade.grade_step1(b, out)["wanted"] is True


def test_plain_string_or_missing_role_fails_wanted():
    b = BRIEFS["b12"]
    for bad in (["honey"], [{"item": "honey"}]):
        out = right_step1(b)
        out["wanted"] = bad
        assert grade.grade_step1(b, out)["wanted"] is False
