# Verification: m0-harness

Overall: ✅ all 12 checks and 122 tests pass (A7 with the stack stopped: 94 passed, 28 skipped, none failed). Re-verified after the Task 8 scope change, with the user's pin on `Recipe pipeline` present.

Date: 2026-10-12  ·  Branch: m0-harness at 6870022

## Part 1: Summary

🎯 **Goal:** Record the G0 decisions and build the test harness: a webhook pipeline in n8n that logs each step, contracts, graders and a runner; plus sample test data in the n8n editor.

🛠️ **How:** SQL run-log columns plus `pg_jsonschema`, 8 JSON Schema contracts, pure Python graders, 3 n8n workflows exported to the repo, an eval runner that reads `app.run` / `app.run_step` back, and a `Test data` sticky note with ready-to-paste JSON in each workflow.

🤔 **Why this way:** Everything is testable with the tools the repo already has (pytest, psycopg, Postgres), the database is the single record of a run, and pins stay in n8n so pinning needs no re-export.

🏁 **Result:** The runner sends 20 briefs through n8n; step 1 logs `ok = true`, grading is red (0/20) on purpose, the baseline is saved in `evals/results/2026-10-12-m0.json`; all three workflows carry a note, and 122 tests pass (94 without the stack).

### 🚦 Steps

- ⏭️ 📝 **Brief:** Skipped as a step: the brief was already on disk from an earlier session; the user approved it as written (10daee8). The scope change (R11/A9) was added later (02d308f).
- ✅ 🗺️ **Plan:** 7 tasks approved (8d171ea), then a revision adding Task 8 (02d308f). One fact correction recorded: `test_style_codes_exist_in_ref` failed with the stack down, so it was marked as a stack test.
- ⚠️ 🔨 **Implement:** 8 tasks plus one review-fix round (9db876d), all ticked.
  - ⚠️ Task 1: no failing-test-first for conftest; the skip path was checked by hand.
  - ⚠️ Task 2: `-m "not stack"` was not run.
  - ⚠️ Task 3: `test_examples` split into two tests (recorded as a deviation).
  - ⚠️ Task 5: `n8n/` is root-owned; `n8n/workflows/` was created with a one-off `docker run --user 0` on the n8n image.
  - ⚠️ Task 6: draft-vs-published was not measured (deferred to M1); `test_pipeline` tests not seen failing first; the webhook returns 200 even when `ok = false`.
  - ⚠️ Task 6 deviations: `$json.error` is a string, `Start run` returns `id::int`, `export_all` skips archived workflows, credential checked through a temporary archived workflow.
  - ⚠️ Task 7: b01 fails on `stated`, `hints` and `wanted`, not only `wanted`; `test_run` tests not seen failing first.
  - ⚠️ Task 8: `test_webhook_ignores_pin` passed from the start (meaningful only with a pin; now measured, see Part 3); `db/015_app.sql` comment changed but not re-applied; the re-export picked up editor defaults (dropped default params, added `binaryMode`).
  - ⚠️ Task 8 deviation: the pipeline sample's contract test builds the step 1 input from `body.request` plus `run_id` 0.
- ❌ 🔍 **Review:** Round 1: fixes needed (1 must-fix: runner tests did not catch a failed run counted as passed; 5 should-fix). 🔧 fixed in 9db876d. Round 2 (3328572) and round 3 for Task 8 (6870022): ready for testing.
  - ⚠️ Note #10: each half of the finished-and-ok check is covered only by the other half.
  - ⚠️ Note #11: the G0 baseline file lacks the step 1 `not_run` key.
  - ⚠️ Note #12: pin-dependent A9 parts were open until the user pinned; closed in this run (C10, C11, Part 3).
  - ⚠️ Note #13: the re-export dropped default parameters and added `binaryMode`; behaviour unchanged.
  - ⚠️ Note #14: the notes test takes `nodes[0]` as the trigger.
- ⚠️ 🧪 **Verify:** All acceptance criteria hold, including A7 with `n8n` and `supabase-pooler` stopped (both started again, healthy, healthz 200) and A9 with the user's pin present. 🧮 spot checks ✅ 12/12 · 🧪 tests ✅ 122/122
  - ⚠️ The user's pin save moved the `Test data` note 8 px and made `Recipe pipeline`'s draft differ from its published version; the repo file is not re-exported (names and connections still match).
  - ⚠️ A9's editor view (node and sub-execution input/output) is the user's check; I did not see it.

