#!/usr/bin/env python3
"""
ba_extract.py — turn the BA 2026 Beer Style Guidelines into styles.json's shape.

Book 5, path 2a. Output is a flat JSON list using the SAME key names as
shared/rag-files/pending/styles.json, so `ingest-ba-styles` can reuse the BJCP
launcher's parse/upsert nodes unchanged.

⛔ Two traps live in the vitals line, and both silently produce plausible wrong
numbers rather than errors (plan 05 §2a):

  Alcohol by Weight (Volume) 3.8%-4.3% (4.8%-5.4%)
    BA leads with WEIGHT. BJCP records volume. Taking the first pair records
    every BA style ~20% weaker than it is. -> take the PARENTHESISED pair.

  Color SRM (EBC) 10-25 (20-50 EBC)
    Same shape, opposite answer: SRM is first, EBC is parenthesised.
    -> take the FIRST pair.

Gravity carries the same shape a third time — 1.048-1.056 (11.9-13.8 °Plato) —
and there the first pair is the one wanted, because °Plato is the parenthetical.

Usage:
  ./ba_extract.py --md ba.md --out ba_styles.json
  ./ba_extract.py --selftest
"""
import argparse, json, re, sys, unicodedata
from pathlib import Path

# The labelled fields of a BA entry, in the order they appear.
FIELDS = [
    ("Color:", "color"),
    ("Clarity:", "clarity"),
    ("Perceived Malt Aroma & Flavor:", "malt"),
    ("Perceived Hop Aroma & Flavor:", "hop"),
    ("Perceived bitterness:", "bitterness"),
    ("Fermentation Characteristics:", "fermentation"),
    ("Body:", "body"),
    ("Additional notes:", "notes"),
]
LABEL_RE = re.compile("(" + "|".join(re.escape(k) for k, _ in FIELDS) + ")", re.I)

# 214 ligature sites, measured. Normalised here rather than in the shared
# cleaning code: BA takes the structured path and never touches the prose
# engine, so this is local, not a change to every book's ingest (rule 2).
LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", "ﬆ": "st"}


def clean(s):
    if s is None:
        return None
    for k, v in LIGATURES.items():
        s = s.replace(k, v)
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("­", "").replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip() or None


# ---------------------------------------------------------------------------
# ⛔ The source PDF's text layer drops some range hyphens — `1.006-1.012` arrives
# as `1.0061.012`, `28-40` as `2840`. `measured` 2026-09-14: BOTH docling and
# pdftotext see the damage identically, so it is in the PDF, not the converter —
# the same class of defect as Draught's unmapped PUA glyphs, not a tool choice.
#
# BA prints most measures twice (SG and °Plato, weight and volume, SRM and EBC),
# and the rest are integers small enough that only one split is arithmetically
# possible. Repair what is determined; ⛔ FLAG the rest rather than guess.
# ---------------------------------------------------------------------------
PLAUSIBLE = {"ibu": (1, 150), "srm": (1, 100)}


def repair_welds(s):
    """Re-insert hyphens whose split point is unambiguous."""
    s = re.sub(r"1\.(\d{3})1\.(\d{3})", r"1.\1-1.\2", s)            # gravity
    s = re.sub(r"(\d+(?:\.\d+)?)%(\d+(?:\.\d+)?)%", r"\1%-\2%", s)  # percent boundary
    return s


def split_int_run(run, kind):
    """Split a welded integer run like '2840' into (28, 40).

    Returns None when the split is NOT unique — the caller must then treat the
    value as unknown. ⛔ Never fall back to a 'most likely' split: a silently
    wrong IBU is exactly the failure mode plan 05 §2a's A3/A4 exist to catch.
    """
    lo, hi = PLAUSIBLE[kind]
    ok = []
    for i in range(1, len(run)):
        a, b = run[:i], run[i:]
        if (a.startswith("0") and len(a) > 1) or (b.startswith("0") and len(b) > 1):
            continue
        ai, bi = int(a), int(b)
        if lo <= ai <= hi and lo <= bi <= hi and ai < bi:
            ok.append((ai, bi))
    return ok[0] if len(ok) == 1 else None


def _open_ended(text):
    """`30+` — BA's way of saying "this dark and darker". Not a damaged range:
    the minimum is real and the maximum genuinely does not exist, so the max
    stays NULL rather than being invented."""
    m = re.search(r"(\d+(?:\.\d+)?)\s*\+", text)
    return (float(m.group(1)), None) if m else None


