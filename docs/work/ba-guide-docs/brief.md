# Bring BA "later" notes in line with D1

Status: approved
Slug: ba-guide-docs · Branch: ba-guide-docs

## Why
D1 was decided on 2026-10-11 (PROJECT.md §5): both style guides are used, BJCP 2021 preferred,
BA 2026 where it describes the beer better or the user is asked, and the user can set BJCP only
or BA only. Step 2 is not built yet and follows this rule in P4. Two docs still describe BA as a
future option, so a reader planning P3 or P4 gets the wrong picture.

Checked against D1, both are out of date:
- `docs/RECIPE-ROADMAP.md` §8, the **Later** row lists "BA as a selectable guide". Under D1, BA is
  already a guide step 2 can pick, and the user can select BA only. That belongs to P4 (step 2),
  not to Later. The D1 note in RECIPE-ROADMAP §9 is already correct; only the phase table
  contradicts it.
- `docs/DATABASE.md` §9 "Later", the row "A style family for BA styles" (line 451) is triggered
  "if BA becomes a selectable guide". That condition is now met. The item itself is still not
  built: measured 2026-10-11, all 169 BA rows in `ref.beer_style` have `category_code` NULL and
  10 distinct `category` values (BJCP: 116 rows, all with `category_code`, 34 categories). So the
  row stays in "Later", but its trigger is wrong.

No other doc says BA is a future or optional guide (grep for "selectable", "BA only",
"BJCP only" outside `docs/finished/`).

## Goal
RECIPE-ROADMAP and DATABASE.md agree with D1: BA is a guide step 2 uses (P4), and the BA style
family is recorded as still to be built, with a trigger that is true under D1.

## Scope
In:
- The RECIPE-ROADMAP §8 phase table: the Later row and the P4 row.
- The DATABASE.md §9 "A style family for BA styles" row: its "When" text.
- PROJECT.md §8 progress-log entries for this work.

Out:
- Building the BA style family, or filling `category_code` for BA rows.
- How BA styles get a corpus profile. The Brewer's Friend corpus is mapped to BJCP styles
  (STYLE-PROFILES.md §1), which this work does not touch.
- Where the user's BJCP only / BA only setting is stored, and the step 2 code itself (P4).
- The test briefs, which keep expecting BJCP codes.
- PROJECT.md §2, §3, §5 and §6, and the D1 note in RECIPE-ROADMAP §9 (already correct).

## Requirements
R1. The RECIPE-ROADMAP §8 Later row no longer lists "BA as a selectable guide"; its other items
    (inventory-first mode, substitutions, batch log → feedback) are unchanged.
R2. RECIPE-ROADMAP states in the phase table that step 2 applies D1 (BJCP preferred, BA where it
    fits better, user setting BJCP only / BA only) in the P4 "Do" cell (user decision,
    2026-10-11).
R3. The DATABASE.md §9 "A style family for BA styles" row stays in §9 and keeps its facts
    (`category_code` NULL for all 169 BA rows, 10 origin families in `category`, the
    STYLE-PROFILES §3 fallback), but its trigger no longer says "if BA becomes a selectable
    guide". The trigger reads: "when a BA style needs a style profile (D1: step 2 can pick a BA
    style)" (user decision, 2026-10-11).
R4. No doc outside `docs/finished/` still describes BA as a future or optional guide.
R5. PROJECT.md §8 has a dated entry for this work linking `docs/work/ba-guide-docs/`.

## Constraints
- CLAUDE.md: do only what was asked; no other doc edits. PROJECT.md §2, §3, §6 unchanged.
- CLAUDE.md / PROJECT.md §10: PROJECT.md is updated in the same change, with a dated §8 entry;
  facts stated are measured.
- conventions.md: commit only explicit paths; brief committed after approval.
- Docs-only change: no DB writes, no code.

## Assumptions
- The BA row counts quoted above stay as measured on 2026-10-11 until this work ships.
- The user's BJCP only / BA only setting is part of step 2's behaviour in P4, not a separate later
  feature *(unverified; D1 says step 2 "follows this rule (P4)" but does not say where the setting
  lives)*.

## Acceptance criteria
A1. `grep -n "selectable" docs/RECIPE-ROADMAP.md` returns nothing, and the Later row still lists
    inventory-first mode, substitutions and batch log → feedback (R1).
A2. The P4 row of the RECIPE-ROADMAP §8 table mentions step 2 picking BJCP or BA per D1, with the
    BJCP only / BA only setting (R2).
A3. `docs/DATABASE.md` §9 still has the "A style family for BA styles" row, with "169",
    "`category_code`", "10" and the STYLE-PROFILES §3 link, and does not contain
    "if BA becomes a selectable guide"; its trigger is "when a BA style needs a style profile
    (D1: step 2 can pick a BA style)" (R3).
A4. `grep -rn -i "selectable guide\|if BA becomes" --include=*.md . | grep -v docs/finished`
    returns nothing (R4).
A5. PROJECT.md §8 has a 2026-10-xx entry naming `ba-guide-docs` with a link to its folder (R5).
A6. `git diff main --stat` on the branch touches only `docs/RECIPE-ROADMAP.md`,
    `docs/DATABASE.md`, `PROJECT.md` and `docs/work/ba-guide-docs/` (scope).

## Open questions
None. Answered by the user 2026-10-11:
1. BA item in the RECIPE-ROADMAP phase table: removed from Later; the P4 "Do" cell says step 2
   picks BJCP or BA per D1, with the BJCP only / BA only setting (R2).
2. DATABASE.md §9 BA style-family row: stays in §9, trigger "when a BA style needs a style
   profile (D1: step 2 can pick a BA style)" (R3).

## Deviations
