# M7 · Steps 12–15: water, mash and boil, fermentation, packaging

Status: approved
Slug: m7-process · Branch: m7-process
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) M7 · [RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md)
§3 steps 12–15, §6, §8 P6
Needs: `m6-compute-validate` (shipped 2026-10-27) and `s5-mash-attenuation` (shipped
2026-10-17). Sources, all in place (checked 2026-10-27, per-file fates in
[SOURCES.md](../../SOURCES.md)): `books/how_to_brew.pdf`, `books/palmer_kaminski_water.pdf`,
`books/white_zainasheff_yeast.pdf`, `books/bjcp_exam_study_guide_2017.pdf`, `water/`,
`articles/` (all under `shared/rag-files/`)

## Why
After M6 a recipe says what goes in, not how to brew it. A brewer also needs salt additions,
a mash and boil schedule, a fermentation plan and carbonation. These are mostly tables and
formulas in Palmer, *Water* and *Yeast*, so by PROJECT.md §6.7 they become data and code, not
LLM text. RECIPE-ROADMAP P6 is done when every recipe has all four; G7 and M8's recipe sheet
wait for it.

## Goal
Every validated recipe gets a process, computed by code from sourced tables and formulas, stored
in `app.recipe.process`: water salts in grams, mash steps and boil, fermentation schedule, and
carbonation with priming sugar.

## What is already there (measured 2026-10-27)
- `app.recipe.process` (jsonb) exists; 0 of the 40 saved recipes have it filled.
- `app.run_step` has steps 0–11 logged, none of 12–15.
- Step 10 already decides the **mash temperature** (`step10.mash_c`: step 4's target, raised
  inside 68.3–69 °C for a low FG, never a brewer's hint) and the **boil time** (`step10.boil`,
  `app.step10_boil`: the largest of 60 min, the grist's `min_boil_min` (rule 13, e.g. 90 min for
  Pilsner malt) and the longest boil addition, with the bittering hop set to it). FG and IBU are
  computed from these two values. Neither is saved with the recipe: `app.save_recipe` leaves
  them in the step 10 row; m6 left saving them to M7.
- Step 10 writes every yeast row (main yeast and souring culture) as `1 pack`, a placeholder
  until M7 sets the pitch rate (m6 plan). `step10.ferm_c` is the temperature of step 6's chosen
  ferment option from `app.ingredient_choices` (e.g. US-05: 18, 21 or 28 °C).
- b14 (23A) now has a souring culture: step 6 picks YF-998 or YF-999 (`ref.yeast.type` `lacto`,
  2 rows), per M5's answer.
- `ref.yeast`: 17 lager, 75 ale, 20 kveik, 2 brett, 2 lacto rows, each with `temp_c` and `form`
  (dry or liquid); no cell count or pack size.
- `ref.water_salt`: 8 salts with ion mg/L per g (gypsum, calcium chloride, epsom, magnesium
  chloride, table salt, baking soda, chalk, slaked lime). No acid is in `ref`.
