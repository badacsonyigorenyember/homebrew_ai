Overall: ✅ all 13 checks and 61 tests pass

# Verification: test-briefs

Branch: test-briefs at 617f189  ·  Run: 2026-10-11  ·  Brief: [brief.md](brief.md)  ·  Plan: [plan.md](plan.md)

## Part 1: Summary

🎯 **Goal:** A fixed set of 20 recipe test briefs that every later recipe phase (P4, P5) is scored against.

🛠️ **How:** One reviewable TOML file, `evals/recipe_briefs.toml`, with 20 `[[brief]]` tables, checked by a 10-test pytest module for shape, coverage and DB-backed style codes.

🤔 **Why this way:** TOML reads like a document for review and needs no new dependency (`tomllib`), and checking style codes against `ref.beer_style` avoids codes written from memory.

🏁 **Result:** 20 user-approved briefs across 16 BJCP categories, all 6 adjuncts needed, every guidance, constraint and hint case covered; 22 style codes all exist in bjcp-2021; P0 is recorded done in PROJECT.md and RECIPE-ROADMAP; the suite passes 61/61.

### 🚦 Steps

- ⏭️ 📝 **Brief:** Skipped: the brief already existed and was approved (62210d0, scope trimmed in d67382f).
- ✅ 🗺️ **Plan:** One run, approved and committed e1cb0fd; the user answered that the DB style-code test is a hard failure when the DB is unreachable.
- ⚠️ 🔨 **Implement:** Five runs: Task 1 ad2ca1f, Task 2 user review 197d747 and 6f37a87, Task 3 a847715, review fix ed8a1ca; all three tasks ticked.
  - ⚠️ Task 1 deviation: `needs` written as a `[brief.needs]` sub-table instead of an inline table (same parsed shape).
  - ⚠️ Task 2: the user changed R3 (prominent adjunct → specialty code, base style as alternative); b12 reworded to 31B alt 18A.
  - ⚠️ Task 2: b12's deviation removed; b16 reworded to add rice as an ingredient deviation, and a `crisp` hint added without being asked (told to the user, no objection).
  - ⚠️ The two Task 2 deviation lines in plan.md read as contradictory unless read in order (review note 3).
- ❌ 🔍 **Review:** Round 1 (7ce0a15) ready for testing with 1 should-fix: the R3 rule was missing from PROJECT.md 🔧 fixed in ed8a1ca. Round 2 (617f189) ready for testing, no findings.
  - ⚠️ The test does not check that a specialty `style` lists its base style in `alt_styles` (review note 2).
  - ⚠️ PROJECT.md links to `docs/work/test-briefs/` need updating when dev-ship moves the folder (review note 4).
  - ⚠️ Open for the ship gate: the RECIPE-ROADMAP "Later · BA as a selectable guide" row and `docs/DATABASE.md:451` may be stale given D1 (review note 7).
- ✅ 🧪 **Verify:** All checks and the full suite run on the branch; A5 (user approval of all 20 briefs) was done in chat on 2026-10-11, and C10 confirms the agreed corrections are in the file. 🧮 spot checks ✅ 13/13 · 🧪 tests ✅ 61/61

👀 **Start here:** `evals/recipe_briefs.toml`: the header comment explains every field, then 20 `[[brief]]` tables b01–b20, each with a request a user would type, its `why`, expected `style`, `deviations` and `needs`.

📁 **Changed files:**
- `PROJECT.md`
- `docs/RECIPE-ROADMAP.md`
- `docs/work/test-briefs/brief.md`
- `docs/work/test-briefs/plan.md`
- `docs/work/test-briefs/review.md`
- `evals/recipe_briefs.toml`
- `tests/test_recipe_briefs.py`

## Part 2: Spot checks

### ✅ C1 · Exactly 20 briefs with unique ids (A1, R1)

```bash
.venv/bin/python -c "import tomllib; b = tomllib.load(open('evals/recipe_briefs.toml', 'rb'))['brief']; print(len(b), len({x['id'] for x in b}))"
```

| Expected | Actual | Result |
|---|---|---|
| 20 20 | 20 20 | ✅ pass |

### ✅ C2 · Every brief has exactly the R2 fields (A1, R2, R4 by shape)

```bash
.venv/bin/python -c "import tomllib; b = tomllib.load(open('evals/recipe_briefs.toml', 'rb'))['brief']; print(sorted({tuple(sorted(x)) for x in b}))"
```

| Expected | Actual | Result |
|---|---|---|
| one key set: alt_styles, deviations, excluded, guidance, hints, id, inventory, needs, request, stated, style, wanted, why | `[('alt_styles', 'deviations', 'excluded', 'guidance', 'hints', 'id', 'inventory', 'needs', 'request', 'stated', 'style', 'wanted', 'why')]` | ✅ pass |

