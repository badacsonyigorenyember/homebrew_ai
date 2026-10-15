# S2 · Formulation rules and ingredient data

Status: approved
Slug: s2-formulation-rules · Branch: s2-formulation-rules
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) side track S2 (replaces `s2-corpus`) ·
[RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §8 · [DATABASE.md](../../DATABASE.md)
Needs: `s1-maths` shipped (done 2026-10-14)
Replaces: the draft brief `s2-corpus` (deleted 2026-10-14, last in commit `57638a1`), which is not
built (decision D7)

## Why
Recipe formulation now works like this (agreed with the user, 2026-10-14). Style numbers and the
user's deviations give the targets. The LLM picks ingredients from a detailed ingredient table and
proposes percentages and the hop-schedule intent. s1's code scales to OG and volume, sizes the
bittering addition for IBU and sets the colour, and a small set of exact rules is checked in code.
Violations go back to the LLM. None of this can run yet: `ref.fermentable.role` is empty (0/81),
18 of 81 fermentables have no `max_pct`, the table does not say what each ingredient does, and
there is no rule-check code. The corpus route (D7, `s2-corpus`) is dropped for now.

## Goal
Every fermentable has a role, a `max_pct`, an enzyme activity, a minimum boil time, its
substitutes and a sourced description of what it adds. One deterministic check takes a proposed
recipe and returns every rule it breaks, in exact words, and the 22 test briefs each have a
plausible recipe that passes. D7 is decided and the project records describe the new approach.

## Scope
In:
- Fermentable data: `role` for all 81, the 18 missing `max_pct` values, new columns
  `enzyme_activity` and `min_boil_min`, substitutes, catalogue descriptions with typical style
  codes for the 74 malts, and descriptions for the 7 adjuncts and sugars. Every value names its
  source in `field_source`.
- The PrimeTime Malt Substitution Chart 2025 registered as a `ref.source`.
- The formulation rules (user decision B) written once, as exact sentences, with the thresholds
  the code checks.
- A rule-check function over a proposed recipe, called the way G0 says (SQL in `db/*.sql`,
  callable from n8n's Postgres node), using s1's functions for every number.
- One reference recipe per test brief (22) as a test fixture, drafted by Claude and reviewed by
  the user, plus failing cases per rule.
- Project records still to do (user decision K): RECIPE-ROADMAP §9's D7 row, the
  WORKFLOW-ROADMAP S2 row and its s2 → s3 arrow, RECIPE-ROADMAP §8 "Later" turned into a list
  (with a TODO for a cited mash-temperature model), and a one-line note under the Needs line of
  the m4, m5 and s3 draft briefs. PROJECT.md §3, §5, §6.7, §7 and §8, the `s2-corpus` deletion
  and the STYLE-PROFILES.md note were done with this brief (see Deviations).

Out:
- The LLM step that picks ingredients, its prompt and contract, and wiring the check into the
  n8n pipeline (m5/m6).
- The colour solver that moves the darkest malt (rule 7): s1 has no colour solver (`pg_proc`
  holds `solve_grist` and `solve_hops` only). m6 builds it with step 10; this work only writes
  rule 7 down.
- A cited model of mash temperature's effect on FG: rule 10 uses an uncited linear mapping now
  (R10), and the cited model goes on the Later list (R20).
- The "don't overdo techniques" rule: `app.brewer_profile` has no technique field (16 columns,
  0 rows, measured 2026-10-14). It is written down as a pending rule for m4 (step 0).
- An enzyme rule using `enzyme_activity` (goes to the Later list, user decision F).
- The ratio corpus (old s2): Later list, revisited only if test-brief results show generic or off
  recipes (user decision J).
- Misc ingredients (`ref.misc` is empty; no test brief needs one, user decision I).
- Descriptions for hops and yeasts.
- Rewriting the m4, m5, m6 and s3 draft briefs beyond the one-line note (R21); each is revisited
  when it is worked on.
- Anything from Brewer's Friend (user decision L).

## Requirements

### Ingredient data
R1. Every one of the 81 fermentables has a `role` (base · kilned · crystal · roast · adjunct ·
    sugar). The 63 Weyermann and Viking malts in the chart take it from their chart group:
    1A → base, 1B → kilned, 1C → crystal, 1D → roast (so Munich, Melanoidin and Abbey are kilned
    and count toward rule 1's 3). In 1E, 2A, 2B and 2C and outside the chart the role follows the
    malt's colour and type:
    - crystal: Carawheat, Viking Caramel 200, the Simpsons crystal malts;
    - roast: Chocolate Wheat;
    - base: Wheat Malt Pale, Viking Wheat, Rye Malt Pale, Viking Rye, Spelt, both smoked wheats,
      Lightly Peated, Enzyme Malt, Eraclea, Bohemian Pilsner, Golden Promise, Maris Otter;
    - kilned: Wheat Malt Dark, Viking cherry and pear smoked (like the chart's beech smoked in
      1B), Acidulated (special purpose; it uses one of rule 1's 3 slots, and its 5 % `max_pct`
      limits it).
    The 7 producer-less rows: Flaked Oats, Barley, Corn, Rice → adjunct; Honey, Brown Candi Sugar,
    Lactose → sugar. Sprau Malt is placed by the user.
R2. Every fermentable has a `max_pct`. The 18 missing values are exactly user decision E
    (Viking Munich Light 100, Munich Dark 100, Lightly Peated 100, Smoked Wheat 100,
    Caramel 30 and 50 → 20, Caramel 100, 150, 200 → 15, Caramel 300, 400, 600 → 10; Flaked Oats 30,
    Flaked Barley 20, Flaked Corn 20, Honey 20, Brown Candi Sugar 20, Lactose 10), each with a
    `field_source` naming where it came from: source `user-supplied`, with the basis the user
    gives per value (Viking catalogue, *How to Brew* estimate, forum consensus, recipe range), or
    "user decision E, 2026-10-14" for a value the user cannot place. The user confirms the bases
    before the values are loaded. The 63 existing values are unchanged.
R3. A new column `enzyme_activity` (none · low · normal · high) is filled from the Weyermann
    catalogue's "Enzyme activity" line and the Viking text (Munich "clearly reduced" → low,
    caramel malts "zero" → none). A row whose sources do not state it stays empty and is listed
    in the work's report; nothing is guessed. No rule reads it yet.
R4. A new column `min_boil_min` holds each fermentable's minimum boil (60 by default, 90 for
    DMS-prone malts). Code proposes the values from role and EBC; every proposed value above 60
    is flagged and confirmed by the user before it is loaded.
R5. Each fermentable lists its substitutes among the 81: the Weyermann ↔ Viking pairs from the
    chart rows, plus user decision D: Eraclea and Bohemian Pilsner → Viking Pilsner; Crystal
    Extra Dark → Caraaroma; DRC → Special W; Golden Promise and Maris Otter → both Weyermann and
    Viking Pale Ale; no
    substitute for Viking Caramel 200, the smoked malts, Sprau and Crystal T50. Each pair names
    its source (chart row or user decision). A pair counts both ways (A ↔ B gives B as A's
    substitute and A as B's) and does not chain (A ↔ B and B ↔ C does not make A ↔ C).
R6. Each of the 74 malts has a short description of what it adds and causes (character,
    sensory, recommended use) from its maltster's catalogue (Weyermann: description, sensory,
    typical styles, recommended addition, enzyme activity; Viking: "Malt character",
    "Applications"; Simpsons: its one line plus the hopline pages' recommended styles), with the
    page or URL as source. Each of the 7 adjuncts and sugars has a short English description
    summarised from the hopline adjuncts page text (Hungarian), and from *How to Brew* for
    honey, with the page or URL as source.
R7. Each malt's typical styles are stored as style codes that exist in `ref.beer_style`
    (BJCP 2021 or BA). A maltster style name with no matching style is mapped to the closest style
    we use or dropped (user decision H). Claude proposes the mapping, code checks every code
    exists, and the user reviews the mapping before it is loaded.
R8. The data load is re-runnable: a second run gives the same rows. Schema changes are `.sql`
    files applied as `postgres`.

### Rules
R9. The rules are written once, in one place, as exact sentences, with the thresholds the code
    checks taken from the same place, so the text and the check cannot disagree. A rule names
    only ingredient roles, style numbers (OG, FG, IBU, SRM, ABV) and ingredient-table fields. It
    never names an ingredient or a style, and never uses a vague word ("some", "usually",
    "typically", "about"). The rule list is linked from PROJECT.md.
R10. The rules are user decision B, with these exact starting thresholds:
    1. At most 5 fermentables; at most 3 of role kilned, crystal or roast (adjunct and sugar do
       not count toward the 3).
    2. At most 3 hop varieties.
    3. Crystal above 60 EBC plus roast is at most 15 % of grist mass.
    4. All crystal at most 25 %; crystal above 60 EBC at most 10 %; crystal above 160 EBC at most
       5 %. Crystal at or below 60 EBC is limited only by rule 6.
    5. Adjunct plus sugar at most 40 %.
    6. Each fermentable at most its `max_pct`.
    7. The colour adjustment moves only the darkest malt, never a crystal malt (written down here;
       enforced by m6's colour solver, not by this check).
    8. Exactly one bittering addition, at the start of the boil; every other hop addition is at
       15 min or less, whirlpool or dry hop.
    9. A target the user did not state (directly, or through ABV for OG and FG) is the style's
       midpoint; a target is outside the style range only when the user stated it or guidance is
       off.
    10. The FG predicted from the yeast's attenuation, each fermentable's `fermentability` and a
        mash temperature between 64 and 69 °C is inside the target FG range: the style's FG
        range, or the target FG ± 0.002 when the user stated the FG or the ABV. Mash temperature
        maps linearly onto the yeast's `attenuation_pct` range: 64 °C → the top of the range,
        69 °C → the bottom. The rule text labels this mapping as an uncited assumption; the cited
        model is on the Later list (R20).
    11. Planned ABV is at most the yeast's alcohol tolerance; the fermentation temperature is
        inside the yeast's temperature range.
    12. Every recipe ingredient has a non-empty `purpose`.
    13. The boil is at least the largest `min_boil_min` in the recipe, and at least 60 min.
    Pending, not checked: only processes the brewer profile allows (needs m4's brewer profile).
R11. Percentages are shares of total fermentable mass, sugars included. Colour thresholds and
    "darkest" use the midpoint of each `ebc` range; an open range (such as "up to 10") uses its
    one bound.

### Rule check
R12. One check takes a proposed recipe (fermentables with `ref` id, % and purpose; hops with
    `ref` id, usage, minutes and purpose; yeast with `ref` id, purpose and fermentation
    temperature; mash temperature; boil time; targets; the style; the user's stated numbers and
    the guidance flag) and returns a list of results, one per rule: pass, fail or unknown.
R13. A failure says which rule, which recipe items, the measured value and the limit, in plain
    words the LLM can act on. It never suggests a replacement ingredient.
R14. Where the data a rule needs is missing (26 yeasts without attenuation, 5 without alcohol
    tolerance, a style without vitals), that rule returns `unknown` with the missing field named,
    not a pass and not a fail.
R15. Every number the check needs (OG, FG, ABV, IBU, SRM) comes from s1's `app.*` functions; FG
    uses `fermentability` per item, so lactose counts as unfermentable. No brewing maths is
    re-implemented. The input and output shapes have JSON Schemas in `shared/contracts/`.
R16. Each test brief (22, `evals/recipe_briefs.toml`) has one reference recipe as a test
    fixture, built from `ref` ingredients and inside the brief's style (or its stated numbers).
    Claude drafts all 22 from the catalogue data and the style ranges; the user reviews them
    before they count as fixtures. Each one passes every rule, or the rule it fails is reported
    and the user decides whether the threshold changes. The fixtures are test data only and never
    go into a prompt.

### Project records
R17. RECIPE-ROADMAP §9's D7 row records D7 as decided, in the words PROJECT.md §3 uses: no ratio
    corpus; the LLM proposes, code scales and checks; revisit if test briefs show a need.
    (PROJECT.md §7 and §3 were already updated, see Deviations.)
R18. *(Done with the brief, see Deviations.)* PROJECT.md §3 and §6.7 describe the new split.
R19. The WORKFLOW-ROADMAP S2 row points to this work instead of `s2-corpus`. (`s2-corpus` is
    already recorded as abandoned and its folder deleted, see Deviations.)
R20. RECIPE-ROADMAP §8's "Later" row becomes a short list that keeps its current items and adds:
    - an enzyme rule using `enzyme_activity`;
    - the ratio corpus (old s2), revisited only if test-brief results show generic or off recipes;
    - TODO: replace rule 10's uncited linear mash-temperature mapping with a cited model of mash
      temperature's effect on attenuation (for example from *How to Brew*'s mash chapter, via a
      doc → calc pass).
R21. The m4, m5 and s3 draft briefs each get one line under their Needs line:
    "s2-corpus abandoned 2026-10-14; revisit in this brief". The s2 → s3 arrow in
    WORKFLOW-ROADMAP's diagram, and the text that calls s1 → s2 → s3 a chain, are marked the same
    way. Nothing else in those briefs changes.

## Constraints
- DB changes are `.sql` files applied with `psql` as `postgres`; the Supabase MCP is read-only
  (CLAUDE.md). Loaders follow the `loaders/` pattern: tests, same rows on a second run.
- Deterministic logic is SQL functions in `db/*.sql`, called from n8n's Postgres node (PROJECT.md
  §4, G0). Brewing maths is s1's tested code; never computed by the LLM (CLAUDE.md).
- Readable over optimal (§6.8): each rule is explicit code a reader can follow, no generic rule
  engine driven by a config table.
- Leave room to say "absent" (§6.3): missing data gives `unknown`, never a guess.
- Every filled field names its source in `field_source` (PROJECT.md §4).
- No git worktree; plain branch `s2-formulation-rules` (CLAUDE.md).

## Assumptions
- The 63 Weyermann/Viking malts the user counted as "in the chart" include Viking Lightly Peated
  (chart group 2C, Malts for Distilling) *(checked: 37 + 32 − 6 = 63)*.
- Grist % is of total fermentable mass including sugars, as recipe sheets usually print it
  *(unverified: the user did not say)*.
- Sugar is added to the boil, so it is not mashed for s1's `mashed` flag; flakes are mashed
  *(unverified)*.
- Rule 10's linear mapping of 64–69 °C onto the yeast's attenuation range is not from a source;
  it is labelled as such in the rule text (R10) *(uncited by decision, 2026-10-15)*.
- `ref.yeast.attenuation_pct` is a range for 93 of 119 yeasts; 16 of those span 1 point or less,
  so for them mash temperature barely moves the predicted FG *(checked 2026-10-15)*.
- `ref.fermentable.ebc` is set for 74 of 81 rows *(checked 2026-10-15)*. The 7 without it are
  Enzyme Malt, the 4 flakes, Honey and Lactose; none is crystal or roast, so rules 3 and 4 never
  need their colour. The 5 open ranges all have only an upper bound ("up to 8" or "up to 10":
  CaraBody, Lightly Peated, both Viking smoked malts, Smoked Wheat).
- The catalogue PDFs state enzyme activity for Weyermann malts per malt, and the Viking text
  covers Munich and caramel malts only *(unverified until extraction)*.

## Acceptance criteria
A1. `ref.fermentable` has 81 rows with a non-null `role`; each chart malt's role matches its chart
    group per R1; the malts in 1E, 2A, 2B, 2C and outside the chart match R1's list (Acidulated
    → kilned, Chocolate Wheat → roast, Carawheat → crystal); Sprau's role is the user's (R1).
A2. 81/81 rows have `max_pct`; the 18 values equal user decision E, each with its `field_source`
    entry; the other 63 are unchanged from before the work (R2).
A3. `enzyme_activity` and `min_boil_min` exist with check constraints; every row above 60 min was
    confirmed by the user; rows with no stated enzyme activity are listed in the report (R3, R4).
A4. The substitute pairs match the chart rows and user decision D; a query shows Eraclea →
    Viking Pilsner, DRC → Special W and no substitute for Crystal T50; a query from either side of
    a pair finds the other; a query on a malt finds no substitute that is only reachable through
    another substitute (R5).
A5. All 74 malts and all 7 adjuncts and sugars have a description with a source; every stored
    style code exists in `ref.beer_style`; the user approved the name → code mapping (R6, R7).
A6. Running the load twice gives the same rows (a checksum before and after) (R8).
A7. A test reads the rule text and finds no `ref.ingredient` name, no `ref.beer_style` name and
    none of the vague words in R9; the thresholds in the text equal the ones the check uses (R9).
A8. For each of rules 1–6 and 8–13, pytest has at least one recipe that passes and one that fails
    exactly that rule (R10, R12).
A9. A failure result names the rule, the items, the value and the limit, and names no ingredient
    that is not in the recipe (R13).
A10. A recipe whose yeast has no attenuation gives `unknown` for rule 10, naming the field (R14).
A11. The check's OG, FG, ABV, IBU and SRM equal direct calls to s1's functions on the same inputs;
    a lactose recipe has a higher predicted FG than the same recipe without it; the input and
    output pass their JSON Schemas (R15).
A12. All 22 reference recipes were drafted by Claude, reviewed by the user, and pass every rule,
    or each failure is listed with the user's decision on it (R16).
A13. RECIPE-ROADMAP §9's D7 row says decided; the WORKFLOW-ROADMAP S2 row links this work;
    RECIPE-ROADMAP §8 Later is a list including the enzyme rule, the corpus revisit and the TODO
    for a cited mash-temperature model; PROJECT.md §7 still holds no D7 and `docs/work/s2-corpus/`
    does not exist (R17–R20).
A14. For one yeast with an attenuation range, rule 10's predicted FG at 64 °C uses the top of the
    range, at 69 °C the bottom, and at 66.5 °C the midpoint; the rule 10 text says the mapping is
    an uncited assumption (R10).
A15. With the stored ranges, Caraamber (60–80 EBC) counts as crystal above 60 EBC and Carared
    (40–60) does not; a malt with an open range is placed by its bound (R11).
A16. The m4, m5 and s3 briefs each have the "s2-corpus abandoned 2026-10-14; revisit in this
    brief" line directly under Needs; WORKFLOW-ROADMAP's s2 → s3 arrow and chain text carry the
    same note; `git diff` shows no other change to those three briefs (R21).

## Open questions
None remain. Questions 5 and 8 were answered on 2026-10-14, and 1, 2, 3, 4, 6, 7, 9 and 10 on
2026-10-15 (see Deviations).

## Deviations
- 2026-10-14 · Q5: the user chose to change both PROJECT.md §3 and §6 now ("This is stronger
  right now than the PROJECT.md. Update both places"). Done with the brief, not at
  implementation: §3 intro, stages B–D and the ratios line rewritten; §6.7 reworded so the LLM
  picks ingredients and proposes percentages and hop-schedule intent while code computes every
  number and checks the rules; D7 moved out of §7 as decided; §5 Brewer's Friend row set aside.
  R17, R18 and A13 narrowed to what is left — the user's decision.
- 2026-10-14 · Q8: the user chose to delete `docs/work/s2-corpus/` (option a). Done with the
  brief (`git rm -r`, last in commit `57638a1`), recorded in PROJECT.md §8; `docs/STYLE-PROFILES.md`
  got a "set aside 2026-10-14 (D7)" note. R19 narrowed to the WORKFLOW-ROADMAP row — the user's
  decision.
- 2026-10-15 · Q1: colour thresholds and "darkest" use the `ebc` midpoint, open ranges their
  bound (option a). R11 fixed; A15 added — the user's decision.
- 2026-10-15 · Q2: roles in 1E, 2A, 2B, 2C and outside the chart as proposed, Acidulated →
  kilned (option a). R1 lists the placements; A1 checks them — the user's decision.
- 2026-10-15 · Q3: Claude drafts the 22 reference recipes from the catalogue and style ranges;
  the user reviews them (option a). R16, A12 and scope updated — the user's decision.
- 2026-10-15 · Q4: rule 10 maps 64 °C → top and 69 °C → bottom of the yeast's attenuation range,
  linearly, labelled as an uncited assumption (option a). The user added: "And add a TODO to
  @RECIPE-ROADMAP.md to use the cited model later". R10 rule 10 and R20 updated, the TODO is in
  scope, A13 extended and A14 added; the cited model is out of scope — the user's decision.
- 2026-10-15 · Q6: the colour solver is left to m6; this work only writes rule 7 down (option a).
  Scope Out and R10 rule 7 updated — the user's decision.
- 2026-10-15 · Q7: descriptions for the 7 adjuncts and sugars are in (hopline adjuncts page,
  Hungarian, summarised in English; *How to Brew* for honey); hops and yeasts out (option a).
  Scope, R6 and A5 extended — the user's decision.
- 2026-10-15 · Q9: a one-line "s2-corpus abandoned 2026-10-14; revisit in this brief" note goes
  under the Needs line of the m4, m5 and s3 briefs, and the WORKFLOW-ROADMAP s2 → s3 arrow is
  marked the same way (option a). Moved from Out to In; R21 and A16 added — the user's decision.
- 2026-10-15 · Q10: substitutes count both ways, no chaining (option a). Moved from Assumptions
  into R5; A4 extended — the user's decision.
- 2026-10-15 · Plan questions 1–3 (recommended options): R2 — the 18 `max_pct` values keep
  source `user-supplied` with a per-value basis the user confirms before loading ("user decision
  E, 2026-10-14" when it cannot be placed); R5 — Golden Promise and Maris Otter pair with both
  Weyermann and Viking Pale Ale; R10 rule 10 — the target FG range is the style's FG range, or the
  target FG ± 0.002 when the user stated the FG or the ABV — the user's decision.
