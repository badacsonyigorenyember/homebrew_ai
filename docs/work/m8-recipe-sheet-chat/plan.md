# M8 · Step 16 and the chat: the recipe sheet you brew from — implementation plan

Stage: implementing
Brief: [brief.md](brief.md)
Branch: m8-recipe-sheet-chat

## Approach

- **Step 16 is SQL around one LLM call, like steps 6–9.** A new sub-workflow `Step 16 · recipe
  sheet` runs after `Save recipe`: SQL gathers the facts of the run and the saved recipe
  (`app.sheet_facts`), builds retrieval queries (`app.sheet_queries`), n8n embeds them with
  `bge-m3` (Ollama `/api/embed`, not an LLM chat call, R6), SQL finds the chunks
  (`app.sheet_sources`, *How to Brew* first, §6.9) and builds the prompt (`app.sheet_prompt`).
  One Ollama chat call (HTTP Request, D2 model, `num_ctx` 32768 as steps 6–9 so the model does not
  reload, `format` = `shared/contracts/sheet.answer.schema.json`) returns **prose only**. SQL checks
  it (`app.sheet_read_answer`), one retry with the failures listed (R7), then SQL writes the
  Markdown (`app.sheet_markdown`) and saves it (`app.save_sheet`). The sub-workflow logs `run_step`
  16 with the call in `llm`, so `evals.run` counts it as a first-try call like steps 1 and 6 (R6).
- **Code writes every number on the sheet (R1, user answer 2).** Every quantity section is
  rendered from the saved rows (`app.recipe`, `recipe_item`, `recipe_deviation`, `process`) and the
  run's step outputs (step 2 reason and alternatives, steps 6–9 `because`/`absent`/
  `unused_inventory`, step 10 `values_used`, the steps 12–15 labels). The LLM's answer is
  `{style_description, why: [{key, text, cite}], notes: [{text, cite}]}`: one `why` per main choice
  key that `app.sheet_facts` lists (`style`, `fermentable:<id>`, `hop:<id>`, `yeast:<id>`,
  `extra:<id>`, `water`, `mash`, `boil`, `fermentation`, `packaging`), each placed next to its item.
- **The check (R1, R3).** Numbers: every number token in the prose (digits not touching a letter or
  digit, so `15B`, `US-05` and `S-04` are not tokens) must equal an allowed value rounded to the
  token's decimals. Allowed = every numeric value of the saved recipe (row, `targets`, `process`,
  item amounts, % and times), every range bound of the chosen style and of the styles step 2
  named (alternatives, mismatch), and numbers inside the recipe's ingredient and style names.
  Citations: every `cite` id must be a chunk this run retrieved, and the sheet must cite at least
  one chunk (the Goal asks for citations; an empty `cite` on one line is the legal "no source"
  of §6.3). Keys: exactly one `why` per listed key. A failure text names the number, the key
  and the field, so the retry message lists them (R7).
- **Citations (R3).** The sheet numbers them in order of first use and lists them at the end:
  a book chunk as `<title>, PDF p. <page> — <section>` (pages in `kb.chunk` are PDF pages,
  [`docs/BOOKS.md`](../../BOOKS.md) line 6), an article chunk as `<title> — <section> — <url>`.
  Retrieval prefers *How to Brew*: for each query, `app.kb_search(…, k => 10)`, then *How to Brew*
  chunks first by score, then the rest by score, keep `sheet_chunks` per query (default 3),
  each chunk once.
- **Failure (R7).** A second failed check logs row 16 ok false with both tries in `llm` and stops
  with `step 16: …`; the pipeline finishes the run ok false with `failed_step` 16 and `recipe_id`.
  The recipe was saved before step 16, so it stays `draft` with `sheet` null.
