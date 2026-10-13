# Review: m1-read-request

Diff: main...m1-read-request at 51deac9  ·  Verdict: ready for testing

Checked: the full branch diff (9 commits, all one-line subjects without body or trailer) against
brief.md R1–R9 / A1–A8 and plan.md Tasks 1–7 and Deviations. Live checks on the stack (2026-10-13):
`db/015_app.sql` + `db/020_step1.sql` re-applied inside `begin … rollback` with
`ON_ERROR_STOP=1`: clean (idempotent); catalog: `app.brief.profile_id` nullable, `app.run_step.llm`
jsonb, `app.step1_read_answer` owned by `postgres`. `pytest -m "not stack"`: 112 passed;
`tests/test_step1_check.py` + `tests/test_workflows.py` (stack): 16 passed. Results file: 7
configurations, `all_right` and split match `benchmark.md`; its prompt and contract sha256 equal
the repo files now. No secrets in the diff; the `Ask model` HTTP nodes need no credential (local
Ollama), the Postgres nodes reuse the existing credential id.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | evals/benchmark.py:175 | `--save` writes one top-level `prompt_sha256` / `contract_sha256` and overwrites it on every save; configurations carry no hash of their own. A prompt or contract change between two configurations would go unnoticed, and the file cannot show that the three 2026-10-12 configurations (merged in, Task 6 deviation) used the same files. | Plan Task 6 asks that "all configurations must show the same prompt and contract hash". Today this rests on the manual check stated in `benchmark.md`, not on the saved data. Storing the hashes per configuration (or refusing to merge on a mismatch) would make it checkable. The current results are not affected as far as can be checked. |
| 2 | should-fix | docs/DATABASE.md:406 | The new `Function app.step1_read_answer …` paragraph ends with a stray ` \|`, left over from the table row it was split from. | It renders as a literal pipe after the sentence. Harmless. |
| 3 | should-fix | PROJECT.md:118 | §4 Delivery workflow row still says `m1-read-request` "(plan drafted 2026-10-12)"; the work is implemented and in review. | Check 8: a status column this work touches is stale (CLAUDE.md asks that PROJECT.md facts be current). |
| 4 | note | db/020_step1.sql:53 | The R3 number check fails closed on number forms the regex does not read as written: measured "1,000 litres" → `batch_l = 1000 is not a number in the request` (the comma is read as a decimal point, 1.000), and ".5" → `abv = 0.5` refused. The header comment names number words and unit conversions only. | Such a request ends with `ok = false` after the retry rather than a wrong brief, so R3 holds. Rare for home-brew sizes; the user decides whether it needs handling. |
| 5 | note | n8n/workflows/recipe-pipeline.json:301 | `Step 1 · save brief` runs after `Step 1 · log ok` and has no error output; if the insert fails, the run stays with `finished_at` null and the webhook gets an n8n error, not `Respond failed`. | Same pattern as m0's `log ok` / `Finish run` nodes; the runner already counts an unfinished run as failed (`run not finished ok`). No action needed now. |
| 6 | note | tests/ (A4) | The "two failed answers end the run with `ok = false`" behaviour is tested only through the MCP `test_workflow` executions 2820 / 2823 (recorded in Deviations), not by a repeatable pytest. The R3 part is in `test_made_up_number_fails`, and the pipeline's failure path in `test_bad_input_logs_failure`. | As planned (Critical behaviour table). A later change to the retry chain would not be caught by `pytest`. |
| 7 | note | app.run / app.brief (live DB) | 505 `app.run` and 482 `app.brief` rows: m0's 23 runs plus about 480 from this work (smoke 40, dry run 20, benchmark 7 × 3 × 20 = 420), not about 60. | The benchmark rows back the `run_id`s in `evals/results/2026-10-13-m1-benchmark.json`; deleting them would break that link. 0 orphan briefs; every run with a brief links to one. |

Plan and brief: every task is done as written or recorded under Deviations (Execute Workflow
publish order, retry executions, `test_request_kept_verbatim` input, smoke-pass prompt changes,
`validate_workflow` on an SDK rendering, merged results file). Task 3's choice to edit the
`create table` text and add the two `alter` statements at the end of `db/015_app.sql` (no new
migration file) is what the plan said, applies cleanly to the live DB and to a fresh one. A1
(19/20 in 3 of 3 runs on the chosen model), A2 (per-configuration table), A6 (seven rows, §4 names
the model, D2 gone from §7) and A7/A8 (tests) are met in the files; A3 and A5 are stack tests in
`tests/test_pipeline.py` that dev-verify runs. No change outside the plan's Files table, apart
from the `Test data` sticky note in `recipe-pipeline.json` moving 8 px.
