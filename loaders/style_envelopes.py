"""Style envelopes for the 26 s3 styles (s3-style-fit Task 4, load mode Task 5).

Two modes, one file:

  python -m loaders.style_envelopes --extract OUT [--style CODE]
      Offline. Sends each style's guideline prose to the D2 model (Ollama, thinking off, the
      JSON Schema as `format`), checks every answer with code, and writes a DRAFT toml to OUT
      (every style `reviewed = false`). Nothing is written to the database. This is never part
      of the n8n pipeline.

  python -m loaders.style_envelopes [FILE]
      Loads the styles the user marked `reviewed = true` in the toml (default
      loaders/style_envelopes.toml) into ref.style_sensory, ref.style_character,
      ref.style_ingredient and ref.style_rule. A reviewed style that still has `unknown` words
      or `problems` is refused. Unreviewed styles are skipped and counted. One transaction,
      re-runnable.

What code checks in an LLM answer (check_answer): every quote is a verbatim piece of the style's
prose, intensity words are on the scale, min <= max, each dimension appears once, character
words and ingredient names resolve to ref rows. A word that does not resolve is kept under
`unknown` for the reviewer; it is not guessed.
"""

import argparse
import datetime
import json
import sys
import time
import tomllib
import urllib.request
from pathlib import Path

from loaders.common import name_key
from loaders.db import connect

HERE = Path(__file__).parent
SCHEMA_PATH = HERE / "style_envelope.schema.json"
PROMPT_PATH = HERE / "style_envelope_prompt.md"
DEFAULT_TOML = HERE / "style_envelopes.toml"

OLLAMA = "http://localhost:11434"
MODEL = "hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K"  # D2
NUM_CTX = 8192

# The 22 styles of evals/recipe_briefs.toml, three alternates (20C, 18A, the honey style) and 20B
# (the Citra table). 3 of the 26 are BA styles; they go through the same path (D9).
S3_STYLES = [
    "10A", "11B", "15A", "15B", "16A", "16B", "17C", "18B", "19C", "1B", "1C", "21A", "21C",
    "23A", "25B", "26B", "31B", "5D", "6A", "8B", "mexican-style-amber-lager",
    "session-india-pale-ale",
    "20C", "18A", "specialty-honey-beer", "20B",
    "30A",  # the specialty style of b23 (coffee and vanilla), added by s9
]

SCALE = {"none": 0, "very low": 1, "low": 2, "medium-low": 3, "medium": 4, "medium-high": 5,
         "high": 6, "very high": 7}
WORD_OF = {number: word for word, number in SCALE.items()}
ROLES = ("base", "kilned", "crystal", "roast", "adjunct", "sugar")
LEVELS = ("required", "typical", "allowed", "out_of_style", "changes_style")

# The guideline fields sent to the model, in reading order, with their labels.
PROSE_FIELDS = [
    ("overallimpression", "Overall impression"),
    ("aroma", "Aroma"),
    ("appearance", "Appearance"),
    ("flavor", "Flavor"),
    ("mouthfeel", "Mouthfeel"),
    ("comments", "Comments"),
    ("characteristicingredients", "Characteristic ingredients"),
    ("entryinstructions", "Entry instructions"),
]


# ---------------------------------------------------------------- the prose


def style_prose(raw: dict) -> str:
    """The guideline fields that are present, each under its label."""
    parts = []
    for key, label in PROSE_FIELDS:
        value = raw.get(key)
        if value and str(value).strip():
            parts.append(f"{label}: {str(value).strip()}")
    return "\n\n".join(parts)


def fold(text: str) -> str:
    """Whitespace folded to single spaces, so a quote can span a line break."""
    return " ".join(text.split())


# ---------------------------------------------------------------- the LLM call


def ask(prose: str, earlier: tuple[dict, list[str]] | None = None) -> dict:
    """One extraction call. `earlier` = (the previous answer, its problems) for the second try."""
    messages = [
        {"role": "system", "content": PROMPT_PATH.read_text(encoding="utf-8")},
        {"role": "user", "content": prose},
    ]
    if earlier:
        answer, problems = earlier
        messages.append({"role": "assistant", "content": json.dumps(answer)})
        messages.append({
            "role": "user",
            "content": "Your answer had these problems:\n- " + "\n- ".join(problems)
            + "\nAnswer again with the same JSON shape, fixing them.",
        })
    body = {
        "model": MODEL,
        "messages": messages,
        "think": False,
        "stream": False,
        "format": json.loads(SCHEMA_PATH.read_text(encoding="utf-8")),
        "options": {"temperature": 0, "seed": 42, "num_ctx": NUM_CTX},
    }
    request = urllib.request.Request(
        OLLAMA + "/api/chat", data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=1800) as response:
        reply = json.loads(response.read().decode("utf-8"))
    return json.loads(reply["message"]["content"])


