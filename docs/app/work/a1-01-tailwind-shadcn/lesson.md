# Lesson: a1-01 · Tailwind and shadcn/ui

## What you will build

The page gets a styling system. Tailwind CSS styles elements with small class names written in the
markup, shadcn/ui adds ready-made components whose source code is copied into your repo, and the
theme's colours follow your operating system's light or dark setting. `StatusBadge` keeps its three
labels but is drawn with shadcn's `Badge`, in a different look per status.

It is done when:

- **AC1** Switching the OS to dark mode switches the page.
- **AC2** The components in `src/components/ui/` came from the shadcn CLI and are unedited, or each
  edit has a one-line comment saying why.
- **AC3** Lint, type check, build and the existing tests pass.

**How the pieces fit.** `src/index.css` is the one stylesheet. It imports Tailwind, holds the theme
(colours as CSS variables, a light set and a dark set) and maps those variables to Tailwind class
names such as `bg-background`. When Vite builds or serves the page, Tailwind's Vite plugin reads your
`.tsx` files, finds the class names you used and writes only the CSS for those. The shadcn CLI is a
tool you run, not a library the page loads: it copies `badge.tsx` into `src/components/ui/`, and
that file is a normal React component built from Tailwind classes. `StatusBadge` imports it with
the `@/` alias, a short name for `src/` that Vite, TypeScript and the shadcn CLI each need to know.

What the tools look like today (measured 2026-11-08 in a scratch copy of your `app/web`, with your
Node 26.13.0, TypeScript 6.0.3 and Vite 8.3; every command output and error message quoted below
comes from that run):

| Thing | Version | Note |
|---|---|---|
| `tailwindcss`, `@tailwindcss/vite` | 4.3.5 | Tailwind 4: configured in CSS, no `tailwind.config.js` |
| `shadcn` (the CLI) | 4.23.0 | asks for a component library and a preset |
| `@base-ui/react` | 1.9.0 | the component library the CLI recommends |

## Steps

1. **Check where you are.** In a terminal in `app/web`, run `git branch --show-current` and
   `git status`.
   *Why:* every change in this ticket belongs on the ticket's branch, and a clean start means the
   review diff shows only this ticket.
   *Check yourself:* the branch is `a1-01-tailwind-shadcn` and `git status` lists nothing to
   commit.

