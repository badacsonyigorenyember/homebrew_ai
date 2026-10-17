# Review: m4-targets-blueprint

Diff: main...m4-targets-blueprint at 9e358fe  ·  Verdict: ready for testing

Checked: the full diff (39 files, 11 commits) against brief R1–R13 / A1–A13 and plan Tasks 1–9
with their Deviations. Ran `.venv/bin/pytest` on `test_step0/3/4/5`, `test_formulation_check`,
`test_formulation_rules`, `test_reference_recipes`, `test_contracts`, `test_grade`, `test_run`:
212 passed (72 s, 2026-10-17). Pipeline tests not run (dev-verify's job). The grader tests were
checked by in-memory mutation of `evals/grade.py` (the repo file was not changed).

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | evals/grade.py:227, :243, :249, :272; tests/test_grade.py | Four grader checks can be broken with all 32 `test_grade.py` tests still passing. Measured by mutation: (a) dropping `and abv_stated` from the derived-OG/FG skip, so a derived OG outside its range passes with no stated ABV; (b) removing the `app.abv`-agreement check (`facts["abv"]` vs the ABV target); (c) removing the ABV-in-range check; (d) `return True` in place of `_every_from_set(output)`; (e) removing the rules-equality check in `grade_step5`. Deleting the whole skip, the mash check and the conflict check were each caught. | These are the grader's A1, A5, A10 and A8 checks for G4. A grader made laxer by mistake would still report 22/22. The SQL-level tests cover the same behaviour in the SQL, so the G4 result itself is not wrong today. |
| 2 | should-fix | PROJECT.md:250 | The Task 5 §8 entry says "ABV of 18 recipes". The fixture diff shows 17 (22 minus the 5 with a stated ABV: b01, b05, b14, b17, b21). It also leaves out b06's SRM change from 2.8 to 2.75. | CLAUDE.md asks for measured facts in PROJECT.md. The entry is wrong about which targets changed. |
| 3 | note | db/039_step4.sql:288 | `knobs` lists every `app.hint_moves` row, including an OG knob that a stated ABV replaced. b14 (`session`, ABV 3) gets `{"knob": "og", "direction": -1}`, but its OG is `derived` (1.0278, solved for the ABV) and not at the session position. b21 (`hoppy`, `session`, ABV 4) is the same. | The OG target's own `from: derived` and its `because` are right (R12). Only a reader of `knobs` alone, such as M8's sheet, would think the session move was applied. |
| 4 | note | evals/grade.py:215 | `grade_step4` expects 20 L when no batch is stated. That is a constant, not the profile's `batch_l`. | It matches the `default` row today. It would fail every unstated-batch brief if that row changes. |
| 5 | note | docs/work/m4-targets-blueprint/hint-sources.md:16 | The full/chewy `attenuation` intent says "a lower-attenuation yeast; oats or dextrin malt". The cited BJCP p77 passage only covers the yeast. Unlike dry's "sugar at most 10 %", the file has no note saying the oats/dextrin part has no passage. | A12 is met (the row has a source). The record overstates what the source covers. |
| 6 | note | db/032_formulation_check.sql:7 | Rule 9 now needs `db/039`, a higher-numbered file. On a fresh database applied in numeric order, `app.check_recipe` raises until 039 is applied. The apply itself succeeds, because plpgsql does not resolve the call at create time. | Ordering only. Today's stack has both files applied (tests pass). |
| 7 | note | — | Implementer flags checked. **Bru'n Water quote:** found verbatim at `shared/rag-files/water/brunwater_water_knowledge.md:294` under "4.2.1 Dilution", and in `kb.chunk` (slug `brunwater-water-knowledge`, section path …4.2.1 Dilution). **Migration 040:** `db/040_kb_search.sql` is on `main` (commit d3a734c), so it is not a gap or a clash. **Hint sources:** all 8 cited slug/page pairs exist in `kb.chunk` with the quoted passages. **Task 5 count at 810:** expected, because the new A11 cases were added inside the existing `test_rule_9`. The old rule 9 would fail the bitter IBU 26.375 case and the 15A ABV 3.81 case, so the new cases do tell the old and new rule apart. **Tasks 3 and 8:** their tests call functions and pipeline steps that did not exist before, so they could not have passed on the old code. **Task 7 derived-OG skip:** deleting the skip is caught by `test_step4_stated_abv_og_outside_passes`; widening it is not (finding 1a). | — |

Plan and brief: every task is done as written or recorded under Deviations (the quoted
`"position"`, `app.step4_pick`, `hint_list`, `app.step5_refs_of_id`, the file-route import of the
three workflows, `tests/step45_sample.json`). A1–A13 are each covered by a named test or by the
saved G4 run (`evals/results/2026-10-17-m4.json`: 22/22 on every step). No scope creep found. DB
changes are `.sql` files, and the workflow files carry only credential references. Commits are
one line each, with no body or trailer.
