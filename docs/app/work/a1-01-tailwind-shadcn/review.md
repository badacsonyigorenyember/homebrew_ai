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
