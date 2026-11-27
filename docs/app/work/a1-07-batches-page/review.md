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
