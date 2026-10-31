# a2-04 · Inventory list view

Stage: ready
Branch: `a2-04-inventory-list-view`
Milestone: M2 · Requirements: F2.1, F2.4, F1.6 ([SYSTEM.md](../SYSTEM.md))
Blocked by: a2-03

## Goal
The Inventory view lists what you have, with search and a kind filter.

## What to build
- The `/inventory` view: a table (name, kind, amount and unit) on wide screens and a list of cards
  on narrow ones.
- A search box and a kind filter (All, fermentable, hop, yeast, misc, water salt, other). Both live
  in the URL query (`?q=&kind=`), so a link or the AI (`open_view`, M6) can open the view already
  filtered.
- Typing in search does not fire a request per key press (debounce, or another approach the lesson
  compares).
- Items with amount 0 show a "used up" badge.
- Loading, empty and error use the shared states (a1-06).

## Acceptance criteria
- **AC1** Opening `/inventory?kind=hop&q=cas` shows the filtered list, with the controls set to
  match.
- **AC2** Changing the filter updates the URL, and Back restores the previous filter.
- **AC3** An empty inventory shows the empty state with a pointer to adding an item.
- **AC4** A used-up item is shown, marked.

## Tests
Needed: component tests with MSW: filtered URL, empty state, used-up badge, error state.

## Out of scope
- Adding, editing and deleting (a2-07, a2-09).

## Deviations

None yet.
