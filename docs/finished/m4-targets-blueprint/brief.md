# M4 · Steps 0, 4 and 5: brewer profile, targets and design frame

Status: approved
Slug: m4-targets-blueprint · Branch: m4-targets-blueprint
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) M4, checkpoint **G4** ·
[RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §3 steps 0, 4, 5, §7 · PROJECT.md §3 (D7)
Needs: `m3-deviations`, `s1-maths`, `s2-formulation-rules` and `s5-mash-attenuation` shipped
(all four are in `docs/finished/`, checked 2026-10-17). `s2-corpus` was abandoned 2026-10-14
(D7) and is not needed: step 5 no longer reads a ratio corpus (see Deviations).

## Why
Stage B turns "what the user wants" into the numbers and limits that steps 6–11 design against:
target OG, FG, ABV, IBU and colour, the mash temperature, and the frame the LLM proposes
ingredients and percentages inside (PROJECT.md §3: the LLM proposes, code scales and checks).
A target that ignores a hint, or a frame that forgets a wanted adjunct's limit, can't be fixed
later. Step 0's brewer profile (batch size, efficiency, losses, water) is also first needed here:
`app.brewer_profile` has 0 rows, and 17 of the 22 briefs state no batch size.

## Goal
For every brief, the pipeline loads a brewer profile, sets targets that follow the style, the
hints and the user's numbers and agree with each other through s1's maths, and builds a design
frame for steps 6–9, all by code. G4's checks pass on b01–b20, and b21 and b22 pass too.

## Scope
In:
- Step 0: read the brewer profile from `app.brewer_profile` (contract `step0.output`, written in
  m0); one test profile stored as the `default` row by a `.sql` file: the reference recipes'
  numbers and default water ions (R2).
- A TODO line in RECIPE-ROADMAP §8 Later: a way for the user to set their own water ions in the
  profile (user request 2026-10-17).
- Step 4: targets from the style's range midpoints, moved by hint knobs and replaced by stated
  numbers; batch size from the brief when stated, else from the profile; mash temperature target;
  ABV computed from OG and FG through s1's `app.abv`.
- One hint table in code (`app.hint_knob()`, today used by step 3's conflicts) that both step 3
  and step 4 read, extended so each row says how far its knob moves and names its book source or
  is marked *unsourced* (RECIPE-ROADMAP §7).
- Step 5: the design frame: the formulation rules and limits in force, a slot for each wanted
  ingredient with its role and `max_pct`, the excluded and inventory words, the ingredient
  intents of the hints, and the attenuation the targets need. No ratio numbers.
- Rule 9 of `app.check_recipe` brought in line with step 4 (R11), and the 22 reference recipes
  re-checked.
- Contracts for steps 4 and 5, sub-workflows for steps 0, 4 and 5 logged in `Recipe pipeline`,
  graders for steps 4 and 5 in `evals/`, and a G4 run on the real pipeline.

Out:
- Choosing products, the LLM prompt for steps 6–9 (M5). Amounts and the validate loop (M6).
  Water, mash schedule and boil (M7): step 4 sets only the mash temperature target.
- Setting the user's own water ions (input path, form or command): a TODO on the Later list
  only. Until then the default ions are used.
- A ratio corpus or numeric ratio defaults (grist % per role, hop split, g/L): D7, Later list.
- A technique field in `app.brewer_profile`: s2's pending rule ("only processes the brewer
  profile allows") stays pending; no test brief needs it.
- Stored inventory (`app.inventory`, 0 rows): step 0 returns it as the contract says, an empty
  list today. Inventory-first design (Later).
- Sourcing the unsourced hint rows: they are built marked *unsourced* and sourced before G6.
- Rewriting the M5, M6 and M7 briefs; each is revisited when it is worked on.

## Requirements
R1. Step 0 outputs the profile used, as `step0.output` defines it: batch L, efficiency %,
    boil-off L/h, losses L, grain absorption L/kg, the 6 water ions (null = unknown), units,
    inventory. With no profile id it reads the `default` row.
R2. The `default` profile holds 20 L, 72 % efficiency, 4 L/h boil-off, 2 L losses and 1.0 L/kg
    grain absorption (the reference recipes' fixture numbers), and distilled water as its ions:
    Ca, Mg, Na, SO₄, Cl and HCO₃ all 0 mg/L, cited to Bru'n Water *Water Knowledge* §4.2.1
    ("Distilled water is free of all ions", source `brunwater-water-knowledge`). The `.sql` file
    says these ions are a placeholder until the user can set their own.
R3. Step 4 outputs the batch size: the brief's stated `batch_l` when there is one, else the
    profile's, and says which.
R4. Step 4 sets OG, FG, IBU and SRM at the style's range midpoint, then moves each knob a hint
    names, then replaces it with a stated number. A stated number always wins, inside or outside
    the range. With guidance off the same rules apply; only a stated number leaves the range.
R5. A hint's "up" moves its target to the middle of the top quarter of the range (87.5 % of the
    way from min to max), "down" to the middle of the bottom quarter (12.5 %). The mash target is
    66.5 °C with no mash hint, 64.5 °C for `dry`/`crisp` and 68.5 °C for `full`/`chewy` (the
    middles of the §7 bands). The knobs, as in RECIPE-ROADMAP §7: `bitter` → IBU up; `malty` →
    IBU down (its BU:GU down) and a kilned-share intent; `darker` → SRM up; `stronger` → OG up;
    `session` → OG down; `dry`/`crisp` → mash and a high-attenuation intent; `full`/`chewy` →
    mash and a low-attenuation intent; `hoppy`/`juicy` → a late and dry hop share intent (no
    target moves).
R6. Every hint table row names its book source or is marked *unsourced*; unsourced rows are used
    as they are and are sourced before G6.
R7. When the brief's hints pull one knob in opposite directions (step 3's conflict, e.g. b11
    `dry` vs `full`), that knob stays at its default (mash 66.5 °C, no attenuation intent) and
    the conflict is passed on in step 4's output. Step 3 and step 4 read the same hint table.
R8. ABV is derived: target ABV = `app.abv(target OG, target FG)`. If it falls outside the
    style's ABV range, OG moves inside its own range just far enough to bring ABV to the nearest
    end of the ABV range. A stated ABV keeps FG and solves OG so that `app.abv` gives it (within
    0.1); the solved OG replaces any OG hint.
R9. A style with no vitals (31B for b12) takes its ranges from step 2's base style (the first
    alternative, 18A) and says so.