👀 **Start here:** Open `Recipe pipeline` in the n8n editor (pin already set) and run "Execute workflow": each node and the `Step 1 · read request` sub-execution show their input and output. From the terminal, `python -m evals.run --brief b01` prints one row: run `ok`, step 1 `fail: stated,hints,wanted`, steps 2 and 3 `not run`.

📁 **Changed files:**
- `PROJECT.md`
- `db/015_app.sql`
- `docs/DATABASE.md`
- `docs/OPERATIONS.md`
- `docs/WORKFLOW-ROADMAP.md`
- `docs/work/m0-harness/brief.md`
- `docs/work/m0-harness/plan.md`
- `docs/work/m0-harness/review.md`
- `docs/work/m0-harness/verification.md`
- `evals/__init__.py`
- `evals/grade.py`
- `evals/results/2026-10-12-m0.json`
- `evals/run.py`
- `evals/workflows.py`
- `loaders/db.py`
- `n8n/workflows/check-contract.json`
- `n8n/workflows/recipe-pipeline.json`
- `n8n/workflows/step-1-read-request.json`
- `pytest.ini`
- `shared/contracts/step0.input.schema.json`
- `shared/contracts/step0.output.schema.json`
- `shared/contracts/step1.input.schema.json`
- `shared/contracts/step1.output.schema.json`
- `shared/contracts/step2.input.schema.json`
- `shared/contracts/step2.output.schema.json`
- `shared/contracts/step3.input.schema.json`
- `shared/contracts/step3.output.schema.json`
- `tests/conftest.py`
- `tests/test_contracts.py`
- `tests/test_grade.py`
- `tests/test_pipeline.py`
- `tests/test_recipe_briefs.py`
- `tests/test_run.py`
- `tests/test_run_log.py`
- `tests/test_workflows.py`


## Part 2: Spot checks

### ✅ C1 · G0 decisions recorded with a why each (A1)

```bash
sed -n '/Pipeline build (G0/,/^$/p' PROJECT.md | grep -c "Why:"
```

| Expected | Actual | Result |
|---|---|---|
| 5 decisions, each with a *Why* | 5 bullets, each with an italic *Why* (checked by reading the block; the grep for "Why:" does not match the italic form) | ✅ pass |

### ✅ C2 · Runner on b01 creates a run and a step 1 row with ok = true (A2)

```bash
.venv/bin/python -m evals.run --brief b01; docker exec supabase-db psql -U postgres -d postgres -tAc "select r.id,r.eval_id,r.ok,r.finished_at is not null,s.step,s.try,s.ok from app.run r join app.run_step s on s.run_id=r.id where r.id=(select max(id) from app.run)"
```

