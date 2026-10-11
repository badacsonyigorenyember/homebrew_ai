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

## Part 1: Summary

Readable at a glance: every line starts with emojis, and the status emoji says whether it went
well. Write it **last**, after Parts 2 and 3 have run, because it includes their results. It is
what the user sees before they approve shipping.

Status emojis: ✅ went well · ⚠️ passed with warnings · ❌ a problem (a failure, a must-fix, an
error), even if it was fixed later; then say `🔧 fixed in <sha>` · ⏭️ skipped.

```markdown
## Part 1: Summary

🎯 **Goal:** <a few words or one sentence: what the work set out to do>

🛠️ **How:** <one sentence: how it was achieved>

🤔 **Why this way:** <one sentence: why this way rather than another>

🏁 **Result:** <one sentence: what exists or works now, with counts where they matter>

### 🚦 Steps

- ⏭️ 📝 **Brief:** <1–2 sentences: what happened, or why it was skipped>
- ✅ 🗺️ **Plan:** <1–2 sentences>
- ⚠️ 🔨 **Implement:** <1–2 sentences: tasks done, fix rounds>
  - ⚠️ <each warning or error, one short line>
- ❌ 🔍 **Review:** <1–2 sentences: verdict, findings> 🔧 fixed in <sha>
- ✅ 🧪 **Verify:** <1–2 sentences> 🧮 spot checks ✅ N/N · 🧪 tests ✅ M/M

👀 **Start here:** <the one place to look first, and what you should see there>

📁 **Changed files:**
- `<path>`
```

- One line per step, in flow order, every step listed (`⏭️` with the reason if it did not run).
- The step lines come from `brief.md` / `plan.md` (ticks, `## Deviations`), `review.md`,
  `git log main..<slug>`, this run's Parts 2 and 3, and the *Flow so far* notes in your prompt
  (warnings and errors the earlier subagents reported). Name every warning or error you find
  there, one sub-bullet each under the step's line; don't drop any to make a step look green.
- 📁 **Changed files:** every path from `git diff --stat main...<slug>`, one per line, paths
  only. Don't describe the changes.

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
with their Cause in Summary. Direct mode: show the Overall line and Part 1 as written; then list
only the failing rows of Parts 2 and 3, not the passing ones. `verification.md` itself keeps
every row.

## Re-verify

After fixes, append `## Re-verify <date>` with every check and the whole suite run again (same
format, earlier results kept above for history), and rewrite the top `Overall:` line and Part 1
from the new run (the earlier ❌ stays, with its 🔧 fix).