- **Style field and the given brief (R5).** `app.step2_best_style` gains `style text default null`:
  a code (BJCP first, within the guide setting) that wins over the pick. When it differs from the
  pick, the output's `style` is that style, `mismatch` is null (step 3 then lists the stated
  number outside its range as a `number` deviation, `app.step3_numbers`), the best fit leads
  `alt_styles`, and `reason` says the user chose it; a code equal to the pick changes nothing (the
  mismatch deviation stays). An unknown code raises (fails step 2, like a bad guide). The webhook
  gains optional `style`, `brief` and `brief_llm`: with `brief`, the pipeline skips the step 1
  call, checks the brief against `step1.output`, and logs row 1 with the given brief and the
  given `llm` (the chat's own step 1 call), so step 1 runs once per chat request and is still
  counted (R5, R6, A4).
- **The chat (R4, R5, R9, R10).** A workflow `Recipe chat`: Chat Trigger (hosted chat, `public`,
  `authentication: n8nUserAuth`, `responseMode: responseNodes`) → `Step 1 · read request` and
  `Step 2 · best-fit style` as sub-workflows → on a `mismatch`, Chat node *Send and Wait for
  Response* with two approval buttons ("Keep 20C" / "Take 15B") → Chat *Send* "this takes a few
  minutes" → HTTP Request to the pipeline webhook with `request`, `brief`, `brief_llm`, `style`,
  `brief_id: "chat"` → the sheet from `app.recipe.sheet`, or the failed step and its error in plain
  words → *Send and Wait* "Accept this sheet?" → `app.accept_recipe` sets `final`. One execution
  holds both questions; no agent node. The harness keeps calling the webhook without `style` and
  never asks.
**Measured while planning (2026-10-29, read-only, nothing written):**
- `app.recipe` has `process` and no `sheet`; `status` check allows `draft`, `final`, `brewed`.
  `app.run_step.step` check already allows 0–16, so row 16 needs no schema change.
- `kb.chunk` has `section_path` and `page` (PDF page); `ref.source` has `title` and `url` (not
  `source_url`; `app.kb_search` returns it as `source_url`). *How to Brew* (`palmer-how-to-brew`)
  943 chunks, all with a page; the 10 Markdown articles have no page and have a URL; the two
  PDF articles have both. `app.kb_search(text, vector, k, candidates, rrf_k)` has no source
  filter, so the *How to Brew* preference is done in `app.sheet_sources`.
- Pipeline order: `Start run` → step 0 → `Step 1 · input` → `Step 1 · read request` → `Step 1 ·
  log ok` → `Step 1 · save brief` → step 2 …; only `Step 1 · save brief`, `Step 2 · input` and
  `Respond failed` read `$("Step 1 · read request")`. `Save recipe` → `Finish run` → `Respond ok`
  (`run_id, ok, recipe_id, tries`).
- Step 1's `llm` object: `{model, think, temperature, seed, tries, prompt_tokens, output_tokens,
  llm_ms, done_reason}`; step 6 adds `steps`, `num_ctx`, `first_errors`. `evals/run.py read_run`
  counts first-try calls as try-1 rows with an `llm`, so row 16 (try 1) counts once and its
  retry in `calls − first`.
- b05 run 4983 (recipe 530): step 2 `mismatch` named 20C Imperial Stout, chose 15B; step 7
  `absent` and `unused_inventory` are `[]`; step 10 `values_used` has `colour`, `alpha`,
  `attenuation`, `ferm_c`, `boil`, `mash` and a `yeast amount` placeholder line (`1 pack … until
  the pitch rate is set (M7)`), which step 14's `pitch[].because` replaces on the sheet;
  steps 12–15 carry `values_used`, `acid.text`, `target.fallback`/`basis`, `co2.from`/`basis`,
  `pitch[].because` ("estimate").
- An absent wanted item comes from code (`app.choose_table`, db/042): `{word, kind: null, reason:
  'no product in the catalogue matches "…"'}`, so Special B is listed by step 9 without the LLM.
- n8n node types on the running instance (n8n MCP `get_node_types`): Chat Trigger 1.4
  (`public`, `mode: hostedChat`, `authentication: none | basicAuth | n8nUserAuth`,
  `options.responseMode: lastNode | responseNodes | streaming`); Chat node 1.3 (`operation: send |
  sendAndWait`, `responseType: approval | freeTextChat`, `approvalOptions.values.approvalType:
  single | double` with `approveLabel` / `disapproveLabel`, `options.limitWaitTime` default 45
  minutes). n8n docs (Context7 `/n8n-io/n8n-docs`): the Chat node's send-and-wait pauses the
  execution until the user answers, released in n8n 2.5. The field the approval answer arrives
  in is read from the first test execution (Task 10), not guessed.
- The `ctx7` CLI failed with "Invalid API key"; the Context7 MCP tools were used instead.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `db/054_recipe_sheet.sql` | new | `app.recipe.sheet text`; `app.save_sheet(recipe_id, sheet)`; `app.accept_recipe(recipe_id)` |
| `db/022_step2.sql` | changed | `app.step2_best_style(brief, request, guide_preference, style text default null)` |
| `db/055_sheet_facts.sql` | new | `app.sheet_facts`, `app.sheet_allowed_numbers`, `app.sheet_queries`, `app.sheet_sources`, `app.sheet_prompt` |
| `db/056_sheet_check.sql` | new | `app.prose_numbers`, `app.sheet_read_answer`, `app.sheet_retry_text` |
| `db/057_sheet_markdown.sql` | new | `app.sheet_markdown` and one helper per section |
| `shared/contracts/step2.input.schema.json` | changed | optional `style` |
| `shared/contracts/step16.input.schema.json`, `step16.output.schema.json`, `sheet.answer.schema.json` | new | step 16 in and out; the LLM's answer (Ollama `format`) |
| `shared/prompts/sheet.system.md` | new | step 16 system prompt |
| `n8n/workflows/step-2-best-fit-style.json` | changed | `style` input passed to SQL |
| `n8n/workflows/step-16-recipe-sheet.json` | new | sub-workflow `Step 16 · recipe sheet` (id `ST16recipesheet1`) |
| `n8n/workflows/recipe-pipeline.json` | changed | `style`, `brief`, `brief_llm`, `sheet_chunks`; given-brief branch; step 16 after the save; its failure finish |
| `n8n/workflows/recipe-chat.json` | new | `Recipe chat` (id `CHATrecipechat01`) |
| `tests/step16_sample.json` | new | the sub-workflow's `Test data` |
| `tests/test_recipe_sheet.py`, `test_sheet_facts.py`, `test_sheet_check.py`, `test_sheet_markdown.py` | new | Tasks 1, 4–6 |
| `tests/test_step2_pick.py`, `test_step3.py`, `test_contracts.py`, `test_workflows.py`, `test_pipeline.py`, `test_run.py`, `test_grade.py` | changed | as each task says |
| `evals/run.py`, `evals/grade.py` | changed | sheet columns and totals (R11) |
| `evals/results/<date>-m8.json` | new | the full brief run (A1, A3, A5) |
| `docs/RECIPE-ROADMAP.md`, `docs/WORKFLOW-ROADMAP.md`, `docs/OPERATIONS.md`, `docs/DATABASE.md` | changed | Task 12 (R12, A10) |
| `PROJECT.md` | changed | §4 rows, §8 per task |

Apply every SQL file as `postgres`, twice (idempotent), then check owners (OPERATIONS §4):
`docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/<file>.sql`, then
`select proname, pg_get_userbyid(proowner) from pg_proc where pronamespace = 'app'::regnamespace
and proname = any(<names>)` and `select tableowner from pg_tables where schemaname = 'app' and
tablename = 'recipe'` (all `postgres`). New SQL files get the header the others have (purpose, work
folder, needs, apply command, idempotent). Workflows: edit the JSON, copy to `shared/`,
`docker exec -e N8N_RUNNERS_BROKER_PORT=5699 -e N8N_RUNNERS_BROKER_LISTEN_ADDRESS=127.0.0.1 n8n n8n
import:workflow --input=/data/shared/<file>`, publish through the MCP (sub-workflows before the
workflows that call them), delete the copy, then `.venv/bin/python -m evals.workflows` (OPERATIONS
§5). Tests that need a saved recipe with its run rows build it in a rolled-back transaction with
`tests.test_save_process`'s helpers (b01, b08, b10, b14 and others `tests.test_validate.case`
supports), inserting the `run_step` rows 2, 6–11 and 12–15 that `app.sheet_facts` reads.

## Tasks

### Task 1: a recipe can hold a sheet and be accepted
Why: R8, R9, A7.
- [x] `db/054_recipe_sheet.sql`: `alter table app.recipe add column if not exists sheet text`;
      `app.save_sheet(recipe_id bigint, sheet text) returns bigint` (raises on an empty sheet or an
      unknown recipe; overwrites, so a re-run of step 16 on the same recipe works);
      `app.accept_recipe(recipe_id bigint) returns text` (raises when `sheet` is null; sets
      `status = 'final'`; a `final` recipe stays `final`; a `brewed` one is not changed back).
- [x] Apply twice; check the table owner and the two functions' owners.
- [x] Write `tests/test_recipe_sheet.py` (stack): save then read the sheet; accept with a sheet
      gives `final`; accept without one raises and leaves `draft`; `brewed` stays `brewed`.
      Seen failing first (functions missing).
- [x] Run `.venv/bin/pytest tests/test_recipe_sheet.py tests/test_save_recipe.py`, expect all pass.
- [x] `docs/DATABASE.md`: the column. PROJECT.md §4 Database row (app column) and §8.
Done when: the column exists owned by `postgres` and the tests pass.
Commit: `Add recipe sheet column and accept function`

### Task 2: step 2 obeys an optional style
Why: R5, A4 (webhook part).
- [x] `db/022_step2.sql`: `drop function if exists app.step2_best_style(jsonb, text, text)`, then
      create it with a fourth argument `style text default null` (Approach, "Style field").
      Resolve the code in `ref.beer_style` under the guide in force, BJCP before BA; unknown →
      `raise exception 'step 2: unknown style %'`. When it differs from the pick: `style` is it,
      no specialty swap, `mismatch` null, `alt_styles` = the pick first then the others (at most
      4), `reason` = `Picked <code> <name>: you chose it (style field); best fit <code>.`
      Header comment states the rule.
- [x] `shared/contracts/step2.input.schema.json`: optional `style` (`string` or null, not in
      `required`). `Step 2 · best-fit style`: trigger input `style` (`any`), read with
      `?? null`, query `select app.step2_best_style($1::jsonb, $2, $3, $4) as result`; `Test data`
      unchanged. Import, publish, export.
- [x] Write tests: `tests/test_step2_pick.py::test_style_field_keeps_named_style` (b05 brief,
      `style` 20C → 20C, mismatch null, `alt_styles[0]` 15B),
      `::test_style_field_equal_to_pick_changes_nothing` (15B → output equals the no-style
      output), `::test_unknown_style_field_raises`; `tests/test_step3.py::test_kept_style_lists_the_number`
      (step 3 on the 20C output lists ABV 4 as a `number` deviation). `tests/test_contracts.py`
      covers the new field. Seen failing first.
- [x] Run `.venv/bin/pytest tests/test_step2_pick.py tests/test_step2_signals.py tests/test_step3.py
      tests/test_contracts.py tests/test_workflows.py`, expect all pass.
- [x] PROJECT.md §8.
Done when: step 2 picks the given style and every existing step 2 test still passes.
Commit: `Let step 2 obey a style field`

### Task 3: the pipeline takes a style and a brief the chat already read
Why: R5, R6, A4.
- [x] `Recipe pipeline` `Run settings`: `style: body.style ?? null`, `brief: body.brief ?? null`,
      `brief_llm: body.brief_llm ?? null`. `Step 2 · input` passes `style`.
- [x] After `Step 1 · input`, an If `Brief given?`: no → `Step 1 · read
      request` as now; yes → `Check contract` (`step1.output`, the given brief, error output to
      `Step 1 · log failure`) → Set `Step 1 · given brief` `{brief, llm: brief_llm}`. Both branches
      join in a Set `Step 1 · result` `{brief, llm}`; `Step 1 · log ok`, `Step 1 · save brief`,
      `Step 2 · input` and `Respond failed` read `$("Step 1 · result")` instead of
      `$("Step 1 · read request")`. Row 1's input gains `brief_given` (true/false). Sticky notes
      say so. Import, publish, export.
- [x] `docs/OPERATIONS.md` §5 webhook line: `style`, `brief`, `brief_llm`.
- [x] Write `tests/test_pipeline.py::test_given_brief_is_step_1` (b01's brief and an `llm`
      object posted: row 1 output equals the brief, its `llm` equals the posted one, `brief_given`
      true) and `::test_style_field_reaches_step_2` (b05 with `style` 20C: row 2's style 20C, row
      3 has the ABV `number` deviation; the run's later outcome is not asserted). Seen failing
      first.
- [x] Run `.venv/bin/pytest tests/test_pipeline.py -k "given_brief or style_field or b01_logs or
      request_kept"`, expect all pass.
