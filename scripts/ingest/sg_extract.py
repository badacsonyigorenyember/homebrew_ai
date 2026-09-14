#!/usr/bin/env python3
"""
sg_extract.py — the BJCP Beer Style Study Guide, scoped to option B.

Book 5 path 2b. Plan 05 §2b, decided 2026-09-14: keep ONLY the fields whose
content is not already a populated `ref.styles` column.

  KEEP   History:     69 sections, 5,289 words — genuinely expanded narrative
         Techniques:  16 sections,   847 words — no ref.styles column exists
  DROP   Overall Impression:, Comments:, Ingredients:, Commercial Examples:
         and every sensory table

⛔ The drops are not a size judgement. `measured` 2026-09-14: ref.styles carries
overall_impression 116/116, comments 116/116, history 116/116,
characteristic_ingredients 116/116, commercial_examples 115/116 — and those rows
are already rendered into the 232 cards competing in every retrieval. The Study
Guide is a BJCP publication about BJCP 2021 styles, so four of its five labelled
fields restate rows the database already holds. That is D31's defect (b).

History survives the same test because it is NOT a restatement: for Doppelbock
the ref.styles row stops at "a 19th century court ruling", while the Guide gives
the etymology of Salvator, the brewery's secularisation, who coined "doppelbock"
and when, and the Christmas/Easter tradition.

Usage:
  ./sg_extract.py --md sg.md --out sg_passages.json
"""
import argparse, json, re, sys, unicodedata
from pathlib import Path

# Every labelled field seen in the Guide. The ones NOT in KEEP are what bound a
# kept field's text — they must all be listed or a kept passage runs on into the
# next field and silently re-imports what option B just dropped.
LABELS = ["Overall Impression:", "Aroma:", "Appearance:", "Flavor:", "Mouthfeel:",
          "History:", "Comments:", "Ingredients:", "Techniques:",
          "Commercial Examples:", "Style Comparison:", "Entry Instructions:",
          "Vital Statistics:"]
KEEP = {"History:": "History", "Techniques:": "Techniques"}
LABEL_RE = re.compile("(" + "|".join(re.escape(l) for l in LABELS) + ")")
HEAD_RE = re.compile(r"^##\s+\*?\s*([0-9]{1,2}[A-Z]?)\.\s*(.+?)\s*$")


def clean(s):
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace("­", "").replace("’", "'")
    s = re.sub(r"\|[^\n]*\|", " ", s)          # drop any table row that leaked in
    return re.sub(r"\s+", " ", s).strip()


def extract(md):
    out = []
    for block in re.split(r"(?=^##\s)", md, flags=re.M):
        head = HEAD_RE.match(block.splitlines()[0] if block.splitlines() else "")
        if not head:
            continue
        code, name = head.group(1), clean(head.group(2))

        # Only the prose lines; the sensory grids are markdown tables.
        prose = "\n".join(l for l in block.splitlines()[1:]
                          if not l.strip().startswith("|"))
        # ⛔ Normalise BEFORE splitting. The PDF is justified, and docling keeps
        # the padding — "Commercial  Examples:" carries a double space. An exact
        # label match silently misses it, and the field it was meant to bound
        # then runs on, re-importing the very text option B dropped. `measured`:
        # 3 passages leaked this way before this line existed.
        prose = re.sub(r"\s+", " ", prose)
        parts = LABEL_RE.split(prose)
        for i in range(1, len(parts), 2):
            label = parts[i]
            if label not in KEEP:
                continue
            body = clean(parts[i + 1])
            if len(body.split()) < 8:          # a stub is not a passage
                continue
            out.append({"code": code, "name": name, "field": KEEP[label], "text": body})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    passages = extract(Path(a.md).read_text())
    Path(a.out).write_text(json.dumps(passages, indent=1, ensure_ascii=False))

    by = {}
    for p in passages:
        by[p["field"]] = by.get(p["field"], 0) + 1
    words = sum(len(p["text"].split()) for p in passages)
    print(f"  {len(passages)} passages -> {a.out}")
    for k, v in sorted(by.items()):
        print(f"     {k:12} {v:4}")
    print(f"  {words:,} words kept  (~{round(words/180)}-{round(words/250)} chunks expected)")

    # The drop list is the point of this script, so prove it held.
    leaked = [p for p in passages
              if re.search(r"Commercial Examples:|Ingredients:|Overall Impression:", p["text"])]
    print(f"  ⛔ dropped-field leakage into kept text: {len(leaked)}")
    return 1 if leaked else 0


if __name__ == "__main__":
    sys.exit(main())
