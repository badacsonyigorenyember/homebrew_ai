# Verification: ref-spotcheck

Overall: ✅ all 11 checks and 51 tests pass

Verified 2026-10-11 on branch `ref-spotcheck` at 1e1a04b, against `plan.md` (no brief; Source is
P1a index item 8, now `docs/FILL-REF-README.md` on `main`) and `review.md`.

## Part 1: Summary

🎯 **Goal:** finish P1a by spot-checking the loaded `ref` data against its sources and recording the measured results.

🛠️ **How:** a read-only SQL pack (`db/checks/ref_spotcheck.sql`) prints counts for all 15 `ref` tables, rows without a source and 10 random rows per loaded table; the user checked the printed rows, and PROJECT.md and DATABASE.md now carry the measured numbers.

🤔 **Why this way:** one re-runnable, read-only file lets anyone repeat the check against the live DB without touching data, and the user's eye on the sources is RECIPE-ROADMAP P1's done condition.

🏁 **Result:** P1a is done and recorded: 16 sources, 285 styles (BJCP 116 + BA 169), 291 ingredients (74 malts, 90 hops, 119 yeasts, 8 salts), 0 rows without a source, the 8 style-fit tables empty; 10 rows per loaded table and all 8 Beer Maverick hop values checked by the user, no errors.

### 🚦 Steps

- ⏭️ 📝 **Brief:** skipped; the plan already existed and names its source (P1a index item 8).
- ✅ 🗺️ **Plan:** written in an earlier session (93d7376), approved here (860b62c).
  - ⚠️ The plan's `Source:` link `../fill-ref/README.md` is broken; the file moved to `docs/FILL-REF-README.md` on `main`.
- ⚠️ 🔨 **Implement:** Task 1 done in 27a1bb3 (pack written and run, user spot-check "All rows match", docs updated); one fix round for the review (3aa647e, d333ddd).
  - ⚠️ Expected suite count changed 40 → 51; recorded under the plan's Deviations.
  - ⚠️ The no-source check can only return 0: `source_id` is `NOT NULL` with a foreign key, so the 0 proves nothing beyond the schema.
- ❌ 🔍 **Review:** first run "ready for testing" with 2 should-fix (DATABASE.md hop gap note did not match `hop.field_source`; hand-entered Beer Maverick values unchecked) 🔧 fixed in 3aa647e, d333ddd; re-review (1e1a04b) found nothing left.
  - ⚠️ The first review counted the Beer Maverick values as 7; there are 8.
- ✅ 🧪 **Verify:** pack re-run (exit 0), counts, sources and the 8 Beer Maverick values queried live, docs checked against them. 🧮 spot checks ✅ 11/11 · 🧪 tests ✅ 51/51

👀 **Start here:** run `docker exec -i supabase-db psql -U postgres -d postgres < db/checks/ref_spotcheck.sql`; you should see the 15 table counts (8 style-fit tables at 0), 0 rows without a source, and 10 random rows for each loaded table (8 for `water_salt`, which has 8).

📁 **Changed files:**
- `PROJECT.md`
- `db/checks/ref_spotcheck.sql`
- `docs/DATABASE.md`
- `docs/work/ref-spotcheck/plan.md`
- `docs/work/ref-spotcheck/review.md`
- `docs/work/ref-spotcheck/verification.md`

## Part 2: Spot checks

### ✅ C1 · `ref` has 15 tables

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from information_schema.tables where table_schema = 'ref'"
```

| Expected | Actual | Result |
|---|---|---|
| 15 | 15 | ✅ pass |

### ✅ C2 · Loaded table counts (source, beer_style, ingredient, fermentable, hop, yeast, water_salt)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select (select count(*) from ref.source)||' '||(select count(*) from ref.beer_style)||' '||(select count(*) from ref.ingredient)||' '||(select count(*) from ref.fermentable)||' '||(select count(*) from ref.hop)||' '||(select count(*) from ref.yeast)||' '||(select count(*) from ref.water_salt)"
```

| Expected | Actual | Result |
|---|---|---|
| 16 285 291 74 90 119 8 | 16 285 291 74 90 119 8 | ✅ pass |

### ✅ C3 · Styles per guide

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select string_agg(guide||' '||n, ', ' order by guide) from (select guide, count(*) n from ref.beer_style group by guide) t"
```

| Expected | Actual | Result |
|---|---|---|
| BA 169, BJCP 116 | BA 169, BJCP 116 | ✅ pass |

### ✅ C4 · Ingredients per kind

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select string_agg(kind||' '||n, ', ' order by kind) from (select kind, count(*) n from ref.ingredient group by kind) t"
```