- [x] Note in PROJECT.md §8 whether the b05 / 20C run validated at step 11 (brief Assumption 2;
      read its `run_step` 11). If it fails all three tries, stop and hand back `needs-input`:
      A4's "keep 20C" case depends on it.
Done when: a webhook run with a given brief logs one step 1 row with the given `llm`, and `style`
reaches step 2.
Commit: `Accept a style and a read brief in the pipeline`

### Task 4: step 16 gathers its facts and finds its sources
Why: R1, R2, R3 (retrieval, §6.9).
- [ ] `db/055_sheet_facts.sql`:
      - `app.sheet_facts(run_id bigint) returns jsonb`: the run's saved recipe (row, items,
        deviations with `requested_by`, process), the style row (code, name, ranges, the BJCP
        `overallimpression` text), step 2 (`reason`, `alt_styles`, `mismatch`) with the ranges of
        the styles it names, steps 6–9 (`because`, `level`, `inventory`, `absent`,
        `unused_inventory`) and step 10 (`values_used`, `colour.because`, `og_used`, `rounding`)
        of the passed try (the try whose step 11 row has `passed` true), steps 12–15 (try 1),
        `choices` (the keys of the Approach with a label each), and `allowed_numbers`. Raises when
        the run has no saved recipe or no process.
      - `app.sheet_allowed_numbers(facts jsonb) returns numeric[]`: the Approach's list (numeric
        leaves via `jsonb_path_query(…, 'strict $.** ? (@.type() == "number")')`, range bounds,
        numbers in names), distinct.
      - `app.sheet_queries(facts jsonb) returns jsonb`: one `{topic, text}` per topic `style`,
        `grist`, `hops`, `yeast`, `water`, `mash`, `boil`, `fermentation`, `packaging`, built from
        names in the facts (e.g. `"Irish Stout roasted barley flaked barley grain bill"`).
      - `app.sheet_sources(queries jsonb, embeddings jsonb, per_query int default 3) returns
        jsonb`: per query `app.kb_search(text, embedding, 10)`, *How to Brew* first then score,
        `per_query` kept, each chunk once (first topic wins); each item `{chunk_id, topic,
        source_slug, title, url, section_path, page, text}`. `per_query` 0 gives `[]`.
