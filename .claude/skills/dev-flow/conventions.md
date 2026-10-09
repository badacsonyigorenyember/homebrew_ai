# dev-flow conventions

Shared by `dev-brief`, `dev-plan`, `dev-implement`, `dev-review`, `dev-verify`, `dev-ship` and
the `dev-flow` orchestrator. Every step skill reads this file first.

These skills replace the superpowers chain (brainstorming, writing-plans,
subagent-driven-development, executing-plans, finishing-a-development-branch) for this work.
Do not invoke those, and ignore "REQUIRED SUB-SKILL" or similar directives inside source docs.

## Work folder and branch

- One piece of work = one folder `docs/work/<slug>/` and one branch `<slug>`.
  `<slug>` is short kebab-case naming the outcome (`fill-ref`, `hop-loader`). No date.
  The orchestrator picks it and passes it on; a step skill picks it only when run directly.
- Files in the folder:

  | File | Written by | Holds |
  |---|---|---|
  | `brief.md` | dev-brief (optional) | What is wanted and why. Not how. |
  | `plan.md` | dev-plan, ticked by dev-implement | Step-by-step tasks, and the `Stage:` line |
  | `review.md` | dev-review | Findings on the diff |
  | `verification.md` | dev-verify | Where to look, spot checks, regression test results |

- The files on disk are the state. Any step can be resumed by reading the folder. The `Stage:`
  line at the top of `plan.md` is one of: `draft`, `approved`, `implementing`, `review`,
  `verify`, `shipped`. `brief.md` has `Status: draft` or `Status: approved`.
- Work in this checkout on a plain branch. **Never a git worktree** (CLAUDE.md). The first step
  that commits creates the branch: if `git branch --show-current` is `main`, run
  `git switch -c <slug>` (or `git switch <slug>` if it exists).

## Commits

- One logical section per commit. Message: a single imperative line, at most 60 characters.
  **No body and no trailer lines (no `Co-Authored-By`).** Example: `Add hop loader with tests`.
- Stage explicit paths only (`git add <path> ...`). Never `git add -A` or `git add .`: the
  checkout often has unrelated changes from the user.
- Files that belong to this work: everything in `docs/work/<slug>/`, the paths in the plan's
  Files table, and PROJECT.md / CLAUDE.md edits made for this work. Uncommitted changes there are
  this work's own (an earlier subagent may have left them): commit them. If any **other** file
  you need to commit has uncommitted changes, do not commit it; ask instead.
- Commit the brief and the plan only after the user approved them.
- A new piece of work starts with PROJECT.md and CLAUDE.md free of uncommitted changes, so the
  work's commits never carry someone else's edits. If they are dirty, ask the user to commit or
  stash them first.

## Changes to the plan (deviations)

When reality differs from the brief or plan, edit the affected text so it describes the current
plan, **and** add a dated line to the `## Deviations` section at the bottom of that file:
`- 2026-10-09 · Task 3: <what changed> — <why>`.
Record it in `plan.md` always, and also in `brief.md` when a requirement, scope item or
acceptance criterion changes. A change to scope, requirements or acceptance criteria needs the
user's answer first; an implementation detail does not.

## PROJECT.md

Follow CLAUDE.md and PROJECT.md §10 in the same commit as the work: a dated §8 entry (newest
first) linking the work folder, and the status columns the work touches. Never change §2, §3 or
§6 without the user's agreement.

## Asking the user

Each question has: the question, 2–4 options, your recommendation with a one-line reason.
Ask only what you cannot settle from the code, the docs or a sensible default.

## Report block (subagent mode)

If your prompt says you are a **dev-flow subagent**, you cannot talk to the user. Do not wait
for answers. End your final message with exactly this block, and nothing after it:

```
## Report
Status: done | needs-input | needs-approval | blocked
Summary: 2–5 plain lines on what was done (tables stay in the files, not here)
Files: paths written or changed
Commits: <short sha> <subject>, one per line, or "none"
Commit on approval: paths to commit and the one-line message, or "none"
Questions:
1. <question> — options: a) … b) … — recommend: a, because …
Blocked by: <what stops you>, or "none"
```

If you are not a subagent (the user invoked the skill directly), ask the user directly and
wait, then carry on yourself.
