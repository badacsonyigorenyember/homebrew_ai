# S1 · Brewing maths library — implementation plan

Stage: implementing
Brief: [brief.md](brief.md)
Branch: s1-maths

## Approach

All maths lives in one SQL file, `db/030_maths.sql`, as small `app.*` functions: one function
per formula, with the source (book, page, table) in a comment above it (R1, R8, §6.8). Per-item
functions take plain numbers in SI units. The recipe-level functions (`app.og`, `app.fg`,
`app.ibu`, `app.srm`) and the two solvers take a **jsonb array of items**, the same way n8n's
Postgres node already passes jsonb to `app.step2_best_style`. Where a book formula is defined
in US units (MCU), the function converts inside, with exact factors. Functions return unrounded
numbers, and rounding is left to display. Bad input (volume ≤ 0, a missing field, an unknown hop
usage) raises an error. It never becomes 0. The file is built task by task, and each task adds
its functions, its tests in `tests/test_maths.py` (marked `stack`, called through `psycopg` like
`tests/test_step2_signals.py`) and its own commit.
Task 1 is the doc → calc write-up, so every later task has a cited formula and a worked example
to test before writing code. The source check below has already found the formulas and examples.
Task 1 writes them up and confirms each page number.

### What the source check found (2026-10-14, read from both PDFs)

*How to Brew* (4th ed.). Page numbers are the printed ones. The PDF page is the printed one + 26.
- **Gravity.** The mass gravity volume equation (ch. 4, p. 52–53): mass × PPG = points × volume.
  Max yield = %FGDB × 46 PPG = %FGDB × 384 PKL (p. 280, "80.7 % of 384 = 310 PKL"). The design
  yield is FGDB × efficiency × 46 (ch. 18, p. 290). **R2 answer:** Palmer applies no moisture
  correction to %FGDB, and the loss is left in the efficiency. So `extract_dbfg_pct` is used as
  stored, for malts and for sugars.
- **Efficiency only applies to mashed fermentables.** Malt extract and sugars go in at their full
  yield: DME at 42 PPG in Joe Ale (p. 78) and in the ch. 4 examples, and OBC's table lists honey,
  sugars and extracts as "NA" at 65 % and 75 %. So each grist item carries `mashed` (true or
  false). The caller sets it from `recipe_item.usage = 'mash'`.
- **SG ↔ °P:** SG = 259 / (259 − °P) (ch. 18, p. 285). Table A.2 (p. 465) is ASBC's table and
  is not this formula. At 1.080 the formula gives 19.19 °P and the table gives 19.3. The brief
  asks only for the round trip (A7), so table A.2 is noted in doc-calc.md and not tested.
- **FG:** apparent attenuation = (OG − FG) / (OG − 1) (ch. 6, p. 108). Table 4.3 (p. 55) has an FG
  row "assuming 75 % fermentability", and all 7 cells are FG = 1 + 0.25 × (OG − 1) within
  ± 0.001. Sugars have 100 % fermentability and lactose is unfermentable (table 24.1, p. 436).
- **ABV:** table 9.1 (p. 150) is "based on the work of Balling" and gives no formula. The plain
  `131.25 × (OG − FG)` misses 65 of its 140 cells by more than 0.1 (worst 0.19). The Balling form
  published in BYO (Bill Pierce, "Calculating Alcohol", https://byo.com/articles/calculating-alcohol/)
  is RE = 0.1886·OE + 0.8114·AE, then ABW = (OE − RE) / (2.0665 − 0.010665·OE), then ABV = 1.259 × ABW.
  With Palmer's °P formula it reproduces **all 140 cells** within 0.1 (worst 0.088, measured with a
  scratch script). BYO also gives ABV = ABW × FG / 0.794, but that misses 29 cells, so the plan
  uses the 1.259 form, which is the one the table follows. **Table 4.3's ABV row does not agree
  with table 9.1** (for example 1.060/1.015 is 6.1 % in table 4.3 and about 5.8 % in table 9.1).
  No formula matches table 4.3, so its ABV row is noted in doc-calc.md and not tested. This
  changes the brief's Assumptions line, not a requirement.
