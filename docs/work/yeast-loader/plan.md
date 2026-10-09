# Yeast loader (Brewtarget, 571 entries) — implementation plan

Stage: draft
Source: [`docs/work/fill-ref/README.md`](../fill-ref/README.md) (P1a index, item 6; was Task 7)
Branch: yeast-loader

## Approach

The two Brewtarget BeerJSON files are read with `read_beerjson` (from `loaders.common`), their
`cultures` parsed into `Yeast` records (pure, unit tested) with temperatures converted to °C,
then deduplicated and written as `ref.ingredient` (kind `yeast`, producer set) + `ref.yeast`.
Dedupe merges only true repeats: the same producer and product id, or, when there is no
product id, the same producer and name.

Needs `ref-schema` shipped. **Needs the user:** re-add
`DefaultContent003-Ingredients-Hops-Yeasts.json` and `DefaultContent004-MoreYeasts.json` (the
plan uses `shared/rag-files/pending/`). Task 1's WLP001 fixture is copied from the first file,
so all tasks are `blocked` until both are back.

Measured shapes (2026-10-08 copies): `beerjson.cultures` holds 296 entries in `DefaultContent003`
and 275 in `DefaultContent004`. Of the 571 entries, 71 have no `product_id`, and 72
`(producer, product_id)` pairs repeat across the two files. 4 entries are already in °C.
DATABASE.md estimated ~500 rows after dedupe (unverified).

Rules for this work: SI units (°F converted once, °C left alone); unknown stays `NULL`; `raw`
keeps the whole record; source `brewtarget-default-data`; the loader is idempotent; source files
are never committed.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `loaders/yeasts.py` | new | `Yeast`, `parse_cultures`, `dedupe`, `load`, CLI |
| `tests/test_yeasts.py` | new | 4 tests |
| `PROJECT.md` | changed | §5 Brewtarget row, §8 |

## Tasks

### Task 1: Parse Brewtarget cultures
Why: attenuation and temperature drive FG and the fermentation step (Review focus 5).
- [ ] In `loaders/yeasts.py`:
  `@dataclass Yeast(name, producer, product_id, type, form, attenuation_pct, temp_c, flocculation, alcohol_tolerance_pct, raw)`;
  `parse_cultures(rows) -> list[Yeast]`. Temperature uses its `unit`: `F` → `f_to_c`, `C` → as
  is, anything else → `ValueError`. Flocculation must be one of the 7 schema values
  (`very low` … `very high`) or `None`.
- [ ] Write the tests first and see them fail on import:
  - `test_wlp001`: the WLP001 record copied from `DefaultContent003` →
    `attenuation_pct == Range(D("73"), D("85"), "[]")`,
    `temp_c == Range(D("17.8"), D("22.8"), "[]")`, `flocculation == "medium"`,
    `alcohol_tolerance_pct == D("10")`
  - `test_celsius_not_converted`: `temperature_range` in `C`, 18–22 →
    `Range(D("18"), D("22"), "[]")` (Review focus 5)
- [ ] Implement, then `.venv/bin/python -m pytest tests/test_yeasts.py -v` → 2 passed; whole suite passes.
Done when: 2 passed.
Commit: `Parse Brewtarget yeast cultures`

### Task 2: Deduplicate yeasts
Why: one row per real strain, without merging different strains (Review focus 5).
- [ ] `dedupe(yeasts) -> list[Yeast]` keys on `(name_key(producer), product_id)` when
  `product_id` is set, otherwise on `(name_key(producer), name_key(name))`, and keeps the record
  with the most non-null fields.
- [ ] Tests first, see them fail:
  - `test_dedupe_same_product`: two `White Labs`/`WLP001` records, one without
    `alcohol_tolerance` → 1 record, and it has the tolerance
  - `test_dedupe_keeps_distinct_unnumbered`: two Omega records with no `product_id` and
    different names → 2 records
- [ ] Implement, then run `tests/test_yeasts.py` → 4 passed; whole suite passes.
Done when: 4 passed.
Commit: `Deduplicate yeasts on producer and product id`

### Task 3: Load yeasts into `ref`
Why: the yeast catalogue step 6 chooses from (Review focus 4).
- [ ] Add `load(conn, yeasts) -> int`. It passes `name = f"{product_id} {name}"` to
  `upsert_ingredient` when `product_id` is set, so different strains from one producer never
  collide on `name_key`, then upserts `ref.yeast` on `ingredient_id`. CLI:
  `python -m loaders.yeasts PATH [PATH…]` (reads every file, then dedupes across all of them).
- [ ] Run it twice with both files.
- [ ] After each run: `select count(*), count(attenuation_pct), count(temp_c) from ref.yeast`
  gives the same result, with `count(*) < 571`. Record the numbers in the plan and in
  PROJECT.md.
- [ ] PROJECT.md §5: Brewtarget row → yeasts loaded, with the measured counts and date.
Done when: both runs give the same counts, below 571.
Commit: `Load Brewtarget yeasts into ref`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| °F ranges converted to °C | `tests/test_yeasts.py::test_wlp001` | 1 |
| °C ranges not converted twice | `tests/test_yeasts.py::test_celsius_not_converted` | 1 |
| True repeats merged, keeping the fuller record | `tests/test_yeasts.py::test_dedupe_same_product` | 2 |
| Different unnumbered strains stay apart | `tests/test_yeasts.py::test_dedupe_keeps_distinct_unnumbered` | 2 |
| Re-running doesn't duplicate | load-twice counts | 3 |

## Approved exceptions

## Deviations
