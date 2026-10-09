---
name: dev-flow
description: Use when the user wants a requirement, idea or existing plan in this project taken all the way from brief to merged code, or wants to resume such work in docs/work/<slug>/.
---

# dev-flow

Run the work through its steps with one subagent per step. Your chat with the user holds only
stage summaries, questions, approvals and the test results. You do not read code, write code or
edit docs yourself; the subagents do. Your only edits are the `Status:`/`Stage:` line and the
approval commits.

Read `.claude/skills/dev-flow/conventions.md` first. These steps replace the superpowers
brainstorming → writing-plans → subagent-driven-development → finishing-a-development-branch
chain for this work. Do not invoke those.

## Before step 1

1. Pick the slug (conventions) and say it to the user in one line.
2. Run `git status --short`. If PROJECT.md or CLAUDE.md has uncommitted changes and this is new
   work, ask the user once to commit or stash them. Don't start until they are clean.

## Where to start

| The user gives | Start at |
|---|---|
| a requirement or idea | 1 Brief |
| a path to an existing spec or plan | 2 Plan, with that path as input |
| a slug, or `docs/work/<slug>/` exists | resume, using the table below |

| State on disk | Next step |
|---|---|
| only `brief.md`, `Status: draft` / `approved` | 1 (approval) / 2 |
| `Stage: draft` / `approved` | 2 (approval) / 3 |
| `Stage: implementing` | 3, first unticked task |
| `Stage: review`, no `review.md` or last verdict *ready for testing* | 4 / 5 |
| `Stage: review`, last verdict *fixes needed* | 3 (fix those findings) |
| `Stage: verify`, last `Overall: ✅` / `❌` | ask to ship / route the failures as in step 5 |

If the user asks to skip the brief for a requirement, start at 2 with the requirement text as
input.

## Steps

| # | Skill | Subagents | Gate |
|---|---|---|---|
| 1 | dev-brief | one | **user approves brief** → commit |
| 2 | dev-plan | one | **user approves plan** → commit |
| 3 | dev-implement | **one per task**, in order, never in parallel | questions only |
| 4 | dev-review | one | must-fix → back to 3, then re-review |
| 5 | dev-verify | one | ❌ `Cause: code` → back to 3, then re-verify; ❌ `Cause: decision` → ask the user; all ✅ → **user approves shipping** |
| 6 | dev-ship | one | — |

Fix loops (4 → 3 → 4 and 5 → 3 → 5) run at most 2 rounds each. If findings or failures remain
after that, show them to the user and ask: fix again, accept as they are, or stop.

## Dispatching

Agent tool, `subagent_type: general-purpose`, not in the background, never `isolation:
worktree`. The prompt:

```
You are a dev-flow subagent. Load the project skill `<skill>` with the Skill tool (or read
.claude/skills/<skill>/SKILL.md) and follow it, with .claude/skills/dev-flow/conventions.md.
Work folder: docs/work/<slug>/   Branch: <slug>
Your job: <the step, e.g. "Implement Task 3 only" or "Fix review findings 1 and 4">
Input: <requirement text, or path of the user's doc>
User decisions so far: <answers and feedback, verbatim>
End with the Report block from the conventions.
```

## Handling a report

- `needs-input`: ask the user the questions (use AskUserQuestion when they have options). Keep
  the subagent's recommendation. Then resume that subagent with SendMessage, or dispatch a new
  one with the answers in *User decisions so far*.
- `needs-approval`: show a 3–6 line summary and the file path, and ask for approval or changes.
  Changes → resume or re-dispatch with the feedback. Approval → set `Status: approved` /
  `Stage: approved` and commit exactly the *Commit on approval* paths and message (create the
  branch first if needed).
- `blocked`: tell the user what blocks it and what they can do. Don't work around it.
- `done`: one progress line to the user (`Task 3/7 done: hop loader + 4 tests · a1b2c3d`), then
  the next step.

Approvals come only from the user in this chat, one per gate. Between gates, don't ask "shall I
continue?". Keep going.

## What the user sees

- After step 4: the must-fix and should-fix findings, one line each. Ask about the should-fix
  ones.
- After step 5: read `verification.md` and show the Overall line, *Start here*, and the
  spot-check and regression tables exactly as written there. Then ask to ship.
- At the end: merge sha, branch, and the paths of brief, plan and verification.
