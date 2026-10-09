Overall: ✅ all 20 checks and 23 tests pass

# Verification: malt-loader

Branch `malt-loader` against `main`. First run 2026-10-09 at 0257ccf (Parts 2 and 3 below, kept for
history); re-verified 2026-10-09 at d80e43e, after fix d6d0a07 (`## Re-verify 2026-10-09` at the
end). Part 1 and the `Overall:` line describe the re-verify run.

## Part 1: Summary

🎯 **Goal:** fill `ref.fermentable` with the grain malts hopline.hu sells from Weyermann, Viking Malt and Simpsons, with figures and per-field sources.

🛠️ **How:** a fetcher saves hopline's product pages, a hand-built JSON holds the maltster catalogue figures, and a tested loader merges them (catalogue wins, hopline fills gaps, a user-supplied figure fills only what both lack) and upserts them.

🤔 **Why this way:** hopline decides what the user can buy, the catalogues are the authoritative figures, and hand-copying the two-column PDFs is easier to check than a fragile PDF parser.

🏁 **Result:** 74 malts in `ref` (Weyermann 37, Viking 32, Simpsons 5): 73 with EBC, all 74 with potential, 62 with `max_pct`, each field's source in `field_source`; 11 `ref.source` rows; 8 hopline products are deliberately skipped, and a re-load changes nothing.

### 🚦 Steps

- ⏭️ 📝 **Brief:** skipped, because a plan already existed; the plan's `Source:` doc and Deviations serve as the spec.
- ✅ 🗺️ **Plan:** one run rewrote the draft for hopline plus the three catalogues; the user approved it (eaaa59e).
- ⚠️ 🔨 **Implement:** all 5 tasks done (20b51f2, 18261c2, c3ee4b1, 767ac27, a2c0c38) plus one fix round after the first verification (d6d0a07); suite 23.
  - ⚠️ Hopline lists "min 70%" extract for Simpsons Crystal T50, DRC and Crystal Extra Dark. The user first chose `NULL`, then reversed it after verification: they now take hopline's 70% (potential 1.0323). 🔧 fixed in d6d0a07
  - ⚠️ Weyermann Acidulated Malt had `NULL` potential, as neither source states an extract. The user supplied "PPG 1.03 ≈ 30": extract 64.9, potential 1.0300 from a new `user-supplied` source (id 67). 🔧 fixed in d6d0a07
  - ⚠️ The permission check refused copying the PDFs into `shared/rag-files/pending/`, so they are read from `~/Downloads` (recorded in Deviations).
  - ⚠️ Carapils and Carahell print a special-use limit as well as the normal one. The user chose 10 / 15 (`usage_printed` keeps the full text).
  - ⚠️ 12 Viking malts have no `max_pct`, because neither source states a limit.
  - ⚠️ New source ids are 43–46 (and 67 for `user-supplied`). The gaps in the sequence are harmless.
- ⚠️ 🔍 **Review:** round 1 ready for testing with 0 must-fix (0257ccf); round 2 after the fix ready for testing with no findings (d80e43e).
  - ⚠️ should-fix 1: "Maximum addition N%" and "under N%" are not parsed, so 4 rows credit hopline for `max_pct` with the same values. The user chose to leave it as is (asked twice).
  - ⚠️ note: Viking Wheat gets `max_pct` 50 from hopline after the catalogue's "around 50%" was rejected.
  - ⚠️ note: the `hopline-malts` edition hard-codes the fetch date.
  - ⚠️ note: the plan commit eaaa59e carries a `Co-Authored-By` trailer.
  - ⚠️ note: one test pairs a Simpsons malt with the Weyermann catalogue fixture; it still tests precedence correctly.
- ✅ 🧪 **Verify:** first run ✅ 16/16 checks, 22/22 tests (3162c1c); the user then changed two data decisions. Re-verify after d6d0a07 checked the loaded rows, sources, the two changed malts, the `user-supplied` provenance and a third load, which changed nothing; no tests were missing. 🧮 spot checks ✅ 20/20 · 🧪 tests ✅ 23/23

