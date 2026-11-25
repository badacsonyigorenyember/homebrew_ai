# Lesson: a1-07 · Batches page and new batch

## What you will build

The Batches page stops being a placeholder. It lists your batches (number, name, style, brew date,
status): a table on wide screens, cards on narrow ones. A "New batch" button opens a form in a
dialog (full screen on a phone): pick a recipe, keep or change the name, pick a brew date, and the
API from a1-06 creates the batch. The app then opens `/batches/:id`, a placeholder page with the
batch's name that a1-09 fills.

It is done when:

- **AC1** No batches shows "No batches yet" and the New batch button.
- **AC2** Creating a batch opens its page, and going back shows it in the list.
- **AC3** A 400 from the API shows its messages next to the fields.
- **AC4** At phone width (375 px) the list and the dialog fit without sideways scrolling.

**How the pieces fit.** One file, `src/features/batches/api.ts`, is the only place that knows the
API: the response types (written by hand until a2-02 generates them), the three fetch functions
and the hooks around them: `useBatches` and `useBrewableRecipes` (TanStack Query *queries*, as
`useHealth` in a0-04) and `useCreateBatch` (a *mutation*, new here). `BatchesPage` calls
`useBatches` and shows loading text, error text, "No batches yet", or `BatchList`, which draws the
table and the cards. Beside the title sits `NewBatchDialog`: the button and the dialog, whose
content is `NewBatchForm`. The form is React Hook Form checked by a Zod schema; on submit it calls
the mutation. When the API answers 201, the form tells the dialog, which closes and sends the
router to `/batches/<id>`, where `BatchPage` reads the id from the URL. When it answers 400, the
form puts each message under its field. The mutation also marks the cached batch list as stale,
so the list is fetched again and already holds the new batch.

What the tools look like today (measured 2026-11-25 in a scratch copy of your `app/web`, with your
Node 26.13.0, TypeScript 6.0.3 and the API on this branch; every error message and behaviour
quoted below comes from that run):

| Thing | Version | Note |
|---|---|---|
| `react-hook-form` | 7.92.0 | forms |
| `zod` | 4.6.7 | schemas; v4 API (`z.iso.date`, `error` param) |
| `@hookform/resolvers` | 7.0.9 | connects the two |
| `shadcn` (the CLI) | 4.23.1 | `add` writes Base UI versions of the components, like your `sheet.tsx` |

What the API sends (measured with curl on the running API):

- `GET /api/batches`: an array of `{ id, number, name, styleCode, styleName, brewDate, status }`;
  `brewDate` is a string like `"2026-12-05"`, `status` is one of `plan`, `prep`, `brew_day`,
  `ferment`, `condition`, `package`, `done` (the check in `db/061_app_batch.sql`).
- `GET /api/recipes/brewable`: an array of `{ id, styleCode, styleName, og, fg, abv, ibu, batchL,
  createdAt }`, newest first; `og` looks like `1.0481`, `createdAt` like
  `"2026-11-04T09:18:21.833969Z"` (a UTC moment, the `Z`).
- `POST /api/batches` with nothing filled in: status 400, `Content-Type: application/problem+json`,
  and a body whose `errors` field has one entry per field, **keys in PascalCase**:
  `{"RecipeId":["The RecipeId field is required."],"Name":["The Name field is required."],"BrewDate":["The BrewDate field is required."]}`.
  A name of only spaces gives the same `Name` message. The other 400 (a recipe with no process)
  and the 404 (unknown recipe) are problem details with a `detail` sentence and no `errors`.

## Steps

1. **Check where you are, and start the API.** In `app/web`, run `git branch --show-current` and
   `git status`. Then start the API (in `app/`, `dotnet run --project api`, "Run the API" in
   `app/README.md`), and the web app (`npm run dev` in `app/web`) in a second terminal.
   *Why:* the work belongs on the ticket's branch, and every browser check below needs the real
   API behind Vite's proxy (a0-04).
   *Check yourself:* the branch is `a1-07-batches-page`; `git status` is clean; the header badge
   says "API ok".

   No commit.

