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

*Changed 2026-11-26, at your request:* steps 4 to 10 are written in more detail: smaller
sub-steps, the markup of each component described piece by piece, every Tailwind class
explained, and a measured check for the mistakes beginners make (including the ones you met in
steps 4 to 6). The step numbers are the same, and your commits so far are kept; step 4 says how
to commit the finished fetch functions.

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
   their hooks, in `src/features/batches/api.ts` (`.ts`: no JSX in this file).

   **Read first (about 30 minutes, in this order).**
   - Your own `src/features/health/useHealth.ts`. This step is that file written twice, with
     different types and URLs. Keep it open beside you.
   - [TypeScript — Everyday Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html):
     "Arrays", "Object Types", "Union Types" and "Literal Types". Look for how `string | null` and
     an array of objects are written.
   - [MDN — Nullish coalescing (`??`)](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing)
     and [Optional chaining (`?.`)](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Optional_chaining):
     the first example of each. Later steps use both.

   **4a. The status type.** An exported `type BatchStatus`. Syntax: `export type`, the name, `=`,
   then the seven values, each in single quotes, separated by `|`: `plan`, `prep`, `brew_day`,
   `ferment`, `condition`, `package`, `done`. Spell them exactly as the database does (`brew_day`
   with an underscore).
   *Why:* a union of exact strings, like `ApiStatus` in a0-03. A variable of this type can only
   hold one of the seven, and step 5's labels can be a `Record<BatchStatus, string>` that the type
   check keeps complete.

   **4b. The batch summary type.** An exported `type BatchSummary`, an object type (curly braces,
   one `name: type;` per line) with these seven fields, named exactly as the JSON names them:
   - `id`: `number`
   - `number`: `number`
   - `name`: `string`
   - `styleCode`: `string`
   - `styleName`: `string | null`
   - `brewDate`: `string`
   - `status`: `BatchStatus`

   *Why:* `response.json()` is typed `any` (a0-04); this type is where you say what the API sends.
   If a field is missing here, TypeScript refuses `batch.name` later, which is how your missing
   `name` and `styleCode` showed up. `styleName` can be `null` because the API's `StyleName` is a
   `string?` (a style can lack a name), and the `| null` makes the compiler stop you from using it
   as a string without checking. `brewDate` stays a string on purpose: it is a *calendar date*, a
   day, not a moment in time (SYSTEM.md §9); step 5c says why turning it into a `Date` goes wrong.

   **4c. The brewable recipe type.** An exported `type BrewableRecipe` with these nine fields:
   - `id`: `number`
   - `styleCode`: `string`
   - `styleName`: `string | null`
   - `og`, `fg`, `abv`, `ibu`: `number | null` each (the API's `decimal?`)
   - `batchL`: `number`
   - `createdAt`: `string`

   *Why:* the dropdown (step 9) needs `id` as each option's value and the style to name the
   option and fill the batch name. Writing the whole shape now makes a2-02's switch to generated
   types a plain swap.

   **4d. The signature of `fetchBatches`.** A function that is **not** exported (only this file
   uses it), written like `fetchHealth`'s first line: the keyword `async`, `function`, the name
   `fetchBatches`, empty brackets, a colon, and the **return type** `Promise<BatchSummary[]>`.
   Then the body in curly braces.
   *Why:* `Promise<BatchSummary[]>` reads "a promise that will give an array of batch summaries"
   (`[]` after a type means "an array of"). It is a *type*, so it goes after the colon, where
   types go, never after `return`. `async` is what makes the function hand back a promise and
   allows `await` inside it.
   *Watch out:* `return Promise<BatchSummary[]>;` in the body is valid TypeScript, and it is a
   trap: it returns `Promise` itself, the built-in that *makes* promises, not a promise of
   batches. Nothing complains in `api.ts`. Measured, the error appears only where the data is
   used, as a long message about *`new(executor: (resolve: …`* and *`readonly [Symbol.species]:
   PromiseConstructor`*: that is the type of the `Promise` constructor.

   **4e. Ask the API.** The first line of the body: a `const` named `response`, `=`, `await`,
   and a call to `fetch` with the text `'/api/batches'`.
   *Why:* `fetch` returns a promise of a response; `await` waits for it and gives you the
   response itself (a0-04). The path starts with `/` and has no host: Vite's proxy sends it to the
   API (a0-04).
   *Watch out:* without `await`, `response` is the promise, not the response. Measured: *Property
   'ok' does not exist on type 'Promise<Response>'.*

   **4f. Fail on an error status.** An `if` whose condition is `!response.ok`, and whose body
   throws a `new Error(…)` with a template literal that says what failed and includes
   `response.status` (for example "Loading batches failed: 502").
   *Why:* `fetch` treats a 500 or 502 as a normal answer; throwing is how TanStack Query learns
   the request failed, so `isError` becomes true and step 6 can show the message.

   **4g. Return the data.** `return response.json();` as the last line.
   *Why:* `json()` reads the body and turns it into objects. The return type from 4d tells
   TypeScript to treat them as `BatchSummary[]`.
   *Check yourself:* the failing check is expected until 4i: typecheck says *'fetchBatches' is
   declared but its value is never read.*

   **4h. `fetchBrewableRecipes`.** The same four parts again: `async`, the name
   `fetchBrewableRecipes`, return type `Promise<BrewableRecipe[]>`, a fetch of
   `'/api/recipes/brewable'`, the `ok` check with its own message, `return response.json()`.
   *Why:* two plain functions, not one generic `fetchJson<T>(url)`: two copies of four lines are
   easier to read than a helper with a type parameter (C7).

   **4i. The two hooks.** Two exported functions, each shaped exactly like `useHealth` without
   the retry options:
   - `useBatches()`: returns `useQuery` with `queryKey: ['batches']` and `queryFn: fetchBatches`;
   - `useBrewableRecipes()`: returns `useQuery` with `queryKey: ['recipes', 'brewable']` and
     `queryFn: fetchBrewableRecipes`.

   The function name is passed **without** round brackets: you hand TanStack Query the function,
   and it calls it. Import `useQuery` by name from `'@tanstack/react-query'` at the top.
   *Why:* name the hook for what it returns: `useBrewableRecipes`, not `useBrewableBatches`. No
   retry options: these lists want the library's patient defaults (a0-04, "Settings for one query
   live on that query"). Query keys are arrays so they can be *hierarchical*:
   `['recipes', 'brewable']` is "the brewable part of recipes", and when M4 adds `['recipes']`,
   invalidating `['recipes']` refreshes both. The key `['batches']` matters in step 8: it is the
   name the mutation uses to mark the list stale.
   Docs: [TanStack Query — Query keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys),
   "Array keys with variables".
   *Check yourself:* `npm run typecheck` and `npm run lint` pass. Nothing calls the hooks yet; an
   unused export breaks no check.

   *Commit:* `src/features/batches/api.ts`, message `Add the batch list types and queries`.
   (If you already committed step 4 with the placeholder functions, commit this as
   `Fetch the batch and recipe lists`.)

5. **Write `BatchList`**, the table and the cards, in `src/features/batches/BatchList.tsx`.

   **Read first (about 45 minutes, in this order).** These pages are the ground rules of JSX, the
   HTML-like syntax inside your components. Every step from here uses them.
   - [react.dev — Writing Markup with JSX](https://react.dev/learn/writing-markup-with-jsx): the
     whole page. Look for "The Rules of JSX": one root element, close every tag, `className` not
     `class`.
   - [react.dev — JavaScript in JSX with Curly Braces](https://react.dev/learn/javascript-in-jsx-with-curly-braces):
     "Where to use curly braces". Text without braces is shown as it is; braces run JavaScript.
   - [react.dev — Your First Component](https://react.dev/learn/your-first-component): "Step 3:
     Add markup" and the pitfall under it about `return` and round brackets.
   - [react.dev — Passing Props to a Component](https://react.dev/learn/passing-props-to-a-component):
     "Step 2: Read props inside the child component".
   - [react.dev — Rendering Lists](https://react.dev/learn/rendering-lists): "Rendering data from
     arrays" and "Keeping list items in order with `key`". Look at the arrow function with round
     brackets inside `map`.
   - [shadcn — Table](https://ui.shadcn.com/docs/components/base/table): "Usage". Your table is
     that example with your columns.
   - [Tailwind — display](https://tailwindcss.com/docs/display): `hidden`, `block`, `table`.

   **5a. The file and its imports.** Create the file. At the top, three imports:
   - `Link` by name from `'react-router'`;
   - `Table`, `TableBody`, `TableCell`, `TableHead`, `TableHeader` and `TableRow` by name from
     `'@/components/ui/table'`;
   - `BatchStatus` and `BatchSummary` from `'./api'`, as a type-only import (`import type`,
     a0-04: they are types, so the line disappears from the JavaScript).

   *Check yourself:* lint and typecheck report the imports as unused. Expected until 5i uses them.

   **5b. The status labels.** Below the imports, outside any function, a `const statusLabels`
   with the type `Record<BatchStatus, string>`, and as its value an object with seven entries:
   `plan: 'Plan'`, `prep: 'Prep'`, `brew_day: 'Brew day'`, `ferment: 'Ferment'`,
   `condition: 'Condition'`, `package: 'Package'`, `done: 'Done'`.
   *Why:* the database's codes are for code; the screen shows words. Outside the component
   because it never changes (a1-02's `menuItems`). The `Record` is the safety net from a0-03:
   measured, leave out `done` and typecheck says *Property 'done' is missing in type '{ plan:
   string; … package: string; }' but required in type 'Record<BatchStatus, string>'.* When M3 adds
   a status, the compiler sends you here.

   **5c. The style text.** Below the labels, a small function `styleText(batch: BatchSummary):
   string` that returns the style code alone when `styleName` is `null`, else the code, a space
   and the name. One `return` with a *conditional (ternary) operator*: a condition, `?`, the value
   when true, `:`, the value when false. Build the "code and name" text with a template literal.
   *Why:* the style is shown twice, in the table and in the cards (5k). One function means one
   rule; change it once. Test `batch.styleName` on its own, compared with `null` by `===`.
   *Watch out:* `batch.styleCode + batch.styleName === null ? …` does not do what it reads like.
   `+` runs before `===`, so it joins the two strings and then asks whether the joined text is
   `null`, which it never is. Measured, lint catches it: *Unexpected constant binary expression.
   Compares constantly with the right-hand side of the `===`.*
   Docs: [MDN — Conditional (ternary) operator](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Conditional_operator).
   *Watch out:* the brew date is a different story; show it as the API sends it. `new Date('2026-12-05')`
   reads a date-only string as midnight **UTC**, and showing it in local time can move it to the
   day before. Measured with Node: in New York, `new Date('2026-12-05').toLocaleDateString('en-GB')`
   prints *04/12/2026*; in Budapest it prints *05/12/2026*.

   **5d. The props and the signature.** A `type BatchListProps`, an object type with one field,
   `batches`, of type `BatchSummary[]`. Then `export function BatchList({ batches }:
   BatchListProps)`, the shape of `MainMenu`'s signature.
   *Why:* `BatchList` only draws what it is given; it does not fetch. That is the
   **container/presentational** split: the page (step 6) owns the query and its loading and error
   states, the list only knows how a batch looks. A list that fetched by itself would need those
   states too, and could not be drawn with made-up batches in a test. The curly braces in the
   parameter pick the `batches` prop out of the props object (destructuring, a1-02).

   **5e. The return and the fragment.** The body is one `return`. Directly after the word
   `return`, **on the same line**, an opening round bracket; on the next line a fragment, `<>`;
   later the closing `</>` and the closing bracket. Between `<>` and `</>` go two things, the
   table (5f) and the cards (5j).
   *Why:* a component returns **one** value, and the table and the list of cards are two siblings.
   A fragment groups them without adding an element to the page (a `<div>` would also work, but
   adds a box you would have to style). The round bracket must start on the `return` line:
   JavaScript ends a statement at a line break when the line already makes sense on its own, and
   a bare `return` makes sense.
   *Watch out:* two siblings with no parent. Measured: *error TS2657: JSX expressions must have
   one parent element.*
   *Watch out:* `return` alone on its line with the markup below it. Measured: no error at all
   from typecheck or lint, and the component draws **nothing** (its HTML is empty), because it
   returned `undefined`.
   Docs: [react.dev — Fragment](https://react.dev/reference/react/Fragment).

   **5f. The table's head.** The first child of the fragment, a `Table` with
   `className="hidden md:table"`. Inside it a `TableHeader`, inside that one `TableRow`, and inside
   that five `TableHead`s with the texts No., Name, Style, Brew date, Status.
   *Why:* `hidden` sets `display: none` at every width; `md:table` sets `display: table` from 768 px
   up, so the table only exists on wide screens (mobile-first, a1-02 step 8). `table`, not
   `block`: a table shown as a block loses its column layout. `TableHead` draws a `<th>`, a header
   cell, which screen readers announce for each cell in its column.
   *Watch out:* `md=:table` or any other misspelt class is not an error anywhere; Tailwind simply
   has no such class, so the table never appears. If something does not show, check the class
   spelling first.

   **5g. One row per batch.** After `TableHeader`, a `TableBody`. Inside it, in curly braces,
   `batches.map(…)` with an arrow function that takes one batch (name the parameter `batch`) and,
   in **round** brackets, returns one `TableRow` with `key={batch.id}`.
   *Why:* `map` turns the array of batches into an array of rows, and React draws an array of
   elements one after another. Round brackets after `=>` return what is inside them; curly
   brackets start a function body, where you would need the word `return`. `key` tells React which
   row is which between renders; the batch's `id` is unique and never changes (a1-02 7d).
   *Watch out:* curly brackets after `=>` and no `return`. Measured: *Type 'void[]' is not
   assignable to type 'ReactNode'.*: the arrow returns nothing, so `map` gives an array of
   nothing.
   *Watch out:* no `key`. Typecheck and lint pass; measured, the browser console (and the test
   output) says *Each child in a list should have a unique "key" prop. Check the render method of
   `TableBody`.*

   **5h. The five cells.** Inside the row, five `TableCell`s, in the header's order:
   - the batch's `number`;
   - the name (5i turns it into a link; put the plain name in for now);
   - `styleText(batch)`;
   - the `brewDate`;
   - the status label: `statusLabels`, then the batch's `status` in square brackets (looking a
     key up in an object by a value, *bracket access*).

   Every value goes in curly braces.
   *Why:* braces switch from markup to JavaScript. Measured: `<TableCell>batch.number</TableCell>`
   without braces shows the text *batch.number* on the page, not 7.
   Docs: [MDN — Property accessors, "Bracket notation"](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Property_accessors#bracket_notation).

   **5i. The name as a link.** In the Name cell, replace the plain name with a `Link`. Its `to`
   prop is a template literal in curly braces: backticks, `/batches/`, then `batch.id` inside
   `${…}`. Its text, between its tags, is the name. Give it `className="font-medium
   hover:underline"`.
   *Why:* a `Link` draws a real `<a href>` (so Tab reaches it, Enter follows it, and a right-click
   can open it in a new tab), but lets the router handle the click without reloading the page
   (a1-02 step 4). The path starts with `/`: a path without it is read relative to the current
   page. `font-medium` makes it look clickable without colour; `hover:underline` is a bonus for a
   mouse, not something you rely on (F1.5: no action needs hover). The link leads to "Page not
   found" until step 7 adds the route; that is expected.
   *Watch out:* double quotes instead of backticks. Measured: the link's `href` becomes the
   literal text *`/batches/${batch.id}`*; only backticks fill in `${…}`.
   Docs: [React Router — Navigating, "Link"](https://reactrouter.com/start/declarative/navigating#link).

   **5j. The cards' list.** The second child of the fragment, after the `Table`: a `<ul>` with
   `className="flex flex-col gap-2 md:hidden"`. Inside it, in curly braces, `batches.map(…)` again,
   returning one `<li>` per batch with `key={batch.id}` and
   `className="rounded-lg border p-3 break-words"`.
   *Why, class by class:* `flex flex-col` stacks the cards vertically; `gap-2` puts 0.5 rem
   *between* them (padding on the `<ul>` would instead push the whole list inwards, out of line
   with the heading above it). `md:hidden` is the table's opposite: shown below 768 px, gone above.
   `border` and `rounded-lg` draw the card's frame, `p-3` keeps the text off the frame.
   `break-words` lets a long name without spaces wrap instead of widening the page (AC4). A
   `<ul>` of `<li>`, because it is a list: a screen reader says "list, 3 items".
   *Watch out:* write `className`, not `class`. Measured: *Type '{ children: Element[]; key:
   number; class: string; }' is not assignable to type 'DetailedHTMLProps<LiHTMLAttributes…'*.
   *Watch out:* both the table and the cards are in the page, and CSS shows one. A test runs
   without CSS (jsdom), so it sees every batch name twice. That is expected; the test lesson shows
   how to look inside one of them.

   **5k. The card's two lines.** Inside each `<li>`, two `<p>`s:
   - the first: a `#`, the batch's `number`, a space, and the same `Link` as in 5i;
   - the second, with `className="text-sm text-muted-foreground"`: `styleText(batch)`, the
     `brewDate` and the status label, separated by ` · ` (a space, a middle dot, a space).

   *Why:* the most important thing (which batch) on the first line, the details smaller and
   greyer on the second, so a list of cards is easy to scan. `text-muted-foreground` is a theme
   colour (a1-01 step 9), so it works in light and dark mode.
   *Watch out:* JSX drops the line break between `{batch.number}` and the `Link` if they are on
   two lines. Measured: the card shows *#7Trial 1*. Write the space as text in braces, `{' '}`,
   after the number.
   *Check yourself:* `npm run typecheck` and `npm run lint` pass. The list is not on any page yet;
   step 6 shows it.

   *Commit:* `src/features/batches/BatchList.tsx`, message `Add the batch list`. Run
   `npm run format` first: the hook checks Prettier's layout and refuses double quotes or
   `{batches}` without spaces.

6. **Show the list on `BatchesPage`.**

   **Read first (about 25 minutes).**
   - [react.dev — Conditional Rendering](https://react.dev/learn/conditional-rendering):
     "Conditional (ternary) operator" and "Logical AND operator (`&&`)", with its pitfall about
     numbers.
   - [react.dev — Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks): "Only call
     Hooks at the top level" and "Only call Hooks from React functions".
   - [TanStack Query — Queries](https://tanstack.com/query/latest/docs/framework/react/guides/queries):
     the list of states (`isPending`, `isError`, `isSuccess`) and the example below it. Your page
     is that example with three changes.

   **6a. The imports.** `useBatches` from `'./api'` and `BatchList` from `'./BatchList'`, both by
   name.

   **6b. Call the hook inside the component.** The first line **inside** `BatchesPage`'s curly
   braces: a `const batches = useBatches();`.
   *Why:* a hook can only run while React is drawing a component (a0-04, "Hooks"). Code at the top
   of a file runs once, when the file is imported, before React draws anything.
   *Watch out:* the call above the function, at the top of the file. Measured: lint says *React
   Hook "useBatches" cannot be called at the top level.*, and every test in `App.test.tsx` fails
   with *TypeError: Cannot read properties of null (reading 'useContext')*: the hook looks for the
   `QueryClient`, and outside a component there is none.
   *Watch out:* the call inside an `if`, or after an early `return`. Measured: *React Hook
   "useBatches" is called conditionally. React Hooks must be called in the exact same order in
   every component render.*

   **6c. What `batches` holds.** Not the batches: the **query result**, an object that describes
   the request. The fields you use: `isPending` (no answer yet), `isError` and `error` (it failed,
   and why), `isSuccess` and `data` (it worked, and the array). Only `data` is the array that
   `BatchList` wants, and only once `isSuccess` is true.
   *Watch out:* `<BatchList batches={batches} />` passes the whole result. Measured: *Type
   'UseQueryResult<…>' is not assignable to type 'BatchSummary[]'*, followed by *is missing the
   following properties from type 'BatchSummary[]': length, pop, push, concat, and 35 more.*: a
   query result is not an array.

   **6d. The page's frame.** Return (round bracket on the `return` line, 5e) one `<div>` with
   `className="flex flex-col gap-4"`. Its first child: a `<div>` with
   `className="flex items-center justify-between gap-2"` holding your existing `<h1>`.
   *Why:* the outer `div` stacks the header row and the list with 1 rem between them. The header
   row puts its children side by side (`flex`), centred vertically (`items-center`), pushed to the
   two ends (`justify-between`); step 10 puts the New batch button at its right end.

   **6e. Loading.** After the header row, in curly braces: `batches.isPending`, `&&`, and a `<p>`
   with "Loading batches…".
   *Why:* `a && b` gives `b` when `a` is true and `false` otherwise, and React draws nothing for
   `false`. So the line shows only while loading. Plain text for now; a2-06 replaces it (F1.6).

   **6f. Error.** The same with `batches.isError` and a `<p>` that says the batches could not be
   loaded, followed by `batches.error.message` in curly braces.
   *Why:* inside the `isError` branch, TypeScript knows `error` is there. Showing the message
   (your text from 4f) tells you which status came back.

   **6g. Success: empty, or the list.** The same with `batches.isSuccess`, but after `&&` a
   ternary, in round brackets: if `batches.data.length === 0`, a `<p>` "No batches yet"; else
   `<BatchList batches={batches.data} />`.
   *Why:* an empty array is a successful answer, not an error and not "loading", so it gets its
   own sentence (AC1). Checking `isSuccess` first is **narrowing**: the query result's type is a
   union of "pending", "error" and "success" shapes, and only the success shape has a `data` that
   is surely an array.
   *Watch out:* `batches.data.length` without the `isSuccess` check. Measured: *'batches.data' is
   possibly 'undefined'.*
   *Watch out:* `{batches.data.length && <BatchList … />}`. Measured: with no batches the page shows
   a *0*. `&&` gives back its left side when that is falsy, and React draws numbers. Compare with
   `=== 0`.
   *Check yourself (AC1, the text):* with the API running, `/batches` shows your trial batch: a
   table on a wide window, a card when the window is narrower than 768 px. Stop the API: after the
   retries (about 7 s, a0-04) the page shows your error sentence; start it again. After step 11's
   delete it shows "No batches yet". `npm test -- --run` passes (measured: the routing tests only
   look at the heading, which is there before the list loads).

   *Commit:* `src/features/batches/BatchesPage.tsx`, message `Show the batches on the Batches page`.
   Add `api.ts` and `BatchList.tsx` to the same commit if they are not committed yet.

7. **Add the batch page placeholder and its route.**

   **Read first (about 15 minutes).**
   - [React Router — Routing, "Dynamic Segments"](https://reactrouter.com/start/declarative/routing#dynamic-segments)
     and [`useParams`](https://reactrouter.com/api/hooks/useParams), "Basic Usage".
   - [MDN — `Array.prototype.find()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/find):
     the first example. `find` returns the first item the function says yes to, or `undefined`.

   **7a. The file and the id.** `src/features/batches/BatchPage.tsx` with `export function
   BatchPage()`. Its first two lines: `const { id } = useParams();` (`useParams` by name from
   `'react-router'`) and `const batches = useBatches();`.
   *Why:* `useParams` returns an object with one entry per dynamic segment of the route (7e
   writes the route with `:id`); the braces pick `id` out of it. Both hook calls come first, before
   any `return` (6b).

   **7b. Loading and error, as early returns.** An `if` on `batches.isPending` that returns a
   `<p>` "Loading…"; then an `if` on `batches.isError` that returns a `<p>` with the error message.
   *Why:* an *early return* ends the function for the cases that cannot show the page, so the rest
   of the function only deals with the success case. After both `if`s, TypeScript knows `data` is
   there (narrowing, 6g), without wrapping everything in `&&`.

   **7c. Find the batch.** A `const batch` = `batches.data.find(…)` with an arrow function that
   takes one batch (call it `b`) and says whether its id matches `id`.
   *Why:* there is no `GET /api/batches/{id}` yet (a1-09 adds it), and the list already holds the
   name. Reading it from the list, not from data handed over during navigation, means the page also
   works when you reload it or paste its URL (SYSTEM.md §3).
   *Watch out:* every URL parameter is a **string** (or `undefined`), and `id` in the list is a
   number. Measured: *This comparison appears to be unintentional because the types 'number' and
   'string | undefined' have no overlap.* Turn the number into text with `String(…)` before
   comparing.

   **7d. The heading.** Return one `<h1>` with `className="text-2xl font-semibold"` (the same as
   the other pages) and, in curly braces, a ternary: the batch's `name` if `batch` was found, else
   "Batch not found".
   *Why:* `find` gives `undefined` when nothing matches (an old link, a deleted batch), and
   `batch.name` on `undefined` would crash the page.

   **7e. The route.** In `App.tsx`: import `BatchPage`, and inside the layout route, next to the
   `batches` route, a `<Route>` with `path={'batches/:id'}` and `element={<BatchPage />}`.
   *Why:* `:id` is a *dynamic segment*: it matches any one part of the path and hands its value to
   `useParams` under the name after the colon. React Router ranks `batches/:id` above the `*`
   route by itself, so the order of the lines does not matter (a1-02, 5f).
   *Watch out:* forget the route and nothing complains. Measured: the batch's link opens *Page not
   found*.
   *Check yourself:* `/batches/123` shows "Batch not found" with the menu around it; clicking your
   trial batch's name in the list opens its page with its name; a reload keeps it. Typecheck, lint
   and tests pass.

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
     the example is the shape of 8f.

   **8a. The request and response types.** Two exported object types:
   - `CreateBatchRequest`: `recipeId` (`number`), `name` (`string`), `brewDate` (`string`, the
     `"2026-12-05"` form a date input gives and `DateOnly` reads);
   - `CreatedBatch`: `id`, `number` (`number` each) and `name` (`string`).

   *Why:* the 201 answer has more (`BatchResponse` in `BatchEndpoints.cs`, with the copied items),
   but a hand-written type should hold what the UI reads: the `id` to open the page. a1-09 reads
   the full batch from its own endpoint, and a2-02 replaces these types anyway.

   **8b. The problem details type.** An exported `type ProblemDetails` with four **optional**
   fields (a `?` after each name, a1-02 7b): `title` and `detail` (`string`), `status`
   (`number`), and `errors`, a `Record<string, string[]>` (field name → its messages).
   *Why:* RFC 9457 problem details are how the API answers every error (SYSTEM.md §9), and the
   curl output above shows both kinds: with `errors` per field, or with only `detail`. All fields
   optional, because neither kind has all of them.

   **8c. The error class: its first line and field.** `export class ApiProblemError extends
   Error`, then curly braces. As the first line inside: a field declaration, `problem`, a colon,
   `ProblemDetails`, and a semicolon.
   *Why:* a **class** is a template for objects; `extends Error` makes every `ApiProblemError`
   also an `Error`, with a message and a stack trace, so anything that handles errors can handle
   it. The field is where the problem details travel with the error. Throw `Error`s, never plain
   objects: every `catch` and `onError` expects one.
   *Watch out:* many TypeScript examples write the field inside the constructor's brackets
   (`constructor(public problem: …)`). Your `tsconfig.app.json` has `erasableSyntaxOnly` on, which
   forbids that (it generates code). Measured: *error TS1294: This syntax is not allowed when
   'erasableSyntaxOnly' is enabled.*
   Docs: [TypeScript — `erasableSyntaxOnly`](https://www.typescriptlang.org/tsconfig/#erasableSyntaxOnly).

   **8d. The constructor.** Below the field: `constructor(problem: ProblemDetails)` and a body of
   two lines. First `super(…)` with a readable message: the problem's `detail`, else its `title`,
   else a fixed sentence (`??` twice). Then `this.problem = problem;`.
   *Why:* `super(...)` runs `Error`'s own constructor, which stores the message; it must come
   before any use of `this`. Anything that shows only `error.message` gets a sentence; the form
   (step 9) checks `error instanceof ApiProblemError` and reads the per-field messages, and that
   check is also what tells TypeScript the error has a `problem` field.
   *Check yourself:* typecheck passes; the class is exported, so it is not "unused".

   **8e. The POST.** Not exported: `async function createBatch(request: CreateBatchRequest):
   Promise<CreatedBatch>`. Its body, in this order:
   - a `const response` = `await fetch('/api/batches', {…})` with an options object of three
     properties: `method: 'POST'`; `headers`, an object with one entry, `'Content-Type':
     'application/json'` (the key in quotes because it contains a dash); `body:
     JSON.stringify(request)`;
   - an `if`: when `response.headers.get('Content-Type')` is `'application/problem+json'`, throw a
     `new ApiProblemError(await response.json())`;
   - an `if`: when the response is not `ok`, throw a plain `Error` naming the status (as in 4f);
   - `return response.json();`.

   *Why:* `JSON.stringify` turns the object into JSON text, the only thing a body can carry.
   Without the `Content-Type` request header, ASP.NET Core does not read the body as JSON:
   measured, it answers *415 Unsupported Media Type* with an empty body. The problem check comes
   first and looks at the *type* of the answer, not only the status: that 415, or a 502 from
   Vite's proxy when the API is stopped, has no problem JSON, and reading one would fail with a
   confusing parse error instead of your message.

   **8f. The mutation hook.** Exported `useCreateBatch()`. Its first line gets the cache:
   `const queryClient = useQueryClient();` (by name from `'@tanstack/react-query'`). Then it
   returns `useMutation({…})` with two properties: `mutationFn: createBatch`, and `onSuccess`, an
   arrow function with no parameters that returns
   `queryClient.invalidateQueries({ queryKey: ['batches'] })`.
   *Why:* a **mutation** is TanStack Query's name for a request that *changes* server data. Unlike
   a query it does not run by itself: it gives you a `mutate` function to call (on submit), and
   tracks that call's `isPending`, `error` and `data`. After a batch is created the cached list is
   out of date. *Invalidating* the `['batches']` key marks it stale and fetches it again at once
   while something shows it. Returning that promise from `onSuccess` makes the mutation wait for
   the refetch before it counts as done, so when the form navigates (step 10) the list in the
   cache already holds the new batch. Measured without the invalidation: the new batch's page
   first shows *Batch not found*, then its name a moment later. This callback lives on the hook
   because every caller wants it; the navigation does not (9k).
   *Check yourself:* `npm run typecheck` and `npm run lint` pass. Still unused; step 9 calls it.

   *Commit:* `src/features/batches/api.ts`, message `Add the create-batch mutation`.

9. **Write `NewBatchForm`**, in `src/features/batches/NewBatchForm.tsx`, in small steps.

   **Read first (about 60 minutes, in this order).**
   - [Zod — Basic usage](https://zod.dev/basics): "Defining a schema", "Parsing data", "Inferring
     types".
   - [Zod — Defining schemas](https://zod.dev/api): "Strings" (`.trim()`, `.min()`), "Numbers",
     "ISO dates" and "Objects".
   - [Zod — Customizing errors](https://zod.dev/error-customization): "The `error` param", the
     first two examples.
   - [React Hook Form — Get started](https://react-hook-form.com/get-started): the first example,
     then "Register fields", "Handle errors" and "Schema Validation". Look at how `register` sits
     on each `<input>`.
   - [React Hook Form — `register`](https://react-hook-form.com/docs/useform/register): the
     options table, `valueAsNumber` and `onChange` in particular.
   - [React Hook Form — `handleSubmit`](https://react-hook-form.com/docs/useform/handlesubmit) and
     [`setError`](https://react-hook-form.com/docs/useform/seterror): the "server error" examples.
   - [React Hook Form resolvers — Zod](https://github.com/react-hook-form/resolvers#zod): the
     example is the shape of 9c.
   - [shadcn — React Hook Form](https://ui.shadcn.com/docs/forms/react-hook-form): how `Field`,
     `FieldLabel` and `FieldError` sit around an input, and `data-invalid` / `aria-invalid`. Its
     examples wrap every input in `Controller`; you use `register` instead (9e says why).
   - [MDN — Spread syntax, "Spread in object literals"](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Spread_syntax#spread_in_object_literals):
     `{...something}` in JSX does the same with props.
   - [MDN — `<input type="date">`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/date),
     "Value": always `yyyy-mm-dd`, whatever the browser shows.

   **9a. The imports.** By name: `useForm` from `'react-hook-form'`; `zodResolver` from
   `'@hookform/resolvers/zod'`; `z` from `'zod'`; `Button` from `'@/components/ui/button'`;
   `Field`, `FieldError`, `FieldGroup`, `FieldLabel` from `'@/components/ui/field'`; `Input` from
   `'@/components/ui/input'`; `NativeSelect`, `NativeSelectOption` from
   `'@/components/ui/native-select'`; and from `'./api'`: `ApiProblemError`, `useBrewableRecipes`,
   `useCreateBatch`, plus the types `BrewableRecipe` and `CreatedBatch` (a `type` word in front of
   each type inside the braces).
   *Check yourself:* all reported unused for now; each later sub-step uses some.

   **9b. The schema.** Below the imports, a `const newBatchSchema = z.object({…})` with three
   keys, mirroring the API's rules:
   - `recipeId`: `z.number(…)` with a message for "nothing picked" as its argument, for example
     `'Choose a recipe'`;
   - `name`: `z.string()`, then `.trim()`, then `.min(1, …)` with a message;
   - `brewDate`: `z.iso.date(…)` with a message.

   *Why:* the API's three `[Required]` rules, checked before the request is sent, so the usual
   mistakes are shown at once without a round trip. `.trim()` then `.min(1)` mirrors exactly what
   `[Required]` does to a string (measured: a name of spaces gets *The Name field is required.*),
   and it also trims the name you send. `z.iso.date()` accepts only a real `yyyy-mm-dd` date, the
   form `DateOnly` reads; an empty date input gives `''`, which fails it. Each schema function
   takes its message as its argument (a string), or an object with an `error` key.

   **9c. The values type.** `type NewBatchValues = z.infer<typeof newBatchSchema>`.
   *Why:* `typeof` on a value gives its type; `z.infer` turns a schema's type into the type of the
   data it accepts: here `{ recipeId: number; name: string; brewDate: string }`. The rules and the
   type come from one place. Hover the name in your editor to see it.

   **9d. The recipe's label.** A function `recipeLabel(recipe: BrewableRecipe): string` that
   returns one line, built from four parts joined with ` · `:
   - the style name, or the code when there is no name (`??`);
   - "OG " and the OG with three decimals (`toFixed(3)`), or a dash when it is `null`;
   - the ABV with a `%`, or a dash;
   - the date part of `createdAt` as a local date: `new Date(…)` of it, then
     `.toLocaleDateString()`.

   *Why:* the ticket asks for style, OG, ABV and date, so recipes of the same style can be told
   apart. `createdAt` is a UTC moment (the `Z`), so `new Date` reads it right, and showing it in
   local time is what SYSTEM.md §9 asks; the brew date in 5c was the other case. Measured:
   `1.0481` shows as *1.048*, and a whole option reads *Weissbier · OG 1.048 · 4.9% · 11/4/2026*
   (the date follows the browser's language). A function, not inline in the markup, so the option
   stays readable.

   **9e. The props, signature and hooks.** A `type NewBatchFormProps` with one field, `onCreated`:
   a function type (brackets with one parameter, `batch: CreatedBatch`, an arrow `=>`, then
   `void`). Then `export function NewBatchForm({ onCreated }: NewBatchFormProps)` and, as its
   first lines:
   - `const recipes = useBrewableRecipes();`
   - `const createBatch = useCreateBatch();`
   - `const form = useForm<NewBatchValues>({…})` with two properties: `resolver:
     zodResolver(newBatchSchema)` and `defaultValues: { name: '', brewDate: '' }`;
   - `const errors = form.formState.errors;`, a short name for what the fields show.

   *Why:* the **callback prop** pattern from a1-02's `onNavigate`: the form does not know it sits
   in a dialog or what happens after a create; it reports "created this batch" and the dialog
   decides (step 10). The `resolver` makes React Hook Form ask Zod on submit. `defaultValues`
   gives each text input a starting value, so React Hook Form knows when a field has been changed
   (*dirty*), which 9l relies on. `recipeId` gets none: an empty choice is the start. All the hook
   calls first, before anything else (6b).

   **9f. The form element.** Return (round bracket on the `return` line) a `<form>` whose
   `onSubmit` is `form.handleSubmit(onSubmit)`, holding one `FieldGroup`. Above the `return`, a
   function `onSubmit(values: NewBatchValues)` with an empty body for now (9k fills it).
   *Why:* `handleSubmit` stops the browser's own submit (which would reload the page), runs Zod,
   and calls your `onSubmit` only with valid, already trimmed values. `FieldGroup` stacks the
   fields with even spacing.
   *Watch out:* `onSubmit={onSubmit}` without `handleSubmit`. Measured: *Type '(values: {
   recipeId: number; name: string; brewDate: string; }) => void' is not assignable to type
   'SubmitEventHandler<HTMLFormElement>'.*: the browser would hand your function an event, not
   the values.

   **9g. The recipe field: its frame and label.** Inside the `FieldGroup`, a `Field` with
   `data-invalid={!!errors.recipeId}`. In it, a `FieldLabel` with `htmlFor="recipeId"` and the
   text "Recipe".
   *Why:* `Field` lays out a label, a control and an error, and turns red when `data-invalid` is
   true. `errors.recipeId` is an object when there is an error and `undefined` when not; `!!`
   (two "not"s) turns that into `true` or `false`. `htmlFor` is JSX's name for HTML's `for`: it
   ties the label to the control whose `id` matches, so clicking the label focuses the select, and
   a screen reader (and a test's `getByLabelText('Recipe')`) finds the select by its label.
   *Watch out:* an `htmlFor` that does not match the control's `id` breaks nothing on screen.
   Measured, a test then says *Found a label with the text of: Name, however no form control was
   found associated to that label.*

   **9h. The select.** After the label, a `NativeSelect` with `id="recipeId"`,
   `className="w-full"`, `aria-invalid={!!errors.recipeId}`, and the result of
   `form.register('recipeId', { valueAsNumber: true })` spread onto it: curly braces, three dots,
   the call.
   *Why:* `register` returns four props (`name`, `ref`, `onChange`, `onBlur`); spreading puts all
   four on the `<select>` at once. That is how React Hook Form reads and watches an input it does
   not control, and it works on anything that behaves like a real input, which is why
   `NativeSelect` needs no `Controller`. A `<select>`'s value is always a string; `valueAsNumber`
   makes React Hook Form hand Zod a number (and `NaN` for the empty option, which `z.number()`
   rejects with your message). `w-full`: the generated component is only as wide as its text
   (`w-fit`); the class makes it fill the dialog. `aria-invalid` tells assistive tech the field is
   wrong and gives it the red border.
   *Watch out:* forget `valueAsNumber` and the type check is happy, but the form never submits:
   measured, after picking a recipe and pressing Create, the field still says *Choose a recipe*,
   because Zod got the string `"1"` and wants a number.

   **9i. The options.** Inside the `NativeSelect`: first a `NativeSelectOption` with `value=""`
   whose text is "Loading recipes…" while `recipes.isPending` and "Choose a recipe" otherwise (a
   ternary). After it, in curly braces, `recipes.data?.map(…)` returning one `NativeSelectOption`
   per recipe, with `key` and `value` its `id` and `recipeLabel(recipe)` as its text. After the
   `NativeSelect`, still inside the `Field`: `<FieldError errors={[errors.recipeId]} />`.
   *Why:* the empty first option is what a new form starts on, so "nothing picked" is a real
   state Zod can reject. `?.` because `data` is `undefined` until the recipes arrive; then the
   `map` simply draws no options yet. `FieldError` draws the message, or nothing when there is no
   error. It takes an **array** of errors, because some fields have several.
   *Watch out:* `errors={errors.name}` without the square brackets. Measured: *Type 'FieldError |
   undefined' is not assignable to type '({ message?: string | undefined; } | undefined)[] |
   undefined'.*

   **9j. The name and brew date fields.** Two more `Field`s built like 9g to 9i:
   - "Name": an `Input` with `id="name"`, `aria-invalid`, and `form.register('name')` spread on it;
   - "Brew date": an `Input` with `id="brewDate"`, `type="date"`, `aria-invalid`, and
     `form.register('brewDate')` spread on it;

   each with its `FieldLabel` and `FieldError`. After them, still in the `FieldGroup`: a `Button`
   with `type="submit"`, `disabled={createBatch.isPending}` and the text "Create batch".
   *Why:* `type="date"` gives every browser and phone its own date picker and always yields
   `yyyy-mm-dd`, the shape the API and `z.iso.date()` want; no date library needed. A button of
   type `submit` inside a `<form>` submits it, by click or by Enter in a field. Disabling it while
   the request runs stops a double click from creating two batches.
   *Check yourself:* typecheck and lint pass except the empty `onSubmit`'s unused `values`
   (expected until 9k). The form is not on screen until step 10.

   **9k. Submit.** Fill in `onSubmit`: one call, `createBatch.mutate(values, {…})`, with two
   properties in the object: `onSuccess: onCreated` (the prop itself, no brackets) and `onError`,
   an arrow function that takes `error` (9l writes its body).
   *Why:* `mutate` starts the request. The callbacks passed to `mutate` (rather than to
   `useMutation`) belong to this one call, which is the place for what only this form does: report
   the new batch, place the errors. TanStack Query runs them only while the form is still on
   screen. `onSuccess` receives the `CreatedBatch` from `createBatch`, which is exactly what
   `onCreated` takes, so it can be passed as it is.

   **9l. The server's errors.** First, above the component, a lookup: a `const fieldNames` with
   the type `Partial<Record<string, keyof NewBatchValues>>` and three entries: `RecipeId:
   'recipeId'`, `Name: 'name'`, `BrewDate: 'brewDate'`. Then the body of `onError`, in words:
   - if `error` is an `ApiProblemError` (`instanceof`) **and** its `problem.errors` is there:
     for each `[key, messages]` pair of `Object.entries(error.problem.errors)` (a `for…of` loop),
     call `form.setError(…)` with the field from `fieldNames[key]`, or `'root.server'` when the
     lookup gives `undefined` (`??`), and `{ message: … }` with the messages joined by a space;
   - otherwise: `form.setError('root.server', { message: error.message })`.

   Then, in the markup, between the last `Field` and the `Button`: when `errors.root?.server` is
   there (`&&`), a `<p>` with `role="alert"`, `className="text-sm text-destructive"` and the
   error's `message`.
   *Why:* this is AC3. The API sends **PascalCase** keys (measured above) and your fields are
   camelCase, so a lookup translates them. `keyof NewBatchValues` is the union of the form's field
   names, so a typo is caught (measured: *Type '"brewdate"' is not assignable to type '"name" |
   "recipeId" | "brewDate" | undefined'. Did you mean '"brewDate"'?*). `Partial` makes the lookup
   of an unknown key typed as possibly `undefined`, which is true, and `?? 'root.server'` handles
   it. `Object.entries` turns an object into an array of `[key, value]` pairs, and the square
   brackets in the `for` pick each pair apart. `root.server` is React Hook Form's place for a
   form-wide error, not tied to a field; `role="alert"` makes a screen reader read it out when it
   appears; `text-destructive` is the theme's error red. A field error you set is cleared on the
   next submit, so the user can fix the field and try again (measured).
   *Watch out:* passing the API's key straight in. Measured with `setError('Name', …)`: *Argument
   of type '"Name"' is not assignable to parameter of type '"name" | "recipeId" | "brewDate" |
   ErrorNamespacePath'.*
   *Watch out:* reading `error.problem` without the `instanceof` check. Measured: *Property
   'problem' does not exist on type 'Error'.* The check is what narrows the type.
   Docs: [MDN — `Object.entries()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/entries),
   [`for...of`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/for...of),
   [TypeScript — `keyof`](https://www.typescriptlang.org/docs/handbook/2/keyof-types.html),
   [`Partial`](https://www.typescriptlang.org/docs/handbook/utility-types.html#partialtype).

   **9m. The name follows the recipe.** In the recipe's `register` call, next to `valueAsNumber`,
   add an `onChange` option: an arrow function that takes the change `event` and
   - finds the picked recipe: `recipes.data?.find(…)`, comparing each recipe's `id` with
     `Number(event.target.value)`;
   - if one was found and the name is not dirty (`!form.getFieldState('name').isDirty`), calls
     `form.setValue('name', …)` with the recipe's style name, or its code (`??`).

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
    - Your own `AppLayout.tsx`: the `Sheet` there is the same shape as this dialog (a1-02 step 10).
    - [React Router — `useNavigate`](https://reactrouter.com/api/hooks/useNavigate): "Navigate to
      another path".

    **10a. The file, imports and state.** `src/features/batches/NewBatchDialog.tsx` with
    `export function NewBatchDialog()`, no props. Imports by name: `useState` from `'react'`,
    `useNavigate` from `'react-router'`, `Button`, the dialog pieces `Dialog`, `DialogContent`,
    `DialogHeader`, `DialogTitle`, `DialogTrigger` from `'@/components/ui/dialog'`, and
    `NewBatchForm` from `'./NewBatchForm'`. First lines of the body: `useState(false)`
    destructured into `open` and `setOpen` (as `menuOpen` in a1-02), and
    `const navigate = useNavigate();`.
    *Why:* the dialog must close after a successful create, and only your code knows when that
    happened, so it is **controlled**, exactly like the drawer in a1-02 step 10. `useNavigate`
    returns a function that sends the router to a path from code, for the moments where no link is
    clicked (here: after the API answered).

    **10b. The dialog and its trigger.** Return a `Dialog` with `open={open}` and
    `onOpenChange={setOpen}`. Its first child: a `DialogTrigger` with `render={<Button />}` and the
    text "New batch" between its tags.
    *Why:* `render` says "draw the trigger as this element, with the dialog's behaviour added", so
    the button opens the dialog and gets the right ARIA attributes.
    *Watch out:* a `<Button>` between `DialogTrigger`'s tags draws a button inside a button.
    Measured, the console says *In HTML, &lt;button&gt; cannot be a descendant of &lt;button&gt;.*

    **10c. The content.** The second child of `Dialog`: a `DialogContent`, holding a
    `DialogHeader` with a `DialogTitle` "New batch", then `<NewBatchForm />` with an `onCreated`
    prop: an arrow function that takes `batch` and, in curly braces, does two things on two lines:
    `setOpen(false)`, then `navigate(…)` with a template literal for `/batches/` and the batch's
    `id`.
    *Why:* `DialogTitle` names the dialog for screen readers (and tests find it by that name). The
    form sits *inside* `DialogContent`, and Base UI removes the content from the page when the
    dialog closes, so each opening starts with a fresh, empty form, and the recipes are only
    fetched once the dialog first opens. The arrow function is needed because two things happen,
    in your order (a1-02's `onNavigate`).

    **10d. Full screen on narrow screens.** Give `DialogContent` this `className`, class by class:
    - `h-svh`: as tall as the visible screen (a1-02 6b);
    - `max-w-none`: no maximum width, so it spans the screen;
    - `content-start`: the rows of the dialog start at the top;
    - `rounded-none`: square corners, as a full screen has;
    - `sm:h-auto`, `sm:max-w-lg`, `sm:rounded-xl`: from 640 px up, back to a centred box as tall as
      its content, at most 32 rem wide (so the long recipe lines fit), with round corners.

    *Why:* the ticket asks for a full-screen sheet on narrow screens. `dialog.tsx` already has a
    `className` prop and merges it with `cn` (a1-01), and `cn` lets a later class beat an earlier
    one of the same kind, so yours win over the defaults without editing the generated file.
    `content-start`: the dialog lays its children out as a grid, and on a full-height box the grid
    spreads the rows out (measured: the form floats in the middle of the screen without it).
    *Watch out:* the generated default includes `max-w-[calc(100%-2rem)]`; without `max-w-none`
    the "full screen" dialog keeps a gap on both sides.

    **10e. Put it on the page.** In `BatchesPage`, import `NewBatchDialog` and put
    `<NewBatchDialog />` in the header row from 6d, after the `<h1>`.
    *Why:* AC1 asks for the button when there are no batches, and it must not depend on the list
    having loaded: the header row is outside the loading, error and success lines, so the button
    shows in every state.
    *Check yourself:* typecheck, lint and tests pass. In the browser, "New batch" opens the dialog
    with the recipes in the dropdown, Escape closes it, and opening it again shows an empty form.
    Press "Create batch" with nothing filled in: measured, the three messages *Choose a recipe*,
    *Give the batch a name* and *Choose a brew date* (or yours) show under their fields and nothing
    is sent.

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
