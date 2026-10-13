# Verification: m2-best-fit-style

Overall: ✅ all 9 checks and 235 tests pass (warnings: see Part 1)

Run 2026-10-13 on branch `m2-best-fit-style` at 784c96a, against the running stack.

## Part 1: Summary

🎯 **Goal:** Pipeline step 2 picks the best-fit beer style from the step 1 brief, scoring BJCP and Brewers Association styles together.

🛠️ **How:** SQL signal functions and one picking function (`app.step2_best_style`) in `db/022_step2.sql`, a 151-pair BA-to-BJCP list, and an n8n sub-workflow wired into the recipe pipeline.

🤔 **Why this way:** Brewing logic stays in tested SQL (G0), every weight is a named constant, and the user's rule (both guides scored, best fit wins, equivalent styles go to BJCP) is applied directly.

🏁 **Result:** b01–b20 pick an accepted style 20/20, b21 and b22 pick their BA style, b05 gives 15B with a 20C mismatch, b12 gives 31B with 18A, b19 gives 17C; the full suite passes (235 tests); G2 step 2 measured 22/22 on the real pipeline at 86e173c.

### 🚦 Steps

- ⏭️ 📝 **Brief:** Already existed; the user approved it (e940d4f).
- ✅ 🗺️ **Plan:** Drafted, then revised for the user's answers; approved (05e941a). Seven tasks.
- ⚠️ 🔨 **Implement:** All 7 tasks ticked, plus fix rounds 2f56b5a, bda1e15, 996276b, 784c96a.
  - ⚠️ Task 1: no failing test seen before the change (8115d6b).
  - ⚠️ Task 2 ran three times: a name-matching script (threshold 0.8 to 0.85 deviation), a characteristics-script redo the user stopped, then Claude-judged pairs (0b966a4, 2ae6d65).
  - ❌ Task 5 stopped once because b05 picked 16A and no constant could fix it; solved in c4df56b with a tight-fit bonus and the catch-all exception. 🔧 fixed in c4df56b
  - ⚠️ Task 5: the catch-all test was written without a test-first fail.
  - ⚠️ Task 6: the n8n MCP drops onError, so workflows were imported through the CLI; a null `guide_preference` arrived as missing and was fixed with `?? null`.
  - ⚠️ Task 7: pytest was not re-run after the G2 measurement; the last fix (784c96a) did not re-run G2 (judged from 22/22 at SQL level).
  - ⚠️ Data issues: about 10 BA style names are cut off in `ref.beer_style`, and BJCP 21B holds only the Brut IPA text.
  - ⚠️ Step 1 misses the b05 `hints` field (21/22), and the overall G2 brief count is 0/22 because step 3 isn't built.
- ❌ 🔍 **Review:** Four rounds: fixes needed (1 must, 3 should), fixes needed (must-fix 10 regression), fixes needed (must-fix 15), then ready for testing. 🔧 fixed in 2f56b5a, bda1e15, 996276b, 784c96a
  - ⚠️ Fix 784c96a (findings 19 and note 20) was not re-reviewed.
  - ⚠️ Open by the user's choice: finding 16 (cue searched across the whole sentence), 17 (DAMPER_GAP misses two-word honey varieties), 18 (in a mismatch the alternatives sit next to the named style); 14 (`style_name_covers` with extra words) also open.
- ✅ 🧪 **Verify:** All acceptance checks reproduced at SQL level on the current commit; whole suite run. 🧮 spot checks ✅ 9/9 · 🧪 tests ✅ 235/235

👀 **Start here:** `db/022_step2.sql`, function `app.step2_best_style` (the weights are in its `declare` block); then `docs/work/m2-best-fit-style/style-pairs.md` for the pair decisions.

📁 **Changed files:**
- `PROJECT.md`
- `db/021_style_pairs.sql`
- `db/022_step2.sql`
- `docs/DATABASE.md`
- `docs/OPERATIONS.md`
- `docs/WORKFLOW-ROADMAP.md`
- `docs/work/m2-best-fit-style/brief.md`
- `docs/work/m2-best-fit-style/plan.md`
- `docs/work/m2-best-fit-style/review.md`
- `docs/work/m2-best-fit-style/style-pairs.md`
- `evals/recipe_briefs.toml`
- `evals/results/2026-10-13-m2-fix.json`
- `evals/results/2026-10-13-m2-fix2.json`
- `evals/results/2026-10-13-m2-fix3.json`
- `evals/results/2026-10-13-m2.json`
- `n8n/workflows/recipe-pipeline.json`
- `n8n/workflows/step-2-best-fit-style.json`
- `shared/contracts/step2.input.schema.json`
- `shared/contracts/step2.output.schema.json`
- `tests/test_contracts.py`
- `tests/test_pipeline.py`
- `tests/test_recipe_briefs.py`
- `tests/test_step2_pick.py`
- `tests/test_step2_signals.py`
- `tests/test_style_pairs.py`
- `tests/test_workflows.py`

## Part 2: Spot checks

Checks C2 to C8 call `app.step2_best_style` through the test helpers (`tests/test_step2_pick.py`) with the briefs in `evals/recipe_briefs.toml`.

