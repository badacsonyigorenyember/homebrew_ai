# M0 · Pipeline foundations — implementation plan

Stage: verify
Brief: [brief.md](brief.md)
Branch: m0-harness

## Approach

The plan follows the brief's recommended answers to its Open questions 1–5 (a, a, a, a, a).
Approving the plan confirms them. Task 1 then writes them into PROJECT.md §4, so every later
task builds on recorded decisions.

- **Where the logic lives (Q1 a).** Deterministic logic is SQL functions in `db/*.sql`, called from
  n8n's Postgres node and tested by pytest through `psycopg`. Code nodes only reshape JSON. M0
  has no step logic yet, so no step function is written here.
- **How tests start a run (Q2 a).** The main workflow `Recipe pipeline` has a webhook,
  `POST http://localhost:5678/webhook/recipe-pipeline`, with body
  `{request, brief_id?, model?}`. It answers once the run has ended, with
  `{run_id, ok, failed_step?, error?}`. Tests and the runner then read `app.run` and
  `app.run_step` through `loaders.db.connect()`. The database is the record. The HTTP answer is
  only the handle.
- **Contracts (Q3 a).** Each contract is a JSON Schema file (draft 2020-12, falling back to
  draft-07 if the extension rejects 2020-12). There is one file per step and side, in
  `shared/contracts/`. That is the only repo folder n8n already sees (mounted at
  `/data/shared`, and `N8N_RESTRICT_FILE_ACCESS_TO=/data/shared`), so no compose change is
  needed. Both sides use one validator: the `pg_jsonschema` extension (0.3.3, a supautils
  privileged extension, so `postgres` can create it). It gives
  `extensions.jsonschema_validation_errors(schema json, instance json) → text[]`. A small helper
  workflow `Check contract` reads the file and calls that function. Tests call the same
  function, so the workflow and the tests cannot disagree about what is valid.
- **The per-step pattern (R3, R4).** Each step is a sub-workflow that checks its input, does its
  work and checks its output, both checks through `Check contract`. The main workflow calls it
  with an *Execute Workflow* node (wait for completion, error output on). Then one Postgres node
  logs the success, or another logs the failure. A failure ends the run. Later steps copy this
  block. The timing comes from a timestamp set just before the call, so no Code node is needed.
- **Logging needs a small schema change.** `app.run.brief_id` is `not null`, but the `app.brief`
  row is only written by step 1 (m1 R4), and `app.run_step` has no column for the error. Task 2
  makes `brief_id` nullable. It adds `app.run.eval_id`, `finished_at` and `ok`, plus
  `app.run_step.error`, with a check that a failed step has an error and a passed one has none.
  The tables are empty (measured 2026-10-12), so nothing is migrated.
- **Workflow files (Q4 a).** Workflows are edited in n8n. `python -m evals.workflows` exports
  them with `n8n export:workflow` into `n8n/workflows/<name>.json`, and a stack test compares
  node names and connections.
- **Eval harness.** `evals/grade.py` holds pure grader functions with unit tests, no stack
  needed. `python -m evals.run` sends the briefs, reads the runs back and prints the table. With
  `--save` it also writes `evals/results/<date>-<label>.json` (Q5 a, committed at checkpoints
  only).
- **Stack-marked tests (R9).** Tests that need the running stack carry
  `@pytest.mark.stack`. `tests/conftest.py` skips them when Postgres or n8n can't be reached.
  `test_style_codes_exist_in_ref` gets the marker too. Today it *fails* when the stack is down
  (its docstring says so), so A7 needs it.
- **The stub must be red.** If the step 1 stub returned empty fields, it would pass every field
  of b04, whose request states nothing (measured). So the stub copies the request text into
  `wanted`, and every brief fails at least that field.

