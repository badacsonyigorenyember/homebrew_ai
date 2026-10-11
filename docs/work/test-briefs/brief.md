# Recipe test briefs (P0)

Status: approved
Slug: test-briefs · Branch: test-briefs

## Why
Every later recipe phase is measured against a fixed set of test briefs (PROJECT.md §6.6;
RECIPE-ROADMAP P4: "≥ 18/20 briefs: right style, right deviations", P5: "≥ 16/20 validate · 0
invented ingredients"). The set does not exist yet, so no pipeline step can be shown to work, and
we cannot tell which ingredients the catalogue still lacks. The current catalogue has grain malts
only. The briefs need to ask for the mainstream adjunct fermentables, so the gap is visible and
gets tested.

## Goal
The repo holds 20 test briefs: natural-language recipe requests, each with the outcome a correct
pipeline must produce for steps 1–3 (style, deviations, what the user asked for). The user has
reviewed them. Together they cover a wide spread of styles, the style-guidance cases from
RECIPE-ROADMAP §4 and §7, and the six adjunct fermentables the user named.

## Scope
In:
- 20 briefs in one machine-readable file in the repo, with an automated check of its shape and
  coverage.
- For each brief: the expected best-fit style, the expected deviations, and the ingredients the
  recipe will need.
- PROJECT.md and RECIPE-ROADMAP status for P0, plus the two ingredient decisions below.

Out:
- Adding oats, candi sugar, corn, rice, lactose, honey or any other ingredient to `ref`, the gap
  report against `ref.ingredient`, the ingredient decisions and any schema change. All of that is
  the separate work item [`adjunct-fermentables`](../adjunct-fermentables/brief.md), which uses
  these briefs.
- Fruit, or any extra whose gravity can't be counted reliably. No brief asks for one (user
  decision, 2026-10-11).
- Extras that add no gravity (spices, herbs, coffee, vanilla, cacao, wood). No brief asks for
  one, so `ref.misc` stays out of the tests for now (user decision, 2026-10-11).
- Reusing the archived test cases (`scripts/stress/recipe_cases.jsonl`, tag
  `archive/pre-reset-2026-10-08`). All 20 briefs are written fresh (user decision, 2026-10-11).
- An eval runner script, step JSON contracts, and any n8n or pipeline work (D3 stays open).
- Deciding D7 (ratio source) and D9 (envelope approval). The P0 roadmap row lists them, but they
  belong to P3 and stay open.
- BA styles as the expected style (D1 leaning: BJCP primary; BA comes "Later").

## Requirements
R1. There are exactly 20 briefs, all written fresh. Each brief's request is in English, written
    the way a user would type it, one to three sentences.
R2. Each brief records: an id, the request text, a one-line *why* (what the brief tests), the
    expected best-fit style as a BJCP 2021 code, acceptable alternative codes only where the
    request is genuinely ambiguous, the expected deviations (each one names what deviates and
    from what), the numbers the user stated (batch L, ABV, OG, IBU, SRM), hint words, wanted
    ingredients, excluded ingredients, the user's stated inventory, guidance on/off, and the
    ingredients the recipe will need, as generic names (e.g. "flaked oats", not an id).
R3. The expected style is the **base style**: adjuncts and extras are ignored, unless the request
    makes an adjunct a stated, prominent feature. Then the specialty code (e.g. 31B Alternative
    Sugar Beer) is expected, with the base style as an accepted alternative. A specialty category
    is also used when no meaningful base style exists. Every expected code exists in
    `ref.beer_style` for source `bjcp-2021`.
R4. Style ranges are not copied into the file. Whatever reads the briefs gets them from
    `ref.beer_style`.
R5. Style spread: the 20 briefs span at least 8 different BJCP categories, with no more than 3
    stouts or porters. There are at least 3 lagers, 2 Belgian styles, 2 wheat or sour styles and
    3 hop-forward styles.
R6. Adjunct fermentables: each of flaked oats, candi sugar, corn, rice, lactose and honey is
    needed by at least one brief. Where possible this is in a style that traditionally uses it.
