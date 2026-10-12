# AI Homebrew Assistant — Project Description

> **This file is the single source of truth for the project:** why it exists, what it
> is trying to do, how it is built, and how far along it is. If code and this file
> disagree, one of them is wrong. Fix it, and record the fix in the [Progress log](#8-progress-log).
>
> Last updated: **2026-10-12**

---

## 1. Why this project exists

Homebrewing knowledge is scattered across books, style guidelines, supplier data sheets and
forum posts. Good recipe design means pulling all of these together at once: style limits,
grain bill proportions, hop timing, yeast behaviour, water chemistry, process technique, and
what is actually in your cupboard or at your shop.

The assistant will:

1. **Ingest brewing books and references** into one reliable knowledge base, so every answer
   can cite its source.
2. **Design recipes from scratch** using that knowledge: style first, then proportions, then
   ingredients, then scaling.
3. **Grow into a general brewing companion** later (troubleshooting, water, process, batch
   history). Recipe design comes first.

It is self-hosted and local-first: models, data and books stay on the home machine.

---

## 2. Goals

### Priority 1 — Recipe creation ⭐

The assistant builds a complete, brewable recipe from a user brief that can include any of:

- the target **style** (BJCP or Brewers Association)
- **extra ingredients** or flavours wanted (fruit, coffee, vanilla, lactose, spices, wood, …)
- **ingredients the user already has** and **what they can get**
- preferences or constraints on **hops, fermentables, yeast and techniques**
- batch size and equipment or efficiency details

The output covers fermentables, hops (amount, timing, use), yeast, water/mash/boil/fermentation
process, and calculated targets (OG, FG, ABV, IBU, SRM). Every choice should be traceable to
the knowledge base or to a clearly labelled assumption.

### Priority 2 and later — other skills *(rough order, will change)*

- Brewing Q&A with citations ("why is my beer astringent?", "what does a diacetyl rest do?")
- Recipe critique and adjustment ("make this less bitter", "I have no Crystal 60, substitute")
- Water chemistry recommendations for a recipe
- Fault diagnosis from tasting notes
- Batch log: record what was brewed and learn from the results

### Non-goals (for now)

- A polished public UI or multi-user hosting
- Commercial-scale brewing
- Cloud LLMs as a hard dependency

---

## 3. How recipe creation works *(current approach)*

Agreed 2026-10-08. Full design, diagrams and worked examples:
[`docs/RECIPE-ROADMAP.md`](docs/RECIPE-ROADMAP.md). Database: [`docs/DATABASE.md`](docs/DATABASE.md).
Build order in n8n, with checkpoints and brief checks (proposal, 2026-10-12):
[`docs/WORKFLOW-ROADMAP.md`](docs/WORKFLOW-ROADMAP.md).

The approach is **proportions first, quantities last**, and **compute first**: the LLM reads the
request (step 1) and writes the recipe sheet (step 16). Everything in between is SQL or
deterministic code, with an LLM tie-break only when scores tie.

```
 A UNDERSTAND   0 brewer profile (stored) · 1 brief · 2 best-fit style · 3 deviation report
 B DESIGN       4 targets (style range + hint knobs + user's numbers) · 5 blueprint (ratios)
 C CHOOSE       6 yeast · 7 fermentables · 8 hops · 9 extras   (scored by code)
 D COMPUTE      10 calculate amounts, OG/FG/ABV/IBU/SRM · 11 validate, retry max 3×
 E PROCESS      12 water · 13 mash + boil · 14 ferment + condition · 15 package
 F DELIVER      16 write + save (reasons, deviations, citations)
```

- **The style is guidance, not law.** A best-fit style is always picked. Guidance is on by
  default: the pipeline's own choices stay in style, and anything the user asks for
  (ingredients or numbers) is accepted and listed as a deviation, never blocked.
- **Style rules are graded on 5 levels** (required · typical · allowed · out of style · changes
  style). They are not written per ingredient: a deterministic function compares the style's
  sensory envelope with the ingredient's automatically derived tags, its usage and its dose, so
  new ingredients need no rules ([`docs/STYLE-FIT.md`](docs/STYLE-FIT.md)).
- **Ratios** come from per-style statistics computed over community recipes (D7).
- Each step has an input/output contract that code can check, so a failure can be pinned to
  one step.

---

## 4. Tech stack

The infrastructure below has run since before the 2026-10-08 reset. Its compose definition
and the Supabase mount files were restored from the archive tag (§9) on 2026-10-09, without the
old `db-init` service; the old schema was not restored and is rebuilt piece by piece. *Why
restore rather than rebuild (was D6): the files were unchanged and needed as they were, and
without them no container could be recreated or even restarted.* Each piece is kept unless a
decision in §7 replaces it. How to operate the stack safely is in
[`docs/OPERATIONS.md`](docs/OPERATIONS.md).

| Layer | Choice | Role | Status |
|---|---|---|---|
| Database | **Supabase** (self-hosted Postgres 15) | Knowledge base, reference data (styles, ingredients), recipes | 🟢 running again since 2026-10-09 ([`recover-stack`](docs/finished/recover-stack/plan.md)). All schemas built 2026-10-11 ([`slim-ref`](docs/finished/slim-ref/plan.md)): `ref` 15 tables, `corpus` 7, `kb` 1, `app` 8, all 31 owned by `postgres`; design in [`docs/DATABASE.md`](docs/DATABASE.md). **P1a `ref` load done.** Measured 2026-10-11: `ref.source` 18 rows; `ref.beer_style` 285, BJCP 2021 116 + BA 2026 169 ([`style-loader`](docs/finished/style-loader/plan.md)); `ref.ingredient` 298, 0 without a source: `ref.fermentable` 81 = 74 grain malts from Weyermann, Viking and Simpsons ([`malt-loader`](docs/finished/malt-loader/plan.md)) + 7 adjuncts (flaked oats, corn, rice and barley, brown candi sugar and lactose from `hopline-adjuncts`, honey from `palmer-how-to-brew`; extract from Palmer Tables 18.5/24.1), `fermentability` `normal` 78 · `full` 2 (candi, honey) · `none` 1 (lactose) ([`adjunct-fermentables`](docs/finished/adjunct-fermentables/plan.md)); `ref.hop` 90, all from `hopline-hops`, 8 values from Beer Maverick ([`hop-loader`](docs/finished/hop-loader/plan.md)); `ref.yeast` 119 from `hopline-yeasts`, 93 with attenuation from the makers' sources, Brewfather and the user ([`yeast-loader`](docs/finished/yeast-loader/plan.md)); `ref.water_salt` 8, ion mg/L per g computed from IUPAC atomic masses ([`water-salts`](docs/finished/water-salts/plan.md)). Fermentables, hops and yeasts name each filled field's source in `field_source`. Every other table is empty until its phase. 10 random rows per loaded table spot-checked by the user against the sources, no errors ([`ref-spotcheck`](docs/finished/ref-spotcheck/plan.md), pack `db/checks/ref_spotcheck.sql`); the 7 adjuncts came after it and were checked in their own verification (16/16). Known gaps: `fermentable.role` stays empty until P3; no malt extracts, and the other hopline adjuncts (rye, wheat and chit flakes, white candi, fructose) are not loaded; `beer_style.co2_vol` was dropped (no source has it; back in P6). *Why this schema (was D4): each typed column is read by a pipeline step and everything else stays in `raw`; behaviour (usage effects, hint knobs, cut points, source weights) lives in code; all tables were created up front, empty, by user decision.* |
| Vector search | **pgvector** (HNSW) + Postgres full-text, fused (hybrid RAG) | Retrieval over book chunks | 🟡 `vector` 0.8.0 installed in schema `extensions`; `kb.chunk` created with HNSW + GIN indexes, empty (2026-10-11, [`slim-ref`](docs/finished/slim-ref/plan.md), shipped) |
| Orchestration | **n8n** (with its own Postgres for metadata) | Ingestion and recipe pipelines, agent | 🟢 running, 3 workflows published (measured 2026-10-12): `Recipe pipeline` (webhook `POST /webhook/recipe-pipeline`, logs to `app.run` / `app.run_step`), `Step 1 · read request` (stub) and `Check contract` (pg_jsonschema check); exported to `n8n/workflows/` ([`m0-harness`](docs/work/m0-harness/plan.md)) |
| Document parsing | **Docling Serve** (ROCm) | PDF → structured Markdown + `HybridChunker` | 🟢 running |
| LLM runtime | **Ollama** (ROCm) | Local chat and embedding models | 🟢 running |
| Chat model | `gemma4:12b-it-q8_0` *(also pulled: `qwen3.8:27b`)* | Reasoning, extraction, recipe drafting | ⚠️ to be re-evaluated (§7) |
| Embedding model | `bge-m3` (1024-dim) | Chunk and query embeddings | 🟢 pulled |
| Web search | **SearXNG** + `webarm` service | Lookups for what the books do not cover | 🔴 `searxng` down since 2026-10-08 (`settings.yml` lost in the reset, [`OPERATIONS.md`](docs/OPERATIONS.md) §1); recovery has an approved brief on branch `recover-searxng` (2026-10-09), not planned or merged. `webarm` running. Optional |
| Scripts | Python (`.venv`), `psycopg` 3, `pytest` (`requirements.txt`) | One-off extract/load jobs, evals | 🟡 `loaders/` package, 68 tests pass (measured 2026-10-11; the style-code test in `tests/test_recipe_briefs.py` needs the running DB). Shared helpers `loaders/common.py` (8 tests) and DB helpers `loaders/db.py` (`connect`, `source_id`, `upsert_ingredient`) ([`ref-schema`](docs/finished/ref-schema/plan.md)); hopline fetcher `loaders/fetch_hopline.py` (`python -m loaders.fetch_hopline OUT.json` for malts, `--hops`, `--yeasts`, `--adjuncts`; 7 tests). Loaders, each with an explicit SKU map where it reads hopline: styles `loaders/styles.py` (`python -m loaders.styles --bjcp PATH --ba PATH`, 4 tests, [`style-loader`](docs/finished/style-loader/plan.md)); malts `loaders/malts.py` + `loaders/malt_products.py` (`python -m loaders.malts --hopline PATH --catalogue PATH`, 9 tests, [`malt-loader`](docs/finished/malt-loader/plan.md)); hops `loaders/hops.py` + `loaders/hop_products.py` (`python -m loaders.hops --hopline PATH --report PATH`, Beer Maverick fill `BEERMAVERICK`, 9 tests, [`hop-loader`](docs/finished/hop-loader/plan.md)); yeasts `loaders/yeasts.py` + `loaders/yeast_products.py` (`python -m loaders.yeasts --hopline PATH --report PATH`, attenuation in `ATTENUATION`, 12 tests, [`yeast-loader`](docs/finished/yeast-loader/plan.md)); water salts `loaders/water_salts.py` (`python -m loaders.water_salts`, 3 tests, [`water-salts`](docs/finished/water-salts/plan.md)); adjuncts `loaders/adjuncts.py` + `loaders/adjunct_products.py` (`python -m loaders.adjuncts --hopline PATH`, Palmer rows as printed, PPG → extract % as PPG / 46 × 100, 6 tests, [`adjunct-fermentables`](docs/finished/adjunct-fermentables/plan.md)). Every loader gives the same rows when run twice. Read-only check pack `db/checks/ref_spotcheck.sql`; recipe test briefs `evals/recipe_briefs.toml` (20 briefs, P0) checked by `tests/test_recipe_briefs.py` (10 tests, [`test-briefs`](docs/finished/test-briefs/plan.md)) |
| Dev tooling | Claude Code: Supabase MCP (read-only, `.mcp.json`), official n8n MCP (local scope) + `n8n-skills` plugin, guard hook (`.claude/hooks/guard.sh`), `find-docs` skill + `.claude/rules/context7.md` (current library docs through the `ctx7` CLI), `database-schema-designer` skill (`.agents/skills/`, `skills-lock.json`) | Building and inspecting the stack; schema changes go through SQL files applied as `postgres` | 🟢 |
| Delivery workflow | Project skills `dev-flow` (orchestrator) + `dev-brief`, `dev-plan`, `dev-implement`, `dev-review`, `dev-verify`, `dev-ship` (`.claude/skills/`) | Brief → plan → build → review → verify → merge, one subagent per step, work in `docs/work/<slug>/` | 🟢 in use; 12 items shipped 2026-10-09 → 2026-10-11, each recorded in `docs/finished/<slug>/`; nothing in progress in `docs/work/` (checked 2026-10-11) |
| Eval guidance | Project skills `retrieval-evaluation-metrics`, `rag-evaluation-frameworks` (`.claude/skills/`) | Reference for building the retrieval test set and regression gate (§6.6) | 🟢 installed, not yet used |

**Pipeline and interface (was D3 and D5, decided 2026-10-11):** the recipe pipeline lives in
n8n, with as many of its parts there as possible; there is no Python service (the Python in
`loaders/` stays for one-off extract/load jobs). The user talks to the assistant through n8n's
chat trigger. *Why: the user's call.*

**Pipeline build (G0, decided 2026-10-12):**
- Deterministic logic is SQL functions in `db/*.sql`, called from n8n's Postgres node; Code nodes
  only reshape JSON. *Why: pytest can call the functions directly, and the data is already in Postgres.*
- A webhook (`POST /webhook/recipe-pipeline`) starts a run; tests read `app.run` and `app.run_step`
  back. *Why: the database is the record, and the same path serves the eval runner and the chat trigger later.*
- Step contracts are JSON Schema files in `shared/contracts/`, checked with `pg_jsonschema` by n8n
  and by tests. *Why: one validator on both sides, and n8n already sees that folder.*
- Workflows are edited in n8n and exported to `n8n/workflows/` (`python -m evals.workflows`).
  *Why: the visual editor stays the place to build, and the repo still holds a reviewable copy.*
- Eval results are saved as `evals/results/<date>-<milestone>.json`, committed at checkpoints only.
  *Why: a history of measured results without a commit for every run.*

**Hardware:** Ryzen 9 9900X · Radeon RX 9070 XT (16 GB VRAM, RDNA 4 / gfx1201) · 32 GB RAM.

---

## 5. Knowledge sources

Not ingested since the reset. On 2026-10-08 the source files were removed from `shared/rag-files/pending/` on purpose, to be re-added as each loader needs them. Now there: `how_to_brew.pdf`, `styles.json`, `ba_styles.json`, `hopline_malts.json`, `malt_catalogue.json`, `hopline_hops.json` (fetched and loaded 2026-10-10) and `hopline_yeasts.json` (fetched and loaded 2026-10-11), `hopline_adjuncts.json` (fetched and loaded 2026-10-11), the three malt catalogue PDFs (Weyermann, Viking Malt, Simpsons; there since 2026-10-09), plus the no longer used `malts.json` (checked 2026-10-11).

| Source | Type | Feeds | Status |
|---|---|---|---|
| *How to Brew* — John Palmer | PDF book | General process, ingredients, maths | 🟡 doc→calc: only Table 18.5 (4 flake rows) and Table 24.1 (3 sugar rows) loaded into `ref.fermentable` ([`adjunct-fermentables`](docs/finished/adjunct-fermentables/plan.md)) |
| *Water* — Palmer & Kaminski | PDF book | Water chemistry | ⬜ |
| *Yeast* — White & Zainasheff | PDF book | Yeast and fermentation | ⬜ |
| Malt data: hopline.hu malt list (`hopline_malts.json`) + Weyermann (Crop 2026), Viking Malt (2023), Simpsons (Nov 2025) catalogues (`malt_catalogue.json`) | Structured (fetched pages + hand-built from the PDFs) | Fermentable catalogue, 74 malts | ✅ loaded into `ref.fermentable`: 74 rows (Weyermann 37, Viking 32, Simpsons 5), 73 with EBC, 74 with extract, 62 with `max_pct` (2026-10-09); grain malts only, no sugars, adjuncts or extracts; 10 rows spot-checked against the source, no errors (2026-10-11, [`ref-spotcheck`](docs/finished/ref-spotcheck/plan.md)) |
| Adjunct data: hopline.hu flake, fermentable sugar and non-fermentable sugar lists (`hopline_adjuncts.json`, 14 products) | Structured (fetched page text) | Fermentable catalogue, 6 adjuncts | ✅ loaded into `ref.fermentable` (2026-10-11, [`adjunct-fermentables`](docs/finished/adjunct-fermentables/plan.md), shipped): flaked oats, corn, rice and barley, brown candi sugar, lactose (6 products, 1 pack size); the pages give only rice's max % (40), the candi's colour (225 EBC) and lactose's fermentability (`none`), the extract comes from Palmer; 7 products skipped with a reason (rye, wheat and chit flakes, white candi, fructose, rice hulls ×2); honey from Palmer only (hopline sells none) |
| Stout Style Guide | PDF | Stout styles and recipes | ⬜ |
| BYO pastry stouts | Markdown | Adjunct technique | ⬜ |
| Draught Beer Quality Manual 2019 | PDF | Serving and dispense | ⬜ |
| BJCP 2021 style guidelines (`styles.json`) | Structured | Styles, 116 rows | ✅ loaded into `ref.beer_style`: 116 rows, 96 with vitals (2026-10-09); 10 rows spot-checked against the source, no errors (2026-10-11, [`ref-spotcheck`](docs/finished/ref-spotcheck/plan.md)) |
| Brewers Association style guidelines (`ba_styles.json`) | Structured | Styles, 169 rows | ✅ loaded into `ref.beer_style`: 169 rows, 144 with OG (2026-10-09); 10 rows spot-checked against the source, no errors (2026-10-11, [`ref-spotcheck`](docs/finished/ref-spotcheck/plan.md)) |
| Hop data: hopline.hu hop list (`hopline_hops.json`, 106 products) | Structured (fetched pages) | Hop catalogue, 90 hops | ✅ loaded into `ref.hop`: 90 rows (5 LUPOMAX), purpose aroma 35 / bittering 4 / dual 51, 90 with alpha and total oil, 89 with origin (2026-10-10); Delta, Lotus, Sterling alpha + oil, Mount Hood oil and Enigma purpose come from Beer Maverick (source `beermaverick`), loaded by the hop loader (2026-10-11); 10 rows spot-checked against the source, no errors (2026-10-11, [`ref-spotcheck`](docs/finished/ref-spotcheck/plan.md)); all 8 Beer Maverick values checked against beermaverick.com by the user, all match (2026-10-11) |
| Fault data (`beer_faults.json`) | Structured | Faults (21) | ⬜ |
| Brewer's Friend recipes (Kaggle, CC0) | Structured, 179,455 recipes | Per-style ratios (D7) | ⬜ 35,620 (views > 500) in the archive dump, measured 2026-10-08 |
| Yeast data: hopline.hu dry and liquid yeast lists (`hopline_yeasts.json`, 129 products) | Structured (fetched pages) | Yeast catalogue, 119 yeasts | ✅ loaded into `ref.yeast`: 119 rows (dry 81, liquid 38; YeastFlow 38, Lallemand 18, Norse Nectar 17, Fermentis 13, Mangrove Jack's 13, Brewline 10, Gozdawa 9, YeasterBunny 1), 119 with temperature, 113 with flocculation, 114 with alcohol tolerance, 93 with attenuation (2026-10-11, [`yeast-loader`](docs/finished/yeast-loader/plan.md), shipped); no page states attenuation; it is copied as printed from the sources the user named: YeastFlow catalogue 34, Lallemand catalogue 17, Brewfather figures from the user 16 (Gozdawa 8, Brewline 8), Mangrove Jack's data sheets 13, Fermentis data sheets 12, user-supplied 1 (YF-666, printed "800-100", confirmed 80–100); 10 rows spot-checked against the source, no errors (2026-10-11, [`ref-spotcheck`](docs/finished/ref-spotcheck/plan.md)); none for Norse Nectar and YeasterBunny (user decision) and 8 strains with no figure in their source ([`report.md`](docs/finished/yeast-loader/report.md)). *Why hopline, not Brewtarget's BeerJSON (was D8): the user chose the shop's own yeasts, as for malts and hops (2026-10-11); the Brewtarget files are no longer needed* |
| AHA recipe-design crash course · Oregon Brew Crew recipe formulation · BJCP exam study guide | Free web / PDF | Design method, rules of thumb, output checklist | ⬜ candidate, not downloaded |

**Style guides (was D1, decided 2026-10-11):** both are used. BJCP 2021 is preferred; BA 2026 is
used where it describes the requested beer better, or the user is asked which to use. The user
can also set a preference: BJCP only or BA only. Within a guide, the best-fit style is the
**base style** by default (adjuncts and extras are ignored). When the request makes an adjunct a
stated, prominent feature, the specialty code is expected (e.g. 31B Alternative Sugar Beer for a
honey-forward blonde), with the base style as the alternative; a specialty category is also used
when no meaningful base style exists ([`test-briefs`](docs/finished/test-briefs/brief.md) R3, agreed
by the user 2026-10-11). Step 2 is not built yet; it follows this rule (P4). *Why: the user's
call: BJCP stays first, as in the first build and the test briefs, but a beer BA describes
better is not forced into BJCP, and the brewer can choose.*

---

## 6. Design principles

Several of these are lessons from the first build (see §9).

1. **Knowledge and truth stay separate.** Book text is *knowledge*, retrieved with RAG and
   cited. Style ranges, ingredient specs and user batches are *structured data*, queried
   exactly. Do not make an LLM read a number that a SQL query can return.
2. **Small LLM steps, each with a checkable contract.** A 12B model drops constraints as they
   pile up. Several narrow calls with validated outputs beat one large prompt.
3. **Leave room to say "absent."** Every output schema needs a legal way to say "not in the
   catalogue", "unknown" or "conflict". A schema with no such slot pushes the model to invent
   something.
4. **The ingredient catalogue is first-class data.** Recipes can only be as good as the
   inventory they choose from. Fermentables, hops, yeasts and adjuncts each need clean,
   complete records.
5. **Keep it simple.** The first build became too complex to reason about. Add a component
   only when a measured need justifies it.
6. **Measure before and after.** Every change to the recipe pipeline is run against a fixed
   set of test briefs, so improvement is shown, not assumed.
7. **Compute first.** Anything that can be SQL or deterministic code must be: it is faster,
   cheaper and testable. The LLM is only for free text in and prose out. Every new source gets
   a *doc → calculation* pass first: its tables, formulas and rules of thumb become data or
   code, and only the remaining prose goes to RAG.
8. **Readable over optimal.** Someone opening a workflow, function or file should understand
   what it does from that file alone. Prefer explicit, somewhat repetitive logic over generic
   machinery driven by config. The first build kept n8n workflow behaviour in database config
   tables: efficient, but you had to trace the tables to know what a workflow did. Optimise
   only when a measured need requires it, and keep the readable version's shape.

---

## 7. Open decisions

| # | Question | Leaning | Status |
|---|---|---|---|
| D2 | Chat model: which model gets the most out of this machine (16 GB VRAM, 32 GB RAM)? | Best answer quality wins; slower answers are fine (user, 2026-10-11). Benchmark `qwen3.8:27b` (worked before), `gemma4:12b` and other candidates that fit, on the recipe test set | open |
| D7 | Where do the recipe ratios (grist %, hop split) come from? | Brewer's Friend corpus through automatic quality gates (no hand curation) → `corpus.style_profile`, thin styles shrunk toward their family, specialty styles use the base style, extra sources weighted (books, DIY Dog, own batches) ([`docs/STYLE-PROFILES.md`](docs/STYLE-PROFILES.md)). Belongs to P3 (moved from P0, 2026-10-11) | open |
| D9 | Who approves the extracted style sensory envelopes before they enter `ref`? | LLM extracts BJCP prose, code parses BA fields, the user reviews. Belongs to P3 (moved from P0, 2026-10-11) | open |

---

## 8. Progress log

Newest first. One entry per meaningful change: what was done, and why if that is not obvious.

### 2026-10-12
- `m0-harness` task 6: three workflows built through the n8n MCP, published, and exported to
  `n8n/workflows/` (first real use of the export path: the `--output` file route works, 3 files
  with credential ids and names only, no secrets). `Recipe pipeline` starts a run, calls the step 1
  stub, logs `run_step` (ok or failure with its error), finishes the run and answers
  `{run_id, ok, failed_step?, error?}`. `Check contract` reads the contract file and calls
  `jsonschema_validation_errors`. The `Postgres account` credential connects as
  `postgres` / database `postgres` (measured). `tests/test_pipeline.py` (3 stack tests: b01 logs
  step 1, empty request logs a failure naming `step1.input`, a request with quotes, commas, `%`,
  `$1` and a newline is kept verbatim) pass. An Execute Workflow error output carries the message
  as a plain string in `$json.error`. Suite: 110 passed (measured).
- `m0-harness` task 5: `evals/workflows.py` exports n8n workflows into `n8n/workflows/`
  (`python -m evals.workflows`), with 3 tests in `tests/test_workflows.py`. Export goes through
  `--output` to a file in `shared/`, because stdout carries log lines. With 0 workflows n8n exits 1
  with "No workflows found", which the code treats as an empty list. Suite: 107 passed (measured).
  The file-output path is not yet exercised with a real workflow (Task 6).
- `m0-harness` task 4: pure graders in `evals/grade.py` (steps 1-3 and `grade_run`) with 16 unit
  tests in `tests/test_grade.py`. A deviation matches on same kind and same subject (quantity for
  number/mismatch, hint rows for conflict, whole word for ingredient). Suite: 104 passed; without
  the stack 85 passed, 19 deselected (measured).
- `m0-harness` task 3: eight JSON Schema contracts in `shared/contracts/` (`step0`-`step3`, input and
  output), each with a legal absent/unknown/conflict slot. `pg_jsonschema` accepts draft 2020-12.
  Measured: 88 passed with the stack up (16 new in `tests/test_contracts.py`).
- `m0-harness` task 2: `db/015_app.sql` now installs `pg_jsonschema` and gives `app.run` a nullable
  `brief_id` plus `eval_id`, `finished_at`, `ok`, and `app.run_step` an `error` column with a check
  (failed step has an error, passed one has none). Applied twice without error; owner `postgres`.
  Measured: 72 passed with the stack up (4 new in `tests/test_run_log.py`).
- `m0-harness` task 1: recorded the G0 decisions in §4 (and in WORKFLOW-ROADMAP G0). Added the
  `stack` pytest marker with a `tests/conftest.py` that skips those tests when Postgres or n8n is
  down. Measured: 68 passed with the stack up, 67 passed + 1 deselected with `-m "not stack"`, and
  1 skipped when n8n's health URL was pointed at a dead port.
- Planned `m0-harness` ([`docs/work/m0-harness/plan.md`](docs/work/m0-harness/plan.md)): 7 tasks.
  Record the G0 decisions and add a `stack` test marker; add the run-log columns and
  `pg_jsonschema`; JSON Schema contracts for steps 0–3 in `shared/contracts/`; pure graders;
  workflow export to `n8n/workflows/`; the `Recipe pipeline` webhook with a step 1 stub and run
  logging; the eval runner and the G0 baseline run. Nothing built yet.
- Wrote draft briefs for all 13 WORKFLOW-ROADMAP work items in `docs/work/` (none approved, no
  branches yet): [`m0-harness`](docs/work/m0-harness/brief.md),
  [`m1-read-request`](docs/work/m1-read-request/brief.md),
  [`m2-best-fit-style`](docs/work/m2-best-fit-style/brief.md),
  [`m3-deviations`](docs/work/m3-deviations/brief.md),
  [`m4-targets-blueprint`](docs/work/m4-targets-blueprint/brief.md),
  [`m5-choose-ingredients`](docs/work/m5-choose-ingredients/brief.md),
  [`m6-compute-validate`](docs/work/m6-compute-validate/brief.md),
  [`m7-process`](docs/work/m7-process/brief.md),
  [`m8-recipe-sheet-chat`](docs/work/m8-recipe-sheet-chat/brief.md),
  [`s1-maths`](docs/work/s1-maths/brief.md), [`s2-corpus`](docs/work/s2-corpus/brief.md),
  [`s3-style-fit`](docs/work/s3-style-fit/brief.md), [`s4-books-kb`](docs/work/s4-books-kb/brief.md).
  Slugs carry the roadmap id (`m<N>-`, `s<N>-`), folders stay flat; the rule is in
  `.claude/skills/dev-flow/conventions.md`. Writing them fixed the order: m3 waits for
  s1 → s2 → s3 (ingredient deviations need `level()`), and `fermentable.role` moves to s2 (the
  corpus name map needs it).
- Wrote [`docs/WORKFLOW-ROADMAP.md`](docs/WORKFLOW-ROADMAP.md), a **proposal** (nothing built
  or decided): milestones M0–M8 for building the recipe pipeline in n8n test-first, 8
  checkpoints (G0 where code lives and how tests reach n8n, through G7), and a brief check per
  milestone. Measured on `evals/recipe_briefs.toml`: the 20 briefs cover steps 1–3 as they
  are; 10 gaps listed for later milestones (e.g. only 5 state a batch size, `needs` names
  Special B and Lactobacillus which are not in `ref`, no held-out briefs). `pytest` 68 passed.
- `dev-flow` now sets a model per subagent: Opus for brief, plan and review (judgment work;
  review stays at least as strong as the code's author), Sonnet for implement, verify and ship
  (specified by the plan; implement runs most often, so most of the cost saving is there). The
  orchestrator stays on the session model. Not yet measured: whether Sonnet raises the number
  of review fix rounds.

### 2026-10-11
- Decided D3 and D5 (user): the recipe pipeline lives in n8n, as much of it as possible, with
  no Python service; the interface is n8n's chat trigger (§4 note). The split inside n8n is
  discussed later. D2 stays open with a new leaning: get the most performance the machine
  allows, speed second; benchmark `qwen3.8:27b` and other models. RECIPE-ROADMAP P8 and
  DATABASE.md §6 updated.
- Checked every doc outside `docs/finished/` against the repo, git history and the running stack
  (DB catalog and counts, `docker ps`, `ollama list`, `pytest` 68 passed) and fixed what was out
  of date: §4 Database, Scripts, Dev tooling, Delivery workflow and Web search rows rewritten to
  the measured current state (the Database row had kept older, contradicting counts; the Scripts
  row lacked `loaders/water_salts.py`); §5 malt PDFs are in `pending/`, not `~/Downloads`; dead
  `docs/work/` links in this log. DATABASE.md: `water_salt` 8 rows (said empty), 18 sources,
  `field_source` on yeasts too, molar mass lives in `loaders/water_salts.py`.
  FILL-REF-README.md: links fixed after its move, marked done. RECIPE-ROADMAP.md: P1a done,
  P1b not started; `hops.json` and `malts.json` no longer named as sources. STYLE-FIT.md: hop
  purpose is loaded, not derived; yeast example is a catalogue yeast. OPERATIONS.md: re-check
  dates and model list. CLAUDE.md: `find-docs` skill listed. STYLE-PROFILES.md,
  DATABASE-REVIEW.md and README.md needed no change.
- Shipped `adjunct-fermentables` ([`docs/finished/adjunct-fermentables/`](docs/finished/adjunct-fermentables/verification.md)),
  merged to `main`: `python -m loaders.fetch_hopline --adjuncts` and `loaders/adjuncts.py` (with
  the explicit map `loaders/adjunct_products.py`) load 7 adjuncts into `ref.fermentable` (flaked
  oats, corn, rice and barley, brown candi sugar, lactose, honey; ids 3392–3398), extract from
  Palmer Tables 18.5/24.1 and hopline's printed figures, every filled field sourced; new column
  `ref.fermentable.fermentability` (`normal` 78, `full` 2, `none` 1); lactose removed from the
  `ref.misc` categories; gap report covers all 47 test-brief names (38 found, 7 added, 2 left
  out). Verification: 16/16 spot checks, 68/68 tests; re-run before the merge: `pytest` 68 passed.
- Fixed adjunct-fermentables review should-fix 1 ([`docs/finished/adjunct-fermentables/review.md`](docs/finished/adjunct-fermentables/review.md)): DATABASE.md and the `loaders/adjuncts.py` docstring note that sugar and honey extracts are Palmer's as-sold PPG ÷ 46 (water included), so P2 must not moisture-correct them. Docs only; no data changed.
- Added the adjunct-fermentables gap report ([`docs/finished/adjunct-fermentables/report.md`](docs/finished/adjunct-fermentables/report.md), R6/A3): 47 test-brief ingredients, 38 found in `ref`, 7 added (ids 3392–3398), 2 left out (Special B: hopline sells none; Lactobacillus: user decision); each NULL in the 7 new rows listed with its reason. Coverage check: `missing: []`.
- Implemented adjunct-fermentables Task 4 ([`docs/finished/adjunct-fermentables/plan.md`](docs/finished/adjunct-fermentables/plan.md)):
  `python -m loaders.adjuncts --hopline shared/rag-files/pending/hopline_adjuncts.json` loaded
  7 adjuncts into `ref` (7 hopline products skipped). Measured: `ref.fermentable` 81 rows
  (74 malts + 7 adjuncts), fermentability `normal` 78, `full` 2, `none` 1; 298 ingredients,
  0 without a source; every filled adjunct field has a `field_source` entry (0 rows missing);
  a second load gives the same 7 rows (md5 `ca6c03d7…` before and after); 68 tests pass.
  DATABASE.md counts updated.
- Implemented adjunct-fermentables Task 3 ([`docs/finished/adjunct-fermentables/plan.md`](docs/finished/adjunct-fermentables/plan.md)):
  `loaders/adjuncts.py` builds 7 adjuncts (4 flakes, brown candi sugar, lactose, honey) from
  hopline's pages and Palmer's Tables 18.5 and 24.1 (`loaders/adjunct_products.py`). Hopline
  wins, Palmer fills the gaps, `field_source` names each filled field's source; `normal`
  fermentability needs none. `build` refuses an unmapped SKU and a hopline figure whose words
  are not on the page. Measured: `build` on `hopline_adjuncts.json` gives 7 items; 68 tests
  pass. Not loaded into `ref` yet (Task 4).
- Implemented adjunct-fermentables Task 2 ([`docs/finished/adjunct-fermentables/plan.md`](docs/finished/adjunct-fermentables/plan.md)):
  `python -m loaders.fetch_hopline --adjuncts OUT.json` saves hopline's flake, fermentable sugar
  and non-fermentable sugar listings and each product page's visible text (`page_text`,
  "Főkategória" up to "Vélemények"). Measured: 14 products (flakes 9, fermentable sugars 3,
  non-fermentable sugars 2), all with text, in `shared/rag-files/pending/hopline_adjuncts.json`.
  Source `hopline-adjuncts` added: 18 `ref.source` rows. 62 tests pass.
- Implemented adjunct-fermentables Task 1 ([`docs/finished/adjunct-fermentables/plan.md`](docs/finished/adjunct-fermentables/plan.md)):
  `ref.fermentable.fermentability` (`full` · `normal` · `none`, default `normal`), source
  `palmer-how-to-brew`, and `lactose` dropped from the `ref.misc` category check. The three
  SQL files applied twice as `postgres` without error. Measured: 74 fermentables, all
  `normal`, other columns unchanged (same md5 before and after); `misc_category_check` without
  lactose; 17 `ref.source` rows; 61 tests pass. DATABASE.md and STYLE-FIT.md updated: lactose
  and honey are fermentables, not misc.
- Planned `adjunct-fermentables` ([`docs/finished/adjunct-fermentables/plan.md`](docs/finished/adjunct-fermentables/plan.md)):
  flaked oats, corn, rice and barley, brown candi sugar, lactose and honey from hopline's pages
  and Palmer's Tables 18.5/24.1. A `fermentability` category (`full` · `normal` · `none`) on
  `ref.fermentable`, lactose out of `ref.misc`, and a gap report against the 20 test briefs.
- Shipped `ba-guide-docs` ([`docs/finished/ba-guide-docs/`](docs/finished/ba-guide-docs/verification.md)),
  merged to `main`: RECIPE-ROADMAP §8 and DATABASE.md §9 now agree with D1 (BA is a step-2
  guide, not a future option). Verified 9/9 spot checks, 61/61 tests.
- Implemented ba-guide-docs ([docs/finished/ba-guide-docs/](docs/finished/ba-guide-docs/plan.md)):
  RECIPE-ROADMAP §8 moves BA from Later into P4 step 2 per D1; DATABASE.md §9 BA style-family
  row now triggered by a BA style needing a profile (still not built: 169 BA rows,
  category_code NULL).
- Planned `ba-guide-docs` ([`docs/finished/ba-guide-docs/plan.md`](docs/finished/ba-guide-docs/plan.md)):
  one docs-only task.
- Wrote brief for `ba-guide-docs` ([`docs/finished/ba-guide-docs/`](docs/finished/ba-guide-docs/brief.md)):
  the RECIPE-ROADMAP "Later · BA as a selectable guide" item and the DATABASE.md §9 BA
  style-family trigger are out of date against D1.
- Shipped `test-briefs` ([`docs/finished/test-briefs/`](docs/finished/test-briefs/verification.md)),
  merged to `main`: P0 is done. [`evals/recipe_briefs.toml`](evals/recipe_briefs.toml) holds
  the 20 user-approved recipe test briefs across 16 BJCP categories, checked by
  `tests/test_recipe_briefs.py` (10 tests; the style-code test needs the running DB). D1
  decided and the R3 classification rule recorded in §5. Verification: 13/13 spot checks,
  61/61 tests; re-run before the merge: `pytest` 61 passed.
- `test-briefs` review fix ([`docs/finished/test-briefs/`](docs/finished/test-briefs/review.md)): D1
  decided by the user: both style guides are used, BJCP 2021 preferred, BA where it describes
  the beer better or the user is asked; the user can set BJCP only or BA only. D1 moved from §7
  to a §5 note, which also states the R3 classification rule: base style by default; when the
  request makes an adjunct a prominent feature, the specialty code, with the base style as the
  alternative (why b12 expects 31B, alt 18A). The briefs still expect BJCP codes. RECIPE-ROADMAP
  §9 notes D1 as decided. Suite: 61 passed.
- `test-briefs` Task 3 ([`docs/finished/test-briefs/`](docs/finished/test-briefs/plan.md)): P0 test
  briefs recorded. [`evals/recipe_briefs.toml`](evals/recipe_briefs.toml) holds 20 briefs, all
  20 reviewed and approved by the user (two reworded in review: b12 now expects 31B Alternative
  Sugar Beer, alt 18A, because the request makes honey prominent; b16 adds a bit of rice as an
  ingredient deviation). Measured by `pytest -s tests/test_recipe_briefs.py`: 16 BJCP
  categories, 3 stouts/porters, 4 lagers, 2 Belgian, 2 wheat/sour, 3 hop-forward; adjuncts
  flaked oats 2, candi sugar 1, flaked corn 1, flaked rice 2, lactose 2, honey 2; deviations
  ingredient 3, number 3, mismatch 1, conflict 1; guidance off 1; exclusions 2, inventories 2;
  every §7 hint row used; 4 batch sizes (10, 15, 20, 23 L); 0 fruit or non-gravity extras. Suite: 61
  passed. RECIPE-ROADMAP §8 shows P0 done; D7 and D9 moved to P3 and stay open (§7).
- Planned `test-briefs` ([`docs/finished/test-briefs/plan.md`](docs/finished/test-briefs/plan.md)):
  20 briefs in `evals/recipe_briefs.toml` (TOML, read with the standard library), checked by
  `tests/test_recipe_briefs.py` against `ref.beer_style` and the brief's coverage minimums,
  then the user's review, then the P0 status in PROJECT.md and RECIPE-ROADMAP.
- Wrote brief for `test-briefs` ([`docs/finished/test-briefs/`](docs/finished/test-briefs/brief.md)):
  P0's 20 test briefs, written fresh in English, covering the adjunct fermentables oats, candi
  sugar, corn, rice, lactose and honey, with no fruit and no non-gravity extras (user decisions).
- Shipped `ref-spotcheck` ([`docs/finished/ref-spotcheck/`](docs/finished/ref-spotcheck/verification.md)),
  merged to `main`: the read-only pack `db/checks/ref_spotcheck.sql` and the measured P1a
  results in PROJECT.md and DATABASE.md (16 sources, 285 styles, 291 ingredients, 0 rows
  without a source, style-fit tables empty; 10 rows per loaded table and the 8 Beer Maverick
  hop values checked by the user, no errors). P1a is done. Verification: 11/11 spot checks,
  51/51 tests; re-run before the merge: `pytest` 51 passed.
- `ref-spotcheck` review fix: DATABASE.md §7 step-2 gap note now names the Beer Maverick
  values as `hop.field_source` records them (Delta, Lotus, Sterling alpha + oil, Mount Hood
  oil, Enigma purpose; 8 values, queried 2026-10-11). The user checked all 8 against
  beermaverick.com: all match.
- `ref-spotcheck` Task 1 ([`docs/finished/ref-spotcheck/plan.md`](docs/finished/ref-spotcheck/plan.md)):
  read-only pack `db/checks/ref_spotcheck.sql` prints counts for all 15 `ref` tables, rows
  without a source and 10 random rows per loaded table. Measured: 16 sources, 285 styles,
  291 ingredients (74 malts, 90 hops, 119 yeasts, 8 salts), 0 rows without a source, the 8
  style-fit tables 0. The user spot-checked the sample (Sterling's hand-entered Beer Maverick
  values included): no errors. This meets RECIPE-ROADMAP P1's "10 rows spot-checked per
  table". `pytest` 51 passed.
- Shipped `water-salts` ([`docs/finished/water-salts/`](docs/finished/water-salts/verification.md)),
  merged to `main`: `loaders/water_salts.py` computes the ion mg/L from 1 g in 1 L for the 8
  common brewing salts from IUPAC atomic masses in tested `Decimal` code, and
  `python -m loaders.water_salts` loads them into `ref.ingredient` (kind `water_salt`, source
  `water-chemistry`) and `ref.water_salt`: 8 rows, stable on re-run. Verification: 7/7 spot
  checks, 52/52 tests (51 pytest + load-twice); re-run before the merge: `pytest` 51 passed.
- `water-salts` Task 2 ([`docs/finished/water-salts/plan.md`](docs/finished/water-salts/plan.md)):
  `python -m loaders.water_salts` loads the 8 salts into `ref.ingredient` (kind `water_salt`,
  source `water-chemistry`) and `ref.water_salt` (`formula`, `ion_mg_per_l_per_g`). Run twice:
  `ref.water_salt` 8 rows both times (measured). 51 tests pass.
- `water-salts` Task 1 ([`docs/finished/water-salts/plan.md`](docs/finished/water-salts/plan.md)):
  `loaders/water_salts.py` computes the mg/L of each ion from 1 g of each of the 8 brewing salts
  in 1 L from IUPAC atomic masses (gypsum Ca 232.8 / SO4 557.9, CaCl2·2H2O Ca 272.6 / Cl 482.3,
  baking soda Na 273.7 / HCO3 726.3). Not loaded yet. 51 tests pass.
- Shipped `yeast-loader` ([`docs/finished/yeast-loader/`](docs/finished/yeast-loader/verification.md)),
  merged to `main`: `loaders/fetch_hopline.py --yeasts` saves hopline.hu's 129 dry and liquid
  yeast pages and `loaders/yeasts.py` with the SKU map `loaders/yeast_products.py` loads them
  as 119 yeasts (dry 81, liquid 38; 8 non-beer yeasts skipped), all values outside `raw` in
  English. `ref.yeast`: 119 with temperature, 113 with flocculation, 114 with alcohol
  tolerance, 93 with attenuation copied as printed from 6 named sources, each field's source in
  `field_source`; 16 `ref.source` rows. Verification: 24/24 spot checks, 48/48 tests; re-run
  before the merge: `pytest` 48 passed.
- `yeast-loader` re-review note 1 ([`docs/finished/yeast-loader/plan.md`](docs/finished/yeast-loader/plan.md)):
  the report glosses the Hungarian page values it quotes in English beside the printed text
  (`'Belga Ale' (Belgian ale)`, `'Közepes' (medium)`, `"max tartomány": max range`). Loader run:
  119 rows, 119/113/114/93 filled, unchanged. 48 tests pass.
- `yeast-loader` change request ([`docs/finished/yeast-loader/plan.md`](docs/finished/yeast-loader/plan.md)):
  no Hungarian outside `raw`. The one Hungarian value, Brewline `302170` "Bajor Búza", is now
  `Bavarian Wheat` (row renamed in place, same id); the `hopline-yeasts` source notes and the
  report are in English, page quotes kept as printed. New test checks the names, type,
  flocculation and `field_source` values. Loader run twice: 119 rows, 119/113/114/93 filled
  (temp, flocculation, alcohol, attenuation), unchanged. 47 tests pass.
- `yeast-loader` Task 6, user answers ([`docs/finished/yeast-loader/plan.md`](docs/finished/yeast-loader/plan.md)):
  8 Brewline products get the user's Brewfather figures (`[a,a]`, source `brewfather`; "german
  wheat" taken as Brewline Bavarian Wheat `302170`), YF-666 gets `[80,100]` as `user-supplied` (page prints
  `800-100`); the unused `brewline-catalogue` source is removed (16 sources, applied twice).
  Run twice, same result: 119 rows, 93 with attenuation, every entry matches the DB; 26 without,
  reasons in [`report.md`](docs/finished/yeast-loader/report.md). 46 tests pass.
- `yeast-loader` Task 6 ([`docs/finished/yeast-loader/plan.md`](docs/finished/yeast-loader/plan.md)):
  attenuation copied as printed from the makers' own sources into `ATTENUATION` in
  `loaders/yeast_products.py` (84 entries, each with source, URL, printed text, date) and loaded
  into `ref.yeast.attenuation_pct` with `field_source` per source; 6 sources added to
  `ref.source` (17 rows, applied twice). Run twice, same result: 119 rows, 84 with attenuation
  (YeastFlow 34, Lallemand 17, Mangrove Jack's 13, Fermentis 12, Brewfather 8); every entry
  re-read against its source and matches the DB. Not filled (35, reasons in
  [`report.md`](docs/finished/yeast-loader/report.md)): Norse Nectar 17 and YeasterBunny 1 (user),
  Brewline 10 (its catalogue PDF lists only other, 500 g strains; asked), Gozdawa W-34/70, CBC-1
  (`n/a%`), BR-8, YF-666 (`800-100` printed), YF-801/998/999 (empty). 10 tests in
  `test_yeasts.py` pass, 46 in the suite.
- `yeast-loader` Task 5 ([`docs/finished/yeast-loader/plan.md`](docs/finished/yeast-loader/plan.md)):
  `python -m loaders.yeasts --hopline PATH --report PATH` loads hopline's yeasts into
  `ref.ingredient` + `ref.yeast`. Run twice, same result both times: 119 rows (dry 81,
  liquid 38; producer counts as planned), 119 with temperature, 113 with flocculation, 114 with
  alcohol tolerance, 0 with attenuation; type ale 75, kveik 20, lager 17, brett 2, unknown 5;
  US-05 `[18,28]` °C, medium, 11 %. The 8 non-beer yeasts are skipped. The report
  ([`report.md`](docs/finished/yeast-loader/report.md)) lists where data block and description
  disagree (temperature 23, flocculation 9, alcohol 5; M20 noted as another strain's
  description), the Brewline rows against the strains they copy, and the 3 kveiks with
  Lactobacillus. 9 tests in `test_yeasts.py` pass, 45 in the suite.
- `yeast-loader` Task 4 ([`docs/finished/yeast-loader/plan.md`](docs/finished/yeast-loader/plan.md)):
  `loaders/yeast_products.py` is the explicit hopline SKU map: 119 yeasts (producer, product id,
  name), 2 Brewline 2 g packs joined to their 12 g product, 8 non-beer yeasts skipped with the
  reason. Names follow the makers' own spelling where it differs from hopline's (checked on
  yeastflow.com and lallemandbrewing.com, e.g. `YF-205 Holy Cölibate`, `Diamond`). Measured
  against `hopline_yeasts.json`: all 129 SKUs in exactly one map; YeastFlow 38, Lallemand 18,
  Norse Nectar 17, Fermentis 13, Mangrove Jack's 13, Brewline 10, Gozdawa 9, YeasterBunny 1;
  dry 81, liquid 38. `test_yeast_map` passes, 44 in the suite.
- `yeast-loader` Task 3 ([`docs/finished/yeast-loader/plan.md`](docs/finished/yeast-loader/plan.md)):
  `loaders/yeasts.py` parses one hopline yeast page into a `Yeast`: temperature in °C (any other
  unit raises), flocculation and style family through fixed maps (unknown raises), alcohol
  tolerance as the data block's range top with the description as fallback, figures from the
  main page only, per-field `field_source` and every page in `raw`; no files, no DB yet.
  7 new tests pass, 43 in the suite; all 121 beer-yeast pages in `hopline_yeasts.json` parse
  without error (one-off check).
- `yeast-loader` Task 2 ([`docs/finished/yeast-loader/plan.md`](docs/finished/yeast-loader/plan.md)):
  `ref.source` gains `hopline-yeasts` and loses the unused `brewtarget-default-data`
  (0 ingredients referenced it); `ref.yeast` gains `field_source jsonb not null` for per-field
  provenance. Both SQL files applied twice as `postgres` without error; measured 11 sources and
  the new column both times; 36 tests pass.
- `yeast-loader` Task 1 ([`docs/finished/yeast-loader/plan.md`](docs/finished/yeast-loader/plan.md)):
  `python -m loaders.fetch_hopline --yeasts OUT.json` reads both yeast pages through their
  product-list request and saves each page's name, spec table, data block and long description
  (table, `<strong>` labels, text). Measured: 129 products (dry 90 on 5 pages, liquid 39 on 2,
  none in both), all with name, data block and description; 6 fetcher tests pass. Malt and hop
  page parsing unchanged (8 pages compared old vs new).
- Planned `yeast-loader` ([`docs/finished/yeast-loader/plan.md`](docs/finished/yeast-loader/plan.md)):
  the source is now hopline.hu's dry and liquid yeast pages instead of the Brewtarget BeerJSON
  files (user decision, D8 closed, §5). Measured on the pages: 129 products (dry 90, liquid 39),
  listed only through the pages' own product-list request; temperature, flocculation, alcohol
  tolerance and style family on nearly all, attenuation on none. Expects 119 yeasts (Brewline
  as its own producer, 2 g packs joined to their 12 g product, 8 non-beer yeasts skipped),
  attenuation from the maker catalogues and data sheets the user named per producer
  (Brewfather figures for 8 Gozdawa strains; none for Norse Nectar and YeasterBunny).
- Wrote brief for `hop-figures` (later dropped, never shipped; in git at
  `941f102^:docs/work/hop-figures/brief.md`), narrowed to the hop loader's Beer Maverick fill
  below plus the slim-ref follow-up doc edits; the oil-unit check moved to a draft brief
  `hop-oil-unit` (never committed).
- Hop loader keeps the Beer Maverick figures: `BEERMAVERICK` in `loaders/hop_products.py`
  (Delta, Lotus, Sterling alpha + total oil, Mount Hood total oil, Enigma purpose, as the user
  entered them in the DB) fills alpha, oil and purpose only where hopline has none, with
  `field_source` `beermaverick` and the entry in `raw`; the report lists the filled fields.
  `db/011_ref_sources.sql` now holds the user's `beermaverick` source row (applied: 11 sources,
  no change). Measured: the first loader run reset Enigma's purpose the user had set (the map
  didn't have it yet); after adding it, two runs give hop data identical to the pre-run
  snapshot: 90 hops, 90 with alpha and total oil, purpose aroma 35 / bittering 4 / dual 51.
  `pytest` 34 passed.
- The user entered the missing hop figures by hand in the DB from BeerMaverick: alpha and total
  oil for Delta, Lotus and Sterling, total oil for Mount Hood (`field_source` `beermaverick`).
  Measured: `ref.hop` 90 rows, 90 with alpha, 90 with total oil. Recorded in the `hop-figures`
  brief (oil-unit check still open). Dropped the `source-fetch-date` follow-up (hopline source
  editions following the fetched file's date): user decision, not needed.
- Follow-ups after `slim-ref`: updated the `ref-spotcheck` plan (pack covers the 7 loaded tables
  and only counts the 8 empty style-fit tables; source check on `beer_style` and `ingredient`;
  expected suite 40; malt gap note without `malts.json`), the `fill-ref` index (schema changes
  since the split, P1b/P3 rows) and the `ref` rules in DATABASE.md §2 (style-fit tables carry no
  `source_id`), plus a BA style-family note in DATABASE.md §9. Wrote draft briefs for
  `hop-figures`, dropped later (confirm the hopline oil unit; fill alpha for
  Delta, Lotus, Sterling and oil for those and Mount Hood, measured `NULL` 2026-10-11).
  `yeast-loader` and `water-salts` needed no change.
- Shipped `slim-ref` ([`docs/finished/slim-ref/`](docs/finished/slim-ref/verification.md)),
  merged to `main`: the approved database review is applied. 7 unused `ref` columns dropped
  and the loaders re-run (285 styles, 164 ingredients, 74 malts, 90 hops); `ref` 15 tables,
  `corpus` 7, `kb` 1, `app` 8, all owned by `postgres`, the new ones empty; `vector` 0.8.0 with
  `kb.chunk` (vector(1024), HNSW + GIN). Verification: 22/22 spot checks, 42/42 tests (33
  pytest + 9 database), re-run before the merge.
- `slim-ref` Task 6 ([`docs/finished/slim-ref/plan.md`](docs/finished/slim-ref/plan.md)): rewrote
  [`docs/DATABASE.md`](docs/DATABASE.md) to describe the built design (31 tables, names checked
  against the catalog; row counts measured: 10 sources, 285 styles, 164 ingredients, 74 malts,
  90 hops, every other table empty); new §8 "Behaviour in code, not tables" and §9 "Later".
  [`docs/DATABASE-REVIEW.md`](docs/DATABASE-REVIEW.md) marked approved and applied, with the
  "Everything in §5" deviation. STYLE-FIT, STYLE-PROFILES and RECIPE-ROADMAP now place usage
  effects, hint knobs, cut points and source weights in code; STYLE-FIT derives the malt role
  from EBC + name keywords (`fermentable.type` is gone). `water-salts` and `ref-spotcheck` plans
  updated for the dropped columns. D4 closed (§4 Database row). Suite: 33 passed.
- `slim-ref` Task 5 ([`docs/finished/slim-ref/plan.md`](docs/finished/slim-ref/plan.md)): created the
  `app` schema from review §5.5 in `db/015_app.sql` (applied twice, no error): schema and 8 empty
  tables owned by `postgres` (`brewer_profile`, `inventory`, `brief`, `recipe`, `recipe_item`,
  `recipe_deviation`, `run`, `run_step`); `app.recipe` has the typed `batch_l`,
  `efficiency_pct`, `og`, `fg`, `abv`, `ibu`, `srm`. Measured totals: `ref` 15, `corpus` 7,
  `kb` 1, `app` 8 tables (31, review §6). Created now, empty, by user decision ("Everything in
  §5"); P4–P5 fill them. Suite: 33 passed.
- `slim-ref` Task 4 ([`docs/finished/slim-ref/plan.md`](docs/finished/slim-ref/plan.md)): installed
  `vector` 0.8.0 in schema `extensions` (created as `postgres`; owner `supabase_admin`, like the
  other 8 extensions) and created the `kb` schema from review §5.4 in `db/014_kb.sql` (applied
  twice, no error): schema and empty `kb.chunk` owned by `postgres`, `embedding vector(1024)`
  (bge-m3), indexes `chunk_embedding_idx` (HNSW), `chunk_fts_idx` (GIN), `chunk_source_id_idx`;
  `ref.source.file_path` (text) added. Created now, empty, by user decision ("Everything in §5");
  P7 fills it. Suite: 33 passed.
- `slim-ref` Task 3 ([`docs/finished/slim-ref/plan.md`](docs/finished/slim-ref/plan.md)): created
  the `corpus` schema from review §5.3 in `db/013_corpus.sql` (applied twice, no error):
  schema owned by `postgres`, 7 empty tables owned by `postgres` (`recipe`, `recipe_item`,
  `name_map`, `style_profile`, `style_grist`, `style_hop_use`, `style_ingredient`) and the
  indexes `recipe_style_id_idx`, `recipe_item_recipe_id_idx`, `recipe_item_kind_raw_key_idx`.
  Created now, empty, by user decision ("Everything in §5"); P1b and P3 fill them. Suite: 33 passed.
- `slim-ref` Task 2 ([`docs/finished/slim-ref/plan.md`](docs/finished/slim-ref/plan.md)): created
  the style-fit vocabulary from review §5.2 in `db/012_style_fit.sql` (applied twice, no error):
  `fermentable.role` (text, empty) and 8 empty tables (`misc`, `tag`, `tag_synonym`,
  `ingredient_tag`, `sensory_dimension`, `style_sensory`, `style_character`, `style_rule`).
  `ref` now has 15 tables, all owned by `postgres`. Rolled-back inserts confirmed `style_rule`
  rejects a row with neither ingredient nor tag, and `style_character` rejects a row without its
  `style_sensory` envelope. Suite: 33 passed.
- `slim-ref` Task 1 ([`docs/finished/slim-ref/plan.md`](docs/finished/slim-ref/plan.md)): dropped the
  7 unused `ref` columns (`beer_style.edition`, `co2_vol`; `fermentable.potential_sg`, `type`;
  `hop.beta_pct`, `oils_pct`; `water_salt.molar_mass`) in `db/010_ref_schema.sql`;
  `ref.beer_style` is now unique on `(source_id, code)`. Styles, malts and hops loaders lose the
  dropped fields (`potential_sg()` stays for the maths library) and were re-run twice: 285 styles
  (285 distinct `(source_id, code)`), 164 ingredients, 74 malts (74 with extract, 0 with
  `potential_sg` in `field_source`), 90 hops (87 with alpha, 0 with `beta_pct` in
  `field_source`); hop report unchanged; Citra's beta still in `raw`. Suite: 33 passed.
- Planned `slim-ref` ([`docs/finished/slim-ref/plan.md`](docs/finished/slim-ref/plan.md)): apply the approved database review: drop
  the 7 unused `ref` columns and re-run the loaders, then create all `corpus`, `kb`, `app` and
  style-fit tables now, empty (user decision "Everything in §5"), and rewrite DATABASE.md.
  Nothing built yet.
- Wrote [`docs/DATABASE-REVIEW.md`](docs/DATABASE-REVIEW.md), a **proposal** (nothing applied):
  each column traced to the pipeline step that reads it, with priorities. Proposes dropping 7
  columns from the built `ref` tables (`beer_style.edition`, `co2_vol`; `fermentable.potential_sg`,
  `type`; `hop.beta_pct`, `oils_pct`; `water_salt.molar_mass`), moving `usage_effect`, `hint_knob`
  and `source_weight` to code, merging `kb.document` into `ref.source`, typed tables instead of
  arrays and mixed jsonb, and a profile snapshot on `app.recipe`. Measured: `ref` `raw` columns
  hold ~630 kB, so the full source records stay. DATABASE.md is unchanged until approval.

### 2026-10-10
- Shipped `hop-loader` ([`docs/finished/hop-loader/`](docs/finished/hop-loader/verification.md)),
  merged to `main`: `loaders/fetch_hopline.py --hops` saves hopline.hu's 106 hop product pages
  and `loaders/hops.py` with the SKU map `loaders/hop_products.py` upserts them as 90 hops.
  `ref.hop` has 90 rows (5 LUPOMAX): purpose aroma 34 / bittering 4 / dual 51 / none 1, alpha
  `NULL` only for Delta, Lotus and Sterling, each field's source in `field_source`; 10
  `ref.source` rows (`hopline-hops` added, `hops-json` and `hopslist` removed).
  Verification: all 17 checks pass; re-run before the merge: `pytest` 33 passed.
- `hop-loader` Task 5 ([`docs/finished/hop-loader/plan.md`](docs/finished/hop-loader/plan.md)):
  `loaders/hops.py` builds, loads and reports (`python -m loaders.hops --hopline PATH --report PATH`).
  Ran it twice, same results both times: `ref.hop` 90 rows (5 LUPOMAX), purpose aroma 34,
  bittering 4, dual 51, `NULL` 1 (Enigma); alpha `NULL` for Delta, Lotus, Sterling; origin
  `NULL` for Dolcita; Citra `{US}`, dual, alpha [10,15], beta [3,4.5], oil [1.5,3]; every hop
  ingredient from `hopline-hops`. Report: [`report.md`](docs/finished/hop-loader/report.md)
  (Nectaron pack sizes differ, Amarillo and Mosaic LUPOMAX repeat the pellet). 8 tests in
  `tests/test_hops.py` pass, suite 33 passed.
- `hop-loader` Task 4 ([`docs/finished/hop-loader/plan.md`](docs/finished/hop-loader/plan.md)):
  `loaders/hop_products.py` maps every hopline hop SKU: 90 main SKUs to a hop name (5 LUPOMAX
  hops kept separate), 16 extra pack sizes to their main SKU, and Delta and Lotus to `NULL`
  figures. `test_hop_map` passes (suite 32 passed); a one-off check found all 106 SKUs of the
  fetched `hopline_hops.json` in the map and every mapped SKU in the file.
- `hop-loader` Task 3 ([`docs/finished/hop-loader/plan.md`](docs/finished/hop-loader/plan.md)):
  `loaders/hops.py` parses one hop from its hopline pages (pure, no files or DB): figures to
  numranges (`?` stays `NULL`, an unknown format raises), country to ISO code (unknown raises),
  purpose from hopline's subcategories, table alpha with the data block's `Alfasav` as fallback.
  6 tests in `tests/test_hops.py` pass, suite 31 passed; all 318 figures and every country in the
  fetched `hopline_hops.json` parse.
- `hop-loader` Task 2 ([`docs/finished/hop-loader/plan.md`](docs/finished/hop-loader/plan.md)):
  `db/011_ref_sources.sql` adds the `hopline-hops` source (fetched 2026-10-10) and deletes the
  unused `hops-json` and `hopslist` rows (0 ingredients referenced them). Applied twice as
  `postgres`: 10 `ref.source` rows both times. Suite 25 passed.
- `hop-loader` Task 1 ([`docs/finished/hop-loader/plan.md`](docs/finished/hop-loader/plan.md)):
  `loaders/fetch_hopline.py` now accepts non-numeric SKUs, reads each page's spec table
  (`spec_table`) and data block (`params`), and has a `--hops` mode that also saves the SKUs of
  hopline's aroma / bittering / dual listings. Ran it: 106 products in
  `shared/rag-files/pending/hopline_hops.json`, every name and spec table set; categories aroma
  101, bittering 60, dual 56. 4 fetcher tests pass, suite 25 passed.
- Planned `hop-loader` ([`docs/finished/hop-loader/plan.md`](docs/finished/hop-loader/plan.md)),
  re-scoped from three hop JSON files (`hops.json`, `hops.hopslist.json`, Brewtarget) to the
  hops hopline.hu sells: 106 products (measured 2026-10-10) = 85 varieties + 5 LUPOMAX + 16
  extra pack sizes, so 90 `ref.hop` rows, figures from hopline's pages only (source
  `hopline-hops`). User decisions: alpha from the spec table, the data block's `Alfasav` only as
  fallback; Delta and Lotus (pages show Falconer's Flight / Taurus) loaded with `NULL` figures;
  LUPOMAX as 5 separate hops. Nothing built yet.
- Wrote brief for `hop-loader` ([`docs/finished/hop-loader/`](docs/finished/hop-loader/brief.md)).

### 2026-10-09
- Shipped `malt-loader` ([`docs/finished/malt-loader/`](docs/finished/malt-loader/verification.md)),
  merged to `main`: `loaders/fetch_hopline.py` saves hopline.hu's malt pages and
  `loaders/malts.py` merges them with the hand-built maltster catalogue figures (catalogue wins,
  hopline fills gaps, a `user-supplied` figure fills only what both lack) and upserts them.
  `ref.fermentable` has 74 malts (Weyermann 37, Viking 32, Simpsons 5): 73 with EBC, 74 with
  potential, 62 with `max_pct`, each field's source in `field_source`; 11 `ref.source` rows.
  Verification: all 20 checks pass; re-run before the merge: `pytest` 23 passed.
- `malt-loader` fix round after verification ([`docs/finished/malt-loader/`](docs/finished/malt-loader/plan.md)),
  two user data decisions: Simpsons Crystal T50, DRC and Crystal Extra Dark now take hopline's
  "min 70%" extract (the `IGNORE_HOPLINE_EXTRACT` special case is removed; the user reversed
  "Keep them NULL"); Weyermann Acidulated Malt gets extract 64.9 from the user's "PPG 1.03 ≈ 30"
  through a new `user-supplied` source (`db/011_ref_sources.sql`, applied twice) and
  `USER_SUPPLIED` in `loaders/malt_products.py`, which fills a field only where both the
  catalogue and hopline lack it. Measured after two loads, same both times: 74 rows, 73 with
  EBC, 74 with potential (no `NULL` left; from Weyermann 36, Viking 31, hopline 6, user-supplied
  1), 62 with `max_pct`. Crystals: extract 70.0, potential 1.0323; Acidulated: extract 64.9,
  potential 1.0300. `tests/test_malts.py` 9 passed; suite 23 passed.
- `malt-loader` Task 5 ([`docs/finished/malt-loader/`](docs/finished/malt-loader/plan.md)): added
  `build`, `load` and the CLI to `loaders/malts.py` (an SKU in neither `PRODUCTS` nor `SKIPPED`
  raises) and loaded the hopline malts: 74 `ref.fermentable` rows (Weyermann 37, Viking Malt 32,
  Simpsons Malt 5), 8 hopline products skipped. Sources: `weyermann-2026` 37, `viking-malt-2023`
  31, `simpsons-malt-2025` 5, `hopline-malts` 1 (Sprau Malt). Measured: 73 with EBC (Viking
  Enzyme Malt has none), 70 with potential (`NULL`: Simpsons Crystal T50, DRC, Crystal Extra
  Dark by user decision, and Weyermann Acidulated Malt, which has no extract in either source),
  62 with `max_pct` (from Weyermann 36, Viking 8, Simpsons 1, hopline 17; 12 Viking malts have
  none). Maris Otter row as tested: EBC 4.4–6.6, extract 79.0, potential 1.0365, max 100.
  Weyermann Carapils and Carahell take the main recommendation as `max_pct` (10, 15; user
  decision), with the full printed sentence kept in `raw`. Ran twice, same counts both times.
  `tests/test_malts.py` 8 passed; suite 22 passed.
- `malt-loader` Task 4 ([`docs/finished/malt-loader/`](docs/finished/malt-loader/plan.md)): built
  `shared/rag-files/pending/malt_catalogue.json` by hand from the Weyermann (Crop 2026), Viking
  (2023) and Simpsons (Nov 2025) PDFs: 72 entries (Weyermann 37, Viking 30, Simpsons 5), each
  with its page, re-checked against the page text (not committed). Added `loaders/malt_products.py`:
  all 82 hopline SKUs decided — 74 mapped (Weyermann 37, Viking 32, Simpsons 5; Sprau Malt has
  no catalogue entry), 8 skipped (BestMalz, Sladovna, malt extracts), and
  `IGNORE_HOPLINE_EXTRACT` for the three Simpsons crystals. Checked: every SKU in
  `hopline_malts.json` is mapped or skipped, every mapped product is in the catalogue exactly
  once. `tests/test_malts.py` 7 passed; suite 21 passed. Not loaded yet (Task 5).
- `malt-loader` Task 3 ([`docs/finished/malt-loader/`](docs/finished/malt-loader/plan.md)): added
  `loaders/malts.py` with the pure part of the loader: `potential_sg` (extract % → SG via
  ppg = extract/100 × 46.214), `max_pct_from_text`, `parse_hopline_spec` and `merge` (catalogue
  wins, hopline fills gaps, `field_source` per field, both records in `raw`). `merge` can ignore
  hopline's extract: the user decided the flat "min 70%" hopline lists for Simpsons Crystal T50,
  DRC and Crystal Extra Dark is not used, so their extract and potential stay `NULL`.
  `tests/test_malts.py` 6 passed; suite 20 passed. Not loaded yet (Tasks 4–5).
- `malt-loader` Task 2 ([`docs/finished/malt-loader/`](docs/finished/malt-loader/plan.md)):
  `db/010_ref_schema.sql` adds `ref.fermentable.field_source jsonb not null` (per-field source,
  as on `ref.hop`) and describes `max_pct` as the stated maximum share of the grist;
  `db/011_ref_sources.sql` adds `hopline-malts`, `weyermann-2026`, `viking-malt-2023` and
  `simpsons-malt-2025`, and deletes the unused `weyermann-specs` and `viking-malt-2020` rows while
  no ingredient references them. Applied both twice as `postgres`, no errors; measured each time:
  10 `ref.source` rows, `field_source` present and `not null`. Suite 14 passed.
- `malt-loader` Task 1 ([`docs/finished/malt-loader/`](docs/finished/malt-loader/plan.md)): added
  `loaders/fetch_hopline.py` (standard library only; `listing_links`, `product_page`, CLI
  `python -m loaders.fetch_hopline OUT.json`, one request per second, never `/shop_ajax/`).
  Ran it: 5 listing pages, 82 products in `shared/rag-files/pending/hopline_malts.json`
  (fetched 2026-10-09, not committed), every name set, spec text set for all 74 malts to be
  mapped (only the 4 liquid extracts, which are skipped, have none). 2 new tests; suite 14 passed.
- Planned `malt-loader` ([`docs/finished/malt-loader/plan.md`](docs/finished/malt-loader/plan.md)),
  re-scoped from `malts.json`: load only the grain malts hopline.hu sells from Weyermann (37),
  Viking Malt (32) and Simpsons (5); Sladovna, BestMalz and malt extracts left out. Figures come
  from the maltster catalogues (Weyermann Crop 2026, Viking 2023, Simpsons Nov 2025), hopline fills
  only what a catalogue lacks, and a new `ref.fermentable.field_source` records the source of each
  field. `max_pct` is now filled from the stated maximum usage (was "NULL until P3"). Nothing built yet.
- Shipped `style-loader` ([`docs/finished/style-loader/`](docs/finished/style-loader/verification.md)),
  merged to `main`: `loaders/styles.py` parses BJCP 2021 and BA 2026 styles and upserts them on
  `(guide, edition, code)`; `ref.beer_style` has 285 rows (BJCP 116, 96 with vitals; BA 169,
  144 with OG, 12 with open-ended SRM), all sourced, whole record in `raw`. Verification: all
  10 checks pass; re-run before the merge: `pytest` 12 passed. Source JSON files stay untracked.
- `style-loader` Task 2 ([`docs/finished/style-loader/`](docs/finished/style-loader/plan.md)): added
  `load` (upsert on `(guide, edition, code)`, `source_id` from `bjcp-2021` / `ba-2026`) and the
  CLI `python -m loaders.styles --bjcp PATH --ba PATH`. The re-added `styles.json` and
  `ba_styles.json` have the field names Task 1 assumed. Ran it twice: both times
  `ref.beer_style` has BA 169 rows (144 with OG) and BJCP 116 (96 with OG), 285 in all;
  15B is `[1.036,1.044]|[25,45]|[25,40]`; 12 BA rows have an open-ended SRM. Suite 12 passed.
- `style-loader` Task 1 ([`docs/finished/style-loader/`](docs/finished/style-loader/plan.md)): added
  `loaders/styles.py` with `Style`, `parse_bjcp` (BJCP 2021, code = style number) and `parse_ba`
  (BA 2026, code = number slug); vitals become `numrange`s through `to_range`, blank text and
  missing vitals stay `None`, `raw` keeps the whole input row. Tested on inline fixtures only
  (the source files are not in the repo yet): `tests/test_styles.py` 4 passed; suite 12 passed.
  Nothing loaded into the DB yet.
- Shipped `ref-schema` ([`docs/finished/ref-schema/`](docs/finished/ref-schema/verification.md)),
  merged to `main`: `ref` schema with 7 tables owned by `postgres` (`db/010_ref_schema.sql`),
  8 `ref.source` rows (`db/011_ref_sources.sql`), and the `loaders/` package with shared helpers
  (`loaders/common.py`) and DB helpers (`loaders/db.py`). Verification: all 11 checks pass;
  re-run before the merge: `pytest` 8 passed. The P1a loaders can now start.
- `ref-schema` review fixes ([`docs/finished/ref-schema/`](docs/finished/ref-schema/plan.md)):
  `beer_style.guide`, `beer_style.code` and `ingredient.kind` are `NOT NULL` (natural keys);
  `hop`, `yeast` and `water_salt` cascade on ingredient delete like `fermentable`;
  `water-chemistry` edition is `IUPAC standard atomic weights 2021`. `010`/`011` gained
  `ALTER`/`UPDATE` statements so they update the existing tables. Measured on the live DB after
  applying twice: the 3 columns `NOT NULL`, all 4 detail FKs `on delete cascade`, 7|7 tables
  owned by `postgres`, 8 sources; a NULL `kind`/`code` insert is rejected and deleting an
  ingredient removes its hop row (rolled back). Suite: 8 passed.
- `ref-schema` Task 3 ([`docs/finished/ref-schema/`](docs/finished/ref-schema/plan.md)): added
  `loaders/db.py` with `connect()` (reads only the 4 connection variables from the root `.env`,
  connects as `postgres.<tenant>` through the pooler), `source_id()` and `upsert_ingredient()`
  (upsert on `(kind, producer_key, name_key)`). Measured: `source_id(c, 'bjcp-2021')` → `1`,
  `source_id(c, 'nope')` → `LookupError`; upserting the same hop twice in one transaction gave
  one row holding the second `raw` (rolled back, `ref.ingredient` still 0 rows). Suite: 8 passed.
- `ref-schema` Task 2 ([`docs/finished/ref-schema/`](docs/finished/ref-schema/plan.md)): added
  `db/010_ref_schema.sql` (`ref` schema with `source`, `beer_style`, `ingredient`, `fermentable`,
  `hop`, `yeast`, `water_salt`) and `db/011_ref_sources.sql` (8 source slugs), applied as
  `postgres`. Measured: 7 of 7 `ref` tables owned by `postgres`, 8 `ref.source` rows; applying
  both files again gave the same counts and no error. Licences other than `GPL-3.0`
  (Brewtarget) and `unknown` (`hops-json`, `hopslist`) are left `NULL`, not checked yet.
- `ref-schema` Task 1 ([`docs/finished/ref-schema/`](docs/finished/ref-schema/plan.md)): added the
  `loaders/` package with the shared helpers in `loaders/common.py` (`num`, `to_range`, `f_to_c`,
  `name_key`, `read_beerjson`), `requirements.txt` (`psycopg[binary]`, `pytest`) and `pytest.ini`.
  `pytest` 9.1.1 installed in `.venv`; `tests/test_common.py` → 8 passed. No DB yet.
- Shipped work now moves from `docs/work/<slug>/` to `docs/finished/<slug>/`: `dev-ship` does it
  as its last step on `main`, after a green verification, the merge and the push, and fixes the
  links into the folder. `docs/work/` holds only work in progress. `recover-stack` moved first.
- `dev-flow` now says in chat which skill it calls (`Called: /dev-plan`) or skips and why,
  runs all six skills unless one is already done, asked to be skipped or has nothing to act on,
  copies the verification tables unchanged, and ends with a flow summary table (each skill:
  called or not, result in a few words). Asked for after `recover-stack`, where the skipped brief
  and the reformatted test tables were not visible enough.
- Shipped `recover-stack` ([`docs/finished/recover-stack/`](docs/finished/recover-stack/verification.md)),
  merged to `main`: compose and Supabase mount files back in the repo (without `db-init`), and
  `supabase-db`, `-kong` and `-pooler` running again (D6). Re-checked before the merge: `select 1`
  → 1, `/rest/v1/` → 401, 0 containers `Restarting`, `docker compose config -q` exit 0, and
  `compose ps` lists the three. First piece of work delivered through `dev-flow`.
- `recover-stack` review fix ([`docs/finished/recover-stack/`](docs/finished/recover-stack/review.md)):
  corrected the docs that said all containers run. `searxng` has been `Exited (127)` since
  2026-10-08 18:48 UTC with the same deleted-bind-mount trap (`searxng/settings.yml` is now a
  root-owned directory; the file is in the archive tag). Updated OPERATIONS.md §1 and the §3
  trap entry, and the §4 SearXNG row. Recovering `searxng` is separate follow-up work, not
  started; nothing was changed on the container.
- `recover-stack` Task 2 ([`docs/finished/recover-stack/`](docs/finished/recover-stack/plan.md)):
  `docker start` brought `supabase-db`, `-kong` and `-pooler` back (all healthy). Checked:
  `select 1` as `postgres` → 1, `/rest/v1/` through Kong → 401, `docker compose ps` lists the
  three. `supabase-edge-functions` was also crash-looping (its `functions/main/index.ts` had been
  removed in the reset); restored it from the archive and restarted it, after which 0 containers
  are `Restarting`. D6 decided: restore the compose and Kong files (done), without `db-init`.
  OPERATIONS.md §1 and CLAUDE.md updated; new trap entry for deleted bind-mount files.
- `recover-stack` Task 1 ([`docs/finished/recover-stack/`](docs/finished/recover-stack/plan.md)): restored
  `docker-compose.yml` (with the `db-init` service removed), `supabase/docker/docker-compose.yml`
  and the 10 bind-mounted DB/Kong/pooler files from the archive tag, after the user removed the
  root-owned placeholder directories and took ownership of `volumes/api` and `volumes/pooler`.
  `docker compose config -q` exits 0. Containers not restarted yet (Task 2).
- Added design principle §6.8 *Readable over optimal*: understandability wins over
  optimisation, after the first build's config-table-driven n8n workflows proved hard to follow.
  CLAUDE.md points to it, and `dev-review` now checks for it.
- Split the P1a plan into 8 dev-flow work items, each with its own `docs/work/<slug>/plan.md`
  (`Stage: draft`, awaiting approval) and branch: `recover-stack`, `ref-schema`, `style-loader`,
  `malt-loader`, `hop-loader`, `yeast-loader`, `water-salts`, `ref-spotcheck`. The index (order,
  source files, global constraints, review focus) is
  [`docs/FILL-REF-README.md`](docs/FILL-REF-README.md) (moved there 2026-10-11), and the original plan was
  removed. Changes found while curating: `recover-stack` uses `docker start` on the existing
  containers (no recreate, so the Kong rule holds); `read_beerjson` moved to the shared helpers so
  the yeast loader doesn't depend on the hop loader; the hop source precedence is a question at
  plan approval; `pytest` is not installed yet (checked).
- Added the delivery-workflow skills: `dev-flow` orchestrates `dev-brief` → `dev-plan` →
  `dev-implement` (one subagent per task) → `dev-review` → `dev-verify` → `dev-ship`, with user
  approval gates on the brief, the plan and shipping. Each piece of work gets
  `docs/work/<slug>/` and branch `<slug>`; one-line commits, `--no-ff` merge to `main`. Not yet
  run on real work.
- Wrote the P1a plan (now split, see above; original at `b84e914:docs/superpowers/plans/2026-10-09-fill-ref.md`):
  recover the stack (D6), then load `ref` (styles, malts, hops, yeasts, water salts) with tested
  Python loaders, plus the order of the phases after it. Found while planning: the Supabase DB,
  Kong and pooler have been down since 2026-10-08 ~20:48, because their bind-mounted files
  (removed in the reset) became empty root-owned directories on restart; all of them are in the
  archive tag. Measured source shapes from the 2026-10-08 copies (counts in the plan). Nothing
  built yet.

### 2026-10-08
- Measured the archived Brewer's Friend corpus (read from the dump, nothing restored): 35,620
  recipes (views > 500 of 179,455), 34,052 mapped to a BJCP 2021 style; 84 of 116 styles have
  ≥ 50 recipes, 19 have 20–49, 9 have 1–19, 4 have none (28D, 29D, 30D, 34A). Junk left: 0
  non-Latin names, 219 OG outside 1.020–1.150, 90 ABV-inconsistent, 3,287 (9 %) grist % not
  summing to 100 ± 2. Wrote [`docs/STYLE-PROFILES.md`](docs/STYLE-PROFILES.md) (quality gates
  instead of hand curation, robust statistics, family shrinkage for thin styles, weighted extra
  sources) and [`docs/STYLE-FIT.md`](docs/STYLE-FIT.md) (deterministic 5-level algorithm with
  automatic ingredient tagging, so new ingredients need no rules). Updated the roadmap,
  `DATABASE.md` (`sensory_dimension`, `source_weight`, gate flags) and D7.
- Agreed the recipe-creation approach after reviewing the roadmap point by point: brief before
  style; style as guidance (best-fit style always picked, user overrides accepted and listed);
  yeast → fermentables → hops → extras; added brewer profile, water, mash + boil, fermentation,
  packaging and a validate loop (16 steps in 6 stages, §3); new principle 7 *compute first*
  (§6). Rewrote [`docs/RECIPE-ROADMAP.md`](docs/RECIPE-ROADMAP.md): style rules organised as
  sensory envelope + ingredient tags + usage effects + dose (worked "Citra in a stout" example
  from BJCP 15B/20B text), a doc → calculation table, and web research on free ratio sources
  (Brewer's Friend CC0 corpus, Beer Analytics, DIY Dog, AHA, Oregon Brew Crew, BJCP study guide,
  Brewtarget yeast data). Wrote [`docs/DATABASE.md`](docs/DATABASE.md): `ref` / `corpus` / `kb` /
  `app` schemas split by trust, ER diagrams, access rules, build order. Design only, nothing
  built. Updated D4, D7–D9 and corrected §5 (the BJCP and BA style JSONs are already in
  `pending/`).
- Wrote [`docs/RECIPE-ROADMAP.md`](docs/RECIPE-ROADMAP.md): a review of the proposed recipe-creation
  flow, an improved 10-step flow (brief → style → conflict check → targets → blueprint → pick →
  calculate → validate → process → write), a 5-level style-rule scale, a hint→knob table, a
  database split by trust (`ref` / `kb` / `corpus` / `app`) and a phased roadmap (P0–P9). It is a
  **proposal**: §3 is unchanged until the user approves it. Added D7–D9.
- Added a scope rule to `CLAUDE.md`: implement only what is asked, no unrequested suggestions or
  follow-up fixes, so sessions can close.
- Hardened the Claude Code setup (audit found the project-specific setup lived outside git):
  committed `.mcp.json` with the Supabase MCP **read-only** on purpose (`~/.mcp.json`, which leaked
  into every project under `~`, moved to `~/.mcp.json.bak`); added `.claude/settings.json` with a
  PreToolUse guard hook (blocks volume deletion, writes to the Postgres data dir, printing `.env`;
  20/20 pipe-test cases pass and it fired live) and the `n8n-skills` plugin at project scope
  (disabled at user scope, as is the unused `supabase` plugin); cleared stale allow rules from
  `settings.local.json`. Moved operational lessons from personal memory into
  [`docs/OPERATIONS.md`](docs/OPERATIONS.md) and expanded `CLAUDE.md` (no worktrees, plans in
  `docs/`, DB-change path). Removed 3 stale worktrees, 8 local branches (all contained in the
  archive tag; remote branches untouched) and junk files. Logged D6.
- Installed two evaluation guides from `Goodnight77/rag-skills` (commit `d403637`, MIT) as
  project skills in `.claude/skills/`: `retrieval-evaluation-metrics` and
  `rag-evaluation-frameworks`. The rest of that plugin was reviewed and not adopted: it is safe
  (no hooks, MCP servers or install scripts) but generic, Qdrant-centred, and pushes complexity
  against §6.5. The `allowed-tools: Bash` grant was removed from the imported frontmatter.
- Created this `PROJECT.md` as the single source of truth for the project, with a standing
  rule in `CLAUDE.md` to update it after every implementation.
- Project reset. All tracked files were removed (archived under tag
  `archive/pre-reset-2026-10-08`), and the Supabase and n8n databases were dumped to
  `~/homebrew-archive-2026-10-08/` and wiped. Reasons: the database had become too complicated
  and messy, ingredient tracking needed a rethink, and style selection needed improvement.

---

## 9. History — the first build (before 2026-10-08)

The first attempt went as far as an ingested corpus of about 2.7k chunks from 11 sources, 285
style records, a chat agent with citations, and a recipe pipeline that passed 7 of 9 test
briefs. Its main lessons are kept in §6. The full design docs (`homebrew_assistant_architecture.md`,
`docs/RECIPE-PIPELINE-V2.md`, `plans/`) can be read with:

```bash
git show archive/pre-reset-2026-10-08:<path>
```

Reuse what still applies from there; do not restore wholesale.

---

## 10. Keeping this file current

- **After anything is implemented**, update the status columns (§4, §5), tick or adjust goals,
  and add a dated entry to §8.
- **When a decision is made**, move it from §7 into the relevant section with a one-line *why*,
  and log it in §8.
- **When the approach changes** (§2, §3, §6), edit the text in place so the file always
  describes the current plan, and log what changed and why. Old thinking belongs in git
  history, not here.
- Keep it readable in one sitting. Detailed designs go in separate docs linked from here.
