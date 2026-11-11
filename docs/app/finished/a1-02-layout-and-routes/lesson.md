# Lesson: a1-02 · Layout, menu and routes

## What you will build

The app gets its frame. A menu on the left lists Batches, Recipes, Inventory, Devices and Settings;
the area on the right shows the page you picked, and every page has its own URL. On a narrow screen
the menu hides behind a button and slides in as a drawer. Each page is a placeholder with its
title for now; later tickets fill them (a1-07 fills Batches).

It is done when:

- **AC1** Clicking each menu item shows its page and changes the URL.
- **AC2** Opening a URL directly (or reloading) shows the right page.
- **AC3** At phone width (browser dev tools, 375 px) the menu is a drawer and nothing scrolls
  sideways.
- **AC4** Everything works by keyboard: Tab reaches each menu item, Enter opens it.

**How the pieces fit.** `main.tsx` wraps the app in `BrowserRouter`, which watches the address bar.
`App.tsx` stops being a page and becomes the list of routes: which URL shows which component. All
the routes sit inside one *layout route* whose component, `AppLayout`, draws the frame: a header
(menu button, app name, the API status badge), the menu, and an empty slot called `Outlet` where
React Router puts the page that matches the URL. The menu is its own component, `MainMenu`, used
twice: in the left column on wide screens and inside a shadcn `Sheet` (the drawer) on narrow ones.
The health badge and its status logic move out of `App.tsx` into `HealthBadge`, which the header
shows. Each page lives in its feature's folder, `src/features/<feature>/`, where a0-04 put
`useHealth`.

What the tools look like today (measured 2026-11-08 in a scratch copy of your `app/web`, with your
Node 26.13.0, TypeScript 6.0.3 and Vite 8.3; every error message quoted below comes from that run):

| Thing | Version | Note |
|---|---|---|
| `react-router` | 8.5.1 | one package; `react-router-dom` no longer exists in v8 |
| `shadcn` (the CLI) | 4.23.0 | `add sheet` writes `sheet.tsx` and reuses your `button.tsx` |

## Steps

1. **Check where you are.** In `app/web`, run `git branch --show-current` and `git status`.
   *Why:* the work belongs on the ticket's branch, and a clean start keeps the review diff to this
   ticket.
   *Check yourself:* the branch is `a1-02-layout-and-routes`; `git status` lists only
   `docs/app/work/a1-02-layout-and-routes/` changes, if any.

