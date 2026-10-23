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


# --- steps 6-9 and the needs classes --------------------------------------------------------
# The graders read the ref facts and the logged candidate rows, never app.choose_check, so a
# fault in the check cannot hide itself. `facts` is facts["choose"] (evals/run.py read_choose_facts):
#   inputs  the logged step 6..9 inputs (candidate rows, slots, inventory words, targets)
#   refs    ingredient id -> kind, name, type, family tags, role, max_pct, ebc, usages, dose
#   excluded_ids  ids of the excluded products and their siblings
#   style   lager, families, souring of the style used (step 4's)

KIND_OF_STEP = {6: "yeast", 7: "fermentable", 8: "hop", 9: "misc"}
STEP_OF_NEEDS = {"yeast": 6, "fermentables": 7, "hops": 8, "misc": 9}
BAD_LEVELS = ("out_of_style", "changes_style")
HOP_MINUTES = {"boil": 90, "whirlpool": 60, "dry_hop": 0}
SUM_TOLERANCE = 0.1


def _picks(step: int, output: dict) -> list[dict]:
    if step == 6:
        return [p for p in (output.get("yeast"), output.get("souring")) if p]
    key = {7: "fermentables", 8: "hops", 9: "extras"}[step]
    return list(output[key])


def expected_dose(dose, role):
    """The dose rule (R7): no range gives None, one point is used as it is, a background item takes
    the low end and a feature the high end."""
    if not dose:
        return None
    low, high = dose
    if low == high:
        return low
    return high if role == "feature" else low


def _pick_problems(step: int, output: dict, facts: dict) -> list[str]:
    """What every pick of a step must meet: A1 (a candidate of the right kind), A2 (not excluded),
    A3 (fitting inventory used), A4 (a good level), A9 (level and because), and the slots."""
    inp = facts["inputs"][step]
    kind = KIND_OF_STEP[step]
    candidates = {r["ingredient_id"] for r in inp["candidates"]}
    problems = []
    picks = _picks(step, output)
    for p in picks:
        i, ref = p["ingredient_id"], facts["refs"].get(p["ingredient_id"])
        if ref is None or ref["kind"] != kind or i not in candidates:
            problems.append(f"A1: {i} is not a {kind} in the candidate table")
            continue
        if i in facts["excluded_ids"]:
            problems.append(f"A2: {ref['name']} is excluded")
        if inp["guidance"] and not p.get("inventory") and not p.get("wanted") and p.get("level") in BAD_LEVELS:
            problems.append(f"A4: {ref['name']} is {p['level']} in {inp['style_used']}")
        if not str(p.get("because") or "").strip() or (inp["guidance"] and not p.get("level")):
            problems.append(f"A9: {ref['name']} has no because or level")
    picked = {p["ingredient_id"] for p in picks}
    fitting = [w for w in inp["inventory_words"] if w["kind"] == kind and w["fits"] and w["ids"]]
    if kind == "yeast":
        if fitting and not any(set(w["ids"]) & picked for w in fitting):
            problems.append("A3: no fitting inventory yeast is used")
    else:
        problems += [f"A3: inventory \"{w['word']}\" is not used" for w in fitting if not set(w["ids"]) & picked]
    problems += [f"slot \"{s['item']}\" is not filled" for s in inp["slots"]
                 if s["kind"] == kind and s["ids"] and not set(s["ids"]) & picked]
    return problems


