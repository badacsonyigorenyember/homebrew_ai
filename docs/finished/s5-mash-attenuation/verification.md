# Verification: s5-mash-attenuation

Overall: ✅ all 9 checks and 714 tests pass

## Part 1: Summary

🎯 **Goal:** Give rule 10's predicted FG a mash-temperature model whose every number has a source.

🛠️ **How:** `app.mash_attenuation` now follows Troester's measured curve: flat up to a knee, then a straight fall, with the numbers stored in `app.formulation_limits()`.

🤔 **Why this way:** It keeps the yeast's attenuation range as input, so callers are unchanged, and adds one cited slope instead of a many-coefficient fit.

🏁 **Result:** Up to 68.3 °C the attenuation is the middle of the yeast's range; above it, 4.15 points lower per °C. All 22 reference recipes pass rule 10, and 714 tests pass.

### 🚦 Steps

- ⏭️ 📝 **Brief:** Skipped as a step; the brief was already on disk and the user approved it (bd9d1a1).
- ✅ 🗺️ **Plan:** Written and approved (e5aa73d); it noted that *Yeast* gives no reference mash temperature, so 66.5 °C.
- ⚠️ 🔨 **Implement:** Tasks 1–3 done (eb4ec6b, e8dcd2b, 7d630ca) plus one review-fix round (5cc73e7).
  - ⚠️ Task 1: the planned per-row check (OE − AE) / OE ≈ attenuation failed for 10 of 11 rows (off by 1.4–7.0); the column is treated as a limit of attenuation, rows checked against the image only; user approved (plan Deviations).
  - ❌ Task 2: b12 and b22 (mash 68 °C) went pass to fail under the new model; per the user, both fixtures now mash at 69 °C (b12 FG 1.0084, b22 FG 1.0106).
  - ⚠️ Task 2 ran twice (stopped at the rule 10 change, then resumed).
- ⚠️ 🔍 **Review:** Ready for testing, 0 must-fix, 2 should-fix, fixed doc-only in 5cc73e7 without running tests. 🔧 fixed in 5cc73e7
  - ⚠️ The `dry` mash hint (64–65 °C) no longer lowers predicted FG, since 64–68.3 °C all give the same attenuation; recorded for M4.
  - ⚠️ Sample 2's average temperature equals its start temperature in the source (possible source error; with 69.5 the slope would be 3.97 and the knee 67.84).
  - ⚠️ The 032 comment hard-codes 68.3 and 4.15; one test checks only differences (absolute levels are pinned by `test_mash_mapping`).
- ✅ 🧪 **Verify:** All spot checks and the full suite pass; both SQL files applied twice cleanly this run. 🧮 spot checks ✅ 9/9 · 🧪 tests ✅ 714/714

👀 **Start here:** `docs/work/s5-mash-attenuation/doc-calc.md` (the source numbers and derivation), then run the Part 2 first example to see 80 at 64–68.3 °C and 78 at 69 °C.

📁 **Changed files:**
- `PROJECT.md`
- `db/031_formulation_rules.sql`
- `db/032_formulation_check.sql`
- `docs/RECIPE-ROADMAP.md`
- `docs/SOURCES.md`
- `docs/work/s5-mash-attenuation/brief.md`
- `docs/work/s5-mash-attenuation/doc-calc.md`
- `docs/work/s5-mash-attenuation/plan.md`
- `docs/work/s5-mash-attenuation/reference-recheck.md`
- `docs/work/s5-mash-attenuation/review.md`
- `tests/fixtures/reference_recipes.toml`
- `tests/test_formulation_check.py`
- `tests/test_formulation_rules.py`
- `tests/test_mash_attenuation.py`

## Part 2: Showcase

| Item | What it does |
|---|---|
| `app.mash_attenuation(numrange, numeric)` | Predicted attenuation from the yeast's range and the mash temperature (Troester curve) |
| `mash_ref_c` 66.5, `mash_knee_c` 68.3, `mash_slope_pct_per_c` 4.15 | The three cited numbers, in `app.formulation_limits()` |
| Rule 10 sentence | Built from those limits; names Troester 2009 |

**A 78–82 % yeast across the mash range**

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select t, round(app.mash_attenuation('[78,82]'::numrange, t),3) from unnest(array[63,64,66.5,68.3,69,70]::numeric[]) t"
```

```text
63|80.000
64|80.000
66.5|80.000
68.3|80.000
69|78.000
70|78.000
```

**A wide 70–90 % range mashed at 69 °C (unclamped slope shows)**

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select app.mash_attenuation('[70,90]'::numrange, 69)"
```

```text
77.0950000000000000
```

**The three stored numbers**

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select app.formulation_limits()->>'mash_ref_c', app.formulation_limits()->>'mash_knee_c', app.formulation_limits()->>'mash_slope_pct_per_c'"
```

```text
66.5|68.3|4.15
```

**Rule 10 now names its source**

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select sentence from app.formulation_rules() where rule = '10'"
```

```text
The mash temperature is between 64 and 69 °C, and the FG predicted from the yeast's attenuation_pct, each fermentable's fermentability and the mash temperature is inside the target FG range: the style's FG range, or the target FG ± 0.002 when the user stated the FG or the ABV. Up to 68.3 °C the attenuation is the middle of the yeast's attenuation_pct range, which applies at 66.5 °C; above 68.3 °C it is 4.15 points lower per °C, never outside that range (Troester 2009, limit of attenuation against mash temperature).
```

