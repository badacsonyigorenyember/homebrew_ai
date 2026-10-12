"""Pure graders that score a pipeline run against a brief in evals/recipe_briefs.toml.

No I/O. Step 1 is graded field by field, step 2 by style code, step 3 by matching deviations
(same kind, same subject). Design: docs/work/m0-harness/plan.md Task 4.
"""

import re

STEP1_FIELDS = ("stated", "hints", "wanted", "excluded", "inventory", "guidance")
QUANTITIES = ("batch_l", "abv", "og", "ibu", "srm")

# RECIPE-ROADMAP §7 hint rows; the same rows as tests/test_recipe_briefs.py::HINT_ROWS.
HINT_ROWS = {
    "bitter": {"bitter"},
    "hoppy/juicy": {"hoppy", "juicy"},
    "dry/crisp": {"dry", "crisp"},
    "full/chewy": {"full", "chewy"},
    "malty": {"malty"},
    "darker": {"darker"},
    "stronger/session": {"stronger", "session"},
}


def _clean_set(items) -> set[str]:
    return {str(x).strip().lower() for x in items or []}


def _whole_word(word: str, text: str) -> bool:
    return re.search(rf"\b{re.escape(word.strip().lower())}\b", text.lower()) is not None


def _stated_equal(a: dict, b: dict) -> bool:
    if set(a) != set(b):
        return False
    return all(abs(float(a[k]) - float(b[k])) <= 1e-9 for k in a)


def grade_step1(brief: dict, output: dict | None) -> dict[str, bool]:
    if output is None:
        return {f: False for f in STEP1_FIELDS}
    result = {}
    for field in ("hints", "wanted", "excluded", "inventory"):
        result[field] = _clean_set(output.get(field)) == _clean_set(brief[field])
    try:
        result["stated"] = _stated_equal(output.get("stated") or {}, brief["stated"])
    except (TypeError, ValueError):
        result["stated"] = False
    result["guidance"] = bool(output.get("guidance")) == bool(brief["guidance"])
    return {f: result[f] for f in STEP1_FIELDS}


def grade_step2(brief: dict, output: dict | None) -> bool:
    if output is None or not output.get("style"):
        return False
    return output["style"].get("code") in [brief["style"], *brief["alt_styles"]]


def subject_key(kind: str, text: str):
    text = text.strip().lower()
    if kind in ("number", "mismatch"):
        for quantity in QUANTITIES:
            if _whole_word(quantity, text):
                return quantity
        return text
    if kind == "conflict":
        return frozenset(
            row for row, words in HINT_ROWS.items() if any(_whole_word(w, text) for w in words)
        )
    return text


def deviation_matches(expected: dict, got: dict) -> bool:
    kind = expected["kind"]
    if got.get("kind") != kind:
        return False
    if kind == "ingredient":
        return _whole_word(expected["what"], got["subject"])
    return subject_key(kind, expected["what"]) == subject_key(kind, got["subject"])


def grade_step3(brief: dict, output: dict | None) -> bool:
    if output is None:
        return False
    unmatched = list(output.get("deviations") or [])
    for expected in brief["deviations"]:
        for i, got in enumerate(unmatched):
            if deviation_matches(expected, got):
                del unmatched[i]
                break
        else:
            return False
    return not unmatched


def grade_run(brief: dict, steps: dict[int, dict | None]) -> dict:
    fields = grade_step1(brief, steps.get(1))
    step1 = {**fields, "ok": all(fields.values())}
    step2 = grade_step2(brief, steps.get(2))
    step3 = grade_step3(brief, steps.get(3))
    return {"step1": step1, "step2": step2, "step3": step3,
            "passed": step1["ok"] and step2 and step3}
