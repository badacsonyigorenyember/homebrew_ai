# M1 · Step 1: read the request, and choose the chat model (D2) — implementation plan

Stage: implementing
Brief: [brief.md](brief.md)
Branch: m1-read-request

## Approach

- **Step 1 is one LLM call through Ollama's own API, then one SQL check.** The stub's middle
  node in `Step 1 · read request` becomes: read the system prompt and the step 1 output
  contract from `shared/`, call Ollama `POST http://ollama:11434/api/chat` with an *HTTP
  Request* node, and check the answer with one SQL function. The contract file itself is sent
  as Ollama's `format`, so the model is held to the same schema the check uses.
  *Why HTTP Request and not the n8n `Ollama Chat Model` + Basic LLM Chain the n8n-skills
  default to:* that node (v1, read with `get_node_types` 2026-10-12) has no `seed`, only
  `format: default | json` (no JSON schema), and gives no token counts, so R4, R5 and the
  structured output could not be met. The skills' other rule, retry with a fixer model
  (`autoFix`), becomes R2's own retry with the same local model (no cloud model, §2).
  Approving this plan confirms the choice (Question 1 in the report).
- **One SQL function does the whole check** (G0: deterministic logic is SQL, Code nodes only
  glue). `app.step1_read_answer(request text, content text, contract json)` returns
  `(brief jsonb, errors text[])`: it parses the model's text (not JSON → an error), drops
  repeated items in the five word lists, validates against the contract with
  `extensions.jsonschema_validation_errors`, and checks that every `stated` number is a number
  written in the request (R3). pytest calls it directly, so R2/R3 are tested without a model
  (A4).
- **Retry once, inside the step (R2).** A failed answer is sent back once as a second
  conversation turn with the error list. A second failure stops the sub-workflow with
  `step 1 answer failed twice: try 1: …; try 2: …`, which the existing pipeline block logs
  with `ok = false`. The two paths are separate, explicit node chains (§6.8), not a loop.
- **Logging (R4, R5).** The sub-workflow stays free of writes (its editor sample keeps
  `run_id: 0`). It returns `{brief, llm}`; the pipeline logs `output = brief`,
  `tokens = prompt + output tokens` and a new `app.run_step.llm` jsonb
  (`model, think, tries, prompt_tokens, output_tokens, llm_ms, done_reason, first_errors`),
  then saves `app.brief` and sets `app.run.brief_id`. `app.brief.profile_id` becomes nullable:
  `app.brewer_profile` is empty and step 0 is M4's work (measured: 0 rows). Model and thinking
  travel as `model` / `think` in the webhook body and in `step1.input`. Options are fixed:
  `temperature 0`, `seed 42`, `num_ctx 8192` (the context the model research measured fit at),
  `num_predict 4096`, `stream false`.
- **Grading (R1, R9).** `named` becomes a graded field. Words are compared after
  normalising (case, accents, hyphens and spacing) and mapping a short synonym list of naming
  variants; a form word never disappears, so `rice` ≠ `flaked rice`. `unknown` is not graded
  (the briefs hold no expectation for it); A3 has its own test.
- **Benchmark (R6, R7).** `evals/benchmark.py` runs one model configuration: unload every
  model, load this one at the same context, read its CPU/GPU split from `ollama ps`, run the 20
  briefs three times through the pipeline, read time and tokens back from `run_step.llm`, and
  merge the summary into one results file. Every configuration runs with the same prompt and
  contract (their sha256 is stored). Quality decides; speed only breaks a tie.
- **The prompt is not tuned to the 20 briefs.** It states the R1 rules in general words and
  quotes no request (a test checks this). Before the benchmark, one smoke pass on the current
  default model may fix *general* rule wording; each change is listed in `benchmark.md`. Then
  the prompt is frozen for all seven configurations.