- **IBU:** Tinseth, U = 1.65 × 0.000125^(Gb − 1) × (1 − e^(−0.04·t)) / 4.15 (p. 80), and
  BU = g × α × U × 1000 / final L (p. 77–78). The boil gravity Gb is the pre-boil gravity
  (p. 78). It reproduces all 160 cells of table 5.5 (p. 81) within 0.0005, and Joe Ale (p. 78–79).
- **Colour:** MCU = °L × lb / gal (app. B, p. 469 and p. 472). Morey, as printed in table B.3
  (p. 470), is SRM = 1.49 × MCU^0.69. EBC = 1.97 × SRM (p. 469), and malt °L is treated as SRM
  (p. 468, "nearly identical").
- **Volumes:** pre-boil = batch + losses + boil-off × time. Boil gravity points = OG points ×
  batch / pre-boil (p. 291–292, "multiply the post-boil gravity by the post-boil volume …").
- **No whirlpool or dry-hop IBU figure** in the book (as the brief expected).

OBC *Recipe Formulation* (2009, 6 pages). The brief asked whether its examples have enough
inputs to recompute. Here is what is there:
- **OG: yes, for both beers.** Every row gives pounds and a yield, the batch is 5 gal, and the
  efficiency is 75 %. With the table's 100 % yields, 75 % efficiency on malts and candi sugar at
  full yield: Dubbel 1.0747 (book 372.25 / 5 = 1.0745, printed "1.075"), Pils 1.0500 (book
  252 / 5 = 1.0504). Both are within ± 0.001.
- **Colour (MCU): yes, for both.** Pils 4.0 MCU (book 4). In the Dubbel table the book's own sum
  is wrong. The candi row says 0.75 lb × 30 °L = 35.25, but the right product is 22.5 (35.25 is
  the row's extract total). The rows give 40.5 MCU, not the printed 43.
- **SRM: not a Morey result.** OBC reads SRM off Daniels' MCU → SRM range table ("17 or 18" for
  the Dubbel, "around 4" for the Pils). Morey gives 19.2 for the Dubbel (40.5 MCU) and 3.9 for
  the Pils.
- **IBU: not reproducible with Tinseth.** OBC uses Daniels' stepped utilisation table with
  IBU = oz × α% × U% / (gal × 1.34), and gives no boil gravity or boil volume. It also gives two
  boil times for the Mt Hood addition (20 min and 30 min in the text). Tinseth on the same
  inputs, at OG, gives Dubbel 21.2 against OBC 25.4, and Pils 40.5 against 42.5.
- **FG and ABV: not given.**

