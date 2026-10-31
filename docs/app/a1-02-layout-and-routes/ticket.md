# a1-02 · Layout, menu and routes

Stage: ready
Branch: `a1-02-layout-and-routes`
Milestone: M1 · Requirements: F1.1, F1.5 ([SYSTEM.md](../SYSTEM.md))
Blocked by: a1-01

## Goal
The app has its frame: a menu on the left, a view on the right, and a URL for every view.

## What to build
- React Router with routes `/inventory`, `/recipes`, `/batches`, `/devices`, `/settings`; `/` goes
  to `/inventory`; an unknown path shows a "not found" view.
- A layout with the left menu (the five items) and the main area; the current item is highlighted.
- Below the medium breakpoint the menu becomes a drawer opened by a button.
- Each route shows a placeholder page with its title.

## Acceptance criteria
- **AC1** Clicking each menu item shows its page and changes the URL.
- **AC2** Opening a URL directly (or reloading) shows the right page.
- **AC3** At phone width (browser dev tools, 375 px) the menu is a drawer and nothing scrolls
  sideways.
- **AC4** Everything works by keyboard: Tab reaches each menu item, Enter opens it.

## Tests
Needed: component tests with a memory router: `/` lands on Inventory; a menu link shows its page; an
unknown path shows "not found".

## Out of scope
- Tabs (a1-03).

## Deviations

None yet.
