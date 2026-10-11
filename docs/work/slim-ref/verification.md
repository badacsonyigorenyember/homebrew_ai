Overall: ✅ all 22 checks and 42 tests pass

# Verification: slim-ref

Branch: slim-ref at ad8c0eb  ·  Run: 2026-10-11  ·  Source: [`docs/DATABASE-REVIEW.md`](../../DATABASE-REVIEW.md) §5, [`plan.md`](plan.md)

## Part 1: Summary

🎯 **Goal:** Apply the approved database review: drop 7 unused `ref` columns and build every table in review §5.

🛠️ **How:** The review's §5 SQL went verbatim into `db/010` and new `db/012`–`db/015`, each applied twice as `postgres`; the three loaders lost the dropped fields and were re-run, and the design docs were rewritten to the built schema.

🤔 **Why this way:** One idempotent `.sql` file per review section keeps the repo the exact definition and matches OPERATIONS.md §4; all tables were created now, empty, by user decision ("Everything in §5").

🏁 **Result:** 31 tables (`ref` 15, `corpus` 7, `kb` 1, `app` 8), all owned by `postgres`; 285 styles, 74 malts, 90 hops reloaded on the slim shape; `vector` 0.8.0 installed with `kb.chunk` (vector(1024), HNSW + GIN); suite 33 passed.

### 🚦 Steps

- ⏭️ 📝 **Brief:** Skipped; the approved spec `docs/DATABASE-REVIEW.md` (committed on `main` in 8b41df1) served as the brief.
- ✅ 🗺️ **Plan:** 6-task plan approved and committed (e2c8824); user chose "Everything in §5" and the malt-role wording "EBC + name keywords".
- ✅ 🔨 **Implement:** All 6 tasks done in one pass each (5c5e0ae, f5dcea1, f8f0878, 35e2b1e, d52a037, 8544e8e), no fix rounds; only "already exists, skipping" notices on second applies.
  - ⚠️ Deviation: all tables created now, empty, not in the phase that fills them (user decision).
  - ⚠️ Deviation: DATABASE.md §7 marks fill step 2 partly done, since `ref.yeast` and `ref.water_salt` have 0 rows.
  - ⚠️ `vector` extension is owned by `supabase_admin` (created as `postgres`), like the other 8 extensions; expected.
- ✅ 🔍 **Review:** Ready for testing, no must-fix or should-fix (ad8c0eb); 3 notes.
  - ⚠️ Note: 010 drops and re-adds `beer_style_source_id_code_key` on every apply (verbatim from the review; harmless at 285 rows).
  - ⚠️ Note: the DATABASE.md ER diagram shows a subset of columns.
  - ⚠️ Note: RECIPE-ROADMAP's carbonation row stays, matching the P6 plan.
- ✅ 🧪 **Verify:** Read-only catalog checks, loaders re-run with no duplicates and no hop-report diff, constraints and idempotency proven in rolled-back transactions. 🧮 spot checks ✅ 22/22 · 🧪 tests ✅ 42/42 (33 pytest + 9 database)

👀 **Start here:** [`docs/DATABASE.md`](../../DATABASE.md): it should describe the four built schemas with the table counts above, list the 7 dropped columns in §2, and name behaviour that moved to code in §8.

📁 **Changed files:**
- `PROJECT.md`
- `db/010_ref_schema.sql`
- `db/012_style_fit.sql`
- `db/013_corpus.sql`
- `db/014_kb.sql`
- `db/015_app.sql`
- `docs/DATABASE-REVIEW.md`
- `docs/DATABASE.md`
- `docs/RECIPE-ROADMAP.md`
- `docs/STYLE-FIT.md`
- `docs/STYLE-PROFILES.md`
- `docs/work/ref-spotcheck/plan.md`
- `docs/work/slim-ref/plan.md`
- `docs/work/slim-ref/review.md`
- `docs/work/water-salts/plan.md`
- `loaders/hops.py`
- `loaders/malts.py`
- `loaders/styles.py`
- `tests/test_hops.py`
- `tests/test_malts.py`
- `tests/test_styles.py`

