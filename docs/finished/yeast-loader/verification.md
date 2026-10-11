# Verification: yeast-loader

Overall: ✅ all 24 checks and 48 tests pass

Branch `yeast-loader` at fb2ec2f, verified 2026-10-11 (second run; the first, at 7c310c6,
passed 20/20 checks and 46/46 tests and predates the English-only change). No brief; checked
against `plan.md` (its Approach, each task's Done-when line, the *Critical behaviour and its
tests* table), `review.md` (both rounds), the user decisions in the plan's Deviations, and the
user's request after the first verification: "Don´t use Hungarian words, instead translate
everything to english. Like Bajor búza" (scope: every value written outside `raw` and the
printed provenance is English; quotes kept as printed get an English gloss).

## Part 1: Summary

🎯 **Goal:** load every beer yeast hopline.hu sells into `ref.yeast`, sourced, in SI units, in English, with attenuation for FG.

🛠️ **How:** fetch hopline's dry and liquid yeast pages (their product lists come from the page's own AJAX listing), map each SKU explicitly to a yeast with an English name, parse the data block (description as fallback), and take attenuation as printed from the maker sources and Brewfather figures the user named.

🤔 **Why this way:** the user wanted the shop's own yeasts, as for malts and hops, and no hopline page states attenuation, so each figure comes from a named source with its printed text kept in `raw`, while everything outside `raw` is English as the user asked.

🏁 **Result:** `ref.yeast` holds 119 yeasts (dry 81, liquid 38; 8 producers, Brewline 10 rows of its own, `302170` now `Bavarian Wheat`), all with temperature, 113 with flocculation, 114 with alcohol tolerance, 93 with attenuation from 6 sources; no Hungarian outside `raw`; every Hungarian quote in `report.md` (35) carries an English gloss.

### 🚦 Steps

