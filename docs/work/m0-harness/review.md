# Review: m0-harness

Diff: main...m0-harness at 23cd856  ·  Verdict: fixes needed

Checked: the full diff against brief R1–R10 / A1–A8 and plan Tasks 1–7. Measured on 2026-10-12:
`pytest` gives 113 passed with the stack up, and `pytest -m "not stack"` gives 89 passed, 24
deselected. In n8n (MCP `get_workflow_details`, read-only), all three workflows have
`versionId == activeVersionId`, so the published versions are the drafts that were exported, and
their node names and connections match the repo files. Commits are one line each with no
trailers. No secrets in the diff: the workflow files carry only the credential id and name. The
DB change is in `db/015_app.sql`.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | must-fix | tests/test_run.py:34, :42; evals/run.py:74 | Neither test covering "the runner never reports a failed run as passed" fails when that guard is removed. Both build runs that have no passed step outputs, so `grade_run` already gives `passed = False`, whatever `run_ok` is. Measured: with `"passed": run_ok and graded["passed"]` mutated to `graded["passed"]`, `tests/test_run.py` still passes (2 passed). The `finished`/`ok` check in `run_brief`, which reads the stored run, has no test either. `test_failed_run_is_reported_failed` also ends with an `or` assertion that the table always meets. | This is a Critical-behaviour row in the plan. Once M1–M3 produce outputs that grade green, a crashed or unfinished run that has good step rows could be counted as passed, and no test would catch it. A test needs step outputs that grade as a pass together with `run_ok = False` (and a `read_run` result with `finished = False`). |
| 2 | should-fix | plan.md Task 6 | The ticked item "confirm in an execution which version the *Execute Workflow* node runs" was not done (implementer note), and there is no Deviations line. OPERATIONS §5 now states, unmeasured, that "a sub-workflow edit needs `publish_workflow` too". | It is harmless today, because draft = published for all three workflows (measured above). `test_repo_files_match_n8n` compares only the exported draft, so it would not notice a sub-workflow left unpublished after an edit in M1. Record it as a deviation, and either measure it or mark the OPERATIONS line as unverified. |
| 3 | should-fix | plan.md Deviations | Three other differences are not recorded: (a) Task 3 `test_examples` became two parametrized tests, `test_good_examples` and `test_bad_examples`; (b) Task 7 expected b01 to be "red on `wanted`", but it fails on `stated`, `hints` and `wanted`, because b01 states `batch_l` and `abv` and the stub returns `stated: {}`; (c) Task 6 `test_b01_logs_step_1` posts `"a pale ale"` and not b01's request. | conventions.md requires a dated Deviations line for every difference. None of the three changes what the work does. |
| 4 | should-fix | evals/run.py:116 | `totals()` gives step 1 only `passed`/`total`, with no `not_run` count. The plan says "per graded step, passed / total, and how many were not run", and step 1 is graded. | Harmless now, because every M0 run has a step 1 row. When step 1 fails at its input check (A3), the totals can't tell "graded wrong" from "never produced output". |
| 5 | should-fix | tests/conftest.py:9, :17–26 | The plan said to use `loaders.db.connect()` (with an optional `connect_timeout` argument added if needed). Instead, conftest copies `connect()`'s arguments and imports the private `_read_env`. A missing `.env`, or a missing key in it, raises `FileNotFoundError` / `KeyError`, which is not caught, so collection errors instead of skipping. | The two copies can drift apart, and then the skip check would test a different connection from the one the tests use. A checkout without `.env` fails the default `pytest` run rather than skipping the stack tests (R9). |
| 6 | should-fix | PROJECT.md:116 (§4 Scripts row) | The status column still reads "68 tests pass (measured 2026-10-11; the style-code test … needs the running DB)". The suite is now 113 tests, and that test is skipped, not failed, when the stack is down. | CLAUDE.md requires measured status columns. The row now describes the state before this work. |
| 7 | note | n8n/workflows/recipe-pipeline.json ("Step 1 · log ok", "Step 1 · log failure") | If a node after the step call fails (the log insert, `Finish run`), or `$json.error` is ever undefined (the `run_step_error_check` constraint then rejects the failure row), the workflow errors with no `run_step` row. The run keeps `finished_at = null`, and no Respond node runs. | The runner still reports the brief as failed ("run not finished ok"), so nothing passes silently. But the reason is only in the n8n execution log, not in `app.run_step`. An n8n error workflow could be considered when steps get real logic. |
| 8 | note | evals/workflows.py:31, :55 | `read_text()` / `write_text()` are called without `encoding="utf-8"`, while the files contain non-ASCII ("·") because of `ensure_ascii=False`. | This works under the current UTF-8 locale and breaks only under a non-UTF-8 one. |
| 9 | note | evals/grade.py `subject_key` | For `number`/`mismatch`, a subject that names two quantities resolves to the first in `QUANTITIES` order. For `conflict`, two texts with no hint words both give an empty frozenset and therefore match. | No brief in `recipe_briefs.toml` hits either case (checked: all 9 expected deviations resolve to the intended key). This is worth knowing when M3 output is graded. |

