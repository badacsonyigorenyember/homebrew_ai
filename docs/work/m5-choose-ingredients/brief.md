# M5 · Steps 6–9: choose yeast, fermentables, hops and extras

Status: approved
Slug: m5-choose-ingredients · Branch: m5-choose-ingredients
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) M5, checkpoint **G5** ·
[RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §3 steps 6–9 · [STYLE-FIT.md](../../STYLE-FIT.md) ·
PROJECT.md §3 (D7)
Needs: `m4-targets-blueprint`, `s3-style-fit`, `s8-ingredient-intake` and `s9-misc-extras`
shipped (all four are in `docs/finished/`, checked 2026-10-18). `s2-corpus` was abandoned
2026-10-14 (D7): there is no corpus popularity to rank by, so this brief follows D7 instead
(see Deviations).

## Why
Step 5 gives a design frame: rules and limits, a slot per wanted item with its `ref` products,
the excluded and inventory words, the hint intents and the attenuation the targets need. It
names no recipe yet. Stage C turns the frame into real products the brewer can buy, with the
grist percentages and the hop-schedule intent that M6 scales into grams (PROJECT.md §3: the LLM
picks from the ingredient table and proposes percentages and hop intent; code checks).
The first build's lesson is that an LLM picking products invents them (§6.4), so every pick
must be a `ref` id that code checks before anything goes on.

## Goal
For every brief, steps 6–9 return a yeast, fermentables with percentages, hop additions and
extras, each a `ref` id from a table code built, checked by code: exclusions honoured, fitting
inventory used, the pipeline's own picks in style, and anything that can't be filled reported
as `absent`. 0 invented ingredients on all 24 briefs.

## Scope
In:
- A candidate table built by code from `ref` for each brief: the products of each kind with
  the fields the LLM needs to choose (fermentable role, `max_pct`, EBC, description; hop alpha,
  purpose, origin and character tags; yeast type, attenuation, temperature, flocculation,
  tolerance and family tags; misc category, usages and sourced dose), each product's level per
  usage in the style used, and marks for inventory and wanted items. Excluded products and
  their siblings are left out (R2).
- A fit test first (R13): does one prompt for all of steps 6–9 (candidate table + brief + frame +
  instructions) fit the D2 model's context on all 24 briefs and still give usable picks? Its
  result picks the shape: one LLM call for steps 6–9 if it passes (your preference), else one
  call per step 6, 7, 8 and 9.
- The LLM call(s) that pick from that table and propose percentages and the hop-schedule intent,
  following step 1's pattern: the contract as the model's `format`, a code check, one retry with
  the check's reasons.
- The code check of the proposal (R1–R8) and the step contracts in `shared/contracts/`.
- Step 9 extras for wanted misc (b23 coffee and vanilla, b24 orange peel): the product and
  usage picked from the row, the dose in g/L set by code from the row's sourced dose.
- Resolver and catalogue changes the briefs need: excluded siblings (Citra → Citra LUPOMAX); the
  alias "dark candi sugar" → Brown Candi Sugar (R3); `ref.yeast.type = 'lacto'` on YF-998 and
  YF-999, set by the yeast loader, and "Lactobacillus" finding type `lacto` (R5). New words go
  in as aliases (`ref.ingredient_alias`, s8) or a spelling row, not as rules that fit a brief.
- An `absent` result for a slot or word no `ref` product can fill.
- Brief check: each brief's `needs` graded as classes through a class map in the grader.
- Steps 6–9 in `Recipe pipeline` after step 5, logged to `app.run_step`; graders; the G5 run.
- Docs: RECIPE-ROADMAP §3 (stage C and rows 6–9 still say "scored by code" and "corpus
  popularity"), WORKFLOW-ROADMAP's M5 row and G5's Decide line.

Out:
- Amounts in kg and g, OG/FG/ABV/IBU/SRM, the formulation-rule check (`app.check_recipe`) and
  its retry loop of at most 3 (M6 step 10 and 11). This step's own check covers only whether
  each pick is legal.
- Mash, boil and fermentation temperatures (M7; step 4 already sets the mash target).
- Process aids (Irish moss, nutrient): who adds them is INGREDIENT-INTAKE Q10, open, for M7.
- New products in `ref` (no Special B: it is graded as a class, R10). Substitution dialogue ("I have no
  Crystal 60") beyond exclusion. Inventory-first mode (Later).
- Water salts in `needs` (M7 step 12).

## Requirements
R1. Every chosen item is a `ref.ingredient.id` from the candidate table the step was given. The
    check refuses any other id, and a test asserts no other path lets an item into the output.
R2. Excluded ingredients are never chosen, also not through a sibling product: b08 no Saaz;
    b16 no Citra, Mosaic, Citra LUPOMAX or Mosaic LUPOMAX. They are removed from the table and
    refused by the check. (Measured 2026-10-18: step 5's `excluded` for b16 holds only Citra
    (470) and Mosaic (488).)
R3. An inventory product that fits (its kind is in the recipe and it is not ⚠️/⛔ at some usage in
    the style used) is chosen; the check fails a proposal that leaves one out. b10: Munich, an
    abbey yeast and Brown Candi Sugar (through the alias "dark candi sugar", user decision
    2026-10-18); b15: Maris Otter, a crystal malt,
    East Kent Golding. An inventory word that does not fit is reported with its reason.
R4. With guidance on, every pick the pipeline makes on its own is ✅, 👍 or ➖ at its usage in
    step 4's style used. A wanted item is picked as a product and usage that keep the best level
    step 3 gave it (m3-deviations R4). With guidance off (b18) any level is allowed. Every pick
    carries its level and reason, so M6 can list model-made deviations.
R5. The yeast's attenuation range overlaps the band step 5 gives (`attenuation.low_pct` to
    `high_pct`); a yeast with no attenuation figure is reported, not assumed. When the style's
    envelope has sourness, step 6 adds one souring culture (`type = 'lacto'`) next to the main
    yeast: b14 gets YF-998 or YF-999 besides its ale yeast. Lager styles get a
    lager yeast: BJCP styles tagged `bottom-fermented` and BA lager styles (b06, b08, b09, b17,
    b22); b13 gets a weizen-family yeast. (Measured 2026-10-18: `app.style_level` rates SafAle
    US-05 `allowed` in 5D, 1B and `mexican-style-amber-lager`, the same as W-34/70, so the level
    alone does not enforce this.)
R6. Fermentables come with a % of grist (the shares add up to 100) and a purpose, each at most
    its `max_pct`, and every wanted fermentable from step 5's slots is placed. Hop additions come
    with usage (`boil`, `whirlpool`, `dry_hop`), minutes, share of hop mass and a purpose: the
    inputs `app.solve_hops` reads. b08 picks a hop that is not Saaz and is ✅ or 👍 in 5D
    (measured: Hallertau Mittelfrüh, Tettnanger, Spalt Select and Hallertau Hersbrücker are
    `typical` at whirlpool).
R7. Each wanted misc gets a misc product and a usage from its row's `usages`. Its dose in g/L is
    set by code from the row's sourced dose and the wanted item's role: `background` takes the
    low end of the sourced range, `feature` the high end, and a one-point dose (coffee beans
    3.0 g/L) is used as it is (user decision 2026-10-18). The LLM never sets a dose (s9). A misc
    with no sourced dose says so.
R8. A wanted or inventory word, or a step 5 slot, that no `ref` product fills returns `absent`
    with the reason, and the recipe goes on without it; nothing is invented to fill it.
R9. Every pick carries a `because`: the LLM's purpose plus code's facts (level and its reason,
    inventory, wanted, the step 5 slot it fills). M6 and the sheet (M8) read it.
R10. Each brief's `needs` (fermentables, hops, yeast, misc) is graded as classes through a class
    map in the grader (kind, role, EBC band, family tag or product names per needs word),
    written in this work and reviewed by you. Each class is covered by a pick or reported
    absent. Special B (b10) is the class dark crystal, covered by Special W or Caraaroma (user
    decision 2026-10-18). (Measured 2026-10-18: 10 of the 48 needs words resolve to no product: Special B,
    Tettnang, Lactobacillus and 7 yeast class words such as "American ale yeast".)
R11. Steps 6–9 run in `Recipe pipeline` after step 5, each logged to `app.run_step` with its own
    step number and a contract in `shared/contracts/`, so a failure pins to one step. The LLM
    call uses the D2 model with the webhook's `temperature` and `seed`, as step 1 does.
R12. RECIPE-ROADMAP §3 and WORKFLOW-ROADMAP (M5 row, G5 Decide line) describe stage C as built,
    with no corpus popularity.
R13. Before the LLM step is built, a fit test measures the one-call prompt on all 24 briefs:
    the prompt's token count (Ollama's `prompt_eval_count`) plus the output budget against the
    context the call can use (step 1 runs with `num_ctx` 8192 and `num_predict` 4096, OPERATIONS
    §5; a larger `num_ctx` counts only if the model still loads and runs on this machine), and a
    quality check: each brief's proposal passes this step's check (R1–R7) within the one retry.
    **Pass** (every brief fits and passes) → one LLM call for steps 6–9. **Fail** → one call per
    step 6, 7, 8 and 9. The numbers and the choice are written to PROJECT.md §8. On a fail the
    runs need 5 LLM calls through stage D, above the "≤ 2 plus tie-breaks" bar of P5 and G6; the
    work reports that and asks you, and does not change PROJECT.md §2, §3 or §6 itself.

## Constraints
- PROJECT.md §3 and D7: the LLM picks ingredients from the ingredient table and proposes
  percentages and hop-schedule intent; code computes every number and checks. Changing that
  split to code only would be a §3 change; per-step calls would touch the P5/G6 call bar (R13).
- §6.2 small LLM steps with checkable contracts; §6.3 and §6.4: absent beats invented, the
  catalogue is the only source of products; §6.7: the LLM never computes a number (doses
  included, s9); §6.8: the table, the check and the dose rule readable from their own files.
- G0: deterministic logic is SQL in `db/*.sql` called from n8n's Postgres node; Code nodes only
  reshape JSON. DB changes are `.sql` files applied with `psql` as `postgres` (OPERATIONS §4).
- Workflows with `onError` are imported with the n8n CLI, since the MCP drops `onError`
  (m3-deviations Task 5), and exported to `n8n/workflows/`.
- `app.resolve_ingredient`'s synonym list takes spellings and common names only, never a row
  that fits a brief (`db/036`).
- P5 and G6 count LLM calls: "≤ 2 per recipe plus tie-breaks" (step 1 is one). One call for
  steps 6–9 keeps that bar; one call per step does not (R13).
- Step 1's call runs with `num_ctx` 8192, `num_predict` 4096, and the model runs 36 % on the CPU
  (PROJECT.md §4, measured 2026-10-13), so a larger context may not fit in 16 GB of VRAM.

## Assumptions
- A candidate table for one brief fits in the D2 model's context and the model keeps to it
  *(unverified; R13's fit test decides)*.
- Hops and yeasts have no description column (s2 left them out); their fields and tags are
  enough for the LLM to choose well *(unverified; the G5 direction check, A12, tests it)*.
- YF-998 and YF-999 (hopline) are Lactobacillus cultures: their hopline spec text says "Lacto",
  their `ref.yeast.type` is NULL and their only tag is `sour` *(measured 2026-10-18)*; Philly
  Sour is a souring yeast, `typical` in 23A, while YF-998 and YF-999 are `allowed` there
  *(measured)*.
- Hopline sells no Special B (adjunct-fermentables report); Special W (68) and Caraaroma (46) are
  the nearest `ref` products *(measured)*.
- Brown Candi Sugar is what a brewer means by "dark candi sugar" *(your call, 2026-10-18)*.

## Acceptance criteria
A1. 0 invented ingredients across b01–b24 on the real pipeline (`python -m evals.run --save
    --label m5`) (R1, G5).
A2. 0 excluded items used: b08 no Saaz; b16 no Citra, Mosaic, Citra LUPOMAX, Mosaic LUPOMAX
    (R2, G5).
A3. b10 and b15 use every inventory item that fits, as listed in R3 (R3, G5).
A4. With guidance on (every brief but b18), no pipeline-made pick is ⚠️ or ⛔, and every wanted
    item keeps step 3's best level (R4).
A5. b06, b08, b09, b17 and b22 get lager yeasts, b13 a weizen-family yeast, and every brief's
    yeast overlaps step 5's attenuation band or the run reports why not (R5).
A6. Every recipe's fermentable shares add up to 100, each at most its `max_pct`; every hop
    addition has usage, minutes and a share; b08's late hop is not Saaz and is ✅ or 👍 in 5D (R6).
A7. b23's coffee and vanilla and b24's orange peel each have a misc product, a usage from the row
    and the code-set dose; a test shows an LLM-given dose is refused (R7).
A8. A test with a made-up wanted word returns `absent` with its reason, and the rest of the
    recipe is still chosen (R8).
A9. Every pick in the 24 outputs has a `because` with its level (R9).
A10. The runner prints `needs` coverage per brief, every gap is an `absent` with a reason, and
     you have reviewed the class map (R10, G5).
A11. All 24 runs log `ok` rows for steps 6–9 whose input and output meet their contracts, and the
     runner prints the LLM calls per run (R11).
A12. You read the picks of 3 briefs and agree a brewer would choose them (G5 direction check).
A13. RECIPE-ROADMAP §3 and WORKFLOW-ROADMAP no longer say "corpus popularity" for stage C (R12).
A14. The fit test's result is recorded before the LLM step is built: per brief the prompt
     tokens, output budget and context used, and whether the proposal passed the check; the
     worst case; and the shape it picked (one call if all 24 fit and pass, else one per step).
     The built pipeline uses that shape, and A11's call count matches it (R13).
A15. b14's recipe has its ale yeast and one `lacto` culture (YF-998 or YF-999); YF-998 and YF-999
     have `type = 'lacto'` after a reload of the yeasts; "Lactobacillus" resolves to them (R5).
A16. b10's inventory "dark candi sugar" resolves to Brown Candi Sugar (R3); b10's Special B need
     is covered by Special W or Caraaroma in the needs report (R10); b23 and b24 doses follow the
     role rule (R7).

## Open questions
None. The five questions of 2026-10-18 are answered (see Deviations).

## Deviations
- 2026-10-16 · Open question 1 (now Open question 2, option c): Milk The Funk souring pages named
  as the source for that option and for m7's souring step ([SOURCES.md](../../SOURCES.md)).
- 2026-10-18 · Why, Goal, Scope, R1–R11: picks are made by the LLM from a table code builds and
  checked by code, not "chosen by code" with corpus popularity; the draft's Open question 2
  (popularity vs inventory vs tags) is dropped — D7 (PROJECT.md §3, 2026-10-14) removed the
  corpus, and `corpus.style_profile` has 0 rows.
- 2026-10-18 · Scope: grist percentages and the hop-schedule intent are now in (D7; the M6 brief
  expects "a list of products and percentages"); amounts stay in M6. The formulation-rule check
  and its retry loop are Out, left to M6's step 11.
- 2026-10-18 · Scope, R7, A7: step 9 is real for b23 and b24 (added by s9) instead of an empty
  pass-through, and code sets the dose (s9 Out: "the LLM never decides amounts").
- 2026-10-18 · Goal, A1, A5: 24 briefs instead of 20; A5 adds b22 (a lager style); R5 adds an
  explicit lager check because the level does not separate ale from lager yeast (measured).
- 2026-10-18 · R2: sibling exclusion is a measured gap (step 5 lists no LUPOMAX product for b16).
- 2026-10-18 · R6: the noble-hop assumption is replaced by measured levels (no `noble` tag
  exists; four German hops are `typical` in 5D).
- 2026-10-18 · Scope, R10: the resolver's class match ("crystal malt" → any crystal malt) moves to
  a reviewed class map in the grader for `needs`; new pipeline words go in as aliases (s8)
  instead of growing `app.ingredient_synonym()`.
- 2026-10-18 · Open questions 2–4: b14's options rewritten, since `ref` already has two
  Lactobacillus cultures (found in s8); Special B gets its own question (hopline sells none);
  b10's "dark candi sugar" does not resolve (measured), so it is asked; Open question 5 is new
  (s9 left the role → dose rule to M5).
- 2026-10-18 · Needs: `s8-ingredient-intake` and `s9-misc-extras` added.
- 2026-10-18 · Scope, R13, A14 (user decision on Open question 1): one LLM call for steps 6–9 is
  preferred, but only if a fit test shows the prompt fits the model's context and gives usable
  picks on all 24 briefs; otherwise one call per step, with the P5/G6 call-count consequence
  reported to you.
- 2026-10-18 · R5, A15 (Open question 2, option a): YF-998 and YF-999 get `type = 'lacto'`,
  "Lactobacillus" finds type `lacto`, and step 6 adds one souring culture when the style's
  envelope has sourness.
- 2026-10-18 · R10, A16 (Open question 3, option a): Special B is graded as a dark-crystal class
  covered by Special W or Caraaroma; no new product.
- 2026-10-18 · R3, A16 (Open question 4, option a): alias "dark candi sugar" → Brown Candi Sugar.
- 2026-10-18 · R7, A16 (Open question 5, option a): `background` takes the low end of the sourced
  dose range, `feature` the high end, a one-point dose as it is.
