# a1-04 · AI panel shell

Stage: ready
Branch: `a1-04-ai-panel-shell`
Milestone: M1 · Requirements: F1.3 ([SYSTEM.md](../SYSTEM.md))
Blocked by: a1-02

## Goal
The AI panel has its place in the layout, before it can talk: docked on the right, collapsible,
full-screen on a phone.

## What to build
- A right-hand panel with a header, an empty message area ("Ask about your brewing") and an input
  with a send button.
- Sending shows a notice that the assistant is not connected yet; nothing is sent anywhere.
- A button collapses and expands the panel; the state is saved like the tabs (a1-03).
- Below the medium breakpoint the panel opens as a full-screen sheet from a button.

## Acceptance criteria
- **AC1** The panel collapses and expands, and stays that way after a reload.
- **AC2** The main view gets the freed width when the panel is collapsed.
- **AC3** At phone width the panel is a full-screen sheet with a close button.
- **AC4** The input is reachable by keyboard and Enter sends.

## Tests
Needed: one component test: collapse, reload (re-render with the saved state), still collapsed.

## Out of scope
- Any chat behaviour (M6).

## Deviations

None yet.