## Re-review 2026-10-12

Diff: 92e457f..9db876d (fix round 1)  ·  Verdict: ready for testing

Checked: findings 1–6 against the fix commit, and the fix diff for new problems. Measured on
2026-10-12: `pytest` gives 115 passed with the stack up, and `pytest -m "not stack"` gives
91 passed, 24 deselected, which matches the new PROJECT.md §4 row. The fix commit is one line
with no trailers, and it touches only files that belong to this work (`loaders/db.py` gets the
optional `connect_timeout` that plan Task 2 allowed). No workflow, SQL or secret changes.

| # | Earlier finding | Status | Evidence |
|---|---|---|---|
| 1 | runner guard untested | resolved | Mutation, measured: with `"passed": run_ok and graded["passed"]` changed to `graded["passed"]`, 2 tests in `tests/test_run.py` fail. With the `stored["finished"] and stored["ok"]` check removed (`if False:`), `test_unfinished_run_is_not_passed` fails. The `or` assertion is now an `and` on the last table row. `evals/run.py` was restored afterwards (`git status` clean). |
| 2 | Execute Workflow version not confirmed | resolved | Deviations line added (Task 6), and OPERATIONS §5 marks the "publish sub-workflows too" advice as unverified, with measurement deferred to M1. |
| 3 | unrecorded differences (a)–(c) | resolved | Three dated Deviations lines in plan.md cover `test_good_examples`/`test_bad_examples`, `test_b01_logs_step_1` posting "a pale ale", and b01 red on `stated`, `hints` and `wanted`. |
| 4 | step 1 has no `not_run` | resolved | `totals()` gives step 1 `not_run`, `format_totals()` prints it for all three steps, and `test_not_run_steps_count_as_failed` asserts it. |
| 5 | conftest copies `connect()` | resolved | `stack_down_reason()` calls `loaders.db.connect(connect_timeout=3)` and catches `OSError`/`KeyError` too. Measured with `ENV_FILE` pointed at a missing file and at a file with only one key: both return `"Postgres"` (skip), and neither raises. Callers of `connect()` with no argument still work (stack tests pass). |
| 6 | stale §4 Scripts row | resolved | The row now gives the measured counts above, and says that stack tests are skipped when the stack is down. A §8 entry for the fixes was added. |

New in the fix diff:

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 10 | note | tests/test_run.py `test_unfinished_run_is_not_passed`; evals/run.py:85 | The test stubs `read_run` with `finished: False, ok: False`, so each half of the check is covered only by the other. Measured: with the check reduced to `if not stored["ok"]:` or to `if not stored["finished"]:`, all `tests/test_run.py` tests still pass. | Removing the whole check is caught (finding 1). A mistake in one half could be missed, for example a run that finished as failed while the HTTP answer said `ok`. A second stub (`finished: True, ok: False`) would cover it. |
| 11 | note | evals/results/2026-10-12-m0.json | The saved G0 baseline was written before the fix, so its `totals.step1` has no `not_run` key (the runs there all have a step 1 row, so the value would be 0). | Nothing reads the results files back today (`grep` checked). A later comparison script would need to allow for the missing key, or the baseline could be re-saved. |