So OBC tests OG and MCU for both beers. Its SRM and IBU figures are written up in doc-calc.md as
a different model (Daniels' tables) and not tested (your answer, 2026-10-14; brief A2 narrowed).

### Decisions taken here (implementation details, not scope)
- **Grist % is a share of mass**, as in the corpus (`style_grist`, STYLE-PROFILES.md G5) and
  `recipe_item.pct`. OBC works in shares of gravity points, which is the same thing when the
  yields are equal (its Pils).
- **The hop split is a share of hop mass among the additions passed in**, as in the corpus
  (`style_hop_use`: hop mass share). Whirlpool and dry-hop additions get their mass but add
  0 IBU. A caller that doses dry hops in g/L leaves them out of the solver.
- **`full` sugars add 0 FG points, `none` adds all of its points, and `normal` adds
  (1 − attenuation) of its points.** So a 100 % candi grist has FG 1.000.
- **Morey uses the constants Palmer prints (1.49, 0.69)**, because the source in the repo is
  Palmer. Morey's own article (1.4922, 0.6859, not in the repo, *unverified*) gives the same
  answers within ± 1 SRM on every listed example.
- `app.calc_version()` returns `'maths-1'`. Any change to a formula or a constant in
  `db/030_maths.sql` bumps it in the same commit, with a line in doc-calc.md.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `docs/work/s1-maths/doc-calc.md` | new | Doc → calc pass: each formula and worked example, with page, inputs, expected value and tolerance, the book errors and the model mismatches (A1) |
| `db/030_maths.sql` | new | All maths functions and `app.calc_version()`, applied as `postgres` |
| `tests/test_maths.py` | new | Worked examples, edge cases and solver round trips, through `psycopg` (stack tests) |
| `docs/work/s1-maths/brief.md` | changed (in the plan commit) | A2 narrowed for OBC, Assumptions updated, two Deviations lines |
| `PROJECT.md` | changed | §4 Database and Scripts rows, §5 *How to Brew* and OBC rows, §8 entries |
| `docs/RECIPE-ROADMAP.md` | changed | §8 P2 done line |
| `docs/WORKFLOW-ROADMAP.md` | changed | G-M "Measured" line |

## Function signatures

All are in schema `app`, owned by `postgres`, and `immutable` unless they raise. `numeric` is
used everywhere. Items are jsonb objects, and the keys listed are required (other keys, such as
an ingredient id, are ignored and kept by the solvers).

| Function | Returns | Formula (source) |
|---|---|---|
| `calc_version()` | text `'maths-1'` | — |
| `sg_to_plato(sg)` · `plato_to_sg(plato)` | numeric | 259 − 259/SG and 259/(259 − °P) (p. 285) |
| `srm_from_ebc(ebc)` · `ebc_from_srm(srm)` | numeric | EBC = 1.97 × SRM (p. 469) |
| `gravity_points(kg, extract_pct, efficiency_pct, volume_l)` | points | kg × extract/100 × 384 × eff/100 / L (p. 280, 290) |
| `og(grist jsonb, efficiency_pct, volume_l)` | SG | items `{kg, extract_pct, mashed}`. Efficiency applies only when `mashed` |
| `fg(grist jsonb, efficiency_pct, volume_l, attenuation_pct)` | SG | items also have `fermentability` (`full`/`normal`/`none`) (p. 108, 436) |
| `abv(og, fg)` | % v/v | Balling form from BYO, via `sg_to_plato` (see above) |
| `preboil_volume(batch_l, boil_min, boil_off_l_h, losses_l)` | L | batch + losses + boil_off × min/60 |
| `boil_gravity(og, batch_l, preboil_l)` | SG | 1 + (OG − 1) × batch/preboil (p. 291) |
| `tinseth_utilisation(boil_sg, minutes)` | fraction | p. 80 |
| `ibu_addition(grams, alpha_pct, minutes, usage, boil_sg, volume_l)` | IBU | `boil` → Tinseth (p. 77–80). `whirlpool`, `dry_hop` → 0, with the R4 comment. Any other usage raises |
| `ibu(hops jsonb, boil_sg, volume_l)` | IBU | items `{g, alpha_pct, minutes, usage}`. An empty array gives 0 |
| `mcu(kg, ebc, volume_l)` | MCU | (EBC/1.97) × (kg/0.45359237) / (L/3.785411784) (p. 469) |
| `grist_mcu(grist jsonb, volume_l)` · `srm(grist jsonb, volume_l)` | MCU · SRM | items `{kg, ebc}`. SRM = 1.49 × MCU^0.69 (p. 470) |
| `solve_grist(target_og, grist jsonb, efficiency_pct, volume_l)` | jsonb | items `{pct, extract_pct, mashed}` → same items + `kg`. pct is normalised by its sum |
| `solve_hops(target_ibu, hops jsonb, boil_sg, volume_l)` | jsonb | items `{share_pct, alpha_pct, minutes, usage}` → same items + `g`. Raises if target > 0 and no `boil` item |

Apply command (OPERATIONS.md §4), run twice to show the file is idempotent:
`docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/030_maths.sql`

Test unit factors, kept as named constants at the top of `tests/test_maths.py` with a comment:
lb 0.45359237 kg, gal 3.785411784 L, oz 28.349523125 g, PPG → extract % = PPG / 46 × 100
(p. 290, the same rule as `loaders/adjuncts.py`), and °L → EBC × 1.97.

## Tasks

### Task 1: Write the doc → calc pass
Why: A1, PROJECT.md §6.7. Every later test cites a row here.
- [x] Write `docs/work/s1-maths/doc-calc.md`, with one section per formula (gravity, efficiency
  and moisture, °P, FG, ABV, IBU, colour, volumes). For each: the formula, the source page or
  table, what it became (function name), and the worked examples with inputs (as printed),
  expected value, tolerance and test name. Use the findings above and confirm each page and
  number against the PDFs (`pdftotext -layout`, into the scratchpad, not the repo).
- [x] Name every case that is not a plain reproduction: the OBC Dubbel MCU sum error, the OBC
  SRM and IBU written up as Daniels' model and not tested (brief A2), the table 4.3 ABV row,
  table A.2 against the 259 formula, the Port O' Palmer option 1 ("about 12" MCU, an approximate
  input, so not tested), and the Mt Hood 20 / 30 min conflict.
