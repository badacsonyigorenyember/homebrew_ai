# M7 · Steps 12–15: water, mash and boil, fermentation, packaging — implementation plan

Stage: implementing
Brief: [brief.md](brief.md)
Branch: m7-process

## Approach

- **Doc → calc first, then one SQL function per step.** Task 1 reads the sources and writes
  [`doc-calc.md`](doc-calc.md): every formula, table and constant steps 12–15 use, with book,
  chapter and page, and the two new mapping tables (style → *Water* Table 18/19 row, style →
  *How to Brew* CO₂ family). You review it before anything is loaded (gate). Then each step is one
  SQL function built from small tested helpers: `app.step12_water`, `app.step13_mash_boil`,
  `app.step14_ferment`, `app.step15_package` (R1, CLAUDE.md: no LLM in any of them). Constants
  without a source are marked `unsourced` in `doc-calc.md` and in the step output (the m4 hint
  table did the same), and listed for you at the gate.
- **Inputs are what the pipeline already has after a passed try.** Step 10's output (amounts,
  `mash_c`, `boil`, `ferm_c`, `numbers`, `batch`), step 4's `targets` (`targets.style.code` is
  the base style for a specialty code, e.g. 30A → 20B, measured on b23's step 4 row), step 1's
  brief (`hints`) and step 0's profile (six ions, volumes, `grain_abs_l_kg`). Nothing from step 10
  is decided again: step 13 copies `mash_c` and `boil.boil_min` (R3, A7).
- **Volumes come from one helper both steps call.** `app.water_volumes(profile, step10)` gives
  strike, sparge and total water (decision 5): total = `app.preboil_volume` (s1) + mashed grain kg ×
  `grain_abs_l_kg`; strike = mashed kg × the water-to-grist ratio from `doc-calc.md` (*How to
  Brew* uses 3 L/kg in its single-infusion example; the doc-calc pass fixes the figure); sparge =
  total − strike, and when that is below 0, strike = total and sparge 0 (said in `because`).
  Sugars (`role = 'sugar'`, not mashed) count in neither. Step 12 doses salts for these volumes and
  step 13 outputs them, so A12 compares one function's numbers.
- **Step 12 water, in this order** (decision 1, 2; `doc-calc.md` confirms each line and its page):
  1. Target row: `ref.beer_style.water_profile` of `targets.style.code` (a *Water* Table 18a/b or
     19a/b row). A style with no row gets `target.from = "none"` and no salts (decision Q1).
  2. Aim inside the row's ranges: sulfate and chloride at the middle of their ranges; a
     sulfate-side hint (`bitter`, and whatever else `doc-calc.md` sources, e.g. `dry`, `crisp`)
     moves sulfate to 87.5 % and chloride to 12.5 % of their ranges, a chloride-side hint
     (`malty`, `full`, …) the other way, both sides at once leave the middle and say so (the 87.5 /
     12.5 positions are RECIPE-ROADMAP §7's, the user's 2026-10-17 decision).
  3. Gypsum for sulfate and calcium chloride for chloride, each `(aim − source) / ion mg per g/L`
     from `ref.water_salt`, never below 0. If calcium is then below the row's minimum, both salts
     rise in their proportion until it is reached or sulfate or chloride hits its maximum (then
     "calcium below the row" is said; HTB Table 8.1 / p. 135 caps: sulfate ≤ 400, chloride ≤ 150,
     together ≤ 500). Calcium above the row's maximum, which the sulfate and
     chloride aims can cause, is reported in the output and not corrected. No magnesium salt (*Water* ch. 7: the tables give no Mg,
     the malt supplies it).
  4. Residual alkalinity (Kolbach, HTB p. 342: RA = alkalinity − Ca/1.4 − Mg/1.7, ppm as CaCO₃).
     Alkalinity follows the **grist**, not the row's RA (outside review 2026-10-28): it is added to
     the strike water only, baking soda while sodium stays at or below 100 mg/L (HTB Table 8.1), slaked
     lime for the rest (*Water*'s Foreign Extra Stout example; chalk is not used), until item 6's pH
     estimate reaches the bottom of item 7's colour target (`doc-calc.md` §6). The row's alkalinity and
     RA ranges are reported references (`outside_row` note), never dosing targets (HTB p. 350, 363).
     At or above the bottom of the target nothing is added; above the top the acid line says acid
     would be needed.
  5. Grams per water: gypsum and calcium chloride at the same g/L in strike and sparge water,
     alkalinity salts in the strike water only; each rounded to 0.1 g, ions recomputed from the
     rounded grams. Output both waters' ions, alkalinity and RA.
  6. Mash pH estimate, *How to Brew* ch. 21's zero-sum method (p. 349–350; not the full titration
     curves, brief Out): pH = 5.4 + Σ mEq / (40 × grist kg), where each mashed fermentable adds kg ×
     its alkalinity (+) or acidity (−) to pH 5.4 from HTB Table 21.4 (nearest-°L row; one roast
     class; flaked and unmalted adjuncts count as base, Bru'n Water) and the strike water adds
     litres × RA in mEq/L; 40 mEq/(pH·kg) is HTB p. 342's 200/Rv rule of thumb. `doc-calc.md` §7.
  7. Acid line (decision 2): the estimate against HTB's mash pH target for the row's colour (p. 341,
     365: pale 5.2–5.4, amber 5.3–5.5, brown/black 5.4–5.6; no row 5.2–5.6; brief A10 question).
     Above the upper bound → `acid.needed` true with "acid would be needed to bring the mash from
     5.xx into x–y", plus the row's "Acidify" flag. No acid amount anywhere (A10).
- **Step 13 mash and boil** (decision 3): mash steps are any neutral rest a source ties to the
  recipe, the single infusion at `step10.mash_c`, and a mash-out (*How to Brew* ch. 16: 77 °C).
  Neutral rests, each with its source and only below the starch range, so rule 10's FG model is
  unchanged: ferulic acid rest (40 °C, 30 min, *How to Brew* ch. 17) for the styles `doc-calc.md` ties it to (German wheat
  beers 10A–10C), beta-glucan rest (45 °C, 20 min) when `role =
  'adjunct'` (flaked grains) is above 20 % of the grist (*How to Brew* ch. 16), protein rest only
  where the doc-calc pass finds a rule our data can test. The boil is `step10.boil` as is; the
  addition schedule lists every boil and whirlpool hop and every mash, boil and whirlpool extra of
  step 10, in time order (largest boil minute first, then whirlpool). Dry hops and fermentation
  extras go to step 14, packaging extras to step 15. The strike water temperature comes from
  *How to Brew* ch. 17's single infusion equation, Tw = (0.4 ÷ (0.985 × r))(T₂ − T₁) + T₂ in its
  metric form (r = `ratio_l_kg`, T₂ = the first mash step's temperature, T₁ = the grain temperature
  `doc-calc.md` §8 fixes; decision Q2, brief R3 as revised 2026-10-28).
- **Step 14 fermentation** (R4; *How to Brew* first, `doc-calc.md` §11): the main temperature is
  step 6's `ferm_c`, raised to at least the yeast range's lower bound + 1 °C. Ale start 1–2 °C
  below it (HTB p. 90), lager start at it (HTB p. 174). Maturation rest from HTB Table 6.2: ales
  raise 3 °C for at least 4 days, lagers raise 8 °C (capped at the yeast's upper bound, so A4 holds
  for every lager yeast in `ref`) for at least 6 days. The days are minimums: each step carries
  `move_on` text with HTB's trigger (the rest starts when gravity is within 2-5 points of FG, Table 6.2;
  souring ends at about pH 3.5, p. 211); then dry hops (HTB p. 72: 3 days, 14 °C), and
  cold conditioning (ales: 5–8 °C below the fermentation temperature, a week) or lagering (lagers:
  2 °C, 14 days). Secondary extras: day and contact time from their `ref.misc` row (`time_min`; none →
  "until it tastes right", `unknown`). A souring culture (b14): pre-souring in the fermenter after
  the boil at 35 °C (the overlap of HTB's 32–46 °C and the culture's `temp_c`) for 1.5 days (HTB
  p. 211), then the main yeast. Phase names say which steps are fermentation: A4 checks `souring`,
  `ferment` and `rest` steps against their yeast's range; `crash`, `lager` and `dry_hop` are
  conditioning below any yeast's range.
