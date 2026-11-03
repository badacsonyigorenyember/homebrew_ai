# a0-03 · Web skeleton

Stage: test-review
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

- 2026-11-02 · TypeScript is pinned to `~6.0.3` in `app/web`, not the template's 7.0.2. With
  `--eslint`, create-vite 9.3.3 asks for TypeScript `~7.0.2`, but `typescript-eslint` 8.72.1 (the
  latest) supports TypeScript `>=4.8.4 <6.1.0`, so `npm install` fails with `ERESOLVE`. Measured in
  a scratch project: with 6.0.3, install, build and lint pass. ESLint was kept over the template's
  new default, Oxlint (your call). Move to TypeScript 7 once `typescript-eslint` supports it.