## Part 2: Spot checks

All commands run from the repo root and are read-only.

### ✅ C1 · Styles unique on the new key (review §5.1)

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select count(*), count(distinct (source_id, code)) from ref.beer_style"
```

| Expected | Actual | Result |
|---|---|---|
| 285\|285 | 285\|285 | ✅ pass |

### ✅ C2 · Styles per guide

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select guide, count(*) from ref.beer_style group by 1 order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| BA\|169, BJCP\|116 | BA\|169, BJCP\|116 | ✅ pass |

### ✅ C3 · Ingredients unchanged

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select count(*) from ref.ingredient"
```

| Expected | Actual | Result |
|---|---|---|
| 164 | 164 | ✅ pass |

### ✅ C4 · Malts keep extract, no `potential_sg` provenance

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select count(*), count(extract_dbfg_pct), count(*) filter (where field_source ? 'potential_sg') from ref.fermentable"
```

| Expected | Actual | Result |
|---|---|---|
| 74\|74\|0 | 74\|74\|0 | ✅ pass |

### ✅ C5 · Hops keep alpha, no `beta_pct` provenance

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select count(*), count(alpha_pct), count(*) filter (where field_source ? 'beta_pct') from ref.hop"
```

| Expected | Actual | Result |
|---|---|---|
| 90\|87\|0 | 90\|87\|0 | ✅ pass |

### ✅ C6 · The 7 dropped columns are gone (review §4.1, §4.2)

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select count(*) from information_schema.columns where table_schema = 'ref' and (table_name, column_name) in (('beer_style','edition'),('beer_style','co2_vol'),('fermentable','potential_sg'),('fermentable','type'),('hop','beta_pct'),('hop','oils_pct'),('water_salt','molar_mass'))"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C7 · Only the new unique key on `beer_style`

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select conname from pg_constraint where conrelid = 'ref.beer_style'::regclass and contype = 'u'"
```

| Expected | Actual | Result |
|---|---|---|
| beer_style_source_id_code_key | beer_style_source_id_code_key | ✅ pass |

### ✅ C8 · Dropped beta stays recoverable from `raw`

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select i.raw->'hopline-hops'->'200750-cs'->'table'->>'Béta-sav' from ref.ingredient i where i.kind = 'hop' and i.name = 'Citra'"
```

| Expected | Actual | Result |
|---|---|---|
| 3-4.5 % | 3-4.5 % | ✅ pass |

### ✅ C9 · 31 tables, all owned by `postgres` (review §6)

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select schemaname, count(*), count(*) filter (where tableowner = 'postgres') from pg_tables where schemaname in ('ref','corpus','kb','app') group by 1 order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| app\|8\|8, corpus\|7\|7, kb\|1\|1, ref\|15\|15 | app\|8\|8, corpus\|7\|7, kb\|1\|1, ref\|15\|15 | ✅ pass |

### ✅ C10 · New schemas owned by `postgres`

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select nspname, nspowner::regrole from pg_namespace where nspname in ('corpus','kb','app') order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| app\|postgres, corpus\|postgres, kb\|postgres | app\|postgres, corpus\|postgres, kb\|postgres | ✅ pass |

### ✅ C11 · No relation in the four schemas has another owner

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select count(*) from pg_class c join pg_namespace n on n.oid = c.relnamespace where n.nspname in ('ref','corpus','kb','app') and c.relowner::regrole::text <> 'postgres'"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C12 · pgvector installed in `extensions`

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select extversion, extnamespace::regnamespace, extowner::regrole from pg_extension where extname = 'vector'"
```

| Expected | Actual | Result |
|---|---|---|
| 0.8.0\|extensions\|supabase_admin (as the other extensions) | 0.8.0\|extensions\|supabase_admin | ✅ pass |

### ✅ C13 · Embedding column matches bge-m3

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select format_type(atttypid, atttypmod) from pg_attribute where attrelid = 'kb.chunk'::regclass and attname = 'embedding'"
```

