# M6 · Steps 10–11: calculate, validate and save (the MVP) — implementation plan

Stage: approved
Brief: [brief.md](brief.md)
Branch: m6-compute-validate

## Approach

- **Step 10 is one SQL function, step 11 another, saving a third.** `app.step10_compute` (new
  `db/046_compute.sql`) turns the steps 6–9 outputs, step 4's targets and step 0's profile into
  amounts and numbers with s1's functions only, and builds the `formulation_check.input` object
  of the recipe. `app.step11_validate` (new `db/047_validate.sql`) runs `app.check_recipe` and
  `app.style_fit_recipe` on that object and checks targets, stated numbers, ids and exclusions
  (R3). `app.save_recipe` (new `db/048_save_recipe.sql`) writes the rows of a passed recipe in one
  transaction (R6, R7). No LLM in any of them (R1, CLAUDE.md).
- **Step 10 takes the same numbers `app.check_recipe` takes, so the check recomputes what step 10
  computed** (R1 "which number"): a fermentable's colour is `app.ebc_mid(ebc)` (middle of the
  range, one bound when open); a fermentable with no colour (Honey, Lactose, Enzyme Malt) counts
  as 0 EBC and is named in `srm_lower_bound`, as `app.style_fit_recipe` already does; a hop's
  alpha is the middle of its range (step 8's `solver.alpha_pct`); the attenuation is
  `app.mash_attenuation(yeast range, mash_c)` (rule 10's figure); extract is
  `extract_dbfg_pct`. OG, FG, ABV and SRM are at the batch volume; IBU at the batch volume with
  the boil gravity from `app.preboil_volume` and `app.boil_gravity(og, batch + losses, preboil)`,
  exactly as in `app.check_recipe`. The fermentation temperature is the `ferm_c` of step 6's
  chosen ferment choice, read from `app.ingredient_choices(yeast, null)` by its label (no text
  parsing); M7 replaces it.
- **Step 10's deterministic adjustments, in this order** (each reported in its output with a
  `because`): (1) boil time = the largest of 60, the grist's largest `min_boil_min` and the
  longest boil addition; the longest boil addition (the bittering one, rule 8) is set to the boil
  time (user decision 2026-10-25, "Set boil, fix hop"); (2) grist kg from `app.solve_grist`; (3) the colour adjustment (R2) when
  SRM misses its target by more than 1, `app.solve_colour` (below); (3b) the mash moved up inside
  rule 10's limits when the predicted FG is below rule 10's range (Task 9b; user decision
  2026-10-26, "Mash + colour reach"); (4) OG moved inside its
  ± 0.002 tolerance towards the ABV target when the ABV misses by more than 0.2 (user decision 2026-10-25, "OG nudge, then LLM");
  (5) hop grams from `app.solve_hops` at the final boil gravity; (6) misc grams = step 9's
  `dose_g_per_l` × batch L; (6b) every amount rounded to what a brewer can weigh and order
  (Task 10b; the grist before the hops, so the hops are solved at the rounded OG's boil gravity);
  (7) OG, FG, ABV, IBU, SRM with `app.og`, `app.fg`, `app.abv`, `app.ibu`,
  `app.srm(app.grist_mcu(...))`, from the rounded amounts.
- **Rounding to weighing steps (Task 10b; user request 2026-10-26, "Now, in M6 (Rec.)").** Steps
  from one function, `app.weighing_steps()`: every malt and flaked grain, roast malts included,
  50 g; sugars, syrups, honey and lactose (role `sugar`) 1 g; hops and extras 1 g; each with a
  floor of one step (never 0) (user answer to Q1, 2026-10-26: "50 g + SRM ± 2"). Because one 50 g
  step of a roast malt moves SRM by more than ± 1 at 20 L (measured, Task 10b), the SRM tolerance
  of step 11 widens to ± 2 in the same task. Each fermentable is rounded down or up to its step (at most 2⁵ = 32
  grists, rule 1 allows 5 fermentables); step 10 takes the grist closest to the exact amounts that
  adds no failure the exact recipe did not have (OG, ABV, SRM against the targets and the stated
  numbers with `app.recipe_tolerances()`, and `app.check_recipe`'s rules, which cover rules 3–6
  shares, rule 10's FG and rule 11's ABV); when none does, the nearest rounding stays and step 11
  fails it, which goes back to the steps 6–9 call (user decision). Then hops to the nearest gram,
  the bittering addition down or up 1 g if that alone pushes IBU out of tolerance. `pct` and a
  hop's `share_pct` are recomputed from the rounded amounts, `recipe.targets.og` is the rounded
  OG, so `app.check_recipe` and A5's recompute from the saved rows give the saved numbers.
- **Colour adjustment (rule 7) is a closed-form solver, as `solve_grist`.** The darkest
  fermentable whose role is not crystal changes its share; the base malt with the largest share
  takes up the difference, so every other share, crystal included, stays exactly as proposed
  (A6; user decision 2026-10-25, "Largest base malt"). MCU is a ratio of two linear functions of that share, so the share solves
  one linear equation. The share must stay above 0 and at most its `max_pct`, and the base malt
  above 0 and at most its `max_pct`; when the darkest non-crystal is the base malt itself or no
  other base malt exists, nothing changes. **Task 9b (user decision 2026-10-26, "Mash + colour
  reach")**: the moving share's upper limit also keeps rules 3 and 5 (a roast stops at the room
  left under the 15 % dark total, an adjunct or sugar under the 40 % adjunct and sugar total), and
  when the move stops at a limit with SRM still more than 1 away, the solver makes one second
  pass with the fermentable that stopped it held fixed: the next-darkest non-crystal moves (the
  mover hit its limit) or the next-largest base malt takes up the change (the base malt hit its
  limit). At most two passes; a crystal never moves. If SRM is still more than 1 from the target,
  step 11 reports a numbers failure (R2).
- **Mash move (Task 9b).** Rule 10 checks the FG predicted at the mash temperature, and
  `app.mash_attenuation` (Troester's curve) lowers the attenuation only above the 68.3 °C knee, by
  4.15 points per °C, never below the yeast's range. So when step 4's mash is the midpoint (not a
  brewer's hint) and the FG predicted at the OG used (after the OG move) is below rule 10's range, step 10 raises
  the mash inside (68.3, 69] °C towards step 4's FG target (bisection; 69 °C when even that leaves FG
  below the target) and makes the OG move again with the new attenuation. An FG above the range cannot be helped by a lower mash (the curve is flat
  below the knee), so the mash stays and the line says why. Rule 10's range comes from one helper,
  `app.rule10_fg_range`, which `app.check_rule_10` also calls, so step 10 and the check read the
  same range. The mash used is `step10.mash_c` and `recipe.mash_c`; saving it with the recipe is
  M7's process work, as the boil time already is, and `evals/show_recipe.py` prints it from the
  step 10 row.
- **Retries (R4, R5; user decision 2026-10-25, "OG nudge, then LLM"):** every step 11 failure (numbers, rule or pick) goes back to the
  steps 6–9 call with its text (rule or number, value, limit), and a pick failure also bans that
  pick. Step 10 is not re-run on its own: its maths is closed form, so the same inputs give the
  same numbers, and its rescales (colour, mash and OG move) already ran inside it. At most 3 tries
  in all.
- **What counts as a pick failure.** With guidance on, a pick the pipeline made on its own (no
  `wanted`, no `inventory` on its step 6–9 pick) whose line in `app.style_fit_recipe` is
  `out_of_style` or `changes_style`; and any excluded product (`app.choose_excluded(frame)`,
  LUPOMAX siblings included). Lines are rated **without the recipe totals** (IBU, SRM): measured
  on the G5 picks, b08's hops are `out_of_style` only because of the user's own 50 IBU, and b03,
  b10, b15, b23's dark malts only because the SRM before the colour adjustment is too high. Those
  are numbers, checked against the targets; banning the pick would be wrong. So
  `app.style_fit_recipe` gains `totals boolean default true`, and step 11 passes false. Wanted
  and inventory picks are never banned (the brewer's choice wins).
- **n8n: the three tries are written out.** A new sub-workflow `Steps 10–11 · compute and
  validate` (contract checks around the two SQL calls, like `Step 4 · targets`), and a new
  `Steps 6–11 · one try` that calls `Steps 6–9 · choose ingredients` and `Steps 10–11`, and logs
  rows 6–11 of that try. The pipeline calls it as `Try 1`, `Try 2`, `Try 3` with an If between
  them, then `Save recipe` and `Finish run`. No loop-back edge: a reader sees the three tries, and
  `$('Node')` references never cross a loop.
- **Retry input to steps 6–9:** `choose.input` gains `feedback` (null on try 1). The sub-workflow
  moves banned ids out of the table into its `excluded` list (`app.choose_ban`), so the existing
  prompt and check refuse them, and appends the failure lines and the failed recipe's picks to the
  prompt (`app.choose_feedback_prompt`). No other prompt change, except Task 9c's: where step
  10's solvers stopped at a limit, step 11's line ends with a concrete `To fix:` instruction
  derived in SQL (user decision 2026-10-26, "Add LLM feedback too").
- **LLM calls (A2, user decision 2026-10-25 "First try ≤ 2"):** `calls` = the sum of
  `run_step.llm.tries` over every row of the run (all tries); `first_try_calls` = the LLM steps
  on try 1, each counted once (step 1 and the steps 6–9 call: 2); `retry_calls` = `calls −
  first_try_calls` (contract retries and tries 2–3). The bar is `first_try_calls ≤ 2`; the other
  two are reported per brief and in the totals.
- **Tolerances live in two places checked against each other:** `app.recipe_tolerances()` in
  `db/047` (OG 0.002, ABV 0.2, IBU 2, SRM 2, batch 0) for step 11, and `evals/grade.py`
  `RECIPE_TOLERANCES` next to the maths tolerances for the harness; a test asserts they are equal
  (user decision "Brewer bar", 2026-10-25; SRM widened from 1 to 2 on 2026-10-26 with the
  rounding, Task 10b, for targets and stated numbers alike). The colour solver in step 10 keeps
  aiming within 1 SRM (its own constant in `app.solve_colour`), so the rounding has the rest of the
  ± 2 to use.

**Measured while planning (2026-10-25, read-only; scratch script, nothing written):** the 24 G5
picks (`evals/results/2026-10-19-m5.json`, b14 run 4246) put through `app.check_recipe` and
`app.style_fit_recipe` the way step 10 will (boil 60 or the largest `min_boil_min`, hop grams from
`app.solve_hops`, no colour adjustment, no OG move):
- rule 8 fails on 8 briefs (b06, b08, b09, b11, b13, b14, b17, b22): the grist needs a 90 min
  boil (Pilsner malts, `min_boil_min` 90) and the LLM's bittering hop is at 60 min (hence step
  10's boil and bittering rule);
- SRM misses its target by more than 1 on 15 briefs, and is null on 4 (b04, b12, b19, b20:
  Honey or Lactose has no colour, hence the 0-EBC lower bound);
- ABV misses by more than 0.2 on 9 briefs, by 0.21–0.49 (b02, b08, b09, b10, b12, b16, b18, b23,
  b24): the yeast's mash-adjusted attenuation differs from the one step 4's FG target assumes. An
  OG move of ± 0.002 shifts ABV by about 0.2, so it would bring about 6 of the 9 inside (estimate,
  unverified; hence step 10's OG move);
- other rule failures: rule 3 b03, b19, b23; rule 4 b19, b22; rule 10 b12, b22; rule 11 b19;
- with totals left in, self-picked lines `out_of_style`: b03 (3), b08 (2, the user's IBU), b10,
  b15, b18 (guidance off), b19 (2), b23 (3); `too_little` hop aroma or flavour on b01, b07, b08,
  b17, b23 (reported, not a failure: R3 does not list it).
So stage D will fail many first tries; the retries carry the work, and the G6 count is unknown
until the run.
Also measured: `app.recipe`, `recipe_item`, `recipe_deviation` 0 rows; `recipe_deviation.level`
check allows only `out_of_style`, `changes_style`; `recipe_item.usage` has no `packaging`
(`ref.misc` Coffee, cold brew has `{packaging}`); `app` has 129 functions; `app.calc_version()` =
`maths-1`; the 25 styles with reviewed envelopes are all used by b01–b24 (`style` or
`alt_styles`), so every held-out style is unrated (accepted by the user, 2026-10-25). The brief's A4 example "1.040 OG at
10 % ABV" raises in step 4 (`fg_for_abv: ABV 10 cannot be reached at OG 1.040`), so it never
reaches step 11; "OG 1.080 at 2 % ABV" passes step 4 (FG 1.0638) and no recipe can meet it (the
lowest yeast attenuation middle is 67.5 %), so A4's test uses that one. In
`tests/test_pipeline.py` the `post` fixture deletes runs and briefs; `app.recipe` references
`app.brief` without cascade, so the fixture must delete recipes first.
**Measured after the first G6 run (2026-10-26, read-only; scratch SQL calling the existing
functions on the logged step 10 and 11 inputs of runs 4463–4487, nothing written):** b01–b20
validated 13/20, bar 16 (failed b03, b07, b09, b10, b12, b18, b19); 15/24 overall after the
b22–b24 reruns (runs 4485–4487). Every failed brief failed the same way on all 3 tries, because the
steps 6–9 call returned the same or similar picks and step 10 is closed form. Causes:
- FG below rule 10's range at the 66.5 °C midpoint mash: b09 (1.0099 vs 1.0100–1.0140), b12
  (1.0070 vs 1.0080–1.0130), b18 (1.0099), b22 (1.0097 vs 1.0100–1.0120). No G6 brief has an FG
  above its range.
- colour not reachable: b03 (Roasted Barley at the 0.01 % floor, SRM 35.9 vs 31; on tries 2–3 the
  solver reached 31 by raising Chocolate Dark Malt and so broke rule 3, 16.1 % and 15.2 %), b07
  (Pale Ale Malt is the only base and the darkest), b10 (Brown Candi Sugar, no base malt), b18
  (Roasted Barley at its max 2 %), b19 (the colour is in two crystals), b23 (Black Malt at 0.01 %).
- ABV high after the OG move hit ± 0.002: b10, b12, b23.
Replaying Task 9b's two changes on those inputs (the mash by calling `app.step10_compute` with
another `mash_c`, the second pass by calling `app.solve_colour` again with the first mover marked
as crystal, rule 3's cap by lowering the roast's `max_pct`; then `app.step11_validate`):
- b09 passes on try 1: FG 1.0110 at 68.6 °C, 1.0114 at 69 °C, step 11 passed.
- b22's try-2 and try-3 picks pass (FG 1.0103–1.0111 at 68.6–69 °C); its try 1 still fails rule 4.
- b03 try 1 still fails: the second pass reaches SRM 31.0 with Chocolate Dark Malt 6.07 % but
  breaks rule 3 (16.1 %); with rule 3's cap Chocolate stops at 5 % and SRM is 28.1. G6's try-3
  picks would pass with the cap (Chocolate 6.08 %, rule 3 at 15 %, SRM 30.5).
- b05 (passed on try 2) reaches its colour on try 1: Chocolate Dark Malt 5 → 9.43 %, SRM 32.5,
  rule 3 at 11.4 %.
- b23 reaches its colour on try 1 (Chocolate Dark Malt 10 → 7.48 %, SRM 35.0) but its ABV 6.25 vs
  5.99 stays: FG 1.0121 is inside its range, so the mash does not move (a mash of 68.6 °C would
  give 6.15; not part of the user's decision).
- not helped: b07 (Flaked Corn, the only lighter fermentable, is at its max 20 %); b10 (even with
  Munich Malt Type 1 taking up the change, which a non-base malt may not, Brown Candi Sugar and
  Abbey Malt at 0.01 % give SRM 14.7 vs 13.5); b12 (SafAle US-05's range is 78–82 %, so at 68.8 °C
  and above it sits at 78 % and FG is 1.0077 vs 1.0080; its ABV comes inside at 4.68); b18 (British
  Ale's range is 75–75 %, so the mash changes nothing); b19 (crystal shares never move; rules 3, 4
  and 11 also fail).
Expected after Task 9b *(estimate, unverified: retries depend on the LLM)*: b01–b20 14 (b09) to 15
(b03 if its retries land as in G6) of 20, still below A1's 16; b22 likely passes. Seeing this, the
user added Task 9c (2026-10-26, "Add LLM feedback too"): the retry is told what to change where
the solvers stop. The attenuation each remaining brief would need, by scanning `app.fg` over
attenuation on its try-1 grist at the OG used: b12 at most 77 % for FG 1.0080 (SafAle US-05 sits at
78 %) and about 76 % for its ABV; b18 at most 74.5 % for FG 1.0100 (British Ale is 75 %); b23 about
77 % for ABV 5.99 (US-05 gives 80 %); b10 about 76 % for ABV 7.18.
Expected after Tasks 9b and 9c *(estimate, unverified)*: b01–b20 about 15–17 of 20 — b07 (one
change: a lighter base malt) likely, b12 (one change: a yeast near 76 %, or less honey) plausible,
b10 and b18 (two or three changes each) possible, b19 unlikely; b23 plausible. The bar of 16 is
within reach, not assured. The user chose to re-measure once with the bar unchanged (2026-10-26).
Re-measured (`m6-9b`, Task 10): 17 of b01–b20, 20/24.
**Measured for Task 10b (2026-10-26, read-only; scratch SQL and Python in a rolled-back
transaction, nothing written):** the last try's logged step 10 output of the 20 validated m6-9b
runs (4503–4526 without 4514, 4520, 4521, 4525), amounts rounded, OG, FG, ABV, IBU and SRM
recomputed with s1's functions (`app.og`, `app.fg`, `app.abv`, `app.ibu` at the rounded OG's boil
gravity, `app.srm(app.grist_mcu())`), `recipe.targets.og` and `pct` from the rounded amounts, then
`app.step11_validate` on the logged step 11 input. These are the saved picks only; what a retry
would do is not replayed *(unverified)*.
- As decided (50 g every malt, nearest step): 11 of the 17 b01–b20 pass. Failing: b03 (ABV 5.51 vs
  5.27, SRM 32.1 vs 31: Roasted Barley 18 → 50 g, Chocolate Dark Malt 312 → 300 g, Caramel 150
  Malt 416 → 400 g), b04 (SRM 36.04 vs 35), b05 (SRM 31.04 vs 32.5), b15 (SRM 15.15 vs 12: Black
  Malt 15 → 50 g in 23 L), b16 (OG 1.0504 vs 1.0525: its OG move sat on the limit), b20 (ABV 4.86
  vs 5.08); b21, b24 pass, b22 fails rule 4 (Caraamber 442 → 450 g, 10.1 %). A11's five: b01, b08,
  b10, b24 pass, b03 fails.
- 50 g with each malt rounded down or up (best of the 2ⁿ): 13 of 17 (adds b16, b20, b22; b03 needs
  Caramel 150 Malt one step below its floor, 350 g). With one step further either way (3ⁿ): 14 of
  17. b04, b05 and b15 pass at no 50 g grid point even two steps either way: at 20 L one 50 g step
  of Chocolate Dark Malt moves SRM about 2.4, wider than the ± 1 tolerance (b04: 33.66 at 400 g,
  36.04 at 450 g, target 35); b05's Roasted Barley is at its 2 % `max_pct` (74 g), so 100 g breaks
  rule 6 and 50 g is too light; b15's 50 g floor alone gives + 3 SRM. **So 14 of b01–b20 at best at SRM ± 1,
  below A1's 16.**
- (Q1 option a, not chosen) Roast malts at 10 g (floor 10 g), the rest as decided, each rounded down or up: **all 17 pass**
  (b01–b20 17/20), b21, b22, b24 pass, A11's five all pass (b03: Roasted Barley 20 g, SRM 30.8).
  Nearest alone gives 13 of 17, so the down-or-up choice is needed either way.
- The user chose 50 g for every malt with SRM ± 2 (Q1 c, 2026-10-26). **Measured for that
  (second pass, same method, all 24 runs' last tries, step 11's SRM and stated-SRM failures
  accepted when within 2 of the target or stated value, each malt rounded down or up as Task 10b
  does):** b01–b20 **16 of 20**, exactly A1's bar, no margin. Pass: b01, b02, b04–b11, b13, b14,
  b17 at the nearest step; b03 (SRM 32.1, ABV 5.46 with Maris Otter rounded down to 3.65 kg), b16
  (Pale Ale Malt 3.25, Flaked Rice 0.95 kg, OG 1.0509), b20 (Caramel 50 Malt up to 0.50 kg, ABV
  4.92) only with the down-or-up choice. Fail: b15 (SRM 15.15 vs 12 at the 50 g floor of Black Malt
  in 23 L, + 3.15; no grid point within two steps helps), b12 (rule 10, as before), b18 (exact
  amounts SRM 17.87 vs 20, − 2.13, so still out at ± 2; the rounded grist also breaks rule 6:
  Roasted Barley 2.5 %, Red Ale Malt 20.3 %), b19 (its last try's exact amounts would pass at
  ± 2, but at 10 L the 50 g steps break rule 4 (Caramel 300 Malt 228 → 250 g, 5.4 %), ABV and
  SRM, and no down-or-up grist avoids it). b21, b22 (rule 4 kept by Caraamber 400 g), b24 pass;
  b23 fails (ABV, as before). 19/24 overall. A11's five all pass. *Unverified: retries are not
  replayed, so b15 and b19 on the real pipeline would go back to the steps 6–9 call; the count
  could move either way.*
- Rounded amounts of the A11 five (50 g, nearest): b01 Pale Ale Malt 4.808 → 4.80 kg, Caramel 50
  0.566 → 0.55, Caramel 30 0.283 → 0.30, Columbus 36.51 → 37 g, Citra and Mosaic 27.382 → 27 g;
  b24 Pale Ale Malt 4.183 → 4.20 kg, both caramels 0.232 → 0.25, Cascade 48.491 → 48 g; b08
  Pilsner Malt 1.928 → 1.95, Carapils 0.101 → 0.10, Magnum 12.673 → 13 g, Tettnanger 8.448 → 8 g;
  b10 Brown Candi Sugar 89 g stays (1 g step). IBU moves at most 1.4 (b01 66.3 → 67.2 nearest),
  inside ± 2 everywhere; no hop needed the down-or-up step.
- `app.check_recipe` costs about 0.74 ms a call (243 calls 180 ms), so 32 candidate grists add
  about 25 ms to step 10.

**Context7 not used:** no library question in this plan; n8n behaviour comes from the repo's
existing workflows and OPERATIONS §5.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `db/045_recipe_deviation_kind.sql` | new | `app.recipe_deviation.kind`, `level` nullable (R7) |
| `db/031_formulation_rules.sql` | changed | rule 7's sentence names the second pass (Task 9b) |
| `db/032_formulation_check.sql` | changed | `check_recipe_items` resolves `extras` (ref.misc); numbers unchanged (R8); `app.rule10_fg_range` (Task 9b) |
| `db/034_style_level.sql` | changed | `app.style_fit_recipe(recipe, extras, totals)`; extras default to `recipe.extras` |
| `db/046_compute.sql` | new | `app.solve_colour`, `app.step10_boil`, `app.step10_compute`; Task 9b: second colour pass, rule 3 and 5 caps, mash move; Task 10b: `app.weighing_steps`, `app.recipe_rule_failures`, `app.step10_round_grist`, `app.step10_round_hops`, rounding in `app.step10_compute` |
| `db/047_validate.sql` | new | `app.recipe_tolerances`, `app.step11_validate`; Task 9c: `app.attenuation_for_fg`, `app.step11_fix`; Task 10b: SRM tolerance 2, rule failures through `app.recipe_rule_failures`, the rounding note on a failure rounding added |
| `db/048_save_recipe.sql` | new | `app.save_recipe` |
| `db/042_choose_table.sql` | changed | `app.choose_ban`, `app.choose_feedback_prompt` (Task 9c: one header sentence) |
| `shared/contracts/formulation_check.input.schema.json` | changed | optional `extras` |
| `shared/contracts/choose.input.schema.json` | changed | `feedback` (null or object) |
| `shared/contracts/step10.{input,output}.schema.json`, `step11.{input,output}.schema.json` | new | logged step rows; Task 10b: `step10.output.rounding` |
| `shared/contracts/try.input.schema.json`, `try.output.schema.json` | new | `Steps 6–11 · one try` |
| `n8n/workflows/steps-10-11-compute-validate.json` | new | sub-workflow `Steps 10–11 · compute and validate` |
| `n8n/workflows/steps-6-11-one-try.json` | new | sub-workflow `Steps 6–11 · one try` |
| `n8n/workflows/steps-6-9-choose-ingredients.json` | changed | ban and feedback on a retry |
| `n8n/workflows/recipe-pipeline.json` | changed | three tries, save, finish |
| `tests/fixtures/reference_recipes.toml` | changed | b23, b24 with `extra` (R8, A9) |
| `evals/heldout_briefs.toml` | new | 5–10 held-out briefs (R10) |
| `evals/run.py`, `evals/grade.py` | changed | recipe columns, tolerances, calls, `--briefs` (R9); Task 10b: `RECIPE_TOLERANCES` SRM 2 |
| `evals/show_recipe.py` | new | prints a saved recipe for your review (A11) |
| `evals/revalidate.py` | new | Task 10b: re-runs steps 10–11 (SQL only, no LLM, nothing saved) on the logged picks of a results file's runs |
| `evals/results/<date>-m6-10b-revalidate.json` | new | Task 10b: the m6-9b picks re-validated after rounding |
| `evals/results/2026-10-25-m6.json`, `2026-10-26-m6-b22.json`, `-b23.json`, `-b24.json` | new | G6 first attempt (before Task 9b), kept as the before measurement |
| `evals/results/<date>-m6-9b.json`, `<date>-m6-heldout.json` | new | G6 re-measure after Task 9b, held-out run |
| `docs/work/m6-compute-validate/g6-recipes.md` | new | the 5 recipes for the A11 gate, printed by `evals.show_recipe` |
| `tests/test_recipe_tables.py`, `test_compute.py`, `test_validate.py`, `test_save_recipe.py` | new | Tasks 1, 3–6 |
| `tests/step1011_sample.json`, `tests/step611_sample.json` | new | Test data notes of the new sub-workflows |
| `tests/test_formulation_check.py`, `test_reference_recipes.py`, `test_style_fit_recipe.py`, `test_choose_table.py`, `test_contracts.py`, `test_workflows.py`, `test_pipeline.py`, `test_grade.py`, `test_run.py`, `test_recipe_briefs.py`, `tests/step69_sample.json` | changed | as each task says |
| `docs/RECIPE-ROADMAP.md`, `docs/WORKFLOW-ROADMAP.md`, `docs/DATABASE.md`, `docs/OPERATIONS.md` | changed | Task 11 |
| `PROJECT.md` | changed | §4 rows, §8 per task |

Apply command for every SQL file (OPERATIONS §4), run twice to show it is idempotent, then check
owners with `select proname, pg_get_userbyid(proowner) from pg_proc where pronamespace =
'app'::regnamespace and proname = any(<names>)` (all `postgres`):
`docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/<file>.sql`
Each new SQL file gets the header the others have (purpose, work folder, needs, apply command,
idempotent). Workflows are imported with the n8n CLI (OPERATIONS §5: edit the JSON, copy to
`shared/`, `import:workflow`, publish through the MCP, delete the copy), sub-workflows published
before the pipeline, then `.venv/bin/python -m evals.workflows`.

## Tasks

### Task 1: every step 3 deviation fits `app.recipe_deviation`
Why: R7 (null levels for number, mismatch and conflict rows), A8.
- [x] `db/045_recipe_deviation_kind.sql` (needs 015): `add column if not exists kind text`;
      backfill none needed (0 rows, measured); `alter column kind set not null`; check
      `recipe_deviation_kind_check` `kind in ('ingredient', 'number', 'mismatch', 'conflict')`;
      `alter column level drop not null`; check `recipe_deviation_level_kind_check`
      `(kind = 'ingredient') = (level is not null)` (an ingredient deviation has a level, the
      others have none, as step 3 gives them). Drop-and-add each constraint so a re-run works.
- [x] Apply twice; `\d app.recipe_deviation` shows `kind` not null and `level` nullable.
- [x] Write `tests/test_recipe_tables.py` (stack, every insert rolled back):
      `test_deviation_takes_every_step3_kind` (one row per kind as step 3 gives it, from
      `app.step3_deviations` of b05, b08, b11, b16 via `tests.test_step4` helpers: inserts pass),
      `test_ingredient_deviation_needs_a_level` (kind ingredient, level null: refused),
      `test_number_deviation_has_no_level` (kind number with a level: refused). See them fail
      before the file is applied.
- [x] `docs/DATABASE.md` `app.recipe_deviation` row. PROJECT.md §8 entry.
Done when: the three tests pass and the file applies twice.
Commit: `Let recipe deviations keep step 3 kinds`

### Task 2: the formulation check takes extras; b23 and b24 get reference recipes
Why: R8, A9 (RECIPE-ROADMAP §8 Later TODO).
- [x] `shared/contracts/formulation_check.input.schema.json`: optional `extras` array, items
      `{ingredient_id integer, usage enum mash|boil|whirlpool|ferment|secondary|packaging,
      g number ≥ 0, purpose string}`, all required, `additionalProperties: false`. Not in the
      top-level `required`, so every existing input stays valid.
- [x] `db/032_formulation_check.sql` `app.check_recipe_items`: each extra must be a `ref.misc`
      row (else raise `check_recipe: ingredient % is not a misc item`) and its usage one of the
      row's `usages` (else raise); returned as `extras [{ingredient_id, name, usage, g,
      purpose, category}]`. `app.check_recipe` does not read them: OG, FG, ABV, IBU and SRM are
      unchanged (comment says so).
- [x] `db/034_style_level.sql` `app.style_fit_recipe(recipe jsonb, extras jsonb default null,
      totals boolean default true)`: extras null → `recipe -> 'extras'` (or `[]`); `totals` false
      leaves `ibu`, `srm` and `srm_lower_bound` out of every line's dose (the comment says why:
      step 11 rates a pick on its own use, the totals are checked against the targets). Drop the
      two-argument version first (CREATE OR REPLACE cannot add a defaulted argument cleanly).
- [x] Apply 032 and 034 twice; owners `postgres`.
- [x] `tests/fixtures/reference_recipes.toml`: `[[recipe]]` b23 (20B base with Coffee, whole
      beans and Vanilla bean, as `extra = [{name, usage, g, purpose}]`, g = the step 9 dose ×
      20 L: coffee 3.0 g/L → 60 g, vanilla 0.05 g/L → 1 g) and b24 (18B with Orange peel,
      whirlpool, 2.64 g/L × 20 L = 52.8 g). Targets from `app.step4_numbers` as the header says;
      only `ref` ingredients. Header gains the `extra` field.
- [x] `tests/test_reference_recipes.py`: `build_input` adds `extras` (misc ids by name);
      `test_every_brief_has_exactly_one_recipe` expects all 24.
- [x] Write `tests/test_formulation_check.py::test_extras_do_not_enter_the_numbers` (a recipe
      with and without b23's two extras: same `numbers`), `test_extra_must_be_misc` (a hop id
      as extra raises), `test_extra_usage_must_be_its_rows` (coffee at `boil` raises);
      `tests/test_style_fit_recipe.py::test_extras_read_from_recipe` (no second argument: misc
      lines present) and `test_totals_off_rates_picks_on_their_own` (b08's reference recipe at
      50 IBU: Magnum `out_of_style` with totals, not with `totals => false`). See each fail first.
- [x] Run `.venv/bin/pytest tests/test_formulation_check.py tests/test_reference_recipes.py tests/test_style_fit_recipe.py tests/test_misc.py tests/test_contracts.py`, expect all pass.
- [x] PROJECT.md §8 entry. b23 and b24 recipes are shown to you at the Task 9 gate.
Done when: 24 reference recipes pass `app.check_recipe` (A9).
Commit: `Check extras and add b23 and b24 references`

### Task 3: the colour adjustment (rule 7) as tested code
Why: R2, A6. s1 has no colour solver (`pg_proc`: `solve_grist`, `solve_hops` only).
- [x] `db/046_compute.sql` (needs 030, 032): `app.solve_colour(target_srm numeric, grist jsonb,
      target_og numeric, efficiency_pct numeric, volume_l numeric) returns jsonb`. Grist items
      `{ingredient_id, name, role, pct, extract_pct, mashed, ebc, max_pct}` (`ebc` null counts as
      0). Returns `{grist, adjusted, reached, srm, darkest, absorber, from_pct, to_pct,
      because}`. Darkest = the highest `ebc` among roles other than `crystal` (ties: larger share,
      then lower id); absorber = the `base` fermentable with the largest share other than the
      darkest. Nothing changes (`adjusted` false) when the SRM at the proposed shares is within 1
      of the target, when there is no absorber, or when the darkest is not darker than the
      absorber. Otherwise solve the darkest's share in closed form (comment derives it from
      `app.grist_mcu` and `app.solve_grist`: MCU = K·N(x)/D(x), both linear in x), clamp to
      (0, `max_pct`] and keep the absorber in (0, its `max_pct`], recompute SRM with
      `app.srm(app.grist_mcu(app.solve_grist(...)))`; `reached` = within 1. `because` names the two
      fermentables and the shares, or why nothing changed.
- [x] Apply twice; owner `postgres`.
- [x] Write `tests/test_compute.py` (stack), each seen failing first:
      `test_colour_moves_only_darkest_and_base` (A6: b15's G5 grist, Maris Otter 88, Crystal
      T50 10, Black Malt 2, target 12: only Black Malt and Maris Otter change, Crystal T50 stays
      10, shares sum 100, SRM within 0.01 of 12); `test_colour_never_moves_crystal` (a grist whose
      darkest is a crystal: the darkest non-crystal moves); `test_colour_reports_unreachable` (b18's
      grist with Roasted Barley at its `max_pct` 2 and target 20: `reached` false, share stays 2);
      `test_colour_needs_a_base` (b01's grist, darkest non-crystal is the base: `adjusted` false
      with the reason); `test_colour_within_tolerance_is_left_alone`;
      `test_colour_matches_s1` (the returned SRM equals `app.srm(app.grist_mcu(...))` of the
      returned grist solved with `app.solve_grist`).
- [x] PROJECT.md §8 entry.
Done when: the colour tests pass.
Commit: `Add the rule 7 colour solver`

### Task 4: step 10 computes amounts and numbers
Why: R1, R2, A5 (SQL half), A7; brief assumptions on boil time and yeast amount.
- [x] `db/046_compute.sql`:
      - `app.step10_boil(grist_ids bigint[], hops jsonb) returns jsonb` → `{boil_min, because}`:
        the largest of 60 (rule 13's floor), the grist's largest `min_boil_min` and the longest
        boil addition's minutes.
      - `app.step10_compute(profile jsonb, targets jsonb, step6 jsonb, step7 jsonb, step8 jsonb,
        step9 jsonb, brief jsonb) returns jsonb` (`targets` is step 4's output). In order: batch =
        `targets.batch_l.value`, efficiency, boil-off and losses from the profile; boil from
        `app.step10_boil`, and the longest boil addition set to it; grist items from step 7
        with `ref.fermentable` facts (`extract_dbfg_pct`, `app.ebc_mid(ebc)`, role, `max_pct`,
        fermentability, mashed = role ≠ `sugar`, as `check_recipe_items`); `app.solve_colour`
        at the target OG; the OG move: when `app.abv(og, fg)` at the target OG misses the
        ABV target by more than 0.2, bisect OG in [target − 0.002, target + 0.002] for the ABV
        target (ABV rises with OG at fixed shares; 40 halvings), else keep the target; grist kg
        from `app.solve_grist` at that OG; hop grams from `app.solve_hops(ibu target, step 8
        solver with the bittering minutes, boil gravity, batch)`; misc g = `dose_g_per_l` ×
        batch (a null dose raises `step 10: no dose for <name>`); yeast rows: step 6's main
        yeast and souring culture (if any) each `1 pack` (placeholder until M7 sets the pitch
        rate); `ferm_c` from `app.ingredient_choices(main yeast, null)` where `label` = step 6's
        `choice`. Numbers: `app.og`, `app.fg` at `app.mash_attenuation`, `app.abv`, `app.ibu`,
        `app.srm(app.grist_mcu(...))` with no-colour items at 0 EBC.
        Output: `{batch {volume_l, efficiency_pct, boil_off_l_h, losses_l}, boil, mash_c,
        ferm_c, og_used {value, moved, because}, colour (solve_colour's result), fermentables
        [{ingredient_id, name, usage, pct, kg, purpose}], hops [{ingredient_id, name, usage,
        minutes, share_pct, alpha_pct, g, purpose}], yeasts [{ingredient_id, name, role
        main|souring, amount 1, unit pack, purpose}], extras [{ingredient_id, name, usage
        (`packaging` saved as `package`), time_min, dose_g_per_l, g, purpose}], numbers {og, fg,
        abv, ibu, srm, attenuation_pct, srm_lower_bound [names]}, values_used [{what, because}]
        (one line each for colour, alpha, attenuation, ferm_c, boil, yeast amount), recipe}`,
        where `recipe` is the `formulation_check.input` object (style code, guidance, stated
        without `batch_l`, hints, targets as numbers, batch, mash, boil, fermentables, hops with
        g, yeast with `ferm_c`, extras with g) that step 11 checks. Stated numbers and hints come
        from step 1's brief, which `step10.input` carries; the function takes it as a seventh
        argument `brief jsonb`.
- [x] Contracts `step10.input` = `{run_id, try, brief, profile, targets, step6, step7, step8,
      step9}`, `step10.output` as above (all required, `additionalProperties: false`, nulls where
      the text above allows them). `tests/test_contracts.py` `NAMES` gains both.
- [x] Apply twice; owners `postgres`.
- [x] Write in `tests/test_compute.py` (stack; inputs: step 4 via `tests.test_step4.step4`,
      profile `app.step0_profile(null)`, steps 6–9 from `good_proposal` through
      `app.choose_outputs` as `tests/test_choose_outputs.py` does), each seen failing first:
      `test_amounts_hit_the_targets` (b01, b08, b10, b14, b16, b23, b24: OG within 0.002 of the
      target, IBU within 0.01 of it, kg and g positive, pct equal step 7's except the two colour
      shares); `test_numbers_are_what_check_recipe_computes` (A5 SQL half: `app.check_recipe` of
      `output.recipe` gives the same OG, FG, ABV, IBU and, where every fermentable has a colour,
      SRM within 1e-9); `test_misc_grams_are_dose_times_batch` (A7: b23 coffee 3.0 × 20 = 60 g and
      vanilla 1 g, b24 orange peel 52.8 g; none in OG/IBU/SRM: removing extras changes no number);
      `test_values_used_named` (R1: every range pick has its line); `test_boil_covers_grist_and_hops`
      (b08: Pilsner Malt → 90, bittering hop at 90; b01 60); `test_og_moves_only_inside_tolerance`
      (a grist with a high-attenuation yeast: OG within 0.002 and ABV nearer the target than at
      the target OG; a case that is in tolerance at the target OG keeps it); `test_lower_bound_named`
      (b04-style grist with Lactose: `srm_lower_bound` = ["Lactose"]); `test_ferm_c_from_choice`
      (b01 US-05 at "ferment at 18 °C" → 18); `test_output_meets_contract`;
      `test_same_input_same_output`.
- [x] Run `.venv/bin/pytest tests/test_compute.py tests/test_contracts.py tests/test_maths.py`, expect all pass.
- [x] `docs/DATABASE.md` §5: the functions of `db/046`. PROJECT.md §8.
Done when: step 10 outputs meet their contract and `app.check_recipe` recomputes their numbers.
Commit: `Compute amounts and numbers in step 10`

### Task 5: step 11 validates and says what to retry
Why: R3, R4 (the failure kinds and the ban), A4 (SQL half).
- [x] `db/047_validate.sql` (needs 046, 042, 034, 032):
      - `app.recipe_tolerances() returns jsonb` immutable: `{"og": 0.002, "abv": 0.2, "ibu": 2,
        "srm": 1, "batch_l": 0}`, comment: user decision "Brewer bar" 2026-10-25, for targets and
        stated numbers alike; `evals/grade.py` `RECIPE_TOLERANCES` must equal it.
      - `app.step11_validate(step10 jsonb, brief jsonb, targets jsonb, frame jsonb, picks jsonb)
        returns jsonb`. `picks` = every step 6–9 pick `{ingredient_id, name, self_picked}`
        (`self_picked` = no `wanted` and no `inventory`). Runs `app.check_recipe(step10.recipe)`
        and `app.style_fit_recipe(step10.recipe, null, false)`. Failures, each `{kind, subject,
        value, limit, text, ban}`:
        `numbers`: OG, ABV, IBU, SRM against step 4's targets with `app.recipe_tolerances()`
        (a null number fails: "cannot be computed: <missing>"); every stated `og`, `abv`, `ibu`,
        `srm` against the computed number; stated `batch_l` equal to `step10.batch.volume_l`; the
        SRM text adds the colour adjustment's `because` when it did not reach the target.
        `rule`: every `check_recipe` result with status `fail`, its failures' texts (they name
        the rule, items, value and limit).
        `pick`: with `targets.guidance` true, every self-picked line `out_of_style` or
        `changes_style` (`ban` = its id); every recipe id in `app.choose_excluded(frame)`
        (`ban` = its id); every item without a `ref` id. Wanted and inventory picks never get a
        `ban`.
        Output: `{passed, failures, banned [{ingredient_id, name, why}], feedback [text],
        check (check_recipe's output), style_fit (style_fit_recipe's output, `too_little` and
        `required` kept for the record only), targets [{key, target, value, tolerance, met}],
        stated [{key, stated, value, tolerance, met}], model_deviations [{subject, level, note}]}`.
        `model_deviations`: self-picked lines `out_of_style` or `changes_style` when guidance is
        off (R6; with guidance on such a line fails instead). `feedback`: one plain line per
        failure, ending with "(banned for the next try)" on a ban.
- [x] Contracts `step11.input` = `{run_id, try, brief, targets, frame, picks, step10}`,
      `step11.output` as above. `NAMES` gains both.
- [x] Apply twice; owners `postgres`.
- [x] Write `tests/test_validate.py` (stack, inputs as Task 4), each seen failing first:
      `test_good_recipe_passes` (b16 from its good proposal, after step 10: passed, no failures);
      `test_target_miss_is_a_numbers_failure` (SRM target moved 3 away: one `numbers` failure,
      value and limit set, no ban); `test_stated_numbers` (b01 ABV 6.5 met; b08 IBU 50 met;
      a stated batch 23 with `volume_l` 20 fails); `test_rule_failure_names_rule_value_limit`
      (a grist with 20 % roast: rule 3 failure text, no ban); `test_self_pick_out_of_style_is_banned`
      (an out-of-style self-picked hop in b08: `pick`, ban its id); `test_wanted_pick_is_never_banned`
      (b23's coffee rated out of style: no ban); `test_user_ibu_does_not_ban_hops` (b08 at its
      stated 50 IBU: no pick failure); `test_excluded_product_fails` (b16 with Citra LUPOMAX forced
      in: `pick`, ban); `test_impossible_target_cannot_pass` (A4 SQL half: "OG 1.080 at 2 % ABV"
      through steps 2–5 and a good proposal: failures include ABV and rule 10, for any yeast in the
      table: loop over every yeast row, none passes); `test_guidance_off_gives_model_deviations`
      (b18: self-picked out-of-style lines become `model_deviations`, not failures);
      `test_output_meets_contract`.
- [x] Run `.venv/bin/pytest tests/test_validate.py tests/test_compute.py tests/test_contracts.py`, expect all pass.
- [x] `docs/DATABASE.md` §5. PROJECT.md §8.
Done when: each failure kind has a test and the impossible target never passes.
Commit: `Validate recipes in step 11`

### Task 6: a validated recipe is saved as rows
Why: R6, R7, A5, A8 (SQL halves).
- [x] `db/048_save_recipe.sql` (needs 045, 047): `app.save_recipe(run_id bigint, step3 jsonb,
      targets jsonb, step10 jsonb, step11 jsonb) returns bigint`. Raises unless `step11.passed`
      is true (R5) and unless the run has a `brief_id`. Inserts `app.recipe` (`brief_id` from
      `app.run`, `style_id` from `ref.beer_style` by `targets.style.code`, `status` draft,
      `targets` = step 4's output, `og`, `fg`, `abv`, `ibu`, `srm` from `step10.numbers`,
      `batch_l` and `efficiency_pct` from `step10.batch`, `calc_version` = `app.calc_version()`);
      one `app.recipe_item` per fermentable (`kg`, `pct`, usage, `time_min` null), hop (`g`,
      `pct` = share, minutes), yeast (`1 pack`, usage `ferment`), extra (`g`, usage, `time_min`),
      each with `ingredient_id` and `raw_name` = the ref name; one `app.recipe_deviation` per step
      3 deviation (`kind`, `subject`, `level`, `requested_by` user, `note` = `because`) and per
      `step11.model_deviations` row (`kind` ingredient, `requested_by` model); then `update app.run
      set recipe_id`. Returns the recipe id. One function, so a failure saves nothing.
- [x] Apply twice; owner `postgres`.
- [x] Write `tests/test_save_recipe.py` (stack; a throwaway `app.run` and `app.brief`, rolled
      back), each seen failing first: `test_rows_match_step10` (b23: item count = fermentables +
      hops + yeasts + extras, amounts equal step 10's at the column scale, units kg/g/pack, coffee
      60 g, A7); `test_recompute_from_saved_rows` (A5: OG, IBU, SRM recomputed from the saved
      `recipe_item` rows with `app.og`, `app.ibu`, `app.srm(app.grist_mcu())` and the same `ref`
      values equal the saved numbers within OG 0.001, IBU 1, SRM 1 — the helper lives in
      `tests/test_save_recipe.py` and is reused by `tests/test_pipeline.py`);
      `test_every_step3_deviation_saved` (A8: b05 mismatch, b11 conflict, b08 number with level
      null, b16 ingredient with its level, all `requested_by` user); `test_model_deviation_saved`;
      `test_refuses_a_failed_validation`; `test_run_points_to_recipe`; `test_snapshot_fields`
      (`calc_version` `maths-1`, batch, efficiency, `targets` = step 4's output).
- [x] Run `.venv/bin/pytest tests/test_save_recipe.py tests/test_recipe_tables.py`, expect all pass.
- [x] `docs/DATABASE.md` §5. PROJECT.md §8.
Done when: a passed recipe saves completely, and a failed one saves nothing.
Commit: `Save validated recipes`

### Task 7: steps 6–9 take the retry feedback
Why: R4 (rule, value, limit, banned pick back to the one LLM call).
- [x] `shared/contracts/choose.input.schema.json`: `feedback` required, `null` or `{try integer
      2–3, lines [string], banned [{ingredient_id, name, why}], last {fermentables, hops, yeast,
      extras} (the failed try's picks: names, pct, share, usage, minutes)}`.
      `tests/step69_sample.json` gains `"feedback": null`.
- [x] `db/042_choose_table.sql`: `app.choose_ban(tbl jsonb, feedback jsonb) returns jsonb`: null
      feedback returns `tbl`; else removes every banned id from `fermentables`, `hops`, `yeasts`,
      `misc` and from `slots[].ids` and `inventory_words[].ids`, and appends to `excluded`
      `{ingredient_id, name, word: name, why: "failed step 11 on try <n>: <why>"}`, so the
      existing check refuses a banned id with its message. `app.choose_feedback_prompt(feedback
      jsonb) returns text`: empty for null; else a block "Try <n>: the last recipe failed step
      11. Fix these and change as little else as you can:" with the lines, then the last picks,
      then the banned names.
- [x] Apply twice; owners `postgres`.
- [x] `n8n/workflows/steps-6-9-choose-ingredients.json`: `Build table` selects
      `app.choose_ban(app.choose_table(...), $5)` and appends `app.choose_feedback_prompt($5)` to
      the prompt; nothing else changes. Import, publish.
- [x] Write in `tests/test_choose_table.py`, each seen failing first: `test_ban_removes_and_excludes`
      (b01 with Caramel 50 banned: no row, listed in `excluded` with the why; `app.choose_check`
      of a proposal using it gives the excluded message); `test_no_feedback_same_table` (null →
      identical table and prompt); `test_feedback_prompt_lines` (every line and banned name
      appears; every number in the block is a number in the feedback).
- [x] Measure (A2 prompt budget): b18's table with a three-line feedback through Ollama once,
      as `evals/fit_test.py` counts it (`prompt_eval_count + 4096 ≤ 32768`); write the tokens in
      the §8 entry. If it does not fit, stop and hand back `needs-input`.
- [x] Run `.venv/bin/pytest tests/test_choose_table.py tests/test_choose_check.py tests/test_choose_outputs.py tests/test_contracts.py tests/test_workflows.py`, expect all pass.
- [x] PROJECT.md §8.
Done when: a retry's table refuses the banned picks and its prompt carries the failures.
Commit: `Pass step 11 failures back to steps 6-9`

### Task 8: the pipeline runs up to three tries and saves the recipe
Why: R4, R5, R6, A4, A5.
- [x] Sub-workflow `Steps 10–11 · compute and validate` (id `ST1011compval01`), JSON from
      `n8n/workflows/step-4-targets.json`'s pattern: trigger with the `step10.input` fields →
      `Check contract` (`step10.input`) → Postgres `select app.step10_compute($1, $2, $3, $4, $5,
      $6, $7)` → `Check contract` (`step10.output`) → build `step11.input` → check → Postgres
      `app.step11_validate` → check (`step11.output`) → return `{step10, step11}`. A raise stops
      the sub-workflow with its message (`step 10: …`). Sticky note and `Test data`
      (`tests/step1011_sample.json`: b01's inputs from Task 4's helpers, `run_id` 0, try 1).
- [x] Sub-workflow `Steps 6–11 · one try` (id `ST611onetry0001`), input `try.input` = `{run_id,
      try, choose (the choose.input object, feedback included), brief, step3, targets, frame,
      profile, started_at}`: `Steps 6–9 · choose ingredients` (continueErrorOutput) → four log rows
      as the pipeline's today, with `try` = the input's (moved from the pipeline) → build
      `step10.input` → `Steps 10–11 · compute and validate` (continueErrorOutput) → `Step 10 · log`
      (ok) → `Step 11 · log`: ok when `step11.passed`, else ok false with `error` = `step 11 (try
      <n>): ` + the feedback lines joined by `; ` (R4) → return `try.output` = `{passed, try,
      step10, step11, next_feedback}` (`next_feedback` built from `step11` for the next try, null
      when passed). Error branches: the steps 6–9 failure row as today (lowest `step N:`), or a
      step 10 failure row, each with this `try`, then `Stop and Error` with the message.
      `Test data` note `tests/step611_sample.json`.
- [x] `Recipe pipeline`: `Step 5 · log ok` → `Try 1 · input` (builds `try.input`, feedback null)
      → `Try 1 · steps 6–11` (continueErrorOutput) → `Try 1 passed?` → yes: `Save recipe`
      (Postgres `select app.save_recipe($1, $2, $3, $4, $5)`) → `Finish run` → `Respond ok`
      (`{run_id, ok, recipe_id, tries}`); no: `Try 2 · input` (feedback = try 1's
      `next_feedback`) → `Try 2 · steps 6–11` → `Try 2 passed?` → … → `Try 3 passed?` no →
      `Finish run (failed, 3 tries)` (ok false) → `Respond failed (3 tries)` (`{run_id, ok: false,
      failed_step: 11, tries: 3, error: "try 1: …; try 2: …; try 3: …"}`, R5). Each try's error
      branch → the existing steps 6–9 failure finish and respond (failed_step from the message).
      Remove the old step 6–9 log nodes from the pipeline. Update the per-step sticky note (steps
      0–11 built).
- [x] Contracts `try.input`, `try.output`; `NAMES` gains both. Import the three new or changed
      sub-workflows, publish them, then the pipeline; delete the copies in `shared/`;
      `.venv/bin/python -m evals.workflows`.
- [x] `tests/test_workflows.py`: `SAMPLES` and `CONTRACT_OF` for the two new files.
      `tests/test_pipeline.py`: the `post` fixture deletes the runs' recipes before runs and
      briefs (select `recipe_id`, delete runs, delete recipes, delete briefs) and its timeout is
      2400 s; `test_b01_validates_and_saves` (one run: `ok`, a `recipe_id`, step 10 and 11 rows
      for the last try ok and valid against their contracts, `test_recompute_from_saved_rows`'s
      helper passes on its rows, A5); `test_impossible_target_fails_after_three_tries` (A4:
      "A blonde ale at OG 1.080 and only 2 % ABV, 20 litres.": `app.run.ok` false, step 11 rows
      for tries 1–3 each ok false with `error`, no `app.recipe` row for the brief, `recipe_id`
      null); `test_steps_6_to_9_logged` keeps passing (try 1 rows). Time the file.
- [x] Run `.venv/bin/pytest tests/test_workflows.py tests/test_pipeline.py`, expect all pass.
- [x] `docs/OPERATIONS.md` §5: eleven workflows, the two new ones, the response fields
      (`recipe_id`, `tries`), the three tries. PROJECT.md §4 Orchestration row and §8.
Done when: a webhook run of b01 saves a recipe, and the impossible brief ends failed after three
tries with each reason logged.
Commit: `Run steps 10-11 with retries in the pipeline`

### Task 9: the harness reports recipes; held-out briefs (gate)
Why: R9, R10, A2, A3, A10, A11.
- [x] `evals/grade.py`: `RECIPE_TOLERANCES = {"og": 0.002, "abv": 0.2, "ibu": 2, "srm": 1,
      "batch_l": 0}` next to the maths tolerances, with the user decision as comment;
      `grade_recipe(brief, recipe)` (pure Python): `validated` (a recipe row exists), `invented`
      (items with `ingredient_id` null), `stated` per stated number `{stated, value, met}` with
      `batch_l` exact, `stated_ok`.
- [x] `evals/run.py`: `read_run` sums `llm.tries` over **every** row (all tries, failed rows
      too) into `calls`, counts `first_try_calls` (try-1 rows with an `llm`, each once) and
      `retry_calls`, and reads `tries` (largest step 11 `try`); `read_recipe(conn, run_id)` reads
      `app.run.recipe_id`'s `app.recipe`, its items and deviations (R9: from the saved rows, not
      the step output); the table gains `valid`, `tries`, `calls (first+retry)`, `stated`
      columns; totals gain `validated` (b01–b20 and all), `invented`, `stated_met`, `calls`,
      `first_try_calls` max, `retry_calls`. `--briefs PATH` (default `evals/recipe_briefs.toml`).
      `passed` stays as today and also needs `validated`.
- [x] `evals/show_recipe.py` (`python -m evals.show_recipe <run_id>`): prints a saved recipe as
      plain text (style, batch, numbers vs targets, fermentables kg and %, hops g, minutes and
      usage, yeast, extras g, deviations, each pick's `because` from the step 6–9 rows), for
      A11. Reads only.
- [x] `evals/heldout_briefs.toml`: draft 6 briefs `h01`–`h06` in the `recipe_briefs.toml`
      format, from styles that no b01–b24 `style` or `alt_styles` uses, spread over families
      (e.g. a Czech lager, a Scottish ale, a Belgian blond, a porter, a Kölsch-type, an English
      barleywine; final picks by the drafting), at least two with stated numbers and one with a
      stated batch size; header: "scored only at checkpoints, never while building; the needs
      words are not graded (the class map covers b01–b24)". These styles have no reviewed
      envelope, so their level checks are off (user decision 2026-10-25, "Accept").
- [x] `tests/test_recipe_briefs.py`: `test_heldout_briefs_have_every_field` (same field check),
      `test_heldout_styles_unused` (A10), `test_heldout_style_codes_exist`; the runner's needs
      grade is skipped for a file other than `recipe_briefs.toml`.
- [x] Tests in `tests/test_grade.py` and `tests/test_run.py` (no stack), each seen failing when
      broken: `grade_recipe` met / missed / batch exact / invented; `calls` over three tries;
      `first_try_calls` 2 with a step 6 contract retry on try 1; `test_harness_tolerances_match_sql`
      (stack: equals `app.recipe_tolerances()`).
- [x] Run `.venv/bin/pytest tests/test_grade.py tests/test_run.py tests/test_recipe_briefs.py`, expect all pass.
- [x] **Gate:** hand back `needs-input` with `evals/heldout_briefs.toml` and the b23 and b24
      reference recipes (Task 2) for your approval (R10, A10). Record your answer in the §8 entry;
      apply changes you ask for before Task 10.
Done when: the runner reports recipes from the saved rows and you approved the held-out briefs.
Commit: `Report recipes in the harness and add held-out briefs`

### Task 9b: step 10 moves the mash for a low FG and reaches colour with a second share
Why: G6's first run validated 13 of b01–b20 (A1's bar 16); user decision 2026-10-26, "Mash + colour
reach (Rec.)" (R2, R4, A6; Approach "Colour adjustment" and "Mash move"; the measured replay above).
- [x] `db/032_formulation_check.sql`: `app.rule10_fg_range(style_code text, target_fg numeric,
      stated jsonb) returns numrange` (stable): the target FG ± `midpoint_tolerance.fg` when
      `stated` has `fg` or `abv`, else `ref.beer_style.fg` of the style, null when the style has
      none. `app.check_rule_10` reads its `lo`/`hi` from it; nothing else in the rule changes.
- [x] `db/046_compute.sql` `app.solve_colour`: add `fixed bigint[] default '{}'` (ids that neither
      move nor take up the change; drop the five-argument version first, as Task 2 did for
      `style_fit_recipe`). The mover's upper limit is the least of its `max_pct`, and for role
      `roast` `dark_total_pct` minus the other rule 3 shares (roast, and crystal above
      `crystal_dark_ebc`), for role `adjunct` or `sugar` `adjunct_sugar_pct` minus the other
      adjunct and sugar shares (limits from `app.formulation_limits()`). When the first pass is
      clamped and SRM is still more than 1 away, call itself once with the clamping fermentable
      added to `fixed`: the mover when its own limit (0.01 % or its upper limit) clamped, else the
      absorber. Output gains `second`: null, or the second pass's `{darkest, absorber, from_pct,
      to_pct, because}`; `grist`, `srm`, `reached`, `adjusted` are the final ones and `because`
      joins both passes. Never more than two passes; update the header comment's derivation note.
- [x] `db/046_compute.sql` `app.step10_compute`, new adjustment 4b after the OG
      move: when `targets.mash_c.from` is not `hint`, the yeast has an attenuation figure, and
      `app.fg` at the OG used (shares after the colour move and the OG move, `app.mash_attenuation` at step 4's
      mash) is below `app.rule10_fg_range(style, t_fg, stated)`'s lower bound, bisect the mash in
      [`mash_knee_c`, `mash_max_c`] (40 halvings; FG does not fall as the mash rises) for FG = step
      4's FG target, or take `mash_max_c` when FG there is still below the target. FG above the
      range, a hint's mash or no figure: the mash stays. The OG move and every later number use
      the attenuation at the mash used; `mash_c` in the output and `recipe.mash_c` are the mash
      used; `values_used` gains `{what: "mash", because}` (moved from/to and why, or why it stays).
- [x] `db/031_formulation_rules.sql` rule 7's sentence: the colour adjustment changes the share of
      the darkest fermentable that is not a crystal and, when that share reaches a limit, of the
      next-darkest one; base malts take up the difference; a crystal's share never changes;
      enforced by the colour solver in step 10. (The steps 6–9 prompt does not carry rule
      sentences, measured in `app.choose_prompt`; the `Test data` samples keep the old sentence:
      they are sample inputs, compared only with their notes.)
- [x] `shared/contracts/step10.output.schema.json`: `colour.second` (null or the object above);
      `tests/test_contracts.py`'s step 10 example gains `"second": None`.
- [x] `evals/show_recipe.py` prints `Mash: <c> °C (<because>)` from the last try's step 10 row
      (the saved rows have no mash until M7); `tests/test_run.py::test_show_recipe_prints_the_saved_recipe`
      asserts the line.
- [x] Apply 031, 032, 046 twice; owners `postgres`; `app` function count for the §8 entry.
- [x] Write, each seen failing first. In `tests/test_compute.py`:
      `test_colour_second_dark_grain` (b23's G6 grist Pale Ale Malt 83, Chocolate Dark Malt 10,
      Caramel 150 Malt 5, Black Malt 2, target 35 at OG 1.0625: Black Malt at 0.01 %, `second`
      moves Chocolate Dark Malt, reached, Caramel 150 Malt stays 5; replay gave 7.48 % and SRM
      35.0); `test_colour_keeps_rule_3` (b03's G6 try-3 grist Maris Otter 73.92, Flaked Oats 15,
      Caramel 150 Malt 8.92, Chocolate Dark Malt 2.16, target 31 at OG 1.055: Chocolate stops at
      15 − 8.92 %, `app.check_recipe` rule 3 passes on the result; replay gave SRM 30.5);
      `test_colour_keeps_rule_5` (a sugar mover next to adjuncts near 40 %: the sugar stops at the
      room left); `test_colour_next_base_takes_up` (a grist whose largest base reaches 0.01 %
      first: the next-largest base malt takes up the rest, `second.absorber` names it);
      `test_colour_never_more_than_two_passes` (b18's grist Pale Ale Malt 88, Caramel 50 Malt 10,
      Roasted Barley 2, target 20: reached false, crystal unchanged, `because` names the limits);
      `test_mash_moves_for_low_fg` (b09's step 10 input with its G6 picks, Munich Malt Type 2 70,
      Pilsner Malt 25, Melanoidin Malt 5 and SafLager S-189: mash in (68.3, 69], FG inside
      `app.rule10_fg_range`, rule 10 of `app.check_recipe(output.recipe)` passes; replay gave FG
      1.0114 at 69 °C); `test_mash_stays_in_range` (b01: 66.5, the line says why);
      `test_mash_hint_stays` (the b09 case with `mash_c.from` = `hint`: 66.5);
      `test_mash_cannot_raise_fg_above_range` (FG target moved so FG is above the range: mash
      stays, the line says the curve is flat below 68.3 °C); `test_mash_stops_at_69` (b12's G6
      picks Pale Ale Malt 85, Honey 15, SafAle US-05: mash at most 69, FG still below 1.0080, rule 10
      still fails; replay gave 1.0077). Update `test_values_used_named` (adds `mash`) and
      `test_amounts_hit_the_targets` (`second`'s two ids also count as moved). In
      `tests/test_formulation_check.py`: `test_rule10_fg_range` (stated ABV: target ± 0.002; none
      stated: the style's range; no style range: null). In `tests/test_validate.py`:
      `test_mash_move_lets_rule_10_pass` (the b09 case through step 10 and step 11: passed).
- [x] Run `.venv/bin/pytest tests/test_compute.py tests/test_validate.py tests/test_formulation_check.py tests/test_formulation_rules.py tests/test_step5.py tests/test_contracts.py tests/test_reference_recipes.py tests/test_save_recipe.py tests/test_run.py`, expect all pass; then `.venv/bin/pytest tests/test_pipeline.py::test_b01_validates_and_saves`, expect pass.
- [x] `docs/DATABASE.md` §5: `app.rule10_fg_range`, `app.solve_colour`'s `fixed` and `second`, the mash
      move. PROJECT.md §8.
Done when: the new tests pass, b09's G6 picks validate in step 11 after step 10, and the
reference recipes still pass `app.check_recipe`.
Commit: `Move the mash for a low FG and reach colour twice`

### Task 9c: a failed try tells the retry what to change
Why: G6's misses repeated over 3 tries because the feedback said what failed but not what the
LLM could change once the solvers stop at a limit; user decision 2026-10-26, "Add LLM feedback
too" (R4; Approach "Retry input"; the measured replay above). Steps 6–9 still choose; SQL derives
the instruction and every number in it (CLAUDE.md: no LLM maths).
- [x] `db/047_validate.sql`: `app.attenuation_for_fg(grist jsonb, og numeric, efficiency_pct
      numeric, volume_l numeric, fg numeric) returns numeric` (immutable): the attenuation at
      which `app.fg(app.solve_grist(og, grist, ...), ..., attenuation)` equals `fg`, by bisection
      over [0, 100] (FG falls as attenuation rises; 40 halvings), clamped to that interval.
- [x] `db/047_validate.sql`: `app.step11_fix(failure jsonb, step10 jsonb, targets jsonb, stated
      jsonb) returns text` (stable), null when no case applies; the grist's roles and colours from
      `ref.fermentable`, the yeast's range and alcohol tolerance from `ref.yeast`. Cases, each one
      plain sentence:
      - SRM failure, colour not reached, too dark, the darkest non-crystal is the only base malt
        (b07): "use a lighter base malt than <base> (<EBC> EBC)".
      - SRM failure, the grist has no base malt (b10): "add a base malt: no other fermentable can
        take up the colour change".
      - SRM failure, too dark, the movers at their limits (b19, b03 try 1): "lower the crystal
        share (<crystal names and %>): the colour adjustment never moves a crystal"; with no crystal,
        the roast names instead.
      - SRM failure, too light, the movers at their limits (b18): "<mover> is at its <limit> %
        limit: add a second dark malt (role roast or kilned)"; when rule 3's cap was the limit:
        "rule 3 leaves no room for more roast: lower <crystal above 60 EBC> to make room".
      - Rule 10, FG below the range (b12, b18): "pick a less attenuative yeast: <yeast> gives <att>
        % here (mash <c> °C) and this grist needs about <N> % for FG <target>", N from
        `app.attenuation_for_fg` at the OG used; when the grist has a `sugar` (honey, candi
        sugar): "…, or lower <names>, which ferment out". FG above the range: "pick a more
        attenuative yeast: about <N> %".
      - ABV failure after the OG move (b10, b12, b23): "pick a yeast attenuating about <N> % (<yeast>
        gives <att> %)", N for `app.fg_for_abv(OG used, ABV target)`; no attenuation figure: "pick
        a yeast with an attenuation figure".
      - Rule 11, ABV above the yeast's tolerance (b19): "pick a yeast with an alcohol tolerance of
        at least <ABV> %".
      - Rules 3 and 4 (b19, b22 try 1): "take at least <value − limit> points off <names>"
        (the failure's own value, limit and items).
      Every other failure (rules 1, 2, 8, 13, picks, stated numbers) has none: its line already
      says it, and a pick is banned. Numbers are rounded as the failure texts round them.
- [x] `app.step11_validate`: each feedback line becomes `<text> To fix: <fix>` when
      `app.step11_fix` gives one (the ban suffix stays last). Failure objects, the output
      contract, `try.output` and the n8n workflows are unchanged: `next_feedback.lines` already
      copies `step11.feedback`, so the fixes reach `choose.input.feedback` and the logged error.
- [x] `db/042_choose_table.sql` `app.choose_feedback_prompt`: the header gains one sentence, "Where
      a line says To fix, do that." Nothing else changes.
- [x] Apply 047 and 042 twice; owners `postgres`; `app` function count for the §8 entry.
- [x] Write, each seen failing first. In `tests/test_validate.py`, each from the G6 picks named
      in the measured paragraph, through step 10 (Task 9b's) and step 11:
      `test_fix_lighter_base` (b07: Pale Ale Malt 80, Flaked Corn 20; the SRM line ends "To fix: use
      a lighter base malt than Pale Ale Malt (6.5 EBC)"); `test_fix_add_base` (b10's try-1 grist);
      `test_fix_lower_crystal` (b19's try-3 grist: names Caramel 150 Malt 15 %);
      `test_fix_darker_malt_at_limit` (b18: Roasted Barley at its 2 % limit);
      `test_fix_less_attenuative_yeast` (b12: US-05 at 78 %, N below 78, Honey named);
      `test_fix_abv_yeast` (b23: N about 77, unverified figure from the replay);
      `test_fix_rule_4_points` (b22's try-1 grist: Caraamber 15 %, "at least 5 points");
      `test_fix_rule_11_tolerance`; `test_no_fix_for_a_pick` (the ban test's line has no "To fix");
      `test_fix_numbers_come_from_sql` (every number in each fix is in the failure, step 10's
      output, `ref` or `app.attenuation_for_fg`'s result as rounded). In `tests/test_validate.py`
      also `test_attenuation_for_fg_inverts_fg` (`app.fg` at the result is within 1e-6 of the
      asked FG, for three grists). `tests/test_choose_table.py::test_feedback_prompt_lines`: the
      header sentence; it keeps passing on lines with fixes (their numbers are the feedback's).
- [x] Measure the prompt budget as Task 7 did (`evals/fit_test.py`'s count, Ollama once each,
      `prompt_eval_count + 4096 ≤ 32768`): b18's table with (a) Task 7's three-line, one-ban
      feedback with a fix on each line, and (b) the longest block G6 gave, b19's five try-1 lines
      (SRM, rule 3, rule 4 twice, rule 11; 652 characters before fixes) with their fixes. Task 7 measured 26,514 + 4,096 = 30,610 with three lines and one ban,
      so about 2,150 tokens are left. Write the counts in the §8 entry. If either does not fit,
      stop and hand back `needs-input` (shorter fix sentences or fewer last-pick lines).
- [x] Run `.venv/bin/pytest tests/test_validate.py tests/test_choose_table.py tests/test_compute.py tests/test_contracts.py tests/test_workflows.py`, expect all pass.
- [x] `docs/DATABASE.md` §5: the two functions. PROJECT.md §8 with the token counts.
Done when: each case has a test, the numbers in a fix come from SQL, and both prompts fit.
Commit: `Tell the retry what to change after step 11`

### Task 10: G6 on the real pipeline (gate)
Why: G6; A1–A3, A7, A8, A10, A11.
- [x] First run, before Task 9b: `--label m6` (2026-10-25, runs 4463–4484; b22–b24 ended with HTTP
      500 or a JSON error and were rerun alone as `m6-b22`, `m6-b23`, `m6-b24`, runs 4485–4487).
      b01–b20 validated 13/20, 15/24 overall; first-try calls 2 on every brief; invented 0;
      stated numbers 10/12. Misses and causes: the measured paragraph under Approach. Fix:
      Tasks 9b and 9c. The four results files are kept as the before measurement.
- [x] After Tasks 9b and 9c, re-measure once (user decision 2026-10-26): `.venv/bin/python -m evals.run
      --save --label m6-9b` (b01–b24; background, wait on the results file, not the process). A
      brief that ends with an HTTP or JSON error (not a step failure) is rerun alone with `--brief
      <id> --save --label m6-9b-<id>`, and the rerun counts. A step 10 raise from Task 9b's code is
      a bug: fix it with a test, rerun that brief, record it. No other change and no second
      re-measure: whatever b01–b20 gives goes to the gate. The prompt is not tuned on these briefs
      beyond Tasks 7 and 9c.
- [x] Measure for the §8 entry: validated b01–b20 (bar ≥ 16) and b21–b24, each next to the first
      run's result; tries per brief; calls, first-try calls (≤ 2 each) and retry calls per brief
      and in total; invented 0 (A2); each A3 stated number with its value; A7 grams of b23 and b24
      from the saved rows; A8 deviations of b05, b11, b08, b16 from `app.recipe_deviation`; A5
      recompute on one validated brief; colour adjustments (with second passes), mash moves and
      OG moves made, from the step 10 rows; the `To fix` lines sent per try and whether the next
      try followed them; run time per brief. Compare with the estimate (about 15–17 of b01–b20
      after Tasks 9b and 9c) and name each brief still failing with its cause.
- [x] Then once: `.venv/bin/python -m evals.run --briefs evals/heldout_briefs.toml --save --label m6-heldout`;
      record its validated count and calls (A10). Nothing is changed because of it.
- [x] **Gate (A11, on the re-measure's recipes; user decision 2026-10-26 "After re-measure"):**
      rewrite `docs/work/m6-compute-validate/g6-recipes.md` with 5 validated recipes from the
      re-measure printed by `evals.show_recipe` (proposal: b01, b03, b08, b10, b23 — IPA, stout,
      lager with a stated IBU, inventory dubbel, coffee extras; a proposed brief that did not
      validate is replaced by another family and named as such), and hand back `needs-input`
      asking: would you brew them? Report the b01–b20 count against A1's bar of 16 in the same
      hand-back. Record your verdict.
- [x] `docs/WORKFLOW-ROADMAP.md` G6 `Measured:` line (Decided left for you).
Done when: the re-measure and held-out results files are saved and the gate is answered.
Commit: `Measure G6 on 24 briefs and the held-out set`

### Task 10b: step 10 rounds amounts to what a brewer can weigh and order
Why: user request 2026-10-26 (scope addition; brief R1, R11, A5, A7, A12): "malts, I want 50g
rounding", hops to 1 g, candi sugar to 1 g; answers "Malts + flaked grains (Rec.)", "1 g (Rec.)",
"Now, in M6 (Rec.)", and Q1 "50 g + SRM ± 2" (brief R3, R11). Approach "Rounding to weighing
steps" and "Tolerances"; the Task 10b measurement above.
- [ ] `db/047_validate.sql` `app.recipe_tolerances()`: `"srm": 2` (was 1); comment: user decision
      2026-10-26 "50 g + SRM ± 2", replacing the SRM part of "Brewer bar" (2026-10-25), for targets
      and stated numbers alike, because one 50 g step of a roast malt moves SRM by more than ± 1 at
      20 L; the other tolerances unchanged. `evals/grade.py` `RECIPE_TOLERANCES` `"srm": 2` with the
      same comment; `tests/test_grade.py`'s literal (`"srm": 1` → 2) and
      `tests/test_run.py::test_harness_tolerances_match_sql` keep them equal. A3 and b18's stated
      SRM 20 are now judged at ± 2 (b18's exact amounts give 17.87, so it still misses). Step 10's
      colour solver keeps its own 1 SRM aim (`app.solve_colour`'s `tolerance` constant; only its
      comment changes to say why it is tighter than step 11), so logged step 10 outputs reproduce.
- [ ] `db/046_compute.sql`: `app.weighing_steps() returns jsonb` immutable: `{"malt_kg": 0.05,
      "sugar_kg": 0.001, "hop_g": 1, "extra_g": 1}`, comment: the user's words and decisions of
      2026-10-26 (every malt and flaked grain, roast malts included, 50 g; role `sugar` 1 g; hops and
      extras 1 g), the floor is one step, never 0. A fermentable's step: role `sugar` → `sugar_kg`,
      any other role → `malt_kg`.
- [ ] `db/046_compute.sql`: `app.recipe_rule_failures(check jsonb) returns jsonb` immutable: the
      `fail` results' failures of an `app.check_recipe` output as `[{rule, text, value, limit}]`,
      without rule 9's OG and ABV target lines (the skip `app.step11_validate` has today, moved here
      with its comment). `app.step11_validate` (db/047) reads its rule failures from it; its output
      does not change (the existing `tests/test_validate.py` proves it).
- [ ] `db/046_compute.sql`: `app.step10_round_grist(grist jsonb, recipe jsonb, targets jsonb,
      stated jsonb, efficiency_pct numeric, volume_l numeric, attenuation_pct numeric) returns
      jsonb` (stable). `grist` is step 10's solved grist (`kg`, role, extract, mashed,
      fermentability, ebc); `recipe` the `formulation_check.input` object built from the exact
      amounts. Every fermentable's rounded-down and rounded-up step (both at least one step; one
      candidate when `kg` is on a step) give at most 32 grists, ordered by the sum of |rounded −
      exact| kg (ties: the order the combinations are listed in, first item fastest; deterministic).
      For each: OG = `app.og`, FG = `app.fg` at `attenuation_pct` (null when null), ABV, SRM; the
      candidate recipe = `recipe` with these `pct` (kg / total × 100) and `targets.og` = that OG;
      its failures = OG, ABV, SRM outside `app.recipe_tolerances()` of step 4's targets or of the
      stated `og`, `abv`, `srm`, plus `app.recipe_rule_failures(app.check_recipe(candidate))`, each
      keyed `numbers <key>` or `rule <n>`. The exact grist's keys are computed the same way. The first
      candidate whose keys are all among the exact grist's wins. None: the nearest step for every
      item. Returns `{grist (kg rounded, pct recomputed), reached, added [keys the chosen grist adds,
      empty when reached], off_nearest [names not at their nearest step], because}`; `because`
      names the step sizes and, when not reached, the added keys with their values.
- [ ] `db/046_compute.sql`: `app.step10_round_hops(hops jsonb, target_ibu numeric, stated jsonb,
      boil_sg numeric, volume_l numeric) returns jsonb` (immutable): every hop's `g` to the nearest
      gram, at least 1 g; when `app.ibu` then misses the target or a stated IBU by more than the
      tolerance and the exact grams did not, the bittering addition (the longest boil addition)
      takes the other of its floor and ceiling. `share_pct` recomputed from the rounded grams.
      Returns `{hops, ibu, because}`.
- [ ] `db/046_compute.sql` `app.step10_compute`: after step 5's `app.solve_grist`, build the
      `recipe` object once (as today), call `app.step10_round_grist` at the attenuation used; the
      boil gravity, `app.solve_hops` and then `app.step10_round_hops` use the rounded OG; misc
      `g` = round(dose × batch), at least 1 g (`dose_g_per_l` kept as is). The output's
      `fermentables` (`kg`, `pct`), `hops` (`g`, `share_pct`), `extras` (`g`), `numbers` and `recipe`
      (`fermentables[].pct`, `targets.og`, `hops[].g`, `extras[].g`) are the rounded ones; `og_used`,
      `colour` and the mash line stay as computed before rounding. New output field `rounding`:
      `{steps (app.weighing_steps()), reached, added, off_nearest, because}` (the grist's, with the
      hops' `because` appended).
- [ ] `db/047_validate.sql` `app.step11_validate`: a failure whose key is in `step10.rounding.added`
      gets its text followed by " It comes from rounding to weighing steps: <rounding.because>" (so
      the retry knows); nothing else changes. `app.step11_fix` is unchanged.
- [ ] `shared/contracts/step10.output.schema.json`: required `rounding` `{steps {malt_kg,
      sugar_kg, hop_g, extra_g}, reached boolean, added [string], off_nearest [string], because
      string}`; `tests/test_contracts.py`'s step 10 example gains it.
- [ ] Apply 046 then 047 twice; owners `postgres`; `app` function count for the §8 entry. No workflow
      changes: `Check contract` reads `shared/contracts/<name>.schema.json` at run time
      (`n8n/workflows/check-contract.json`), and the try passes `step10` through as an object;
      `app.save_recipe` already saves step 10's `kg`, `pct`, `g` and `share_pct`.
- [ ] Write, each seen failing first. In `tests/test_compute.py`:
      `test_weighing_steps_as_decided` (the four values); `test_amounts_on_weighing_steps` (b01,
      b10, b23, b24 from their good proposals: every fermentable kg a whole multiple of its step and
      at least one step, hops and extras whole grams ≥ 1, `pct` = kg / total × 100 within 1e-9,
      hop `share_pct` from the rounded grams); `test_floor_is_one_step` (a roast needing 4 g → 50 g,
      vanilla 0.05 g/L × 20 L stays 1 g, a 0.3 g hop → 1 g); `test_rounding_keeps_og`
      (b16's m6-9b grist Pale Ale Malt 70, Flaked Rice 20, Caramel 50 Malt 10 at OG used 1.0505,
      target 1.0525: nearest gives OG 1.0504 out of tolerance, the chosen grist 3.25 / 0.95 /
      0.45 kg keeps it, measured); `test_rounding_keeps_rule_4` (b22's m6-9b grist with Caraamber
      at 10 %: 400 g, not the nearest 450 g; rule 4 passes, measured); `test_rounding_reports_unreached`
      (a 10 L grist whose Black Malt needs 3 g, so 50 g puts SRM more than 2 off: no candidate keeps SRM, `reached` false, nearest
      amounts, `added` = [`numbers srm`], `because` names it); `test_rounding_adds_no_failure_it_did_not_cause`
      (a recipe that already fails rule 8 before rounding: `reached` true, rule 8 not in `added`);
      `test_hops_rounded_inside_ibu` (b08 at 10 L: IBU within 2 of 50; Magnum 13 g). Update
      `test_amounts_hit_the_targets` (OG within 0.002, IBU within 2, pct within one step's share of
      step 7's), `test_misc_grams_are_dose_times_batch` (A7: coffee 60 g, vanilla 1 g, orange peel
      53 g, i.e. dose × batch rounded) and `test_numbers_are_what_check_recipe_computes` (unchanged
      assertion, now on rounded amounts). Task 9b and 9c tests whose figures move with rounding
      (e.g. `test_fix_abv_yeast`'s N) keep their cases; a changed figure is updated and named in
      Deviations. Task 5 and 9c tests whose SRM case was 1–2 off and now passes at ± 2 (for example
      b19's try-3 grist in `test_fix_lower_crystal`, whose exact SRM is within 2 of 19.5) move the
      target so the case still fails, named in Deviations. In `tests/test_validate.py`: `test_rounding_failure_says_rounding` (the unreached
      case through step 11: the SRM line ends with the rounding sentence),
      `test_srm_tolerance_is_two` (b04's m6-9b grist rounded: SRM 36.04 against 35 passes; the
      target moved 2.5 away fails, "limit +- 2"; a stated SRM 2.5 away fails) and
      `test_rule_failures_unchanged` (`app.recipe_rule_failures` gives step 11 the same failures as
      before, on the rule 3 and rule 4 cases). In `tests/test_save_recipe.py`:
      `test_saved_amounts_on_steps` (b23: every saved `amount` on its step; coffee 60 g) and
      `test_recompute_from_saved_rows` keeps passing (A5, now exact to the column scale).
- [ ] `evals/revalidate.py` (`python -m evals.revalidate <results.json> [--save --label L]`):
      for each brief in the file, the last try of its run (largest `try` with a step 11 row): call
      `app.step10_compute` on the logged step 10 `input` fields and `app.step11_validate` on the
      logged step 11 `input` with that new step 10; print per brief `before` (the logged step 11
      `passed`), `after`, the failures' texts and the rounded fermentables and hops; totals
      `{b01_b20: {before, after}, all: {before, after}}`; `--save` writes
      `evals/results/<date>-<label>.json`. SELECTs and function calls only: no LLM, no `app.run`,
      `run_step` or `recipe` writes. `tests/test_run.py::test_revalidate_totals` (no stack: the
      totals of a hand-made list).
- [ ] Before applying the SQL: `.venv/bin/python -m evals.revalidate evals/results/2026-10-26-m6-9b.json`,
      expect `before` = `after` on all 24 (17 of b01–b20): the code that ran is the code
      re-run. A difference stops the task (`blocked`, with the brief and the field).
- [ ] **Bar re-check (no G6 re-run):** after applying, `.venv/bin/python -m evals.revalidate
      evals/results/2026-10-26-m6-9b.json --save --label m6-10b-revalidate`. Expect b01–b20 after
      ≥ 16 (A1's bar, unchanged). Measured estimate *(unverified)*: exactly 16 — b15 (Black Malt's
      50 g floor, SRM + 3.15) and b19 (10 L, rule 4 at 50 g steps) fail with the known b12 and b18;
      b21, b22, b24 pass, b23 fails; 19/24. There is no margin: if it is below 16, stop and hand
      back `needs-input` with the failing briefs and their causes; no G6 re-run, step change or
      further tolerance change without you. A brief that passes `before` and fails `after`
      is a rounding miss; on the real pipeline it would go to a retry *(unverified what the retry
      does)*.
- [ ] Run `.venv/bin/pytest tests/test_compute.py tests/test_validate.py tests/test_save_recipe.py tests/test_contracts.py tests/test_reference_recipes.py tests/test_choose_table.py tests/test_run.py tests/test_grade.py`, expect all pass; then `.venv/bin/pytest tests/test_pipeline.py::test_b01_validates_and_saves`
      (one real run: saved rows on their steps, A5 recompute passes), expect pass.
- [ ] `docs/work/m6-compute-validate/g6-recipes.md`: a section "Rounded (Task 10b)" with the five
      A11 recipes' rounded fermentables, hops, extras and numbers from the revalidate file; the
      review and verdict above it stay as given. The 20 recipes saved by m6-9b stay as saved
      (unrounded): they are the G6 record.
- [ ] `docs/DATABASE.md` §5: the four functions, the rounding in step 10 and `app.recipe_tolerances()`
      SRM 2 (its line names SRM 1 today). PROJECT.md §8 with the before/after counts per brief
      group, the A11 five and the SRM tolerance change.
Done when: the new tests pass, SQL and harness SRM tolerances are both 2, every amount step 10
gives is on its weighing step, the saved picks re-validate at ≥ 16 of b01–b20, and b01's pipeline run saves rounded rows that recompute to
the saved numbers.
Commit: `Round amounts to weighing steps, SRM tolerance 2`

### Task 11: the docs describe stage D as built
Why: scope (PROJECT.md is the entry point).
- [ ] `docs/RECIPE-ROADMAP.md` §3: rows 10 and 11 say what is built (value picks, the boil and
      bittering rule, colour solver with its second pass and rule 3/5 caps, mash move, OG move,
      misc grams, rounding to weighing steps (Task 10b: the steps, the down-or-up choice that adds
      no failure, numbers from the rounded amounts), the failure kinds, ban, three tries);
      the diagram's S11 edges match it (one "fail: back to the steps 6–9 call, max 3 tries"
      edge); §8 P5 status line; the Later TODO "reference recipes for b23 and b24"
      removed; the fruit TODO stays (brief Out). `docs/WORKFLOW-ROADMAP.md`: M6 row, §3 risk
      rows for tolerances and held-out briefs marked decided.
- [ ] PROJECT.md §3 stays (it already describes stage D), §4 rows (Database functions and
      `app` function count, Orchestration, Scripts: `evals/show_recipe.py`, `evals/revalidate.py`, held-out file,
      test count from a full `pytest` run with the stack up) and §8.
Done when: the roadmaps describe what is built and the full suite passes.
Commit: `Describe stage D as built`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| Every step 3 deviation fits a row, none dropped | `test_recipe_tables.py::test_deviation_takes_every_step3_kind` | 1 |
| Extras never enter OG/IBU/SRM | `test_formulation_check.py::test_extras_do_not_enter_the_numbers`, `test_compute.py::test_misc_grams_are_dose_times_batch` | 2, 4 |
| Colour adjustment moves only the darkest non-crystal and the base | `test_compute.py::test_colour_moves_only_darkest_and_base`, `test_colour_never_moves_crystal` | 3 |
| Step 10's numbers are what the check recomputes | `test_compute.py::test_numbers_are_what_check_recipe_computes` | 4 |
| OG moves only inside its tolerance | `test_compute.py::test_og_moves_only_inside_tolerance` | 4 |
| The second colour pass never moves a crystal and never breaks rules 3 or 5 | `test_compute.py::test_colour_second_dark_grain`, `test_colour_keeps_rule_3`, `test_colour_keeps_rule_5`, `test_colour_never_more_than_two_passes` | 9b |
| The mash moves only up, inside 68.3–69 °C, only for an FG below rule 10's range, never a hint's | `test_compute.py::test_mash_moves_for_low_fg`, `test_mash_stays_in_range`, `test_mash_hint_stays`, `test_mash_cannot_raise_fg_above_range`, `test_mash_stops_at_69` | 9b |
| Step 10 and rule 10 read the same FG range and mash | `test_formulation_check.py::test_rule10_fg_range`, `test_validate.py::test_mash_move_lets_rule_10_pass` | 9b |
| Every saved amount is on its weighing step, never 0, and the numbers are computed from the rounded amounts | `test_compute.py::test_amounts_on_weighing_steps`, `test_floor_is_one_step`, `test_numbers_are_what_check_recipe_computes`, `test_save_recipe.py::test_saved_amounts_on_steps`, `test_recompute_from_saved_rows` | 10b |
| Rounding never adds a failure when a grist on the steps avoids it, and says so when none does | `test_compute.py::test_rounding_keeps_og`, `test_rounding_keeps_rule_4`, `test_rounding_reports_unreached`, `test_rounding_adds_no_failure_it_did_not_cause`, `test_validate.py::test_rounding_failure_says_rounding` | 10b |
| Every number in a retry's `To fix` comes from SQL, and the needed attenuation inverts `app.fg` | `test_validate.py::test_fix_numbers_come_from_sql`, `test_attenuation_for_fg_inverts_fg`, `test_choose_table.py::test_feedback_prompt_lines` | 9c |
| Each failure kind is caught; only self-picks are banned | `test_validate.py` (one test per kind, `test_wanted_pick_is_never_banned`, `test_user_ibu_does_not_ban_hops`) | 5 |
| An impossible target never passes | `test_validate.py::test_impossible_target_cannot_pass`, `test_pipeline.py::test_impossible_target_fails_after_three_tries` | 5, 8 |
| A saved recipe recomputes to its saved numbers | `test_save_recipe.py::test_recompute_from_saved_rows`, `test_pipeline.py::test_b01_validates_and_saves` | 6, 8 |
| A failed validation saves nothing | `test_save_recipe.py::test_refuses_a_failed_validation` | 6 |
| A banned pick cannot come back on a retry | `test_choose_table.py::test_ban_removes_and_excludes` | 7 |
| Harness and SQL tolerances agree | `test_run.py::test_harness_tolerances_match_sql` | 9 |

## Approved exceptions

None needed: SQL through `psql` as `postgres`, workflows through the n8n CLI import as
OPERATIONS §5 says; no container is recreated.

## Deviations
- 2026-10-25 · Approach, Tasks 3, 4, 9: the four planning questions answered by the user with the recommended option each: (Q1) step 10 does one pass that may move OG within ± 0.002 towards the ABV target, and any number still off goes back to the steps 6–9 call with the value and target, no step-10-only retry (brief R4 updated); (Q2) boil = the largest of 60, the grist's `min_boil_min` and the longest boil addition, which is set to the boil time; (Q3) the base malt with the largest share takes up the colour change; (Q4) held-out styles without reviewed envelopes are accepted.
- 2026-10-25 · Task 4: `app.step10_abv` added (ABV of a grist at an OG, used by the OG move), beside the two functions the plan names — it keeps the bisection readable.
- 2026-10-25 · Task 4: a yeast with no attenuation figure (b10's Abbey Monk Ale) gives `numbers.fg`, `abv` and `attenuation_pct` null and no OG move, instead of raising — step 11's "a null number fails" then sends it back; the output contract allows those nulls.
- 2026-10-25 · Task 4: `recipe.targets.og` is the OG used (moved), not step 4's target, so `app.check_recipe` recomputes step 10's numbers (the task's own test). Rule 9 then fails when the move is above 0.001 and OG is unstated with guidance on; Task 5 must decide how step 11 treats that (asked in the Task 4 report).
- 2026-10-25 · Task 5: step 11 ignores rule 9's OG line (user answer "Skip rule 9's OG line (Rec.)": step 10 moves OG on purpose and step 11 checks the OG against the target at ± 0.002) — and also rule 9's ABV line ("the ABV target is not app.abv of the OG and FG targets"), because the same moved `recipe.targets.og` breaks it (seen on b23: 5.99 vs 5.72); ABV is checked against its target at ± 0.2 by the numbers check. The ABV skip is the implementer's extension of the user's answer.
- 2026-10-25 · Task 5: a yeast with no attenuation figure gives a `numbers` failure "the ABV cannot be computed: the yeast has no attenuation figure" (as the user's note asked).
- 2026-10-25 · Task 5: tests use b08 and b14 for the passing recipe (not b16: the first good proposal for b16 picks a yeast with no attenuation figure, and b01, b16, b23 and b24 miss SRM because the proposal's only base is a Pilsner malt, so the colour adjustment has no absorber). Hops are never `out_of_style` with the totals off, so the ban tests swap in an out-of-style fermentable instead of a hop; the impossible-target test rates the table's levels typical before building the proposal (the style it lands in, Session Beer, has no envelope).
- 2026-10-25 · Task 6: `test_rows_match_step10` checks coffee against step 10's own dose × 20 L (the good proposal gives 6.0 g/L, not 3.0) and gives b23 a passed step 11 (its first proposal does not pass); `test_refuses_a_run_without_a_brief` added.
- 2026-10-25 · Task 7: `choose.input.feedback` is required in the contract but declared without a type in the sub-workflow trigger (n8n sends a null input as missing; the contract-check node maps it with `?? null`). The prompt block starts with a `TRY <n>` heading like the other blocks, then the plan's sentence. Added `test_ban_removes_from_slots_and_inventory` and a bad example (`feedback.try` 1) in `tests/test_contracts.py`.
- 2026-10-25 · Task 8: `Steps 10–11 · compute and validate` returns `{step10, step11, step11_input}` (the plan says `{step10, step11}`) — `Steps 6–11 · one try` logs row 11 with the input the sub-workflow built, and rebuilding it there would copy the expression. `try.output.next_feedback` is also null after try 3 (no try 4 exists), and its `banned` list is every ban so far (the feedback's own plus the new ones), so try 3's table also refuses try 1's bans.
- 2026-10-25 · Task 8: the pipeline's failure branch for the tries is one `Finish run (failed, steps 6–11)` / `Respond failed (steps 6–11)` pair for the three `Try n` nodes and for `Save recipe`'s error output (the finish query returns the error text, so the respond node needs no node name); `failed_step` reads `step N:` or `stepN.` in the message (lowest, 6 when none, 11 for a `save_recipe` error), so a step 10 or 11 failure reports 10 or 11.
- 2026-10-25 · Task 8: the pipeline run found two bugs in earlier tasks, fixed here with a test each: `db/046_compute.sql` raised "the choice "<NULL>" of German Lager is not a fermentation temperature" when step 6 picks a yeast with no `choice` — step 10 now takes the middle of the yeast's `temp_c` range and says so in `values_used` (`test_ferm_c_without_a_choice_is_the_range_middle`); `db/047_validate.sql` treated an unrated style line (`level` null, a style with no reviewed envelope) as a pick failure with a ban, and the output then broke its contract (`test_unrated_style_bans_nothing`).
- 2026-10-25 · Task 9: `grade_result` gains `recipe`, `stats` and `grade_needs`, and `read_run` reads all `run_step` rows in one query (the plan says it sums over every row; the old two queries are folded into it); `totals["calls"]` keeps its shape and the new counts are separate keys (`first_try_calls_max`, `retry_calls`, `validated`, `invented`, `stated_met`); `tests/test_run.py` and `test_grade.py` gain `test_show_recipe_prints_the_saved_recipe` and `test_read_recipe_reads_the_saved_rows` (not in the plan) — they cover the new reader and printer; two older run tests now pass a recipe because `passed` needs one.
- 2026-10-26 · Approach, Task 9b (new), Tasks 10, 11, Files, Critical behaviour: G6's first run validated 13 of b01–b20 (bar 16), each miss repeating over 3 tries; the user chose "Mash + colour reach (Rec.)", which changes the planning answers Q1 and Q3: step 10's one pass now also raises the mash inside 68.3–69 °C towards the FG target when the predicted FG is below rule 10's range (Q1 had only the OG move), and the colour solver may make a second pass, with the next-darkest non-crystal or the next-largest base malt (Q3 had only the darkest and the largest base). Brief R2, R4, A6 and Scope changed with it (brief Deviations). Task 9b builds it; Task 10's first run is recorded, and it now re-measures b01–b24 once, then the held-out set, then asks A11 on the re-measure's recipes (user decision "After re-measure (Rec.)"); A1's bar stays 16. Plan back to `draft` for approval.
- 2026-10-26 · Task 9b: three details the user's choice did not name, chosen here: (1) the colour mover's limit also keeps rules 3 and 5 — G6's b03 retries reached the colour by raising Chocolate Dark Malt and so failed rule 3 (16.1 %, 15.2 %), and a second pass without the cap repeats that on b03's try 1; (2) a brewer's mash hint is never moved, as wanted picks are never banned; (3) the mash moved is not saved with the recipe (no column until M7's process, as for the boil time) — it is in the step 10 row and printed by `evals.show_recipe`. Measured in the replay (Approach): the mash does not move for an ABV that is still high after the OG move with FG inside its range (b23 would reach 6.15 at 68.6 °C); that would go beyond the user's decision and is left out.
- 2026-10-26 · Task 9b: `app.check_rule_10` reads its FG range from the new `app.rule10_fg_range` (same results), so step 10's mash move and the check cannot drift apart.
- 2026-10-26 · Approach, Task 9c (new), Tasks 10, Files, Critical behaviour: after the Task 9b estimate (14–15 of b01–b20), the user chose "Add LLM feedback too": where step 10's solvers stop at a limit, step 11's feedback line ends with a `To fix:` instruction (a lighter base malt, add a base malt, lower the crystal, add a dark malt, a yeast near a computed attenuation, a yeast with enough alcohol tolerance, points to take off for rules 3 and 4), derived in SQL with every number computed there. This is prompt and retry tuning on the G6 briefs, approved by the user; Task 10's "not tuned beyond Task 7's block" now reads beyond Tasks 7 and 9c. Brief R4 and Scope changed with it (brief Deviations). The prompt budget is measured as in Task 7. A1 stays 16; still one re-measure.
- 2026-10-26 · Task 9c: the instruction is derived in `app.step11_validate` (new `app.step11_fix`), not in `app.choose_feedback_prompt` as the request suggested: step 11 has step 10's output, the grist's roles and the yeast's figures, while the prompt function only sees the feedback text. The fix travels in the existing `feedback` lines, so no contract or workflow changes; `app.choose_feedback_prompt` gains one header sentence. The direction for a low FG is a less attenuative yeast (G6's b12 and b18 are too dry), the opposite of the request's example "pick a more attenuative yeast", which applies to an FG above the range.
- 2026-10-26 · Task 9b: the mash move is decided after the OG move, on the FG at the OG used, and the OG move is made again with the new attenuation (the plan said FG at the target OG, with the OG move after). Found on b09's G6 picks: FG at the target OG 1.0103 was inside rule 10's range while the OG the move then chose gave 1.0099, below it, so the plan's order never moved the mash. The OG-move block became `app.step10_og_move` (same maths) so it can run twice.
- 2026-10-26 · Task 9b: tests use b09's real G6 yeast SafLager S-189 (the plan named SafAle US-05; run 4471's step 10 input shows S-189), whose mash goes to 69 °C (FG 1.0114, as in the replay) rather than a value inside (68.3, 69). `test_colour_keeps_rule_3` runs two targets (31: reached below the room left; 34: Chocolate Dark Malt stops at 15 − 8.92 = 6.08 %), because b03's target 31 is reached before the cap binds. `test_colour_second_dark_grain` expects Chocolate Dark Malt 7.48 ± 0.3 (the test solver runs at 70 % efficiency; the replay at the real one gave 7.48, this gives 7.23).
- 2026-10-26 · Task 9b: the rule 3 and 5 caps never force a share down: the limit is `greatest(room left, the share it starts at)`. Without that, b23's G6 grist (roast and dark crystal already at 17 % of the grist) could not even lower Black Malt, because the room left was below 0. The step 10 contract `values_used.what` enum gains `mash`.
- 2026-10-26 · Task 9c: the feedback header reads "Fix these and change as little else as you can. Where a line says To fix, do that:" (one sentence added inside the header line, not a new line); `tests/test_choose_table.py::test_feedback_prompt_lines` checks the new wording. A fix is joined to its line with a full stop added when the failure text has none. Too light with the darkest non-crystal being a base malt gives no fix (no limit was reached); the rule 3 variant needs a crystal above 60 EBC to name, else none. Measured prompt budget: 26,594 and 26,842 prompt tokens + 4,096, both within 32,768 (PROJECT.md §8).
- 2026-10-26 · Task 10: gate answered. A11: "would brew after the listed changes; the direction is right" (review in `g6-recipes.md`). b12, b18, b19, b23 accepted as known failures (user: "Accept as known (Rec.)"): b12 and b23 repeat the same picks despite `To fix`; b18 and b19 have no dark malt left to reach the colour. b24 stands in for the non-validating b23 in the five recipes. Rounding is left to a separate plan task.
- 2026-10-26 · Approach, Task 10b (new), Tasks 10, 11, Files, Critical behaviour: user-requested scope addition: step 10 rounds every amount to what a brewer can weigh and order (malts and flaked grains 50 g, sugars, syrups, honey and lactose 1 g, hops and extras 1 g, each with a one-step floor, never 0), computes OG, FG, ABV, IBU and SRM from the rounded amounts, and step 11 validates the rounded recipe, a miss going to a retry; saved rows hold the rounded amounts and `pct` follows them (user answers "Malts + flaked grains (Rec.)", "1 g (Rec.)", "Now, in M6 (Rec.)"). Chosen here: each amount is rounded down or up, whichever grist adds no failure the exact amounts did not have (measured: nearest alone keeps 11 of the 17 validated b01–b20). The bar is re-checked by re-validating the saved m6-9b picks through the new steps 10–11 (`evals/revalidate.py`, SQL only), not by a G6 re-run. Measured with 50 g for every malt: at best 14 of b01–b20, below A1's 16 (b04, b05, b15: one 50 g step of a roast malt moves SRM more than ± 1); with roast malts at 10 g: 17. Open as Q1; Task 10b is written for the recommended answer. Brief Scope, R1, R11 (new), A5, A7, A12 (new) changed with it (brief Deviations). Plan back to `draft` for approval.
- 2026-10-26 · Approach, Task 10b, Files: user answer to Q1, "50 g + SRM ± 2" (option c): every malt and flaked grain, roast malts included, rounds to 50 g steps with a 50 g floor (no 10 g roast step); sugars, honey and lactose, hops and extras 1 g; and the SRM tolerance widens from ± 1 to ± 2 for targets and stated numbers. This changes the user's "Brewer bar" decision (2026-10-25) for SRM only; OG, ABV, IBU and batch are unchanged. Task 10b now sets `app.recipe_tolerances()` and `evals/grade.py` `RECIPE_TOLERANCES` SRM to 2 (tests kept equal), drops `roast_kg`, and keeps step 10's colour solver aiming within 1. Re-measured read-only with ± 2: b01–b20 16 of 20, exactly the bar (fail b12, b15, b18, b19), 19/24 *(unverified: retries not replayed)*; the stop-and-ask rule at < 16 stays. Brief R3, R11 and the Assumptions changed with it (brief Deviations).
