# Test lesson: a1-02 · Layout, menu and routes

## What you will test

Four behaviours, all at the **component** level: `App` drawn in jsdom inside a `MemoryRouter`, the
same way `renderApp` already draws it for the health tests. That level, because routing is not in
one component: it is `App`'s route list, `AppLayout`'s `Outlet` and `MainMenu`'s links working
together. Drawing `App` whole tests what you see on the screen; drawing `MainMenu` alone would only
test that React Router's `NavLink` works.

| # | Behaviour | AC |
|---|---|---|
| T1 | `/` shows the Batches page | AC2 (and F1.1: `/` opens Batches) |
| T2 | opening `/inventory` directly shows the Inventory page | AC2 |
| T3 | clicking Recipes in the menu shows the Recipes page and marks Recipes as the current link | AC1 |
| T4 | an unknown path shows "Page not found" | ticket "What to build" |

What not to test, and why:

- **Every route.** All five pages are reached the same way; one direct URL (T2) and one click (T3)
  cover the mechanism. Five near-copies would fail together and tell you nothing more.
- **The highlight's colour or class names.** A class is how it looks, not what it means. T3 checks
  `aria-current="page"`, which is what a screen reader announces and what `NavLink` sets on the
  current link; the colour you checked by eye.
- **The drawer and the 375 px layout (AC3).** jsdom has no layout and does not load your CSS, so
  `hidden md:block` changes nothing there: the column is "visible" at any width. AC3 stays a check
  in the browser, as you did in the lesson.
- **Focus, Escape and Tab (AC4).** The drawer's focus handling is Base UI's, tested by Base UI; the
  links are plain `<a>` elements. You checked these by hand.
- **The four health tests.** They keep working unchanged.

## Steps

Every step ends with all checks passing and a **Commit** line, like the lesson.

1. **Check where you are, and close review #7.** `git branch --show-current` says
   `a1-02-layout-and-routes`; `git status` is clean. Then change `SettingsPage`'s `<div>` to an
   `<h1>` (both tags; the classes stay).
   *Why:* every test below finds a page by its heading. Settings is not tested here, but a page
   whose title is not a heading cannot be found that way. Measured, with the `<div>`:
   *TestingLibraryElementError: Unable to find an accessible element with the role "heading" and
   name "Settings"*.
   *Check yourself:* on `/settings`, `document.querySelectorAll('main h1').length` in the browser
   console prints `1`.

   *Commit:* `app/web/src/features/settings/SettingsPage.tsx`, message
   `Make the Settings title a heading`.

2. **Install user-event.** In `app/web`: `npm install --save-dev @testing-library/user-event`.
   *Why:* T3 clicks a link. **user-event** simulates what a real user does: a click is a pointer
   moving in, pressing, releasing, focus moving, then the click, in the order a browser fires them.
   Testing Library's older `fireEvent` sends only the one `click` event, which is not what a person
   causes. It is a dev dependency (`--save-dev`), because only the tests use it, never the app.
   Docs: [user-event — Introduction](https://testing-library.com/docs/user-event/intro) (5
   minutes; read "Differences from fireEvent").
   *Check yourself:* `package.json` lists `@testing-library/user-event` 14.6.x under
   `devDependencies`. Nothing uses it yet, and every check still passes (measured).

   *Commit:* `app/web/package.json`, `app/web/package-lock.json`, message `Add user-event`.