### ✅ C3 · Every expected and alternative code exists in ref.beer_style for bjcp-2021 (A2, R3)

```bash
.venv/bin/python -c "import tomllib; b = tomllib.load(open('evals/recipe_briefs.toml', 'rb'))['brief']; print(','.join(sorted({c for x in b for c in [x['style'], *x['alt_styles']]})))"
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(distinct b.code) from ref.beer_style b join ref.source s on s.id = b.source_id where s.slug = 'bjcp-2021' and b.code in ('10A','11B','15A','15B','16A','16B','17C','18A','18B','19C','1B','1C','20C','21A','21C','23A','25B','26B','31B','5D','6A','8B')"
```

| Expected | Actual | Result |
|---|---|---|
| 22 distinct codes in the file, 22 found in the DB | 22 codes (`10A,11B,15A,15B,16A,16B,17C,18A,18B,19C,1B,1C,20C,21A,21C,23A,25B,26B,31B,5D,6A,8B`), DB count 22 | ✅ pass |

### ✅ C4 · Style spread (A3, R5)

```bash
.venv/bin/python -c "from tests.test_recipe_briefs import coverage, BRIEFS; c = coverage(BRIEFS); print(', '.join(f'{k}={c[k]}' for k in ('categories', 'stouts_porters', 'lagers', 'belgian', 'wheat_sour', 'hop_forward')))"
```

| Expected | Actual | Result |
|---|---|---|
| categories ≥ 8, stouts_porters ≤ 3, lagers ≥ 3, belgian ≥ 2, wheat_sour ≥ 2, hop_forward ≥ 3 | categories=16, stouts_porters=3, lagers=4, belgian=2, wheat_sour=2, hop_forward=3 | ✅ pass |

### ✅ C5 · Each of the six adjuncts is needed (A3, R6)

```bash
.venv/bin/python -c "from tests.test_recipe_briefs import coverage, BRIEFS; c = coverage(BRIEFS); print(', '.join(f'{k.split(\": \")[-1]}={v}' for k, v in c.items() if k.startswith('adjunct')))"
```

| Expected | Actual | Result |
|---|---|---|
| each ≥ 1 | flaked oats=2, candi sugar=1, flaked corn=1, flaked rice=2, lactose=2, honey=2 | ✅ pass |

### ✅ C6 · Guidance cases (A3, R7)

```bash
.venv/bin/python -c "from tests.test_recipe_briefs import coverage, BRIEFS; c = coverage(BRIEFS); print(', '.join(f'{k.split(\": \")[-1]}={v}' for k, v in c.items() if k.startswith('deviation') or k == 'guidance_off'))"
```

| Expected | Actual | Result |
|---|---|---|
| conflict ≥ 1, ingredient ≥ 3, mismatch ≥ 1, number ≥ 2, guidance_off ≥ 1 | conflict=1, ingredient=3, mismatch=1, number=3, guidance_off=1 | ✅ pass |

### ✅ C7 · Constraints, batch sizes, no fruit or non-gravity extras (A3, R8, R10, R11)

```bash
.venv/bin/python -c "from tests.test_recipe_briefs import coverage, BRIEFS; c = coverage(BRIEFS); print(', '.join(f'{k}={c[k]}' for k in ('exclusions', 'inventories', 'batch_sizes', 'batch_sizes_not_20', 'non_gravity_words')))"
```

| Expected | Actual | Result |
|---|---|---|
| exclusions ≥ 2, inventories ≥ 2, batch_sizes ≥ 3, batch_sizes_not_20 ≥ 1, non_gravity_words = 0 | exclusions=2, inventories=2, batch_sizes=4, batch_sizes_not_20=3, non_gravity_words=0 | ✅ pass |

### ✅ C8 · Every RECIPE-ROADMAP §7 hint row is used (A3, R9)

```bash
.venv/bin/python -c "from tests.test_recipe_briefs import coverage, BRIEFS; c = coverage(BRIEFS); print(', '.join(f'{k.split(\": \")[-1]}={v}' for k, v in c.items() if k.startswith('hint')))"
```

| Expected | Actual | Result |
|---|---|---|
| all 7 rows ≥ 1 | bitter=2, hoppy/juicy=1, dry/crisp=3, full/chewy=3, malty=2, darker=1, stronger/session=2 | ✅ pass |

### ✅ C9 · No style ranges in the briefs file (A4, R4)

```bash
grep -cE '[0-9]+(\.[0-9]+)? *(–|-|to) *[0-9]' evals/recipe_briefs.toml
grep -ciE '^\s*(og|fg|ibu|srm|abv)_(min|max|low|high)' evals/recipe_briefs.toml
```

