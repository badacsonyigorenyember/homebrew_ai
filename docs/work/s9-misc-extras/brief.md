# S9 · Misc extras: spices, fruit, coffee and process aids through the pipeline

Status: draft
Slug: s9-misc-extras · Branch: s9-misc-extras
Design: [INGREDIENT-INTAKE.md](../../INGREDIENT-INTAKE.md) §3, §4, §8, §9, §11 (rows marked s9)
Needs: `s8-ingredient-intake` shipped. Build order: s5 → s8 → **s9** → m4 → m5.
`s10-ingredient-form` builds on this.

## Blocked by
Written 2026-10-17 as a draft, ahead of s8, so the shape of the work is known. It can't be
approved or planned until these are cleared:

| # | Blocker | Blocks | Cleared when |
|---|---|---|---|
| B1 | **s8 is not built.** This work adds misc to s8's loader, checker, templates, alias table and tagger; their names and file shape are only fixed once s8's plan is approved. | approval (names may change), implementation (needs the code) | s8's plan is approved (for approval of this brief); s8 is shipped (for the plan) |
| B2 | **Open questions 1–3 below** (Q2 categories, Q3 fruit, Q5 coffee/cacao/vanilla). They change the schema and the style-fit rows. | approval | you answer them |
| B3 | **Dose sources are unverified.** Usage, dose and the dose → intensity cut points need a source. Candidates: *How to Brew* ch. 13 "Fruit, spices" (pp. 217–230, where the loader cut tables, BOOKS.md §3) and Janish's coffee guide (`janish-coffee-beers`, in `kb`). Neither has had a doc → calc pass, and no process-aid source (Irish moss, yeast nutrient) is named yet. | planning (no sourced number, no cut point) | a doc → calc pass (Task 1 of the plan) shows what they state, and you name a source for each process aid |
| B4 | **New test briefs and envelopes need your review.** The two test briefs with extras (P0 rule) and the specialty-style envelopes (D9: every envelope is reviewed by you) can't be finished without you. | verification | you approve the briefs and review the envelopes during the work |

## Why
`ref.misc` has 0 rows and a single `category` column. Misc words in a brief ("coffee",
"cinnamon") come out of step 3 as `unrated`, `app.style_level` raises an error for a misc
ingredient, step 2 maps only honey and molasses to a specialty style, and process aids (Irish
moss, yeast nutrient) have no place at all (INGREDIENT-INTAKE G5–G8). You want to fill misc
yourself from the intake files (decided 2026-10-17), and M4–M8 need misc rows to build their
extras slots, amounts, schedule and sheet.

## Goal
A flavour misc or a process aid added as one intake file is usable in steps 2 and 3: a wanted
spice or coffee gets a style-fit level with a reason, a `feature` extra moves step 2 to its
specialty style, and a process aid is neutral in every style. After this, a new spice needs only
its file, not code.

## Scope
In:
- `ref.misc` gains `purpose` (`flavour` · `process`), `usages`, `time_min`, `dose_g_per_l`,
  `description` and `field_source`; categories per Open question 1. Fruit per Open question 2.
- Misc in the intake path: `shared/ingredients/misc/`, templates for a flavour misc and a process
  aid, `load_misc` in `loaders/extra_ingredients.py`, the checker accepting misc (it refuses misc
  today, s8 R2).
- The tagger's misc branch; misc kind words in the resolver (`spice`, `fruit`, …).
- Style fit for flavour misc: rows in `app.usage_effects()` per category (sensations per Open
  question 3), dose → intensity cut points with a source, `app.style_level` accepting misc usages,
  `app.ingredient_choices` giving misc choices, `app.style_fit_recipe` taking an extras list.
- Process aids: `allowed` in every style with "no flavour effect", never a deviation.
  Categories that change the numbers (enzyme, acid, if Open question 1 is a) load and are marked
  "waits for maths".
- Step 2: `app.specialty_style()` by misc category, keeping the honey and molasses rows.
- Envelopes (`loaders/style_envelopes.toml`) for the specialty styles the new test briefs need,
  extracted and reviewed as in s3.
- Two new recipe test briefs with extras in `evals/recipe_briefs.toml`, approved by you (e.g. a
  coffee-vanilla stout: feature extra → specialty style; a pale ale with a little orange peel:
  background extra → base style + deviation), and steps 1–3 measured on all briefs.
- First misc entries: the products the two test briefs need, plus Irish moss and yeast nutrient,
  each from a source you name.
- DATABASE.md, STYLE-FIT.md, RECIPE-ROADMAP.md step 9, WORKFLOW-ROADMAP.md (s8, s9, s10 rows) and
  PROJECT.md updated.

Out:
- Choosing extras for a recipe (M5 step 9), amounts in grams (M6), the formulation-check contract
  (M6), placing extras and process aids in the schedule and who adds process aids (M7, Q10), the
  sheet (M8).
- Maths for ingredients that change the numbers (enzymes, acids).
- The n8n form (s10). New sensory dimensions (Open question 3 b only if a reviewed envelope needs
  one).

