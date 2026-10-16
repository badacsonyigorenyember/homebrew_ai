# Verification: s6-style-neighbours

Overall: ✅ all 10 checks and 674 tests pass

Stage: verify  ·  Branch: s6-style-neighbours  ·  Run 2026-10-16 at 8415545

## Part 1: Summary

🎯 **Goal:** Measure how well step 2 tells apart the BJCP exam's neighbouring styles, re-check the 21 envelopes against Barnes' 2008 cards, and check D1 against BJCP 2021's specialty-entry text.

🛠️ **How:** A check set of 91 study-guide triples and 83 briefs (`evals/style_neighbours.toml`), a runner that sends each brief to `app.step2_best_style` with guide `any` in Run A (no family noun) and Run B (family noun as `named`), a hand-written Barnes cross-check decided by you, and a specialty-entry note.

🤔 **Why this way:** Report only, no pass bar and no step 2 change, so tuning is decided from a measured baseline; the briefs use only words and numbers from each style's 2021 entry so the set is not fitted to the scorer.

🏁 **Result:** Run A picks the right style first on 75/83 (90%) and has it in the top 3 on 83/83. On the 61 briefs of the 50 single-family triples, Run A gets 55/61 and Run B 44/61 right first (gap -11, -18 points); top 3 is 61/61 against 57/61. 65 envelope differences were decided (62 keep, 3 changed and loaded); D1 left as is.

### 🚦 Steps

- ✅ 📝 **Brief:** Folded in your answers (numbers and words, report only, keep the Barnes check); approved in 35fcec6.
- ✅ 🗺️ **Plan:** Resumed once for "1b" (guide `any`) and "2c" (Runs A and B with the gap); planner measured that `named` boosts and does not filter. Approved in dda69e2.
- ⚠️ 🔨 **Implement:** Six tasks done (7cacbe7, 288c1ce, c16ab63, 4d2c05f, 79495e1, 2fdb99e), plus a review-fix round (8415545).
  - ⚠️ Style count corrected from 84 to 83 (Vienna and Vienna Lager are both 7A); Deviations in brief and plan.
  - ⚠️ Task 2: the full-suite summary line was lost (dots only, no failures seen); `wheat` barred as a family noun, words checked through `app.brief_words`; some request wording is unnatural ("beechwood", "Maillard").
  - ⚠️ Task 5: card-silent dimensions listed separately, not counted as differences (Deviation).
  - ⚠️ Task 6: `guard.sh` blocked a check of the environment file; the command was re-run without it.
  - ⚠️ Review fixes: first `test_reload_is_identical` failed because the DB still held the old quotes; a reload fixed it. The new 20B roast quote backs acrid but no longer covers coffee and chocolate.
- ⚠️ 🔍 **Review:** Ready for testing, no must-fix; 2 should-fix (stale quotes on the 3 changed envelopes, stale cross-check header) 🔧 fixed in 8415545.
  - ⚠️ Note: `top3` can list the same style twice (a BA candidate shown as its BJCP pair), 10 of 83 Run A briefs and 19 of 61 Run B briefs; re-measured with distinct styles the top-3 misses are unchanged (A 0, B 4).
  - ⚠️ Note: some request sentences hold extra descriptive words not checked against the 2021 entry; no effect, since step 2 does not read the request when the guide is passed.
- ✅ 🧪 **Verify:** All checks and the whole suite pass; step 2 unchanged. 🧮 spot checks ✅ 10/10 · 🧪 tests ✅ 674/674

👀 **Start here:** The runner output in Part 2, example 1 (`python -m evals.style_neighbours`): the four-line table at the top is the measured result.

📁 **Changed files:**
- `PROJECT.md`
- `docs/work/s6-style-neighbours/brief.md`
- `docs/work/s6-style-neighbours/envelope-crosscheck.md`
- `docs/work/s6-style-neighbours/plan.md`
- `docs/work/s6-style-neighbours/review.md`
- `docs/work/s6-style-neighbours/specialty-entry.md`
- `evals/results/2026-10-16-s6.json`
- `evals/style_neighbours.py`
- `evals/style_neighbours.toml`
- `loaders/style_envelopes.toml`
- `tests/test_style_neighbours.py`

(`docs/work/s6-style-neighbours/verification.md` is added by this verification.)

## Part 2: Showcase

| Piece | What it does |
|---|---|
| `evals/style_neighbours.toml` | 91 study-guide triples and 83 briefs, one per style |
| `evals/style_neighbours.py` | Runs the briefs through step 2 (guide `any`), Runs A and B, prints the gap |
| `envelope-crosscheck.md` | 65 Barnes-vs-envelope differences with your decisions |
| `specialty-entry.md` | BJCP 2021 specialty-entry text vs D1; declined |
| `loaders/style_envelopes.toml` | 3 envelope rows changed (18A malt, 20B roast, 25B body) |

**1. The measured result** (read-only: no `--save`)

```bash
.venv/bin/python -m evals.style_neighbours | head -6
```

