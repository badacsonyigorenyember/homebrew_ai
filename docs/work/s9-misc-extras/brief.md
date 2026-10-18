# S9 · Misc extras: spices, fruit, coffee and process aids through the pipeline

Status: approved
Slug: s9-misc-extras · Branch: s9-misc-extras
Design: [INGREDIENT-INTAKE.md](../../INGREDIENT-INTAKE.md) §3, §4, §8, §9, §11 (rows marked s9)
Needs: `s8-ingredient-intake` (shipped 2026-10-17, [`docs/finished/`](../../finished/s8-ingredient-intake/verification.md))
and `m4-targets-blueprint` (shipped 2026-10-17, [`docs/finished/`](../../finished/m4-targets-blueprint/verification.md)).
m4 shipped before s9, as INGREDIENT-INTAKE Q7 b proposed; s9 comes before `m5-choose-ingredients`,
whose step 9 needs misc rows. `s10-ingredient-form` builds on this.

## Blocked by
Revised 2026-10-18 against what s8 and m4 built, then against your answers of the same day.

| # | Blocker | Status | Blocks | Cleared when |
|---|---|---|---|---|
| B1 | s8 not built | **Cleared.** s8 shipped on 2026-10-17. Names and paths below are what it built. | — | — |
| B2 | Open questions unanswered | **Cleared.** You answered all five on 2026-10-18 (Open questions below). | — | — |
| B3 | **Dose sources are partly unverified.** No doc → calc pass has been done for misc. Coffee: `janish-coffee-beers` gives one data point per form for a 5-gallon batch: dry-beaned whole beans 2 oz for 48 h (about 3.0 g/L) and cold brew 4 oz coarse ground in 1,200 mL for 16 h (about 6.0 g/L) *(read in `shared/rag-files/articles/janish_coffee_beers.md`, 2026-10-18)*. These are "noticeable" anchors, not ranges. Vanilla and orange peel: candidate *How to Brew* ch. 13 "Fruit, spices" (PDF pp. 217–230; its tables on pp. 217–219, 221–225 and 227–228 were cut from `kb`, BOOKS.md §3, so the PDF must be read); what it states is unverified. | **Stands** | the tasks after the plan's doc → calc task (cut points, the three entries). Not approval or planning. | the doc → calc pass shows what each source states, and you accept it. The subtle and aggressive cut points need a second source or your judgment, as in s3 (`basis: "set by the user"`). A product with no sourced dose loads with dose `NULL` (R15). |
| B4 | **New test briefs and envelopes need your review.** The new test briefs change P0, so you approve them; every envelope is reviewed by you before it enters `ref` (D9). | **Stands** | the tasks that add the briefs and the envelopes, and verification | you approve the briefs and review the envelopes during the work |

## Why
`ref.misc` has 0 rows and two columns, `ingredient_id` and `category`. The category check
allows 10 values. Misc words in a brief ("coffee", "cinnamon") come out of step 3 as `unrated`,
and `app.style_level` raises an error for a misc ingredient. Step 2 maps only honey and molasses
to a specialty style, and process aids (Irish moss, yeast nutrient) have no place at all
(INGREDIENT-INTAKE G5–G8; measured 2026-10-18). The s8 intake checker refuses misc files
("misc arrives in s9"). You want to fill misc yourself from intake files (decided 2026-10-17).
M5–M8 need misc rows to build their extras, amounts, schedule and sheet.

## Goal
A flavour misc or a process aid added as one intake file is usable in steps 2, 3 and 5. A
wanted spice or coffee gets a style-fit level with a reason. A `feature` extra moves step 2 to
its specialty style, and a process aid is neutral in every style. After this, a new spice needs
only its file, not code.

## How a flavour misc is read (your model, 2026-10-18)
Misc here is the added product (coffee beans, cacao nibs), not a flavour that comes from malt.
A flavour misc is read on three layers:

1. **Category (the cause) drives step 2.** The category gives the specialty style: fruit →
   29A; spice, herb, coffee, cacao, vanilla → 30A; wood → 33A; smoke → 32A. The base style
   stays the first alternative.
2. **Added-character dimension (the effect) is scored in step 3.** Each flavour misc scores on
   exactly one of the four existing specialty dimensions: `fruit`, `spice` (BJCP's spice, herb
   or vegetable), `wood` or `smoke`. Its dose gives the intensity, in BJCP's words from 29A,
   30A and 33A (subtle, noticeable, aggressive), through cut points with a source. Coffee and
   cacao do not drive `roast`, and vanilla does not drive `sweetness`.
