# Confirm the hop oil unit and fill the missing hop figures

Status: draft
Slug: hop-figures · Branch: hop-figures

## Why
`ref.hop` comes from hopline.hu's pages only ([`hop-loader`](../../finished/hop-loader/brief.md)).
Two things from that work are still open:

- **The oil unit was never checked.** hopline writes total oil as `%`, but the loader stores it
  as mL/100 g without checking (hop-loader review note 4). Nectaron's page says `ml`. After the
  database review this matters more: total oil is the only oil figure left
  (`hop.oils_pct` was dropped in [`slim-ref`](../../finished/slim-ref/plan.md)), and style fit
  computes hop-aroma intensity from it ([STYLE-FIT.md](../../STYLE-FIT.md) §4).
- **Four hops have gaps.** Measured 2026-10-11: alpha `NULL` for Delta, Lotus and Sterling, and
  total oil `NULL` for those three plus Mount Hood. A hop with no alpha can't be used for
  bittering (IBU), and one with no oil gets no aroma-intensity figure.

## Goal
The oil unit is confirmed against a grower source (or corrected), and the four hops have alpha
and oil figures from a named source, each field's source recorded in `field_source`.

## Scope
In: checking hopline's oil figures against a grower source for a few hops; filling alpha and
total oil for Delta, Lotus, Sterling and Mount Hood; recording the source of each filled field.
Out: beta acids and the oil breakdown (no step reads them, [DATABASE.md](../../DATABASE.md) §2);
re-checking every hop against a grower sheet; adding hops hopline doesn't sell; hop character
tags (P3).

## Requirements
R1. hopline's total-oil figures are checked against a grower source for at least 5 hops,
    Nectaron included, and the result (same unit or not) is written down.
R2. If the unit differs, the stored `total_oil_ml_100g` values are converted or the column is
    corrected, with the conversion in tested code.
R3. Delta, Lotus, Sterling and Mount Hood get the missing alpha and total oil from a named
    source; hopline's figures, where present, are not overwritten.
R4. Each filled field names its source in `hop.field_source`, and the new source exists in
    `ref.source` with an edition or date.
R5. The hop loader stays idempotent and keeps everything it has in `raw`.

## Constraints
- Brewing figures are data from a source, never LLM guesses (CLAUDE.md).
- Schema or source changes are `.sql` files applied as `postgres` (docs/OPERATIONS.md §4).
- Unknown stays `NULL`; a figure no source states is not invented (PROJECT.md §6.3).
- Readable over optimal (PROJECT.md §6.8): follow the malt loader's `USER_SUPPLIED` pattern
  rather than a generic override mechanism.
- Source files are never committed.

## Assumptions
- hopline's oil values (0.4–4.6) already are mL/100 g, so R2 will turn out to be a no-op
  *(unverified)*.
- Delta and Lotus are only missing figures because their hopline pages show another hop
  (`NULL_FIGURES` in `loaders/hop_products.py`); their names, origin and purpose are right
  *(unverified)*.

## Acceptance criteria
A1. The brief or plan records the oil comparison for ≥ 5 hops, Nectaron included (R1).
A2. `select count(*) from ref.hop where total_oil_ml_100g is null` → 0, and the unit matches the
    check (R1, R2, R3).
A3. `select count(*) from ref.hop where alpha_pct is null` → 0 (R3).
A4. The four hops' `field_source` names the new source for each filled field; every other hop's
    `field_source` is unchanged (R3, R4).
A5. Running the hop loader twice gives the same counts, and the whole pytest suite passes (R5).

## Open questions
1. Where do the missing figures come from? — options: a) a grower's published variety sheet
   (e.g. Yakima Chief Hops or BarthHaas), as a new `ref.source` row b) figures you supply, through
   the existing `user-supplied` source, as for Acidulated malt c) leave them `NULL` until a hop
   is needed — recommend: a, because a grower sheet is citable and also serves the R1 unit check.

## Deviations
- 2026-10-11 · R3, R4: the user entered the missing figures by hand in the DB from BeerMaverick
  (Delta, Lotus, Sterling alpha + total oil, Mount Hood total oil; `field_source` names
  `beermaverick`). Measured: 90/90 hops with alpha and total oil. R1 (oil-unit check) is still
  open.
- 2026-10-11 · R3–R5: done outside dev-flow on the user's request. The hop loader's `BEERMAVERICK`
  map (`loaders/hop_products.py`) holds the user's Beer Maverick values (also Enigma's purpose)
  and fills only what hopline lacks; the `beermaverick` source row is in `db/011_ref_sources.sql`.
  Two loader runs give the same hop data. Open question 1 is settled (Beer Maverick). Only R1,
  the oil-unit check, remains.
