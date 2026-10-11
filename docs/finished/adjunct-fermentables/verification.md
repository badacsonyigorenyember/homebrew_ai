Overall: ✅ all 16 checks and 68 tests pass

# Verification: adjunct-fermentables

Run on 2026-10-11 on branch `adjunct-fermentables` at 21c9898, against the running stack.
Brief: [brief.md](brief.md) · Plan: [plan.md](plan.md) · Review: [review.md](review.md) ·
Gap report: [report.md](report.md)

## Part 1: Summary

🎯 **Goal:** put the adjunct fermentables the recipes need (oats, candi sugar, corn, rice, lactose, honey, and whatever the 20 test briefs lack) into `ref`, sourced, with what the gravity, FG and colour maths need.

🛠️ **How:** a `--adjuncts` hopline fetch, an explicit SKU → Palmer-row map (`loaders/adjunct_products.py`) and a loader (`loaders/adjuncts.py`) that takes hopline's printed figures first and Palmer's *How to Brew* Tables 18.5/24.1 for the rest, plus a new `ref.fermentable.fermentability` column (`full` / `normal` / `none`).

🤔 **Why this way:** it is the malt loader's pattern (readable explicit map, every figure checked against the fetched page), and one reference book for every figure hopline doesn't print, as the user decided.

🏁 **Result:** 7 adjuncts in `ref` (ids 3392–3398: 4 flakes, brown candi sugar, lactose, honey), every filled field sourced; fermentability `normal` 78 / `full` 2 / `none` 1; `ref.misc` no longer accepts lactose; the gap report covers all 47 test-brief names (38 found, 7 added, 2 left out).

### 🚦 Steps

- ⏭️ 📝 **Brief:** skipped; the brief already existed and was approved (f8abb70, rebased to 3168c4e).
- ⚠️ 🗺️ **Plan:** ran twice and was approved as written in a84bf8d, with candi sugar on Palmer's table-sugar row, flaked barley added for b05 and Special B left out.
  - ⚠️ Run 1 returned needs-input: the branch was cut before `test-briefs` merged; run 2 rebased onto `main` (249a452).
  - ⚠️ Run 1 asked about Lactobacillus (b14); the user chose to leave it out (recorded in the gap report).
- ❌ 🔨 **Implement:** all 5 tasks done (28ed14c, 90ab804, 58a222c, d550920, 388c772) plus one review fix (d2c892a); 68 tests pass. 🔧 fixed in 388c772
  - ❌ Task 5 was blocked: the subagent's Write tool refused to create `report.md`; with the user's authorization the orchestrator wrote the checked content verbatim and ran the coverage command (`missing: []`). 🔧 fixed in 388c772
  - ⚠️ Task 1 set DATABASE.md's source count to 17 as measured then, for Task 4 to update; it now reads 18 (checked in this run).
  - ⚠️ DATABASE.md's `water_salt` row still says "empty" though 8 salts are loaded; left alone as out of scope (still so in this run).
- ⚠️ 🔍 **Review:** ready for testing, 0 must-fix; re-review (21c9898) found no new findings. 🔧 fixed in d2c892a
  - ⚠️ Should-fix 1: sugar and honey extracts are as-sold PPG ÷ 46 in a dry-basis column, undocumented; now documented in DATABASE.md and the loader docstring (plan deviation). 🔧 fixed in d2c892a
  - ⚠️ Note 2: Brown Candi Sugar's extract and `full` come from Palmer's table-sugar row (a sucrose proxy); approved in the plan, no action.
- ✅ 🧪 **Verify:** every check of A1–A8 ran against the database, the PDF and the fetched pages; the loader was run once more and the fingerprint is unchanged. 🧮 spot checks ✅ 16/16 · 🧪 tests ✅ 68/68

👀 **Start here:** [report.md](report.md) Part 2: the 7 new rows with their extract, colour, max % and fermentability, each value marked Palmer or hopline, and each `NULL` with its reason.

