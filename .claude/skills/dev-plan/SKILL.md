---
name: dev-plan
description: Use when a brief in docs/work/<slug>/brief.md is approved, or the user points at an existing spec, design doc or plan in this project, and a step-by-step implementation plan is needed before any code is written.
---

# dev-plan

Write `docs/work/<slug>/plan.md`: the tasks that turn the brief into working, tested changes.
The main reader is the agent that implements it, with no other context. A human must still be
able to follow it in one read.

First read `.claude/skills/dev-flow/conventions.md` and `PROJECT.md`.

## Input

- `docs/work/<slug>/brief.md`, or
- a document the user names (for example `docs/superpowers/plans/…md`). Do not move it. Link
  it as `Source:` in the plan, and carry over its decisions instead of re-deciding them, except
  its git workflow: the branch is always `<slug>`, commits follow the conventions, and steps
  about PRs or worktrees are dropped (dev-ship merges locally).
- If `plan.md` exists, you are revising it: apply the feedback, keep the rest.

## Steps

1. Read the input and every doc it links. Check facts against the real code, files and DB
   catalog (read-only). A wrong path or table name in a plan costs a failed task later.
2. Cut the work into tasks. One task = one commit = one thing a reviewer can judge. Order them
   so each task leaves the repo working.
3. For each critical behaviour, name the regression test that protects it, and put it in the
   task that builds that behaviour. Critical means: wrong output would corrupt data or a
   recipe, or a later step depends on it. Not row counts.
4. Write `plan.md` from the template. Give exact paths, commands, SQL and signatures where
   guessing would go wrong. Describe the rest in words. No walls of code.
5. If a step needs to break a rule in CLAUDE.md, docs/OPERATIONS.md or dev-implement (for
   example recreating a container), make it an open question. Once the user allows it, record
   it in an `## Approved exceptions` section of the plan: what, which task, and why.
6. Prepare a PROJECT.md §8 line: `Planned <slug> (docs/work/<slug>/plan.md)`.
7. Hand over: subagent mode → `needs-approval` (or `needs-input`), with `Commit on approval:
   docs/work/<slug>/plan.md PROJECT.md <Source path, if untracked> — Add plan: <slug>`.
   Direct mode → summarise the task list, ask, and on approval set `Stage: approved` and commit.

## Template

```markdown
# <Title> — implementation plan

Stage: draft
Brief: [brief.md](brief.md)  ·  or  ·  Source: <path to the user's doc>
Branch: <slug>

## Approach
3–10 lines: how the pieces fit, and why this way.

## Files
| Path | New / changed | Purpose |

## Tasks

### Task 1: <outcome, in words>
Why: one line, linked to R/A numbers.
- [ ] <concrete step: file, command or change>
- [ ] Write test `tests/…::test_…`: <what it proves>
- [ ] Run `<command>`, expect <result>
Done when: <checkable condition>
Commit: `<one-line message>`

### Task 2: …

## Critical behaviour and its tests
| Behaviour | Test | Task |

## Approved exceptions

## Deviations
```

## Rules

- Brewing maths (gravity, IBU, colour, scaling) is deterministic, tested code. Never an LLM
  step.
- DB changes are `.sql` files applied with `psql` as `postgres` (docs/OPERATIONS.md §4).
- No task "cleans up" or refactors what the brief did not ask for.
- If a task needs something from the user (a file, a `sudo` command), say so in that task.