- [ ] Apply twice; owners.
- [ ] Write `tests/test_sheet_facts.py` (stack): facts of a saved b10 case list every recipe item
      once in `choices` and the inventory flags; `allowed_numbers` holds the saved OG, a salt's
      grams and 15B's ABV bounds; a run without a recipe raises; `test_htb_first` (a mash query:
      every kept chunk is *How to Brew* when the top 10 hold at least `per_query` of them; uses
      Ollama for the embedding, as `tests/test_kb_search.py` does); `per_query` 0 gives none.
      Seen failing first.
- [ ] Run `.venv/bin/pytest tests/test_sheet_facts.py tests/test_kb_search.py`, expect all pass.
- [ ] PROJECT.md §8.
Done when: facts and sources come back for a saved case and the tests pass.
Commit: `Gather step 16 facts and sources`

### Task 5: the LLM's prose has a contract, a prompt and a check
Why: R1, R3, R7, A1, A6 (check level), §6.2, §6.3.
- [ ] `shared/contracts/sheet.answer.schema.json`: `{style_description: string, why: [{key,
      text, cite: [integer]}], notes: [{text, cite: [integer]}]}`, all required, no extra
      properties; `cite` may be empty (the "no source" slot). `shared/prompts/sheet.system.md`:
      prose only; one `why` per listed key; numbers only as shown in the facts, else none; cite
      chunk ids from the Sources list; *How to Brew* first where it covers the point; plain
      brewer's English.
