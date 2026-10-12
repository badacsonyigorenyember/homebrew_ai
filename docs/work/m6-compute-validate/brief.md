# M6 · Steps 10–11: calculate, validate and save (the MVP)

Status: draft
Slug: m6-compute-validate · Branch: m6-compute-validate
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) M6, checkpoint **G6** (MVP) ·
[RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §3 steps 10–11, §8 P5
Needs: `m5-choose-ingredients` and `s1-maths` shipped

## Why
After stage C the recipe is a list of products and percentages. Stage D turns it into kilograms
and grams, computes what the beer will be, and checks it against the targets and the style before
anyone sees it. This is where the pipeline first produces a complete, numerically correct,
style-checked recipe: the MVP (RECIPE-ROADMAP §8).

## Goal
For every brief the pipeline computes amounts and OG/FG/ABV/IBU/SRM, validates them, retries
within limits, and saves the recipe as rows. At least 16 of 20 briefs validate, with 0 invented
ingredients and at most 2 LLM calls per recipe plus tie-breaks, and you would brew the 5 recipes
you review.

## Scope
In:
- Step 10: amounts from blueprint %, targets and the profile through s1's solvers; computed OG,
  FG, ABV, IBU, SRM.
- Step 11: validation and the retry loop (numbers off → rescale in step 10; a bad pick → back to
  step 6, at most 3 times), with the reason for each retry.
- Saving `app.recipe`, `app.recipe_item`, `app.recipe_deviation` (user and model deviations), with
  `calc_version`, `batch_l` and `efficiency_pct` snapshots, `status = draft`.
- Tolerances for stated numbers (WORKFLOW-ROADMAP §3).
- 5–10 held-out briefs, written before G6 and scored only at checkpoints (WORKFLOW-ROADMAP §3).
- The G6 run and your review of 5 full recipes.

Out:
- Process (M7) and prose (M8). Editing a saved recipe. Versions (`parent_id`) beyond the field.

## Requirements
R1. Step 10 computes every `recipe_item` amount (kg, g) and its `pct`, and the five results, only
    through s1's functions; no LLM.
R2. Step 11 checks: results within the targets' tolerance; stated numbers met within the stated
    tolerance; every item a `ref` id; `max_pct` respected; with guidance on, no model-made ⚠️/⛔;
    excluded items absent.
R3. A numbers failure rescales (step 10 again); a pick failure returns to step 6 with that pick
    banned; at most 3 retries, each a `run_step` row with its `try` number and reason.
R4. After 3 failed tries the run ends with `ok = false` and the list of what failed; no recipe is
    saved as valid.
R5. A validated recipe is saved as rows: `recipe` (style, targets, results, snapshots,
    `calc_version`), `recipe_item` (ingredient, usage, time, pct, amount, unit), `recipe_deviation`
    (subject, level, requested_by, note), linked to `app.brief` and `app.run`.
R6. The runner reports per brief: validated or not, tries used, LLM calls, stated numbers met; and
    totals; it reads the saved rows, not the step output.
R7. The held-out briefs follow the `evals/recipe_briefs.toml` format in a separate file, are
    approved by you, and are not used while building.

## Constraints
- CLAUDE.md: maths is code. PROJECT.md §6.6: every change measured on the fixed brief set.
- `app` table shapes per `db/015_app.sql`; changes as `.sql` files applied as `postgres`.

## Assumptions
- Tolerances from s1's Open question 1 apply to targets as well *(to confirm in Open question 1)*.

## Acceptance criteria
A1. ≥ 16/20 briefs validate (R2, G6).
A2. 0 invented ingredients; ≤ 2 LLM calls per recipe plus tie-breaks, counted from `run_step`
    (R1, G6).
A3. b01 (6.5 %), b08 (50 IBU), b14 (3 %), b17 (7 %), b18 (20 SRM) meet their stated numbers within
    tolerance (R2).
A4. A test with an impossible target (e.g. 1.040 OG at 10 % ABV) ends with `ok = false` after at
    most 3 tries and the reasons, and saves nothing as valid (R3, R4).
A5. For one validated brief, recomputing OG/IBU from the saved rows with s1 matches the saved
    results (R5).
A6. The held-out file exists, is approved, and its score at G6 is recorded (R7).
A7. You read 5 full recipes and record your verdict in PROJECT.md §8 (G6 direction check).

## Open questions
1. Tolerance for stated numbers? — options: a) ABV ± 0.2, IBU ± 2, SRM ± 1, OG ± 0.002, batch
   exact; b) the s1 maths tolerances — recommend a: a brewer wouldn't notice those.
2. Who writes the held-out briefs? — options: a) drafted in this work from styles the 20 don't
   use, you approve; b) you write them — recommend a.

## Deviations
