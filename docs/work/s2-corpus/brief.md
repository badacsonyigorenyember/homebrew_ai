# S2 · Recipe corpus and style profiles (P1b, D7)

Status: draft
Slug: s2-corpus · Branch: s2-corpus
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) side track P1b + P3, checkpoint **G-S**
(profile part) · [STYLE-PROFILES.md](../../STYLE-PROFILES.md) · [DATABASE.md](../../DATABASE.md)
§3, §7 row 4
Needs: `s1-maths` shipped (gate G4 recomputes OG and IBU)

## Why
Step 5 (blueprint) needs starting ratios per style: grist % per role, hop split by use, dosage,
yeast and ingredient popularity. Steps 6–9 rank candidates by what brewers of the style use, and
s3 calibrates its intensity cut points on the same data. None of it exists: the `corpus` tables
are empty, and D7 (PROJECT.md §7) is still open.

## Goal
The 35,620 archived Brewer's Friend recipes are in `corpus`, each flagged by gates G1–G7 with a
quality weight, mapped to roles and ingredients, and summarised into `style_profile` and its
three child tables for every style with data. D7 is decided with measured numbers.

## Scope
In:
- Loading `corpus.bf_recipes` and its `bf_fermentables`, `bf_hops`, `bf_yeasts`, `bf_miscs`
  from `~/homebrew-archive-2026-10-08/supabase-postgres.dump` into `corpus.recipe` and
  `corpus.recipe_item`, raw strings kept as written.
- `ref.fermentable.role` (base · kilned · crystal · roast · adjunct · sugar) from EBC and name
  keywords (STYLE-FIT.md §2), because the name map needs roles.
- `corpus.name_map`: raw names → a `ref` ingredient or a role, method `exact` · `rule` ·
  `reviewed`; unmapped stays unmapped.
- Gates G1–G7 as flags and a weight (STYLE-PROFILES.md §2), never deleting a recipe.
- The profile job: weighted median and IQR per role, hop use shares and g/L, top ingredients;
  family shrinkage for thin styles (k = 30); specialty styles from their base style.
- The spot check (30 kept + 30 dropped recipes, you mark each) and its precision.

Out:
- More sources (DIY Dog, books, views 100–500, own batches: STYLE-PROFILES.md §4). BA style
  families (DATABASE.md §9). Tags and envelopes (s3).

## Requirements
R1. A loader (re-runnable, same rows on a second run) fills `corpus.recipe` and
    `corpus.recipe_item` from the archive dump without restoring the old schema into the live DB.
R2. Every recipe gets `gates` flags G1–G7 and a quality weight; thresholds live in code next to
    their tests; no recipe is deleted.
R3. G4 recomputes OG and IBU with s1's functions and flags recipes off by more than a stated
    tolerance.
R4. `ref.fermentable.role` is set for all 81 fermentables by a tested rule (EBC + name keywords);
    any fermentable the rule can't place is listed for review, not guessed.
R5. `corpus.name_map` maps raw names to roles or `ref` ids; for the 22 brief styles (20 + 2
    alternates) at least 90 % of grist mass is mapped to a role (DATABASE.md §7 row 4).
R6. The profile job fills `style_profile`, `style_grist`, `style_hop_use` and
    `style_ingredient`, re-runnable, storing `n_recipes` and the family blend share.
R7. Thin styles blend with their family by n/(n + k), k = 30; styles with 0 recipes use the
    family; specialty styles (BJCP 28–34) use their base style.
R8. The spot check is run once, and the gate precision is recorded in PROJECT.md.
R9. D7 moves from PROJECT.md §7 to the relevant section with its *why*.

## Constraints
- Corpus data is never embedded into `kb` (DATABASE.md §3).
- DB changes as `.sql` files applied as `postgres`; loaders follow the `loaders/` pattern (tests,
  same rows on re-run).
- Source weights are a dict in code (DATABASE.md §8).
- Never restore the archive wholesale (PROJECT.md §9); read only what this work needs.

## Assumptions
- The archive tables keep 35,620 recipes, 34,052 mapped to a BJCP 2021 style (measured
  2026-10-08, STYLE-PROFILES.md §1) *(not re-measured)*.
- The dump's `corpus.bf_*` tables hold per-recipe ingredient rows (the table list shows
  `bf_fermentables`, `bf_hops`, `bf_yeasts`, `bf_miscs`; contents not checked).

## Acceptance criteria
A1. `corpus.recipe` holds 35,620 rows after two loads (R1).
A2. Gate counts per gate are printed and recorded; no row is missing after gating (R2, R3).
A3. Every `ref.fermentable` row has a role or is on the review list (R4).
A4. For each of the 22 brief styles, ≥ 90 % of weighted grist mass maps to a role (R5).
A5. 21A's profile matches its Beer Analytics page by hand: base %, top 3 hops, top yeast; 15B has
    roast in ≥ 90 % of weighted recipes (STYLE-PROFILES.md §5) (R6).
A6. A style with n < 50 shows a family blend share > 0 (R7).
A7. The spot-check precision is in PROJECT.md §8; D7 is no longer in §7 (R8, R9).

## Open questions
1. Read the dump how? — options: a) restore the needed `corpus.bf_*` tables into a scratch
   schema, copy, then drop the scratch schema; b) `pg_restore` to plain SQL/CSV files and load
   from files — recommend b: nothing from the old schema touches the live DB.
2. Who reviews unmapped names? — options: a) you review the top unmapped names by grist mass,
   until R5 passes; b) leave them unmapped — recommend a, capped at the names that block R5.

## Deviations
