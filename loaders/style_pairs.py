"""Propose which BA 2026 style is the same style as a BJCP 2021 style, for the user to review.

Step 2 returns the BJCP style when a BA style wins and a reviewed BJCP equivalent exists
(docs/work/m2-best-fit-style/plan.md). This script only proposes: it matches by name and writes
a markdown table with an empty `decision` column. The user fills it in; only reviewed rows go
into db/021_style_pairs.sql.

Run: python -m loaders.style_pairs --out docs/work/m2-best-fit-style/style-pairs.md
"""

import argparse
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

from loaders.db import connect

FILLER = {"style", "and", "or", "the", "of", "beer"}
SAME_WORD_RATIO = 0.85

REVIEW_NOTE = """\
# BA to BJCP style pairs: for your review

The script proposed a BJCP equivalent for each BA 2026 style by name. Fill the **decision**
column of every row you want paired:

- `keep`: the proposed BJCP style is the same style as the BA one
- a BJCP code (for example `5B`): that BJCP style is the match (also for a row with no proposal)
- `drop` or empty: no pair, the BA style stays a BA style

When step 2's best fit is a BA style that has a pair, step 2 returns the BJCP style instead.
Where several BJCP styles are proposed, write the one code you want.
"""


def name_words(name: str) -> list[str]:
    """Lower-case words of a style name: accents dropped, filler dropped, IPA spelled out."""
    decomposed = unicodedata.normalize("NFKD", name)
    plain = "".join(c for c in decomposed if not unicodedata.combining(c)).lower()
    words = []
    for word in re.sub(r"[^a-z]+", " ", plain).split():
        if word == "ipa":
            words += ["india", "pale", "ale"]
        elif word not in FILLER:
            words.append(word)
    return words


def same_word(a: str, b: str) -> bool:
    """Equal, or spelled nearly the same (koelsch / kolsch)."""
    return a == b or SequenceMatcher(None, a, b).ratio() >= SAME_WORD_RATIO


def count_matched(words: list[str], others: list[str]) -> int:
    """How many of `words` have a matching word in `others`."""
    return sum(any(same_word(w, o) for o in others) for w in words)


def propose(ba_rows: list[dict], bjcp_rows: list[dict]) -> list[dict]:
    """One proposal per BA row, sorted by BA name.

    Rows are dicts with code, name, abv. A BJCP style is proposed when all its words are in
    the BA name or all the BA name's words are in the BJCP name. Of those, the ones matching
    the most words are kept; ties are all listed.
    """
    proposals = []
    for ba in sorted(ba_rows, key=lambda r: r["name"]):
        ba_words = name_words(ba["name"])
        found = []
        for bjcp in bjcp_rows:
            bjcp_words = name_words(bjcp["name"])
            if not ba_words or not bjcp_words:
                continue
            bjcp_in_ba = count_matched(bjcp_words, ba_words) == len(bjcp_words)
            ba_in_bjcp = count_matched(ba_words, bjcp_words) == len(ba_words)
            if bjcp_in_ba and ba_in_bjcp:
                kind = "same words"
            elif bjcp_in_ba:
                kind = "BJCP name inside BA name"
            elif ba_in_bjcp:
                kind = "BA name inside BJCP name"
            else:
                continue
            found.append((min(len(ba_words), len(bjcp_words)), kind, bjcp))
        best = max((n for n, _, _ in found), default=0)
        top = [(kind, b) for n, kind, b in found if n == best]
        proposals.append({
            "ba": ba,
            "matches": [b for _, b in top],
            "match": top[0][0] if top else "",
        })
    return proposals


def read_styles() -> tuple[list[dict], list[dict]]:
    """(BA rows, BJCP rows) from ref.beer_style."""
    sql = """select code, name, coalesce(abv::text, '') from ref.beer_style
             where guide = %s order by code"""
    with connect() as conn:
        out = []
        for guide in ("BA", "BJCP"):
            rows = conn.execute(sql, (guide,)).fetchall()
            out.append([{"code": c, "name": n, "abv": a} for c, n, a in rows])
    return out[0], out[1]


def render(proposals: list[dict]) -> str:
    """The review file: how-to note, then one table row per BA style."""
    lines = [
        REVIEW_NOTE,
        "| BA code | BA name | proposed BJCP | match | ABV BA | ABV BJCP | decision |",
        "|---|---|---|---|---|---|---|",
    ]
    for p in proposals:
        ba = p["ba"]
        proposed = "<br>".join(f"{m['code']} {m['name']}" for m in p["matches"])
        abv_bjcp = "<br>".join(m["abv"] for m in p["matches"])
        lines.append(
            f"| `{ba['code']}` | {ba['name']} | {proposed} | {p['match']} "
            f"| {ba['abv']} | {abv_bjcp} |  |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    ba_rows, bjcp_rows = read_styles()
    proposals = propose(ba_rows, bjcp_rows)
    args.out.write_text(render(proposals), encoding="utf-8")
    paired = sum(1 for p in proposals if p["matches"])
    print(f"{len(proposals)} BA styles, {paired} with a proposed BJCP pair -> {args.out}")


if __name__ == "__main__":
    main()