# ---------------------------------------------------------------- checking an answer


def load_lookups(conn) -> dict:
    """What check_answer resolves words against, read once from ref.

    characters: name_key(word) -> character tag name (synonyms, then the tag names themselves)
    tags:       name_key(name) -> origin or family tag name (for characteristic ingredients)
    ingredients: name_key(name) -> ["producer|name", ...] (several = ambiguous)
    """
    characters = {name_key(name): name for (name,) in conn.execute("select name from ref.tag where facet = 'character'")}
    for word, name in conn.execute(
        "select s.word, t.name from ref.tag_synonym s join ref.tag t on t.id = s.tag_id"
    ):
        characters[word] = name
    tags = {name_key(n): n for (n,) in conn.execute("select name from ref.tag where facet in ('origin', 'family')")}
    ingredients = {}
    for producer, name in conn.execute("select producer, name from ref.ingredient order by id"):
        ingredients.setdefault(name_key(name), []).append(f"{producer}|{name}")
    return {"characters": characters, "tags": tags, "ingredients": ingredients}


def check_answer(lookups: dict, prose: str, answer: dict) -> tuple[dict, list[str]]:
    """The model's answer as a draft with names resolved, plus the list of problems found.

    A problem is something the model got wrong and could fix (a quote not in the text, min above
    max, a repeated dimension, an ingredient with two or no kinds). A word we cannot resolve is
    not a problem: it is kept under `unknown` for the reviewer.
    """
    problems = []
    folded_prose = fold(prose)
    draft = {"sensory": [], "ingredients": []}

    seen = set()
    for entry in answer.get("sensory", []):
        dimension = entry["dimension"]
        if dimension in seen:
            problems.append(f"{dimension}: given more than once")
        seen.add(dimension)
        if fold(entry["quote"]) not in folded_prose or not entry["quote"].strip():
            problems.append(f"{dimension}: the quote is not a verbatim piece of the guideline text: {entry['quote']!r}")
        low, high = entry["min"], entry["max"]
        if low not in SCALE or high not in SCALE:
            problems.append(f"{dimension}: {low!r} / {high!r} are not on the scale")
        elif SCALE[low] > SCALE[high]:
            problems.append(f"{dimension}: min {low} is above max {high}")
        characters, unknown = [], []
        for word in entry["characters"]:
            tag = lookups["characters"].get(name_key(word))
            if tag is None:
                unknown.append(word)
            elif tag not in characters:
                characters.append(tag)
        draft["sensory"].append({
            "dimension": dimension, "min": low, "max": high, "characters": characters,
            "quote": entry["quote"], "unknown": unknown,
        })

    for entry in answer.get("ingredients", []):
        kinds = [k for k in ("role", "ingredient", "tag") if entry.get(k)]
        item = {"required": bool(entry["required"]), "min_pct": entry.get("min_pct"),
                "quote": entry["quote"], "unknown": []}
        label = entry.get("role") or entry.get("ingredient") or entry.get("tag") or "?"
        if len(kinds) != 1:
            problems.append(f"ingredient {label!r}: set exactly one of role, ingredient, tag (got {kinds})")
            continue
        if fold(entry["quote"]) not in folded_prose or not entry["quote"].strip():
            problems.append(f"ingredient {label!r}: the quote is not a verbatim piece of the guideline text: {entry['quote']!r}")
        if item["min_pct"] is not None and not entry.get("role"):
            problems.append(f"ingredient {label!r}: min_pct only goes with a role")
        kind = kinds[0]
        if kind == "role":
            item["role"] = entry["role"]
        elif kind == "ingredient":
            found = lookups["ingredients"].get(name_key(entry["ingredient"]), [])
            if len(found) == 1:
                item["ingredient"] = found[0]
            else:  # not in ref, or several producers: the reviewer picks
                item["ingredient"] = entry["ingredient"]
                item["unknown"].append(entry["ingredient"])
        else:
            tag = lookups["tags"].get(name_key(entry["tag"]))
            item["tag"] = tag or entry["tag"]
            if tag is None:
                item["unknown"].append(entry["tag"])
        draft["ingredients"].append(item)

    return draft, problems


