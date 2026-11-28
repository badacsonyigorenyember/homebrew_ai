# Test lesson: a1-07 · Batches page and new batch

## What you will test

Four behaviours, the four the ticket's `## Tests` asks for, all at the **component** level: `App`
drawn in jsdom inside a `MemoryRouter`, with **MSW** answering the API calls, the way
`src/App.test.tsx` already tests the health badge and the routes. That level, because each
behaviour crosses components. The list is `BatchesPage`, `BatchList` and `api.ts` together. A
create goes through the dialog, the form, the POST, the router and `BatchPage`. Drawing `App`
whole tests what you see; drawing `NewBatchForm` alone could not show that the app navigates.

| # | Behaviour | AC |
|---|---|---|
| T1 | the batches from the API show in the list, with their number, name, style, brew date and status label | AC2, ticket "What to build" |
| T2 | with no batches, the page says "No batches yet" and shows the New Batch button | AC1 |
| T3 | picking a recipe and a brew date and pressing Create batch sends the right request and opens the new batch's page | AC2 |
| T4 | a 400 from the API shows its message under the field it is about, and marks that field invalid | AC3 |

What not to test, and why:

- **The phone layout (AC4).** jsdom has no layout and does not load your CSS. `hidden md:table`
  and `md:hidden` change nothing there, so the table **and** the cards are both on the page in
  every test. T1 copes with that (step 3); AC4 stays a browser check, as in the review.
- **The recipe option's text.** It ends in `toLocaleDateString()`, which follows the machine's
  language: *11/4/2026* here, *04/11/2026* on a British machine. A test of the exact text would
  pass on yours and fail elsewhere. T3 picks the recipe by its `value` (the id) instead.
- **The messages of an empty form** (*Choose a recipe* and the others). They come from your Zod
  schema, which you checked by hand in the lesson. The ticket's list does not ask for them, and T4
  already proves that an error reaches its field.
- **The name following the recipe** as its own test: T3 covers it on the way. T3 never types a
  name, so the name it sends, *Weissbier*, can only have come from the recipe.
- **Loading and error text.** Plain placeholders; a2-06 replaces them with the shared states.
- **The eleven existing tests.** They keep working, unchanged apart from step 2's move.

## Steps

Every step ends with all checks passing and a **Commit** line. Paths are from `app/web`.

1. **Give the batch list a default answer in the fake API.**

   **Do:** in `src/test/server.ts`, add a second handler to `setupServer(…)`, after the health
   one and in the same shape: `http.get` for `'/api/batches'`, whose function returns
   `HttpResponse.json([])`, an empty array.

   **Why:** `/` opens the Batches page, and since this ticket that page asks for
   `GET /api/batches`. Every routing test in `App.test.tsx` draws it, and nothing answers. The
   tests still pass today, but only because they finish before the page notices. Measured, a test
   that waits for the page: MSW prints *[MSW] Error: intercepted a request without a matching
   request handler: • GET /api/batches*, and the page shows *The page could not be loaded: fetch
   failed*. `setup.ts` asks for exactly that error (`onUnhandledFrame: 'error'`), so a request
   nobody planned for is loud. An empty list is the honest default: "the API is up and you have no
   batches". A test that needs batches replaces it for itself with `server.use(…)`, as your
   `'shows "API down" when the API is stopped'` test in `App.test.tsx` does for the health check.
   T2 relies on this default.

   **Check yourself:** `npm test -- --run` says *Tests 11 passed (11)*.

   **Commit:** `src/test/server.ts`, message `Answer the batch list in the fake API`.