- ⏭️ 📝 **Brief:** skipped, a draft plan already existed (source: `docs/FILL-REF-README.md` item 6).
- ✅ 🗺️ **Plan:** 4 rounds: rewritten from the Brewtarget files to hopline's yeast pages, then the user's answers applied (Brewline own rows, 2 g packs joined, non-beer skipped, M20 data block, attenuation sources); approved in a703f82.
- ⚠️ 🔨 **Implement:** 6 tasks done (42fb3d2, 2d51fc0, 9ed2117, 15c3e72, fd98582, 4ea42cf, 650a5e8), one review-fix round (7c310c6).
  - ⚠️ Task 1: `details` added in the yeast fetch only, not `product_page` (the malt fetch would break); labels end at `<br`, `</p>` or `<strong>`.
  - ⚠️ Task 1: M54 `302220-H` and M84 `302250-H` have odd temperature labels (handled in the Task 5 report).
  - ⚠️ Task 4: SafBrew BR-8 and M36 Liberty Bell Ale were named from memory (confirmed on the makers' sites in Task 6).
  - ⚠️ Task 5: `BREWLINE_COPIES` added for the report; temperature compared on 125 pages, not the planned 121.
  - ⚠️ Task 6: hopline's maker links point at the wrong strain or a dead page for Fermentis BE-256, S-33, BR-8 and Mangrove Jack's M20, M47, M84, so the strains' own maker pages were read; Lallemand read from product pages (Suava from its data sheet).
  - ⚠️ Task 6: the Brewline catalogue PDF lists none of the 10 products; the user supplied Brewfather figures instead and the `brewline-catalogue` source was removed.
- ⚠️ 🔍 **Review:** ready for testing (d30ba59), 0 must-fix, 1 should-fix, 2 notes.
  - ⚠️ should-fix: `docs/RECIPE-ROADMAP.md` still named Brewtarget and an open D8 🔧 fixed in 7c310c6 (C20).
  - ⚠️ note: no test ties each attenuation figure to its printed text (checked one-off here, C16: 92/92 match).
  - ⚠️ note: the `brewline-catalogue` delete only cleans the running DB (harmless; C7 shows it gone).
- ⚠️ 🧪 **Verify (round 1):** ✅ 20/20 checks, ✅ 46/46 tests (c8fd791); the user answered "Not yet" to shipping and asked for no Hungarian words.
  - ⚠️ change request: "Bajor Búza" was the one Hungarian DB value 🔧 fixed in 28c4cf0 (C21, C22).
- ✅ 🔨 **Implement (change request):** 28c4cf0: Brewline `302170` renamed in place to `Bavarian Wheat` by `db/011` (same id, no 120th row), `hopline-yeasts` source note and report labels in English, new `test_no_hungarian_outside_raw`; 47 tests.
- ⚠️ 🔍 **Re-review:** ready for testing (9daa86e), 0 must-fix, 2 notes.
  - ⚠️ note: two Hungarian quotes in `report.md` had no English gloss (`'Belga Ale'`, `max tartomány`) 🔧 fixed in fb2ec2f (C24).
  - ⚠️ note: `verification.md` predated the change 🔧 rewritten by this run.
- ✅ 🔨 **Implement (re-review note 1):** fb2ec2f: glosses from `STYLE_FAMILIES_EN`, `FLOCCULATION` and `DESCRIPTION_PHRASES_EN`, new `test_report_glosses_hungarian_quotes`; 48 tests, counts unchanged.
- ✅ 🧪 **Verify (round 2):** all checks and the whole suite run on the live DB; the loader re-run kept 119 rows (one `Bavarian Wheat`) and regenerated `report.md` byte for byte. 🧮 spot checks ✅ 24/24 · 🧪 tests ✅ 48/48

👀 **Start here:** [`report.md`](report.md), section "Brewline rows and the strains their pages say they copy": `Bavarian Wheat (302170) copies SafAle WB-06` and `'Belga Ale' (Belgian ale)` show the English names and glosses; below it, "Yeasts without attenuation (26)" gives every yeast without a figure with its reason.

📁 **Changed files:**
- `PROJECT.md`
- `db/010_ref_schema.sql`
- `db/011_ref_sources.sql`
- `docs/DATABASE.md`
- `docs/FILL-REF-README.md`
- `docs/RECIPE-ROADMAP.md`
- `docs/work/yeast-loader/plan.md`
- `docs/work/yeast-loader/report.md`
- `docs/work/yeast-loader/review.md`
- `docs/work/yeast-loader/verification.md`
- `loaders/fetch_hopline.py`
- `loaders/yeast_products.py`
- `loaders/yeasts.py`
- `tests/test_fetch_hopline.py`
- `tests/test_yeasts.py`

## Part 2: Spot checks

### ✅ C1 · Row and field counts (Task 5, Task 6)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*), count(temp_c), count(flocculation), count(alcohol_tolerance_pct), count(attenuation_pct) from ref.yeast"
```

| Expected | Actual | Result |
|---|---|---|
| 119\|119\|113\|114\|93 | 119\|119\|113\|114\|93 | ✅ pass |

### ✅ C2 · Form split (Task 5)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select form, count(*) from ref.yeast group by 1 order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| dry 81, liquid 38 | dry\|81, liquid\|38 | ✅ pass |

### ✅ C3 · Rows per producer (Approach)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select i.producer, count(*) from ref.yeast y join ref.ingredient i on i.id = y.ingredient_id group by 1 order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| YeastFlow 38, Lallemand 18, Norse Nectar 17, Fermentis 13, Mangrove Jack's 13, Brewline 10, Gozdawa 9, YeasterBunny 1 | Brewline 10, Fermentis 13, Gozdawa 9, Lallemand 18, Mangrove Jack's 13, Norse Nectar 17, YeasterBunny 1, YeastFlow 38 | ✅ pass |

### ✅ C4 · US-05 row (Task 5 Done-when, Task 6)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select y.product_id, y.form, y.type, y.temp_c, y.flocculation, y.alcohol_tolerance_pct, y.attenuation_pct, y.field_source->>'attenuation_pct', (select count(*) from jsonb_object_keys(i.raw->'hopline-yeasts')) from ref.yeast y join ref.ingredient i on i.id=y.ingredient_id where y.product_id='US-05'"
```

| Expected | Actual | Result |
|---|---|---|
| US-05, dry, ale, [18,28], medium, 11.0, attenuation from fermentis-datasheets, 1 hopline SKU in raw | US-05\|dry\|ale\|[18,28]\|medium\|11.0\|[78,82]\|fermentis-datasheets\|1 | ✅ pass |

### ✅ C5 · Every yeast ingredient sourced to hopline-yeasts (Task 5)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.ingredient where kind = 'yeast' and source_id <> (select id from ref.source where slug = 'hopline-yeasts')"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C6 · Attenuation per source (Task 6)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select coalesce(field_source->>'attenuation_pct','none'), count(*) from ref.yeast group by 1 order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| brewfather 16, fermentis 12, lallemand 17, mangrovejacks 13, user-supplied 1, yeastflow 34, none 26 (as in PROJECT.md §5) | brewfather 16, fermentis-datasheets 12, lallemand-catalogue 17, mangrovejacks-datasheets 13, none 26, user-supplied 1, yeastflow-catalogue 34 | ✅ pass |

### ✅ C7 · Sources: 16, hopline-yeasts in, brewtarget-default-data and brewline-catalogue out (Task 2, Task 6)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*), bool_or(slug='hopline-yeasts'), bool_or(slug='brewtarget-default-data'), bool_or(slug='brewline-catalogue') from ref.source"
```

| Expected | Actual | Result |
|---|---|---|
| 16\|t\|f\|f | 16\|t\|f\|f | ✅ pass |

### ✅ C8 · `ref.yeast.field_source` is jsonb not null (Task 2)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select is_nullable, data_type from information_schema.columns where table_schema='ref' and table_name='yeast' and column_name='field_source'"
```

| Expected | Actual | Result |
|---|---|---|
| NO\|jsonb | NO\|jsonb | ✅ pass |

### ✅ C9 · Norse Nectar and YeasterBunny loaded, attenuation NULL (user decision)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select i.producer, count(*), count(y.attenuation_pct) from ref.yeast y join ref.ingredient i on i.id=y.ingredient_id where i.producer in ('Norse Nectar','YeasterBunny') group by 1 order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| Norse Nectar 17 / 0, YeasterBunny 1 / 0 | Norse Nectar\|17\|0, YeasterBunny\|1\|0 | ✅ pass |

### ✅ C10 · Brewline: 10 rows in English, user's Brewfather figures, Abbey Monk Ale and Pure Hornindal NULL (user decisions)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select i.name, y.attenuation_pct, y.field_source->>'attenuation_pct' from ref.yeast y join ref.ingredient i on i.id=y.ingredient_id where i.producer='Brewline' order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| Belgian Wit 78, Bavarian Wheat 73, British Ale 75, Czech Lager 76, German Lager 81, High Performance Ale 81, Köln 78, U.S. West Coast Ale 80, all `[a,a]` brewfather; Abbey Monk Ale and Pure Hornindal empty | Abbey Monk Ale (empty), Bavarian Wheat [73,73], Belgian Wit [78,78], British Ale [75,75], Czech Lager [76,76], German Lager [81,81], High Performance Ale [81,81], Köln [78,78], Pure Hornindal (empty), U.S. West Coast Ale [80,80]; all 8 brewfather | ✅ pass |

### ✅ C11 · 2 g packs kept in raw of their 12 g product (user decision)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select i.name, (select string_agg(k, ',' order by k) from jsonb_object_keys(i.raw->'hopline-yeasts') k) from ref.yeast y join ref.ingredient i on i.id=y.ingredient_id where i.raw->'hopline-yeasts' ? '301600' or i.raw->'hopline-yeasts' ? '301610' order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| British Ale 301021,301610; U.S. West Coast Ale 301600,301601 | British Ale\|301021,301610; U.S. West Coast Ale\|301600,301601 | ✅ pass |

### ✅ C12 · The 8 non-beer yeasts are not loaded (user decision)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.ingredient i where i.kind='yeast' and (select bool_or(k in ('301580','301560','301570','301581','300250','301591','300230','301241')) from jsonb_object_keys(i.raw->'hopline-yeasts') k)"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C13 · YF-666 user-supplied 80–100, M20 from its data sheet, Gozdawa W-34/70 NULL (user decisions)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select y.product_id, i.name, y.attenuation_pct, y.field_source->>'attenuation_pct', i.raw->'user-supplied'->>'printed' from ref.yeast y join ref.ingredient i on i.id=y.ingredient_id where y.product_id in ('YF-666','M20') or (i.producer='Gozdawa' and i.name='W-34/70') order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| YF-666 [80,100] user-supplied, printed 800-100; M20 mangrovejacks-datasheets; W-34/70 no attenuation | M20\|M20 Bavarian Wheat\|[70,75]\|mangrovejacks-datasheets; W-34/70\|W-34/70\|(empty); YF-666\|YF-666 Yeastman\|[80,100]\|user-supplied\|800-100 | ✅ pass |

### ✅ C14 · M20 loads its data-block temperature, not the other strain's description (user decision)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select y.temp_c from ref.yeast y where y.product_id='M20'"
```

| Expected | Actual | Result |
|---|---|---|
| [18,30] (data block `18 – 30 °C`; the description's `18 - 22 °C` is listed in report.md) | [18,30] | ✅ pass |

### ✅ C15 · Every ATTENUATION entry is in ref.yeast with its source (Task 6 Done-when)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAF'|' -c "select k, y.attenuation_pct, y.field_source->>'attenuation_pct' from ref.yeast y join ref.ingredient i on i.id = y.ingredient_id, jsonb_object_keys(i.raw->'hopline-yeasts') k where y.attenuation_pct is not null" | .venv/bin/python -c "import sys; from loaders.yeast_products import ATTENUATION as A; db = {l.split('|')[0]: l.strip().split('|')[1:] for l in sys.stdin if l.strip()}; f = lambda x: x.rstrip('0').rstrip('.') if '.' in x else x; bad = [s for s, e in A.items() if db.get(s) != ['[%s,%s]' % tuple(map(f, e['attenuation_pct'])), e['source']]]; print(len(A), 'entries,', len(bad), 'mismatched', bad)"
```

| Expected | Actual | Result |
|---|---|---|
| 93 entries, 0 mismatched | 93 entries, 0 mismatched [] | ✅ pass |

### ✅ C16 · Each attenuation figure matches its printed text (review note 2; YF-666 is the user's correction)

```bash
.venv/bin/python -c "import re; from loaders.yeast_products import ATTENUATION as A; n = lambda t: [x.replace(',', '.') for x in re.findall(r'\d+(?:[.,]\d+)?', t)]; bad = [(s, e['printed'], e['attenuation_pct']) for s, e in A.items() if s != '301242' and n(e['printed']) not in (list(e['attenuation_pct']), [e['attenuation_pct'][0]] if e['attenuation_pct'][0] == e['attenuation_pct'][1] else None)]; print(len(A) - 1, 'checked,', len(bad), 'differ from printed', bad)"
```

| Expected | Actual | Result |
|---|---|---|
| 92 checked, 0 differ | 92 checked, 0 differ from printed [] | ✅ pass |

### ✅ C17 · Fetched file holds 129 products, dry 90, liquid 39, none in both (Task 1 Done-when)

```bash
.venv/bin/python -c "import json; d = json.load(open('shared/rag-files/pending/hopline_yeasts.json')); print(len(d['products']), len(d['forms']['dry']), len(d['forms']['liquid']), len(set(d['forms']['dry']) & set(d['forms']['liquid'])))"
```

| Expected | Actual | Result |
|---|---|---|
| 129 90 39 0 | 129 90 39 0 | ✅ pass |

### ✅ C18 · No LLM in the yeast code (Rules)

```bash
grep -nwiE "ollama|llm" loaders/yeasts.py loaders/yeast_products.py; echo "grep exit $?"
```

| Expected | Actual | Result |
|---|---|---|
| no match (exit 1) | grep exit 1 | ✅ pass |

### ✅ C19 · No source file committed (Rules)

```bash
git ls-files shared/rag-files/pending | wc -l
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C20 · RECIPE-ROADMAP.md names hopline and D8 as decided (review finding 1)

```bash
grep -i brewtarget docs/RECIPE-ROADMAP.md | grep -vc "Not used: yeasts come from hopline"; grep -c "D8 (yeast data) is decided" docs/RECIPE-ROADMAP.md
```

| Expected | Actual | Result |
|---|---|---|
| 0 (Brewtarget only as "Not used"), 1 | 0, 1 | ✅ pass |

### ✅ C21 · Brewline `302170` is Bavarian Wheat, [73,73] brewfather; no Bajor row left (user's English request)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select i.name, i.name_key, y.attenuation_pct, y.field_source->>'attenuation_pct', (select count(*) from ref.ingredient where kind='yeast' and name_key like 'bajor%') from ref.ingredient i join ref.yeast y on y.ingredient_id=i.id where i.kind='yeast' and i.raw->'hopline-yeasts' ? '302170'"
```

| Expected | Actual | Result |
|---|---|---|
| Bavarian Wheat\|bavarianwheat\|[73,73]\|brewfather\|0 | Bavarian Wheat\|bavarianwheat\|[73,73]\|brewfather\|0 | ✅ pass |

### ✅ C22 · No Hungarian outside `raw` in the yeast rows (user's English request)

Same detector as `test_no_hungarian_outside_raw` (letters áéíóőúű, or a Hungarian page word),
run on every column of the 119 rows except `raw`; the second command lists the non-ASCII names.

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.yeast y join ref.ingredient i on i.id=y.ingredient_id where lower(concat_ws(' ', i.name, i.name_key, i.producer, i.producer_key, y.product_id, y.type, y.form, y.flocculation, y.field_source::text)) ~ '[áéíóőúű]|\m(élesztő|eleszto|bajor|búza|buza|belga|amerikai|sör|száraz|folyékony|alacsony|közepes|magas|nagyon|semleges|gyümölcsös)\M'"
docker exec supabase-db psql -U postgres -d postgres -tAc "select string_agg(i.name, ', ' order by i.name) from ref.ingredient i where kind='yeast' and i.name ~ '[^ -~]'"
```

| Expected | Actual | Result |
|---|---|---|
| 0; only German / maker spellings: Köln, YF-110 Kölschermeister, YF-201 St. Cölibate, YF-205 Holy Cölibate | 0; Köln, YF-110 Kölschermeister, YF-201 St. Cölibate, YF-205 Holy Cölibate | ✅ pass |

### ✅ C23 · The 7 yeast-related sources are English (user's English request)

Title, edition, publisher, licence and notes, URLs stripped (a hopline URL keeps its slug).

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select string_agg(slug, ',' order by slug) filter (where lower(regexp_replace(concat_ws(' ', title, edition, publisher, licence, notes), 'https?://\S+', '', 'g')) ~ '[áéíóőúű]|\m(élesztő|eleszto|bajor|búza|buza|belga|amerikai|sör|száraz|folyékony|alacsony|közepes|magas|nagyon|semleges|gyümölcsös)\M'), count(*) from ref.source where slug in ('hopline-yeasts','fermentis-datasheets','lallemand-catalogue','mangrovejacks-datasheets','yeastflow-catalogue','brewfather','user-supplied')"
```

| Expected | Actual | Result |
|---|---|---|
| (none flagged)\|7 | \|7 | ✅ pass |

### ✅ C24 · Every Hungarian quote in report.md has an English gloss (user's English request, re-review note 1)

A quoted page value is Hungarian by the same detector (plus `tartomány`); it must be followed by
` (` and its gloss. The Norse Nectar temperature note is explained by its own paragraph instead.

```bash
.venv/bin/python - <<'EOF'
import re
t = open('docs/work/yeast-loader/report.md').read()
W = {"élesztő","eleszto","bajor","búza","buza","belga","amerikai","sör","száraz","folyékony","alacsony","közepes","magas","nagyon","semleges","gyümölcsös","tartomány"}
hu = lambda s: bool(set("áéíóőúű") & set(s.lower())) or bool(W & set(re.findall(r"\w+", s.lower())))
quotes = [(m.group(1), t[m.end():m.end()+2]) for m in re.finditer(r"(?<=[\s(])'([^']+)'(?=[\s,;.)]|$)", t, re.M)]
h = [(q, after) for q, after in quotes if hu(q)]
note = [q for q, a in h if "ezek a törzsek" in q]
bad = [q for q, a in h if "ezek a törzsek" not in q and a != " ("]
print(len(h), "Hungarian quotes,", len(note), "Norse Nectar notes,", "note explained" if "says the strains are adapted to high temperatures" in t else "note NOT explained", ",", len(bad), "unglossed", bad)
EOF
cat docs/DATABASE.md docs/FILL-REF-README.md docs/RECIPE-ROADMAP.md docs/work/yeast-loader/report.md | grep -ci bajor
```

| Expected | Actual | Result |
|---|---|---|
| 0 unglossed, Norse Nectar note explained; "Bajor" in none of the English docs or the report | 35 Hungarian quotes, 10 Norse Nectar notes, note explained , 0 unglossed []; 0 | ✅ pass |

## Part 3: Regression tests

Every test the plan's *Critical behaviour and its tests* table names exists; none was added.

Command: `.venv/bin/python -m pytest -v`  ·  Result: ✅ 48 passed

| Test | Protects | Result |
|---|---|---|
| tests/test_fetch_hopline.py::test_ajax_listing_body | Every yeast SKU is found, though the pages load their list by script | ✅ |
| tests/test_fetch_hopline.py::test_long_description | Description table and labels captured, CSS excluded | ✅ |
| tests/test_yeasts.py::test_parse_range | Temperatures stored in °C as printed; °F or any other unit raises | ✅ |
| tests/test_yeasts.py::test_tolerance | Alcohol tolerance = range top; description only as fallback | ✅ |
| tests/test_yeasts.py::test_flocculation | Flocculation words → the schema values; unknown raises | ✅ |
| tests/test_yeasts.py::test_type_of | Style family → type; unknown raises | ✅ |
| tests/test_yeasts.py::test_us05 | Figures from the main page only; `field_source` and `raw` complete | ✅ |
| tests/test_yeasts.py::test_brewline_pack_size | 2 g pack kept in raw, its figures ignored | ✅ |
| tests/test_yeasts.py::test_description_fills_gaps | Description fills data-block gaps; Min/Max temperature read | ✅ |
| tests/test_yeasts.py::test_yeast_map | Every SKU decided once; no two yeasts share a key; attenuation entries and sources valid | ✅ |
| tests/test_yeasts.py::test_unknown_sku_raises | A new hopline product never loads silently | ✅ |
| tests/test_yeasts.py::test_attenuation_fill | Attenuation only from a named source, one figure → `[a,a]`, `field_source` per source | ✅ |
| tests/test_yeasts.py::test_no_hungarian_outside_raw | No Hungarian in names, type, flocculation, `field_source` (fails on "Bajor Búza") | ✅ |
| tests/test_yeasts.py::test_report_glosses_hungarian_quotes | A Hungarian value the report quotes gets its English gloss; English values are quoted alone | ✅ |
| Loader re-run (below) | Re-running doesn't duplicate, and the rename doesn't add a 120th row | ✅ |
| The other 34 tests (common, hops, malts, styles, earlier fetch tests) | Earlier loaders unchanged | ✅ |

Re-run, report written to the scratchpad and compared with the committed one:

```bash
.venv/bin/python -m loaders.yeasts --hopline shared/rag-files/pending/hopline_yeasts.json --report <scratchpad>/report.md
docker exec supabase-db psql -U postgres -d postgres -tAc "select (select count(*) from ref.yeast), (select count(*) from ref.ingredient where kind='yeast'), (select count(attenuation_pct) from ref.yeast), (select count(*) from ref.ingredient where kind='yeast' and name='Bavarian Wheat')"
cmp <scratchpad>/report.md docs/work/yeast-loader/report.md && echo "report identical"
```

| Expected | Actual | Result |
|---|---|---|
| loaded 119, skipped 8; 119\|119\|93\|1; report identical | loaded: 119 yeasts, skipped: 8 non-beer yeasts; 119\|119\|93\|1; report identical | ✅ pass |

Failures: none.
