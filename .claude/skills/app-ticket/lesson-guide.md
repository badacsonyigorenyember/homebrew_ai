# Writing lessons

The user is new to React, TypeScript and .NET (SYSTEM.md C8) and learns by doing. A lesson teaches
what the ticket needs, so the user can build it alone, and it teaches it inside the steps: there
is no separate concepts or patterns section to read first. Each step says what to do, why it is
needed, and why it is done that way. Plain words; explain every new term the first time.

## What a lesson may contain

- Concepts, explained in words, with why they exist, in the step that first needs them.
- Names: of libraries, CLI commands and their purpose, files and folders to create, functions,
  hooks, components, endpoints, configuration keys.
- A signature: a function, component or endpoint's name, parameters and return type, without its
  body, when a concept cannot be explained without it.
- A pseudo-step in one line ("read the key from configuration, compare it, return 401 if it
  differs").
- Syntax described in words, for a construct the user meets for the first time ("the keyword
  `type`, a name, `=`, then the values in double quotes separated by `|`"). One construct at a
  time, never a whole file read out in words.
- Shell commands for setup tickets (installing tools, creating projects), because they are
  tooling, not the app's code.
- Links to official docs, including their examples.

Anything else, such as a function body, a component's JSX, a test body or a config file's contents,
is solution code and stays out.

## `lesson.md`: its parts, in this order

```markdown
# Lesson: <short id> · <title>

## What you will build
Two or three sentences, then the acceptance criteria it must meet (AC1…, by id). Then a short
paragraph on how the pieces fit together (what calls what, where data goes), so the steps have a
map. No concept explanations here; they come in the steps.

## Steps
The main part of the lesson. A numbered list of small subtasks in building order, each written as
"Steps" below describes.

## Files you will touch
Paths to create or change, one line each on what goes there. No docs: `app/README.md` and the
other docs are not a lesson step; Claude writes them before shipping (SKILL.md Ship step 2).

## Before you ask for a review
A short checklist: the ACs, the checks to run, the questions to ask yourself, and that every
step is committed (`git status` shows nothing of this ticket left uncommitted).
```

## Steps

### Every step is a commit

The user commits after each numbered step, so each step has to end with the app working. The
pre-commit hook (`app/web/.husky/pre-commit`) runs `dotnet format --verify-no-changes`,
`dotnet build -warnaserror` and `dotnet test` when the commit touches the API, its tests or `db/`,
and lint, type check, tests, build and Prettier when it touches `app/web`, and refuses the commit if
any of them fails. A step that leaves the app broken for a later step to fix
cannot be committed. Order and size the steps so that this never happens:

- **Green at every step end.** When a numbered step is done, every check the hook runs passes (for
  the API: `dotnet build` and `dotnet test`), and the app still does what it did before, or more.
  Sub-steps (9a, 9b, …) inside a step may leave a check failing, as long as a later sub-step of the
  **same** step fixes it.
- **Build before you wire.** A new piece (a component, a hook, a page, an endpoint) is written and
  exported in its own step, unused; an unused export breaks no check. A later step puts it to use.
- **Change a thing together with everything it breaks.** When a change breaks its callers or the
  existing tests (a router around `App`, a renamed prop, a moved function), the step that makes it
  also updates those callers and tests. Moving code means: create the new place, switch the users
  to it, delete the old place, all in one step.
- **Setup is a step too.** Installing a package (`package.json` and `package-lock.json`) or adding
  a generated component is its own commit.
- **Checking is not a commit.** A step that only checks an AC in the browser or runs a command says
  "No commit" instead of a Commit line.

If a step cannot be made green without growing past one sitting, split the work differently
(build the piece first, wire it second) rather than allowing a broken commit.

### The parts of a step

Every step has these parts, in this order. Each part is its own labelled block on its own lines,
in steps and sub-steps (9a, 9b, …) alike, so the to-do can be read without the explanation and
the other way round; never one paragraph that mixes them (decided 2026-11-28, a1-07). Each block
is a paragraph of its own, with a **blank line** before it, also inside a sub-step: Markdown joins
lines that have no blank line between them, so a **Do:** line followed directly by a **Why:** line
renders as one paragraph (the user saw exactly that in a1-07's test lesson).

1. **What to do**, in a bold title, then a **Do:** block: a sentence or two, or a list.
2. **Why:**, a separate block after the Do block: why this step is needed (what would be missing or broken without it) and why it is done
   this way rather than the obvious alternative ("a named export, not `export default`, so a
   renamed import cannot silently point at the wrong thing").
   - A **new concept** is explained here, in the first step that needs it: what it is, the problem
     it solves, how it fits this ticket, and a doc link. Later steps refer back to it ("the query
     key from step 4") instead of explaining it again.
   - A concept **met in an earlier ticket** gets one line and a pointer into the user's own code,
     not into an earlier lesson: the file and the function, type or component that does the same
     thing, and what is alike ("in `api.ts`, `useBatches` has the shape you need: a `useQuery`
     with a key and a fetch function"). Never "as in a1-02 step 10" or "the pattern from a1-02's
     `onNavigate`": the user has the code open, not the old lessons. Check the earlier tickets'
     lessons only to know what was taught.
   - A **pattern** is taught in the step that applies it: its name, why it is good, and what the
     usual mistake looks like, in words.
3. **Watch out:** (only when there is one) the mistake beginners make at this step and how it shows
   up (the error text, what the screen does).
4. **Check yourself:** a way to see it works (a command, a URL, what the screen shows).
5. **Commit:** the paths to `git add` (explicit paths, never `-A` or `.`) and a one-line message,
   imperative, at most 60 characters ([`dev-flow/conventions.md`](../dev-flow/conventions.md)), for
   example `Add the five placeholder pages`. The hook running green is the step's last check. A
   step with nothing to commit says "No commit".

A step that is only tooling (run a command, open a page) still gets its *Why*, in a sentence.

### Code steps

A step that asks for code must be doable from the step alone plus the docs it links. "Write the
component" is too big; a0-03's step 9 (`docs/app/finished/a0-03-web-skeleton/lesson.md`) is the
model for the size and the checks.

- **Read first.** Before the first code step that uses a new language construct, a short reading
  list in the order to read it: each link names the sections to read (not the whole page) and what
  to look for, and the time it takes. Include plain JavaScript pages (MDN) when the step uses
  JavaScript the user has not met (destructuring, bracket access, imports), and a place to try
  things without the project (the TypeScript Playground; for C#, a scratch console project made
  outside the repo).
- **Imports where they are first used.** No sub-step of imports at the start of a file. The
  sub-step that first uses a name says, in its Do block, to import it. The source is given only
  when more than one place offers that name and the editor could pick the wrong one (`screen`
  from `@testing-library/react`, not `@testing-library/dom`; `http` from `msw/http`, as the
  project's other files), and a type is marked as a type import; otherwise the name is enough,
  because the editor's auto-import finds it (decided 2026-11-28, a1-07).
- **One new piece per sub-step** (9a, 9b, …): one type, one function signature, one JSX element.
  Each sub-step names the construct, describes its syntax in words, says why it is
  written that way and what it does when the app runs, and points to the docs example closest to it
  ("react.dev's `MyButton` has the same structure").
- **A check per sub-step**, preferably one that breaks something on purpose and shows the exact
  error message ("remove one key: `npm run typecheck` says *Property 'unknown' is missing*").
  Run each such error before writing it down, with the project's own tool versions, in a scratch
  folder outside the repo; never write an error message from memory.
- **Say when a failing check is expected** and which later sub-step fixes it (an unused parameter
  until the body uses it), so a red error does not read as a mistake. That sub-step is always in
  the same numbered step: no check is still failing when the step reaches its Commit line.

### UI steps

The user finds the API lessons' level of detail right and has no UI experience (decided
2026-11-26, a1-07; refined 2026-11-27). Detail goes to what is new in UI work, not to what the
user knows from .NET:

- **What .NET already taught, said plainly.** Functions, parameters, return types, `async` and
  `await`, generics, classes, object and union types: name them in one phrase ("an async function
  `fetchBatches`, no parameters, returning `Promise<BatchSummary[]>`"), never token by token. The
  "syntax described in words" rule above is for constructs with no C# counterpart (JSX, spread,
  destructuring, template literals, optional chaining).
- **Exact class strings.** Every Tailwind class is given exactly as it is written in the code
  (`rounded-lg border p-3 break-words`, not "a border, rounded corners and padding"), each with a
  few words on what it does.
- **Exact values and fields.** Every list the code needs is written out in full: union values,
  object fields with their types, the keys of a lookup, option texts, routes, query keys, the
  JSON field names. Never "the seven statuses from the database" or "the fields of the response";
  the user must not have to look them up in the database, the API or the docs.
- **The Why explains; it never instructs.** Everything the user has to build is in the "what to
  do" part. The Why says what each part is good for and why it is done that way; it carries no
  extra prop, class, value or step that the code needs.
- **New components and APIs shown in use.** The first time a library piece is used (a shadcn
  component, a hook, a React Hook Form or TanStack function), the step says how to use it, not
  only where its docs are: which file under `src/components/ui/` or which package it comes from,
  which pieces it has, how they nest ("`Table`; inside it `TableHeader` with one `TableRow` of
  `TableHead`s; then `TableBody` with a `TableRow` of `TableCell`s per item"), and the props this
  ticket needs. The doc link is for further reading, never required to finish the step.
- **Imports at first use**, as "Code steps" above says: the name, and the source only when there
  is a choice.
- **The markup piece by piece:** one element per sub-step (or a short list in words when elements
  nest), in the order it appears, with its props and what goes between its tags. Words only,
  never the JSX itself.
- **The JSX ground rules in the first component step of a ticket**, as a read-first list with
  react.dev pages: one root element or a fragment, the round bracket on the `return` line, curly
  braces for values, `className`, `map` returning in round brackets with a `key`.
- **Hooks placed:** the hook calls listed as the first lines of the body, with the rule (no hook
  outside a component, in an `if` or after an early `return`).
- **What the screen shows** after the sub-step, or that nothing shows yet and which step shows
  it.
- **Watch-outs from real mistakes:** the errors the user actually hit in earlier UI tickets, each
  measured, go into later lessons where the same construct comes back.

## `test-lesson.md`: its parts, in this order

```markdown
# Test lesson: <short id> · <title>

## What you will test
Each behaviour worth a test, tied to its AC, and the level it belongs at (unit, API integration,
component) with why. Then, in a few lines, what not to test (framework behaviour, private details,
things the type checker already proves) and why.

## Steps
Written as "Steps" above: what to do, *Why*, *Watch out*, *Check yourself*. New test concepts
(test runner, fixtures, faking the API or database) and test patterns (arrange-act-assert, one
behaviour per test, names that state the behaviour, test data kept small and visible) are taught
in the step that first uses them. The first step for each test is to see it fail (write it before
the behaviour exists, or break the code briefly). Writing a test is a code step: follow "Code
steps" above (read first, one new piece per sub-step, checked error messages) and "Every step is a
commit": the hook runs the tests, so seeing a test fail happens inside the step, and the step
commits it only once it passes.

## Before you ask for a test review
Checklist.
```

## Size

As long as the ticket needs and no longer. The steps carry the lesson: when a step's *Why* grows
past a short paragraph, split the step rather than move the explanation out of it. Skip a section
only by writing "None for this ticket."
