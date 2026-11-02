# a1-07 · Batches page and new batch

Stage: ready
Branch: `a1-07-batches-page`
Milestone: M1 · Requirements: F4.1, F1.5 ([SYSTEM.md](../SYSTEM.md))
Blocked by: a1-06

## Goal
You see your batches and start a new one from a recipe, in the browser.

## What to build
- The `/batches` view: the batches (number, name, style, brew date, status) as a table on wide
  screens and cards on narrow ones.
- A "New batch" button opening a dialog (a full-screen sheet on narrow screens): a recipe dropdown
  from `GET /api/recipes/brewable` (style, OG, ABV and date in each option), a name (the style
  name by default) and a brew date. React Hook Form with a Zod schema that mirrors the API's rules.
- On success the dialog closes and the app opens `/batches/:id`, a placeholder with the batch's
  name until a1-09.
- The response types are written by hand in one file, `src/features/batches/api.ts`; a2-02
  replaces them with generated ones.
- Plain loading and error text for now; the shared states come in a2-06.

## Acceptance criteria
- **AC1** No batches shows "No batches yet" and the New batch button.
- **AC2** Creating a batch opens its page, and going back shows it in the list.
- **AC3** A 400 from the API shows its messages next to the fields.
- **AC4** At phone width (375 px) the list and the dialog fit without sideways scrolling.

## Tests
Needed: component tests with MSW: the list, the empty list, a successful create that navigates, a
server error shown on a field.

## Out of scope
- The batch page itself (a1-09).

## Deviations

None yet.
