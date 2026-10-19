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


# --- steps 6-9 and the needs classes (docs/work/m5-choose-ingredients Task 8) ----------------------
# tests/fixtures/choose_samples.json holds real outputs of the good proposals of
# tests/test_choose_check.py and the facts evals/run.py read_choose_facts reads for them. Regenerate it
# with the helpers of tests/test_choose_outputs.py (step_inputs, outputs) and run.read_choose_facts.
import json  # noqa: E402

import pytest  # noqa: E402

from evals import run  # noqa: E402

SAMPLES = json.loads((Path(__file__).resolve().parent / "fixtures" / "choose_samples.json").read_text("utf-8"))
CLASSES = run.load_classes()
GRADERS = {6: grade.step6_problems, 7: grade.step7_problems, 8: grade.step8_problems, 9: grade.step9_problems}


def sample(bid):
    """(steps 6-9 outputs, facts) of a good proposal, deep-copied so a test can break them."""
    s = copy.deepcopy(SAMPLES[bid])
    facts = s["facts"]
    facts["refs"] = {int(k): v for k, v in facts["refs"].items()}
    facts["inputs"] = {int(k): v for k, v in facts["inputs"].items()}
    facts["excluded_ids"] = set(facts["excluded_ids"])
    return {int(k): v for k, v in s["steps"].items()}, facts


def problems(step, steps, facts):
    return GRADERS[step](steps[step], facts)


def mentions(found, code):
    return any(code in p for p in found)


@pytest.mark.parametrize("bid", ["b01", "b08", "b10", "b14", "b16", "b23", "b24"])
def test_good_picks_pass_steps_6_to_9(bid):
    steps, facts = sample(bid)
    for n in (6, 7, 8, 9):
        assert problems(n, steps, facts) == []
        assert getattr(grade, f"grade_step{n}")(BRIEFS[bid], steps[n], facts) is True


def test_missing_step_or_facts_fails():
    steps, facts = sample("b01")
    for n in (6, 7, 8, 9):
        assert GRADERS[n](None, facts) and GRADERS[n](steps[n], None)


def test_a1_id_must_be_a_candidate_of_the_kind():
    steps, facts = sample("b01")
    steps[7]["fermentables"][0]["ingredient_id"] = 987654321  # invented
    assert mentions(problems(7, steps, facts), "A1")
    steps, facts = sample("b01")
    hop = steps[8]["hops"][0]["ingredient_id"]
    steps[7]["fermentables"][0]["ingredient_id"] = hop  # a hop in the fermentables
    assert mentions(problems(7, steps, facts), "A1")
    steps, facts = sample("b01")
    first = steps[7]["fermentables"][0]["ingredient_id"]
    facts["inputs"][7]["candidates"] = [r for r in facts["inputs"][7]["candidates"] if r["ingredient_id"] != first]
    assert mentions(problems(7, steps, facts), "A1")  # a real product the table did not list


def test_a2_excluded_products():
    steps, facts = sample("b16")
    assert facts["excluded_ids"]  # Citra, Mosaic and their LUPOMAX siblings
    facts["excluded_ids"].add(steps[8]["hops"][0]["ingredient_id"])
    assert mentions(problems(8, steps, facts), "A2")


def test_run_py_finds_siblings_by_form_word():
    assert run._stripped("Citra LUPOMAX") == run._stripped("Citra") == "citra"
    assert run._stripped("Citra Blanc") != run._stripped("Citra")


def test_a3_fitting_inventory_must_be_used():
    steps, facts = sample("b10")
    munich = next(w for w in facts["inputs"][7]["inventory_words"] if w["word"] == "Munich malt")
    steps[7]["fermentables"] = [f for f in steps[7]["fermentables"] if f["ingredient_id"] not in munich["ids"]]
    assert mentions(problems(7, steps, facts), "A3")
    steps, facts = sample("b10")  # an inventory word that does not fit may stay unused
    for w in facts["inputs"][7]["inventory_words"]:
        w["fits"] = False
    steps[7]["fermentables"] = [f for f in steps[7]["fermentables"] if f["ingredient_id"] not in munich["ids"]]
    assert not mentions(problems(7, steps, facts), "A3")


