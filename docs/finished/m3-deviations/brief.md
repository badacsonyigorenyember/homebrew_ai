# M3 · Step 3: the deviation report

Status: approved
Slug: m3-deviations · Branch: m3-deviations
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) M3, checkpoint **G3** (= RECIPE-ROADMAP
P4 done) · [RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §3 step 3, §4, §7 · [STYLE-FIT.md](../../STYLE-FIT.md)
Needs: `m2-best-fit-style`, `s3-style-fit` and `s6-style-neighbours`, all shipped
([m2](../../finished/m2-best-fit-style/brief.md), [s3](../../finished/s3-style-fit/report.md),
[s6](../../finished/s6-style-neighbours/brief.md)).

## Why
"The style is guidance, not law": anything the user asks for is accepted, never blocked, and
listed as a deviation (RECIPE-ROADMAP §4). Step 3 is where that list is made, before design
starts, so later steps know which user wishes override the style and the recipe sheet can show
the Deviations box. A false deviation (oats in a hazy IPA) is as wrong as a missed one.

## Goal
Step 3 lists every deviation of the brief from the chosen style, of the four kinds the briefs use
(ingredient, number, mismatch, conflict), and nothing else. Stage A (steps 0–3) meets
RECIPE-ROADMAP P4: at least 18 of b01–b20 with the right style and the right deviations, with b21
and b22 reported beside it.

## Scope
In:
- Number deviations: a stated number outside the chosen style's range (b08 IBU 50 in 5D 22–40,
  b17 ABV 7 in 8B 4.4–5.4, b18 SRM 20 in 15A 9–14).
- Mismatch: carried from step 2's `mismatch` (b05: named 20C, ABV 8.0–12.0, chosen 15B).
- Conflict: hints that pull the same knob opposite ways (b11 "dry" vs "full", "chewy").
- Ingredient deviations: wanted ingredients that `app.style_level` rates `out_of_style` or
  `changes_style` in every choice later steps could make (b16 rice in 18B, b19 honey in 17C,
  b20 lactose in 19C).
- The first version of the ingredient-word resolver (word → `ref.ingredient` ids). None exists
  yet, and M5's brief says it extends "M3's first version".
- Step 3 as a step of `recipe-pipeline`: its own sub-workflow, checked against the existing
  `step3.input` / `step3.output` contracts, logged to `app.run_step`.
- Guidance off (b18): deviations are still listed; the output says guidance is off.
- The G3 checkpoint run and the decision to start stage B.

Out:
- Writing `app.recipe_deviation` rows: they need a recipe, which exists from M6; until then the
  deviations live in the step 3 output. (That table has no `kind` and a not-null `level`, so M6
  will have to fit number, mismatch and conflict rows into it.)
- Asking the user anything. Model-made deviations (later steps add those).
- Excluded ingredients: never deviations, so step 3 does not resolve them (M5 does).
- Inventory ingredients: step 3 does not rate them. Inventory is "use it if it fits": M5 uses an
  inventory item only when it fits the style (its R3), and inventory-first mode stays Later.
- Choosing products, amounts or temperatures (M5–M7). Changing step 2 or `app.style_level`.
- Hint-vs-number conflicts ("session" with a stated 7 %): not a kind the briefs use.

## Requirements
R1. Step 3 returns the `step3.output` contract (`shared/contracts/step3.output.schema.json`):
    `deviations[]`, each with `kind` (ingredient · number · mismatch · conflict), `subject` (the
    ingredient word or the number, e.g. "IBU 50"), `from` (what in the style it departs from,
    e.g. "5D IBU 22–40"), `level` (`out_of_style` or `changes_style` for ingredients, null for the
    other kinds), `requested_by` (`user`) and a `because` built by code from the facts used;
    `unrated[]`; and `guidance`.
R2. Number deviations compare each stated `abv`, `og`, `ibu` and `srm` with the chosen style's
    range in `ref.beer_style` (bounds inclusive). A number inside the range is not a deviation.
    `batch_l` is never one. A style with no range for that number (31B) gives no deviation.
R3. Conflicts come from the hint table (RECIPE-ROADMAP §7), held in code: two hints whose knobs
    move the same quantity in opposite directions make one conflict naming both hints. From the
    table as it stands that is dry/crisp vs full/chewy (mash temperature, attenuation),
    stronger vs session (OG) and bitter vs malty (BU:GU). Hints in the same row never conflict.
