# M3 · Step 3: the deviation report — implementation plan

Stage: approved
Brief: [brief.md](brief.md)
Branch: m3-deviations

## Approach

- **Step 3 is SQL, called from one new sub-workflow**, as step 2 is (G0: deterministic logic in
  `db/*.sql`, Code nodes only glue). No LLM call (R7).
- **Two SQL files.** `db/036_ingredient_resolver.sql` holds the first ingredient-word resolver,
  on its own because M5 extends it. `db/037_step3.sql` holds the step 3 rules and the function
  that assembles them, `app.step3_deviations(brief jsonb, style jsonb) returns jsonb`. The
  numbers follow apply order: 037 needs 034 (`app.style_level`) and 036.
- **Resolver** `app.resolve_ingredient(word)`: words are normalised (lower case, accents removed,
  punctuation read as spaces, a trailing `s` dropped from words longer than 3 letters, a small
  synonym list such as `abbaye` → `abbey`). The **kind words** `malt` (fermentable), `hop`
  (hop) and `yeast` (yeast) restrict the kind, so "crystal malt" never reaches the Crystal hop
  and "abbey yeast" never reaches Abbey Malt. Then two match rules, the first that finds
  anything wins: (1) the same words as a product's name; (2) every remaining word (kind word
  removed) among the product's name and producer words. No match → no ids (the word goes to
  `unrated`). It reads only `ref.ingredient`, never `evals/` (brief Constraints).
- **Numbers (R2)**: each stated `abv`, `og`, `ibu`, `srm` against the chosen style's range with
  `numrange @>` (bounds inclusive, an open end works); `batch_l` is never compared; no range → no
  deviation.
- **Mismatch**: step 2's `mismatch` object becomes one deviation, unchanged in meaning.
- **Conflicts (R3)**: `app.hint_knob()` is the §7 hint table as a `values` list (hint, side,
  knob, direction). Two sides of the brief's hints that push one knob in opposite directions make
  one conflict naming the brief's hints of each side ("dry vs full, chewy"). Synonym hints share a
  side (dry/crisp, full/chewy, hoppy/juicy) and so never conflict; `stronger` and `session` are
  separate sides.
- **Ingredients (R4, best case)**: for each `wanted` item, every resolved product is rated with
  `app.style_level` over every choice later steps could make: fermentable mash and boil; hop boil
  at the start minute of each boil band in `app.usage_effects()` (0, 5, 30), whirlpool, dry hop,
  and only whirlpool and dry hop when the role is `feature`; yeast `ferment` at both ends of its
  `ref.yeast.temp_c` and at each warm-step temperature of `app.style_fit_cut_points()` that lies
  inside the range (the level only changes at those, measured: Abbey Monk Ale in 26B is
  `out_of_style` up to 21 °C, `allowed` from 22 °C). No dose is passed. The best level wins
  (rank required < typical < allowed < out_of_style < changes_style; ties go by product name,
  then choice order). Only `out_of_style` or `changes_style` becomes a deviation; its `because`
  names the product and the choice. A word with no ids, only non-rateable kinds (water salt), or
  `level: null` (no reviewed envelope) goes to `unrated`. Excluded and inventory are never read.
- **Output order** is fixed (R7 determinism): numbers (abv, og, ibu, srm), mismatch, conflicts in
  table order, ingredients in `wanted` order. `requested_by` is always `user`. `guidance` is the
  brief's (R6). No style → conflicts only, every wanted word in `unrated` (R8).
- **The bar is tested at SQL level first** (step 1's expected brief + `app.step2_best_style` +
  step 3, graded with `evals.grade.grade_step3`), then measured on the real pipeline at G3.