def test_a3_one_fitting_inventory_yeast_is_enough():
    steps, facts = sample("b10")
    word = next(w for w in facts["inputs"][6]["inventory_words"] if w["kind"] == "yeast")
    other = [i for i in word["ids"] if i != steps[6]["yeast"]["ingredient_id"]]
    assert other
    facts["inputs"][6]["inventory_words"].append({"word": "second", "kind": "yeast", "fits": True, "ids": other})
    assert problems(6, steps, facts) == []
    steps[6]["yeast"]["ingredient_id"] = next(r["ingredient_id"] for r in facts["inputs"][6]["candidates"]
                                              if r["ingredient_id"] not in word["ids"] + other and r["type"] == "ale")
    facts["refs"][steps[6]["yeast"]["ingredient_id"]] = {**facts["refs"][word["ids"][0]], "name": "Other"}
    assert mentions(problems(6, steps, facts), "A3")


def test_a4_pipeline_pick_in_style():
    steps, facts = sample("b01")
    pick = steps[7]["fermentables"][0]
    pick["level"], pick["inventory"], pick["wanted"] = "out_of_style", None, None
    assert mentions(problems(7, steps, facts), "A4")
    pick["level"] = "changes_style"
    assert mentions(problems(7, steps, facts), "A4")
    pick["inventory"] = "my malt"  # an inventory pick is judged by the table (R3), not by A4
    assert not mentions(problems(7, steps, facts), "A4")
    facts["inputs"][7]["guidance"] = False
    pick["inventory"] = None
    assert not mentions(problems(7, steps, facts), "A4")


def test_a5_yeast_rules():
    steps, facts = sample("b08")  # a lager style that requires the lager family
    assert facts["style"]["lager"] is True
    ale = next(r for r in facts["inputs"][6]["candidates"] if r["type"] == "ale")
    steps[6]["yeast"]["ingredient_id"] = ale["ingredient_id"]
    facts["refs"][ale["ingredient_id"]] = {"kind": "yeast", "name": ale["name"], "type": "ale", "family": ["ale"]}
    found = problems(6, steps, facts)
    assert mentions(found, "not a lager yeast") and mentions(found, "lacks the family")
    steps, facts = sample("b10")  # needs the belgian family
    main = steps[6]["yeast"]["ingredient_id"]
    facts["refs"][main]["family"] = ["ale"]
    assert mentions(problems(6, steps, facts), "lacks the family belgian")
    steps, facts = sample("b01")
    facts["refs"][steps[6]["yeast"]["ingredient_id"]]["type"] = "lacto"
    assert mentions(problems(6, steps, facts), "lacto culture")


def test_a5_band_only_when_another_yeast_reaches_it():
    steps, facts = sample("b01")
    rows = {r["ingredient_id"]: r for r in facts["inputs"][6]["candidates"]}
    main = rows[steps[6]["yeast"]["ingredient_id"]]
    main["overlaps_band"] = False
    assert mentions(problems(6, steps, facts), "attenuation band")
    steps[6]["yeast"]["inventory"] = "my yeast"  # an inventory yeast is exempt
    assert not mentions(problems(6, steps, facts), "attenuation band")
    steps[6]["yeast"]["inventory"] = None
    for r in rows.values():
        r["overlaps_band"] = False  # no usable yeast reaches the band: reported, not failed
    assert not mentions(problems(6, steps, facts), "attenuation band")
    main["overlaps_band"] = None  # no figure: not assumed
    rows[next(i for i in rows if i != main["ingredient_id"])]["overlaps_band"] = True
    assert not mentions(problems(6, steps, facts), "attenuation band")


def test_a15_sour_style_needs_a_lacto_culture():
    steps, facts = sample("b14")
    assert facts["style"]["souring"] and steps[6]["souring"]
    assert problems(6, steps, facts) == []
    steps[6]["souring"] = None
    assert mentions(problems(6, steps, facts), "A15")
    steps, facts = sample("b14")
    facts["refs"][steps[6]["souring"]["ingredient_id"]]["type"] = "ale"
    assert mentions(problems(6, steps, facts), "A15")
    steps, facts = sample("b01")  # a culture nobody asked for
    facts["style"]["souring"] = False
    culture = 990001  # a lacto culture in the table
    facts["inputs"][6]["candidates"].append({"ingredient_id": culture, "name": "Culture", "kind": "yeast", "type": "lacto",
                                             "family": ["sour"], "overlaps_band": None})
    steps[6]["souring"] = {**steps[6]["yeast"], "ingredient_id": culture, "inventory": None, "wanted": None}
    facts["refs"][culture] = {"kind": "yeast", "name": "Culture", "type": "lacto", "family": ["sour"]}
    assert mentions(problems(6, steps, facts), "nobody asked")