**Reference recipes affected (from `reference-recheck.md`, measured in Task 2)**

| Brief | Style | Mash | FG before | FG new model | Rule 10 new model | FG after fixture fix |
|---|---|---|---|---|---|---|
| b12 | 18A | 68 to 69 °C | 1.0081 | 1.0077 (target 1.0080–1.0130) | fail | 1.0084 pass |
| b22 | mexican-style-amber-lager | 68 to 69 °C | 1.0101 | 1.0092 (target 1.0100–1.0120) | fail | 1.0106 pass |

## Part 3: Spot checks

### ✅ C1 · Both SQL files apply twice without error (A2)

```bash
for f in 031_formulation_rules 032_formulation_check; do for i in 1 2; do docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 -q < db/$f.sql >/dev/null 2>&1; echo "$f run$i exit $?"; done; done
```

| Expected | Actual | Result |
|---|---|---|
| exit 0 four times | exit 0 four times | ✅ pass |

### ✅ C2 · Functions owned by postgres (A2)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select proowner::regrole, proname from pg_proc where proname in ('mash_attenuation','formulation_limits','formulation_rules') order by 2"
```

| Expected | Actual | Result |
|---|---|---|
| postgres for all three | postgres for all three | ✅ pass |

### ✅ C3 · Rule 10 names the source, no "uncited assumption" (A4)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select sentence ilike '%Troester%', sentence ilike '%uncited%' from app.formulation_rules() where rule = '10'"
```

| Expected | Actual | Result |
|---|---|---|
| t\|f | t\|f | ✅ pass |

### ✅ C4 · Ends and middle of the model (A3, R4)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select app.mash_attenuation('[78,82]'::numrange,64), app.mash_attenuation('[78,82]'::numrange,69), app.mash_attenuation('[70,90]'::numrange,69)"
```

| Expected | Actual | Result |
|---|---|---|
| 80 \| 78 \| 77.095 | 80.0000000000000000\|78\|77.0950000000000000 | ✅ pass |

### ✅ C5 · Null inputs give null (R4)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select app.mash_attenuation(null,66) is null, app.mash_attenuation('[78,82]'::numrange,null) is null"
```

| Expected | Actual | Result |
|---|---|---|
| t\|t | t\|t | ✅ pass |

### ✅ C6 · Stored model numbers match the approved doc-calc (A1)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select app.formulation_limits()->>'mash_ref_c', app.formulation_limits()->>'mash_knee_c', app.formulation_limits()->>'mash_slope_pct_per_c'"; head -3 docs/work/s5-mash-attenuation/doc-calc.md | tail -1
```

| Expected | Actual | Result |
|---|---|---|
| 66.5\|68.3\|4.15 and "Approved by the user" line | 66.5\|68.3\|4.15; "Approved by the user 2026-10-17" | ✅ pass |

### ✅ C7 · All 22 reference recipes recorded and passing rule 10 (A5)

```bash
grep -c '^| b[0-9]' docs/work/s5-mash-attenuation/reference-recheck.md; grep -n "All 22" docs/work/s5-mash-attenuation/reference-recheck.md
```

| Expected | Actual | Result |
|---|---|---|
| 22 rows before/after; changes settled | 22 (before/after table) + 2 (fixed re-measure); "All 22 recipes pass rule 10." | ✅ pass |

Note: `grep -c` counted 24 lines because the b12 and b22 re-measure rows also start with `| b`; the 22-row table is complete.

### ✅ C8 · Roadmap §8 has no rule 10 TODO (A6)

```bash
grep -n -i "uncited" docs/RECIPE-ROADMAP.md; echo "grep exit $?"
```

| Expected | Actual | Result |
|---|---|---|
| no match (exit 1) | no match, grep exit 1 | ✅ pass |

### ✅ C9 · Terrill's strain finding recorded as a known limit (R7, A1)

```bash
grep -n -i "3522\|1272\|2206" docs/work/s5-mash-attenuation/doc-calc.md | head -5
```

| Expected | Actual | Result |
|---|---|---|
| lines for the three strains | doc-calc.md lines 178 (3522), 179 (2206), 180 (1272), 187–188 (known limit) | ✅ pass |

## Part 4: Regression tests

Command: `.venv/bin/pytest -q`  ·  Result: ✅ 714 passed in 176.56s

| Test | Protects | Result |
|---|---|---|
| tests/test_mash_attenuation.py::test_slope_fits_the_table | Stored slope matches least-squares fit of Troester's table | ✅ |
| tests/test_mash_attenuation.py::test_knee_meets_the_plateau | Stored knee is where the line meets the plateau | ✅ |
| tests/test_mash_attenuation.py::test_curve_reproduces_the_table | Curve within 2.5 points of every source row | ✅ |
| tests/test_mash_attenuation.py::test_function_follows_the_curve | SQL function follows the curve over 64–69 °C | ✅ |
| tests/test_formulation_check.py::test_mash_mapping | Ends, middle and clamps (R4) | ✅ |
| tests/test_formulation_rules.py::test_text_uses_the_limits, ::test_rule_10_names_its_source | Rule 10 sentence shows the limits and names its source | ✅ |
| tests/test_formulation_check.py::test_rule_10 | Rule 10 still fails and passes where it should | ✅ |
| tests/test_reference_recipes.py::test_every_rule_passes[b01..b22] | All 22 reference recipes pass | ✅ (22/22) |

Failures: none.
