# S1 · Brewing maths library (P2)

Status: draft
Slug: s1-maths · Branch: s1-maths
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) side track P2, checkpoint **G-M** ·
[RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §6, §8 P2
Needs: `m0-harness` shipped (G0 decides where this code lives)

## Why
Gravity, ABV, bitterness and colour are needed by steps 4, 10 and 11, and by the corpus quality
gate G4 (s2), which recomputes OG and IBU to catch bad recipes. CLAUDE.md forbids asking the LLM
for any of these. They must be deterministic, tested code that matches the books, before any
recipe number is shown to a brewer.

## Goal
A tested maths library that computes a recipe's OG, FG, ABV, IBU and colour from its rows, and
solves amounts for a target OG and IBU. Every function reproduces the worked examples in
*How to Brew* (and OBC where it has one) within the agreed tolerance.

## Scope
In:
- A doc → calculation pass on `shared/rag-files/pending/how_to_brew.pdf` for the formulas and
  worked examples these functions need, written up in this folder (`doc-calc.md`: what was found,
  where, and what it became).
- Functions: extract → points; OG from grist, efficiency and volume; FG from OG, yeast
  attenuation and fermentability (`full` · `normal` · `none`); ABV; IBU (Tinseth) by addition;
  colour (Morey) from EBC; EBC ↔ SRM; volumes (pre-boil from boil-off and losses).
- Solvers: grist amounts from target OG and grist %; hop amounts from target IBU and hop split.
- A `calc_version` string that names this version of the maths (`app.recipe.calc_version`).

Out:
- Water chemistry, priming sugar, pitch rate (M7, with their sources). Mash temperature ↔ FG
  (a hint knob in M4). Whirlpool and dry-hop IBU beyond what Palmer gives (Open question 2).

## Requirements
R1. Each function takes and returns SI units (kg, g, L, °C, EBC), with SG as 1.xxx and plato
    available, and states its source (book, chapter, table or page) next to it.
R2. Fermentable extract is read as stored in `ref.fermentable.extract_dbfg_pct`; sugars and honey
    are Palmer's as-sold values and are not moisture-corrected (DATABASE.md note).
R3. FG uses the yeast's attenuation and the fermentability of each fermentable: `none` (lactose)
    adds gravity that does not ferment, `full` (candi, honey) ferments fully.
R4. IBU uses Tinseth per addition, with utilisation from boil time and boil gravity; the solver
    finds hop grams for a target IBU given each addition's share and time.
R5. Colour uses Morey on MCU from EBC, kg and litres; EBC ↔ SRM uses one stated factor.
R6. The OG solver finds grist kg for a target OG given grist %, efficiency and volume.
R7. Tests reproduce every worked example `doc-calc.md` lists, within the tolerance of Open
    question 1, and edge cases: zero hops, 100 % sugar, a non-fermentable at 10 %.
R8. Code lives where G0 decided, and is callable from n8n the same way the steps call code.

## Constraints
- CLAUDE.md: brewing maths is deterministic, tested code; never the LLM, never a skill.
- PROJECT.md §6.7: a doc → calculation pass comes first for each source.
- §6.8: one function per formula, readable without a config table.
- Never tune constants to fit an example; a miss means a wrong formula or unit.

## Assumptions
- *How to Brew* (the PDF in `pending/`) has worked examples for gravity, IBU and colour
  *(unverified for this edition)*.
- The OBC recipe formulation PDF (2009) is not downloaded; its examples are optional
  *(RECIPE-ROADMAP §2 lists it as a candidate)*.

## Acceptance criteria
A1. `doc-calc.md` lists each formula and worked example used, with page or table (R1).
A2. Tests for every listed worked example pass within tolerance (R7, G-M).
A3. A test recipe with 10 % lactose has a higher FG than the same recipe without, and with candi
    sugar a lower one (R3).
A4. Solving for OG 1.060 and then computing OG from the result gives 1.060 ± 0.001; the same for
    IBU 50 ± 1 (R4, R6).
A5. A step workflow (or the harness) calls one function the way G0 decided and gets the same
    number as the unit test (R8).
A6. `calc_version` is defined and documented (Scope).

## Open questions
1. Tolerances? — options: a) OG ± 0.001, FG ± 0.002, ABV ± 0.1, IBU ± 1, SRM ± 1 (EBC ± 2); b) set
   per example from the book's own rounding — recommend a, with b where the book rounds coarser.
2. IBU for whirlpool and dry hop? — options: a) whirlpool at a fixed utilisation by temperature
   from a cited source, dry hop 0; b) both 0 for now — recommend b until a source is found; the
   recipe sheet says so.
3. Water chemistry was grouped under P2 in RECIPE-ROADMAP. Move it to M7, next to the *Water*
   book? — options: a) yes; b) keep it here — recommend a: M7 is the first step that reads it.

## Deviations
