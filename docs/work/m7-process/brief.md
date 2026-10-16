# M7 · Steps 12–15: water, mash and boil, fermentation, packaging

Status: draft
Slug: m7-process · Branch: m7-process
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) M7 · [RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md)
§3 steps 12–15, §6, §8 P6
Needs: `m6-compute-validate` and `s5-mash-attenuation` shipped. Sources, all in place
(checked 2026-10-16, per-file fates in [SOURCES.md](../../SOURCES.md)): `books/how_to_brew.pdf`,
`books/palmer_kaminski_water.pdf`, `books/white_zainasheff_yeast.pdf`,
`books/bjcp_exam_study_guide_2017.pdf`, `water/`, `articles/` (all under `shared/rag-files/`)

## Why
After M6 a recipe says what goes in, not how to brew it. A brewer also needs salt additions,
a mash and boil schedule, a fermentation plan and carbonation. These are mostly tables and
formulas in Palmer, *Water* and *Yeast*, so by PROJECT.md §6.7 they become data and code, not
LLM text. RECIPE-ROADMAP P6 is done when every recipe has all four.

## Goal
Every validated recipe gets a process, computed by code from sourced tables and formulas, stored
in `app.recipe.process`: water salts in grams, mash steps and boil, fermentation schedule, and
carbonation with priming sugar.

## Scope
In:
- A doc → calculation pass on Palmer (water, carbonation chapters), *Water* and *Yeast* for what
  these steps need, written up in this folder (`doc-calc.md`). Also in the pass: the BJCP study
  guide's 8-city ion table (§IV.B, readable copy `water/bjcp_study_guide_water.md`), Bru'n Water's
  *Water Knowledge* (`water/brunwater_water_knowledge.md`), Janish's dry-hop paper and post
  (`articles/janish_dry_hop_best_practices_tq_2021.pdf`, `articles/janish_short_cool_dry_hopping.md`)
  and the Milk The Funk souring pages (`articles/mtf_*.md`).
- Step 12 water: target ion profile per style and hints (SO₄:Cl), salt grams from the source water
  ions and `ref.water_salt`; residual alkalinity or mash pH estimate. Expected values for the test
  cases may come from running the Bru'n Water 1.25 spreadsheet (`water/brunwater_1.25.xlsx`) by
  hand; its formulas are not copied (© all rights reserved).
- Step 13 mash and boil: mash temperature from the M4 target (whose effect on FG is
  `s5-mash-attenuation`'s model), rests where the style calls for them (with a source), boil length
  (e.g. longer for pilsner malt), hop schedule from M5/M6.
- Step 14 fermentation: temperature from the yeast's range and the style, rests (diacetyl for
  lagers), dry-hop day, temperature and contact time (Janish), cold crash, lagering; pitch rate from
  *Yeast*; a souring schedule for b14 (Berliner Weisse) per M5's answer, from the Milk The Funk
  pages.
- Step 15 packaging: CO₂ volumes per style (`ref.beer_style.co2_vol`, back with a source,
  DATABASE.md §9) and priming sugar grams.
- Brief check: a small `process` expectation for the briefs that need one (WORKFLOW-ROADMAP §3).

Out:
- Kegging and force-carb tables beyond priming. Mash pH from a full titration model if the
  books' simpler estimate suffices. Equipment profiles beyond `app.brewer_profile`.

## Requirements
R1. Every formula and table used is listed in `doc-calc.md` with book, chapter and page, and is
    code or `ref` data with tests; nothing is LLM-generated.
R2. Step 12 outputs salt grams per addition, the resulting ion profile, and the target it aimed
    for with its source; amounts never negative; with no salts needed it says so.
R3. Step 13 outputs mash steps (°C, minutes), mash-out if used, boil minutes, and the hop schedule
    in time order, from the recipe rows.
R4. Step 14 outputs fermentation steps (°C, days) inside the chosen yeast's `temp_c` range, plus
    rests and dry-hop timing where they apply, and pitch rate.
R5. Step 15 outputs CO₂ volumes from the style with its source, and priming sugar grams for the
    batch volume and beer temperature.
R6. The four outputs are stored in `app.recipe.process` and logged as `run_step` 12–15.
R7. The briefs that need it get a `process` expectation (e.g. b13 weizen temperature band, a lager
    schedule, b14 souring per M5's answer), approved by you, and the runner grades it.

## Constraints
- PROJECT.md §6.7: doc → calculation first; only prose goes to `kb` (s4).
- DB changes (`co2_vol`) as `.sql` files applied as `postgres`; values with a source.
- RECIPE-ROADMAP §6 lists where each piece comes from.

## Assumptions
- Palmer has a carbonation-by-style table usable for `co2_vol` *(RECIPE-ROADMAP §6 says ch. 11;
  not checked in this edition)*.

## Acceptance criteria
A1. `doc-calc.md` exists and each listed item maps to a tested function or `ref` column (R1).
A2. All validated recipes have water, mash, boil, fermentation and packaging in `process` (R6,
    RECIPE-ROADMAP P6).
A3. A test reproduces one worked salt-addition example from *Water* or Palmer within tolerance
    (R2).
A4. Every fermentation temperature is inside its yeast's range; lager recipes have a diacetyl
    rest (R4).
A5. Priming sugar for a test case matches a worked example from Palmer within ± 5 % (R5).
A6. The `process` expectations pass for the briefs that have them (R7).

## Open questions
1. Water target profiles: from where? — options: a) style-based targets from *Water* (or Palmer's
   style table), moved by hints (bitter → more sulfate); b) only SO₄:Cl ratio bands; c) the
   classic city profiles (BJCP study guide's 8-city table) as targets for their home styles —
   recommend a if the book has a table, else b; c only as a check of a's numbers.

## Deviations
- 2026-10-16 · Needs, Scope, Assumptions, Open questions: sources now named by path; BJCP water
  table, Bru'n Water *Water Knowledge* (calc) and spreadsheet (test oracle only), Janish dry-hop
  sources and Milk The Funk souring pages added; needs `s5-mash-attenuation`; the "PDF not
  available" assumption and question dropped (all files present) — user asked to place the new
  sources ([SOURCES.md](../../SOURCES.md)).