2. **Install React Router.** In `app/web`: `npm install react-router`.
   *Why:* a **client-side router** makes one HTML page behave like many. The browser loads
   `index.html` once; after that, when you click a link, the router changes the address bar itself
   (with the browser's History API) and swaps the component on screen, without asking the server
   for a new page. That is why the app feels instant and why the TanStack Query cache and the open
   drawer survive a click. SYSTEM.md §3 needs a URL per view because tabs (a2-03) and the AI panel
   (F6.3) will open views by URL.
   React Router has three **modes**. You use **declarative mode**: routes are JSX elements
   (`<Route>`) inside your components. *Data mode* adds loaders that fetch data before a page shows;
   you already fetch with TanStack Query, so loaders would be a second way to do the same thing.
   *Framework mode* takes over the build and the project layout, which is more than a menu needs.
   Moving to data mode later is possible without rewriting the pages.
   Docs: [React Router — Picking a Mode](https://reactrouter.com/start/modes) (read "Declarative"
   and "Data", 5 minutes), [Declarative installation](https://reactrouter.com/start/declarative/installation).
   *Watch out:* most tutorials import from `react-router-dom`. That package was removed in v8; v8
   puts everything in `react-router`. Measured with the wrong import:
   *error TS2307: Cannot find module 'react-router-dom' or its corresponding type declarations.*
   *Check yourself:* `package.json` lists `react-router` 8.5.x under `dependencies`.

3. **Move the badge out of `App.tsx`**, so `App.tsx` is free to become the route list in step 5.
   Create `src/features/health/HealthBadge.tsx` with a named export `function HealthBadge()`, no
   props. Move into it everything `App` does today for the badge: the `useHealth()` call, the
   `statusLookup` record, the comment and the `status` line. It returns only the `StatusBadge`
   element; the `<h1>Brewing App</h1>` and the wrapping `<div>` do not come along. Fix the imports
   for the new folder: `useHealth` is now a neighbour (`./useHealth`), and `StatusBadge` is reached
   with the `@/` alias.
   *Why:* the badge is part of the frame, shown on every page, not part of one page. Keeping the
   hook call and the status mapping together in one small component means the layout only places
   `<HealthBadge />` and does not need to know how the status is worked out. This is a **move, not
   a rewrite**: copy the lines as they are, so the review diff shows the same code in a new place.
   *Watch out:* do not delete `App.tsx`'s default export or `App.test.tsx` yet; step 5 rewrites
   `App`, step 12 adapts the test.
   *Check yourself:* `npm run typecheck` passes. `App.tsx` can keep using the old code until step
   5, so nothing breaks yet.

4. **Write the five placeholder pages and the not-found page.**
   - `src/features/batches/BatchesPage.tsx` with `export function BatchesPage()`, returning one
     `<h1>` with the text "Batches". The same for `recipes/RecipesPage.tsx`,
     `inventory/InventoryPage.tsx`, `devices/DevicesPage.tsx` and `settings/SettingsPage.tsx`.
   - `src/components/NotFoundPage.tsx` with `export function NotFoundPage()`: an `<h1>` "Page not
     found" and a link back to Batches. The link is React Router's `Link` component with a `to`
     prop of `'/batches'`.

   *Why:* each page in its feature's folder is where its real content goes later (a1-07 writes
   `BatchesPage`), so the file is created once, in the right place. One component per page, rather
   than one `PlaceholderPage` with a `title` prop, because these files stop being alike as soon as
   the features arrive. The page title is the page's `<h1>`: a page has one `<h1>`, it says where
   you are, and screen readers and tests find the page by it. Give it a size class (for example
   `text-2xl font-semibold`), since Preflight made headings plain (a1-01 step 4).
   `Link` instead of `<a href>`: a plain `<a>` makes the browser load the whole page from the server
   again (the cache and the badge start over); `Link` draws the same `<a>` but lets the router
   handle the click. Not-found is a page of its own, not a redirect to Batches, so a mistyped URL
   tells you it is mistyped.
   Docs: [React Router — Navigating, "Link"](https://reactrouter.com/start/declarative/navigating#link).
   *Check yourself:* `npm run typecheck` passes. Nothing shows them yet; step 5 does.

5. **Turn `App.tsx` into the route list**, in small steps.

   **Read first (about 20 minutes).**
   - [React Router — Routing](https://reactrouter.com/start/declarative/routing): "Configuring
     Routes", "Nested Routes", "Layout Routes", "Index Routes" and "Splats". Look for how a route
     inside another one is written, and which route has no `path`.
   - [React Router — `<Navigate>`](https://reactrouter.com/api/components/Navigate): the `to` and
     `replace` props.

   **5a. The imports.** Replace `App.tsx`'s imports with: `Navigate`, `Route` and `Routes` by name
   from `'react-router'`; the five pages and `NotFoundPage` by name; and `AppLayout` from
   `'./components/layout/AppLayout'` (the file comes in step 6). `useHealth` and `StatusBadge` are
   no longer used here.
   *Check yourself:* the failing check is expected until step 6: typecheck says *error TS2307:
   Cannot find module './components/layout/AppLayout' or its corresponding type declarations.*,
   and the names you have not used yet are reported as unused until 5b to 5f use them.

   **5b. The `Routes` element.** `App` returns a single `<Routes>` element. `Routes` looks at the
   current URL, finds the best-matching `<Route>` among its children and draws that route's
   `element`. Keep `function App()` and `export default App` as they are; `main.tsx` and the test
   import it that way.

   **5c. The layout route.** Inside `Routes`, one `<Route>` with an `element` prop of
   `<AppLayout />` and **no `path`**. Every other route goes between its opening and closing tags.
   *Why:* a route without a path adds no part to the URL; it only says "draw this component around
   the children". That is a *layout route*. It is how the menu stays on screen for every page,
   including not-found, without each page drawing it.

   **5d. The five pages.** Inside the layout route, a `<Route>` per page: `path="batches"` with
   `element={<BatchesPage />}`, and the same for the other four. Write the path without a leading
   `/`: child paths are relative to their parent, and this parent has none.
   *Check yourself:* after step 6, `/recipes` shows "Recipes".

   **5e. The index route.** A `<Route>` with the `index` prop (a prop written alone, which means
   `true`) and an `element` of `<Navigate to="/batches" replace />`.
   *Why:* the *index route* is what its parent shows at the parent's own URL; here that URL is `/`.
   `Navigate` is a component that, when drawn, sends the browser to `to`. F1.1 says `/` opens
   Batches; a redirect rather than drawing `BatchesPage` at `/` too keeps one URL per view, so the
   menu highlight and later the tabs see `/batches`. `replace` swaps the current history entry
   instead of adding one: without it, the Back button from `/batches` returns to `/`, which
   redirects to `/batches` again, and you are stuck.

   **5f. The catch-all route.** Last inside the layout route, a `<Route>` with `path="*"` and
   `element={<NotFoundPage />}`.
   *Why:* `*` (a *splat*) matches any path. React Router ranks routes by how specific they are, not
   by order, so `*` only wins when nothing else matches. Inside the layout route, so the menu is
   still there to get you back.

6. **Write `AppLayout`**, the frame, in `src/components/layout/AppLayout.tsx`, in small steps. The
   menu itself comes in step 7 and the drawer in steps 9 and 10; this step builds the shape.

   **Read first (about 20 minutes).**
   - [React Router — Routing, "Nested Routes"](https://reactrouter.com/start/declarative/routing#nested-routes):
     what `<Outlet />` does.
   - [Tailwind — Responsive design](https://tailwindcss.com/docs/responsive-design): "Overview",
     "Working mobile-first" and the breakpoint table. Look for what `md:` means and why an
     unprefixed class applies at every width.
   - [Tailwind — Flex](https://tailwindcss.com/docs/flex) and
     [`min-width`](https://tailwindcss.com/docs/min-width): `flex-1` and `min-w-0`.

   **6a. The signature.** `export function AppLayout()`, no props, in the new folder
   `src/components/layout/`.
   *Why:* `components/` holds what is shared by every feature; `layout/` groups the frame's pieces
   (`AppLayout`, `MainMenu`) so they are easy to find.

   **6b. The outer shape.** A wrapping `<div>` that is at least the screen's height (`min-h-svh`)
   and stacks its children vertically (`flex flex-col`). Inside it: a `<header>` and, below it,
   a `<div>` that holds the menu column and the page side by side (`flex flex-1`).
   *Why:* `svh` is the *small viewport height*, the height when a phone's address bar is showing,
   so the frame never ends up taller than the visible screen.

   **6c. The header.** A `<header>` with a fixed height and its items in a row, centred vertically
   (`flex h-14 items-center gap-2`), a bottom border, side padding. In it, for now: the app's name
   "Brewing App" as a `<span>` (not an `<h1>`: the page's title is the `<h1>`, step 4), and
   `<HealthBadge />` pushed to the right edge (a wrapper with `ml-auto`, margin-left auto, takes up
   the free space before it).

   **6d. The menu column.** An `<aside>` with a fixed width (`w-56`), `shrink-0` so the page cannot
   squeeze it, a right border and padding. For now, put a placeholder text in it; step 8 puts the
   menu there.

   *Changed 2026-11-08, after you finished 6d:* from here on, every numbered step ends with all
   checks passing and a **Commit:** line, so you can commit step by step. The router (was step 10)
   and the test fix (was step 12) moved into this step as 6f and 6g, because the app cannot pass
   its checks without them; the later steps are renumbered.

   **6e. The page slot.** A `<main>` with `flex-1` (take the remaining width), `min-w-0` and padding,
   and inside it `<Outlet />`, imported by name from `'react-router'`.
   *Why:* `Outlet` is where the layout route draws whichever child route matches the URL (step 5c).
   `<main>` marks the page's main content for screen readers and gives "skip to content" tools a
   target. `min-w-0`: a flex item by default refuses to get narrower than its content, so one wide
   table later would push the page wider than the screen and scroll sideways (AC3). `min-w-0` lets
   it shrink and keeps the overflow inside `<main>`.
   *Watch out:* forget `<Outlet />` and nothing complains: measured, the menu and header draw and
   the page side stays empty on every URL.

   **6f. Give the app a router.** In `main.tsx`, import `BrowserRouter` by name from
   `'react-router'` and wrap `<App />` in it, inside `QueryClientProvider`.
   *Why:* `Routes` and `Outlet` (and `NavLink` in step 7) read the URL from the router above them.
   `BrowserRouter` connects that to the browser's address bar. It goes in `main.tsx`, not in
   `App`, so tests can wrap the same `App` in a different router that keeps the URL in memory
   (6g, and the test lesson). Without it, measured, the page is blank and the console says
   *Uncaught Error: useRoutes() may be used only in the context of a &lt;Router&gt; component.*
   *Check yourself:* `npm run dev`, open the address it prints. `/` turns into `/batches` and shows
   "Batches" next to the column's placeholder text. The failing check is expected until 6g:
   `npm test -- --run` now fails, see there.

   **6g. Keep the existing tests passing.** Run `npm test -- --run`. Measured, the four `App` tests
   fail with *Error: useRoutes() may be used only in the context of a &lt;Router&gt;
   component.*, because `renderApp` draws `App` with no router around it. In `App.test.tsx`,
   import `MemoryRouter` by name from `'react-router'` and wrap `<App />` in it, inside
   `QueryClientProvider`.
   *Why:* a test has no address bar. `MemoryRouter` is a router that keeps its URL in a list in
   memory, so a test can start the app at any path; with no starting path it is at `/`, which
   redirects to `/batches`, and the badge is in the header on every page. The four tests still
   check what they checked before. The new routing tests are the test lesson's work. This belongs
   in the same step as 6f: the change that breaks the tests and the fix go in one commit.
   Docs: [React Router — `MemoryRouter`](https://reactrouter.com/api/declarative-routers/MemoryRouter).
   *Check yourself:* *Tests 7 passed (7)*.

   **6h. Check and commit.** Run `npm run lint`, `npm run typecheck`, `npm test -- --run` and
   `npm run build`.
   *Why:* this is the first point since step 2 where the app works again: routes, layout and
   router are all in place. Everything from steps 2 to 6 that is not committed yet goes in now.
   *Check yourself:* all four pass, and `git status` shows only this ticket's files.

   *Commit:* whichever of these `git status` still lists: `package.json`, `package-lock.json`,
   `src/main.tsx`, `src/App.tsx`, `src/App.test.tsx`, `src/features/health/HealthBadge.tsx`,
   `src/components/layout/AppLayout.tsx` (all under `app/web/`), message
   `Add routes and the app layout`. If the hook refuses the commit, the step is not finished: fix
   what it reports and commit again.

7. **Write `MainMenu`**, in `src/components/layout/MainMenu.tsx`, in small steps.

   **Read first (about 20 minutes).**
   - [react.dev — Rendering Lists](https://react.dev/learn/rendering-lists): "Rendering data from
     arrays" and "Keeping list items in order with `key`". Look for why `key` exists.
   - [MDN — Array.prototype.map()](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/map):
     the first example, if `.map` is new.
   - [React Router — Navigating, "NavLink"](https://reactrouter.com/start/declarative/navigating#navlink):
     the `className` callback.
   - [MDN — Arrow functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Arrow_functions),
     "Function body": an arrow with an expression and no curly braces returns that expression.

   **7a. The menu items.** Above the component, outside it, a `const` named for example `menuItems`:
   an array of five objects, each with a `to` (`'/batches'`, …) and a `label` (`'Batches'`, …), in
   the order of F1.1.
   *Why:* the menu is *data*, and the markup is written once for all of them. Adding a sixth view
   later is one line. Outside the component because it never changes; inside, it would be built
   again on every render for nothing. Write the paths with a leading `/` here: these are absolute
   links, unlike the relative route paths in step 5d.

   **7b. The props type.** A `type MainMenuProps` with one optional field, `onNavigate`, whose type
   is a function with no parameters that returns nothing. An optional field has a `?` after its
   name; a function type is written as the parameter list in brackets, an arrow `=>`, then the
   return type `void`.
   *Why:* the drawer (step 10) needs to know when a link was clicked, so it can close. The column
   (step 8) does not care, so the prop is optional. The menu does not know about drawers; it only
   reports "someone navigated". That is the **callback prop** pattern: a child tells its parent
   something happened by calling a function the parent passed in, and the parent decides what to do.

   **7c. The signature.** `export function MainMenu({ onNavigate }: MainMenuProps)`, the same shape
   as `StatusBadge`'s.

   **7d. The list.** Return a `<nav>` with an `aria-label` of `"Main"`, holding a `<ul>`. Inside the
   `<ul>`, in curly braces, `menuItems.map(…)` with an arrow function that takes one item and
   returns an `<li>` for it. The `<li>` gets a `key` prop of the item's `to`.
   *Why:* `<nav>` tells screen readers "this is navigation", and the label names it, since a page
   can have several. A `<ul>` of `<li>` is how a list of links is marked up, so a screen reader says
   "list, 5 items". The `key` is how React tells the items apart between renders; it must be unique
   among siblings and stay the same for the same item, which the path is. (The array index would
   change if items were reordered.)
   *Watch out:* forget the `key` and lint and typecheck both pass; React reports it in the browser
   console instead. Measured: *Each child in a list should have a unique "key" prop. … Check the
   render method of `MainMenu`.*

   **7e. The link.** Inside each `<li>`, a `NavLink` (imported by name from `'react-router'`) with
   `to` set to the item's `to`, `onClick` set to `onNavigate`, and the item's `label` as its text.
   *Why:* `NavLink` is `Link` (step 4) that also knows whether its `to` is the current URL. It sets
   `aria-current="page"` on the active link by itself (measured), which screen readers announce as
   "current page" and which your tests can look for. Passing `onNavigate` straight to `onClick` is
   fine when it is missing: `onClick={undefined}` means "no handler". Tab reaches each link and
   Enter follows it because `NavLink` draws a real `<a href>` (AC4); do not use a `<div>` or a
   `<button>` with an `onClick` that navigates, which loses both.

   **7f. The highlight.** Give `NavLink` a `className` that is a **function** instead of a string:
   an arrow function that takes an object, picks out its `isActive` field with destructuring (curly
   braces around the name in the parameter list), and returns the class names. Build them with
   `cn` from `'@/lib/utils'` (a1-01 step 8): first the classes every link has (block, padding,
   rounded corners, a hover background), then `isActive && '…'` with the active classes (for
   example `bg-accent font-medium`).
   *Why:* React Router calls the function on every render and passes it the link's state, so the
   class follows the URL with no state of yours. `cn` skips `false`, so `isActive && 'classes'`
   adds them only when active. A colour from the theme (`bg-accent`, a1-01 step 9) works in light
   and dark.
   Docs: the `className` example in the NavLink section above is this shape.
   *Check yourself:* `npm run typecheck` and `npm run lint` pass. If typecheck says *Binding element
   'isActive' implicitly has an 'any' type*, the function is on something that is not a `NavLink`
   (measured with the wrong import from step 2). Nothing changes on screen yet: `MainMenu` is
   exported but not used, which breaks no check (measured: the whole hook passes). Step 8 uses it.

   *Commit:* `src/components/layout/MainMenu.tsx`, message `Add the main menu`.

8. **Put the menu in the column.** In `AppLayout`, replace the `<aside>` placeholder with
   `<MainMenu />`, no props. Then hide the column on narrow screens: `hidden` (display none) plus
   `md:block` (display block from the `md` breakpoint up).
   *Why:* Tailwind is **mobile-first**: a class without a prefix applies at every width, and `md:`
   applies from 768 px (48rem) up. So you write the narrow layout first and add what changes on
   wider screens, which is what F1.5 asks for ("narrow layout first"). The ticket's "below the
   medium breakpoint" is exactly "without `md:`".
   *Check yourself (AC1):* with `npm run dev`, each of the five links shows its page, the URL
   changes, and the clicked link is highlighted. Drag the window narrower than 768 px: the column
   disappears. For now there is no way to the menu at that width; step 10 adds the button. Lint,
   type check and tests pass.

   *Commit:* `src/components/layout/AppLayout.tsx`, message `Show the menu in the left column`.

9. **Add the Sheet component.** In `app/web`: `npx shadcn@latest add sheet`.

   **Read first for steps 9 and 10 (about 15 minutes).**
   - [shadcn — Sheet (Base UI)](https://ui.shadcn.com/docs/components/base/sheet): "Usage" and
     "Side". Look at how `SheetTrigger` uses `render`.
   - [react.dev — State: A Component's Memory](https://react.dev/learn/state-a-components-memory):
     "Adding a state variable" and "Anatomy of `useState`".
   - [Base UI — Dialog](https://base-ui.com/react/components/dialog), the "State" example: the
     `open` and `onOpenChange` props, and why `onOpenChange` is preferred over a `useEffect`.

   *Why:* a drawer is a dialog that slides in from an edge. Getting a dialog right is more work than
   it looks: focus must move into it, Tab must stay inside it, Escape must close it, focus must go
   back to the button afterwards, and the page behind must not scroll. Base UI's `Dialog`, which
   `sheet.tsx` wraps, does all of that; measured in the scratch run: Escape and a link click close
   it, and focus returns to the menu button. Your `.prettierignore` and ESLint override from a1-01
   already cover the new file.
   *Check yourself:* the output says *Created 1 file: src/components/ui/sheet.tsx* and skips
   `button.tsx` (already identical). Nothing uses it yet, and every check still passes (measured).

   *Commit:* `src/components/ui/sheet.tsx`, message `Add the shadcn Sheet component`.

10. **Put the menu in a drawer on narrow screens**, in small steps, all in `AppLayout`.


   **10a. The state.** At the top of `AppLayout`'s body, `useState(false)` from `'react'`, with the
   result destructured into two names, for example `menuOpen` and `setMenuOpen`: square brackets
   around the two names, then `=`, then the call.
   *Why:* **state** is a value a component remembers between renders; changing it with the setter
   makes React draw the component again. The drawer must close after a link click (otherwise,
   measured, the URL changes but the drawer stays open over the new page), and only your code knows
   when a link was clicked. So the drawer is **controlled**: your state holds whether it is open,
   and the drawer only asks for changes. An *uncontrolled* `Sheet` (no `open` prop) keeps that
   value to itself, and you cannot close it from outside.
   *Check yourself:* the failing check is expected until 10b and 10d use them: lint says *'menuOpen'
   is assigned a value but never used* (and the same for `setMenuOpen`), typecheck says *error
   TS6133: 'menuOpen' is declared but its value is never read.*

   **10b. The `Sheet`.** In the header, before the app name, a `<Sheet>` with `open={menuOpen}` and
   `onOpenChange={setMenuOpen}`.
   *Why:* `onOpenChange` is called with `true` or `false` whenever the drawer wants to open or close
   (button, Escape, a click on the dimmed page). The setter takes exactly that one value, so it can
   be passed as it is.

   **10c. The trigger.** Inside the `Sheet`, a `SheetTrigger` whose `render` prop is a shadcn
   `<Button>` with `variant="ghost"`, `size="icon"`, `aria-label="Open menu"` and the class
   `md:hidden`. Between `SheetTrigger`'s tags goes the icon: `<MenuIcon />` from `lucide-react`.
   *Why:* `render` is Base UI's way to say "draw the trigger as this element, with my behaviour
   added" (you met it as `useRender` in a1-01 step 11). The button has only an icon, so the
   `aria-label` is its name for screen readers and for tests (`getByRole('button', { name: 'Open
   menu' })`). `md:hidden` is step 8 the other way round: shown below 768 px, hidden above.
   *Watch out:* putting a `<Button>` *between* `SheetTrigger`'s tags instead of in `render` draws a
   button inside a button. Measured, the browser console says: *In HTML, &lt;button&gt; cannot be a
   descendant of &lt;button&gt;.*
   *Watch out:* `asChild`, which many shadcn examples use, belongs to the Radix version; your
   components are Base UI and use `render`.

   **10d. The drawer's content.** After the trigger, inside the `Sheet`: `<SheetContent>` with
   `side="left"` and some padding, holding a `SheetTitle` ("Brewing App" or "Menu") and
   `<MainMenu />` with an `onNavigate` that sets the state to `false`: an arrow function with no
   parameters that calls `setMenuOpen(false)`.
   *Why:* `side="left"`, because the menu lives on the left on wide screens too. `SheetTitle` gives
   the dialog its accessible name, so a screen reader says what opened. The arrow function is needed
   because `onNavigate` takes no arguments and `setMenuOpen` needs one; writing
   `onNavigate={setMenuOpen(false)}` would *call* it during render instead of passing a function.
   This is the same `MainMenu` as in the column: one component, two containers, so the five links
   are written once.
   *Check yourself:* `npm run typecheck` and `npm run lint` pass. With `npm run dev`, make the
   window narrower than 768 px: the column disappears, the menu button shows, and it opens the
   drawer; a link click changes the page and closes it. Step 12 checks this properly at 375 px.

   *Commit:* `src/components/layout/AppLayout.tsx`, message `Open the menu in a drawer when narrow`.

11. **Check AC2: direct URLs.** With `npm run dev` running, type `/inventory` into the address bar
    and press Enter, then reload on `/settings`, then open `/nope`.
    *Why:* clicking a link never asks the server for the page, but typing a URL or reloading does.
    Vite's dev server answers any path that is not a file with `index.html` (measured: `/recipes`
    answers 200), the router starts, reads the path and draws the right page. Packaged builds will
    need the same rule from whatever serves them (Tauri in M8), which is why this check stays on
    the list.
    *Check yourself:* `/inventory` and `/settings` show their pages with the right item
    highlighted; `/nope` shows "Page not found" with no item highlighted and the menu still there.

    No commit.

12. **Check AC3 at phone width.** With `npm run dev` running, press F12, click the device toolbar
    icon (Ctrl+Shift+M) and choose a width of 375. Open the drawer, click Recipes, then try Escape
    and a click on the dimmed side.
    *Why:* this is the layout a phone gets in M9; checking it now is what makes that milestone a
    pass, not a rewrite (F1.5).
    *Check yourself:* the left column is gone and the menu button shows; the drawer slides in from
    the left; a link click changes the page and closes the drawer. In the console,
    `document.documentElement.scrollWidth` prints `375` (measured), the same as the screen: nothing
    scrolls sideways.

    No commit.

13. **Check AC4 by keyboard.** On a wide window, click the address bar, then press Tab repeatedly:
    focus goes through the five menu links in order, each with a visible ring. Press Enter on one.
    Then at 375 px: Tab to the menu button, Enter opens the drawer, Tab moves through its links, Enter
    opens one.
    *Check yourself:* Enter follows the link; at 375 px the drawer closes and focus is back on the
    menu button (measured). If a link shows no focus ring, give the link classes a
    `focus-visible:` ring (Tailwind's `focus-visible:` prefix applies only when focus came from the
    keyboard).

    *Commit:* only if you added a focus ring: `src/components/layout/MainMenu.tsx`, message
    `Show a focus ring on menu links`. Otherwise no commit.

14. **Prove the generated file is unedited.** `npx shadcn@latest add sheet button badge --diff`.
    *Why:* the a1-01 rule holds for every file in `src/components/ui/`: as the CLI wrote it.
    *Check yourself:* every file says *No changes.*

    No commit.

15. **Run every check and ask for a review** (say "review a1-02").
    *Check yourself:* the list under "Before you ask for a review" is all ticked.

## Files you will touch

- `app/web/package.json`, `app/web/package-lock.json` — `react-router`.
- `app/web/src/main.tsx` — `BrowserRouter` around `App`.
- `app/web/src/App.tsx` — becomes the route list: layout route, index redirect, five pages,
  catch-all.
- `app/web/src/App.test.tsx` — `MemoryRouter` around `App` in `renderApp`, nothing else.
- `app/web/src/features/health/HealthBadge.tsx` — new: the badge and its status logic, moved from
  `App.tsx`.
- `app/web/src/components/layout/AppLayout.tsx` — new: header, drawer, menu column, `<main>` with
  `Outlet`.
- `app/web/src/components/layout/MainMenu.tsx` — new: the five `NavLink`s.
- `app/web/src/components/NotFoundPage.tsx` — new.
- `app/web/src/features/{batches,recipes,inventory,devices,settings}/<Name>Page.tsx` — new, one
  placeholder page each.
- `app/web/src/components/ui/sheet.tsx` — new, written by `shadcn add sheet`, unedited.

## Before you ask for a review

- [ ] AC1: each of the five links shows its page, the URL changes, and the link is highlighted.
- [ ] AC2: typing `/inventory`, reloading on `/settings` and opening `/nope` each show the right
      page; `/` becomes `/batches`, and Back from there does not bounce you to `/`.
- [ ] AC3: at 375 px the column is gone, the drawer opens and closes on a link click, and
      `document.documentElement.scrollWidth` is 375.
- [ ] AC4: Tab reaches each menu link with a visible focus ring, Enter opens it, on both widths.
- [ ] `npm run lint`, `npm run typecheck`, `npm test -- --run`, `npm run build` and
      `npx prettier . --check` pass.
- [ ] `npx shadcn@latest add sheet button badge --diff` says *No changes.* for each.
- [ ] No import from `react-router-dom`; no `<a href>` to an app page.
- [ ] The browser console shows no React warning (the `key` one in particular).
- [ ] Every step is committed: `git status` shows nothing of this ticket left uncommitted, and
      `git log --oneline main..` lists your step commits.
- [ ] Could you add a sixth view by adding one route and one menu item, and nothing else?
