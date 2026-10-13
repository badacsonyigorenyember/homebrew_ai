# Verification: m1-read-request

Overall: ✅ all 8 checks and 151 tests pass

Run 2026-10-13 on branch `m1-read-request` at 59bd030, stack up (17 containers).

## Part 1: Summary

🎯 **Goal:** Step 1 turns a request into a contract-checked brief JSON stored in `app.brief`, and D2 (the chat model) is decided by benchmark.

🛠️ **How:** One HTTP Request to Ollama with the contract as `format`, one SQL check function (`app.step1_read_answer`) with a single retry, a `named` field and user-word rule in the 20 briefs, and `evals/benchmark.py` for 7 configurations x 3 runs x 20 briefs.

🤔 **Why this way:** The n8n Ollama node has no seed, no JSON-schema `format` and no token counts, so R4/R5 could not be met with it; deterministic checks live in SQL, not in the LLM or a Code node.

🏁 **Result:** `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K` (thinking off) is the step 1 default: 19/20 briefs right in all 3 runs, 12.5 s median; D2 moved to PROJECT.md §4; `pytest` 151 passed.

### 🚦 Steps

- ⚠️ 📝 **Brief:** Drafted in an earlier session, revised with the user's answers and model research (`model-research.md`), approved, committed 9994737.
  - ⚠️ `ctx7` CLI failed with "Invalid API key"; the Ollama docs were read on the web instead.
- ⚠️ 🗺️ **Plan:** 7 tasks, approved, committed bb1413f; measured that Ollama enforces `maxItems` but not `uniqueItems`, so `app.brief.profile_id` became nullable (no `brewer_profile` rows).
  - ⚠️ `ctx7` "Invalid API key" again.
- ⚠️ 🔨 **Implement:** All 7 tasks done (41a8fa2, d3c7171, ca6fb0a, 3f76ccf, 73efe1e, dd20d9c, 51deac9), plus one fix round (ab94d94).
  - ⚠️ Task 3: the contract-example failure was not confirmed by breaking the change.
  - ⚠️ Task 4: `test_request_kept_verbatim` input changed; `validate_workflow` ran on an SDK rendering, not the stored workflow; `Ask model` nodes have no credential (Ollama needs none).
  - ⚠️ Task 4: smoke pass 15/20 to 17/20 needed two general prompt edits; prompt then frozen.
  - ⚠️ Task 5 and the review fix: new tests were not seen failing first.
  - ❌ Task 6: first attempt aborted by an API session limit 🔧 retry reused the 3 saved configs (dd20d9c).
  - ⚠️ Task 6: the three 2026-10-12 result sets were merged into `2026-10-13-m1-benchmark.json`; code unchanged so tests were not re-run there.
  - ⚠️ Remaining misses: b05 `hints` "session" inferred; qwen3.8:27b b19 `named` null not inspected.
- ✅ 🔍 **Review:** Two reviews, both "ready for testing"; 0 must-fix, 3 should-fix (per-config hashes, stray `|` in DATABASE.md, stale PROJECT.md row) 🔧 fixed in ab94d94; re-review 59bd030 found nothing new.
  - ⚠️ Note: R3 refuses "1,000 L" and ".5" (fails closed, `ok = false`).
  - ⚠️ Note: `Step 1 · save brief` has no error output.
  - ⚠️ Note: the A4 two-failure retry path is tested only through MCP executions 2820/2823, not pytest.
  - ⚠️ Note: about 480 `app.run`/`app.brief` rows from this work remain and back the benchmark `run_id`s.
- ✅ 🧪 **Verify:** All acceptance criteria A1-A8 confirmed against the results file, the live DB and tests. 🧮 spot checks ✅ 8/8 · 🧪 tests ✅ 151/151 (stack up).

👀 **Start here:** `docs/work/m1-read-request/benchmark.md`: the 7-row table where only the Qwen3.8-27B UD-Q6_K rows reach 19/20 three times; then PROJECT.md §4 "Chat model".

