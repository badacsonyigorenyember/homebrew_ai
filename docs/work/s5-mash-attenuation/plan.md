# S5 · A cited model of mash temperature's effect on attenuation — implementation plan

Stage: approved
Brief: [brief.md](brief.md)
Branch: s5-mash-attenuation

## Approach

- **Source numbers come from Troester's appendix table, not from the figure.** The PDF's
  appendix "Temperature series" table (PDF p. 22) lists all 11 mashes of Figure 10 (PDF p. 11)
  with average mash temperature and attenuation to one decimal. It is an image, so its rows are
  transcribed into `doc-calc.md` and approved by the user (R1). Figure 10 and its text ("~4 %/C"
  over 12 °C) are the cross-check.
- **The curve (brief question 1, answer a).** Troester's limit of attenuation is flat at its
  measured peak, then falls in a straight line: `L(T) = plateau − slope × max(0, T − knee)`.
  - `slope` = least-squares fit over the table rows above the knee (samples 7, 2, 15, 13, 6, 14;
    69.3–78.6 °C).
  - `plateau` = mean of the rows at the peak (samples 10, 8, 9; 63.3–65.9 °C).
  - `knee` = where the fitted line meets the plateau.
  - A read-only scratch computation on 2026-10-17 gave slope 4.153, intercept 371.28,
    plateau 87.83 and knee 68.25 °C. Task 1 measures these again; it does not copy them.
  - Stored rounded: knee 68.3 °C, slope 4.15 points per °C.
  - Samples 12 and 11 (59.9 and 61.9 °C) lie below the 64 °C mash limit, on the rising side of
    the curve, and are left out.
- **The model.** The yeast's attenuation_pct range applies at the reference temperature 66.5 °C
  (brief question 2, answer b; *Yeast* states none). Its middle is the attenuation there. At any
  other mash temperature the curve's difference is added:
  `middle + L(mash) − L(66.5)` = `middle − slope × (max(mash, knee) − max(66.5, knee))`.
  The mash temperature is clamped to 64–69 °C, as today, and the result to the yeast's range.
  Because 66.5 lies below the knee, the model in one sentence (R4) is: *up to 68.3 °C the
  attenuation is the middle of the yeast's range; above 68.3 °C it is 4.15 points lower per °C,
  never outside the yeast's range.*