👀 **Start here:** `docker exec -it supabase-db psql -U postgres -d postgres`, then
`select i.producer, i.name, f.ebc, f.potential_sg, f.max_pct, f.field_source from ref.fermentable f join ref.ingredient i on i.id = f.ingredient_id order by 1, 2;`.
You should see 74 malts, each with the source of every filled field and no empty potential.
Weyermann Acidulated Malt shows potential 1.0300 from `user-supplied`; Simpsons Crystal T50, DRC and
Crystal Extra Dark show 1.0323 from `hopline-malts`.

📁 **Changed files:**
- `PROJECT.md`
- `db/010_ref_schema.sql`
- `db/011_ref_sources.sql`
- `docs/work/fill-ref/README.md`
- `docs/work/malt-loader/plan.md`
- `docs/work/malt-loader/review.md`
- `docs/work/malt-loader/verification.md`
- `loaders/fetch_hopline.py`
- `loaders/malt_products.py`
- `loaders/malts.py`
- `tests/test_fetch_hopline.py`
- `tests/test_malts.py`

## Part 2: Spot checks

First run, at 0257ccf, before fix d6d0a07. C1, C7, C8 and C11 no longer describe the data; see
`## Re-verify 2026-10-09`.

### ✅ C1 · 10 sources, the 4 malt sources replace the 2 old ones

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select string_agg(slug, ',' order by id) from ref.source"
```

| Expected | Actual | Result |
|---|---|---|
| 6 non-malt slugs + `hopline-malts,weyermann-2026,viking-malt-2023,simpsons-malt-2025` | `bjcp-2021,ba-2026,hops-json,hopslist,brewtarget-default-data,water-chemistry,hopline-malts,weyermann-2026,viking-malt-2023,simpsons-malt-2025` | ✅ pass |

### ✅ C2 · Old sources gone

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.source where slug in ('weyermann-specs','viking-malt-2020')"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C3 · `field_source jsonb not null`

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select data_type, is_nullable from information_schema.columns where table_schema='ref' and table_name='fermentable' and column_name='field_source'"
```

| Expected | Actual | Result |
|---|---|---|
| `jsonb\|NO` | `jsonb\|NO` | ✅ pass |

### ✅ C4 · Malts per producer

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select i.producer, count(*) from ref.ingredient i join ref.fermentable f on f.ingredient_id = i.id group by 1 order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| `Simpsons Malt\|5`, `Viking Malt\|32`, `Weyermann\|37` | `Simpsons Malt\|5`, `Viking Malt\|32`, `Weyermann\|37` | ✅ pass |

### ✅ C5 · Row source per malt

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select s.slug, count(*) from ref.ingredient i join ref.source s on s.id = i.source_id where i.kind = 'fermentable' group by 1 order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| `hopline-malts\|1`, `simpsons-malt-2025\|5`, `viking-malt-2023\|31`, `weyermann-2026\|37` | `hopline-malts\|1`, `simpsons-malt-2025\|5`, `viking-malt-2023\|31`, `weyermann-2026\|37` | ✅ pass |