📁 **Changed files:**
- `PROJECT.md`
- `db/015_app.sql`
- `db/020_step1.sql`
- `docs/DATABASE.md`
- `docs/OPERATIONS.md`
- `docs/WORKFLOW-ROADMAP.md`
- `docs/work/m1-read-request/benchmark.md`
- `docs/work/m1-read-request/brief.md`
- `docs/work/m1-read-request/model-research.md`
- `docs/work/m1-read-request/plan.md`
- `docs/work/m1-read-request/review.md`
- `evals/benchmark.py`
- `evals/grade.py`
- `evals/recipe_briefs.toml`
- `evals/results/2026-10-13-m1-benchmark.json`
- `evals/run.py`
- `n8n/workflows/check-contract.json`
- `n8n/workflows/recipe-pipeline.json`
- `n8n/workflows/step-1-read-request.json`
- `shared/contracts/step1.input.schema.json`
- `shared/contracts/step1.output.schema.json`
- `shared/prompts/step1.system.md`
- `tests/test_benchmark.py`
- `tests/test_contracts.py`
- `tests/test_grade.py`
- `tests/test_pipeline.py`
- `tests/test_prompt.py`
- `tests/test_recipe_briefs.py`
- `tests/test_run.py`
- `tests/test_step1_check.py`
- `tests/test_workflows.py`
- `docs/work/m1-read-request/verification.md`

## Part 2: Spot checks

### ✅ C1 · The chosen model reaches the bar in every run (A1)

```bash
.venv/bin/python - <<'PY'
import json
from evals import benchmark as b
d = json.load(open('evals/results/2026-10-13-m1-benchmark.json'))
for k, c in d['configs'].items():
    print(k, c['summary']['all_right'], b.meets_bar(c['summary']))
PY
```

| Expected | Actual | Result |
|---|---|---|
| Qwen3.8-27B UD-Q6_K (think off and on) `[19,19,19]` True; others below 19 | UD-Q6_K no-think `[19, 19, 19]` True, think `[19, 19, 19]` True; qwen3.8:27b `[18,18,18]`, gemma4:12b-it-q8_0 `[17,17,17]`, gemma4:12b `[16,16,16]`, gemma4:31b-it-qat `[17,17,17]`, gemma4:26b-a4b-it-qat `[12,13,13]`, all False | ✅ pass |

### ✅ C2 · The named cases in the stored briefs (A2)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select r.id, b.brief->>'named', b.brief->'stated', b.brief->'excluded', b.guidance_on from app.run r join app.brief b on b.id=r.brief_id where r.id in (610,613,623) order by r.id"
```

Runs 610 / 613 / 623 are b05 / b08 / b18 of the third UD-Q6_K no-think run.

| Expected | Actual | Result |
|---|---|---|
| b05 `imperial stout`, `{"abv": 4}`; b08 `excluded` Saaz, `stated` batch_l 10 + ibu 50; b18 `guidance_on` false | `610\|imperial stout\|{"abv": 4}\|[]\|t`; `613\|German pils\|{"ibu": 50, "batch_l": 10}\|["Saaz"]\|t`; `623\|Irish red ale\|{"srm": 20}\|[]\|f` | ✅ pass |

### ✅ C3 · Unknown hint word goes to `unknown` (A3)

```bash
.venv/bin/pytest -q tests/test_pipeline.py -k "unknown_word or b01_logs or bad_input" 2>&1 | tail -1
```

| Expected | Actual | Result |
|---|---|---|
| 3 passed (`test_unknown_word_goes_to_unknown` among them) | 3 passed, 2 deselected | ✅ pass |

### ✅ C4 · A made-up number fails the check (A4)

```bash
.venv/bin/pytest -q tests/test_step1_check.py 2>&1 | tail -1
```

| Expected | Actual | Result |
|---|---|---|
| 6 passed (`test_made_up_number_fails`: `stated.abv` error) | 6 passed in 0.04s | ✅ pass |

The two-failures-end-with-`ok = false` path has no pytest; it was shown by MCP executions 2820 / 2823 (plan Deviations), not re-run here.

### ✅ C5 · A run leaves one brief and a logged step (A5)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select r.id, r.model, r.ok, s.step, s.ms>0, s.tokens>0, s.llm->>'model' from app.run r join app.run_step s on s.run_id=r.id where r.id=610"
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from app.run r where r.finished_at is not null and r.ok and r.brief_id is null and r.eval_id like 'b%' and r.id>=266"
```

