Overall: ✅ all 11 checks and 9 tests pass

# Verification: ref-schema

Branch `ref-schema` at 4e578bb, against `main`. Run 2026-10-09.

## Part 1: Where to look

**Start here:** `docker exec -it supabase-db psql -U postgres -d postgres`, then `\dt ref.*` and
`select slug, edition, licence from ref.source;`. You should see 7 tables in `ref`, all owned by
`postgres`, and 8 source rows, each with an edition. All other `ref` tables are empty: the
loaders that fill them are later work items.

**Database**
- New schema `ref` with 7 tables (`db/010_ref_schema.sql`): `source`, `beer_style`,
  `ingredient`, and the per-kind detail tables `fermentable`, `hop`, `yeast`, `water_salt`.
  Ranges are `numrange`; every data row has a `source_id` and a whole `raw jsonb`.
- Natural keys `beer_style (guide, edition, code)` and `ingredient (kind, producer_key,
  name_key)`; all their columns are `NOT NULL`, so a re-run upsert always hits `ON CONFLICT`.
- All 4 detail tables reference `ref.ingredient` with `on delete cascade`.
- 8 rows added to `ref.source` (`db/011_ref_sources.sql`); `water-chemistry` edition is
  `IUPAC standard atomic weights 2021`, the two hop-list sources carry licence `unknown`.
- Both files end with `ALTER`/`UPDATE` statements that bring an older copy of the schema up to
  date, and both can be re-applied without changing anything.

**Scripts**
- `loaders/common.py`: shared helpers for every loader. Turns source values into `Decimal`,
  `numrange` bounds (open-ended when one side is missing, `NULL` when both are), °C from °F,
  and accent-folded name keys; also reads Brewtarget BeerJSON with its `//` header.
- `loaders/db.py`: one connection path (pooler, as `postgres.<tenant>`, reading only 4 `.env`
  variables), a `source_id` lookup that fails loudly, and `upsert_ingredient`, which updates
  the existing row on the natural key instead of adding a duplicate.

**Files and config**
- `requirements.txt` (`psycopg[binary]`, `pytest`), `pytest.ini`, `loaders/__init__.py`,
  `tests/test_common.py` (8 tests). PROJECT.md §4 and §8 updated.

## Part 2: Spot checks

### ✅ C1 · Schema and 7 tables owned by postgres

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select nspowner::regrole from pg_namespace where nspname='ref'; select count(*) filter (where tableowner='postgres') || '|' || count(*) from pg_tables where schemaname='ref'"
```

| Expected | Actual | Result |
|---|---|---|
| `postgres` / `7\|7` | `postgres` / `7\|7` | ✅ pass |

### ✅ C2 · 8 sources, every one with an edition (global constraint)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) || '|' || count(*) filter (where coalesce(edition,'') <> '') from ref.source"
```

| Expected | Actual | Result |
|---|---|---|
| `8\|8` | `8\|8` | ✅ pass |

### ✅ C3 · The 8 planned slugs

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select string_agg(slug, ',' order by slug) from ref.source"
```

| Expected | Actual | Result |
|---|---|---|
| ba-2026, bjcp-2021, brewtarget-default-data, hops-json, hopslist, viking-malt-2020, water-chemistry, weyermann-specs | `ba-2026,bjcp-2021,brewtarget-default-data,hops-json,hopslist,viking-malt-2020,water-chemistry,weyermann-specs` | ✅ pass |

### ✅ C4 · Licences and provenance notes

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select slug, coalesce(licence,'NULL'), notes from ref.source where slug in ('hops-json','hopslist','brewtarget-default-data') order by slug"
```

| Expected | Actual | Result |
|---|---|---|
| brewtarget `GPL-3.0`; both hop sources `unknown` / `provenance unverified` | `brewtarget-default-data\|GPL-3.0\|BeerJSON files …`, `hops-json\|unknown\|provenance unverified`, `hopslist\|unknown\|provenance unverified` | ✅ pass |

### ✅ C5 · water-chemistry edition names the table year (review finding 3)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select edition from ref.source where slug='water-chemistry'"
```

| Expected | Actual | Result |
|---|---|---|
| `IUPAC standard atomic weights 2021` | `IUPAC standard atomic weights 2021` | ✅ pass |

### ✅ C6 · Natural-key and source_id columns are NOT NULL (review finding 1, Review focus 4)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) filter (where is_nullable = 'YES') || '|' || count(*) from information_schema.columns where table_schema = 'ref' and (table_name, column_name) in (('beer_style','guide'), ('beer_style','edition'), ('beer_style','code'), ('ingredient','kind'), ('ingredient','producer_key'), ('ingredient','name_key'), ('beer_style','source_id'), ('ingredient','source_id'))"
```