R7. Guidance cases (RECIPE-ROADMAP §4): at least 3 ingredient deviations, 2 number deviations
    (a user number outside the style range), 1 name-vs-numbers mismatch ("4 % imperial stout"
    style), 1 brief with guidance off, and 1 contradictory request whose correct outcome is to
    name the conflict (§6.3 "conflict" slot).
R8. Constraint cases: at least 2 briefs exclude ingredients ("I have no …"), and at least 2 state
    the user's inventory ("I have …").
R9. Every hint row in RECIPE-ROADMAP §7 (bitter, hoppy/juicy, dry/crisp, full/chewy, malty,
    darker, stronger/session) is used by at least one brief.
R10. At least 3 different batch sizes appear, and at least one is not 20 L.
R11. No brief asks for fruit or for an extra that adds no gravity (spice, herb, coffee, vanilla,
    cacao, wood). Every ingredient a brief wants or needs is a fermentable, hop, yeast or water
    salt.
R12. An automated test reads the file and checks R1–R3 and R5–R11. A count that misses its
    minimum fails the test.
R13. The P0 status is updated in PROJECT.md and in the RECIPE-ROADMAP §8 row, D7 and D9 are
    noted as moved to P3, and the briefs file is linked.

## Constraints
- Readable over optimal (PROJECT.md §6.8): a person can review a brief from the file alone. Any
  structure needs a reason.
- Measured, not hoped (CLAUDE.md): style codes are checked against the DB, not written from
  memory.
- PROJECT.md §2, §3 and §6 are not changed. The ingredient decision goes in the progress log and
  the open-decisions and status text.
- No git worktree. Plain branch `test-briefs` (CLAUDE.md).
- The DB is read-only for this work: only queries, no writes.

## Assumptions
- The user reviews each brief's expected style and deviations. Those are judgement calls, and the
  user's call wins. *(unverified)*
- hopline.hu or another source has data for the six adjuncts. This does not matter for this work,
  only for the next one. *(unverified)*

## Acceptance criteria
A1. The test (R12) passes and counts exactly 20 briefs, each with every R2 field present (empty
    is allowed for fields the request doesn't use) (R1, R2).
A2. A query returns a `bjcp-2021` row in `ref.beer_style` for every expected and alternative code
    in the file (R3).
A3. The test reports, and the minimums hold for: ≥ 8 BJCP categories, ≤ 3 stouts/porters, ≥ 3
    lagers, ≥ 2 Belgian, ≥ 2 wheat/sour, ≥ 3 hop-forward (R5); each of the six adjuncts ≥ 1
    (R6); ≥ 3 ingredient deviations, ≥ 2 number deviations, ≥ 1 mismatch, ≥ 1 guidance-off,
    ≥ 1 conflict (R7); ≥ 2 exclusions, ≥ 2 inventories (R8); every §7 hint row ≥ 1 (R9); ≥ 3
    batch sizes, one not 20 L (R10); 0 fruit and 0 non-gravity extras (R11).
A4. A search of the file for style range values (OG/IBU/SRM bands) finds none. Only numbers the
    user stated appear (R4).
A5. The user has read all 20 briefs and approved the expected style and deviations of each one
    (R2, R3).
A6. PROJECT.md has the dated §8 entry, the P0 status, a note on
    D7/D9 and the link to the file, and RECIPE-ROADMAP §8 shows P0 done (R13).
A7. `pytest` passes in full: the existing tests plus the new one.

## Open questions
None. Answered by the user on 2026-10-11: no non-gravity extras (R11), English only (R1), all
20 briefs written fresh (Scope).

## Deviations
- 2026-10-11 · Scope, R13, A6: the ingredient decisions moved to the separate work item
  `adjunct-fermentables` — the user asked for two work items: test briefs, and adding the
  remaining ingredients.
- 2026-10-11 · R3: a prominent, stated adjunct now means the specialty code is expected (base
  style as alternative); b12 becomes 31B with alt 18A — user review (A5): the assistant should
  tell a user that a honey-forward blonde is an alternative sugar beer, not a blonde ale.
