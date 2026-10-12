# M0 · Pipeline foundations: where code lives, the test harness, run logging

Status: approved
Slug: m0-harness · Branch: m0-harness
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) M0, checkpoint **G0**

## Why
n8n runs no workflows yet, and PROJECT.md §4 leaves open how the recipe pipeline is split inside
n8n and where the deterministic maths runs. Every later milestone (M1–M8) is built test-first
against the 20 briefs in `evals/recipe_briefs.toml`, so the way tests reach n8n and score its
output has to exist, and be agreed, before the first real step is built.

## Goal
The G0 decisions are recorded in PROJECT.md. A test can send a brief's request to the pipeline in
n8n, the pipeline logs each step in `app.run` / `app.run_step`, and the test reads that log back and
scores it against the brief. Only a stub step exists; it fails the real grading on purpose (red).

## Scope
In:
- The G0 decisions (Open questions 1–4), written into PROJECT.md §4 with a one-line *why*.
- A main pipeline workflow in n8n with a test entry point and the run logging pattern.
- One stub step sub-workflow (step 1) with its input/output contract, showing the pattern every
  later step copies.
- Written contracts for steps 0–3 (what goes in, what comes out, the "none / unknown / conflict"
  slot), so M1–M3 build against them.
- The eval harness: a runner that sends briefs and reads results, and pure grader functions with
  unit tests that run without the stack.
- Workflows kept in the repo as files, so they are versioned and reviewable.
- Test data in n8n: each workflow carries a sticky note with ready-to-paste JSON for its
  trigger (b01's request), which the user pins in the editor, so "Execute workflow" runs it and
  each node's input and output can be inspected, including inside the sub-workflows (added
  2026-10-12).

Out:
- Any real step logic (M1 onward). The chat trigger (M8). Contracts for steps 4–16 (each
  milestone writes its own). The maths library (s1). Brewer profile fixtures (M4).

## Requirements
R1. PROJECT.md §4 records: where deterministic logic lives (SQL functions, Code nodes or another
    option), how tests trigger a run, how they read the result, and the contract format. The
    WORKFLOW-ROADMAP G0 row is marked decided.
R2. A pipeline workflow in n8n takes a request text (and optionally a brief id from the eval set) and
    returns a run id. It creates one `app.run` row per run, with the model name.
R3. Every step writes one `app.run_step` row per try: `step`, `try`, `input`, `output`, `ok`, `ms`,
    and `tokens` where an LLM was called. A step that fails writes `ok = false` and the error,
    and the run stops there; nothing fails silently.
R4. Step 1 exists as a stub sub-workflow that copies its input to its output in the step 1
    contract shape, and is called by the main workflow through the same call every later step
    will use.
R5. Contracts for steps 0, 1, 2 and 3 are written down (file and format per R1), each with a legal
    way to say "absent", "unknown" or "conflict" (PROJECT.md §6.3).
R6. A runner sends every brief in `evals/recipe_briefs.toml` (or one, by id) to the pipeline,
    waits for the run to finish, and reads its `run_step` rows.
R7. Grader functions score a run against a brief: per-field compare for step 1 (stated, hints,
    wanted, excluded, inventory, guidance), style-or-alternative for step 2, and the deviation
    match rule for step 3 (same `kind` and same subject). They are pure functions with unit tests
    that do not need the stack.
R8. The runner prints a per-brief pass/fail table and totals per graded step, and can save the
    result so two runs can be compared (Open question 5).
R9. Tests that need the running stack are marked so the default `pytest` run still passes
    without it, as `test_style_codes_exist_in_ref` does today.
R10. Each workflow built in this work is saved in the repo as a file, and the file matches what
    runs in n8n (Open question 4).
