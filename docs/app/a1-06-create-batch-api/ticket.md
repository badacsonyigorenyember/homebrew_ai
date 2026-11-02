# a1-06 · Create a batch from a recipe

Stage: ready
Branch: `a1-06-create-batch-api`
Milestone: M1 · Requirements: F4.1 ([SYSTEM.md](../SYSTEM.md))
Blocked by: a1-05

## Goal
The API makes a batch from a saved recipe, as a copy, so you can brew without a recipe page.

## What to build
- `GET /api/recipes/brewable`: the recipes that have a `process`, newest first, with `id`, style
  code and name, `og`, `fg`, `abv`, `ibu`, `batchL` and the created date. This feeds the new-batch
  dropdown; the recipe pages are M4.
- `POST /api/batches` with `recipeId`, `name` and `brewDate`, in one transaction:
  - the next batch number (the highest so far plus one);
  - a batch with status `plan` that copies the recipe's `batch_l`, `efficiency_pct`, `process`,
    `og`, `fg`, `abv`, `ibu` and `srm`;
  - one `batch_item` per recipe item, keeping the recipe item's id as its source.
  - 201 Created with a `Location` header and the batch.
- `GET /api/batches`: number, name, style, brew date and status, latest brew date first.
- Numbers are copied, never computed (C4).

## Acceptance criteria
- **AC1** A new batch's items match the recipe's items; changing the recipe's item afterwards (in
  the test database) does not change the batch's.
- **AC2** Two batches get numbers 1 and 2.
- **AC3** A recipe without a `process` gives 400 problem details saying so; an unknown recipe gives
  404.
- **AC4** A missing name or brew date gives 400 with a message per field.
- **AC5** `GET /api/batches` lists the new batch.

## Tests
Needed: integration tests on the test database for each criterion.

## Out of scope
- Brew-day steps (a1-08).
- Editing the batch recipe (M3).
- Recipe list and detail pages (M4).

## Deviations

None yet.