### ✅ C6 · Every fermentable ingredient has a detail row

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.ingredient i left join ref.fermentable f on f.ingredient_id = i.id where i.kind = 'fermentable' and f.ingredient_id is null"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C7 · `NULL` potential only where no extract is used

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select string_agg(i.name, ', ' order by i.name) from ref.fermentable f join ref.ingredient i on i.id = f.ingredient_id where f.potential_sg is null"
```

| Expected | Actual | Result |
|---|---|---|
| Crystal Extra Dark, Crystal T50, DRC (+ Acidulated Malt: no extract in either source, Deviations) | Acidulated Malt, Crystal Extra Dark, Crystal T50, DRC | ✅ pass |

### ✅ C8 · Simpsons crystals ignore hopline's "min 70%"

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select i.name, f.extract_dbfg_pct is null, f.potential_sg is null, f.field_source ? 'potential_sg' from ref.fermentable f join ref.ingredient i on i.id = f.ingredient_id where i.producer = 'Simpsons Malt' and i.name in ('Crystal T50','DRC','Crystal Extra Dark') order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| 3 rows `t\|t\|f` | `Crystal Extra Dark\|t\|t\|f`, `Crystal T50\|t\|t\|f`, `DRC\|t\|t\|f` | ✅ pass |

### ✅ C9 · Maris Otter row: catalogue wins, hopline fills

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select f.ebc, f.extract_dbfg_pct, f.potential_sg, f.max_pct, f.field_source from ref.fermentable f join ref.ingredient i on i.id = f.ingredient_id where i.name ilike '%maris otter%'"
```

| Expected | Actual | Result |
|---|---|---|
| `[4.4,6.6]\|79.0\|1.0365\|100.0`, ebc from `simpsons-malt-2025`, the other 3 from `hopline-malts` | `[4.4,6.6]\|79.0\|1.0365\|100.0\|{"ebc": "simpsons-malt-2025", "max_pct": "hopline-malts", "potential_sg": "hopline-malts", "extract_dbfg_pct": "hopline-malts"}` | ✅ pass |

