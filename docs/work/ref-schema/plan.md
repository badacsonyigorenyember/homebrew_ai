# `ref` schema, source rows and loader helpers — implementation plan

Stage: verify
Source: [`docs/work/fill-ref/README.md`](../fill-ref/README.md) (P1a index, item 2; was Tasks 2–3)
Branch: ref-schema

## Approach

This lays the base every P1a loader builds on. The schema lives in `.sql` files applied with
`psql` as `postgres`. Loaders are Python: a pure `parse_*` function per source file (unit
tested, no DB), then a `load()` that upserts on a natural key through `psycopg`. This item
builds the shared parts: unit and range helpers, BeerJSON reading, the `ref` tables, the
`ref.source` rows, and the connection and upsert helpers. Nothing calls an LLM.

Needs `recover-stack` shipped (DB running). Task 1 needs no DB.

Rules for this work:
- Schema objects come only from `.sql` files in `db/`, applied as `postgres`:
  `docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/<file>.sql`.
  Never through MCP, never as `supabase_admin`. Both files are idempotent (`IF NOT EXISTS`,
  `ON CONFLICT DO NOTHING`).
- `connect()` reads only `POSTGRES_DB`, `POSTGRES_PASSWORD`, `POOLER_TENANT_ID`, `POSTGRES_PORT`
  from the root `.env` and connects as `postgres.<POOLER_TENANT_ID>` to
  `localhost:${POSTGRES_PORT}` (the pooler). Never print `.env`.
- Units are SI; unknown stays `NULL`; every `ref` row has a `source_id` and a whole `raw jsonb`.

Tech: Postgres 15 (self-hosted Supabase), Python 3.12 in `.venv`, `psycopg` 3 (3.3.6 installed),
`pytest` (not installed yet, checked 2026-10-09).

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `requirements.txt` | new | `psycopg[binary]>=3.2`, `pytest>=8` |
| `pytest.ini` | new | `[pytest]` / `pythonpath = .` / `testpaths = tests` |
| `loaders/__init__.py` | new | package marker |
| `loaders/common.py` | new | `num`, `to_range`, `f_to_c`, `name_key`, `read_beerjson` |
| `tests/test_common.py` | new | 8 tests for the helpers |
| `db/010_ref_schema.sql` | new | `ref` schema and its 7 tables |
| `db/011_ref_sources.sql` | new | 8 `ref.source` rows |
| `loaders/db.py` | new | `connect`, `source_id`, `upsert_ingredient` |
| `PROJECT.md` | changed | §4 (Scripts row), §8 |

## Tasks

### Task 1: Loader package and shared helpers
Why: every loader needs the same range, unit and name handling (Review focus 1–3).
- [x] Create `requirements.txt` and `pytest.ini`, then
  `.venv/bin/python -m pip install -r requirements.txt` → `Successfully installed pytest…`
- [x] In `loaders/common.py`:
  - `num(x: str | float | int | None) -> Decimal | None`: `None`, `""` and whitespace → `None`.
    Builds the Decimal from `str(x)`, so `5.0` → `Decimal("5.0")`.
  - `to_range(lo, hi) -> psycopg.types.range.Range | None`: both missing → `None`; both present
    → `[lo,hi]`; only `lo` → `[lo,)`; only `hi` → `(,hi]`; `lo > hi` → `ValueError` naming both
    values. Inputs go through `num`.
  - `f_to_c(f: Decimal | float) -> Decimal`, rounded to 0.1.
  - `name_key(s: str) -> str`: NFKD accent folding, drop `®™©`, lowercase, keep only `[a-z0-9]`.
    Parentheses are dropped as characters, but their content is kept (`Saaz (US)` → `saazus`).
  - `read_beerjson(path) -> dict`: drops lines whose stripped text starts with `//`, then
    returns `json.loads(...)["beerjson"]`. Used by `hop-loader` and `yeast-loader`.
- [x] Write `tests/test_common.py` first and see it fail (`ModuleNotFoundError: loaders`):
  ```python
  from decimal import Decimal as D
  import pytest
  from psycopg.types.range import Range
  from loaders.common import num, to_range, f_to_c, name_key, read_beerjson

  def test_num():
      assert num(None) is None and num("") is None and num("  ") is None
      assert num("25") == D("25") and num(5.0) == D("5.0")

  def test_to_range_closed():
      assert to_range("1.056", "1.070") == Range(D("1.056"), D("1.070"), "[]")

  def test_to_range_open_ended():          # Review focus 1
      assert to_range(5.0, None) == Range(D("5.0"), None, "[)")
      assert to_range(None, "12") == Range(None, D("12"), "(]")

  def test_to_range_missing():             # Review focus 2
      assert to_range(None, "") is None

  def test_to_range_inverted_raises():
      with pytest.raises(ValueError, match="10.*5"):
          to_range(10, 5)

  def test_f_to_c():
      assert f_to_c(64) == D("17.8") and f_to_c(73) == D("22.8")

  def test_name_key():
      assert name_key("Citra®") == "citra"
      assert name_key("Hallertau Mittelfrüh") == "hallertaumittelfruh"
      assert name_key("Saaz (US)") == "saazus"      # Review focus 3
  ```
  plus `test_read_beerjson_strips_comment_header` (uses `tmp_path`: a file with two `//` lines,
  then `{"beerjson": {"version": 1}}` → `{"version": 1}`).
- [x] Implement, then `.venv/bin/python -m pytest tests/test_common.py -v` → 8 passed.
Done when: 8 passed.
Commit: `Add loader helpers: ranges, units, name keys`

