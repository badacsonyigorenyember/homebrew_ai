"""Pure graders that score a pipeline run against a brief in evals/recipe_briefs.toml.

No I/O. Step 1 is graded field by field, step 2 by style code, step 3 by matching deviations
(same kind, same subject). Steps 4 and 5 are checked against the brief and against `facts` the
caller reads from the database (style ranges, app.abv, the rules); the grader holds no brewing
maths of its own. Design: docs/work/m0-harness/plan.md Task 4,
docs/work/m4-targets-blueprint/plan.md Task 7.
"""

import re
import unicodedata

STEP1_FIELDS = ("named", "stated", "hints", "wanted", "excluded", "inventory", "guidance")
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

# What each hint moves among the step 4 targets (knob, direction), for hints that move one.
# Kept apart from the SQL table (app.hint_knob) on purpose, so the grader checks it.
HINT_KNOBS = {
    "bitter": [("ibu", 1)],
    "dry": [("mash", -1)], "crisp": [("mash", -1)],
    "full": [("mash", 1)], "chewy": [("mash", 1)],
    "malty": [("ibu", -1)],
    "darker": [("srm", 1)],
    "stronger": [("og", 1)],
    "session": [("og", -1)],
}
INTENT_HINTS = ("hoppy", "juicy", "dry", "crisp", "full", "chewy", "malty", "darker")
MASH_C = {-1: 64.5, 1: 68.5}
MASH_DEFAULT_C = 66.5
TARGETS = ("og", "fg", "abv", "ibu", "srm")
ABV_TOLERANCE = 0.1
EPS = 1e-6


# Naming variants of the same ingredient, each mapped to its first word. A pair must never
# differ by a form or condition word (flaked, ground, malted...): `rice` is not `flaked rice`.
SYNONYMS = (
    ("crystal malt", "caramel malt"),
    ("east kent goldings", "ekg"),
)
_SYNONYM_OF = {variant: pair[0] for pair in SYNONYMS for variant in pair}


def normalise(word) -> str:
    """Compare words without case, accents, hyphens or spacing differences."""
    text = unicodedata.normalize("NFKD", str(word))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(text.lower().replace("-", " ").split())


def _plain_set(items) -> set[str]:
    return {str(x).strip().lower() for x in items or []}


def _clean_set(items) -> set[str]:
    words = (normalise(x) for x in items or [])
    return {_SYNONYM_OF.get(w, w) for w in words}


def _wanted_pairs(items) -> set[tuple[str, str]] | None:
    """(clean item, role) pairs. None if any entry is not an {item, role} object with a role."""
    pairs = set()
    for x in items or []:
        if not isinstance(x, dict) or not x.get("role") or "item" not in x:
            return None
        pairs.add((_clean_set([x["item"]]).pop(), x["role"]))
    return pairs


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
    result["named"] = (
        output.get("named") is not None and normalise(output["named"]) == normalise(brief["named"])
    )
    result["hints"] = _plain_set(output.get("hints")) == _plain_set(brief["hints"])
    got_wanted = _wanted_pairs(output.get("wanted"))
    result["wanted"] = got_wanted is not None and got_wanted == _wanted_pairs(brief["wanted"])
    for field in ("excluded", "inventory"):
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


def _conflicted_hints(brief: dict) -> set[str]:
    """Hints of the brief that sit in one of its expected conflicts."""
    rows = set()
    for dev in brief["deviations"]:
        if dev["kind"] == "conflict":
            rows |= subject_key("conflict", dev["what"])
    return {h for row in rows for h in HINT_ROWS[row] if h in brief["hints"]}


def _in_range(value, bounds) -> bool:
    if bounds is None:
        return False
    lo, hi = bounds
    return (lo is None or value >= float(lo) - EPS) and (hi is None or value <= float(hi) + EPS)


def _quarter(value, bounds, direction) -> bool:
    """Top quarter of the range for an up move, bottom quarter for a down move."""
    lo, hi = (float(x) for x in bounds)
    edge = hi - (hi - lo) / 4 if direction == 1 else lo + (hi - lo) / 4
    return value >= edge - EPS if direction == 1 else value <= edge + EPS


def _expected_conflicts_found(brief: dict, output: dict) -> bool:
    unmatched = list(output.get("conflicts") or [])
    for expected in brief["deviations"]:
        if expected["kind"] != "conflict":
            continue
        for i, got in enumerate(unmatched):
            if deviation_matches(expected, got):
                del unmatched[i]
                break
        else:
            return False
    return True


