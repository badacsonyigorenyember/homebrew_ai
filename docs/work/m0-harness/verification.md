# Verification: m0-harness

Overall: ✅ all 8 checks and 115 tests pass (A7 with the stack stopped: 91 passed, 24 skipped, none failed)

Date: 2026-10-12  ·  Branch: m0-harness at 3328572

## Part 1: Summary

🎯 **Goal:** Record the G0 decisions and build the test harness: a webhook pipeline in n8n that logs each step, contracts, graders and a runner.

🛠️ **How:** SQL run-log columns plus `pg_jsonschema`, 8 JSON Schema contracts, pure Python graders, 3 n8n workflows exported to the repo, and an eval runner that reads `app.run` / `app.run_step` back.

🤔 **Why this way:** Everything is testable with the tools the repo already has (pytest, psycopg, Postgres), and the database is the single record of a run.

🏁 **Result:** The runner sends 20 briefs through n8n; step 1 logs `ok = true` for each, grading is red (0/20) on purpose, the baseline is saved in `evals/results/2026-10-12-m0.json`, and 115 tests pass (91 without the stack).

### 🚦 Steps

- ⏭️ 📝 **Brief:** Skipped as a step: the brief was already on disk from an earlier session; the user approved it as written (10daee8).
- ✅ 🗺️ **Plan:** 7 tasks, approved. One fact correction recorded: `test_style_codes_exist_in_ref` failed with the stack down, so it was marked as a stack test.
- ⚠️ 🔨 **Implement:** 7 tasks plus one review-fix round (9db876d), all ticked.
  - ⚠️ Task 1: no failing-test-first for conftest; the skip path was checked by hand.
  - ⚠️ Task 2: `-m "not stack"` was not run.
  - ⚠️ Task 3: `test_examples` split into two tests (later recorded as a deviation).
  - ⚠️ Task 5: `n8n/` is root-owned; `n8n/workflows/` was created with a one-off `docker run --user 0` on the n8n image.
  - ⚠️ Task 6: draft-vs-published was not measured (deferred to M1); `test_pipeline` tests not seen failing first; the webhook returns 200 even when `ok = false`.
  - ⚠️ Task 6 deviations: `$json.error` is a string, `Start run` returns `id::int`, `export_all` skips archived workflows, credential checked through a temporary archived workflow.
  - ⚠️ Task 7: b01 fails on `stated`, `hints` and `wanted`, not only `wanted`; `test_run` tests not seen failing first.
- ❌ 🔍 **Review:** Round 1: fixes needed (1 must-fix: runner tests did not catch a failed run counted as passed; 5 should-fix). 🔧 fixed in 9db876d. Round 2 (3328572): ready for testing, with notes #10 and #11.
  - ⚠️ Note #10: each half of the finished-and-ok check is covered only by the other half.
  - ⚠️ Note #11: the G0 baseline file lacks the step 1 `not_run` key.
- ✅ 🧪 **Verify:** All acceptance criteria hold, including A7 with `n8n` and `supabase-pooler` stopped; both were started again and are healthy. 🧮 spot checks ✅ 8/8 · 🧪 tests ✅ 115/115

👀 **Start here:** `python -m evals.run --brief b01` prints one row: run `ok`, step 1 `fail: stated,hints,wanted`, steps 2 and 3 `not run`.

📁 **Changed files:**
- `PROJECT.md`
- `db/015_app.sql`
- `docs/DATABASE.md`
- `docs/OPERATIONS.md`
- `docs/WORKFLOW-ROADMAP.md`
- `docs/work/m0-harness/brief.md`
- `docs/work/m0-harness/plan.md`
- `docs/work/m0-harness/review.md`
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
| one run, step 1 try 1 ok = true | `83\|b01\|t\|t\|1\|1\|t`; table row `b01 ok fail: stated,hints,wanted / not run / not run FAIL` | ✅ pass |

### ✅ C3 · Forced failure is logged and reported as failed (A3)

```bash
.venv/bin/python - <<'PY'   # run_brief on b01 with request ""
...
PY
docker exec supabase-db psql -U postgres -d postgres -tAc "select r.id,r.ok,s.ok,s.error from app.run r join app.run_step s on s.run_id=r.id where r.id=(select max(id) from app.run)"
```

| Expected | Actual | Result |
|---|---|---|
| passed = False; step row ok = false with error naming step1.input | `False False contract step1.input: "" is shorter than 1 character`; row `84\|f\|f\|contract step1.input: "" is shorter than 1 character` | ✅ pass |

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
| 0 bad runs (measured before my C3 run existed; the C3 failure run was removed afterwards); 3 files | 1 while run 84 (my C3 failure run) existed, which is the expected failure; 3 files: check-contract, recipe-pipeline, step-1-read-request. After cleanup 21 rows remain (the 20 baseline runs plus 1 earlier b01 run). | ✅ pass |

### ✅ C8 · Containers healthy after the A7 stop/start

```bash
docker ps --format '{{.Names}} {{.Status}}' | grep -E 'n8n|pooler'; curl -s -o /dev/null -w "%{http_code}" localhost:5678/healthz
```

| Expected | Actual | Result |
|---|---|---|
| both Up, n8n healthz 200 | `n8n Up 43 seconds`, `supabase-pooler Up 43 seconds (healthy)`, `200` | ✅ pass |

## Part 3: Regression tests

Command: `.venv/bin/pytest -q`  ·  Result: ✅ 115 passed (stack up)

A7, stack stopped (`docker stop n8n supabase-pooler`, then `.venv/bin/pytest -q`): ✅ 91 passed, 24 skipped, 0 failed. The skipped ones are the `stack`-marked tests (reason "stack not running: Postgres"). Also `.venv/bin/pytest -q -m "not stack"` with the stack up: ✅ 91 passed, 24 deselected. Both containers were started again with `docker start` (no recreate).

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

Failures: none.