## Re-review 2026-10-12 (Task 8 scope change)

Diff: 29b132b..61e5cd2 (plan revision 02d308f, implementation 61e5cd2)  ·  Verdict: ready for testing

Checked: the brief/plan revision against the user's request (sticky notes with ready-to-paste
JSON, the user pins), R11 and A9 against plan Task 8, the implementation against Task 8, and
the earlier reviewed work for regressions. Measured on 2026-10-12:

- `pytest` gives 122 passed with the stack up; `pytest -m "not stack"` gives 94 passed,
  28 deselected. Both match the PROJECT.md §4 row and the plan's expectation (115 + 7).
- n8n (MCP `get_workflow_details`, read-only): all three workflows have
  `versionId == activeVersionId`, the draft and active node lists are the same, and each has one
  `Test data` sticky note with the JSON from the plan's sample table. Connections are unchanged.
- The repo files equal `shape()` of a fresh `export_all()` in full (not only node names and
  connections). `pinData` is `{}` for all three, so the user has not pinned yet.
- No `app.run` row has an `eval_id` like `editor-%` (the implementer's editor-b01 run was removed).
  `grep -i -E "password|token|secret|authorization|cookie|api.?key"` on the three workflow files
  finds nothing.
- Revision: brief scope item, R11, A9 and a Deviations line, and plan Task 8, Files table,
  Critical-behaviour rows and Deviations line all say the same thing, and match the user's
  choice (notes only, the user pins). The approved A7 exception is now recorded under Approved
  exceptions. Both commits are one line with no trailers, and they touch only files in the
  plan's Files table and this work's docs. `db/015_app.sql` changes a `--` comment only, so
  there is nothing to apply.
- Tests: `test_test_data_notes` fails if a note is missing, duplicated, holds a different sample,
  or a sub-workflow's input names drift from the sample. `test_webhook_ignores_pin` asserts both
  `eval_id = 'b02'` and the posted request, which a pinned b01 sample would break. The pipeline
  contract check builds the step 1 input from `body.request` + `run_id: 0`; that deviation is
  recorded and correct, because `step1.input` has `additionalProperties: false` and `brief_id`
  is not part of it.
- Earlier findings 1–6 stay resolved. OPERATIONS §5's "unverified" note about which version
  Execute Workflow runs still holds (draft = active again).

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 12 | note | A9; tests/test_pipeline.py `test_webhook_ignores_pin` | The A9 parts that depend on the pin are not met yet: no workflow has `pinData` (measured), so the test passes without testing anything, and the user's editor check has not happened. The plan's "For re-verify" paragraph covers this: the user pins and runs the pipeline sample, and verification then runs the suite with the pin present. | If verification ran before the user pins, A9 would look covered when it is not. |
| 13 | note | n8n/workflows/*.json | The re-export dropped parameters whose values are n8n defaults (webhook `authentication: none`, trigger `inputSource`, the `string` input type, `operation: read`, `binaryPropertyName: data`, `errorType`, Set `mode: manual`, Execute Workflow `source` / `mode`) and added `settings.binaryMode: "separate"`. Runtime behaviour is unchanged: the files equal the live export and the suite passes. | Someone reading the files no longer sees some settings spelled out, for example that the webhook has no auth. That fact is in OPERATIONS and the n8n MCP trigger info. |
| 14 | note | tests/test_workflows.py:52 | `test_test_data_notes` treats `nodes[0]` as the trigger. That holds in all three files today (checked). If the node order changed, the test would fail with a `KeyError` rather than pass by mistake. | No silent gap. It is only a less clear failure message. |