def _pair(text):
    """First 'a-b' numeric range in text, as floats.

    ⚠️ Percent signs sit BETWEEN the number and the dash in BA's ABV field
    (`3.8%-4.3%`), so they are stripped first. Without that the range does not
    match at all and every BA style silently lands with a null ABV — a failure
    that looks like missing data rather than a parser bug.
    """
    text = text.replace("%", " ")
    m = re.search(r"(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)", text)
    return (float(m.group(1)), float(m.group(2))) if m else (None, None)


def parse_vitals(line):
    """Pull OG/FG/ABV/IBU/SRM out of a BA vitals line. See the module docstring."""
    out = dict.fromkeys(
        "ogmin ogmax fgmin fgmax abvmin abvmax ibumin ibumax srmmin srmmax".split())
    if not line:
        return out

    line = repair_welds(line)
    unresolved = []

    # Split on the bullet separator BA uses between measures.
    for seg in re.split(r"[•·]", line):
        s = seg.strip()
        low = s.lower()

        # BA writes "Varies with style" for anything base-style dependent — the
        # same case as BJCP's 20 specialty styles (README §5.4 finding 2). NULL
        # is the correct record; scraping a number out of the following text is
        # how a specialty style acquires a fictional SRM.
        if "varies" in low:
            continue

        if "original gravity" in low:
            # 1.048-1.056 (11.9-13.8 °Plato) -> FIRST pair; °Plato is parenthetical
            out["ogmin"], out["ogmax"] = _pair(re.sub(r"\([^)]*\)", "", s))
        elif "final gravity" in low or "apparent extract" in low:
            out["fgmin"], out["fgmax"] = _pair(re.sub(r"\([^)]*\)", "", s))
        elif "alcohol" in low:
            # ⛔ by WEIGHT first, by VOLUME parenthesised -> take the parenthesis
            paren = re.findall(r"\(([^)]*)\)", s)
            vol = next((p for p in paren if "%" in p or re.search(r"\d", p)), None)
            if vol:
                out["abvmin"], out["abvmax"] = _pair(vol)
            else:                      # single-value styles state ABV once only
                out["abvmin"], out["abvmax"] = _pair(s)
        elif "bitterness" in low or "ibu" in low:
            bare = re.sub(r"\([^)]*\)", "", s)
            out["ibumin"], out["ibumax"] = _pair(bare)
            if out["ibumin"] is None and (oe := _open_ended(bare)):
                out["ibumin"], out["ibumax"] = oe
            if out["ibumin"] is None:
                m = re.search(r"(\d{2,6})", bare)
                got = split_int_run(m.group(1), "ibu") if m else None
                if got: out["ibumin"], out["ibumax"] = got
                elif m: unresolved.append("ibu:" + m.group(1))
        elif "color" in low or "srm" in low:
            # ⛔ SRM first, EBC parenthesised -> strip the parenthesis
            bare = re.sub(r"\([^)]*\)", "", s)
            out["srmmin"], out["srmmax"] = _pair(bare)
            if out["srmmin"] is None and (oe := _open_ended(bare)):
                out["srmmin"], out["srmmax"] = oe
            if out["srmmin"] is None:
                m = re.search(r"(\d{2,6})", bare)
                got = split_int_run(m.group(1), "srm") if m else None
                if got: out["srmmin"], out["srmmax"] = got
                elif m: unresolved.append("srm:" + m.group(1))
    out["_unresolved"] = unresolved or None
    return out


