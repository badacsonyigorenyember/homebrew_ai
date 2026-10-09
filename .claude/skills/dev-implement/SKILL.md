---
name: dev-implement
description: Use when an approved plan in docs/work/<slug>/plan.md has unticked tasks to build, or when review or verification findings for that work need fixing.
---

# dev-implement

Build the plan's tasks, with their tests, one commit per task.

First read `.claude/skills/dev-flow/conventions.md`, then `plan.md` and `brief.md` (if any).

## Scope of one run

- Subagent mode: exactly the task(s) or findings named in your prompt.
- Direct mode: the next unticked tasks in order, until done or blocked.

## Per task

1. Check you are on branch `<slug>` and the tasks before this one are ticked. Set
   `Stage: implementing` if it is `approved`.
2. Do the steps. Write the task's tests together with the code, and see each one fail before
   the code that makes it pass exists (or, for a test added afterwards, by briefly breaking the
   code). A test you never saw fail proves nothing.
3. Run the task's tests and the rest of the suite. Read the output. Do not tick or commit with
   failing tests.
4. Tick the task's checkboxes in `plan.md`.
5. Reality differs from the plan? Follow *Changes to the plan* in the conventions. If it touches
   scope, requirements or acceptance criteria, stop and ask (`needs-input`) before going on.
6. Update PROJECT.md per the conventions, then commit the task's files, `plan.md` and
   PROJECT.md with the task's one-line message.

## Fixing findings

For review or verification findings: fix each one named, add or adjust a test that would have
caught it, run the suite, record the fix as a deviation if it changes the plan, and commit
(`Fix <what>`).

## Rules

- Do only what the task says. No extra refactors or cleanups.
- A rule below may be broken only where `plan.md` lists it under *Approved exceptions*. Any
  other conflict between a task and a rule → `needs-input`.
- DB changes: `.sql` files in the repo, applied with `psql` as `postgres` per
  docs/OPERATIONS.md §4. Never write through the Supabase MCP. Never recreate `supabase-kong`.
- Never print `.env`. Don't work around `.claude/hooks/guard.sh`; report what it blocked.
- Three failed attempts at the same problem → stop and report `blocked` with what you tried.
- Use superpowers:systematic-debugging for any failure you don't understand.