- [x] Record the ABV formula source (BYO URL, author) and the fit: 140/140 cells within 0.1, plus
  the two BYO variants that do not fit (FG/0.794: 29 misses) and 131.25 (65 misses).
- [x] Add `calc_version` = `maths-1`, with the bump rule and a version log.
Done when: every formula the functions use has a page, and every example in the "Critical
behaviour" table below appears in doc-calc.md with its expected value.
Commit: `Add doc-calc pass for s1-maths`

### Task 2: Conversions, gravity and volumes
Why: R1, R2, R6 (forward part), R10, A2, A6, A7.
- [x] Create `db/030_maths.sql`, with a header like `db/022_step2.sql` (purpose, needs
  `db/015_app.sql`, apply command, idempotent), then `calc_version`, `sg_to_plato`,
  `plato_to_sg`, `srm_from_ebc`, `ebc_from_srm`, `gravity_points`, `og`, `preboil_volume` and
  `boil_gravity`.
- [x] Write tests in `tests/test_maths.py`:
  - `test_plato_round_trip`: SG 1.010, 1.050 and 1.100 → °P → SG, each within 0.001 (A7).
  - `test_preboil_volume_example`: 20 L, 60 min, 3 L/h, 2 L → 25 L (A7).
  - `test_og_palmer_dme_example`: 5 lb DME at 42 PPG, not mashed, in 3 gal → 1.070 (p. 53).
  - `test_og_palmer_short_stout_max_yield`: table 18.4, 6 gal at 100 % → 1.052, and at 73 % → 1.038.
  - `test_og_palmer_short_stout_planned_us` (7 lb + 4 × 0.5 lb, FGDB 81/75/74/74/78, 75 %,
    5 gal → 1.050) and `…_metric` (3.5 kg pale 80 % + 4 × 0.225 kg, 75 %, 20 L → 1.050) (p. 290–292).
  - `test_boil_gravity_joe_ale`: 2.5 kg DME at 350 PKL (extract 91.3 %), not mashed, in 23 L → 1.038 (p. 78).
  - `test_og_obc_dubbel` (→ 1.0745) and `test_og_obc_pils` (→ 1.0504), with OBC's 100 % column
    values, malts mashed at 75 % and candi sugar not mashed. Inputs as in doc-calc.md.
  - `test_efficiency_skips_unmashed`: the same sugar item gives the same OG at 50 % and 100 % efficiency.
  - `test_calc_version_defined` (A6), and `test_bad_volume_raises`.
- [x] Apply the file twice, then run `pytest tests/test_maths.py` and expect all to pass.
Done when: the tests pass and `pg_proc` shows the new functions owned by `postgres`.
Commit: `Add gravity, volume and unit maths with tests`

### Task 3: FG and ABV
Why: R3, R9, A2, A7.
- [x] Add `fg` and `abv` to `db/030_maths.sql`, each with its source comment. `abv` calls
  `sg_to_plato`.
- [x] Write tests:
  - `test_fg_table_4_3`: the 7 OG cells at 75 % attenuation → FG within 0.002 (p. 55).
  - `test_abv_table_9_1`: all 140 cells of table 9.1, typed into the test as a literal table
    from p. 150, each within 0.1 (A7, R9).
  - `test_fg_all_candi_is_one`, `test_fg_lactose_only_is_og` (`none` keeps all its points),
    and `test_fg_unknown_fermentability_raises`.
- [x] Apply twice, then run `pytest tests/test_maths.py`.
Done when: all 140 ABV cells and 7 FG cells pass.
Commit: `Add FG and ABV maths with tests`