Measured while planning (2026-10-12): n8n 2.23.4, no workflows. Credentials: `Postgres account`
(`fDjeFLjBj3r9berH`, settings unverified) and `Ollama account`. n8n reaches `supabase-db:5432`
over `aihomebrewassistant_default` (TCP connect from the n8n container; the host aliases are
`supabase-db` and `db`). `pg_jsonschema` 0.3.3 is available but not installed. The 8 `app`
tables are empty, and `app.run` / `app.run_step` columns match `db/015_app.sql`. The Python
`jsonschema` package is not installed, and this plan does not need it.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `PROJECT.md` | changed | §4 G0 decisions (R1), status rows, §8 entries |
| `docs/WORKFLOW-ROADMAP.md` | changed | G0 marked decided, with the measured bar (R1) |
| `docs/DATABASE.md` | changed | `app.run` / `run_step` columns, `pg_jsonschema` in `extensions` |
| `docs/OPERATIONS.md` | changed | §5: pipeline webhook, workflow export command, what the Postgres credential connects as |
| `pytest.ini` | changed | registers the `stack` marker |
| `tests/conftest.py` | new | skips `stack` tests when Postgres or n8n is down |
| `tests/test_recipe_briefs.py` | changed | `test_style_codes_exist_in_ref` marked `stack` |
| `db/015_app.sql` | changed | `pg_jsonschema`; run-log columns and check |
| `tests/test_run_log.py` | new | the run-log constraints (stack) |
| `shared/contracts/step{0,1,2,3}.{input,output}.schema.json` | new (8 files) | step contracts (R5) |
| `tests/test_contracts.py` | new | contract files: shape, absent slots, validator examples |
| `evals/__init__.py` | new | package marker, like `loaders/` |
| `evals/grade.py` | new | pure graders for steps 1–3 (R7) |
| `tests/test_grade.py` | new | grader unit tests (A6) |
| `evals/workflows.py` | new | export n8n workflows to `n8n/workflows/` (R10) |
| `tests/test_workflows.py` | new | export shaping (unit) and repo-vs-n8n match (stack, A8) |
| `n8n/workflows/recipe-pipeline.json` | new | main workflow, exported |
| `n8n/workflows/step-1-read-request.json` | new | step 1 stub, exported |
| `n8n/workflows/check-contract.json` | new | contract-check helper, exported |
| `tests/test_pipeline.py` | new | end-to-end run logging (stack, A2, A3) |
| `evals/run.py` | new | the runner (R6, R8) |
| `tests/test_run.py` | new | runner summary (unit), runner against n8n (stack) |
| `evals/results/<date>-m0.json` | new | the G0 checkpoint run (A5) |

## Tasks