## Requirements
R1. `ref.misc` holds `purpose`, `category`, `usages`, `time_min`, `dose_g_per_l`, `description`,
    `field_source`, with the categories of Open question 1; schema change as a `.sql` file.
R2. A misc intake file (flavour or process) passes `--check` and loads like the other kinds:
    required fields per purpose (INGREDIENT-INTAKE §3), each figure with its source, idempotent.
R3. A flavour misc is tagged from its category and descriptors; a process aid gets no tags.
R4. `app.resolve_ingredient` finds a misc product by name, alias or kind word, and a kind word
    restricts the kind as `malt`, `hop` and `yeast` do.
R5. `app.style_level` returns a level and a reason for a flavour misc in each of its usages,
    from `app.usage_effects()` and dose cut points that each name a source.
R6. `app.style_level` returns `allowed` with "no flavour effect" for a process aid in any style.
R7. Step 3 rates a wanted misc word at its best choice (no longer `unrated` when the product is in
    `ref`), and lists it as a deviation when the best level is `out_of_style` or `changes_style`.
R8. Step 2 picks the specialty style for a `feature` misc by category, with the base style as the
    alternative; a `background` misc leaves the base style.
R9. `app.style_fit_recipe` accepts an extras list and rates each extra like R5–R6.
R10. The two new test briefs are in `evals/recipe_briefs.toml` with their expected style and
     deviations, approved by you; steps 1–3 pass on them and stay at G3's level on the 22 others.
R11. The first misc entries are loaded through intake files, each figure from a source you name.

## Constraints
- CLAUDE.md: readable over optimal; usage effects and cut points stay code next to their tests
  (DATABASE.md §8), never a config table. Schema changes as `.sql` files applied as `postgres`.
- PROJECT.md §6.7: doc → calculation first; a dose or cut point without a source is not used.
- `ref` rules: sourced, SI units (g/L, minutes, days), unknown stays `NULL`, nothing guessed.
- Misc never enters OG, IBU or SRM (DATABASE.md §2).
- No LLM in the intake path. Envelopes are LLM-extracted offline and reviewed by you (D9).
- PROJECT.md §6.6: the pipeline change is measured on the fixed brief set.

## Assumptions
- *How to Brew* ch. 13 states usage and dose for common fruit and spices *(unverified, B3)*.
- Janish's coffee guide states a coffee dose and contact time *(unverified, B3)*.
- s8 ships with the file shape and alias table its brief describes *(unverified until s8's plan,
  B1)*.
- The four specialty dimensions (`spice`, `fruit`, `wood`, `smoke`) are enough for the first
  entries *(measured 2026-10-17: they exist; enough is unverified)*.

## Acceptance criteria
A1. `ref.misc` has the R1 columns and the decided categories, owned by `postgres` (R1).
A2. A flavour misc fixture and a process-aid fixture pass `--check` and load; loading twice gives
    the same rows; a misc file missing a required field is refused, naming file and field (R2).
A3. The flavour fixture has its family and character tags, the process aid none, and neither has
    an `ingredient_review` row (R3).
A4. `app.resolve_ingredient` returns the misc product for its name, each alias and its kind word
    plus name, and no product of another kind (R4).
A5. For a flavour misc and a style with that sensation in its envelope, `app.style_level` gives a
    level and a reason for each usage, and each cut point used names its source in code (R5).
A6. A process aid is `allowed` with "no flavour effect" in every style that has an envelope (R6).
A7. Step 3 on the new test briefs rates each wanted misc word; none of them is `unrated` (R7).
A8. The coffee-vanilla brief's step 2 picks the specialty style with the base style as the
    alternative; the orange-peel brief keeps the base style and lists the extra as a deviation
    if it is out of style (R8, R10).
A9. `app.style_fit_recipe` with one flavour extra and one process aid returns a line for each (R9).
A10. `python -m evals.run` on all briefs: steps 1–3 pass on the two new briefs and on at least
     as many of the 22 others as G3 (R10).
A11. The first misc entries are in `ref.misc`, each figure with its source (R11).

## Open questions
1. **Misc categories (Q2).** — options: a) flavour categories as today (spice, herb, fruit, wood,
   coffee, cacao, vanilla, smoke, other) plus process categories `fining`, `nutrient`, `enzyme`,
   `acid`, `other-process`, with enzyme and acid marked "changes the numbers"; b) the 10 categories
   as they are, process aids under `fining` and `other` — recommend a: Irish moss and yeast
   nutrient get real places, and the checker knows which ones wait for maths.
2. **Fruit (Q3).** — options: a) fruit with a sourced sugar content is a fermentable with a new
   role `fruit` (enters OG), fruit without one is flavour misc; b) all fruit is misc — recommend a:
   keeps the "gravity → fermentable" rule true. With a, the `fruit` role is in this work's scope.
3. **Coffee, cacao, vanilla (Q5).** — options: a) coffee and cacao drive `roast` with their
   character tags, vanilla drives `sweetness` with tag `vanilla`; b) new specialty dimensions
   `coffee`, `chocolate`, `vanilla` — recommend a first; b only if a reviewed envelope needs it.

## Deviations
