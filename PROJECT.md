# AI Homebrew Assistant — Project Description

> **This file is the single source of truth for the project:** why it exists, what it
> is trying to do, how it is built, and how far along it is. If code and this file
> disagree, one of them is wrong. Fix it, and record the fix in the [Progress log](#8-progress-log).
>
> Last updated: **2026-10-10**

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
| Database | **Supabase** (self-hosted Postgres 15) | Knowledge base, reference data (styles, ingredients), recipes | 🟢 running again since 2026-10-09 ([`recover-stack`](docs/finished/recover-stack/plan.md)); `ref` schema rebuilt: 7 tables owned by `postgres` (2026-10-09, [`ref-schema`](docs/finished/ref-schema/plan.md), shipped); 11 `ref.source` rows, the 2 `malts.json` sources replaced by 4 malt sources plus a `user-supplied` source for hand-entered figures, and `ref.fermentable.field_source` added (2026-10-09, [`malt-loader`](docs/finished/malt-loader/plan.md), shipped); `ref.beer_style` has 285 rows, BJCP 2021 116 + BA 2026 169 (2026-10-09, [`style-loader`](docs/finished/style-loader/plan.md), shipped); `ref.fermentable` has 74 rows with 74 `ref.ingredient` rows (2026-10-09, [`malt-loader`](docs/finished/malt-loader/plan.md), shipped); `hop`, `yeast` and `water_salt` are empty |
| Vector search | **pgvector** (HNSW) + Postgres full-text, fused (hybrid RAG) | Retrieval over book chunks | ⬜ schema not rebuilt |
| Orchestration | **n8n** (with its own Postgres for metadata) | Ingestion and recipe pipelines, agent | 🟢 running, no workflows |
| Document parsing | **Docling Serve** (ROCm) | PDF → structured Markdown + `HybridChunker` | 🟢 running |
| LLM runtime | **Ollama** (ROCm) | Local chat and embedding models | 🟢 running |
| Chat model | `gemma4:12b-it-q8_0` *(also pulled: `qwen3.8:27b`)* | Reasoning, extraction, recipe drafting | ⚠️ to be re-evaluated (§7) |
| Embedding model | `bge-m3` (1024-dim) | Chunk and query embeddings | 🟢 pulled |
| Web search | **SearXNG** + `webarm` service | Lookups for what the books do not cover | 🔴 `searxng` down since 2026-10-08 (`settings.yml` lost in the reset, [`OPERATIONS.md`](docs/OPERATIONS.md) §1); recovery is separate work, not started. `webarm` running. Optional |
| Scripts | Python (`.venv`), `psycopg` 3, `pytest` (`requirements.txt`) | One-off extract/load jobs, evals | 🟡 `loaders/` package: shared helpers in `loaders/common.py` (8 unit tests pass) and DB helpers in `loaders/db.py` (`connect`, `source_id`, `upsert_ingredient`, checked against the running DB) (2026-10-09, [`ref-schema`](docs/finished/ref-schema/plan.md), shipped); styles loader `loaders/styles.py` (`python -m loaders.styles --bjcp PATH --ba PATH`, 4 unit tests pass) (2026-10-09, [`style-loader`](docs/finished/style-loader/plan.md), shipped); hopline fetcher `loaders/fetch_hopline.py` (malts: `python -m loaders.fetch_hopline OUT.json`; hops with `--hops`, added 2026-10-10 in [`hop-loader`](docs/work/hop-loader/plan.md); 4 unit tests pass) and malt loader `loaders/malts.py` with the SKU map `loaders/malt_products.py` (`python -m loaders.malts --hopline PATH --catalogue PATH`, 9 unit tests pass) (2026-10-09, [`malt-loader`](docs/finished/malt-loader/plan.md), shipped) |
| Dev tooling | Claude Code: Supabase MCP (read-only, `.mcp.json`), official n8n MCP (local scope) + `n8n-skills` plugin, guard hook (`.claude/hooks/guard.sh`) | Building and inspecting the stack; schema changes go through SQL files applied as `postgres` | 🟢 |
| Delivery workflow | Project skills `dev-flow` (orchestrator) + `dev-brief`, `dev-plan`, `dev-implement`, `dev-review`, `dev-verify`, `dev-ship` (`.claude/skills/`) | Brief → plan → build → review → verify → merge, one subagent per step, work in `docs/work/<slug>/` | 🟢 in use; shipped: [`recover-stack`](docs/finished/recover-stack/plan.md), [`ref-schema`](docs/finished/ref-schema/plan.md), [`style-loader`](docs/finished/style-loader/plan.md) (2026-10-09) |
| Eval guidance | Project skills `retrieval-evaluation-metrics`, `rag-evaluation-frameworks` (`.claude/skills/`) | Reference for building the retrieval test set and regression gate (§6.6) | 🟢 installed, not yet used |

**Hardware:** Ryzen 9 9900X · Radeon RX 9070 XT (16 GB VRAM, RDNA 4 / gfx1201) · 32 GB RAM.

---

## 5. Knowledge sources

Not ingested since the reset. On 2026-10-08 the source files were removed from `shared/rag-files/pending/` on purpose, to be re-added as each loader needs them. Now there: `how_to_brew.pdf`, `styles.json`, `ba_styles.json`, `hopline_malts.json`, `malt_catalogue.json` and `hopline_hops.json` (fetched 2026-10-10), plus the no longer used `malts.json` (checked 2026-10-10). The three malt catalogue PDFs are read from `~/Downloads`.

| Source | Type | Feeds | Status |
|---|---|---|---|
| *How to Brew* — John Palmer | PDF book | General process, ingredients, maths | ⬜ |
| *Water* — Palmer & Kaminski | PDF book | Water chemistry | ⬜ |
| *Yeast* — White & Zainasheff | PDF book | Yeast and fermentation | ⬜ |
| Malt data: hopline.hu malt list (`hopline_malts.json`) + Weyermann (Crop 2026), Viking Malt (2023), Simpsons (Nov 2025) catalogues (`malt_catalogue.json`) | Structured (fetched pages + hand-built from the PDFs) | Fermentable catalogue, 74 malts | ✅ loaded into `ref.fermentable`: 74 rows (Weyermann 37, Viking 32, Simpsons 5), 73 with EBC, 74 with potential, 62 with `max_pct` (2026-10-09) |
| Stout Style Guide | PDF | Stout styles and recipes | ⬜ |
| BYO pastry stouts | Markdown | Adjunct technique | ⬜ |
| Draught Beer Quality Manual 2019 | PDF | Serving and dispense | ⬜ |
| BJCP 2021 style guidelines (`styles.json`) | Structured | Styles, 116 rows | ✅ loaded into `ref.beer_style`: 116 rows, 96 with vitals (2026-10-09) |
| Brewers Association style guidelines (`ba_styles.json`) | Structured | Styles, 169 rows | ✅ loaded into `ref.beer_style`: 169 rows, 144 with OG (2026-10-09) |
| Hop data (`hops.json`, `hops.hopslist.json`), fault data (`beer_faults.json`) | Structured | Hop catalogue (72 + 268), faults (21) | ⬜ |
| Brewer's Friend recipes (Kaggle, CC0) | Structured, 179,455 recipes | Per-style ratios (D7) | ⬜ 35,620 (views > 500) in the archive dump, measured 2026-10-08 |
| Brewtarget default data (GPL-3) | Structured, BeerJSON | Yeast (296 + 275 entries), hops (282) (D8) | ⬜ downloaded before the reset (`DefaultContent003/004`), to be re-added |
| AHA recipe-design crash course · Oregon Brew Crew recipe formulation · BJCP exam study guide | Free web / PDF | Design method, rules of thumb, output checklist | ⬜ candidate, not downloaded |

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
| D1 | Which style system is primary: BJCP, Brewers Association, or both? | BJCP 2021 as primary (the first build resolved styles against BJCP, classifying to the base style); BA as an alternative the user can pick | open |
| D2 | Chat model: keep `gemma4:12b` or move to `qwen3.8:27b` (fits 16 GB at Q4, slower)? | Benchmark both on the recipe test set before deciding | open |
| D3 | Where does the recipe pipeline live: n8n workflows, Postgres functions, or a Python service? | Undecided. The first build used n8n plus SQL and became hard to follow | open |
| D4 | Ingredient catalogue: what schema, and where does the data come from? | Schema designed in [`docs/DATABASE.md`](docs/DATABASE.md) §2 (one `ref.ingredient` table + one table per kind, tags, source per row). Data sources: D7, D8 | open |
| D5 | How the user interacts: chat UI, CLI, n8n chat trigger? | — | open |
| D7 | Where do the recipe ratios (grist %, hop split) come from? | Brewer's Friend corpus through automatic quality gates (no hand curation) → `corpus.style_profile`, thin styles shrunk toward their family, specialty styles use the base style, extra sources weighted (books, DIY Dog, own batches) ([`docs/STYLE-PROFILES.md`](docs/STYLE-PROFILES.md)) | open |
| D8 | Yeast data source | Brewtarget default data: 571 entries with attenuation and temperature ranges, GPL-3 (fine for a private install) | open |
| D9 | Who approves the extracted style sensory envelopes before they enter `ref`? | LLM extracts BJCP prose, code parses BA fields, the user reviews | open |

---

## 8. Progress log

Newest first. One entry per meaningful change: what was done, and why if that is not obvious.

### 2026-10-10
- `hop-loader` Task 1 ([`docs/work/hop-loader/plan.md`](docs/work/hop-loader/plan.md)):
  `loaders/fetch_hopline.py` now accepts non-numeric SKUs, reads each page's spec table
  (`spec_table`) and data block (`params`), and has a `--hops` mode that also saves the SKUs of
  hopline's aroma / bittering / dual listings. Ran it: 106 products in
  `shared/rag-files/pending/hopline_hops.json`, every name and spec table set; categories aroma
  101, bittering 60, dual 56. 4 fetcher tests pass, suite 25 passed.
- Planned `hop-loader` ([`docs/work/hop-loader/plan.md`](docs/work/hop-loader/plan.md)),
  re-scoped from three hop JSON files (`hops.json`, `hops.hopslist.json`, Brewtarget) to the
  hops hopline.hu sells: 106 products (measured 2026-10-10) = 85 varieties + 5 LUPOMAX + 16
  extra pack sizes, so 90 `ref.hop` rows, figures from hopline's pages only (source
  `hopline-hops`). User decisions: alpha from the spec table, the data block's `Alfasav` only as
  fallback; Delta and Lotus (pages show Falconer's Flight / Taurus) loaded with `NULL` figures;
  LUPOMAX as 5 separate hops. Nothing built yet.
- Wrote brief for `hop-loader` ([`docs/work/hop-loader/`](docs/work/hop-loader/brief.md)).

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
  [`docs/work/fill-ref/README.md`](docs/work/fill-ref/README.md), and the original plan was
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
