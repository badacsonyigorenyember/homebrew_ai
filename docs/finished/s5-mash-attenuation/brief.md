# S5 · A cited model of mash temperature's effect on attenuation

Status: approved
Slug: s5-mash-attenuation · Branch: s5-mash-attenuation
Roadmap: [RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §8 Later (the rule 10 TODO) ·
[`s2-formulation-rules`](../../finished/s2-formulation-rules/brief.md) rule 10 ·
[SOURCES.md](../../SOURCES.md)
Needs: `s2-formulation-rules` shipped (it is). Before: `m4-targets-blueprint`, whose mash knob and
FG target use this model, and `m7-process`, whose mash step uses it.

## Why
`app.mash_attenuation` (`db/032_formulation_check.sql`) predicts attenuation by mapping the yeast's
attenuation range linearly onto 64–69 °C: the top of the range at 64 °C, the bottom at 69 °C. Its
own comment and rule 10's sentence call it an UNCITED ASSUMPTION. Rule 10 checks the predicted FG
against the style with it, and M4 will set the mash temperature from hints (`dry` → 64–65 °C,
`full` → 68–69 °C) and expect the FG to follow. A wrong slope gives wrong FG targets in every
recipe. We now have measured sources:
- Troester, *Effects of mash parameters on attenuation and efficiency* (2009, CC BY-NC 3.0):
  limit of attenuation against average mash temperature for Pilsner malt; after the peak it falls
  almost linearly, about 4 % per °C over a 12 °C range (Figure 10, PDF p. 11); also mash time, pH,
  crush and thickness.
- Troester, *Mash Time Dependency of Wort Fermentability* (wiki): fermentability keeps changing
  after the iodine test is negative.
- Terrill, *Observations on Attenuations* (2017): 44 batches, three strains; within the normal
  single-infusion range one strain's attenuation stays almost flat while another falls with mash
  temperature. The plots are images.

## Goal
Predicted attenuation, and with it the predicted FG in rule 10 and in M4, comes from a model whose
every number has a source, documented and tested, and rule 10 no longer says "uncited".

## Scope
In:
- A doc → calc pass on the three sources (`doc-calc.md` in this folder): which numbers are read,
  from which figure, table or page, and how. Values read off figure images are listed one by one
  and checked by you.
- A replacement for `app.mash_attenuation` with the same inputs (the yeast's attenuation range
  and the mash temperature), so its callers stay unchanged.
- Rule 10's sentence and limits updated; the RECIPE-ROADMAP §8 TODO line resolved.
- The 22 reference recipes re-checked with the new model.

Out:
- Multi-step mash profiles and decoction (RECIPE-ROADMAP §8 Later, stays there). Mash pH,
  crush and thickness effects (no input for them in a recipe). Per-strain curves for the 119
  yeasts (no data). Changing the 64–69 °C mash limits unless a source says so.

## Requirements
R1. Every number the model uses is in `doc-calc.md` with its source, figure or page, and how it
    was read; values read from images are marked so and approved by you.
R2. The model is a SQL function in `db/` with the same signature as `app.mash_attenuation`, owned
    by `postgres`, applied twice without error.
R3. Tests reproduce the source values the model is built from (the points read from Troester's
    Figure 10 or appendix table) within a tolerance stated in `doc-calc.md`.
R4. The model's behaviour across 64–69 °C is stated in one sentence a reader can check (for
    example "x points less per °C above y °C, never outside the yeast's range"), and a test pins
    the ends and one middle value, replacing `test_mash_mapping`.
R5. Rule 10's sentence no longer contains "uncited assumption" and names the source; the
    `test_formulation_rules.py` checks still pass.
R6. All 22 reference recipes are re-run; any whose rule 10 result changes is shown to you before
    the model is accepted, with old and new predicted FG.
R7. Terrill's strain finding is recorded in `doc-calc.md` as a known limit of the model (which
    strains behave how, as far as the text says).

## Constraints
- PROJECT.md §6.7: doc → calc first; the LLM never computes the number.
- §6.8 readable over optimal: one function a reader can follow, no fitted curve with many
  coefficients unless the data needs it.
- DB changes as `.sql` files applied as `postgres` (OPERATIONS.md §4).
- Troester's PDF is CC BY-NC 3.0: cite it in the function comment and in `doc-calc.md`.

## Assumptions
- Troester's limit of attenuation is the wort's fermentability limit, measured with a fast
  ferment test on a single all-Pilsner-malt grist with a ~4 °C temperature drop over the rest
  *(as the paper states; transfer to other grists unverified)*.
- The yeast makers' attenuation ranges correspond to a standard wort mashed somewhere near the
  middle of 64–69 °C *(unverified; Terrill reports most of his batches above Wyeast's range)*.

## Acceptance criteria
A1. `doc-calc.md` lists every model number with source and figure/page; you approved the values
    read from images (R1, R7).
A2. The new function exists, is owned by `postgres`, and `db/032` (or its new file) applies twice
    without error (R2).
A3. The source-value tests and the replaced `test_mash_mapping` pass (R3, R4).
A4. `select sentence from app.formulation_rules() where rule = '10'` names the source and has no
    "uncited assumption" (R5).
A5. The 22 reference recipes' rule 10 results before and after are recorded; every change was
    shown to you and settled (R6).
A6. RECIPE-ROADMAP §8 no longer has the rule 10 TODO; full `pytest` passes (R5, R6).

## Open questions
1. Model shape? — **decided 2026-10-17 (user): a)** keep the yeast range; flat below Troester's
   measured peak, Troester's slope above it, clamped to the yeast's range. Why: closest to
   today's inputs, one cited slope; b) drops the yeast range, c) needs data Terrill only shows as
   images for three strains.
2. Reference temperature (where the yeast's stated range applies)? — **decided 2026-10-17 (user):
   c, else b.** *Yeast* states no mash temperature for a strain's range (only "for the average
   wort", PDF p. 130; full-text search of the book, 2026-10-17), so b: **66.5 °C**, the middle of
   64–69 °C.

## Deviations