**Measured while planning (2026-10-16):** `ref.ingredient` kinds: fermentable 81, hop 89, yeast
119, water_salt 8 (no `misc`). The five wanted words match one product each by whole word: Flaked
Oats 3393, Flaked Rice 3395, Flaked Corn 3392 (adjunct), Honey 3398, Lactose 3397 (sugar). The
Crystal hop is 515; Crystal T50 and Crystal Extra Dark are malts; Abbey Malt 42 is a fermentable;
abbey yeasts are Abbaye 1845 (17–25 °C), Abbey Monk Ale 1817 (18–26 °C), M47 Belgian Abbey 1872
(18–25 °C). All 119 yeasts have `temp_c`, all with inclusive bounds. Ester and phenol warm steps
are both `above_c: 21` (strict `>`). Hop boil bands in `app.usage_effects()`: 0–4, 5–29, 30+.
Citra in 15B: boil 60 min `allowed`, whirlpool and dry hop `out_of_style`; in 21A whirlpool and
dry hop `typical`. `app.style_number_score` gives `IBU 50 outside 22–40` for 5D. The step 3
contracts and `evals/grade.py::grade_step3` exist and need no change; `evals/run.py` already
grades steps 2 and 3. `app.run_step.step` allows 0–16. Pipeline today: `Step 2 · log ok` →
`Finish run`. Context7 was not used: no library question.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `db/036_ingredient_resolver.sql` | new | `app.ingredient_words`, `app.ingredient_synonym`, `app.ingredient_kind_word`, `app.resolve_ingredient` |
| `tests/test_ingredient_resolver.py` | new | resolver rules, A7 |
| `db/037_step3.sql` | new | number, mismatch and conflict rules; best-case rating; `app.step3_deviations` |
| `tests/test_step3.py` | new | R2–R6, R8, A2–A6, contract, SQL-level bar |
| `n8n/workflows/step-3-deviations.json` | new | the step 3 sub-workflow, exported |
| `n8n/workflows/recipe-pipeline.json` | changed | step 3 block after step 2 |
| `tests/test_workflows.py` | changed | step 3 `Test data` sample, checked against `step3.input` |
| `tests/test_pipeline.py` | changed | step 3 logged (R7) |
| `evals/results/<date>-m3.json` | new | G3 checkpoint results |
| `docs/DATABASE.md`, `docs/OPERATIONS.md` | changed | §5 function lines; five workflows, step 3 in the editor-run list |
| `docs/WORKFLOW-ROADMAP.md`, `docs/RECIPE-ROADMAP.md` | changed | G3 measured and decided; P4 done row |
| `PROJECT.md` | changed | §4 Orchestration row, §8 per task |

## Tasks

