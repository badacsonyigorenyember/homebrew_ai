# Test lesson: a0-03 · Web skeleton

The first frontend tests. You set up three tools (Vitest, React Testing Library, jsdom) and write
three small tests: one per status, each checking that `StatusBadge` shows its label (AC4).

What the tools look like today (measured 2026-11-03 by setting this up in a scratch copy of your
`app/web`, with your TypeScript 6.0.3 and Vite 8; every error message quoted below comes from
that run):

| Package | Version | What it is |
|---|---|---|
| `vitest` | 5.1.0 | the test runner; supports Vite 6, 7 and 8 |
| `jsdom` | 30.1.3 | a fake browser page inside Node |
| `@testing-library/react` | 16.3.3 | draws a component into that page and finds things on it |
| `@testing-library/dom` | 10.4.2 | the part of Testing Library the React package builds on; you install it yourself |
| `@testing-library/jest-dom` | 7.0.1 | extra checks such as `toBeInTheDocument` |

All five installed next to your packages with no conflict.

## What to test

| Behaviour | AC | Level | Why this level |
|---|---|---|---|
| `status="ok"` shows the ok label | AC4 | component | the label is what the user sees; a component test draws the component and reads the page, as a user would |
| `status="down"` shows the down label | AC4 | component | same |
| `status="unknown"` shows the unknown label | AC4 | component | same |

Three tests, one per status. Each one draws the badge with one status and checks that the text
on the page is the label you mean for that status.

