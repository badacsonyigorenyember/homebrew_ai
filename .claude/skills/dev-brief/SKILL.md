---
name: dev-brief
description: Use when the user gives a requirement, idea or feature request in this project that has no written brief yet and needs one before planning, or asks to write or revise a brief in docs/work/<slug>/.
---

# dev-brief

Turn a requirement into `docs/work/<slug>/brief.md`: **what** is wanted and **why**, precise
enough that a plan can be written from it and the result can be tested against it. It is not an
implementation plan: no file-level steps, no code.

First read `.claude/skills/dev-flow/conventions.md` and `PROJECT.md`.

## Steps

1. Pick the slug. If `docs/work/<slug>/brief.md` exists, you are revising it: apply the
   feedback you were given and keep everything else.
2. Gather facts. Read the docs PROJECT.md links for this area. Check the real state (files,
   `git log`, the DB catalog, running containers) instead of trusting written status. Read-only.
3. List what you cannot settle yourself (scope, priority, trade-offs only the user can decide).
   Put each in **Open questions** with options and a recommendation.
4. Write `brief.md` from the template below. Plain language, short sentences.
5. If the requirement would change PROJECT.md §2, §3 or §6, say so as a question. Do not edit
   those sections.
6. Prepare (do not commit) a PROJECT.md §8 line: `Wrote brief for <slug> (docs/work/<slug>/)`.
7. Hand over for approval:
   - subagent mode: report `needs-input` if there are open questions, otherwise
     `needs-approval`, with `Commit on approval: docs/work/<slug>/brief.md PROJECT.md —
     Add brief: <slug>`.
   - direct mode: show the brief's Goal, Requirements and Acceptance criteria, ask the open
     questions, and on approval set `Status: approved`, create the branch, and commit.

## Template

```markdown
# <Title>

Status: draft
Slug: <slug> · Branch: <slug>

## Why
The problem in 2–4 sentences, and who or what it blocks.

## Goal
What is true when this is done, in 1–3 sentences.

## Scope
In: …
Out: … (name the tempting neighbours that are deliberately left out)

## Requirements
R1. <one testable statement>
R2. …

## Constraints
Rules from CLAUDE.md, PROJECT.md §6 and docs/OPERATIONS.md that bind this work.

## Assumptions
Things taken as true without checking, each marked *(unverified)*.

## Acceptance criteria
A1. <observable check, linked to R-numbers>: e.g. "`ref.style` holds 116 BJCP rows (R1)"
A2. …

## Open questions
1. <question> — options … — recommend …

## Deviations
```

Every requirement has at least one acceptance criterion. Acceptance criteria are what
`dev-verify` will check, so make them observable.