R11. Each workflow built in this work has a `Test data` sticky note holding a sample its trigger
    accepts (b01's request; for the pipeline webhook, `brief_id` `editor-b01`). The user pins
    it; webhook calls ignore pins. Pipeline runs started from the editor are told apart from eval
    runs by `eval_id` and can be removed. The notes are in the repo files with no secrets; pins
    are not, so pinning needs no re-export.

## Constraints
- Readable over optimal (PROJECT.md §6.8): someone opening a workflow or SQL file understands
  it from that file alone. No config tables that drive workflow behaviour.
- Brewing maths is deterministic, tested code, never the LLM (CLAUDE.md).
- DB changes are `.sql` files applied as `postgres` (OPERATIONS.md §4); MCP is read-only.
- n8n work follows the `n8n-skills` plugin: validate before publishing, check `connections` after
  every create or update, secrets only in n8n credentials (no tokens in node fields).
- Headless `n8n execute` needs the other broker port (OPERATIONS.md §5).
- `app.run_step` already exists (`db/015_app.sql`): primary key (`run_id`, `step`, `try`).

## Assumptions
- n8n 2.23.4 can reach `supabase-db` with a Postgres credential connecting as `postgres`
  *(unverified: no credential has been checked since the reset)*.
- Python Code nodes need an external task runner this stack does not run *(unverified against
  the n8n 2.23 docs)*.
- The `app` tables are empty and their columns are as DATABASE.md §5 shows *(checked on the
  catalog for `ref`, not re-checked for `app`)*.

## Acceptance criteria
A1. PROJECT.md §4 holds the four G0 decisions, each with a *why* (R1).
A2. Running the runner on b01 creates one `app.run` row and a `run_step` row for step 1 with
    `ok = true` (R2, R3, R4).
A3. A forced failure in the stub (e.g. a bad input) gives a `run_step` row with `ok = false` and
    the error text, and the runner reports the brief as failed, not as passed (R3, R6).
A4. Contract files for steps 0–3 exist, and each has an absent/unknown/conflict slot (R5).
A5. The runner on all 20 briefs prints a table with 20 rows; step 1 grading is red (the stub
    copies the request, so the fields are wrong), and the totals are printed (R6, R8).
A6. Grader unit tests pass without the stack, including: a deviation with the same kind but
    another subject does not match; an alternative style counts as a pass (R7, R9).
A7. `pytest` with the stack stopped passes, skipping only the marked tests (R9).
A8. The workflow files in the repo match the workflows in n8n (compared by node names and
    connections) (R10).
A9. Each workflow's `Test data` note holds JSON that, pinned on its trigger, runs the workflow
    with "Execute workflow" in the editor. For `Recipe pipeline` the run is logged with
    `eval_id = 'editor-b01'`, and each node and the step 1 sub-execution show their input and
    output (checked by the user). With the user's pin present, a webhook POST runs on the posted
    request (test). The repo files hold the notes and no secret (R10, R11).

## Open questions
1. Where does deterministic logic live? — options: a) SQL functions in `db/*.sql`, called from
   n8n's Postgres node, tested by pytest through `psycopg`; b) JavaScript in Code nodes, tested
   only by running workflows; c) Python Code nodes with an external task runner — recommend a:
   it is testable with the tools the repo already has, readable as one SQL file per step, and the
   data is already in Postgres. Code nodes only reshape JSON.
2. How does a test start a run? — options: a) a webhook on the pipeline workflow; b) the
   `n8n execute` CLI; c) the n8n MCP `execute_workflow` tool — recommend a: one HTTP call from
   pytest, returns the run id, and the same entry point serves the chat trigger later.
3. Contract format? — options: a) JSON Schema files, one per step, in the repo, checked in the
   workflow and in the tests; b) prose tables in a doc — recommend a: code can check it on both
   sides.
4. How do workflow files get into the repo? — options: a) export after every change (CLI export
   or the MCP's workflow details) into `n8n/workflows/<name>.json`; b) author in the repo with the
   Workflow SDK and push to n8n — recommend a for now: n8n stays the place where workflows are
   edited and run; the file is the reviewable copy.
5. Keep run results? — options: a) save each full run as `evals/results/<date>-<milestone>.json`,
   committed at checkpoints only; b) print only — recommend a: G1–G6 compare runs.

## Deviations
- 2026-10-12 · Scope: added test data in n8n (scope item, R11, A9; plan Task 8) — the user asked
  to run the workflows in the editor and watch the data move from node to node, and asked for it
  in this work rather than a later one. They chose a sticky note with ready-to-paste JSON in each
  workflow, which they pin themselves; the pipeline sample is tagged `editor-b01`.