3. **Character tags describe the taste.** Tags such as `coffee`, `chocolate`, `vanilla`,
   `cinnamon` and `citrus` (flavour-wheel words) explain a choice and help match brief words.
   They are never scored. One tag can sit on products of different categories, e.g. `vanilla`
   on a vanilla pod (`spice`) and on oak chips (`wood`).

## Scope
In:
- `ref.misc` gains `purpose` (`flavour` · `process`), `usages`, `time_min`, `dose_g_per_l`,
  `description` and `field_source`, with the categories and usages of decision 1.
- Misc in the s8 intake path:
  - a `shared/ingredients/misc/` folder;
  - a template for a flavour misc and one for a process aid in `shared/ingredients/_templates/`;
  - `load_misc` in `loaders/extra_ingredients.py`;
  - the checker accepting misc files instead of refusing them;
  - misc in the load summary, with its "waits for maths" and "waits" lines (decisions 2 and 5),
    and in `db/checks/ref_spotcheck.sql`;
  - `shared/ingredients/README.md` covering misc.
- One misc entry per form of a product (decision 5). Each form has its own dose, time and
  usage.
- The tagger (`loaders/tags.py`) gets a misc branch for intake rows. A flavour misc gets a family
  tag from its category, which needs new family tags in `loaders/style_fit_vocab.toml`, and
  character tags from its descriptor words. New character tags are added to the vocabulary as
  the entries need them (`cinnamon` is not a tag today, measured). A process aid gets no tags.
- Misc kind words (`spice`, `fruit`, …) in `app.ingredient_kind_word()` (`db/036`). Misc aliases
  use s8's `ref.ingredient_alias` unchanged.
- Style fit for flavour misc (layer 2):
  - rows in `app.usage_effects()`, one dimension per flavour category;
  - dose → intensity cut points in `app.style_fit_cut_points()`, each with a source;
  - `app.style_level` accepting misc usages;
  - `app.ingredient_choices` giving misc choices from the row's usages;
  - `app.style_fit_recipe` taking an extras list.
- Process aids are `allowed` in every style with "no flavour effect", and never a deviation.
  Categories that change the numbers (`enzyme`, `acid`) load and are marked "waits for maths".
- Step 2 (layer 1): `app.specialty_style()` by the misc category of the resolved product,
  keeping the honey and molasses rows.
- Step 5: a misc product in a slot carries its purpose, usages, time and dose range from the
  misc row (decision 4).
- Envelopes (`loaders/style_envelopes.toml`) for the specialty styles the new test briefs need,
  extracted and reviewed as in s3.
- New recipe test briefs with extras in `evals/recipe_briefs.toml`, approved by you. Proposed:
  a coffee-vanilla stout (a feature extra, so a specialty style) and a pale ale "with a little
  orange peel" (a background extra, so the base style plus a deviation). Steps 1–5 are measured
  on all briefs.
- The real misc entries those briefs need, from named sources: one coffee form (or both), a
  vanilla form and an orange peel form (decision 5). Process aids are proven by test fixtures
  only.
- A TODO, on RECIPE-ROADMAP's Later list, that fruit as a fermentable is decided with M6
  (decision 2).
- Docs updated: DATABASE.md (misc row, fill order), STYLE-FIT.md §2–§4 (the three layers),
  RECIPE-ROADMAP.md step 9 (it still says "corpus misc usage stats"), WORKFLOW-ROADMAP.md (no
  s8, s9 or s10 row or node yet, measured), INGREDIENT-INTAKE.md §12 (decided questions), and
  PROJECT.md.

Out:
- Real process-aid entries (Irish moss, yeast nutrient): added later through intake files,
  when a step needs them.
- Choosing extras and turning a brief's intensity into a dose (M5 step 9). The LLM never
  decides amounts: the brief gives an intensity, and code maps it to the row's sourced dose.
- Amounts in grams (M6) and the formulation-check contract's extras (M6).
- Placing extras and process aids in the schedule, and who adds process aids (M7, Q10).
- The sheet (M8).
- Maths for ingredients that change the numbers: enzymes, acids, and fruit sugar (decision 2).
- Liquid extracts dosed in mL/L (e.g. vanilla extract): marked "waits", loaded by a later work
  item (decision 5).
- Side effects on the base beer's dimensions (bitterness from some spices, drying from fruit),
  unless a source gives a number.
- New sensory dimensions.
- The n8n form (s10).