| Expected | Actual | Result |
|---|---|---|
| 0, 0 | 0, 0 | ✅ pass |

### ✅ C10 · The user's review corrections are in the file (A5)

```bash
.venv/bin/python -c "import tomllib; b = {x['id']: x for x in tomllib.load(open('evals/recipe_briefs.toml', 'rb'))['brief']}; print(*(f\"{i} {b[i]['style']} alt={b[i]['alt_styles']} dev={[d['kind'] for d in b[i]['deviations']]} hints={b[i]['hints']}\" for i in ('b12', 'b16')), sep=' | '); print('b14 yeast', b['b14']['needs']['yeast'], '| b16 rice', 'flaked rice' in b['b16']['needs']['fermentables'])"
```

| Expected | Actual | Result |
|---|---|---|
| b12 31B alt 18A, no deviation; b16 18B, one ingredient deviation, `crisp`, needs flaked rice; b14 keeps Lactobacillus under yeast | `b12 31B alt=['18A'] dev=[] hints=[] \| b16 18B alt=[] dev=['ingredient'] hints=['crisp']` / `b14 yeast ['German ale yeast', 'Lactobacillus'] \| b16 rice True` | ✅ pass |

### ✅ C11 · PROJECT.md records P0, D7/D9 moved to P3, D1 out of §7 (A6, R13)

```bash
grep -cE 'recipe_briefs\.toml' PROJECT.md
grep -E '^\| D(7|9) ' PROJECT.md | grep -c 'Belongs to P3 (moved from P0, 2026-10-11)'
grep -cE '^\| D1 ' PROJECT.md
```

| Expected | Actual | Result |
|---|---|---|
| ≥ 2 (§4 row and §8 entry), 2, 0 | 3, 2, 0 | ✅ pass |

### ✅ C12 · RECIPE-ROADMAP §8 shows P0 done with the link, D7/D9 in P3 (A6, R13)

```bash
grep -E '^\| \*\*P0\*\*' docs/RECIPE-ROADMAP.md | grep -oE '✅ done 2026-10-11|recipe_briefs\.toml|D7 and D9 moved to P3' | sort -u
grep -cE 'Settle D7, D9|\(decided in P3\)' docs/RECIPE-ROADMAP.md
```

| Expected | Actual | Result |
|---|---|---|
| all three phrases; 3 (P3 row, D7, D9) | `D7 and D9 moved to P3`, `recipe_briefs.toml`, `✅ done 2026-10-11`; 3 | ✅ pass |

### ✅ C13 · PROJECT.md §2, §3 and §6 are unchanged against main (constraint)

```bash
diff <(git show main:PROJECT.md | awk '/^## (2|3|6)\./{p=1} /^## (1|4|5|7)\./{p=0} p') <(awk '/^## (2|3|6)\./{p=1} /^## (1|4|5|7)\./{p=0} p' PROJECT.md) | wc -l
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

## Part 3: Regression tests

All five critical behaviours in the plan's table have their named tests; none were missing, so
no tests were added.

Command: `.venv/bin/python -m pytest -q` (and `-v tests/test_recipe_briefs.py` for the rows below)  ·  Result: ✅ 61 passed

| Test | Protects | Result |
|---|---|---|
| tests/test_recipe_briefs.py::test_style_codes_exist_in_ref | every expected style code exists in BJCP 2021 (live DB, hard failure without it) | ✅ |
| tests/test_recipe_briefs.py::test_twenty_briefs_with_every_field | 20 briefs, every R2 field, no style-range keys | ✅ |
| tests/test_recipe_briefs.py::test_adjuncts_needed | the six adjuncts stay needed (read by `adjunct-fermentables`) | ✅ |
| tests/test_recipe_briefs.py::test_no_fruit_or_non_gravity_extras | no ingredient outside fermentable/hop/yeast/salt | ✅ |
| tests/test_recipe_briefs.py::test_style_spread | R5 style spread minimums | ✅ |
| tests/test_recipe_briefs.py::test_guidance_cases | R7 guidance case minimums | ✅ |
| tests/test_recipe_briefs.py::test_constraint_cases | R8 exclusion and inventory minimums | ✅ |
| tests/test_recipe_briefs.py::test_hint_rows | R9 every §7 hint row used | ✅ |
| tests/test_recipe_briefs.py::test_batch_sizes | R10 batch size spread | ✅ |
| tests/test_recipe_briefs.py::test_print_coverage | prints the A3 counts (`pytest -s`) | ✅ |
| the 51 existing tests | earlier work | ✅ |

Failures: none.
