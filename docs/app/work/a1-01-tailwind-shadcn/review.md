# Review: a1-01 · Tailwind and shadcn/ui

## Round 1 · 2026-11-08 · d8f2f76

Checks (in `app/web`, Node 26.13.0, project TypeScript 6.0.3; working tree clean):
`npm run lint` exit 0, but it checks only `src/components/ui/` (#1) ·
`npm run typecheck` ok ·
`npm test -- --run` 7 passed (unchanged tests) ·
`npm run build` ok, with one Vite warning (#3) ·
`npx prettier . --check` "All matched files use Prettier code style!" ·
`npx shadcn@latest add badge button --diff`: `badge.tsx` "No changes."; `button.tsx` "Formatting-only
changes (spacing, quotes, semicolons)" (#2) ·
language server: the editor runs the same checker as `tsc -b`, which reports nothing ·
`web-design-guidelines` and `vercel-composition-patterns`: not run; no view changed, only one badge.

AC1 was tried on a scratch copy of the branch (`git archive HEAD`, `npm ci`, `vite build`,
`vite preview`), in the browser with `prefers-color-scheme` emulated. The fixes for #1 and #3 were
also tried there, not in your files.

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | light: body `oklch(1 0 0)`, the "API ok" badge `oklch(0.205 0 0)`; switched to dark without a reload: body `oklch(0.145 0 0)`, badge `oklch(0.922 0 0)`. `<html>` has no class, so this is the media query, not `.dark` |
| AC2 | no | `badge.tsx` is as the CLI wrote it; `button.tsx` has been reformatted by Prettier (#2) |
| AC3 | no | every check exits 0, but lint skips your own files (#1), so "lint passes" is not shown yet |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Spec (AC3) | must fix | `app/web/eslint.config.js:12` | The existing config object's `files` was changed from `'**/*.{ts,tsx}'` to `'src/components/ui/**/*.tsx'`, and the rule override was put in that same object. That object is the one that switches on every rule (recommended JS and TypeScript rules, hooks, Fast Refresh), so now it applies to the `ui` files only. `npx eslint src/App.tsx src/components/StatusBadge.tsx` says *File ignored because no matching configuration was supplied* for both. And inside `ui/`, the Fast Refresh rule is off, so it guards nothing anywhere. | Lint "passes" because it reads almost nothing, and your pre-commit hook trusts it. An unused variable in `StatusBadge.tsx` would go through today. Put `'**/*.{ts,tsx}'` back, and add the override as a **separate** object before `eslintConfigPrettier` (lesson step 13). Measured on a scratch copy with that change: `eslint .` passes on your code, and an unused variable is reported again. | [ESLint — Configuration files, "Specifying files and ignores"](https://eslint.org/docs/latest/use/configure/configuration-files#specifying-files-and-ignores), and its section "Cascading configuration objects" |
| 2 | Spec (AC2) | must fix | `app/web/src/components/ui/button.tsx` | Prettier rewrote it (single quotes, semicolons), probably before `.prettierignore` existed, while it was still in the `@/` folder. The CLI reports "Formatting-only changes". | AC2 asks for unedited files or a comment per edit. A reformatted file also hides any real edit from `--diff` later. Run `npx shadcn@latest add button --overwrite`: `.prettierignore` now keeps it as written. Nothing uses `Button` yet, so deleting the file is fine too; a1-02 can add it again. | lesson step 12; [shadcn — CLI, `add`](https://ui.shadcn.com/docs/cli#add) |
| 3 | Standards | should fix | `app/web/vite.config.ts:10` | `npm run build` warns: *Your Vite config uses features that are unsupported by `configLoader: 'native'`, which is planned to become the default in a future major version of Vite: `__dirname` (vite.config.ts:10:41). Use `import.meta.dirname` instead*. Lesson step 5 told you `__dirname` was fine; I checked only the type checker, not the build output. That was my mistake, and the step is corrected. | `__dirname` exists only in CommonJS modules. Your `package.json` says `"type": "module"`, where the ES module way is `import.meta.dirname`. Today Vite translates your config so `__dirname` still works; the warning says that will stop. Measured on a scratch copy: with `import.meta.dirname`, the warning is gone and typecheck and the tests still pass. | [Vite — Configuring Vite, "Config loading"](https://vite.dev/config/), [Node — `import.meta.dirname`](https://nodejs.org/api/esm.html#importmetadirname) |
| 4 | Standards | nice to have | `app/web/src/components/StatusBadge.tsx:16` | `variants` lists its keys as `down, ok, unknown`; `labels` and `ApiStatus` use `ok, down, unknown`. | The same order in every lookup lets a reader compare them line by line. | — |
| 5 | Standards | nice to have | `app/web/src/components/StatusBadge.tsx:22` | The badge changes from "unknown" to "ok" or "down" by itself, but a screen reader is not told. `Badge` passes any extra prop on to its `<span>`, so `role="status"` would make the change announced. | A status that updates on its own is the case `role="status"` exists for. You will meet it again with loading and error states (F1.6, a2-06). | [MDN — ARIA `status` role](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/status_role) |

Done well:
- The dark-mode edit is exactly the two changes: no `@custom-variant dark`, and the dark values on
  `:root` inside `@media (prefers-color-scheme: dark)`. It switches live, CSS only.
- `paths` is `"@/*"` in both tsconfig files with no `baseUrl`, after the `@/` folder detour. That
  is the reading of the error you will need again: the folder was a symptom, the alias key was the
  cause.
- `variants` is typed `Record<ApiStatus, 'default' | 'destructive' | 'secondary'>`, so a fourth
  status cannot be added without TypeScript asking for its look.

Verdict: fixes needed

## Round 2 · 2026-11-08 · uncommitted (on 20f30fe)

Checks (in `app/web`, working tree as you left it; four files changed):
`npm run lint` exit 0, and it now lints `App.tsx` and `StatusBadge.tsx` again ·
`npm run typecheck` ok ·
`npm test -- --run` 7 passed ·
`npm run build` ok, no warning ·
`npx prettier . --check` exit 1: `src/components/StatusBadge.tsx` (#6) ·
`npx shadcn@latest add badge button --diff`: both "No changes." ·
`web-design-guidelines` and `vercel-composition-patterns`: not run; the only view change is one
attribute.

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | `index.css` is unchanged since round 1, where the live switch was measured |
| AC2 | yes | the CLI reports "No changes." for `badge.tsx` and `button.tsx` |
| AC3 | no | lint, typecheck, tests and build pass, but `prettier --check` fails, and your pre-commit hook runs it, so this work cannot be committed yet (#6) |

Round 1 findings:

| # | Status | Note |
|---|---|---|
| 1 | partly fixed | Every file is linted again. But the override is still inside the main object, so the Fast Refresh rule is now off for **all** files (#7) |
| 2 | fixed | `button.tsx` is back to the CLI's version |
| 3 | fixed | `import.meta.dirname`; the build warning is gone |
| 4 | fixed | `variants` follows `ok, down, unknown` |
| 5 | fixed | `role="status"` on the badge |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 6 | Spec (AC3) | must fix | `app/web/src/components/StatusBadge.tsx:22` | Adding `role="status"` made the `return` line longer than Prettier's 80 columns, and Prettier wants it wrapped in parentheses over five lines. | The pre-commit hook runs `prettier --check .` and will refuse the commit. Run `npx prettier --write src/components/StatusBadge.tsx`, or format on save in your editor. | [Prettier — CLI, `--write`](https://prettier.io/docs/cli#--write) |
| 7 | Standards | should fix | `app/web/eslint.config.js:12-13` | `files` lists both `'**/*.{ts,tsx}'` and `'src/components/ui/**/*.tsx'`, and `rules` turns `react-refresh/only-export-components` off in that same object. The first glob already matches everything, so the second adds nothing, and the rule is off everywhere: `npx eslint --print-config src/App.tsx` shows it at `0`. Measured: a file with `export const statusNames = ['ok'];` next to a component passes lint today, and fails with the rule on. | That rule is what tells you a file will lose its state on every save in the dev server. You will write many component files in M1 and M2. Keep the main object with `files: ['**/*.{ts,tsx}']` and no `rules`, and add a **second** object with `files: ['src/components/ui/**/*.tsx']` and only the rule override, before `eslintConfigPrettier` (lesson step 13). Later objects win for the files they match. | [ESLint — Configuration files, "Cascading configuration objects"](https://eslint.org/docs/latest/use/configure/configuration-files#cascading-configuration-objects) |

Done well:
- `button.tsx` was restored with the CLI rather than by hand, and `.prettierignore` kept it that
  way: `--diff` now proves AC2 for both files.
- `import.meta.dirname` is the ES module way, and it fits `"type": "module"` in `package.json`.
- Both nice-to-haves were picked up, including `role="status"` passed straight through `Badge`.

Verdict: fixes needed

## Round 3 · 2026-11-08 · uncommitted (on 20f30fe)

Checks (in `app/web`, working tree as you left it):
`npm run lint` exit 0 ·
`npm run typecheck` ok ·
`npm test -- --run` 7 passed ·
`npm run build` ok, no warning ·
`npx prettier . --check` "All matched files use Prettier code style!" ·
`npx shadcn@latest add badge button --diff`: both "No changes." ·
`npx eslint --print-config`: `react-refresh/only-export-components` is `2` for `src/App.tsx` and
`0` for `src/components/ui/badge.tsx`; a test file with `export const statusNames = ['ok'];` next to a
component, linted from stdin, fails with that rule.

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | `index.css` is unchanged since round 1, where the live switch was measured |
| AC2 | yes | the CLI reports "No changes." for `badge.tsx` and `button.tsx` |
| AC3 | yes | lint (now over every file), typecheck, the 7 existing tests, build and Prettier all pass |

Earlier findings: #1 fixed (all files linted, rule off only in `ui/`) · #2–#5 fixed (round 2) ·
#6 fixed (`StatusBadge.tsx` formatted) · #7 fixed (separate override object).

No new findings.

Done well:
- The ESLint config is now two objects that each do one job, and `--print-config` shows the rule on
  for your files and off for shadcn's only.

Verdict: ready to ship (the ticket's `## Tests` says no new tests are needed)