def slug_code(name):
    """BA publishes no style codes, and (guide, guide_year, code) is the key, so
    the code must be derived from something stable. The name is the only stable
    thing BA gives; a reshuffling integer would orphan cards on re-import."""
    s = unicodedata.normalize("NFKD", clean(name) or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", s)).strip("-")[:80]


def split_entries(txt):
    """Yield (name, category, body) per style entry, from pdftotext output.

    ⛔ NOT from docling markdown, and the reason is measured (plan 05 §2a):
    docling's md export welds hyphenated numeric ranges together — `1.006-1.012`
    becomes `1.0061.012`, `28-40` becomes `2840` — on 295 of 699 measures, 42%.
    pdftotext loses none. The structure is regular either way, so the lossless
    one wins: every entry opens with a `Color:` line, its name is the line above,
    and BA's section headings are ALL CAPS.
    """
    lines = txt.splitlines()
    cat_re = re.compile(r"^[A-Z][A-Z &/'-]{6,}$")

    starts = []
    for ci in [i for i, l in enumerate(lines) if l.startswith("Color:")]:
        j = ci - 1
        while j >= 0 and not lines[j].strip():
            j -= 1
        starts.append((j, ci))

    for n, (ni, ci) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        category = next((lines[k].strip() for k in range(ni, -1, -1)
                         if cat_re.match(lines[k].strip())), None)
        yield lines[ni].strip(), category, "\n".join(lines[ci:end])


def extract(md):
    styles, seen = [], {}
    for name, category, body in split_entries(md):
        # &amp; survives some converters; normalise before matching labels.
        body = body.replace("&amp;", "&")
        fields, order = {}, LABEL_RE.split(body)
        for j in range(1, len(order), 2):
            key = next(v for k, v in FIELDS if k.lower() == order[j].lower().strip())
            fields[key] = clean(order[j + 1])

        # The vitals line wraps across several physical lines; clean() collapses
        # the whitespace, which re-joins it.
        vit = re.search(r"Original Gravity.*", body, re.S | re.I)
        vitals = parse_vitals(clean(vit.group(0)) if vit else "")
        unresolved = vitals.pop("_unresolved", None)

        code = slug_code(name)
        seen[code] = seen.get(code, 0) + 1
        if seen[code] > 1:                      # duplicate names must stay distinct
            code = f"{code}-{seen[code]}"

        aroma = " ".join(x for x in [fields.get("malt"), fields.get("hop")] if x)
        flavor = " ".join(x for x in [
            fields.get("malt"), fields.get("hop"),
            ("Perceived bitterness: " + fields["bitterness"]) if fields.get("bitterness") else None
        ] if x)
        appearance = " ".join(x for x in [fields.get("color"), fields.get("clarity")] if x)

        styles.append({
            "name": clean(name), "number": code,
            "category": clean(category), "categorynumber": None,
            "overallimpression": None,
            "aroma": aroma or None, "appearance": appearance or None,
            "flavor": flavor or None, "mouthfeel": fields.get("body"),
            "comments": fields.get("fermentation"),
            "history": None,
            "characteristicingredients": fields.get("notes"),
            "stylecomparison": None,
            "commercialexamples": [], "tags": [],
            **vitals,
        })
        if unresolved:
            UNRESOLVED.append((clean(name), unresolved))
    return styles


UNRESOLVED = []


SELFTEST = [
    ("Original Gravity (°Plato) 1.048-1.056 (11.9-13.8 °Plato) • Apparent Extract/Final "
     "Gravity (°Plato) 1.008-1.016 (2.1-4.1 °Plato) • Alcohol by Weight (Volume) "
     "3.8%-4.3% (4.8%-5.4%) • Hop Bitterness (IBU) 10-15 • Color SRM (EBC) 10-25 (20-50 EBC)",
     dict(ogmin=1.048, ogmax=1.056, fgmin=1.008, fgmax=1.016,
          abvmin=4.8, abvmax=5.4, ibumin=10, ibumax=15, srmmin=10, srmmax=25)),
]


def selftest():
    bad = 0
    for line, want in SELFTEST:
        got = parse_vitals(line)
        for k, v in want.items():
            if float(got[k]) != float(v):
                print(f"  FAIL {k}: got {got[k]}, want {v}"); bad += 1
    print("  selftest:", "FAILED" if bad else "all vitals parsed correctly")
    print("  slug_code('South German-Style Dunkel Weizen') ->", slug_code("South German-Style Dunkel Weizen"))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md"); ap.add_argument("--out"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    styles = extract(Path(a.md).read_text())
    if UNRESOLVED:
        print(f"  ⛔ {len(UNRESOLVED)} styles have a welded range that is NOT uniquely"
              " splittable — left NULL, not guessed:")
        for nm, u in UNRESOLVED:
            print(f"       {nm}: {', '.join(u)}")
    Path(a.out).write_text(json.dumps(styles, indent=1, ensure_ascii=False))
    withv = sum(1 for s in styles if s["ogmin"] is not None)
    print(f"  {len(styles)} styles -> {a.out}  ({withv} with vitals)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
