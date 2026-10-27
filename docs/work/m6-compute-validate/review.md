# Review: m6-compute-validate

Diff: main...m6-compute-validate at e74e702  ·  Verdict: fixes needed

Checked: `git diff main...m6-compute-validate` (59 files), `git log --oneline main..m6-compute-validate`
(18 one-line commits), brief R1–R11 / A1–A12, plan Tasks 1–11 and Deviations. Ran the task's test
files with the stack up (`tests/test_compute.py test_validate.py test_save_recipe.py
test_recipe_tables.py test_reference_recipes.py test_run.py test_grade.py test_choose_table.py
test_contracts.py`): 345 passed in 71 s. I also replayed b15's logged try 1 (run 4517) through
`app.step10_compute` and `app.step11_validate` in a read-only transaction. `tests/test_pipeline.py`
was not run.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | must-fix | tests/test_compute.py:566-571 | Task 10b's rounding tests are not in the committed file. `grist_of`'s body was replaced by the last four lines of another test: it calls itself (`grist = grist_of(conn, out, 1.013)`) and reads undefined `inp` and `recipe`. Nothing calls it, so pytest still collects the file and it passes. Missing: `test_floor_is_one_step`, `test_rounding_keeps_og`, `test_rounding_keeps_rule_4`, `test_rounding_reports_unreached`, `test_rounding_adds_no_failure_it_did_not_cause` and the real `grist_of`. `compute_logged` and `logged_input` (for the b16/b22 m6-9b cases) have no caller left. This is in commit 9f8b4cc as committed, not a working-tree change. | The plan's critical-behaviour table (plan.md:965-966) names these tests for "never 0" and "rounding never adds a failure when a grist on the steps avoids it, and says so when none does". The down-or-up search in `app.step10_round_grist` and its `added` report are the main logic of Task 10b, and no test checks them now (only `test_rounding_failure_says_rounding` in step 11 touches `added`). PROJECT.md §8's "342 passed" for Task 10b counts a file without them. |
| 2 | should-fix | db/047_validate.sql:98-106 (`app.step11_fix`) | When SRM is too dark and the grist has a crystal, the fix always says "lower the crystal share … the colour adjustment never moves a crystal". It does not check that the movers stopped at a limit, which the Task 9c case requires ("too dark, the movers at their limits", plan.md:720). The read-only replay of b15 (run 4517 try 1, `colour.reached` true) gave: "… It comes from rounding to weighing steps … To fix: lower the crystal share (Crystal T50 10 %)". The real cause is Black Malt's 50 g floor in 23 L. `step11_fix` also reads `step10.colour.grist` and `og_used` from before rounding, so its figures describe the exact grist and not the rounded recipe that failed. | b15 is the brief the rounding newly fails, and b01–b20 sits exactly on A1's bar (16). On the real pipeline its retry would be told to change something that does not fix the miss. The bar's "unverified on real retries" depends on this line. |
| 3 | should-fix | plan.md:1010, PROJECT.md:258 | Three tests in `tests/test_pipeline.py` no longer assert a whole-run `ok`: `test_guide_setting_reaches_step_2` and `test_request_kept_verbatim` (Task 8), and `test_webhook_ignores_pin` (Task 11). Only the Task 11 one has a Deviations line. Task 8's two appear in PROJECT.md §8 only. The full suite was measured as 1215 passed / 1 failed before the last edit, and the edited test was re-run on its own; the whole suite has not passed in one run. | Records rule (conventions "Changes to the plan"). Verification needs one full green run after the last test edit. |
| 4 | note | db/046_compute.sql:897-900 | The `values_used` colour line is built from `items` after `app.solve_colour`. By then a null EBC has already been replaced with 0, so the "no colour, counted as 0" branch never runs. Logged outputs say "Lactose 0" and "Honey 0" (runs for b19 and b20). `srm_lower_bound` still names them correctly. | R1 asks that the values used be named. The line is still true, but a reader cannot see that the 0 is a stand-in. |
| 5 | note | db/046_compute.sql:52, 299-300 | The colour solver's 1 SRM aim and `app.step10_og_move`'s OG 0.002 and ABV 0.2 are constants of their own. They are not read from `app.recipe_tolerances()`, and only the harness and SQL tolerances are tested equal. The SRM aim is tighter than the step 11 tolerance on purpose (plan Approach). | If the OG or ABV tolerance changes, it has to be changed in two places in SQL. |
| 6 | note | evals/results/2026-10-27-m6-10b-revalidate.json, PROJECT.md §8 | A1 and A12 after rounding are measured by re-validating the saved m6-9b picks (16 of b01–b20, no margin), not by a pipeline run, as the plan says. The 20 recipes saved in m6-9b are unrounded. The only real run on the rounded code is `test_b01_validates_and_saves`. A3 is not fully met: b18's stated SRM and b19's batch run did not validate, and both were accepted as known failures by the user on 2026-10-26. | Matches the user's decisions; verification should report it as is. |
| 7 | note | plan.md:257 | The Files table names `n8n/workflows/steps-10-11-compute-validate.json`. The committed file is `steps-10-11-compute-and-validate.json`. | Records only. |
| 8 | note | tests/fixtures/reference_recipes.toml (b23) | The implementer flagged b23's reference grist as different from the plan. Plan Task 2 names no grist, only "20B base with Coffee, whole beans and Vanilla bean" and the extras' grams, and the fixture matches that. No deviation line is needed. | None. |
| 9 | note | Tasks 3, 5 | The implementers report writing code before tests and checking the tests by breaking the code, instead of "see each fail first". The tests present for those tasks do assert the critical behaviour (colour moves only the darkest non-crystal and a base; each failure kind; only self-picks banned; the impossible target never passes). | Process only; the coverage is in place. |