- **Same signature, same place.** `app.mash_attenuation(numrange, numeric)` keeps its signature
  and stays in `db/032_formulation_check.sql`; only its body and comment change. `check_recipe`
  and `app.style_level` (db/034) call it unchanged.
  - The three model numbers go into `app.formulation_limits()` (db/031) as `mash_ref_c`,
    `mash_knee_c` and `mash_slope_pct_per_c`. The function and rule 10's sentence both read them
    there, so the sentence and the check cannot disagree (db/031's design).
- **Tests pin the constants to the source.** `tests/test_mash_attenuation.py` holds the
  transcribed table. It re-derives slope and knee from that table and compares them with the
  stored limits, and checks that the curve reproduces every row within the stated tolerance (R3).
  The replaced `test_mash_mapping` pins the SQL function's ends and middle (R4).
- **Reference recipes (R6).** The 22 recipes are measured before and after the new SQL is
  applied, into `reference-recheck.md`. A read-only preview on 2026-10-17 (new attenuation fed
  through `app.fg`) suggested that b12 and b22 (both mashed at 68 °C) move from pass to fail,
  with predicted FG below their range. The real numbers come from Task 2. Any change stops the
  task for the user's decision before the commit, so every commit leaves `pytest` green.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `docs/work/s5-mash-attenuation/doc-calc.md` | New | Doc → calc pass: transcribed table, derivation, tolerance, assumptions, Terrill's limits (R1, R7) |
| `docs/work/s5-mash-attenuation/reference-recheck.md` | New | The 22 recipes' rule 10 results before and after (R6, A5) |
| `db/031_formulation_rules.sql` | Changed | 3 new limits; rule 10 sentence names Troester, drops "uncited assumption" (R5) |
| `db/032_formulation_check.sql` | Changed | `app.mash_attenuation` body and comment (R2) |
| `tests/test_mash_attenuation.py` | New | Source-value tests and SQL-follows-curve test (R3) |
| `tests/test_formulation_check.py` | Changed | `test_mash_mapping` replaced by the pinned new behaviour (R4) |
| `tests/test_formulation_rules.py` | Changed | New limits mapped to rule 10 in `LIMIT_RULES`; rule 10 names its source (R5) |
| `tests/fixtures/reference_recipes.toml` | Changed only if the user settles a change by editing a recipe | R6 |
| `tests/test_reference_recipes.py` | Changed only if the user accepts a failure (`ACCEPTED_FAILURES`) | R6 |
| `docs/RECIPE-ROADMAP.md` | Changed | §8 Later: the rule 10 mash-mapping bullet removed (A6) |
| `docs/SOURCES.md` | Changed | Rows for the three sources: calc done by s5 |
| `PROJECT.md` | Changed | §5 articles row status, §8 entries |

## Tasks

### Task 1: Doc → calc pass written and its image-read values approved
Why: R1, R3 tolerance, R7, A1; every later number comes from here.
- [ ] Write `docs/work/s5-mash-attenuation/doc-calc.md`, in the style of
      `docs/finished/s1-maths/doc-calc.md`. Sections:
  1. **Sources.** Each source with its file under `shared/rag-files/`, licence and page
     numbering:
     - Troester 2009, `articles/braukaiser_mash_parameters_2009.pdf`, CC BY-NC 3.0, cited by PDF
       page.
     - Troester mash-time wiki, `articles/braukaiser_mash_time_fermentability.md`.
     - Terrill 2017, `articles/terrill_observations_on_attenuations.md`.
     - White & Zainasheff, *Yeast*, `books/white_zainasheff_yeast.pdf`.
  2. **Troester's temperature series.** All 11 rows of the appendix table (PDF p. 22):
     - Columns: number, starting, end and average temperature, OE, AE and attenuation.
     - Marked **read from an image (typed table)**.
     - One spot check per row: attenuation = (OE − AE) / OE × 100, within 0.5 (e.g. sample 2:
       (13.1 − 2.6) / 13.1 = 80.2).
     - Note: this is apparent attenuation, the same measure as `ref.yeast.attenuation_pct`.
  3. **Derivation.** Which rows go where and why:
     - The plateau rows, the slope rows, and the two rows below 64 °C that are left out.
     - The least-squares slope and intercept, the plateau mean, the knee, and the rounding
       (knee to 0.1 °C, slope to 0.01).
     - Recompute with a scratch script in the scratchpad (not kept).
     - Cross-check against the PDF p. 11 text: slope "~4 %/C" over a 12 °C range, and the
       figure's regression line starting near 68 °C.
  4. **Tolerance (R3).** Each table row from 63.3 to 78.6 °C within **2.5 points** of the curve
     (largest residual expected near 2.2, sample 15). Stored slope within 0.01 of the fit. Stored
     knee within 0.1 °C of the derived one.
  5. **Reference temperature.** *Yeast* gives no mash temperature for a strain's range; it says
     only that the range is for the average wort (PDF p. 130). Hence 66.5 °C (brief question 2).
     The middle of the yeast's range is taken as its value there.
  6. **The model.** The formula from this plan's Approach, the R4 sentence, and a worked table
     for `[78,82]` at 64, 66.5, 68.3, 69 and 70 °C (expect 80, 80, 80, 78 clamped (77.095
     unclamped), 78), plus `[70,90]` at 69 °C (expect 77.095).
  7. **Assumptions and known limits.**
     - A recipe's single mash temperature is read as Troester's average mash temperature. His
       mashes dropped ~4 °C over 60 min (PDF p. 11).
     - One all-Pilsner grist, pH 5.5, 60 min. The mash-time wiki shows fermentability still
       changing after a negative iodine test, so the model holds for a ~60 min rest.
     - Briggs's single-infusion data is not linear past the peak (PDF p. 11–12).
     - Pre-peak rows below 64 °C are not modelled.
  8. **Terrill (R7).** As far as the text says:
     - 3522: attenuation falls nearly linearly with temperature.
     - 2206: no strong correlation.
     - 1272: flat from 64–70 °C, sharp drop above.
     - Lab ranges are comparative; most of his batches attenuated above Wyeast's 72–77 %.
     - The plots are images and were not saved, so no numbers are taken from them. This is a
       known limit: per-strain behaviour is not modelled.
  9. **Version log.** `calc_version` is not changed: it covers `db/030_maths.sql` only, and this
     work does not touch that file.
- [ ] Commit, then **stop and report `needs-approval`**. The user checks the 11 transcribed rows
      against PDF p. 22 and approves the derived knee, slope and tolerance. On approval add
      `Approved by the user <date>` at the top of `doc-calc.md`, in Task 2's commit.
      If the approved numbers differ from 68.3 / 4.15, update the expected values in this plan
      and add a Deviations line.
Done when: `doc-calc.md` has all nine sections and the user has approved the image-read rows and
the derived numbers.
Commit: `Add doc-calc pass for mash attenuation`

### Task 2: Mash attenuation follows Troester's curve, recipes re-checked
Why: R2–R6, A2–A5.
- [ ] **Before anything is applied**, measure the 22 reference recipes with the current
      function. For each, record the brief, `mash_c`, yeast `attenuation_pct`,
      `numbers.attenuation_pct`, `numbers.fg`, rule 10 status and the target FG range. Use a
      scratch script in the scratchpad that imports `RECIPES`, `build_input` and `check` from
      `tests.test_reference_recipes`, run with `.venv/bin/python`. Write the "before" columns
      of `reference-recheck.md`.
- [ ] Write the tests first and see them fail against the current function:
  - `tests/test_mash_attenuation.py`:
    - `TEMPERATURE_SERIES`: sample → (average °C, attenuation %), the 11 approved rows, with a
      comment citing Troester 2009, appendix table, PDF p. 22, and doc-calc §2.
    - `test_slope_fits_the_table`: least-squares over samples 7, 2, 15, 13, 6, 14. The slope's
      magnitude is within 0.01 of `formulation_limits()->'mash_slope_pct_per_c'`.
    - `test_knee_meets_the_plateau`: (intercept − mean of samples 10, 8, 9) / slope is within
      0.1 of `mash_knee_c`.
    - `test_curve_reproduces_the_table`: `plateau − slope × max(0, T − knee)`, using the stored
      knee and slope, is within 2.5 of each row from samples 10, 8, 9, 7, 2, 15, 13, 6, 14.
    - `test_function_follows_the_curve`: for `'[0,100]'` and mash 64.0 to 69.0 in 0.5 steps,
      `app.mash_attenuation(r, T) − app.mash_attenuation(r, 66.5)` equals the curve's
      `L(T) − L(66.5)` within 1e-6.
  - `tests/test_formulation_check.py::test_mash_mapping`, replaced:
    - `[78,82]` gives 80 at 64, 66.5 and 68.3; 78 at 69 and at 70 (clamped); 80 at 63.
    - `[70,90]` gives 77.095 at 69.
    - Null range or null mash gives null.
    - The rule 10 sentence has no "uncited assumption".
    - `check(... mash_c=64)["numbers"]["attenuation_pct"] == approx(80)`.
  - `tests/test_formulation_rules.py`:
    - `LIMIT_RULES` gains `"mash_ref_c": ["10"], "mash_knee_c": ["10"],
      "mash_slope_pct_per_c": ["10"]`.
    - New `test_rule_10_names_its_source`: the sentence contains "Troester" and not "uncited".
- [ ] `db/031_formulation_rules.sql`:
  - Add `"mash_ref_c": 66.5, "mash_knee_c": 68.3, "mash_slope_pct_per_c": 4.15` to
    `app.formulation_limits()`, with a comment line pointing to the s5 doc-calc.
  - Rewrite rule 10's sentence with `format()` from those limits. It keeps the mash limits and
    the FG-range clause. It ends with the R4 behaviour and names the source, e.g. "…Up to
    68.3 °C the attenuation is the middle of the yeast's attenuation_pct range, which applies at
    66.5 °C; above 68.3 °C it is 4.15 points lower per °C, never outside that range (Troester
    2009, limit of attenuation against mash temperature)."
  - The sentence must not use "some", "usually", "typically", "about" (`VAGUE`) or any
    ingredient name (so no "Pilsner").
- [ ] `db/032_formulation_check.sql`: rewrite `app.mash_attenuation(attenuation numrange,
      mash_c numeric) returns numeric` (plpgsql, immutable, same signature).
  - Read the five mash limits.
  - Return null on a null range, an open bound or a null mash, as today.
  - `clamped := greatest(low_c, least(high_c, mash_c))`, `middle := (top + bottom) / 2`.
  - `result := middle − slope × (greatest(clamped, knee_c) − greatest(ref_c, knee_c))`, then
    clamp it to `[bottom, top]`.
  - The comment replaces "UNCITED ASSUMPTION". It cites Troester 2009 (braukaiser.com,
    CC BY-NC 3.0, Figure 10 and appendix temperature series) and the doc-calc, and gives the
    R4 sentence.
- [ ] Apply both files twice each as postgres, 031 first:
      `docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/031_formulation_rules.sql`
      then the same for `db/032_formulation_check.sql`. Expect no error either time.
      Check the owner: `select proowner::regrole from pg_proc where proname in
      ('mash_attenuation','formulation_limits','formulation_rules')` gives `postgres` for each.
- [ ] Run `.venv/bin/pytest tests/test_mash_attenuation.py tests/test_formulation_check.py
      tests/test_formulation_rules.py`. Expect all pass.
- [ ] Measure the 22 recipes again with the same script and fill the "after" columns of
      `reference-recheck.md`, with one line on which statuses changed.
- [ ] If any recipe's rule 10 status changed: **stop before committing and report
      `needs-input`**. Show the user the before/after rows with old and new predicted FG and
      the target range. Options per recipe:
  - a) change the recipe in `tests/fixtures/reference_recipes.toml`, for example raising
    `mash_c` to 69 °C, as the new model's way to raise the FG;
  - b) accept the failure in `ACCEPTED_FAILURES` with the user's decision and date;
  - c) revisit the model, which goes back to Task 1.

  Apply the user's answer and record it in `reference-recheck.md` (decision and date).