### Task 4: IBU (Tinseth), whirlpool and dry hop at 0
Why: R4, A2, A8.
- [x] Add `tinseth_utilisation`, `ibu_addition` and `ibu`. Above the 0-IBU rule, add a comment:
  whirlpool and dry hop count as 0 IBU for now, a cited model is a late-game follow-up
  (RECIPE-ROADMAP §8 Later), and the book gives no figure.
- [x] Write tests:
  - `test_tinseth_table_5_5`: all 160 cells within 0.001 (p. 81).
  - `test_ibu_joe_ale_metric`: 28 g 8 % 60 min → 30.3 and 42 g 4 % 15 min → 11.2, Gb 1.038,
    19 L, total 41.5, each within 1. `test_ibu_joe_ale_us`: 1 oz and 1.5 oz in 5 gal → 30.8 and 11.4.
  - `test_ibu_no_hops_is_zero` (edge case, R7).
  - `test_whirlpool_and_dry_hop_add_no_ibu`: Joe Ale plus a 50 g whirlpool and a 100 g dry hop
    gives the same IBU (A8).
  - `test_ibu_unknown_usage_raises`.
- [x] Apply twice, then run `pytest tests/test_maths.py`.
Done when: the tests pass.
Commit: `Add Tinseth IBU maths with tests`

### Task 5: Colour (MCU, Morey, EBC)
Why: R5, A2.
- [x] Add `mcu`, `grist_mcu` and `srm`.
- [x] Write tests. Inputs are given in °L, converted × 1.97 to EBC, and MCU is checked to 0.01:
  - `test_mcu_palmer_simple`: 8 lb at 2 °L + 2 lb at 4 °L in 5 gal → 4.8 MCU (p. 469).
  - `test_srm_shay_steam`: 12 MCU → 8 SRM; `test_srm_port_o_palmer`: 72 MCU → 28 SRM;
    `test_srm_port_o_palmer_more_chocolate`: 107 MCU → 37 SRM (p. 472–473), SRM within 1.
  - `test_mcu_obc_pils`: 4.0 MCU, and SRM within 1 of 4.
  - `test_mcu_obc_dubbel`: 40.5 MCU, recomputed from the book's rows. The book's printed 43 is
    its own arithmetic slip (named in doc-calc.md), so the test asserts 40.5.
  - `test_ebc_srm_round_trip` and `test_colour_missing_ebc_raises`.
- [x] Apply twice, then run `pytest tests/test_maths.py`.
Done when: the tests pass.
Commit: `Add Morey colour maths with tests`

### Task 6: Solvers
Why: R4, R6, R7 edge cases, A3, A4.
- [ ] Add `solve_grist` and `solve_hops`. Both are closed form, because OG and IBU are linear in
  mass. kg_i = pct_i/Σpct × M, where M = target points × L / Σ(pct_i/Σpct × extract_i × 3.84 × eff_i).
  The hop solver works the same way for grams.
- [ ] Write tests:
  - `test_solve_grist_round_trip`: target 1.060, grist 80 % pale (extract 80 %), 10 % Munich
    (75 %), 10 % crystal (74 %), efficiency 75 %, 20 L → `og` of the result within 0.001 of 1.060 (A4).
  - `test_solve_hops_round_trip`: target 50 IBU, 60/15/0 min boil plus a dry hop, then
    `boil_gravity` from `preboil_volume`, `ibu` of the result within 1 of 50 (A4).
  - `test_lactose_raises_fg_candi_lowers_it` (A3): three grists, each solved to OG 1.060 at 75 %
    attenuation: 100 % pale, 90 % pale + 10 % lactose, and 90 % pale + 10 % candi. Expect
    FG(lactose) > FG(pale) > FG(candi).
  - `test_solve_grist_all_sugar`: 100 % sugar, not mashed, round-trips at any efficiency (edge case).
  - `test_solve_hops_without_boil_addition_raises`, and `test_solve_hops_zero_target`.
- [ ] Apply twice, then run `pytest tests/test_maths.py`.
Done when: the tests pass.
Commit: `Add grist and hop solvers with tests`