| Expected | Actual | Result |
|---|---|---|
| vector(1024) | vector(1024) | ✅ pass |

### ✅ C14 · `kb.chunk` indexes: HNSW and GIN

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select indexname, indexdef ~ 'hnsw', indexdef ~ 'gin' from pg_indexes where schemaname = 'kb' order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| chunk_embedding_idx\|t\|f, chunk_fts_idx\|f\|t, chunk_pkey, chunk_source_id_idx | chunk_embedding_idx\|t\|f, chunk_fts_idx\|f\|t, chunk_pkey\|f\|f, chunk_source_id_idx\|f\|f | ✅ pass |

### ✅ C15 · `ref.source.file_path` replaces `kb.document`

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select data_type from information_schema.columns where table_schema = 'ref' and table_name = 'source' and column_name = 'file_path'"
```

| Expected | Actual | Result |
|---|---|---|
| text | text | ✅ pass |

### ✅ C16 · `fermentable.role` exists

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select data_type from information_schema.columns where table_schema = 'ref' and table_name = 'fermentable' and column_name = 'role'"
```

| Expected | Actual | Result |
|---|---|---|
| text | text | ✅ pass |

### ✅ C17 · `corpus` indexes

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select indexname from pg_indexes where schemaname = 'corpus' and indexname like '%\_idx' order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| recipe_item_kind_raw_key_idx, recipe_item_recipe_id_idx, recipe_style_id_idx | recipe_item_kind_raw_key_idx, recipe_item_recipe_id_idx, recipe_style_id_idx | ✅ pass |

### ✅ C18 · `ref.ingredient_tag` reverse-lookup index

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select count(*) from pg_indexes where schemaname = 'ref' and indexname = 'ingredient_tag_tag_id_idx'"
```

| Expected | Actual | Result |
|---|---|---|
| 1 | 1 | ✅ pass |

### ✅ C19 · `app.recipe` has the typed snapshot and result columns

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select count(*) from information_schema.columns where table_schema = 'app' and table_name = 'recipe' and column_name in ('batch_l','efficiency_pct','og','fg','abv','ibu','srm')"
```

| Expected | Actual | Result |
|---|---|---|
| 7 | 7 | ✅ pass |

### ✅ C20 · New tables are empty, `role` not yet filled

```bash
docker exec -i supabase-db psql -U postgres -d postgres -At -c "select (select count(*) from ref.tag), (select count(*) from ref.misc), (select count(*) from kb.chunk), (select count(*) from corpus.recipe), (select count(*) from app.recipe), (select count(*) from ref.fermentable where role is not null)"
```

| Expected | Actual | Result |
|---|---|---|
| 0\|0\|0\|0\|0\|0 | 0\|0\|0\|0\|0\|0 | ✅ pass |

### ✅ C21 · No code, SQL or n8n file still names a dropped column

```bash
git grep -n -w -E 'beta_pct|oils_pct|molar_mass|co2_vol|potential_sg' -- loaders tests db n8n ':!db/010_ref_schema.sql' | grep -v -E 'potential_sg\(|import .*potential_sg' | wc -l
```

| Expected | Actual | Result |
|---|---|---|
| 0 (only the kept `potential_sg()` function and its test) | 0 | ✅ pass |

### ✅ C22 · Docs mention dropped items only as dropped or moved to code

```bash
grep -rn -E 'potential_sg|beta_pct|oils_pct|molar_mass|co2_vol|usage_effect|hint_knob|source_weight|kb\.document|character_tags' docs/DATABASE.md docs/STYLE-FIT.md docs/STYLE-PROFILES.md docs/RECIPE-ROADMAP.md docs/work/ --exclude-dir=slim-ref
```

| Expected | Actual | Result |
|---|---|---|
| every line says dropped, moved to code, or later (P6) | 11 lines: DATABASE.md 205–207 (dropped list), 427–431 (§8 in code), 444 (§9 later); ref-spotcheck plan 41, 58 and water-salts plan 71 (dropped) | ✅ pass |

