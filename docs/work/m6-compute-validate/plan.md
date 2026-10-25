# M6 · Steps 10–11: calculate, validate and save (the MVP) — implementation plan

Stage: implementing
Brief: [brief.md](brief.md)
Branch: m6-compute-validate

## Approach

- **Step 10 is one SQL function, step 11 another, saving a third.** `app.step10_compute` (new
  `db/046_compute.sql`) turns the steps 6–9 outputs, step 4's targets and step 0's profile into
  amounts and numbers with s1's functions only, and builds the `formulation_check.input` object
  of the recipe. `app.step11_validate` (new `db/047_validate.sql`) runs `app.check_recipe` and
  `app.style_fit_recipe` on that object and checks targets, stated numbers, ids and exclusions
  (R3). `app.save_recipe` (new `db/048_save_recipe.sql`) writes the rows of a passed recipe in one
  transaction (R6, R7). No LLM in any of them (R1, CLAUDE.md).
- **Step 10 takes the same numbers `app.check_recipe` takes, so the check recomputes what step 10
  computed** (R1 "which number"): a fermentable's colour is `app.ebc_mid(ebc)` (middle of the
  range, one bound when open); a fermentable with no colour (Honey, Lactose, Enzyme Malt) counts
  as 0 EBC and is named in `srm_lower_bound`, as `app.style_fit_recipe` already does; a hop's
  alpha is the middle of its range (step 8's `solver.alpha_pct`); the attenuation is
  `app.mash_attenuation(yeast range, mash_c)` (rule 10's figure); extract is
  `extract_dbfg_pct`. OG, FG, ABV and SRM are at the batch volume; IBU at the batch volume with
  the boil gravity from `app.preboil_volume` and `app.boil_gravity(og, batch + losses, preboil)`,
  exactly as in `app.check_recipe`. The fermentation temperature is the `ferm_c` of step 6's
  chosen ferment choice, read from `app.ingredient_choices(yeast, null)` by its label (no text
  parsing); M7 replaces it.
- **Step 10's deterministic adjustments, in this order** (each reported in its output with a
  `because`): (1) boil time = the largest of 60, the grist's largest `min_boil_min` and the
  longest boil addition; the longest boil addition (the bittering one, rule 8) is set to the boil
  time (user decision 2026-10-25, "Set boil, fix hop"); (2) grist kg from `app.solve_grist`; (3) the colour adjustment (R2) when
  SRM misses its target by more than 1, `app.solve_colour` (below); (4) OG moved inside its
  ± 0.002 tolerance towards the ABV target when the ABV misses by more than 0.2 (user decision 2026-10-25, "OG nudge, then LLM");
  (5) hop grams from `app.solve_hops` at the final boil gravity; (6) misc grams = step 9's
  `dose_g_per_l` × batch L; (7) OG, FG, ABV, IBU, SRM with `app.og`, `app.fg`, `app.abv`,
  `app.ibu`, `app.srm(app.grist_mcu(...))`.
- **Colour adjustment (rule 7) is a closed-form solver, as `solve_grist`.** The darkest
  fermentable whose role is not crystal changes its share; the base malt with the largest share
  takes up the difference, so every other share, crystal included, stays exactly as proposed
  (A6; user decision 2026-10-25, "Largest base malt"). MCU is a ratio of two linear functions of that share, so the share solves
  one linear equation. The share must stay above 0 and at most its `max_pct`, and the base malt
  above 0 and at most its `max_pct`; when the darkest non-crystal is the base malt itself or no
  other base malt exists, nothing changes. If SRM is still more than 1 from the target, step 11
  reports a numbers failure (R2).
- **Retries (R4, R5; user decision 2026-10-25, "OG nudge, then LLM"):** every step 11 failure (numbers, rule or pick) goes back to the
  steps 6–9 call with its text (rule or number, value, limit), and a pick failure also bans that
  pick. Step 10 is not re-run on its own: its maths is closed form, so the same inputs give the
  same numbers, and its one rescale (the OG move) already ran inside it. At most 3 tries in all.
- **What counts as a pick failure.** With guidance on, a pick the pipeline made on its own (no
  `wanted`, no `inventory` on its step 6–9 pick) whose line in `app.style_fit_recipe` is
  `out_of_style` or `changes_style`; and any excluded product (`app.choose_excluded(frame)`,
  LUPOMAX siblings included). Lines are rated **without the recipe totals** (IBU, SRM): measured
  on the G5 picks, b08's hops are `out_of_style` only because of the user's own 50 IBU, and b03,
  b10, b15, b23's dark malts only because the SRM before the colour adjustment is too high. Those
  are numbers, checked against the targets; banning the pick would be wrong. So
  `app.style_fit_recipe` gains `totals boolean default true`, and step 11 passes false. Wanted
  and inventory picks are never banned (the brewer's choice wins).
- **n8n: the three tries are written out.** A new sub-workflow `Steps 10–11 · compute and
  validate` (contract checks around the two SQL calls, like `Step 4 · targets`), and a new
  `Steps 6–11 · one try` that calls `Steps 6–9 · choose ingredients` and `Steps 10–11`, and logs
  rows 6–11 of that try. The pipeline calls it as `Try 1`, `Try 2`, `Try 3` with an If between
  them, then `Save recipe` and `Finish run`. No loop-back edge: a reader sees the three tries, and
  `$('Node')` references never cross a loop.
- **Retry input to steps 6–9:** `choose.input` gains `feedback` (null on try 1). The sub-workflow
  moves banned ids out of the table into its `excluded` list (`app.choose_ban`), so the existing
  prompt and check refuse them, and appends the failure lines and the failed recipe's picks to the
  prompt (`app.choose_feedback_prompt`). No other prompt change.
- **LLM calls (A2, user decision 2026-10-25 "First try ≤ 2"):** `calls` = the sum of
  `run_step.llm.tries` over every row of the run (all tries); `first_try_calls` = the LLM steps
  on try 1, each counted once (step 1 and the steps 6–9 call: 2); `retry_calls` = `calls −
  first_try_calls` (contract retries and tries 2–3). The bar is `first_try_calls ≤ 2`; the other
  two are reported per brief and in the totals.
- **Tolerances live in two places checked against each other:** `app.recipe_tolerances()` in
  `db/047` (OG 0.002, ABV 0.2, IBU 2, SRM 1, batch 0) for step 11, and `evals/grade.py`
  `RECIPE_TOLERANCES` next to the maths tolerances for the harness; a test asserts they are equal
  (user decision "Brewer bar", 2026-10-25).

**Measured while planning (2026-10-25, read-only; scratch script, nothing written):** the 24 G5
picks (`evals/results/2026-10-19-m5.json`, b14 run 4246) put through `app.check_recipe` and
`app.style_fit_recipe` the way step 10 will (boil 60 or the largest `min_boil_min`, hop grams from
`app.solve_hops`, no colour adjustment, no OG move):
- rule 8 fails on 8 briefs (b06, b08, b09, b11, b13, b14, b17, b22): the grist needs a 90 min
  boil (Pilsner malts, `min_boil_min` 90) and the LLM's bittering hop is at 60 min (hence step
  10's boil and bittering rule);
- SRM misses its target by more than 1 on 15 briefs, and is null on 4 (b04, b12, b19, b20:
  Honey or Lactose has no colour, hence the 0-EBC lower bound);
- ABV misses by more than 0.2 on 9 briefs, by 0.21–0.49 (b02, b08, b09, b10, b12, b16, b18, b23,
  b24): the yeast's mash-adjusted attenuation differs from the one step 4's FG target assumes. An
  OG move of ± 0.002 shifts ABV by about 0.2, so it would bring about 6 of the 9 inside (estimate,
  unverified; hence step 10's OG move);
- other rule failures: rule 3 b03, b19, b23; rule 4 b19, b22; rule 10 b12, b22; rule 11 b19;
- with totals left in, self-picked lines `out_of_style`: b03 (3), b08 (2, the user's IBU), b10,
  b15, b18 (guidance off), b19 (2), b23 (3); `too_little` hop aroma or flavour on b01, b07, b08,
  b17, b23 (reported, not a failure: R3 does not list it).
So stage D will fail many first tries; the retries carry the work, and the G6 count is unknown
until the run.
Also measured: `app.recipe`, `recipe_item`, `recipe_deviation` 0 rows; `recipe_deviation.level`
check allows only `out_of_style`, `changes_style`; `recipe_item.usage` has no `packaging`
(`ref.misc` Coffee, cold brew has `{packaging}`); `app` has 129 functions; `app.calc_version()` =
`maths-1`; the 25 styles with reviewed envelopes are all used by b01–b24 (`style` or
`alt_styles`), so every held-out style is unrated (accepted by the user, 2026-10-25). The brief's A4 example "1.040 OG at
10 % ABV" raises in step 4 (`fg_for_abv: ABV 10 cannot be reached at OG 1.040`), so it never
reaches step 11; "OG 1.080 at 2 % ABV" passes step 4 (FG 1.0638) and no recipe can meet it (the
lowest yeast attenuation middle is 67.5 %), so A4's test uses that one. In
`tests/test_pipeline.py` the `post` fixture deletes runs and briefs; `app.recipe` references
`app.brief` without cascade, so the fixture must delete recipes first.
**Context7 not used:** no library question in this plan; n8n behaviour comes from the repo's
existing workflows and OPERATIONS §5.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `db/045_recipe_deviation_kind.sql` | new | `app.recipe_deviation.kind`, `level` nullable (R7) |
| `db/032_formulation_check.sql` | changed | `check_recipe_items` resolves `extras` (ref.misc); numbers unchanged (R8) |
| `db/034_style_level.sql` | changed | `app.style_fit_recipe(recipe, extras, totals)`; extras default to `recipe.extras` |
| `db/046_compute.sql` | new | `app.solve_colour`, `app.step10_boil`, `app.step10_compute` |
| `db/047_validate.sql` | new | `app.recipe_tolerances`, `app.step11_validate` |
| `db/048_save_recipe.sql` | new | `app.save_recipe` |
| `db/042_choose_table.sql` | changed | `app.choose_ban`, `app.choose_feedback_prompt` |
| `shared/contracts/formulation_check.input.schema.json` | changed | optional `extras` |
| `shared/contracts/choose.input.schema.json` | changed | `feedback` (null or object) |
| `shared/contracts/step10.{input,output}.schema.json`, `step11.{input,output}.schema.json` | new | logged step rows |
| `shared/contracts/try.input.schema.json`, `try.output.schema.json` | new | `Steps 6–11 · one try` |
| `n8n/workflows/steps-10-11-compute-validate.json` | new | sub-workflow `Steps 10–11 · compute and validate` |
| `n8n/workflows/steps-6-11-one-try.json` | new | sub-workflow `Steps 6–11 · one try` |
| `n8n/workflows/steps-6-9-choose-ingredients.json` | changed | ban and feedback on a retry |
| `n8n/workflows/recipe-pipeline.json` | changed | three tries, save, finish |
| `tests/fixtures/reference_recipes.toml` | changed | b23, b24 with `extra` (R8, A9) |
| `evals/heldout_briefs.toml` | new | 5–10 held-out briefs (R10) |
| `evals/run.py`, `evals/grade.py` | changed | recipe columns, tolerances, calls, `--briefs` (R9) |
| `evals/show_recipe.py` | new | prints a saved recipe for your review (A11) |
| `evals/results/<date>-m6.json`, `<date>-m6-heldout.json` | new | G6 results |
| `tests/test_recipe_tables.py`, `test_compute.py`, `test_validate.py`, `test_save_recipe.py` | new | Tasks 1, 3–6 |
| `tests/step1011_sample.json`, `tests/step611_sample.json` | new | Test data notes of the new sub-workflows |
| `tests/test_formulation_check.py`, `test_reference_recipes.py`, `test_style_fit_recipe.py`, `test_choose_table.py`, `test_contracts.py`, `test_workflows.py`, `test_pipeline.py`, `test_grade.py`, `test_run.py`, `test_recipe_briefs.py`, `tests/step69_sample.json` | changed | as each task says |
| `docs/RECIPE-ROADMAP.md`, `docs/WORKFLOW-ROADMAP.md`, `docs/DATABASE.md`, `docs/OPERATIONS.md` | changed | Task 11 |
| `PROJECT.md` | changed | §4 rows, §8 per task |

Apply command for every SQL file (OPERATIONS §4), run twice to show it is idempotent, then check
owners with `select proname, pg_get_userbyid(proowner) from pg_proc where pronamespace =
'app'::regnamespace and proname = any(<names>)` (all `postgres`):
`docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/<file>.sql`
Each new SQL file gets the header the others have (purpose, work folder, needs, apply command,
idempotent). Workflows are imported with the n8n CLI (OPERATIONS §5: edit the JSON, copy to
`shared/`, `import:workflow`, publish through the MCP, delete the copy), sub-workflows published
before the pipeline, then `.venv/bin/python -m evals.workflows`.

## Tasks

### Task 1: every step 3 deviation fits `app.recipe_deviation`
Why: R7 (null levels for number, mismatch and conflict rows), A8.
- [x] `db/045_recipe_deviation_kind.sql` (needs 015): `add column if not exists kind text`;
      backfill none needed (0 rows, measured); `alter column kind set not null`; check
      `recipe_deviation_kind_check` `kind in ('ingredient', 'number', 'mismatch', 'conflict')`;
      `alter column level drop not null`; check `recipe_deviation_level_kind_check`
      `(kind = 'ingredient') = (level is not null)` (an ingredient deviation has a level, the
      others have none, as step 3 gives them). Drop-and-add each constraint so a re-run works.
- [x] Apply twice; `\d app.recipe_deviation` shows `kind` not null and `level` nullable.
- [x] Write `tests/test_recipe_tables.py` (stack, every insert rolled back):
      `test_deviation_takes_every_step3_kind` (one row per kind as step 3 gives it, from
      `app.step3_deviations` of b05, b08, b11, b16 via `tests.test_step4` helpers: inserts pass),
      `test_ingredient_deviation_needs_a_level` (kind ingredient, level null: refused),
      `test_number_deviation_has_no_level` (kind number with a level: refused). See them fail
      before the file is applied.
- [x] `docs/DATABASE.md` `app.recipe_deviation` row. PROJECT.md §8 entry.
Done when: the three tests pass and the file applies twice.
Commit: `Let recipe deviations keep step 3 kinds`

### Task 2: the formulation check takes extras; b23 and b24 get reference recipes
Why: R8, A9 (RECIPE-ROADMAP §8 Later TODO).
- [x] `shared/contracts/formulation_check.input.schema.json`: optional `extras` array, items
      `{ingredient_id integer, usage enum mash|boil|whirlpool|ferment|secondary|packaging,
      g number ≥ 0, purpose string}`, all required, `additionalProperties: false`. Not in the
      top-level `required`, so every existing input stays valid.
- [x] `db/032_formulation_check.sql` `app.check_recipe_items`: each extra must be a `ref.misc`
      row (else raise `check_recipe: ingredient % is not a misc item`) and its usage one of the
      row's `usages` (else raise); returned as `extras [{ingredient_id, name, usage, g,
      purpose, category}]`. `app.check_recipe` does not read them: OG, FG, ABV, IBU and SRM are
      unchanged (comment says so).
- [x] `db/034_style_level.sql` `app.style_fit_recipe(recipe jsonb, extras jsonb default null,
      totals boolean default true)`: extras null → `recipe -> 'extras'` (or `[]`); `totals` false
      leaves `ibu`, `srm` and `srm_lower_bound` out of every line's dose (the comment says why:
      step 11 rates a pick on its own use, the totals are checked against the targets). Drop the
      two-argument version first (CREATE OR REPLACE cannot add a defaulted argument cleanly).
- [x] Apply 032 and 034 twice; owners `postgres`.
- [x] `tests/fixtures/reference_recipes.toml`: `[[recipe]]` b23 (20B base with Coffee, whole
      beans and Vanilla bean, as `extra = [{name, usage, g, purpose}]`, g = the step 9 dose ×
      20 L: coffee 3.0 g/L → 60 g, vanilla 0.05 g/L → 1 g) and b24 (18B with Orange peel,
      whirlpool, 2.64 g/L × 20 L = 52.8 g). Targets from `app.step4_numbers` as the header says;
      only `ref` ingredients. Header gains the `extra` field.
- [x] `tests/test_reference_recipes.py`: `build_input` adds `extras` (misc ids by name);
      `test_every_brief_has_exactly_one_recipe` expects all 24.
- [x] Write `tests/test_formulation_check.py::test_extras_do_not_enter_the_numbers` (a recipe
      with and without b23's two extras: same `numbers`), `test_extra_must_be_misc` (a hop id
      as extra raises), `test_extra_usage_must_be_its_rows` (coffee at `boil` raises);
      `tests/test_style_fit_recipe.py::test_extras_read_from_recipe` (no second argument: misc
      lines present) and `test_totals_off_rates_picks_on_their_own` (b08's reference recipe at
      50 IBU: Magnum `out_of_style` with totals, not with `totals => false`). See each fail first.
- [x] Run `.venv/bin/pytest tests/test_formulation_check.py tests/test_reference_recipes.py tests/test_style_fit_recipe.py tests/test_misc.py tests/test_contracts.py`, expect all pass.
- [x] PROJECT.md §8 entry. b23 and b24 recipes are shown to you at the Task 9 gate.
Done when: 24 reference recipes pass `app.check_recipe` (A9).
Commit: `Check extras and add b23 and b24 references`

### Task 3: the colour adjustment (rule 7) as tested code
Why: R2, A6. s1 has no colour solver (`pg_proc`: `solve_grist`, `solve_hops` only).
- [x] `db/046_compute.sql` (needs 030, 032): `app.solve_colour(target_srm numeric, grist jsonb,
      target_og numeric, efficiency_pct numeric, volume_l numeric) returns jsonb`. Grist items
      `{ingredient_id, name, role, pct, extract_pct, mashed, ebc, max_pct}` (`ebc` null counts as
      0). Returns `{grist, adjusted, reached, srm, darkest, absorber, from_pct, to_pct,
      because}`. Darkest = the highest `ebc` among roles other than `crystal` (ties: larger share,
      then lower id); absorber = the `base` fermentable with the largest share other than the
      darkest. Nothing changes (`adjusted` false) when the SRM at the proposed shares is within 1
      of the target, when there is no absorber, or when the darkest is not darker than the
      absorber. Otherwise solve the darkest's share in closed form (comment derives it from
      `app.grist_mcu` and `app.solve_grist`: MCU = K·N(x)/D(x), both linear in x), clamp to
      (0, `max_pct`] and keep the absorber in (0, its `max_pct`], recompute SRM with
      `app.srm(app.grist_mcu(app.solve_grist(...)))`; `reached` = within 1. `because` names the two
      fermentables and the shares, or why nothing changed.
- [x] Apply twice; owner `postgres`.
- [x] Write `tests/test_compute.py` (stack), each seen failing first:
      `test_colour_moves_only_darkest_and_base` (A6: b15's G5 grist, Maris Otter 88, Crystal
      T50 10, Black Malt 2, target 12: only Black Malt and Maris Otter change, Crystal T50 stays
      10, shares sum 100, SRM within 0.01 of 12); `test_colour_never_moves_crystal` (a grist whose
      darkest is a crystal: the darkest non-crystal moves); `test_colour_reports_unreachable` (b18's
      grist with Roasted Barley at its `max_pct` 2 and target 20: `reached` false, share stays 2);
      `test_colour_needs_a_base` (b01's grist, darkest non-crystal is the base: `adjusted` false
      with the reason); `test_colour_within_tolerance_is_left_alone`;
      `test_colour_matches_s1` (the returned SRM equals `app.srm(app.grist_mcu(...))` of the
      returned grist solved with `app.solve_grist`).
- [x] PROJECT.md §8 entry.
Done when: the colour tests pass.
Commit: `Add the rule 7 colour solver`

### Task 4: step 10 computes amounts and numbers
Why: R1, R2, A5 (SQL half), A7; brief assumptions on boil time and yeast amount.
- [x] `db/046_compute.sql`:
      - `app.step10_boil(grist_ids bigint[], hops jsonb) returns jsonb` → `{boil_min, because}`:
        the largest of 60 (rule 13's floor), the grist's largest `min_boil_min` and the longest
        boil addition's minutes.
      - `app.step10_compute(profile jsonb, targets jsonb, step6 jsonb, step7 jsonb, step8 jsonb,
        step9 jsonb, brief jsonb) returns jsonb` (`targets` is step 4's output). In order: batch =
        `targets.batch_l.value`, efficiency, boil-off and losses from the profile; boil from
        `app.step10_boil`, and the longest boil addition set to it; grist items from step 7
        with `ref.fermentable` facts (`extract_dbfg_pct`, `app.ebc_mid(ebc)`, role, `max_pct`,
        fermentability, mashed = role ≠ `sugar`, as `check_recipe_items`); `app.solve_colour`
        at the target OG; the OG move: when `app.abv(og, fg)` at the target OG misses the
        ABV target by more than 0.2, bisect OG in [target − 0.002, target + 0.002] for the ABV
        target (ABV rises with OG at fixed shares; 40 halvings), else keep the target; grist kg
        from `app.solve_grist` at that OG; hop grams from `app.solve_hops(ibu target, step 8
        solver with the bittering minutes, boil gravity, batch)`; misc g = `dose_g_per_l` ×
        batch (a null dose raises `step 10: no dose for <name>`); yeast rows: step 6's main
        yeast and souring culture (if any) each `1 pack` (placeholder until M7 sets the pitch
        rate); `ferm_c` from `app.ingredient_choices(main yeast, null)` where `label` = step 6's
        `choice`. Numbers: `app.og`, `app.fg` at `app.mash_attenuation`, `app.abv`, `app.ibu`,
        `app.srm(app.grist_mcu(...))` with no-colour items at 0 EBC.
        Output: `{batch {volume_l, efficiency_pct, boil_off_l_h, losses_l}, boil, mash_c,
        ferm_c, og_used {value, moved, because}, colour (solve_colour's result), fermentables
        [{ingredient_id, name, usage, pct, kg, purpose}], hops [{ingredient_id, name, usage,
        minutes, share_pct, alpha_pct, g, purpose}], yeasts [{ingredient_id, name, role
        main|souring, amount 1, unit pack, purpose}], extras [{ingredient_id, name, usage
        (`packaging` saved as `package`), time_min, dose_g_per_l, g, purpose}], numbers {og, fg,
        abv, ibu, srm, attenuation_pct, srm_lower_bound [names]}, values_used [{what, because}]
        (one line each for colour, alpha, attenuation, ferm_c, boil, yeast amount), recipe}`,
        where `recipe` is the `formulation_check.input` object (style code, guidance, stated
        without `batch_l`, hints, targets as numbers, batch, mash, boil, fermentables, hops with
        g, yeast with `ferm_c`, extras with g) that step 11 checks. Stated numbers and hints come
        from step 1's brief, which `step10.input` carries; the function takes it as a seventh
        argument `brief jsonb`.
- [x] Contracts `step10.input` = `{run_id, try, brief, profile, targets, step6, step7, step8,
      step9}`, `step10.output` as above (all required, `additionalProperties: false`, nulls where
      the text above allows them). `tests/test_contracts.py` `NAMES` gains both.
- [x] Apply twice; owners `postgres`.
- [x] Write in `tests/test_compute.py` (stack; inputs: step 4 via `tests.test_step4.step4`,
      profile `app.step0_profile(null)`, steps 6–9 from `good_proposal` through
      `app.choose_outputs` as `tests/test_choose_outputs.py` does), each seen failing first:
      `test_amounts_hit_the_targets` (b01, b08, b10, b14, b16, b23, b24: OG within 0.002 of the
      target, IBU within 0.01 of it, kg and g positive, pct equal step 7's except the two colour
      shares); `test_numbers_are_what_check_recipe_computes` (A5 SQL half: `app.check_recipe` of
      `output.recipe` gives the same OG, FG, ABV, IBU and, where every fermentable has a colour,
      SRM within 1e-9); `test_misc_grams_are_dose_times_batch` (A7: b23 coffee 3.0 × 20 = 60 g and
      vanilla 1 g, b24 orange peel 52.8 g; none in OG/IBU/SRM: removing extras changes no number);
      `test_values_used_named` (R1: every range pick has its line); `test_boil_covers_grist_and_hops`
      (b08: Pilsner Malt → 90, bittering hop at 90; b01 60); `test_og_moves_only_inside_tolerance`
      (a grist with a high-attenuation yeast: OG within 0.002 and ABV nearer the target than at
      the target OG; a case that is in tolerance at the target OG keeps it); `test_lower_bound_named`
      (b04-style grist with Lactose: `srm_lower_bound` = ["Lactose"]); `test_ferm_c_from_choice`
      (b01 US-05 at "ferment at 18 °C" → 18); `test_output_meets_contract`;
      `test_same_input_same_output`.
- [x] Run `.venv/bin/pytest tests/test_compute.py tests/test_contracts.py tests/test_maths.py`, expect all pass.
- [x] `docs/DATABASE.md` §5: the functions of `db/046`. PROJECT.md §8.
Done when: step 10 outputs meet their contract and `app.check_recipe` recomputes their numbers.
Commit: `Compute amounts and numbers in step 10`

### Task 5: step 11 validates and says what to retry
Why: R3, R4 (the failure kinds and the ban), A4 (SQL half).
- [x] `db/047_validate.sql` (needs 046, 042, 034, 032):
      - `app.recipe_tolerances() returns jsonb` immutable: `{"og": 0.002, "abv": 0.2, "ibu": 2,
        "srm": 1, "batch_l": 0}`, comment: user decision "Brewer bar" 2026-10-25, for targets and
        stated numbers alike; `evals/grade.py` `RECIPE_TOLERANCES` must equal it.
      - `app.step11_validate(step10 jsonb, brief jsonb, targets jsonb, frame jsonb, picks jsonb)
        returns jsonb`. `picks` = every step 6–9 pick `{ingredient_id, name, self_picked}`
        (`self_picked` = no `wanted` and no `inventory`). Runs `app.check_recipe(step10.recipe)`
        and `app.style_fit_recipe(step10.recipe, null, false)`. Failures, each `{kind, subject,
        value, limit, text, ban}`:
        `numbers`: OG, ABV, IBU, SRM against step 4's targets with `app.recipe_tolerances()`
        (a null number fails: "cannot be computed: <missing>"); every stated `og`, `abv`, `ibu`,
        `srm` against the computed number; stated `batch_l` equal to `step10.batch.volume_l`; the
        SRM text adds the colour adjustment's `because` when it did not reach the target.
        `rule`: every `check_recipe` result with status `fail`, its failures' texts (they name
        the rule, items, value and limit).
        `pick`: with `targets.guidance` true, every self-picked line `out_of_style` or
        `changes_style` (`ban` = its id); every recipe id in `app.choose_excluded(frame)`
        (`ban` = its id); every item without a `ref` id. Wanted and inventory picks never get a
        `ban`.
        Output: `{passed, failures, banned [{ingredient_id, name, why}], feedback [text],
        check (check_recipe's output), style_fit (style_fit_recipe's output, `too_little` and
        `required` kept for the record only), targets [{key, target, value, tolerance, met}],
        stated [{key, stated, value, tolerance, met}], model_deviations [{subject, level, note}]}`.
        `model_deviations`: self-picked lines `out_of_style` or `changes_style` when guidance is
        off (R6; with guidance on such a line fails instead). `feedback`: one plain line per
        failure, ending with "(banned for the next try)" on a ban.
- [x] Contracts `step11.input` = `{run_id, try, brief, targets, frame, picks, step10}`,
      `step11.output` as above. `NAMES` gains both.
- [x] Apply twice; owners `postgres`.
- [x] Write `tests/test_validate.py` (stack, inputs as Task 4), each seen failing first:
      `test_good_recipe_passes` (b16 from its good proposal, after step 10: passed, no failures);
      `test_target_miss_is_a_numbers_failure` (SRM target moved 3 away: one `numbers` failure,
      value and limit set, no ban); `test_stated_numbers` (b01 ABV 6.5 met; b08 IBU 50 met;
      a stated batch 23 with `volume_l` 20 fails); `test_rule_failure_names_rule_value_limit`
      (a grist with 20 % roast: rule 3 failure text, no ban); `test_self_pick_out_of_style_is_banned`
      (an out-of-style self-picked hop in b08: `pick`, ban its id); `test_wanted_pick_is_never_banned`
      (b23's coffee rated out of style: no ban); `test_user_ibu_does_not_ban_hops` (b08 at its
      stated 50 IBU: no pick failure); `test_excluded_product_fails` (b16 with Citra LUPOMAX forced
      in: `pick`, ban); `test_impossible_target_cannot_pass` (A4 SQL half: "OG 1.080 at 2 % ABV"
      through steps 2–5 and a good proposal: failures include ABV and rule 10, for any yeast in the
      table: loop over every yeast row, none passes); `test_guidance_off_gives_model_deviations`
      (b18: self-picked out-of-style lines become `model_deviations`, not failures);
      `test_output_meets_contract`.
- [x] Run `.venv/bin/pytest tests/test_validate.py tests/test_compute.py tests/test_contracts.py`, expect all pass.
- [x] `docs/DATABASE.md` §5. PROJECT.md §8.
Done when: each failure kind has a test and the impossible target never passes.
Commit: `Validate recipes in step 11`

### Task 6: a validated recipe is saved as rows
Why: R6, R7, A5, A8 (SQL halves).
- [ ] `db/048_save_recipe.sql` (needs 045, 047): `app.save_recipe(run_id bigint, step3 jsonb,
      targets jsonb, step10 jsonb, step11 jsonb) returns bigint`. Raises unless `step11.passed`
      is true (R5) and unless the run has a `brief_id`. Inserts `app.recipe` (`brief_id` from
      `app.run`, `style_id` from `ref.beer_style` by `targets.style.code`, `status` draft,
      `targets` = step 4's output, `og`, `fg`, `abv`, `ibu`, `srm` from `step10.numbers`,
      `batch_l` and `efficiency_pct` from `step10.batch`, `calc_version` = `app.calc_version()`);
      one `app.recipe_item` per fermentable (`kg`, `pct`, usage, `time_min` null), hop (`g`,
      `pct` = share, minutes), yeast (`1 pack`, usage `ferment`), extra (`g`, usage, `time_min`),
      each with `ingredient_id` and `raw_name` = the ref name; one `app.recipe_deviation` per step
      3 deviation (`kind`, `subject`, `level`, `requested_by` user, `note` = `because`) and per
      `step11.model_deviations` row (`kind` ingredient, `requested_by` model); then `update app.run
      set recipe_id`. Returns the recipe id. One function, so a failure saves nothing.
- [ ] Apply twice; owner `postgres`.
- [ ] Write `tests/test_save_recipe.py` (stack; a throwaway `app.run` and `app.brief`, rolled
      back), each seen failing first: `test_rows_match_step10` (b23: item count = fermentables +
      hops + yeasts + extras, amounts equal step 10's at the column scale, units kg/g/pack, coffee
      60 g, A7); `test_recompute_from_saved_rows` (A5: OG, IBU, SRM recomputed from the saved
      `recipe_item` rows with `app.og`, `app.ibu`, `app.srm(app.grist_mcu())` and the same `ref`
      values equal the saved numbers within OG 0.001, IBU 1, SRM 1 — the helper lives in
      `tests/test_save_recipe.py` and is reused by `tests/test_pipeline.py`);
      `test_every_step3_deviation_saved` (A8: b05 mismatch, b11 conflict, b08 number with level
      null, b16 ingredient with its level, all `requested_by` user); `test_model_deviation_saved`;
      `test_refuses_a_failed_validation`; `test_run_points_to_recipe`; `test_snapshot_fields`
      (`calc_version` `maths-1`, batch, efficiency, `targets` = step 4's output).
- [ ] Run `.venv/bin/pytest tests/test_save_recipe.py tests/test_recipe_tables.py`, expect all pass.
- [ ] `docs/DATABASE.md` §5. PROJECT.md §8.
Done when: a passed recipe saves completely, and a failed one saves nothing.
Commit: `Save validated recipes`

### Task 7: steps 6–9 take the retry feedback
Why: R4 (rule, value, limit, banned pick back to the one LLM call).
- [ ] `shared/contracts/choose.input.schema.json`: `feedback` required, `null` or `{try integer
      2–3, lines [string], banned [{ingredient_id, name, why}], last {fermentables, hops, yeast,
      extras} (the failed try's picks: names, pct, share, usage, minutes)}`.
      `tests/step69_sample.json` gains `"feedback": null`.
- [ ] `db/042_choose_table.sql`: `app.choose_ban(tbl jsonb, feedback jsonb) returns jsonb`: null
      feedback returns `tbl`; else removes every banned id from `fermentables`, `hops`, `yeasts`,
      `misc` and from `slots[].ids` and `inventory_words[].ids`, and appends to `excluded`
      `{ingredient_id, name, word: name, why: "failed step 11 on try <n>: <why>"}`, so the
      existing check refuses a banned id with its message. `app.choose_feedback_prompt(feedback
      jsonb) returns text`: empty for null; else a block "Try <n>: the last recipe failed step
      11. Fix these and change as little else as you can:" with the lines, then the last picks,
      then the banned names.
- [ ] Apply twice; owners `postgres`.
- [ ] `n8n/workflows/steps-6-9-choose-ingredients.json`: `Build table` selects
      `app.choose_ban(app.choose_table(...), $5)` and appends `app.choose_feedback_prompt($5)` to
      the prompt; nothing else changes. Import, publish.
- [ ] Write in `tests/test_choose_table.py`, each seen failing first: `test_ban_removes_and_excludes`
      (b01 with Caramel 50 banned: no row, listed in `excluded` with the why; `app.choose_check`
      of a proposal using it gives the excluded message); `test_no_feedback_same_table` (null →
      identical table and prompt); `test_feedback_prompt_lines` (every line and banned name
      appears; every number in the block is a number in the feedback).
- [ ] Measure (A2 prompt budget): b18's table with a three-line feedback through Ollama once,
      as `evals/fit_test.py` counts it (`prompt_eval_count + 4096 ≤ 32768`); write the tokens in
      the §8 entry. If it does not fit, stop and hand back `needs-input`.
- [ ] Run `.venv/bin/pytest tests/test_choose_table.py tests/test_choose_check.py tests/test_choose_outputs.py tests/test_contracts.py tests/test_workflows.py`, expect all pass.
- [ ] PROJECT.md §8.
Done when: a retry's table refuses the banned picks and its prompt carries the failures.
Commit: `Pass step 11 failures back to steps 6-9`

### Task 8: the pipeline runs up to three tries and saves the recipe
Why: R4, R5, R6, A4, A5.
- [ ] Sub-workflow `Steps 10–11 · compute and validate` (id `ST1011compval01`), JSON from
      `n8n/workflows/step-4-targets.json`'s pattern: trigger with the `step10.input` fields →
      `Check contract` (`step10.input`) → Postgres `select app.step10_compute($1, $2, $3, $4, $5,
      $6, $7)` → `Check contract` (`step10.output`) → build `step11.input` → check → Postgres
      `app.step11_validate` → check (`step11.output`) → return `{step10, step11}`. A raise stops
      the sub-workflow with its message (`step 10: …`). Sticky note and `Test data`
      (`tests/step1011_sample.json`: b01's inputs from Task 4's helpers, `run_id` 0, try 1).
- [ ] Sub-workflow `Steps 6–11 · one try` (id `ST611onetry0001`), input `try.input` = `{run_id,
      try, choose (the choose.input object, feedback included), brief, step3, targets, frame,
      profile, started_at}`: `Steps 6–9 · choose ingredients` (continueErrorOutput) → four log rows
      as the pipeline's today, with `try` = the input's (moved from the pipeline) → build
      `step10.input` → `Steps 10–11 · compute and validate` (continueErrorOutput) → `Step 10 · log`
      (ok) → `Step 11 · log`: ok when `step11.passed`, else ok false with `error` = `step 11 (try
      <n>): ` + the feedback lines joined by `; ` (R4) → return `try.output` = `{passed, try,
      step10, step11, next_feedback}` (`next_feedback` built from `step11` for the next try, null
      when passed). Error branches: the steps 6–9 failure row as today (lowest `step N:`), or a
      step 10 failure row, each with this `try`, then `Stop and Error` with the message.
      `Test data` note `tests/step611_sample.json`.
- [ ] `Recipe pipeline`: `Step 5 · log ok` → `Try 1 · input` (builds `try.input`, feedback null)
      → `Try 1 · steps 6–11` (continueErrorOutput) → `Try 1 passed?` → yes: `Save recipe`
      (Postgres `select app.save_recipe($1, $2, $3, $4, $5)`) → `Finish run` → `Respond ok`
      (`{run_id, ok, recipe_id, tries}`); no: `Try 2 · input` (feedback = try 1's
      `next_feedback`) → `Try 2 · steps 6–11` → `Try 2 passed?` → … → `Try 3 passed?` no →
      `Finish run (failed, 3 tries)` (ok false) → `Respond failed (3 tries)` (`{run_id, ok: false,
      failed_step: 11, tries: 3, error: "try 1: …; try 2: …; try 3: …"}`, R5). Each try's error
      branch → the existing steps 6–9 failure finish and respond (failed_step from the message).
      Remove the old step 6–9 log nodes from the pipeline. Update the per-step sticky note (steps
      0–11 built).
- [ ] Contracts `try.input`, `try.output`; `NAMES` gains both. Import the three new or changed
      sub-workflows, publish them, then the pipeline; delete the copies in `shared/`;
      `.venv/bin/python -m evals.workflows`.
- [ ] `tests/test_workflows.py`: `SAMPLES` and `CONTRACT_OF` for the two new files.
      `tests/test_pipeline.py`: the `post` fixture deletes the runs' recipes before runs and
      briefs (select `recipe_id`, delete runs, delete recipes, delete briefs) and its timeout is
      2400 s; `test_b01_validates_and_saves` (one run: `ok`, a `recipe_id`, step 10 and 11 rows
      for the last try ok and valid against their contracts, `test_recompute_from_saved_rows`'s
      helper passes on its rows, A5); `test_impossible_target_fails_after_three_tries` (A4:
      "A blonde ale at OG 1.080 and only 2 % ABV, 20 litres.": `app.run.ok` false, step 11 rows
      for tries 1–3 each ok false with `error`, no `app.recipe` row for the brief, `recipe_id`
      null); `test_steps_6_to_9_logged` keeps passing (try 1 rows). Time the file.
- [ ] Run `.venv/bin/pytest tests/test_workflows.py tests/test_pipeline.py`, expect all pass.
- [ ] `docs/OPERATIONS.md` §5: eleven workflows, the two new ones, the response fields
      (`recipe_id`, `tries`), the three tries. PROJECT.md §4 Orchestration row and §8.
Done when: a webhook run of b01 saves a recipe, and the impossible brief ends failed after three
tries with each reason logged.
Commit: `Run steps 10-11 with retries in the pipeline`

### Task 9: the harness reports recipes; held-out briefs (gate)
Why: R9, R10, A2, A3, A10, A11.
- [ ] `evals/grade.py`: `RECIPE_TOLERANCES = {"og": 0.002, "abv": 0.2, "ibu": 2, "srm": 1,
      "batch_l": 0}` next to the maths tolerances, with the user decision as comment;
      `grade_recipe(brief, recipe)` (pure Python): `validated` (a recipe row exists), `invented`
      (items with `ingredient_id` null), `stated` per stated number `{stated, value, met}` with
      `batch_l` exact, `stated_ok`.
- [ ] `evals/run.py`: `read_run` sums `llm.tries` over **every** row (all tries, failed rows
      too) into `calls`, counts `first_try_calls` (try-1 rows with an `llm`, each once) and
      `retry_calls`, and reads `tries` (largest step 11 `try`); `read_recipe(conn, run_id)` reads
      `app.run.recipe_id`'s `app.recipe`, its items and deviations (R9: from the saved rows, not
      the step output); the table gains `valid`, `tries`, `calls (first+retry)`, `stated`
      columns; totals gain `validated` (b01–b20 and all), `invented`, `stated_met`, `calls`,
      `first_try_calls` max, `retry_calls`. `--briefs PATH` (default `evals/recipe_briefs.toml`).
      `passed` stays as today and also needs `validated`.
- [ ] `evals/show_recipe.py` (`python -m evals.show_recipe <run_id>`): prints a saved recipe as
      plain text (style, batch, numbers vs targets, fermentables kg and %, hops g, minutes and
      usage, yeast, extras g, deviations, each pick's `because` from the step 6–9 rows), for
      A11. Reads only.
- [ ] `evals/heldout_briefs.toml`: draft 6 briefs `h01`–`h06` in the `recipe_briefs.toml`
      format, from styles that no b01–b24 `style` or `alt_styles` uses, spread over families
      (e.g. a Czech lager, a Scottish ale, a Belgian blond, a porter, a Kölsch-type, an English
      barleywine; final picks by the drafting), at least two with stated numbers and one with a
      stated batch size; header: "scored only at checkpoints, never while building; the needs
      words are not graded (the class map covers b01–b24)". These styles have no reviewed
      envelope, so their level checks are off (user decision 2026-10-25, "Accept").
- [ ] `tests/test_recipe_briefs.py`: `test_heldout_briefs_have_every_field` (same field check),
      `test_heldout_styles_unused` (A10), `test_heldout_style_codes_exist`; the runner's needs
      grade is skipped for a file other than `recipe_briefs.toml`.
- [ ] Tests in `tests/test_grade.py` and `tests/test_run.py` (no stack), each seen failing when
      broken: `grade_recipe` met / missed / batch exact / invented; `calls` over three tries;
      `first_try_calls` 2 with a step 6 contract retry on try 1; `test_harness_tolerances_match_sql`
      (stack: equals `app.recipe_tolerances()`).
- [ ] Run `.venv/bin/pytest tests/test_grade.py tests/test_run.py tests/test_recipe_briefs.py`, expect all pass.
- [ ] **Gate:** hand back `needs-input` with `evals/heldout_briefs.toml` and the b23 and b24
      reference recipes (Task 2) for your approval (R10, A10). Record your answer in the §8 entry;
      apply changes you ask for before Task 10.
Done when: the runner reports recipes from the saved rows and you approved the held-out briefs.
Commit: `Report recipes in the harness and add held-out briefs`

### Task 10: G6 on the real pipeline (gate)
Why: G6; A1–A3, A7, A8, A10, A11.
- [ ] `.venv/bin/python -m evals.run --save --label m6` (b01–b24; background, wait on the results
      file, not the process). A miss is fixed in its task's code and the run repeated; record
      each miss and its fix. The prompt is not tuned on these briefs beyond Task 7's block.
- [ ] Measure for the §8 entry: validated b01–b20 (bar ≥ 16) and b21–b24; tries per brief;
      calls, first-try calls (≤ 2 each) and retry calls per brief and in total; invented 0 (A2);
      each A3 stated number with its value; A7 grams of b23 and b24 from the saved rows; A8
      deviations of b05, b11, b08, b16 from `app.recipe_deviation`; A5 recompute on one validated
      brief; colour adjustments and OG moves made; run time per brief.
- [ ] Then once: `.venv/bin/python -m evals.run --briefs evals/heldout_briefs.toml --save --label m6-heldout`;
      record its validated count and calls (A10). Nothing is changed because of it.
- [ ] **Gate (A11):** hand back `needs-input` with 5 validated recipes printed by
      `evals.show_recipe` (proposal: b01, b03, b08, b10, b23 — IPA, stout, lager with a stated
      IBU, inventory dubbel, coffee extras), asking: would you brew them? Record your verdict.
- [ ] `docs/WORKFLOW-ROADMAP.md` G6 `Measured:` line (Decided left for you).
Done when: both results files are saved and the gate is answered.
Commit: `Measure G6 on 24 briefs and the held-out set`

### Task 11: the docs describe stage D as built
Why: scope (PROJECT.md is the entry point).
- [ ] `docs/RECIPE-ROADMAP.md` §3: rows 10 and 11 say what is built (value picks, the boil and
      bittering rule, colour solver, OG move, misc grams, the failure kinds, ban, three tries);
      the diagram's S11 edges match it (one "fail: back to the steps 6–9 call, max 3 tries"
      edge); §8 P5 status line; the Later TODO "reference recipes for b23 and b24"
      removed; the fruit TODO stays (brief Out). `docs/WORKFLOW-ROADMAP.md`: M6 row, §3 risk
      rows for tolerances and held-out briefs marked decided.
- [ ] PROJECT.md §3 stays (it already describes stage D), §4 rows (Database functions and
      `app` function count, Orchestration, Scripts: `evals/show_recipe.py`, held-out file,
      test count from a full `pytest` run with the stack up) and §8.
Done when: the roadmaps describe what is built and the full suite passes.
Commit: `Describe stage D as built`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| Every step 3 deviation fits a row, none dropped | `test_recipe_tables.py::test_deviation_takes_every_step3_kind` | 1 |
| Extras never enter OG/IBU/SRM | `test_formulation_check.py::test_extras_do_not_enter_the_numbers`, `test_compute.py::test_misc_grams_are_dose_times_batch` | 2, 4 |
| Colour adjustment moves only the darkest non-crystal and the base | `test_compute.py::test_colour_moves_only_darkest_and_base`, `test_colour_never_moves_crystal` | 3 |
| Step 10's numbers are what the check recomputes | `test_compute.py::test_numbers_are_what_check_recipe_computes` | 4 |
| OG moves only inside its tolerance | `test_compute.py::test_og_moves_only_inside_tolerance` | 4 |
| Each failure kind is caught; only self-picks are banned | `test_validate.py` (one test per kind, `test_wanted_pick_is_never_banned`, `test_user_ibu_does_not_ban_hops`) | 5 |
| An impossible target never passes | `test_validate.py::test_impossible_target_cannot_pass`, `test_pipeline.py::test_impossible_target_fails_after_three_tries` | 5, 8 |
| A saved recipe recomputes to its saved numbers | `test_save_recipe.py::test_recompute_from_saved_rows`, `test_pipeline.py::test_b01_validates_and_saves` | 6, 8 |
| A failed validation saves nothing | `test_save_recipe.py::test_refuses_a_failed_validation` | 6 |
| A banned pick cannot come back on a retry | `test_choose_table.py::test_ban_removes_and_excludes` | 7 |
| Harness and SQL tolerances agree | `test_run.py::test_harness_tolerances_match_sql` | 9 |

## Approved exceptions

None needed: SQL through `psql` as `postgres`, workflows through the n8n CLI import as
OPERATIONS §5 says; no container is recreated.

## Deviations
- 2026-10-25 · Approach, Tasks 3, 4, 9: the four planning questions answered by the user with the recommended option each: (Q1) step 10 does one pass that may move OG within ± 0.002 towards the ABV target, and any number still off goes back to the steps 6–9 call with the value and target, no step-10-only retry (brief R4 updated); (Q2) boil = the largest of 60, the grist's `min_boil_min` and the longest boil addition, which is set to the boil time; (Q3) the base malt with the largest share takes up the colour change; (Q4) held-out styles without reviewed envelopes are accepted.
- 2026-10-25 · Task 4: `app.step10_abv` added (ABV of a grist at an OG, used by the OG move), beside the two functions the plan names — it keeps the bisection readable.
- 2026-10-25 · Task 4: a yeast with no attenuation figure (b10's Abbey Monk Ale) gives `numbers.fg`, `abv` and `attenuation_pct` null and no OG move, instead of raising — step 11's "a null number fails" then sends it back; the output contract allows those nulls.
- 2026-10-25 · Task 4: `recipe.targets.og` is the OG used (moved), not step 4's target, so `app.check_recipe` recomputes step 10's numbers (the task's own test). Rule 9 then fails when the move is above 0.001 and OG is unstated with guidance on; Task 5 must decide how step 11 treats that (asked in the Task 4 report).
- 2026-10-25 · Task 5: step 11 ignores rule 9's OG line (user answer "Skip rule 9's OG line (Rec.)": step 10 moves OG on purpose and step 11 checks the OG against the target at ± 0.002) — and also rule 9's ABV line ("the ABV target is not app.abv of the OG and FG targets"), because the same moved `recipe.targets.og` breaks it (seen on b23: 5.99 vs 5.72); ABV is checked against its target at ± 0.2 by the numbers check. The ABV skip is the implementer's extension of the user's answer.
- 2026-10-25 · Task 5: a yeast with no attenuation figure gives a `numbers` failure "the ABV cannot be computed: the yeast has no attenuation figure" (as the user's note asked).
- 2026-10-25 · Task 5: tests use b08 and b14 for the passing recipe (not b16: the first good proposal for b16 picks a yeast with no attenuation figure, and b01, b16, b23 and b24 miss SRM because the proposal's only base is a Pilsner malt, so the colour adjustment has no absorber). Hops are never `out_of_style` with the totals off, so the ban tests swap in an out-of-style fermentable instead of a hop; the impossible-target test rates the table's levels typical before building the proposal (the style it lands in, Session Beer, has no envelope).