📁 **Changed files:**
- `PROJECT.md`
- `db/010_ref_schema.sql`
- `db/011_ref_sources.sql`
- `db/012_style_fit.sql`
- `docs/DATABASE.md`
- `docs/STYLE-FIT.md`
- `docs/work/adjunct-fermentables/brief.md`
- `docs/work/adjunct-fermentables/plan.md`
- `docs/work/adjunct-fermentables/report.md`
- `docs/work/adjunct-fermentables/review.md`
- `loaders/adjunct_products.py`
- `loaders/adjuncts.py`
- `loaders/fetch_hopline.py`
- `tests/test_adjuncts.py`
- `tests/test_fetch_hopline.py`

## Part 2: Spot checks

All commands run from the repo root. Database queries are read-only. The one write is the
setup step of C15, the loader's own idempotent upsert, which A8 asks for.

### ✅ C1 · the six adjuncts and flaked barley have ingredient + fermentable rows (A1)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select i.id, i.name, i.kind from ref.ingredient i join ref.fermentable f on f.ingredient_id = i.id where i.name in ('Flaked Oats','Brown Candi Sugar','Flaked Corn','Flaked Rice','Lactose','Honey','Flaked Barley') order by i.id"
```

| Expected | Actual | Result |
|---|---|---|
| 7 rows, kind `fermentable`: Flaked Oats, Flaked Corn, Flaked Rice, Flaked Barley, Brown Candi Sugar, Lactose, Honey | 3392\|Flaked Corn\|fermentable<br>3393\|Flaked Oats\|fermentable<br>3394\|Flaked Barley\|fermentable<br>3395\|Flaked Rice\|fermentable<br>3396\|Brown Candi Sugar\|fermentable<br>3397\|Lactose\|fermentable<br>3398\|Honey\|fermentable | ✅ pass |

### ✅ C2 · no ingredient without a source (A2)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.ingredient where source_id is null"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C3 · every filled field of the new rows has a `field_source` entry (A2)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.ingredient i join ref.fermentable f on f.ingredient_id = i.id join ref.source s on s.id = i.source_id cross join lateral (values ('extract_dbfg_pct', f.extract_dbfg_pct is not null), ('ebc', f.ebc is not null), ('max_pct', f.max_pct is not null), ('fermentability', f.fermentability <> 'normal')) v(k, filled) where s.slug in ('hopline-adjuncts', 'palmer-how-to-brew') and v.filled and not f.field_source ? v.k"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C4 · the new rows' values and sources match report.md Part 2 (A3)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select i.name, f.extract_dbfg_pct, f.ebc, f.max_pct, f.fermentability, f.field_source from ref.ingredient i join ref.fermentable f on f.ingredient_id = i.id join ref.source s on s.id = i.source_id where s.slug in ('hopline-adjuncts','palmer-how-to-brew') order by i.name"
```

| Expected | Actual | Result |
|---|---|---|
| Extract filled on all 7; EBC only on candi (225, hopline); max % only on rice (40, hopline); all other EBC and max % `NULL`, as listed with reasons in report.md Part 2 | Brown Candi Sugar\|100.0\|[225,225]\|\|full\|{"ebc": "hopline-adjuncts", "fermentability": "palmer-how-to-brew", "extract_dbfg_pct": "palmer-how-to-brew"}<br>Flaked Barley\|70.0\|\|\|normal\|{"extract_dbfg_pct": "palmer-how-to-brew"}<br>Flaked Corn\|84.0\|\|\|normal\|{"extract_dbfg_pct": "palmer-how-to-brew"}<br>Flaked Oats\|70.0\|\|\|normal\|{"extract_dbfg_pct": "palmer-how-to-brew"}<br>Flaked Rice\|82.0\|\|40.0\|normal\|{"max_pct": "hopline-adjuncts", "extract_dbfg_pct": "palmer-how-to-brew"}<br>Honey\|82.6\|\|\|full\|{"fermentability": "palmer-how-to-brew", "extract_dbfg_pct": "palmer-how-to-brew"}<br>Lactose\|100.0\|\|\|none\|{"fermentability": "hopline-adjuncts", "extract_dbfg_pct": "palmer-how-to-brew"} | ✅ pass |

### ✅ C5 · the hopline flake and lactose pages print no colour, so their `NULL` EBC is right (A3)