## Part 3: Regression tests

No critical test from the plan was missing: the pytest ones exist, and the database ones are
commands, run below. Nothing was added.

Command: `.venv/bin/python -m pytest -v`  ·  Result: ✅ 33 passed

| Test | Protects | Result |
|---|---|---|
| tests/test_malts.py::test_catalogue_wins_hopline_fills | Malt extract merged correctly without `potential_sg` | ✅ |
| tests/test_malts.py::test_user_supplied_fills_only_gaps | Malt extract merge, user data fills gaps only | ✅ |
| tests/test_malts.py::test_hopline_only | Malt `field_source` holds no dropped key | ✅ |
| tests/test_malts.py::test_potential_sg | Potential SG maths unchanged (maths library) | ✅ |
| tests/test_hops.py::test_citra | Hop figures and provenance correct without `beta_pct` | ✅ |
| tests/test_hops.py::test_pack_sizes_and_null_figures | Hop null figures without `beta_pct` | ✅ |
| tests/test_styles.py::test_bjcp_21a, ::test_ba_code_is_slug | Style parsing without `edition` | ✅ |
| the other 26 tests in tests/ | unchanged loader and fetch behaviour | ✅ |

Database regression tests (run 2026-10-11; the loaders are the project's idempotent upserts,
re-run once more on the same source files; the SQL tests run inside transactions that are
rolled back, so nothing is kept):

| Test | Protects | Result |
|---|---|---|
| `.venv/bin/python -m loaders.styles --bjcp shared/rag-files/pending/styles.json --ba shared/rag-files/pending/ba_styles.json`, then C1 | Re-loading styles upserts on `(source_id, code)`, no duplicates: printed `BJCP 2021: 116 styles`, `BA 2026: 169 styles`; C1 `285\|285` | ✅ |
| `.venv/bin/python -m loaders.malts --hopline shared/rag-files/pending/hopline_malts.json --catalogue shared/rag-files/pending/malt_catalogue.json`, then C4 | Malt reload: `loaded: 74 malts`; C4 `74\|74\|0` | ✅ |
| `R=$(mktemp -d)/report.md; .venv/bin/python -m loaders.hops --hopline shared/rag-files/pending/hopline_hops.json --report "$R" && diff "$R" docs/finished/hop-loader/report.md`, then C5 | Hop reload unchanged: `loaded: 90 hops`, no diff; C5 `90\|87\|0` | ✅ |
| C3 after the reloads | `ref.ingredient` stays 164 | ✅ |
| `begin; insert into ref.style_rule (style_id, level, quote) select id, 'allowed', 'test' from ref.beer_style limit 1; rollback;` | A style rule targets exactly one of ingredient or tag: rejected by `style_rule_check` | ✅ |
| `begin; insert into ref.tag (facet, name) values ('character', 'slim-ref-test'); insert into ref.style_character (style_id, dimension, tag_id) select b.id, 'hop_aroma', t.id from ref.beer_style b, ref.tag t limit 1; rollback;` then `select count(*) from ref.tag` | A style character needs its envelope row: rejected by `style_character_style_id_dimension_fkey`; `ref.tag` back to 0 | ✅ |
| `for f in db/010_ref_schema.sql db/012_style_fit.sql db/013_corpus.sql db/014_kb.sql db/015_app.sql; do { echo 'begin;'; cat "$f"; echo 'rollback;'; } \| docker exec -i supabase-db psql -U postgres -d postgres -q -v ON_ERROR_STOP=1 2>&1 \| grep -c ERROR; done` | Each SQL file re-applies on the built database without error (idempotent): `0 0 0 0 0`, psql exit 0 for all five | ✅ |
| C13 | Embeddings match bge-m3, `vector(1024)` | ✅ |
| C9, C10, C11 | Every new object owned by `postgres` | ✅ |

Failures: none.
