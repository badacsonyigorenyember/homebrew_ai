# Review: ba-guide-docs

Diff: main...ba-guide-docs at 9ca8ca6  ·  Verdict: ready for testing

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | note | docs/RECIPE-ROADMAP.md:294, :299 | Later row now `inventory-first mode · substitutions · batch log → feedback`; P4 "Do" cell carries the D1 text word for word as planned, "Done when" unchanged. Its wording matches PROJECT.md §5 (line 144) and the RECIPE-ROADMAP §9 D1 note (line 310), and "(§9)" points at the right section (`## 9. Still open`, line 303). | R1, R2, A1, A2 met. |
| 2 | note | docs/DATABASE.md:451 | Only the trigger changed, to the user's chosen text; 169, `category_code` NULL, STYLE-PROFILES.md §3 link and "10 origin families" kept word for word. `grep -c "if BA becomes a selectable guide"` → 0. | R3, A3 met. |
| 3 | note | PROJECT.md:212 | A4 check (run with `command grep`, per plan Deviations) gives exactly one hit, `./PROJECT.md:212`, inside §8 (lines 200–707): the brief entry quoting the old wording as history. No other doc outside `docs/finished/` calls BA future or optional (also grepped "BA only", "BJCP only", "BA as a"). | R4, A4 met. |
| 4 | note | PROJECT.md:205–213 | §8 has the Implemented, Planned and Brief entries under 2026-10-11, newest first, linking the work folder; new entries avoid the A4 phrases. No status column describes these docs, so none changed. | R5, A5 met; records complete. |
| 5 | note | branch | `git diff main...ba-guide-docs --stat` touches only `PROJECT.md`, `docs/DATABASE.md`, `docs/RECIPE-ROADMAP.md` and `docs/work/ba-guide-docs/`. Three commits, one line each, no trailers. No secrets, no DB or code changes; §2, §3, §5, §6 of PROJECT.md untouched. | A6 met; scope and safety clean. |