R4. Ingredient deviations: each wanted word (not inventory, not excluded) is resolved to `ref`
    ids and rated with `app.style_level(style_code, ingredient_id, usage, dose)` on the chosen
    style, best case: it is a deviation only when no choice keeps it in style. The word's level
    is the best level over
    - every product the word resolves to,
    - for a yeast, fermentation temperatures across its own `ref.yeast.temp_c` range,
    - for a hop, its usages; a `feature` hop only over whirlpool and dry hop.
    Only a best level of `out_of_style` or `changes_style` becomes a deviation, naming the
    product and the choice that came closest in its `because`. A word that resolves to no `ref`
    id, or that `style_level` returns `level: null` for (style without a reviewed envelope), goes
    into `unrated`, not into deviations. M5 must then pick a product (and M7 a temperature) that
    keeps a non-deviating wanted word in style.
R5. Excluded ingredients are never deviations.
R6. With guidance off, the same deviations are listed and `guidance` is false.
R7. The step is deterministic code with no LLM call. It runs in `recipe-pipeline` after step 2,
    checks its input and output against the step 3 contracts, and logs to `app.run_step`
    (step 3), so `python -m evals.run` grades it.
R8. When step 2 returns no style, step 3 still returns: conflicts only, every wanted word in
    `unrated`.

## Constraints
- PROJECT.md §3 and RECIPE-ROADMAP §4: deviations are listed, never blocked; no blocking questions.
- §6.8: the conflict rules read as one small table next to their tests; the resolver reads as a
  short ordered list of match rules.
- CLAUDE.md: database objects go in a `.sql` file applied with `psql` as `postgres`
  (OPERATIONS.md §4), not through the read-only Supabase MCP.
- The resolver keeps its own synonym list. It must not read the grader's `evals/grade.py`
  `SYNONYMS` or the brief fixtures (same rule as `test_no_prompt_or_workflow_mentions_the_fixture`).
- The resolver needs the ingredient kind from the word: "Crystal" is also a hop and "Abbey Malt" a
  fermentable, so "crystal malt" and "abbey yeast" must not match them.

## Assumptions
Verified 2026-10-16 against the live database and the code:
- `app.style_level(style_code text, ingredient_id bigint, usage text, dose jsonb default '{}')`
  returns `{level, because}` (`db/034_style_level.sql`). Usage must fit the kind (hop: boil,
  whirlpool, dry_hop; fermentable: mash, boil; yeast: ferment), and a hop boil needs
  `dose.minutes`. With no dose, the dose, colour and bitterness checks are skipped with a note.
- For adjuncts and sugars the level does not depend on usage or dose (`ref.style_rule` has 0
  rows): typical when the style's characteristic ingredients name it, else `out_of_style`. So
  ingredient deviations on these briefs are always `out_of_style`.
- Measured with no dose: b02 Flaked Oats/21C, b06 Flaked Rice/1B, b07 Flaked Corn/1C, b12
  Honey/31B are `typical`; b16 Flaked Rice/18B, b19 Honey/17C, b20 Lactose/19C are
  `out_of_style`. b10 Brown Candi Sugar/26B is `typical`, Munich malts/26B `allowed`; b15 Maris
  Otter `allowed`, crystal malts and East Kent Golding (late) `typical` in 11B.
