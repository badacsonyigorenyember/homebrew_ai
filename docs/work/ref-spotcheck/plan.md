# `ref` spot-check pack and P1a results — implementation plan

Stage: draft
Source: [`docs/work/fill-ref/README.md`](../fill-ref/README.md) (P1a index, item 8; was Task 9)
Branch: ref-spotcheck

## Approach

A read-only SQL pack prints what a person needs to check `ref` against the source PDFs:
counts per table, rows missing a source, and 10 random rows per table. The user's spot-check
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
- [ ] Write `db/checks/ref_spotcheck.sql`: row counts per `ref` table; rows with no `source_id`
  (must be 0); and 10 random rows per table (`order by random() limit 10`) with the columns a
  person would check against the sources.
- [ ] Run it: `docker exec -i supabase-db psql -U postgres -d postgres < db/checks/ref_spotcheck.sql`.
  Put the output in the Report for the user (`needs-input`) and wait for their spot-check
  result before the doc updates.
- [ ] Run the whole suite: `.venv/bin/python -m pytest -v` → all passed (28 expected:
  common 8, styles 4, fermentables 3, hops 6, yeasts 4, water salts 3).
- [ ] Update the docs with measured numbers only. Record known gaps as facts: `malts.json` has no
  type, so fermentable roles wait for P3; it has no sugars, adjuncts or generic malts (feeds
  D4); `co2_vol` is NULL until P2. Add the user's spot-check result.
Done when: 0 rows without a source, the suite passes, and the user has spot-checked.
Commit: `Add ref spot-check pack; record P1a results`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| Every `ref` row is sourced | `ref_spotcheck.sql` no-source count = 0 | 1 |
| All P1a parsers still behave | whole suite (28 tests) | 1 |

## Approved exceptions

## Deviations
