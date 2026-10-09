---
name: dev-verify
description: Use when the work in docs/work/<slug>/ is implemented and reviewed and needs testing, or the user asks what changed, where to look, or whether the tests pass for that work.
---

# dev-verify

Produce `docs/work/<slug>/verification.md` with three parts, and **run everything you list**.
An expected value without an actual value from a real run is not a check.

First read `.claude/skills/dev-flow/conventions.md`, `plan.md`, `review.md` and `brief.md` (or,
without a brief, the plan's `Source:` doc: its acceptance criteria, Done-when lines and review
focus are what you check). Set `Stage: verify`. Collect the changes with `git diff --stat main...<slug>`.

## Part 1: Where to look

For a human starting a manual check. Summarise; don't list every item.

- **Start here:** the one place to look first, and what you should see there.
- Then one short block per kind of change that happened. Skip kinds that did not change:
  - **Database:** schemas, tables, functions and views added, changed or removed, with
    summarised counts ("116 BJCP styles added to `ref.style`", "all rows with id < 100 removed").
  - **Workflows** (n8n), **scripts and services:** for each, its name, then what it does, what
    problem it solves, and how it solves it, 1–2 sentences each.
  - **Files and config:** what changed and where.

## Part 2: Spot checks

Quick, read-only commands that confirm the acceptance criteria and the data. Each must run
as-is from the repo root, print no secrets, and give a short output. For each, run it, then
write it like this:

````markdown
### ✅ C1 · BJCP styles loaded (A1)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.style where system = 'BJCP'"
```

| Expected | Actual | Result |
|---|---|---|
| 116 | 116 | ✅ pass |
````

The heading starts with ✅ or ❌. `Actual` is the real output, trimmed. Never edit the expected
value to match. Under each ❌ add one line: `Cause: code` (the code is wrong) or `Cause: decision`
(the expectation may be wrong, or something is missing that only the user can supply), with why.

## Part 3: Regression tests

Tests that protect critical behaviour (the plan's *Critical behaviour and its tests* table),
not item counts. Add any critical test the plan named that is missing, and commit it
(`Add tests for <what>`). Then run the whole suite and record:

```markdown
Command: `<exact command>`  ·  Result: ✅ 24 passed  |  ❌ 22 passed, 2 failed

| Test | Protects | Result |
|---|---|---|
| tests/test_gravity.py::test_og_from_grist | OG maths matches Palmer's worked example | ✅ |

Failures:
- `tests/…::test_…`: <assertion, expected vs got, one line>
```

## Finish

Top of the file: one line, `Overall: ✅ all N checks and M tests pass` or `Overall: ❌ …
failed: C3, test_x`. Commit `verification.md` and `plan.md` (`Add verification: <slug>`).

Do not fix failures here. Subagent mode: report `done` with the Overall line and the failed IDs
with their Cause in Summary. Direct mode: show the Overall line, the Start here block, and both
tables.

## Re-verify

After fixes, append `## Re-verify <date>` with every check and the whole suite run again (same
format, earlier results kept above for history), and rewrite the top `Overall:` line from the
new run.