R10. Step 5 outputs the design frame for steps 6–9: the formulation rules in force with their
    limits (`app.formulation_rules()`, `app.formulation_limits()`); one slot per wanted
    ingredient with its resolved `ref` id or ids, role and `max_pct`; the excluded and inventory
    words with their resolved ids; each hint's ingredient intent (e.g. `full` → oats or dextrin
    malt, `dry` → sugar at most 10 %); and the apparent attenuation the targets need, with the
    yeast attenuation band that reaches it at the mash target through `app.mash_attenuation`
    (s5). It holds no grist, hop-split or dosage numbers.
R11. Rule 9 of `app.check_recipe` accepts what step 4 produces: it no longer checks ABV against
    its midpoint but checks that the ABV target is `app.abv(OG target, FG target)` within 0.1;
    it gets the brief's hints in its input and accepts a target at the position R5 gives for
    them; an unstated, unhinted target off its midpoint still fails. The reference recipes get
    their briefs' hints and step 4's targets (ingredients and process unchanged). All 22
    reference recipes pass every rule after the change, or each failure is reported and the user
    decides.
R12. Every value in steps 4 and 5 says where it came from: range midpoint, hint (which one),
    stated, derived (ABV, or OG moved for ABV), profile, or base style. The recipe sheet (M8) can
    explain it from this alone.
R13. Steps 0, 4 and 5 are deterministic SQL called from n8n's Postgres node, with JSON Schema
    contracts in `shared/contracts/`, and each logs a row to `app.run_step` (steps 0, 4, 5). No
    LLM call.

