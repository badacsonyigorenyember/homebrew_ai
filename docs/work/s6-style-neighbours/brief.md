# S6 · Neighbouring styles: step 2 checks and an envelope cross-check

Status: approved
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
  does not name the style, written as a user would: one or two stated numbers plus two to four
  descriptive words, built from the 2021 guideline text (its stats and distinguishing words),
  with the expected style and its two triple partners. The 2008 comparison sheet may
  suggest which words set neighbours apart; every word must also be in the 2021 description.
- A runner that sends each brief straight to `app.step2_best_style` with guide `any`, the
  pipeline default (no step 1 LLM call), in two runs, and reports them side by side with no pass
  bar: right style first, right style in the top 3, and a confusion list per triple.
  - **Run A**, without a family noun: numbers and words only, `named` empty. The end-to-end figure.
  - **Run B**, with the triple's family noun (stout, bock, lager…) as `named`. The
    neighbour-confusion figure. Only triples whose three styles share one family; a triple that
    spans families runs only in Run A and is marked and counted in the report.
  - The gap between A and B on the same briefs.
  A BA style can win under `any`; that brief counts as a miss and the report names the BA pick.
- The first measured result recorded in PROJECT.md §8.
- A cross-check report in this folder: for each of the ~21 envelopes with a 2008 flashcard, the
  dimensions where Barnes' intensity or characters differ from `loaders/style_envelopes.toml`.
  You decide each difference; agreed changes go into the toml with the s3 review flow, and the
  golden set must stay green.
- A short note comparing BJCP 2021's specialty-entry rules with the D1 base-style rule: agrees,
  or a proposed change put to you.

Out:
- Tuning step 2's weights from the result (its own work item if the numbers call for it).
- Loading anything from the 2008 sources into `ref` or `kb`. Briefs for BA styles (the triples
  are BJCP only; BA styles are still scored, since the guide is `any`). Envelopes for new styles.

## Requirements
R1. The check set has one brief per distinct style in the 91 triples (83 styles from 84 names: Vienna, mapped
    above, and Vienna Lager are both 7A), each with the expected BJCP 2021 code and its triple partners; no brief's Run A text
    contains the style's name or an alias from `app.style_alias()`. A family noun appears only in
    Run B, and only as the family word in `named`.
R2. Each brief states one or two numbers and two to four descriptive words. Every number and
    descriptive word in a brief comes from that style's BJCP 2021 entry in
    `ref.beer_style`; the brief file says so in its header, and a test checks the stated numbers
    lie inside the style's 2021 ranges.
R3. The runner calls step 2 with guide `any` and prints, for Run A and Run B side by side, the
    share with the right style first, the share with it in the top 3, and, per triple, which
    partner (or other style, BA picks named) was picked instead; the gap between A and B on the
    briefs both runs cover; and the triples run only in A (spanning families), marked and counted.
    `--save` writes `evals/results/<date>-s6.json`.
R4. The first run's numbers (both runs and the gap) are recorded in PROJECT.md §8 as measured. There is no pass bar:
    whether to tune step 2 is decided from the result. No step 2 code changes in this work.
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
  *(true for `app.step2_best_style(brief, request, guide_preference)`; the request text is read
  only for guide words, and not at all when the guide is passed)*.
- `named` boosts, it does not filter *(measured 2026-10-16 from `db/022_step2.sql`)*: each style
  gets 4 × the share of its name words matched, so a family noun lifts only styles whose name
  holds that word, and unevenly ("stout" adds 2 to Irish Stout, 1.33 to Foreign Extra Stout;
  "bock" adds 2 to Helles Bock and Dunkles Bock, 0 to Doppelbock and Eisbock). Run B is read with
  this in mind: it is step 2's real behaviour with a family word, not a pick restricted to the
  family.
- About 21 of the 26 envelopes have a 2008 flashcard *(counted by hand from the flashcard
  headers; check per style)*.

## Acceptance criteria
A1. The check set exists with one brief per triple style (83), each with expected code and
    partners; a test confirms no brief's Run A text contains its style's name or alias, and that
    each family noun is a family word only (R1).
A2. A test confirms each brief has one or two stated numbers and two to four descriptive words,
    and every stated number lies in the style's 2021 range (R2).
A3. `python -m evals.<runner>` prints right-first, top-3 and the per-triple confusions for Run A
    and Run B side by side, the gap, and the count of triples run only in A; the first run is
    saved and recorded in PROJECT.md §8 (R3, R4).
A4. `git diff` of the work shows no change to `db/022_step2.sql` (R4).
A5. The cross-check report covers every envelope with a 2008 counterpart, each difference has
    your decision, agreed changes are in the toml, loaded twice, and the golden set passes (R5, R6).
A6. The specialty-entry note exists, and any D1 change was approved by you or recorded as
    declined (R7).

## Decisions
1. Brief content: both numbers and words (one or two stated numbers plus two to four descriptive
   words) — closest to real requests, still one brief per style.
2. No bar for the check set: report only, decide on tuning from the result — there is no baseline
   yet.
3. The Barnes 2008 envelope cross-check stays in this work, as scoped — you want a second look at
   the envelopes.
4. Guide `any` in the runner, the pipeline default: a BA pick counts as a miss and is named (plan
   review, "1b").
5. Two runs side by side: A without and B with the triple's family noun as `named`, plus the gap;
   triples spanning families only in A, marked and counted (plan review, "2c").

## Deviations
- 2026-10-16 · Scope, R1, R3, R4, A1, A3: the runner uses guide `any` (a BA pick is a named miss)
  and runs every brief twice, A without and B with the triple's family noun as `named`, reported
  side by side with the gap; triples spanning families run only in A, marked and counted — your
  answers "1b" and "2c" at plan review. Assumption added: `named` boosts, it does not filter.
- 2026-10-16 · R1, A1: 83 briefs, not 84 — 84 counted printed names; Vienna and Vienna Lager are the
  same style (7A). Found when the triples were built.