- `app.brewer_profile` `default`: six ions, all 0 mg/L (distilled water, Bru'n Water §4.2.1);
  20 L, 72 %, boil-off 4 L/h, losses 2 L, grain absorption 1.0 L/kg. Setting your own ions is a
  RECIPE-ROADMAP §8 Later TODO.
- `ref.beer_style` has no `co2_vol` column (dropped in slim-ref; DATABASE.md §9 lists it for P6).
- `ref.misc`: 4 rows, all flavour (coffee ×2, vanilla, orange peel); no process aid.
- The sources have what the steps need: *How to Brew* ch. 10 "Priming" (Tables 10.1–10.3, and a
  list of CO₂ volumes for 8 style families, p. 159); *Water* ch. 7, Tables 18a/b and 19a/b,
  "Suggested Water Profiles" for lager and ale styles (Ca, alkalinity, sulfate, chloride,
  Kolbach RA, an "acidify" flag and example styles per row), and three worked examples (American
  pale ale, Pilsner, Foreign Extra Stout); *Water* ch. 4–5 (residual alkalinity, malt acidity,
  mash pH); *Yeast*, "Pitching Rates" (0.75 million cells/mL/°P for ales, 1.5 for lagers, and a
  worked example; dry yeast 7–20 billion cells/g) and "Diacetyl Rest".

## Scope
In:
- A doc → calculation pass on Palmer (water, priming chapters), *Water* and *Yeast* for what
  these steps need, written up in this folder (`doc-calc.md`). Also in the pass: the BJCP study
  guide's 8-city ion table (§IV.B, readable copy `water/bjcp_study_guide_water.md`), Bru'n Water's
  *Water Knowledge* (`water/brunwater_water_knowledge.md`), Janish's dry-hop paper and post
  (`articles/janish_dry_hop_best_practices_tq_2021.pdf`, `articles/janish_short_cool_dry_hopping.md`)
  and the Milk The Funk souring pages (`articles/mtf_berliner_weissbier.md`,
  `articles/mtf_lactobacillus_fermentation.md`).
- Step 12 water: target ion profile from *Water*'s Tables 18a/b and 19a/b (ch. 7), each style
  mapped to one row (type, colour, bitterness) in a table you review, and moved inside that row's
  ranges by hints (bitter → more sulfate, SO₄:Cl); salt grams from the source water ions (the
  brewer profile's six ions) and `ref.water_salt`, dosed for step 13's strike and sparge volumes;
  residual alkalinity and a mash pH estimate, saying when acid would be needed (no acid is dosed).
  The BJCP 8-city table is only a check of the targets. Expected values for the test cases may come from running the Bru'n Water 1.25
  spreadsheet (`water/brunwater_1.25.xlsx`) by hand; its formulas are not copied (© all rights
  reserved).
- Step 13 mash and boil: a single infusion at the mash temperature step 10 used, plus mash-out,
  and the boil time step 10 used (neither decided again); rests that do not change
  fermentability (ferulic-acid, protein, beta-glucan) where a source ties them to the style or to
  an ingredient in the grist, so rule 10's FG model is unchanged; strike and sparge water volumes
  from the brewer profile (grain absorption, boil-off, losses) with s1's volume functions; the
  strike water temperature (*How to Brew* ch. 17's infusion equation); and the hop and extras
  schedule in time order from the recipe rows (boil minutes, whirlpool).
- Step 14 fermentation: temperature from the yeast's range and the style, starting from step 6's
  chosen ferment option (a ramp, not one flat temperature: the G6 review found 15 C too cool for
  b03 and wanted b10 to start at 17-18 C and rise to 21-23 C,
  [`g6-recipes.md`](../../finished/m6-compute-validate/g6-recipes.md)), rests (diacetyl for
  lagers), dry-hop day, temperature and contact time (Janish), secondary extras (e.g. coffee
  beans, vanilla) at their usage and time, cold crash, lagering; pitch rate from *Yeast*, which
  replaces step 10's `1 pack` placeholder on the yeast rows; a souring schedule for b14 (Berliner
  Weisse) with the souring culture step 6 picked, from the Milk The Funk pages.
- Step 15 packaging: CO₂ volumes per style (`ref.beer_style.co2_vol`, back with a source:
  *How to Brew* ch. 10's 8 style families, each style mapped to a family in a table you review),
  priming sugar grams, and packaging extras (e.g. cold brew coffee).
- Saving: the four outputs go to `app.recipe.process`, together with step 10's mash and boil.
- Brief check: a small `process` expectation for the briefs that need one (WORKFLOW-ROADMAP §3).
- Docs: RECIPE-ROADMAP §3 rows 12–15, §6 and §8 P6, WORKFLOW-ROADMAP M7, PROJECT.md §5 source
  rows and DATABASE.md describe what is built (§6 currently says Palmer ch. 11 for carbonation;
  it is ch. 10).

Out:
- Kegging and force-carb tables beyond priming. Mash pH from a full titration model if the
  books' simpler estimate suffices. Equipment profiles beyond `app.brewer_profile`.
- Changing step 10's mash or boil time, or re-running steps 10–11 from step 13.
- A mash schedule that changes the predicted FG (multi-step mash profiles, decoction): a
  RECIPE-ROADMAP §8 Later TODO.
- Yeast starters, and setting your own water ions (Later TODO).
- Acid additions (lactic acid, acidulated malt) and their maths (*Water* ch. 6): step 12 only
  says when acid would be needed. Can follow as its own work item.
- Process aids (Irish moss, nutrient): INGREDIENT-INTAKE Q10 stays open; M7 places only the
  recipe's own extras.
- Prose about the process (M8, step 16).

## Requirements
R1. Every formula and table used is listed in `doc-calc.md` with book, chapter and page, and is
    code or `ref` data with tests; nothing is LLM-generated.
R2. Step 12 outputs salt grams per addition, split between strike and sparge water, the
    resulting ion profile, and the target it aimed for (the *Water* Table 18/19 row the style
    maps to, with its source and the hint that moved it); amounts never negative; with no salts
    needed it says so. It also outputs the residual alkalinity and the estimated mash pH, and says
    when acid would be needed to reach the target pH; it doses no acid.
R3. Step 13 outputs mash steps (°C, minutes): a single infusion at step 10's `mash_c`, plus any
    rest that does not change fermentability where a source ties it to the style or an
    ingredient, each with its source; a mash-out; boil minutes equal to step 10's
    `boil.boil_min`; strike and sparge water volumes (L) from the brewer profile; the strike
    water temperature (°C); and the hop and extras schedule in time order, from the recipe rows.
R4. Step 14 outputs fermentation steps (°C, days) inside the chosen yeast's `temp_c` range, plus
    rests, dry-hop timing and secondary extras where they apply, the souring schedule where a
    souring culture was picked, and pitch rate (cells needed and the yeast amount, which replaces
    the `1 pack` placeholder in the saved yeast rows).
R5. Step 15 outputs CO₂ volumes from the style with its source, and priming sugar grams for the
    batch volume and beer temperature.
R6. The four outputs, with step 10's mash and boil, are stored in `app.recipe.process` and logged
    as `run_step` 12–15.
R7. The briefs that need it get a `process` expectation (e.g. b13 weizen temperature band, a lager
    schedule, b14 souring), approved by you, and the runner grades it.

## Constraints
- PROJECT.md §6.7: doc → calculation first; only prose goes to `kb` (s4).
- CLAUDE.md: brewing maths is deterministic, tested code; the LLM computes nothing in these steps.
- PROJECT.md §6.3: each output has a legal "none / unknown" (e.g. no salts needed, no rest, a
  yeast with no sourced cell count).
- PROJECT.md §6.8: readable over optimal.
- DB changes (`co2_vol`, any new function or column) as `.sql` files applied as `postgres`;
  values with a source.
- RECIPE-ROADMAP §6 lists where each piece comes from.
- The Bru'n Water spreadsheet is a test oracle only; its formulas are not copied.

## Assumptions
- *How to Brew*'s 8 style families cover every style a recipe can get once each style is mapped
  to one *(the mapping is new and reviewed by you)*.
- A sourced cell count per pack or per gram exists for the yeasts the briefs use (makers' data
  sheets, or *How to Brew*'s 10 billion cells/g for dry yeast and 100 billion per liquid package)
  *(unverified per product)*.
- *Water*'s Tables 18–19 rows can be matched to a recipe from its style, colour and bitterness
  *(unverified until the doc → calc pass)*.

## Acceptance criteria
A1. `doc-calc.md` exists and each listed item maps to a tested function or `ref` column (R1).
A2. All validated recipes of a full brief run have water, mash, boil, fermentation and packaging
    in `process`, and `run_step` rows 12–15 (R6, RECIPE-ROADMAP P6).
A3. A test reproduces one worked salt-addition example from *Water* ch. 7 (American pale ale,
    Pilsner or Foreign Extra Stout) or Palmer within tolerance (R2).
A4. Every fermentation temperature is inside its yeast's range; recipes whose main yeast is
    `type` lager have a diacetyl rest (R4).
A5. Priming sugar for a test case matches a worked example from Palmer within ± 5 % (R5).
A6. The `process` expectations pass for the briefs that have them (R7).
A7. Each saved recipe's `process` mash and boil equal its step 10 `mash_c` and `boil.boil_min`,
    and its yeast rows no longer say `1 pack` unless the pitch rate gives one pack or none is
    sourced (a souring culture is pitched at *How to Brew* p. 206's rate) (R3, R4, R6).
A8. A test reproduces the pitching-rate worked example in *How to Brew* ch. 7, Table 7.1 (p. 114:
    1.050 SG, 0.75 billion cells/L/°P, 20 L = 180 billion cells) (R4).
A9. Every saved recipe's water target names its *Water* Table 18/19 row; a test checks the
    style-to-row table covers every style a b01–b24 recipe gets; the BJCP 8-city table is used
    only as a check in a test (R2).
A10. A test case with a pale grist on distilled water gets a mash pH estimate above the target
     (*How to Brew* p. 341/365: pale 5.2-5.4, amber 5.3-5.5, dark 5.4-5.6; 5.2-5.6 when the style
     has no water row) and an "acid would be needed" line; no output holds an acid amount (R2).
A11. No mash step changes the recipe's FG: after steps 12–15 every saved recipe's `fg` still
     equals its step 10 FG, and every rest besides the infusion and mash-out has a source (R3).
A12. A test reproduces strike and sparge volumes for a test case from s1's volume functions and
     the profile, and step 12's salt grams are for those volumes (R2, R3).

## Open questions
None open. Decided by you, 2026-10-27:
1. Water target profiles: *Water*'s Tables 18a/b and 19a/b (ch. 7), each style mapped to a row
   and moved by hints ("Water tables"). The BJCP 8-city table is a check only.
2. Acid: salts only; step 12 reports the estimated mash pH and says when acid would be needed,
   no acid dosing ("Salts only").
3. Mash rests: a single infusion at step 10's mash plus mash-out, plus rests that do not change
   fermentability (ferulic, protein, beta-glucan) where a source ties them to a style or
   ingredient; rule 10's FG model unchanged ("Plus neutral rests").
4. Process aids: INGREDIENT-INTAKE Q10 stays open; M7 places only the recipe's own extras ("Leave
   Q10 open").
5. Water volumes: step 13 outputs strike and sparge volumes from the profile with s1's volume
   functions, and step 12 doses salts for them ("Strike + sparge").

## Deviations
- 2026-10-16 · Needs, Scope, Assumptions, Open questions: sources now named by path; BJCP water
  table, Bru'n Water *Water Knowledge* (calc) and spreadsheet (test oracle only), Janish dry-hop
  sources and Milk The Funk souring pages added; needs `s5-mash-attenuation`; the "PDF not
  available" assumption and question dropped (all files present) — user asked to place the new
  sources ([SOURCES.md](../../SOURCES.md)).
- 2026-10-27 · Needs, new "What is already there", Scope, R3, R6, A7: step 13 takes the mash and
  boil time step 10 used instead of choosing a boil length, and saves both in `process` — m6
  shipped with step 10 deciding them (rule 13 already gives Pilsner malt 90 min) and FG and IBU
  depend on them; m6 left saving them to M7.
- 2026-10-27 · Scope, R4, A7, A8: the pitch rate sets the yeast amount and replaces step 10's
  `1 pack` placeholder — m6 wrote the placeholder for M7 to replace.
- 2026-10-27 · Scope, R3, R4: extras (whirlpool, secondary, packaging usages) appear in the
  schedule at their usage and time; step 14 starts from step 6's chosen ferment option; b14's
  souring uses the culture step 6 picks (YF-998/YF-999) — INGREDIENT-INTAKE's M7 row and M5's
  answer, now built.
- 2026-10-27 · Scope, Assumptions, Open question 1: carbonation is *How to Brew* ch. 10, not
  ch. 11, and gives 8 style families rather than a per-style table, so `co2_vol` needs a reviewed
  style-to-family mapping; *Water* has style tables (18a/b, 19a/b), so question 1 now recommends
  a without the "if the book has a table" condition — checked in the PDFs.
- 2026-10-27 · Out, Open questions 2–5: acid, mash rests, process aids and water volumes raised
  as questions; starters, own water ions and FG-changing mash schedules named as out — found
  while checking against the shipped work; scope waits for your answers.
- 2026-10-27 · Scope (steps 12 and 13), Out, R2, R3, new A9–A12, Open questions: your answers
  to questions 1–5 written in — water targets from *Water* Tables 18–19 mapped per style; salts
  only, with a mash pH estimate and an "acid needed" line; neutral rests added beside the single
  infusion and mash-out, FG model unchanged; process aids out (Q10 open); strike and sparge
  volumes in step 13, salts dosed for them — user decisions in chat.
- 2026-10-28 · Scope (step 13), R3, A7: step 13 also outputs the strike water temperature
  (*How to Brew* ch. 17 infusion equation); A7 allows `1 pack` where no pitch rate is sourced, so
  the souring culture keeps `1 pack` marked "no sourced pitch rate"; styles outside the reviewed
  tables get no water row (no salts) and Palmer's default 2.5 CO₂ volumes, wider coverage a Later
  TODO — user answers to the plan's questions 1–3 in chat.
- 2026-10-28 · Assumptions, A7, A8, A10: user answers to the doc-calc gate, under the new rule that
  *How to Brew* is the source of truth for brewing method. A7: the souring culture is pitched at HTB
  p. 206's rate (100-200 billion cells per 19 L), not `1 pack`. A8: the worked example is HTB Table 7.1
  (180 billion cells, same number as *Yeast*'s). A10: "the target" is HTB's mash pH target by colour.
  The cell-count assumption cites HTB.
