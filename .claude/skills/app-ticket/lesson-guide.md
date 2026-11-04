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
Paths to create or change, one line each on what goes there.

## Before you ask for a review
A short checklist: the ACs, the checks to run, the questions to ask yourself.
```

## Steps

Every step has these parts, in this order:

1. **What to do**, in a bold title and a sentence or two.
2. **Why:** why this step is needed (what would be missing or broken without it) and why it is done
   this way rather than the obvious alternative ("a named export, not `export default`, so a
   renamed import cannot silently point at the wrong thing").
   - A **new concept** is explained here, in the first step that needs it: what it is, the problem
     it solves, how it fits this ticket, and a doc link. Later steps refer back to it ("the query
     key from step 4") instead of explaining it again. Check the earlier tickets' lessons; a
     concept met there gets one line and a pointer, not a new explanation.
   - A **pattern** is taught in the step that applies it: its name, why it is good, and what the
     usual mistake looks like, in words.
3. **Watch out:** (only when there is one) the mistake beginners make at this step and how it shows
   up (the error text, what the screen does).
4. **Check yourself:** a way to see it works (a command, a URL, what the screen shows).

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
- **One new piece per sub-step** (9a, 9b, …): one type, one function signature, one JSX element,
  one import. Each sub-step names the construct, describes its syntax in words, says why it is
  written that way and what it does when the app runs, and points to the docs example closest to it
  ("react.dev's `MyButton` has the same structure").
- **A check per sub-step**, preferably one that breaks something on purpose and shows the exact
  error message ("remove one key: `npm run typecheck` says *Property 'unknown' is missing*").
  Run each such error before writing it down, with the project's own tool versions, in a scratch
  folder outside the repo; never write an error message from memory.
- **Say when a failing check is expected** and which later sub-step fixes it (an unused parameter
  until the body uses it), so a red error does not read as a mistake.

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
steps" above (read first, one new piece per sub-step, checked error messages).

## Before you ask for a test review
Checklist.
```

## Size

As long as the ticket needs and no longer. The steps carry the lesson: when a step's *Why* grows
past a short paragraph, split the step rather than move the explanation out of it. Skip a section
only by writing "None for this ticket."
