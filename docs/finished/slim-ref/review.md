# Review: slim-ref

Diff: main...slim-ref at 8544e8e  ·  Verdict: ready for testing

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | note | db/010_ref_schema.sql:118-120 | The review §5.1 block drops and re-adds `beer_style_source_id_code_key` on every apply, so the unique index is rebuilt each run. Taken verbatim from the review, as the plan asks. | Harmless at 285 rows, and no foreign key depends on that constraint (corpus and app reference `beer_style.id`). |
| 2 | note | docs/DATABASE.md:100-150 | The ER diagram lists a subset of columns: `beer_style` leaves out `category`, `category_code`; `ingredient` leaves out `name_key`, `producer_key`; `source` leaves out `publisher`, `notes`. Every column it does name exists in the catalog. | No dropped or invented column is shown. The `.sql` files are named as the exact definitions. |
| 3 | note | docs/RECIPE-ROADMAP.md:237 | "Carbonation volumes per style … `ref.beer_style` column + function" stays. | Matches DATABASE.md §9 (`co2_vol` comes back in P6 with its source), so it describes the current plan. |

## What was checked

- **Plan:** all 6 tasks done as written. The only differences are the two recorded under
  Deviations (all tables created now, by user decision; DATABASE.md §7 step 2 marked partly done).
- **Spec (DATABASE-REVIEW.md §5):** each `db/01x` file was compared line by line, whitespace
  ignored, with the review's §5.1–§5.5 SQL. The only differences are header comments and the
  added `create extension if not exists vector with schema extensions` in 014, which the plan
  calls for.
- **Loaders and tests:** `edition`, `potential_sg` and `beta_pct` were removed from the
  dataclasses, merge/parse code, inserts and upsert `set` lists. The styles upsert is
  `on conflict (source_id, code)`, and `source_id` is no longer in the `set` list.
  `potential_sg()` and `test_potential_sg` are kept. `git grep` finds no code, SQL or n8n file
  that still names a dropped column.
- **Live DB (read-only, 2026-10-11):** `ref` 15 / `corpus` 7 / `kb` 1 / `app` 8 tables, all
  owned by `postgres`. No object in the four schemas has another owner. The three new schemas
  are owned by `postgres`. `beer_style` is 285|285 distinct `(source_id, code)`. The only unique
  constraint is `beer_style_source_id_code_key`. `fermentable` 74|74|0 and `hop` 90|87|0
  (`field_source` holds no dropped keys). `vector` 0.8.0 is in `extensions` (owner
  `supabase_admin`). `kb.chunk.embedding` is `vector(1024)` and has HNSW, GIN, pkey and
  `source_id` indexes. The `ref` columns match DATABASE.md.
- **Tests:** `.venv/bin/python -m pytest -q` → 33 passed.
- **Malt role wording:** STYLE-FIT §2, DATABASE.md §2 and PROJECT.md §8 say "EBC + name
  keywords", as the user decided.
- **Scope:** every changed file is in the plan's Files table. No unrelated edits.
- **Safety:** no secrets in the diff, and every DB change is a `.sql` file applied as `postgres`.
- **Records:** PROJECT.md has §4 Database / Vector search rows, the §5 malt row ("74 with
  extract"), D4 removed from §7 with its *why* in §4, one §8 entry per task (newest first), and
  "Last updated" 2026-10-11. The DATABASE-REVIEW status and Deviations are updated. All 7
  commits are one line each, with no body or trailer.