def step6_problems(output: dict | None, facts: dict | None) -> list[str]:
    if output is None or facts is None:
        return ["step did not run"]
    try:
        problems = _pick_problems(6, output, facts)
        main, souring = output["yeast"], output.get("souring")
        ref, style = facts["refs"].get(main["ingredient_id"]), facts["style"]
        if ref is None:
            return problems
        if ref["type"] == "lacto":
            problems.append("A5: the main yeast is a lacto culture")
        elif ref["type"] not in ("ale", "lager", "kveik"):
            problems.append(f"A5: {ref['name']} is not a brewing yeast (type {ref['type']})")
        if style["lager"] and ref["type"] != "lager":
            problems.append(f"A5: {ref['name']} is not a lager yeast for a lager style")
        missing = [f for f in style["families"] if f not in ref["family"]]
        if missing:
            problems.append(f"A5: {ref['name']} lacks the family {', '.join(missing)}")
        if style["souring"] and not (souring and (facts["refs"].get(souring["ingredient_id"]) or {}).get("type") == "lacto"):
            problems.append("A15: the style is sour and no lacto culture is picked")
        if souring:
            if (facts["refs"].get(souring["ingredient_id"]) or {}).get("type") != "lacto":
                problems.append("A15: the souring pick is not a lacto culture")
            if not style["souring"] and not souring.get("inventory") and not souring.get("wanted"):
                problems.append("A15: a souring culture nobody asked for")
        rows = {r["ingredient_id"]: r for r in facts["inputs"][6]["candidates"]}
        row = rows.get(main["ingredient_id"], {})
        usable = [r for r in rows.values() if r["type"] != "lacto"
                  and (not style["lager"] or r["type"] == "lager")
                  and all(f in r["family"] for f in style["families"])]
        marked = main.get("inventory") or main.get("wanted")
        if (row.get("overlaps_band") is False and not marked
                and any(r["overlaps_band"] is True for r in usable)):
            problems.append("A5: the yeast misses the attenuation band while another usable one reaches it")
        return problems
    except (KeyError, TypeError):
        return ["step 6 output is malformed"]


def step7_problems(output: dict | None, facts: dict | None) -> list[str]:
    if output is None or facts is None:
        return ["step did not run"]
    try:
        problems = _pick_problems(7, output, facts)
        picks = output["fermentables"]
        ids = [p["ingredient_id"] for p in picks]
        if len(ids) != len(set(ids)):
            problems.append("A6: a fermentable is picked twice")
        if abs(sum(float(p["pct"]) for p in picks) - 100) > SUM_TOLERANCE:
            problems.append("A6: fermentable shares do not add up to 100")
        for p in picks:
            ref = facts["refs"].get(p["ingredient_id"]) or {}
            if float(p["pct"]) <= 0:
                problems.append(f"A6: {ref.get('name')} has no share")
            if ref.get("max_pct") is not None and float(p["pct"]) > float(ref["max_pct"]) + EPS:
                problems.append(f"A6: {ref['name']} {p['pct']} % is above its maximum {ref['max_pct']} %")
        return problems
    except (KeyError, TypeError, ValueError):
        return ["step 7 output is malformed"]


def step8_problems(output: dict | None, facts: dict | None) -> list[str]:
    if output is None or facts is None:
        return ["step did not run"]
    try:
        problems = _pick_problems(8, output, facts)
        hops = output["hops"]
        if hops and abs(sum(float(h["share_pct"]) for h in hops) - 100) > SUM_TOLERANCE:
            problems.append("A6: hop shares do not add up to 100")
        for h in hops:
            name = (facts["refs"].get(h["ingredient_id"]) or {}).get("name")
            top = HOP_MINUTES.get(h.get("usage"))
            if top is None or not 0 <= float(h["minutes"]) <= top:
                problems.append(f"A6: {name} has usage {h.get('usage')} and minutes {h.get('minutes')}")
            if float(h["share_pct"]) <= 0:
                problems.append(f"A6: {name} has no share")
        ibu = facts["inputs"][8]["targets"].get("ibu") or 0
        if ibu > 0 and not any(h["usage"] == "boil" for h in hops):
            problems.append("A6: the IBU target is above 0 and no hop is boiled")
        return problems
    except (KeyError, TypeError, ValueError):
        return ["step 8 output is malformed"]


def step9_problems(output: dict | None, facts: dict | None) -> list[str]:
    if output is None or facts is None:
        return ["step did not run"]
    try:
        problems = _pick_problems(9, output, facts)
        for e in output["extras"]:
            ref = facts["refs"].get(e["ingredient_id"]) or {}
            if e["usage"] not in ref.get("usages", []):
                problems.append(f"A7: {ref.get('name')} usage {e['usage']} is not one of its usages")
            role = (e.get("wanted") or {}).get("role")
            want = expected_dose(ref.get("dose"), role)
            got = e["dose_g_per_l"]
            if (want is None) != (got is None) or (want is not None and abs(float(got) - float(want)) > 1e-9):
                problems.append(f"A7/A16: {ref.get('name')} dose {got} is not the {role or 'default'} rule's {want}")
        return problems
    except (KeyError, TypeError, ValueError):
        return ["step 9 output is malformed"]