- **Pitch rate** (*How to Brew* ch. 7): cells = rate × wort litres × °P, rate 1.5 billion/L/°P for lager
  yeasts and 0.75 for the rest (fresh yeast), wort = the batch volume, °P = `app.sg_to_plato(og)`. Dry
  yeast: grams = cells ÷ 10 billion viable cells per gram (HTB p. 108), rounded up to 1 g; liquid:
  packs = cells ÷ 100 billion, rounded up. These generic HTB cell counts (10 billion per gram, 100 billion per pack, the 150 billion
  souring midpoint) are labelled estimates, not the maker's spec, in the yeast line's `because`. This replaces step 10's `1 pack` in the saved yeast rows
  (A7). The souring culture (`type = 'lacto'`) is pitched at HTB p. 206's rate, 150 billion cells per
  19 L scaled to the batch, in 100-billion packs, and the main yeast then uses 1.0 billion/L/°P (HTB
  p. 212); decision Q3 as revised 2026-10-28.
- **Step 15 packaging** (R5): CO₂ volumes = the middle of `ref.beer_style.co2_vol` (the style's
  *How to Brew* p. 159 family); a style with none uses 2.5 volumes, Palmer's "medium carbonation"
  (p. 155), marked `from: default` (decision Q1). Priming sugar (table sugar) grams = (target − residual
  CO₂) × batch L × (342.3 ÷ 4) ÷ gas volume, with residual CO₂ and gas volume from Table 10.3's row
  for the highest beer temperature after fermentation (*How to Brew* p. 159: the residual is set
  by that temperature), which step 14 outputs. Packaging extras with their grams.
- **Saving** (R6): the pipeline runs steps 12–15 after a passed try and before saving, so a
  failure there saves nothing. `app.recipe_process(step10, step12, step13, step14, step15)`
  builds the saved object `{water, mash, boil, fermentation, packaging}` and raises when its mash
  or boil differ from step 10's (A7); `app.save_recipe` gains `process jsonb default null`, writes
  `app.recipe.process` and takes the yeast amounts from step 14's pitch. The default keeps stage
  D's tests and callers working.
- **n8n:** a sub-workflow `Steps 12–15 · process` (contract checks around the four SQL calls and
  `app.recipe_process`, one log row per step, `try` 1), called by the pipeline between `Try n
  passed?` and `Save recipe`, with its own failure finish (`failed_step` 12–15).

**Measured while planning (2026-10-27, read-only, nothing written):**
- `ref.water_salt`: 8 salts, ions in mg/L per g in 1 L (`water-salts` plan). They reproduce
  *Water*'s Table 17 per-gallon figures: calcium chloride 272.6 / 3.785 = 72.0 mg/L Ca and 127.4
  Cl per g/gal, gypsum 61.5 Ca and 147.4 SO₄, slaked lime ΔRA 19.3 mEq per g/L. So the book's
  Pilsner example (30 ppm Ca in 10 gal → 4.17 g calcium chloride, 53.5 ppm Cl), its American pale
  ale option 1 (RA 44 at 101 ppm Ca, 9 at 150) and its Foreign Extra Stout option 1a (0.087 g/L
  slaked lime for ΔRA 1.68 mEq/L) are all checkable with `ref` as it is.
- *Water* Tables 18a/b (6 lager rows) and 19a/b (10 ale rows) are in the PDF text with Ca,
  alkalinity, sulfate, chloride, Kolbach RA, Acidify and a style list per row; strength, colour and
  bitterness bands are defined above them (Light OG 30–45 … Strong 65+; Pale 0–9 SRM … Black 35+;
  Soft 10–20 IBU … Assertive 36–100). Some cells are one number (light lager Ca "50", a minimum,
  per the Pilsner example) and some rows have a bracketed outlier (Dortmunder Export); Task 1
  says how each is stored.
- *How to Brew* Table 10.3 (5–30 °C rows: gas volume, residual CO₂, g/L sucrose for 1.5–4.5
  volumes) and the p. 159 family list (8 families) are in the text. (2.5 − 0.80) × 19 × 3.49 = 113 g
  and with corn sugar (÷ 0.91 × 3.68) 131 g: Table 10.1's two figures.
- *Yeast*: pitch rates 0.75 / 1.5 million cells per mL per °P and the worked example (0.75 × 20 000
  mL × 12 °P = 180 billion); dry yeast 7–20 billion cells/g; "the average liquid yeast package for
  homebrewers has about 100 billion cells"; diacetyl rest 18–20 °C for two days; the ramp
  (1–2 °C below, rise over 18–36 h, +2–5 °C over the last third).
- `ref.yeast` lager ranges: 17 rows, upper bounds 13–20 °C (10 of them at or below 15 °C), so a
  fixed 18 °C diacetyl rest would leave A4; hence the rest at the upper bound. Lacto (YF-998,
  YF-999) 15–35 °C, liquid. 3 yeasts have no `type`.
- `ref.fermentable` has no grain-species column: flaked barley, corn, oats and rice are `role =
  'adjunct'`; malted wheat and rye are `base`. The beta-glucan rule therefore reads the role
  (corn and rice included: a harmless rest below the starch range).
