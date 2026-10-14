# Verification: m2-adjunct-role

Overall: ✅ all 8 checks and 252 tests pass (warnings: see Part 1)

Run 2026-10-14 on branch `m2-adjunct-role` at abceb02, against the running stack.

## Part 1: Summary

🎯 **Goal:** Step 1 gives each wanted ingredient a role (`feature` or `background`), and step 2 picks the specialty style from that role instead of an English word-rule parser.

🛠️ **How:** `wanted` items became `{item, role}` objects (contract, prompt, check, grader); a measurement tool (`evals/roles.py`) gated the change on 34 wordings; then step 2 was switched to the role and `app.adjunct_cue` / `app.adjunct_is_prominent` were deleted.

🤔 **Why this way:** Whether the user wants an adjunct to stand out is language understanding, which is step 1's job; every earlier review round had found one more wording the SQL word lists missed.

🏁 **Result:** Gate MET (clear 21/21, held-out 10/10, 34/34 consistent); G1 step 1 22/22 and G2 step 2 22/22 (b05 15B, b12 31B, b19 17C, b17 8B); word rule gone from repo and database; 252 tests pass.

### 🚦 Steps

- ✅ 📝 **Brief:** Drafted with 6 questions, answers folded in, approved (99d3bdd).
- ✅ 🗺️ **Plan:** 9 tasks, the A9 exception and the 10 held-out wordings approved with it (f75ee38).
- ⚠️ 🔨 **Implement:** All 9 tasks done; the gate failed once, was retuned once more with user approval, then met.
  - ⚠️ Task 2: workflows imported with the n8n CLI instead of the MCP route; two existing tests relaxed for optional fields (recorded as a deviation).
  - ⚠️ Tasks 3 and 4: most new tests passed on the first run, so they were not seen failing.
  - ⚠️ Task 5: the abort-on-mismatched-settings path was only exercised on the matching path.
  - ❌ Task 6 run 1: gate NOT MET (clear 19/21, r07 and r12 lost the item to `unknown`; G1 step 1 21/22, b05 hint). One prompt edit was tried and reverted because it broke b19. 🔧 fixed in af64d2b (retune), measured in af8f36d: gate MET.
  - ❌ Task 6 run 2: af8f36d overwrote the second half of `plan.md`. 🔧 fixed in 20f0a2c (sections restored from af64d2b).
  - ⚠️ Task 8: the grep for removed names skipped `evals/results/` JSONs, which still mention `word_rule` (saved results, kept on purpose).
  - ⚠️ The extra retune also changed two step 1 rules outside the role (drinking remarks are dropped, an ingredient wish goes to `wanted`); the user approved it and it is recorded in the brief and plan.
- ⚠️ 🔍 **Review:** Round 1 found no must-fix and 2 should-fix (brief Deviations line, PROJECT.md wording) 🔧 fixed in b7e899c; round 2 ready for testing.
  - ⚠️ Clear 21/21 and G1 22/22 are scores on wordings the retune drew from; held-out 10/10 is the only independent score.
  - ⚠️ Step 1 median on the 22 briefs rose from 12.72 s to 13.18–13.40 s (gated wordings 12.82 s vs the 12.5 s target).
  - ⚠️ Open notes: Task 2 text still names the MCP route; stale "(R5)" note on the `Build model request` node; the §8 entry says "section 4" for a sentence in §5.
- ✅ 🧪 **Verify:** All checks and the full suite ran against the stack. 🧮 spot checks ✅ 8/8 · 🧪 tests ✅ 252/252

👀 **Start here:** `evals/results/2026-10-14-m2-role-gate.json` (the `gate` block: all four points `ok`, `met: true`), then the b12 reason in `app.run_step` run 1849: `honey has the role "feature" in step 1's brief; base style 18A`.

📁 **Changed files:**
- `PROJECT.md`
- `db/020_step1.sql`
- `db/022_step2.sql`
- `db/023_drop_adjunct_rule.sql`
- `docs/DATABASE.md`
- `docs/OPERATIONS.md`
- `docs/WORKFLOW-ROADMAP.md`
- `docs/work/m2-adjunct-role/brief.md`
- `docs/work/m2-adjunct-role/plan.md`
- `docs/work/m2-adjunct-role/review.md`
- `evals/grade.py`
- `evals/recipe_briefs.toml`
- `evals/results/2026-10-13-m2-role-g1.json`
- `evals/results/2026-10-13-m2-role-gate.json`
- `evals/results/2026-10-14-m2-role-g1.json`
- `evals/results/2026-10-14-m2-role-gate.json`
- `evals/results/2026-10-14-m2-role.json`
- `evals/role_wordings.toml`
- `evals/roles.py`
- `evals/run.py`
- `n8n/workflows/recipe-pipeline.json`
- `n8n/workflows/step-1-read-request.json`
- `shared/contracts/step1.input.schema.json`
- `shared/contracts/step1.output.schema.json`
- `shared/contracts/step2.input.schema.json`
- `shared/prompts/step1.system.md`
- `tests/test_contracts.py`
- `tests/test_grade.py`
- `tests/test_pipeline.py`
- `tests/test_prompt.py`
- `tests/test_recipe_briefs.py`
- `tests/test_role_wordings.py`
- `tests/test_roles.py`
- `tests/test_run.py`
- `tests/test_step1_check.py`
- `tests/test_step2_pick.py`
- `tests/test_step2_signals.py`
- `tests/test_workflows.py`

