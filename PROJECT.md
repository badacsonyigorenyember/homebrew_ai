# AI Homebrew Assistant — Project Description

> **This file is the single source of truth for the project:** why it exists, what it
> is trying to do, how it is built, and how far along it is. If code and this file
> disagree, one of them is wrong. Fix it, and record the fix in the [Progress log](#8-progress-log).
>
> Last updated: **2026-10-16**

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

Agreed 2026-10-08; ingredient choice and ratios revised 2026-10-14 (D7). Full design, diagrams and worked examples:
[`docs/RECIPE-ROADMAP.md`](docs/RECIPE-ROADMAP.md). Database: [`docs/DATABASE.md`](docs/DATABASE.md).
Build order in n8n, with checkpoints and brief checks (proposal, 2026-10-12):
[`docs/WORKFLOW-ROADMAP.md`](docs/WORKFLOW-ROADMAP.md).

The approach is **proportions first, quantities last**, and **compute first**: the LLM reads the
request (step 1), picks the ingredients and proposes their percentages and hop-schedule intent
(steps 6–9), and writes the recipe sheet (step 16). Every number is SQL or deterministic code:
targets, scaling, OG/FG/ABV/IBU/SRM and the formulation-rule checks. A broken rule goes back to
the LLM with the rule, the value and the limit.

```
 A UNDERSTAND   0 brewer profile (stored) · 1 brief · 2 best-fit style · 3 deviation report
 B DESIGN       4 targets (style range + hint knobs + user's numbers) · 5 formulation rules (exact, checked by code)
 C CHOOSE       6 yeast · 7 fermentables · 8 hops · 9 extras   (LLM picks from the ingredient table, proposes % and hop-schedule intent)
 D COMPUTE      10 scale to OG/volume, size bittering for IBU, set colour; OG/FG/ABV/IBU/SRM · 11 check rules, violations back to the LLM, retry max 3×
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
- **Ratios and choices (was D7, decided 2026-10-14):** there is no ratio corpus. The LLM proposes
  ingredients, percentages and hop-schedule intent from a detailed ingredient table (what each
  ingredient is and does); code scales them, computes every number and checks a small set of
  exact, general formulation rules that name only ingredient roles, style numbers and
  ingredient-table fields, never an ingredient or a style
  ([`s2-formulation-rules`](docs/finished/s2-formulation-rules/brief.md)). *Why: no ratio corpus;
  LLM proposes, code scales and checks; revisit if test briefs show a need.* Rules: `select * from app.formulation_rules()`, [`db/031_formulation_rules.sql`](db/031_formulation_rules.sql).
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
| Database | **Supabase** (self-hosted Postgres 15) | Knowledge base, reference data (styles, ingredients), recipes | 🟢 running again since 2026-10-09 ([`recover-stack`](docs/finished/recover-stack/plan.md)). All schemas built 2026-10-11 ([`slim-ref`](docs/finished/slim-ref/plan.md)): `ref` 15 tables, `corpus` 7, `kb` 1, `app` 8, all 31 owned by `postgres` (`ref` has 19 tables since `s3-style-fit` (`style_ingredient`, `ingredient_review`), 35 in all, measured 2026-10-15, all owned by `postgres`; the 64 `app` functions, including those in `db/033` and `db/034`, are owned by `postgres` too). Style-fit data measured 2026-10-15: `ref.tag` 69, `tag_synonym` 239, `ingredient_tag` 806 (fermentable 234, hop 343, yeast 229), `ingredient_review` 38, `sensory_dimension` 18, `style_sensory` 189, `style_character` 237, `style_ingredient` 116, `style_rule` 0; design in [`docs/DATABASE.md`](docs/DATABASE.md). **P1a `ref` load done.** Measured 2026-10-11: `ref.source` 18 rows (20 on 2026-10-15); `ref.beer_style` 285, BJCP 2021 116 + BA 2026 169 ([`style-loader`](docs/finished/style-loader/plan.md)); `ref.ingredient` 298, 0 without a source: `ref.fermentable` 81 = 74 grain malts from Weyermann, Viking and Simpsons ([`malt-loader`](docs/finished/malt-loader/plan.md)) + 7 adjuncts (flaked oats, corn, rice and barley, brown candi sugar and lactose from `hopline-adjuncts`, honey from `palmer-how-to-brew`; extract from Palmer Tables 18.5/24.1), `fermentability` `normal` 78 · `full` 2 (candi, honey) · `none` 1 (lactose) ([`adjunct-fermentables`](docs/finished/adjunct-fermentables/plan.md)); `ref.hop` 90, all from `hopline-hops`, 8 values from Beer Maverick ([`hop-loader`](docs/finished/hop-loader/plan.md)); `ref.yeast` 119 from `hopline-yeasts`, 93 with attenuation from the makers' sources, Brewfather and the user ([`yeast-loader`](docs/finished/yeast-loader/plan.md)); `ref.water_salt` 8, ion mg/L per g computed from IUPAC atomic masses ([`water-salts`](docs/finished/water-salts/plan.md)). Fermentables, hops and yeasts name each filled field's source in `field_source`. Every other table is empty until its phase. **Maths library (`s1-maths`, 2026-10-14):** 19 `app.*` functions in [`db/030_maths.sql`](db/030_maths.sql) (gravity, FG, ABV, °Plato, Tinseth IBU, Morey colour, volumes, grist and hop solvers), all owned by `postgres`, `app.calc_version()` = `maths-1`; checked through n8n's Postgres node once ([plan](docs/finished/s1-maths/plan.md)). 10 random rows per loaded table spot-checked by the user against the sources, no errors ([`ref-spotcheck`](docs/finished/ref-spotcheck/plan.md), pack `db/checks/ref_spotcheck.sql`); the 7 adjuncts came after it and were checked in their own verification (16/16). **Formulation data and check (`s2-formulation-rules`, 2026-10-15):** `ref.fermentable` 81/81 with `role`, `max_pct` (18 by user decision E, 63 untouched), `min_boil_min` (7 at 90) and `description`, 51 with `enzyme_activity`; `ref.fermentable_substitute` 27 pairs; `ref.fermentable_style` 623 rows; loaded by `python -m loaders.fermentable_facts` (after `loaders.malts` and `loaders.adjuncts`). Rules in [`db/031_formulation_rules.sql`](db/031_formulation_rules.sql) (`select * from app.formulation_rules()`, 15 rows: 13 rules, 12 checked), check `app.check_recipe` in [`db/032_formulation_check.sql`](db/032_formulation_check.sql); 22 reviewed reference recipes in `tests/fixtures/reference_recipes.toml` all pass. **Known gaps:** no malt extracts, and the other hopline adjuncts (rye, wheat and chit flakes, white candi, fructose) are not loaded; `beer_style.co2_vol` was dropped (no source has it; back in P6). *Why this schema (was D4): each typed column is read by a pipeline step and everything else stays in `raw`; behaviour (usage effects, hint knobs, cut points, source weights) lives in code; all tables were created up front, empty, by user decision.* |
| Vector search | **pgvector** (HNSW) + Postgres full-text, fused (hybrid RAG) | Retrieval over book chunks | 🟢 `vector` 0.8.0 installed in schema `extensions`; `kb.chunk` created with HNSW + GIN indexes (2026-10-11, [`slim-ref`](docs/finished/slim-ref/plan.md), shipped); `app.kb_search` (`db/040_kb_search.sql`) fuses both by reciprocal rank; `kb.chunk` holds 943 *How to Brew*, 357 *Water*, 454 *Yeast*, 341 *Malt* and 85 BJCP study guide chunks, 2,180 in all (measured 2026-10-16, [`s4-books-kb`](docs/finished/s4-books-kb/plan.md)), plus 258 chunks from 12 articles (205 Markdown, 53 PDF; each source has its `source_url`, which `app.kb_search` returns; [`s7-kb-articles`](docs/finished/s7-kb-articles/plan.md)); retrieval evaluated: recall@5 0.422, MRR@10 0.354 on 45 questions, bar 0.40 met (`evals/results/2026-10-16-s4.json`); with articles (s7, 60 questions): books 0.422 / 0.345, bar met, articles 0.867 / 0.608 (`evals/results/2026-10-16-s7.json`) |
| Orchestration | **n8n** (with its own Postgres for metadata) | Ingestion and recipe pipelines, agent | 🟢 running, 4 workflows published (measured 2026-10-13): `Recipe pipeline` (webhook `POST /webhook/recipe-pipeline`, logs steps 1 and 2 to `app.run` / `app.run_step`; optional body fields `guide`, `temperature` and `seed`; the last two reach step 1, defaults 0 and 42), `Step 1 · read request` (one Ollama call with the contract as `format`, SQL check `app.step1_read_answer`, one retry; [`m1-read-request`](docs/finished/m1-read-request/plan.md)) `Step 2 · best-fit style` (contract checks around one SQL call, `app.step2_best_style`; [`m2-best-fit-style`](docs/finished/m2-best-fit-style/plan.md)) and `Check contract` (pg_jsonschema check); exported to `n8n/workflows/` ([`m0-harness`](docs/finished/m0-harness/plan.md)) |
| Document parsing | **Docling Serve** (ROCm) | PDF → structured Markdown + `HybridChunker` | 🟢 running |
| LLM runtime | **Ollama** (ROCm) | Local chat and embedding models | 🟢 running |
| Chat model | `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K` (Q6_K), thinking off *(D2, decided 2026-10-13)* | Reasoning, extraction, recipe drafting | 🟢 step 1 default in `Recipe pipeline`; 19/20 briefs right in all 3 runs, 12.5 s median, 36%/64% CPU/GPU (measured, [`benchmark.md`](docs/finished/m1-read-request/benchmark.md)). Why: quality first, and only this model met the bar; thinking on scored the same at about 8x the time and added a b08 `wanted` miss. Other pulled models: see OPERATIONS §6 |
| Embedding model | `bge-m3` (1024-dim) | Chunk and query embeddings | 🟢 pulled |
| Web search | **SearXNG** + `webarm` service | Lookups for what the books do not cover | 🔴 `searxng` down since 2026-10-08 (`settings.yml` lost in the reset, [`OPERATIONS.md`](docs/OPERATIONS.md) §1); recovery has an approved brief on branch `recover-searxng` (2026-10-09), not planned or merged. `webarm` running. Optional |
| Scripts | Python (`.venv`), `psycopg` 3, `pytest` (`requirements.txt`) | One-off extract/load jobs, evals | 🟡 `loaders/` package; `pytest` gives 571 passed with the stack up (168 s, measured 2026-10-16) and 171 passed, 364 deselected with `-m "not stack"` (measured 2026-10-15; `tests/test_maths.py` is 79 of them, all stack tests; stack tests are skipped when Postgres or n8n is down). Shared helpers `loaders/common.py` (8 tests) and DB helpers `loaders/db.py` (`connect`, `source_id`, `upsert_ingredient`) ([`ref-schema`](docs/finished/ref-schema/plan.md)); hopline fetcher `loaders/fetch_hopline.py` (`python -m loaders.fetch_hopline OUT.json` for malts, `--hops`, `--yeasts`, `--adjuncts`; 7 tests). Loaders, each with an explicit SKU map where it reads hopline: styles `loaders/styles.py` (`python -m loaders.styles --bjcp PATH --ba PATH`, 4 tests, [`style-loader`](docs/finished/style-loader/plan.md)); malts `loaders/malts.py` + `loaders/malt_products.py` (`python -m loaders.malts --hopline PATH --catalogue PATH`, 9 tests, [`malt-loader`](docs/finished/malt-loader/plan.md)); hops `loaders/hops.py` + `loaders/hop_products.py` (`python -m loaders.hops --hopline PATH --report PATH`, Beer Maverick fill `BEERMAVERICK`, 9 tests, [`hop-loader`](docs/finished/hop-loader/plan.md)); yeasts `loaders/yeasts.py` + `loaders/yeast_products.py` (`python -m loaders.yeasts --hopline PATH --report PATH`, attenuation in `ATTENUATION`, 12 tests, [`yeast-loader`](docs/finished/yeast-loader/plan.md)); water salts `loaders/water_salts.py` (`python -m loaders.water_salts`, 3 tests, [`water-salts`](docs/finished/water-salts/plan.md)); adjuncts `loaders/adjuncts.py` + `loaders/adjunct_products.py` (`python -m loaders.adjuncts --hopline PATH`, Palmer rows as printed, PPG → extract % as PPG / 46 × 100, 6 tests, [`adjunct-fermentables`](docs/finished/adjunct-fermentables/plan.md)). fermentable facts `loaders/fermentable_facts.py` + `.toml` (`python -m loaders.fermentable_facts`, runs after malts and adjuncts; `tests/test_fermentable_facts.py` 22, `tests/test_formulation_rules.py` 4, `tests/test_formulation_check.py` 37, `tests/test_reference_recipes.py` 26, [`s2-formulation-rules`](docs/finished/s2-formulation-rules/plan.md)). style-fit tags `loaders/tags.py` (`python -m loaders.tags`, vocabulary in `loaders/style_fit_vocab.toml`; runs after the ingredient loaders and `loaders.fermentable_facts`) and style envelopes `loaders/style_envelopes.py` (`python -m loaders.style_envelopes` loads the reviewed `loaders/style_envelopes.toml`; runs after `loaders.tags`; `--extract` asks the D2 model offline and is not part of the pipeline), [`s3-style-fit`](docs/finished/s3-style-fit/plan.md). books `loaders/books.py` (`python -m loaders.books <slug>`, one book at a time into `kb.chunk`; `tests/test_books.py`, `tests/test_kb_search.py` for `app.kb_search`, [`s4-books-kb`](docs/finished/s4-books-kb/plan.md)). Every loader gives the same rows when run twice. Read-only check pack `db/checks/ref_spotcheck.sql`; eval harness `evals/` (`grade.py` graders, `run.py` runner, `workflows.py` export; `python -m evals.run`, G0 baseline in `evals/results/2026-10-12-m0.json`, [`m0-harness`](docs/finished/m0-harness/plan.md)); retrieval eval `evals/retrieval.py` (`python -m evals.retrieval`; `tests/test_retrieval_eval.py`); recipe test briefs `evals/recipe_briefs.toml` (22 briefs, P0) checked by `tests/test_recipe_briefs.py` (10 tests, [`test-briefs`](docs/finished/test-briefs/plan.md)) |
| Dev tooling | Claude Code: Supabase MCP (read-only, `.mcp.json`), official n8n MCP (local scope) + `n8n-skills` plugin, guard hook (`.claude/hooks/guard.sh`), `find-docs` skill + `.claude/rules/context7.md` (current library docs through the `ctx7` CLI), `database-schema-designer` skill (`.agents/skills/`, `skills-lock.json`) | Building and inspecting the stack; schema changes go through SQL files applied as `postgres` | 🟢 |
| Delivery workflow | Project skills `dev-flow` (orchestrator) + `dev-brief`, `dev-plan`, `dev-implement`, `dev-review`, `dev-verify`, `dev-ship` (`.claude/skills/`) | Brief → plan → build → review → verify → merge, one subagent per step, work in `docs/work/<slug>/` | 🟢 in use; 12 items shipped 2026-10-09 → 2026-10-11, each recorded in `docs/finished/<slug>/`; `m1-read-request` shipped 2026-10-13 ([`docs/finished/m1-read-request/`](docs/finished/m1-read-request/)) |
| Eval guidance | Project skills `retrieval-evaluation-metrics`, `rag-evaluation-frameworks` (`.claude/skills/`) | Reference for building the retrieval test set and regression gate (§6.6) | 🟢 installed; used for the s4 retrieval eval (`evals/retrieval.py`, recall@5 and MRR@10); s7 run with articles 2026-10-16: books 0.422 / 0.345 (bar 0.40 met), articles 0.867 / 0.608 (no bar), [BOOKS.md](docs/BOOKS.md) §1d |

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

Not ingested since the reset. On 2026-10-08 the source files were removed on purpose, to be re-added as each loader needs them. Since 2026-10-16 they sit in topic folders under `shared/rag-files/` (git-ignored, every loader takes its paths as arguments): `books/` (*How to Brew*, *Water*, *Yeast*, *Malt*, the BJCP exam study guide, `obc_recipe_formulation.pdf`), `styles/` (`styles.json`, `ba_styles.json`, the BJCP 2021 introductions, two BJCP 2008 style aids), `hopline/` (`hopline_malts.json`, `hopline_hops.json` fetched and loaded 2026-10-10, `hopline_yeasts.json` and `hopline_adjuncts.json` fetched and loaded 2026-10-11), `maltsters/` (`malt_catalogue.json`, the Weyermann, Viking Malt and Simpsons catalogue PDFs, the PrimeTime substitution chart), `water/` (Bru'n Water's *Water Knowledge* and spreadsheet), `sensory/` (BJCP fault list and *Beer Characteristics*, YCH sensory ballots, flavour wheel, Cicerone syllabus), `articles/` (Troester, Terrill, Janish, Milk The Funk) and `recipes/` (`recipes_full.txt`, not used). The unused `malts.json` was deleted 2026-10-16. **Every file, its fate (kb, calc, check, oracle, later, copy) and the work item that uses it: [`docs/SOURCES.md`](docs/SOURCES.md)** (decided 2026-10-16).

| Source | Type | Feeds | Status |
|---|---|---|---|
| *How to Brew* — John Palmer | PDF book | General process, ingredients, maths | 🟡 doc→calc done for gravity, FG, ABV (table 9.1, via the Balling form), °Plato, IBU (Tinseth, table 5.5), colour and volumes, written up in [`doc-calc.md`](docs/finished/s1-maths/doc-calc.md) and tested in `tests/test_maths.py` ([`s1-maths`](docs/finished/s1-maths/plan.md)). Table 18.5 (4 flake rows) and Table 24.1 (3 sugar rows) loaded into `ref.fermentable` ([`adjunct-fermentables`](docs/finished/adjunct-fermentables/plan.md)). Water, mash and the other chapters not done. Prose in `kb.chunk`: 943 chunks, tables cut, pages 1–26 and 579–612 skipped (2026-10-16); the pages where tables and formulas were cut, and which pass covers them, are in [`docs/BOOKS.md`](docs/BOOKS.md) §3 |
| *Water* — Palmer & Kaminski (`books/palmer_kaminski_water.pdf`) | PDF book | Water chemistry | 🟡 prose in `kb.chunk`: 357 chunks, tables cut, pages 1–18 and 238–273 skipped (2026-10-16, [`docs/BOOKS.md`](docs/BOOKS.md) §3); calc not passed yet (m7-process) |
| *Yeast* — White & Zainasheff (`books/white_zainasheff_yeast.pdf`) | PDF book | Yeast and fermentation | 🟡 prose in `kb.chunk`: 454 chunks, tables cut, pages 1–21 and 305–325 skipped (2026-10-16, [`docs/BOOKS.md`](docs/BOOKS.md) §3); calc not passed yet (m7-process) |
| *Malt* — Mallett (`books/mallett_malt.pdf`) | PDF book | Malt, malting and malt chemistry | 🟡 prose in `kb.chunk`: 341 chunks, tables cut, pages 1–16 and 263–335 skipped (2026-10-16, [`docs/BOOKS.md`](docs/BOOKS.md) §3); no calc pass (malt data comes from the maltster catalogues) |
| *BJCP Beer Exam Study Guide* (`books/bjcp_exam_study_guide_2017.pdf`) | PDF | Ingredients and brewing process (section IV only) | 🟡 prose in `kb.chunk`: 85 chunks, tables cut, pages 1–45 skipped (2026-10-16, [`docs/BOOKS.md`](docs/BOOKS.md) §3); the §IV.B water table goes to m7-process |
| *Malt* — Mallett (`books/mallett_malt.pdf`) | PDF book | Malt background for the recipe sheet | ⬜ kb in s4-books-kb (no calc: malt data comes from the catalogues) |
| Web articles and short papers (`articles/`, `water/brunwater_water_knowledge.md`, `styles/bjcp_2021_introductions.md`; 12 sources) | Markdown / PDF, saved 2026-10-16 | Mash attenuation, dry hopping, souring, water, BJCP introductions | 🟡 kb done (s7-kb-articles, 2026-10-16: 258 chunks, 12 sources with URLs); calc still in s5-mash-attenuation and m7-process ([SOURCES.md](docs/SOURCES.md)) |
| BJCP 2008 style aids: Barnes flashcards, style comparison (`styles/`) | PDF | Check of the s3 envelopes; words for step 2 checks | ⬜ check only in s6-style-neighbours; never `ref` or `kb` (2008 numbers contradict 2021) |
| Sensory and serving references (`sensory/`: YCH ballots, flavour wheel, Cicerone CBS syllabus) | PDF | Vocabulary reference; Priority 2 | ⬜ later / check ([SOURCES.md](docs/SOURCES.md)) |
| Malt data: hopline.hu malt list (`hopline_malts.json`) + Weyermann (Crop 2026), Viking Malt (2023), Simpsons (Nov 2025) catalogues (`malt_catalogue.json`) | Structured (fetched pages + hand-built from the PDFs) | Fermentable catalogue, 74 malts | ✅ loaded into `ref.fermentable`: 74 rows (Weyermann 37, Viking 32, Simpsons 5), 73 with EBC, 74 with extract, 62 with `max_pct` (2026-10-09); roles, descriptions, enzyme activity and typical styles added 2026-10-15 (s2-formulation-rules); grain malts only, no sugars, adjuncts or extracts; 10 rows spot-checked against the source, no errors (2026-10-11, [`ref-spotcheck`](docs/finished/ref-spotcheck/plan.md)) |
| Adjunct data: hopline.hu flake, fermentable sugar and non-fermentable sugar lists (`hopline_adjuncts.json`, 14 products) | Structured (fetched page text) | Fermentable catalogue, 6 adjuncts | ✅ loaded into `ref.fermentable` (2026-10-11, [`adjunct-fermentables`](docs/finished/adjunct-fermentables/plan.md), shipped): flaked oats, corn, rice and barley, brown candi sugar, lactose (6 products, 1 pack size); the pages give only rice's max % (40), the candi's colour (225 EBC) and lactose's fermentability (`none`), the extract comes from Palmer; 7 products skipped with a reason (rye, wheat and chit flakes, white candi, fructose, rice hulls ×2); honey from Palmer only (hopline sells none); flake colours (0-3.2 / 1.576 / 1.97 EBC) from Simpsons and Briess, Honey and Lactose still without colour (2026-10-15, s3-style-fit); roles and descriptions added 2026-10-15 (s2-formulation-rules; Sprau Malt is `adjunct`) |
| Stout Style Guide | PDF | Stout styles and recipes | ⬜ |
| BYO pastry stouts | Markdown | Adjunct technique | ⬜ |
| Draught Beer Quality Manual 2019 | PDF | Serving and dispense | ⬜ |
| BJCP 2021 style guidelines (`styles.json`) | Structured | Styles, 116 rows | ✅ loaded into `ref.beer_style`: 116 rows, 96 with vitals (2026-10-09); 10 rows spot-checked against the source, no errors (2026-10-11, [`ref-spotcheck`](docs/finished/ref-spotcheck/plan.md)) |
| Brewers Association style guidelines (`ba_styles.json`) | Structured | Styles, 169 rows | ✅ loaded into `ref.beer_style`: 169 rows, 144 with OG (2026-10-09); 10 rows spot-checked against the source, no errors (2026-10-11, [`ref-spotcheck`](docs/finished/ref-spotcheck/plan.md)) |
| Hop data: hopline.hu hop list (`hopline_hops.json`, 106 products) | Structured (fetched pages) | Hop catalogue, 89 hops | ✅ loaded into `ref.hop`: 89 rows (5 LUPOMAX), purpose aroma 35 / bittering 4 / dual 50, 89 with alpha and total oil, 88 with origin (2026-10-15: Sterling removed by the user, `db/035_drop_sterling.sql`, excluded in the hop loader; was 90 rows, 2026-10-10); Delta, Lotus, Sterling alpha + oil, Mount Hood oil and Enigma purpose come from Beer Maverick (source `beermaverick`), loaded by the hop loader (2026-10-11); 10 rows spot-checked against the source, no errors (2026-10-11, [`ref-spotcheck`](docs/finished/ref-spotcheck/plan.md)); all 8 Beer Maverick values checked against beermaverick.com by the user, all match (2026-10-11) |
| Fault data: BJCP fault list 2012 (24) + study guide *Beer Characteristics* (25) (`sensory/`); `beer_faults.json` was lost in the reset | PDF / Markdown | Faults → causes (`ref.fault`, Priority 2) | ⬜ later |
| Brewer's Friend recipes (Kaggle, CC0) | Structured, 179,455 recipes | Not used: no ratio corpus (D7, decided 2026-10-14) | ⬜ set aside 2026-10-14; 35,620 (views > 500) in the archive dump, measured 2026-10-08 |
| Yeast data: hopline.hu dry and liquid yeast lists (`hopline_yeasts.json`, 129 products) | Structured (fetched pages) | Yeast catalogue, 119 yeasts | ✅ loaded into `ref.yeast`: 119 rows (dry 81, liquid 38; YeastFlow 38, Lallemand 18, Norse Nectar 17, Fermentis 13, Mangrove Jack's 13, Brewline 10, Gozdawa 9, YeasterBunny 1), 119 with temperature, 113 with flocculation, 114 with alcohol tolerance, 93 with attenuation (2026-10-11, [`yeast-loader`](docs/finished/yeast-loader/plan.md), shipped); no page states attenuation; it is copied as printed from the sources the user named: YeastFlow catalogue 34, Lallemand catalogue 17, Brewfather figures from the user 16 (Gozdawa 8, Brewline 8), Mangrove Jack's data sheets 13, Fermentis data sheets 12, user-supplied 1 (YF-666, printed "800-100", confirmed 80–100); 10 rows spot-checked against the source, no errors (2026-10-11, [`ref-spotcheck`](docs/finished/ref-spotcheck/plan.md)); none for Norse Nectar and YeasterBunny (user decision) and 8 strains with no figure in their source ([`report.md`](docs/finished/yeast-loader/report.md)). *Why hopline, not Brewtarget's BeerJSON (was D8): the user chose the shop's own yeasts, as for malts and hops (2026-10-11); the Brewtarget files are no longer needed* |
| AHA recipe-design crash course · Oregon Brew Crew recipe formulation · BJCP exam study guide | Free web / PDF | Design method, rules of thumb, output checklist | 🟡 OBC *Recipe Formulation* downloaded 2026-10-14 (`shared/rag-files/books/obc_recipe_formulation.pdf`); doc→calc done, OG and MCU of its Dubbel and Pils examples tested, its SRM and IBU (Daniels' tables) written up and not tested ([`doc-calc.md`](docs/finished/s1-maths/doc-calc.md)). BJCP study guide (Dec 2017, 2015 guidelines, `books/bjcp_exam_study_guide_2017.pdf`): §IV into kb in s4-books-kb, its 91 S0 style triples in s6-style-neighbours, its water table in m7-process ⬜; its web edition's *Beer Characteristics* and *Water* pages are kept as readable copies in `sensory/` and `water/` (2026-10-16). AHA ⬜ candidate, not downloaded |

**Style envelopes (was D9, decided 2026-10-15):** the D2 model extracts BJCP and BA guideline prose offline, and the user reviews every envelope before it enters `ref`; a BA field parser comes later, when all 169 BA styles are wanted. *Why: one path for 26 styles is less to build than a parser for 3, and nothing enters `ref` unreviewed.*

**Style guides (was D1, decided 2026-10-11, rule revised 2026-10-13):** both guides are scored
together and the best fit wins, with no head start for either. A BA style that is the same
beer as a BJCP style (the decided pair list, [`style-pairs.md`](docs/finished/m2-best-fit-style/style-pairs.md),
`app.style_pair()`) is returned as the BJCP style; a BA style paired only with a BJCP catch-all
keeps the BA style. Equal scores go BJCP first, then by code. BJCP only or BA only comes from
the webhook's `guide` field, or from the request text when the field is not sent; the field
wins. Within a guide, the best-fit style is the **base style** by default (adjuncts and extras
are ignored). When step 1 gives a wanted adjunct the role `feature`, the specialty code
is picked (e.g. 31B Alternative Sugar Beer for a honey-forward blonde), with the base style as
the alternative; a `background` adjunct leaves the base style ([`test-briefs`](docs/finished/test-briefs/brief.md) R3). Step 2 is built
(`app.step2_best_style`, [`m2-best-fit-style`](docs/finished/m2-best-fit-style/plan.md)). *Why: the
user's call (2026-10-13): the style is loose guidance that helps select resources, so the
closest style wins whichever guide it is in.*

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
   cheaper and testable. The LLM handles free text in and prose out, and the recipe choices:
   it picks ingredients and proposes percentages and hop-schedule intent. Code then scales,
   computes every number (gravity, IBU, colour, amounts) and checks the formulation rules; the
   LLM never computes a number. Every new source gets
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
| — | none open | | |

---

## 8. Progress log

Newest first. One entry per meaningful change: what was done, and why if that is not obvious.

### 2026-10-16
- s6-style-neighbours Task 4: wrote [`specialty-entry.md`](docs/work/s6-style-neighbours/specialty-entry.md), comparing the BJCP 2021 Specialty-Type introduction and entry instructions with D1. Verdict: the core rule agrees (base style by default, specialty style only for a recognizable feature, base style kept as the alternative); the gaps are coverage, not contradiction. Step 2 lists only honey and molasses (BJCP 31B) and honey (BA) where BJCP names seven ingredient families, it picks among several adjuncts alphabetically where BJCP takes the dominant one, and it has no filter keeping 28–34 out of the base pick (unmeasured). User decision: leave D1 and step 2 as they are, because the honey/molasses scope is deliberate and the runner's confusions can justify widening or filtering later. D1 and `db/` unchanged.
- s6-style-neighbours Task 3: wrote the runner `python -m evals.style_neighbours [--save]` ([`evals/style_neighbours.py`](evals/style_neighbours.py)) and made the first measured run (guide `any`, step 2 unchanged, no pass bar; tuning step 2 is decided from this result, not in this work). Run A (no family noun), all 83 briefs: right first 75/83 (90%), top 3 83/83 (100%), no style 0, BA picks 0. On the 61 briefs of the 50 single-family triples: Run A 55/61 (90%) right first, 61/61 top 3; Run B (family noun as `named`) 44/61 (72%) right first, 57/61 (93%) top 3; gap B - A -11 (-18 pts) right first, -4 (-7 pts) top 3. The 41 mixed triples run in A only. Run A misses (8): 19C, 20B, 9A, 14C, 25B, 8B, 23F, 26A; no triple has more than one miss. Run B: most confusions in triples 82 (3 of 3 styles wrong), 95, 84, 81, 79, 77 (2 each); the family noun mostly pulls picks to a style whose name holds it (e.g. 'stout' to 20B, 'wheat' to 1D, 'lager' to 1B). Results: [`evals/results/2026-10-16-s6.json`](evals/results/2026-10-16-s6.json). `tests/test_style_neighbours.py`: 103 pass ([plan](docs/work/s6-style-neighbours/plan.md)).
- s6-style-neighbours Task 2: wrote the 83 briefs, one per distinct triple style, in [`evals/style_neighbours.toml`](evals/style_neighbours.toml). Each has 1-2 stated numbers inside the style's 2021 range (the one that sets it apart from its partners where there is one) and 2-4 words (step 1 hints plus other words) taken from its 2021 entry; no request holds a style name, alias or family noun. `tests/test_style_neighbours.py` now has 97 passing cases against the stack (range, words in the entry, no name in the request, step 1 contract). Step 2 was not run on the briefs ([plan](docs/work/s6-style-neighbours/plan.md)).
- s6-style-neighbours Task 1: built the 91 study-guide triples (S0 table, pages 30-33; ids 1-110 minus the 19 removed) with their BJCP 2021 codes in [`evals/style_neighbours.toml`](evals/style_neighbours.toml), with a `family` noun from BJCP's 2021 family tags: 50 single-family, 41 mixed (measured). They cover 83 distinct styles, not the 84 the brief counted (84 printed names; Vienna and Vienna Lager are both 7A), so there will be 83 briefs; Run B covers 61 of them. `tests/test_style_neighbours.py`: 6 tests pass against the stack ([plan](docs/work/s6-style-neighbours/plan.md)). Step 2 not run on anything yet.
- Planned s6-style-neighbours ([`docs/work/s6-style-neighbours/plan.md`](docs/work/s6-style-neighbours/plan.md)): six tasks. The 91 study-guide triples with their 2021 codes and 83 briefs (1–2 numbers, 2–4 words from each style's 2021 entry, no name, alias or family noun) in `evals/style_neighbours.toml`, checked against `ref.beer_style`; `python -m evals.style_neighbours [--save]` runs step 2 with guide `any` twice, A without and B with the triple's family noun (from BJCP's family tags) as `named`, and reports right-first, top 3, confusions per triple and the A–B gap side by side, no bar (50 triples single-family, 41 A only; `named` boosts by name words, it does not filter, measured); a note on the BJCP 2021 specialty-entry rules vs D1; a hand-written Barnes 2008 cross-check of the 21 envelopes with a 2008 card (all 21 cards found), decided by the user, agreed changes loaded with the s3 flow. Step 2 does not change.
- Shipped s7-kb-articles ([`docs/finished/s7-kb-articles/`](docs/finished/s7-kb-articles/plan.md)): 12 articles and short papers (258 chunks, each with its `source_url`) in `kb`, `app.kb_search` returns `source_url`, eval reports books (recall@5 0.422, bar 0.40 met) and articles (0.867, no bar) apart; verification all 10 checks, full `pytest` 571 passed (re-run on the branch before merge, measured 2026-10-16).
- s7-kb-articles Task 8 ([`docs/finished/s7-kb-articles/`](docs/finished/s7-kb-articles/plan.md)): `python -m evals.retrieval --save s7` on 60 questions: books (q01-q45) recall@5 **0.422**, MRR@10 0.345, bar 0.40 met (s4: 0.422 / 0.354); articles (q46-q60, no bar) recall@5 0.867, MRR@10 0.608. Missed article questions: q56 (Lactobacillus) and q59 (Terrill). Kb holds 2,180 book chunks and 258 article chunks (205 Markdown, 53 PDF). No retrieval setting changed. Full `pytest` 571 passed (168 s, measured with the stack up). `tests/test_kb_search.py::test_returns_k_rows_with_source_and_page` failed once real article chunks were loaded (page-less vector hits entered the top 5), so it now uses a unique query word and checks the page on its own rows only. Results in [BOOKS.md](docs/BOOKS.md) §1d.
- s7-kb-articles Task 7 ([`docs/finished/s7-kb-articles/`](docs/finished/s7-kb-articles/plan.md)): 15 article questions (`q46`-`q60`, one passage per article plus a second for Bru'n Water, BJCP introductions and the Troester PDF) added to `evals/retrieval_questions.toml`, picked before any retrieval ran and reviewed by the user on 2026-10-16. Markdown expects have no `page`; q01-q45 untouched. `tests/test_retrieval_eval.py` 10 passed, including `test_every_quote_resolves`. The eval itself has not been run yet.
- s7-kb-articles Task 6 ([`docs/finished/s7-kb-articles/`](docs/finished/s7-kb-articles/plan.md)): `evals/retrieval.py` reports books and articles separately; the 0.40 recall@5 bar is judged on the books group only, articles are reported with no bar. New `cite()` cites a page-less chunk by slug, title and URL instead of a page. Tests in `tests/test_retrieval_eval.py` (`test_summarise_bar_on_books_only`, `test_summarise_bar_not_met`, `test_cite_without_page`).
- s7-kb-articles Task 5 ([`docs/finished/s7-kb-articles/`](docs/finished/s7-kb-articles/plan.md)): the two PDF articles are in `kb`: Troester mash parameters 26 chunks (pp. 1-20; pp. 22-23 skipped, conclusion prose on p. 20 kept), Janish TQ dry-hop paper 27 chunks (cover skipped, 3 `REFERENCES` chunks dropped by section). SQL checks returned 0 rows; all 12 article sources have a URL and chunks, books unchanged at 2,180. [BOOKS.md](docs/BOOKS.md) §1c lists both.
- s7-kb-articles Task 4 ([`docs/finished/s7-kb-articles/`](docs/finished/s7-kb-articles/plan.md)): the ten Markdown articles are in `kb`: 205 chunks (Troester mash time 5, Terrill 4, Janish short/cool 14, hot side 17, pH 9, coffee 18, MtF Berliner 11, MtF Lactobacillus 7, Bru'n Water 78, BJCP introductions 42), each with its URL, `page` null. `dropped by section` was > 0 for all six sources with `drop_sections`. SQL checks for leaked header lines, `[n]` markers, left-out section headings, pages on Markdown and table-like rows all returned 0. The books still hold 2,180 chunks with the same per-book counts; re-ingesting `janish-ph-hoppy-beers` with `--reuse-docling` gave the same fingerprint. [BOOKS.md](docs/BOOKS.md) has the new §1c (articles) and §2b (adding an article). The two PDF articles and the eval are not done yet.
- s7-kb-articles Task 3 ([`docs/finished/s7-kb-articles/`](docs/finished/s7-kb-articles/plan.md)): `db/040_kb_search.sql` now drops and recreates `app.kb_search` (return type changed) so it returns `source_url` after `source_title`; applied twice to the running DB as `postgres`, owner `postgres`, ACL null, no dependent objects. `tests/test_kb_search.py::test_returns_source_url` added.
- s7-kb-articles Task 2 ([`docs/finished/s7-kb-articles/`](docs/finished/s7-kb-articles/plan.md)): `upsert_source` writes `ref.source.url` and keeps an existing URL when a later entry has none; stack test `test_upsert_source_writes_url` (seen failing first), `tests/test_books.py` 21 passed.
- s7-kb-articles Task 1 ([`docs/finished/s7-kb-articles/`](docs/finished/s7-kb-articles/plan.md)): `loaders/books.py` takes Markdown sources (`clean_markdown`, `page` null) and drops chunks under named headings (`drop_sections`); `ARTICLES` holds the 12 entries (`python -m loaders.books --help` lists 17 slugs). 17 unit tests in `tests/test_books.py` pass, whole non-stack suite 193 passed. Nothing ingested yet. The Troester wiki page still returned HTTP 500 on 2026-10-16, so its URL is unverified.
- Planned s7-kb-articles ([`docs/finished/s7-kb-articles/plan.md`](docs/finished/s7-kb-articles/plan.md)): the s4 loader takes Markdown (header lines and `[n]` markers cleaned before Docling, `page` null) and drops named reference, footnote and link sections by heading, for Markdown and PDF alike; 12 `ARTICLES` entries with URLs (Troester's PDF cited by its braukaiser.com wiki page, found 2026-10-16); `app.kb_search` returns `source_url`; the eval reports books (bar 0.40) and articles (no bar) apart; 15 article questions for review. Docling was checked to keep the full heading path for Markdown and to mark the TQ paper's references as a heading.
- Revised brief for s7-kb-articles ([`docs/finished/s7-kb-articles/`](docs/finished/s7-kb-articles/brief.md)) against the shipped s4 loader and eval: names the 12 files (10 Markdown, 2 PDF), leaves out reference and footnote sections, `app.kb_search` returns the source URL, books' recall@5 held at 0.40 on s4's 45 questions (below it, the work stops and reports; tuning is its own item), articles' recall@5 and MRR@10 reported with no bar, Troester's PDF cited by its braukaiser.com wiki page (user decisions). Docling's chunk endpoint was checked to take Markdown (empty page list, headings as section path).
- Shipped s4-books-kb ([`docs/finished/s4-books-kb/`](docs/finished/s4-books-kb/plan.md)): five books (2,180 chunks) in `kb`, `app.kb_search` hybrid retrieval and the retrieval eval (recall@5 0.422, MRR@10 0.354 on 45 questions, bar 0.40 met); verification all 8 checks, full `pytest` 557 passed (re-run on the branch before merge, measured 2026-10-16).
- s4-books-kb review fixes ([`docs/finished/s4-books-kb/review.md`](docs/finished/s4-books-kb/review.md)): BOOKS.md §3 marks each *How to Brew* cut table and formula page with the `s1-maths` section or `adjunct-fermentables` pass that covers it (the rest are not passed yet); DATABASE.md §4 and §7 now say all five books, 2,180 chunks; the Scripts row lists the books loader, retrieval eval and their tests; *How to Brew* is by Palmer alone; the retrieval-tuning TODO notes that `candidates` above 40 needs `hnsw.ef_search` raised.
- s4-books-kb Task 9 ([`docs/finished/s4-books-kb/`](docs/finished/s4-books-kb/plan.md)): first measured retrieval run (`python -m evals.retrieval --save s4-first`, [`evals/results/2026-10-16-s4-first.json`](evals/results/2026-10-16-s4-first.json), before any tuning): recall@5 0.422, MRR@10 0.354 on 45 questions; per book in [`docs/BOOKS.md`](docs/BOOKS.md) §1b. `RECALL_AT_5_BAR` set to 0.40 (the first run rounded down to 0.05, user's decision). Final run (`--save s4`, [`evals/results/2026-10-16-s4.json`](evals/results/2026-10-16-s4.json)): same numbers, bar met; full `pytest` 557 passed in 168 s. Tuning is not part of this work; a TODO is in [RECIPE-ROADMAP](docs/RECIPE-ROADMAP.md) §8 Later.
- s4-books-kb Task 8 ([`docs/finished/s4-books-kb/`](docs/finished/s4-books-kb/plan.md)): [`evals/retrieval_questions.toml`](evals/retrieval_questions.toml) holds 45 retrieval questions, 9 per book across the five books, each with page and a short quote (56 quotes); passages picked evenly by page before any retrieval was run. Reviewed and approved by the user as written, 2026-10-16. Measured: all quotes resolve to chunks of their book (`test_every_quote_resolves`, seen failing with a broken quote); 6 tests pass in `tests/test_retrieval_eval.py`. No retrieval run yet (Task 9).
- s4-books-kb Task 7 ([`docs/finished/s4-books-kb/`](docs/finished/s4-books-kb/plan.md)): [`evals/retrieval.py`](evals/retrieval.py) computes recall@5 and MRR@10 of `app.kb_search` against a question set (`python -m evals.retrieval [--save LABEL]`, `--question "…"` prints the top 5 cited chunks). `RECALL_AT_5_BAR` is `None` until Task 9; the question set (Task 8) does not exist yet. 4 unit tests in `tests/test_retrieval_eval.py` (seen failing before the module existed). Measured: the diacetyl-rest question returns 5 chunks with source and page.
- s4-books-kb Task 6b ([`docs/finished/s4-books-kb/`](docs/finished/s4-books-kb/plan.md)): ingested *Malt* (Mallett, 2014) and the *BJCP Beer Exam Study Guide* (section IV only) by following [`docs/BOOKS.md`](docs/BOOKS.md) §2. *Malt*: Docling (2.3 min) made 458 chunks from 335 pages; pages 1–16 and 263–335 skipped and tables cut leave 341 (tokens min 46, median 316, max 514). Study guide: Docling (51 s) made 202 chunks from 77 pages; pages 1–45 skipped and tables cut leave 85 (tokens min 59, median 313, max 510). 0 table-like rows in both (measured). Counts per book: *How to Brew* 943, *Water* 357, *Yeast* 454, unchanged with the same fingerprints; five books in `kb`. Second ingests with `--reuse-docling` gave the same fingerprints. BOOKS.md gets both rows and doc → calc notes.
- s4-books-kb Task 6 ([`docs/finished/s4-books-kb/`](docs/finished/s4-books-kb/plan.md)): ingested *Yeast* (White & Zainasheff, 2010) by following [`docs/BOOKS.md`](docs/BOOKS.md) §2 only, with `python -m loaders.books white-zainasheff-yeast`. Docling (2.1 min) made 526 chunks from 325 pages; pages 1–21 and 305–325 skipped and tables cut leave 454 (tokens min 31, median 298, max 514; 0 table-like rows; measured). Counts per book before and after: *How to Brew* 943, *Water* 357, unchanged (A6). A second ingest with `--reuse-docling` gave the same count and fingerprint (`39be2bdf…`, A1). BOOKS.md gets the *Yeast* row and doc → calc note (52 table pages, 2 formula pages, none passed yet) and three clarified steps in §2.
- s4-books-kb Task 5 ([`docs/finished/s4-books-kb/`](docs/finished/s4-books-kb/plan.md)): ingested *Water* (Palmer & Kaminski, 2013) with `python -m loaders.books palmer-kaminski-water`, following [`docs/BOOKS.md`](docs/BOOKS.md) §2. Docling (2.5 min) made 440 chunks from 273 pages; pages 1–18 and 238–273 skipped and tables cut leave 357 (tokens min 35, median 319, max 514; 0 table-like rows; measured). A second ingest from a fresh Docling run gave the same count and fingerprint. *How to Brew* stayed at 943 with the same fingerprint. BOOKS.md gets the *Water* row and its doc → calc note (59 table pages, 14 formula pages, none passed yet) and two clarified steps in §2.
- s4-books-kb Task 4 ([`docs/finished/s4-books-kb/`](docs/finished/s4-books-kb/plan.md)): ingested *How to Brew* with `python -m loaders.books palmer-how-to-brew`. Docling made 1,276 chunks from the 612 pages; with pages 1–26 (front matter) and 579–612 (bibliography, index) skipped and tables and `<!-- formula-not-decoded -->` placeholders cut, 943 chunks remain (tokens min 32, median 273, max 514; 0 table-like rows; measured). A second ingest from a fresh Docling run gave the same count and the same text fingerprint. `loaders/books.py` also strips the formula placeholder (new unit test). The Docling result is saved in `shared/rag-files/docling-chunks/`, because `shared/docling-scratch/` is owned by root and the first 612-page run could not save there (plan deviation). New [`docs/BOOKS.md`](docs/BOOKS.md): books in `kb`, how to add one, doc → calc notes for *How to Brew* (194 table pages, 43 formula pages by chapter; the page-by-page mapping to `s1-maths` sections is not done). `docs/DATABASE.md` §4 and §7 updated.
- s4-books-kb Task 3 ([`docs/finished/s4-books-kb/`](docs/finished/s4-books-kb/plan.md)): `db/040_kb_search.sql` adds `app.kb_search(query_text, query_embedding, k, candidates, rrf_k)`: 40 nearest chunks (HNSW) and 40 best any-word full-text matches fused by reciprocal rank (k = 60), returning source slug, title, section, page, text, score and both ranks. Applied as `postgres` (owner checked). `tests/test_kb_search.py`: 4 stack tests on synthetic chunks, rolled back (2 seen failing with the OR query broken); full `pytest` 550 passed in 139 s (measured). `kb.chunk` is still empty.
- s4-books-kb Task 2 ([`docs/finished/s4-books-kb/`](docs/finished/s4-books-kb/plan.md)): `loaders/books.py` gets `upsert_source` (keeps the `ref.source` id), `replace_chunks` (one book's chunks deleted and inserted in the caller's transaction) and the `main()` flow (Docling or `--reuse-docling`, embed, one transaction). `tests/test_books.py` has 3 stack tests, rolled back (seen failing with the delete removed); full `pytest` 546 passed in 139 s with the stack up (measured). `kb.chunk` is still empty; nothing ingested, and `main()` has not been run against Docling yet.
- s4-books-kb Task 1 ([`docs/finished/s4-books-kb/`](docs/finished/s4-books-kb/plan.md)): `loaders/books.py` holds the `Book` list (How to Brew only so far) and the pure part of the loader: Docling form fields, result check, table stripping, prose rows, embedding parse. `tests/test_books.py` has 8 unit tests; full `pytest` 543 passed in 148 s with the stack up (measured). Docling and database steps are not written yet (Task 2); nothing ingested.
- Sorted all new source files and decided each one's fate (user request): read the 7 books and guides and 6 more PDFs and the spreadsheet the user downloaded, and saved 12 web pages as Markdown or PDF (Troester's mash-time wiki page, Terrill's attenuation post, 4 Janish posts plus his MBAA TQ dry-hop paper, 2 Milk The Funk pages, Bru'n Water *Water Knowledge*, the BJCP 2021 introductions). `books/pending/` is gone: files renamed and moved into `books/`, `styles/` and the new `water/`, `sensory/` and `articles/` folders (each with a tracked `.gitkeep`). Per-file fates in the new [`docs/SOURCES.md`](docs/SOURCES.md). Briefs: s4-books-kb now covers five books (adds *Malt* and the study guide's §IV, test set ≥ 40) with brief and plan Deviations; m7-process names its sources (BJCP water table, Bru'n Water as calc source and spreadsheet as test oracle only, Janish dry-hop, Milk The Funk souring) and needs s5; m4 needs s5; m5 and m8 notes. New draft briefs: [`s5-mash-attenuation`](docs/work/s5-mash-attenuation/brief.md) (cited model replacing rule 10's uncited mapping), [`s6-style-neighbours`](docs/work/s6-style-neighbours/brief.md) (step 2 check set from the 91 triples, Barnes envelope cross-check, D1 vs BJCP specialty-entry text), [`s7-kb-articles`](docs/finished/s7-kb-articles/brief.md) (12 articles into kb). WORKFLOW-ROADMAP graph and table, RECIPE-ROADMAP (rule 10 TODO → s5, fault source) and DATABASE.md (`ref.fault` source) updated. Nothing ingested or loaded.
- Marked the build order s4 → s7 → s6 → m3 → s5 → m4 → m5 → m6 → m7 → m8 in the briefs (user request): s4 no longer waits for m7's doc → calc pass (tables never enter `kb`), and s4, s5 and s7 now say which items wait for them; WORKFLOW-ROADMAP gets the order line and S4's needs fixed.
- Saved two pages of the BJCP Beer Exam Study Guide web edition as Markdown in `shared/rag-files/books/pending/` (user request: keep what is valuable): `bjcp_troubleshooting.md` (*Beer Characteristics*, 25 sections, ~5,000 words) and `bjcp_water.md` (~1,750 words, famous-waters table). Checked: same 2017 text as Section IV of `BJCP_Study_Guide.pdf`; the 8 × 6 ion table matches the PDF. The other four pages (wort production, hops, malt, yeast) were not saved: they repeat *How to Brew*, hopline and `ref.yeast` data. Not ingested.
- `tests/test_pipeline.py` (the only tests that call the model) now unloads every model from Ollama when its last test finishes, via `evals.benchmark.unload_all()` (user request: the model stayed loaded after a test run and had to be stopped by hand). Checked: after one pipeline test, `ollama ps` is empty and the Ollama log shows the stop right after the test's `/api/chat`.
- Split `shared/rag-files/pending/` into `books/`, `styles/`, `hopline/`, `maltsters/` and `recipes/` (user request: the flat folder had become a mess and "pending" no longer meant anything). Deleted the unused `malts.json`. `.gitignore` now ignores everything under `shared/rag-files/` except each folder's `.gitkeep` (checked: `git status` shows only the five `.gitkeep` files). `db/011_ref_sources.sql` points the *How to Brew* and PrimeTime notes at the new paths and gets a correction for existing rows; applied twice as `postgres` (`UPDATE 1` ×2, then 0). Updated §5, the m7-process brief, FILL-REF-README and DATABASE-REVIEW; `docs/finished/` and older §8 entries keep the old path as history. Re-ran styles, malts, hops, yeasts, adjuncts and then `fermentable_facts` from the new paths: counts and md5 of `ref.beer_style`, `ingredient`, `fermentable`, `hop`, `yeast`, `source` identical to before (measured). pytest would not have caught a stale path: no test reads these files.
- Planned s4-books-kb ([`docs/finished/s4-books-kb/plan.md`](docs/finished/s4-books-kb/plan.md)): Python loader `loaders/books.py` (one `BOOKS` entry + `python -m loaders.books <slug>` per book, tables kept out of `kb`), `app.kb_search` (vector + full text, reciprocal-rank fusion), reviewed question set and `python -m evals.retrieval`; 9 tasks.
- Wrote brief for s4-books-kb ([`docs/finished/s4-books-kb/`](docs/finished/s4-books-kb/brief.md)): ingestion as a Python loader so a further book is one source entry plus one documented command (R7); the recall@5 bar is set from the first measured run and fixed before the first tuning change.

### 2026-10-15
- Shipped s3-style-fit ([`docs/finished/s3-style-fit/`](docs/finished/s3-style-fit/report.md)): style-fit tags, envelopes for 26 styles, `app.style_level` / `app.style_fit_recipe` and the golden set (G-S met). Verification: 12 checks passed; full `pytest` 535 passed in 167 s on the branch (measured at ship time).
- s3-style-fit re-review fixes (2026-10-15, [`docs/finished/s3-style-fit/`](docs/finished/s3-style-fit/review.md) findings 11-14): the flake colour sources now resolve (`simpsons-malt-2025`, new `briess-flakes-web` row in `db/011_ref_sources.sql`, `ref.source` 20 rows; loaders re-run, 0 `field_source` values without a `ref.source` row, measured); DATABASE.md EBC count 78; lower-bound colour rule recorded in the brief Deviations and STYLE-FIT §4; roadmap G-S test count 535. Full `pytest` 535 passed.
- s3-style-fit review fixes (2026-10-15, [`docs/finished/s3-style-fit/`](docs/finished/s3-style-fit/report.md) §7): review finding 1, the colour check (R7) was skipped on 11 of 22 reference recipes because fermentables without `ebc` make `app.check_recipe` return SRM null, so the earlier "G-S: met" below was not verified for colour. Flaked Barley and Oats now have 0-3.2 EBC (Simpsons p. 2), Flaked Corn 1.576 and Flaked Rice 1.97 EBC (Briess 0.8 and 1 SRM × 1.97), written by `loaders/adjuncts.py` so a re-run keeps them; Honey, Lactose and Enzyme Malt still have none (no sourced value). `app.style_fit_recipe` now computes the SRM as a lower bound (those count as 0 EBC) and says so in the because; "too much colour" needs even the lower bound over the style max. Only b19 failed (26.7 vs 17C 14-25); the user chose to fix the recipe: Caramunich Type 2 8 → 5 %, Roasted Barley 2 → 1 %, Maris Otter 80 → 84 %, Honey 10 %, lower-bound SRM 18.8, OG 1.100, IBU 26.3. Findings 2-5: the because names the missing colour, "needs review" only for flagged ingredients and once, IBU/SRM rounded, `style_level` readability. Not verified: colour below the style range is not checked. Full `pytest` 535 passed in 142 s, `-m "not stack"` 171 passed, 364 deselected (measured).
- s3-style-fit Task 10 (2026-10-15): measured status recorded. Full `pytest` 531 passed in 132 s with the stack up, `-m "not stack"` 171 passed, 360 deselected; row counts and function owners queried from the live DB (§4 Database row, DATABASE.md §2 and §7). **G-S: met, with a correction (see the 2026-10-15 review-fix entry above this one).** The Citra table reproduces from SQL, 26 style envelopes reviewed by the user, the golden set passes, every reference-recipe line is rated and only the briefs' own deviations (b08, b18) are flagged. Correction: this relied on a colour check that was skipped on 11 of 22 recipes (SRM null); it now runs as a lower bound. The A10 grep found no corpus route for style fit. `tests/test_fermentable_facts.py::test_db_enzyme_and_boil` now reads `docs/finished/s2-formulation-rules/report.md` (moved when s2 shipped), so the suite has no failure.
- s3-style-fit Task 9: `app.style_fit_recipe` added to [`db/034_style_level.sql`](db/034_style_level.sql) (every line through `style_level` with the recipe's totals, required check, hop/roast min check on recipe totals with one-level tolerance); applied twice as `postgres`. [`tests/test_style_fit_recipe.py`](tests/test_style_fit_recipe.py) 5 tests pass over the 22 reference recipes. At the stop the user settled the findings: b08 and b18 accepted as the briefs' deviations, b10 and b07/b12 reference recipes adjusted, Mexican-Style Amber Lager roast min low → none (details in [report.md](docs/finished/s3-style-fit/report.md) §6); full `pytest` 530 passed, 1 failed (the known `test_db_enzyme_and_boil`) (measured).
- s3-style-fit Task 8: [`db/034_style_level.sql`](db/034_style_level.sql) adds `app.style_level` (STYLE-FIT §5: step 0 counts reviewed ingredient rows, override, adjunct/sugar rule, usage-effect loop with colour/bitterness vs the style range, intensity max check, yeast min check with one-level tolerance skipped for needs-review yeasts, best-pair character match, combine, `fermentable_style` bump), `app.tag_match` and two helpers (`level_word`, `tag_under`); applied twice as `postgres`, functions owned by `postgres` (measured). [`tests/test_style_level.py`](tests/test_style_level.py) 12 tests and [`tests/test_style_fit_golden.py`](tests/test_style_fit_golden.py) (53 approved cases, `test_citra_table`, `test_m3_cases_have_no_rule`) all pass without changing any expected level; breaking the bump order made 5 of them fail; full `pytest` 525 passed, 1 failed (the known `test_db_enzyme_and_boil`) (measured).
- s3-style-fit Task 7: [`db/033_style_fit_effects.sql`](db/033_style_fit_effects.sql) adds `app.usage_effects()` (25 rows, STYLE-FIT §3), `app.style_fit_cut_points()` (every approved cut point O1–O7, R1–R7, E1–E4, P1–P3, `min_tolerance` 1 and `character_match`, each with its basis), `app.intensity_level`, `app.oil_dose` and `app.roast_index`; applied twice as `postgres`, all five functions owned by `postgres` (measured). [`tests/test_style_fit_effects.py`](tests/test_style_fit_effects.py): 6 tests pass (3 seen failing with a basis stripped and a threshold out of order); full `pytest` 458 passed, 1 failed (the known `test_db_enzyme_and_boil`) (measured). `style_level` is Task 8.
- s3-style-fit Task 6: cut points and golden set approved by the user ([`cut-points.md`](docs/finished/s3-style-fit/cut-points.md), [`golden-review.md`](docs/finished/s3-style-fit/golden-review.md), report §4–§5). Oil dose O1–O7 and roast index R1–R5 from *How to Brew* (pp. 71–72, 230–231, 388, 404, its recipes), O7 value, R6–R7 and the ester/phenol bases set by the user; esters 3 for an ester character and +1 above 21 °C (the plan's 4 and midpoint rule failed reference b05). New, agreed through the golden review: a min check with one-level tolerance (yeasts per ingredient, hops and roast on recipe totals in Task 9) and step 0 rating 31B / Specialty Honey Beer; STYLE-FIT §4–§5 updated. On paper no reference recipe is above a max; b07, b12, b22 are below a recipe-total min (→ Task 9 stop). [`tests/fixtures/style_fit_golden.toml`](tests/fixtures/style_fit_golden.toml): 53 cases, all approved (y02 set to ⚠️ by the user). Not in code yet (Tasks 7–8).
- s3-style-fit: the user removed the Sterling hop ("It is from Saaz, and not really available on hopline as well"). [`db/035_drop_sterling.sql`](db/035_drop_sterling.sql) deletes it (cascading to its `ref.hop`, `ingredient_tag` and `ingredient_review` rows; nothing else referenced it), applied twice as `postgres`; `loaders/hop_products.py` gets an `EXCLUDED` map so `loaders.hops` skips SKU 200929 on a re-run (dry run of `build`: 89 hops, no Sterling). Measured: 89 hops, 297 ingredients, `ref.ingredient_review` 38 (the YeastFlow yeasts, no hop).
- s3-style-fit Task 5: the user reviewed all 26 style envelopes against [`envelope-review.md`](docs/finished/s3-style-fit/envelope-review.md) and approved them as proposed; [`loaders/style_envelopes.toml`](loaders/style_envelopes.toml) is `reviewed = true` for all 26 and loaded twice with identical results: `ref.style_sensory` 189 rows, `style_character` 237, `style_ingredient` 116, `style_rule` 0 (31B and specialty-honey-beer have the sugar row only, no sensory rows). Vocabulary: 239 synonyms (34 added), 3 no-character words, 2 yeast-family overrides; `python -m loaders.tags` re-run: 39 ingredients flagged (Sterling + 38 YeastFlow with no aroma text). Three new stack tests in `tests/test_style_envelopes.py` (seen failing with a wrong expectation); full `pytest` 451 passed, 1 failed (the known `test_db_enzyme_and_boil`) (measured). Review notes: [report §3](docs/finished/s3-style-fit/report.md).
- s3-style-fit Task 4: [`loaders/style_envelopes.py`](loaders/style_envelopes.py) (`--extract` asks the D2 model offline, code checks every answer: verbatim quotes, scale words, min <= max, one entry per dimension, words resolved to `ref` rows; load mode reads the reviewed toml), [`loaders/style_envelope.schema.json`](loaders/style_envelope.schema.json) and [`loaders/style_envelope_prompt.md`](loaders/style_envelope_prompt.md). The run over the 26 styles took 66 min; 24 drafts are clean, 10A and 16B keep 5 problems, 31B came out empty ("same as the base beer"); nothing is in `ref` and the draft is not committed (review is Task 5). 10 tests in `tests/test_style_envelopes.py`; full `pytest` 448 passed, 1 failed (the earlier `test_db_enzyme_and_boil`) (measured). Details: [report §2](docs/finished/s3-style-fit/report.md).
- s3-style-fit Task 3: [`loaders/style_fit_vocab.toml`](loaders/style_fit_vocab.toml) (18 dimensions, 69 tags, 205 synonyms) and [`loaders/tags.py`](loaders/tags.py) (`python -m loaders.tags`) load the vocabulary and derive `ref.ingredient_tag`: 803 rows (89/90 hops with origin and character, 81/81 fermentables with role family, 117/119 yeasts with family, 55 yeasts with character), `reviewed = false`. Hop character comes from the shop's "Aroma :" line, else the "Komló aroma" list. 50 ingredients are in `ref.ingredient_review` (8 hops, 42 yeasts; 38 of them YeastFlow strains with no aroma text); nothing is guessed. `tests/test_tags.py` 10 tests pass (seen failing with `hop_words` using both sources); full `pytest` 438 passed, 1 failed (the known `test_db_enzyme_and_boil`). Details in [`docs/finished/s3-style-fit/report.md`](docs/finished/s3-style-fit/report.md) §1.
- s3-style-fit Task 2: [`db/012_style_fit.sql`](db/012_style_fit.sql) adds `ref.style_ingredient` (characteristic ingredients) and `ref.ingredient_review` (flagged ingredients), both empty until Tasks 3 and 5. Applied twice as `postgres`; `ref` now has 19 tables, all owned by `postgres` (measured). `tests/test_tags.py::test_schema` passes (seen failing with the tables dropped). Full `pytest`: 429 passed, 1 failed: `test_fermentable_facts.py::test_db_enzyme_and_boil` reads `docs/work/s2-formulation-rules/report.md`, which moved to `docs/finished/` when s2 shipped (not from this change).
- s3-style-fit Task 1: design docs describe style fit without a corpus. STYLE-FIT §4 (cut points from *How to Brew* and OBC, colour/bitterness vs the style range), §5 (step 1b adjunct/sugar rule, `fermentable_style` bump, best-pair character match, no-envelope and missing-dose notes), §6 (BJCP and BA through the LLM extract); RECIPE-ROADMAP §5, WORKFLOW-ROADMAP (S2 → S3, G-S bar), DATABASE §2, §7, §8 updated; D9 decided and moved out of §7 into §5. Docs only; A10 grep checked.
- Planned s3-style-fit ([`docs/finished/s3-style-fit/plan.md`](docs/finished/s3-style-fit/plan.md)): 10 tasks; design docs first (STYLE-FIT §4/§5, corpus mentions, D9 out of §7); `ref.style_ingredient` and `ref.ingredient_review`; vocabulary and tagging in `loaders/style_fit_vocab.toml` + `loaders/tags.py` (hop character from the hopline "Aroma :" line, measured 87/90 hops); offline LLM extraction `loaders/style_envelopes.py`; usage effects and cut points in `db/033_style_fit_effects.sql`, `app.style_level` and `app.style_fit_recipe` in `db/034_style_level.sql`; three user stops (Task 5: the 26 envelopes; Task 6: cut-point gaps and the golden set; Task 9: only if a reference-recipe line is unexpectedly ⚠️/⛔).
- Wrote brief for s3-style-fit ([`docs/finished/s3-style-fit/`](docs/finished/s3-style-fit/brief.md)): revised the 2026-10-12 draft so it no longer needs `s2-corpus` (abandoned, D7). Envelopes for 26 styles (22 brief styles, 3 alternates, 20B for the Citra table); the corpus popularity bump and corpus-calibrated cut points are replaced. The user's answers: cut points from *How to Brew* and OBC; a general adjunct/sugar rule (named in the style's characteristic ingredients 👍, else ⚠️); `ref.fermentable_style` as the 👍 bump for fermentables; the 3 BA styles through the same LLM extraction and review; Claude drafts the golden set. STYLE-FIT.md §4 and §5 change accordingly (agreed). New checks: M3's 7 ingredient cases in the golden set, and every reference-recipe ingredient rated in its style. Measured: all style-fit `ref` tables empty, all 90 hops have (Hungarian) descriptor text.
- Shipped s2-formulation-rules ([`docs/work/s2-formulation-rules/`](docs/finished/s2-formulation-rules/plan.md)): verified (16 checks, full `pytest` 429 passed, re-run on the branch before the merge) and merged to `main`. Delivered: fermentable roles, `max_pct`, `min_boil_min`, enzyme activity, descriptions, 27 substitute pairs and 623 style rows in `ref`; the 13 formulation rules (`app.formulation_rules()`) and the check `app.check_recipe` (12 checked rules); 22 user-approved reference recipes that all pass. The work folder moves to `docs/finished/s2-formulation-rules/`. Status columns in §4 and §5 already describe the shipped state.
- Fixed s2-formulation-rules review findings 1-5 ([`docs/work/s2-formulation-rules/`](docs/finished/s2-formulation-rules/plan.md)): rule 9 sentence now says it applies when style guidance is on (user's answer, brief Deviations); rule 10's stated FG/ABV band reads `midpoint_tolerance.fg`, and a mash below 64 °C reports `limit` 64; tests for rules 9, 10, 11, 13 now assert that only their own rule fails, with 64/69 °C mash boundaries and a check-side limits test; §4 counts (17 `ref` tables, 33 in all, 19 sources), code span and known gaps, and DATABASE.md gaps corrected. `db/031` and `db/032` applied twice as `postgres`.
- Finished s2-formulation-rules Task 9 ([`docs/work/s2-formulation-rules/`](docs/finished/s2-formulation-rules/plan.md)): full `pytest` 429 passed in 132 s with the stack up, `-m "not stack"` 157 passed, 272 deselected (measured). §4 Database and Scripts rows and §5 malt and adjunct rows now describe the roles, columns, tables, rules and check (live counts: 81 roles, 81 `max_pct`, 51 enzyme activity, 7 long boils, 81 descriptions, 27 substitute pairs, 623 style rows). A13 re-checked: D7 decided in RECIPE-ROADMAP §9, §8 Later list, WORKFLOW-ROADMAP S2 link, no D7 row in §7, no `docs/work/s2-corpus/`.
- Implemented s2-formulation-rules Task 8 ([`docs/work/s2-formulation-rules/`](docs/finished/s2-formulation-rules/plan.md)): `tests/fixtures/reference_recipes.toml` holds 22 reference recipes (one per brief, built only from `ref` rows); the user approved them 2026-10-15 (b12 checked against 18A). All 22 pass all 12 checked rules in `app.check_recipe`; `tests/test_reference_recipes.py` 26 tests pass, no accepted failures. Three first drafts failed rule 10 (b12, b16, b22) and were fixed in the recipes. Multi-step mash profiles added to RECIPE-ROADMAP §8 Later (user request).
- Implemented s2-formulation-rules Task 7 ([`docs/work/s2-formulation-rules/`](docs/finished/s2-formulation-rules/plan.md)): [`db/032_formulation_check.sql`](db/032_formulation_check.sql) adds `app.check_rule_8` to `_13` (hop additions, style-midpoint targets, mash and predicted FG, yeast tolerance and temperature, purposes, boil time); `app.check_recipe` now returns 12 results (rules 1-6, 8-13), numbers passed to the rules. Applied twice, 12 rule functions owned by `postgres`. `tests/test_formulation_check.py` now has 37 tests (all pass); rule 9 skips the midpoint test when guidance is off (my reading of "outside the range only when stated or guidance off").
- Implemented s2-formulation-rules Task 6 ([`docs/work/s2-formulation-rules/`](docs/finished/s2-formulation-rules/plan.md)): [`db/032_formulation_check.sql`](db/032_formulation_check.sql) adds `app.ebc_mid`, `app.mash_attenuation` (linear, uncited), `app.check_recipe_items` (resolves ids, raises on bad input), `app.check_rule_1` to `_6` and `app.check_recipe` (numbers from s1's functions only, results for rules 1–6). Contracts `shared/contracts/formulation_check.{input,output}.schema.json`. Applied twice, all functions owned by `postgres`; `tests/test_formulation_check.py` 27 passed and `tests/test_contracts.py` passed; the rule-5 boundary, the colour boundary and the mash mapping were each seen failing when broken. Rules 8–13 come in Task 7.
- Implemented s2-formulation-rules Task 5 ([`docs/work/s2-formulation-rules/`](docs/finished/s2-formulation-rules/plan.md)): `db/031_formulation_rules.sql` holds `app.formulation_limits()` (every threshold, as jsonb) and `app.formulation_rules()` (definitions, rules 1–13, pending; 7 and pending unchecked), each sentence built with `format()` from the limits. Applied twice, both owned by `postgres`; `tests/test_formulation_rules.py` 4 passed (rule list, no ingredient or style name, no vague words, text follows the limits).
- Implemented s2-formulation-rules Task 4 ([`docs/work/s2-formulation-rules/`](docs/finished/s2-formulation-rules/plan.md)) after the user's review: Sprau → adjunct, 7 long boils (90 min) confirmed, 247-name style table approved (21 dropped), `max_pct` bases confirmed (9 are "user decision E"). Loaded with `python -m loaders.fermentable_facts`: roles 81/81, `max_pct` 81/81, `min_boil_min` 81, descriptions 81, 27 substitute pairs, 623 malt-style rows. Checked: the 63 catalogue `max_pct` values keep their checksum; a second load leaves the three tables identical; `tests/test_fermentable_facts.py` 22 passed (one test seen failing with the description write broken). 30 rows have no stated enzyme activity, listed in [`report.md`](docs/finished/s2-formulation-rules/report.md).
- Implemented s2-formulation-rules Task 3 ([`docs/work/s2-formulation-rules/`](docs/finished/s2-formulation-rules/plan.md)): `loaders/fermentable_facts.toml` holds roles for 80 of 81 fermentables (base 20, kilned 13, crystal 27, roast 13, adjunct 4, sugar 3; Sprau left open for the user), the 18 `max_pct` values of decision E (basis drafted: 5 placed, 13 `unplaced`, to be confirmed at the Task 4 stop), enzyme activity for 36 Weyermann and 15 Viking rows from the printed words, and 27 substitute pairs (19 chart, 8 user decisions); `loaders/fermentable_facts.py` reads, checks and loads it (load after `loaders.malts` and `loaders.adjuncts`). Nothing is loaded yet: `--propose-min-boil` proposes 90 min for 7 rows (4 Pilsner-type malts, both wheat malts, Eraclea) awaiting confirmation. `tests/test_fermentable_facts.py` 11 passed (two checked by breaking the code).
- Implemented s2-formulation-rules Task 2 ([`docs/work/s2-formulation-rules/`](docs/finished/s2-formulation-rules/plan.md)): `db/010_ref_schema.sql` adds `enzyme_activity`, `min_boil_min`, `description`, `description_ref` to `ref.fermentable` plus `ref.fermentable_substitute`, the `ref.fermentable_substitutes` view and `ref.fermentable_style`; `db/011_ref_sources.sql` adds the `malt-substitution-2025` source. Both files applied twice as `postgres` without errors; objects owned by `postgres`; `test_schema` passes. Tables are empty (loaded in Task 4).
- Implemented s2-formulation-rules Task 1 ([`docs/work/s2-formulation-rules/`](docs/finished/s2-formulation-rules/plan.md)): RECIPE-ROADMAP §9 D7 row set to decided, §8 Later turned into a list (enzyme rule, ratio corpus, mash-temperature TODO); WORKFLOW-ROADMAP S2 row, node and s2 → s3 edge now record that s2-corpus is gone; one note line in the m4, m5 and s3 briefs. Docs only; checked: 3 files / 3 insertions in the briefs, no `docs/work/s2-corpus/`, no D7 row in §7.
- Planned s2-formulation-rules ([`docs/work/s2-formulation-rules/plan.md`](docs/finished/s2-formulation-rules/plan.md)): 9 tasks; fermentable data in `loaders/fermentable_facts.toml`, rule text and limits in `db/031_formulation_rules.sql`, the check `app.check_recipe` in `db/032_formulation_check.sql`; two user review stops (Task 4: Sprau's role, long boils, style mapping; Task 8: the 22 reference recipes).

### 2026-10-14
- Wrote brief for s2-formulation-rules ([`docs/work/s2-formulation-rules/`](docs/finished/s2-formulation-rules/brief.md)): fermentable roles, `max_pct` gaps, enzyme activity, minimum boil, substitutes and catalogue descriptions, 13 exact formulation rules checked in code, one reference recipe per test brief. Draft, 8 open questions. With the user's agreement: D7 decided and moved out of §7 (no ratio corpus; LLM proposes, code scales and checks; revisit if test briefs show a need); §3 (intro, stages B–D, the ratios line) and §6.7 reworded so the LLM picks ingredients and proposes percentages and hop-schedule intent while code computes every number and checks the rules; §5 Brewer's Friend row set aside. `s2-corpus` abandoned: its draft brief `docs/work/s2-corpus/` is deleted (last in commit `57638a1`), and [`docs/STYLE-PROFILES.md`](docs/STYLE-PROFILES.md) is marked set aside.
- Shipped `s1-maths` ([`docs/work/s1-maths/`](docs/finished/s1-maths/plan.md)): the 19 `app.*` maths functions in `db/030_maths.sql` merged to `main`; verification ✅ (9 checks, full `pytest` 333 passed, re-run before merge). The branch also carries a showcase section for `dev-verify` and `dev-flow`.
- `s1-maths` review fixes: `app.boil_gravity` now takes `postboil_l` (batch + losses, HTB p. 291) instead of `batch_l`, and a JSON `null` field or array argument raises in `og`, `fg`, `ibu`, `grist_mcu`, `solve_grist` and `solve_hops` (both found by review, tests written first). `db/030_maths.sql` applied twice, 19 functions owned by `postgres`; full `pytest` measured 333 passed in 127.9 s ([plan](docs/finished/s1-maths/plan.md)).
- `s1-maths` Task 8: full `pytest` measured 331 passed in 127.7 s with the stack up (141 passed, 190 deselected with `-m "not stack"`); `tests/test_maths.py` is 79 tests. §4 Database and Scripts rows, §5 *How to Brew*, OBC and pending-files text, RECIPE-ROADMAP §8 P2 and WORKFLOW-ROADMAP G-M updated with these numbers ([plan](docs/finished/s1-maths/plan.md)).
- `s1-maths` Task 7: all 19 functions of [`db/030_maths.sql`](db/030_maths.sql) are owned by `postgres` (`pg_proc`). A one-off workflow `Maths check` (manual trigger, Postgres node with the `Postgres account` credential) ran `app.ibu` on the Joe Ale metric hops through n8n: execution 12623 returned 41.563655217631827951010459749021753347368421052631578, the same digits as `psql` (A5). The workflow was archived afterwards ([plan](docs/finished/s1-maths/plan.md)).
- `s1-maths` Task 6: `app.solve_grist` (jsonb items `{pct, extract_pct, mashed}` to the same items plus `kg`) and `app.solve_hops` (items `{share_pct, alpha_pct, minutes, usage}` to the same items plus `g`) added to [`db/030_maths.sql`](db/030_maths.sql) (applied twice, no errors). Both are closed form, since OG and IBU are linear in mass; a positive IBU target with no boil addition raises, and a target of 0 gives 0 g. `tests/test_maths.py`: 79 passed (full suite 331 passed); the grist round trip is within 0.001 OG, the hop round trip within 1 IBU, and FG orders lactose > pale > candi at OG 1.060. The solver tests were seen to fail with the solver constants changed ([plan](docs/finished/s1-maths/plan.md)).
- `s1-maths` Task 5: `app.mcu` (EBC in, °L = EBC / 1.97), `app.grist_mcu` (jsonb items `{kg, ebc}`) and `app.srm` (Morey, Palmer's constants 1.49 and 0.69, takes MCU) added to [`db/030_maths.sql`](db/030_maths.sql) (applied twice, no errors). `tests/test_maths.py`: 70 passed (full suite 322 passed); MCU of Palmer's example and both OBC beers within 0.01 (Dubbel against the recomputed 40.5), Shay Steam, Port O' Palmer and its option 2 within 1 SRM ([plan](docs/finished/s1-maths/plan.md)).
- `s1-maths` Task 4: `app.tinseth_utilisation`, `app.ibu_addition` and `app.ibu` added to [`db/030_maths.sql`](db/030_maths.sql) (applied twice, no errors). Whirlpool and dry hop count as 0 IBU, marked in a comment above the rule and pointing to RECIPE-ROADMAP §8 Later; an unknown usage raises. `tests/test_maths.py`: 62 passed (full suite 314 passed); all 160 cells of table 5.5 within 0.001, Joe Ale metric and US within 1 IBU ([plan](docs/finished/s1-maths/plan.md)).
- `s1-maths` Task 3: `app.fg` (per-item fermentability `full`/`normal`/`none`, attenuation from p. 108) and `app.abv` (Balling form via `sg_to_plato`) added to [`db/030_maths.sql`](db/030_maths.sql) (applied twice, both owned by `postgres`). `tests/test_maths.py`: 41 passed (full suite 293 passed); all 7 FG cells of table 4.3 within 0.002 and all 140 ABV cells of table 9.1 within 0.1 ([plan](docs/finished/s1-maths/plan.md)).
- `s1-maths` Task 2: [`db/030_maths.sql`](db/030_maths.sql) created with `app.calc_version()` (`maths-1`), SG/°P and SRM/EBC conversions, `gravity_points`, `og`, `preboil_volume` and `boil_gravity` (applied twice, 9 functions owned by `postgres`). `tests/test_maths.py`: 17 passed (full suite 269 passed), covering the Palmer DME, Short Stout (max yield, 73 %, US and metric) and Joe Ale examples, OBC Dubbel and Pils OG, and the p. 291 boil-gravity example ([plan](docs/finished/s1-maths/plan.md)).
- Wrote the doc → calc pass for `s1-maths` ([`docs/work/s1-maths/doc-calc.md`](docs/finished/s1-maths/doc-calc.md)): every formula with its *How to Brew* page, every worked example recomputed from the PDFs with its tolerance and test name, and the non-reproduction cases named (OBC Dubbel MCU slip 40.5 vs 43, OBC SRM and IBU as Daniels' model and untested, table 4.3 ABV row, table A.2, Port O' Palmer option 1, Mt Hood 20/30 min). Re-measured: the Balling ABV form fits 140/140 cells of table 9.1 (worst 0.088); `131.25 × ΔSG` misses 65, not 56. `calc_version` `maths-1` defined. No code yet.
- Planned `s1-maths` ([`docs/work/s1-maths/plan.md`](docs/finished/s1-maths/plan.md)): 8 tasks, all maths as `app.*` SQL functions in `db/030_maths.sql`. Source check of both PDFs: Palmer's gravity, IBU (all 160 cells of table 5.5), colour and FG examples reproduce; ABV uses the Balling form published by BYO, which matches all 140 cells of table 9.1 within 0.1 (`131.25 × ΔSG` misses 65); table 4.3's ABV row disagrees with table 9.1 and is not tested. OBC gives enough inputs for OG and MCU of both beers (its Dubbel MCU sum has an arithmetic slip, 40.5 not 43), but its SRM and IBU come from Daniels' tables, not Morey or Tinseth. The user's answer: OBC is tested for OG and MCU only, and its SRM and IBU are written up in `doc-calc.md` without a test (brief A2 narrowed).
- Finished the brief for `s1-maths` ([`docs/work/s1-maths/`](docs/finished/s1-maths/brief.md)): code location set from G0 (SQL functions in `db/*.sql`), functions take plain numbers, ABV, °Plato and pre-boil volume requirements added, *How to Brew* checked as the 4th edition (2017) with worked examples for gravity, IBU, colour and ABV. The user's answers: fixed tolerances (OG ± 0.001, FG ± 0.002, ABV ± 0.1, IBU ± 1, SRM ± 1); whirlpool and dry-hop IBU count as 0, with a cited model listed as a late-game follow-up under "Later" in [RECIPE-ROADMAP §8](docs/RECIPE-ROADMAP.md); water chemistry moved from P2 to M7 (P6); the user downloads the OBC *Recipe Formulation* PDF before planning, and its Dubbel and Bohemian Pils examples become tests.
- Shipped `m2-adjunct-role` ([`docs/work/m2-adjunct-role/`](docs/finished/m2-adjunct-role/plan.md), 2026-10-14): step 1 gives each wanted item a role (`feature` / `background`) and step 2 picks the specialty style from it; the English adjunct word rule is gone. Gate MET (clear 21/21, held-out 10/10, 34/34 consistent), G1 22/22, G2 22/22, `pytest` 252 passed, verification all 8 checks passed.
- `m2-adjunct-role` review fixes: recorded the 2026-10-14 step 1 retune (drinking remarks dropped, ingredient wishes to `wanted`) as a brief deviation, and reworded the specialty-style sentence in section 4 so only `feature` picks the specialty code ([review](docs/finished/m2-adjunct-role/review.md)). Docs only.
- `m2-adjunct-role` Task 9: G1 and G2 re-measured with the frozen prompt and the role-based step 2 (`evals.run --save --label m2-role`, [`evals/results/2026-10-14-m2-role.json`](evals/results/2026-10-14-m2-role.json)): step 1 22/22 (roles counted), step 2 22/22; b05 picks 15B with the 20C mismatch (alternatives 16A, 16B), b12 31B (alternative 18A), b19 17C, b17 8B. `pytest` 252 passed. §5 style-guide sentence and the 2026-10-13 known limitation updated; WORKFLOW-ROADMAP G1 and G2 Measured lines added. Plan: [`docs/work/m2-adjunct-role/plan.md`](docs/finished/m2-adjunct-role/plan.md).
- `m2-adjunct-role` Task 8: the adjunct word rule is gone. Removed `app.adjunct_cue` and `app.adjunct_is_prominent` from [`db/022_step2.sql`](db/022_step2.sql), added [`db/023_drop_adjunct_rule.sql`](db/023_drop_adjunct_rule.sql) (applied twice; `pg_proc` holds neither function), deleted their 24 tests and the word-rule column in `evals/roles.py`; the saved gate results keep their `word_rule` values. The grep finds only the two drop lines. `pytest` 252 passed. Plan: [`docs/work/m2-adjunct-role/plan.md`](docs/finished/m2-adjunct-role/plan.md).
- `m2-adjunct-role` Task 7: step 2 now picks the specialty style from the role. A wanted item with a specialty style for the guide and `role = feature` gives 31B (honey) with the base style as first alternative; `background` keeps the base, whatever cue words the request holds. The reason reads `... has the role "feature" in step 1's brief; base style ...`. `request` is read only for guide words (contract description updated). The word-rule functions were removed in Task 8. Suite: 276 passed. Plan: [`docs/work/m2-adjunct-role/plan.md`](docs/finished/m2-adjunct-role/plan.md).

### 2026-10-13
- `m2-adjunct-role` Task 6: role gate re-measured after one more prompt retune the user allowed (compounds like "X forward" go to `wanted`; a remark about how much the user will drink is no hint and no `unknown` wish) ([`evals/results/2026-10-14-m2-role-gate.json`](evals/results/2026-10-14-m2-role-gate.json), details in the plan's Gate result): **MET**. b12/b19 right every run; clear 21/21; same role in all 3 gated runs for 34/34 wordings; held-out 10/10. Hot runs (temperature 0.8, report only): clear 61/63, held-out 29/30, r05, r20 and h03 flipped. Word rule on the same set 28/31. Step 1 median 12.82 s (gated) against 12.5 s. G1 (`m2-role-g1`): step 1 22/22, step 2 22/22. The first attempt (Task 4 prompt) was NOT MET at clear 19/21 ([`2026-10-13-m2-role-gate.json`](evals/results/2026-10-13-m2-role-gate.json)). Task 7 not started, nothing deleted.
- `m2-adjunct-role` Task 5: wrote the role measurement tool [`evals/roles.py`](evals/roles.py) (`python -m evals.roles`): sends the measurement set through the real webhook at the gated (temperature 0, seed 42) and hot (0.8, seeds 1-3) settings, stops if step 1's logged temperature/seed differ from what was sent, scores the adjunct's role, and computes the R6 verdict; held-out wordings run only in a full run. 15 unit tests in `tests/test_roles.py`. Dry run on r01 and r15 (1 run, gated): both right, no error. `pytest` 273 passed.
- `m2-adjunct-role` Task 4: step 1's `wanted` items are now `{item, role}` objects (contract, prompt with `feature` / `background` definitions and a `background` default, `db/020_step1.sql` comment). Step 2 reads `w ->> 'item'` and still decides by the word rule. Live `evals.run --brief b12`: step 1 and step 2 pass, `wanted` logged as `[{"item": "honey", "role": "feature"}]` (single run, not the gate). `pytest` 258 passed.
- `m2-adjunct-role` Task 3: the test briefs carry expected roles (`wanted` entries are `{ item, role }`: b12 honey `feature`, the other six `background`), and `evals/grade.py` grades `wanted` on (item, role) pairs; a plain string or missing role counts as wrong. Grader and brief-shape tests updated, three new role tests. No live run yet (step 1 still returns the old shape until Task 4). `pytest` 250 passed.
- `m2-adjunct-role` Task 2: the webhook takes optional `temperature` and `seed` (defaults 0 and 42). They go through `Run settings`, step 1's input check and its Ollama options, and are logged in step 1's `input` and `llm`. Both workflows were changed in JSON, imported with `n8n import:workflow` and published (step 1 first). `evals.run.send()` can send them. New tests for the contract, the defaults and the 0.8 / 1 case; `pytest` 247 passed
- `m2-adjunct-role` Task 1: wrote the role measurement set [`evals/role_wordings.toml`](evals/role_wordings.toml) (21 clear, 3 ambiguous, 10 held-out wordings, labels as approved) with shape tests; the prompt test now also checks that no measurement wording is quoted. `pytest` tests/test_role_wordings.py and tests/test_prompt.py: 12 passed.
- Planned `m2-adjunct-role` ([`docs/work/m2-adjunct-role/plan.md`](docs/finished/m2-adjunct-role/plan.md)): 9 tasks; the role measurement and gate (Task 6) is a stop point before step 2 changes its decision or anything is deleted; 10 held-out wordings with expected roles written into the plan.
- Wrote brief for m2-adjunct-role ([`docs/work/m2-adjunct-role/`](docs/finished/m2-adjunct-role/brief.md)): step 1 gives each wanted item a role (`feature` / `background`) and step 2 reads it instead of the adjunct word rules, after a measurement gate on the D2 model.
- Shipped `m2-best-fit-style` ([`docs/finished/m2-best-fit-style/`](docs/finished/m2-best-fit-style/plan.md), 2026-10-13): step 2 picks the best-fit style with `app.step2_best_style` and runs in the pipeline. Verified (9 checks, `pytest` 235 passed, re-run on the branch before merge); G2 met, last measured at the third re-review fix (`--label m2-fix3`, [`evals/results/2026-10-13-m2-fix3.json`](evals/results/2026-10-13-m2-fix3.json): step 2 22/22; only a wording fix to the damper reach words came after). **Known limitation, decided by the user after verification:** step 2 judges whether an adjunct is prominent from hand-written word lists (cue, damper and joining words in `app.adjunct_cue`). This is to be replaced in a separate piece of work, where step 1 classifies each adjunct as feature or background. **Resolved by `m2-adjunct-role` (2026-10-14):** step 1 gives each wanted item a role and the word lists are gone.
- `m2-best-fit-style` third re-review fix (finding 19, note 20, 2026-10-13): "with" also ends a damper's reach, so "Honey forward with some citrus." stays prominent; finding-15 wordings still not prominent; comment above `app.adjunct_cue` fixed. `pytest` 235 passed; all 22 briefs right at SQL level, b12 still 31B ("shines"); G2 not re-run (no step 2 output changed).
- `m2-best-fit-style` second re-review fix (finding 15, 2026-10-13): the damper rule now checks both sides of the adjunct: a damper cancels prominence when it is in the same clause, within `DAMPER_GAP` words before or after, with no conjunction between. "honey that is subtle, with the hops up front" and "the honey should be subtle and the hops forward" are not prominent; the finding-12 wordings stay prominent; b12 still picks 31B ("shines"). `pytest` 233 passed; SQL level b01-b20 20/20 exact, b21 and b22 right; G2 re-run (`--label m2-fix3`, [`evals/results/2026-10-13-m2-fix3.json`](evals/results/2026-10-13-m2-fix3.json)): step 2 22/22, step 1 21/22 (b05 `hints`), briefs 0/22 (step 3 not built).
- `m2-best-fit-style` re-review fixes (findings 10-12): `NO_NAME_FACTOR` now applies only when choosing `alt_styles` (new `alt_total`); the pick, `unknown` and the mismatch use the plain total again, so "a 5% barleywine", "a 4% tripel", "an 8% kolsch", "a 4% doppelbock" and "an 8% berliner weisse" each get a pick plus the mismatch naming the requested style (regression tests); b05 picks 15B (lead back to about 0.05) with alternatives 16A and 16B, no pale lager. The reason quotes the user's word ("shines"), not the stem. A damper cancels prominence only when it comes before the adjunct (superseded by finding 15 above), in the same clause, within `DAMPER_GAP` words and with no conjunction between. `pytest` 227 passed; SQL level b01-b20 20/20 exact, b21 and b22 right; G2 re-run (`--label m2-fix2`, [`evals/results/2026-10-13-m2-fix2.json`](evals/results/2026-10-13-m2-fix2.json)): step 2 22/22, step 1 21/22 (b05 `hints`), briefs 0/22 (step 3 not built).
- `m2-best-fit-style` review fixes (findings 1-4): A4's catch-all example is now a smoke porter (the pastry stout example used items not in the database); the SQL bar test checks the picked style like the G2 grader; `NO_NAME_FACTOR = 0.5` stops numbers and hint words alone from ranking unrelated styles when the name matches some style (b05: 3A falls from 2.07 to 1.03, alternatives are now 16A and 16B), and the mismatch's named style must contain every named word (b21 with BJCP only no longer names 12C); prominence cues match word forms and a damper only counts near the adjunct. `pytest` 215 passed; SQL level b01-b20 20/20 exact, b21 and b22 right; G2 re-run on the real pipeline (`--label m2-fix`, [`evals/results/2026-10-13-m2-fix.json`](evals/results/2026-10-13-m2-fix.json)): step 2 22/22, step 1 21/22 (b05 `hints`), briefs 0/22 (step 3 not built).
- `m2-best-fit-style` Task 7: G2 measured on the real pipeline (`evals.run --save --label m2`, D2 model, [`evals/results/2026-10-13-m2.json`](evals/results/2026-10-13-m2.json)): step 2 22/22 (b01-b20 20/20, bar 18/20; b21 and b22 right); b05 15B with the 20C mismatch, b12 31B (alternative 18A), b19 17C. Step 1 21/22 (b05 `hints` wrong, step 2 unaffected). No constant tuned. Step 3 not built, so briefs 0/22 overall. §5 style-guide paragraph rewritten to the rule as built; WORKFLOW-ROADMAP G2 Measured line added.
- `m2-best-fit-style` Task 6: the pipeline runs step 2 and logs it. New sub-workflow `Step 2 · best-fit style` (input check, one `Score styles` SQL call, output check, no writes), published before the pipeline; `Recipe pipeline` gained `guide` in `Run settings` and the step 2 block (input, call with an error output, log ok / log failure, `failed_step: 2`). Edited through the n8n MCP except the pipeline's step 2 call: the MCP drops `onError`, so the pipeline was changed in its JSON and imported with `n8n import:workflow`, then published. Measured: a null `guide_preference` was lost between the workflows (`required property` error) until the sub-workflow read it with `?? null`; after that run 829 logged step 2 with `guide_preference: null`. New tests `test_step_2_logged`, `test_guide_setting_reaches_step_2`, `test_bad_guide_fails_at_step_2`; `pytest` 206 passed.
- `m2-best-fit-style` Task 5: `app.step2_best_style` in [`db/022_step2.sql`](db/022_step2.sql) picks the style, with step 2's contracts updated
  (`request`, `reason`, null `guide_preference`). User decisions: the number score has a general tightness bonus (a 4 % imperial stout now
  gives 15B, not 16A), and a BA style paired with a BJCP catch-all keeps the BA style (pastry stout stays BA, not 30D; style guidance
  is a help to pick resources, not strict). Measured at SQL level: b01-b20 20/20 hit, b21 and b22 right, b05 15B with mismatch 20C,
  b12 31B (alt 18A), b19 17C, b17 8B; applied twice, owned by `postgres`; `pytest` all passed.
- `m2-best-fit-style` Task 4: step 2's signals are ten tested SQL functions in [`db/022_step2.sql`](db/022_step2.sql)
  (name match, number fit, hint and unknown words, tags, adjunct prominence, guide named in the request, alias and specialty lists
  with a source per row; applied twice, owned by `postgres`). `tests/test_step2_signals.py` has 25 stack tests; `pytest` 180 passed.
- `m2-best-fit-style` Task 3: the decided pairs are a versioned SQL list, `app.style_pair()` in [`db/021_style_pairs.sql`](db/021_style_pairs.sql)
  (151 pairs, one per line with a name comment; applied twice, owned by `postgres`). `tests/test_style_pairs.py` (3 stack tests)
  checks the codes exist, each BA style is paired once, and the list equals the paired rows of `style-pairs.md`; `pytest` 155 passed.
- `m2-best-fit-style` Task 2: Claude read the full BJCP 2021 and BA 2026 guideline content in `ref.beer_style` and decided which
  BA styles pair with a BJCP style: by look, aroma and taste, vitals only vetoing when the ABV or IBU ranges don't overlap; names
  not used. The user delegated the decision (2026-10-13, no row review); the name-matching `loaders/style_pairs.py` and its tests
  were removed. [`style-pairs.md`](docs/finished/m2-best-fit-style/style-pairs.md): 169 BA styles, 151 paired, 18 unpaired (b21's
  and b22's BA styles unpaired on purpose).
- `m2-best-fit-style` Task 1: added briefs b21 (session IPA, BA `session-india-pale-ale`) and b22 (Mexican amber lager,
  BA `mexican-style-amber-lager`); `tests/test_recipe_briefs.py` now expects 22 briefs and reads codes from both guides. 39 passed in the
  brief, grade and run tests.
- Planned `m2-best-fit-style` ([`docs/finished/m2-best-fit-style/plan.md`](docs/finished/m2-best-fit-style/plan.md)).
- Shipped `m1-read-request` ([`docs/finished/m1-read-request/`](docs/finished/m1-read-request/)): step 1 reads the request with
  one Ollama call checked by SQL, D2 decided (Qwen3.8-27B UD-Q6_K, thinking off). Verified: 8 checks, `pytest` 151 passed;
  merged to `main`.
- `m1-read-request` review fixes: `--save` stores the prompt and contract sha256 per configuration (the
  7 saved ones were backfilled with the hashes `benchmark.md` records as checked before and after), a stray `|` in
  `docs/DATABASE.md` and the stale Delivery workflow row here are fixed ([`review.md`](docs/finished/m1-read-request/review.md)).
- `m1-read-request` Task 7: D2 decided (user): `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K`, thinking off, is the
  step 1 default (`Recipe pipeline` `Run settings`, the `Test data` samples and `tests/test_workflows.py`).
  Why: quality first, only configuration family that met the bar, thinking on gave no gain at about 8x
  the time ([`benchmark.md`](docs/finished/m1-read-request/benchmark.md)). Workflows published and
  re-exported; `pytest` 150 passed with the stack up on the new default. D2 moved from §7 to §4.
- `m1-read-request` Task 6: D2 benchmark measured, 7 configurations x 3 runs x 20 briefs, same prompt and
  contract hash ([`benchmark.md`](docs/finished/m1-read-request/benchmark.md)). Bar 19/20 in every run:
  `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K` meets it with thinking off (12.5 s median, 36%/64% CPU/GPU)
  and with thinking on (96.7 s median); others below (qwen3.8:27b 18/20, gemma4:12b-it-q8_0 and
  gemma4:31b-it-qat 17/20, gemma4:12b 16/20, gemma4:26b-a4b-it-qat 12-13/20). Remaining misses:
  b05 `hints` ("session" inferred) and, with thinking on, b08 `wanted` ("noble-type hop"). D2 stays open
  until Task 7 chooses. Three models pulled (about 53 GB).

### 2026-10-12
- `m1-read-request` Task 5: `evals/benchmark.py` runs one model configuration (unload all, load at
  `num_ctx` 8192, read the CPU/GPU split from `ollama ps`, run the 20 briefs N times through the
  pipeline, summarise per-field accuracy, median/p90 LLM time, retries; `--save` merges into
  `evals/results/<date>-m1-benchmark.json` with prompt and contract sha256; `--table` prints the
  markdown table). `evals/run.py` gained `--think`, `--timeout` and keeps step 1's `llm`. Suite:
  150 passed. Dry run, `gemma4:12b` no-think, 1 run: 16/20 right, 100% GPU, median 1.6 s, p90 2.2 s,
  1 retry (not the benchmark; Task 6 does that). The dry run left 20 more `app.run` / `app.brief` rows.
- `m1-read-request` Task 4: step 1 is real. `Step 1 · read request` reads `shared/prompts/step1.system.md`
  and the output contract, calls Ollama `/api/chat` (HTTP Request; contract as `format`, temperature 0,
  seed 42, `num_ctx` 8192), checks the answer with `app.step1_read_answer` and retries once with the
  error list; a second failure stops with `step 1 answer failed twice: try 1: ...; try 2: ...`. The
  pipeline passes `model` / `think`, logs tokens and `run_step.llm`, and saves `app.brief` and
  `app.run.brief_id`. Measured: an Execute Workflow node runs the **published** version of the
  sub-workflow, not the draft (a pipeline run against the old published stub failed its step 1
  input check). Retry wiring tested through MCP `test_workflow` (executions 2820: `tries = 2` with
  `first_errors`; 2823: stops naming both tries). Smoke pass on `gemma4:12b-it-q8_0`, 20 briefs, 20
  finished runs: step 1 15/20 on the first prompt, 17/20 after two general wording changes (hints only
  from words the user wrote; numbers matched to their unit); prompt frozen. `.venv/bin/pytest`: 143
  passed. Plan: [`docs/finished/m1-read-request/plan.md`](docs/finished/m1-read-request/plan.md).
- `m1-read-request` Task 3: `db/020_step1.sql` adds `app.step1_read_answer(request, content,
  contract)` (parse, drop repeated words, contract check, every `stated` number must be written in
  the request); `app.brief.profile_id` is nullable and `app.run_step.llm` exists (both SQL files
  applied twice on the stack); the step 1 output contract gains `uniqueItems` and `maxItems`.
  `.venv/bin/pytest`: 135 passed. Plan: [`docs/finished/m1-read-request/plan.md`](docs/finished/m1-read-request/plan.md).
- `m1-read-request` Task 2: `evals/grade.py` grades `named` and compares ingredient words after
  normalising (case, accents, hyphens, spacing) and a two-pair naming-synonym list; a form word
  is never dropped (`rice` != `flaked rice`). `.venv/bin/pytest -m "not stack"`: 100 passed.
  Plan: [`docs/finished/m1-read-request/plan.md`](docs/finished/m1-read-request/plan.md).
- `m1-read-request` Task 1: the 20 recipe briefs gain `named` (the style words the user wrote) and
  hold ingredient words as the user wrote them (b02 `oats`, b06/b16 `rice`, b07 `corn`, b10
  `dark candi sugar`, `abbey yeast`); `test_words_are_the_users` checks it. Suite without stack:
  95 passed.
- Approved brief and planned `m1-read-request` ([`docs/finished/m1-read-request/`](docs/finished/m1-read-request/),
  [plan](docs/finished/m1-read-request/plan.md)): step 1 reads the request with one Ollama call
  (JSON schema in `format`, temperature 0, seed 42), one SQL check (contract + no invented
  numbers) and one retry; the brief is saved in `app.brief`; the grader keeps the user's own
  ingredient words (`rice` ≠ `flaked rice`) and grades a new `named` field; the D2 benchmark
  runs six models with thinking off, then the best with thinking on. Measured while planning:
  Ollama enforces `maxItems` but not `uniqueItems` in `format`; without a cap, `gemma4:12b`
  with thinking on repeated one hint until the 8K context ran out.
- Shipped `m0-harness` ([`docs/work/m0-harness/`](docs/finished/m0-harness/)): G0 decisions, the eval
  harness (`evals/`), `app.run` / `app.run_step` logging with `pg_jsonschema`, 8 contracts in
  `shared/contracts/`, and three published n8n workflows exported to `n8n/workflows/`, each with
  a `Test data` note. Verified 12/12 checks and 122 tests (94 without the stack); regression
  suite re-run on the branch before merging. Shipped without republishing or re-exporting
  `Recipe pipeline`; the 8 px note-position drift from the user's pin stays as recorded in
  verification.md.
- `m0-harness` task 8: each workflow has a `Test data` sticky note with ready-to-paste JSON
  (b01's request; the pipeline sample uses `brief_id: "editor-b01"`). The user pins it in the
  editor; nothing is pinned yet. All three workflows were republished (`versionId ==
  activeVersionId` for each) and re-exported. The pipeline sample ran once through MCP
  `execute_workflow` (manual): execution 2665 `success`, step 1 returned the stub output with
  `wanted[0]` = b01's request, sub-executions 2666 (step 1) and 2667/2668 (Check contract) ran;
  one `app.run` `editor-b01` (`ok`, finished, one step 1 row `ok`) was then deleted. New tests:
  3 note checks, 3 contract checks, `test_webhook_ignores_pin`; `pytest` 122 passed, `-m "not
  stack"` 94 passed. All tasks done; review is next.
- Revised plan `m0-harness` (docs/work/m0-harness/plan.md): Task 8 adds a `Test data` sticky
  note with ready-to-paste JSON (b01's request) to each n8n workflow; the user pins it and runs the
  workflow in the editor. Pipeline editor runs are logged as `eval_id = 'editor-b01'`. Scope
  change agreed by the user before shipping; re-review and re-verify follow.
- `m0-harness` review fixes: tests now fail if the runner counts a failed or unfinished run as
  passed (checked by mutating `evals/run.py`); `totals()` reports step 1 `not_run`; the test skip
  check reuses `loaders.db.connect`; plan deviations recorded; §4 Scripts test count corrected.
- `m0-harness` task 7: `evals/run.py` sends each brief to the pipeline webhook, reads the run
  back from `app.run` / `app.run_step`, grades it and prints the table and totals
  (`python -m evals.run [--brief b01] [--model NAME] [--save --label m0]`). **G0 result
  (measured):** the saved 20-brief run `evals/results/2026-10-12-m0.json` is red as designed: every
  run finished ok with one step 1 row (20/20), step 1 0/20, steps 2 and 3 0/20 (20 not run
  each), briefs 0/20, exit code 1. `tests/test_run.py` has 3 tests (2 unit, 1 stack: an empty
  request is reported failed with `step1.input`). All tasks of `m0-harness` are done; review is next.
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
- Planned `m0-harness` ([`docs/work/m0-harness/plan.md`](docs/finished/m0-harness/plan.md)): 7 tasks.
  Record the G0 decisions and add a `stack` test marker; add the run-log columns and
  `pg_jsonschema`; JSON Schema contracts for steps 0–3 in `shared/contracts/`; pure graders;
  workflow export to `n8n/workflows/`; the `Recipe pipeline` webhook with a step 1 stub and run
  logging; the eval runner and the G0 baseline run. Nothing built yet.
- Wrote draft briefs for all 13 WORKFLOW-ROADMAP work items in `docs/work/` (none approved, no
  branches yet): [`m0-harness`](docs/finished/m0-harness/brief.md),
  [`m1-read-request`](docs/finished/m1-read-request/brief.md),
  [`m2-best-fit-style`](docs/finished/m2-best-fit-style/brief.md),
  [`m3-deviations`](docs/work/m3-deviations/brief.md),
  [`m4-targets-blueprint`](docs/work/m4-targets-blueprint/brief.md),
  [`m5-choose-ingredients`](docs/work/m5-choose-ingredients/brief.md),
  [`m6-compute-validate`](docs/work/m6-compute-validate/brief.md),
  [`m7-process`](docs/work/m7-process/brief.md),
  [`m8-recipe-sheet-chat`](docs/work/m8-recipe-sheet-chat/brief.md),
  [`s1-maths`](docs/finished/s1-maths/brief.md), [`s2-corpus`](docs/work/s2-corpus/brief.md),
  [`s3-style-fit`](docs/finished/s3-style-fit/brief.md), [`s4-books-kb`](docs/finished/s4-books-kb/brief.md).
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