## Constraints
- PROJECT.md §3: proportions first, quantities last; the style is guidance; the LLM proposes,
  code scales and checks (D7). Step 5 holds no ratio numbers.
- PROJECT.md §4, G0: logic is SQL in `db/*.sql`; Code nodes only reshape JSON; contracts checked
  with `pg_jsonschema`; workflows exported to `n8n/workflows/`.
- CLAUDE.md: brewing maths (gravity, ABV, attenuation) is s1's or s5's tested code, never the LLM;
  DB changes are `.sql` files applied as `postgres`; readable over optimal (§6.8): the hint table
  is one readable function, not a config table.
- §6.3: a slot that can't be filled, a missing style vital or an unknown ion has a legal "absent"
  value, never a guess.
- RECIPE-ROADMAP §7: "each row gets a book source before it is trusted" (here: before G6, R6).
- s5 doc-calc §7: under Troester's curve every mash from 64 to 68.3 °C predicts the same FG, so
  `dry`'s mash knob does not lower the predicted FG; its FG effect comes through the attenuation
  intent (yeast choice in M5). Step 4 must not expect the mash knob alone to move FG.

## Assumptions
- `app.brewer_profile` (16 columns, 0 rows, no technique column, measured 2026-10-17) holds the
  test profile as a normal row *(checked: columns match `step0.output`)*.
- The `corpus` tables exist but are empty (`corpus.style_profile` 0 rows, measured 2026-10-17);
  nothing in this work reads them.
- Midpoint ABV and the ABV from midpoint OG and FG disagree for most brief styles (measured
  2026-10-17 with `app.abv`: 17C 9.14 vs 8.25, 16A 4.35 vs 5.00, 15A 3.72 vs 4.40). Under R8,
  15A's derived 3.72 is below its 3.8 minimum, so its OG moves from 1.041 to about 1.042
  *(computed, to be confirmed by the tests)*.
- b19 (`stronger`) puts 17C's OG at 1.1225, which gives ABV 12.1 against a 10.0 maximum; R8
  then brings OG back to about 1.1065 *(computed 2026-10-17 with FG at its midpoint 1.029)*.
- Distilled-water ions (all 0) are neutral for M7's salt maths, which builds the profile from
  additions *(unverified until M7)*.

## Acceptance criteria
A1. For b01–b22, every target is inside the style range (the base style's for b12), except a
    stated number or an OG solved from a stated ABV (marked derived, naming the stated ABV),
    with guidance on or off (R4, R8, R9, G4).
A2. b01's IBU target is 66.25 (87.5 % of 21A's 40–70); b09's IBU is 18.75 (12.5 % of 6A's
    18–24); b06's mash target is 64.5 °C; b03's is 68.5 °C; b19's OG is above 17C's midpoint
    1.100 and its ABV at most 10.0 (R5, R8).
A3. b11's mash target is 66.5 °C with no attenuation intent, and the "dry vs full, chewy"
    conflict is in step 4's output (R7).
A4. b08 targets IBU 50 and 10 L; b13 15 L; b15 23 L; b01 20 L and b19 10 L, both marked
    "stated"; b17 ABV 7; b18 SRM 20 with guidance off; every other brief 20 L marked "profile"
    (R3, R4).
A5. For every brief, `app.abv(target OG, target FG)` is within 0.1 of the target ABV and inside
    the ABV range unless the ABV was stated; b01's target ABV is 6.5, b14's 3, b17's 7 and b21's
    4, each with FG at its midpoint and OG solved (R8).
A6. b12's targets come from 18A and the output says so (R9).
A7. The `default` profile row holds 20 L, 72 %, 4 L/h, 2 L, 1.0 L/kg and six 0 mg/L ions, and
    its `.sql` file cites Bru'n Water *Water Knowledge* §4.2.1; RECIPE-ROADMAP §8 Later has the
    TODO for user-set water ions (R1, R2).
A8. Each wanted ingredient of b02, b06, b07, b12, b16, b19 and b20 has a step 5 slot with its
    `ref` id, role and `max_pct`; b08's and b16's excluded words and b10's and b15's inventory
    words are in the frame; b02, b03, b06 and b09 carry their hints' ingredient intents; the
    frame's rules equal `app.formulation_rules()`; the frame holds no grist % or hop-split
    number (R10).