**Measured while planning (2026-10-12):** Ollama 0.34.0 answers on `http://ollama:11434` from
inside the n8n container. A JSON schema in `format` is honoured by `gemma4:12b`, with `$schema`,
`title` and `description` keys present, with thinking off and on (thinking goes to
`message.thinking`, the JSON to `message.content`). `maxItems` is enforced, `uniqueItems` is not:
with no `maxItems`, thinking on repeated `"bitter"` until the 8K context ran out
(`done_reason: length`, 8153 tokens); with `maxItems: 2` it stopped (`["bitter","bitter"]`).
Hence the contract gains `maxItems` on every list and `uniqueItems` as the checked rule, and the
SQL function drops exact repeats before checking. The response carries `prompt_eval_count`,
`eval_count`, `total_duration` and `load_duration` (ns); call time is taken as
`total_duration − load_duration`. `app.brewer_profile` and `app.brief` have 0 rows,
`app.run` 23 (m0's). No function exists in schema `app`. Context7 (`ctx7`) failed with
"Invalid API key", so Ollama's API was checked live instead of in its docs.

**`named` values (R8, for your review with this plan).** The style words as the user wrote
them: origin words stay (American, German, Bavarian…), words that describe the beer rather
than name the style go (classic, traditional, proper, simple, crisp, dry, light, tart).

| Brief | `named` | Brief | `named` |
|---|---|---|---|
| b01 | West Coast IPA | b11 | saison |
| b02 | hazy IPA | b12 | blonde ale |
| b03 | oatmeal stout | b13 | Bavarian hefeweizen |
| b04 | milk stout | b14 | Berliner Weisse |
| b05 | imperial stout | b15 | English best bitter |
| b06 | American lager | b16 | American pale ale |
| b07 | cream ale | b17 | schwarzbier |
| b08 | German pils | b18 | Irish red ale |
| b09 | Märzen | b19 | wee heavy |
| b10 | Belgian dubbel | b20 | American brown ale |

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `evals/recipe_briefs.toml` | changed | `named` in all 20; b02, b06, b07, b10, b16 in the user's words; header link fixed (R8) |
| `tests/test_recipe_briefs.py` | changed | allows `named`; words come from the request; `wanted` inside `needs` by whole word |
| `evals/grade.py` | changed | `named` graded; normalising and synonyms (R9) |
| `tests/test_grade.py` | changed | A8 and `named` cases |
| `db/015_app.sql` | changed | `app.brief.profile_id` nullable; `app.run_step.llm` |
| `db/020_step1.sql` | new | `app.step1_read_answer` (R2, R3) |
| `shared/contracts/step1.output.schema.json` | changed | `uniqueItems` + `maxItems` on the lists |
| `shared/contracts/step1.input.schema.json` | changed | `model`, `think` |
| `tests/test_step1_check.py` | new | the SQL check (stack) |
| `tests/test_contracts.py` | changed | new good / bad examples |
| `shared/prompts/step1.system.md` | new | the system prompt |
| `tests/test_prompt.py` | new | prompt names every field and hint, quotes no brief |
| `n8n/workflows/step-1-read-request.json` | changed | the LLM step, exported |
| `n8n/workflows/recipe-pipeline.json` | changed | `model` / `think` passed on; tokens, `llm`, `app.brief` saved |
| `tests/test_workflows.py` | changed | new samples; `num_ctx` matches the benchmark |
| `tests/test_pipeline.py` | changed | A3, A5; verbatim check moves to `input` and `app.brief` |
| `evals/run.py` | changed | `--think`, `--timeout`, step 1 `llm` read back |
| `tests/test_run.py` | changed | `send` body carries `think` |
| `evals/benchmark.py` | new | one configuration per call, summary, markdown table (R6) |
| `tests/test_benchmark.py` | new | summary, bar, best pick, `ollama ps` parsing |
| `evals/results/<date>-m1-benchmark.json` | new | G1 checkpoint results |
| `docs/work/m1-read-request/benchmark.md` | new | R6 table, analysis, D2 (R7) |
| `docs/DATABASE.md`, `docs/OPERATIONS.md`, `docs/WORKFLOW-ROADMAP.md` | changed | new column and function; webhook body, models; G1 measured |
| `PROJECT.md` | changed | §4, §7 D2, §8 per task |

## Tasks

### Task 1: the 20 briefs use the user's own ingredient words and name the style
Why: R8, R1; A7.
- [x] `evals/recipe_briefs.toml`: add `named = "<value>"` after `request` in every brief, with
      the values in the table above. Change b02 `wanted` to `["oats"]`, b06 `["rice"]`, b07
      `["corn"]`, b16 `["rice"]`, b10 `inventory` to `["dark candi sugar", "Munich malt",
      "abbey yeast"]`. `needs` stays as it is. Header: add a `named` line to the field list
      ("the style words the user wrote, without words that only describe the beer"), add to the
      `wanted` / `excluded` / `inventory` lines "in the user's words: amount words dropped,
      form words (flaked, ground, malted…) kept", and point the brief link to
      `docs/finished/test-briefs/brief.md` (WORKFLOW-ROADMAP §3 asks for this fix with the first
      brief change).
- [x] `tests/test_recipe_briefs.py`: add `named` to `FIELDS` and require a non-empty string.
      New `test_words_are_the_users`: each `named`, `wanted`, `excluded` and `inventory` item
      appears in its `request` (case-insensitive, accents kept). In
      `test_no_fruit_or_non_gravity_extras`, a `wanted` word passes when it appears as a whole
      word inside some `needs` item (`oats` in `flaked oats`).
- [x] Run `.venv/bin/pytest tests/test_recipe_briefs.py`, expect all pass. Run
      `.venv/bin/pytest -m "not stack"`; `tests/test_grade.py` may now fail on b02/b06/b16
      wording only if a test hard-codes the old words: fix such a test to the new words.
- [x] PROJECT.md §8 entry.
Done when: all 20 briefs have `named`, the five briefs hold the R8 words, and the suite passes.
Commit: `Add named and user words to the recipe briefs`

### Task 2: the grader scores `named` and compares words the R9 way
Why: R9, R1; A8.
- [ ] `evals/grade.py`: `STEP1_FIELDS` gains `named` (first). New `normalise(word) -> str`:
      NFKD and drop combining marks, lower case, hyphens to spaces, runs of whitespace to one
      space, trimmed. New `SYNONYMS`, a short list of pairs of naming variants only, each
      mapped to its first word: `("crystal malt", "caramel malt")`, `("east kent goldings",
      "ekg")`. A pair must never differ by a form or condition word; a comment says so.
      `_clean_set` becomes "normalise, then map synonyms". `named`: equal after `normalise`,
      and `null` equals only a missing expectation (every brief has one, so `null` is wrong).
      `hints` keep the plain set compare.
- [ ] `tests/test_grade.py`: `right_step1` copies `named`. New
      `test_form_word_is_a_different_ingredient` (`rice` vs `flaked rice` → False),
      `test_case_and_spacing_ignored` (`Flaked  Rice` vs `flaked rice` → True),
      `test_synonym_pair_counts_as_equal` (`caramel malt` vs `crystal malt` → True),
      `test_accents_ignored_in_named` (`Marzen` vs `Märzen` → True),
      `test_named_null_is_wrong` (b05 with `named: null` → `named` False only).
- [ ] Run `.venv/bin/pytest tests/test_grade.py tests/test_run.py`, expect all pass.
Done when: the A8 cases pass and the runner table lists `named` among step 1 fields.
Commit: `Grade named and compare words by the R9 rule`

### Task 3: one SQL function checks a model answer against the contract and the request
Why: R2, R3, R4; A4 (check part). DB changes as `.sql` applied with `psql` as `postgres`.
- [ ] `db/015_app.sql`: in the `create table` text, `app.brief.profile_id` without `not null`
      (comment: "null until step 0 builds profiles, M4") and `app.run_step.llm jsonb` (comment:
      "LLM steps: model, think, tries, tokens, llm_ms, done_reason, first_errors"). At the end:
      ```sql
      alter table app.brief alter column profile_id drop not null;
      alter table app.run_step add column if not exists llm jsonb;
      ```
- [ ] `shared/contracts/step1.output.schema.json`: `uniqueItems: true` on `hints`, `wanted`,
      `excluded`, `inventory`, `unknown`; `maxItems` 11 on `hints`, 20 on the others. The stub
      output still passes.
- [ ] `db/020_step1.sql` (header like `015_app.sql`: purpose, apply command, idempotent):
      `create or replace function app.step1_read_answer(request text, content text, contract json)
      returns table (brief jsonb, errors text[]) language plpgsql`. In this order:
      1. `content::jsonb` in a `begin … exception` block; on failure return
         `(null, array['answer is not JSON: ' || sqlerrm])`.
      2. For each of `hints, wanted, excluded, inventory, unknown` that is an array: keep the
         first of each exact repeat, order kept.
      3. `errors := coalesce(extensions.jsonschema_validation_errors(contract, brief::json), '{}')`.
      4. Numbers in the request: `regexp_matches(request, '\d+(?:[.,]\d+)?', 'g')`, comma read as
         a point, cast to numeric. For each key of `brief->'stated'` whose value is a number and
         equals none of them: add `stated.<key> = <value> is not a number in the request`.
      Return the cleaned brief and the errors. Comment: words for numbers ("twenty") and unit
      conversions are not recognised, so such a `stated` value fails the check (R3: only
      numbers the user wrote).
- [ ] Apply both files twice:
      `docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/015_app.sql`
      and the same for `db/020_step1.sql`. Check the catalog: `profile_id` nullable, `llm`
      present, the function owned by `postgres`.
- [ ] Write `tests/test_step1_check.py` (all `stack`; the contract read from the repo file):
      `test_good_answer_passes` (b01's expected brief as content → `[]`, brief unchanged);
      `test_made_up_number_fails` (A4: b01's request, `stated.abv = 7` → one error naming
      `stated.abv`); `test_written_forms_of_a_number_match` (`1.060` matches `1.06`, `6,5 %`
      matches `6.5`); `test_not_json_fails` (`{"named": ` → `answer is not JSON`);
      `test_repeated_words_dropped` (`hints ["bitter","bitter"]` → `["bitter"]`, no error);
      `test_contract_errors_reported` (hint `funky` → an error).
- [ ] `tests/test_contracts.py`: bad example `step1.output` with `wanted: ["oats", "oats"]`.
- [ ] `docs/DATABASE.md`: `brief.profile_id` nullable and why, `run_step.llm`, the function in
      one line.
- [ ] Run `.venv/bin/pytest`, expect all pass. PROJECT.md §8 entry.
Done when: both SQL files apply twice cleanly and the 6 new tests pass.
Commit: `Add step 1 answer check in SQL`

### Task 4: step 1 asks the model, checks, retries once, and the pipeline logs and saves the brief
Why: R1, R2, R4, R5; A3, A4 (wiring), A5. Load the n8n skills first
(`using-n8n-skills-official`, `n8n-workflow-lifecycle-official`, `n8n-node-configuration-official`,
`n8n-error-handling-official`, `n8n-agents-official`) and follow the MCP order: SDK reference →
`get_node_types` → validate → update → check `connections` → publish.
- [ ] `shared/prompts/step1.system.md`: one clear system prompt (no examples taken from the
      briefs). It says what each field holds, as R1 does: `named` (the style words the user
      wrote, origin words kept, describing words dropped, or null); `stated` (only `batch_l`,
      `abv`, `og`, `ibu`, `srm`, only numbers the user wrote, no conversion); `hints` (only
      the 11 vocabulary words, used when the user uses that word or a direct form of it —
      "crisper" → crisp, "bone dry" → dry); `wanted`, `excluded`, `inventory` (ingredients in
      the user's words: drop amount words, keep form and condition words; words that are part
      of the style name are not ingredients; "I have no X" means excluded); `guidance` (false
      only when the user says to ignore the style); `unknown` (anything asked for that fits no
      field). Answer in JSON only.
- [ ] Write `tests/test_prompt.py` (no stack): the prompt names all 8 output fields and all 11
      hint words; no run of 5 consecutive words from any brief's `request` appears in it
      (case-insensitive).
- [ ] `shared/contracts/step1.input.schema.json`: add required `model` (string, `minLength: 1`)
      and `think` (boolean). Update `tests/test_contracts.py` examples to match.
- [ ] Workflow `Step 1 · read request` (`xmIkYM80AJ6ynxML`): trigger inputs gain `model`
      (string) and `think` (boolean). Replace `Stub: copy request` with, in order:
      *Read file* `/data/shared/prompts/step1.system.md` → *Extract from File* (text) "Prompt";
      *Read file* + *Extract from File* (JSON) "Step 1 contract" for
      `/data/shared/contracts/step1.output.schema.json`;
      *Set* "Build model request": `{model, think, stream: false, format: <contract>,
      options: {temperature: 0, seed: 42, num_ctx: 8192, num_predict: 4096},
      messages: [{role: system, content: <prompt>}, {role: user, content: <request>}]}`;
      *HTTP Request* "Ask model": `POST http://ollama:11434/api/chat`, JSON body
      `={{ $json }}`, no auth, option timeout 1 800 000 ms;
      *Postgres* "Check answer":
      `select brief, coalesce(errors, '{}') as errors from app.step1_read_answer($1, $2, $3::json)`
      with `[request, $json.message.content, JSON.stringify(<contract>)]` as one expression
      returning an array (the m0 rule: never a comma-separated list);
      *If* "Answer ok?".
      True → *Execute Workflow* "Check step 1 output" (`Check contract`, `step1.output`) → *Set*
      "Return first answer" `{brief, llm}`.
      False → *Set* "Build retry request": the first request's messages plus
      `{role: assistant, content: <first answer>}` and `{role: user, content: "That answer
      failed these checks: <errors joined by '; '>. Answer the same request again, as JSON in
      the same shape."}` → *HTTP Request* "Ask model again" (same settings) → *Postgres*
      "Check second answer" → *If* "Second answer ok?" → true: "Check step 1 output (retry)" →
      "Return second answer"; false: *Stop and Error* `step 1 answer failed twice: try 1:
      <errors 1>; try 2: <errors 2>`.
      `llm` = `{model, think, tries: 1|2, prompt_tokens, output_tokens` (sums of
      `prompt_eval_count` / `eval_count`), `llm_ms` (sum of `(total_duration −
      load_duration) / 1e6`, rounded), `done_reason` (last call), `first_errors` (try 2 only)`}`.
      Update the sticky note (no longer a stub: what each part does, the retry, writes
      nothing) and the `Test data` sample to
      `[{"run_id": 0, "request": "<b01>", "model": "gemma4:12b-it-q8_0", "think": false}]`.
- [ ] Workflow `Recipe pipeline` (`eMkkdBar6NIqUa1g`): `Run settings` gains
      `think: body.think ?? false`; `Step 1 · input` and the Execute Workflow mapping pass
      `model` and `think`. `Step 1 · log ok` logs `output = brief`, `tokens =
      llm.prompt_tokens + llm.output_tokens`, `llm` as jsonb. New Postgres node
      "Step 1 · save brief" after it:
      ```sql
      with b as (
        insert into app.brief (request_text, brief, guidance_on)
        values ($1, $2::jsonb, ($2::jsonb ->> 'guidance')::boolean) returning id)
      update app.run set brief_id = (select id from b) where id = $3 returning brief_id
      ```
      → `Finish run`. Update the per-step sticky note (step 1 now saves the brief).
      The `Check contract` sample in `check-contract.json` gains `model` and `think` (it checks
      `step1.input`).
- [ ] Validate, update, check `connections`, publish all three changed workflows. **Measure**
      which version an Execute Workflow node runs: before publishing `Step 1 · read request`,
      run the pipeline once on its draft and see in the execution whether the new nodes ran.
      Record the answer in OPERATIONS §5 (m0 left it unverified).
- [ ] Retry wiring (A4, R2) through MCP `test_workflow` on `Step 1 · read request`, which pins
      the HTTP and Postgres nodes: (a) "Check answer" pinned with an error, "Check second
      answer" with none → the workflow returns `llm.tries = 2` and `first_errors`; (b) both
      pinned with errors → it stops with `step 1 answer failed twice` naming both. Record the
      two execution ids in the plan's Deviations if anything differs.
- [ ] Tests:
      `tests/test_workflows.py`: `SAMPLES` / `STEP1_INPUT` carry `model` and `think`; new
      `test_num_ctx_matches_benchmark` (no stack): the `num_ctx` in the exported "Build model
      request" node equals `evals.benchmark.NUM_CTX` (create `evals/benchmark.py` now with
      only `NUM_CTX = 8192` and a docstring; Task 5 fills it).
      `tests/test_pipeline.py`: `post` timeout 600 s, and its cleanup also deletes the runs'
      `app.brief` rows. `test_b01_logs_step_1` (A5) also checks: `app.run.brief_id` set; one
      `app.brief` row with `request_text` = the request, `brief` = the step output,
      `guidance_on` = its `guidance`, `profile_id` null; `run_step.tokens > 0`; `llm.model` =
      `app.run.model`, `llm.tries` in (1, 2). `test_request_kept_verbatim` checks
      `input.request` and `app.brief.request_text` (no longer `wanted[0]`). New
      `test_unknown_word_goes_to_unknown` (A3): "A pale ale, and make it funky." → `ok`, no
      hint `funky`, some `unknown` item contains `funky`.
- [ ] Run `.venv/bin/python -m evals.workflows`; read the diff: no secrets, only the intended
      nodes changed. Run `.venv/bin/pytest`, expect all pass.
- [ ] Smoke pass on the default model: `.venv/bin/python -m evals.run`. Expect 20 finished
      runs (step 1 graded, steps 2–3 not run). Fix wiring bugs. Prompt wording may change only
      as a general rule that quotes no brief (`test_prompt.py`); note each change for
      `benchmark.md`. Then the prompt is frozen.
- [ ] `docs/OPERATIONS.md` §5: webhook body `think`, the step 1 call (Ollama URL, fixed
      options), the Execute Workflow version answer. PROJECT.md §4 Orchestration row and §8.
Done when: the workflows run published, their files match n8n, A3 and A5 tests pass, the retry
wiring behaved as in (a) and (b), and the smoke pass finished 20 runs.
Commit: `Build step 1 with the LLM call, check and retry`

### Task 5: the benchmark tool runs one model configuration and summarises it
Why: R6; A6 (tooling).
- [ ] `evals/run.py`: `send(..., think=False, timeout=...)` puts `think` in the body;
      `run_brief(conn, brief, model=None, think=False, timeout=1800)`; `read_run` also returns
      step 1's `llm`; CLI `--think`, `--timeout` (default 1800 s). Results keep `llm`.
- [ ] `evals/benchmark.py` (stdlib only):
      - `NUM_CTX = 8192`, `OLLAMA = "http://localhost:11434"`.
      - `unload_all()`: for each model in `docker exec ollama ollama ps`, `ollama stop <name>`.
      - `load(model)`: `POST /api/generate {"model", "prompt": "", "options": {"num_ctx": NUM_CTX}}`
        so the pipeline's first call does not reload it.
      - `processor_split(ps_text, model) -> str`: the PROCESSOR column for that model
        ("100% GPU", "15%/85% CPU/GPU").
      - `model_details(model) -> dict`: `POST /api/show` → `quantization_level`, `parameter_size`.
      - `percentile(values, p)` (nearest rank); `summarise(runs) -> dict` where `runs` is three
        lists of runner results: `all_right` per run (step 1 `ok` and run ok), accuracy per
        field over all brief-runs (a failed run counts every field wrong), median and p90 of
        `llm_ms` in seconds, retries (`tries == 2`) and failed runs counted.
      - `meets_bar(summary)`: every run ≥ 19/20. `pick_best(configs)`: most `all_right` in
        total, then the higher worst run, then the lower median time.
      - `markdown_table(configs)`: one row per configuration (tag, quant, think, split,
        all-right per run, per-field accuracy, median / p90 s, retries).
      - CLI `python -m evals.benchmark --model TAG [--think] [--runs 3] [--save]`: unload all,
        load, read the split, run the briefs `--runs` times, print the summary, unload. With
        `--save`, merge it into `evals/results/<date>-m1-benchmark.json` under `"<tag>|think"`
        or `"<tag>|no-think"`, with the sha256 of the prompt and the contract and every result.
        `--table PATH` prints `markdown_table` for a saved file.
- [ ] Write `tests/test_benchmark.py` (no stack): `test_bar_needs_every_run` ([19, 19, 18] →
      False; [20, 19, 19] → True); `test_failed_run_counts_every_field_wrong`;
      `test_best_is_quality_before_speed` (more all-right but slower wins);
      `test_tie_broken_by_worst_run_then_speed`; `test_processor_split_parses_ollama_ps` (a
      captured `ollama ps` text with two models); `test_percentile_nearest_rank`.
      `tests/test_run.py`: `test_send_puts_think_in_body` (monkeypatched `urlopen`).
- [ ] Run `.venv/bin/pytest`, expect all pass. Run
      `.venv/bin/python -m evals.benchmark --model gemma4:12b --runs 1` as a dry run; expect a
      summary with a split and times.
Done when: the tests pass and the dry run prints a summary.
Commit: `Add model benchmark tool for step 1`

### Task 6: the six candidates and the best with thinking on are measured (G1)
Why: R6, R7; A1, A2, A6.
- [ ] Check free disk (`docker exec ollama df -h /root/.ollama`, about 57 GB needed). Pull, in
      the background: `docker exec ollama ollama pull gemma4:31b-it-qat`,
      `gemma4:26b-a4b-it-qat`, `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K`. `ollama list` shows
      all three. Only these six chat models are run (brief constraint).
- [ ] Run `python -m evals.benchmark --model <tag> --runs 3 --save` for `qwen3.8:27b`,
      `gemma4:12b-it-q8_0`, `gemma4:12b`, `gemma4:31b-it-qat`, `gemma4:26b-a4b-it-qat`,
      `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K` (in the background, one after the other). Then
      `pick_best` over them, and run that tag again with `--think`. All configurations must
      show the same prompt and contract hash.
- [ ] Write `docs/work/m1-read-request/benchmark.md`: date, machine, prompt and contract hash,
      the prompt changes from the smoke pass, the `markdown_table`, A2 per configuration (b05
      `abv 4` + `named`, b18 `guidance false`, b08 `excluded Saaz`, `batch_l 10`, `ibu 50`), and
      every failing field of the best configuration with its cause class: **prompt**,
      **contract** or **ambiguous brief** (R7). Synonyms added during this task (only naming
      variants) are listed for your review.
- [ ] **If no configuration meets the bar:** stop here. Report `needs-input` with
      `benchmark.md`; the bar is not lowered and the prompt is not changed without you (R7).
- [ ] PROJECT.md §8 entry with the measured result.
Done when: `benchmark.md` holds all seven rows and the cause analysis, and the results file is
saved.
Commit: `Run the D2 benchmark for step 1`

### Task 7: D2 is decided and the pipeline uses the chosen model
Why: R7; A1, A6. Only after Task 6 met the bar.
- [ ] `Recipe pipeline` → `Run settings`: default `model` (and `think`, if thinking on won)
      set to the chosen configuration; the `Test data` samples' `model` / `think` likewise
      (and `SAMPLES` in `tests/test_workflows.py`). Publish, `python -m evals.workflows`.
- [ ] `.venv/bin/pytest` (stack up), expect all pass, now on the chosen model (A3, A5).
- [ ] PROJECT.md: §4 Chat model row names the chosen tag, quantisation, think setting and
      measured result, with the *why* (quality first, then speed; link `benchmark.md`); D2
      leaves §7; §8 entry. `docs/WORKFLOW-ROADMAP.md` G1: a **Measured** line; §3 M1 row:
      decided, step 1 outputs the user's words and M5's resolver maps them. OPERATIONS §6:
      the pulled models.
- [ ] Commit `evals/results/<date>-m1-benchmark.json` (G1 is a checkpoint).
Done when: the pipeline default is the chosen model, the suite passes on it, and D2 is in §4.
Commit: `Decide D2 and make it the step 1 default`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| A number the user did not write never passes into `stated` | `tests/test_step1_check.py::test_made_up_number_fails` | 3 |
| A number the user wrote in another notation still passes | `tests/test_step1_check.py::test_written_forms_of_a_number_match` | 3 |
| A non-JSON or off-contract answer is an error, not a guessed brief | `::test_not_json_fails`, `::test_contract_errors_reported` | 3 |
| Two failed answers end the run with `ok = false` and both errors | MCP `test_workflow` case (b) on `Step 1 · read request` | 4 |
| `flaked rice` and `rice` are graded as different ingredients | `tests/test_grade.py::test_form_word_is_a_different_ingredient` | 2 |
| Case, spacing, accents and listed synonyms do not fail a right word | `::test_case_and_spacing_ignored`, `::test_synonym_pair_counts_as_equal`, `::test_accents_ignored_in_named` | 2 |
| Expected words are the user's own words | `tests/test_recipe_briefs.py::test_words_are_the_users` | 1 |
| The prompt is not fitted to the 20 briefs | `tests/test_prompt.py` | 4 |
| Each run saves its brief and logs model, time and tokens | `tests/test_pipeline.py::test_b01_logs_step_1` | 4 |
| An unknown wish goes to `unknown`, not `hints` | `tests/test_pipeline.py::test_unknown_word_goes_to_unknown` | 4 |
| The benchmark loads the model at the context the pipeline uses | `tests/test_workflows.py::test_num_ctx_matches_benchmark` | 4 |
| The bar needs every run, and quality beats speed | `tests/test_benchmark.py::test_bar_needs_every_run`, `::test_best_is_quality_before_speed` | 5 |

## Approved exceptions

## Deviations