def grade_step6(brief, output, facts) -> bool:
    return not step6_problems(output, facts)


def grade_step7(brief, output, facts) -> bool:
    return not step7_problems(output, facts)


def grade_step8(brief, output, facts) -> bool:
    return not step8_problems(output, facts)


def grade_step9(brief, output, facts) -> bool:
    return not step9_problems(output, facts)


def _overlaps(bounds, row_ebc) -> bool:
    if not row_ebc or row_ebc.get("low") is None or row_ebc.get("high") is None:
        return False
    return float(row_ebc["low"]) <= bounds[1] and float(row_ebc["high"]) >= bounds[0]


def class_matches(cls: dict, row: dict) -> bool:
    """A candidate row belongs to a needs class: by product name, or by all the fields the class gives."""
    if "names" in cls:
        return normalise(row["name"]) in {normalise(n) for n in cls["names"]}
    if "role" in cls and row.get("role") != cls["role"]:
        return False
    if "ebc" in cls and not _overlaps(cls["ebc"], row.get("ebc")):
        return False
    if "family" in cls and cls["family"] not in (row.get("family") or []):
        return False
    if "type" in cls and row.get("type") != cls["type"]:
        return False
    if "origin" in cls and cls["origin"] not in (row.get("origins") or []):
        return False
    if "purpose" in cls and row.get("purpose") != cls["purpose"]:
        return False
    if "category" in cls and row.get("category") != cls["category"]:
        return False
    return True


def _colour_fits(pick: dict, row: dict) -> bool:
    """A crystal or kilned malt stands in for a class member only at its colour: the EBC ranges overlap
    (Caraamber is not a Special B, Melanoidin Malt is not a Munich Light Malt; no range known, or
    another role: alike)."""
    a, b = pick.get("ebc"), row.get("ebc")
    if pick.get("role") not in ("crystal", "kilned") or not a or not b or None in (a.get("low"), a.get("high"), b.get("low"), b.get("high")):
        return True
    return _overlaps((float(b["low"]), float(b["high"])), a)


ALPHA_SLACK_PCT = 3


def _alpha_fits(pick: dict, row: dict) -> bool:
    """A hop stands in for a class member only at its strength: the alpha ranges come within
    ALPHA_SLACK_PCT points of each other (Herkules at 12-17 % is not a Hallertau Mittelfrüh at 3.5 %,
    but Challenger at 6.5-9 % is an East Kent Golding at 5-6 %; no range known: alike)."""
    a, b = pick.get("alpha"), row.get("alpha")
    if not a or not b or None in (a.get("low"), a.get("high"), b.get("low"), b.get("high")):
        return True
    return float(a["low"]) <= float(b["high"]) + ALPHA_SLACK_PCT and float(a["high"]) >= float(b["low"]) - ALPHA_SLACK_PCT


def stands_in(kind: str, class_rows: list[dict], pick: dict) -> bool:
    """A pick that is not in the class but plays its part (R10, user decision 2026-10-19), by kind:
    a fermentable of the same role (a crystal or kilned malt also needs an overlapping EBC range, so only a dark crystal
    stands in for a dark crystal class); a hop of the same origin that has the class member's purpose or is `dual`
    and an alpha range within ALPHA_SLACK_PCT points; a yeast of the same type that shares a family tag other than the bare `ale` (a lager yeast
    for a lager class needs no more); an extra of the same category. The pick already passed the
    step's checks, so it is in the style."""
    for row in class_rows:
        if kind == "fermentables":
            if pick.get("role") and pick.get("role") == row.get("role") and _colour_fits(pick, row):
                return True
        elif kind == "hops":
            # per class member: the pick does the member's job (same purpose) or both (it is `dual`)
            if set(pick.get("origins") or ()) & set(row.get("origins") or ()) and \
                    pick.get("purpose") in (row.get("purpose"), "dual") and _alpha_fits(pick, row):
                return True
        elif kind == "yeast":
            shared = set(pick.get("family") or ()) & set(row.get("family") or ())
            if pick.get("type") and pick.get("type") == row.get("type") and shared - {"ale"}:
                return True
        elif kind == "misc":
            if pick.get("category") and pick.get("category") == row.get("category"):
                return True
    return False


