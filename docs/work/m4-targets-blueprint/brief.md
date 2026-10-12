# M4 · Steps 0, 4 and 5: brewer profile, targets and blueprint

Status: draft
Slug: m4-targets-blueprint · Branch: m4-targets-blueprint
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) M4, checkpoint **G4** ·
[RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §3 steps 0, 4, 5, §7 · [STYLE-PROFILES.md](../../STYLE-PROFILES.md)
Needs: `m3-deviations`, `s1-maths` and `s2-corpus` shipped

## Why
Stage B turns "what the user wants" into numbers to design against: target OG, FG, ABV, IBU and
colour, and the starting ratios (grist % per role, hop split, dosage). Steps 6–11 only fill and
compute against these, so a target that ignores a hint, or a ratio that is not typical for the
style, can't be fixed later. Step 0's brewer profile (batch size, efficiency, water) is also
first needed here, and 15 of 20 briefs state no batch size.

## Goal
For every brief, the pipeline loads a brewer profile, sets targets that follow the style, the
hints and the user's numbers, and builds a blueprint from the style's corpus profile, all by
code. G4's checks pass on all 20 briefs.

## Scope
In:
- Step 0: read the brewer profile from `app.brewer_profile`; one test profile as a fixture
  (WORKFLOW-ROADMAP §3), used when a brief states nothing; a stated batch size overrides it for
  that recipe.
- Step 4: targets from range midpoints, hint knobs (RECIPE-ROADMAP §7, a dict in code, each row
  with its book source), stated numbers; FG and ABV consistent through s1.
- Step 5: blueprint from `corpus.style_profile` and children: grist % per role, hop mass share
  per use, late/dry-hop g/L, yeast attenuation band, a slot for each wanted ingredient; capped by
  rules of thumb with a source.

Out:
- Choosing products (M5). Amounts (M6). Mash temperature beyond the target value (M7 builds the
  mash). Inventory-first design (Later in RECIPE-ROADMAP §8).

## Requirements
R1. Step 0 outputs the profile used: batch L, efficiency %, boil-off, losses, grain absorption,
    the 6 water ions. A stated `batch_l` replaces the profile's for this run and is marked so.
R2. Step 4 starts every target at the style range midpoint. With guidance on, values the model
    chooses stay inside the range; a stated number always wins, inside or outside.
R3. Each hint moves its knobs as the §7 table says (e.g. `bitter` → IBU in the top 25 % of the
    range; `dry` → mash 64–65 °C and higher attenuation; `full` → mash 68–69 °C), from a dict in
    code where every row names its book source or is marked *unsourced*.
R4. A conflict from step 3 (b11) leaves the conflicting knob at its midpoint and is passed on.
R5. Targets are consistent: ABV, OG and FG agree through s1's functions.
R6. Step 5's grist % per role comes from the style's profile (p50), adjusted by hints (`malty` →
    kilned share up, `darker` → crystal/roast up) within the profile's IQR, and sums to 100 %.
R7. Each wanted adjunct gets a grist slot at the style's median dose from `style_ingredient`, or
    a sourced rule of thumb when the corpus has none, never above `ref.fermentable.max_pct`.
R8. Hop split by use (bittering · late · whirlpool · dry) and dosage come from `style_hop_use`;
    `hoppy` / `juicy` raise the late and dry shares.
R9. Every value says where it came from (range midpoint, hint, stated, profile n and blend share),
    so the recipe sheet can explain it.
R10. Both steps are deterministic code and log to `run_step` (steps 0, 4, 5).

## Constraints
- PROJECT.md §3: proportions first, quantities last; the style is guidance.
- Hint knobs are code, not a table (DATABASE.md §8).
- RECIPE-ROADMAP §7: "each row gets a book source before it is trusted".

## Assumptions
- `app.brewer_profile` can hold the test profile as a normal row *(columns per DATABASE.md §5)*.
- s2's profiles cover all 22 brief styles, with family blending where thin *(s2's A4–A6)*.

## Acceptance criteria
A1. For all 20 briefs, every target is inside the style range except where a stated number or
    guidance off says otherwise (R2, G4).
A2. b01's IBU target is in the top 25 % of 21A's range; b06's mash target is 64–65 °C; b03's is
    68–69 °C (R3).
A3. b11's body/mash knob stays at the midpoint and the conflict is in the output (R4).
A4. b08 targets IBU 50 and 10 L; b17 ABV 7; b18 SRM 20 with guidance off (R1, R2).
A5. Each blueprint's grist % sums to 100 ± 0.1, and every wanted adjunct has a slot within its
    `max_pct` (R6, R7).
A6. b02's late + dry hop share is higher than 21C's profile median (R8).
A7. Every hint row in code has a source or is marked unsourced, and the unsourced ones are listed
    in this folder (R3).

## Open questions
1. Test profile values? — options: a) 20 L, 72 % efficiency, soft water (you give the ion numbers
   of your tap water); b) a generic profile from Palmer — recommend a: the recipes are for you.
2. Unsourced hint rows: build with them or wait? — options: a) build, mark them unsourced, source
   them before G6; b) source all first — recommend a.

## Deviations