Checked and found as planned: `db/045` (kind, nullable level, paired check), `db/048` (one function, refuses a failed
step 11 or a run without a brief, `packaging` saved as `package`), `app.solve_colour` (the second pass holds the
fermentable that stopped the first, rule 3/5 caps never force a share down, a crystal never moves), the mash move
(only up, inside the knee and 69 °C, never a hint's, the OG move made again), `app.step10_round_hops`, the
three-try pipeline with no loop-back edge, bans carried to later tries, `Respond failed (3 tries)` with each try's
lines, harness calls (all tries, first-try, retry) and tolerances read from saved rows. Column scales
(`abv numeric(4,1)`, `pct numeric(5,2)`, `amount numeric(10,3)`) cannot flip a stated-number verdict for a recipe step
11 passed. No secrets in the diff. All DB changes are `.sql` files. Commits are one line each. PROJECT.md §2, §3 and §6
are unchanged.

## Re-review 2026-10-27

Diff: 516dce8..m6-compute-validate at e7888d6 (c12c97b, 90536eb, e7888d6)  ·  Verdict: ready for testing

Checked: `git diff 516dce8..HEAD` (5 files), the three commits (one line each, no body), `app.step11_fix` in
full against `app.solve_colour`'s `reached`, `app.step10_round_grist`'s `added` keys and step 10's output
fields, and the restored tests against the helpers they call. Ran `tests/test_compute.py tests/test_validate.py`
with the stack up: 104 passed in 33 s, nothing skipped (so run 4517 is present and
`test_fix_names_rounding_not_crystal` ran). The `evals.revalidate` figures in PROJECT.md (16 of b01-b20, 19
overall) were not re-measured here. The full-suite run is left to dev-verify, as decided.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | fixed | tests/test_compute.py:566-690 | `grist_of` is a real helper again (`app.solve_grist` on ref items with fermentability), and the five tests the plan names are back: `test_floor_is_one_step` (Black Malt 4 g to 50 g, vanilla 0.4 g to 1 g, a 0.3 g hop to 1 g), `test_rounding_keeps_og` (b16, exact kg per item and `off_nearest`), `test_rounding_keeps_rule_4` (b22, Caraamber 400 g, rule 4 passes on the shaped recipe), `test_rounding_reports_unreached` (`reached` false, nearest steps, `because` names SRM) and `test_rounding_adds_no_failure_it_did_not_cause` (rule 8 not blamed). Each first proves the exact grist passes or fails as claimed, so the asserts would fail if the down-or-up search or `added` broke. `compute_logged`/`logged_input` have callers again. | Closes round 1's must-fix. |
| 2 | fixed | db/047_validate.sql:97-116 | Too dark now gives a fix only when `step10.colour.reached` is false (the first or second pass's final `reached`, db/046:209, 223); a miss in `step10.rounding.added` ("numbers srm", the one key `step10_grist_failures` uses for target and stated SRM) gives none, matching the implementer's choice. Shares and OG come from the rounded `step10.fermentables` (joined to the solver's facts by `ingredient_id`) and `numbers.og`; the too-light branch keeps the solver's grist for the rule 3 room, which is where the mover stopped. `test_fix_crystal_only_when_the_movers_stopped` flips `reached` and `added` and expects null for each; `test_fix_names_rounding_not_crystal` replays run 4517 try 1 and finds the rounding sentence with no "crystal" and no "To fix". Both would fail on the old function. | Closes round 1's should-fix 2. |
| 3 | fixed | plan.md:1011, PROJECT.md:246 | Task 8's two relaxed `ok` assertions have their Deviations line; PROJECT.md §8 has a dated entry for the fixes and says the full suite has not run in one go. | Closes round 1's should-fix 3 (the full run is dev-verify's). |
| 4 | note | db/047_validate.sql:162-165 | In the too-light rule 3 sentence ("lower <crystal> to make room") the crystal shares printed come from the solver's grist (`cgrist`), so they are the exact shares, not the rounded ones. plan.md:1012 says the shares in every fix are the rounded recipe's. The cap check itself rightly uses the solver's grist. | The retry may see e.g. 9.5 % where the recipe has 9.47 %; harmless, and `test_fix_numbers_come_from_sql` allows both. |
| 5 | note | plan.md:712-736, 865 | The Task 9c and 10b task text was not edited with the fix: 10b still says "`app.step11_fix` is unchanged", and the 9c cases do not say that a reached colour or a rounding-added miss gives no fix, or that N uses the rounded OG ("at the OG used"). The Deviations line at plan.md:1012 records all of it. | Records only: conventions ask for the task text to describe the current plan as well. |

No new findings in correctness, scope, safety or tests beyond notes 4 and 5. Commits are one line each, the DB change
is in the `.sql` file, no secrets in the diff.