A9. For every brief, step 5's needed attenuation equals (OG − FG) / (OG − 1) of step 4's targets,
    and its yeast band reaches it at the mash target through `app.mash_attenuation` (R10).
A10. Every value in step 4's and step 5's outputs has a non-empty `from` (R12).
A11. `app.check_recipe` passes rule 9 for b01's hinted IBU 66.25 and for a derived ABV off its
    midpoint, and fails it for an unstated, unhinted IBU off its midpoint and for a hinted IBU
    that is not at the R5 position; all 22 reference recipes pass every rule, or each failure is
    listed with the user's decision (R11).
A12. Every hint table row has a source or is marked unsourced, and the unsourced rows are listed
    in this folder (R6).
A13. `python -m evals.run --save --label m4` on the real pipeline: steps 0, 4 and 5 are logged
    for every brief, their outputs meet their contracts, steps 4 and 5 pass on b01–b20 (20/20)
    and on b21 and b22, and steps 1–3 score no worse than G3 (R13, G4).

## Open questions
None. All five were answered by the user on 2026-10-17 (see Deviations).

## Deviations
- 2026-10-16 · Needs: `s5-mash-attenuation` added, so step 4's mash target and step 5's
  attenuation band follow a cited model ([SOURCES.md](../../SOURCES.md)).
- 2026-10-17 · Step 5 rewritten for D7: `s2-corpus` was abandoned and `corpus.style_profile` is
  empty, so the blueprint from corpus ratios (old R6–R8, A5, A6, the s2 assumption) becomes the
  design frame built from s2's rules and `ref` data; Needs now lists `s2-formulation-rules`
  instead of `s2-corpus`. Title changed; the slug stays.
- 2026-10-17 · Checked against what shipped: rule 9 (`db/032`) and the ABV midpoints conflict
  with hint knobs and with s1's ABV; `dry`'s mash knob does not move FG under s5's model
  (Constraints); 31B has no vitals (R9); the batch override moved from step 0 to step 4, because
  step 0 runs before step 1 reads the brief (R3); 22 briefs, not 20.
- 2026-10-17 · Q1: OG and FG from midpoints and hints, ABV derived by `app.abv`, OG moved just
  far enough when that ABV is out of range, a stated ABV keeps FG and solves OG, rule 9 stops
  checking ABV against its midpoint (option a). R8, R11, A5 — the user's decision.
- 2026-10-17 · Q2: up/down to the middle of the top/bottom quarter, mash to the middle of its
  band (64.5 / 68.5 °C), rule 9 gets the hints and accepts the hinted position (option a). R5,
  R11, A2, A11 — the user's decision.
- 2026-10-17 · Q3: step 5 is the design frame with no ratio numbers (option a). R10, A8 — the
  user's decision.
- 2026-10-17 · Q4: the reference-recipe numbers plus default ions; the user: "set a default for
  now, and add a TODO to be able to set this as well". Default chosen: distilled water (all six
  ions 0 mg/L, Bru'n Water *Water Knowledge* §4.2.1); a RECIPE-ROADMAP §8 Later TODO for user-set
  ions is in scope, the input path itself is out. R2, A7 — the user's decision.
- 2026-10-17 · Q5: build with unsourced hint rows, marked, and source them before G6 (option a).
  R6, A12 — the user's decision.
- 2026-10-17 · Planning: A4 left out b19's stated 10 L and counted b01's stated 20 L as
  "profile"; A4 now follows R3 (option a) — the user's decision.
- 2026-10-17 · Planning: an OG solved from a stated ABV may leave the OG range (b14 1.0279 below
  23A's 1.028, b17 1.0672 above 8B's 1.052); A1 counts it as following the stated number, marked
  derived (option a) — the user's decision.
- 2026-10-17 · Planning: R11's re-check gives the reference recipes their briefs' hints and step
  4's targets, and rule 9 checks the ABV target against `app.abv` of OG and FG within 0.1
  (option a) — the user's decision.
