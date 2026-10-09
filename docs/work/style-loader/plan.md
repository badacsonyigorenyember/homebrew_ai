# Styles loader (BJCP 2021 + BA 2026) — implementation plan

Stage: review
Source: [`docs/work/fill-ref/README.md`](../fill-ref/README.md) (P1a index, item 3; was Task 4)
Branch: style-loader

## Approach

`loaders/styles.py` parses the two style JSON files into `Style` records with a pure function
per guide (unit tested, no DB), then upserts them into `ref.beer_style` on
`(guide, edition, code)`. Vitals become `numrange`s through `to_range`, so open-ended and
missing ranges stay honest. The whole input record is kept in `raw`, because P3 tagging reads
the prose fields later.

Needs `ref-schema` shipped. **Needs the user:** re-add `styles.json` and `ba_styles.json`
(the plan uses `shared/rag-files/pending/`). Without them, Task 2 is `blocked`.

Measured shapes (2026-10-08 copies): `styles.json` is a list of 116, all values strings, and
20 styles have no vitals (27A–34C). `ba_styles.json` is a list of 169 with numbers as floats.
25 have no OG, and 12 have `srmmin` but no `srmmax`.

Rules for this work: every row has `source_id` (`bjcp-2021`, `ba-2026`); unknown stays `NULL`;
the loader is idempotent; source files are never committed; the DB is reached only through
`loaders.db`.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `loaders/styles.py` | new | `Style`, `parse_bjcp`, `parse_ba`, `load`, CLI |
| `tests/test_styles.py` | new | 4 parser tests |
| `PROJECT.md` | changed | §5 BJCP and BA rows, §8 |

## Tasks

### Task 1: Parse BJCP and BA styles
Why: correct ranges are what the style fit and targets depend on (Review focus 1, 2).
- [x] In `loaders/styles.py`, using `num` and `to_range` from `loaders.common`:
  `@dataclass Style(guide, edition, code, name, category, category_code, og, fg, ibu, srm, abv, characteristic_ingredients, raw)`;
  `parse_bjcp(rows: list[dict]) -> list[Style]` (guide `"BJCP"`, edition `"2021"`, code = `number`);
  `parse_ba(rows) -> list[Style]` (guide `"BA"`, edition `"2026"`, code = the `number` slug).
  `raw` = the whole input dict.
- [x] Write the tests first and see them fail on import. Fixtures are inline dicts copied from the
  measured files:
  - `test_bjcp_21a`: `{number:"21A", name:"American IPA", ogmin:"1.056", ogmax:"1.070", ibumin:"40", ibumax:"70", srmmin:"6", srmmax:"14", …}` → `og == Range(D("1.056"), D("1.070"), "[]")`, `ibu == Range(D("40"), D("70"), "[]")`, `guide == "BJCP"`, `"aroma" in raw`
  - `test_bjcp_specialty_no_vitals`: a `27A` row with empty vitals → all five ranges `None`,
    and the row is returned (Review focus 2)
  - `test_ba_open_srm`: `{number:"x", srmmin:5.0, srmmax:None, …}` → `srm == Range(D("5.0"), None, "[)")` (Review focus 1)
  - `test_ba_code_is_slug`: `ordinary-bitter` → `code == "ordinary-bitter"`, `edition == "2026"`
- [x] Implement, then `.venv/bin/python -m pytest tests/test_styles.py -v` → 4 passed; whole suite passes.
Done when: 4 passed.
Commit: `Parse BJCP 2021 and BA 2026 styles`

### Task 2: Load styles into `ref.beer_style`
Why: every later step picks its style from this table (Review focus 4).
- [x] Add `load(conn, styles: list[Style]) -> int`, an upsert on `(guide, edition, code)` with
  `source_id` from `source_id(conn, 'bjcp-2021' | 'ba-2026')`, and the CLI
  `python -m loaders.styles --bjcp PATH --ba PATH`.
- [x] Run it twice:
  `.venv/bin/python -m loaders.styles --bjcp shared/rag-files/pending/styles.json --ba shared/rag-files/pending/ba_styles.json`
- [x] After each run: `select guide, count(*), count(og) from ref.beer_style group by 1 order by 1`
  → `BA|169|144`, `BJCP|116|96`.
- [x] `select og, ibu, srm from ref.beer_style where guide='BJCP' and code='15B'` →
  `[1.036,1.044]|[25,45]|[25,40]` (measured in `styles.json`).
- [x] PROJECT.md §5: BJCP and BA rows → loaded, with the measured counts and date.
Done when: both runs give the same counts and 15B matches.
Commit: `Load BJCP 2021 and BA 2026 styles into ref`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| BJCP string vitals become closed ranges | `tests/test_styles.py::test_bjcp_21a` | 1 |
| Specialty styles load with `NULL` ranges | `tests/test_styles.py::test_bjcp_specialty_no_vitals` | 1 |
| BA open-ended SRM stays `[5,)` | `tests/test_styles.py::test_ba_open_srm` | 1 |
| BA code is the slug, edition 2026 | `tests/test_styles.py::test_ba_code_is_slug` | 1 |
| Re-running doesn't duplicate | load-twice counts | 2 |

## Approved exceptions

## Deviations
