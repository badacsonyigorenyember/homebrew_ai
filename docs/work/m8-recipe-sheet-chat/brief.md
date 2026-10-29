# M8 · Step 16 and the chat: the recipe sheet you brew from

Status: approved
Slug: m8-recipe-sheet-chat · Branch: m8-recipe-sheet-chat
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) M8, checkpoint **G7** ·
[RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §3 step 16, §4, §8 P8 · PROJECT.md §4 (D5)
Needs: `m7-process` (shipped 2026-10-29), `s4-books-kb` and `s7-kb-articles` (shipped
2026-10-16), all in `docs/finished/`

## Why
The pipeline now runs steps 0 to 15 and saves a recipe with its process, but the output is rows
and JSON (`evals.show_recipe` prints them for a developer). The brewer needs one readable sheet:
what to buy, what to do, why each choice was made, what deviates from the style, and where the
reasoning comes from. The user talks to the assistant through n8n's chat trigger (D5), which does
not exist yet; it also has to ask the one question the pipeline may need back (b05: "15B Irish
Stout fits 4 % better. Keep 20C?").

## Goal
From the n8n chat, a request becomes a saved recipe and a recipe sheet. Code puts every number on
the sheet from the saved rows, and the second writing LLM call adds the reasons, with book and
article citations and a Deviations box, ready to brew from (the brew is
[`s11-brew-day`](../s11-brew-day/brief.md), which closes G7).

## Scope
In:
- Step 16: a sheet built from the saved recipe (`app.recipe`, `recipe_item`, `recipe_deviation`,
  `process`), the run's step outputs (the `because` lines, step 10's `values_used`, the labels of
  steps 12 to 15) and `kb` chunks found with `app.kb_search`. Code writes every quantity section; one LLM
  call writes only the prose; code checks the prose's numbers and citations.
- The sheet's contents follow the BJCP exam study guide's recipe question T14 (p. 33): style
  description, target parameters, ingredients with why and how the amounts were worked out, and
  the procedure from mash to packaging with a style reason for each part.
- Storing the sheet in a new `sheet` text column on `app.recipe` (a new `.sql` file) and logging
  step 16 as `run_step` 16.
- An n8n chat workflow (Chat Trigger, hosted chat) as the user's entry point, running the same
  pipeline as the webhook the harness uses.
- One question back on a style mismatch (step 2's `mismatch`), asked before the recipe is built
  with n8n's Chat node "Send and Wait for Response", and a new optional `style` field on the
  pipeline that step 2 obeys, so the choice is applied to the run.
- Accepting the sheet in the chat sets the recipe's `status` to `final`.
- The harness (`evals.run`) reports the sheet checks per brief.
- The LLM call bar's wording in RECIPE-ROADMAP and WORKFLOW-ROADMAP: three first-try calls.

Out:
- The brew-day log and the brew ([`s11-brew-day`](../s11-brew-day/brief.md)).
- Recipe editing by chat ("make it less bitter"; Priority 2), brewing Q&A, the batch log in the
  database (Priority 2), the `brewed` status. A UI other than n8n's hosted chat. A printable
  HTML or PDF sheet.
- Fixing what the sheet shows from earlier steps: the known `because` level errors, crystal
  share, thin hop schedules, the candi sugar amount (RECIPE-ROADMAP §8 Later). The sheet shows
  the saved values and reasons as they are.
- Acid amounts, water rows for more styles, tuning retrieval (RECIPE-ROADMAP §8 Later).
- Auth on the existing `recipe-pipeline` webhook (only the chat gets auth here).

## Requirements
R1. Step 16 reads only the saved recipe rows, its deviations and process, the run's step outputs
    and the retrieved `kb` chunks. It never computes or changes a number. Code writes every
    quantity section of the sheet (amounts, times, temperatures, volumes, OG/FG/ABV/IBU/SRM, CO₂
    volumes, salt grams) from the saved values. The LLM writes only the prose: the style
    description, the "why" lines and notes. A code check fails the step if any number in the
    LLM's prose is not a saved value or a style range value.
R2. The sheet has, in this order: style and why it was picked (with the alternative, if any);
    target parameters and the results (batch, OG, FG, ABV, IBU, SRM against the style ranges);
    fermentables (kg, %), hops (g, time, use), yeast (amount, pitch), extras (g, when); how the
    amounts were worked out (from step 10's `values_used` and adjustments); water (salts, mash pH
    estimate, the acid line); mash; boil; fermentation; packaging (CO₂ volumes, priming sugar);
    a Deviations box naming who asked for each (`requested_by`); a "why" for each main choice;
    absent or unused items (steps 6 to 9 `absent` and `unused_inventory`) with what to do about
    them. Labels from steps 12 to 15 ("estimate", "acid would be needed", a `fallback` or basis
    label) appear on the sheet next to their values.
R3. Each citation names a `kb.chunk` id that the run retrieved. It shows the source title and
    the page for a book chunk, or the section and the source URL for an article chunk (205 of the
    2,438 chunks have no page, measured 2026-10-29). A citation that does not resolve fails the
    check. Retrieval asks for *How to Brew* first where it covers the point (§6.9).
R4. The chat workflow starts the same pipeline as the webhook, and the run is logged the same way
    (`app.run`, `app.run_step` 0 to 16). The chat answers at once that the recipe takes a few
    minutes, then shows the sheet. A failed run shows the failed step and its error in plain
    words, and no sheet.
R5. The chat runs steps 1 and 2 before the build. When step 2 reports a `mismatch`, the chat
    asks once whether to keep the named style or take the best fit, then runs the pipeline with
    the chosen style in a new optional `style` field, which step 2 obeys. Step 1 runs once per
    request on the chat path too: the pipeline takes the brief the chat already read. The
    mismatch or the out-of-range number is listed as a deviation either way. Without `style` the
    pipeline picks the best fit as now; the harness never asks.
R6. LLM chat calls per recipe on the first try are at most 3 (step 1, steps 6–9, step 16),
    counted from `run_step.llm.tries` as `evals/run.py` does; retries are counted and reported,
    not hidden. Embedding calls for retrieval are not LLM chat calls and are
    not counted.
R7. If step 16's check fails, it retries once with the failed numbers or citations listed. A
    second failure finishes the run with `failed_step` 16; the recipe stays saved as `draft`
    without a sheet.
R8. The sheet is stored as Markdown in `app.recipe.sheet` (a new text column, added by a new
    `.sql` file applied as `postgres`) and returned to the chat.
R9. After the sheet, the chat offers to accept it; accepting sets `app.recipe.status` to `final`.
R10. The chat uses n8n User Auth: only someone logged in to this n8n can use it.
R11. `evals.run` reports per brief whether a sheet was saved, whether its number check and
    citation check passed, and the number of citations.
R12. RECIPE-ROADMAP (TL;DR, §6, P5) and WORKFLOW-ROADMAP (G6 bar) state the call bar as at most 3
    first-try LLM calls per recipe (step 1, steps 6–9, step 16), retries reported.

## Constraints
- PROJECT.md §6.1 and §6.7: numbers come from SQL or code; the LLM writes prose only.
- §6.2: one narrow writing call with a checkable output (a contract in `shared/contracts/`,
  checked with `pg_jsonschema`, G0).
- §6.3: the sheet has a legal way to say "absent" or "unknown".
- §6.9: *How to Brew* first for brewing-method citations; other books and articles only where it
  is silent.
- §6.8: readable over optimal; deterministic logic is SQL in `db/*.sql`, Code nodes only reshape
  JSON (G0).
- DB changes are `.sql` files applied with `psql` as `postgres` (OPERATIONS §4); the Supabase MCP
  is read-only.
- n8n: workflows with `onError` are imported with the n8n CLI (the MCP drops `onError`),
  published, and exported with `python -m evals.workflows` (OPERATIONS §5). Ollama is called with
  an HTTP Request node as steps 1 and 6–9 are, not the `Ollama Chat Model` node. n8n-skills rules
  for chat and LLM nodes apply.
- The chat model is D2 (`hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K`, thinking off); queries are
  embedded with `bge-m3` for `app.kb_search`.
- The m7 tests keep passing (the full suite with the stack up).

## Assumptions
- n8n 2.23.4 is running (checked 2026-10-29); the Chat node's "Send and Wait for Response" (n8n
  2.5 and later, n8n docs) holds the mismatch question and the accept step inside one execution,
  with no agent node. Whether the hosted chat waits through a run of 3 to 8 minutes without
  timing out is *(unverified)*.
- A recipe kept in 20C at 4 % ABV (b05, "keep 20C") passes step 11, since the user's number is a
  target and a listed deviation *(unverified)*.
- The step 16 prompt (saved recipe, reasons and retrieved chunks) fits the model's context on
  this machine *(unverified; the plan measures it with `prompt_eval_count`, as m5 did)*.
- The 19 briefs that validated in the m7 run (2026-10-28) still validate when re-run; the
  pipeline is not deterministic past step 1, so the count may move by one or two *(unverified)*.

## Acceptance criteria
A1. On a full brief run, every brief with a saved recipe has a sheet whose number check passes:
    every quantity section is written by code from the saved rows, and every number in the
    LLM's prose equals a saved value or a style range value (R1, R7, R11).
A2. b10's sheet has every R2 section in order, with its inventory items named as used. A request
    that asks for Special B (not in `ref`; `app.resolve_ingredient('Special B')` returns no row,
    measured 2026-10-29) gives a sheet that lists Special B as absent with what to do (R2).
A3. On 5 sample sheets (b01, b05, b08, b13, b14), every citation resolves to a `kb.chunk` the run
    retrieved, and shows page or section and URL as R3 says (R3).
A4. You test the chat by hand in n8n's hosted chat for A4, A7 and A8. b05 asked through the
    chat asks about the style once, before the build; answering "keep
    20C" gives a 20C recipe with the 4 % ABV listed as a deviation; answering "take 15B" gives a
    15B recipe with the mismatch listed. Each of these runs has one step 1 call (R5, R6). A
    webhook run with `style` set to `20C` gives a 20C recipe, and one without `style` picks 15B as
    now (R5). The chat run's `app.run` and `run_step` rows match a webhook run's shape, with row
    16 added (R4).
A5. On the full brief run, first-try LLM calls are at most 3 on every brief, and the totals show
    the retry calls (R6, R11).
A6. A failing step 16 check (a test with a wrong number or an unknown chunk id) gives one retry,
    then `failed_step` 16 with the recipe saved as `draft` and no sheet (R7).
A7. Accepting a sheet in the chat sets that recipe's `status` to `final`; the sheet is in
    `app.recipe.sheet`, and the column is owned by `postgres` like the rest of `app` (R8, R9).
A8. Opening the chat URL while not logged in to n8n is refused; logged in, it works (R10).
A9. Not checked in m8: the brew moved to [`s11-brew-day`](../s11-brew-day/brief.md), which
    closes G7's "you brew from it".
A10. RECIPE-ROADMAP and WORKFLOW-ROADMAP no longer say "about 2" or "≤ 2" LLM calls per recipe
    for the full pipeline; they say at most 3 first-try calls with retries reported (R12).

## Open questions
None. The five questions of 2026-10-29 are answered (see Deviations).

## Deviations
- 2026-10-16 · Needs: `s7-kb-articles` added (dry-hop, souring, water and BJCP introduction
  articles for the sheet's citations, [SOURCES.md](../../SOURCES.md)).
- 2026-10-29 · Brief revised against what shipped (m5, m6, m7, s4, s7). Why, Goal, Scope and R1:
  the sheet reads the saved `process` and the run's step outputs; quantities are written by code
  (pending Open question 2). R2 gains "how the amounts were worked out" and the steps 12–15
  labels (T14 asks for both; m7 labels its estimates). R3: articles have no page, so a citation
  shows section and URL. R4 gains the plain failure message; R5 names the mechanism (Chat node
  "Send and Wait for Response", which settles the old assumption) and the harness path. R6: three
  first-try calls, not two (Open question 4). New R7 (retry, then `failed_step` 16), R9 (accept
  sets `final`, was only in Scope), R10 (chat auth; OPERATIONS §5 left the webhook's auth to M8),
  R11 (harness reports the sheet). A1 counts briefs with a saved recipe (19/24 validated at m7)
  instead of "all validated briefs". A2: b10 never asked for Special B (it is a `needs` class,
  graded only, m5), so the absent case uses a request that names Special B. A3 names the five
  briefs. New A6-A8. The old Open question 2 (sheet format) is settled as Markdown in the chat,
  and a printable sheet moved to Out.
- 2026-10-29 · Your answers to the five open questions, each the recommended option, written in.
  (1) The sheet is Markdown in a new `app.recipe.sheet` text column, added by a new `.sql` file:
  Scope, R8, A7. (2) Code writes every quantity section from the saved rows, the LLM writes only
  the prose, and the number check covers the prose: Scope, R1, A1. (3) The style question comes
  before the build: the chat runs steps 1 and 2, asks, then runs the pipeline with a new optional
  `style` field that step 2 obeys. Step 1 runs once per chat request, so R6 holds on the chat
  path too: Scope, R5, A4. (4) The bar is at most 3 first-try LLM calls (step 1, steps 6–9,
  step 16), with retries reported, and the roadmaps' wording is updated: R6, new R12 and A10.
  (5) The chat uses n8n User Auth: R10, A8.
- 2026-10-29 · Added after approval, at your request. Scope In, new R13 and A9: a brew-day log
  made from the sheet, a file under `docs/brews/` with each step's planned and actual
  temperature, time and gravity, filled in during a Claude session on brew day. "Batch log" in
  Out now reads as the database batch log (Priority 2), which stays out. A4: you test the chat
  by hand in n8n's hosted chat, and that hand test covers A4, A7 and A8.
- 2026-10-29 · Brew day moved to its own side track, your decision ("move brew day (R13, A9,
  Tasks 12 and 14) into its own side track s11-brew-day"). The brew-day log left Scope In and R13
  is removed; A9 now points to [`s11-brew-day`](../s11-brew-day/brief.md), which closes G7's
  "you brew from it"; the brew-day log and the brew are listed under Out, and the Goal says the
  brew is s11. Everything else in m8 is unchanged.