### Task 2: `ref` schema and source rows
Why: the tables every loader writes into, each row traceable to a source.
- [x] `db/010_ref_schema.sql`: `create schema if not exists ref` and these tables, all owned by
  `postgres`. Column names are fixed by this list:
  - `source(id identity pk, slug text unique not null, title, edition, publisher, licence, url, notes)`
  - `beer_style(id identity pk, source_id fk not null, guide text not null check in ('BJCP','BA'), edition text not null, code text not null, name, category, category_code, og numrange, fg numrange, ibu numrange, srm numrange, abv numrange, co2_vol numrange, characteristic_ingredients text, raw jsonb not null, unique(guide, edition, code))`. `co2_vol` stays NULL until P2.
  - `ingredient(id identity pk, kind text not null check in ('fermentable','hop','yeast','misc','water_salt'), name text not null, name_key text not null, producer text not null default '', producer_key text not null default '', source_id fk not null, raw jsonb not null, unique(kind, producer_key, name_key))`
  - `fermentable(ingredient_id pk fk on delete cascade, potential_sg numeric(5,4), extract_dbfg_pct numeric(4,1), ebc numrange, type text, max_pct numeric(4,1))`. `type` and `max_pct` stay NULL until P3.
  - `hop(ingredient_id pk fk on delete cascade, origins text[], purpose text check in ('aroma','bittering','dual'), alpha_pct numrange, beta_pct numrange, total_oil_ml_100g numrange, oils_pct jsonb, field_source jsonb not null)`
  - `yeast(ingredient_id pk fk on delete cascade, product_id text, type text, form text, attenuation_pct numrange, temp_c numrange, flocculation text check in ('very low','low','medium low','medium','medium high','high','very high'), alcohol_tolerance_pct numeric(4,1))`
  - `water_salt(ingredient_id pk fk on delete cascade, formula text not null, molar_mass numeric(7,3) not null, ion_mg_per_l_per_g jsonb not null)`
- [x] `db/011_ref_sources.sql` inserts these slugs `ON CONFLICT (slug) DO NOTHING`, each with an
  edition or version: `bjcp-2021`, `ba-2026`, `weyermann-specs`, `viking-malt-2020`, `hops-json`,
  `hopslist`, `brewtarget-default-data` (licence `GPL-3.0`), `water-chemistry` (standard atomic
  masses, edition `IUPAC standard atomic weights 2021`). For `hops-json` and `hopslist` the provenance is unknown: licence `unknown`,
  notes `provenance unverified`.
- [x] Apply `010` then `011` with the command under *Rules* → no `ERROR`.
- [x] Verify: `docker exec supabase-db psql -U postgres -d postgres -Atc "select count(*) filter (where tableowner='postgres'), count(*) from pg_tables where schemaname='ref'; select count(*) from ref.source"` → `7|7` and `8`
- [x] Apply both files again → same output, no error.
Done when: 7 tables owned by `postgres`, 8 sources, and re-applying changes nothing.
Commit: `Add ref schema and source rows`

### Task 3: DB helpers for loaders
Why: one connection path and one natural-key upsert, so re-running a loader never duplicates (Review focus 4).
- [x] `loaders/db.py`:
  - `connect() -> psycopg.Connection`: reads the 4 variables from the root `.env`,
    `autocommit=False`.
  - `source_id(conn, slug: str) -> int`: raises `LookupError` if the slug is missing.
  - `upsert_ingredient(conn, kind: str, name: str, producer: str, source_id: int, raw: dict) -> int`:
    `INSERT … ON CONFLICT (kind, producer_key, name_key) DO UPDATE` returning `id`, with
    `name_key = name_key(name)`, `producer_key = name_key(producer)` (`''` when there's no
    producer).
- [x] Verify: `.venv/bin/python -c "from loaders.db import connect, source_id; c=connect(); print(source_id(c,'bjcp-2021'))"` → an integer
- [x] Verify the error path: `source_id(c, 'nope')` raises `LookupError`.
- [x] Run the whole suite → all pass.
Done when: both verifies behave as stated.
Commit: `Add DB helpers for ref loaders`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| Open-ended range keeps its open bound | `tests/test_common.py::test_to_range_open_ended` | 1 |
| Missing range is `NULL`, not zero | `tests/test_common.py::test_to_range_missing` | 1 |
| Inverted range is rejected | `tests/test_common.py::test_to_range_inverted_raises` | 1 |
| °F → °C conversion | `tests/test_common.py::test_f_to_c` | 1 |
| Name keys keep `(US)` apart from the plain name | `tests/test_common.py::test_name_key` | 1 |
| BeerJSON comment header is stripped | `tests/test_common.py::test_read_beerjson_strips_comment_header` | 1 |
| Schema and sources are idempotent | re-apply check (Task 2) | 2 |

## Approved exceptions

## Deviations
- 2026-10-09 · Task 2: `beer_style.guide`, `beer_style.code` and `ingredient.kind` are now
  `NOT NULL` — review finding 1: a NULL in a natural key never hits `ON CONFLICT`, so re-runs
  would duplicate. User approved.
- 2026-10-09 · Task 2: `hop`, `yeast` and `water_salt` FKs to `ref.ingredient` now
  `on delete cascade`, like `fermentable` — review finding 2: same delete behaviour for every
  kind. User approved.
- 2026-10-09 · Task 2: `water-chemistry` edition is `IUPAC standard atomic weights 2021` —
  review finding 3: the edition must name the table year. User approved.
- 2026-10-09 · Task 2: since the tables already existed, `010` ends with `ALTER` statements
  (`set not null`; drop-and-add of the three FKs) and `011` with an `UPDATE` of the
  `water-chemistry` edition, so both files bring an existing DB to the new state and stay
  idempotent. Applied twice to the live DB and twice to a scratch DB (then dropped): same result.
