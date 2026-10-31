# a1-03 · Tabs

Stage: ready
Branch: `a1-03-tabs`
Milestone: M1 · Requirements: F1.2 ([SYSTEM.md](../SYSTEM.md))
Blocked by: a1-02

## Goal
Views open as tabs, so you can keep an inventory list and a batch open side by side and switch
between them.

## What to build
- A tab bar above the main area. Navigating to a view opens a tab for its path, or focuses the one
  already open.
- Each tab has a title and a close button; closing the active tab focuses its neighbour; closing the
  last shows the Inventory view.
- The tab logic is a pure reducer in its own file (open, focus, close), used through one hook.
- Open tabs and the active tab are saved in `localStorage` and restored on reload; reading and
  writing are wrapped so a blocked storage never breaks the app.

## Acceptance criteria
- **AC1** Opening Inventory twice gives one tab.
- **AC2** Closing the active tab focuses the neighbour on its left (or right when it was first).
- **AC3** After a reload the same tabs are open and the same one is active.
- **AC4** With `localStorage` throwing (simulate in a test), the app still works with one tab.

## Tests
Needed: unit tests for the reducer (open, focus existing, close active, close last); one component
test that clicking a menu item adds a tab.

## Out of scope
- Tabs for detail views such as `/inventory/12` work by the same rule; nothing extra to build here.

## Deviations

None yet.
