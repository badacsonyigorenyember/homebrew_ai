# a0-03 · Web skeleton

Stage: ready
Branch: `a0-03-web-skeleton`
Milestone: M0 · Requirements: F1.5 (start) ([SYSTEM.md](../SYSTEM.md))
Blocked by: a0-01

## Goal
A React + TypeScript page runs in the browser, with linting and type checks, and one small component
that takes typed props.

## What to build
- `app/web` created from Vite's React + TypeScript template.
- The page shows the title "Brewing app" and a `StatusBadge` component.
- `StatusBadge` takes a `status` prop typed as `"ok" | "down" | "unknown"` and shows a different
  label for each.
- ESLint (from the template) and Prettier, with scripts `dev`, `build`, `lint`, `typecheck` and
  `format`.
- `app/README.md` gains "Run the web app".

## Acceptance criteria
- **AC1** `npm run dev` shows the page in the browser.
- **AC2** `npm run build`, `npm run lint` and `npm run typecheck` pass with no errors.
- **AC3** Passing a status outside the three values is a type error (`npm run typecheck` fails).
- **AC4** Each of the three statuses shows its own label.

## Tests
Needed. First frontend test lesson: Vitest, React Testing Library and jsdom set up; tests that
`StatusBadge` shows the right label for each status.

## Out of scope
- Tailwind and shadcn (a1-01).
- Calling the API (a0-04).

## Deviations

None yet.
