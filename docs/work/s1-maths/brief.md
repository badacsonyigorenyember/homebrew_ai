# S1 · Brewing maths library (P2)

Status: approved
Slug: s1-maths · Branch: s1-maths
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) side track P2, checkpoint **G-M** ·
[RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §6, §8 P2
Needs: `m0-harness` shipped ✅ 2026-10-12. G0 decided that deterministic logic is SQL functions
in `db/*.sql`, called from n8n's Postgres node and tested from pytest through `psycopg`
([PROJECT.md §4](../../../PROJECT.md)). Planning also needs the OBC *Recipe Formulation* PDF
in `shared/rag-files/pending/`; you download it before planning starts.

## Why
Gravity, ABV, bitterness and colour are needed by steps 4, 10 and 11, and by the corpus quality
gate G4 (s2), which recomputes OG and IBU to catch bad recipes. CLAUDE.md forbids asking the LLM
for any of these. They must be deterministic, tested code that matches the books, before any
recipe number is shown to a brewer.

## Goal
A tested maths library that computes a recipe's OG, FG, ABV, IBU and colour from its rows, and
solves amounts for a target OG and IBU. Every function reproduces the worked examples in
*How to Brew* and in the OBC *Recipe Formulation* PDF (2009) within the agreed tolerances.

## Scope
In:
- A doc → calculation pass on `shared/rag-files/pending/how_to_brew.pdf` and on the OBC
  *Recipe Formulation* PDF (its Dubbel and Bohemian Pils examples) for the formulas and worked
  examples these functions need, written up in this folder (`doc-calc.md`: what was found,
  where, and what it became).
- Functions: extract → points; OG from grist, efficiency and volume; FG from OG, yeast
  attenuation and fermentability (`full` · `normal` · `none`); ABV; IBU (Tinseth) by addition;
  colour (Morey) from EBC; EBC ↔ SRM; SG ↔ °Plato; volumes (pre-boil from boil-off and losses).
- Each function takes plain numbers (kg, %, EBC, minutes, L), and the recipe-level totals (OG of a
  grist, IBU of all additions, colour of a grist) take a list of such items. That way the book's
  examples, the corpus recipes (s2) and step 10 (m6) all call the same functions.
- Solvers: grist amounts from target OG and grist %; hop amounts from target IBU and hop split.
- A `calc_version` string that names this version of the maths (`app.recipe.calc_version`).

Out:
- Water chemistry, priming sugar, pitch rate (M7, with their sources). Water chemistry moved
  from P2 to M7 (your answer, 2026-10-14). Mash temperature ↔ FG (a hint knob in M4).
- Whirlpool and dry-hop IBU above 0. In this work both count as 0 IBU (R4). A cited model for
  them is a late-game follow-up, listed under "Later" in RECIPE-ROADMAP §8 so it is not lost
  once this work ships.
- Reading `ref` or `app` rows, and choosing one number from a `numrange` (`ref.fermentable.ebc`,
  `ref.hop.alpha_pct`, `ref.yeast.attenuation_pct`). The caller does that: step 10 (m6) or the
  corpus gate (s2).
- Unit conversion for display (US units). The functions only convert inside, where a formula is
  defined in US units.

## Requirements
R1. Each function takes and returns SI units (kg, g, L, °C, EBC), with SG as 1.xxx and plato
    available, and states its source (book, chapter, table or page) next to it.
R2. Fermentable extract means what `ref.fermentable.extract_dbfg_pct` stores; sugars and honey
    are Palmer's as-sold values and are not moisture-corrected (DATABASE.md note). For malts
    (% dry basis), the function does what *How to Brew* ch. 18 does about moisture (a correction,
    or none with the loss left in efficiency). `doc-calc.md` records which, with the page.
R3. FG uses the yeast's attenuation and the fermentability of each fermentable: `none` (lactose)
    adds gravity that does not ferment, `full` (candi, honey) ferments fully.
R4. IBU uses Tinseth per addition, with utilisation from boil time and boil gravity; the solver
    finds hop grams for a target IBU given each addition's share and time. Whirlpool and dry-hop
    additions give 0 IBU, and the function says so next to that rule.
R5. Colour uses Morey on MCU from EBC, kg and litres; EBC ↔ SRM uses one stated factor.
R6. The OG solver finds grist kg for a target OG given grist %, efficiency and volume.
R7. Tests reproduce every worked example `doc-calc.md` lists (Palmer's and OBC's) within these
    tolerances: OG ± 0.001, FG ± 0.002, ABV ± 0.1, IBU ± 1, SRM ± 1 (EBC ± 2). A tolerance is
    looser only where the book itself rounds more coarsely, and `doc-calc.md` names each such
    case. Edge cases are tested too: zero hops, 100 % sugar, a non-fermentable at 10 %.
R8. The functions are SQL functions in a `db/*.sql` file, applied with `psql` as `postgres`
    (G0, OPERATIONS.md §4). They are callable from n8n's Postgres node the way step 2 calls
    `app.step2_best_style`, and pytest tests them through `psycopg`.
R9. ABV comes from OG and FG and reproduces Palmer's table 9.1 within tolerance. The formula is
    the one `doc-calc.md` cites.
R10. Pre-boil volume comes from batch volume, boil time, boil-off rate and losses (the
    `app.brewer_profile` fields). Boil gravity for Tinseth comes from it.

## Constraints
- CLAUDE.md: brewing maths is deterministic, tested code; never the LLM, never a skill.
- PROJECT.md §6.7: a doc → calculation pass comes first for each source.
- §6.8: one function per formula, readable without a config table.
- Never tune constants to fit an example; a miss means a wrong formula or unit.
- CLAUDE.md: database changes go in `.sql` files in the repo, applied with `psql` as `postgres`,
  never through the Supabase MCP (it is read-only) or as `supabase_admin`.
- DATABASE.md: units are SI, and conversion to other units happens only at display. `misc`
  extras never enter the OG/IBU/SRM maths.

## Assumptions
- *How to Brew* in `pending/` is the 4th edition (2017, 612 pages; checked 2026-10-14). It has
  worked examples for gravity points (ch. 4, in PPG and PKL), efficiency (ch. 18, table 18.4),
  IBU (ch. 5, the "Joe Ale" example on Tinseth's table 5.5), colour (appendix B, an MCU example
  and Morey in table B.3) and ABV (table 9.1). Checked while planning (2026-10-14): the gravity,
  IBU, colour and FG examples reproduce. Table 4.3's ABV row disagrees with table 9.1 and matches
  no formula, so it is recorded in `doc-calc.md` and not tested (its FG row is tested). Most
  examples are in US units, so the tests convert their inputs with stated factors.
- The OBC *Recipe Formulation* PDF (2009, 6 pages) is in `pending/` (downloaded 2026-10-14).
  Checked while planning: its Dubbel and Bohemian Pils examples give enough inputs to recompute
  OG and MCU. Its SRM and IBU figures come from Daniels' tables (MCU → SRM ranges, stepped hop
  utilisation), not from Morey or Tinseth, and its IBU example has no boil gravity or volume.