- [ ] `db/055_sheet_facts.sql` gains `app.sheet_prompt(facts jsonb, sources jsonb) returns text`:
      the facts (labelled sections, numbers as the sheet shows them), the keys to write, the
      sources as `[<chunk_id>] <title> — <section>: <text>`.
- [ ] `db/056_sheet_check.sql`: `app.prose_numbers(t text) returns text[]` (the token rule of the
      Approach); `app.sheet_read_answer(content text, facts jsonb, sources jsonb) returns table
      (answer jsonb, errors text[])`: JSON parse, contract (`extensions.jsonschema_validation_errors`
      on the schema file's text passed in by n8n, as step 1 does), keys (missing, unknown,
      repeated), numbers (`number 152 in why[mash] is not a saved value or a style range value`),
      citations (`chunk 9999 in notes[0] was not retrieved`; `the sheet cites no source`);
      `app.sheet_retry_text(errors text[]) returns text`.
- [ ] Apply twice; owners.
- [ ] Write `tests/test_sheet_check.py` (stack, rolled back): a good answer passes; a wrong number,
      `66` for a 66.5 °C mash, a number in the style description, an unknown chunk id, no
      citation at all, a missing key and an unknown key each fail with their message; `1.040`
      for a saved 1.0401 and `15B` / `US-05` in a text pass; an empty `cite` on one line passes.
      `tests/test_contracts.py`: `sheet.answer` in `NAMES`, its absent slot (`why.cite`, array).
      Seen failing first.
- [ ] Measure the prompt once (scratchpad script, not committed): for the saved m7 run with the
      longest `app.sheet_prompt` among runs 4976–4998, ask Ollama as the workflow will (system
      prompt, `num_ctx` 32768, `num_predict` 4096, the contract as `format`) and record
      `prompt_eval_count` + 4096 ≤ 32768 and whether the answer passes the check, in PROJECT.md
      §8. Over the limit → stop and hand back `needs-input` (fewer chunks per query is the
      likely fix).
- [ ] Run `.venv/bin/pytest tests/test_sheet_check.py tests/test_contracts.py`, expect all pass.
Done when: the check rejects every listed case, and the measured prompt fits.
Commit: `Add the step 16 answer contract and check`