| Expected | Actual | Result |
|---|---|---|
| fermentable 74, hop 90, water_salt 8, yeast 119 | fermentable 74, hop 90, water_salt 8, yeast 119 | ✅ pass |

### ✅ C5 · The 8 style-fit tables are empty (critical behaviour)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select (select count(*) from ref.misc)+(select count(*) from ref.tag)+(select count(*) from ref.tag_synonym)+(select count(*) from ref.ingredient_tag)+(select count(*) from ref.sensory_dimension)+(select count(*) from ref.style_sensory)+(select count(*) from ref.style_character)+(select count(*) from ref.style_rule)"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C6 · Every loaded row has a source (critical behaviour)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select (select count(*) from ref.beer_style b left join ref.source s on s.id=b.source_id where s.id is null)+(select count(*) from ref.ingredient i left join ref.source s on s.id=i.source_id where s.id is null)"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C7 · The pack runs clean and prints 10 rows per loaded table

```bash
docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/checks/ref_spotcheck.sql | grep -E '^\([0-9]+ rows?\)' | tr '\n' ' '; echo "exit ${PIPESTATUS[0]}"
```

| Expected | Actual | Result |
|---|---|---|
| 15, 4, 2 rows, then 10 for each of the 6 larger tables and 8 for `water_salt`; exit 0 | (15 rows) (4 rows) (2 rows) (10 rows) ×6 (8 rows) exit 0 | ✅ pass |

### ✅ C8 · The pack is read-only

```bash
grep -ciE '^\s*(insert|update|delete|create|drop|alter|truncate|grant)\b' db/checks/ref_spotcheck.sql; grep -c 'set default_transaction_read_only = on;' db/checks/ref_spotcheck.sql
```

| Expected | Actual | Result |
|---|---|---|
| 0 write statements, 1 read-only setting | 0, 1 | ✅ pass |

### ✅ C9 · Exactly the 8 Beer Maverick hop values the docs name

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select string_agg(i.name||'.'||k, ', ' order by i.name, k) from ref.hop h join ref.ingredient i on i.id=h.ingredient_id, jsonb_each_text(h.field_source) f(k,v) where v='beermaverick'"
```

| Expected | Actual | Result |
|---|---|---|
| Delta, Lotus, Sterling alpha + oil; Mount Hood oil; Enigma purpose | Delta.alpha_pct, Delta.total_oil_ml_100g, Enigma.purpose, Lotus.alpha_pct, Lotus.total_oil_ml_100g, Mount Hood.total_oil_ml_100g, Sterling.alpha_pct, Sterling.total_oil_ml_100g | ✅ pass |

### ✅ C10 · Every `field_source` slug resolves to a `ref.source` row

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from (select v from ref.fermentable, jsonb_each_text(field_source) f(k,v) union all select v from ref.hop, jsonb_each_text(field_source) f(k,v) union all select v from ref.yeast, jsonb_each_text(field_source) f(k,v)) x where v not in (select slug from ref.source)"
```

| Expected | Actual | Result |
|---|---|---|
| 0 (of 1308 field_source values) | 0 | ✅ pass |

### ✅ C11 · Docs carry the measured counts and the Beer Maverick note

```bash
grep -c '291 ingredients' PROJECT.md docs/DATABASE.md | tr '\n' ' '; grep -c "Mount Hood's oil and Enigma's purpose; all 8 checked against beermaverick.com" docs/DATABASE.md
```

| Expected | Actual | Result |
|---|---|---|
| both files ≥ 1; note present (1) | docs/DATABASE.md:1 PROJECT.md:2; 1 | ✅ pass |

## Part 3: Regression tests

The plan's critical behaviours are covered by C5 (style-fit tables empty), C6 (every loaded row
sourced) and the whole suite below. The plan names no other test, so none was added.

Command: `.venv/bin/python -m pytest -q`  ·  Result: ✅ 51 passed

| Test | Protects | Result |
|---|---|---|
| tests/test_common.py (8) | shared loader helpers | ✅ |
| tests/test_styles.py (4) | BJCP and BA style parsing | ✅ |
| tests/test_malts.py (9) | malt catalogue parsing | ✅ |
| tests/test_hops.py (9) | hop parsing, incl. Beer Maverick values | ✅ |
| tests/test_fetch_hopline.py (6) | hopline page fetching and parsing | ✅ |
| tests/test_yeasts.py (12) | yeast parsing and attenuation sources | ✅ |
| tests/test_water_salts.py (3) | salt ion maths from atomic masses | ✅ |
