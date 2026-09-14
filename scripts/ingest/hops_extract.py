#!/usr/bin/env python3
"""
hops_extract.py — the Hop Variety Handbook into ref.hops shape.

Book 7. 44 pages, 36 of them carrying exactly two spec cards, 72 hops total —
`measured` 2026-09-14, and the regularity is the reason this is an extraction
rather than a chunking job.

Layout per card: a left column with the hop name and a prose description, a right
column holding a 2-wide label/value grid of ten numeric specs, and a full-width
bottom row of three text fields.

  Origin              Total oils ml/100g       <- label line
    DE                    2,1 - 2,4            <- value line
  Hop type                Myrcene %
  Dual purpose            <47
  ...
  Beer types   Flavour and scent   Alternative hop

⛔ Two value traps, both measured, both silent if missed:

  381 decimal COMMAS — `8-14,5` is 8 to 14.5, not 8 to 145 and not 8 to 14 and 5.
   24 `<` BOUNDS     — `<47` is an open-ended UPPER bound: max 47, no minimum.
                       The mirror of BA 2026's `30+`, handled the same way — the
                       bound that exists is recorded and the one that does not
                       stays NULL rather than being invented as 0.

Usage:
  ./hops_extract.py --txt hops.layout.txt --out hops.json
  ./hops_extract.py --selftest
"""
import argparse, json, re, sys, unicodedata
from pathlib import Path

# Right-hand grid: (label, column prefix) in the order they appear, paired L/R.
SPEC_PAIRS = [
    ("Origin", "origin"),                    ("Total oils ml/100g", "total_oils"),
    ("Hop type", "hop_type"),                ("Myrcene %", "myrcene"),
    ("Alpha acid %", "alpha"),               ("Humulene %", "humulene"),
    ("Beta acid %", "beta"),                 ("Caryophyllene %", "caryophyllene"),
    ("Cohumulone %", "cohumulone"),          ("Farnesene %", "farnesene"),
]
LABELS = {l for l, _ in SPEC_PAIRS}
TEXT_ROW = ["Beer types", "Flavour and scent", "Alternative hop"]
NUMERIC = {"total_oils", "myrcene", "alpha", "humulene", "beta",
           "caryophyllene", "cohumulone", "farnesene"}
# ⛔ NOT a constant. The right-hand grid's left edge moves between pages — measured
# 2026-09-14 it ranges from column 57 to 68 — and a fixed split cuts THROUGH the
# word "Origin", which is how two hops ended up named "O". Each card derives its
# own split from where its own Origin label starts.
SPLIT_COL_FALLBACK = 58

# Ranges the source damaged beyond deterministic repair. Reported, never guessed.
UNRESOLVED = []


def clean(s):
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace("’", "'").replace("­", "")
    return re.sub(r"\s+", " ", s).strip()


def parse_range(raw):
    """'8-14,5' -> (8.0, 14.5) · '<47' -> (None, 47.0) · '68' -> (68.0, 68.0).

    ⛔ The comma is a DECIMAL point here, never a thousands separator and never a
    list separator — this handbook is European. Converting it before splitting on
    the dash is what keeps `14,5` from becoming two numbers.
    """
    if not raw:
        return (None, None)
    s = clean(raw).replace(",", ".")
    if not re.search(r"\d", s):
        return (None, None)

    if s.lstrip().startswith("<"):           # open-ended upper bound
        m = re.search(r"<\s*(\d+(?:\.\d+)?)", s)
        return (None, float(m.group(1))) if m else (None, None)
    if s.lstrip().startswith(">"):           # open-ended lower bound
        m = re.search(r">\s*(\d+(?:\.\d+)?)", s)
        return (float(m.group(1)), None) if m else (None, None)

    m = re.search(r"(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)", s)
    if m:
        return (float(m.group(1)), float(m.group(2)))
    m = re.search(r"(\d+(?:\.\d+)?)", s)     # a single value is its own range
    return (float(m.group(1)), float(m.group(1))) if m else (None, None)


def grid_left(lines):
    """Leftmost column at which ANY grid label starts, minus a margin.

    ⛔ Not the column of `Origin`: each label is centred within the right-hand
    column, so they start at different offsets — `Origin` at 64 while `Hop type`
    starts at 63. Splitting on Origin's column therefore slices the very next
    label in half and the field silently disappears. Take the minimum over all
    of them so the cut lands left of every label.
    """
    cols = [i for l in lines for lab in LABELS
            if (i := l.find(lab)) >= 0]
    return max(min(cols) - 2, 1) if cols else SPLIT_COL_FALLBACK


def split_cols(line, at):
    return line[:at], line[at:]


def two_cells(line):
    """Split a grid line into its left and right cell on a 2+ space run."""
    parts = [p for p in re.split(r"\s{2,}", line.strip()) if p]
    if len(parts) >= 2:
        return parts[0], parts[-1]
    return (parts[0], "") if parts else ("", "")


