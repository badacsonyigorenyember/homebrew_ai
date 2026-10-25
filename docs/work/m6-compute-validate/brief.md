# M6 · Steps 10–11: calculate, validate and save (the MVP)

Status: approved
Slug: m6-compute-validate · Branch: m6-compute-validate
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) M6, checkpoint **G6** (MVP) ·
[RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §3 steps 10–11, §8 P5
Needs: `s1-maths` shipped ✅ 2026-10-14, `s2-formulation-rules` shipped ✅ 2026-10-15,
`m5-choose-ingredients` shipped ✅ 2026-10-23 (all in `docs/finished/`)

## Why
After stage C (steps 6–9, one LLM call) the recipe is a list of `ref` products with grist
percentages, hop shares and minutes, and misc doses in g/L. Stage D turns that into kilograms and
grams, computes what the beer will be, and checks it against the targets, the user's stated
numbers and s2's formulation rules before anyone sees it. This is where the pipeline first
produces a complete, numerically correct, style-checked recipe: the MVP (RECIPE-ROADMAP §8 P5).

## Goal
For every brief the pipeline computes amounts and OG/FG/ABV/IBU/SRM with s1's functions,
validates them, retries within limits, and saves the recipe as `app.recipe` rows. At least 16 of
b01–b20 validate, with 0 invented ingredients and at most 2 LLM calls per recipe plus tie-breaks,
and you would brew the 5 recipes you review.

## Scope
In:
- Step 10: amounts from the step 7–9 outputs, step 4's targets and step 0's profile, through s1's
  functions: grist kg from `app.solve_grist` (target OG, grist %, efficiency, volume), hop grams
  from `app.solve_hops` (target IBU, step 8's `solver` list, boil gravity from
  `app.preboil_volume`), misc grams as step 9's `dose_g_per_l` × batch L (never in OG/IBU/SRM).
  Then OG, FG, ABV, IBU and SRM with `app.og`, `app.fg`, `app.abv`, `app.ibu`, `app.srm`
  (via `app.grist_mcu`).
- The colour adjustment s2 left to this work (rule 7): when SRM misses its target, only the share
  of the darkest fermentable that is not a crystal malt changes. s1 has no colour solver
  (`pg_proc`: `solve_grist` and `solve_hops` only), so this work builds it as tested code.
- Step 11: validation with `app.check_recipe` (s2 rules 1–13) plus the checks in R3, and the retry
  loop of at most 3 tries (numbers off → step 10 again; a rule or pick failure → back to the
  steps 6–9 call with the rule, the value and the limit, PROJECT.md §3), with the reason for each
  retry.
- The formulation-check contract's extras (s9 Out): `formulation_check.input` takes the misc
  items, so b23 and b24 can be checked, and reference recipes for b23 and b24 join
  `tests/fixtures/reference_recipes.toml` (the RECIPE-ROADMAP §8 Later TODO).
- Saving `app.recipe`, `app.recipe_item` and `app.recipe_deviation` (user and model deviations),
  with `calc_version`, `batch_l` and `efficiency_pct` snapshots, `status = draft`, and
  `app.run.recipe_id` set.
- Tolerances for stated numbers and targets (WORKFLOW-ROADMAP §3), in the harness next to the
  G-M maths tolerances.
- 5–10 held-out briefs, drafted in this work from styles b01–b24 do not use, approved by you
  before G6 and scored only at checkpoints (WORKFLOW-ROADMAP §3).
- The G6 run and your review of 5 full recipes.

Out:
- Process (M7: water, mash schedule, boil, fermentation, packaging, pitch rate) and prose (M8).
- Editing a saved recipe. Versions (`parent_id`) beyond the field.
- Fruit as a fermentable (RECIPE-ROADMAP §8 Later TODO "decided with M6"): `ref.misc` has no fruit
  row (measured 2026-10-25: coffee 2, spice 1, vanilla 1) and no brief has fruit, so there is
  nothing to test. The TODO stays on the Later list.
- Whirlpool and dry-hop IBU above 0 (s1, Later list).
- A new LLM call, prompt or tie-break. The steps 6–9 prompt changes only if a retry needs the
  failed rule passed in.

## Requirements
R1. Step 10 computes every `recipe_item` amount (kg for fermentables, g for hops and misc) and
    keeps its `pct`, and computes OG, FG, ABV, IBU and SRM, only through s1's functions and
    tested SQL; no LLM. Where a `ref` value is a range (EBC, alpha, attenuation), the plan names
    which number step 10 takes (s1 leaves that choice to step 10).
R2. When the SRM result misses its target, step 10 changes only the share of the darkest
    non-crystal fermentable (rule 7), then recomputes; if that cannot reach the target within
    tolerance, step 11 reports it as a numbers failure.
R3. Step 11 passes a recipe only when all of these hold: `app.check_recipe` has no `fail`
    result; OG, ABV, IBU and SRM are within tolerance of step 4's targets (OG ± 0.002,
    ABV ± 0.2, IBU ± 2, SRM ± 1; FG is checked by rule 10); every stated number is met within the
    same tolerance and a stated batch size exactly; every item has a `ref` id; with guidance on,
    no item the pipeline picked on its own is rated `out_of_style` or `changes_style`; no
    excluded product (as `app.choose_excluded` reads them, LUPOMAX siblings included) is in the
    recipe.