## Requirements
R1. `ref.misc` holds `purpose`, `category`, `usages`, `time_min`, `dose_g_per_l`,
    `description` and `field_source`. Usages are `mash`, `boil`, `whirlpool`, `ferment`,
    `secondary` and `packaging`. Flavour categories are `spice`, `herb`, `fruit`, `wood`,
    `coffee`, `cacao`, `vanilla`, `smoke` and `other`; process categories are `fining`,
    `nutrient`, `enzyme`, `acid` and `other-process`. The schema change is a `.sql` file applied
    as `postgres`.
R2. A misc intake file (flavour or process) in `shared/ingredients/misc/` passes `--check` and
    loads like the s8 kinds. Its required fields depend on its purpose (INGREDIENT-INTAKE §3).
    Every filled figure needs its `<field>_ref`, and every descriptor word must be a known tag or
    synonym. The load is idempotent. The load summary and the spot-check pack count misc rows.
R3. A flavour misc is tagged from its category and descriptor words. A process aid gets no
    tags, and it is neither flagged for review nor reported as untagged.
R4. `app.resolve_ingredient` finds a misc product by name, alias or kind word. A misc kind
    word restricts the kind, as `malt`, `hop` and `yeast` do.
R5. `app.style_level` returns a level and a reason for a flavour misc in each of its usages.
    The level comes only from its category's one added-character dimension (`fruit` for fruit;
    `spice` for spice, herb, coffee, cacao and vanilla; `wood`; `smoke`) and its dose → intensity
    cut points, each of which names a source. Character tags do not change the level. A misc in
    the flavour category `other` has no dimension, and `app.style_level` says so instead of
    guessing one.
R6. `app.style_level` returns `allowed` with "no flavour effect" for a process aid in any
    style.
R7. Step 3 rates a wanted misc word at its best choice, so it is no longer `unrated` when the
    product is in `ref`. It lists the word as a deviation when the best level is `out_of_style`
    or `changes_style`.
R8. Step 2 picks the specialty style for a `feature` misc by its category (fruit → 29A; spice,
    herb, coffee, cacao, vanilla → 30A; wood → 33A; smoke → 32A; and the BA equivalents), with
    the base style as the first alternative (step 4 takes a specialty style's ranges from it,
    m4 R9). A `background` misc, or a `feature` misc in `other`, leaves the base style.
R9. `app.style_fit_recipe` accepts an extras list and rates each extra as R5 and R6 do.
R10. The new test briefs are in `evals/recipe_briefs.toml` with their expected style and
     deviations, approved by you. Steps 1–5 pass on them, and stay at G4's level on the 22
     others (each step 22/22, measured 2026-10-17).
R11. The products the new test briefs need (coffee, vanilla, orange peel), one entry per form
     used, are loaded through intake files, each figure from a named source you accept.
     Process aids are loaded only as test fixtures, in rolled-back transactions.
R12. In step 5, a slot's misc product carries its purpose, usages, time and dose range from the
     misc row, and `step5.output` allows them.
R13. Fruit is flavour misc. A fruit file whose source gives a sugar content loads, and the load
     summary marks it "waits for maths" with the TODO "fruit as a fermentable is decided with
     M6". The same TODO is on RECIPE-ROADMAP's Later list.
R14. Each form of a product is its own misc entry (e.g. coffee whole beans dry-beaned, coffee
     cold brew), with its own dose, time and usages. A liquid form is dosed as g of dry product
     per L of beer where the source allows (cold brew: g coffee per L beer). A true liquid
     extract (e.g. vanilla extract) is reported as "waits" (no mL/L dose yet) and not loaded.
     Roast level and processing go in tags and description, never in the dose.
R15. A flavour misc without a sourced dose keeps `dose_g_per_l` `NULL`, and `app.style_level`
     and step 5 say "no sourced dose" instead of guessing an intensity or an amount.

## Constraints
- CLAUDE.md: readable over optimal. Usage effects and cut points stay code next to their tests,
  never a config table (DATABASE.md §8). Schema changes are `.sql` files applied as `postgres`,
  never through MCP. Brewing maths is deterministic, tested code.
- PROJECT.md §6.7: doc → calculation first. A dose or cut point without a source is not used.
- PROJECT.md §6.3: a missing dose or dimension has a legal "absent" value, never a guess.
- `ref` rules (DATABASE.md §2): sourced, SI units (g/L, minutes, days), unknown stays `NULL`,
  nothing guessed.
- Misc never enters OG, IBU or SRM (DATABASE.md §2).
- s8's intake rules hold for misc too: one file per ingredient, no LLM in the path, `--check`
  writes nothing, intake rows stay apart from loader rows, and fixtures load only in rolled-back
  test transactions.
- Envelopes are extracted offline by the D2 model and reviewed by you (D9).
- PROJECT.md §6.6: the pipeline change is measured on the fixed brief set.

