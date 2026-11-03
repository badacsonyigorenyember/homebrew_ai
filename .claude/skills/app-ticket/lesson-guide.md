# Writing lessons

The user is new to React, TypeScript and .NET (SYSTEM.md C8). A lesson teaches what the ticket
needs, so the user can build it alone. Plain words; explain every new term the first time.

## What a lesson may contain

- Concepts, explained in words, with why they exist.
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
Two or three sentences, then the acceptance criteria it must meet (AC1…, by id).

## New concepts
One subsection per concept the ticket needs and the user has not met in an earlier ticket
(check the earlier tickets' lessons). For each: what it is, why it exists (the problem it solves),
how it fits this ticket, and a doc link. Split into "React and TypeScript" and ".NET" when both
appear.

## Patterns to follow
Each pattern named, why it is good, and what the usual mistake looks like, in words. Only the
patterns this ticket uses.

## Steps
A numbered list of small subtasks in building order. Each ends with "Check yourself:" and a way
to see it works (a command, a URL, what the screen shows). Steps where the user writes code
follow "Code steps" below.

## Files you will touch
Paths to create or change, one line each on what goes there.

## Pitfalls
The mistakes beginners make with this ticket's tools, and how each one shows up.

## Before you ask for a review
A short checklist: the ACs, the checks to run, the questions to ask yourself.
```

## Code steps

The user follows the steps more than the concepts, so a step that asks for code must be doable
from the step alone plus the docs it links. "Write the component" is too big; a0-03's step 9
(`docs/app/work/a0-03-web-skeleton/lesson.md`, later in `finished/`) is the model.

- **Read first.** Before the first code step that uses a new language construct, a short reading
  list in the order to read it: each link names the sections to read (not the whole page) and what
  to look for, and the time it takes. Include plain JavaScript pages (MDN) when the step uses
  JavaScript the user has not met (destructuring, bracket access, imports), and a place to try
  things without the project (the TypeScript Playground; for C#, a scratch console project made
  outside the repo).
- **One new piece per sub-step** (9a, 9b, …): one type, one function signature, one JSX element,
  one import. Each sub-step names the construct, describes its syntax in words, says why it is
  written that way, and points to the docs example closest to it ("react.dev's `MyButton` has the
  same structure").
- **A check per sub-step**, preferably one that breaks something on purpose and shows the exact
  error message ("remove one key: `npm run typecheck` says *Property 'unknown' is missing*").
  Run each such error before writing it down, with the project's own tool versions, in a scratch
  folder outside the repo; never write an error message from memory.
- **Say when a failing check is expected** and which later sub-step fixes it (an unused parameter
  until the body uses it), so a red error does not read as a mistake.

## `test-lesson.md`: its parts, in this order

```markdown
# Test lesson: <short id> · <title>

## What to test
Each behaviour worth a test, tied to its AC, and the level it belongs at (unit, API integration,
component) with why.

## What not to test
Framework behaviour, private details, things the type checker already proves.

## New concepts
As in the lesson: test runner, fixtures, faking the API or database, whatever is new.

## Patterns
Arrange-act-assert, one behaviour per test, names that state the behaviour, test data kept
small and visible, and whichever others this ticket needs.

## Steps
Numbered, each with "Check yourself:". The first step for each test is to see it fail
(write it before the behaviour exists, or break the code briefly). Writing a test is a code
step: follow "Code steps" above (read first, one new piece per sub-step, checked error messages).

## Before you ask for a test review
Checklist.
```

## Size

As long as the ticket needs and no longer. A setup ticket's lesson is mostly concepts and steps; a
feature ticket's is mostly patterns and steps. Skip a section only by writing "None for this
ticket."