**Where the expected labels come from:** what *you* want the screen to say, not a copy of what
the component says now. If you copy the strings from `StatusBadge.tsx`, the test agrees with any
typo in it. (You'll see this happen in step 6.)

## What not to test

- **A status outside the three** (`"broken"`). TypeScript already refuses it (AC3); a test can't
  even be written for it without fighting the type checker.
- **That it is a `<span>`**, or that the labels live in a `Record`. Those are *how* the component
  works. If you change the `Record` to a `switch` tomorrow, the user sees the same thing, so the
  tests should still pass.
- **React itself**: that `render` works, that props arrive. React's own tests cover that.
- **`App`**. It has no behaviour of its own yet: it shows a heading and one badge. A test for it
  would only repeat the `StatusBadge` tests.

## New concepts

**Automated tests.** A test is a small function that runs your code with a known input and checks
the result. It earns its keep later: when you change the component in a1-01 (Tailwind) or a0-04
(real API status), `npm test` tells you in a second whether the labels still come out right,
without opening the browser and clicking through all three statuses again.

**Vitest.** The test runner. It finds files whose names end in `.test.tsx` (or `.test.ts`,
`.spec.tsx`, …), runs every test in them and prints which passed and which failed. It is made by
the Vite team and reads your `vite.config.ts`, so tests understand TypeScript and JSX exactly the
way `npm run dev` does, with no second setup. `vitest` on its own starts *watch mode*: it stays
running and reruns the tests each time you save (press `q` to quit). `vitest --run` runs them
once and exits, which is what the review and ship steps use (`npm test -- --run`; the lone `--`
passes `--run` through npm to Vitest).
Docs: [Vitest — Getting started](https://vitest.dev/guide/).

**Test environment and jsdom.** Tests run in Node, and Node has no web page: no `document`, no
elements. A React component needs one to draw into. *jsdom* builds a fake page in memory, with
`document`, elements and text, but no screen. The Vitest option `environment` set to `'jsdom'`
gives every test file such a page.
Docs: [Vitest — Test environment](https://vitest.dev/guide/environment.html),
[`environment` option](https://vitest.dev/config/environment).

**React Testing Library.** Two things you use from it:
- `render(...)` draws a component into jsdom's page.
- `screen` is the whole page, with *queries* that find things on it the way a user would:
  by the text they read, or by a role such as "button". `screen.getByText('...')` returns the
  element showing that text; if there is none, or more than one, it throws an error, and the
  test fails.

The library's idea is to test what the user sees, not the component's insides, so a test
survives a rewrite that keeps the screen the same. For a plain piece of text like a badge,
`getByText` is the right query.
Docs: [React Testing Library — Introduction](https://testing-library.com/docs/react-testing-library/intro/),
[Guiding principles](https://testing-library.com/docs/guiding-principles),
[Queries → Priority](https://testing-library.com/docs/queries/about#priority) (read `getByText`).

**`expect` and matchers.** `expect(value)` starts a check; the *matcher* after the dot says what
must be true: `expect(x).toBe(3)`. If it isn't true, the test fails with a message showing what
was expected and what was found. Vitest comes with general matchers; `jest-dom` adds matchers for
page elements, such as `toBeInTheDocument()` ("this element is on the page").
Docs: [Vitest — `expect`](https://vitest.dev/api/expect.html),
[jest-dom README → With Vitest](https://github.com/testing-library/jest-dom#with-vitest).

**`describe`, `it` and arrow functions.** A test is written as `it('name', function)`: a name that
states the behaviour, and the function to run. The function is usually written as an *arrow
function*: round brackets for the parameters (empty here), `=>`, then the body in curly braces.
`describe('StatusBadge', ...)` groups tests under one heading in the output; it's optional, but it
makes the output read like a sentence ("StatusBadge › shows the ok label"). `test` is another name
for `it`.
Docs: [Vitest — `test`/`it`](https://vitest.dev/api/test.html),
[`describe`](https://vitest.dev/api/describe.html),
[Arrow functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Arrow_functions)
(MDN).

**Setup file.** A file Vitest runs before every test file (option `setupFiles`). You put two
things in it, once, instead of repeating them in every test file:
1. **The jest-dom matchers.** An import of `@testing-library/jest-dom/vitest` adds them to
   `expect`. It is a *side-effect import*: `import` and the module name in quotes, nothing
   imported by name, because the point is the code that runs when it loads.
2. **Cleanup.** `render` adds the component to the page, and nothing takes it away when the test
   ends. Testing Library has `cleanup()` for that, and calls it on its own *only* when the runner
   provides `afterEach` as a global. Vitest doesn't, unless you switch on its `globals` option.
   Without cleanup, the second test still sees what the first one drew. (Measured: two tests that
   each render the ok badge make the second fail with *Found multiple elements with the text: API
   ok*.) So the setup file registers `cleanup` to run after each test: `afterEach` with an arrow
   function that calls `cleanup()`.

This lesson uses explicit imports (`import { it, expect } from 'vitest'` in each file) rather
than Vitest's `globals` option, so every file says where its names come from (readable over
clever, SYSTEM.md C7).
Docs: [`setupFiles`](https://vitest.dev/config/setupfiles),
[`afterEach`](https://vitest.dev/api/hooks.html#aftereach),
[RTL `cleanup`](https://testing-library.com/docs/react-testing-library/api#cleanup),
[side-effect imports](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/import#import_a_module_for_its_side_effects_only)
(MDN).

**Tests are code the type checker reads too.** `tsconfig.app.json` checks everything in `src/`,
so test files and the setup file are type-checked by `npm run typecheck`. That is also how
`toBeInTheDocument` gets its type: TypeScript learns about it from the jest-dom import in the
setup file, *because* that file is in `src/`. The test files are not part of the app: `vite build`
only bundles what `main.tsx` imports, so tests never reach `dist/`.

## Patterns

- **Arrange, act, assert.** Each test has three parts, in this order: set up (here: `render` the
  badge with one status), do the thing (here: nothing; the badge has no button), check (one
  `expect`). Leave a blank line between the parts. *Usual mistake:* checks scattered between
  several renders in one test.
- **One behaviour per test.** One status per test, three tests. When one fails, its name tells
  you which status broke. *Usual mistake:* one test with three renders and three `expect`s: the
  first failure hides the other two.
- **Names that state the behaviour.** `it('shows "API down" when the status is down', ...)`, not
  `it('test 2', ...)` or `it('works', ...)`. The failing test's name is the bug report.
- **Test data small and visible.** The status and the expected label are written right in the
  test, as plain strings. No loops building names, no shared variables at the top: a reader sees
  input and expected output in three lines. (Vitest's `it.each` can run one test body over a
  table of cases; for three cases, three plain tests are easier to read. Keep `it.each` for later
  tickets with many cases: [`test.each`](https://vitest.dev/api/test.html#test-each).)
- **Query like a user.** `screen.getByText` with the label, not looking up a CSS class or
  counting `<span>`s.
- **The test file sits next to what it tests.** `src/components/StatusBadge.test.tsx` beside
  `StatusBadge.tsx`. *Why:* you see at a glance which components have tests, and an import of
  `./StatusBadge` is all it needs.
- **See it fail before you trust it.** A test that has never failed may be checking nothing (as
  the typecheck script was in review round 1). Every step below makes the test fail once.

## Steps

**Read first (about 40 minutes, in this order).** Each item is the background for a step below.
- [Vitest — Getting started](https://vitest.dev/guide/): *Writing tests* and *Configuring
  Vitest*. Look for: the test file name pattern, and that the config can live in `vite.config.ts`.
- [React Testing Library — Example](https://testing-library.com/docs/react-testing-library/example-intro/):
  read the example and find the three parts (render, query, `expect`). It tests a button click, so
  it has an *act* part that yours doesn't.
- [Queries → Priority](https://testing-library.com/docs/queries/about#priority): why `getByText`
  fits a badge.
- [Arrow functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Arrow_functions)
  (MDN), the first examples only: `() => { ... }`.
- [jest-dom README → With Vitest](https://github.com/testing-library/jest-dom#with-vitest): the
  setup file and the `setupFiles` option.

**1. Install the test packages.** In `app/web`:
`npm install --save-dev vitest jsdom @testing-library/react @testing-library/dom @testing-library/jest-dom`.
*Check yourself:* no `ERESOLVE`; `package.json`'s `devDependencies` lists the five packages;
`npx vitest --version` prints `vitest/5.1.0` or newer.

**2. Tell Vitest about the page.** In `vite.config.ts`:
- **2a.** The `test` key you're about to add isn't part of Vite's own config type, so TypeScript
  would reject it. Vitest's docs give a *triple-slash directive* for that: one line at the very top
  of the file, before the imports: three slashes, then a `reference` tag whose `types` attribute
  is `vitest/config` (copy the exact line from
  [Vitest — Configuring Vitest](https://vitest.dev/config/), the `vite.config` example with
  `/// <reference ...`). It tells TypeScript to load Vitest's additions to Vite's config type.
- **2b.** Next to `plugins` in the object passed to `defineConfig`, add a `test` key whose value
  is an object with one option for now: `environment`, the string `'jsdom'`.

*Check yourself:* `npm run typecheck` passes (it checks `vite.config.ts` through
`tsconfig.node.json`). `npx vitest --run` prints *No test files found, exiting with code 1*:
Vitest runs and found nothing to test, which is right for now.

**3. The `test` script.** In `package.json`'s `scripts`, a `test` entry that runs `vitest`.
*Check yourself:* `npm test -- --run` prints the same *No test files found*.

**4. The setup file.**
- **4a.** Create `src/test/setup.ts` (`.ts`: no JSX in it). First line: the side-effect import of
  `@testing-library/jest-dom/vitest`.
- **4b.** Below it, import `cleanup` by name from `@testing-library/react` and `afterEach` by name
  from `vitest` (curly braces with the name, `from`, the package name in quotes, as you did for
  `StatusBadge` in `App.tsx`).
- **4c.** Call `afterEach` with one argument: an arrow function with no parameters whose body calls
  `cleanup()`.
- **4d.** In `vite.config.ts`, in the `test` object, add `setupFiles`: an *array* (square
  brackets) holding one string, the path of the setup file relative to `vite.config.ts`, starting
  with `./src/`.

*Check yourself:* `npm run typecheck` and `npm run lint` pass. `npm test -- --run` still says *No
test files found* (the setup file is not a test file, so that's still right).

**5. The first test, for `ok`.** Create `src/components/StatusBadge.test.tsx` (`.tsx`: the test
writes `<StatusBadge ... />`).
- **5a. Imports.** Three lines: `render` and `screen` from `@testing-library/react`; `describe`,
  `it` and `expect` from `vitest`; `StatusBadge` from `./StatusBadge`.
- **5b. The group.** `describe` with the name `'StatusBadge'` and an arrow function; the tests go
  inside its body.
- **5c. The test.** Inside it, `it` with a name stating the behaviour (for example *shows "API ok"
  when the status is ok*) and an arrow function.
- **5d. Arrange.** In that function's body, call `render` with the badge written as JSX, exactly as
  in `App.tsx`, with `status` set to `"ok"`.
- **5e. Assert.** After a blank line: `expect`, with `screen.getByText` and the label you want as
  its argument, then `.toBeInTheDocument()`.
- **5f. See it fail.** Change the ok label in `StatusBadge.tsx` for a moment (add a letter).
  *Check yourself:* `npm test -- --run` fails with *Unable to find an element with the text: API
  ok* (your label in place of "API ok"), and below it prints the page as jsdom has it, showing the
  wrong label. Undo the change: the test passes, *Tests 1 passed (1)*.

**6. The tests for `down` and `unknown`.** Two more `it` blocks inside the same `describe`, each
with its own name, its own `render` with one status and its own `expect` with the label you want
for that status, written from what the screen should say (see "Where the expected labels come
from").
*Check yourself:* `npm test -- --run`. If your `down` label in the component still reads "API
downm", the `down` test fails with *Unable to find an element with the text: API down*, and the
printed page shows `API downm`: that is review finding #4, found by a test. Fix the typo in the
component, not the test, and run again: *Tests 3 passed (3)*.

**7. Break it on purpose.** In `StatusBadge.tsx`, swap two labels (give `ok` the down label and
`down` the ok label).
*Check yourself:* two tests fail and their names tell you which statuses are wrong; the third
passes. Undo the swap; all three pass.

**8. See why the setup file matters.** Comment out the `afterEach` call in `src/test/setup.ts`
(two slashes at the start of each of its lines).
*Check yourself:* the tests may still pass, because each test looks for a *different* label. Now
copy your ok test once more (same `render`, same `expect`) and run: the copy fails with *Found
multiple elements with the text: API ok*, because the first test's badge is still on the page.
Delete the copy and uncomment the `afterEach`: three tests pass.

**9. Run every check.** `npm run lint`, `npm run typecheck`, `npm test -- --run`, `npm run build`,
`npm run format`.
*Check yourself:* all pass, `format` changes nothing (or you commit what it changed), and
`dist/assets/` has no test code in it (the JavaScript file is about the same size as before).

**10. README.** In `app/README.md` "Run the web app", one table row for `npm test` (watch mode,
`q` to quit) and how to run the tests once (`npm test -- --run`).

## Before you ask for a test review

- [ ] Three tests, one per status, each with a name that states the behaviour.
- [ ] Each test has the shape: `render` one badge, one `expect` with `getByText`.
- [ ] The expected labels are the labels you mean, written in the test, not pasted from the
  component.
- [ ] You saw each test fail once (step 5f, 6 or 7) and pass after.
- [ ] `src/test/setup.ts` has the jest-dom import and the `afterEach` cleanup; `vite.config.ts`
  has `environment` and `setupFiles`.
- [ ] `npm run lint`, `npm run typecheck`, `npm test -- --run` and `npm run build` pass.
- [ ] `app/README.md` mentions `npm test`.
- [ ] If you change `StatusBadge`'s `Record` to a `switch` and keep the same labels, would every test
  still pass? (It should.)

Then say "review the tests".