- b10's "abbey yeast" depends on product and temperature in 26B: Lallemand Abbaye is `typical`
  with no temperature; Brewline Abbey Monk Ale is `out_of_style` with none or 20 °C and
  `allowed` at 23 °C; Mangrove Jack's M47 is `out_of_style` at all three. This is why R4 rates
  the best case. (b10's yeast is inventory, so step 3 no longer rates it.)
- All 22 brief styles have a reviewed envelope (s3: 26 styles), so none gives `level: null`.
- The 5 distinct wanted words in b01–b22 (oats, rice, corn, honey, lactose) each match exactly
  one `ref` product: Flaked Oats, Flaked Rice, Flaked Corn, Honey, Lactose.
- Step 2's latest outputs (runs 1838–1859, 2026-10-15) pick the expected style for all 22 briefs;
  only b05 has a `mismatch` (`{named: "20C Imperial Stout", range: "ABV 8.0–12.0", chosen: "15B
  Irish Stout"}`). s6 did not change step 2.
- The grader already exists (`evals/grade.py` `grade_step3`): same kind, and for ingredients the
  expected word as a whole word in `subject`; numbers and mismatches by the quantity named;
  conflicts by hint rows; no extra deviations allowed. `evals/run.py` grades step 3 from
  `app.run_step`.
- The stated numbers inside their range: b01 ABV 6.5 (21A 5.5–7.5), b05 ABV 4 (15B 3.8–5.0), b14
  ABV 3 (23A 2.8–3.8), b21 ABV 4 (BA session IPA 0.5–5.0).

Unverified:
- The step 1 LLM keeps its 22/22 from 2026-10-14 in the G3 run *(unverified)*.

## Acceptance criteria
A1. The runner shows ≥ 18 of b01–b20 with step 2 and step 3 both passing (the harness rule:
    every expected deviation, no extra one); b21 and b22 are reported beside it (R1–R6, R8, G3).
A2. b08, b17, b18 each give exactly one number deviation; b05 one mismatch; b11 one conflict
    naming "dry" and "full"/"chewy"; b16, b19, b20 one ingredient deviation each (R2–R4).
A3. b02, b06, b07 and b12 give no deviation, and b10's and b15's inventory gives none because
    it is not rated (R4).
A4. b08's excluded Saaz and b16's excluded Citra and Mosaic are not deviations (R5).
A5. b18's output lists the SRM deviation and has `guidance: false` (R6).
A6. Tests for the number, conflict, resolver and ingredient rules pass; the conflict rule is also
    tested on bitter + malty and stronger + session; the best-case rule is tested on a word with
    several products, a yeast whose level changes across its `temp_c` range, and a `feature` hop
    (rated at whirlpool and dry hop only); a no-style input gives R8's output. Rules that read
    `ref` run as stack tests (R2–R4, R8).
A7. The 5 wanted words of b01–b22 resolve to their `ref` products (none lands in `unrated`), and
    a resolver test shows "crystal malt" does not resolve to the Crystal hop (R4).
A8. Every step 3 output in the G3 run passes the `step3.output` contract and is in `app.run_step`
    as step 3 (R1, R7).
A9. WORKFLOW-ROADMAP G3 and RECIPE-ROADMAP P4 are marked with the measured score (G3).

## Open questions
None.

## Deviations
- 2026-10-16 · Needs: `s6-style-neighbours` before the G3 run, so stage A is judged with the
  neighbour check in hand ([SOURCES.md](../../SOURCES.md)). s6 has since shipped.
- 2026-10-16 · Goal, A1: 22 briefs exist now (b21, b22 added 2026-10-13); the bar stays ≥ 18 of
  b01–b20 with b21 and b22 reported, as G2 did; A1 counts step 2 and step 3 passing (P4's "right
  style, right deviations") — the draft said "18 of 20".
- 2026-10-16 · R1: aligned with the `step3.output` contract already in the repo: words that cannot
  be rated go in `unrated[]` instead of a `level: unknown`, and `guidance` is a field.
- 2026-10-16 · Scope, Constraints: the resolver is settled as in scope (draft Open question 1, a):
  none exists in the code, and M5's brief extends "M3's first version". It keeps its own synonym
  list, not the grader's.
- 2026-10-16 · R4: draft Open question 2's option a (usage from the style's corpus recipes) is
  gone, since s2-corpus was abandoned (D7). Replaced by new Open question 2; inventory moved to
  Open question 1 (both answered below).
- 2026-10-16 · R2, R7, R8 and A6–A8: added what the draft left implicit: which numbers are
  compared, the pipeline wiring and contract check, the no-style case, resolver and contract
  checks; A6's "without the stack" dropped, because the ingredient and number rules read `ref`.
- 2026-10-16 · A3: b10 and b15 added; they expect no deviation under either answer to Open
  question 1.
- 2026-10-16 · Scope, R4, R8, A3, A7: inventory is not rated by step 3 (user, Open question 1:
  "Wanted words only"); M5 uses inventory only when it fits. A7 now covers the 5 wanted words.
- 2026-10-16 · R4, A6: best-case rating (user, Open question 2: "Best case"): a deviation only
  when no product, no temperature in the yeast's `temp_c` range and no usage keeps the word in
  style; a `feature` hop is rated at whirlpool or dry hop only.
