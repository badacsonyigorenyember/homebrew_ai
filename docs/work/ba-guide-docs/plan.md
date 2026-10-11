# Bring BA "later" notes in line with D1 — implementation plan

Stage: verify
Brief: [brief.md](brief.md)
Branch: ba-guide-docs

## Approach
Docs-only change, two table cells and one table row, plus the PROJECT.md §8 log. In
`docs/RECIPE-ROADMAP.md` §8 the BA item leaves the **Later** row and the **P4** "Do" cell says
how step 2 applies D1 (R1, R2). In `docs/DATABASE.md` §9 the BA style-family row keeps its facts
and gets the trigger the user chose (R3). Nothing else in either file changes: the mermaid
diagram has no BA item, and the D1 note in RECIPE-ROADMAP §9 is already correct. One task, one
commit, because the two edits are one judgement ("does the doc set agree with D1?").

Checked 2026-10-11 on branch `ba-guide-docs`: the Later row is `docs/RECIPE-ROADMAP.md` line
299, the P4 row line 294, the BA row `docs/DATABASE.md` line 451. Line numbers are a guide only;
match on the text.

## Files
| Path | New / changed | Purpose |
|---|---|---|
| `docs/RECIPE-ROADMAP.md` | changed | §8 table: Later row loses the BA item; P4 "Do" cell states D1 for step 2 |
| `docs/DATABASE.md` | changed | §9 "A style family for BA styles": new trigger text |
| `PROJECT.md` | changed | §8 progress-log entries (plan, implementation) |
| `docs/work/ba-guide-docs/plan.md` | changed | ticks, `Stage:` line |

## Tasks

### Task 1: RECIPE-ROADMAP and DATABASE.md agree with D1
Why: R1–R5, A1–A6.
- [x] `docs/RECIPE-ROADMAP.md` §8 table, Later row. Replace
      `| **Later** | BA as a selectable guide · inventory-first mode · substitutions · batch log → feedback | |`
      with
      `| **Later** | inventory-first mode · substitutions · batch log → feedback | |`
- [x] Same table, P4 row. Replace the "Do" cell `Steps 0–3` with
      `Steps 0–3. Step 2 picks the style from BJCP 2021 or BA 2026 per D1 (§9): BJCP preferred, BA where it describes the beer better or the user is asked, and one guide only when the user sets BJCP only or BA only`.
      Leave the "Done when" cell (`≥ 18/20 briefs: right style, right deviations`) as it is.
- [x] `docs/DATABASE.md` §9, row "A style family for BA styles". In the "When" cell replace
      `if BA becomes a selectable guide:` with
      `when a BA style needs a style profile (D1: step 2 can pick a BA style):`.
      Keep the rest of the cell word for word (the `category_code` NULL for all 169 BA rows, the
      STYLE-PROFILES §3 link, the 10 origin families example).
- [x] PROJECT.md §8, under `### 2026-10-11` (or a new dated heading at the top if the date has
      moved on), add an entry above the existing `ba-guide-docs` lines:
      `Implemented ba-guide-docs ([docs/work/ba-guide-docs/](docs/work/ba-guide-docs/plan.md)): RECIPE-ROADMAP §8 moves BA from Later into P4 step 2 per D1; DATABASE.md §9 BA style-family row now triggered by a BA style needing a profile (still not built: 169 BA rows, category_code NULL).`
      Do not write the phrases "selectable guide" or "if BA becomes" in new entries, so the A4
      check stays clean. No status column changes (no status cell describes these docs).
- [x] Run the checks below; each must give the stated result.
- [x] Set `Stage: review` in this plan, tick the steps.

Checks (from the brief's acceptance criteria):
- A1: `grep -n "selectable" docs/RECIPE-ROADMAP.md` → no output, exit 1.
  `grep -n '^| \*\*Later\*\*' docs/RECIPE-ROADMAP.md` → one line listing inventory-first mode,
  substitutions, batch log → feedback.
- A2: `grep -n '^| \*\*P4\*\*' docs/RECIPE-ROADMAP.md` → one line containing "D1",
  "BJCP only" and "BA only".
- A3: `grep -n "A style family for BA styles" docs/DATABASE.md` → one line containing
  "when a BA style needs a style profile (D1: step 2 can pick a BA style)", "169",
  "`category_code`", "10 origin families" and "STYLE-PROFILES.md"; and
  `grep -c "if BA becomes a selectable guide" docs/DATABASE.md` → `0`.
- A4 (narrowed by user decision 2026-10-11, see brief Deviations): `grep -rn -i "selectable guide\|if BA becomes" --include=*.md . | grep -v "^./docs/finished/\|^./docs/work/ba-guide-docs/"`
  → exactly one hit, `./PROJECT.md:<n>`, where `<n>` lies between the `## 8. Progress log`
  heading and the next `## ` heading (the 2026-10-11 brief entry, which records the old
  wording as history).
- A5: `grep -n "ba-guide-docs" PROJECT.md` → includes the new Implemented entry with the
  `docs/work/ba-guide-docs/` link.
- A6: `git diff main --stat` → only `PROJECT.md`, `docs/DATABASE.md`, `docs/RECIPE-ROADMAP.md`
  and files under `docs/work/ba-guide-docs/`.

Done when: all six checks give the stated results.
Commit: `Align BA guide notes with D1`
(stage `docs/RECIPE-ROADMAP.md docs/DATABASE.md PROJECT.md docs/work/ba-guide-docs/plan.md`)

## Critical behaviour and its tests
None. Docs-only change: no data, recipe or later step depends on it at run time. The grep
checks in Task 1 cover the acceptance criteria.

## Approved exceptions

## Deviations
- 2026-10-11 · Task 1: the A4 check leaves out `docs/work/ba-guide-docs/` and expects exactly one hit, the PROJECT.md §8 log entry for the brief — the brief's first A4 could never pass (user decision; brief.md updated).
- 2026-10-11 · Task 1: run the A4 check with `command grep` (GNU grep) — in the Claude Code shell `grep` is a ugrep wrapper that prints paths without `./`, so the `^./docs/...` filter does not match; with GNU grep the check gives the stated one hit.