```text
guide: any   briefs: 83   triples: 91 (50 single-family, 41 mixed: A only)
                               right first         top 3  no style  BA picks
Run A, all briefs                75/83 90%    83/83 100%         0         0
Run A, Run B briefs              55/61 90%    61/61 100%         0         0
Run B (family named)             44/61 72%     57/61 93%         0         0
gap B - A                        -11 (-18 pts)      -4 (-7 pts)
```

**2. One brief, as a brewer would write it (Scottish Light, 14A)**

```bash
.venv/bin/python -c "
from evals.style_neighbours import *
from loaders.db import connect
t,b=load(); br={x['code']:x for x in b}
with connect() as c:
    x=br['14A']; print(x['request']); print(measure(c,x))
"
```

```text
A malty session beer with toffee and butterscotch, about 2.8% ABV.
{'code': '14A', 'picked': '14A', 'top3': ['14A', '27D', '5A'], 'right_first': True, 'in_top3': True}
```

**3. A miss: a hoppy roasty stout brief (20B) goes to 20C in both runs**

```bash
.venv/bin/python -c "
from evals.style_neighbours import *
from loaders.db import connect
t,b=load(); br={x['code']:x for x in b}; fam=run_b_family(t)
with connect() as c:
    x=br['20B']; print(x['request']); print('A', measure(c,x)); print('B', measure(c,x,fam['20B']))
"
```

```text
A hoppy, bitter, roasty beer with citrus hop flavor, about 65 IBU and SRM 35.
A {'code': '20B', 'picked': '20C', 'top3': ['20C', '20B', '16D'], 'right_first': False, 'in_top3': True}
B {'code': '20B', 'picked': '20C', 'top3': ['20C', '20B', '16D'], 'right_first': False, 'in_top3': True}
```

**4. What the family noun does: triple 63 (barley wines), Run A vs Run B**

```bash
.venv/bin/python -m evals.style_neighbours | grep -A2 '^#63 '
```

```text
#63  17D / 17B / 17C  A  17D:ok  17B:ok  17C:ok
                  B  17D:other 17A  17B:ok  17C:17B   ["ale" name score 17C=0.0  17D=0.0  17B=0.5]
```

**5. The three applied envelope fixes** (diff of the toml against main)

```bash
git diff main...s6-style-neighbours -- loaders/style_envelopes.toml | grep '^[+-]' | grep -v '^+++\|^---' | grep -E 'max =|characters ='
```

```text
-max = "medium-low"
+max = "medium"
-characters = ["bready"]
+characters = ["bready", "toasty", "biscuit"]
-characters = ["roast", "coffee", "chocolate"]
+characters = ["roast", "coffee", "chocolate", "acrid"]
```

## Part 3: Spot checks

### ✅ C1 · Check set has 91 triples and 83 briefs, one per distinct style (A1)

```bash
.venv/bin/python -c "
import tomllib
d=tomllib.load(open('evals/style_neighbours.toml','rb'))
codes={c for t in d['triple'] for c in t['codes']}
print(len(d['triple']),len(d['brief']),len(codes),codes=={b['code'] for b in d['brief']})"
```

| Expected | Actual | Result |
|---|---|---|
| 91 83 83 True | 91 83 83 True | ✅ pass |

### ✅ C2 · No brief request contains a BJCP 2021 style name (A1, R1)

Independent of the test: accent-folded, whole-phrase match of every BJCP name against every request.

```bash
.venv/bin/python -c "
import tomllib,re,unicodedata
from loaders.db import connect
d=tomllib.load(open('evals/style_neighbours.toml','rb'))
f=lambda s:''.join(c for c in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(c)!='Mn')
with connect() as c:
    ns=[f(n) for (n,) in c.execute(\"select name from ref.beer_style where guide='BJCP'\")]
    print([(b['code'],n) for b in d['brief'] for n in ns if re.search(r'\b'+re.escape(n)+r'\b',f(b['request']))])"
```

| Expected | Actual | Result |
|---|---|---|
| `[]` | `[]` | ✅ pass |

### ✅ C3 · Every stated number lies in the style's 2021 range (A2, R2)

```bash
.venv/bin/python -c "
import tomllib
from loaders.db import connect
d=tomllib.load(open('evals/style_neighbours.toml','rb'))
with connect() as c:
    print([(b['code'],k,v) for b in d['brief'] for k,v in b['stated'].items() if not c.execute(f\"select %s::numeric <@ {k} from ref.beer_style where guide='BJCP' and code=%s\",(v,b['code'])).fetchone()[0]])"
```

| Expected | Actual | Result |
|---|---|---|
| `[]` | `[]` | ✅ pass |

### ✅ C4 · Family noun is a family word only, 50 single-family triples (A1)

```bash
.venv/bin/pytest -q tests/test_style_neighbours.py -k "family" 2>&1 | tail -1
.venv/bin/python -c "
import tomllib
d=tomllib.load(open('evals/style_neighbours.toml','rb'))
print(sum(1 for t in d['triple'] if t['family']), sorted({t['family'] for t in d['triple'] if t['family']}))"
```

| Expected | Actual | Result |
|---|---|---|
| tests pass; 50 single-family; nouns within ale, lager, bock, ipa, porter, stout, wheat | tests pass (see Part 4); 50 single-family, nouns within that list | ✅ pass |

