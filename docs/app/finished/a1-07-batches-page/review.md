# Review: a1-07 · Batches page and new batch

## Round 1 · 2026-11-28 · aefc8ed

Checks: `npm run lint` ok · `npm run typecheck` ok · `npm test -- --run` ok (11 passed) ·
`npm run build` ok (a chunk-size warning, not an error) · `prettier --check .` ok. No API changes
on the branch, so no `dotnet` checks. Browser checks against the running API (port 5080) and the
dev server (5173).

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | `/batches` with the batches request answering `[]` (fetch replaced in the page): "No batches yet" and the New Batch button. The button also shows with batches in the list. |
| AC2 | **no** | Created "Trial review" from a Weissbier recipe: the POST returned 201, then the app opened `/batchs/4`, which shows *Page not found* (#1). Back showed the batch in the list; `/batches/4` showed its name. The trial batch is deleted. |
| AC3 | **no** | Made the real API answer 400 by changing the request's name to spaces in the page's fetch: the response had `errors: { Name: ["The Name field is required."] }`, and nothing appeared on screen (#2). |
| AC4 | yes | At 375 × 812: the list shows cards, page `scrollWidth` 375. The dialog is 375 × 812 at x 0, `scrollWidth` 375. |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Spec | must fix | `src/features/batches/NewBatchDialog.tsx:26` | The path after a create is spelled `/batchs/`, so a new batch opens *Page not found* (measured). | AC2. Nothing checks the text of a path: typecheck, lint and tests all passed. | [useNavigate](https://reactrouter.com/api/hooks/useNavigate) |
| 2 | Spec | must fix | `src/features/batches/NewBatchForm.tsx:106-119` | The Name and Brew date fields were copied from the Recipe field and still read the recipe's error: `data-invalid` and `FieldError` use `errors.recipeId`, and both labels have `htmlFor` `recipeId`. Measured: an empty submit shows *Choose a recipe* under all three fields; a 400 for Name shows nothing. Each field needs its own key: `name`, `brewDate`. | AC3. The labels also matter beyond looks: clicking "Name" focuses the recipe select. A test's `getByLabelText('Name')` would find the select too, and the test lesson's tests find fields that way. | lesson 9g, 9j |
| 3 | Standards | must fix | `src/features/batches/NewBatchForm.tsx:108`, `:116` | `aria-invalid` written with no value means `true`, always. Measured: Name and Brew date have a red border as soon as the dialog opens. Give it the same `!!errors.…` value as the field's `data-invalid`. | A screen reader announces both fields as invalid before you typed anything, and the red border stops meaning "wrong". In JSX, an attribute with no value is `true`. | [MDN aria-invalid](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-invalid) |
| 4 | Standards | must fix | `src/features/batches/NewBatchForm.tsx:85` | The `onChange` is a JSX prop after the `register` spread, so it replaces React Hook Form's own `onChange`. It belongs in `register`'s options object, next to `valueAsNumber` (lesson 9m). Measured: the browser still submits, because `register`'s `onBlur` records the value when focus leaves the select. But the *Choose a recipe* error stays under a picked recipe until the next submit. In a test that changes the select without a blur, the form never submits. | It works by accident, through the blur. Your component tests (test lesson) change the select and then submit, so they depend on this. Correction to my answer yesterday: I said it would always fail; in a real browser it gets through on blur. | [register, `onChange` option](https://react-hook-form.com/docs/useform/register) |
| 5 | Spec | must fix | `src/features/batches/NewBatchForm.tsx:34-38` | `getDate()` is the day of the month, so every option ends in *4* (measured: *Weissbier·1.048·4.9%·4*). The OG has no "OG " in front of it, and the separator has no spaces around the dot. Lesson 9d: `toLocaleDateString()` on the `Date`, and ` · ` between the parts. | The ticket asks for the date in each option, so two recipes of one style can be told apart; both Weissbier recipes here differ only by date. | [MDN toLocaleDateString](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/toLocaleDateString) |
| 6 | Standards | should fix | `src/features/batches/api.ts:102` | `useBrewableBatches` fetches recipes; name it after what it returns (`useBrewableRecipes`, as the query key and the fetch function already say). | A hook's name is what the next feature's author goes by. "Batches" sends whoever needs the recipes next looking in the wrong place. | |
| 7 | Standards | nice to have | `src/features/batches/BatchesPage.tsx:11` | The heading's classes became `''`, so "Batches" is body-size text. On `main` it had `text-2xl font-semibold`, like every other page. | The pages look alike. | |
| 8 | Standards | nice to have | `src/features/batches/NewBatchForm.tsx:27` | `z.iso.date()` has no message, so an empty date would show Zod's default *Invalid ISO date* (measured with Zod 4.6.7), not your words like the other two fields. | One voice across the form's messages. | lesson 9b |
| 9 | Standards | nice to have | `src/features/batches/NewBatchDialog.tsx:21-29` | The form sits inside `DialogHeader`; lesson 10c puts it after the header, inside `DialogContent`. | The header is for the title (and a description), and its `gap-2` spaces the whole form like a title block. | [shadcn Dialog](https://ui.shadcn.com/docs/components/base/dialog) |

Done well:
- The three loading, error and success states on `BatchesPage`, with the empty list as its own
  sentence and the button outside them, so AC1 holds in every state.
- `ApiProblemError` and the `onError` branch: field errors go to their fields through a typed
  lookup, and anything else goes to `root.server`. Once #2 is fixed, AC3 works with the API's real
  PascalCase answer.
- `BatchList`: the status labels as a `Record<BatchStatus, string>`, so a new status would be a
  type error. The table and card switch at `md` fits AC4, measured.

Verdict: fixes needed

## Round 2 · 2026-11-28 · 8bd3d7a

Checks: `npm run lint` ok · `npm run typecheck` ok · `npm test -- --run` ok (11 passed) ·
`npm run build` ok · `prettier --check .` ok. Browser checks against the running API and dev
server, as in round 1.

Round 1 findings:

| # | Status | How checked |
|---|---|---|
| 1 | fixed | A create opened `/batches/6` with the batch's name. |
| 2 | **partly fixed** | The errors are right: an empty submit shows *Choose a recipe*, *Choose a name*, *Choose a brew date* under their own fields. The labels are not: "Name" and "Brew date" still have `htmlFor` `recipeId` (measured in the page). Now finding 10. |
| 3 | fixed | All three fields have `aria-invalid="false"` when the dialog opens. |
| 4 | fixed | After picking a recipe the *Choose a recipe* error goes away and the name becomes *Weissbier*. |
| 5 | fixed | The option has the OG and a real date: *Weissbier·OG 1.048·4.9%·11/4/2026, 10:18:21 AM*. Its form is finding 11. |
| 6 | fixed | `useBrewableRecipes`. |
| 7 | fixed | `text-2xl font-semibold`. |
| 8 | fixed | *Choose a brew date*. |
| 9 | fixed | The form is after `DialogHeader`. |

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | Unchanged since round 1 (`BatchesPage` only got its heading classes back). |
| AC2 | yes | Created "Trial review": the dialog closed, `/batches/6` showed *Trial review*, Back showed it first in the list with number 4, *10A Weissbier*, *2026-11-28*, *Plan*. The trial batch is deleted. |
| AC3 | yes | The real API's 400 (the request's name changed to spaces in the page's fetch): *The Name field is required.* under Name, the field red, the dialog open. |
| AC4 | yes | Unchanged since round 1; the dialog's classes are the same. |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 10 | Standards | must fix | `src/features/batches/NewBatchForm.tsx:108`, `:117` | The "Name" and "Brew date" labels still point at `recipeId`. Each label's `htmlFor` must be the `id` of its own input: `name`, `brewDate`. | Clicking "Name" focuses the recipe select, a screen reader reads the select as "Name", and the test lesson's tests find each field by its label: `getByLabelText('Name')` would get the select. | lesson 9g |
| 11 | Standards | nice to have | `src/features/batches/NewBatchForm.tsx:37-38` | `toLocaleString()` adds the time of day, and the parts are joined with a bare `·`. Lesson 9d: `toLocaleDateString()` and ` · ` with spaces, so the line reads *Weissbier · OG 1.048 · 4.9% · 11/4/2026*. | The time of day does not help tell two recipes apart, and the bare dots run the parts together. | [MDN toLocaleDateString](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/toLocaleDateString) |

Done well:
- Every round 1 finding got its own small commit with a clear message, so each fix can be read
  alone.
- The recipe's `onChange` now sits in `register`'s options: the name follows the recipe and the
  recipe's error clears as soon as you pick one.

Verdict: fixes needed

## Round 3 · 2026-11-28 · e5c3674

Checks: `npm run lint` ok · `npm run typecheck` ok · `npm test -- --run` ok (11 passed) ·
`npm run build` ok · `prettier --check .` ok.

Earlier findings:

| # | Status | How checked |
|---|---|---|
| 10 | fixed | In the page, each label's `control` is its own input: Recipe → `recipeId`, Name → `name`, Brew date → `brewDate`; the accessibility tree has a textbox named "Name". |
| 11 | fixed | The option reads *Weissbier · OG 1.048 · 4.9% · 11/4/2026*. |

| AC | Met | How checked |
|---|---|---|
| AC1–AC4 | yes | As in round 2; these two commits change only the labels and the option text. |

No new findings.

Done well: both fixes are exactly the change asked for, each in its own commit.

Verdict: ready for tests

# Test review

## Round 1 · 2026-11-28 · d3b6c05

Checks: `npm run lint` ok · `npm run typecheck` ok · `npm test -- --run` ok (15 passed; 4 runs,
15 each) · `npm run build` ok · `prettier --check .` ok. No API changes, so no `dotnet` checks.

| Test | Behaviour (AC) | Broke | Failed? |
|---|---|---|---|
| T1 `lists the batches` | the row shows number, name, style, date, status label (AC2) | `BatchList.tsx`: `batch.status` instead of `statusLabels[batch.status]` in the table | yes: *Unable to find role="row" and name "1 First brew 10A Weissbier 2026-11-28 Brew day"* |
| T2 `shows "No batches yet" …` | the empty sentence and the button (AC1) | `BatchesPage.tsx`: `=== 1` instead of `=== 0` | yes: *Unable to find an element with the text: No batches yet.* |
| T2, the button | | `NewBatchDialog.tsx`: the trigger's text changed to "Add batch" | yes: *Unable to find an accessible element with the role "button" and name "New Batch"* |
| T3 `creates a batch and opens its page` | the request and the new page (AC2) | `NewBatchDialog.tsx`: `/batchs/` in `navigate` | yes: *Unable to find role="heading" and name "Weissbier"* |
| T3, the request | | `NewBatchForm.tsx`: the name follows the style code instead of the style name | yes: *expected { recipeId: 1489, name: '10A', …(1) } to deeply equal { recipeId: 1489, …(2) }* |
| T4 `shows the API's message …` | the 400's message on the Name field (AC3) | `NewBatchForm.tsx`: the `Name: 'name'` line removed from `fieldNames` | yes: *expect(element).toBeInvalid() … Received element is not currently invalid* |

Each break was undone exactly: `git diff` of every file matched what it was before.

Needed and reliable: no duplicates, no test of framework behaviour. No test depends on time,
order or the machine's language: T3 and T4 wait for the recipe option and pick it by value. The
fake API is MSW, no real network.

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Standards | should fix | `src/features/batches/batches.test.tsx:47`, `:101` | Two checks have no matcher. Line 47 is a bare `screen.getByRole(…)`; line 101 is `expect(await screen.findByText(…))` with nothing after it. They catch a missing element only because `getBy` and `findBy` throw. Measured: removing the button still fails T2. Wrap line 47 in `expect(…)`, and give both `.toBeInTheDocument()`, like the line above each. | `expect(x)` alone asserts nothing. The day one of these becomes a `queryBy` (which returns `null` instead of throwing), the test passes with the element gone. With a matcher, each line reads as the check it is. | [jest-dom `toBeInTheDocument`](https://github.com/testing-library/jest-dom#tobeinthedocument) |
| 2 | Standards | nice to have | `src/features/batches/batches.test.tsx:52` | `let sent;` has no type, so TypeScript treats it as `any`. Step 5b gives it `unknown`. | With `any`, a typo like `sent.recipeID` compiles; `unknown` makes you check first. | test lesson 5b |
| 3 | Standards | nice to have | `src/features/batches/batches.test.tsx:86` | *occured*: the real API's title says *occurred*. | The fake 400 is meant to be a copy of the real one (measured with curl). | |

Done well:
- `fillOutCreateBatchForm`: T3 and T4 share the user's steps, so the two tests show only what
  differs, the fake API and the asserts.
- T3 checks both sides of a create: the page the user lands on, and the exact body the API gets.
  The second break above (the name default) is caught only by the body check.
- Every test finds things by role, label or text, the way a person does.

Verdict: ready to ship (finding 1 is worth the two-line fix first)

## Round 2 · 2026-11-28 · 5266efc

Checks: `npm run lint` ok · `npm run typecheck` ok · `npm test -- --run` ok (15 passed) ·
`npm run build` ok · `prettier --check .` ok.

| # | Status | How checked |
|---|---|---|
| 1 | **partly fixed** | Line 47 now reads `expect(screen.getByRole('button', …)).toBeInTheDocument()`. Line 103 (101 in round 1) is still `expect(await screen.findByText('The Name field is required.'))` with no matcher. |
| 2 | fixed | `let sent: unknown;`. |
| 3 | fixed | *occurred*. |

No new findings; the commit changes only these three lines, so the round 1 breaks still hold.

Verdict: ready to ship (finding 1's second line is worth the one-line fix first)

## Round 3 · 2026-11-28 · 6b5bf00

Checks: `dotnet build` ok (0 warnings) · `dotnet test` ok (14 passed) · `npm run lint` ok ·
`npm run typecheck` ok · `npm test -- --run` ok (15 passed) · `npm run build` ok ·
`prettier --check .` ok.

| # | Status | How checked |
|---|---|---|
| 1 | fixed | Line 103 is now `expect(await screen.findByText('The Name field is required.')).toBeInTheDocument()`. |

No new findings.

Verdict: ready to ship