2. **Install Tailwind.** In `app/web`: `npm install tailwindcss @tailwindcss/vite`.
   *Why:* **Tailwind** is a *utility-first* CSS framework. Instead of writing a CSS rule per element
   (`.status-badge { padding: … }`), you put small single-purpose classes on the element itself:
   `px-2` (horizontal padding), `text-xs` (small text), `rounded-full`. Each class does one thing.
   The point is that the styles live next to the markup they style, so you never hunt for which CSS
   rule affects an element, and deleting a component deletes its styles. At build time Tailwind
   scans your source files for the class names you used and generates only that CSS, so unused
   classes cost nothing. Two packages: `tailwindcss` is the engine, `@tailwindcss/vite` plugs it
   into Vite so it runs during `npm run dev`, `npm run build` and the tests.
   Docs: [Tailwind — Styling with utility classes](https://tailwindcss.com/docs/styling-with-utility-classes)
   (read "Overview" and "Why not just use inline styles?", 10 minutes),
   [Installing with Vite](https://tailwindcss.com/docs/installation/using-vite).
   *Check yourself:* `package.json` lists both packages (version 4.3.x); `npm ls tailwindcss` shows
   one version.

3. **Register the plugin in `vite.config.ts`.** Import the default export of `@tailwindcss/vite`
   (the docs name it `tailwindcss`) and add a call to it as a second item in the `plugins` array,
   after `react()`.
   *Why:* installing a Vite plugin does nothing until the config lists it; `plugins` is the list of
   build steps Vite runs on your files. Leave `test` and `server.proxy` as they are.
   *Watch out:* writing `tailwindcss` without the brackets adds the function itself instead of the
   plugin it returns.
   *Check yourself:* `npm run typecheck` passes and `npm run dev` still serves the page.

4. **Replace the template CSS with Tailwind.** Delete everything in `src/index.css` and leave one
   line: an `@import` of `"tailwindcss"`.
   *Why:* the CSS in that file is the Vite template's demo (fixed 1126 px column, purple accent);
   none of it is yours, and the next step writes the real theme into this same file. The import
   pulls in Tailwind's layers, including **Preflight**, a reset that removes browser default styles
   so every element starts plain and the same in every browser.
   Docs: [Tailwind — Preflight](https://tailwindcss.com/docs/preflight).
   *Watch out:* after this, "Brewing App" is no longer big and bold. That is Preflight resetting the
   `<h1>`, not a bug. Headings get their size from classes now.
   *Check yourself:* with `npm run dev` running, add `text-3xl font-bold` to the `<h1>`'s
   `className` in `App.tsx` (JSX writes the HTML `class` attribute as `className`): the heading
   grows on save. Keep or remove it; page layout itself is a1-02.

5. **Teach Vite the `@` alias.** In `vite.config.ts`, add a `resolve` key next to `plugins`, whose
   `alias` object maps `'@'` to the absolute path of your `src` folder. The shadcn Vite page shows
   the line: Node's `path.resolve` joins the folder the config lives in (`__dirname`) with
   `./src`; import `path` from `'path'` at the top.
   *Why:* an **import alias** is a short name for a folder. With it, `@/components/ui/badge`
   means the same file from anywhere in `src/`, instead of `../../components/ui/badge` whose number
   of `../` depends on where the importing file sits. shadcn's generated files import each other this
   way, so the alias is required, not a style choice. Vite needs it to find the file when it serves,
   builds and tests the app (Vitest reads the same config).
   Docs: [shadcn — Vite installation, "Update vite.config.ts"](https://ui.shadcn.com/docs/installation/vite),
   [Vite — `resolve.alias`](https://vite.dev/config/shared-options#resolve-alias).
   *Check yourself:* `npm run typecheck` passes (measured: `__dirname` is accepted in this config).

6. **Teach TypeScript the alias, in `tsconfig.app.json`.** In `compilerOptions`, add `paths`: an
   object whose key is `"@/*"` and whose value is an array with one string, `"./src/*"`. The `*` on
   each side means "whatever follows".
   *Why:* TypeScript resolves imports on its own, without reading `vite.config.ts`, so it needs the
   same mapping. `tsconfig.app.json` is the config that checks your `src/` files.
   Docs: [TypeScript — `paths`](https://www.typescriptlang.org/tsconfig/#paths).
   *Watch out:* the shadcn page also adds `"baseUrl": "."`. Do not copy it. Your TypeScript 6.0.3
   refuses it:
   *error TS5101: Option 'baseUrl' is deprecated and will stop functioning in TypeScript 7.0.* Since
   TypeScript 4.1, `paths` works without `baseUrl` and is read relative to the tsconfig file.
   *Check yourself:* `npm run typecheck` passes. (Step 12a shows the error you get when this entry
   is missing.)

7. **Teach the shadcn CLI the alias, in `tsconfig.json`.** The root `tsconfig.json` has only
   `files` and `references`. Add a `compilerOptions` object to it with the same `paths` entry as
   step 6.
   *Why:* the root file is the one the shadcn CLI reads to find out where `@/` points (TypeScript's
   own check uses the `references` and ignores it). Measured without it: the CLI does not complain;
   it plans to write `@/components/ui/badge.tsx`, a folder literally named `@` in `app/web`.
   *Check yourself:* the two tsconfig files have the same `paths` entry, and neither has `baseUrl`.

8. **Set up shadcn/ui.** In `app/web`: `npx shadcn@latest init`. It asks two questions. For the
   component library, take **Base UI (Recommended)**; for the preset, take **Nova**.
   *Why:* **shadcn/ui** is not a component package you install and import from `node_modules`. It
   is a CLI that copies each component's source into your repo, where it becomes your code: you can
   read it, and it changes only when you change it. (SYSTEM.md §4 picked it for that reason.)
   `init` prepares the project once. Its two questions:
   - The **component library** supplies *behaviour* without styling: keyboard handling, focus,
     accessibility attributes. These are called *headless* components. shadcn draws them with
     Tailwind. Base UI is the CLI's default and recommended choice; Radix UI is the older one many
     tutorials show. Most docs pages have a Base UI and a Radix tab; read the Base UI one.
   - The **preset** is the visual style (spacing, corner radius, font). Nova is the first and
     default one; it is easy to change later with `shadcn apply`.

   What `init` writes, so you can read the diff:
   - `components.json`: the CLI's settings (where your CSS is, the aliases, the style). Every later
     `shadcn add` reads it.
   - `src/lib/utils.ts`: the `cn` helper that combines class names and lets a later class override
     an earlier one (`px-2` then `px-4` gives `px-4`). Generated components call it.
   - `src/index.css`: the theme, explained in step 9.
   - `package.json` dependencies: `@base-ui/react` (the behaviour), `class-variance-authority` (picks
     classes per variant, used by `Badge`), `cn` (the class merger), `lucide-react` (icons),
     `tw-animate-css` (animation classes), `@fontsource-variable/geist` (the Nova font, served from
     your app, not a CDN), and `shadcn` itself (its `shadcn/tailwind.css` is imported by
     `index.css`).

   Docs: [shadcn — Vite installation](https://ui.shadcn.com/docs/installation/vite),
   [`components.json`](https://ui.shadcn.com/docs/components-json).
   *Watch out:* if steps 3 to 7 are not done, `init` stops at its checks with
   *No Tailwind CSS configuration found at …* and
   *Could not find valid path aliases or package imports for init.* Fix the step it names and run
   `init` again.
   *Check yourself:* the output ends with *Project initialization completed.*; `git status` shows
   `components.json` and `src/lib/` as new and `package.json`, `package-lock.json`,
   `src/index.css` as changed.

9. **Read the theme in `src/index.css`.** Nothing to write yet; read the file top to bottom.
   *Why:* the next step changes it, and later tickets add to it. Four parts:
   - **CSS custom properties (variables).** A name starting with `--` holds a value
     (`--background: oklch(1 0 0);`), and `var(--background)` reads it. A variable set on `:root`
     (the `<html>` element) is visible to every element. `oklch(…)` is a way to write a colour.
   - **`:root { … }`** holds the light values; **`.dark { … }`** holds the dark values of the same
     names. Same names, different values: switching the set switches every colour at once.
   - **`@theme inline { … }`** tells Tailwind to make class names from variables:
     `--color-background: var(--background)` is what makes `bg-background` and `text-background`
     exist. So a component says `bg-primary` and never a colour value.
   - **`@layer base`** gives `body` the background and text colour from the theme.

   The variables are named by **role** (`background`, `primary`, `destructive`, `muted`), not by
   colour (`white`, `red`). That is the pattern to keep when you add one later: a role keeps its
   meaning in both themes, a colour name would be a lie in one of them.
   Docs: [shadcn — Theming](https://ui.shadcn.com/docs/theming) (read "Convention" and "Adding new
   tokens"), [MDN — Using CSS custom properties](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties),
   [Tailwind — Theme variables](https://tailwindcss.com/docs/theme).
   *Check yourself:* you can say which line makes the class `text-muted-foreground` exist, and where
   its dark value comes from.

10. **Make dark mode follow the OS.** Two edits in `src/index.css`:
    - **10a.** Delete the `@custom-variant dark …` line near the top.
    - **10b.** Change the `.dark { … }` block so its variables apply when the OS is dark: wrap it in
      an `@media (prefers-color-scheme: dark) { … }` block, and change its selector from `.dark` to
      `:root`. Keep the variables inside unchanged.

    *Why:* **`prefers-color-scheme`** is a CSS *media query*: the browser tells the page whether the
    OS is set to light or dark, and the rules inside `@media (prefers-color-scheme: dark)` apply only
    while it says dark. It changes live, without a reload. shadcn's default is different: it switches
    on a `.dark` class on `<html>`, which is meant for a theme toggle button that some JavaScript
    turns on and off. This ticket has no toggle, only "follow the OS", so nothing would ever add that
    class: the dark values would never apply. The two edits fix both places that read the class:
    - Tailwind's `dark:` prefix (the generated `Badge` uses classes such as
      `dark:bg-destructive/20`) follows `prefers-color-scheme` by default. The deleted line had
      changed it to "inside `.dark`"; removing it restores the default.
    - The dark variables now sit on `:root` while the OS is dark, so they replace the light values
      from the `:root` block above.

    This is CSS only: no JavaScript, no flash of the wrong theme while the page loads. If a toggle is
    wanted one day, these two edits are what you undo.
    Docs: [Tailwind — Dark mode](https://tailwindcss.com/docs/dark-mode) (first two sections),
    [MDN — `prefers-color-scheme`](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme).
    *Watch out:* a media query holds rules; it is not a rule itself. Variables written straight
    inside `@media (…) { … }` with no selector around them do nothing. They need the `:root { … }`
    inside it.
    *Watch out:* do not edit `src/components/ui/` to make this work. The `.tsx` files never mention
    `.dark`; only `index.css` does.
    *Check yourself (AC1):* with `npm run dev` running, open the page and press F12. In Chrome's
    DevTools, open the ⋮ menu → More tools → Rendering, and set "Emulate CSS media feature
    prefers-color-scheme" to `dark`, then `light`: the background turns near-black and back without a
    reload. Then do it for real: Ubuntu Settings → Appearance → Dark; the open page follows.
    Measured in the scratch run: the body background is `oklch(1 0 0)` in light and
    `oklch(0.145 0 0)` in dark.

11. **Add the Badge component.** In `app/web`: `npx shadcn@latest add badge`.
    *Why:* this is the CLI's main job: copy one component into `src/components/ui/`. Read the file
    it creates. You will see three things you have not met; you only need to recognise them, not
    write them:
    - `cva(…)` from `class-variance-authority`: a base string of Tailwind classes, then one string
      per **variant** (`default`, `secondary`, `destructive`, `outline`, `ghost`, `link`). The
      `variant` prop picks one.
    - `cn(…)` from step 8, which merges the variant's classes with any `className` you pass.
    - `useRender` and `mergeProps` from Base UI, which draw a `<span>` by default and let a caller
      draw something else instead. You will not use that here.

    Docs: [shadcn — Badge (Base UI)](https://ui.shadcn.com/docs/components/base/badge).
    *Check yourself:* the output says *Created 1 file: src/components/ui/badge.tsx*.

12. **Keep Prettier off the generated folder.** Run `npx prettier . --check`. Measured: it lists
    `src/components/ui/badge.tsx`, `src/index.css` and `src/lib/utils.ts`, because the CLI writes
    double quotes and no semicolons and your `.prettierrc` says the opposite. Create
    `.prettierignore` in `app/web` with one line, the folder `src/components/ui/`. Then run
    `npm run format` to format the other two files, which are yours to own.
    *Why:* AC2 says the generated files stay as the CLI wrote them, and step 16 checks that by
    asking the CLI to compare. A Prettier-formatted `badge.tsx` differs from the CLI's version in
    every line, so that check could no longer tell a real edit from a quote change. Your pre-commit
    hook runs `prettier --check .`, so without the ignore entry you also could not commit.
    Docs: [Prettier — Ignoring code](https://prettier.io/docs/ignore).
    *Watch out:* do not run `npm run format` before the ignore file exists; it rewrites `badge.tsx`.
    If it already happened, run `npx shadcn@latest add badge --overwrite` to get the original back.
    *Check yourself:* `npx prettier . --check` ends with *All matched files use Prettier code
    style!*

13. **Settle the lint error the generated file brings.** Run `npm run lint`. Measured:

    > `src/components/ui/badge.tsx  51:17  error  Fast refresh only works when a file only exports
    > components. Use a new file to share constants or functions between components
    > react-refresh/only-export-components`

    Add one more object to the array in `eslint.config.js`, before `eslintConfigPrettier` (which
    stays last): its `files` key is an array with the glob `'src/components/ui/**/*.tsx'`, and its
    `rules` key turns `'react-refresh/only-export-components'` to `'off'`.
    *Why:* **Fast Refresh** is what updates the page in place when you save a component, keeping its
    state. It can do that only for files that export nothing but components, and this rule warns you
    when a file breaks that. `badge.tsx` also exports `badgeVariants`, the class list, so other
    components can look like a badge. The cost is only that saving `badge.tsx` reloads the page
    instead of updating it in place, which does not matter for a file you do not edit. A config
    object with `files` applies its rules only to matching files, so the rule still guards every file
    you write. This is the *scoped override* pattern: change the rule where the exception is, not
    everywhere.
    Docs: [ESLint — Configuration files, "Specifying files and ignores"](https://eslint.org/docs/latest/use/configure/configuration-files#specifying-files-and-ignores),
    [eslint-plugin-react-refresh README](https://github.com/ArnaudBarre/eslint-plugin-react-refresh).
    *Watch out:* the usual quick fix is an `// eslint-disable-next-line` comment in `badge.tsx`. That
    is an edit to a generated file (AC2), and you would repeat it in every future component that
    exports a variant list.
    *Check yourself:* `npm run lint` passes. Then, for a moment, add an exported constant to
    `StatusBadge.tsx`: lint reports the same rule there, proving the override reaches only
    `src/components/ui/`. Remove it.

14. **Rebuild `StatusBadge` on `Badge`**, in small steps. The type, the props and the labels stay.

    **Read first (about 15 minutes).**
    - [shadcn — Badge (Base UI)](https://ui.shadcn.com/docs/components/base/badge), "Usage" and
      "Examples": how the component is imported and how `variant` is passed.
    - [react.dev — Passing props to a component, "Passing JSX as children"](https://react.dev/learn/passing-props-to-a-component#passing-jsx-as-children):
      the text between `<Badge>` and `</Badge>` reaches the component as its `children` prop.
    - Your own `StatusBadge.tsx` and the 9e step of the a0-03 lesson
      (`docs/app/finished/a0-03-web-skeleton/lesson.md`): the `Record<ApiStatus, string>` lookup,
      which 14c repeats for a second value.

    **14a. The import.** At the top of `StatusBadge.tsx`, import `Badge` by name from
    `'@/components/ui/badge'`. It is a named import, in curly braces, like `StatusBadge` in
    `App.tsx`. The `@/` is the alias from steps 5 to 7.
    *Check yourself:* the failing check is expected until 14b uses it: `npm run typecheck` says
    *error TS6133: 'Badge' is declared but its value is never read.* and `npm run lint` says
    *'Badge' is defined but never used*. To see why step 6 matters, delete the `paths` entry from
    `tsconfig.app.json` for a moment: typecheck now says *error TS2307: Cannot find module
    '@/components/ui/badge' or its corresponding type declarations.* Put it back.

    **14b. The element.** Replace the `<span>` and `</span>` tags with `<Badge>` and `</Badge>`, the
    label lookup staying between them.
    *Why:* `Badge` is a component like yours, so you use it like an HTML tag, capitalised. Without a
    `variant`, it uses `default`.
    *Check yourself:* `npm run typecheck` and `npm run lint` pass; the page shows the label in a dark
    pill (light theme). `npm test -- --run` still passes: the tests look for the label *text*,
    and `Badge` still draws a `<span>` containing it.

    **14c. A variant per status.** Decide which look each status gets (for example `down` as
    `destructive`; `ok` and `unknown` from `default`, `secondary` or `outline`; your choice). Add a
    second lookup next to `labels`, built like it: a `const` annotated with `Record<ApiStatus, …>`,
    where the value type is a union of the variant names you use, each in quotes, separated by `|`
    (the same syntax as `ApiStatus` itself). Pass the looked-up value to `Badge` as its `variant`
    prop, in curly braces, the same square-bracket lookup as the label.
    *Why:* the `Record` keeps the same safety net as `labels`: a fourth status cannot be added
    without TypeScript asking for its look. Writing the three names as your own union keeps the file
    readable; the type checker still compares them with what `Badge` accepts.
    *Check yourself:* put a name `Badge` does not have (for example `'success'`) into both the union
    and one entry. `npm run typecheck` says *Type '"success"' is not assignable to type '"default" |
    "secondary" | "destructive" | "outline" | "ghost" | "link" | null | undefined'.* The list in
    that message is the variants from `badge.tsx`. Undo it. Then stop the API (or start the page
    without it) and see the `down` look; start it and see `ok`.

15. **Run the existing tests.** `npm test -- --run`.
    *Why:* AC3. The labels did not change, so the tests should pass unchanged; the ticket asks you to
    update them only if a label's markup changed.
    *Check yourself:* *Tests 7 passed (7)* (the scratch run's result with the same tests).

16. **Prove AC2.** `npx shadcn@latest add badge --diff`.
    *Why:* `--diff` asks the CLI to compare the file in your repo with what it would write now, and
    changes nothing. That is the evidence that `badge.tsx` is unedited.
    *Check yourself:* it prints `src/components/ui/badge.tsx (skip)` and *No changes.* Measured the
    other way round: after changing one class in `badge.tsx`, it prints the file as `(overwrite)`
    with the changed line.

17. **Run every check and ask for a review** (say "review a1-01").
    *Check yourself:* the list under "Before you ask for a review" is all ticked.

## Files you will touch

- `app/web/package.json`, `app/web/package-lock.json` — Tailwind, its Vite plugin and the packages
  `shadcn init` adds.
- `app/web/vite.config.ts` — the Tailwind plugin and the `@` alias.
- `app/web/tsconfig.app.json` — `paths` for `@/*`.
- `app/web/tsconfig.json` — `compilerOptions.paths` for the shadcn CLI.
- `app/web/components.json` — new, written by `shadcn init`.
- `app/web/src/lib/utils.ts` — new, written by `shadcn init` (formatted by Prettier).
- `app/web/src/index.css` — replaced: the Tailwind import, shadcn's theme, your dark-mode edits.
- `app/web/src/components/ui/badge.tsx` — new, written by `shadcn add badge`, unedited.
- `app/web/.prettierignore` — new: `src/components/ui/`.
- `app/web/eslint.config.js` — the scoped override for `src/components/ui/`.
- `app/web/src/components/StatusBadge.tsx` — draws `Badge` with a variant per status.
- `app/web/src/App.tsx` — only if you gave the heading classes in step 4.

## Before you ask for a review

- [ ] AC1: emulating `prefers-color-scheme: dark` in DevTools, and switching Ubuntu to dark, both
      switch the page without a reload.
- [ ] AC2: `npx shadcn@latest add badge --diff` says *No changes.*; nothing in
      `src/components/ui/` was touched by hand or by Prettier.
- [ ] AC3: `npm run lint`, `npm run typecheck`, `npm test -- --run` and `npm run build` pass, and
      `npx prettier . --check` passes (the pre-commit hook runs all five).
- [ ] Neither tsconfig file has `baseUrl`; both have the same `paths`.
- [ ] No `.dark` selector or `@custom-variant dark` line left in `index.css`.
- [ ] `git status` shows no `node_modules/`, `dist/` or a folder named `@`.
- [ ] Could you add a fourth status and be sure TypeScript asks for both its label and its look?