### Task 1: the G0 decisions are recorded, and stack tests skip cleanly
Why: R1, R9; A1, A7.
- [x] PROJECT.md §4: replace the sentence "How the parts are split inside n8n, including where
      the deterministic maths (P2) runs, is discussed when the pipeline is built." with a
      **Pipeline build (G0, decided <date>)** note. It lists the five decisions from the Approach,
      each with a one-line *why* (the brief's reasons): SQL functions + Postgres node, Code
      nodes only for glue; a webhook starts a run, and `app.run` / `app.run_step` are read back;
      JSON Schema files in `shared/contracts/`, checked with `pg_jsonschema` on both sides;
      workflows edited in n8n and exported to `n8n/workflows/`; eval results in
      `evals/results/`, committed at checkpoints.
- [x] `docs/WORKFLOW-ROADMAP.md` §2 G0: replace "*Leaning, for you to decide:*…" with the
      decisions (one line each) and a link to PROJECT.md §4. Leave the **Bar** line; Task 7 adds
      the measured result.
- [x] `pytest.ini`: add `markers = stack: needs the running stack (Postgres and n8n)`.
- [x] `tests/conftest.py`: a session-cached `stack_up()` is true when `loaders.db.connect()`
      succeeds (pass `connect_timeout=3`; add an optional `connect_timeout` argument to
      `connect` only if needed) **and** `GET http://localhost:5678/healthz` answers 200 within
      3 s. In `pytest_collection_modifyitems`, add
      `pytest.mark.skip(reason="stack not running: <which part>")` to every item marked `stack`
      when it is false.
- [x] `tests/test_recipe_briefs.py`: mark `test_style_codes_exist_in_ref` with
      `@pytest.mark.stack`, and change the docstring's "fails when the stack is not running" to
      "is skipped when…".
- [x] Run `.venv/bin/pytest`, expect 68 passed (stack up). Run
      `.venv/bin/pytest -m "not stack"`, expect 67 passed, 1 deselected.
Done when: §4 holds the five decisions, each with its *why*, and both pytest runs give the stated
counts.
Commit: `Record G0 decisions and mark stack tests`

### Task 2: the run log can record a run before step 1, and every failure has its error
Why: R2, R3; A2, A3.
- [x] `db/015_app.sql`: near the top, `create extension if not exists pg_jsonschema with schema
      extensions;` with a comment ("step contract checks, docs/work/m0-harness"). In the
      `create table` text, show the new columns too, so the file reads as the current design.
      At the end, add idempotent alters for the live tables:
      ```sql
      alter table app.run alter column brief_id drop not null;   -- step 1 writes app.brief
      alter table app.run add column if not exists eval_id     text;        -- 'b01' when sent by the runner
      alter table app.run add column if not exists finished_at timestamptz; -- null = still running or crashed
      alter table app.run add column if not exists ok          boolean;     -- null until finished
      alter table app.run_step add column if not exists error  text;
      alter table app.run_step drop constraint if exists run_step_error_check;
      alter table app.run_step add  constraint run_step_error_check check (ok = (error is null));
      ```
- [x] Apply twice:
      `docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/015_app.sql`.
      Both runs give no error. Then check the catalog: the extension is in `extensions`, the 4
      new columns exist, `brief_id` is nullable, and the tables are owned by `postgres`.
- [x] Write `tests/test_run_log.py` (all `stack`; each test in a transaction that is rolled
      back):
      `test_run_starts_without_brief` (insert `app.run (model, eval_id)` with no `brief_id`
      succeeds); `test_failed_step_needs_error` (`ok = false, error = null` raises
      `psycopg.errors.CheckViolation`); `test_passed_step_has_no_error` (`ok = true` with an
      error raises the same); `test_jsonschema_errors_available` (`select
      extensions.jsonschema_validation_errors('{"type":"object"}', '1')` returns one error).
- [x] `docs/DATABASE.md`: the `run` / `run_step` diagram entries and the table row get the new
      columns, with a one-line why (a run exists before its brief; a failure always says why).
      The extensions note also gets `pg_jsonschema`.
- [x] Run `.venv/bin/pytest`, expect all pass.
Done when: the SQL file applies twice cleanly, and the 4 tests pass.
Commit: `Add run-log columns and pg_jsonschema`

### Task 3: contracts for steps 0–3 exist, each with a legal "absent" slot
Why: R5; A4. Field lists follow the draft briefs m1 R1, m2 R1/R8 and m3 R1. They are first
versions: M1–M3 may change them, with a deviation in their own plan.
- [x] Write 8 files `shared/contracts/step<N>.<input|output>.schema.json`. Each has `$schema`,
      `title`, a `description` that says what the step does and where its slot for absent,
      unknown or conflict is, `type: object`, `required` (all listed fields) and
      `additionalProperties: false`. Every input has `run_id` (integer). Use no `$ref` to other
      files: a field that carries an earlier step's output is `type: object`, and its
      description names the contract that already checked it.

      | Contract | Fields | Absent / unknown / conflict slot |
      |---|---|---|
      | step0.input | `run_id`, `profile_id` (integer or null = the default profile) | `profile_id: null` |
      | step0.output | `batch_l`, `efficiency_pct`, `boil_off_l_h`, `losses_l`, `grain_abs_l_kg` (numbers); `water` {`ca`,`mg`,`na`,`so4`,`cl`,`hco3`: number or null}; `units` (`metric`\|`us`); `inventory` [{`raw_name`, `ingredient_id` (integer or null), `amount`, `unit` (`g`\|`kg`\|`ml`\|`l`\|`pack`)}] | water ion `null` = unknown; `ingredient_id: null` = not in the catalogue |
      | step1.input | `run_id`, `request` (string, `minLength: 1`) | none (the input is the user's text) |
      | step1.output | `named` (string or null); `stated` {optional `batch_l` 1–1000, `abv` 0–20, `og` 1.000–1.200, `ibu` 0–200, `srm` 0–100; no other key}; `hints` (array, enum: bitter, hoppy, juicy, dry, crisp, full, chewy, malty, darker, stronger, session); `wanted`, `excluded`, `inventory`, `unknown` (arrays of strings); `guidance` (boolean) | `named: null`; `unknown` for words that fit no field |
      | step2.input | `run_id`, `brief` (object, step1.output), `guide_preference` (`any`\|`bjcp`\|`ba`) | none |
      | step2.output | `style` ({`id` integer, `guide`, `code`, `name`} or null); `unknown_reason` (string or null); `alt_styles` (array of codes); `candidates` (≤ 5 × {`guide`, `code`, `score` number}); `scores` (object of signal → number); `mismatch` ({`named`, `range`, `chosen`} or null); `guide_reason` (string) | `style: null` with `unknown_reason`; `mismatch: null` |
      | step3.input | `run_id`, `brief` (object, step1.output), `style` (object, step2.output) | none |
      | step3.output | `deviations` [{`kind` (`ingredient`\|`number`\|`mismatch`\|`conflict`), `subject`, `from`, `level` (`out_of_style`\|`changes_style`\|null), `requested_by` (`user`\|`model`), `because`}]; `unrated` (array of strings); `guidance` (boolean) | `kind: conflict`; `unrated` = ingredients `level()` cannot rate (unknown) |
- [x] Write `tests/test_contracts.py`:
      - `test_contract_files_complete` (no stack): exactly the 8 files exist. Each parses, has
        `$schema`, `title`, `description`, `required` covering every property, and
        `additionalProperties: false`. Every input requires `run_id`.
      - `test_every_output_has_an_absent_slot` (no stack): an explicit dict in the test names
        each output's slot from the table above (e.g. `step1.output` → `named` allows `null`,
        `unknown` is an array). The test checks each slot is in the schema.
      - `test_schemas_valid` (stack): `extensions.jsonschema_is_valid(schema)` is true for all 8.
      - `test_examples` (stack): per contract, one good example that uses its absent slot gives
        `[]` from `jsonschema_validation_errors`. Bad examples give at least one error:
        `step1.input` with `request: ""`, `step1.output` with hint `funky` and with
        `stated.abv = 45`, `step2.output` without `unknown_reason`, `step3.output` with kind
        `typo`. Examples are small dicts in the test.
- [x] Run `.venv/bin/pytest tests/test_contracts.py`, expect all pass. Run the full suite.
Done when: 8 contract files, and the 4 tests pass.
Commit: `Add JSON Schema contracts for steps 0-3`

### Task 4: graders score a run against a brief
Why: R7; A6. The step 3 rule ("same kind, same subject") is written here, in code, as
WORKFLOW-ROADMAP §3 asks.
- [x] `evals/__init__.py` (empty) and `evals/grade.py`. Pure functions, no I/O:
      - `grade_step1(brief: dict, output: dict | None) -> dict[str, bool]`. Keys: `stated`,
        `hints`, `wanted`, `excluded`, `inventory`, `guidance`. Lists compare as sets of
        trimmed, lower-cased strings. `stated` compares the same keys with numbers equal within
        1e-9. `guidance` compares as a bool. If `output` is None, every field is False.
      - `grade_step2(brief, output) -> bool`: `output["style"]["code"]` is `brief["style"]` or
        in `brief["alt_styles"]`. False when the output is None or `style` is null.
      - `subject_key(kind: str, text: str)`. For `number` and `mismatch`: the quantity named
        (`batch_l`, `abv`, `og`, `ibu`, `srm`), found as a whole word, case-insensitive
        ("IBU 50" → `ibu`, "name 'imperial stout' with ABV 4" → `abv`); no quantity → the
        lower-cased text. For `conflict`: the frozenset of RECIPE-ROADMAP §7 hint rows whose
        words appear ("'bone dry' vs 'full and chewy'" → {`dry/crisp`, `full/chewy`}).
        Hold the rows in a small dict in the module, the same rows as
        `tests/test_recipe_briefs.py::HINT_ROWS`. For `ingredient`: the lower-cased, trimmed text.
      - `deviation_matches(expected: dict, got: dict) -> bool`. Same `kind`, and the subjects
        match. Expected uses `what`, the pipeline uses `subject`. For `ingredient` they match
        when the expected word appears as a whole word in the pipeline's subject ("rice" in
        "flaked rice"); for the other kinds the keys must be equal.
      - `grade_step3(brief, output) -> bool`. Every expected deviation matches a different found
        one, and no found deviation is left unmatched. False when the output is None.
      - `grade_run(brief, steps: dict[int, dict | None]) -> dict` gives
        `{"step1": {...fields, "ok": all}, "step2": bool, "step3": bool, "passed": all three}`.
        A step without a passed `run_step` row is graded with output None.