2. **Move `renderApp` out of `App.test.tsx`, so the batch tests can use it.**

   **Do:**
   - Create `src/test/renderApp.tsx`. Its imports, by name unless said otherwise: `QueryClient`
     and `QueryClientProvider` from `'@tanstack/react-query'`; `render` from
     `'@testing-library/react'`; `MemoryRouter` from `'react-router'`; and `App`, the **default**
     import (no curly braces), from `'@/App'`.
   - Move the whole `renderApp` function from `App.test.tsx` into it, unchanged, with `export` in
     front of `function`.
   - In `App.test.tsx`: delete the function and the imports only it used (`QueryClient`,
     `QueryClientProvider`, `render`, `App`, `MemoryRouter`). Keep `screen` from the
     `'@testing-library/react'` line. Add `renderApp` by name from `'./test/renderApp'`.

   **Why:** the batch tests in step 3 draw the whole app exactly as the routing tests do. A
   second copy of the function would drift from the first: the next change (a provider, a
   default option) would land in one copy only. `src/test/` already holds the shared test setup
   (`server.ts`, `setup.ts`). The file ends in `.tsx` because the function contains JSX.
   Create, switch, delete in one step: the app is never in a state where the helper exists twice
   or not at all.

   **Watch out:** a leftover import. Lint names each one (*'MemoryRouter' is defined but never
   used*); delete what it lists.

   **Check yourself:** `npm run lint` and `npm run typecheck` pass (measured, including the
   React Refresh rule, which does not mind this file), and `npm test -- --run` still says
   *Tests 11 passed (11)*.

   **Commit:** `src/test/renderApp.tsx`, `src/App.test.tsx`, message
   `Share renderApp between test files`.