### ✅ C10 · Potential follows the formula on every row (maths)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.fermentable where potential_sg is distinct from round(1 + extract_dbfg_pct/100*46.214/1000, 4)"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C11 · Measured counts match PROJECT.md (rows, EBC, potential, max_pct)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*), count(ebc), count(potential_sg), count(max_pct) from ref.fermentable"
```

| Expected | Actual | Result |
|---|---|---|
| `74\|73\|70\|62` | `74\|73\|70\|62` | ✅ pass |

### ✅ C12 · `max_pct` source split matches PROJECT.md

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select field_source->>'max_pct', count(*) from ref.fermentable where max_pct is not null group by 1 order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| hopline 17, simpsons 1, viking 8, weyermann 36 | `hopline-malts\|17`, `simpsons-malt-2025\|1`, `viking-malt-2023\|8`, `weyermann-2026\|36` | ✅ pass |

### ✅ C13 · `field_source` lists exactly the filled fields

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.fermentable f where exists (select 1 from jsonb_each_text(f.field_source) e where (e.key='ebc' and f.ebc is null) or (e.key='max_pct' and f.max_pct is null) or (e.key='potential_sg' and f.potential_sg is null) or (e.key='extract_dbfg_pct' and f.extract_dbfg_pct is null)) or (f.ebc is not null and not f.field_source ? 'ebc') or (f.potential_sg is not null and not f.field_source ? 'potential_sg') or (f.max_pct is not null and not f.field_source ? 'max_pct')"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C14 · User decisions: Carapils / Carahell limits, two smoked pilsners, Sprau hopline-only

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select i.name, s.slug, f.max_pct, (select string_agg(k, ',' order by k) from jsonb_object_keys(i.raw) k) from ref.fermentable f join ref.ingredient i on i.id = f.ingredient_id join ref.source s on s.id = i.source_id where i.name in ('Carapils','Carahell','Sprau Malt') or i.name like 'Smoked Malt (%' order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| Carahell 15 and Carapils 10 from `weyermann-2026`; 2 separate Smoked Malt rows (cherry wood, pear wood) from `viking-malt-2023`; Sprau Malt from `hopline-malts` only | `Carahell\|weyermann-2026\|15.0\|hopline-malts,weyermann-2026`, `Carapils\|weyermann-2026\|10.0\|hopline-malts,weyermann-2026`, `Smoked Malt (cherry wood)\|viking-malt-2023\|100.0\|hopline-malts,viking-malt-2023`, `Smoked Malt (pear wood)\|viking-malt-2023\|100.0\|hopline-malts,viking-malt-2023`, `Sprau Malt\|hopline-malts\|15.0\|hopline-malts` | ✅ pass |

### ✅ C15 · Every hopline SKU decided, every mapped product in the catalogue once

```bash
.venv/bin/python -c "import json; from loaders.malt_products import PRODUCTS, SKIPPED; h=json.load(open('shared/rag-files/pending/hopline_malts.json')); c=json.load(open('shared/rag-files/pending/malt_catalogue.json')); s=[p['sku'] for p in h['products']]; k=[(e['maltster'],e['product']) for e in c]; n={(p,q) for p,q,_ in PRODUCTS.values() if q}; print(len(s), sum(x in PRODUCTS for x in s), sum(x in SKIPPED for x in s), sum(x not in PRODUCTS and x not in SKIPPED for x in s), len(n), sum(k.count(x)==1 for x in n))"
```

| Expected | Actual | Result |
|---|---|---|
| `82 74 8 0 72 72` | `82 74 8 0 72 72` | ✅ pass |

### ✅ C16 · Source files git-ignored and not committed

```bash
git check-ignore shared/rag-files/pending/hopline_malts.json shared/rag-files/pending/malt_catalogue.json; git ls-files shared/rag-files/pending | grep -c malt
```

| Expected | Actual | Result |
|---|---|---|
| both paths listed, `0` tracked | both paths listed, `0` | ✅ pass |

## Part 3: Regression tests

No test from the plan's *Critical behaviour and its tests* table was missing, so none were added.

Command: `.venv/bin/python -m pytest -v`  ·  Result: ✅ 22 passed

| Test | Protects | Result |
|---|---|---|
| tests/test_fetch_hopline.py::test_listing_links | Listing SKUs and URLs in order, no repeats | ✅ |
| tests/test_fetch_hopline.py::test_product_page | Hopline page facts captured, script text excluded, both breadcrumb kinds | ✅ |
| tests/test_malts.py::test_potential_sg | Extract % → SG (`ppg = extract/100 × 46.214`), 4 places | ✅ |
| tests/test_malts.py::test_max_pct_from_text | Only a stated upper limit becomes `max_pct` | ✅ |
| tests/test_malts.py::test_hopline_spec | Hopline formats: ranges, single, `max`, `-`, `?` | ✅ |
| tests/test_malts.py::test_catalogue_wins_hopline_fills | Catalogue wins, hopline fills gaps, `field_source` and `raw` record both | ✅ |
| tests/test_malts.py::test_no_extract_stays_null | No extract (or hopline's ignored) stays `NULL`, never 0 | ✅ |
| tests/test_malts.py::test_hopline_only | Unmatched product sourced to hopline, never a guessed catalogue | ✅ |
| tests/test_malts.py::test_product_map | Every SKU decided once; no two malts share a name key | ✅ |
| tests/test_malts.py::test_unknown_sku_raises | A new hopline product never loads silently | ✅ |
| tests/test_common.py (8), tests/test_styles.py (4) | Earlier work: shared helpers, styles loader | ✅ |

Load-twice (idempotency, plan's last critical row): ran
`.venv/bin/python -m loaders.malts --hopline shared/rag-files/pending/hopline_malts.json --catalogue shared/rag-files/pending/malt_catalogue.json`
a third time. It printed `loaded: 74 malts` and `skipped: 8 hopline products`. Before and after the run,
the count and md5 over name, producer, EBC, potential, `max_pct`, `field_source` and source of
every row were the same, `74|a0aa865f3b2415df04ee6779771f99b8`, and `ref.ingredient` still has 74 rows. ✅

Failures: none.

## Re-verify 2026-10-09

Branch at d80e43e, after fix d6d0a07. Every check from the first run is run again. The expected
values of C1, C7, C8 and C11 changed with the user's two data decisions in the fix round (plan
Deviations, last two entries: crystals take hopline's 70%; Acidulated Malt gets 64.9 from
`user-supplied`); C17–C20 are new and check the fix.

### ✅ C1 · 11 sources: the 4 malt sources replace the 2 old ones, plus `user-supplied`

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select string_agg(slug, ',' order by id) from ref.source"
```