- [x] Write `tests/test_grade.py`. Each case uses a real brief from `evals/recipe_briefs.toml`
      where one fits:
      `test_step1_all_fields_right`; `test_step1_each_field_can_fail` (one wrong field →
      only that field False); `test_step1_order_and_case_ignored`;
      `test_step1_missing_output_fails_every_field`; `test_step2_expected_style_passes`;
      `test_step2_alternative_style_passes` (b05 with `20C`, A6); `test_step2_other_style_fails`;
      `test_step2_unknown_style_fails`; `test_same_kind_other_subject_does_not_match` (b08 IBU vs
      a found number deviation on ABV, A6); `test_other_kind_same_subject_does_not_match`;
      `test_ingredient_word_inside_subject_matches` (b16 rice / "flaked rice");
      `test_conflict_subject_is_hint_rows` (b11);
      `test_step3_extra_deviation_fails`; `test_step3_missing_deviation_fails`;
      `test_step3_none_expected_none_found_passes`.
- [x] Run `.venv/bin/pytest tests/test_grade.py`, expect all pass. Run the full suite.
Done when: the graders exist and the tests pass without the stack
(`.venv/bin/pytest -m "not stack"`).
Commit: `Add pure graders for steps 1-3 with tests`

### Task 5: workflows can be exported into the repo
Why: R10; A8 (the comparison runs in Task 6, once workflows exist).
- [x] `evals/workflows.py`:
      - `export_all() -> list[dict]` runs
        `docker exec n8n n8n export:workflow --all --pretty` and parses the JSON array. If
        stdout carries log lines and is not pure JSON, export with
        `--output=/data/shared/.n8n-export.json` instead. That is `shared/.n8n-export.json` on
        the host, root-owned (OPERATIONS §5). Read it, then remove it. Record which way works in
        OPERATIONS §5.
      - `shape(workflow: dict) -> dict` keeps `id`, `name`, `nodes`, `connections` and
        `settings`, and drops the rest (timestamps, version ids, `shared`, `pinData`), so a file
        changes only when the workflow does.
      - `file_name(name: str) -> str`: lower-case, each run of non-alphanumerics → `-`, trimmed,
        plus `.json` ("Step 1 · read request" → `step-1-read-request.json`).
      - `node_graph(workflow) -> (set[str], dict)`: node names and connections, for comparing.
      - CLI `python -m evals.workflows` writes each shaped workflow to `n8n/workflows/` with
        `json.dumps(..., indent=2, ensure_ascii=False)` and a trailing newline, and prints the
        paths.
