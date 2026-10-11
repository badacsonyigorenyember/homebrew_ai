# `ref` spot-check pack and P1a results — implementation plan

Stage: approved
Source: [`docs/work/fill-ref/README.md`](../fill-ref/README.md) (P1a index, item 8; was Task 9)
Branch: ref-spotcheck

## Approach

A read-only SQL pack prints what a person needs to check `ref` against the source PDFs:
counts per table, rows missing a source, and 10 random rows per table. It covers the 7 tables
P1a loads (`source`, `beer_style`, `ingredient`, `fermentable`, `hop`, `yeast`, `water_salt`);
the 8 style-fit tables `slim-ref` created are empty until P3 and are only counted. The user's spot-check
of that output is RECIPE-ROADMAP P1's done condition ("10 rows spot-checked per table"). Then
the measured P1a results go into PROJECT.md and DATABASE.md.

Needs `style-loader`, `malt-loader`, `hop-loader`, `yeast-loader` and `water-salts` shipped.
**Needs the user:** spot-check the printed rows and say which, if any, are wrong.

Rules for this work: record measured numbers only, and known gaps as facts, not fixes.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `db/checks/ref_spotcheck.sql` | new | read-only spot-check queries |
| `PROJECT.md` | changed | §4 Database row, §5 status column, §8 |
| `docs/DATABASE.md` | changed | status line; §7 steps 1–2 marked done with measured counts |

## Tasks

### Task 1: Spot-check pack, run and record P1a
Why: P1's done condition, and PROJECT.md must state measured facts.
- [ ] Write `db/checks/ref_spotcheck.sql`: row counts for all 15 `ref` tables (the 8 style-fit
  tables must be 0); rows with no `source_id` in `beer_style` and `ingredient`, the two loaded
  tables that carry one (must be 0; the kind tables are sourced through their ingredient row);
  and 10 random rows per loaded table (`order by random() limit 10`) with the columns a person
  would check against the sources.
- [ ] Run it: `docker exec -i supabase-db psql -U postgres -d postgres < db/checks/ref_spotcheck.sql`.
  Put the output in the Report for the user (`needs-input`) and wait for their spot-check
  result before the doc updates.
- [ ] Run the whole suite: `.venv/bin/python -m pytest -v` → all passed (40 expected:
  common 8, styles 4, malts 9, hops 8, fetch_hopline 4, yeasts 4, water salts 3).
- [ ] Update the docs with measured numbers only. Record known gaps as facts:
  `fermentable.role` exists but stays empty until P3; the 74 malts are grain malts from three
  maltsters only (no sugars, adjuncts or extracts); `beer_style.co2_vol` was dropped (no source
  has it; back in P6); the missing alpha and oil of Delta, Lotus, Sterling and Mount Hood were
  entered by hand from BeerMaverick (2026-10-11), so check those against their source too. Add the
  user's spot-check result.
Done when: 0 rows without a source, the suite passes, and the user has spot-checked.
Commit: `Add ref spot-check pack; record P1a results`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| Every loaded `ref` row is sourced | `ref_spotcheck.sql` no-source count = 0 | 1 |
| The style-fit tables are still empty | `ref_spotcheck.sql` counts = 0 | 1 |
| All P1a parsers still behave | whole suite (40 tests) | 1 |

## Approved exceptions

## Deviations

- 2026-10-11 · Task 1: gap notes updated for slim-ref — `fermentable.type` and
  `beer_style.co2_vol` were dropped by the database review, `fermentable.role` was created empty,
  and D4 is closed
- 2026-10-11 · Task 1: the pack covers the 7 loaded tables and only counts the 8 empty style-fit
  tables, and the source check runs on `beer_style` and `ingredient` — `slim-ref` created tables
  without `source_id`; expected suite 28 → 40 and the malt gap note no longer names `malts.json`
  — the loaders were re-scoped and gained tests after this plan was written