## Assumptions
- *How to Brew* ch. 13 states usage and dose for vanilla and orange peel *(unverified, B3)*.
- Janish's two coffee points are a fair "noticeable" anchor for each form *(your reading,
  2026-10-18; the figures themselves were checked in the article)*.
- BJCP files coffee, cacao and vanilla under 30A, spice, herb or vegetable. Only a coffee stout
  among 30A's commercial examples was found so far (`ref.beer_style` raw, 2026-10-18). The rule
  itself would be in the BJCP 2021 specialty-type introduction, which is not in `styles.json`
  *(unverified; the plan's doc → calc task checks it)*.
- The four specialty dimensions (`spice`, `fruit`, `wood`, `smoke`) exist *(measured
  2026-10-18)*.
- The character tags the three entries need exist: `coffee`, `vanilla` and `orange` *(measured
  2026-10-18)*. The family facet has no misc tags yet *(measured)*.
- 29A, 30A, 32A and 33A have no vitals, so step 4 takes their ranges from the base style (m4
  R9). The 24 reviewed envelopes include none of the BJCP 29–34 specialty styles, and only 25B
  has a `spice` row *(measured 2026-10-18)*.
- A misc product already reaches a step 5 slot through `app.step5_refs`, with `role` and
  `max_pct` null *(read from `db/041`; not run with a misc row)*.

## Acceptance criteria
A1. `ref.misc` has the R1 columns, categories and usages, owned by `postgres` (R1).
A2. A flavour misc fixture and a process-aid fixture pass `--check` and load in a rolled-back
    transaction. Loading twice gives the same rows. A misc file missing a required field for its
    purpose is refused, naming file and field. The load summary and the spot-check pack show
    the misc rows (R2).
A3. The flavour fixture has its family and character tags. The process aid has none, is not
    flagged in the summary, and neither has an `ingredient_review` row (R3).
A4. `app.resolve_ingredient` returns the misc product for its name, each alias, and its kind
    word plus name, and no product of another kind (R4).
A5. For a flavour misc and a style whose envelope has its category's dimension,
    `app.style_level` gives a level and a reason for each usage. Each cut point used names its
    source in code. Two fixtures with the same category and dose but different character tags
    get the same level (R5).
A6. A process aid is `allowed` with "no flavour effect" in every style that has an envelope
    (R6).
A7. Step 3 on the new test briefs rates each wanted misc word, and none of them is `unrated`
    (R7).
A8. The coffee-vanilla brief's step 2 picks 30A, with the base style as the first alternative.
    The orange-peel brief keeps the base style, and lists the extra as a deviation if it is out
    of style (R8, R10).
A9. `app.style_fit_recipe` with one flavour extra and one process aid returns a line for each
    (R9).
A10. `python -m evals.run` on all briefs: steps 1–5 pass on the new briefs, and each of steps
     1–5 still passes 22/22 on the others (R10).
A11. The coffee, vanilla and orange peel entries are in `ref.misc`, each figure with its
     source. The live `ref` has no process-aid row (R11).
A12. Step 5 on the coffee-vanilla brief has a slot whose misc product shows purpose, usages,
     time and dose range, and the output meets `step5.output` (R12).
A13. A fruit fixture with a sourced sugar content loads as flavour misc, and the summary marks
     it "waits for maths" with the M6 TODO. RECIPE-ROADMAP's Later list has the TODO (R13).
A14. Two fixture forms of one product (e.g. dry-beaned and cold brew coffee) load as two
     entries with their own dose and time. A vanilla-extract fixture dosed in mL is reported as
     "waits" and not loaded (R14).
A15. A flavour fixture without a dose loads with `dose_g_per_l` `NULL`. `app.style_level` and
     step 5 say "no sourced dose" for it (R15).

## Open questions
None open. Decided by you on 2026-10-18:
1. **Categories and usages (INGREDIENT-INTAKE Q2): a.** Today's flavour categories plus the
   process categories `fining`, `nutrient`, `enzyme`, `acid` and `other-process`, with enzyme and
   acid marked "changes the numbers". *Why: Irish moss and yeast nutrient get real places, and
   the checker knows which ones wait for maths.*
2. **Fruit (Q3): c, with a TODO.** All fruit is flavour misc. A fruit file with a sourced sugar
   content is marked "waits for maths", and fruit as a fermentable is decided with M6 (R13).
   *Why: a fruit role needs a new fermentable usage, rule changes and gravity maths for additions
   after the boil (M6).*
3. **Coffee, cacao, vanilla (Q5): replaced by the three-layer model above.** The category
   drives step 2, one of the four existing specialty dimensions is scored, and character tags
   only describe. No new sensory dimensions. *Why: you adopted it after comparing two flavour
   wheels (Meilgaard's, and Mark Dredge's, in `shared/rag-files/sensory/`). It scores what was
   added, not the malt's flavour.*
4. **Step 5 slot: a.** A misc product in a slot carries its usages, time and dose range (R12).
   *Why: step 5 is the frame steps 6–9 work inside, and it already carries the fermentable
   limits.*
5. **Real entries: only the products the test briefs need,** from named sources. Process aids
   are proven by fixtures. *Why: R10 can be measured on the live pipeline, and real items come
   in when a step needs them, as in s8.*
   **Forms: one entry per form,** each with its own dose, time and usage (R14). *Why: dry-beaned
   and cold brew coffee are dosed and timed differently in the source.*

## Deviations
- 2026-10-18 · Needs, Blocked by, Scope, R2, R3, R8, Assumptions: revised against what s8 and
  m4 built. B1 cleared. The names and paths are now s8's: the `misc/` folder, `load_misc`, the
  `<field>_ref` keys, s8's alias table, misc kind words in `app.ingredient_kind_word()`, the load
  summary, the spot-check pack and the README. R3 and A3 add that a process aid is not reported
  as untagged, because s8's summary flags a row with no tags. R8 and A8 name the base style as
  the first alternative, which m4's step 4 reads. — s8 and m4 shipped 2026-10-17.
- 2026-10-18 · Goal, R10, A10: steps 1–5 are measured, and must stay at G4's level (22/22 each),
  not only steps 1–3 at G3's. — m4 added steps 4 and 5 and their graders, so the new briefs pass
  through them too.
- 2026-10-18 · Scope, R11, R12, A11, A12: a step 5 misc slot and the choice of real entries were
  added as questions. — m4's slot has no misc fields, and s8 changed to "no real items until a
  step needs them".
- 2026-10-18 · Open question 2: the recommendation changed from a to c. — measured: a fruit role
  also needs a new fermentable usage, rule changes and post-boil gravity maths (M6).
- 2026-10-18 · Scope (docs): INGREDIENT-INTAKE.md §12 and `shared/ingredients/README.md` added
  to the docs to update. WORKFLOW-ROADMAP.md has no s8 row either (measured). — s8 did not add
  them.
- 2026-10-18 · B2, R1, A1: B2 cleared. The categories and usages are fixed as decision 1 (option
  a). — your answer.
- 2026-10-18 · Scope, Out, R13, A13: all fruit is flavour misc. A fruit file with a sourced sugar
  content is marked "waits for maths" with the TODO "fruit as a fermentable is decided with M6",
  in the load summary and on RECIPE-ROADMAP's Later list. — your answer (option c plus a TODO).
- 2026-10-18 · Goal, new section "How a flavour misc is read", Scope, Out, R5, R8, A5, A8,
  Assumptions: old Q3 (coffee and cacao → `roast`, vanilla → `sweetness`) is replaced by your
  three-layer model. The category gives the specialty style. Each flavour misc scores on one of
  `fruit`, `spice`, `wood` or `smoke`, by dose → subtle, noticeable or aggressive. Character tags
  are never scored. Base-beer side effects are out unless sourced. Whether BJCP files coffee,
  cacao and vanilla under 30A is now an unverified assumption. — your answer.
- 2026-10-18 · R12, A12: the step 5 misc slot is no longer conditional. — your answer (option a).
- 2026-10-18 · Scope, Out, B3, R11, A11: the real entries are the test briefs' products only
  (coffee, vanilla, orange peel). Irish moss and yeast nutrient are out as real entries and are
  proven by fixtures, so B3 no longer needs a process-aid source. — your answer (option b).
- 2026-10-18 · Scope, Out, R14, A14: one entry per form of a product. A liquid form is dosed as g
  of dry product per L where the source allows. A liquid extract is reported as "waits" and not
  loaded until a later item adds mL/L. Roast level and processing go in tags and description. —
  your answer.
- 2026-10-18 · R5, R8: a flavour misc in `other` gets no dimension and no specialty style, and says so. — follows from your model, which names no dimension for `other`; it is the legal "absent" value (PROJECT.md §6.3), not a guess.
- 2026-10-18 · Out, Constraints, B3, R15, A15: the LLM never decides amounts. A misc without a
  sourced dose keeps dose `NULL`, and the pipeline says "no sourced dose". B3 records Janish's
  two coffee points (about 3.0 g/L dry-beaned for 48 h, about 6.0 g/L cold brew for 16 h) as
  "noticeable" anchors only. — your dose-sourcing notes.