- [x] Write `tests/test_workflows.py`: `test_shape_drops_volatile_fields` and
      `test_file_name` (no stack, made-up workflow dicts); `test_repo_files_match_n8n` (stack):
      for every workflow in `export_all()`, a file `n8n/workflows/<file_name>` exists, and
      `node_graph` is equal; no file without a workflow. With no workflows in n8n yet, it passes
      on both being empty.
- [x] Run `.venv/bin/pytest tests/test_workflows.py`, expect all pass.
Done when: the CLI runs (0 workflows today) and the 3 tests pass.
Commit: `Add n8n workflow export to the repo`

### Task 6: a request runs through n8n and leaves its run log
Why: R2, R3, R4, R10; A2, A3, A8. Load the `n8n-skills` skills before building
(`using-n8n-skills-official`, then `n8n-workflow-lifecycle-official`,
`n8n-subworkflows-official`, `n8n-error-handling-official`, `n8n-node-configuration-official`).
Follow the n8n MCP order: SDK reference → suggested nodes → `get_node_types` → validate → create
→ check `connections` after every create or update → publish.
- [x] **Check the Postgres credential first.** Build `Check contract` (below) and run it
      through the MCP `test_workflow` with a temporary query `select current_user,
      current_database(), inet_server_addr()`. Expect `postgres`, `postgres`, the `supabase-db`
      address. If not, stop and ask the user to fix `Postgres account` in the n8n UI: host
      `supabase-db`, port 5432, database `postgres`, user `postgres`, password =
      `POSTGRES_PASSWORD` from `.env`. **The user enters the password**; never read or type it.
      Record what it connects as in OPERATIONS §5.