### Task 6: code writes the sheet in Markdown
Why: R1, R2, R3, A1, A2, A3.
- [ ] `db/057_sheet_markdown.sql`: `app.sheet_markdown(facts jsonb, sources jsonb, answer jsonb)
      returns text` calling one helper per section, in R2's order: style (pick, step 2 reason,
      alternative or mismatch, description, why); targets and results (batch, efficiency, OG,
      FG, ABV, IBU, SRM: target with its `from`, result, style range); fermentables (kg, %, "from
      your inventory"); hops (g, minutes, use); yeast (amount and unit from the saved row, cells,
      the pitch `because` with "estimate"); extras (g, when; "none"); how the amounts were worked
      out (step 10 `values_used` without the yeast placeholder line, colour and OG moves,
      rounding, then step 14's pitch line); water (row, basis, `fallback` label, salts per water,
      mash pH "estimate, unverified against Bru'n Water", the acid line); mash (steps, strike
      temperature and volumes); boil (minutes, additions in order); fermentation (steps with
      days and `move_on`, dry hops, secondary); packaging (CO₂ volumes with family, basis and
      `from`, priming sugar g at its temperature, packaging extras); Deviations box (subject,
      kind, level, "you asked" / "the pipeline chose" from `requested_by`, note); absent and
      unused items with what to do (not in the catalogue: "add it through
      `shared/ingredients/` and ask again, or brew without it"; all products excluded: "drop the
      exclusion to use it"; unused inventory: its reason, "keep it for another brew"); notes;
      sources (Approach, "Citations"). Each `why` goes under its item or section with its
      citation numbers. Display precision: gravity 3 decimals, ABV/%/°C/L 1 decimal, kg 2
      decimals, g and minutes whole.
- [ ] Apply twice; owners.
- [ ] Write `tests/test_sheet_markdown.py` (stack, rolled back, a fixed answer):
      `test_quantities_equal_saved_rows` (b01 and b10: every fermentable, hop, yeast and salt
      line and the OG/FG/ABV/IBU/SRM row parse back to the saved values at the display precision),
      `test_section_order` (R2's headings in order), `test_labels_shown` (estimate, acid line,
      fallback/basis, CO₂ `from`), `test_deviations_box` (b05 mismatch and a `model` deviation
      named as such), `test_inventory_named` (b10's inventory items marked),
      `test_absent_special_b` (facts with step 9 absent `Special B`, kind null: listed with what
      to do), `test_citation_format` (a book chunk shows title and PDF page, an article chunk
      section and URL; numbers follow first use). Seen failing first.
- [ ] Run `.venv/bin/pytest tests/test_sheet_markdown.py tests/test_sheet_check.py`, expect all
      pass.
- [ ] PROJECT.md §8.
Done when: the sheet of a saved case has every R2 section with the saved numbers.
Commit: `Write the recipe sheet in Markdown`

### Task 7: the pipeline writes and saves the sheet as step 16
Why: R4, R6, R7, R8, A1, A5, A6.
- [ ] Contracts `step16.input` `{run_id, recipe_id, model, think, temperature, seed, sheet_chunks}`
      and `step16.output` `{recipe_id, sources: [{chunk_id, topic}], answer, check: {numbers_ok,
      citations_ok, citations, errors}, sheet_chars}`; `tests/test_contracts.py` `NAMES` uses
      `range(17)`.
- [ ] Sub-workflow `Step 16 · recipe sheet` (id `ST16recipesheet1`), in the pattern of
      `steps-6-9-choose-ingredients.json` and `steps-12-15-process.json`: trigger → `Check
      contract` (`step16.input`) → Postgres `Sheet facts` (`app.sheet_facts`, `app.sheet_queries`) →
      HTTP `Embed queries` (`POST http://ollama:11434/api/embed`, `{model: "bge-m3", input: [texts],
      truncate: false}`) → Postgres `Find sources` (`app.sheet_sources($1, $2, $3)`) → `Build
      prompt` → read `sheet.system.md` and `sheet.answer.schema.json` → `Build model request`
      (`num_ctx` 32768, `num_predict` 4096, temperature and seed from the input) → `Ask model` →
      `Check answer` (`app.sheet_read_answer`) → ok? → else `Build retry request` (assistant answer
      + `app.sheet_retry_text`) → `Ask model again` → `Check second answer` → ok? → else
      `Step 16 · log failure` (ok false, `llm` with `tries` 2 and `first_errors`, error `step 16:
      <errors>`) → `Stop and Error`. On ok: `Write sheet` (`app.sheet_markdown`) → `Save sheet`
      (`app.save_sheet`) → `Check contract` (`step16.output`) → `Step 16 · log ok` (row 16, try 1,
      `llm` as step 1's with `num_ctx`, `tokens`) → return. Sticky note and `Test data`
      (`tests/step16_sample.json`: a saved m7 run's `run_id` and `recipe_id`; the note says it
      writes that recipe's sheet).
- [ ] `Recipe pipeline`: `Run settings` gains `sheet_chunks: body.sheet_chunks ?? 3`; `Save recipe` →
      `Step 16 · input` → `Step 16 · recipe sheet` (continueErrorOutput) → `Finish run` →
      `Respond ok` (adds `sheet: true`); error → `Finish run (failed, step 16)` → `Respond failed
      (step 16)` `{run_id, ok: false, failed_step: 16, recipe_id, error}`. Per-step sticky note:
      steps 0–16 built. Import and publish the sub-workflow, then the pipeline; export.
- [ ] `tests/test_workflows.py`: `SAMPLES` / `CONTRACT_OF` for the new file;
      `test_sheet_num_ctx_matches_choose` (the step 16 request's `num_ctx` equals
      `evals/fit_test.py` `CHOOSE_NUM_CTX`).
- [ ] `tests/test_pipeline.py::test_b01_validates_and_saves` also checks row 16 (ok, try 1, `llm`
      present, valid against `step16.output`, `check` all true), `app.recipe.sheet` not null and
      `first_try_calls` ≤ 3 (via `evals.run.read_run`). New `::test_sheet_fails_twice_without_sources`
      (b01 with `sheet_chunks` 0: row 16 ok false with `llm.tries` 2, the answer `failed_step` 16
      with `recipe_id`, that recipe `draft` with `sheet` null). Time the file.
- [ ] Run `.venv/bin/pytest tests/test_workflows.py tests/test_pipeline.py tests/test_contracts.py`,
      expect all pass.
- [ ] `docs/OPERATIONS.md` §5: thirteen workflows, `sheet_chunks`, `failed_step` 16 with
      `recipe_id`, the step 16 Ollama and embed calls. PROJECT.md §4 Orchestration row and §8.
Done when: a webhook run of b01 saves a recipe with its sheet and logs row 16, and the no-sources
run fails step 16 after one retry with the recipe kept as a draft.
Commit: `Write the recipe sheet in the pipeline`

### Task 8: the harness reports the sheets
Why: R11, A1, A5.
- [ ] `evals/run.py`: `read_recipe` adds `sheet` (present or not); `read_run` keeps row 16's
      `check`; the table gains a `sheet` column (`ok n=<citations>`, `FAIL(numbers)`,
      `FAIL(citations)`, `NONE` without a sheet, `-` without a recipe); totals gain `sheets
      saved x/y` (of runs with a saved recipe), `number check x/y`, `citation check x/y`,
      `citations` (total); first-try max and retry calls stay as they are. Pure helpers in
      `evals/grade.py` if a grade is needed (`grade_sheet(recipe, step16)`).
- [ ] Write tests in `tests/test_run.py` and `tests/test_grade.py` for the column and totals
      (sheet ok, failed check, no sheet, no recipe). Seen failing first.
- [ ] Run `.venv/bin/pytest tests/test_run.py tests/test_grade.py tests/test_recipe_briefs.py`,
      expect all pass.
- [ ] PROJECT.md §8.
Done when: `evals.run` prints the sheet column and totals.
Commit: `Report recipe sheets in the harness`

### Task 9: a full brief run has a checked sheet on every saved recipe (gate)
Why: A1, A2, A3, A5; A4 webhook part.
- [ ] `.venv/bin/python -m evals.run --save --label m8` (b01–b24). Record in PROJECT.md §8:
      validated count (a sanity check against m7's 19/24), sheets saved / saved recipes, number
      and citation checks, citations, first-try max (A5: ≤ 3), retry calls, run time.
- [ ] A2: read b10's sheet (every R2 section, inventory items named as used). One webhook run of a
      request naming Special B (e.g. `"A Belgian dubbel with Special B and dark candi sugar."`,
      `brief_id` `m8-special-b`): its sheet lists Special B as absent with what to do. If step 1
      does not put Special B in `wanted`, rephrase once and say so.
- [ ] A3: for b01, b05, b08, b13, b14, a read-only query: every citation number on the sheet maps
      to a chunk id in row 16's `sources`, and each shows page or section and URL as R3 says.
- [ ] A4 webhook part: b05 with `style` 20C gives a 20C recipe with ABV 4 as a deviation; b05
      without `style` picks 15B (both from the run above or one extra webhook call).
- [ ] Hand back `needs-approval` with the totals, any brief whose step 16 failed (its errors), and
      b10's and the Special B sheet's paths in the results for you to read.
Done when: you approved the results (A1, A2, A3, A5).
Commit: `Record the m8 full brief run`

### Task 10: the chat workflow runs the pipeline
Why: R4, R5, R9, R10.
- [ ] `Recipe chat` (id `CHATrecipechat01`): Chat Trigger (`public: true`, `mode: hostedChat`,
      `authentication: n8nUserAuth`, `options.responseMode: responseNodes`, a title and
      placeholder) → Set `Chat request` `{request: chatInput}` → `Step 1 · read request`
      (`run_id` 0, the default model, `think` false, temperature 0, seed 42; error → Chat send
      "I could not read the request: …") → `Step 2 · best-fit style` (`run_id` 0, `guide_preference`
      null, `style` null) → If `Mismatch?` → yes: Chat *Send and Wait* (approval, double):
      "You named <named>, but <range> is outside it; <chosen> fits better. Keep <named code>?",
      buttons `Keep <named code>` / `Take <chosen code>` → Set `style` to the chosen code (first
      word of `named` or `chosen`) → no / after: Chat *Send* "Building the recipe; this takes a
      few minutes." → HTTP `Run pipeline` (`POST http://localhost:5678/webhook/recipe-pipeline`,
      body `{request, brief, brief_llm, style, brief_id: "chat"}`, timeout 30 min) → If `Recipe
      ok?` → Postgres `select sheet from app.recipe where id = $1` → Chat *Send* the sheet → Chat
      *Send and Wait* (approval, double: `Accept` / `Not now`) "Accept this sheet as final?" →
      accepted: Postgres `select app.accept_recipe($1)` → Chat *Send* "Saved as final (recipe
      <id>)."; failed: Chat *Send* "The recipe stopped at step <n> (<step name>): <error>" with
      the recipe id when one was saved (a Set node holds the 17 step names). Read the approval
      answer field from the first test execution and use that name. Sticky note: what it does,
      the chat URL, that it needs an n8n login.
- [ ] Import, publish, export (`n8n/workflows/recipe-chat.json`). `tests/test_workflows.py`
      `test_file_name` covers it; it has no `Test data` note (tested by hand, Task 11).
- [ ] `docs/OPERATIONS.md` §5: the chat URL, User Auth, `brief_id` `chat` runs, the long wait.
      PROJECT.md §4 Orchestration row and §8.
- [ ] Run `.venv/bin/pytest tests/test_workflows.py`, expect all pass.
Done when: the chat workflow is published and exported.
Commit: `Add the recipe chat workflow`

### Task 11: you test the chat by hand (gate)
Why: A4, A7, A8; brief Assumption 1 (the hosted chat waits through a long run).
- [ ] Hand back `needs-input` with the chat URL and these steps for you: (1) in a private window,
      not logged in, open the chat URL: refused (A8); (2) logged in, ask b05's request, answer
      "Keep 20C": a 20C sheet with ABV 4 in the Deviations box; (3) b05 again, "Take 15B": a 15B
      sheet with the mismatch listed; (4) accept one sheet (A7); (5) any request of yours.
- [ ] After your test, read-only checks per chat run: `app.run.eval_id = 'chat'`, rows 0–16 like
      a webhook run, one row 1 with `llm.tries` 1 and `brief_given` true (A4), the accepted
      recipe `final` with its sheet (A7). Record in PROJECT.md §8. If the hosted chat dropped the
      long wait, stop and hand back `needs-input` with what happened.
Done when: you report the hand test passed and the checks agree.
Commit: `Record the chat hand test`

### Task 12: the docs describe step 16 and the chat as built
Why: R12, A10.
- [ ] `docs/RECIPE-ROADMAP.md`: TL;DR line 13, §6 (the "gate for every step" note, line 226) and
      P5 (line 294) state the bar as at most 3 first-try LLM calls per recipe (step 1, steps 6–9,
      step 16), retries reported; §3 row 16 and P8 say what is built, with the measured counts.
      `docs/WORKFLOW-ROADMAP.md`: G6 bar (line 198) the same wording; M8 row and G7 with the
      measured results; G7's "you brew one" stays open and points to the side track
      `s11-brew-day` (brew-day log and brew day, moved out of m8). No "about 2" or "≤ 2" left
      for the full pipeline (`grep -n "about 2\|≤ 2" docs/*ROADMAP.md`).
- [ ] `docs/OPERATIONS.md` complete for the chat and step 16; `docs/DATABASE.md` column done in
      Task 1. PROJECT.md §3 diagram line F unchanged unless wrong; §4 rows; §8.
Done when: A10's grep finds nothing and the docs match what runs.
Commit: `Describe step 16 and the chat in the docs`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| A sheet is saved only through `app.save_sheet`; accept needs a sheet | `tests/test_recipe_sheet.py` | 1 |
| Step 2 obeys `style`; equal to the pick changes nothing; kept style lists the number | `test_step2_pick.py::test_style_field_*`, `test_step3.py::test_kept_style_lists_the_number` | 2 |
| A given brief is logged as step 1 with its own `llm` (one step 1 call per chat request) | `test_pipeline.py::test_given_brief_is_step_1` | 3 |
| Sources prefer *How to Brew*; facts carry every item and the allowed numbers | `test_sheet_facts.py` | 4 |
| A prose number not saved, an unknown chunk, no citation, a missing key fail the check | `test_sheet_check.py` | 5 |
| Every quantity on the sheet equals the saved rows; R2 order; labels; deviations; absent items; citation format | `test_sheet_markdown.py` | 6 |
| Step 16 is logged and counted; two failed checks give `failed_step` 16 and a draft without a sheet | `test_pipeline.py::test_b01_validates_and_saves`, `::test_sheet_fails_twice_without_sources` | 7 |
| The harness reports sheets and checks | `test_run.py`, `test_grade.py` | 8 |

## Approved exceptions

None.

## Deviations
- 2026-10-29 · Tasks 12 and 14, Approach: the brew-day log (R13) and brew day (A9) moved out of m8 into the new side track `s11-brew-day` (draft brief), with `evals/brew_log.py`, `tests/test_brew_log.py` and `docs/brews/`; the docs task is now Task 12 and keeps G7's "you brew one" open, pointing to s11 — your answer to plan question 1. Your answer to question 2: the sheet must cite at least one retrieved chunk, as planned.
- 2026-10-29 · Task 1: the tests use b08 instead of b01 — b01 does not pass step 11 on its own, so `save_recipe` refuses it.
- 2026-10-29 · Task 3: `Brief given?` sits after `Step 1 · input`, not after `Step 0 · log ok` — the step 1 log nodes read `Step 1 · input` (run id, start time), which must have run on both branches. `Step 1 · given brief` takes `llm` as `brief_llm ?? {}` and `Step 1 · log ok` counts tokens with `?? 0`, so a given brief without an `llm` still logs.