def test_a6_fermentable_shares():
    steps, facts = sample("b01")
    steps[7]["fermentables"][0]["pct"] -= 1  # sum 99
    assert mentions(problems(7, steps, facts), "100")
    steps, facts = sample("b01")
    pick = steps[7]["fermentables"][-1]
    facts["refs"][pick["ingredient_id"]]["max_pct"] = pick["pct"] - 1
    assert mentions(problems(7, steps, facts), "above its maximum")
    steps, facts = sample("b01")
    steps[7]["fermentables"].append(dict(steps[7]["fermentables"][0], pct=0.0))
    found = problems(7, steps, facts)
    assert mentions(found, "twice") and mentions(found, "no share")


def test_a6_hop_fields():
    steps, facts = sample("b01")
    assert facts["inputs"][8]["targets"]["ibu"] > 0
    steps[8]["hops"][0]["share_pct"] += 1
    assert mentions(problems(8, steps, facts), "100")
    steps, facts = sample("b01")
    for h in steps[8]["hops"]:
        h["usage"], h["minutes"] = "dry_hop", 0
    assert mentions(problems(8, steps, facts), "no hop is boiled")
    steps, facts = sample("b01")
    steps[8]["hops"][0].update(usage="dry_hop", minutes=3)
    assert mentions(problems(8, steps, facts), "minutes 3")
    steps, facts = sample("b01")
    steps[8]["hops"][0].update(usage="boil", minutes=120)
    assert mentions(problems(8, steps, facts), "minutes 120")
    steps, facts = sample("b01")
    steps[8]["hops"][0].update(usage="mash")
    assert mentions(problems(8, steps, facts), "usage mash")


def test_a7_dose_rule():
    assert grade.expected_dose(None, "feature") is None
    assert grade.expected_dose([3.0, 3.0], "feature") == 3.0
    assert grade.expected_dose([3.0, 3.0], "background") == 3.0
    assert grade.expected_dose([0.05, 0.53], "background") == 0.05
    assert grade.expected_dose([0.05, 0.53], "feature") == 0.53
    assert grade.expected_dose([0.05, 0.53], None) == 0.05
    assert grade.expected_dose([2.64, 2.64], "background") == 2.64


def test_a7_a16_extras_follow_the_rule():
    steps, facts = sample("b23")
    vanilla = next(e for e in steps[9]["extras"] if e["name"] == "Vanilla bean")
    wanted = facts["refs"][vanilla["ingredient_id"]]["dose"]
    assert vanilla["dose_g_per_l"] == grade.expected_dose(wanted, vanilla["wanted"]["role"])
    wrong = wanted[1] if vanilla["dose_g_per_l"] == wanted[0] else wanted[0]
    vanilla["dose_g_per_l"] = wrong  # the other end of the range
    assert mentions(problems(9, steps, facts), "A7/A16")
    steps, facts = sample("b23")
    steps[9]["extras"][0]["dose_g_per_l"] = 99.0
    assert mentions(problems(9, steps, facts), "A7/A16")
    steps, facts = sample("b24")
    steps[9]["extras"][0]["dose_g_per_l"] = None  # a sourced dose must be set
    assert mentions(problems(9, steps, facts), "A7/A16")
    steps, facts = sample("b24")
    steps[9]["extras"][0]["usage"] = "mash"
    assert mentions(problems(9, steps, facts), "not one of its usages")


def test_a9_every_pick_has_because_and_level():
    for step, key in ((7, "fermentables"), (8, "hops"), (9, "extras")):
        bid = "b23" if step == 9 else "b01"
        steps, facts = sample(bid)
        steps[step][key][0]["because"] = " "
        assert mentions(problems(step, steps, facts), "A9")
        steps, facts = sample(bid)
        steps[step][key][0]["level"] = None
        assert mentions(problems(step, steps, facts), "A9")
        facts["inputs"][step]["guidance"] = False  # no level without guidance
        assert not mentions(problems(step, steps, facts), "A9")
    steps, facts = sample("b01")
    steps[6]["yeast"]["because"] = ""
    assert mentions(problems(6, steps, facts), "A9")


def test_slot_must_be_filled():
    steps, facts = sample("b23")
    slot = next(s for s in facts["inputs"][9]["slots"] if s["kind"] == "misc" and s["ids"])
    steps[9]["extras"] = [e for e in steps[9]["extras"] if e["ingredient_id"] not in slot["ids"]]
    assert mentions(problems(9, steps, facts), "is not filled")


# needs classes

def needs_of(bid, steps, facts):
    return grade.grade_needs(BRIEFS[bid], steps, facts, CLASSES)