- [x] Workflow **`Check contract`** (trigger *When Executed by Another Workflow*, inputs
      `contract` string and `value` object):
      *Read file* `/data/shared/contracts/{{contract}}.schema.json` → *Extract from File* (JSON)
      → Postgres
      `select coalesce(extensions.jsonschema_validation_errors($1::json, $2::json), '{}') as errors`.
      Pass both parameters as one expression that returns an array of `JSON.stringify(...)`
      strings: a comma-separated parameter list splits JSON on its commas. Confirm the option
      with `get_node_types`. Then *If* errors is empty: return `{ok: true}`; else *Stop and
      Error* with `contract <contract>: <errors joined by "; ">`.
- [x] Workflow **`Step 1 · read request`** (stub; trigger inputs `run_id`, `request`): call
      `Check contract` with `step1.input` → *Set* "Stub: copy request" builds the step 1 output:
      `named: null, stated: {}, hints: [], wanted: [request], excluded: [], inventory: [],
      guidance: true, unknown: []` → call `Check contract` with `step1.output` → return the
      output. A sticky note says: stub for M0; it copies the request into `wanted` so grading is
      red; M1 replaces the middle node.
- [x] Workflow **`Recipe pipeline`**:
      *Webhook* (`POST`, path `recipe-pipeline`, respond with *Respond to Webhook*) → *Set*
      "Run settings": `request = body.request ?? ""`, `eval_id = body.brief_id ?? null`,
      `model = body.model ?? "gemma4:12b-it-q8_0"` → Postgres "Start run":
      `insert into app.run (model, eval_id) values ($1, $2) returning id` → *Set* "Step 1 ·
      input": `{run_id, request}` plus `started_at = $now.toISO()` → *Execute Workflow*
      "Step 1 · read request" (from the database by id, wait for completion, *On Error: continue
      (using error output)*).
      Success → Postgres "Step 1 · log ok": `insert into app.run_step (run_id, step, try, input,
      output, ok, ms) values ($1, 1, 1, $2::jsonb, $3::jsonb, true, <ms>)`, with
      `<ms> = round(extract(epoch from clock_timestamp() - $4::timestamptz) * 1000)::int` →
      Postgres "Finish run": `update app.run set finished_at = now(), ok = true where id = $1` →
      *Respond* `{run_id, ok: true}`.
      Error output → Postgres "Step 1 · log failure": the same insert with `output` null,
      `ok = false` and `error` = the error message. Read its real path from one failed execution
      (`get_execution`), and write the path into this plan as a deviation if it is not
      `$json.error.message`. (Measured: it is the plain string `$json.error`.) → "Finish run (failed)" with `ok = false` → *Respond*
      `{run_id, ok: false, failed_step: 1, error}`.
      A sticky note explains the per-step block (set input + start time → call → log ok / log
      failure → finish) that steps 2–16 copy, and that a failure ends the run.
- [x] Validate, create, check `connections`, and publish all three. `Recipe pipeline` must be
      published for its production webhook. Publish the two sub-workflows too, and confirm in an
      execution which version the *Execute Workflow* node runs.
