# Review: ref-schema

Diff: main...ref-schema at 7ac4ae5  ·  Verdict: ready for testing

Checked: every task in `plan.md` against the diff, the Source doc (`docs/work/fill-ref/README.md`
global constraints and Review focus 1–4), scope, correctness of the helpers, tests, safety and
records. Also ran `pytest` (8 passed) and read the live catalog as `postgres`: schema `ref` and
all 7 tables owned by `postgres`, 8 `ref.source` rows, `ref.ingredient` empty, only
`ref.fermentable` has `on delete cascade`.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | db/010_ref_schema.sql:47, :26, :28 | `ingredient.kind`, `beer_style.guide` and `beer_style.code` are nullable, yet they are part of the natural keys `unique (kind, producer_key, name_key)` and `unique (guide, edition, code)`. Postgres treats NULLs as distinct, so a row with a NULL key never hits `ON CONFLICT` and every re-run adds a duplicate. Matches the plan's wording; today every planned loader passes a constant `kind`/`guide`, and BA codes are slugs, so it is harmless now. | Review focus 4 (re-running never duplicates) then rests on loader discipline, not on the schema. `NOT NULL` on the three columns would make it hold by construction. |
| 2 | should-fix | db/010_ref_schema.sql:57, :66, :77, :90 | `on delete cascade` is on `fermentable` only; `hop`, `yeast` and `water_salt` reference `ref.ingredient` without it. Matches the plan's wording. | Inconsistent: deleting a fermentable ingredient removes its detail row, deleting a hop/yeast/salt fails with an FK error. Safe (no data loss), but a re-load or cleanup step will behave differently per kind. User decides which is intended. |
| 3 | should-fix | db/011_ref_sources.sql:42 | `water-chemistry` has edition `IUPAC standard atomic weights`, which names no edition or year. | Global constraint: every source has an edition or version. The `water-salts` loader computes molar masses from specific atomic weights, so the table year (e.g. the CIAAW/IUPAC 2021 values) is what makes those numbers traceable. |
| 4 | note | loaders/common.py:51-60 | `name_key` drops characters NFKD does not decompose: `Weißbier` → `weibier`, `Æble` → `ble`, `日本` → `''`. An all-non-Latin name gives an empty key, so two such names of one kind and producer would upsert into one row. None of the measured source files is known to contain such names. | Silent merge risk only if a future source has them; the plan's `name_key` spec is met as written. |
| 5 | note | tests/test_common.py:13-15 | Implementer note (a) confirmed: psycopg's `Range` turns a `None` side's bound to open on construction (`Range(5, None, "[]").bounds == "[)"`), so the test cannot tell `[5,)` from `[5,]`. No implementation can produce the wrong bound there; the test still fails for `NULL`, `[5,0]` and `[5,5]`, which is what Review focus 1 names. | No action. |
| 6 | note | db/011_ref_sources.sql | 5 sources have `licence` NULL (implementer note c). The plan required only `GPL-3.0` and `unknown`; the file header and the PROJECT.md §8 entry say NULL means not checked yet. | No action now; worth settling before any data is published. |
| 7 | note | loaders/db.py | No unit tests (implementer note d); the plan asks only for command checks. PROJECT.md §8 records the measured results, including the upsert-twice check rolled back. | dev-verify should re-run the two Task 3 commands. |
| 8 | note | db/010_ref_schema.sql:38 | `characteristic_ingredients` is `text`, as the plan says; `docs/DATABASE.md` §2 draws it as `text_arr`. | The plan is the spec here; DATABASE.md is now out of step on this one column. |

Plan: all three tasks done as written; no deviations needed. Scope: only the plan's Files table
plus PROJECT.md. Safety: no secrets in the diff, schema only from `db/*.sql`, `connect()` reads
only the 4 named variables. Records: PROJECT.md §4 (Database and Scripts rows) and §8 updated
per task; commits are single lines with no body or trailer.