### ✅ C5 · Step 2 is unchanged: no diff to `db/` (A4, R4)

```bash
git diff main -- db/022_step2.sql | wc -l; git diff main --stat -- db | wc -l
```

| Expected | Actual | Result |
|---|---|---|
| 0 and 0 | 0 and 0 | ✅ pass |

### ✅ C6 · Saved result matches the runner and PROJECT.md §8 (A3, R3, R4)

```bash
.venv/bin/python -c "
import json
r=json.load(open('evals/results/2026-10-16-s6.json'))
print(r['guide'],r['mixed_triples'],r['run_a_all']['right_first'],r['run_a_all']['in_top3'],r['run_b']['n'] if 'n' in r['run_b'] else '',r['gap']['right_first'],r['gap']['in_top3'])"
grep -c "right first 75/83 (90%), top 3 83/83 (100%)" PROJECT.md
```

| Expected | Actual | Result |
|---|---|---|
| `any 41 75 83 61 -11 -4` and 1 PROJECT.md line with 75/83 and 83/83 | `any 41 75 83 61 -11 -4` and `1` | ✅ pass |

### ✅ C7 · Envelope DB rows: 25B body max medium, counts 189 / 240, all reviewed (A5, R6)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select b.code,s.dimension,s.min_level,s.max_level,s.reviewed from ref.style_sensory s join ref.beer_style b on b.id=s.style_id where b.code='25B' and s.dimension='body'"
docker exec supabase-db psql -U postgres -d postgres -tAc "select (select count(*) from ref.style_sensory)||' '||(select count(*) from ref.style_character)||' unreviewed '||(select count(*) from ref.style_sensory where not reviewed)"
```

| Expected | Actual | Result |
|---|---|---|
| `25B|body|2|4|t` (4 = medium); `189 240 unreviewed 0` | `25B|body|2|4|t`; `189 240 unreviewed 0` | ✅ pass |

### ✅ C8 · Cross-check: all 65 difference rows have a decision (A5, R5)

```bash
awk -F'|' '/^\| D[0-9]/ {n++; d=$(NF-1); gsub(/ /,"",d); if(d=="")e++} END{print n, e+0}' docs/work/s6-style-neighbours/envelope-crosscheck.md
```

| Expected | Actual | Result |
|---|---|---|
| 65 rows, 0 empty | 65 0 | ✅ pass |

### ✅ C9 · Specialty-entry note exists with the decision recorded (A6, R7)

```bash
grep -n "^## Decision" -A1 docs/work/s6-style-neighbours/specialty-entry.md | cut -c1-80
```

| Expected | Actual | Result |
|---|---|---|
| a Decision section saying declined | `## Decision` / `Declined (user, 2026-10-16, option a): D1 and step 2 stay as they are...` | ✅ pass |

### ✅ C10 · Commits are one line, at most 60 characters, no body or trailer

```bash
git log --format='%s' main..s6-style-neighbours | awk '{print length($0)}' | sort -n | tail -1; git log --format='%b' main..s6-style-neighbours | grep -c .
```

| Expected | Actual | Result |
|---|---|---|
| longest 60 or less; 0 body lines | 45; 0 | ✅ pass |

## Part 4: Regression tests

Command: `.venv/bin/pytest -q`  ·  Result: ✅ 674 passed (143.6 s)

| Test | Protects | Result |
|---|---|---|
| tests/test_style_neighbours.py::test_triples_are_the_91, test_83_distinct_styles, test_triple_names_match_2021 | The triples and codes match the study guide and `ref` | ✅ |
| tests/test_style_neighbours.py::test_triple_family_from_2021_tags, test_family_is_a_family_word_only, test_one_family_per_style | Family noun follows BJCP tags and is never a style name | ✅ |
| tests/test_style_neighbours.py::test_no_style_name_in_request, test_brief_shape | No brief gives its style away; `named` empty in Run A | ✅ |
| tests/test_style_neighbours.py::test_stated_numbers_in_2021_range, test_words_from_2021_entry | Numbers in range, words from the 2021 entry | ✅ |
| tests/test_style_neighbours.py::test_briefs_fit_step1_contract | Briefs are valid step 1 output | ✅ |
| tests/test_style_neighbours.py::test_summarise_first_and_top3, test_confusions_partner_other_none, test_measure_one_brief, test_ba_candidate_written_as_pair | Right-first, top 3 and confusions counted correctly; BA picks are named misses | ✅ |
| tests/test_style_neighbours.py::test_run_b_only_single_family, test_gap_on_same_briefs | Run B covers single-family triples only; gap compares the same briefs | ✅ |
| tests/test_style_envelopes.py::test_reload_is_identical, test_26_styles_reviewed | Envelope loads identically twice; quotes are in the 2021 text | ✅ |
| tests/test_style_fit_golden.py, test_style_fit_recipe.py, test_style_level.py | Golden set and reference recipes stay green after the 3 envelope fixes | ✅ (192 passed together with the style-neighbours and envelope tests) |

Failures: none.