- [x] Write `tests/test_pipeline.py` (all `stack`; POST with `urllib.request`, read through
      `loaders.db.connect()`):
      `test_b01_logs_step_1` (A2): POST b01's request with `brief_id = "b01"`. The response has
      `ok: true`. One `app.run` row with that id, `eval_id = 'b01'`, a model, `finished_at` set,
      `ok = true`. One `run_step` row: step 1, try 1, `ok = true`, `error` null, `ms >= 0`,
      `input = {run_id, request}`. Its `output` gives `[]` from
      `jsonschema_validation_errors` against `shared/contracts/step1.output.schema.json`.
      `test_bad_input_logs_failure` (A3): POST `request: ""`. The response has `ok: false,
      failed_step: 1`. The run has `ok = false`. The step 1 row has `ok = false`, and `error`
      contains `step1.input`.
      `test_request_kept_verbatim`: a request with quotes, commas, a `%`, `$1` and a newline
      comes back unchanged in `input.request` and in `output.wanted[0]`.
- [x] Run `python -m evals.workflows`. Expect 3 files in `n8n/workflows/`. Read them: no
      credential secrets, only credential ids and names.
- [x] `docs/OPERATIONS.md` §5: the webhook URL and body, `python -m evals.workflows` after every
      workflow change, and what the Postgres credential connects as.
- [x] Run `.venv/bin/pytest`, expect all pass, including `test_repo_files_match_n8n` with 3
      workflows.
Done when: the 3 workflows run published in n8n, their files are in the repo and match, and
`tests/test_pipeline.py` passes.
Commit: `Add recipe pipeline with step 1 stub and run log`

### Task 7: the runner sends the briefs and prints the graded table (G0 bar)
Why: R6, R8; A3, A5, and the G0 bar.
- [x] `evals/run.py` (stdlib only: `argparse`, `json`, `urllib.request`, `tomllib`):
      - `send(request, brief_id, model=None, url=PIPELINE_URL, timeout=600) -> dict`. A non-200
        answer or a timeout returns `{"ok": False, "error": ...}` instead of raising, so one bad
        brief doesn't stop the run.
      - `read_run(conn, run_id) -> dict`: the `app.run` row and its `run_step` rows by step
        (latest `try`).
      - `run_brief(conn, brief, model=None) -> dict`: send, read, then `grade.grade_run`. The
        result holds `id`, `run_id`, `run_ok` and `error`. If the run is not finished
        (`finished_at` null), or `ok` is not true, the brief is failed, with the error.
      - `table(results) -> str`: one row per brief (`brief`, `run`, `step 1`, `step 2`,
        `step 3`, `result`). Step 1 shows the failed field names. A step with no row shows
        `not run`, and a failed run shows `failed at step N: <error>`.
      - `totals(results) -> dict`: per graded step, passed / total, and how many were not run;
        briefs passed / total. A step that was not run counts as not passed.
      - CLI: `python -m evals.run [--brief b01] [--model NAME] [--save --label m0]`. It prints
        the table and totals. `--save` writes `evals/results/<YYYY-MM-DD>-<label>.json` with
        date, label, model, the results and the totals. Exit code 0 only when every brief
        passed.
- [x] Write `tests/test_run.py`: `test_not_run_steps_count_as_failed` and
      `test_failed_run_is_reported_failed` (no stack; build results from made-up run dicts);
      `test_runner_reports_bad_request_as_failed` (stack, A3): `run_brief` on b01 with its
      `request` set to `""` gives `passed = False`, and an error that contains `step1.input`.
- [x] Run `python -m evals.run --brief b01`. Expect 1 row, step 1 red on `wanted`, run ok. Then
      `python -m evals.run --save --label m0`. Expect 20 rows, step 1 0/20, steps 2 and 3 0/20
      (20 not run), briefs 0/20, exit code 1 (A5).
- [x] Check in the DB that every run of the saved file has `finished_at` set and one step 1 row
      with `ok = true`.
- [x] PROJECT.md: §4 Orchestration row (3 workflows, published, measured) and Scripts row
      (`evals/` harness and its tests). §8 entry with the measured G0 result. WORKFLOW-ROADMAP
      G0: the measured bar line. Commit `evals/results/<date>-m0.json` (G0 is a checkpoint).