| Expected | Actual | Result |
|---|---|---|
| 6 non-malt slugs + `hopline-malts,weyermann-2026,viking-malt-2023,simpsons-malt-2025,user-supplied` | `bjcp-2021,ba-2026,hops-json,hopslist,brewtarget-default-data,water-chemistry,hopline-malts,weyermann-2026,viking-malt-2023,simpsons-malt-2025,user-supplied` | ✅ pass |

### ✅ C2 · Old sources gone

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.source where slug in ('weyermann-specs','viking-malt-2020')"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C3 · `field_source jsonb not null`

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select data_type, is_nullable from information_schema.columns where table_schema='ref' and table_name='fermentable' and column_name='field_source'"
```

| Expected | Actual | Result |
|---|---|---|
| `jsonb\|NO` | `jsonb\|NO` | ✅ pass |

### ✅ C4 · Malts per producer

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select i.producer, count(*) from ref.ingredient i join ref.fermentable f on f.ingredient_id = i.id group by 1 order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| `Simpsons Malt\|5`, `Viking Malt\|32`, `Weyermann\|37` | `Simpsons Malt\|5`, `Viking Malt\|32`, `Weyermann\|37` | ✅ pass |

### ✅ C5 · Row source per malt

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select s.slug, count(*) from ref.ingredient i join ref.source s on s.id = i.source_id where i.kind = 'fermentable' group by 1 order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| `hopline-malts\|1`, `simpsons-malt-2025\|5`, `viking-malt-2023\|31`, `weyermann-2026\|37` | `hopline-malts\|1`, `simpsons-malt-2025\|5`, `viking-malt-2023\|31`, `weyermann-2026\|37` | ✅ pass |

### ✅ C6 · Every fermentable ingredient has a detail row

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.ingredient i left join ref.fermentable f on f.ingredient_id = i.id where i.kind = 'fermentable' and f.ingredient_id is null"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C7 · No `NULL` potential left

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.fermentable where potential_sg is null"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C8 · Simpsons crystals take hopline's "min 70%"

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select i.name, f.extract_dbfg_pct, f.potential_sg, f.field_source->>'extract_dbfg_pct', f.field_source->>'potential_sg' from ref.fermentable f join ref.ingredient i on i.id = f.ingredient_id where i.producer = 'Simpsons Malt' and i.name in ('Crystal T50','DRC','Crystal Extra Dark') order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| 3 rows `70.0\|1.0323\|hopline-malts\|hopline-malts` | `Crystal Extra Dark\|70.0\|1.0323\|hopline-malts\|hopline-malts`, `Crystal T50\|70.0\|1.0323\|hopline-malts\|hopline-malts`, `DRC\|70.0\|1.0323\|hopline-malts\|hopline-malts` | ✅ pass |

### ✅ C9 · Maris Otter row: catalogue wins, hopline fills

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select f.ebc, f.extract_dbfg_pct, f.potential_sg, f.max_pct, f.field_source from ref.fermentable f join ref.ingredient i on i.id = f.ingredient_id where i.name ilike '%maris otter%'"
```

| Expected | Actual | Result |
|---|---|---|
| `[4.4,6.6]\|79.0\|1.0365\|100.0`, ebc from `simpsons-malt-2025`, the other 3 from `hopline-malts` | `[4.4,6.6]\|79.0\|1.0365\|100.0\|{"ebc": "simpsons-malt-2025", "max_pct": "hopline-malts", "potential_sg": "hopline-malts", "extract_dbfg_pct": "hopline-malts"}` | ✅ pass |