3. **T1: the list shows the batches.** A new file, `src/features/batches/batches.test.tsx`, in
   small steps. A test file sits next to the code it tests, in its feature folder, like
   `src/components/StatusBadge.test.tsx` next to `StatusBadge.tsx`.

   **Read first (about 10 minutes).**
   - [Testing Library — `ByRole`](https://testing-library.com/docs/queries/byrole), the `name`
     option: for a table row, the name is the text of its cells, joined by spaces.
   - [MSW — `server.use`](https://mswjs.io/docs/api/setup-server/use): a handler added for one
     test goes **in front of** the defaults, and `resetHandlers` in `setup.ts` removes it after
     the test.

   **3a. The test batch.**

   **Do:** a `const firstBatch` with the type `BatchSummary` (a type import) and these values:
   `id: 7`, `number: 1`, `name: 'First brew'`, `styleCode: '10A'`, `styleName: 'Weissbier'`,
   `brewDate: '2026-11-28'`, `status: 'brew_day'`.

   **Why:** this is **test data**, kept small and visible at the top of the file, so the reader
   sees what the API "returned" without looking anywhere else. The type makes TypeScript check it
   against what `api.ts` expects from the real API: a missing field or a misspelt status is a
   type error, not a silent mismatch. Each value is chosen so a mistake shows. `id` 7 and
   `number` 1 differ, so mixing them up is visible. `status` is `brew_day`, the one value whose
   label (*Brew day*) is not just the value with a capital letter, so a missing `statusLabels`
   lookup is caught.

   **Check yourself:** lint reports `firstBatch` as unused, and `npm test` says *No test suite
   found in file* (measured). Both are expected until 3c and 3b.

   **3b. The group and the test.**

   **Do:** `describe('batches', …)` with an arrow function, and inside it an `it` with an `async`
   arrow function, named for example `'lists the batches'`. Import `describe` and `it`.

   **Why:** the same shape as `describe('routes', …)` in `App.test.tsx`. It is `async` because the
   list arrives after the fake API answers, and the test has to wait for it (3d).

   **3c. Arrange.**

   **Do:** two lines.
   - `server.use(…)` with one handler: `http.get('/api/batches', …)` returning
     `HttpResponse.json(…)` of an array holding `firstBatch`. Import `server`, and `http` and
     `HttpResponse` from `'msw/http'` (the `msw` package offers them in more than one place;
     `server.ts` and `App.test.tsx` use this one).
   - `renderApp('/batches')`. Import `renderApp`.

   **Why:** for this one test, the API has one batch. Starting at `/batches` rather than `/` says
   which page the test is about, without relying on the redirect.

   **3d. Assert.**

   **Do:** `expect(await screen.findByRole('row', { name: '1 First brew 10A Weissbier 2026-11-28
   Brew day' })).toBeInTheDocument()`. Import `expect`, and `screen` from
   `'@testing-library/react'` (not `'@testing-library/dom'`, which offers it too).

   **Why:** `findByRole` waits (up to a second) for the element, because the list only appears
   once the fake API has answered. One row holds every column the ticket asks for, so one assert
   checks them all and that they belong to the same batch. A row is found by role and its whole
   text. Its name puts a space between cells, so the style cell (`10A Weissbier`, from
   `styleText`) reads into the name naturally. A row only exists in the table, not in the cards.

   **Watch out:** `findByText('First brew')`. Measured: *TestingLibraryElementError: Found
   multiple elements with the text: First brew*. In jsdom both the table's link and the card's
   link are on the page ("What not to test"), so the name alone is ambiguous.

   **3e. See it fail.**

   **Do:** in `BatchList.tsx`, show `batch.status` instead of `statusLabels[batch.status]` in the
   table's status cell for a moment, and run the test. Then undo it.

   **Why:** a test you have never seen fail may check nothing. Measured: *TestingLibraryElementError:
   Unable to find role="row" and name "1 First brew 10A Weissbier 2026-11-28 Brew day"*. The row
   now ends in *brew_day*.

   **Check yourself:** after the undo, `git diff src/features/batches/BatchList.tsx` shows nothing.
   `npm test -- --run` says *Tests 12 passed (12)*; lint and typecheck pass.

   **Commit:** `src/features/batches/batches.test.tsx`, message `Test the batch list`.

4. **T2: no batches shows "No batches yet" and the button.**

   **Do:** a second `it` in `describe('batches', …)`, `async`, for example
   `'shows "No batches yet" and the New batch button when there are none'`.
   - Arrange: `renderApp('/batches')`, and **no** `server.use`: the default from step 1 answers
     `[]`.
   - Assert, twice: `await screen.findByText('No batches yet')` is in the document; then
     `screen.getByRole('button', { name: 'New Batch' })` is in the document (your button's text,
     with its capital B).

   **Why:** AC1 has two parts, the sentence and the button, and both are what the user sees in
   that one state, so one test holds both asserts. The first needs `findBy` and `await`: the
   sentence appears after the answer. The second can be `getBy` without `await`, because by then
   the page is drawn, and the button is in the header row anyway, outside the loading branches.

   **Watch out:** `getByText('No batches yet')` without waiting. Measured: *Unable to find an
   element with the text: No batches yet.* The test looked while the page still said *Loading
   batches…*.

   **See it fail:** change `batches.data.length === 0` to `=== 1` in `BatchesPage.tsx` for a
   moment. Measured: *Unable to find an element with the text: No batches yet.* Undo it.

   **Check yourself:** *Tests 13 passed (13)*.

   **Commit:** `src/features/batches/batches.test.tsx`, message `Test the empty batch list`.

5. **T3: a create sends the right request and opens the batch's page.** The longest test, in
   small steps.

   **Read first (about 15 minutes).**
   - [user-event — `selectOptions`](https://testing-library.com/docs/user-event/utility#selectoptions-deselectoptions)
     and [`type`](https://testing-library.com/docs/user-event/convenience#type).
   - [MSW — Request body](https://mswjs.io/docs/http/intercepting-requests/body): `await
     request.json()` inside a handler.
   - [Vitest — `toEqual`](https://vitest.dev/api/expect.html#toequal).

   **5a. A test recipe.**

   **Do:** below `firstBatch`, a `const weissbier` of type `BrewableRecipe` (a type import):
   `id: 1489`, `styleCode: '10A'`, `styleName: 'Weissbier'`, `og: 1.0481`, `fg: 1.0099`,
   `abv: 4.9`, `ibu: 11.8`, `batchL: 10`, `createdAt: '2026-11-04T09:18:21Z'`.

   **Why:** the form needs at least one recipe to pick. These are the values of your real
   recipe 1489 (measured from `GET /api/recipes/brewable`), so the test looks like the app does.

   **Check yourself:** lint reports `weissbier` as unused until 5c; that is expected.

   **5b. The test and its two variables.**

   **Do:** a third `it`, `async`, for example `'creates a batch and opens its page'`. Its first
   two lines: `let batches` of type `BatchSummary[]`, starting as an empty array; and `let sent`
   of type `unknown`, with no value.

   **Why:** the fake API needs a memory. Before the create the list is empty; after it, the list
   has the new batch, because `BatchPage` finds the batch's name in the list. `sent` keeps what
   the form posted, so the test can check it after the click. `unknown` is TypeScript's "anything,
   and you must check before using it", the honest type for a body that came over the wire.

   **5c. The fake API for this test.**

   **Do:** `server.use(…)` with three handlers:
   - `http.get('/api/recipes/brewable', …)` returning `HttpResponse.json` of an array holding
     `weissbier`;
   - `http.get('/api/batches', …)` returning `HttpResponse.json(batches)`;
   - `http.post('/api/batches', …)` with an `async` arrow function that takes one argument and
     destructures `request` out of it (curly braces around the parameter, as `useParams` in
     `BatchPage`). In its body, three lines: `sent = await request.json();`, then `batches = …` an
     array holding a copy of `firstBatch` with the name changed, written as an object with
     `...firstBatch` first and `name: 'Weissbier'` after it, and last `return HttpResponse.json(…)`
     with two arguments: the body `{ id: 7, number: 1, name: 'Weissbier' }` and the options
     `{ status: 201 }`.

   **Why:** the GET handler reads `batches` each time it is called, not once. So when
   `useCreateBatch` invalidates the `['batches']` query after the POST, the refetch gets the new
   list. That is your real invalidation at work. `...firstBatch` copies every field, and the
   `name` after it overrides one, so the copy stays a complete `BatchSummary` without repeating
   seven lines. The 201 and the body match what the real API sends (`CreatedBatch`).

   **Watch out:** forgetting the `batches = …` line. Measured: *Unable to find role="heading" and
   name "Weissbier"*, because the page says *Batch not found.*: the list never got the new batch.

   **Watch out:** forgetting the recipes handler. Measured: *[MSW] Error: intercepted a request
   without a matching request handler: • GET /api/recipes/brewable*, then *Unable to find
   role="option" and name `/^Weissbier/`*.

   **5d. Act: fill in and send the form.**

   **Do:** first `const user = userEvent.setup();` (import `userEvent`), then
   `renderApp('/batches')`, then these lines, each starting with `await`:
   - `user.click` on `screen.getByRole('button', { name: 'New Batch' })`;
   - `screen.findByRole('option', { name: /^Weissbier/ })`, waiting for the recipe to arrive (the
     slashes make a regular expression; `^` means "starts with");
   - `user.selectOptions` with two arguments: `screen.getByRole('combobox', { name: 'Recipe' })`
     and the value `'1489'`;
   - `user.type` with `screen.getByLabelText('Brew date')` and `'2026-11-28'`;
   - `user.click` on `screen.getByRole('button', { name: 'Create batch' })`.

   **Why:** the steps a person takes, in their order. There is no typing in Name on purpose: your
   `onChange` in `register` fills it with the style name (*Weissbier*), and 5e checks that it
   was sent. A `<select>` has the role `combobox`, and its name comes from its label (*Recipe*);
   that is why the labels' `htmlFor` mattered in review round 2. `selectOptions` picks by the
   option's `value`, here the recipe's id, so the test does not depend on the date's language. A
   date input has no `textbox` role, so it is found by its label. Measured with `getByRole('textbox',
   { name: 'Brew date' })`: *Unable to find an accessible element with the role "textbox" and name
   "Brew date"*.

   **Watch out:** selecting before the recipe has arrived. Measured, with the recipes answer
   delayed by 200 ms: *TestingLibraryElementError: Value "1489" not found in options*. The dialog
   opens at once, but the options come with the API's answer. Without the `findByRole('option', …)`
   line the test passes on a fast machine and fails on a slow one: the worst kind of test.

   **5e. Assert, twice.**

   **Do:** `await screen.findByRole('heading', { name: 'Weissbier' })` is in the document. Then
   `expect(sent).toEqual(…)` with `{ recipeId: 1489, name: 'Weissbier', brewDate: '2026-11-28' }`.

   **Why:** the heading is the user's view of AC2: the dialog closed and the batch's own page
   opened. The body is the API's view. `recipeId` is a **number** (your `valueAsNumber`), the name
   is the recipe's default, and the date is in `yyyy-mm-dd`. `toEqual` compares the contents;
   `toBe` asks whether it is the very same object.

   **Watch out:** `toBe` instead of `toEqual`. Measured: *expected { recipeId: 1489, …(2) } to be
   { recipeId: 1489, …(2) } // Object.is equality*, and Vitest's hint *If it should pass with deep
   equality, replace "toBe" with "toStrictEqual"*.

   **5f. See it fail.**

   **Do:** put back the typo from review round 1, `/batchs/` in `NewBatchDialog.tsx`'s
   `navigate`, and run the test. Then undo it.

   **Why:** this is the mistake the review found by hand. Measured: *Unable to find role="heading"
   and name "Weissbier"*. From now on, the test finds it for you.

   **Check yourself:** *Tests 14 passed (14)*; lint and typecheck pass.

   **Commit:** `src/features/batches/batches.test.tsx`, message `Test creating a batch`.

6. **T4: a 400 from the API shows under its field.**

   **Do:** a fourth `it`, `async`, for example `"shows the API's message under the field it is
   about"` (double quotes outside, because the name has an apostrophe).
   - Arrange: `server.use(…)` with two handlers: the recipes one as in 5c, and
     `http.post('/api/batches', …)` returning `HttpResponse.json(…)` with two arguments. The body:
     `{ title: 'One or more validation errors occurred.', status: 400, errors: { Name: ['The Name
     field is required.'] } }`. The options: `{ status: 400, headers: { 'Content-Type':
     'application/problem+json' } }`. Then `userEvent.setup()` and `renderApp('/batches')`, as in
     5d.
   - Act: the same lines as 5d.
   - Assert, twice: `await screen.findByText('The Name field is required.')` is in the document;
     then `screen.getByRole('textbox', { name: 'Name' })` passes `toBeInvalid()`.

   **Why:** the body is the real API's 400, measured with curl in the lesson: the PascalCase
   `Name` key and ASP.NET Core's sentence. The form's own Zod check passes here (the name is
   *Weissbier*), so only the fake API can produce this error. The header matters: `createBatch`
   in `api.ts` recognises a problem by its content type, and `HttpResponse.json` would otherwise
   send `application/json`. `toBeInvalid()` checks `aria-invalid="true"`. The message alone could
   be anywhere on the page; the field being invalid proves it reached the **Name** field. That is
   AC3's "next to the fields".

   **Watch out:** leaving out `headers`. Measured: *Unable to find an element with the text: The
   Name field is required.* `createBatch` then does not recognise the answer as a problem, throws
   a plain `Error`, and the API's messages never reach the fields.

   **See it fail:** delete the `Name: 'name'` line from `fieldNames` in `NewBatchForm.tsx` for a
   moment. Measured: the text is still found, because the message goes to the form-wide alert
   (`root.server`) instead, and the second assert fails: *expect(element).toBeInvalid() …
   Received element is not currently invalid*. This is why the test has two asserts. Undo it.

   **Check yourself:** *Tests 15 passed (15)*.

   **Commit:** `src/features/batches/batches.test.tsx`, message `Test showing an API error`.

7. **Run everything and ask for a test review** (say "review the tests").

   **Check yourself:** the list below is all ticked.

   No commit.

## Before you ask for a test review

- [ ] `npm run lint`, `npm run typecheck`, `npm test -- --run` (*Tests 15 passed (15)*),
      `npm run build` and `npx prettier . --check` pass.
- [ ] You saw each of T1–T4 fail once (3e, 4, 5f, 6) and undid each break: `git status` shows no
      change outside the test files.
- [ ] No test depends on timing or on your machine's language: T3 and T4 wait for the recipe
      option, and pick it by its value.
- [ ] Each test's name says what the user gets.
- [ ] Every step is committed; `git log --oneline main..` lists them.
