---
name: dev-review
description: Use when all tasks in docs/work/<slug>/plan.md are ticked and the branch diff needs a fresh check against the brief and plan before testing, or when the user asks to review that work.
---

# dev-review

Check the branch with fresh eyes against what was asked. You find and report. You do not fix.

First read `.claude/skills/dev-flow/conventions.md`, then `plan.md` and `brief.md`. If there is
no brief, read the plan's `Source:` doc in its place.
Set `Stage: review`.

## What to check

Read `git diff main...<slug>` and `git log --oneline main..<slug>`, then:

1. **Plan:** every task is done as written, or the difference is recorded under Deviations.
2. **Brief:** every requirement and acceptance criterion is met or covered by a planned check.
3. **Scope:** nothing was changed that the brief and plan did not ask for.
4. **Correctness:** bugs, wrong edge cases, wrong units, maths not done in tested code.
5. **Tests:** they test the critical behaviour named in the plan, and would fail if it broke.
6. **Safety:** no secrets in the diff, DB changes are `.sql` files, guard rules respected.
7. **Records:** PROJECT.md §8 and status columns updated, commits are one line each.

## Output: `docs/work/<slug>/review.md`

```markdown
# Review: <slug>

Diff: main...<slug> at <short sha>  ·  Verdict: ready for testing | fixes needed

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | must-fix | path:line | … | … |
```

Severity: **must-fix** (wrong result, broken requirement, data or secret risk, missing
critical test), **should-fix** (real but harmless now; the user decides), **note** (no action).
Only report what you checked in the code. No style opinions.

Commit `review.md` and `plan.md` (`Add review: <slug>`). Subagent mode: report `done`, with the must-fix and
should-fix items in Summary. Direct mode: show the table.

A re-review after fixes checks only the earlier findings and the new commits, and appends a
`## Re-review <date>` section.