- [x] Run `.venv/bin/pytest`, expect all pass.
Done when: the saved 20-brief run shows the red table with totals, and the suite passes.
Commit: `Add eval runner and G0 baseline run`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| A failed step always records its error; a passed one never does | `tests/test_run_log.py::test_failed_step_needs_error`, `::test_passed_step_has_no_error` | 2 |
| A step's bad input stops the run with `ok = false` and the error, not silently | `tests/test_pipeline.py::test_bad_input_logs_failure` | 6 |
| The runner never reports a failed run as passed | `tests/test_run.py::test_failed_run_is_reported_failed`, `::test_runner_reports_bad_request_as_failed` | 7 |
| Request text reaches the log unchanged (no splitting on commas, no injection) | `tests/test_pipeline.py::test_request_kept_verbatim` | 6 |
| A run's step 1 row matches the step 1 contract | `tests/test_pipeline.py::test_b01_logs_step_1` | 6 |
| Contracts accept their absent slot and reject bad values | `tests/test_contracts.py::test_examples`, `::test_every_output_has_an_absent_slot` | 3 |
| Deviation match = same kind and same subject | `tests/test_grade.py::test_same_kind_other_subject_does_not_match`, `::test_other_kind_same_subject_does_not_match` | 4 |
| An alternative style counts as a pass | `tests/test_grade.py::test_step2_alternative_style_passes` | 4 |
| A missing step output fails every graded field | `tests/test_grade.py::test_step1_missing_output_fails_every_field` | 4 |
| Repo workflow files match n8n | `tests/test_workflows.py::test_repo_files_match_n8n` | 5, 6 |
| The default suite passes without the stack | `tests/conftest.py` skip, checked as A7 in verification | 1 |

## Approved exceptions

None yet. Pending (question 3 in the plan's report): verification may stop and start the `n8n`
and `supabase-pooler` containers (`docker stop` / `docker start`, no recreate) to check A7.

## Deviations
- 2026-10-12 · Plan: `test_style_codes_exist_in_ref` fails today when the stack is down, rather
  than being skipped as brief R9 says. Task 1 marks it `stack` so that A7 can hold. This is a fact
  correction, not a scope change.
- 2026-10-12 · Task 6: the Execute Workflow error output carries the message as a plain string in
  `$json.error`, not `$json.error.message` — measured from one failed execution; the log-failure
  and respond expressions use `$json.error`.
- 2026-10-12 · Task 6: `export_all()` skips archived workflows — the MCP has no delete, and the
  archived temporary credential-check workflow (Postgres credential check) would otherwise be
  exported as a fourth file. Implementation detail only.
- 2026-10-12 · Task 6: `Start run` returns `id::int`, because the Postgres node returns bigint as
  text and the step 1 trigger input `run_id` is a number.
- 2026-10-12 · Task 6: the Postgres credential was checked with a temporary one-node workflow run
  through `execute_workflow` (then archived), because `test_workflow` pins credentialed nodes and
  would not have run the query. Result: `postgres`, `postgres`, `172.19.0.13`.
- 2026-10-12 · Task 3: `test_examples` became two parametrized tests, `test_good_examples` and
  `test_bad_examples` — one assertion style per test reads better. Same coverage.
- 2026-10-12 · Task 6: the item "confirm in an execution which version the Execute Workflow node
  runs" was not done. Draft = published for all three workflows (measured in review), so nothing
  depends on it today; OPERATIONS §5 now marks the "publish sub-workflows too" advice as unverified.
  Measure it when M1 first edits a sub-workflow.
- 2026-10-12 · Task 6: `test_b01_logs_step_1` posts `"a pale ale"`, not b01's request — it only
  checks that step 1 is logged, which does not depend on the text.
- 2026-10-12 · Task 7: b01 was expected to be red on `wanted` only; it is red on `stated`, `hints`
  and `wanted`, because b01 states `batch_l` and `abv` and the stub returns `stated: {}`.
- 2026-10-12 · Review fixes: tests for `run_ok and` and the unfinished-run check (both seen to fail
  with the code mutated); `totals()` step 1 now has `not_run`; `tests/conftest.py` uses
  `loaders.db.connect(connect_timeout=3)` and skips when the env file or a key is missing.