- [ ] Run `.venv/bin/pytest`. Expect all pass.
Done when: A2–A5 hold. Both SQL files applied twice cleanly and owned by `postgres`; the new
tests pass and were seen failing first; the rule 10 sentence names Troester; every rule 10
change is settled by the user and recorded; full `pytest` passes.
Commit: `Replace mash mapping with Troester's curve`

### Task 3: Roadmap and source status show the TODO resolved
Why: A6; PROJECT.md §10.
- [ ] `docs/RECIPE-ROADMAP.md` §8 Later: remove the bullet "replacing rule 10's uncited linear
      mash-temperature mapping with a cited model: now a work item, …". Leave the multi-step
      mash TODO, which is still out of scope.
- [ ] `docs/SOURCES.md` rows for `braukaiser_mash_parameters_2009.pdf`,
      `braukaiser_mash_time_fermentability.md` and `terrill_observations_on_attenuations.md`:
      the s5 calc pass is done (doc-calc link).
- [ ] `PROJECT.md` §5 articles row: drop "calc still in s5-mash-attenuation" and keep
      m7-process.
- [ ] Run `.venv/bin/pytest`. Expect all pass.
Done when: `grep -n "uncited" docs/RECIPE-ROADMAP.md` finds nothing, and full `pytest` passes.
Commit: `Mark rule 10 mash model done in roadmap`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| Stored slope matches the least-squares fit of Troester's table | `tests/test_mash_attenuation.py::test_slope_fits_the_table` | 2 |
| Stored knee is where the fitted line meets the measured plateau | `tests/test_mash_attenuation.py::test_knee_meets_the_plateau` | 2 |
| The curve reproduces Troester's rows within 2.5 points | `tests/test_mash_attenuation.py::test_curve_reproduces_the_table` | 2 |
| The SQL function follows the curve across 64–69 °C | `tests/test_mash_attenuation.py::test_function_follows_the_curve` | 2 |
| Ends, middle and clamps of `app.mash_attenuation` (R4) | `tests/test_formulation_check.py::test_mash_mapping` | 2 |
| Rule 10 sentence shows the new limits and names its source (R5) | `tests/test_formulation_rules.py::test_text_uses_the_limits`, `::test_rule_10_names_its_source` | 2 |
| Rule 10 still fails and passes where it should | `tests/test_formulation_check.py::test_rule_10` (unchanged, must pass) | 2 |
| The 22 reference recipes pass, or failures are accepted by the user | `tests/test_reference_recipes.py::test_every_rule_passes` | 2 |

## Approved exceptions

None.

## Deviations