R4. A numbers failure runs step 10 again; a rule or pick failure re-runs the steps 6–9 call with
    the failed rule, the value and the limit (and that pick banned). There are at most 3 tries in
    all; each try logs its step rows in `app.run_step` with its `try` number and, on a failed
    step 11, the reason in `error`.
R5. After 3 failed tries the run ends with `app.run.ok = false` and the list of what failed; no
    recipe is saved as valid.
R6. A validated recipe is saved as rows: `app.recipe` (`brief_id`, `style_id`, `targets`, `og`,
    `fg`, `abv`, `ibu`, `srm`, `batch_l`, `efficiency_pct`, `calc_version` from
    `app.calc_version()`, `status = draft`); one `app.recipe_item` per fermentable, hop, yeast and
    extra (`ingredient_id`, `raw_name`, `usage`, `time_min`, `pct`, `amount`, `unit`); one
    `app.recipe_deviation` per step 3 deviation (`requested_by = user`) and per model-made
    deviation (`requested_by = model`), with `subject`, `level` and `note`. `app.run.recipe_id`
    points to it.
R7. Every step 3 deviation is saved, including number, mismatch and conflict rows. Step 3 can give
    `level` null (mismatch, conflict) while `app.recipe_deviation.level` is not null with two
    values, so the plan fits them in with a `.sql` change; none is dropped.
R8. `formulation_check.input` accepts misc items, which do not enter OG/IBU/SRM; reference
    recipes for b23 and b24 pass `app.check_recipe` in `tests/test_reference_recipes.py`.
R9. The runner reports per brief: validated or not, tries used, LLM calls, stated numbers met;
    and totals. It reads the saved `app.recipe` rows, not the step output.
R10. The held-out briefs (5–10) are drafted in this work from styles b01–b24 do not use, follow
    the `evals/recipe_briefs.toml` format in a separate file, are approved by you, and are run
    only at checkpoints, never while building.

## Constraints
- CLAUDE.md: brewing maths is deterministic, tested code; never the LLM, never a skill.
  PROJECT.md §6.7: the LLM never computes a number. §6.6: every change measured on the fixed
  brief set. §6.8: readable over optimal.
- G0: deterministic logic is SQL in `db/*.sql`, called from n8n's Postgres node; Code nodes only
  reshape JSON. Table shapes per `db/015_app.sql`; changes as new `.sql` files applied with `psql`
  as `postgres` (OPERATIONS.md §4), never through the Supabase MCP.
- `app.recipe_item.usage` allows `mash`, `sparge`, `boil`, `whirlpool`, `ferment`, `dry_hop`,
  `secondary`, `package`; `ref.misc` usages use `packaging`, so the plan maps or widens one of
  them. Units are `g`, `kg`, `ml`, `l`, `pack`.