```bash
.venv/bin/python -c "
import json, re
d = json.load(open('shared/rag-files/pending/hopline_adjuncts.json', encoding='utf-8'))
t = {p['sku']: p['text'] for p in d['products']}
print(sorted(s for s in ['400150', '400270', '400110', '400030-cs'] if re.search(r'\d+\s*EBC', t[s])))"
```

| Expected | Actual | Result |
|---|---|---|
| `[]` (no "N EBC" on the oat, corn, barley and lactose pages) | `[]` | ✅ pass |

### ✅ C6 · fermentability counts (A4)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select fermentability, count(*) from ref.fermentable group by 1 order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| full 2, none 1, normal 78 (74 malts + 4 flakes) | full\|2<br>none\|1<br>normal\|78 | ✅ pass |

### ✅ C7 · fermentability per adjunct (A4)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select i.name, f.fermentability from ref.ingredient i join ref.fermentable f on f.ingredient_id = i.id join ref.source s on s.id = i.source_id where s.slug in ('hopline-adjuncts','palmer-how-to-brew') order by i.name"
```

| Expected | Actual | Result |
|---|---|---|
| lactose `none`; honey, candi `full`; the 4 flakes `normal` | Brown Candi Sugar\|full<br>Flaked Barley\|normal<br>Flaked Corn\|normal<br>Flaked Oats\|normal<br>Flaked Rice\|normal<br>Honey\|full<br>Lactose\|none | ✅ pass |

### ✅ C8 · every malt is `normal` (A4)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.fermentable f join ref.ingredient i on i.id = f.ingredient_id join ref.source s on s.id = i.source_id where s.slug not in ('hopline-adjuncts','palmer-how-to-brew') and f.fermentability <> 'normal'"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C9 · `ref.misc`'s category check no longer accepts lactose (A5)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select pg_get_constraintdef(oid) from pg_constraint where conname = 'misc_category_check'"
```

| Expected | Actual | Result |
|---|---|---|
| a check list without `lactose` | CHECK ((category = ANY (ARRAY['spice'::text, 'herb'::text, 'fruit'::text, 'wood'::text, 'coffee'::text, 'cacao'::text, 'vanilla'::text, 'smoke'::text, 'fining'::text, 'other'::text]))) | ✅ pass |

### ✅ C10 · DATABASE.md describes lactose and honey as fermentables; STYLE-FIT.md no longer lists lactose as misc (A5)

```bash
grep -cE "Anything with gravity \(malts, flakes, sugars, lactose, honey\) is a .fermentable.|lactose stays whole in FG|Extras without gravity data \(cinnamon, vanilla\) are .misc." docs/DATABASE.md; grep -c "lactose" docs/STYLE-FIT.md
```

| Expected | Actual | Result |
|---|---|---|
| 3 (the fermentable rule, lactose in FG, the misc rule), then 0 | 3<br>0 | ✅ pass |

### ✅ C11 · the flake extracts match Palmer Table 18.5 as printed (A7)

```bash
pdftotext -f 315 -l 315 -layout shared/rag-files/pending/how_to_brew.pdf - | grep -E "^ (Oatmeal|Corn|Barley|Rice) \(flaked\)" | awk '{print $1, $2, $3}'
```

| Expected | Actual | Result |
|---|---|---|
| oats 70 %, corn 84 %, barley 70 %, rice 82 % (the loaded 70.0, 84.0, 70.0, 82.0 in C4) | Oatmeal (flaked) 70%<br>Corn (flaked) 84%<br>Barley (flaked) 70%<br>Rice (flaked) 82% | ✅ pass |

### ✅ C12 · the sugar rows match Palmer Table 24.1 as printed (A7)

```bash
pdftotext -f 462 -l 462 -layout shared/rag-files/pending/how_to_brew.pdf - | grep -E "^  (Table sugar|Lactose|Honey) " | awk '{if ($1=="Table") print $1, $2, $3, $5; else print $1, $2, $4}'
```

| Expected | Actual | Result |
|---|---|---|
| table sugar 46 PPG 100 % (candi: 100.0, `full`); lactose 46 PPG "…" (100.0, `none`); honey 38 PPG 95 % (82.6, `full`) | Table sugar 46 100%<br>Lactose 46 …<br>Honey 38 95% | ✅ pass |