### Task 7: Check a maths function through n8n's Postgres node
Why: R8, A5.
- [ ] Query `pg_proc` for every function in `db/030_maths.sql`. Expect each one owned by `postgres`.
- [ ] Through the n8n MCP (official server, SDK reference first), create a workflow
  `Maths check`: a manual trigger and one Postgres node with the existing `Postgres account`
  credential, running the Joe Ale metric `select app.ibu('[…]'::jsonb, 1.038, 19) as ibu`.
  Execute it once with the MCP (`execute_workflow` / `test_workflow`). If the MCP cannot run it,
  use the headless command in OPERATIONS.md §5.
- [ ] Compare the result with `test_ibu_joe_ale_metric`'s computed value (the same digits).
  Record the execution id and the number in this plan's Deviations (or verification later),
  then archive the workflow. It has no pipeline role, and m6 makes the real calls.
Done when: the n8n result equals the SQL result from pytest, and the evidence is written down.
Commit: `Record n8n check of maths functions` (docs only)

### Task 8: Docs and full run
Why: CLAUDE.md, PROJECT.md §10, G-M.
- [ ] Run the full `pytest`, and record the measured counts.
- [ ] PROJECT.md: in §4, the Database row (maths functions in `db/030_maths.sql`, `calc_version`
  `maths-1`) and the Scripts row (the test count); in §5, the *How to Brew* row (doc → calc for
  gravity, IBU, colour, ABV, °P: link doc-calc.md), the OBC row (downloaded 2026-10-14, doc → calc
  done, OG and MCU tested) and the pending-files sentence; a §8 entry.
- [ ] RECIPE-ROADMAP §8 P2 "done" line, and WORKFLOW-ROADMAP G-M "Measured" line, each with numbers.
Done when: the docs state measured results only.
Commit: `Update docs for s1-maths`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| OG from grist matches Palmer and OBC | `test_og_palmer_*`, `test_og_obc_dubbel`, `test_og_obc_pils` | 2 |
| Efficiency never applied to sugars and extracts | `test_efficiency_skips_unmashed` | 2 |
| Boil gravity and pre-boil volume (Tinseth input) | `test_boil_gravity_joe_ale`, `test_preboil_volume_example` | 2 |
| °P round trip | `test_plato_round_trip` | 2 |
| FG follows attenuation and fermentability | `test_fg_table_4_3`, `test_lactose_raises_fg_candi_lowers_it` | 3, 6 |
| ABV matches table 9.1 | `test_abv_table_9_1` | 3 |
| Tinseth utilisation and IBU | `test_tinseth_table_5_5`, `test_ibu_joe_ale_*` | 4 |
| Whirlpool and dry hop add 0 IBU | `test_whirlpool_and_dry_hop_add_no_ibu` | 4 |
| MCU and Morey colour | `test_mcu_*`, `test_srm_*` | 5 |
| Solvers invert the forward maths | `test_solve_grist_round_trip`, `test_solve_hops_round_trip` | 6 |
| Same number through n8n | Task 7 check (manual, recorded) | 7 |

## Approved exceptions

None.

## Deviations
- 2026-10-14 · Approach, Task 1, Task 5: OBC's examples are tested for OG and MCU only (the Dubbel
  MCU against the recomputed 40.5, with the book's 35.25 / 43 slip documented). Its SRM and IBU
  figures are written up in doc-calc.md as Daniels' model and not tested. This was the user's
  answer, and brief A2 was narrowed in the same change.
- 2026-10-14 · Task 3: table 4.3's ABV row is not tested. It disagrees with table 9.1 and matches no
  formula. Its FG row is tested. The brief's Assumptions were updated to match.
- 2026-10-14 · Task 1: the 131.25 × (OG − FG) ABV form misses 65 of table 9.1's 140 cells (worst 0.194), not 56 as the source check said. The Balling form still fits 140/140 (worst 0.088). Choice unchanged.
- 2026-10-14 · Task 2: add `test_boil_gravity_book_example` (HTB p. 291: 5 gal at 1.050, 6 gal pre-boil → 1.042, 7 gal → 1.036), cited in doc-calc.md section 2. It is a second boil-gravity check beside `test_boil_gravity_joe_ale`.