### Task 1: a wanted word resolves to its `ref` products
Why: R4 (resolver), A7; M5 extends this first version.
- [ ] `db/036_ingredient_resolver.sql` (header like `db/022_step2.sql`: purpose, "first version,
      extended by M5", needs `010_ref_schema.sql` and `015_app.sql`, apply command, idempotent;
      `create or replace`; `immutable` where no table is read). Comment at the top: the resolver
      keeps its own synonym list and never reads `evals/` or the brief fixtures.
      - `app.ingredient_words(t text) returns text[]`: lower case; accents removed with
        `translate` (the letters of step 2's `app.style_words`); anything not a letter or digit →
        space; split; drop a trailing `s` from words longer than 3 letters that do not end in
        `ss`; then each word replaced by its `app.ingredient_synonym()` `same_as`.
      - `app.ingredient_synonym() returns table (word text, same_as text, note text)`: a
        `values` list, starting with `abbaye` → `abbey`, `caramel` → `crystal`, `maize` → `corn`,
        each with a one-line note (spelling or common name). Comment: add a row only for a
        spelling or common name of the same product, never to fit a brief.
      - `app.ingredient_kind_word() returns table (word text, kind text)`: `malt` → fermentable,
        `hop` → hop, `yeast` → yeast.
      - `app.resolve_ingredient(word text) returns table (ingredient_id bigint, kind text, name
        text, rule text)`, `language sql stable`: the Approach's kind restriction and the two
        rules in order, written as two commented CTEs (`same_name`, `all_words`); the kind word is
        removed from the words for rule 2 only, and only when another word remains. Rows ordered
        by `name, ingredient_id`. `rule` is `same name` or `all words`.
- [ ] Apply twice: `docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1
      < db/036_ingredient_resolver.sql`. Check `pg_proc`: the four functions owned by `postgres`.
- [ ] Write `tests/test_ingredient_resolver.py` (stack unless said):
      `test_brief_wanted_words_resolve` (A7: `oats`, `rice`, `corn`, `honey`, `lactose` → exactly
      Flaked Oats, Flaked Rice, Flaked Corn, Honey, Lactose, one row each; and every `wanted`
      item of b01–b22 in `evals/recipe_briefs.toml` resolves to at least one row);
      `test_crystal_malt_is_not_the_crystal_hop` (A7: all rows `fermentable`, Crystal T50 among
      them, no `hop` row); `test_abbey_yeast_is_not_abbey_malt` (all rows `yeast`: Abbaye, Abbey
      Monk Ale, M47 Belgian Abbey); `test_same_name_wins` (`Citra` → Citra only, not Citra
      LUPOMAX; `Abbey Malt` → Abbey Malt only); `test_case_plural_and_synonym` (`Flaked OATS` →
      Flaked Oats; `East Kent Goldings` → East Kent Golding; `abbaye yeast` gives the same rows as
      `abbey yeast`); `test_unknown_word_resolves_to_nothing` (`unicorn tears` → no rows);
      `test_resolver_reads_no_fixture` (not stack: the SQL file does not contain
      `recipe_briefs`, `evals` or `SYNONYMS`).
- [ ] Run `.venv/bin/pytest tests/test_ingredient_resolver.py`, expect all pass; then
      `.venv/bin/pytest`, expect all pass.
- [ ] `docs/DATABASE.md` §5: one line for the resolver. PROJECT.md §8 entry.
Done when: the file applies twice cleanly, owned by `postgres`, and the resolver tests pass.
Commit: `Add the first ingredient-word resolver`

### Task 2: numbers, mismatch and conflicts are tested SQL rules
Why: R1, R2, R3, R6; A2 (b05, b08, b11, b17, b18), A6 (conflict tests).
- [ ] `db/037_step3.sql` (header as Task 1; needs `022_step2.sql`, `034_style_level.sql`,
      `036_ingredient_resolver.sql`):
      - `app.hint_knob() returns table (hint text, side text, knob text, direction int)`: the
        RECIPE-ROADMAP §7 table as a `values` list, one line per hint and knob, with the table
        quoted in a comment above it: bitter (ibu +1, bu_gu +1); hoppy, juicy (late_hop_share
        +1, side `hoppy/juicy`); dry, crisp (mash_temp −1, attenuation +1, side `dry/crisp`);
        full, chewy (mash_temp +1, attenuation −1, side `full/chewy`); malty (munich_share +1,
        bu_gu −1); darker (srm +1); stronger (og +1); session (og −1). "sugar ≤ 10 %" is a cap,
        not a direction, and is left out (comment says so).
      - `app.step3_conflicts(hints jsonb) returns jsonb`: one deviation per pair of sides present
        in the hints with a shared knob of opposite direction: `kind conflict`, `subject` "<hints of
        side A, comma-separated> vs <hints of side B>" (in table order), `from` "the request's own
        hints (RECIPE-ROADMAP §7)", `level` null, `requested_by` `user`, `because` naming each
        side's knobs ("dry lowers mash temperature and raises attenuation; full, chewy raise mash
        temperature and lower attenuation"), built from the table.
      - `app.step3_numbers(stated jsonb, style_code text) returns jsonb`: per `abv`, `og`, `ibu`,
        `srm` (a `values` list of key and label) with a non-empty range on the style and a value
        outside it (`not range @> value`): `kind number`, `subject` "IBU 50", `from` "5D IBU
        22–40" (open end written `40+`), `level` null, `because` "IBU 50 is above German Pils
        (5D)'s IBU range 22–40" (or "below").
      - `app.step3_mismatch(stated jsonb, mismatch jsonb) returns jsonb`: null mismatch → `[]`;
        else one deviation `kind mismatch`, `subject` "<named> with <label value, for each label
        of ABV/OG/IBU/SRM that appears in `mismatch.range` and is stated>" (b05: "20C Imperial
        Stout with ABV 4"), `from` "<named> <range>", `level` null, `because` "you named <named>,
        but <subject values> is outside its <range>; <chosen> fits better and was chosen".
- [ ] Apply twice (command as in Task 1, file `db/037_step3.sql`); `pg_proc` owner `postgres`.
- [ ] Write the first part of `tests/test_step3.py` (all stack; helpers `brief_of(b)` as in
      `tests/test_step2_pick.py`, `sql(conn, fn, *args)`):
      `test_number_outside_is_a_deviation` (b08 IBU 50 in 5D → one, subject "IBU 50", from
      contains "22–40"; b17 ABV 7 in 8B; b18 SRM 20 in 15A); `test_number_inside_or_on_edge_is_not`
      (b01 ABV 6.5 in 21A, b05 ABV 4 in 15B, b14 ABV 3 in 23A, b21 ABV 4 in
      `session-india-pale-ale`; ABV 5.5 and 7.5 in 21A); `test_batch_is_never_a_deviation`
      (`batch_l` 500 in 21A → none); `test_style_without_range_gives_none` (ABV 12 in 31B → none);
      `test_mismatch_carried` (step 2's b05 output → one mismatch, subject contains "20C" and
      "ABV 4"; null mismatch → `[]`); `test_dry_vs_full_chewy_is_one_conflict` (b11 hints → one
      conflict naming dry, full and chewy; graded equal to b11's expected deviation with
      `evals.grade.deviation_matches`); `test_bitter_vs_malty`; `test_stronger_vs_session`;
      `test_same_side_never_conflicts` (dry + crisp, full + chewy, hoppy + juicy → none);
      `test_unrelated_hints_do_not_conflict` (b19's malty + stronger, b21's hoppy + session → none).
- [ ] Run `.venv/bin/pytest tests/test_step3.py`, expect all pass. `docs/DATABASE.md` §5: one line
      per rule function. PROJECT.md §8 entry.
Done when: the rule tests pass and the file applies twice cleanly.
Commit: `Add step 3 number, mismatch and conflict rules`

### Task 3: a wanted word is rated at its best possible choice
Why: R4, R5; A3, A6 (best case on several products, yeast temperature, feature hop).
- [ ] Append to `db/037_step3.sql`:
      - `app.level_rank(level text) returns int`, immutable: required 1, typical 2, allowed 3,
        out_of_style 4, changes_style 5, else null.
      - `app.ingredient_choices(ingredient_id bigint, role text) returns table (usage text, dose
        jsonb, label text, ord int)`, stable: the Approach's choices, in this order. Fermentable:
        `mash`, `boil` (dose `{}`). Hop: unless `role = 'feature'`, `boil` with
        `{"minutes": m}` for each distinct `min_minutes` of the hop `boil` rows of
        `app.usage_effects()` (label "boil 30 min"); then `whirlpool`, `dry_hop` (label "dry
        hop"). Yeast: `ferment` with `{"ferm_c": t}` for `lower(temp_c)`, each `warm_step.above_c`
        of the esters and phenols cut points that lies inside the range, and `upper(temp_c)`,
        distinct (label "ferment at 26 °C"). Other kinds: no rows.
      - `app.rate_wanted(style_code text, item text, role text) returns jsonb`, stable: resolve
        `item`; rate every product × choice with `app.style_level`; return the best by
        `level_rank`, then product name, then `ord`: `{level, ingredient_id, name, choice,
        because}`, where `because` is "<name> (<choice>) is the closest choice: <style_level's
        because>". Returns `{"level": null, "reason": ...}` when no product resolves, when no
        product has a rateable kind, or when `style_level` gives `level: null` (the reason says
        which).
- [ ] Apply twice.
- [ ] Add to `tests/test_step3.py`: `test_out_of_style_words` (rice/18B, honey/17C, lactose/19C →
      `out_of_style`); `test_in_style_words` (oats/21C, rice/1B, corn/1C, honey/31B → `typical`);
      `test_best_over_products` ("abbey yeast" in 26B → Abbaye, `typical`);
      `test_yeast_best_over_its_temperature_range` ("Abbey Monk Ale" in 26B → `allowed`, choice
      names a temperature above 21 °C; "M47 Belgian Abbey" in 26B → `out_of_style`);
      `test_feature_hop_rated_late_only` (Citra in 15B: role `feature` → `out_of_style` and the
      choice is whirlpool or dry hop; role `background` → `allowed` at a boil);
      `test_unresolved_word_is_unrated` (`unicorn tears` → level null);
      `test_style_without_envelope_is_unrated` (a BJCP code with no reviewed `ref.style_sensory`
      or `ref.style_ingredient` row, found by query in the test → level null, reason names the
      envelope).
- [ ] Run `.venv/bin/pytest tests/test_step3.py`, expect all pass. `docs/DATABASE.md` §5 line.
      PROJECT.md §8 entry.
Done when: the best-case tests pass.
Commit: `Rate wanted words at their best choice`

### Task 4: one SQL function returns the step 3 output
Why: R1, R4–R8; A1 (SQL level), A2–A5, A8 (contract).
- [ ] Append `app.step3_deviations(brief jsonb, style jsonb) returns jsonb`, `language plpgsql
      stable`, commented in this order: 1. *No style* (`style -> 'style'` null): deviations =
      conflicts only, `unrated` = every wanted `item` (R8). 2. *Numbers* from `brief.stated` and
      the style code. 3. *Mismatch* from `style.mismatch`. 4. *Conflicts* from `brief.hints`.
      5. *Ingredients*: for each `brief.wanted` item in order, `app.rate_wanted(code, item,
      role)`; null level → `unrated` (the item text); `out_of_style` / `changes_style` → `kind
      ingredient`, `subject` the item text, `from` "<code> <style name> ingredients", `level`,
      `because` from `rate_wanted`. `excluded` and `inventory` are not read. 6. Return
      `{deviations, unrated, guidance: brief.guidance}`.
- [ ] Apply twice.
- [ ] Add to `tests/test_step3.py` (helper `step3(conn, b)`: b's expected brief → 
      `app.step2_best_style(brief, request, null)` → `app.step3_deviations`):
      `test_a2_cases` (b08, b17, b18 one number each; b05 one mismatch; b11 one conflict; b16,
      b19, b20 one ingredient each; nothing else); `test_a3_no_false_deviations` (b02, b06, b07,
      b10, b12, b15 → no deviation, `unrated` empty); `test_excluded_never_a_deviation` (A4: b08,
      b16 → no deviation or `unrated` entry mentions Saaz, Citra or Mosaic);
      `test_guidance_off_keeps_deviations` (A5: b18 → the SRM deviation, `guidance` false);
      `test_no_style_gives_conflicts_only` (R8: style output with `style` null, brief with hints
      dry + full, wanted rice, ABV 9 → one conflict, `unrated == ["rice"]`);
      `test_same_input_same_output` (all 22 twice, equal);
      `test_output_meets_contract` (A8: all 22 and the no-style case validate against
      `step3.output` with `extensions.jsonschema_validation_errors`);
      `test_briefs_reach_the_bar` (A1 at SQL level: `grade_step2` and `grade_step3` both pass on
      ≥ 18 of b01–b20, and on b21 and b22; the failure message lists each miss with its
      deviations).
- [ ] Run `.venv/bin/pytest tests/test_step3.py tests/test_contracts.py`. If the bar test fails,
      find the rule that misleads; a fix may change a rule or the resolver only in a general way
      (never a rule for one brief), each as a dated Deviations line with the count before and
      after. If that does not reach the bar, stop and report `needs-input` with the misses.
- [ ] Run `.venv/bin/pytest`, expect all pass. `docs/DATABASE.md` §5 line. PROJECT.md §8 entry
      with the SQL-level count.
Done when: the step 3 tests pass and the SQL-level count is ≥ 18/20 with b21 and b22 passing.
Commit: `Add the step 3 deviation report in SQL`

### Task 5: the pipeline runs step 3 and logs it
Why: R7; A8 (logged as step 3). Load the n8n skills first (`using-n8n-skills-official`,
`n8n-workflow-lifecycle-official`, `n8n-node-configuration-official`,
`n8n-error-handling-official`) and follow the MCP order: SDK reference → `get_node_types` →
validate → create / update → check `connections` → publish. Publish the sub-workflow before the
pipeline run that uses it (OPERATIONS §5). Nodes with `onError` go in through the JSON file and
`n8n import:workflow`, as OPERATIONS §5 says (the MCP drops `onError`).
- [ ] New workflow `Step 3 · deviations`, a copy of step 2's shape: trigger *When Executed by
      Another Workflow* with inputs `run_id` (number), `brief` (object), `style` (object) →
      *Execute Workflow* "Check step 3 input" (`Check contract`, `step3.input`) → *Postgres*
      "Find deviations": `select app.step3_deviations($1::jsonb, $2::jsonb) as result` with the
      two values as one expression returning an array → "Check step 3 output" (`step3.output`) →
      *Set* "Return result". Sticky note: what it does, that it writes nothing and calls no LLM;
      `Test data` note with `[{"run_id": 0, "brief": <the step 2 sample brief>, "style": <its step 2
      output for 21A>}]`.
- [ ] `Recipe pipeline` (`eMkkdBar6NIqUa1g`): `Step 2 · log ok` now goes to *Set* "Step 3 ·
      input" `{run_id, brief: <Step 1 · read request output>, style: <Step 2 · best-fit style
      output>, started_at}` → *Execute Workflow* "Step 3 · deviations" (`onError:
      continueErrorOutput`) → ok: "Step 3 · log ok" (`app.run_step` step 3, try 1, input without
      `started_at`, ms as step 2) → `Finish run`; error: "Step 3 · log failure" → "Finish run
      (failed, step 3)" → "Respond failed (step 3)" with `failed_step: 3`. Update the per-step
      sticky note.
- [ ] Validate, import / update, check `connections`, publish both. `.venv/bin/python -m
      evals.workflows`; read the diff: no secrets, only the intended nodes changed.
- [ ] Tests: `tests/test_workflows.py`: `SAMPLES["step-3-deviations.json"]`, `CONTRACT_OF` →
      `step3.input`, `STEP1_INPUT` entry. `tests/test_pipeline.py`: `test_b01_logs_step_1`
      expects steps `[1, 2, 3]`; new `test_step_3_logged` (R7: the West Coast IPA request →
      step 3 row `ok`, `ms >= 0`, `input == {run_id, brief: <step 1 output>, style: <step 2
      output>}`, output passes `step3.output`). `test_bad_guide_fails_at_step_2` keeps `[1, 2]`.
- [ ] Run `.venv/bin/pytest`, expect all pass.
- [ ] `docs/OPERATIONS.md` §5: five workflows to publish; `Step 3 · deviations` in the editor-run
      list. PROJECT.md §4 Orchestration row (5 workflows, steps 1–3 logged) and §8 entry.
Done when: both workflows run published, their files match n8n, and the pipeline tests pass.
Commit: `Run step 3 in the pipeline`

### Task 6: G3 is measured on the real pipeline
Why: G3 (= RECIPE-ROADMAP P4); A1, A2, A8, A9.
- [ ] `.venv/bin/python -m evals.run --save --label m3` (stack up, D2 model). Count b01–b20 with
      step 2 and step 3 both passing; report b21 and b22 beside it. For each step 3 miss, compare
      with Task 4's SQL-level result: a miss only seen here comes from step 1's output (name the
      field), not from step 3.
- [ ] Check A8 on the saved run: every step 3 row of the run is `ok` and its output passes
      `step3.output` (one `psql` query with `extensions.jsonschema_validation_errors`).
- [ ] **If the bar is not met:** fix only in a general way as in Task 4, re-run the SQL tests and
      the runner, and record each change in Deviations. If that does not reach it, stop and report
      `needs-input` with the misses; the bar is not lowered.
- [ ] `docs/WORKFLOW-ROADMAP.md` G3: **Measured** line (counts, A2 cases, results file) and
      **Decided**: stage B (M4) starts next, since the bar is met. `docs/RECIPE-ROADMAP.md` §8 P4
      row: done, with the date, the count and a link to this plan. PROJECT.md §8 entry with the
      measured numbers.
- [ ] Commit `evals/results/<date>-m3.json`.
Done when: the saved run shows ≥ 18/20 on b01–b20 with step 2 and step 3 passing, b21 and b22
reported, and the docs carry the measured numbers.
Commit: `Measure G3 for step 3`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| A wanted word reaches its own product, and the kind word keeps malts, hops and yeasts apart | `tests/test_ingredient_resolver.py::test_brief_wanted_words_resolve`, `::test_crystal_malt_is_not_the_crystal_hop`, `::test_abbey_yeast_is_not_abbey_malt` | 1 |
| The resolver never reads the grader or the briefs | `::test_resolver_reads_no_fixture` | 1 |
| A stated number is a deviation only outside the range; edges, `batch_l` and missing ranges are not | `tests/test_step3.py::test_number_outside_is_a_deviation`, `::test_number_inside_or_on_edge_is_not`, `::test_batch_is_never_a_deviation`, `::test_style_without_range_gives_none` | 2 |
| Opposite hints make one conflict; same-side and unrelated hints none | `::test_dry_vs_full_chewy_is_one_conflict`, `::test_bitter_vs_malty`, `::test_stronger_vs_session`, `::test_same_side_never_conflicts`, `::test_unrelated_hints_do_not_conflict` | 2 |
| Step 2's mismatch is carried | `::test_mismatch_carried` | 2 |
| A word is a deviation only when no product, temperature or usage keeps it in style | `::test_best_over_products`, `::test_yeast_best_over_its_temperature_range`, `::test_feature_hop_rated_late_only`, `::test_out_of_style_words`, `::test_in_style_words` | 3 |
| A word that cannot be rated goes to `unrated`, never to deviations | `::test_unresolved_word_is_unrated`, `::test_style_without_envelope_is_unrated` | 3 |
| No false deviations; excluded and inventory never rated | `::test_a3_no_false_deviations`, `::test_excluded_never_a_deviation` | 4 |
| Guidance off still lists deviations; no style gives conflicts only | `::test_guidance_off_keeps_deviations`, `::test_no_style_gives_conflicts_only` | 4 |
| Same input, same output; output meets the contract | `::test_same_input_same_output`, `::test_output_meets_contract` | 4 |
| Step 3 is logged with input, output and time | `tests/test_pipeline.py::test_step_3_logged` | 5 |

## Approved exceptions

## Deviations