2. **Install the form libraries.** In `app/web`:
   `npm install react-hook-form zod @hookform/resolvers`.
   *Why:* a form looks simple and is not: every field needs its current value, whether it was
   touched, its error, and the whole form needs "submitting" and "submit only when valid". Written
   by hand with `useState`, that is a state variable and a handler per field, and a re-render of
   the whole form on every key press. **React Hook Form** keeps the values in the inputs
   themselves (*uncontrolled* inputs, the opposite of the controlled `Sheet` from a1-02) and only
   re-renders when something you display changes, such as an error. **Zod** describes what valid
   data looks like as a *schema*, an object you build once and ask "is this valid?". The same
   schema also gives you the TypeScript type of the form's values, so the rules and the type can
   never drift apart. `@hookform/resolvers` is the small adapter that lets React Hook Form ask Zod.
   SYSTEM.md §4 picked these; Zod checks the AI's UI actions later too (F6.3).
   Docs: [React Hook Form — Get started](https://react-hook-form.com/get-started) (read the first
   example and "Schema Validation", 10 minutes), [Zod — Intro](https://zod.dev/) and
   [Basic usage](https://zod.dev/basics) (10 minutes).
   *Watch out:* most tutorials online are Zod 3. Zod 4 changed how custom messages are written
   (`error` instead of `message`, `required_error` and `invalid_type_error`) and moved date strings
   to `z.iso.date()`. Read zod.dev, not a blog post.
   *Check yourself:* `package.json` lists the three under `dependencies`.

   *Commit:* `package.json`, `package-lock.json`, message `Add React Hook Form and Zod`.

3. **Add the shadcn components.** In `app/web`:
   `npx shadcn@latest add table dialog field input native-select`.
   *Why:* the same reason as the Sheet in a1-02: a dialog has to trap focus, close on Escape and
   give focus back; a table and labelled inputs have the right markup and theme colours already.
   `field` is shadcn's set of form pieces (`Field`, `FieldLabel`, `FieldError`, `FieldGroup`) that
   lay out a label, an input and its error and mark the field red when invalid; it brings `label`
   and `separator` with it. **Native select** rather than shadcn's `select`: it draws the
   browser's own `<select>`, so on a phone you get the phone's own picker, it works with React
   Hook Form's `register` with no glue (step 9), and tests can pick an option with one call. The
   custom `select` needs a `Controller` wrapper and is harder to test, for nothing this form needs.
   Docs: [shadcn — Native Select](https://ui.shadcn.com/docs/components/base/native-select),
   [Field](https://ui.shadcn.com/docs/components/base/field).
   *Check yourself:* measured, the output says *Created 7 files:* `table.tsx`, `input.tsx`,
   `label.tsx`, `native-select.tsx`, `separator.tsx`, `dialog.tsx`, `field.tsx`, and skips
   `button.tsx`. Nothing uses them yet and every check still passes (measured: lint, typecheck,
   tests, build). `.prettierignore` and the ESLint override from a1-01 already cover the folder.

   *Commit:* the seven new files under `src/components/ui/`, message
   `Add the shadcn table, dialog and form components`.

4. **Write the read side of `api.ts`**: the types for the two lists, their fetch functions and
   their hooks. Create `src/features/batches/api.ts` (`.ts`: no JSX).

   **Read first (about 25 minutes).**
   - [TypeScript — Everyday Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html):
     "Arrays", "Union Types" and "Literal Types". Look for how `string | null` is written and
     what an array type looks like.
   - [MDN — Nullish coalescing (`??`)](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing)
     and [Optional chaining (`?.`)](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Optional_chaining):
     the first example of each. You use both from step 5 on.
   - Your own `src/features/health/useHealth.ts`: this step is that file three times over.

   **4a. The status type.** An exported `type BatchStatus`: the seven status strings from the
   list above, joined by `|`, exactly as the database spells them (`brew_day` with an underscore).
   *Why:* a union of the exact values, the same idea as `ApiStatus` in a0-03, so step 5's labels
   can be a `Record<BatchStatus, string>` that the type check keeps complete.

   **4b. The batch summary type.** An exported `type BatchSummary`, an object type with the seven
   fields of a `GET /api/batches` item, named as the JSON names them (camelCase). `id` and
   `number` are `number`; `brewDate` is a `string`; `status` is your `BatchStatus`; `styleName` is
   `string | null`, because the API's `StyleName` is `string?` (a style can lack a name).
   *Why:* the response type says what you expect; `response.json()` itself is `any` (a0-04). A
   `null` in the type makes the compiler stop you from calling a string method on it without a
   check. `brewDate` stays a string on purpose: it is a *calendar date*, a day, not a moment in
   time (SYSTEM.md §9), and step 5 says why turning it into a `Date` goes wrong.

   **4c. The brewable recipe type.** An exported `type BrewableRecipe` with the nine fields of a
   `GET /api/recipes/brewable` item. `og`, `fg`, `abv` and `ibu` are `number | null` (the API's
   `decimal?`); `batchL` is `number`; `createdAt` is a `string`.
   *Why:* the dropdown shows style, OG, ABV and date (the ticket). You could leave out fields the
   page does not use; writing the whole shape now makes a2-02's switch to generated types a plain
   swap.

   **4d. The two fetch functions.** Not exported: `fetchBatches()` returning
   `Promise<BatchSummary[]>` (`[]` after a type means "an array of"), which fetches
   `/api/batches`, throws on a non-`ok` response and returns the JSON; and
   `fetchBrewableRecipes()` returning `Promise<BrewableRecipe[]>`, the same for
   `/api/recipes/brewable`. Each error message names what failed and the status.
   *Why:* the same shape as `fetchHealth`, for the same reasons (a0-04 "The query function throws
   on failure"). Two plain functions, not one generic `fetchJson<T>(url)`: two copies of four lines
   are easier to read than a helper with a type parameter (C7).
   *Check yourself:* the failing check is expected until 4e: typecheck says *'fetchBatches' is
   declared but its value is never read.*

   **4e. The two hooks.** Exported: `useBatches()`, a `useQuery` with the key `['batches']` and
   `fetchBatches`; and `useBrewableRecipes()`, a `useQuery` with the key `['recipes',
   'brewable']` and `fetchBrewableRecipes`. No retry options: these want the library's defaults
   (a0-04, "Settings for one query live on that query").
   *Why:* query keys are arrays so they can be *hierarchical*: `['recipes', 'brewable']` is "the
   brewable part of recipes", and when M4 adds `['recipes']` for the full list, invalidating
   `['recipes']` refreshes both. The key `['batches']` matters in step 8: that is the name the
   mutation uses to mark the list stale.
   Docs: [TanStack Query — Query keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys),
   "Array keys with variables".
   *Check yourself:* `npm run typecheck` and `npm run lint` pass. Nothing calls the hooks yet;
   an unused export breaks no check.

   *Commit:* `src/features/batches/api.ts`, message `Add the batch list types and queries`.

5. **Write `BatchList`**, the table and the cards, in `src/features/batches/BatchList.tsx`.

   **Read first (about 15 minutes).**
   - [shadcn — Table](https://ui.shadcn.com/docs/components/base/table): "Usage". The pieces are
     `Table`, `TableHeader`, `TableRow`, `TableHead`, `TableBody`, `TableCell`.
   - [Tailwind — display](https://tailwindcss.com/docs/display): `hidden`, `block`, `table`.

   **5a. The props and signature.** A `type BatchListProps` with one field, `batches`, a
   `BatchSummary[]` (a type-only import from `./api`, a0-04), and
   `export function BatchList({ batches }: BatchListProps)`.
   *Why:* `BatchList` only draws what it is given; it does not fetch. That is the
   **container/presentational** split: the page (step 6) owns the query and its loading and error
   states, the list only knows how a batch looks. A list that fetches by itself would need the
   loading and empty states too, and could not be drawn with made-up batches in a test.

   **5b. The status labels.** Above the component, a `const statusLabels` typed
   `Record<BatchStatus, string>`: `plan` → `'Plan'`, `brew_day` → `'Brew day'`, and so on for all
   seven.
   *Why:* the database's codes are for code; the screen shows words. The `Record` is the safety
   net you know from a0-03: measured, leave out `done` and typecheck says *Property 'done' is
   missing in type '{ plan: string; … package: string; }' but required in type
   'Record<BatchStatus, string>'.* When M3 adds a status, the compiler shows you this table.

   **5c. The table, for wide screens.** Return a fragment (`<>…</>`, a1-02's `<>` around two
   siblings) holding first a `Table` with the class `hidden md:table`. A header row with the five
   column names (No., Name, Style, Brew date, Status), then in the body `batches.map(…)` returning
   one `TableRow` per batch, `key` its `id`, and five `TableCell`s: the number, the name, the style
   (code, then name when there is one), the brew date as it came, and `statusLabels[status]`.
   *Why:* `hidden` hides the table on every width, `md:table` shows it again from 768 px with
   `display: table` (not `md:block`, which would break the table's column layout). Mobile-first
   as in a1-02 step 8. The name is a React Router `Link` to `` `/batches/${id}` `` (a template
   literal, a0-04), so you can open a batch from the list; step 7 adds that page.
   *Watch out:* the brew date. `new Date('2026-12-05')` reads a date-only string as midnight
   **UTC**, and showing it in local time can move it to the day before. Measured with Node:
   in New York, `new Date('2026-12-05').toLocaleDateString('en-GB')` prints *04/12/2026*; in
   Budapest it prints *05/12/2026*. Show the string as the API sent it.

   **5d. The cards, for narrow screens.** After the table, a `<ul>` with `md:hidden` (and a small
   gap between items), one `<li>` per batch with a border, rounded corners and padding: the number
   and name (the same `Link`) on the first line, and style, brew date and status on a smaller,
   muted second line (`text-sm text-muted-foreground`).
   *Why:* a five-column table does not fit 375 px; squeezed, it scrolls sideways (AC4). The same
   data as a short card per batch fits any width. Both are in the page and CSS shows one, the same
   trick as the menu column and the drawer button in a1-02.
   *Watch out:* because both are in the page, a test that runs without CSS (jsdom, the test
   lesson) sees each batch name twice. That is expected; the test lesson shows how to look inside
   one of them.
   *Check yourself:* `npm run typecheck` and `npm run lint` pass. Nothing shows it yet; step 6
   does.

   *Commit:* `src/features/batches/BatchList.tsx`, message `Add the batch list`.

6. **Show the list on `BatchesPage`.** In `BatchesPage.tsx`: call `useBatches()` at the top of the
   component and keep the result in one `const` (for example `batches`). Keep the `<h1>`, then
   show exactly one of four things: "Loading batches…" while `isPending`; an error sentence with
   `error.message` when `isError`; "No batches yet" when it succeeded with an empty array; else
   `<BatchList batches={…} />` with the data. Wrap the page in a `div` that stacks its children
   with a gap (`flex flex-col gap-4`), and put the `<h1>` in a row (`flex items-center
   justify-between`) that will also hold the New batch button in step 10.
   *Why:* plain text states for now; a2-06 replaces them with the shared ones (F1.6). Check
   `isPending` and `isError` first: after them TypeScript knows `data` is there, so
   `batches.data.length` needs no `?.`. This is *narrowing*: TanStack Query's result type is a
   union, and checking `isSuccess` (or ruling out the others) tells the compiler which member you
   have. An empty array is a successful answer, not an error and not "loading", so it gets its own
   sentence (AC1).
   Docs: [react.dev — Conditional rendering](https://react.dev/learn/conditional-rendering),
   "Logical AND operator (`&&`)" and "Conditional (ternary) operator".
   *Watch out:* `{batches.data.length && <BatchList … />}` with an empty list draws a literal `0`
   on the page: `&&` returns its left side when that is falsy, and React draws numbers. Compare
   with `=== 0`, or use a ternary.
   *Check yourself (AC1, the text):* with the API running and no batches, `/batches` shows
   "Batches" and "No batches yet". Stop the API: after the retries (about 7 s, a0-04) it shows
   your error sentence. Start it again. `npm test -- --run` still passes (measured: the routing
   tests only look at the heading, which is there before the list loads).

   *Commit:* `src/features/batches/BatchesPage.tsx`, message `Show the batches on the Batches page`.

7. **Add the batch page placeholder and its route.**

   **Read first (about 10 minutes).**
   - [React Router — Routing, "Dynamic Segments"](https://reactrouter.com/start/declarative/routing#dynamic-segments)
     and [`useParams`](https://reactrouter.com/api/hooks/useParams), "Basic Usage".

   **7a. The page.** `src/features/batches/BatchPage.tsx` with `export function BatchPage()`. It
   reads `id` from `useParams()` (destructured), calls `useBatches()`, shows short loading and
   error text like step 6, then finds the batch in the list whose `id` matches and shows its
   `name` as the `<h1>`, or "Batch not found" when none matches.
   *Why:* there is no `GET /api/batches/{id}` yet (a1-09 adds it), and the list already holds the
   name. Reading it from the list, not from data handed over during navigation, means the page
   also works when you reload it or paste its URL, the "every view has a URL" rule (SYSTEM.md
   §3). a1-09 replaces the body; the file and the route stay.
   *Watch out:* every URL parameter is a **string** (or `undefined`, if the route had no such
   segment), and `id` in the list is a number. Measured, comparing them directly fails the type
   check: *This comparison appears to be unintentional because the types 'number' and 'string |
   undefined' have no overlap.* Turn one side into the other's type before comparing
   (`String(…)` or `Number(…)`).

   **7b. The route.** In `App.tsx`, inside the layout route, a `<Route>` with
   `path="batches/:id"` and `element={<BatchPage />}`, next to the `batches` route.
   *Why:* `:id` is a *dynamic segment*: it matches any one part of the path and hands its value
   to `useParams` under the name after the colon. React Router ranks `batches/:id` above the `*`
   route by itself, so the order of the lines does not matter (a1-02, 5f).
   *Check yourself:* `/batches/123` shows "Batch not found" with the menu around it; `/batches`
   still shows the list. Once a batch exists (step 11), its link in the list opens its page.
   Typecheck, lint and tests pass.

   *Commit:* `src/features/batches/BatchPage.tsx`, `src/App.tsx`, message
   `Add the batch page placeholder`.

8. **Write the create side of `api.ts`**: the request and response types, the error class, the
   POST and the mutation hook.

   **Read first (about 35 minutes).**
   - [MDN — Using the Fetch API, "Setting a body"](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch#setting_a_body)
     and "Setting headers": a POST with JSON is `method`, a `Content-Type` header and
     `JSON.stringify` of the data.
   - [MDN — Classes](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes),
     "Defining classes", "Constructor" and "Inheritance": a class, `extends`, `super(...)`.
   - [TypeScript — Narrowing, "instanceof narrowing"](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#instanceof-narrowing).
   - [TanStack Query — Mutations](https://tanstack.com/query/latest/docs/framework/react/guides/mutations):
     the first example, "Mutation Side Effects", and the paragraph on callbacks passed to `mutate`.
   - [TanStack Query — Invalidations from Mutations](https://tanstack.com/query/latest/docs/framework/react/guides/invalidations-from-mutations):
     the example is the shape of 8e.

   **8a. The request and response types.** Exported: `type CreateBatchRequest` with `recipeId`
   (`number`), `name` (`string`) and `brewDate` (`string`, the `"2026-12-05"` form a date input
   gives and `DateOnly` reads); and `type CreatedBatch` with the fields of the 201 answer you use:
   at least `id`, `number` and `name`.
   *Why:* the answer has more (`BatchResponse` in `BatchEndpoints.cs`, with the copied items), but
   a hand-written type should hold what the UI reads; a1-09 reads the full batch from its own
   endpoint, and a2-02 replaces these types anyway.

   **8b. The problem details type.** Exported `type ProblemDetails` with four optional fields:
   `title` and `detail` (`string`), `status` (`number`), and `errors`, a
   `Record<string, string[]>` (field name → its messages).
   *Why:* RFC 9457 problem details are how the API answers every error (SYSTEM.md §9), and the
   curl output above shows both kinds: with `errors` per field, or with only `detail`. All fields
   optional, because neither kind has all of them.

   **8c. The error class.** Exported `class ApiProblemError extends Error`, with one field,
   `problem`, typed `ProblemDetails`, declared on its own line at the top of the class body, and a
   constructor that takes a `ProblemDetails`, calls `super(...)` with a readable message (the
   problem's `detail`, else its `title`, else a fixed sentence: `??` twice) and then stores the
   problem in `this.problem`.
   *Why:* `fetch` gives you a problem object; TanStack Query hands your code whatever the mutation
   function threw. Throwing an `Error` subclass that carries the problem keeps both: anything that
   only shows `error.message` gets a sentence, and the form (step 9) can check
   `error instanceof ApiProblemError` and read the per-field messages. That `instanceof` check is
   also what tells TypeScript the error has a `problem` field. Throw `Error`s, never plain objects:
   an `Error` has a stack trace, and every `catch` and `onError` expects one.
   *Watch out:* many TypeScript examples write the field inside the constructor's brackets
   (`constructor(public problem: …)`). Your `tsconfig.app.json` has `erasableSyntaxOnly` on, which
   forbids that (it generates code). Measured: *error TS1294: This syntax is not allowed when
   'erasableSyntaxOnly' is enabled.*
   Docs: [TypeScript — `erasableSyntaxOnly`](https://www.typescriptlang.org/tsconfig/#erasableSyntaxOnly).

   **8d. The POST.** Not exported: `async function createBatch(request: CreateBatchRequest):
   Promise<CreatedBatch>`. It fetches `/api/batches` with an options object: `method: 'POST'`,
   a `headers` object with `'Content-Type': 'application/json'`, and `body` set to
   `JSON.stringify(request)`. Then, in this order: if the response's `Content-Type` header
   (`response.headers.get(...)`) is `application/problem+json`, throw a new `ApiProblemError` made
   from the awaited JSON; else if it is not `ok`, throw a plain `Error` naming the status (as in
   4d); else return the JSON.
   *Why:* without the `Content-Type` request header, ASP.NET Core does not read the body as JSON:
   measured, it answers *415 Unsupported Media Type* with an empty body. The problem check comes
   first and looks at the *type* of the answer, not only the status: that 415, or a 502 from
   Vite's proxy when the API is stopped, has no problem JSON, and reading one would fail with a
   confusing parse error instead of your message.

   **8e. The mutation hook.** Exported `useCreateBatch()`. It gets the query client with
   `useQueryClient()` and returns `useMutation` with `mutationFn: createBatch` and an `onSuccess`
   that returns `queryClient.invalidateQueries({ queryKey: ['batches'] })`.
   *Why:* a **mutation** is TanStack Query's name for a request that *changes* server data. Unlike
   a query it does not run by itself: it gives you a `mutate` function to call (on submit), and
   tracks that call's `isPending`, `error` and `data`. After a batch is created the cached list is
   out of date. *Invalidating* the `['batches']` key marks it stale and fetches it again at once
   while something shows it. Returning the promise from `onSuccess` makes the mutation wait for
   that refetch before it counts as done, so when the form navigates (step 10) the list in the
   cache already holds the new batch. Measured without the invalidation: the new batch's page
   first shows *Batch not found*, then its name a moment later. This callback lives on the hook
   because every caller wants it; the navigation does not (step 9g).
   *Check yourself:* `npm run typecheck` and `npm run lint` pass. Still unused; step 9 calls it.

   *Commit:* `src/features/batches/api.ts`, message `Add the create-batch mutation`.

9. **Write `NewBatchForm`**, in `src/features/batches/NewBatchForm.tsx`, in small steps.

   **Read first (about 45 minutes, in this order).**
   - [Zod — Basic usage](https://zod.dev/basics): "Defining a schema", "Parsing data", "Inferring
     types".
   - [Zod — Defining schemas](https://zod.dev/api): "Strings" (`.trim()`, `.min()`), "Numbers",
     "ISO dates" and "Objects".
   - [Zod — Customizing errors](https://zod.dev/error-customization): "The `error` param", the
     first two examples.
   - [React Hook Form — `register`](https://react-hook-form.com/docs/useform/register): the
     options table, `valueAsNumber` and `onChange` in particular.
   - [React Hook Form — `handleSubmit`](https://react-hook-form.com/docs/useform/handlesubmit) and
     [`setError`](https://react-hook-form.com/docs/useform/seterror): the "server error" examples.
   - [React Hook Form resolvers — Zod](https://github.com/react-hook-form/resolvers#zod): the
     example is the shape of 9c.
   - [shadcn — React Hook Form](https://ui.shadcn.com/docs/forms/react-hook-form): how `Field`,
     `FieldLabel` and `FieldError` sit around an input, and `data-invalid` / `aria-invalid`. Its
     examples wrap every input in `Controller`; you use `register` instead (9d says why).
   - [MDN — `<input type="date">`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/date),
     "Value": always `yyyy-mm-dd`, whatever the browser shows.

   **9a. The schema.** Above the component, a `const newBatchSchema = z.object({...})` (import
   `z` by name from `'zod'`) with three keys, mirroring the API's rules:
   - `recipeId`: `z.number(...)` with a custom message for "nothing picked", for example
     "Choose a recipe";
   - `name`: `z.string()`, then `.trim()`, then `.min(1, ...)` with a message;
   - `brewDate`: `z.iso.date(...)` with a message.

   *Why:* the API's three `[Required]` rules, checked before the request is sent, so the usual
   mistakes are shown at once without a round trip. `.trim()` then `.min(1)` mirrors exactly what
   `[Required]` does to a string (measured: a name of spaces gets *The Name field is required.*),
   and it also trims the name you send. `z.iso.date()` accepts only a real `yyyy-mm-dd` date, the
   form `DateOnly` reads; an empty date input gives `''`, which fails it. The custom message is
   the first argument (a string), or an object with an `error` key.
   *Check yourself:* the failing check is expected until 9b uses it: *'newBatchSchema' is
   declared but its value is never read.*

   **9b. The values type.** `type NewBatchValues = z.infer<typeof newBatchSchema>`.
   *Why:* `typeof` on a value gives its type; `z.infer` turns a schema's type into the type of the
   data it accepts: here `{ recipeId: number; name: string; brewDate: string }`. The rules and the
   type now come from one place. Hover the name in your editor to see it.

   **9c. The props, signature and form.** A `type NewBatchFormProps` with one field, `onCreated`,
   a function that takes a `CreatedBatch` and returns `void`, and
   `export function NewBatchForm({ onCreated }: NewBatchFormProps)`. In the body:
   `useBrewableRecipes()`, `useCreateBatch()`, and `useForm<NewBatchValues>({...})` (from
   `'react-hook-form'`) with `resolver: zodResolver(newBatchSchema)` (from
   `'@hookform/resolvers/zod'`) and `defaultValues` of an empty `name` and an empty `brewDate`.
   Keep the result whole in one `const`, for example `form`.
   *Why:* the **callback prop** pattern from a1-02's `onNavigate`: the form does not know it sits
   in a dialog or what happens after a create; it reports "created this batch" and the dialog
   decides (step 10). `defaultValues` gives each text input a starting value, so React Hook Form
   knows when a field has been changed (*dirty*), which 9i relies on. `recipeId` gets none: an
   empty choice is the start.

   **9d. The form element and the recipe field.** Return a `<form>` whose `onSubmit` is
   `form.handleSubmit(onSubmit)` (9g writes `onSubmit`; write an empty one for now), holding a
   `FieldGroup`. In it, a `Field` with `data-invalid` set to whether there is a `recipeId` error
   (`!!form.formState.errors.recipeId`, the `!!` turns "an object or undefined" into `true` or
   `false`), holding:
   - a `FieldLabel` with `htmlFor="recipeId"` and the text "Recipe";
   - a `NativeSelect` with `id="recipeId"`, `className="w-full"`, `aria-invalid` set like
     `data-invalid`, and the result of `form.register('recipeId', { valueAsNumber: true })` spread
     onto it (`{...` the call `}`);
   - inside it, a first `NativeSelectOption` with `value=""` and "Choose a recipe" (or
     "Loading recipes…" while the recipes query is pending), then `recipes.data?.map(…)` with one
     option per recipe, `key` and `value` its `id`, and its label from 9e;
   - after the select, `<FieldError errors={[…]} />` with the `recipeId` error in an array.

   *Why:* `register('recipeId')` returns `name`, `ref`, `onChange` and `onBlur`; spreading them
   onto the `<select>` is how React Hook Form connects to an input it does not control. That only
   works on elements that behave like real inputs, which is why `NativeSelect` needs no
   `Controller`. A `<select>`'s value is always a string; `valueAsNumber` makes React Hook Form
   hand Zod a number (and `NaN` for the empty option, which `z.number()` rejects with your
   message). `htmlFor` matching `id` ties the label to the select, so clicking the label focuses
   it and a screen reader (and a test's `getByLabelText`) finds the select by "Recipe".
   `aria-invalid` tells assistive tech the field is wrong and gives it the red border.
   *Watch out:* forget `valueAsNumber` and the type check is happy, but the form never submits:
   measured, after picking a recipe and pressing Create, the select still says *Choose a recipe*,
   because Zod got the string `"1"` and wants a number.
   *Watch out:* the `<form>` needs `handleSubmit` around your function. A bare `onSubmit={...}`
   lets the browser do its own submit, which loads the page again.

   **9e. The recipe's label.** Above the component, a small function `recipeLabel(recipe:
   BrewableRecipe): string` that returns one line: the style name (or the code when there is no
   name: `??`), the OG with three decimals (`toFixed(3)`), the ABV with a `%`, and the date part of
   `createdAt` as a local date (`new Date(createdAt).toLocaleDateString()`), joined with ` · `.
   Show a dash for an OG or ABV that is `null`.
   *Why:* the ticket asks for style, OG, ABV and date, so recipes of the same style can be told
   apart. `createdAt` is a UTC moment (the `Z`), so `new Date` reads it right, and showing it in
   local time is what SYSTEM.md §9 asks; the brew date in 5c was the other case. `toFixed(3)`:
   measured, `1.0481` shows as *1.048*. A function, not inline in the JSX, so the option line
   stays readable. Measured in the test run: *Weissbier · OG 1.048 · 4.9% · 11/4/2026* (the date
   follows the browser's language).
   *Check yourself:* typecheck passes once 9d uses it.

   **9f. The name and brew date fields.** Two more `Field`s like 9d: "Name" with an `Input`
   registered as `name`, and "Brew date" with an `Input` of `type="date"` registered as
   `brewDate`, each with its `id`, `aria-invalid`, `data-invalid` and `FieldError`. After them, a
   submit `Button` ("Create batch", `type="submit"`) that is `disabled` while the mutation
   `isPending`.
   *Why:* `type="date"` gives every browser and phone its own date picker and always yields
   `yyyy-mm-dd`, the shape the API and `z.iso.date()` want; no date library needed. Disabling the
   button while the request runs stops a double click from creating two batches.
   *Check yourself:* typecheck and lint pass. The form is not on screen until step 10.

   **9g. Submit.** Write `onSubmit(values: NewBatchValues)` inside the component: it calls
   `createBatch.mutate(values, { onSuccess: …, onError: … })`, where `onSuccess` is `onCreated`
   (passed as it is) and `onError` is 9h.
   *Why:* `handleSubmit` runs Zod first and calls your function only with valid, already trimmed
   values, so `onSubmit` never sees a bad form. The callbacks passed to `mutate` (rather than to
   `useMutation`) belong to this one call, which is the place for what only this form does:
   report the new batch, place the errors. TanStack Query runs them only while the form is still
   on screen.

   **9h. The server's errors.** In `onError(error)`: if `error` is an `ApiProblemError` **and** its
   problem has `errors`, go through them with `for (const [key, messages] of
   Object.entries(…))`, look up the form field for each `key`, and call `form.setError(field, {
   message: … })` with the messages joined by a space. A key you have no field for, and any other
   error, goes to `form.setError('root.server', { message: … })` with the problem's message
   (`error.message`). Under the fields, before the button, show `form.formState.errors.root?.server`
   when it is there, as a `<p role="alert">` in the destructive colour.
   The lookup is a `const fieldNames` above the component, typed
   `Partial<Record<string, keyof NewBatchValues>>`, mapping `RecipeId` → `'recipeId'`,
   `Name` → `'name'`, `BrewDate` → `'brewDate'`.
   *Why:* this is AC3. The API sends **PascalCase** keys (measured above) and your fields are
   camelCase, so a lookup translates them. `keyof NewBatchValues` is the union of the form's field
   names, so a typo is caught (measured: *Type '"brewdate"' is not assignable to type '"name" |
   "recipeId" | "brewDate" | undefined'. Did you mean '"brewDate"'?*). `Partial` makes a lookup of
   an unknown key typed as possibly `undefined`, which is true, and the `??` to `'root.server'`
   handles it. `Object.entries` turns an object into an array of `[key, value]` pairs, and the
   square brackets in the `for` pick the pair apart (destructuring, a1-02). `root.server` is React
   Hook Form's place for a form-wide error, not tied to a field; `role="alert"` makes a screen
   reader read it out when it appears. A field error you set is cleared on the next submit, so the
   user can fix the field and try again (measured).
   *Watch out:* passing the API's key straight in fails the type check. Measured with
   `setError('Name', …)`: *Argument of type '"Name"' is not assignable to parameter of type
   '"name" | "recipeId" | "brewDate" | ErrorNamespacePath'.*
   *Watch out:* reading `error.problem` without the `instanceof` check fails too: *Property
   'problem' does not exist on type 'Error'.* The check is what narrows the type.
   Docs: [MDN — `Object.entries()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/entries),
   [`for...of`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/for...of),
   [TypeScript — `keyof`](https://www.typescriptlang.org/docs/handbook/2/keyof-types.html),
   [`Partial`](https://www.typescriptlang.org/docs/handbook/utility-types.html#partialtype).

   **9i. The name follows the recipe.** Add an `onChange` option to the recipe's `register` call
   (next to `valueAsNumber`): a function that takes the change event, finds the picked recipe in
   `recipes.data` by `Number(event.target.value)`, and, if there is one and the name field is not
   dirty (`form.getFieldState('name').isDirty`), calls `form.setValue('name', …)` with the
   recipe's style name (or code).
   *Why:* the ticket wants the style name as the default name. Doing it in the select's change
   handler, rather than in a `useEffect` that watches the recipe, keeps cause and effect in one
   place: "when you pick a recipe, the name follows". An effect would run after every render and
   is the pattern react.dev warns against for this
   ([You might not need an Effect, "Sharing logic between event handlers"](https://react.dev/learn/you-might-not-need-an-effect#sharing-logic-between-event-handlers)).
   `setValue` without options does not mark the field dirty, so the name keeps following the
   recipe until **you** type in it; after that, your name stays. Measured: pick Weissbier, the
   name says *Weissbier*; pick American Pale Ale, it says *American Pale Ale*; type "My one" and
   pick Weissbier again, it stays *My one*.
   *Check yourself:* `npm run typecheck` and `npm run lint` pass.

   *Commit:* `src/features/batches/NewBatchForm.tsx`, message `Add the new batch form`.

10. **Write `NewBatchDialog` and put it on the page.**

    **Read first (about 15 minutes).**
    - [shadcn — Dialog (Base UI)](https://ui.shadcn.com/docs/components/base/dialog): "Usage".
      The same `render` trigger as your `Sheet`.
    - [React Router — `useNavigate`](https://reactrouter.com/api/hooks/useNavigate): "Navigate to
      another path".

    **10a. The component and its state.** `src/features/batches/NewBatchDialog.tsx` with
    `export function NewBatchDialog()`, no props. In it, `useState(false)` for whether it is open
    (as `menuOpen` in a1-02) and `useNavigate()` from `'react-router'`.
    *Why:* the dialog must close after a successful create, and only your code knows when that
    happened, so it is **controlled**, exactly like the drawer in a1-02 step 10. `useNavigate`
    returns a function that sends the router to a path from code, for the moments where no link is
    clicked (here: after the API answered).

    **10b. The dialog.** Return a `Dialog` with `open` and `onOpenChange` wired to the state; in
    it a `DialogTrigger` whose `render` is a `<Button />` and whose text is "New batch"; then a
    `DialogContent` holding a `DialogHeader` with a `DialogTitle` "New batch", and
    `<NewBatchForm />` with an `onCreated` arrow function that takes the batch, sets the state to
    `false` and navigates to `` `/batches/${batch.id}` ``.
    *Why:* `DialogTitle` names the dialog for screen readers (and tests find it by that name).
    The form sits *inside* `DialogContent`, and Base UI removes the content from the page when the
    dialog closes, so each opening starts with a fresh, empty form, and the recipes are only
    fetched once the dialog first opens. The arrow function is needed for the same reason as
    a1-02's `onNavigate`: two things happen, in your order.

    **10c. Full screen on narrow screens.** Give `DialogContent` a `className` that makes it the
    whole screen below the `sm` breakpoint (640 px) and the normal centred box from `sm` up: full
    height (`h-svh`), no max width (`max-w-none`), square corners (`rounded-none`), content at the
    top (`content-start`); then `sm:h-auto`, a `sm:max-w-…` (for example `lg`, so the long recipe
    lines fit) and `sm:rounded-xl`.
    *Why:* the ticket asks for a full-screen sheet on narrow screens. `dialog.tsx` already has a
    `className` prop and merges it with `cn` (a1-01), and `cn` lets a later class beat an earlier
    one of the same kind, so yours win over the defaults without editing the generated file.
    `content-start`: the dialog lays its children out as a grid, and on a full-height box the grid
    spreads the rows out (measured: the form floats in the middle of the screen without it).
    *Watch out:* the generated default includes `max-w-[calc(100%-2rem)]`; without `max-w-none`
    the "full screen" dialog keeps a gap on both sides.

    **10d. Put it on the page.** In `BatchesPage`, `<NewBatchDialog />` in the row beside the
    `<h1>` from step 6, shown in every state (loading, error, empty, list).
    *Why:* AC1 asks for the button when there are no batches, and it must not depend on the list
    having loaded: you can create a batch while the list is still on its way.
    *Check yourself:* typecheck, lint and tests pass. In the browser, "New batch" opens the
    dialog with the recipes in the dropdown, Escape closes it, and opening it again shows an empty
    form. Press "Create batch" with nothing filled in: measured, the three messages
    *Choose a recipe*, *Give the batch a name* and *Choose a brew date* (or yours) show under their
    fields and nothing is sent.

    *Commit:* `src/features/batches/NewBatchDialog.tsx`, `src/features/batches/BatchesPage.tsx`,
    message `Open the new batch dialog from the Batches page`.

11. **Check AC1 and AC2 in the browser, then delete the trial batches.** With no batches, `/batches`
    shows "No batches yet" and the button (AC1). Create a batch named `Trial 1` from a recipe with
    a brew date: the dialog closes and the page shows "Trial 1" at `/batches/<id>`. Press the
    browser's Back button: the list shows `Trial 1` with number, style, date and "Plan" (AC2).
    Click its name: its page opens. Reload that page: the name is still there. Then, in psql as in
    a1-06: `delete from app.batch where name like 'Trial%';`.
    *Why:* these are real batches in the stack's database, and the next batch number is the
    highest plus one, so leftover trials would push your first real batch's number up
    (`app/README.md`).
    *Check yourself:* after the delete, `/batches` shows "No batches yet" again.

    No commit.

12. **Check AC3 against the real API.** The Zod schema stops every 400 the API would send, so to
    see a real one, take the `resolver` line out of `useForm` for a moment. Pick a recipe and a
    date, type only spaces as the name, and press Create.
    *Why:* this proves your mapping works with the API's real answer, not only with the fake one
    the test lesson uses: the PascalCase key, the problem content type, the message.
    While the line is out, `npm run typecheck` reports `zodResolver` and `newBatchSchema` as
    unused; the dev server does not type-check, so the page still runs.
    *Check yourself:* *The Name field is required.* (the API's message, measured with curl) shows
    under Name, in red, and the dialog stays open. Put the `resolver` line back; `git diff` shows
    nothing in the form.

    No commit.

13. **Check AC4 at phone width.** F12, the device toolbar (Ctrl+Shift+M), width 375. Look at the
    list with at least one batch (create a `Trial` one and delete it afterwards as in step 11),
    then open the dialog.
    *Check yourself:* the list shows cards, not the table; the dialog fills the screen with the
    form at the top; the recipe line is cut off inside the select rather than widening the page.
    In the console, `document.documentElement.scrollWidth` prints `375` with the dialog open
    (measured), and the same on the list. If it is wider, find the element with the browser's
    inspector: usually a long word needing `min-w-0` or `break-words`.

    No commit.

14. **Prove the generated files are unedited.**
    `npx shadcn@latest add table dialog field input native-select label separator --diff`.
    *Why:* the a1-01 rule: `src/components/ui/` holds the CLI's files as written; your changes go
    through `className` (10c).
    *Check yourself:* every file says *No changes.*

    No commit.

15. **Run every check and ask for a review** (say "review a1-07").
    *Watch out:* `npm run build` now prints *(!) Some chunks are larger than 500 kB after
    minification.* (measured: 532 kB, up from 391 kB, mostly Zod and React Hook Form). It is a
    warning, not a failure: the build finishes and the hook passes. Splitting the bundle matters
    for a site loaded over the internet, not for an app on your LAN and later inside Tauri.
    *Check yourself:* the list under "Before you ask for a review" is all ticked.

## Files you will touch

- `app/web/package.json`, `app/web/package-lock.json` — `react-hook-form`, `zod`,
  `@hookform/resolvers`.
- `app/web/src/components/ui/{table,dialog,field,input,native-select,label,separator}.tsx` — new,
  written by `shadcn add`, unedited.
- `app/web/src/features/batches/api.ts` — new: the hand-written API types, the error class, the
  three fetch functions, `useBatches`, `useBrewableRecipes`, `useCreateBatch`.
- `app/web/src/features/batches/BatchList.tsx` — new: the table (wide) and the cards (narrow).
- `app/web/src/features/batches/BatchesPage.tsx` — the list with its states, and the New batch
  button.
- `app/web/src/features/batches/BatchPage.tsx` — new: the placeholder at `/batches/:id`.
- `app/web/src/features/batches/NewBatchForm.tsx` — new: the Zod schema and the form.
- `app/web/src/features/batches/NewBatchDialog.tsx` — new: the button, the dialog, closing and
  navigating after a create.
- `app/web/src/App.tsx` — the `batches/:id` route.

## Before you ask for a review

- [ ] AC1: with no batches, `/batches` shows "No batches yet" and the New batch button.
- [ ] AC2: creating a batch opens `/batches/<id>` with its name; Back shows it in the list; a
      reload of its page still shows the name.
- [ ] AC3: with the resolver taken out for a moment, a name of spaces shows the API's *The Name
      field is required.* under Name (and the resolver is back).
- [ ] AC4: at 375 px the list is cards, the dialog fills the screen, and
      `document.documentElement.scrollWidth` is 375 for both.
- [ ] The trial batches are deleted: `/batches` shows "No batches yet".
- [ ] `npm run lint`, `npm run typecheck`, `npm test -- --run`, `npm run build` and
      `npx prettier . --check` pass.
- [ ] `npx shadcn@latest add … --diff` (step 14) says *No changes.* for each file.
- [ ] Only `api.ts` mentions an `/api/...` path; no component calls `fetch`.
- [ ] No `useEffect` in `src/features/batches/` (`grep -rn useEffect src/features/batches`).
- [ ] The browser console shows no React warning.
- [ ] Every step is committed: `git status` shows nothing of this ticket left uncommitted, and
      `git log --oneline main..` lists your step commits.
- [ ] Could you add a fourth field to the form by touching only the schema, the field markup and
      the `fieldNames` lookup?