| Expected | Actual | Result |
|---|---|---|
| `0\|8` (none of 8 nullable) | `0\|8` | ✅ pass |

### ✅ C7 · Every detail table cascades on ingredient delete (review finding 2)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select string_agg(conrelid::regclass || ':' || confdeltype::text, ',' order by conrelid::regclass::text) from pg_constraint where contype = 'f' and confrelid = 'ref.ingredient'::regclass"
```

| Expected | Actual | Result |
|---|---|---|
| all 4 `:c` | `ref.fermentable:c,ref.hop:c,ref.water_salt:c,ref.yeast:c` | ✅ pass |

### ✅ C8 · Natural-key unique constraints

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select conrelid::regclass || ':' || pg_get_constraintdef(oid) from pg_constraint where contype='u' and connamespace='ref'::regnamespace order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| `beer_style (guide, edition, code)`, `ingredient (kind, producer_key, name_key)`, `source (slug)` | `ref.beer_style:UNIQUE (guide, edition, code)`, `ref.ingredient:UNIQUE (kind, producer_key, name_key)`, `ref.source:UNIQUE (slug)` | ✅ pass |

### ✅ C9 · connect() through the pooler and source_id lookup (Task 3)

```bash
.venv/bin/python -c "from loaders.db import connect, source_id; print(source_id(connect(), 'bjcp-2021'))"
```

| Expected | Actual | Result |
|---|---|---|
| an integer | `1` | ✅ pass |

### ✅ C10 · Missing slug raises LookupError (Task 3)

```bash
.venv/bin/python -c $'from loaders.db import connect, source_id\ntry: source_id(connect(), "nope")\nexcept LookupError as e: print("LookupError:", e)'
```

| Expected | Actual | Result |
|---|---|---|
| `LookupError` | `LookupError: no ref.source row with slug 'nope'` | ✅ pass |

### ✅ C11 · upsert_ingredient twice gives one row, same id; rolled back (Review focus 4)

```bash
.venv/bin/python -c "from loaders.db import connect, source_id, upsert_ingredient as up; c=connect(); s=source_id(c, 'water-chemistry'); a=up(c, 'water_salt', 'Gypsum', '', s, {'v': 1}); b=up(c, 'water_salt', 'gypsum ', '', s, {'v': 2}); print(a == b, c.execute('select count(*) from ref.ingredient').fetchone()[0]); c.rollback(); print(c.execute('select count(*) from ref.ingredient').fetchone()[0])"
```

| Expected | Actual | Result |
|---|---|---|
| `True 1` then `0` (nothing left behind) | `True 1` / `0` | ✅ pass |

## Part 3: Regression tests

Command: `.venv/bin/python -m pytest -v`  ·  Result: ✅ 8 passed

| Test | Protects | Result |
|---|---|---|
| tests/test_common.py::test_num | Empty and whitespace values become `None`; Decimal built from `str` | ✅ |
| tests/test_common.py::test_to_range_closed | Two bounds give a closed `[lo,hi]` range | ✅ |
| tests/test_common.py::test_to_range_open_ended | Open-ended range keeps its open bound (Review focus 1) | ✅ |
| tests/test_common.py::test_to_range_missing | Missing range is `NULL`, not zero (Review focus 2) | ✅ |
| tests/test_common.py::test_to_range_inverted_raises | Inverted range is rejected | ✅ |
| tests/test_common.py::test_f_to_c | °F → °C conversion | ✅ |
| tests/test_common.py::test_name_key | Name keys keep `(US)` apart from the plain name (Review focus 3) | ✅ |
| tests/test_common.py::test_read_beerjson_strips_comment_header | BeerJSON comment header is stripped | ✅ |

The plan's last critical behaviour, *Schema and sources are idempotent*, is a command check, not
a pytest. Run: catalog fingerprint (md5 over every `ref` constraint definition, every `ref`
column's type and nullability, and every `ref.source` row), apply `010` then `011` with
`docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/<file>.sql`,
fingerprint again.

| Test | Protects | Result |
|---|---|---|
| Re-apply `010` + `011` on the live DB | Schema and sources are idempotent | ✅ fingerprint `b14dfa90…` before and after, no `ERROR`, still 8 sources and `7\|7` tables |

No critical test from the plan was missing, so none was added.