def parse_card(lines, split_at=None):
    """One card: the lines from its `Origin` label line to the next card's."""
    if split_at is None:
        split_at = (lines[0].index("Origin") if lines and "Origin" in lines[0]
                    else SPLIT_COL_FALLBACK)
    left = [split_cols(l, split_at)[0] for l in lines]
    right = [split_cols(l, split_at)[1] for l in lines]

    # --- right grid: a label line is followed by its value line ---------------
    spec = {}
    for i, r in enumerate(right):
        cells = [c for c in re.split(r"\s{2,}", r.strip()) if c]
        if not cells or not any(c in LABELS for c in cells):
            continue
        pair = [(l, k) for l, k in SPEC_PAIRS if l in cells]
        if not pair:
            continue
        # ⛔ Stop at the NEXT label. A label whose value is blank in the source —
        # Elixir has no Humulene and no Caryophyllene — would otherwise adopt the
        # value belonging to the row below it, which is how Mistral acquired a
        # humulene range of 9.5-1.8 from two different rows.
        for j in range(i + 1, len(right)):
            if any(lab in right[j] for lab in LABELS):
                break
            if not right[j].strip():
                continue
            lv, rv = two_cells(right[j])
            if len(pair) == 2:
                spec[pair[0][1]], spec[pair[1][1]] = lv, rv
            else:
                spec[pair[0][1]] = lv
            break

    # --- left column: the name is the first short line, then the prose --------
    name, desc = None, []
    for l in left:
        t = l.strip()
        if not t:
            continue
        if name is None:
            name = t
        else:
            desc.append(t)
    # the bottom text row bleeds into the left column; cut it at its label
    blob = " ".join(desc)
    for lab in TEXT_ROW:
        blob = blob.split(lab)[0]

    # --- bottom row: three cells, assigned by COLUMN RANGE ---------------------
    # ⛔ The three values do NOT share a line. "Alternative hop" wraps onto its own
    # line above or below the other two, so splitting one line into three cells
    # finds it on fewer than half the cards (measured: 31 of 72). Take the column
    # where each label starts, and slice every following line by those ranges.
    text = {}
    for i, l in enumerate(lines):
        if "Beer types" not in l:
            continue
        bounds = [l.find(lab) for lab in TEXT_ROW]
        if any(b < 0 for b in bounds):
            break
        # ⛔ Slicing at the midpoint between labels cuts mid-word: the VALUES are
        # wider than the labels above them, so "Wheat beer" became "Wh" + "eat
        # beer". Split each line into whole segments on a 3+ space run instead,
        # and give each segment to whichever column its START is nearest to.
        acc = ["", "", ""]
        for j in range(i + 1, len(lines)):
            if not lines[j].strip():
                continue
            for m in re.finditer(r"\S(?:.*?\S)?(?=\s{3,}|$)", lines[j]):
                seg = m.group(0).strip()
                if not seg:
                    continue
                k = min(range(3), key=lambda c: abs(m.start() - bounds[c]))
                acc[k] = (acc[k] + " " + seg).strip()
        text["beer_types"], text["flavour"], text["alternatives"] = acc
        break

    row = {"name": clean(name), "description": clean(blob) or None,
           "origin": clean(spec.get("origin")) or None,
           "hop_type": clean(spec.get("hop_type")) or None}
    for k in NUMERIC:
        lo, hi = parse_range(spec.get(k))
        # ⛔ An inverted range means the source lost a decimal comma — Krush's
        # total oils reads "05-3,0" where it should read "0,5-3,0". The plausible
        # value is obvious to a brewer and is STILL not recorded: inferring it is
        # the same move as inferring a fault's cause. NULL it and report it.
        if lo is not None and hi is not None and lo > hi:
            UNRESOLVED.append((clean(name) if (name := row.get("name")) else "?",
                               f"{k}={spec.get(k)!r}"))
            lo = hi = None
        row[f"{k}_min"], row[f"{k}_max"] = lo, hi
    for k in ("beer_types", "flavour", "alternatives"):
        v = clean(text.get(k))
        row[k] = [x.strip() for x in v.split(",") if x.strip()] if v else []
    return row


def extract(txt):
    hops = []
    for page in txt.split("\f"):
        lines = page.splitlines()
        starts = [i for i, l in enumerate(lines)
                  if "Origin" in l and "Total oils" in l]
        for n, s in enumerate(starts):
            end = starts[n + 1] if n + 1 < len(starts) else len(lines)
            card = parse_card(lines[s:end], grid_left(lines[s:end]))
            if card["name"]:
                hops.append(card)
    return hops


SELFTEST = [
    ("8-14,5", (8.0, 14.5)), ("2,1 - 2,4", (2.1, 2.4)), ("<47", (None, 47.0)),
    ("<5,4", (None, 5.4)),   ("6 - 11", (6.0, 11.0)),   ("6-7", (6.0, 7.0)),
    ("68", (68.0, 68.0)),    ("", (None, None)),        ("0,1 - 0,5", (0.1, 0.5)),
]


def selftest():
    bad = 0
    for raw, want in SELFTEST:
        got = parse_range(raw)
        if got != want:
            print(f"  FAIL {raw!r}: got {got}, want {want}"); bad += 1
    print("  selftest:", "FAILED" if bad else f"all {len(SELFTEST)} range forms parsed correctly")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--txt"); ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    hops = extract(Path(a.txt).read_text())
    Path(a.out).write_text(json.dumps(hops, indent=1, ensure_ascii=False))
    filled = lambda k: sum(1 for h in hops if h.get(k) not in (None, [], ""))
    if UNRESOLVED:
        print(f"  ⛔ {len(UNRESOLVED)} range(s) inverted in the SOURCE — nulled, not guessed:")
        for nm, d in UNRESOLVED:
            print(f"       {nm}: {d}")
    print(f"  {len(hops)} hops -> {a.out}")
    for k in ("origin", "hop_type", "description", "alpha_min", "total_oils_min",
              "myrcene_min", "beer_types", "flavour", "alternatives"):
        print(f"     {k:16} {filled(k):3}/{len(hops)}")
    dup = [h["name"] for h in hops if [x["name"] for x in hops].count(h["name"]) > 1]
    if dup:
        print(f"  ⛔ duplicate names: {sorted(set(dup))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
