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

## Round 2 · 2026-11-03 · 18cce14

Checks (in `app/web`, Node 26.13.0, project TypeScript 6.0.3; working tree clean):
`npm run lint` ok ·
`npm run typecheck` (`tsc -b`) ok, also with `--force`, so the result isn't a cached one ·
`npm run build` ok ·
`npx prettier . --check` "All matched files use Prettier code style!" ·
no `npm test` yet (tests come next).

AC1, AC3 and AC4 were tried in a scratch copy of `app/web` with its own TypeScript cache, so your
files and your `node_modules/.tmp` were not touched.

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | `vite` on the scratch copy: the page and tab show "Brewing App" and "API ok" |
| AC2 | yes | `build`, `lint` and `typecheck` all exit 0 |
| AC3 | yes | with `status="broken"`: `npm run typecheck` exits 2 with `src/App.tsx(7,20): error TS2322: Type '"broken"' is not assignable to type 'ApiStatus'` |
| AC4 | yes | page text: `ok` → "API ok", `down` → "API downm", `unknown` → "API status unknown" |

Round 1 findings:

| # | Status |
|---|---|
| 1 `typecheck` checks no files | fixed: `tsc -b` follows the references (`18cce14`) |
| 2 heading and title | fixed: both say "Brewing App" (`49be51b`); the ticket writes "app" in lower case, either is fine |
| 3 Prettier not applied | fixed: every file passes `--check` |
| 4 typo "API downm" | still open (nice to have) |
| 5 `labels` rebuilt on every render | still open (nice to have) |
| 6 template `app/web/README.md` | still open (nice to have) |

No new findings.

Done well:
- You fixed #1 the right way: the same build-mode check the `build` script runs, so `typecheck`
  and `build` can't disagree about types.
- Each fix is its own small commit with a clear message, which makes this round easy to check.

Verdict: ready for tests

# Test review

## Round 1 · 2026-11-03 · 12920d9

Checks (in `app/web`, Node 26.13.0, project TypeScript 6.0.3; working tree clean):
`npm run lint` ok ·
`npm run typecheck` ok (also `tsc -b --force`) ·
`npm test -- --run` 3 passed (3) ·
`npm run build` ok ·
`npx prettier . --check` all files formatted.

Break-the-code check: one label in `StatusBadge.tsx` changed at a time, the tests run, the edit
undone, and `git diff` checked to match what it was before.

| Test | Behaviour (AC) | What I broke | Failed? |
|---|---|---|---|
| shows "API ok" when the status is ok | `ok` label on the page (AC4) | `ok: 'API OK'` | yes: *Unable to find an element with the text: API ok*; only this test failed |
| shows "API down" when the status is down | `down` label (AC4) | `down: 'API ok'` | yes: *Unable to find an element with the text: API down*; only this test failed |
| shows "API unknown" when the status is unknown | `unknown` label (AC4) | `unknown: 'API unknown'` | yes: *Unable to find an element with the text: API status unknown*; only this test failed (see #1) |

The setup file's cleanup was checked in a scratch copy: with a fourth test rendering `ok` again,
all 4 pass; with the `afterEach` line removed, it fails with *Found multiple elements with the
text: API ok*. So each test starts on an empty page.

Needed: each test covers one status, none repeats another, and none tests React, Testing Library
or what the type checker already refuses. Reliable: no time, randomness, network or order
dependence (the cleanup check above covers order).

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Standards | should fix | `app/web/src/components/StatusBadge.test.tsx:22` | The third test's name says it shows "API unknown", but it checks for "API status unknown". The break-the-code check shows the result: with the label changed to "API unknown", the test named *shows "API unknown"* fails. | The name is the bug report when a test fails. Here it says the opposite of what went wrong. | test lesson, "Names that state the behaviour" |
| 2 | Standards | nice to have | `app/web/src/components/StatusBadge.test.tsx:5`, `:13`, `:21` | Each test has its own `describe('StatusBadge', ...)`. One `describe` with the three `it` blocks inside does the same job. | A group is there to hold the component's tests together. With three groups of the same name, the next test you add has no clear place to go. | test lesson step 6; [`describe`](https://vitest.dev/api/describe.html) |
| 3 | Standards | nice to have | `app/web/src/test/setup.ts:1` | `import {} from '@testing-library/jest-dom/vitest'`. It works (the matchers load and the types are found), but the usual way to write it is the plain side-effect import: `import`, then the module name in quotes. | Empty braces look like an import whose names were deleted by mistake. The plain form says the module is loaded only for what it does when it runs. | [MDN: import for side effects only](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/import#import_a_module_for_its_side_effects_only); test lesson step 4a |

Code review findings still open: #5 `labels` rebuilt on every render and #6 template
`app/web/README.md` (both nice to have). #4 "API downm" was fixed in `e1ec4ea`: the `down` test
caught it, as intended.

Not a finding: you asked in this conversation for the README, so I wrote it. `app/README.md`
"Run the web app" now has rows for `npm test`, `npm test -- --run` and your `npm run cleanup`,
plus a short note on where tests live and what the setup file does. It's uncommitted; read it and
commit it with your next commit.

Done well:
- Every test failed when its label broke, and only that test failed: one behaviour per test, as
  the lesson asked.
- The cleanup is in the setup file, so tests don't depend on their order.
- `npm run cleanup` runs all the review and ship checks in one command.

Verdict: ready to ship (fix #1 first: it's a rename)
