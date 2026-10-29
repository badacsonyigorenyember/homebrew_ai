---
name: pause-work
description: Use when the user wants to pause, wrap up or stop for now and continue later, and background agents or tasks are still running in this session. Stops them safely and writes down their progress so the work can be resumed.
---

# pause-work

Stop every running background task without losing its progress, and write one note that lets
the work resume later. The conversation itself usually stays (the user continues in the same
context), so the note covers only what lives in the background tasks and on disk: what each
task finished, what it left half-done, and what it changed outside the repo.

Don't start new work, don't fix anything you find, and don't revert anything.

## Steps

1. **List what is running.** The background agents and shell tasks started in this session that
   have not reported completion. Note for each: its job (skill, task number), and when it
   started. If nothing is running, say so and go to step 4.

2. **Ask each running agent to stop at a safe point** (SendMessage to its agent id):
   - Start no new step, test run or import. A command already running may finish.
   - If it is partway through an n8n import or publish, a SQL file or a commit, finish only
     that one, so no live system is left half-changed.
   - Commit nothing half-done; leave uncommitted changes in place; revert nothing.
   - Hand back a progress report: checkboxes done; each file changed and whether it is
     committed (sha) or not; live-system changes (n8n workflow name, id, published version,
     whether it matches the repo file; SQL applied; test rows or runs left in the database);
     tests run and their results; the exact next step; traps and deviations not yet written
     down. Status `blocked`, Blocked by "paused by the user".

   Wait for the reports. Stop a shell task, or an agent that has not answered after its
   running command should have finished, with TaskStop, and record that it was killed.

3. **Check the reports against what is real.** Reports are claims, not proof:
   - `git status --short`, `git log --oneline -5`, and `git diff --stat` on the branch.
   - For n8n: compare the live workflow with the repo file (n8n MCP `get_workflow_details`,
     read-only), when a report names an import or a killed task may have been importing.
   - For the database: query the catalog (read-only Supabase MCP) for objects a report says it
     created, and for leftover test runs if it names any.
   - The plan's checkboxes and `Stage:` line.
   Note every difference between a report and what you see.

4. **Write the pause note.** For dev-flow work: `docs/work/<slug>/paused.md`. Otherwise give
   the note in chat only. Contents, in this order:
   - `Paused: <date>` · branch · last commit · the dev-flow step and task that was running.
   - **Resume with:** the one next action, exact (`/dev-flow docs/work/<slug>`, then "Task 7:
     finish the checkbox …").
   - **Per background task:** job, how it ended (reported / killed), done, half-done,
     uncommitted files, live-system changes and whether they match the repo, tests and
     results.
   - **Open items:** decisions waiting on the user, unverified claims, differences found in
     step 3, deviations not yet in `plan.md`.
   - **Do not:** anything that would break on resume (for example "don't re-import from the
     repo file before Task 7's edit is in it").

   Write facts you checked, and mark anything you could not check as *(unverified)*.
   Don't commit the note, or anything else, unless the user asks: the half-done work stays as
   it is, and the note says so.

5. **Close.** Give the user: what was stopped, the note's path, the resume line, and the
   uncommitted files. Nothing else.

## On resume

dev-flow reads `paused.md` before choosing the next step, finishes or redoes what it lists,
and deletes it when the half-done work is committed.