## Part 2: Spot checks

### ✅ C1 · Gated prompt is the committed prompt (R6)

```bash
sha256sum shared/prompts/step1.system.md | cut -c1-64; python3 -c "import json;print(json.load(open('evals/results/2026-10-14-m2-role-gate.json'))['prompt_sha256'])"
```

| Expected | Actual | Result |
|---|---|---|
| both hashes equal | d217b628…196e864b both times | ✅ pass |

### ✅ C2 · Gate verdict, point by point (R6, A4)

```bash
python3 -c "import json;print(json.dumps(json.load(open('evals/results/2026-10-14-m2-role-gate.json'))['gate']))"
```

| Expected | Actual | Result |
|---|---|---|
| b12/b19 right, clear ≥20/21, no inconsistent wording, held-out ≥9/10, `met: true` | b12 feature and b19 background in every run; clear 21/21; inconsistent []; held-out 10/10; met true | ✅ pass |

### ✅ C3 · Step 1 contract item shape (R1, A1)

```bash
python3 -c "import json;print(json.dumps(json.load(open('shared/contracts/step1.output.schema.json'))['properties']['wanted']['items']))"
```

| Expected | Actual | Result |
|---|---|---|
| object, required item + role, role enum feature/background, no extra keys | `{"required": ["item","role"], "additionalProperties": false, ... "role": {"enum": ["feature","background"]}}` | ✅ pass |

### ✅ C4 · Measurement set holds 34 wordings, 10 held out (R5, A5)

```bash
grep -c '^\[\[wording\]\]' evals/role_wordings.toml; grep -c 'set = "held_out"' evals/role_wordings.toml
```

| Expected | Actual | Result |
|---|---|---|
| 34 and 10 | 34 and 10 | ✅ pass |

### ✅ C5 · Word rule gone from the code (A9)

```bash
grep -rn "adjunct_cue\|adjunct_is_prominent\|DAMPER" db tests evals/*.py evals/*.toml shared n8n
```

| Expected | Actual | Result |
|---|---|---|
| only the two `drop function` lines in `db/023_drop_adjunct_rule.sql` | `db/023_drop_adjunct_rule.sql:6` and `:7` only | ✅ pass |

### ✅ C6 · Word rule gone from the database (A9)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='app' and p.proname in ('adjunct_cue','adjunct_is_prominent')"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C7 · G1/G2 totals on the real pipeline (R10, A10)

```bash
python3 -c "import json;print(json.load(open('evals/results/2026-10-14-m2-role.json'))['totals'])"
```

| Expected | Actual | Result |
|---|---|---|
| step 1 22/22, step 2 22/22 | step1 22/22, step2 22/22 (step 3 not built: not_run 22) | ✅ pass |

### ✅ C8 · Step 2 picks and reasons for b12, b19, b05, b17 (R7, R8, A8, R10)

```bash
for r in 1849 1856 1842 1854; do docker exec supabase-db psql -U postgres -d postgres -tAc "select $r, output->>'reason' from app.run_step where run_id=$r and step=2"; done
```

| Expected | Actual | Result |
|---|---|---|
| b12 31B citing `"feature"`, b19 17C, b05 15B, b17 8B | 1849: `Picked 31B ... honey has the role "feature" ... base style 18A`; 1856: `Picked 17C Wee Heavy`; 1842: `Picked 15B Irish Stout`; 1854: `Picked 8B Schwarzbier` | ✅ pass |

## Part 3: Regression tests

Command: `.venv/bin/python -m pytest -q`  ·  Result: ✅ 252 passed (2 min 8 s, stack up)

| Test | Protects | Result |
|---|---|---|
| tests/test_role_wordings.py | held-out wordings fixed, matching the plan table | ✅ |
| tests/test_prompt.py::test_prompt_names_every_role | prompt defines both roles | ✅ |
| tests/test_pipeline.py::test_temperature_and_seed_reach_step_1, ::test_default_temperature_and_seed | temperature/seed reach the Ollama call; defaults stay 0/42 | ✅ |
| tests/test_grade.py::test_wrong_role_fails_wanted | a wrong role fails `wanted` in G1 | ✅ |
| tests/test_contracts.py::test_bad_examples, tests/test_step1_check.py::test_plain_string_item_fails | contract rejects plain strings, missing or unknown roles, extra keys | ✅ |
| tests/test_roles.py | scored role and each R6 gate point computed correctly | ✅ |
| tests/test_step2_pick.py::test_feature_role_without_cue_word_picks_specialty, ::test_background_role_keeps_base_even_with_cue_words | role alone decides specialty vs base | ✅ |
| tests/test_step2_pick.py::test_b12_reason_cites_the_role | reason cites the role | ✅ |
| tests/test_step2_pick.py::test_briefs_reach_the_bar | no regression on the 22 briefs | ✅ |

Failures: none.