def grade_needs(brief: dict, steps: dict, facts: dict | None, classes: list[dict]) -> dict:
    """Per kind and word of the brief's needs: `covered` (a pick is in the class), `substituted: <picks>`
    (no pick is in the class but a pick of the same kind stands in for it, see `stands_in`), `gap` (the candidate
    table has a product of the class and no pick is one or stands in), or `absent: <reason>` (the table has none).
    Water salts are M7's and are skipped."""
    by_word = {(c["kind"], normalise(c["word"])): c for c in classes}
    result = {}
    for kind, words in brief["needs"].items():
        step = STEP_OF_NEEDS.get(kind)
        if step is None:
            continue
        out = steps.get(step)
        inputs = (facts or {}).get("inputs", {}).get(step)
        result[kind] = {}
        for word in words:
            cls = by_word.get((kind, normalise(word)))
            if cls is None:
                verdict = "gap: no class for this word in evals/needs_classes.toml"
            elif out is None or inputs is None:
                verdict = f"gap: step {step} did not run"
            else:
                try:
                    picked = {p["ingredient_id"] for p in _picks(step, out)}
                    rows = [r for r in inputs["candidates"] if class_matches(cls, r)]
                except (KeyError, TypeError):
                    rows, picked = [], set()
                    verdict = f"gap: step {step} output is malformed"
                    result[kind][word] = verdict
                    continue
                if any(r["ingredient_id"] in picked for r in rows):
                    verdict = "covered"
                elif rows:
                    by_id = {r["ingredient_id"]: r for r in inputs["candidates"]}
                    standing = [by_id[i]["name"] for i in sorted(picked)
                                if i in by_id and stands_in(kind, rows, by_id[i])]
                    verdict = f"substituted: {', '.join(standing)}" if standing else "gap"
                else:
                    verdict = f"absent: no product of the class \"{word}\" is in the candidate table"
            result[kind][word] = verdict
    return result


def needs_ok(needs: dict) -> bool:
    return all(v == "covered" or v.startswith(("absent", "substituted")) for words in needs.values() for v in words.values())


def grade_run(brief: dict, steps: dict[int, dict | None], facts: dict | None = None,
              classes: list[dict] | None = None) -> dict:
    """`facts` holds what steps 4 and 5 need from the database: {"step4": ..., "step5": ...}, and for
    steps 6-9 and the needs {"choose": ...}. `classes` is the needs class map."""
    facts = facts or {}
    fields = grade_step1(brief, steps.get(1))
    step1 = {**fields, "ok": all(fields.values())}
    step2 = grade_step2(brief, steps.get(2))
    step3 = grade_step3(brief, steps.get(3))
    step4 = grade_step4(brief, steps.get(4), facts.get("step4"))
    step5 = grade_step5(brief, steps.get(5), steps.get(4), facts.get("step5"))
    choose = facts.get("choose")
    problems = {n: fn(steps.get(n), choose) for n, fn in
                ((6, step6_problems), (7, step7_problems), (8, step8_problems), (9, step9_problems))}
    needs = grade_needs(brief, steps, choose, classes or [])
    chosen = {n: not p for n, p in problems.items()}
    return {"step1": step1, "step2": step2, "step3": step3, "step4": step4, "step5": step5,
            "step6": chosen[6], "step7": chosen[7], "step8": chosen[8], "step9": chosen[9],
            "needs": needs, "needs_ok": needs_ok(needs),
            "problems": {n: p for n, p in problems.items() if p},
            "passed": step1["ok"] and step2 and step3 and step4 and step5 and all(chosen.values())
            and needs_ok(needs)}
