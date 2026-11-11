# Review: a1-02 · Layout, menu and routes

## Round 1 · 2026-11-11 · 896b969

Checks (in `app/web`, working tree clean):
`npm run lint` exit 0 ·
`npm run typecheck` ok ·
`npm test -- --run` 7 passed ·
`npm run build` ok, no warning ·
`npx prettier . --check` "All matched files use Prettier code style!" ·
`npx shadcn@latest add sheet button badge --diff`: all three "No changes." ·
browser console: no React warning on any page.

Tried in the dev server (Chromium, 2026-11-11):

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | clicked Devices from `/nope/deeper` and Inventory from `/batches`: the URL and the page changed, and the clicked link got `aria-current="page"` and the highlight |
| AC2 | yes | typed `/recipes` and `/settings`: right page and highlight; `/nope/deeper` shows "Page not found" inside the layout; `/` becomes `/batches`, and Back from there returns to the page before `/` (`/settings`), so `replace` works |
| AC3 | **no** | at 375 px the menu button and the drawer work, but the left column is still shown: `aside` is 224 px wide and `<main>` is left with 151 px (screenshot taken). `scrollWidth` is 375, so nothing scrolls sideways; the "menu is a drawer" half fails |
| AC4 | yes | at 375 px: Tab reaches "Open menu" first, Enter opens the drawer with focus on Batches and a visible ring, Tab and Enter on Inventory opens it, the drawer closes and focus returns to "Open menu"; Escape closes it the same way. On a wide window the column links are plain `<a href>` and take Tab and Enter |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Spec (AC3) | must fix | `app/web/src/components/layout/AppLayout.tsx:44` | The `<aside>` has no `hidden md:block` (lesson step 8), so below 768 px both the column and the drawer button show. The page area shrinks to 151 px at 375 px, and a keyboard user tabs through the five links twice: once in the drawer, once in the column. | AC3 asks that the menu *is* a drawer at phone width. Hide the column below `md`, and show it from `md` up, on the `<aside>` (not on `MainMenu`, which the drawer reuses). | [Tailwind — Responsive design, "Working mobile-first"](https://tailwindcss.com/docs/responsive-design#working-mobile-first) |
| 2 | Standards | should fix | `app/web/src/components/layout/MainMenu.tsx:5-9` | `'/batches'` is absolute, the other four (`'devices'`, `'inventory'`, …) are relative. They work today only because `MainMenu` is drawn by `AppLayout`, whose route has no path, so relative links resolve against `/`. A relative `to` is resolved against the route the link is drawn in, not against the site root. | The menu's links mean "this view, from anywhere", which is what an absolute path says. If the menu is ever drawn inside a nested route (a batch page with its own layout in a1-09, for example), the relative ones would point under that route instead. Write all five with a leading `/` (lesson step 7a). | [React Router — Navigating, "Link"](https://reactrouter.com/start/declarative/navigating#link), [`<Link>` `relative` prop](https://reactrouter.com/api/components/Link#relative) |
| 3 | Spec | nice to have | `app/web/src/components/layout/MainMenu.tsx:4-10` | The items are in alphabetical order (Batches, Devices, Inventory, Recipes, Settings). F1.1 lists Batches, Recipes, Inventory, Devices, Settings. | The F1.1 order puts the views you brew with first and Settings last; Devices before Recipes is the order nobody would pick on purpose. | [SYSTEM.md F1.1](../../SYSTEM.md#f1--app-shell) |
| 4 | Standards | nice to have | `app/web/src/components/layout/AppLayout.tsx:19,47`, the five `*Page.tsx`, `NotFoundPage.tsx:6` | The header has no side padding or bottom border, so "Brewing App" touches the window's left edge; `<main>` has no padding, so the page title touches the column's border; every `<h1>` is 16 px, the same as body text (measured), because Preflight resets headings. | The frame is what every later page sits in; a page title that looks like body text and content glued to the edges will be copied into every view. Lesson steps 4, 6c and 6e name the classes (`px-4 border-b`, `p-4`, `text-2xl font-semibold`). | [Tailwind — Preflight, "Headings are unstyled"](https://tailwindcss.com/docs/preflight#headings-are-unstyled) |
| 5 | Standards | nice to have | `app/web/src/features/health/HealthBadge.tsx:1-2` | The imports end in `.ts` and `.tsx`, and the neighbour `useHealth` is reached through the full `@/features/health/…` alias. The rest of `src/` imports without extensions, and a neighbour as `./useHealth`. | One way of writing imports keeps them easy to scan and to search for. The extension works only because the Vite template allows it; TypeScript's default does not. | [TypeScript — `allowImportingTsExtensions`](https://www.typescriptlang.org/tsconfig/#allowImportingTsExtensions) |

Outside the ticket: commit `48d7dc9` (the `home` brewer profile, `db/058_home_profile.sql`, PROJECT.md,
RECIPE-ROADMAP.md) is on this branch, so it will reach `main` when a1-02 ships. Not reviewed here.

Done well:
- The drawer is right in every detail the lesson asked for: controlled `Sheet`, `render` on the
  trigger (no nested button), an `aria-label` on the icon button, the same `MainMenu` reused with
  an `onNavigate` callback. Measured: focus goes in, Escape and a link close it, and focus comes back.
- Every step is its own commit, each a working app: the history reads as the lesson's steps.
- `HealthBadge` was moved, not rewritten: the status logic and its comment came across unchanged,
  and the four old tests pass with only the `MemoryRouter` added.

Verdict: fixes needed
