# Review: a0-03 · Web skeleton

## Round 1 · 2026-11-03 · 1a7f8ef + uncommitted

Checks (in `app/web`, Node 26.13.0, project TypeScript 6.0.3):
`npm run lint` ok ·
`npm run typecheck` exits 0, **but checks no files** (`npx tsc --listFilesOnly` prints nothing) ·
`npm run build` ok (its `tsc -b` checks `src/` and `vite.config.ts`) ·
`npx prettier . --check` 2 files not formatted (`src/App.tsx`, `src/components/StatusBadge.tsx`) ·
no `npm test` yet (tests come after this review) ·
language server: the editor runs the same checker as `tsc -b`, which reports nothing on the
branch as it is ·
`web-design-guidelines` and `vercel-composition-patterns`: not run, because the page is one
heading and one `<span>`, with no layout, interaction or component composition yet.

AC3 and AC4 were tried in a scratch copy of `app/web` (outside the repo, same `node_modules`), so
your files were not touched.

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | `vite` on the scratch copy: the page shows "My Application" and "API ok" (wrong heading, see #2) |
| AC2 | no | `build` and `lint` pass; `typecheck` passes only because it checks nothing (#1) |
| AC3 | no | with `status="broken"` in `App.tsx`: `npm run typecheck` exits 0; `npx tsc -b` fails with `TS2322: Type '"broken"' is not assignable to type 'ApiStatus'` |
| AC4 | yes | page text for each status: `ok` → "API ok", `down` → "API downm", `unknown` → "API status unknown" |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Spec | must fix | `app/web/package.json:12` | `typecheck` runs `tsc --noEmit`. Your root `tsconfig.json` lists no files (`"files": []`) and only points at `tsconfig.app.json` and `tsconfig.node.json`. Plain `tsc` reads only the root file, so it checks zero files and always passes. Only build mode (the flag the `build` script uses) follows the references. `noEmit` is already set in both referenced files. | AC2 and AC3 depend on this script. As it is, it would pass with any type error, and every later ticket's review and ship step relies on it. | [Project references → Build mode](https://www.typescriptlang.org/docs/handbook/project-references.html#build-mode-for-typescript); lesson step 5 |
| 2 | Spec | must fix | `app/web/src/App.tsx:6`, `app/web/index.html:7` | The heading says "My Application" and the tab title says "Homebrew App". The ticket asks for "Brewing app". | The ticket's "What to build" says what the page shows; the next tickets and their tests look for this text. | ticket "What to build"; lesson step 8 |
| 3 | Standards | should fix | `app/web/src/App.tsx`, `app/web/src/components/StatusBadge.tsx` | Neither file has been through Prettier: double quotes and missing semicolons against your `.prettierrc`, 4-space and 6-space indents. Run `npm run format` before each commit. Rider can also run Prettier on save. | The formatter only helps if every file goes through it. Otherwise the next format run puts layout changes into an unrelated commit. | [Rider: Prettier](https://www.jetbrains.com/help/rider/Prettier.html); lesson "Patterns to follow" |
| 4 | Spec | nice to have | `app/web/src/components/StatusBadge.tsx:10` | Typo in a label: "API downm". | It's the text on the screen. | — |
| 5 | Standards | nice to have | `app/web/src/components/StatusBadge.tsx:8` | The `labels` object is created inside the component, so React builds it again on every render. It doesn't use `status`, so it can live at the top level of the file, next to the types. | It's a pattern you'll use often: anything that doesn't depend on props or state goes outside the component. It's clearer (the fixed data is in one place, separate from the drawing) and not rebuilt each time. | [Keeping components pure](https://react.dev/learn/keeping-components-pure) |
| 6 | Standards | nice to have | `app/web/README.md` | It's still the template's README (Oxc vs SWC plugins, expanding the ESLint config). How to run the app now lives in `app/README.md`. | Two READMEs that disagree confuse whoever opens the folder first. Replace it with one line pointing to `app/README.md`, or delete it. | — |

Not a finding: `app/README.md` now has "Run the web app". You asked for that in this
conversation, so I wrote it. It's uncommitted with the rest of your work; read it and commit it
with your next commit.

Done well:
- `Record<ApiStatus, string>` for the labels: a missing or extra status is a type error, so the
  mapping can't fall out of step with the type.
- One named union (`ApiStatus`) used by the props type, and a separate `StatusBadgeProps`: the
  type says exactly what is allowed, which is what AC3 needs once the script checks files.
- The setup is pinned the way the lesson asked: TypeScript `~6.0.3`, Prettier exact (`3.9.10`),
  `eslint-config-prettier` last in the config. The template's demo files are removed and the
  setup is committed in small, separate steps.

Verdict: fixes needed