def _every_from_set(node) -> bool:
    """Every {value, from, because} object in the output has a non-empty `from`."""
    if isinstance(node, dict):
        if "value" in node and not node.get("from"):
            return False
        return all(_every_from_set(v) for v in node.values())
    if isinstance(node, list):
        return all(_every_from_set(v) for v in node)
    return True


def grade_step4(brief: dict, output: dict | None, facts: dict | None) -> bool:
    """facts = {"ranges": {og, fg, abv, ibu, srm: [lo, hi] | None} of output.style.code,
    "abv": app.abv(target og, target fg)}. An OG solved from a stated ABV may leave its range."""
    if output is None or facts is None:
        return False
    try:
        wanted_style = brief["style"]
        style = output["style"]
        if style["from"] == "base_style":
            wanted_style = brief["alt_styles"][0]
        if style["code"] != wanted_style:
            return False
        batch = output["batch_l"]
        if float(batch["value"]) != float(brief["stated"].get("batch_l", 20)):
            return False
        if batch["from"] != ("stated" if "batch_l" in brief["stated"] else "profile"):
            return False
        t = output["targets"]
        ranges = facts["ranges"]
        abv_stated = "abv" in brief["stated"]
        value = {k: None if t[k]["value"] is None else float(t[k]["value"]) for k in TARGETS}
        for k in TARGETS:
            if k in brief["stated"]:
                if value[k] is None or abs(value[k] - float(brief["stated"][k])) > EPS or t[k]["from"] != "stated":
                    return False
            elif t[k]["from"] == "derived" and k in ("og", "fg") and abv_stated:
                continue
            elif value[k] is None or not _in_range(value[k], ranges.get(k)):
                return False
        hints = set(brief["hints"]) - _conflicted_hints(brief)
        mash = MASH_DEFAULT_C
        for hint in sorted(hints):
            for knob, direction in HINT_KNOBS.get(hint, []):
                if knob == "mash":
                    mash = MASH_C[direction]
                elif t[knob]["from"] in ("stated", "derived"):
                    continue
                elif not _quarter(value[knob], ranges[knob], direction):
                    return False
        if float(output["mash_c"]["value"]) != mash:
            return False
        if abs(float(facts["abv"]) - value["abv"]) > ABV_TOLERANCE:
            return False
        if not abv_stated and not _in_range(value["abv"], ranges.get("abv")):
            return False
        if not _expected_conflicts_found(brief, output):
            return False
        return _every_from_set(output)
    except (KeyError, TypeError, ValueError, IndexError):
        return False


def grade_step5(brief: dict, output: dict | None, step4: dict | None, facts: dict | None) -> bool:
    """facts = {"rules": rows of app.formulation_rules() as {rule, checked, sentence},
    "band_attenuation": app.mash_attenuation of the frame's yeast band (middle +- 3) at step 4's mash}."""
    if output is None or step4 is None or facts is None:
        return False
    try:
        if any(not slot["refs"] for slot in output["slots"]):
            return False
        if [normalise(s["item"]) for s in output["slots"]] != [normalise(w["item"]) for w in brief["wanted"]]:
            return False
        for field, got in (("excluded", output["excluded"]), ("inventory", output["inventory"])):
            have = {normalise(x["word"]) for x in got}
            if not {normalise(w) for w in brief[field]} <= have:
                return False
        covered = {h.strip() for i in output["intents"] for h in i["hints"].split(",")}
        for hint in INTENT_HINTS:
            if hint in brief["hints"] and hint not in _conflicted_hints(brief) and hint not in covered:
                return False
        if output["rules"]["rows"] != facts["rules"]:
            return False
        og = float(step4["targets"]["og"]["value"])
        fg = float(step4["targets"]["fg"]["value"])
        needed = 100 * (og - fg) / (og - 1)
        att = output["attenuation"]
        if abs(float(att["needed_pct"]) - needed) > 0.01:
            return False
        return abs(float(facts["band_attenuation"]) - needed) <= 0.01
    except (KeyError, TypeError, ValueError):
        return False


def grade_run(brief: dict, steps: dict[int, dict | None], facts: dict | None = None) -> dict:
    """`facts` holds what steps 4 and 5 need from the database: {"step4": ..., "step5": ...}."""
    facts = facts or {}
    fields = grade_step1(brief, steps.get(1))
    step1 = {**fields, "ok": all(fields.values())}
    step2 = grade_step2(brief, steps.get(2))
    step3 = grade_step3(brief, steps.get(3))
    step4 = grade_step4(brief, steps.get(4), facts.get("step4"))
    step5 = grade_step5(brief, steps.get(5), steps.get(4), facts.get("step5"))
    return {"step1": step1, "step2": step2, "step3": step3, "step4": step4, "step5": step5,
            "passed": step1["ok"] and step2 and step3 and step4 and step5}
