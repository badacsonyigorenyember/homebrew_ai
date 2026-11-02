# Lesson: a0-03 · Web skeleton

## What you will build

The frontend project, `app/web`: a Vite + React + TypeScript app that shows the heading
"Brewing app" and one small component of your own, `StatusBadge`, which shows a different label for
each of three statuses. Around it you set up the checks every later ticket runs: a type check,
ESLint and Prettier.

It is done when:

- **AC1** `npm run dev` shows the page in the browser.
- **AC2** `npm run build`, `npm run lint` and `npm run typecheck` pass with no errors.
- **AC3** Passing a status outside the three values is a type error (`npm run typecheck` fails).
- **AC4** Each of the three statuses shows its own label.

What the tools look like today (measured 2026-11-02 by scaffolding the template in a scratch
folder, so you know what to expect):

| Thing | Version | Note |
|---|---|---|
| `create-vite` | 9.3.3 | React templates now use **Oxlint** unless you pass `--eslint` |
| Vite | 8.3 | needs Node 20.19+ or 22.12+; you have 26 |
| React | 19.3 | |
| TypeScript in the template | 7.0.2 | **too new for ESLint's TypeScript plugin**, see below |
| `typescript-eslint` | 8.72.1 | supports TypeScript `>=4.8.4 <6.1.0` only |
| Prettier | 3.9.10 | |
| `eslint-config-prettier` | 10.1.8 | |

**Decided with you on 2026-11-02:** ESLint, as the ticket says, with TypeScript pinned to
`~6.0.3` in the project until `typescript-eslint` supports TypeScript 7. Tested in the scratch
project: with 6.0.3, `npm install`, `npm run build` and `npm run lint` all pass. With the
template's 7.0.2, `npm install` stops with `ERESOLVE` (a dependency conflict, explained under
Pitfalls). The ticket's `## Deviations` records this.

## New concepts

### Tools

