# a1-01 · Tailwind and shadcn/ui

Stage: ready
Branch: `a1-01-tailwind-shadcn`
Milestone: M1 · Requirements: F1.5, F1.6 (base) ([SYSTEM.md](../SYSTEM.md))
Blocked by: a0-06

## Goal
The app has its styling system: Tailwind for layout and spacing, shadcn/ui for components, light and
dark following the OS.

## What to build
- Tailwind CSS and shadcn/ui set up in `app/web` with their CLIs.
- A theme in CSS variables; dark mode follows the operating system.
- `StatusBadge` rebuilt on shadcn's `Badge`.

## Acceptance criteria
- **AC1** Switching the OS to dark mode switches the page.
- **AC2** The components in `src/components/ui/` came from the shadcn CLI and are unedited, or each
  edit has a one-line comment saying why.
- **AC3** Lint, type check, build and the existing tests pass.

## Tests
Not needed: no new behaviour; update the existing tests if a label's markup changed.

## Out of scope
- Layout and menu (a1-02).

## Deviations

None yet.