### ✅ C10 · Potential follows the formula on every row (maths)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.fermentable where potential_sg is distinct from round(1 + extract_dbfg_pct/100*46.214/1000, 4)"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C11 · Measured counts match PROJECT.md (rows, EBC, potential, max_pct)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*), count(ebc), count(potential_sg), count(max_pct) from ref.fermentable"
```

| Expected | Actual | Result |
|---|---|---|
| `74\|73\|74\|62` | `74\|73\|74\|62` | ✅ pass |

### ✅ C12 · `max_pct` source split unchanged

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select field_source->>'max_pct', count(*) from ref.fermentable where max_pct is not null group by 1 order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| hopline 17, simpsons 1, viking 8, weyermann 36 | `hopline-malts\|17`, `simpsons-malt-2025\|1`, `viking-malt-2023\|8`, `weyermann-2026\|36` | ✅ pass |

### ✅ C13 · `field_source` lists exactly the filled fields

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.fermentable f where exists (select 1 from jsonb_each_text(f.field_source) e where (e.key='ebc' and f.ebc is null) or (e.key='max_pct' and f.max_pct is null) or (e.key='potential_sg' and f.potential_sg is null) or (e.key='extract_dbfg_pct' and f.extract_dbfg_pct is null)) or (f.ebc is not null and not f.field_source ? 'ebc') or (f.potential_sg is not null and not f.field_source ? 'potential_sg') or (f.max_pct is not null and not f.field_source ? 'max_pct')"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C14 · User decisions: Carapils / Carahell limits, two smoked pilsners, Sprau hopline-only

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select i.name, s.slug, f.max_pct, (select string_agg(k, ',' order by k) from jsonb_object_keys(i.raw) k) from ref.fermentable f join ref.ingredient i on i.id = f.ingredient_id join ref.source s on s.id = i.source_id where i.name in ('Carapils','Carahell','Sprau Malt') or i.name like 'Smoked Malt (%' order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| Carahell 15 and Carapils 10 from `weyermann-2026`; 2 separate Smoked Malt rows (cherry wood, pear wood) from `viking-malt-2023`; Sprau Malt from `hopline-malts` only | `Carahell\|weyermann-2026\|15.0\|hopline-malts,weyermann-2026`, `Carapils\|weyermann-2026\|10.0\|hopline-malts,weyermann-2026`, `Smoked Malt (cherry wood)\|viking-malt-2023\|100.0\|hopline-malts,viking-malt-2023`, `Smoked Malt (pear wood)\|viking-malt-2023\|100.0\|hopline-malts,viking-malt-2023`, `Sprau Malt\|hopline-malts\|15.0\|hopline-malts` | ✅ pass |

### ✅ C15 · Every hopline SKU decided, every mapped product in the catalogue once

```bash
.venv/bin/python -c "import json; from loaders.malt_products import PRODUCTS, SKIPPED; h=json.load(open('shared/rag-files/pending/hopline_malts.json')); c=json.load(open('shared/rag-files/pending/malt_catalogue.json')); s=[p['sku'] for p in h['products']]; k=[(e['maltster'],e['product']) for e in c]; n={(p,q) for p,q,_ in PRODUCTS.values() if q}; print(len(s), sum(x in PRODUCTS for x in s), sum(x in SKIPPED for x in s), sum(x not in PRODUCTS and x not in SKIPPED for x in s), len(n), sum(k.count(x)==1 for x in n))"
```

| Expected | Actual | Result |
|---|---|---|
| `82 74 8 0 72 72` | `82 74 8 0 72 72` | ✅ pass |

### ✅ C16 · Source files git-ignored and not committed

```bash
git check-ignore shared/rag-files/pending/hopline_malts.json shared/rag-files/pending/malt_catalogue.json; git ls-files shared/rag-files/pending | grep -c malt
```

| Expected | Actual | Result |
|---|---|---|
| both paths listed, `0` tracked | both paths listed, `0` | ✅ pass |

### ✅ C17 · Acidulated Malt: user-supplied extract with the user's wording kept

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select i.name, f.extract_dbfg_pct, f.potential_sg, f.field_source->>'extract_dbfg_pct', f.field_source->>'potential_sg', i.raw->'user-supplied'->>'user_wording' from ref.fermentable f join ref.ingredient i on i.id = f.ingredient_id where i.producer = 'Weyermann' and i.name = 'Acidulated Malt'"
```

