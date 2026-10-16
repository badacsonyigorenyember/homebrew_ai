# M5 · Steps 6–9: choose yeast, fermentables, hops and extras

Status: draft
Slug: m5-choose-ingredients · Branch: m5-choose-ingredients
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) M5, checkpoint **G5** ·
[RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §3 steps 6–9 · [STYLE-FIT.md](../../STYLE-FIT.md)
Needs: `m4-targets-blueprint` and `s3-style-fit` shipped
s2-corpus abandoned 2026-10-14; revisit in this brief

## Why
The blueprint says "base 88 %, crystal 5 %, 25 % of hop mass at 60 min". Stage C turns each slot
into a real product the brewer can buy at hopline, chosen by code. The first build's main lesson
is that recipes can only be as good as the catalogue, and an LLM picking products invents them
(PROJECT.md §6.4). Here, every pick is a `ref` id, scored and explained.

## Goal
For every brief, steps 6–9 fill every blueprint slot with a `ref` ingredient, honouring
exclusions and inventory, keeping the pipeline's own picks in style, and reporting what is
missing instead of inventing it. 0 invented ingredients on all 20 briefs.

## Scope
In:
- A resolver from ingredient words (brief `wanted`, `excluded`, `inventory`) to `ref` ids:
  exact name, `name_key`, a synonym list, then a role or class match ("crystal malt" → any
  crystal-role malt); extends M3's first version.
- Step 6 yeast: type/family fits the style, attenuation fits the FG target, inventory first, then
  corpus popularity, then `level()`.
- Step 7 fermentables: each grist role filled; inventory first, then popularity; `max_pct`
  respected; wanted adjuncts placed.
- Step 8 hops: bittering by alpha; late, whirlpool and dry by tag match to hints and the style's
  envelope characters; exclusions removed before scoring.
- Step 9 extras: non-grist extras (none in the 20 briefs; the step passes through with an empty
  list and a test with one made-up extra).
- An "absent" result for slots no `ref` item can fill (b10 Special B, b14 Lactobacillus).
- Brief check: `needs` graded as classes; decide b14 (Open question 1).

Out:
- Amounts (M6). Substitution dialogue ("I have no Crystal 60") beyond exclusion. Inventory-first
  mode as a design driver (Later).

## Requirements
R1. Every chosen item is a `ref.ingredient.id`; a test asserts there is no other way for an item to
    enter the recipe.
R2. Excluded ingredients are never chosen, also not through a synonym or a sibling product (b16:
    no Citra, no Mosaic in any form, LUPOMAX included).
R3. An inventory item that fits a slot (role, type, level not ⚠️/⛔) is chosen over a non-inventory
    one (b10 candi sugar, Munich, abbey yeast; b15 Maris Otter, crystal, EKG).
R4. With guidance on, the pipeline's own picks have `level()` ✅, 👍 or ➖; user-wanted items keep
    the level M3 gave them.
R5. Yeast attenuation is within reach of the FG target (s1) and its type matches the style family
    (lager styles get lager yeast).
R6. Hop late/dry picks score by tag match to hints and envelope characters; b08 picks a
    noble-type hop that isn't Saaz.
R7. A slot with no fitting `ref` item returns `absent` with the reason, and the recipe goes on
    without it; nothing is invented to fill it.
R8. Every pick carries its score breakdown and a because (inventory, popularity n, tag match,
    level), for the sheet.
R9. Each brief's `needs` is graded as classes: each listed item is covered by a pick of that
    class, or reported absent.
R10. Steps are deterministic code and log to `run_step` (steps 6–9).

## Constraints
- PROJECT.md §6.3 and §6.4: absent beats invented; the catalogue is the only source of products.
- §6.8: one readable scoring function per step; weights visible in it.

## Assumptions
- hopline's 90 hops include at least one noble-type hop other than Saaz with tags that say so
  *(unverified until s3 tags them)*.
- Ref covers 45 of the 47 brief ingredient names; Special B and Lactobacillus are not in `ref`
  (adjunct-fermentables report, 2026-10-11).

## Acceptance criteria
A1. 0 invented ingredients across all 20 briefs (R1, G5).
A2. 0 excluded items used (b08, b16) (R2).
A3. b10 and b15 use every inventory item that fits a slot (R3).
A4. With guidance on, no pipeline-made pick is ⚠️ or ⛔ (R4).
A5. Lager briefs (b06, b08, b09, b17) get lager yeasts; b13 a weizen yeast (R5).
A6. b10's Special B slot and b14's Lactobacillus are `absent` with reasons, or follow the answer
    to Open question 1 (R7).
A7. `needs` coverage per brief is printed by the runner; every gap is an `absent` (R9).
A8. You read the picks of 3 briefs and agree a brewer would choose them (G5 direction check).

## Open questions
1. b14 Berliner Weisse needs a souring culture. — options: a) add one Lactobacillus product to
   `ref` from hopline or a maker (its own small work item); b) keep it absent and let the sheet
   say "sour with Lactobacillus or a kettle sour"; c) swap b14 for another wheat style — recommend
   a if hopline sells one, else b. Either way, the souring method and its schedule are sourced from
   the Milk The Funk pages in `shared/rag-files/articles/` (m7-process step 14, kb through
   s7-kb-articles).
2. Popularity vs inventory vs tags: equal weights or an order? — options: a) a strict order
   (inventory, then fit, then popularity); b) weighted sum — recommend a: easier to read and to
   explain on the sheet.

## Deviations
- 2026-10-16 · Open question 1: Milk The Funk souring pages named as the source for option b and
  for m7's souring step ([SOURCES.md](../../SOURCES.md)).