def extract_style(lookups: dict, raw: dict) -> dict:
    """Ask, check, and on problems ask once more. The returned dict is one draft [[style]]."""
    prose = style_prose(raw)
    answer = ask(prose)
    draft, problems = check_answer(lookups, prose, answer)
    tries = 1
    if problems:
        answer = ask(prose, earlier=(answer, problems))
        draft, problems = check_answer(lookups, prose, answer)
        tries = 2
    draft["problems"] = problems
    draft["tries"] = tries
    return draft


# ---------------------------------------------------------------- writing the draft toml


def q(value) -> str:
    """A TOML basic string (JSON string escapes are valid TOML)."""
    return json.dumps(value, ensure_ascii=False)


def qlist(values) -> str:
    return "[" + ", ".join(q(v) for v in values) + "]"


HEADER = """\
# Style envelopes for the 26 s3 styles. A DRAFT written by `python -m loaders.style_envelopes
# --extract`: the D2 model read each style's guideline text, code checked the answer. Nothing here
# is in `ref` until you review a style and set `reviewed = true`, then run
# `python -m loaders.style_envelopes`.
#
# To review a style: read each [[style.sensory]] against the guideline text (the `quote` must say
# what min/max claim), fix min/max (scale: none, very low, low, medium-low, medium, medium-high,
# high, very high), fix `characters` (tag names), and replace every word under `unknown` by a
# tag name, an ingredient written "producer|name" ("|Flaked Rice" has no producer), or by adding
# a synonym to loaders/style_fit_vocab.toml. Empty `unknown` and `problems` first.
# An optional [[style.rule]] (ingredient "producer|name" or tag; level; usage; quote) loads into
# ref.style_rule.

"""


def draft_toml(styles: list[tuple[str, str, dict]], model: str, date: str) -> str:
    out = [HEADER]
    for code, name, d in styles:
        out.append("[[style]]")
        out.append(f"code = {q(code)}")
        out.append(f"name = {q(name)}")
        out.append("reviewed = false")
        out.append(f"extracted = {{ model = {q(model)}, date = {q(date)}, tries = {d['tries']} }}")
        out.append(f"problems = {qlist(d['problems'])}")
        out.append("")
        for s in d["sensory"]:
            out.append("[[style.sensory]]")
            out.append(f"dimension = {q(s['dimension'])}")
            out.append(f"min = {q(s['min'])}")
            out.append(f"max = {q(s['max'])}")
            out.append(f"characters = {qlist(s['characters'])}")
            out.append(f"unknown = {qlist(s['unknown'])}")
            out.append(f"quote = {q(s['quote'])}")
            out.append("")
        for i in d["ingredients"]:
            out.append("[[style.ingredient]]")
            for key in ("role", "ingredient", "tag"):
                if key in i:
                    out.append(f"{key} = {q(i[key])}")
            out.append(f"required = {'true' if i['required'] else 'false'}")
            if i["min_pct"] is not None:
                out.append(f"min_pct = {i['min_pct']}")
            out.append(f"unknown = {qlist(i['unknown'])}")
            out.append(f"quote = {q(i['quote'])}")
            out.append("")
    return "\n".join(out)


def extract(conn, out_path: Path, only: str | None) -> None:
    codes = [only] if only else S3_STYLES
    lookups = load_lookups(conn)
    date = datetime.date.today().isoformat()
    styles = []
    started = time.time()
    for code in codes:
        row = conn.execute("select name, raw from ref.beer_style where code = %s", (code,)).fetchone()
        if row is None:
            raise LookupError(f"no ref.beer_style row with code {code!r}")
        t = time.time()
        d = extract_style(lookups, row[1])
        styles.append((code, row[0], d))
        unknown = sum(len(s["unknown"]) for s in d["sensory"]) + sum(len(i["unknown"]) for i in d["ingredients"])
        print(f"{code:28} {time.time() - t:5.1f}s tries={d['tries']} sensory={len(d['sensory'])} "
              f"ingredients={len(d['ingredients'])} unknown={unknown} problems={len(d['problems'])}", flush=True)
        out_path.write_text(draft_toml(styles, MODEL, date), encoding="utf-8")  # keep what is done so far
    print(f"{len(styles)} styles in {time.time() - started:.0f}s -> {out_path}")


# ---------------------------------------------------------------- loading reviewed styles


def refuse_unfinished(style: dict) -> None:
    """A style marked reviewed must have nothing left to resolve."""
    left = list(style.get("problems", []))
    for part in ("sensory", "ingredient"):
        for item in style.get(part, []):
            left += [f"unknown {w!r}" for w in item.get("unknown", [])]
    if left:
        raise ValueError(f"style {style['code']} is marked reviewed but has open items: {left}")


