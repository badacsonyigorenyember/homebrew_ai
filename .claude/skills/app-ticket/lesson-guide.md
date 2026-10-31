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
to see it works (a command, a URL, what the screen shows).

## Files you will touch
Paths to create or change, one line each on what goes there.

## Pitfalls
The mistakes beginners make with this ticket's tools, and how each one shows up.

## Before you ask for a review
A short checklist: the ACs, the checks to run, the questions to ask yourself.
```

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
(write it before the behaviour exists, or break the code briefly).

## Before you ask for a test review
Checklist.
```

## Size

As long as the ticket needs and no longer. A setup ticket's lesson is mostly concepts and steps; a
feature ticket's is mostly patterns and steps. Skip a section only by writing "None for this
ticket."