- Palmer gives no whirlpool or dry-hop IBU figure *(unverified; a text search of the PDF found
  none)*.

## Acceptance criteria
A1. `doc-calc.md` lists each formula and worked example used, with page or table (R1).
A2. Tests for every listed worked example pass within R7's tolerances (R7, G-M): Palmer's, and
    OBC's OG and MCU for the Dubbel and the Bohemian Pils (Pils 4.0 MCU; Dubbel 40.5 MCU,
    recomputed from the book's rows, since its printed 35.25 candi row and 43 total are an
    arithmetic slip). OBC's SRM and IBU figures use Daniels' tables, a different model. They are
    written up in `doc-calc.md` and not tested.
A3. A test recipe with 10 % lactose has a higher FG than the same recipe without, and with candi
    sugar a lower one (R3).
A4. Solving for OG 1.060 and then computing OG from the result gives 1.060 ± 0.001; the same for
    IBU 50 ± 1 (R4, R6).
A5. `pg_proc` lists the maths functions owned by `postgres`, from a `db/*.sql` file. One of them,
    called through n8n's Postgres node with the existing Postgres credential (a test execution),
    gives the same number as its unit test (R8).
A6. `calc_version` is defined and documented (Scope).
A7. ABV matches table 9.1 within tolerance at the cells `doc-calc.md` lists (R9). SG → °Plato →
    SG round-trips within 0.001 (R1). Pre-boil volume for 20 L, 60 min, 3 L/h boil-off and 2 L
    losses is 25 L (batch + losses + boil-off; Palmer gives no cooling-shrinkage figure in a
    text search) (R10).
A8. Adding a whirlpool or a dry-hop addition to a test recipe leaves its IBU unchanged (R4).

## Open questions
None open. Your answers, 2026-10-14:
1. Tolerances: a fixed bar, OG ± 0.001, FG ± 0.002, ABV ± 0.1, IBU ± 1, SRM ± 1 (EBC ± 2). It is
   looser only where the book itself rounds more coarsely (R7).
2. Whirlpool and dry-hop IBU: "both 0 for now, but somewhere mark these late game followups" (R4,
   Scope Out, RECIPE-ROADMAP §8 Later).
3. Water chemistry moves from P2 to M7; the RECIPE-ROADMAP §8 P2 box drops "water".
4. OBC: you download the PDF into `pending/` before planning, and its Dubbel and Bohemian Pils
   examples become tests too (Scope, R7, A2).

## Deviations
- 2026-10-14 · Scope: the OBC *Recipe Formulation* PDF is now required (it was optional), and its
  Dubbel and Bohemian Pils examples are tests (A2) — your answer to Open question 4.
- 2026-10-14 · R4, A8: whirlpool and dry-hop additions give 0 IBU, and a cited model for them
  is a late-game follow-up (RECIPE-ROADMAP §8 Later) — your answer to Open question 2.
- 2026-10-14 · Scope: water chemistry moved from P2 to M7, and RECIPE-ROADMAP §8 was updated to
  match — your answer to Open question 3.
- 2026-10-14 · A2: OBC's examples are tested for OG and MCU only. Its SRM and IBU figures come from
  Daniels' tables, not Morey or Tinseth, and are written up in `doc-calc.md` without a test.
  The Dubbel MCU is tested against the recomputed 40.5, not the book's 43 (arithmetic slip on the
  candi row). This was your answer while planning.
- 2026-10-14 · Assumptions: table 4.3's ABV row is not tested. It disagrees with table 9.1 and no
  formula matches it. ABV is tested on table 9.1 (R9, A7). Found while planning.