**Vite.** Two jobs. In development (`vite`, your `dev` script) it runs a local web server at
`http://localhost:5173`: the browser asks for a file, Vite turns your TypeScript and JSX into plain
JavaScript on the fly and sends it, and when you save a file the page updates without a reload (*hot
module replacement*, HMR). For release (`vite build`) it *bundles*: it follows every import from the
entry point and writes a few small, optimised files to `dist/`. `vite preview` serves `dist/` so you
can look at the built version.
Docs: [Vite — Getting started](https://vite.dev/guide/).

**Vite does not check types.** Vite only strips the TypeScript out of each file; it never asks "is
this type right?". That is on purpose: stripping works file by file and is fast, while type
checking needs the whole program. So a type error does **not** stop `npm run dev`: the page still
loads. Type errors are caught by the TypeScript compiler, `tsc`, which is why the template's `build`
script runs `tsc -b` before `vite build`, and why this ticket adds a `typecheck` script.
Docs: [Vite — TypeScript, "Transpile only"](https://vite.dev/guide/features.html#transpile-only).

**`create-vite` and templates.** `npm create vite@latest` downloads and runs the `create-vite`
package, which copies a starter project (a *template*) into a new folder. `react-ts` is React with
TypeScript. Options after a lone `--` go to `create-vite` instead of to npm.
Docs: [create-vite README](https://github.com/vitejs/vite/tree/main/packages/create-vite).

**`package.json`, scripts and the lock file.** `package.json` lists the project's packages and its
*scripts*: named commands run with `npm run <name>`. Inside a script, commands are found in the
project's own `node_modules/.bin` first, so `tsc` in a script is the project's TypeScript, not the
global one. `dependencies` are shipped with the app (React); `devDependencies` are tools used only
while building (Vite, TypeScript, ESLint). Versions are *ranges*: `^19.3.1` means "19.x, at least
19.3.1", `~6.0.3` means "6.0.x, at least 6.0.3". `package-lock.json` records the exact version
`npm install` picked for every package, including the packages they need; it is committed, so the
same install happens on another machine. `npm ci` installs exactly what the lock file says.
Docs: [npm scripts](https://docs.npmjs.com/cli/using-npm/scripts),
[package-lock.json](https://docs.npmjs.com/cli/configuring-npm/package-lock-json),
[`npm ci`](https://docs.npmjs.com/cli/commands/npm-ci).

**Peer dependencies.** A plugin can say "I work with these versions of the host tool" (a *peer
dependency*). `typescript-eslint` 8.72.1 says TypeScript below 6.1. The template asks for TypeScript
7.0.2, so npm cannot satisfy both and refuses to install. That refusal protects you: a plugin running
against a TypeScript it was not built for can crash or report wrong errors.
Docs: [typescript-eslint — dependency versions](https://typescript-eslint.io/users/dependency-versions).

**`tsconfig` files and project references.** `tsconfig.json` tells `tsc` which files to check and
how strictly. The template has three: `tsconfig.app.json` for your code in `src/` (browser
code), `tsconfig.node.json` for `vite.config.ts` (code that runs in Node), and `tsconfig.json`, which
only points at the other two (*project references*). `tsc -b` ("build mode") checks every referenced
project. Both have `noEmit: true`, so `tsc` only checks and writes no JavaScript (Vite does that). It
keeps a small cache in `node_modules/.tmp/` to make the next run faster.
Docs: [Project references](https://www.typescriptlang.org/docs/handbook/project-references.html),
[`noEmit`](https://www.typescriptlang.org/tsconfig/#noEmit).

**ESLint.** A *linter*: it reads your code and reports patterns that are legal but likely wrong
(an unused variable, a React hook called inside an `if`). Its settings are in `eslint.config.js`, the
*flat config* format: one array of config objects, applied in order, later ones overriding earlier
ones. The template's array already has the recommended JavaScript rules, `typescript-eslint`'s
recommended rules and two React plugins (`react-hooks`, `react-refresh`).
Docs: [ESLint — configuration files](https://eslint.org/docs/latest/use/configure/configuration-files).

**Prettier.** A *formatter*: it rewrites code into one fixed layout (quotes, semicolons, line
length, indentation), so you never argue with yourself about style, and diffs show only real
changes. `prettier . --write` formats every file; `prettier . --check` only reports. It reads its
options from `.prettierrc`, skips what `.prettierignore` lists, and already skips `node_modules` and
whatever the `.gitignore` in the folder it runs from lists (`dist` is there).
Docs: [Install](https://prettier.io/docs/install), [Options](https://prettier.io/docs/options),
[Ignoring code](https://prettier.io/docs/ignore).

**ESLint and Prettier together.** ESLint has some formatting rules too, and they can fight with
Prettier (one adds what the other removes). `eslint-config-prettier` is a config that only switches
those rules off. It goes **last** in the flat config array, so it overrides the configs before it. You
import its `/flat` entry point. The result: ESLint finds bugs, Prettier owns the layout.
Docs: [eslint-config-prettier README](https://github.com/prettier/eslint-config-prettier).

### React and TypeScript

**What runs where.** `index.html` is the page the browser loads. It has one empty `<div id="root">`
and a `<script>` tag for `src/main.tsx`. `main.tsx` asks React to take over that div
(`createRoot(...).render(...)`) and draw your top-level component, `App`, inside it. Everything you
see is drawn by components from then on. `StrictMode` around `App` is a development-only helper that
runs some code twice to expose bugs; it changes nothing in the built app.
Docs: [Add React to an existing project](https://react.dev/learn/add-react-to-an-existing-project),
[`StrictMode`](https://react.dev/reference/react/StrictMode).

**Components.** A React component is a function whose name starts with a capital letter and which
returns what to show. The capital letter is how React tells your `<StatusBadge />` from an HTML
tag like `<span>`. Each component usually lives in its own `.tsx` file and is exported from it.
Docs: [Your first component](https://react.dev/learn/your-first-component).

**JSX.** The HTML-like syntax inside `.tsx` files. It is not HTML: it is turned into JavaScript
calls. Differences you meet here: one parent element per return, `className` instead of `class`,
every tag closed (`<StatusBadge />`), and curly braces `{ }` to drop a JavaScript value into the
markup.
Docs: [Writing markup with JSX](https://react.dev/learn/writing-markup-with-jsx),
[JavaScript in JSX with curly braces](https://react.dev/learn/javascript-in-jsx-with-curly-braces).

**Props.** A component's inputs, written like HTML attributes where it is used
(`<StatusBadge status="ok" />`). React collects them into one object and passes it as the
function's single argument; you usually *destructure* it straight away, taking out the fields you
need by name. Props are read-only: a component never changes its own props.
Docs: [Passing props to a component](https://react.dev/learn/passing-props-to-a-component).

**Typing props.** You describe the props object with a TypeScript `type` (or `interface`) and annotate
the function's parameter with it. From then on, TypeScript checks every place the component is used:
a missing prop, a wrong name or a wrong value is a red underline in the editor and an error in
`tsc`. The shape of the signature, without a body, is
`function StatusBadge({ status }: StatusBadgeProps)`. You do not need to write the return type;
TypeScript works it out.
Docs: [Using TypeScript — typing component props](https://react.dev/learn/typescript#typing-component-props).

**Literal types and unions.** In TypeScript, `"ok"` can be a *type*: the type whose only value is the
string `"ok"`. A *union*, written with `|`, means "one of these". So `"ok" | "down" | "unknown"`
accepts exactly those three strings and nothing else; `"broken"` or `"OK"` is a type error. This is
what makes AC3 work. Give the union a name with a `type` alias (for example `Status`), so the
props type and anything else that needs it say the same thing.
Docs: [Literal types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#literal-types),
[Union types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#union-types).

**Choosing what to show from a prop.** Two plain ways to turn a status into a label: a lookup object
whose keys are the three statuses and whose values are the labels, or a `switch` on the status with
one `case` per value. Typing the lookup object with `Record<Status, string>` means TypeScript
complains if one of the three keys is missing, so a fourth status added later cannot be forgotten.
Docs: [Conditional rendering](https://react.dev/learn/conditional-rendering),
[`Record<Keys, Type>`](https://www.typescriptlang.org/docs/handbook/utility-types.html#recordkeys-type).

## Patterns to follow

- **One component per file, named like the component.** `StatusBadge` lives in
  `src/components/StatusBadge.tsx` and is a named export. *Why:* you find a component by its name,
  and the `react-refresh` lint rule wants component files to export components (so HMR can update
  them in place). *Usual mistake:* leaving it inside `App.tsx` "for now".
- **Let the type say what is allowed.** The three statuses are written once, as a named union, and
  the props type uses that name. *Why:* one place to change, and the type checker finds every use.
  *Usual mistake:* `status: string`, which accepts anything and makes AC3 impossible.
- **Make the mapping complete by type, not by habit.** Prefer the `Record<Status, string>` lookup
  (or a `switch` that TypeScript can see covers every case) over a chain of `if`s with a fallback
  `else`. *Why:* a fallback silently shows something for a value you forgot. *Usual mistake:* an
  `else` branch that hides a missing case.
- **Scripts are the interface.** Every check is an `npm run` script, and you run the script, not the
  bare tool. *Why:* the script uses the project's pinned versions and flags, and later tickets, the
  review and the ship step run exactly these names. *Usual mistake:* typing `tsc` in the terminal,
  which runs your *global* TypeScript 7.0.2, not the project's 6.0.3.
- **Pin what changes output.** Prettier is installed with `--save-exact` (no `^`), because Prettier
  changes its layout in patch releases and an unpinned upgrade would reformat files on its own. The
  TypeScript pin is `~6.0.3` (patch updates only) for the peer-dependency reason above.
- **Tooling changes and code changes in separate steps.** Run the first full `npm run format` on the
  fresh template before you write your own code. *Why:* the review diff then shows your component,
  not 20 lines of quote changes mixed in.
- **Keep only what the ticket shows.** The template's counter, logos, `hero.png` and its demo CSS
  are not part of the ticket; remove what the page no longer uses. *Why:* the next tickets start from
  a clean `src/`, and Tailwind replaces the CSS in a1-01 anyway.

## Steps

1. **Check where you are.** In a new terminal, go to this ticket's checkout and run
   `git branch --show-current`, `node -v` and `npm -v`.
   *Check yourself:* the branch is `a0-03-web-skeleton`, Node is `v26.*`. No `app/web` folder exists
   yet.

2. **Create the project** from inside `app/`:
   `npm create vite@latest web -- --template react-ts --eslint --no-immediate`.
   `--eslint` picks ESLint over Oxlint; `--no-immediate` stops it from installing straight away
   (that install would fail on the TypeScript conflict).
   *Check yourself:* `app/web/` has `package.json`, `eslint.config.js` (and **no** `.oxlintrc.json`),
   `index.html`, `src/main.tsx`, `src/App.tsx` and three `tsconfig*.json` files. In `package.json`,
   `lint` is `eslint .`.

3. **Pin TypeScript and install.** In `app/web`: `npm install --save-dev typescript@~6.0.3`. This
   changes the range in `package.json` and installs everything else in the same run.
   *Check yourself:* no `ERESOLVE` error; `npx tsc -v` in `app/web` prints `Version 6.0.3`;
   `package-lock.json` exists.

4. **See the template run.** `npm run dev`, open the address it prints.
   *Check yourself:* the Vite + React demo page loads. Stop the server with Ctrl+C.
   `npm run build` and `npm run lint` both finish without errors.

5. **Add the `typecheck` script.** One new entry in `scripts` that runs the same type check the
   `build` script runs first, on its own. Read the `build` script to see which command that is.
   *Check yourself:* `npm run typecheck` prints nothing and exits 0. Then put a deliberate type error
   in `App.tsx` (for example assign a number to a `const` you annotated as `string`):
   `npm run typecheck` fails and names the file and line, while `npm run dev` still shows the page.
   Undo the error.

6. **Add Prettier.** `npm install --save-dev --save-exact prettier`, then create `.prettierrc`
   (decide two things: single or double quotes, `singleQuote`; semicolons or not, `semi`; the
   template uses single quotes and no semicolons, Prettier's default is the opposite, either is fine)
   and a `.prettierignore` if you find something it should skip that `.gitignore` does not cover.
   Add a `format` script that formats the whole project.
   *Check yourself:* `npx prettier . --check` lists files before you format; after `npm run format`,
   the same check says "All matched files use Prettier code style!". `dist/` and `node_modules/` are
   never listed.

7. **Make ESLint and Prettier agree.** `npm install --save-dev eslint-config-prettier`, then add its
   flat config as the **last** item of the array in `eslint.config.js`.
   *Check yourself:* `npm run lint` passes. The package's CLI helper (its README, "CLI helper tool")
   reports no conflicting rules.

8. **Clean the template.** Replace the demo in `App.tsx` with the page: the heading "Brewing app"
   and room for the badge. Delete what is now unused (images in `src/assets/`, `App.css` if you do
   not use it). Set the `<title>` in `index.html` to "Brewing app" too, so the browser tab says it.
   *Check yourself:* the page shows only the heading; `npm run lint` and `npm run typecheck` pass (an
   import of a deleted file is a type error, so this check catches leftovers).

9. **Write `StatusBadge`.** In `src/components/StatusBadge.tsx`: a named union type for the
   three statuses, a props type with a `status` field of that type, and the component, which shows
   one label per status (your wording, for example "API OK", "API down", "API status unknown"). Use
   it in `App` with one status.
   *Check yourself:* the page shows the heading and the label. Change the status in `App` to each of
   the other two values and watch the label change after each save (AC4).

10. **Prove AC3.** In `App`, set `status` to a value outside the three (for example `"broken"`).
    *Check yourself:* the editor underlines it; `npm run typecheck` fails with an error saying the
    string is not assignable to your union type; `npm run build` fails too. Undo it.

11. **Write "Run the web app" in `app/README.md`.** A new section after Toolchain: where the project
    is, the one-time install (`npm ci`), how to start the dev server and at which address, and one
    line per script (`dev`, `build`, `lint`, `typecheck`, `format`). Add one line saying the project
    pins TypeScript 6.0 (not the global 7.0.2) and why.
    *Check yourself:* someone with the toolchain from a0-01 could run the app from the README alone.

12. **Run every check and ask for a review** (say "review a0-03").
    *Check yourself:* the list under "Before you ask for a review" is all ticked.

## Files you will touch

- `app/web/` — new: the whole Vite project, as the template creates it, minus the demo files you
  delete.
- `app/web/package.json` — TypeScript pinned to `~6.0.3`; Prettier and `eslint-config-prettier`
  added; `typecheck` and `format` scripts.
- `app/web/package-lock.json` — new, written by npm; committed.
- `app/web/eslint.config.js` — `eslint-config-prettier/flat` added last.
- `app/web/.prettierrc` — new: your two formatting choices.
- `app/web/.prettierignore` — new, only if something needs ignoring that `.gitignore` does not
  cover.
- `app/web/index.html` — the page title.
- `app/web/src/App.tsx` — the heading and one `StatusBadge`.
- `app/web/src/components/StatusBadge.tsx` — new: the status type, the props type and the component.
- `app/README.md` — a "Run the web app" section.

Not committed: `node_modules/`, `dist/` and `node_modules/.tmp/` (the template's `.gitignore`
already covers them).

## Pitfalls

- **`ERESOLVE could not resolve ... peer typescript@">=4.8.4 <6.1.0" from typescript-eslint`.**
  The template's TypeScript 7 is installed before the pin. Do step 3 before any plain
  `npm install`. Never answer it with `--force` or `--legacy-peer-deps`: those install the
  combination npm just told you is broken.
- **No `--eslint` flag.** You get `.oxlintrc.json`, `"lint": "oxlint"` and no `eslint.config.js`.
  Delete `app/web` and run step 2 again; that is simpler than converting by hand.
- **Missing `--` in `npm create vite@latest web -- --template ...`.** npm keeps the options for
  itself, and you get the interactive questions or the plain JavaScript template.
- **Running `create-vite` in the wrong folder.** Run it from `app/`, or you get `web/` at the repo
  root or a project nested in `app/web/web/`.
- **`tsc` in the terminal says something different from `npm run typecheck`.** Plain `tsc` is your
  global 7.0.2; the script uses the project's 6.0.3. Use the script, or `npx tsc` inside `app/web`.
- **"The page works, so the types are fine."** Vite shows the page even with type errors. Run
  `npm run typecheck` (or watch the editor's red underlines) before you believe it.
- **`status: string` in the props type.** Everything works and every check passes, except AC3:
  `"broken"` is accepted. Read the error you get in step 10; if there is none, the type is too wide.
- **`eslint-config-prettier` not last.** A config after it can switch formatting rules back on, and
  `npm run lint` starts reporting quotes or semicolons that Prettier wrote.
- **Importing from the wrong place.** `import ... from 'eslint-config-prettier'` (without `/flat`)
  also works, but the README asks for `/flat` in flat config files.
- **Component name in lower case.** `<statusBadge />` is treated as an unknown HTML tag: nothing
  shows, and React logs a warning in the browser console (F12).
- **Formatting the template after writing your code.** Your component review is then buried under
  formatting changes in every template file. Format first (step 6), then write code.

## Before you ask for a review

- [ ] AC1: `npm run dev` shows "Brewing app" and the badge.
- [ ] AC2: `npm run build`, `npm run lint` and `npm run typecheck` each finish with no errors.
- [ ] AC3: a status outside the three makes `npm run typecheck` fail (tried in step 10, undone).
- [ ] AC4: each of the three statuses shows its own label (tried in step 9).
- [ ] `npx prettier . --check` passes, so `npm run format` has nothing left to change.
- [ ] `npx tsc -v` in `app/web` is 6.0.3; `package-lock.json` is there.
- [ ] `app/README.md` has "Run the web app" with every script.
- [ ] `git status` shows only `app/web/` (no `node_modules/` or `dist/`) and `app/README.md`.
- [ ] Could you add a fourth status and be sure TypeScript points at every place to update?