3. **Let `renderApp` start at any path**, in `src/App.test.tsx`, in two sub-steps.

   **Read first (about 10 minutes).**
   - [MDN — Default parameters](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Default_parameters):
     the first example.
   - [React Router — `MemoryRouter`](https://reactrouter.com/api/declarative-routers/MemoryRouter):
     the `initialEntries` prop.

   **3a. The parameter.** Give `renderApp` one parameter, `path`, with a default value of `'/'`:
   the name, `=`, then the value, inside the brackets.
   *Why:* T2 and T4 start somewhere else than `/`; T1 and the four health tests start at `/`. A
   default means the existing calls `renderApp()` stay as they are. TypeScript works out that
   `path` is a string from the default, so it needs no type written.
   *Check yourself:* the failing check is expected until 3b uses it: typecheck says *error TS6133:
   'path' is declared but its value is never read.*, lint *'path' is assigned a value but never
   used* (both measured).

   **3b. The starting URL.** Give `MemoryRouter` the prop `initialEntries`: an array with one
   item, `path`, in square brackets inside the curly braces.
   *Why:* `MemoryRouter` keeps a history list in memory instead of the address bar (lesson step
   6g). `initialEntries` is that list at the start; the last entry is where the app opens. One
   entry is "the user typed this URL", which is exactly AC2.
   *Check yourself:* `npm test -- --run` still says *Tests 7 passed (7)*.

   *Commit:* `app/web/src/App.test.tsx`, message `Let renderApp start at a given path`.

4. **T1: `/` shows the Batches page.** A new `describe('routes', …)` block below the existing
   one in `App.test.tsx`, with the first `it` inside.

   **Read first (about 10 minutes).**
   - [Testing Library — `ByRole`](https://testing-library.com/docs/queries/byrole): the first
     paragraph and the `name` option.
   - [Queries → Priority](https://testing-library.com/docs/queries/about#priority) again (you read
     it in a0-03): `getByRole` is first in the list.

   **4a. The group.** `describe('routes', …)` with an arrow function, the same shape as
   `describe('App', …)` (a0-03 test lesson). It sits next to the health tests because both test
   `App`; the name says which behaviour the group covers.

   **4b. The test's name.** An `it` whose name states the behaviour, for example `'opens Batches at
   /'`. A name that says what the user gets, not how the code does it, reads as a list of what the
   app does when the tests run.

   **4c. Arrange.** `renderApp()` with no argument: the default `'/'` from 3a.

   **4d. Assert.** `expect(screen.getByRole('heading', { name: 'Batches' })).toBeInTheDocument()`.
   The first argument is the **role**, what the element *is* to a screen reader (`heading`, `link`,
   `button`); the second is an object whose `name` is its accessible name, here the heading's text.
   *Why `getByRole`, not `getByText('Batches')`:* the word "Batches" is on the page twice, the
   heading and the menu link, and `getByText` fails (measured: *TestingLibraryElementError: Found
   multiple elements with the text: Batches*). The role
   says which one you mean, and it is how a person using a screen reader finds the title. It also
   checks that the title *is* a heading, which is why step 1 mattered.
   *Why `getBy` and no `await`:* the redirect from `/` happens inside `render`, so the page is
   already there when `render` returns (measured: `getByRole` passes). `findBy` with `await` is for
   what arrives later, like the API answer in a0-04.
   *There is no act part:* the "act" is opening the URL, which `renderApp` does. That is fine; a
   test has arrange, act and assert only where it needs them.

   **4e. See it fail.** The page already works, so the test passed the first time. A test you
   have never seen fail may check nothing. Delete the `index` route line in `App.tsx` for a
   moment and run the test. Measured: *TestingLibraryElementError: Unable to find role="heading"
   and name "Batches"*. Put the line back.
   *Check yourself:* `npm test -- --run` says *Tests 8 passed (8)*.

   *Commit:* `app/web/src/App.test.tsx`, message `Test that / opens Batches`.

5. **T2: a page opens directly from its URL.** A second `it` in `describe('routes', …)`, for
   example `'opens a page directly from its URL'`. Arrange: `renderApp('/inventory')`. Assert:
   the heading named Inventory, as in 4d.
   *Why Inventory:* any page but Batches. Batches is where `/` goes, so a test on Batches would
   pass even if the starting path were ignored.
   *See it fail:* remove `initialEntries` from `MemoryRouter` for a moment (the app then starts
   at `/`). Measured: *Unable to find an accessible element with the role "heading" and name
   "Inventory"*, and typecheck and lint complain about the unused `path` again. Put it back.
   *Check yourself:* *Tests 9 passed (9)*.

   *Commit:* `app/web/src/App.test.tsx`, message `Test opening a page by its URL`.

6. **T3: a menu link shows its page and is marked current.** A third `it`, in small steps.

   **Read first (about 10 minutes).**
   - [user-event — Writing tests with userEvent](https://testing-library.com/docs/user-event/intro#writing-tests-with-userevent):
     `setup()`, then `await` each action.
   - [jest-dom — `toHaveAttribute`](https://github.com/testing-library/jest-dom#tohaveattribute).

   **6a. The name and `async`.** For example `'shows the page of a clicked menu link and marks the
   link current'`. Mark the arrow function `async` (a0-04 test lesson), because 6c waits for the
   click.

   **6b. Arrange.** First `userEvent.setup()`, imported by name (`userEvent`, in curly braces)
   from `'@testing-library/user-event'`, kept in a `const`, for example `user`. Then
   `renderApp('/batches')`.
   *Why `setup()` first:* it prepares the simulated user (keyboard and pointer state) for this
   test; the docs call it before rendering. Start on Batches, so the click really goes somewhere
   else.

   **6c. Act.** `await user.click(…)` with `screen.getByRole('link', { name: 'Recipes' })`.
   *Why `await`:* a user-event action is a sequence of events and returns a promise; the page has
   changed only once it is done.
   *Watch out:* without the `await`, lint and typecheck say nothing, and the test fails because it
   looks before the click happened. Measured: *Unable to find an accessible element with the role
   "heading" and name "Recipes"*.

   **6d. Assert, twice.** After a blank line: the heading named Recipes is in the document (as
   4d). Then, the same link, found again with `getByRole('link', { name: 'Recipes' })`, has the
   attribute `aria-current` with the value `'page'`: `toHaveAttribute` takes the attribute's name
   and the expected value.
   *Why two asserts in one test:* both describe the one thing a click does (AC1: the page changes
   and the menu shows where you are). The rule "one behaviour per test" is about behaviours, not
   about `expect` lines.
   *Why `aria-current` and not the `bg-accent` class:* see "What not to test".

   **6e. See it fail, both asserts.** First change `NavLink` to `Link` in `MainMenu.tsx` (all of
   them; `Link` does not know which link is current). Measured: the heading still passes, the
   second assert fails with *expect(element).toHaveAttribute("aria-current", "page") … Expected
   the element to have attribute*. Undo. Then change Recipes' `to` to `'/recipe'` for a moment.
   Measured: *Unable to find an accessible element with the role "heading" and name "Recipes"*
   (the click lands on "Page not found"). Undo.
   *Check yourself:* *Tests 10 passed (10)*.

   *Commit:* `app/web/src/App.test.tsx`, message `Test that a menu link opens its page`.

7. **T4: an unknown path shows "Page not found".** A fourth `it`, for example `'shows "Page not
   found" for an unknown path'`. Arrange: `renderApp('/nope')`. Assert: the heading named
   `Page not found`.
   *See it fail:* delete the `path={'*'}` route in `App.tsx` for a moment. Measured: the test
   fails with *Unable to find an accessible element with the role "heading" and name "Page not
   found"*, and React Router warns in the output *No routes matched location "/nope"*: without a
   catch-all, an unknown URL draws nothing at all. Put it back.
   *Check yourself:* *Tests 11 passed (11)*.

   *Commit:* `app/web/src/App.test.tsx`, message `Test the not-found page`.

8. **Run everything and ask for a test review** (say "review the tests").
   *Check yourself:* the list below is all ticked.

   No commit.

## Before you ask for a test review

- [ ] `npm run lint`, `npm run typecheck`, `npm test -- --run` (*Tests 11 passed (11)*),
      `npm run build` and `npx prettier . --check` pass.
- [ ] You saw each of T1–T4 fail once (4e, 5, 6e, 7) and put the code back each time:
      `git status` shows no change to `App.tsx` or `MainMenu.tsx`.
- [ ] Every test finds things by role and name; none by class name or by `getByText` on a word
      the menu also shows.
- [ ] Each test's name says what the user gets, and reads well after "routes" in the output.
- [ ] `@testing-library/user-event` is under `devDependencies`, not `dependencies`.
- [ ] Every step is committed; `git log --oneline main..` lists them.