- `app.run_step` primary key is (`run_id`, `step`, `try`), `step` 0–16; `ok` is true exactly when
  `error` is null.
- Workflows with `onError` are imported with the n8n CLI (m3-deviations Task 5) and exported to
  `n8n/workflows/`.
- WORKFLOW-ROADMAP's earlier checkpoints scored b01–b20 and reported b21 onward alongside; G6
  does the same.

## Assumptions
- The tolerances above (your answer, 2026-10-25: "Brewer bar") apply to stated numbers and to
  targets alike. They are looser than s1's maths tolerances on purpose: a brewer would not notice
  the difference.
- LLM calls are counted as `evals/run.py` does: the sum of `run_step.llm.tries` over the run. A
  clean run has 2 (step 1, and the one steps 6–9 call). The "≤ 2 per recipe plus tie-breaks" bar
  is read as the calls on a run's first try; retries (the steps 6–9 contract retry, step 11's
  retries) are counted and reported per brief and in the totals, not hidden *(unverified: this
  reading of the P5/G6 bar is to be confirmed by you; G5 measured 55 calls in 24 runs, 7 runs
  with 3)*. No tie-break call exists (m5 removed the step 7 edge).
- No step before M7 sets a boil time (steps 0–5 have no boil field, measured). Step 10 uses the
  shortest boil rule 13 allows: 60 min, or the largest `min_boil_min` of the grist if longer;
  M7 replaces it *(unverified that this matches what M7 will choose)*.
- Pitch rate is M7 (s1 Out), so the yeast row's amount is a placeholder in `pack` that the plan
  states *(unverified)*.
- The test profile from m4 (20 L, 72 %, 4 L/h, 2 L, 1.0 L/kg) is used where a brief states no
  batch size.

## Acceptance criteria
A1. ≥ 16 of b01–b20 validate on the real pipeline; b21–b24 are run and reported alongside
    (R3, G6).
A2. 0 invented ingredients (every saved `recipe_item.ingredient_id` is a `ref` id); LLM calls per
    recipe counted from `run_step.llm.tries` and reported per brief and in total, ≤ 2 on the first
    try (R1, R9, G6).
A3. Every stated number is met within tolerance on the briefs that state one: ABV b01 6.5, b05 4,
    b14 3, b17 7, b21 4; IBU b08 50; SRM b18 20; batch exact b01 20 L, b08 10 L, b13 15 L,
    b15 23 L, b19 10 L (R3).
A4. A test with an impossible target (e.g. 1.040 OG at 10 % ABV) ends with `app.run.ok = false`
    after at most 3 tries, each try's reason in `run_step.error`, and saves no recipe (R4, R5).
A5. For one validated brief, recomputing OG, IBU and SRM from its saved `recipe_item` rows with
    s1's functions and the `ref` values step 10 used matches the saved results within s1's
    tolerances (R1, R6).
A6. A test recipe whose SRM misses its target changes only the darkest non-crystal fermentable's
    share, and a crystal malt's share stays unchanged (R2).
A7. b23's saved coffee and vanilla rows and b24's orange peel row have grams equal to the step 9
    dose × batch L (R1, R6).
A8. b05 (mismatch), b11 (conflict), b08 (number) and b16 (ingredient) have their step 3
    deviations as `app.recipe_deviation` rows with `requested_by = user` (R6, R7).
A9. `tests/test_reference_recipes.py` passes with reference recipes for b01–b24 (R8).
A10. The held-out file exists, its styles appear in no b01–b24 `style` or `alt_styles`, you
    approved it, and its score at G6 is recorded in PROJECT.md §8 (R10).
A11. You read 5 full recipes and your verdict is recorded in PROJECT.md §8 (G6 direction check).

## Open questions
None open. Your answers, 2026-10-25:
1. Tolerance for stated numbers: "Brewer bar" — ABV ± 0.2, IBU ± 2, SRM ± 1, OG ± 0.002, batch
   exact; the same tolerances apply to targets (R3, Assumptions).
2. Held-out briefs: "Drafted here" — drafted in this work from styles the test briefs do not use;
   you approve them (Scope, R10, A10).

## Deviations