| Expected | Actual | Result |
|---|---|---|
| `Acidulated Malt\|64.9\|1.0300\|user-supplied\|user-supplied\|PPG: 1.03 which means ~30?` | `Acidulated Malt\|64.9\|1.0300\|user-supplied\|user-supplied\|PPG: 1.03 which means ~30?` | ✅ pass |

### ✅ C18 · Only one row carries user-supplied figures

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.ingredient where raw ? 'user-supplied'"
```

| Expected | Actual | Result |
|---|---|---|
| 1 | 1 | ✅ pass |

### ✅ C19 · Potential source split matches PROJECT.md

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select field_source->>'potential_sg', count(*) from ref.fermentable group by 1 order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| hopline 6, user-supplied 1, viking 31, weyermann 36 | `hopline-malts\|6`, `user-supplied\|1`, `viking-malt-2023\|31`, `weyermann-2026\|36` | ✅ pass |

### ✅ C20 · Potential always shares the extract's source

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.fermentable where field_source->>'potential_sg' is distinct from field_source->>'extract_dbfg_pct'"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### Regression tests (re-run)

No test from the plan's *Critical behaviour and its tests* table is missing
(`test_user_supplied_fills_only_gaps` was added by the fix round), so none were added.

Command: `.venv/bin/python -m pytest -v`  ·  Result: ✅ 23 passed

| Test | Protects | Result |
|---|---|---|
| tests/test_fetch_hopline.py::test_listing_links | Listing SKUs and URLs in order, no repeats | ✅ |
| tests/test_fetch_hopline.py::test_product_page | Hopline page facts captured, script text excluded, both breadcrumb kinds | ✅ |
| tests/test_malts.py::test_potential_sg | Extract % → SG (`ppg = extract/100 × 46.214`), 4 places | ✅ |
| tests/test_malts.py::test_max_pct_from_text | Only a stated upper limit becomes `max_pct` | ✅ |
| tests/test_malts.py::test_hopline_spec | Hopline formats: ranges, single, `max`, `-`, `?` | ✅ |
| tests/test_malts.py::test_catalogue_wins_hopline_fills | Catalogue wins, hopline fills gaps, `field_source` and `raw` record both | ✅ |
| tests/test_malts.py::test_no_extract_stays_null | No extract anywhere (missing or hopline `? %`) stays `NULL`, never 0 | ✅ |
| tests/test_malts.py::test_user_supplied_fills_only_gaps | A user-supplied figure fills only what both sources lack; `build` passes it for SKU 101080 | ✅ |
| tests/test_malts.py::test_hopline_only | Unmatched product sourced to hopline, never a guessed catalogue | ✅ |
| tests/test_malts.py::test_product_map | Every SKU decided once; no two malts share a name key | ✅ |
| tests/test_malts.py::test_unknown_sku_raises | A new hopline product never loads silently | ✅ |
| tests/test_common.py (8), tests/test_styles.py (4) | Earlier work: shared helpers, styles loader | ✅ |

Load-twice (idempotency, plan's last critical row): ran
`.venv/bin/python -m loaders.malts --hopline shared/rag-files/pending/hopline_malts.json --catalogue shared/rag-files/pending/malt_catalogue.json`
once more. It printed `loaded: 74 malts` and `skipped: 8 hopline products`. Before and after the run,
the count and md5 over name, producer, EBC, potential, `max_pct`, `field_source` and source of
every row were the same, `74|8308644581c33a9d9caf7674e7825796` (different from the first run's hash
because 4 rows changed in d6d0a07), and `ref.ingredient` still has 74 fermentable rows. ✅

Failures: none.
