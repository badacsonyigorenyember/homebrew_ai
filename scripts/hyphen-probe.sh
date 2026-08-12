#!/usr/bin/env bash
# =============================================================================
# hyphen-probe.sh — find numeric ranges that a PDF's line wrapping will destroy.
#
# WHY THIS EXISTS
# ---------------
# Every PDF text extractor joins wrapped lines and drops the trailing hyphen,
# because that hyphen is almost always a word split: "compa-\nnies" -> "companies".
# When the wrap lands inside a numeric range the same rule silently corrupts data:
#
#     ...boiled for 45-        ->   "boiled for 4590 minutes"
#     90 minutes to isomerize
#
# The result is not a parse error, it is a plausible wrong number. Docling and
# poppler both do it, no Docling option disables it (all 45 convert options were
# checked), and OCR does not help — the OCR pipeline joins lines the same way.
# So it has to be repaired downstream, per source, from `text_repairs`.
#
# This script finds the sites BEFORE ingest, using `pdftotext -layout`, which is
# the one extraction mode that preserves the physical line breaks and therefore
# still knows the hyphen was there.
#
# Usage:  ./scripts/hyphen-probe.sh shared/rag-files/pending/some-book.pdf
#
# Prints each at-risk site with context, then a draft `text_repairs` JSON array
# for the launcher (plans/phase3/00a-rebuild.md §2.2 node 1).
#
# ⛔ REVIEW THE OUTPUT — DO NOT PASTE IT BLIND. Table columns produce false
#    positives: in Yeast, "Total 2,3-" wraps next to a "900 ppb" cell and the
#    probe reports "2,3-900", which is two unrelated values, not a range.
#    Delete those lines from the array before using it.
# =============================================================================
set -euo pipefail

PDF="${1:-}"
[ -n "$PDF" ] && [ -f "$PDF" ] || { echo "usage: $0 <path-to.pdf>" >&2; exit 2; }

DIR=$(cd "$(dirname "$PDF")" && pwd)
BASE=$(basename "$PDF")

docker run --rm -v "$DIR:/w:ro" minidocks/poppler \
  pdftotext -layout "/w/$BASE" - 2>/dev/null |
python3 -c '
import json, re, sys

lines = sys.stdin.read().split("\n")
sites = []
for i in range(len(lines) - 1):
    left, right = lines[i].rstrip(), lines[i + 1].lstrip()
    m = re.search(r"(\S*?[\d.,]+)-$", left)
    if not (m and re.match(r"[\d.]", right)):
        continue
    head = m.group(1)                      # "45", "1.006", "$20"
    tail = right.split()[0]                # "90", "1.010", "50"
    sites.append({
        "line": i + 1,
        "context": (left[-46:], right[:38]),
        "find":    head + tail,            # what the extractor will produce
        "replace": head + "-" + tail,      # what the page actually says
    })

print(f"{len(sites)} at-risk site(s)\n")
for s in sites:
    print("  line %-7d ...%-46s | %s" % (s["line"], *s["context"]))

if not sites:
    print("\ntext_repairs: []")
    sys.exit(0)

# Collapse duplicates: the same fusion can occur on several pages, and one
# find/replace pair repairs all of them.
seen, pairs = set(), []
for s in sites:
    if s["find"] in seen:
        continue
    seen.add(s["find"])
    pairs.append([s["find"], s["replace"]])

print("\ndraft text_repairs (review, then paste into the launcher):\n")
print(json.dumps(pairs, ensure_ascii=False))
'
