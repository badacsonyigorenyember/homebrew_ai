# M3 · Step 3: the deviation report

Status: draft
Slug: m3-deviations · Branch: m3-deviations
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) M3, checkpoint **G3** (= RECIPE-ROADMAP
P4 done) · [RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §3 step 3, §4 · [STYLE-FIT.md](../../STYLE-FIT.md)
Needs: `m2-best-fit-style` and `s3-style-fit` shipped (ingredient deviations use s3's `level()`);
`s6-style-neighbours` before the G3 run (its step 2 measurement, 2026-10-16)

## Why
"The style is guidance, not law": anything the user asks for is accepted, never blocked, and
listed as a deviation (RECIPE-ROADMAP §4). Step 3 is where that list is made, before design
starts, so later steps know which user wishes override the style and the recipe sheet can show
the Deviations box. A false deviation (oats in a hazy IPA) is as wrong as a missed one.

## Goal
Step 3 lists every deviation of the brief from the chosen style, of the four kinds the briefs use
(ingredient, number, mismatch, conflict), and nothing else. Stage A (steps 0–3) meets
RECIPE-ROADMAP P4: at least 18 of 20 briefs with the right style and the right deviations.

## Scope
In:
- Number deviations: a stated number outside the chosen style's range (b08 IBU 50 in 5D, b17
  ABV 7 in 8B, b18 SRM 20 in 15A).
- Mismatch: carried from step 2 (b05).
- Conflict: hints that pull the same knob opposite ways (b11 "dry" vs "full, chewy").
- Ingredient deviations: wanted or inventory ingredients that s3's `level()` rates out of style
  (⚠️) or style-changing (⛔) (b16 rice in 18B, b19 honey in 17C, b20 lactose in 19C).
- Guidance off (b18): deviations are still listed, marked as accepted by the user.
- The G3 checkpoint run and the decision to start stage B.

Out:
- Writing `app.recipe_deviation` rows: they need a recipe, which exists from M6; until then the
  deviations live in the step 3 output. Asking the user anything. Model-made deviations (later
  steps add those).

## Requirements
R1. Step 3 returns a list of deviations, each with `kind` (ingredient · number · mismatch ·
    conflict), `subject` (the ingredient or the number), `from` (what in the style it departs
    from, e.g. "5D IBU 22–40"), `level` (`out_of_style` or `changes_style` for ingredients),
    `requested_by` (`user`) and a `because` text built by code from the facts used.
R2. Number deviations compare each stated number with the chosen style's range in
    `ref.beer_style`; a number inside the range is not a deviation.
R3. Conflicts come from the hint table (RECIPE-ROADMAP §7), held in code: two hints whose knobs
    move the same quantity in opposite directions make one conflict naming both hints.
R4. Ingredient deviations use s3's `level()` on each wanted and inventory ingredient with its
    likely usage; only ⚠️ and ⛔ results become deviations. An ingredient `level()` cannot rate
    (no tags) is reported as `unknown`, not as a deviation and not as fine.
R5. Excluded ingredients are never deviations.
R6. With guidance off, the same deviations are listed; the output says guidance is off.
R7. The step is deterministic code, with no LLM call, and logs to `run_step` (step 3).

## Constraints
- PROJECT.md §3: deviations are listed, never blocked; no blocking questions.
- §6.8: the conflict rules read as one small dict next to their tests.
- Ingredient words are resolved to `ref` ids by the resolver M5 uses; if that resolver does not
  exist yet, this work adds its first version (Open question 1).

## Assumptions
- s3's `level()` takes (style, ingredient, usage, dose) and works with a "typical" dose when no
  dose is known yet *(unverified until s3 is planned)*.
- b02 oats in 21C, b06 rice in 1B, b07 corn in 1C and b12 honey in 31B are typical for their
  styles and give no deviation (from the briefs, `deviations = []`).

## Acceptance criteria
A1. The runner shows ≥ 18/20 briefs with the right style and exactly the expected deviations,
    graded by the harness rule (kind + subject) (R1–R6, G3).
A2. b08, b17, b18 each give one number deviation; b05 one mismatch; b11 one conflict naming
    "dry" and "full"/"chewy"; b16, b19, b20 one ingredient deviation each (R2–R4).
A3. b02, b06, b07 and b12 give no deviation (R4).
A4. b08's excluded Saaz and b16's excluded Citra and Mosaic are not deviations (R5).
A5. b18's output lists the SRM deviation and says guidance is off (R6).
A6. Unit tests for the number, conflict and ingredient rules pass without the stack (R2–R4).
A7. WORKFLOW-ROADMAP G3 and RECIPE-ROADMAP P4 are marked with the measured score.

## Open questions
1. Who resolves ingredient words to `ref` ids first? — options: a) this work adds a simple
   resolver (exact name, then `name_key`, then the harness synonym list), M5 extends it; b) wait
   for M5 — recommend a: `level()` needs ids.
2. Which usage does `level()` assume for a wanted ingredient before the recipe exists? —
   options: a) its most common usage in the style's corpus recipes (s2), else the ingredient
   kind's default (malt → mash, hop → boil); b) always the kind's default — recommend a.

## Deviations
- 2026-10-16 · Needs: `s6-style-neighbours` before the G3 run, so stage A is judged with the
  neighbour check in hand ([SOURCES.md](../../SOURCES.md)).