| Expected | Actual | Result |
|---|---|---|
| step 1 row with model, ms > 0, tokens > 0, `llm.model` = run model; 0 finished-ok runs without a brief | `610\|hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K\|t\|1\|t\|t\|hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K`; count `0` | ✅ pass |

### ✅ C6 · Benchmark table has 7 rows; D2 decided in PROJECT.md (A6)

```bash
grep -c '^| \(qwen3.8\|gemma4\|hf.co\)' docs/work/m1-read-request/benchmark.md; awk '/^## 7/{f=1;next} /^## 8/{f=0} f' PROJECT.md | grep -c '^| D2\|\*\*D2'; grep -c 'Chat model.*UD-Q6_K' PROJECT.md
```

| Expected | Actual | Result |
|---|---|---|
| 7 table rows, 0 D2 rows in §7, 1 chosen-model row in §4 | 7, 0, 1 | ✅ pass |

### ✅ C7 · `named` in all 20 briefs and the user's words (A7)

```bash
.venv/bin/python - <<'PY'
import tomllib
bs = tomllib.load(open('evals/recipe_briefs.toml','rb'))['brief']
print(len(bs), sum('named' in (b.get('expected') or b) for b in bs))
PY
.venv/bin/pytest -q tests/test_recipe_briefs.py 2>&1 | tail -1
```

| Expected | Actual | Result |
|---|---|---|
| 20 briefs, 20 with `named`; recipe-brief tests pass (incl. `test_words_are_the_users`) | `20 20`; all passed (full list in Part 3) | ✅ pass |

### ✅ C8 · Grader rules (A8)

```bash
.venv/bin/pytest -q tests/test_grade.py -k "form_word or case_and or synonym" 2>&1 | tail -1
```

| Expected | Actual | Result |
|---|---|---|
| 3 passed (`rice` vs `flaked rice` wrong; `Flaked Rice` right; synonym pair right) | 3 passed, 18 deselected | ✅ pass |

## Part 3: Regression tests

Command: `.venv/bin/pytest -v`  ·  Result: ✅ 151 passed (stack up, 36 s). All critical tests the plan named exist; none had to be added.

| Test | Protects | Result |
|---|---|---|
| tests/test_step1_check.py::test_made_up_number_fails | A number the user did not write never passes into `stated` | ✅ |
| tests/test_step1_check.py::test_written_forms_of_a_number_match | A number in another notation still passes | ✅ |
| tests/test_step1_check.py::test_not_json_fails, ::test_contract_errors_reported | Off-contract answers are errors, not a guessed brief | ✅ |
| tests/test_grade.py::test_form_word_is_a_different_ingredient | `flaked rice` and `rice` graded as different | ✅ |
| tests/test_grade.py::test_case_and_spacing_ignored, ::test_synonym_pair_counts_as_equal, ::test_accents_ignored_in_named | Case, spacing, accents, listed synonyms do not fail a right word | ✅ |
| tests/test_recipe_briefs.py::test_words_are_the_users | Expected words are the user's own | ✅ |
| tests/test_prompt.py (4 tests) | The prompt covers every field/hint/number and quotes no brief | ✅ |
| tests/test_pipeline.py::test_b01_logs_step_1 | Each run saves its brief and logs model, time, tokens | ✅ |
| tests/test_pipeline.py::test_unknown_word_goes_to_unknown | Unknown wish goes to `unknown`, not `hints` | ✅ |
| tests/test_workflows.py::test_num_ctx_matches_benchmark | Benchmark loads the model at the pipeline's context | ✅ |
| tests/test_benchmark.py::test_bar_needs_every_run, ::test_best_is_quality_before_speed | The bar needs every run; quality beats speed | ✅ |
| tests/test_benchmark.py::test_each_saved_config_keeps_its_own_hashes | Saved configurations carry their own prompt/contract hashes | ✅ |

Failures: none.
