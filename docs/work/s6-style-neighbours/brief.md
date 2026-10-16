# S6 · Neighbouring styles: step 2 checks and an envelope cross-check

Status: draft
Slug: s6-style-neighbours · Branch: s6-style-neighbours
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) M2/M3 (before checkpoint **G3**) ·
[`m2-best-fit-style`](../../finished/m2-best-fit-style/brief.md) ·
[`s3-style-fit`](../../finished/s3-style-fit/brief.md) · [SOURCES.md](../../SOURCES.md)
Needs: `m2-best-fit-style` and `s3-style-fit` shipped (both are). Before `m3-deviations`' G3 run.

## Why
Step 2 is tested on 22 briefs, which rarely sit between two close styles. The hard part of picking
a style is telling neighbours apart: Scottish Light, Heavy and Export, the Bocks, Irish, Sweet and
Oatmeal Stout. The BJCP Beer Exam Study Guide (2017) lists 91 groups of three styles that judges
must compare and contrast (question S0): 84 style names, 80 of them exact BJCP 2021 names, the
other four map to 7A Vienna Lager, 17D English Barley Wine, 26A Belgian Single and 21B Specialty
IPA (Belgian IPA is one of its types) (measured 2026-10-16). Nobody has checked how step 2 does on
them.

Two more sources can check work already done, without entering `ref` or `kb`:
- Barnes' *BJCP Style Flashcards* (c. 2011) put each BJCP 2008 style's aroma, flavour and
  mouthfeel into a grid (intensity, character, optional, unacceptable), close to the shape of the
  26 reviewed envelopes. About 21 of the 26 have a 2008 counterpart (not 21C Hazy IPA, 31B and the
  three BA styles). The 2008 guidelines differ from 2021, so only you can tell an envelope mistake
  from a guideline change.
- The BJCP 2021 *Introduction to Specialty-Type Beer* says how a base style and a specialty
  ingredient are entered ("Base Style", "Best Fit"). Step 2 already picks the base style by default
  and the specialty code for a `feature` adjunct (PROJECT.md §5, D1). Whether BJCP's own text
  agrees has not been checked.

## Goal
We know, measured, how often step 2 picks the right style among its exam neighbours, and which
neighbours it confuses; the 21 envelopes with a 2008 counterpart have been compared with Barnes'
grids and every difference was settled by you; and the D1 base-style rule has been checked
against BJCP 2021's specialty-entry text.

## Scope
In:
- A check set in `evals/`: for each style named in the 91 triples, one step-1-shaped brief that
  does not name the style, built from the 2021 guideline text (its stats and distinguishing
  words), with the expected style and its two triple partners. The 2008 comparison sheet may
  suggest which words set neighbours apart; every word must also be in the 2021 description.
- A runner that sends each brief straight to `app.step2_best_style` (no step 1 LLM call) and
  reports: right style first, right style in the top 3, and a confusion list per triple.
- The first measured result recorded in PROJECT.md §8.
- A cross-check report in this folder: for each of the ~21 envelopes with a 2008 flashcard, the
  dimensions where Barnes' intensity or characters differ from `loaders/style_envelopes.toml`.
  You decide each difference; agreed changes go into the toml with the s3 review flow, and the
  golden set must stay green.
- A short note comparing BJCP 2021's specialty-entry rules with the D1 base-style rule: agrees,
  or a proposed change put to you.

Out:
- Tuning step 2's weights from the result (its own work item if the numbers call for it).
- Loading anything from the 2008 sources into `ref` or `kb`. BA styles (the triples are BJCP
  only). Envelopes for new styles.

## Requirements
R1. The check set has one brief per distinct style in the 91 triples (84 names, the four mapped as
    above), each with the expected BJCP 2021 code and its triple partners; no brief contains the
    style's name or an alias from `app.style_alias()`.
R2. Every number and descriptive word in a brief comes from that style's BJCP 2021 entry in
    `ref.beer_style`; the brief file says so in its header, and a test checks the stated numbers
    lie inside the style's 2021 ranges.
R3. The runner prints the share with the right style first, the share with it in the top 3, and,
    per triple, which partner was picked instead; `--save` writes `evals/results/<date>-s6.json`.
R4. The first run's numbers are recorded in PROJECT.md §8 as measured; no step 2 code changes in
    this work.
R5. The envelope cross-check report lists, per envelope with a 2008 counterpart, each dimension
    that differs (Barnes' words, the envelope's level, the 2021 quote behind it), and your decision
    for each.
R6. Agreed envelope changes are applied through `loaders/style_envelopes.toml` (`reviewed = true`),
    loaded twice with identical results, and `tests/test_style_fit_golden.py` passes.
R7. A note in this folder compares the 2021 specialty-entry text with the D1 rule, quoting at most
    short phrases; any proposed change to PROJECT.md §5 D1 is put to you, not made.

## Constraints
- PROJECT.md §6.6 measure before and after; §6.8 readable over optimal.
- BJCP 2008 numbers and codes never enter `ref` or `kb` (SOURCES.md).
- PROJECT.md §2, §3, §6 and D1 change only with your agreement.
- Copyright: the briefs paraphrase the 2021 guidelines; no long quotes in the repo.

## Assumptions
- Step 2 can be called with a hand-written brief JSON and request text, without step 1
  *(true for `app.step2_best_style(brief, request, guide_preference)`; the request text is still
  used for guide words)*.
- About 21 of the 26 envelopes have a 2008 flashcard *(counted by hand from the flashcard
  headers; check per style)*.

## Acceptance criteria
A1. The check set exists with one brief per triple style (84), each with expected code and
    partners; a test confirms no brief contains its style's name or alias (R1).
A2. A test confirms every stated number lies in the style's 2021 range (R2).
A3. `python -m evals.<runner>` prints right-first, top-3 and the per-triple confusions; the first
    run is saved and recorded in PROJECT.md §8 (R3, R4).
A4. `git diff` of the work shows no change to `db/022_step2.sql` (R4).
A5. The cross-check report covers every envelope with a 2008 counterpart, each difference has
    your decision, agreed changes are in the toml, loaded twice, and the golden set passes (R5, R6).
A6. The specialty-entry note exists, and any D1 change was approved by you or recorded as
    declined (R7).

## Open questions
1. Brief content: numbers, words or both? — options: a) both, as a user would write (one or two
   stated numbers plus two to four descriptive words); b) words only, to test word scoring;
   c) one of each per style — recommend a: closest to real requests, and still one brief per style.
2. A bar for the check set? — options: a) report only, decide on tuning from the result;
   b) set a bar now — recommend a: there is no baseline yet.
3. Do the Barnes cross-check here or drop it? — options: a) here, as scoped; b) drop it, since the
   envelopes are reviewed and the golden set passes — recommend a only if you want a second look
   at the envelopes; I expect most differences to be 2008-vs-2021 changes.

## Deviations