def test_needs_classes_cover_every_needs_word():
    """Every needs word of the 24 briefs has a class, and no class is unused; water salts are M7's."""
    words = {(kind, w) for b in BRIEFS.values() for kind, ws in b["needs"].items() if kind != "water_salts" for w in ws}
    classes = {(c["kind"], c["word"]) for c in CLASSES}
    assert classes == words and len(CLASSES) == 48
    for c in CLASSES:
        assert c["why"].strip()
        fields = set(c) - {"kind", "word", "why"}
        assert fields == {"names"} or (fields and "names" not in fields and fields <= {"role", "ebc", "family", "type", "origin", "purpose", "category"})


def test_needs_special_b_is_covered_by_special_w_or_caraaroma():
    steps, facts = sample("b10")
    rows = {r["name"]: r for r in facts["inputs"][7]["candidates"]}
    assert "Special W" in rows and "Caraaroma" in rows
    assert needs_of("b10", steps, facts)["fermentables"]["Special B"] == "gap"  # in the table, not picked
    for name in ("Special W", "Caraaroma"):
        steps, facts = sample("b10")
        steps[7]["fermentables"].append(dict(steps[7]["fermentables"][0], ingredient_id=rows[name]["ingredient_id"]))
        assert needs_of("b10", steps, facts)["fermentables"]["Special B"] == "covered"


def test_needs_lactobacillus_is_covered_by_a_lacto_pick():
    steps, facts = sample("b14")
    assert needs_of("b14", steps, facts)["yeast"]["Lactobacillus"] == "covered"
    steps[6]["souring"] = None
    assert needs_of("b14", steps, facts)["yeast"]["Lactobacillus"] == "gap"


def test_needs_absent_when_no_product_is_in_the_table():
    steps, facts = sample("b10")
    special = {"Special W", "Caraaroma"}
    facts["inputs"][7]["candidates"] = [r for r in facts["inputs"][7]["candidates"] if r["name"] not in special]
    verdict = needs_of("b10", steps, facts)["fermentables"]["Special B"]
    assert verdict.startswith("absent") and "Special B" in verdict
    assert grade.needs_ok({"fermentables": {"Special B": verdict}})
    assert not grade.needs_ok({"fermentables": {"Special B": "gap"}})


def test_needs_by_attribute_class_and_missing_pieces():
    steps, facts = sample("b01")
    verdicts = needs_of("b01", steps, facts)
    assert "water_salts" not in verdicts
    rows = facts["inputs"][7]["candidates"]
    crystal = grade.class_matches(next(c for c in CLASSES if c["word"] == "crystal malt"), {
        "name": "x", "role": "crystal", "ebc": {"low": 100, "high": 120}})
    assert crystal
    cls = {"role": "crystal", "ebc": [5, 300]}
    assert not grade.class_matches(cls, {"name": "x", "role": "crystal", "ebc": {"low": 350, "high": 450}})
    assert not grade.class_matches(cls, {"name": "x", "role": "base", "ebc": {"low": 100, "high": 120}})
    assert not grade.class_matches(cls, {"name": "x", "role": "crystal", "ebc": None})
    assert grade.class_matches({"names": ["Tettnanger"]}, {"name": "tettnanger"})
    assert grade.class_matches({"origin": "DE", "purpose": "aroma"}, {"name": "x", "origins": ["DE"], "purpose": "aroma"})
    assert not grade.class_matches({"origin": "DE", "purpose": "aroma"}, {"name": "x", "origins": ["DE"], "purpose": "bittering"})
    assert rows
    # a step that did not run is a gap, and so is a word with no class
    none = grade.grade_needs(BRIEFS["b01"], {}, None, CLASSES)
    assert all(v.startswith("gap") for ws in none.values() for v in ws.values())
    assert grade.grade_needs(BRIEFS["b01"], steps, facts, [])["yeast"]["American ale yeast"].startswith("gap: no class")


def test_grade_run_includes_steps_6_to_9_and_needs():
    steps, facts = sample("b10")
    graded = grade.grade_run(BRIEFS["b10"], steps, {"choose": facts}, CLASSES)
    assert [graded[f"step{n}"] for n in (6, 7, 8, 9)] == [True] * 4
    assert graded["needs_ok"] is False and graded["passed"] is False  # Special B is a gap
    assert graded["problems"] == {}
    steps[7]["fermentables"][0]["because"] = ""
    graded = grade.grade_run(BRIEFS["b10"], steps, {"choose": facts}, CLASSES)
    assert graded["step7"] is False and 7 in graded["problems"]