- Step 4 `targets.style.code` is the base style for specialty codes (b23 30A → 20B, "step 2's first
  alternative"). The styles step 4 uses for b01–b24 and h01–h06 are about 30 codes, listed in
  Task 1; `ref.beer_style` has 285 (BJCP 116 in 34 categories, BA 169 in 10).
- `app.brewer_profile` `default`: all ions 0, 20 L, boil-off 4 L/h, losses 2 L, absorption 1.0
  L/kg; no water-to-grist ratio and no water pH column.
- `app.recipe_item.usage` already allows `mash` and `sparge`; units `g` and `pack` exist, so
  dry yeast in grams needs no schema change.
- Pipeline: `Try 1/2/3 passed?` → `Save recipe` (`select app.save_recipe($1..$5)`) → `Finish run`
  → `Respond ok`. `tests/test_contracts.py` `NAMES` covers `step0`–`step11`.

**Context7 not used:** no library question in this plan; n8n behaviour comes from the repo's
existing workflows and OPERATIONS §5.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `docs/work/m7-process/doc-calc.md` | new | Task 1: the doc → calc pass, the two mapping tables, the schedule constants |
| `db/049_process_ref.sql` | new | `ref.water_profile` (Tables 18–19 and `web-berliner-weisse`), `ref.beer_style.water_profile`, `water_basis`, `co2_vol`, `co2_family`, `co2_basis` |
| `db/050_water.sql` | new | `app.salt_ions`, `app.residual_alkalinity`, `app.water_volumes`, `app.water_aim`, `app.salt_additions`, `app.alkalinity_dose`, `app.malt_acidity`, `app.mash_ph_estimate`, `app.step12_water` |
| `db/051_mash_boil.sql` | new | `app.mash_rests`, `app.strike_temp`, `app.step13_mash_boil` |
| `db/052_ferment.sql` | new | `app.pitch_rate`, `app.ferment_schedule`, `app.step14_ferment` |
| `db/053_package.sql` | new | `app.residual_co2`, `app.priming_sugar_g`, `app.step15_package` |
| `db/048_save_recipe.sql` | changed | `app.recipe_process`; `app.save_recipe(..., process jsonb default null)` |
| `shared/contracts/step12.{input,output}.schema.json` … `step15.*` | new | the four steps' contracts |
| `shared/contracts/process.input.schema.json`, `process.output.schema.json` | new | the sub-workflow input; the saved `app.recipe.process` object |
| `n8n/workflows/steps-12-15-process.json` | new | sub-workflow `Steps 12–15 · process` |
| `n8n/workflows/recipe-pipeline.json` | changed | steps 12–15 between the tries and the save; their failure finish |
| `tests/step1215_sample.json` | new | the sub-workflow's `Test data` |
| `tests/test_process_ref.py`, `test_water.py`, `test_mash_boil.py`, `test_ferment.py`, `test_package.py`, `test_save_process.py` | new | Tasks 2–8 |
| `tests/test_contracts.py`, `test_workflows.py`, `test_pipeline.py`, `test_save_recipe.py`, `test_recipe_briefs.py`, `test_grade.py`, `test_run.py` | changed | as each task says |
| `evals/recipe_briefs.toml`, `evals/heldout_briefs.toml` | changed | `process` expectations (R7) |
| `evals/grade.py`, `evals/run.py`, `evals/show_recipe.py` | changed | grade and print `process` |
| `evals/results/<date>-m7.json` | new | the full brief run (A2, A6) |
| `docs/RECIPE-ROADMAP.md`, `docs/WORKFLOW-ROADMAP.md`, `docs/DATABASE.md`, `docs/OPERATIONS.md`, `docs/BOOKS.md`, `docs/SOURCES.md` | changed | Task 12 |
| `PROJECT.md` | changed | §4, §5 rows, §8 per task |

Apply command for every SQL file (OPERATIONS §4), run twice to show it is idempotent, then check
owners with `select proname, pg_get_userbyid(proowner) from pg_proc where pronamespace =
'app'::regnamespace and proname = any(<names>)` (all `postgres`; tables with `pg_tables.tableowner`):
`docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/<file>.sql`
Each new SQL file gets the header the others have (purpose, work folder, needs, apply command,
idempotent). Every function comment names its `doc-calc.md` section and the book page. Workflows
are imported with the n8n CLI (OPERATIONS §5: edit the JSON, copy to `shared/`,
`import:workflow`, publish through the MCP, delete the copy), the sub-workflow before the
pipeline, then `.venv/bin/python -m evals.workflows`. Tests use `tests.test_compute`'s
`step10_input` / `compute` helpers to get real step 10 outputs (b01, b08, b10, b14, b16, b23, b24
are already there; add b03, b05, b13 where a task needs them).

## Tasks

### Task 1: the doc → calc pass is written up (gate)
Why: R1, A1; brief Assumptions (8 families cover the styles, a cell count exists, Table 18–19
rows match the styles).
- [x] Read and write `docs/work/m7-process/doc-calc.md`, one numbered section per item, each with
      book, chapter, printed page and PDF page (HTB printed + 26 = PDF, `docs/BOOKS.md`), the
      formula or table, the worked example if the book has one, and what it becomes (function or
      `ref` column, test name). Use `pdftotext -layout` into the scratchpad; quote no more than a
      table needs. Sections:
      1. *Water* Table 17 / `ref.water_salt` check (Ca, SO₄, Cl per g/gal from the stored g/L).
      2. Kolbach RA (ch. 4) in ppm as CaCO₃ and mEq/L; alkalinity from HCO₃ (× 50/61.02), OH.
      3. Tables 18a/b and 19a/b: all 16 rows in full, how a single number and a bracketed outlier
         are stored (proposal: a single Ca number is a minimum `[50,)`; outliers left out and
         named), the band definitions, the Acidify meanings.
      4. **Style → row table** (reviewed by you): every style step 4 uses for b01–b24 and h01–h06
         (21A, 21C, 16B, 16A, 15B, 20C, 1B, 1C, 5D, 6A, 26B, 25B, 18A (b12's base), 10A, 23A, 11B,
         18B, 8B, 15A, 17C, 19C, session-india-pale-ale, mexican-style-amber-lager, 20B (b23's
         base), 3B, 14B, 25A, 13C, 5B, 17D; confirm with `tests.test_step4.step4` per brief, and
         add any base style it returns that is not listed), each with its row and why: the row's
         style list names it, else the bands at the style's range midpoints (OG, SRM, IBU) and
         lager or ale from the style; ties and judgement calls marked.
      5. Hints → aim (sulfate side, chloride side) with the passage for each (*Water* ch. 7 on
         sulfate and chloride; Bru'n Water *Water Knowledge*); the 87.5 / 12.5 positions.
      6. Salt order and limits (Approach step 12, items 3–5): sources for "no Mg salt", Na ≤ 100,
         lime over chalk, alkalinity in the strike water only; the three worked examples (Pilsner,
         American pale ale option 1, Foreign Extra Stout option 1a) with the numbers a test checks.
      7. Mash pH: the zero-sum method (ch. 5), Table 9 rows → classes by `role` and EBC with the
         figure each class uses (re pH 5.4: alkalinity or acidity mEq/kg, buffer mEq/(pH·kg); where
         Troester and Bies differ, the mean, said), the water term, the target range 5.2–5.6, and
         a hand-worked case (pale grist on distilled water with the light-lager aim) that A10's test
         uses.
      8. Water-to-grist ratio for the strike (HTB ch. 16–17 and *Water* Table 5's "typical near 4";
         one figure, with the reason), total water = pre-boil + absorption; the strike water
         temperature: HTB ch. 17's single infusion equation, the metric constant, the grain
         temperature used (one figure, `unsourced` if no page gives it) and the book's worked
         example with the numbers a test checks.
      9. Mash rests: ferulic, beta-glucan, protein, mash-out: temperature, minutes, trigger
         (style codes or grist fact), each with page; saccharification time.
      10. Pitch rate, cells per gram for dry yeast (one figure with the reason), cells per liquid
          pack; the worked example.
      11. Fermentation schedule per yeast type (ale and kveik, lager, souring): start offset,
          rise, hold days, end raise, diacetyl rest, crash or lagering temperature and days; any
          figure no source gives is marked `unsourced` with the value proposed.
      12. Dry hop (Janish paper and post): day, temperature, contact days. Secondary extras: day,
          contact from `time_min`.
      13. Souring (MTF Berliner and Lactobacillus pages): method (pre-souring in the fermenter after
          the boil), temperature, days, then the main yeast.
      14. CO₂: the p. 159 families; **style → family table** (reviewed by you) for the same styles
          as section 4, each with why; the default 2.5 volumes (p. 155); Table 10.3's residual and
          gas-volume columns (all 26 rows, as data); the priming formula and Table 10.1's cane and
          corn sugar figures.
      15. The BJCP 8-city table (`water/bjcp_study_guide_water.md`): which mapped style each city
          checks (Pilsen 3B, Dortmund 5D or Export, Munich 8A-type dark lagers, Vienna, Burton,
          Dublin 15B, Edinburgh, London) and what the check compares (sulfate vs chloride dominance
          and RA order between rows), as test expectations only.
      16. Bru'n Water 1.25: oracle only; whether you supply a mash-pH figure for one case (Task 3).
      17. What is not used and why (titration curves, Z alkalinity without a water pH, acid
          tables, kegging tables, starters).
- [x] Check the brief's three assumptions against what you found and write the result at the top
      of `doc-calc.md` (each: holds, or how it does not).
- [x] PROJECT.md §8 entry. Hand back `needs-approval`: sections 4, 5, 11 and 14 (the reviewed
      tables and the unsourced values) for your review, with any assumption that failed as a
      question. Do not start Task 2 before the answer.
Done when: every item steps 12–15 use is in `doc-calc.md` with a page, and you approved the
mapping tables.
Commit: `Add the m7 doc-calc pass`

### Task 2: the water rows and CO₂ volumes are `ref` data
Why: R1, R2 (target row), R5 (`co2_vol`), A9.
- [x] `db/049_process_ref.sql` (needs 010, 011): `ref.water_profile` (`code text primary key`,
      `table_no text check (table_no in ('18','19','web'))`, `beer_type` lager|ale, `strength`, `colour`,
      `bitterness`, `ca`, `alkalinity`, `so4`, `cl`, `ra` numrange, `acidify` yes|maybe|no,
      `styles text`, `source_id` → `ref.source` slug `palmer-kaminski-water`, `page text`); the 16
      rows from `doc-calc.md` §3 plus the web-sourced `web-berliner-weisse` (`table_no = 'web'`, its own
      `ref.source` row, doc-calc §4b), `on conflict (code) do update`. `ref.beer_style` gains
      `water_profile text references ref.water_profile (code)`, `water_basis` and `co2_basis` (each
      `listed|inferred|judgement|web`, a check constraint), `co2_vol numrange`, `co2_family
      text` (`add column if not exists`), and one `update` per style of `doc-calc.md` §4 and §14
      (by `code`; the comment names the section). Codes are row names a reader can follow
      (`ale-medium-pale-assertive`), not numbers.
- [x] Apply twice; tables and functions owned by `postgres`; row counts printed.
- [x] Write `tests/test_process_ref.py` (stack), each seen failing first:
      `test_water_rows_are_the_books` (the 16 rows with `table_no in ('18','19')`; three spot checks against `doc-calc.md`: medium
      ale pale moderate–assertive SO₄ `[100,400]` and RA `[-30,30]`, light lager Ca from 50,
      strong ale brown/black alkalinity `[120,200]`);
      `test_every_brief_style_has_a_row_and_co2` (A9: for b01–b24 and h01–h06, `targets.style.code`
      from `tests.test_step4.step4` and every listed `alt_styles` code with ranges has
      `water_profile` and `co2_vol`, except 23A, whose row is `web-berliner-weisse`, and every mapped style has `water_basis` and `co2_basis`); `test_basis_labels` (doc-calc §4/§14 lists: the `listed`, `inferred`, `judgement`, `web` sets match); `test_co2_inside_its_family` (each `co2_vol` equals its
      family's p. 159 range); `test_rows_have_a_source`.
- [x] Run `.venv/bin/pytest tests/test_process_ref.py tests/test_styles.py`, expect all pass.
- [x] `docs/DATABASE.md` §2 rows for `water_profile` and the three columns, §9 `co2_vol` line
      removed. PROJECT.md §8.
Done when: every brief style has a water row and CO₂ volumes from a reviewed table.
Commit: `Load water rows and CO2 volumes into ref`

### Task 3: water maths as tested code
Why: R1, R2, A3, A10 (the estimate), A12 (volumes).
- [x] `db/050_water.sql` (needs 030, 049), each function immutable or stable, raising on bad
      input:
      - `app.salt_ions(salts jsonb, volume_l numeric) returns jsonb`: salts `[{ingredient_id, g}]`
        → mg/L of each ion `ref.water_salt` lists, summed (`{ca, mg, na, so4, cl, hco3, oh, co3}`).
      - `app.residual_alkalinity(ions jsonb) returns jsonb` → `{alkalinity_ppm, ra_ppm, ra_meq_l}`
        (alkalinity from HCO₃, CO₃ and OH as CaCO₃; Kolbach).
      - `app.water_volumes(profile jsonb, step10 jsonb) returns jsonb` → `{grist_kg, ratio_l_kg,
        preboil_l, absorbed_l, total_l, strike_l, sparge_l, because}` (Approach; mashed items are
        `step10.fermentables` whose `ref.fermentable.role` is not `sugar`).
      - `app.water_aim(row text, hints text[]) returns jsonb` → `{ca, so4, cl, alkalinity, ra,
        moved_by [text]}` (Approach step 12 item 2; unbounded upper ends as `doc-calc.md` §3 says).
      - `app.salt_additions(source jsonb, aim jsonb, row text, strike_l numeric, sparge_l numeric)
        returns jsonb` → `{salts [{ingredient_id, name, aims_at, strike_g, sparge_g, total_g}],
        none_needed, strike_water {ions, alkalinity_ppm, ra_ppm}, sparge_water {…}, notes [text]}`
        (items 3 and 5: gypsum and calcium chloride only).
      - `app.alkalinity_dose(grist jsonb, strike_ions jsonb, strike_l numeric, target_low numeric)
        returns jsonb` → `{ra_needed_meq_l, salts [{ingredient_id, name, strike_g}], because}`
        (item 4: baking soda to Na ≤ 100 mg/L, then slaked lime; nothing when the estimate is already
        at or above `target_low`).
      - `app.malt_acidity(role text, ebc numeric) returns jsonb` → `{class, meq_kg, buffer, page}`
        (§7 classes; one `case` a reader can follow).
      - `app.mash_ph_estimate(grist jsonb, strike_ions jsonb, strike_l numeric, colour text) returns jsonb` →
        `{ph, target_low, target_high, terms [{what, meq, buffer}], because}` (the target comes from the
        row's colour, item 7; `colour` is a fourth argument, null for 5.2–5.6).
- [x] Apply twice; owners `postgres`.
- [x] Write `tests/test_water.py` (stack), each seen failing first:
      `test_pilsner_example` (A3: calcium chloride for 30 ppm Ca in 37.854 L → 4.17 g ± 0.02, and
      4.2 g gives Cl 53.5 ± 0.2; *Water* ch. 7); `test_pale_ale_option_1` (RA 44 ± 1 at Ca 101,
      9 ± 1 at 150 for the book's water); `test_foreign_extra_stout_lime` (0.087 ± 0.002 g/L
      slaked lime raises RA by 1.68 mEq/L); `test_table17_per_gallon` (§1 figures);
      `test_volumes_add_up` (A12: b01's step 10 with the default profile: strike + sparge =
      total = pre-boil + kg × 1.0, strike = kg × ratio, sugars not counted; a high-gravity case
      where strike ≥ total gives sparge 0 and says so); `test_salts_never_negative` (a source water
      above every aim: no salt, `none_needed` true); `test_aim_moves_with_hints` (same row: `bitter`
      gives higher sulfate and lower chloride than no hint, `malty` the reverse, both → middle with
      a note); `test_calcium_brought_to_minimum`; `test_alkalinity_only_in_strike`
      (a dark grist on distilled water: baking soda and lime only in `strike_g`, Na ≤ 100);
      `test_alkalinity_follows_grist` (the doc-calc §6 case: 4 kg Pilsen + 1 kg caramel 60L + 1 kg
      roast, 18 L: 0.2314 g/L baking soda, estimate then 5.400 ± 0.01; the pale 4 kg Pilsen grist: no
      dose); `test_alkalinity_soda_then_lime` (a need above Na 100 mg/L: soda to the cap, lime for the
      rest); `test_row_ranges_are_references` (a recipe whose water is outside the row's alkalinity or RA
      range gets an `outside_row` note and no extra dose);
      `test_pale_grist_needs_acid` (A10: the §7 hand-worked case: estimate within 0.02 of
      `doc-calc.md`'s 5.573 and above the pale target's 5.4); `test_dark_grist_on_distilled_is_low` (b05-style roast
      grist without alkalinity: estimate below 5.4; doc-calc §7: 5.30); `test_ph_terms_add_up` (Σ meq / Σ buffer
      reproduces `ph`).
- [x] (not done, no figure came; §16 says the estimate is unverified against Bru'n Water) Optional, needs you: if you enter b08's grist and its step 12 waters into Bru'n Water 1.25
      and send its mash pH, add `test_brunwater_oracle` (± 0.15) and note it in `doc-calc.md` §16;
      otherwise §16 says the estimate is checked only against the book's figures *(unverified
      against Bru'n Water)*. Do not wait for it.
- [x] Run `.venv/bin/pytest tests/test_water.py tests/test_maths.py`, expect all pass.
- [x] `docs/DATABASE.md` §5 (functions of `db/050`). PROJECT.md §8.
Done when: the three worked examples and A10's case pass.
Commit: `Add water maths from the Water book`

### Task 4: step 12 doses salts for the recipe's water
Why: R2, A3, A9, A10, A12.
- [x] `db/050_water.sql`: `app.step12_water(profile jsonb, targets jsonb, brief jsonb, step10
      jsonb) returns jsonb` → `{target {from style|none, style_code, row, table_no, beer_type,
      strength, colour, bitterness, ranges {ca, alkalinity, so4, cl, ra} (references), acidify, page, aim,
      basis (listed|inferred|judgement|web), fallback (basis is not listed), outside_row [text],
      moved_by}, source_water {ions, alkalinity_ppm, ra_ppm}, volumes (app.water_volumes),
      salts, none_needed, strike_water, sparge_water, mash_ph, acid {needed, text, acidify},
      values_used [{what, because, source}]}`. With no row: `target.from = "none"`, `salts []`,
      `none_needed` true with "style X has no water row", the waters equal the source water, the pH
      estimate still made (decision Q1). `acid` never holds an amount.
- [x] Contracts `step12.input` = `{run_id, brief, profile, targets, step10}` and
      `step12.output` as above (all required, `additionalProperties: false`, nulls where the text
      allows). `tests/test_contracts.py`: `NAMES` covers `range(16)`, `ABSENT_SLOTS["step12.output"]
      = [("salts", "array"), ("target.row", "null")]`.
- [x] Apply twice; owners `postgres`.
- [x] Write in `tests/test_water.py` (inputs: `tests.test_compute.step10_input` / `compute`), each
      seen failing first: `test_step12_names_its_row` (A9: b01, b05, b08, b13, b16: `target.row`
      is the style's `water_profile`, `page` set); `test_step12_volumes_are_step13s` (A12: equals
      `app.water_volumes` of the same inputs); `test_step12_b08_needs_acid` (A10 through the step:
      `acid.needed` true, no number in `acid` but the estimate); `test_no_acid_amount_anywhere`
      (A10: no key in any of the five outputs named `*acid*_g`, `*_ml`, or an acid ingredient);
      `test_targets_agree_with_bjcp_cities` (A9: §15's checks on the mapped styles' aims; the city
      table is read from `water/bjcp_study_guide_water.md` and never stored);
      `test_unmapped_style_has_no_salts` (decision Q1: a style with `water_profile` null);
      `test_step12_meets_contract`; `test_step12_same_input_same_output`.
- [x] Run `.venv/bin/pytest tests/test_water.py tests/test_contracts.py`, expect all pass.
- [x] `docs/DATABASE.md` §5. PROJECT.md §8.
Done when: step 12 outputs meet the contract and name their row, and the pale case says acid.
Commit: `Compute water salts in step 12`

### Task 5: step 13 gives the mash steps, volumes and boil schedule
Why: R3, A7, A11, A12.
- [x] `db/051_mash_boil.sql` (needs 050): `app.mash_rests(style_code text, grist jsonb, mash_c
      numeric) returns jsonb` → the ordered steps `[{name, temp_c, minutes, why, source}]`: the
      neutral rests whose trigger holds (`doc-calc.md` §9), the saccharification rest at `mash_c`,
      the mash-out. `app.step13_mash_boil(profile jsonb, targets jsonb, step10 jsonb) returns
      jsonb` → `{mash {mash_c, steps, volumes (app.water_volumes), strike_c, grain_c}, boil
      {boil_min, because,
      additions [{at_min, kind hop|extra, ingredient_id, name, usage, g}], whirlpool […]},
      values_used}`: `mash_c` = `step10.mash_c`, `boil` = `step10.boil` as is, additions sorted by
      minute descending (whirlpool after the boil, by its minutes); mash, boil and whirlpool
      extras placed by `time_min`.
- [x] `app.strike_temp(ratio_l_kg numeric, grain_c numeric, target_c numeric) returns numeric`
      (HTB ch. 17 single infusion equation, metric form from `doc-calc.md` §8; raises on a ratio
      ≤ 0); `mash.strike_c` = the strike temperature for the first mash step (a rest when there is
      one, else the saccharification rest) at `volumes.ratio_l_kg`, `mash.grain_c` = §8's grain
      temperature. Decision Q2.
- [x] Contracts `step13.input` = `{run_id, profile, targets, step10}`, `step13.output`;
      `ABSENT_SLOTS["step13.output"] = [("boil.whirlpool", "array")]`.
- [x] Apply twice; owners `postgres`.
- [x] Write `tests/test_mash_boil.py` (stack), each seen failing first:
      `test_mash_and_boil_are_step10s` (A7: b01, b08, b14: saccharification `temp_c` =
      `step10.mash_c`, `boil_min` = `step10.boil.boil_min`); `test_rests_are_neutral_and_sourced`
      (A11: every step other than the saccharification rest is below the starch range of
      `doc-calc.md` §9 or the mash-out, and has a `source`); `test_weizen_gets_ferulic_rest` (b13);
      `test_flaked_over_20_gets_beta_glucan_rest` (a grist with 25 % Flaked Oats; 15 % gets none);
      `test_single_infusion_otherwise` (b01: saccharification and mash-out only);
      `test_additions_in_time_order` (b01 boil hops by minute, whirlpool last; b24's orange peel at
      whirlpool); `test_no_dry_hop_or_secondary_here` (b02, b23); `test_strike_temp_example`
      (HTB ch. 17's worked example within 0.5 °C, `doc-calc.md` §8); `test_strike_c_targets_first_step`
      (b01: `strike_c` = `app.strike_temp` of its ratio, grain temperature and `mash_c`; b13: of its
      ferulic rest); `test_volumes_equal_step12s`
      (A12); `test_step13_meets_contract`.
- [x] Run `.venv/bin/pytest tests/test_mash_boil.py tests/test_contracts.py`, expect all pass.
- [x] `docs/DATABASE.md` §5. PROJECT.md §8.
Done when: step 13 copies step 10's mash and boil, every extra rest is neutral and sourced, and
the strike temperature reproduces the book's example.
Commit: `Add mash steps and boil schedule in step 13`

### Task 6: step 14 plans the fermentation and the pitch
Why: R4, A4, A7 (amounts), A8.
- [x] `db/052_ferment.sql` (needs 030, 051): `app.pitch_rate(yeast_id bigint, og numeric,
      volume_l numeric, after_souring boolean default false) returns jsonb` → `{rate_m_per_ml_p, plato, cells_billion, amount, unit
      g|pack, because}` (Approach; the `because` of every computed amount says the cell counts per gram and per pack are HTB's generic figures, not the maker's spec; a souring culture, `ref.yeast.type = 'lacto'`, and any yeast
      whose amount cannot be computed give `cells_billion` null, `amount` 1, `unit` pack and
      `because` "no sourced pitch rate"; a souring culture gets HTB p. 206's rate, 150 billion cells
      per 19 L scaled to the batch, ⌈cells ÷ 100⌉ packs, and the main yeast 1.0 billion/L/°P
      after souring (p. 212), decision Q3 as revised 2026-10-28). `app.ferment_schedule(main
      jsonb, souring jsonb, ferm_c numeric, dry_hop boolean default false) returns jsonb` → `[{phase souring|ferment|rest|dry_hop|
      crash|lager, yeast_id, temp_c, days (the minimum), why, source, move_on (HTB's trigger text or null)}]` (Approach; constants from
      `doc-calc.md` §11 and §13). `app.step14_ferment(targets jsonb, step10 jsonb) returns jsonb` →
      `{steps, pitch [{ingredient_id, name, role, …pitch_rate}], dry_hops [{day, temp_c,
      contact_days, hops [{ingredient_id, name, g}]}], secondary [{usage, day, ingredient_id, name, g,
      contact_days}], max_temp_c, values_used}`; `max_temp_c` is the highest `temp_c` of the
      ferment and rest steps (what step 15 reads; the souring step is left out, see Deviations).
- [x] Contracts `step14.input` = `{run_id, targets, step10}`, `step14.output`;
      `ABSENT_SLOTS["step14.output"] = [("pitch.cells_billion", "null"), ("dry_hops", "array"),
      ("secondary.contact_days", "null")]`.
- [x] Apply twice; owners `postgres`.
- [x] Write `tests/test_ferment.py` (stack), each seen failing first:
      `test_yeast_book_example` (A8: ale, 20 L, 12 °P → 180 billion cells; a lager at the same wort
      → 360); `test_dry_yeast_in_grams` (US-05 b01: grams = ⌈cells ÷ §10's figure⌉, unit g);
      `test_liquid_yeast_in_packs` (a liquid ale: ⌈cells ÷ 100⌉ packs); `test_every_ferment_temp_in_range`
      (A4: for every `ref.yeast` row of type ale, kveik and lager, the schedule from each of its
      `app.ingredient_choices` ferment options: every souring, ferment and rest step inside its
      yeast's `temp_c`); `test_every_lager_has_diacetyl_rest` (A4: every lager row);
      `test_ramp_shape` (start < main ≤ end raise, start inside the range; b03's S-04 at step 6's
      15 °C starts at 15 and holds at 16 or above); `test_b13_weizen_schedule`;
      `test_gravity_trigger_on_the_rest` (the rest and the ferment hold before it carry `move_on` text with
      "at least" and "2-5 points of FG", HTB Table 6.2); `test_pitch_is_labelled_as_an_estimate` (every
      pitch `because` says "generic" and "not the maker's spec": dry, liquid, culture, main after souring);
      `test_no_sourced_rate_is_one_pack`; `test_b14_souring_first` (souring step with YF-998 inside 15–35 °C and HTB's 32–46 °C band, before
      the main yeast's first step); `test_souring_culture_pitch` (b14: YF-998 pitch
      150 × L ÷ 19 billion cells, 2 packs for 20 L; the main yeast's rate 1.0); `test_dry_hop_after_fermentation` (b02 with synthetic dry hops added to step 10: day after the last
      ferment step, Janish temperature and contact days, grams equal step 10's);
      `test_secondary_extras` (b23 with a synthetic step 10 holding coffee beans 60 g, contact 2 days from `time_min` 2880; vanilla
      `contact_days` null); `test_max_temp` (b08: equals its diacetyl rest temperature; b14's souring 35 °C does not count);
      `test_step14_meets_contract`.
- [x] Run `.venv/bin/pytest tests/test_ferment.py tests/test_contracts.py`, expect all pass.
- [x] `docs/DATABASE.md` §5. PROJECT.md §8.
Done when: every yeast in `ref` gets a schedule inside its range, lagers rest, and the book's
pitch example reproduces.
Commit: `Plan fermentation and pitch rate in step 14`

### Task 7: step 15 sets carbonation and priming sugar
Why: R5, A5.
- [x] `db/053_package.sql` (needs 049, 052): `app.residual_co2(temp_c numeric) returns jsonb` →
      `{temp_c, gas_l_mol, residual_vol}` from Table 10.3's rows written as a `values` list (the
      nearest whole °C row; below 5 or above 30 raises); `app.priming_sugar_g(co2_vol numeric,
      temp_c numeric, volume_l numeric) returns numeric` (sucrose, Approach formula);
      `app.step15_package(targets jsonb, step10 jsonb, step14 jsonb) returns jsonb` → `{co2 {volumes, basis,
      range, family, from style|default, source}, priming {sugar "table sugar (sucrose)", g,
      g_per_l, temp_c, residual_vol, volume_l, source}, extras [{ingredient_id, name, g}]}`; grams
      rounded to 1 g.
- [x] Contracts `step15.input` = `{run_id, targets, step10, step14}`, `step15.output`;
      `ABSENT_SLOTS["step15.output"] = [("co2.range", "null"), ("extras", "array")]`.
- [x] Apply twice; owners `postgres`.
- [x] Write `tests/test_package.py` (stack), each seen failing first: `test_palmer_cane_sugar`
      (A5: 2.5 volumes, 19 L, 21 °C → within 5 % of Table 10.1's 113 g); `test_table_10_3_cells`
      (5 °C 2.5 → 4.4, 21 °C 2.5 → 6.0, 30 °C 4.5 → 13.1 g/L, each ± 0.1); `test_residual_rows`
      (all 26 rows equal `doc-calc.md` §14); `test_priming_uses_max_temp` (b08: `temp_c` =
      step 14's `max_temp_c`); `test_co2_from_style` (b13 inside the German wheat family, b05
      porter-and-stout); `test_default_co2` (decision Q1: a style with `co2_vol` null → 2.5, `from`
      default); `test_packaging_extras` (step 10 extras with cold brew coffee at `package`);
      `test_step15_meets_contract`.
- [x] Run `.venv/bin/pytest tests/test_package.py tests/test_contracts.py`, expect all pass.
- [x] `docs/DATABASE.md` §5. PROJECT.md §8.
Done when: Palmer's priming figure and Table 10.3 reproduce.
Commit: `Add carbonation and priming in step 15`

### Task 8: the process is saved with the recipe
Why: R6, A7, A11.
- [x] `db/048_save_recipe.sql`: `app.recipe_process(step10 jsonb, step12 jsonb, step13 jsonb,
      step14 jsonb, step15 jsonb) returns jsonb` → `{water: step12, mash: step13.mash, boil:
      step13.boil, fermentation: step14, packaging: step15}`; raises `recipe_process: mash <x> is
      not step 10's <y>` (and the same for the boil) when they differ. Drop the five-argument
      `app.save_recipe` and create `app.save_recipe(run_id bigint, step3 jsonb, targets jsonb,
      step10 jsonb, step11 jsonb, process jsonb default null)`: with `process`, sets
      `app.recipe.process` and writes each yeast row's `amount` and `unit` from
      `process.fermentation.pitch` (matched by `ingredient_id`; a yeast missing from it raises);
      without, as today (the comment says only stage D tests call it so).
- [x] Contract `process.output` (the saved object). Apply 048 twice; owners `postgres`.
- [x] Write `tests/test_save_process.py` (stack; a throwaway run and brief, rolled back, as
      `tests/test_save_recipe.py` does), each seen failing first: `test_process_saved`
      (b23: `app.recipe.process` valid against `process.output`, its water, mash, boil,
      fermentation and packaging equal the step outputs); `test_mash_and_boil_match_step10` (A7
      on the saved row); `test_yeast_rows_from_pitch` (A7: b01's yeast row `g` with step 14's
      amount; b14's souring row has step 14's packs and `because`); `test_fg_unchanged` (A11: saved `fg` = step 10's
      `numbers.fg`); `test_recipe_process_refuses_other_mash`; `test_save_without_process_still_works`.
      `tests/test_save_recipe.py` keeps passing unchanged.
- [x] Run `.venv/bin/pytest tests/test_save_process.py tests/test_save_recipe.py tests/test_contracts.py`,
      expect all pass.
- [x] `docs/DATABASE.md` §5 (`app.recipe.process` shape). PROJECT.md §8.
Done when: a saved recipe carries its process and real yeast amounts.
Commit: `Save the process with the recipe`

### Task 9: the pipeline runs steps 12–15 before saving
Why: R6, A2 (wiring).
- [x] Sub-workflow `Steps 12–15 · process` (id `ST1215process01`), JSON from
      `n8n/workflows/steps-10-11-compute-and-validate.json`'s pattern: trigger with the
      `process.input` fields `{run_id, brief, profile, targets, step10}` → `Check contract` →
      for each step: Postgres `select app.step12_water($1,$2,$3,$4)` → `Check contract`
      (`step12.output`) → `Step 12 · log` (`app.run_step`, `try` 1, ok, ms) — the same for step 13
      (`app.step13_mash_boil($1,$2,$3)`), step 14 (`app.step14_ferment($1,$2)`) and step 15
      (`app.step15_package($1,$2,$3)`, with step 14's output) → Postgres `app.recipe_process(...)`
      → `Check contract` (`process.output`) → return
      `{step12, step13, step14, step15, process}`. A raise logs that step's row with ok false and
      `error` (`step 1N: …`), then `Stop and Error`. Sticky note and `Test data`
      (`tests/step1215_sample.json`: b01's step 10 from Task 4's helpers, `run_id` 0).
- [x] `Recipe pipeline`: each `Try n passed?` yes → `Steps 12–15 · input` → `Steps 12–15 ·
      process` (continueErrorOutput) → `Save recipe` (`select app.save_recipe($1, $2, $3, $4, $5,
      $6)` with `$6` the returned `process`) → `Finish run` → `Respond ok`; error →
      `Finish run (failed, steps 12–15)` → `Respond failed (steps 12–15)` (`failed_step` from the
      message). Update the per-step sticky note (steps 0–15 built).
- [x] Contract `process.input`; `NAMES` gains `process.input`, `process.output`. Import and publish
      the sub-workflow, then the pipeline; delete the copies in `shared/`; `.venv/bin/python -m
      evals.workflows`.
- [x] `tests/test_workflows.py`: `SAMPLES` and `CONTRACT_OF` for the new file.
      `tests/test_pipeline.py::test_b01_validates_and_saves` also checks rows 12–15 (ok, valid
      against their contracts, `try` 1) and the saved `process` (valid against `process.output`,
      mash and boil equal the step 10 row's); `test_impossible_target_fails_after_three_tries` also
      checks no row 12–15. Time the file.
- [x] Run `.venv/bin/pytest tests/test_workflows.py tests/test_pipeline.py`, expect all pass.
- [x] `docs/OPERATIONS.md` §5: twelve workflows, the new one, `failed_step` 12–15. PROJECT.md §4
      Orchestration row and §8.
Done when: a webhook run of b01 saves a recipe with its process and logs steps 12–15.
Commit: `Run steps 12-15 in the pipeline`

### Task 10: the briefs get process expectations and the harness grades them (gate)
Why: R7, A6 (WORKFLOW-ROADMAP §3 M7 row).
- [x] Propose a `process` table for the briefs that need one, with keys only from: `ferm_c`
      (`[low, high]` that every `ferment` step must lie in), `diacetyl_rest` (bool), `lagering`
      (bool), `souring` (bool), `water_row` (expected `ref.water_profile` code). Approved 2026-10-28 (plus `packaging_extras`, a sixth key, for b23's coffee at packaging; b02 gets none): b13
      weizen `ferm_c` band, b06, b08, b09, b17 lager schedule (`diacetyl_rest`, `lagering`), b14
      `souring`, b01 and b05 `water_row`; every other brief `process = {}`. Hand back
      `needs-approval` with the table (values and why); write the approved values into
      `evals/recipe_briefs.toml` (header documents the field) and `process = {}` into
      `evals/heldout_briefs.toml`.
- [x] `tests/test_recipe_briefs.py`: `FIELDS` gains `process`; `test_process_keys` (only the five
      keys, `ferm_c` a two-number range, `water_row` an existing code).
- [x] `evals/grade.py` `grade_process(brief, process) -> dict` (pure Python: `present` = the
      saved process has all five parts; each expectation `{expected, got, met}`; `process_ok`).
      `evals/run.py` `read_recipe` adds `process`; the result line and totals add
      `process present` and `process ok`. `evals/show_recipe.py` prints water (row, salts per
      water, pH, acid line), mash steps and volumes, boil schedule, fermentation steps and pitch,
      CO₂ and priming.
- [x] Write `tests/test_grade.py::test_grade_process_*` (met, not met, missing process, empty
      expectations) and extend `tests/test_run.py` for the new columns. Each seen failing first.
- [x] Run `.venv/bin/pytest tests/test_recipe_briefs.py tests/test_grade.py tests/test_run.py`,
      expect all pass.
- [x] PROJECT.md §8.
Done when: you approved the expectations and the harness grades them.
Commit: `Add process expectations to the briefs`

### Task 11: a full brief run has a process on every validated recipe (gate)
Why: A2, A6, A7, A11 on the real pipeline.
- [ ] `.venv/bin/python -m evals.run --save --label m7` (b01–b24; the stack and Ollama up,
      OPERATIONS §6). Measure and write into PROJECT.md §8: validated count (stage D unchanged,
      compare with m6's 19–20/24 as a sanity check, not a bar), every validated run has rows 12–15
      ok and a saved `process` (A2), `process ok` per brief with expectations (A6), every saved
      recipe's mash and boil equal its step 10 row and its `fg` equals step 10's (A7, A11, by one
      read-only SQL query written into the entry), yeast rows no longer `1 pack` unless the pitch rate gives one pack
      (A7 as revised 2026-10-28).
- [ ] If a check fails, stop and hand back `needs-input` with the failing briefs and the cause;
      do not tune expectations to pass.
- [ ] Hand back `needs-approval` with the counts and `evals.show_recipe` output of b08, b13 and b14
      (a lager, a weizen, the souring schedule).
Done when: every validated recipe of the run has its process and the expectations pass.
Commit: `Measure steps 12-15 on the briefs`

### Task 12: the docs describe stage E as built
Why: brief Scope "Docs".
- [ ] `docs/RECIPE-ROADMAP.md`: §3 rows 12–15 say what is built (functions, sources, the acid
      line, the neutral rests, pitch, priming); §6: carbonation is *How to Brew* ch. 10 (Tables
      10.1–10.3, p. 159 families), residual alkalinity and salts *Water* ch. 4–7 with the tables, mash
      pH ch. 5, pitch rate HTB ch. 7; §8 P6 marked done with the measured counts; §8 Later gains acid
      dosing (*Water* ch. 6, Appendix B), own water ions (already there: check), and water rows and
      CO₂ families for the styles outside the reviewed tables (decision Q1).
- [ ] `docs/WORKFLOW-ROADMAP.md`: M7 row (built, date, counts), §3 M7 gap marked done.
- [ ] `PROJECT.md` §5: *How to Brew* (carbonation and mash chapters passed), *Water* and *Yeast*
      ("calc done: m7-process") rows, the BJCP study guide's water table (check only).
      `docs/BOOKS.md`: the m7 owner notes say what was passed. `docs/SOURCES.md`: fates of the
      m7 rows. `docs/DATABASE.md` §7 fill order and §9 (P6 items done).
- [ ] PROJECT.md §8.
Done when: no doc says steps 12–15 are unbuilt or cites Palmer ch. 11 for carbonation.
Commit: `Describe steps 12-15 in the docs`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| Salt grams reproduce *Water*'s worked examples (A3) | `test_water.py::test_pilsner_example`, `test_pale_ale_option_1`, `test_foreign_extra_stout_lime` | 3 |
| Salts are never negative; none when not needed | `test_water.py::test_salts_never_negative` | 3 |
| Strike + sparge = total water; step 12 doses for step 13's volumes (A12) | `test_water.py::test_volumes_add_up`, `test_step12_volumes_are_step13s`; `test_mash_boil.py::test_volumes_equal_step12s` | 3, 4, 5 |
| Pale grist on distilled water → acid line, no acid amount (A10) | `test_water.py::test_pale_grist_needs_acid`, `test_step12_b08_needs_acid`, `test_no_acid_amount_anywhere` | 3, 4 |
| Every brief style has a reviewed water row and CO₂ volumes (A9) | `test_process_ref.py::test_every_brief_style_has_a_row_and_co2` | 2 |
| Each recipe names its target row; city table only a check (A9) | `test_water.py::test_step12_names_its_row`, `test_targets_agree_with_bjcp_cities` | 4 |
| Step 13's mash and boil are step 10's (A7) | `test_mash_boil.py::test_mash_and_boil_are_step10s`; `test_save_process.py::test_mash_and_boil_match_step10` | 5, 8 |
| Strike temperature reproduces HTB ch. 17's example (R3) | `test_mash_boil.py::test_strike_temp_example` | 5 |
| No rest changes fermentability; each has a source (A11) | `test_mash_boil.py::test_rests_are_neutral_and_sourced`; `test_save_process.py::test_fg_unchanged` | 5, 8 |
| Every fermentation temperature inside its yeast's range; lagers rest (A4) | `test_ferment.py::test_every_ferment_temp_in_range`, `test_every_lager_has_diacetyl_rest` | 6 |
| Pitch rate reproduces the pitching-rate example (A8; HTB Table 7.1 or *Yeast*, doc-calc question 1) | `test_ferment.py::test_yeast_book_example` | 6 |
| Priming reproduces Palmer within 5 % (A5) | `test_package.py::test_palmer_cane_sugar`, `test_table_10_3_cells` | 7 |
| Saved process and yeast amounts (R6, A7) | `test_save_process.py::test_process_saved`, `test_yeast_rows_from_pitch` | 8 |
| Pipeline logs 12–15 and saves the process | `test_pipeline.py::test_b01_validates_and_saves` | 9 |
| Process expectations graded (A6) | `test_grade.py::test_grade_process_*` | 10 |

## Decisions (were open questions)

Answered by you in chat, 2026-10-28:
- **Q1** Styles outside the reviewed tables: "No row, defaults". No water row → no salts, "style
  has no water row", the pH estimate of the source water; CO₂ 2.5 volumes, Palmer's default
  (p. 155), marked `default`. Wider coverage is a RECIPE-ROADMAP §8 Later TODO (Task 12).
- **Q2** Strike water temperature: "Add it". HTB ch. 17's single infusion equation as one
  function, tested against the book's worked example (Task 5; brief R3).
- **Q3** Souring culture amount: first "Keep 1 pack" (2026-10-28), **replaced the same day**
  by "Use HTB's rate": *How to Brew* p. 206 gives 100-200 billion Lactobacillus cells per 19 L,
  so the culture gets 150 billion per 19 L scaled to the batch in 100-billion packs, and the main
  yeast 1.0 billion/L/°P after souring (p. 212). Brief A7 revised (Tasks 6, 8, 11).
- **Q4-Q8 (doc-calc gate, 2026-10-28)** A8 cites HTB Table 7.1; acid line target by colour (HTB
  p. 341/365); hint positions kept plus HTB ion caps; souring in the fermenter after the boil;
  `ref.water_salt` left as stored; honey beer CO₂ = HTB American ales 2.2-2.7.

## Approved exceptions

None.

## Deviations
- 2026-10-28 · Task 5: `step13.mash` also carries `additions` (the extras step 10 puts in the mash, empty today), and the whirlpool entries use `minutes` where boil entries use `at_min`; a boil extra with no `time_min` goes in at the start of the boil. `app.strike_temp` rounds to 0.1 °C. `test_no_acid_amount_anywhere` now covers step 13 inside `tests/test_water.py` (no separate step 13 test). Implementation details, no scope change.
- 2026-10-28 · Task 1 (Approach step 12 items 3 and 6, step 13 strike): the doc → calc pass changed three
  details, none of scope — (a) calcium above the row maximum is reported, not corrected (doc-calc
  §6); (b) flaked and unmalted adjuncts count as base for mash pH (Bru'n Water §2.4; HTB silent);
  (c) the strike equation uses the book's exact constant 0.4 ÷ (0.985 × r), not the rounded 0.41
  (73.23 vs 73.29 °C at 3 L/kg, doc-calc §8).
- 2026-10-28 · Approach, Files, Tasks 1, 5, 6, 8, 11, 12, Open questions → Decisions: Q1 (no
  water row and 2.5 CO₂ volumes for unmapped styles), Q2 (strike water temperature added to
  step 13 as `app.strike_temp`, Task 5 bullet unconditional, two tests) and Q3 (souring culture
  keeps `1 pack` marked "no sourced pitch rate"; brief A7 and R3 revised) written in — user
  answers in chat.
- 2026-10-28 · Task 1 (user rule: *How to Brew* is the only source of truth where it covers the point; user
  answers to the gate questions): doc-calc §18 lists every switch. Plan text changed to match —
  step 12 item 6 and 7 (mash pH from HTB Table 21.4, 40 mEq/(pH·kg) from HTB p. 342, colour-specific
  target from HTB p. 341/365; this restores the plan's b05-style dark-grist test, which *Water*'s Table 9
  had broken) and item 3 (HTB ion caps); step 13 (ferulic rest 40 °C / 30 min, HTB); step 14 (HTB Table 6.2
  maturation rests: lagers 6 days, ales 4 days, user answer; lager start at the target temperature; dry hop
  3 days; ale cold conditioning from HTB p. 95; souring 35 °C for 1.5 days from HTB p. 211); pitch rate
  (HTB ch. 7: 10 billion cells per gram of dry yeast, user's 7 billion reported alongside). Two plan
  decisions are now in question and wait for the user: Q3 (souring culture 1 pack; HTB p. 206 gives
  a rate) and brief A8 (names *Yeast*'s example; HTB Table 7.1 gives the same 180 billion). Also answered:
  23A CO₂ family = German wheat beer 3.3–4.5; 23A and `specialty-honey-beer` get web-sourced
  `ref.water_profile` rows (doc-calc §4b), which Task 2 stores with `table_no = 'web'`, a `basis` column and
  their own `ref.source` rows (so Task 2's "16 rows" test counts `table_no in ('18','19')`).
- 2026-10-28 · Approach (step 12, step 14 pitch), Tasks 6, 8, 11, Decisions Q3, Critical behaviour table: user
  answers to the doc-calc gate. Q3 revised: the souring culture is pitched at HTB p. 206's rate
  (150 billion cells per 19 L, 2 packs for 20 L) and no longer keeps `1 pack`; the main yeast uses 1.0
  billion/L/°P after souring. `test_souring_culture_keeps_one_pack` became `test_souring_culture_pitch`. Brief A7, A8
  and A10 revised (see brief Deviations). The acid line uses HTB's colour-specific mash pH target. Soured
  in the fermenter after the boil, as planned. Nothing else in the plan changed.
- 2026-10-28 · Approach (step 12 item 4), Tasks 2, 3, 4, 7, Files table: outside review, "apply all three". (1) Alkalinity is
  dosed from the grist-based pH estimate to the bottom of the colour target, not to the middle of the row's RA
  range; the row's alkalinity and RA are references (`outside_row` note). New `app.alkalinity_dose`,
  `app.mash_ph_estimate` takes the colour, tests `test_alkalinity_follows_grist`, `test_alkalinity_soda_then_lime` and
  `test_row_ranges_are_references` added; the pH model (40 mEq/(pH·kg) buffer) now drives dosing and is unverified
  against Bru'n Water. (2) `ref.beer_style.water_basis` and `co2_basis` (`listed|inferred|judgement|web`) carry into
  step 12's `target.basis`/`fallback` and step 15's `co2.basis`; `test_basis_labels` added. (3) `web-honey-beer` dropped:
  one web row (`web-berliner-weisse`) in `ref.water_profile`; `specialty-honey-beer` gets the no-row defaults and the 2.5
  volumes default.
- 2026-10-28 · Task 3: three small helpers were added to `db/050_water.sql` besides the listed functions, and two parameters renamed — `app.add_ions` (adds two waters' ions), `app.mashed_grist(step10)` (the non-sugar fermentables with role and middle EBC, used by `app.water_volumes` and later by step 12) and `app.outside_row(ions, row_code)` (the `outside_row:` notes, reused by step 12 for the final waters); `row` became `row_code` (a reserved word). `app.water_aim` also returns `ca` (the row's floor) and the row's alkalinity and RA as `{low, high}` references; `app.alkalinity_dose` returns `ra_needed_meq_l` as the RA still to add. The grist for `app.mash_ph_estimate` and `app.alkalinity_dose` is `[{name, kg, role, ebc}]`, not ingredient ids, so tests can give a grist directly. Implementation details, no scope change. `test_brunwater_oracle` not added (no figure).
- 2026-10-28 · Task 4: `NAMES` in `tests/test_contracts.py` covers `range(13)`, not `range(16)` — the step 13-15 contracts do not exist yet; each of Tasks 5-7 widens it. `test_no_acid_amount_anywhere` checks step 12's output only, for the same reason (Tasks 5-7 add theirs). `app.range_json(numrange)` was added to `db/050_water.sql` to output the row's ranges.
- 2026-10-28 · Approach (step 14), Task 6 (user, "Yes, add both"): (1) fermentation steps advance on gravity: `days` stays as the minimum and every step has `move_on` text with HTB Table 6.2's trigger (rest starts when gravity is within 2-5 points of FG; ale hold at least 2 more days, lager 4; souring 18-36 hours or about pH 3.5, p. 211); `test_gravity_trigger_on_the_rest` added. (2) Generic HTB cell counts (10 billion/g dry, 100 billion/pack, 150 billion souring midpoint) are labelled estimates in each yeast line's `because`; `test_pitch_is_labelled_as_an_estimate` added. doc-calc §10 and §11 reworded.
- 2026-10-28 · Task 6: implementation details. `app.pitch_rate` takes a fourth parameter `after_souring` (the main yeast's 1.0 rate) and `app.ferment_schedule` a fourth `dry_hop` (adds the `dry_hop` step before cold conditioning). `max_temp_c` is the highest `ferment` or `rest` temperature, not `souring` too: the culture is at 35 °C before the yeast has made CO2, and Table 10.3 (Task 7) stops at 30 °C, so including it would make step 15 raise for every souring recipe. `secondary` items gain `usage` (`secondary` or `ferment`; a `ferment` extra goes in at pitching, day 0), because step 10's `ferment` extras belong to step 14. The tests for dry hops and secondary extras use a step 10 with those entries added: b02 and b23 have none (b23's coffee is cold brew at `package`).
- 2026-10-28 · Task 7: implementation details. `step15.output` has no `values_used`; each block carries its own `source` instead (the plan's shape). `app.priming_sugar_g` returns the unrounded grams (the Table 10.3 g/L cells need it); `app.step15_package` rounds `g` to 1 g and gives `g_per_l` to 0.01. `co2.basis`, `co2.family` and `co2.range` are null for the 2.5 default. `priming.temp_c` is the Table 10.3 row used (step 14's `max_temp_c` to the nearest whole °C).
- 2026-10-28 · Task 10: the `process` keys are six, not five: `packaging_extras` (words that must each appear in a packaging extra's name in step 15) is added for b23's coffee, at your request. The plan's text said "keys only from" the five.
