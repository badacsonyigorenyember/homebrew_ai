# M4 · Steps 0, 4 and 5: brewer profile, targets and design frame — implementation plan

Stage: verify
Brief: [brief.md](brief.md)
Branch: m4-targets-blueprint

## Approach

- **Three steps, three SQL files, three sub-workflows**, as steps 2 and 3 are (G0: logic in
  `db/*.sql`, Code nodes only glue, no LLM; R13). `db/038_step0.sql` (profile reader and the
  `default` row), `db/039_step4.sql` (targets), `db/041_step5.sql` (design frame; 040 is taken by
  `kb_search`). The pipeline runs step 0 before step 1 and steps 4, 5 after step 3, each logged.
- **One hint table.** `app.hint_knob()` in `db/037_step3.sql` gets four more columns:
  `position` (fraction of the style range for `og`, `ibu`, `srm`: 0.875 up, 0.125 down; R5),
  `mash_c` (64.5 / 68.5 for `mash_temp`), `intent` (the ingredient intent step 5 passes on) and
  `source` (`<ref.source slug>, <where>` or `unsourced`; R6). A new row `malty → ibu −1`
  (R5: malty moves IBU down). Step 3's conflicts keep reading it; step 4 and step 5 read it through
  one helper, `app.hint_moves(hints)`, which drops every knob the hints pull both ways (R7).
  Intents sit on the knob they belong to (`dry`'s "high-attenuation yeast; sugar at most 10 %" on
  `attenuation`, `full`'s "lower-attenuation yeast; oats or dextrin malt" on `attenuation`), so a
  conflicting knob drops its intent too (A3).
- **Targets (R4, R5, R8).** `app.step4_numbers(style_code, stated, hints)` is the one place that
  says where OG, FG, ABV, IBU and SRM go: stated, else the hinted position, else the midpoint;
  then ABV = `app.abv(OG, FG)`; if that ABV is outside the ABV range and OG is not stated, OG
  moves inside its range just far enough (`app.og_for_abv`, bisection on s1's `app.abv`); a
  stated ABV keeps FG and solves OG. Guidance does not change this (R4). `app.step4_targets`
  wraps it with the style used (base style for a style with no vitals, R9), batch size (R3),
  mash target (R5, R7), applied knobs and step 3's conflicts.
- **Rule 9 calls `app.step4_numbers`** for its expected values, so the check and step 4 cannot
  disagree (R11). Its input gets the brief's `hints`. It stops comparing ABV with its midpoint
  and instead checks the ABV target is `app.abv(OG target, FG target)` within the ABV tolerance
  (this keeps `midpoint_tolerance.abv` in use and the sentence test whole). OG and FG still count
  as stated when the ABV is stated; guidance off still skips the rule.
- **Every value says where it came from (R12):** `{value, from, because}`, `from` an enum
  (`midpoint`, `hint`, `stated`, `derived`, `profile`, `none`, …) a grader can read, `because` a
  sentence for the recipe sheet.
- **Step 5 holds no ratio numbers (R10, D7):** the rules and limits, one slot per wanted word with
  its resolved ids, ingredient-table `role` and `max_pct`, the excluded and inventory words with
  ids, the applied knobs' intents, and the attenuation the targets need with the yeast band that
  reaches it through `app.mash_attenuation`.
- **Graders stay pure Python and independent of the SQL** (G4: "checked by code against
  `ref.beer_style`"): `evals/run.py` reads the facts a grader needs (style ranges, `app.abv`,
  the rules) from the database and passes them in.

**Readings of the brief, decided by the user 2026-10-17 (option a each; brief A1, A4, R11 updated):**
1. A4 follows R3: b01 20 L `stated`, b19 10 L `stated`, the 17 others 20 L `profile`.
2. A1: an OG solved from a stated ABV follows that number and may leave the range (measured: b14 1.0279 < 23A's 1.028, b17 1.0672 >
   8B's 1.052). It has `from: derived` and a `because` naming the stated ABV; the grader accepts it.
3. R11's re-check: rule 9 checks the ABV target against `app.abv(OG, FG)` within 0.1, and the reference recipes get each brief's `hints`, and all 22 `targets` become
   step 4's targets (changes b01, b09, b22 IBU, b19 OG and IBU, b18 OG, and every ABV to
   `app.abv` of its OG and FG). Ingredients, `mash_c` and process settings are not touched.

**Measured while planning (2026-10-17):** `app.brewer_profile` 0 rows, `app.inventory` 0 rows,
16 profile columns as the brief says, no unique key on `name`. Of the 22 brief styles only 15A
(b18) has a midpoint-derived ABV outside its ABV range (3.72 < 3.8; OG for 3.8 is 1.0417). b19:
`stronger` puts 17C's OG at 1.1225, ABV 12.13; ABV 10.0 needs OG 1.1065 at FG 1.029. Stated-ABV
OGs at the FG midpoint (0.0001 scan): b01 1.0613, b05 1.0401, b14 1.0279, b17 1.0672, b21
1.0407. 31B has no OG, FG, ABV, IBU or SRM; every other brief style has closed ranges.
`app.resolve_ingredient`: every wanted word finds one fermentable (Flaked Oats adjunct 30 %,
Flaked Rice adjunct 40 %, Flaked Corn adjunct 20 %, Honey sugar 20 %, Lactose sugar 10 %);
"dark candi sugar" finds nothing; "crystal malt" 11 rows, "Munich malt" 4. The reference recipes
hold midpoint targets and no hints. `tests/test_contracts.py` requires every property of a
contract to be required (except step 1's `temperature`, `seed`) and lists contracts for steps
0–3 only; `test_formulation_rules.py::test_text_uses_the_limits` requires every
`midpoint_tolerance` value in rule 9's sentence. `app.hint_knob()` is read with
`with ordinality as h(hint, side, knob, direction, ord)`, so new columns need that alias list
changed. Context7 was not used: no library question (n8n is handled through its skills in Task 8).

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `db/038_step0.sql` | new | `default` profile row (insert if absent), `app.step0_profile` |
| `db/037_step3.sql` | changed | `app.hint_knob()` with position, mash_c, intent, source; malty → IBU row; `step3_conflicts` alias list |
| `db/039_step4.sql` | new | `app.range_position`, `app.og_for_abv`, `app.fg_for_abv`, `app.hint_moves`, `app.step4_numbers`, `app.step4_targets` |
| `db/031_formulation_rules.sql`, `db/032_formulation_check.sql` | changed | rule 9 sentence and check |
| `db/041_step5.sql` | new | `app.step5_refs`, `app.step5_attenuation`, `app.step5_frame` |
| `shared/contracts/step4.{input,output}.schema.json`, `step5.{input,output}.schema.json` | new | step contracts |
| `shared/contracts/formulation_check.input.schema.json` | changed | required `hints` |
| `tests/test_step0.py`, `tests/test_step4.py`, `tests/test_step5.py` | new | step tests |
| `tests/test_step3.py`, `tests/test_formulation_check.py`, `tests/test_formulation_rules.py`, `tests/test_reference_recipes.py`, `tests/test_contracts.py`, `tests/test_grade.py`, `tests/test_run.py`, `tests/test_workflows.py`, `tests/test_pipeline.py` | changed | as each task says |
| `tests/fixtures/reference_recipes.toml` | changed | `hints` per recipe; targets = step 4's |
| `evals/grade.py`, `evals/run.py` | changed | `grade_step4`, `grade_step5`; steps 4, 5 graded |
| `n8n/workflows/step-0-load-profile.json`, `step-4-targets.json`, `step-5-design-frame.json` | new | sub-workflows, exported |
| `n8n/workflows/recipe-pipeline.json` | changed | step 0 before step 1; steps 4, 5 after step 3; `profile_id` |
| `docs/work/m4-targets-blueprint/hint-sources.md` | new | every hint row's source or *unsourced* (A12) |
| `evals/results/<date>-m4.json` | new | G4 results |
| `docs/DATABASE.md`, `docs/OPERATIONS.md`, `docs/RECIPE-ROADMAP.md`, `docs/WORKFLOW-ROADMAP.md`, `docs/SOURCES.md` | changed | function lines; workflows; §3 step 4–5 rows, §7, §8 Later TODO; G4; Bru'n Water use |
| `PROJECT.md` | changed | §4 rows, §8 per task |

Apply command for every SQL file (OPERATIONS §4), run twice to show it is idempotent, then check
owners with `select proname, pg_get_userbyid(proowner) from pg_proc where pronamespace = 'app'::regnamespace and proname = any(<names>)`:
`docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/<file>.sql`

## Tasks

### Task 1: step 0 reads a stored profile, with a cited default
Why: R1, R2; A7. Step 0 is first needed here.
- [x] `db/038_step0.sql` (header as `db/037`: purpose, needs `015_app.sql`, apply command,
      idempotent).
      - The `default` row: `insert into app.brewer_profile (name, batch_l, efficiency_pct,
        boil_off_l_h, losses_l, grain_abs_l_kg, ca_mg_l, mg_mg_l, na_mg_l, so4_mg_l, cl_mg_l,
        hco3_mg_l, units) select 'default', 20, 72, 4, 2, 1.0, 0, 0, 0, 0, 0, 0, 'metric' where
        not exists (select 1 from app.brewer_profile where name = 'default')`. Never an update:
        a re-run must not overwrite numbers the user changed later. Comment above it: the
        brewhouse numbers are the reference recipes' fixture numbers; the ions are distilled
        water, Bru'n Water *Water Knowledge* §4.2.1, "Distilled water is free of all ions"
        (source `brunwater-water-knowledge`), a **placeholder until the user can set their own
        water** (RECIPE-ROADMAP §8 Later).
      - `app.step0_profile(profile_id bigint) returns jsonb`, `plpgsql stable`: null → the
        `default` row with the lowest id; an id with no row → `raise exception 'step 0: no
        brewer profile %'`; no `default` row → raise naming `db/038_step0.sql`. Returns the
        `step0.output` shape: `batch_l`, `efficiency_pct`, `boil_off_l_h`, `losses_l`,
        `grain_abs_l_kg`, `water {ca, mg, na, so4, cl, hco3}` (null stays null), `units`,
        `inventory` (the profile's `app.inventory` rows as `{raw_name, ingredient_id, amount,
        unit}`, ordered by id; `[]` today).
- [x] Apply twice; `select count(*) from app.brewer_profile where name = 'default'` is 1 after
      both runs; owner `postgres`.
- [x] Write `tests/test_step0.py` (stack): `test_default_profile` (A7: null → 20, 72, 4, 2, 1.0,
      six ions 0, `metric`, inventory `[]`); `test_output_meets_contract` (validates against
      `step0.output` with `extensions.jsonschema_validation_errors`); `test_profile_by_id` (a row
      inserted in a rolled-back transaction with two null ions and one inventory row is returned
      by its id, nulls kept, the inventory row present); `test_unknown_id_raises`;
      `test_rerun_keeps_user_values` (in a rolled-back transaction: update the default's `ca_mg_l`
      to 50, run the insert statement from the file again, `ca_mg_l` is still 50);
      `test_sql_cites_water_source` (not stack: the file contains `brunwater-water-knowledge`,
      `4.2.1` and `placeholder`).
- [x] `docs/RECIPE-ROADMAP.md` §8 Later cell: add `- TODO: let the user set their own water
      ions in the brewer profile (input path, form or command); until then the default profile
      uses distilled water (all six ions 0 mg/L, Bru'n Water §4.2.1; user request 2026-10-17)`.
      `docs/SOURCES.md` `brunwater_water_knowledge.md` row: add "m4: default profile ions (§4.2.1)".
- [x] Run `.venv/bin/pytest tests/test_step0.py tests/test_contracts.py`, expect all pass.
- [x] `docs/DATABASE.md` §5: `app.step0_profile` and the `default` row. PROJECT.md §4 Database
      row (`app.brewer_profile` 1 row) and §8 entry.
Done when: the file applies twice with one `default` row, and the step 0 tests pass.
Commit: `Add step 0 profile reader and default profile`

### Task 2: one hint table says how far each knob moves and where that comes from
Why: R5, R6, R7; A12. Step 3 and step 4 read the same table.
- [x] `db/037_step3.sql`: replace `app.hint_knob()` with `drop function if exists
      app.hint_knob();` then `create function app.hint_knob() returns table (hint text, side
      text, knob text, direction int, position numeric, mash_c numeric, intent text, source
      text)` (the return type changes, so `create or replace` cannot be used). Rows, in this
      order (new columns: position · mash_c · intent):
      - bitter: `ibu` +1 · 0.875 · – · –; `bu_gu` +1 · – · – · – (BU:GU follows from the IBU move)
      - hoppy, juicy (`hoppy/juicy`): `late_hop_share` +1 · – · – · "a larger late and dry hop share (IBU unchanged)"
      - dry, crisp (`dry/crisp`): `mash_temp` −1 · – · 64.5 · –; `attenuation` +1 · – · – · "a high-attenuation yeast; sugar at most 10 % of the grist"
      - full, chewy (`full/chewy`): `mash_temp` +1 · – · 68.5 · –; `attenuation` −1 · – · – · "a lower-attenuation yeast; oats or dextrin malt"
      - malty: **new** `ibu` −1 · 0.125 · – · –; `munich_share` +1 · – · – · "a larger kilned share (Munich or Vienna)"; `bu_gu` −1
      - darker: `srm` +1 · 0.875 · – · "colour from crystal or roast"
      - stronger: `og` +1 · 0.875; session: `og` −1 · 0.125
      Update the comment above it: RECIPE-ROADMAP §7 as it now stands; what each column means
      (`position` 0 = range min, 1 = max, user decision 2026-10-17: the middle of the top or
      bottom quarter; `mash_c` the middle of the §7 band); "sugar at most 10 %" is an intent,
      not a direction.
- [x] Sources (R6): for each row, look for a passage that states that knob for that hint, in
      `kb.chunk` (full text: `select s.slug, c.page, c.section_path, left(c.text, 300) from
      kb.chunk c join ref.source s on s.id = c.source_id where c.fts @@ websearch_to_tsquery('english', '<words>')`;
      start with mash temperature and body or fermentability, oats and body, sugar and dryness,
      crystal or roast and colour, Munich and malty, BU:GU). A row gets `'<slug>, <page or
      section>'` only when the passage states the knob; the positions (0.875 / 0.125) and the
      exact mash values are the user's decision and are not themselves sourced. Every other row is
      `'unsourced'`. Write `docs/work/m4-targets-blueprint/hint-sources.md`: one line per row
      (hint, knob, source with a quote of at most 15 words, or *unsourced*), and the list of
      unsourced rows to source before G6 (brief Out of scope).
- [x] In `app.step3_conflicts`, change the alias list to
      `with ordinality as h(hint, side, knob, direction, position, mash_c, intent, source, ord)`
      (the ordinality column comes after all of them); the rest is unchanged.
- [x] Apply twice; owner `postgres`.
- [x] Tests: `tests/test_step3.py` passes unchanged (the conflict texts keep their substrings;
      bitter vs malty now also names IBU). New in `tests/test_step4.py` (stack):
      `test_hint_rows_sourced_or_marked` (A12: every `source` is `unsourced` or starts with a
      `ref.source.slug` followed by `, `); `test_hint_positions` (R5: every `og`, `ibu`, `srm`
      row has position 0.875 for +1 and 0.125 for −1; every `mash_temp` row has `mash_c` 64.5
      for −1 and 68.5 for +1; no other row has either); `test_malty_lowers_ibu`.
- [x] Run `.venv/bin/pytest tests/test_step3.py tests/test_step4.py`, expect all pass.
- [x] `docs/RECIPE-ROADMAP.md` §7: the table names the positions (top / bottom quarter → 87.5 %
      / 12.5 %, mash 64.5 / 68.5 °C, malty IBU down) and links `hint-sources.md`; the "starter
      table" line says unsourced rows are used marked and sourced before G6. `docs/DATABASE.md`
      §5 `hint_knob` line. PROJECT.md §8 entry with the count of sourced and unsourced rows.
Done when: step 3 tests pass unchanged, every row has a source or `unsourced`, and
`hint-sources.md` lists the unsourced rows.
Commit: `Extend the hint table with positions and sources`

### Task 3: target numbers follow the style, the hints and the user's numbers
Why: R4, R5, R7, R8; A1, A2, A5 at function level. Wrong targets corrupt every later step.
- [x] `db/039_step4.sql` (header as `db/037`; needs `030_maths.sql`, `031`, `037`):
      - `app.range_position(r numrange, fraction numeric) returns numeric`, immutable: null for
        a null or empty range; the one bound when the other is open; else
        `lower + fraction × (upper − lower)`.
      - `app.og_for_abv(abv numeric, fg numeric) returns numeric`, immutable: bisection on OG
        between `fg` and 1.200 for 40 rounds, `app.abv` rising with OG; raise when `abv` is not
        reachable in that interval. `app.fg_for_abv(og numeric, abv numeric)`: the same on FG
        between 1.000 and `og` (for a request that states both OG and ABV; no brief does).
        Comment: inverse of s1's `app.abv`, no new formula.
      - `app.hint_moves(hints jsonb) returns table (knob text, direction int, hints text,
        position numeric, mash_c numeric, intent text, source text)`, stable: the
        `app.hint_knob()` rows of the brief's hints, minus every knob that has both +1 and −1
        among them (R7); one row per knob and direction, `hints` the brief's hints for it
        comma-separated in table order, `source` the distinct sources joined with `; `.
      - `app.step4_numbers(style_code text, stated jsonb, hints jsonb) returns jsonb`, `plpgsql
        stable`, commented in this order, each value `{value, from, because}`:
        1. IBU and SRM: stated → `stated`; else a moved knob → `hint`, value
           `app.range_position(range, position)`, because "bitter: 87.5 % of 21A IBU 40–70";
           else `midpoint` (position 0.5), because "midpoint of 21A IBU 40–70"; no range → value
           null, `none`.
        2. OG the same way; FG is stated or `midpoint` (no hint moves FG).
        3. ABV: stated ABV and stated OG → FG = `app.fg_for_abv`, `derived`. Stated ABV only →
           OG = `app.og_for_abv(abv, fg)`, `derived`, because "solved so app.abv gives the stated
           ABV 6.5 at FG 1.011"; it replaces an OG hint. Else ABV = `app.abv(og, fg)`, `derived`;
           if outside the ABV range and OG is not stated, OG = `app.og_for_abv(<nearest end>,
           fg)`, kept inside the OG range, `derived`, because names the OG it moved from and the
           range end; ABV recomputed.
        4. Rounding: OG and FG to 4 decimals, ABV to 2; IBU and SRM not rounded (66.25, 13.625).
           An OG solved to reach an ABV range end is rounded toward the inside (down for the
           maximum, up for the minimum), so the rounded ABV stays in range.
- [x] Apply twice; owner `postgres`.
- [x] Add to `tests/test_step4.py` (stack): `test_range_position` (21A IBU 0.875 → 66.25, 6A IBU
      0.125 → 18.75, open range `[40,)` → 40, null → null); `test_og_for_abv_inverts_abv`
      (for ABV 3, 4, 6.5, 7, 10 and FG 1.0045–1.029: `app.abv(app.og_for_abv(a, fg), fg)` within
      0.01 of a; same for `fg_for_abv`); `test_midpoints_without_hints` (16A: OG 1.052, FG 1.018,
      IBU 30, SRM 35, all `midpoint`); `test_hint_moves_ibu` (A2: 21A + bitter → 66.25 `hint`;
      6A + malty → 18.75); `test_stated_wins` (5D + bitter + IBU 50 → 50 `stated`; 15A + darker +
      SRM 20 → 20 `stated`); `test_conflicting_hints_leave_default` (`hint_moves` of dry, full,
      chewy has no `mash_temp` or `attenuation` row; bitter + malty leaves IBU at the midpoint);
      `test_stated_abv_solves_og` (A5: b01 21A ABV 6.5 → FG 1.011, `app.abv(og, fg)` within 0.1
      of 6.5; b14 23A ABV 3 + session → OG solved, not the session position; b17 8B ABV 7;
      b21 session IPA ABV 4); `test_abv_out_of_range_moves_og` (A2, R8: 15A → ABV ≥ 3.8 and OG
      just above 1.041; 17C + stronger → OG > 1.100, ABV ≤ 10.0, OG `derived` and its because
      names 1.1225); `test_derived_abv_inside_range` (A5 for each b01–b22 style with the brief's
      stated and hints: ABV within 0.1 of `app.abv(og, fg)`, and inside the ABV range unless
      stated); `test_style_without_ranges` (31B: every value null with `none`, a stated IBU
      still `stated`).
- [x] Run `.venv/bin/pytest tests/test_step4.py`, expect all pass. `docs/DATABASE.md` §5 lines.
      PROJECT.md §8 entry.
Done when: the target tests pass and the file applies twice cleanly.
Commit: `Add step 4 target numbers in SQL`

### Task 4: one SQL function returns the step 4 output, with its contracts
Why: R3, R7, R9, R12; A1–A6, A10 at SQL level.
- [x] Append `app.step4_targets(brief jsonb, style jsonb, profile jsonb, deviations jsonb)
      returns jsonb`, `plpgsql stable`, commented in this order:
      1. *Style used*: step 2's `style.code`, `from: chosen`; when that style has none of OG, FG,
         ABV, IBU, SRM, the first `alt_styles` code that has them, `from: base_style`, because
         "31B has no OG, FG, ABV, IBU or SRM range; its base style 18A (step 2's first
         alternative) is used"; no style or no usable alternative → code null, `from: none`.
      2. *Batch*: `brief.stated.batch_l` → `stated`; else `profile.batch_l` → `profile`.
      3. *Numbers*: `app.step4_numbers(code, brief.stated, brief.hints)`.
      4. *Mash*: a `mash_temp` row of `app.hint_moves` → its `mash_c`, `hint`; else the middle of
         `mash_min_c`..`mash_max_c` from `app.formulation_limits()` (66.5), `midpoint`, because
         "middle of rule 10's mash range 64–69 °C".
      5. *Knobs*: every `app.hint_moves` row as `{knob, direction, hints, intent, source}`.
      6. *Conflicts*: the `kind: conflict` items of `deviations.deviations`, unchanged.
      7. Return `{style, batch_l, targets {og, fg, abv, ibu, srm}, mash_c, knobs, conflicts,
         guidance}` (`guidance` the brief's).
- [x] Contracts: `shared/contracts/step4.input.schema.json` (`run_id` integer, `brief`, `style`,
      `profile`, `deviations` objects; description says each is an already-checked step
      output) and `step4.output.schema.json`: `additionalProperties: false` everywhere, every
      property required; each value object `{value: number|null, from, because: string
      minLength 1}` with `from` enums: style `chosen|base_style|none` (and `code`, `name`
      string|null instead of `value`), batch `stated|profile`, targets
      `midpoint|hint|stated|derived|none`, mash `midpoint|hint`; `knobs` items `{knob,
      direction: -1|1, hints, intent: string|null, source}`; `conflicts` items = the
      `step3.output` deviation shape. Description names the absent slots: a target `value` null
      with `from: none`; `style.code` null.
- [x] `tests/test_contracts.py`: `NAMES` for steps 0–5; `ABSENT_SLOTS["step4.output"] =
      [("targets.og.value", "null"), ("conflicts", "array")]`; a `GOOD` example and two `BAD`
      ones (a `from` outside the enum; a missing `because`).
- [x] Apply twice.
- [x] Add to `tests/test_step4.py` (helper `step4(conn, b)`: b's expected step 1 brief →
      `app.step2_best_style` → `app.step3_deviations` → `app.step0_profile(null)` →
      `app.step4_targets`, as `tests/test_step3.py::step3` builds steps 2 and 3):
      `test_a2_cases` (b01 IBU 66.25, b09 IBU 18.75, b06 mash 64.5, b03 mash 68.5, b19 OG >
      1.100 and ABV ≤ 10.0); `test_b11_conflict` (A3: mash 66.5 `midpoint`, no `attenuation`
      knob, one conflict naming dry, full and chewy); `test_batch_and_stated` (A4: b08 IBU 50 and 10 L, b13 15 L, b15 23 L, b01 20 L and b19 10 L `stated`,
      b17 ABV 7, b18 SRM 20 with `guidance` false, the 17 others 20 L `profile`);
      `test_targets_inside_range` (A1: b01–b22, every target inside the range of the style used
      unless `stated`, or OG/FG `derived` from a stated ABV); `test_b12_base_style` (A6: style
      18A `base_style`, targets inside 18A's ranges); `test_every_value_has_from` (A10);
      `test_same_input_same_output` (all 22 twice); `test_output_meets_contract` (all 22).
- [x] Run `.venv/bin/pytest tests/test_step4.py tests/test_contracts.py`, expect all pass;
      then `.venv/bin/pytest`. `docs/DATABASE.md` §5 line. PROJECT.md §8 entry.
Done when: the step 4 tests and the contract tests pass.
Commit: `Add the step 4 targets output and contracts`

### Task 5: rule 9 accepts what step 4 produces
Why: R11; A11. Rule 9 must not reject step 4's targets in M6.
- [x] `db/032_formulation_check.sql` `app.check_rule_9`, rewritten in place (header Needs adds
      `039_step4.sql`): when guidance is off, pass as today. Else
      `expected := app.step4_numbers(style_code, stated, recipe->'hints')`; for `og`, `fg`,
      `ibu`, `srm` not stated (OG and FG count as stated when ABV is stated, as today), fail when
      `|target − expected.value| > midpoint_tolerance.<k>`, message "Rule 9: the IBU target 55
      was not stated and is not 66.25 (bitter: 87.5 % of 21A IBU 40–70), within 1."; a null
      expected value goes to `missing` as today. ABV: fail when
      `|targets.abv − app.abv(targets.og, targets.fg)| > midpoint_tolerance.abv`. Pass message:
      "Rule 9: every target the user did not state is where step 4 puts it."
- [x] `db/031_formulation_rules.sql` rule 9 sentence (still built with `format()` from every
      `midpoint_tolerance` value): with guidance on, an unstated OG, FG, IBU or SRM is the
      style's midpoint, moved by the request's hints to 87.5 % (up) or 12.5 % (down) of the
      range, with OG moved inside its range as far as needed for the ABV from OG and FG to reach
      the ABV range; within the tolerances; OG and FG count as stated when the ABV is stated;
      the ABV target is app.abv of the OG and FG targets within the ABV tolerance; a target is
      outside the range only when stated or guidance is off.
- [x] `shared/contracts/formulation_check.input.schema.json`: required `hints`, the
      `step1.output` hints array (same enum, unique). `tests/test_contracts.py` `CHECK_IN` gets
      `"hints": []`.
- [x] `tests/fixtures/reference_recipes.toml`: each recipe gets `hints` = its brief's hints;
      `targets` become step 4's (`app.step4_numbers(style_code, stated, hints)`, values as
      returned; stated ones unchanged); header comment updated ("targets: step 4's targets for
      the brief's stated numbers and hints"). Nothing else changes.
      `tests/test_reference_recipes.py`: `build_input` passes `hints`;
      `test_recipe_follows_its_brief` asserts `rec["hints"] == brief["hints"]`.
- [x] Apply 031 and 032 twice.
- [x] `tests/test_formulation_check.py`: `recipe()` base gets `"hints": []` and an ABV target
      equal to `app.abv` of its OG and FG; `test_rule_9` keeps its cases (stated ABV, unstated
      IBU off midpoint fails, stated IBU passes, guidance off passes, OG tolerance) and gains
      (A11): 18A + `bitter` with IBU at 87.5 % passes; the same with IBU at the midpoint fails
      and the message names "bitter"; 15A with the OG moved for ABV 3.8 passes; an ABV target 0.3
      away from `app.abv(og, fg)` fails. `tests/test_formulation_rules.py` keeps passing (each
      tolerance in the sentence).
- [x] Run `.venv/bin/pytest tests/test_formulation_check.py tests/test_formulation_rules.py
      tests/test_reference_recipes.py tests/test_contracts.py`. **If a reference recipe fails
      any rule**, do not change its ingredients or process: stop and report `needs-input` with
      each failure (brief, rule, message) for the user to decide (R11).
- [x] Run `.venv/bin/pytest`, expect all pass. `docs/DATABASE.md` rule 9 note. PROJECT.md §8
      entry with the re-check result (22 recipes, which targets changed).
Done when: rule 9 tests pass and all 22 reference recipes pass every rule, or the failures are
reported.
Commit: `Align rule 9 with step 4 targets`

### Task 6: step 5 builds the design frame
Why: R10, R12; A8, A9, A10 at SQL level.
- [x] `db/041_step5.sql` (header as `db/037`; needs `031`, `032` (`app.mash_attenuation`),
      `036`, `039`):
      - `app.step5_refs(word text) returns jsonb`, stable: `app.resolve_ingredient(word)` rows as
        `[{ingredient_id, kind, name, role, max_pct}]` (`role`, `max_pct` from
        `ref.fermentable`, null for other kinds or when unset), ordered as the resolver orders.
      - `app.step5_attenuation(targets jsonb) returns jsonb`, stable, from step 4's output:
        `needed_pct` = 100 × (OG − FG) / (OG − 1); `low_pct`, `high_pct` the same at rule 10's FG
        range (the style's FG range, or target FG ± `midpoint_tolerance.fg` when the ABV is
        stated) at the target OG; `mash_c` step 4's; `yeast_middle_pct` (and low/high) = each
        of those + `mash_slope_pct_per_c` × max(0, mash − `mash_knee_c`) from
        `app.formulation_limits()`: the middle of a yeast's `attenuation_pct` range that
        `app.mash_attenuation` turns into it at that mash. Values rounded to 2; `from: derived`,
        `because` naming the formula and Troester's curve. Null OG or FG → nulls, `from: none`.
        Comment: fermentability (lactose, sugar) is rule 10's business in M6, not assumed here.
      - `app.step5_frame(brief jsonb, profile jsonb, targets jsonb) returns jsonb`, `plpgsql
        stable`, commented: `style_code` (step 4's); `rules {from: "app.formulation_rules()
        (db/031)", rows: [{rule, checked, sentence}]}`; `limits {from, values:
        app.formulation_limits()}`; `slots`: per `brief.wanted` item in order `{item,
        wanted_role, refs: app.step5_refs(item), from}` (`from` "wanted in the request", or "not
        in the catalogue" when `refs` is `[]`); `excluded`: per word `{word, refs, from}`;
        `inventory`: brief words `from: request`, then profile inventory rows `from: profile`
        (refs from the row's `ingredient_id` when set); `intents`: step 4's knobs that have an
        intent, `{hints, knob, intent, source, from: "hint"}`; `attenuation`; `guidance`.
- [x] Contracts `step5.input` (`run_id`, `brief`, `profile`, `targets` objects) and
      `step5.output` (`additionalProperties: false` throughout; the only numbers are ids,
      `max_pct`, `limits.values`, rule numbers in text and the attenuation fields).
      `tests/test_contracts.py`: `ABSENT_SLOTS["step5.output"] = [("slots.refs", "array"),
      ("attenuation.needed_pct", "null")]`, GOOD and BAD examples (an extra `grist` key; a slot
      without `refs`).
- [x] Apply twice.
- [x] Write `tests/test_step5.py` (helper `step5(conn, b)` on top of `step4`): `test_slots`
      (A8: b02 oats → Flaked Oats adjunct 30; b06, b16 rice → Flaked Rice; b07 corn → Flaked
      Corn; b12, b19 honey → Honey sugar 20; b20 lactose → Lactose sugar 10; each `wanted_role`
      the brief's); `test_excluded_and_inventory` (b08 Saaz, b16 Citra and Mosaic with their hop
      ids; b10's three words and b15's three present, "dark candi sugar" with `refs []` and
      "not in the catalogue"); `test_intents` (b02 late and dry hop share; b03 lower-attenuation
      and oats; b06 high-attenuation and sugar at most 10 %; b09 kilned share; b11 no
      attenuation intent); `test_rules_equal_formulation_rules`; `test_no_ratio_numbers` (A8:
      walk every b01–b22 frame; no key other than an allowed list holds a number; no key named
      `pct` or `grist` or containing `split`); `test_needed_attenuation` (A9: for b01–b22,
      `needed_pct` = 100 × (OG − FG)/(OG − 1) of step 4 within 0.01, and
      `app.mash_attenuation(numrange(m − 3, m + 3), mash_c)` with m = `yeast_middle_pct` is within
      0.01 of `needed_pct`); `test_every_value_has_from` (A10); `test_same_input_same_output`;
      `test_output_meets_contract`.
- [x] Run `.venv/bin/pytest tests/test_step5.py tests/test_contracts.py`, expect all pass; then
      `.venv/bin/pytest`. `docs/DATABASE.md` §5 lines. PROJECT.md §8 entry.
Done when: the step 5 tests pass.
Commit: `Add the step 5 design frame in SQL`

### Task 7: graders score steps 4 and 5
Why: G4, A13; the bar is checked at SQL level before the pipeline run.
- [x] `evals/grade.py` (pure, no I/O; docstring updated):
      - `grade_step4(brief, output, facts) -> bool`, `facts = {"ranges": {og, fg, abv, ibu,
        srm: [lo, hi] | None} of output.style.code, "abv": app.abv(target og, fg)}`: style code
        is the brief's style, or with `from: base_style` the brief's first `alt_styles` code;
        batch as R3; each target equals a stated number with
        `from: stated`, else is inside its range, or is OG/FG `derived` while ABV is stated;
        each hint of the brief not in an expected conflict: up knobs in the top quarter, down in
        the bottom quarter (G4), unless stated or OG `derived`; mash 64.5 for dry/crisp, 68.5 for
        full/chewy, 66.5 with none or a conflict; `facts.abv` within 0.1 of the ABV target and
        inside its range unless stated; every expected conflict in `conflicts`
        (`deviation_matches`); every value's `from` non-empty. A small `HINT_KNOBS` dict
        (hint → knob, direction) beside `HINT_ROWS`, comment: kept apart from the SQL table on
        purpose, so the grader checks it.
      - `grade_step5(brief, output, step4, facts) -> bool`, `facts["rules"]` the rows of
        `app.formulation_rules()`, `facts["band_attenuation"]` = `app.mash_attenuation` at
        `yeast_middle_pct ± 3`: a slot with non-empty refs per wanted item; every excluded and
        inventory word present (by `normalise`); an intent for each brief hint of hoppy, juicy,
        dry, crisp, full, chewy, malty, darker unless it is in an expected conflict; rules equal;
        `needed_pct` = 100 × (OG − FG)/(OG − 1) of step 4 within 0.01 and `band_attenuation`
        within 0.01 of it.
      - `grade_run(brief, steps, facts=None)` adds `step4`, `step5`; `passed` needs all.
- [x] `evals/run.py`: `GRADED_STEPS = (2, 3, 4, 5)`; `read_facts(conn, steps)` builds the facts
      with three queries; `grade_result`, `table` and `totals` show steps 4 and 5.
- [x] Tests: `tests/test_grade.py` (not stack, hand-built outputs): `test_step4_right_passes`,
      `test_step4_hint_not_moved_fails`, `test_step4_out_of_range_fails`,
      `test_step4_stated_abv_og_outside_passes`, `test_step4_conflict_missing_fails`,
      `test_step5_right_passes`, `test_step5_missing_slot_fails`,
      `test_step5_wrong_attenuation_fails`; `test_grade_run_combines_steps` extended.
      `tests/test_run.py`: the existing tests updated for four graded steps.
      `tests/test_step5.py::test_briefs_reach_the_bar` (stack, SQL level: the Task 6 chain plus
      `read_facts`; `grade_step4` and `grade_step5` pass on 20/20 of b01–b20 and on b21, b22;
      the failure message lists each miss).
- [x] Run `.venv/bin/pytest tests/test_grade.py tests/test_run.py tests/test_step5.py`. If the bar
      test fails, find the cause; a fix may change a rule only in a general way (never for one
      brief), each as a dated Deviations line; if that does not reach the bar, stop and report
      `needs-input` with the misses.
- [x] Run `.venv/bin/pytest`, expect all pass. PROJECT.md §8 entry with the SQL-level count.
Done when: the grader tests pass and the SQL-level bar is 20/20 plus b21, b22.
Commit: `Grade steps 4 and 5`

### Task 8: the pipeline runs steps 0, 4 and 5 and logs them
Why: R13; A13 (logged). Load the n8n skills first (`using-n8n-skills-official`,
`n8n-workflow-lifecycle-official`, `n8n-node-configuration-official`,
`n8n-error-handling-official`) and follow the MCP order: SDK reference → `get_node_types` →
validate → create / update → check `connections` → publish. Publish each sub-workflow before the
pipeline that calls it (OPERATIONS §5). Nodes with `onError` go in through the JSON file and
`n8n import:workflow` (OPERATIONS §5; the MCP drops `onError`).
- [x] Three sub-workflows, each a copy of `Step 3 · deviations`' shape (trigger *When Executed by
      Another Workflow* → "Check step N input" → *Postgres* → "Check step N output" → "Return
      result", sticky note saying it writes nothing and calls no LLM, `Test data` note):
      - `Step 0 · load profile`: inputs `run_id`, `profile_id`; query
        `select app.step0_profile(($1::jsonb ->> 'profile_id')::bigint) as result` with
        `JSON.stringify({profile_id: $json.profile_id ?? null})` (a null input arrives missing,
        OPERATIONS §5).
      - `Step 4 · targets`: inputs `run_id`, `brief`, `style`, `profile`, `deviations`;
        `select app.step4_targets($1::jsonb, $2::jsonb, $3::jsonb, $4::jsonb) as result`.
      - `Step 5 · design frame`: inputs `run_id`, `brief`, `profile`, `targets`;
        `select app.step5_frame($1::jsonb, $2::jsonb, $3::jsonb) as result`.
- [x] `Recipe pipeline` (`eMkkdBar6NIqUa1g`): `Run settings` gets `profile_id` (body field,
      default null). `Start run` → "Step 0 · input" → "Step 0 · load profile" (`onError:
      continueErrorOutput`) → "Step 0 · log ok" (`app.run_step` step 0, try 1) → "Step 1 ·
      input"; error → "Step 0 · log failure" → "Finish run (failed, step 0)" → "Respond failed
      (step 0)" with `failed_step: 0`. After "Step 3 · log ok": step 4 and step 5 blocks of the
      same shape (inputs from the named nodes' outputs), then `Finish run`. Update the per-step
      sticky note.
- [x] Validate, import / update, check `connections`, publish all four.
      `.venv/bin/python -m evals.workflows`; read the diff: no secrets, only the intended nodes.
- [x] Tests: `tests/test_workflows.py` `SAMPLES`, `CONTRACT_OF`, `STEP1_INPUT` for the three new
      files (step 4 and 5 samples from the step 3 sample's brief and style, with
      `tests/step3_sample_style.json`). `tests/test_pipeline.py`: `test_b01_logs_step_1`
      expects steps `[0, 1, 2, 3, 4, 5]`; new `test_step_0_logged`, `test_step_4_logged`,
      `test_step_5_logged` (row `ok`, `ms >= 0`, input as the block sends it, output meets its
      contract); `test_profile_id_reaches_step_0` (an unknown `profile_id` fails at step 0 with
      `failed_step: 0`); the step 2 failure test expects `[0, 1, 2]`.
- [x] Run `.venv/bin/pytest`, expect all pass.
- [x] `docs/OPERATIONS.md` §5: eight workflows to publish; the webhook body's `profile_id`; the
      three new workflows in the editor-run list. PROJECT.md §4 Orchestration row (8 workflows,
      steps 0–5 logged) and §8 entry.
Done when: all four workflows run published, their files match n8n, and the pipeline tests pass.
Commit: `Run steps 0, 4 and 5 in the pipeline`

### Task 9: G4 is measured on the real pipeline
Why: G4; A13.
- [x] `.venv/bin/python -m evals.run --save --label m4` (stack up, D2 model). Count b01–b20 with
      steps 4 and 5 passing; report b21, b22 and steps 1–3 beside it (bar: steps 1–3 22/22 as at
      G3). A step 4 or 5 miss not seen at SQL level (Task 7) comes from step 1's output: name
      the field.
- [x] Check on the saved run: every step 0, 4 and 5 row is `ok` and meets its contract (one
      `psql` query with `extensions.jsonschema_validation_errors`).
- [x] **If the bar is not met:** fix only in a general way as in Task 7, re-run, record each
      change in Deviations; else stop and report `needs-input` with the misses. The bar is not
      lowered.
- [x] `docs/WORKFLOW-ROADMAP.md`: G4 **Measured** line (counts, A2 cases, results file) and
      **Decided** line left for the user; M4 row text "blueprint (ratios)" → "design frame".
      `docs/RECIPE-ROADMAP.md` §3: step 4 and step 5 rows of the step table and the step 5 box
      of the flow describe what was built (design frame, no ratios). PROJECT.md §8 entry with the
      measured numbers.
- [x] Commit `evals/results/<date>-m4.json`.
Done when: the saved run shows steps 4 and 5 passing on 20/20 of b01–b20 and on b21, b22, steps
1–3 no worse than G3, and the docs carry the measured numbers.
Commit: `Measure G4 for steps 0, 4 and 5`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| The default profile holds the agreed numbers and ions, and a re-run never overwrites user values | `tests/test_step0.py::test_default_profile`, `::test_rerun_keeps_user_values` | 1 |
| Every hint row moves its knob by the agreed amount and has a source or `unsourced` | `tests/test_step4.py::test_hint_positions`, `::test_hint_rows_sourced_or_marked` | 2 |
| Step 3's conflicts still work on the extended table | `tests/test_step3.py` (unchanged) | 2 |
| A hint moves its target to the quarter middle; a stated number wins; opposite hints leave the default | `tests/test_step4.py::test_hint_moves_ibu`, `::test_stated_wins`, `::test_conflicting_hints_leave_default` | 3 |
| ABV comes from `app.abv`; OG moves just far enough; a stated ABV solves OG; rounding keeps ABV in range | `::test_og_for_abv_inverts_abv`, `::test_stated_abv_solves_og`, `::test_abv_out_of_range_moves_og`, `::test_derived_abv_inside_range` | 3 |
| Batch, base style, b11 conflict and the A2 numbers in the step 4 output | `::test_a2_cases`, `::test_b11_conflict`, `::test_batch_and_stated`, `::test_b12_base_style`, `::test_targets_inside_range` | 4 |
| Every value says where it came from | `tests/test_step4.py::test_every_value_has_from`, `tests/test_step5.py::test_every_value_has_from` | 4, 6 |
| Rule 9 accepts step 4's targets and still rejects an unstated, unhinted or misplaced one | `tests/test_formulation_check.py::test_rule_9` | 5 |
| The 22 reference recipes pass every rule | `tests/test_reference_recipes.py` | 5 |
| The frame names wanted, excluded and inventory products with role and `max_pct`, and holds no ratio numbers | `tests/test_step5.py::test_slots`, `::test_excluded_and_inventory`, `::test_no_ratio_numbers` | 6 |
| Needed attenuation and the yeast band agree with `app.mash_attenuation` | `::test_needed_attenuation` | 6 |
| Outputs meet their contracts and are deterministic | `test_output_meets_contract`, `test_same_input_same_output` in `test_step0/4/5.py` | 1, 4, 6 |
| G4 bar at SQL level | `tests/test_step5.py::test_briefs_reach_the_bar` | 7 |
| Steps 0, 4 and 5 are logged with input, output and time | `tests/test_pipeline.py::test_step_0_logged`, `::test_step_4_logged`, `::test_step_5_logged` | 8 |

## Approved exceptions

## Deviations
- 2026-10-17 · Task 8: the three new sub-workflows were authored as JSON files and imported with `n8n import:workflow` (fixed ids `ST0loadprofile01`, `ST4targets00001x`, `ST5designframe01`), then published, rather than built through `create_workflow_from_code`; the plan allows the file route for `onError` and it keeps the files as the source. `Step 1 · input` now reads `run_id` from `Start run` (it came from the previous node). Test samples for steps 4 and 5 use `tests/step45_sample.json` (profile, deviations, targets for the step 3 sample).
- 2026-10-17 · Approach: the three readings of the brief (A4 batch sizes, A1 solved OG, R11
  reference re-check with the ABV check) confirmed by the user, option a each; brief updated.
- 2026-10-17 · Task 2: the column is declared and read as `"position"` (quoted) — `position` is a SQL keyword and a bare name is a syntax error in the return type and the alias list.
- 2026-10-17 · Task 3: added helper `app.step4_pick` (one range-based target) beside the planned functions, and `app.step4_numbers` names its list parameter `hint_list` — a plpgsql parameter named `hints` clashes with the `hints` column of `app.hint_moves`; callers pass it by position.
- 2026-10-17 · Task 4: `tests/test_contracts.py` `NAMES` covers steps 0–4 now, not 0–5 — step 5's contract files are written in Task 6, and the file-completeness test needs every name to exist; Task 6 adds step 5.
- 2026-10-17 · Task 6: added helper `app.step5_refs_of_id` (refs for a profile inventory row's `ingredient_id`); a brief word that resolves to nothing gets `from: not in the catalogue` in `excluded` and `inventory` as in `slots` (found: `request`); attenuation fields are `needed_pct`, `low_pct`, `high_pct`, `mash_c`, `yeast_middle_pct`, `yeast_low_pct`, `yeast_high_pct`; `step5_frame`'s `targets` is the whole step 4 output — the plan left these shapes open.