### ✅ C13 · every hopline figure's quoted words are on its fetched page (A7)

```bash
.venv/bin/python -c "
import json
from loaders.adjunct_products import PRODUCTS
d = json.load(open('shared/rag-files/pending/hopline_adjuncts.json', encoding='utf-8'))
t = {p['sku']: p['text'] for p in d['products']}
print([(sku, f, v, w in t[sku]) for sku, (_, _, figs) in PRODUCTS.items() for f, (v, w) in figs.items()])"
```

| Expected | Actual | Result |
|---|---|---|
| rice max 40, candi EBC 225, lactose `none`, each `True` | [('400100', 'max_pct', '40', True), ('400091-cs', 'ebc', '225', True), ('400030-cs', 'fermentability', 'none', True)] | ✅ pass |

### ✅ C14 · the gap report covers every test-brief ingredient (A6)

```bash
.venv/bin/python -c "
import tomllib, re
briefs = tomllib.load(open('evals/recipe_briefs.toml','rb'))['brief']
names = {n for b in briefs for n in [*b['wanted'], *b['excluded'], *b['inventory'], *[x for v in b['needs'].values() for x in v]]}
report = open('docs/work/adjunct-fermentables/report.md', encoding='utf-8').read()
missing = sorted(n for n in names if not re.search(r'\|\s*' + re.escape(n) + r'\s*\|', report))
print(len(names), 'names;', 'missing:', missing)"
```

| Expected | Actual | Result |
|---|---|---|
| `missing: []` | 47 names; missing: [] | ✅ pass |

Both `left out` rows (Special B, Lactobacillus) carry a reason in report.md.

### ✅ C15 · loading again changes nothing (A8)

Setup, run once in this verification (a third load after Task 4's two):
`.venv/bin/python -m loaders.adjuncts --hopline shared/rag-files/pending/hopline_adjuncts.json`
→ `loaded: 7 adjuncts`, `skipped: 7 hopline products (see SKIPPED in loaders/adjunct_products.py)`.
The fingerprint below was also taken before that load: same value.

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*), md5(string_agg(i.name || i.raw::text || f::text, '|' order by i.name)) from ref.ingredient i join ref.fermentable f on f.ingredient_id = i.id join ref.source s on s.id = i.source_id where s.slug in ('hopline-adjuncts', 'palmer-how-to-brew')"
```

| Expected | Actual | Result |
|---|---|---|
| 7\|ca6c03d7ba34b2876328337122a2e288 (Task 4, both runs) | 7\|ca6c03d7ba34b2876328337122a2e288 | ✅ pass |

### ✅ C16 · the Palmer and hopline-adjuncts sources are in `ref.source` (R2, R7)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.source"
```

| Expected | Actual | Result |
|---|---|---|
| 18 | 18 | ✅ pass |

## Part 3: Regression tests

Every test in the plan's *Critical behaviour and its tests* table exists; none had to be added.
The two catalog-query rows of that table are C6–C9 and C15 above.

Command: `.venv/bin/python -m pytest`  ·  Result: ✅ 68 passed

| Test | Protects | Result |
|---|---|---|
| tests/test_adjuncts.py::test_extract_pct_from_ppg | Palmer PPG → extract % (46 → 100.0, 38 → 82.6) | ✅ |
| tests/test_adjuncts.py::test_build_values_per_adjunct | each adjunct gets the printed extract, colour, max % and the right fermentability | ✅ |
| tests/test_adjuncts.py::test_every_filled_field_has_a_source | every filled field names its source; `normal` needs none | ✅ |
| tests/test_adjuncts.py::test_unmapped_sku_raises | a new hopline product never loads without a decision | ✅ |
| tests/test_adjuncts.py::test_hopline_figure_not_on_page_raises | a hand-typed hopline figure must be on the page | ✅ |
| tests/test_adjuncts.py::test_maps_do_not_overlap | the SKU maps and Palmer rows are consistent | ✅ |
| tests/test_fetch_hopline.py::test_page_text_runs_from_main_category_to_reviews | the page text the adjunct figures are read from | ✅ |