| Expected | Actual | Result |
|---|---|---|
| one run, step 1 try 1 ok = true | `140\|b01\|t\|t\|1\|1\|t` (re-run this verification, with the user's pin on `Recipe pipeline` present); table row `b01 ok fail: stated,hints,wanted / not run / not run FAIL` | ✅ pass |

### ✅ C3 · Forced failure is logged and reported as failed (A3)

```bash
.venv/bin/python - <<'PY'   # run_brief on b01 with request ""
...
PY
docker exec supabase-db psql -U postgres -d postgres -tAc "select r.id,r.ok,s.ok,s.error from app.run r join app.run_step s on s.run_id=r.id where r.id=(select max(id) from app.run)"
```

| Expected | Actual | Result |
|---|---|---|
| passed = False; step row ok = false with error naming step1.input | `False False contract step1.input: "" is shorter than 1 character`; row `141\|f\|f\|contract step1.input: "" is shorter than 1 character` | ✅ pass |

### ✅ C4 · Contract files for steps 0-3 exist (A4)

```bash
ls shared/contracts | wc -l
```

| Expected | Actual | Result |
|---|---|---|
| 8 | 8 (absent slots are checked by `test_every_output_has_an_absent_slot`, see Part 3) | ✅ pass |

### ✅ C5 · Run-log schema: extension, columns, owner (Task 2)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select extname, extnamespace::regnamespace from pg_extension where extname='pg_jsonschema'; select column_name,is_nullable from information_schema.columns where table_schema='app' and ((table_name='run' and column_name in ('brief_id','eval_id','finished_at','ok')) or (table_name='run_step' and column_name='error')) order by 1; select distinct tableowner from pg_tables where schemaname='app'"
```

| Expected | Actual | Result |
|---|---|---|
| extension in `extensions`; 5 columns, all nullable; owner postgres | `pg_jsonschema\|extensions`; brief_id, error, eval_id, finished_at, ok all `YES`; `postgres` | ✅ pass |

### ✅ C6 · 20-brief baseline: 20 rows, step 1 red, totals, briefs 0/20 (A5)

```bash
python3 -c "import json;d=json.load(open('evals/results/2026-10-12-m0.json'));print(len(d['results']));print(json.dumps(d['totals']))"
```

| Expected | Actual | Result |
|---|---|---|
| 20 rows; step 1 0/20; briefs 0/20 | `20`; `step1 0/20, step2 0/20 (20 not run), step3 0/20 (20 not run), briefs 0/20` | ✅ pass |

Note: I did not re-run all 20 briefs (it would add 20 `app.run` rows); the saved file from the Task 7 run is what was read. The runner's exit code 1 for a red run was seen in C2 (exit=1).

### ✅ C7 · Every baseline run finished with a step 1 row ok = true, and 3 workflow files exist (Task 7, A8)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from app.run r where r.finished_at is null or not exists(select 1 from app.run_step s where s.run_id=r.id and s.step=1 and s.ok)"; ls n8n/workflows
```

| Expected | Actual | Result |
|---|---|---|
| 0 bad runs (measured before my C3 run existed; the C3 failure run was removed afterwards); 3 files | not re-run in this round (see C12); in the first round it was 1 while the C3 failure run existed, which is the expected failure; 3 files: check-contract, recipe-pipeline, step-1-read-request. After cleanup 21 rows remain (the 20 baseline runs plus 1 earlier b01 run). | ✅ pass |

### ✅ C8 · Containers healthy after the A7 stop/start

```bash
docker ps --format '{{.Names}} {{.Status}}' | grep -E 'n8n|pooler'; curl -s -o /dev/null -w "%{http_code}" localhost:5678/healthz
```

| Expected | Actual | Result |
|---|---|---|
| both Up, n8n healthz 200 | `n8n Up 25 seconds`, `supabase-pooler Up 25 seconds (healthy)`, `200` (after this round's stop/start) | ✅ pass |

### ✅ C9 · Each workflow has one `Test data` note with JSON, no secret (A9, R11)

```bash
.venv/bin/pytest -q tests/test_workflows.py -k "test_data"; grep -i -c -E "password|token|secret|authorization|cookie|api.?key" n8n/workflows/*.json
```

| Expected | Actual | Result |
|---|---|---|
| 6 tests pass (3 notes, 3 contract); 0 secret matches per file | 6 passed (`test_test_data_notes` ×3, `test_test_data_meets_contracts` ×3); `step-1-read-request.json:0`, `check-contract.json:0`, `recipe-pipeline.json:0` | ✅ pass |

### ✅ C10 · User's pin is on `Recipe pipeline` only; repo files match n8n (A8, A9)

```bash
.venv/bin/python -c "from evals.workflows import export_all; print({w['name']:list(w.get('pinData') or {}) for w in export_all()})"; .venv/bin/pytest -q tests/test_workflows.py::test_repo_files_match_n8n
```

| Expected | Actual | Result |
|---|---|---|
| Pin on `POST recipe-pipeline` only; names + connections of the 3 repo files equal n8n | `{'Recipe pipeline': ['POST recipe-pipeline'], 'Check contract': [], 'Step 1 · read request': []}`; `test_repo_files_match_n8n` passed. Pin holds 1 item: `body.request` = b01's request, `brief_id` `editor-b01`. | ✅ pass |

Note: the repo files do not equal `shape()` of a fresh export in full any more. `Recipe pipeline`'s `Test data` note position is `[0, 368]` in n8n and `[0, 360]` in the repo (the user moved it when pinning); nothing else differs, and `pinData` is not in the file, as intended. The pin save also made the draft differ from the published version again (`versionId` ≠ `activeVersionId` on `Recipe pipeline`; the other two are equal). The files were not re-exported (outside this verification); the A8 comparison (names and connections) holds.

### ✅ C11 · The user's editor run is logged with `eval_id = 'editor-b01'` and its step 1 row (A9)

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select id,eval_id,ok,finished_at is not null fin,(select count(*) from app.run_step s where s.run_id=r.id) steps from app.run r where eval_id like 'editor-%' order by id"
```

| Expected | Actual | Result |
|---|---|---|
| the user's editor run(s): finished, ok, one step 1 row | 1 row: run 129, `editor-b01`, `ok = t`, `fin = t`, 1 step (step 1, ok = true) | ✅ pass |

Run 129 belongs to the user and was left in place. The user's own check (each node's and the step 1 sub-execution's input and output are visible in the editor) is theirs; I have not seen the editor.

### ✅ C12 · My check runs removed; only the user's editor run and eval baseline remain

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "delete from app.run where id in (140,141) returning id; select count(*) from app.run where eval_id like 'editor-%'; select count(*) from app.run"
```

| Expected | Actual | Result |
|---|---|---|
| my 2 runs (C2, C3) deleted; 1 `editor-%` row; 23 rows total (21 eval runs + editor run + 1 other eval run already there) | `DELETE 2`; `1`; `23` | ✅ pass |

## Part 3: Regression tests

Command: `.venv/bin/pytest -q`  ·  Result: ✅ 122 passed (stack up, user's pin on `Recipe pipeline`)

**Pin state when `test_webhook_ignores_pin` ran: present.** `export_all()` showed `pinData` on `Recipe pipeline` node `POST recipe-pipeline` (1 item: `body.request` = b01's request, `brief_id` `editor-b01`) before and after the test runs; `Check contract` and `Step 1 · read request` have none. The test passed (posted `b02` request kept, `eval_id = 'b02'`), so the pin was ignored by the webhook.

A7, stack stopped (`docker stop n8n supabase-pooler`, then `.venv/bin/pytest -q`): ✅ 94 passed, 28 skipped, 0 failed. The skipped ones are the `stack`-marked tests. Also `.venv/bin/pytest -q -m "not stack"` with the stack up: ✅ 94 passed, 28 deselected. Both containers were started again with `docker start` (no recreate): `n8n Up`, `supabase-pooler Up (healthy)`, healthz 200.

| Test | Protects | Result |
|---|---|---|
| tests/test_run_log.py::test_failed_step_needs_error, ::test_passed_step_has_no_error | A failed step always records its error; a passed one never does | ✅ |
| tests/test_pipeline.py::test_bad_input_logs_failure | A bad step input stops the run with ok = false and the error | ✅ |
| tests/test_run.py::test_failed_run_is_reported_failed, ::test_runner_reports_bad_request_as_failed, ::test_unfinished_run_is_not_passed | The runner never reports a failed run as passed | ✅ |
| tests/test_pipeline.py::test_request_kept_verbatim | Request text reaches the log unchanged | ✅ |
| tests/test_pipeline.py::test_b01_logs_step_1 | Step 1 row matches the step 1 contract | ✅ |
| tests/test_contracts.py::test_good_examples, ::test_bad_examples, ::test_every_output_has_an_absent_slot | Contracts accept the absent slot and reject bad values | ✅ |
| tests/test_grade.py::test_same_kind_other_subject_does_not_match, ::test_other_kind_same_subject_does_not_match | Deviation match = same kind and same subject | ✅ |
| tests/test_grade.py::test_step2_alternative_style_passes | An alternative style counts as a pass | ✅ |
| tests/test_grade.py::test_step1_missing_output_fails_every_field | A missing step output fails every graded field | ✅ |
| tests/test_workflows.py::test_repo_files_match_n8n | Repo workflow files match n8n (A8) | ✅ |
| tests/conftest.py skip logic | The default suite passes without the stack (A7) | ✅ |
| tests/test_pipeline.py::test_webhook_ignores_pin | A webhook call runs on the posted request, never on the pinned sample (measured with the pin present) | ✅ |
| tests/test_workflows.py::test_test_data_notes (×3), ::test_test_data_meets_contracts (×3) | Each note holds a sample its trigger accepts, with the b01 request, `editor-b01`, no secret header | ✅ |
| tests/test_workflows.py::test_shape_drops_volatile_fields | A user's pin never changes the repo files | ✅ |

Failures: none.