### ✅ C1 · Functions exist and are owned by postgres

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*), count(*) filter (where proowner::regrole::text='postgres') from pg_proc where pronamespace='app'::regnamespace and proname in ('step2_best_style','style_pair','bjcp_catch_all')"
```

| Expected | Actual | Result |
|---|---|---|
| 3\|3 | 3\|3 | ✅ pass |

### ✅ C2 · Pair list size (151 paired)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from app.style_pair()"
```

| Expected | Actual | Result |
|---|---|---|
| 151 | 151 | ✅ pass |

### ✅ C3 · b01–b20 pick an accepted style (A1)

Run: the helper loop over `b01`..`b20`, counting `style.code` in `style` or `alt_styles`.

| Expected | Actual | Result |
|---|---|---|
| ≥ 18/20 | 20/20 | ✅ pass |

### ✅ C4 · b21 and b22 pick their BA style (A1)

| Expected | Actual | Result |
|---|---|---|
| session-india-pale-ale, mexican-style-amber-lager | session-india-pale-ale, mexican-style-amber-lager | ✅ pass |

### ✅ C5 · b05, b12, b19 (A2)

| Expected | Actual | Result |
|---|---|---|
| b05 15B, mismatch names 20C and ABV range; b12 31B with 18A alternative; b19 17C | b05 15B, mismatch `{named: 20C Imperial Stout, range: ABV 8.0–12.0, chosen: 15B Irish Stout}`; b12 31B, alt 18A; b19 17C | ✅ pass |

### ✅ C6 · Same input, same output (A3)

| Expected | Actual | Result |
|---|---|---|
| True for all 22 briefs | True | ✅ pass |

### ✅ C7 · Guide override and pair rule (A4)

| Expected | Actual | Result |
|---|---|---|
| b01 with `ba`: BA style and webhook reason; field `any` beats "Use a BA style" text (21A); Koelsch gives 5B | west-coast-style-india-pale-ale, "webhook setting: ba"; 21A; 5B | ✅ pass |

### ✅ C8 · No beer gives the unknown result (A5)

| Expected | Actual | Result |
|---|---|---|
| `style` null | `{"style": null, "reason": "No style fits the request, so no style is picked.", ...}` | ✅ pass |

### ✅ C9 · G2 saved run on the real pipeline

```bash
python3 -c "import json;print(json.load(open('evals/results/2026-10-13-m2.json'))['totals']['step2'])"
```

| Expected | Actual | Result |
|---|---|---|
| step 2 passes b01–b20 ≥ 18, b21, b22 right | {'passed': 22, 'total': 22, 'not_run': 0} | ✅ pass |

Note: the saved run is from 86e173c; fixes since then were checked at SQL level (C3) and by the test suite (which includes the pipeline tests).

## Part 3: Regression tests

Command: `.venv/bin/pytest -q`  ·  Result: ✅ 235 passed (115.9 s)

| Test | Protects | Result |
|---|---|---|
| tests/test_style_pairs.py::test_pair_list_matches_file, ::test_pair_codes_exist, ::test_each_ba_style_paired_once | Only the decided pairs map BA to BJCP | ✅ |
| tests/test_step2_pick.py::test_ba_winner_with_pair_returns_bjcp | Under `any`, a paired BA winner returns BJCP; BA only keeps BA | ✅ |
| tests/test_step2_pick.py::test_smoke_porter_keeps_the_ba_style | A BA style paired with a BJCP catch-all keeps the BA style | ✅ |
| tests/test_step2_pick.py::test_ba_only_field_b01, ::test_ba_only_from_request_b01, ::test_field_beats_request_text | The `guide` field wins over the request text | ✅ |
| tests/test_step2_pick.py::test_b05_irish_stout_with_mismatch, ::test_b17_number_outside_is_not_a_mismatch | A ruling-out number reports a mismatch; an outside number elsewhere does not | ✅ |
| tests/test_step2_pick.py::test_b12_honey_forward_is_a_honey_specialty, ::test_b19_some_honey_keeps_wee_heavy | Prominent adjunct picks the specialty; a minor one doesn't | ✅ |
| tests/test_step2_signals.py (damper and cue tests) | Adjunct prominence, two-sided bounded damper check | ✅ |
| tests/test_step2_signals.py::test_accents_and_case_ignored, ::test_ipa_spelled_out, ::test_guide_words_not_part_of_the_name, ::test_partial_name | Name matching rules | ✅ |
| tests/test_step2_signals.py::test_every_alias_has_a_source | Every alias has a source (A7) | ✅ |
| tests/test_step2_pick.py::test_same_input_same_output, ::test_equal_names_go_to_bjcp | Determinism; ties go to BJCP | ✅ |
| tests/test_step2_pick.py::test_no_beer_is_unknown | No forced pick | ✅ |
| tests/test_step2_pick.py::test_output_meets_contract, tests/test_contracts.py | Output meets the step 2 contract | ✅ |
| tests/test_step2_pick.py::test_briefs_reach_the_bar | SQL-level G2 bar | ✅ |
| tests/test_pipeline.py (step 2 logged, bad guide fails at step 2, guide reaches step 2) | Pipeline wiring and logging | ✅ |

Failures: none.