def _ingredient_id(conn, spec: str) -> int:
    producer, _, name = spec.partition("|")
    row = conn.execute(
        "select id from ref.ingredient where producer_key = %s and name_key = %s",
        (name_key(producer), name_key(name)),
    ).fetchall()
    if len(row) != 1:
        raise LookupError(f"ingredient {spec!r}: {len(row)} matches (write it as 'producer|name')")
    return row[0][0]


def _tag_id(conn, facets: tuple, name: str) -> int:
    row = conn.execute("select id from ref.tag where facet = any(%s) and name = %s", (list(facets), name)).fetchone()
    if row is None:
        raise LookupError(f"no {'/'.join(facets)} tag {name!r}")
    return row[0]


def load_style(conn, style: dict) -> dict:
    """Replace one reviewed style's rows in ref. Returns row counts."""
    refuse_unfinished(style)
    row = conn.execute("select id from ref.beer_style where code = %s", (style["code"],)).fetchone()
    if row is None:
        raise LookupError(f"no ref.beer_style row with code {style['code']!r}")
    style_id = row[0]

    conn.execute("delete from ref.style_sensory where style_id = %s", (style_id,))  # cascades to style_character
    conn.execute("delete from ref.style_ingredient where style_id = %s", (style_id,))
    conn.execute("delete from ref.style_rule where style_id = %s", (style_id,))
    counts = {"sensory": 0, "character": 0, "ingredient": 0, "rule": 0}

    for s in style.get("sensory", []):
        conn.execute(
            "insert into ref.style_sensory (style_id, dimension, min_level, max_level, quote, reviewed) "
            "values (%s, %s, %s, %s, %s, true)",
            (style_id, s["dimension"], SCALE[s["min"]], SCALE[s["max"]], s["quote"]),
        )
        counts["sensory"] += 1
        for name in dict.fromkeys(s.get("characters", [])):
            conn.execute(
                "insert into ref.style_character (style_id, dimension, tag_id) values (%s, %s, %s)",
                (style_id, s["dimension"], _tag_id(conn, ("character",), name)),
            )
            counts["character"] += 1

    for i in style.get("ingredient", []):
        conn.execute(
            "insert into ref.style_ingredient (style_id, role, ingredient_id, tag_id, required, min_pct, quote, reviewed) "
            "values (%s, %s, %s, %s, %s, %s, %s, true)",
            (style_id, i.get("role"),
             _ingredient_id(conn, i["ingredient"]) if i.get("ingredient") else None,
             _tag_id(conn, ("origin", "family"), i["tag"]) if i.get("tag") else None,
             i.get("required", False), i.get("min_pct"), i["quote"]),
        )
        counts["ingredient"] += 1

    for r in style.get("rule", []):
        if r["level"] not in LEVELS:
            raise ValueError(f"style {style['code']} rule: level {r['level']!r} is not one of {LEVELS}")
        conn.execute(
            "insert into ref.style_rule (style_id, ingredient_id, tag_id, usage, level, max_pct, quote) "
            "values (%s, %s, %s, %s, %s, %s, %s)",
            (style_id,
             _ingredient_id(conn, r["ingredient"]) if r.get("ingredient") else None,
             _tag_id(conn, ("origin", "family", "character"), r["tag"]) if r.get("tag") else None,
             r.get("usage"), r["level"], r.get("max_pct"), r["quote"]),
        )
        counts["rule"] += 1
    return counts


def load(conn, path: Path) -> None:
    with open(path, "rb") as f:
        styles = tomllib.load(f)["style"]
    for style in styles:  # refuse before writing anything
        if style["reviewed"]:
            refuse_unfinished(style)
    totals = {"sensory": 0, "character": 0, "ingredient": 0, "rule": 0}
    loaded = 0
    for style in styles:
        if not style["reviewed"]:
            continue
        for key, n in load_style(conn, style).items():
            totals[key] += n
        loaded += 1
    print(f"loaded {loaded} reviewed styles, skipped {len(styles) - loaded} unreviewed: {totals}")


# ---------------------------------------------------------------- run


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("file", nargs="?", type=Path, default=DEFAULT_TOML, help="toml to load")
    parser.add_argument("--extract", metavar="OUT", type=Path, help="ask the LLM and write a draft toml")
    parser.add_argument("--style", help="with --extract: only this style code")
    args = parser.parse_args(argv)
    if args.style and not args.extract:
        parser.error("--style goes with --extract")
    with connect() as conn:  # commits on success, rolls back on error
        if args.extract:
            extract(conn, args.extract, args.style)
        else:
            load(conn, args.file)


if __name__ == "__main__":
    sys.exit(main())
