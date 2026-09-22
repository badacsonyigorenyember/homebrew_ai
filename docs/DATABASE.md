# The Postgres database

Every schema, every table, what is actually in it, and the **full chain** from the
table to the thing a user touches.

`measured` 2026-09-18 against the live `supabase-db` container. Row counts, sizes,
columns, foreign keys and grants come from the catalog. The chains come from two
mechanical sweeps, not from reading prose:

```bash
# which tables each function body actually names
docker exec supabase-db psql -U supabase_admin -d postgres -At -c "
select n.nspname||'.'||p.proname||' >> '||(
  select coalesce(string_agg(distinct m[1],', ' order by m[1]),'-')
  from regexp_matches(p.prosrc,'\m((?:kb|brew|ref|corpus|mem|obs|nlq)\.[a-z_0-9]+)','g') m)
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname in ('brew','corpus','kb','mem','obs','ref','nlq') order by 1;"
```

```bash
# which DB objects each workflow names, and which workflow calls which
grep -oE '\b(kb|brew|ref|corpus|mem|obs|nlq)\.[a-z_0-9]+' n8n/demo-data/workflows/*.json | sort -u
```

**How to read a chain.** `table → function() → workflow → entry point`. Arrows point
the way the *data* flows out, so the rightmost item is what a person sees. `⇐ writes`
marks the reverse direction.

---

## 1. The schemas

Seven schemas are this project's; the rest ship with Supabase. The split is the trust
boundary: `kb`/`ref` is *published* knowledge, `corpus` is *observed* practice, `brew`
is *the brewer's own* data, and `nlq` is the only one the agent's DB login can reach.

| Schema | Tables | Rows | On-disk | What it holds | Written by | Reaches the user through |
|---|---|---|---|---|---|---|
| `kb` | 5 | 5 943 | ~170 MB | Ingested books, articles and datasheets, chunked and embedded | `wf1-ingest-book`, 5 structured `ingest-*`, `hopslist_load.py` | `nlq.search_knowledge()` → `wf-step-retrieve` → `chat-agent` |
| `ref` | 4 | 651 | ~2.9 MB | Structured *published* reference: styles, malts, hops, faults | the structured `ingest-*` workflows, `db/init/26` | `ref.f_style_bands()` → `cap-formulate-recipe`; and as generated cards in `kb.chunks` |
| `corpus` | 9 (+2 views) | 1 935 375 | ~430 MB | 174 554 scraped homebrew recipes (brewersfriend, CC0) | `scripts/ingest/corpus_load.py` | `nlq.common_practice()` → `wf-step-practice` → `chat-agent`; `nlq.find_exemplars()` → `cap-formulate-recipe` |
| `brew` | 7 | 1 138 | ~740 kB | The brewer's own catalogue, recipes, batches, tasting notes | `brew.f_save_recipe()`, `db/init` seeds | `brew.f_catalogue()` / `brew.f_compute_recipe()` → `cap-formulate-recipe` → `chat-agent` |
| `obs` | 5 | 1 241 | ~1.1 MB | Run/step tracing, prompt registry, model profiles, retrieval log | `obs.f_start_run/f_log_step/f_finish_run/f_log_retrieval` | `obs.f_step_config()` → `wf-step-llm` (config); `scripts/stress/*.py` (analysis) |
| `mem` | 3 | 734 | ~630 kB | Conversation turns; the (unused) learned-preference store | `chat-agent`, `mem.f_save_memory()` | `scripts/stress/grounding_eval.py`, `recipe_eval.py` |
| `nlq` | 1 matview | — | — | **The agent's entire read surface** — 13 functions over the four schemas above | `nlq.f_refresh_corpus_lexemes()` ⇐ `wf1-ingest-book` | every agent tool, via `n8n_agent` |
| `public` | 1 | 1 352 | 1.9 MB | n8n's own LangChain chat-memory table. Not ours — §9 | n8n Postgres Chat Memory node | n8n internals only |

Stock Supabase schemas — `auth` (23 tables), `storage` (10), `supabase_migrations`,
plus `realtime`/`vault`/`graphql*` — are unused. Nothing in `db/init/` writes them and
no workflow reads them; they exist because GoTrue and storage-api are running.

---

## 2. The call graph

Everything below hangs off five entry points.

### 2.1 The chat path — `chat-agent` (webhook)

`chat-agent` is an AI Agent node with exactly four tools. Every answer a user gets
comes through one of these four branches.

```
chat-agent  (POST /webhook/<id>/chat)
│   reads  obs.profiles           → which model to run
│   reads  obs.f_session_chunk_ids() → obs.retrievals  (what this session already saw)
│   writes mem.chat_turns
│
├── tool: search_brewing_knowledge
│     └── wf-step-retrieve-multi          (splits the question into parts)
│           └── wf-step-retrieve          ×N, one per part
│                 ├── nlq.corpus_vocabulary_gap() → kb.chunks, kb.document_versions,
│                 │                                  nlq.corpus_lexemes
│                 ├── nlq.search_knowledge()      → kb.chunks, kb.chunk_embeddings,
│                 │                                  kb.documents, kb.document_versions,
│                 │                                  nlq.corpus_lexemes
│                 ├── kb.documents                 (direct, for the citation header)
│                 └── obs.f_log_retrieval()       ⇒ obs.retrievals
│
├── tool: brainstorm_pairing
│     └── cap-brainstorm-pairing
│           ├── obs.f_start_run()  ⇒ obs.runs
│           ├── Step 1 parse    → wf-step-llm
│           ├── Step 2a/2b      → wf-step-retrieve   (anchor + technique)
│           ├── Step 3 propose  → wf-step-llm
│           ├── Step 5 compose  → wf-step-llm
│           └── obs.f_finish_run() ⇒ obs.runs
│
├── tool: formulate_recipe
│     └── cap-formulate-recipe
│           ├── obs.f_start_run()          ⇒ obs.runs
│           ├── brew.f_catalogue()          → brew.ingredients
│           ├── brew.f_resolve_request()    → brew.ingredients, corpus.recipe_search,
│           │                                 nlq.f_resolve_ingredient_loose,
│           │                                 nlq.ingredient_practice
│           ├── ref.f_style_bands()         → ref.styles
│           ├── nlq.find_cohort()           → nlq.f_cohort_ids → corpus.recipe_search
│           ├── nlq.find_exemplars()        → corpus.recipe_* (all five)
│           ├── nlq.cohort_stats()          → corpus.recipe_*, ref.f_range_text
│           ├── nlq.ingredient_practice()   → corpus.recipe_misc, corpus.recipes
│           ├── Step 1/3/3b/4 → wf-step-llm  (parse, propose, re-propose, compose)
│           ├── brew.f_compute_recipe()      → brew.ingredients
│           ├── brew.f_fit_ibu() / f_fit_to_abv() → brew.f_fit_recipe → f_compute_recipe
│           ├── brew.f_save_recipe()         ⇒ brew.recipes, brew.recipe_items
│           └── obs.f_finish_run()           ⇒ obs.runs
│
└── tool: common_practice
      └── wf-step-practice
            └── nlq.common_practice() → corpus.recipes, corpus.recipe_fermentables,
                                         corpus.recipe_hops, corpus.recipe_misc,
                                         corpus.recipe_yeasts, nlq.f_corpus_styles
```

Every `wf-step-llm` call expands to:

```
wf-step-llm
  ├── obs.f_step_config(profile, prompt_name) → obs.profiles, obs.prompts
  ├── (Ollama HTTP call)
  └── obs.f_log_step()                        ⇒ obs.steps
```

⛔ `chat-agent` and `wf-step-retrieve` have `settings.availableInMCP = false`, so they
must be edited via tracked JSON + `n8n import:workflow` — which deactivates them and
drops the webhook registration. Probe the webhook before trusting any chat-driven test.

### 2.2 The ingest path — two families

**Book launchers** (`ingest-draught`, `-how-to-brew`, `-malt`, `-pastry-stouts`,
`-stout-guide`, `-water`, `-yeast`) are two nodes: a manual trigger and an
`executeWorkflow` into `wf1-ingest-book`. They only set parameters.

```
ingest-<book>  →  wf1-ingest-book
                    ├── docling-serve  POST /v1/chunk/hybrid/file/async → poll → result
                    ├── ⇒ kb.documents, kb.document_versions, kb.chunks
                    ├── Ollama embed  ⇒ kb.chunk_embeddings
                    ├── kb.promote_version()  → kb.chunks, kb.chunk_embeddings,
                    │                            kb.document_versions  (gate: missing = 0)
                    ├── nlq.f_refresh_corpus_lexemes() ⇒ nlq.corpus_lexemes
                    └── nlq.corpus_vocabulary_gap()     (post-ingest check)
                    └── ⇒ kb.ingest_log at every stage
```

**Structured ingests** (`ingest-bjcp-styles`, `-ba-styles`, `-beer-faults`,
`-hop-varieties`, `-study-guide`) are standalone and run the **D32 contract**: load the
structured source into `ref.*`, then *generate* the narrative cards in `kb.chunks`
**from those `ref` rows**, so the two cannot drift.

```
ingest-bjcp-styles  (manual)
  ├── Upsert style rows        ⇒ ref.styles
  ├── Ensure KB doc + version  ⇒ kb.documents, kb.document_versions
  ├── Demote + clear old cards ⇒ kb.chunks
  ├── Generate style cards     : ref.styles ──► kb.chunks     ← the D32 join
  ├── Ollama embed             ⇒ kb.chunk_embeddings
  ├── kb.promote_version()
  └── Log run summary          ⇒ kb.ingest_log
```

`ingest-hop-varieties` does the same with `ref.hops` + `ref.f_range_text()`;
`ingest-beer-faults` with `ref.faults`.

### 2.3 The corpus path — CLI only

```
scripts/ingest/corpus_load.py
  ├── ⇒ corpus.recipes, corpus.recipe_fermentables, corpus.recipe_hops,
  │      corpus.recipe_misc, corpus.recipe_yeasts
  ├── corpus.f_rebuild_dims()   ⇒ corpus.fermentables, hops, miscs, yeasts
  ├── corpus.f_rebuild_styles() ⇒ corpus.styles   (reads ref.styles for the bridge)
  └── corpus.f_rebuild_search() ⇒ corpus.recipe_search
```

Nothing in n8n writes `corpus`. It is loaded once from the CLI and read forever after.

### 2.4 Side paths

| Entry point | Chain |
|---|---|
| `scripts/ask.sh` | `nlq.search_knowledge()` → `kb.*` — retrieval without the agent, for debugging |
| `scripts/ingest/hopslist_load.py` | ⇒ `ref.hops`, then generates cards ⇒ `kb.documents`/`document_versions`/`chunks`/`chunk_embeddings` → `kb.promote_version()`; also reads `corpus.hops` |
| `scripts/ingest/hops_extract.py`, `hopslist_extract.py`, `sg_extract.py`, `ba_extract.py` | PDF/HTML → JSON destined for `ref.hops` / `ref.styles`. No DB write of their own |
| `services/webarm/webarm.py` | SearXNG → fetch → docling → bge-m3 → rank. Returns `kb.chunks`-shaped rows to `wf-step-retrieve` **without writing them** — the web arm is not the corpus |
| `wf-step-retrieve-keywords` | `nlq.corpus_coverage()` + `nlq.corpus_vocabulary_gap()` → `kb.chunks`, then `wf-step-retrieve`. ⚠️ Untracked in git as of this writing |

### 2.5 The eval paths

Evals deliberately read `obs`/`mem`, not the chat transcript.

| Script | Chain |
|---|---|
| `grounding_eval.py` | drives the `chat-agent` webhook → then reads `mem.chat_turns`, `obs.f_session_chunk_ids()` → `obs.retrievals`, `kb.chunks`, and checks claims against `ref.styles` / `ref.hops` / `ref.faults` + `nlq.corpus_vocabulary_gap()` |
| `recipe_eval.py` | `obs.f_start_run()` → drives `cap-formulate-recipe` → reads `obs.runs`, `obs.steps`, `obs.retrievals`, `brew.recipes`, `brew.recipe_items`, `brew.f_catalogue()`, `brew.f_abv()`, `mem.chat_turns` |
| `tier1_routing.py`, `tier2_e2e.py`, `decompose_eval.py` | n8n-level only; no direct DB access |

---

## 3. `kb` — the knowledge base

Why it exists: the assistant must answer from books it can cite, not from model
weights. Every chunk traces to a document version, and every version records the
Docling build and chunker config that produced it, so a chunk's origin is reproducible.

⛔ The table comment on `kb.chunks` is a real architectural rule: **knowledge only —
never insert data derived from `brew.*`**. The brewer's own beers are not knowledge.

| Table | Rows | Size | What kind of data | Written by | Read by — full chain |
|---|---|---|---|---|---|
| `kb.documents` | 13 | 80 kB | One row per source work: `slug`, `title`, `doc_type` (book/article/datasheet/style_guide), `authority` (reference/guideline/practitioner), `authors[]`. `authority` is what lets retrieval rank a guideline above a blog post | `wf1-ingest-book`, 5 structured `ingest-*`, `hopslist_load.py` | `nlq.search_knowledge()` → `wf-step-retrieve` → `wf-step-retrieve-multi` → `chat-agent`<br>`nlq.search_knowledge()` → `wf-step-retrieve` → `cap-brainstorm-pairing` / `cap-formulate-recipe` → `chat-agent`<br>`nlq.search_knowledge()` → `scripts/ask.sh`<br>direct → `wf-step-retrieve` (citation header) |
| `kb.document_versions` | 14 | 160 kB | Provenance for one ingest of one file: `version`, `file_sha256`, `docling_version`, `chunker_config`, `page_count`, `image_dir`, `is_current`. The version+config pair is why **anything destined for `kb.*` must go through docling-serve** | same as above | `nlq.search_knowledge()` → `wf-step-retrieve` → `chat-agent`<br>`nlq.corpus_vocabulary_gap()` → `wf-step-retrieve` / `wf-step-retrieve-keywords` / `cap-*` / `wf1-ingest-book` / `grounding_eval.py`<br>`nlq.corpus_coverage()` → `wf-step-retrieve-keywords`<br>`kb.promote_version()` → every ingest workflow (the gate) |
| `kb.chunks` | 2 946 | 125 MB | The retrievable unit. `content` is embedded, `raw_content` is shown to the user, `heading_path[]` + `page_from/to` are the citation, `image_refs[]` the figures. `fts` is a generated tsvector (GIN); `raw_content` also carries a trigram index for rare terms | `wf1-ingest-book`; the structured `ingest-*` **generate** cards from `ref.*`; `hopslist_load.py` | `nlq.search_knowledge()` → `wf-step-retrieve` → `wf-step-retrieve-multi` → `chat-agent`<br>`nlq.search_knowledge()` → `wf-step-retrieve` → `cap-brainstorm-pairing` / `cap-formulate-recipe` → `chat-agent`<br>`nlq.corpus_vocabulary_gap()` → `nlq.corpus_lexemes` → the gap check in `wf-step-retrieve`, `cap-*`, `wf1-ingest-book`<br>`nlq.corpus_coverage()` → `wf-step-retrieve-keywords`<br>`nlq.f_refresh_corpus_lexemes()` ⇒ `nlq.corpus_lexemes` ⇐ `wf1-ingest-book`<br>`kb.promote_version()` → ingest gate<br>direct → `wf-step-retrieve-keywords`, `grounding_eval.py`, `services/webarm/webarm.py` (shape only) |
| `kb.chunk_embeddings` | 2 946 | 45 MB | bge-m3 vectors, HNSW cosine (`m=16 ef_construction=64`). Keyed `(chunk_id, model)` so re-embedding with a new model does not destroy the old vectors | ingest workflows, `hopslist_load.py` | `nlq.search_knowledge()` (the vector leg of the RRF) → `wf-step-retrieve` → `chat-agent`<br>`kb.promote_version()` → ingest gate (`missing` count) |
| `kb.ingest_log` | 24 | 112 kB | Per-stage ingest breadcrumbs: `stage`, `level`, `message`, `detail` jsonb. What you read when a book ingests to zero chunks | every ingest workflow | **humans only** — no function or workflow reads it. `docs/TESTING.md` procedures |

**What is actually in there** — 13 documents, 2 946 chunks:

| Slug | Type | Authority | Loaded by |
|---|---|---|---|
| `how-to-brew-palmer` | book | reference | `ingest-how-to-brew` → `wf1-ingest-book` |
| `water-comprehensive-guide` | book | reference | `ingest-water` → `wf1-ingest-book` |
| `yeast-practical-guide` | book | reference | `ingest-yeast` → `wf1-ingest-book` |
| `malt-practical-guide` | book | reference | `ingest-malt` → `wf1-ingest-book` |
| `draught-beer-quality-manual` | book | reference | `ingest-draught` → `wf1-ingest-book` |
| `bjcp-2021-beer-styles` | style_guide | guideline | `ingest-bjcp-styles` (generated from `ref.styles`) |
| `ba-2026-beer-styles` | style_guide | guideline | `ingest-ba-styles` (generated from `ref.styles`) |
| `bjcp-style-study-guide` | style_guide | guideline | `ingest-study-guide` (generated from `ref.styles`) |
| `hop-variety-handbook` | datasheet | reference | `ingest-hop-varieties` (generated from `ref.hops`) |
| `hopslist-hop-database` | datasheet | reference | `scripts/ingest/hopslist_load.py` (generated from `ref.hops`) |
| `beer-fault-list` | datasheet | guideline | `ingest-beer-faults` (generated from `ref.faults`) |
| `byo-stout-style-guide` | article | practitioner | `ingest-stout-guide` → `wf1-ingest-book` |
| `byo-pastry-stouts` | article | practitioner | `ingest-pastry-stouts` → `wf1-ingest-book` |

Six of the thirteen are **generated from `ref.*` rows**, not converted from a file.
That is the D32 contract: the prose a model reads and the numbers SQL reads come from
one source, so they cannot disagree.

---

## 4. `ref` — published reference data

Why it exists: numbers must not be retrieved as prose. A style's IBU range is a SQL
range, never an embedded sentence a model can misread.

| Table | Rows | Size | What kind of data | Written by | Read by — full chain |
|---|---|---|---|---|---|
| `ref.styles` | 285 | 1.9 MB | Style guidelines as rows, all sources side by side: **BJCP 2021 (116)**, **BA 2026 (169)**. `og/fg/ibu/srm/abv` min+max, 10 prose columns, `commercial_examples[]`, `tags[]`. `has_vitals` is generated from `og_min IS NOT NULL` — many BA styles are prose-only | `ingest-bjcp-styles`, `ingest-ba-styles`, `ingest-study-guide`; extracted by `sg_extract.py` | `ref.f_style_bands()` → `cap-formulate-recipe` (the band the recipe must land in) → `chat-agent`<br>card generation SQL → `kb.chunks` → `nlq.search_knowledge()` → `wf-step-retrieve` → `chat-agent`<br>`corpus.f_rebuild_styles()` → `corpus.styles.ref_style_id` ⇐ `corpus_load.py`<br>`nlq.find_batches()` → *(no live caller)*<br>FK target of `brew.recipes.style_id`<br>direct → `grounding_eval.py` |
| `ref.malts` | 77 | 216 kB | Maltster datasheets. Stores **both** source units (extract % DBFG, colour EBC) and calculator units (PPG, °L) — the first so a figure can be audited against the datasheet, the second so the compute step never converts units itself. `source_doc` names the datasheet | `db/init/26_ref_malts.sql` | `db/init/27`, `28`, `32`, `33` seed ⇒ `brew.ingredients` → `brew.f_catalogue()` / `brew.f_compute_recipe()` → `cap-formulate-recipe` → `chat-agent`<br>FK target of `corpus.fermentables.ref_malt_id`<br>⚠️ **no function reads `ref.malts` at runtime** — it reaches the agent only as seeded `brew.ingredients` rows |
| `ref.hops` | 268 | 672 kB | Hop varieties with full oil profiles: alpha/beta/cohumulone/total oils/myrcene/humulene/caryophyllene/farnesene min+max, `beer_types[]`, `flavour[]`, `alternatives[]`. A NULL range end is an **open bound from the source**, not missing data | `ingest-hop-varieties`, `hopslist_load.py`; extracted by `hops_extract.py`, `hopslist_extract.py` | card generation + `ref.f_range_text()` → `kb.chunks` → `nlq.search_knowledge()` → `wf-step-retrieve` → `chat-agent`<br>`db/init/27`, `28`, `33` seed ⇒ `brew.ingredients` → `brew.f_catalogue()` → `cap-formulate-recipe`<br>FK target of `corpus.hops.ref_hop_id`<br>direct → `grounding_eval.py` |
| `ref.faults` | 21 | 112 kB | Beer off-flavours: `name`, `descriptors[]`, `solutions`. **No `cause` column on purpose** — the source has none and causes must never be inferred | `ingest-beer-faults` | card generation → `kb.chunks` → `nlq.search_knowledge()` → `wf-step-retrieve` → `chat-agent`<br>direct → `grounding_eval.py` |

---

## 5. `corpus` — 174 554 scraped recipes

Why it exists: to answer "what do brewers actually *do* for this style?" with quantiles
over real recipes instead of a model's guess. Largest thing in the database by an order
of magnitude.

⛔ Three standing rules, all in the table comments:
- `corpus.recipes` is **observed practice** — not truth (`brew.*`), not published
  reference (`ref.*`).
- It is **NEVER embedded into `kb.*`** — unvalidated and unattributed.
- `corpus.yeasts` specs are the recipe site's own strain database, carry no
  `source_doc`, and **must not be promoted into a `ref.*` table**.

### 5.1 Fact tables

| Table | Rows | Size | What kind of data | Read by — full chain |
|---|---|---|---|---|
| `corpus.recipes` | 174 554 | 60 MB | One row per scraped recipe: `source` (all `brewersfriend`), `source_ref`, `style_raw`, `method`, `batch_l`, `og`/`fg`/`abv`/`ibu`/`color_srm`, `mash_ph`, `rating`, `num_ratings`, `views` | `nlq.f_corpus_styles()` → `nlq.common_practice()` → `wf-step-practice` → `chat-agent`<br>`nlq.find_exemplars()` → `cap-formulate-recipe` → `chat-agent`<br>`nlq.ingredient_usage()` → `nlq.ingredient_practice()` → `cap-formulate-recipe`<br>`corpus.f_rebuild_search/styles()` ⇐ `corpus_load.py`<br>`corpus.v_recipe` (view) |
| `corpus.recipe_fermentables` | 658 090 | 109 MB | Grain bill lines: `amount_kg`, `potential_ppg`, `color_lovibond` (⚠️ the source card mislabels this field as Lintner), `pct_bill` | `nlq.common_practice()` → `wf-step-practice` → `chat-agent`<br>`nlq.cohort_stats()` → `cap-formulate-recipe` → `chat-agent`<br>`nlq.find_exemplars()` → `cap-formulate-recipe`<br>`corpus.f_rebuild_dims/search()` ⇐ `corpus_load.py` |
| `corpus.recipe_hops` | 605 406 | 115 MB | Hop additions kept **normalised** — a hop used at boil, whirlpool and two dry hops is four rows. `use`, `use_temp_c`, `time_value`/`time_unit`/`time_raw`, `ibu_contrib`, `pct_amount` | same three chains as `recipe_fermentables` |
| `corpus.recipe_misc` | 141 857 | 25 MB | Adjuncts, spices, water agents, finings. `amount_value`/`amount_unit` are **generated** from `amount_raw`; units are never converted, so beans, oz and tsp sit side by side | `nlq.ingredient_usage()` → `nlq.ingredient_practice()` → `cap-formulate-recipe` → `chat-agent`<br>`nlq.ingredient_practice()` → `brew.f_resolve_request()` → `cap-formulate-recipe`<br>`nlq.common_practice()` → `wf-step-practice`<br>`nlq.cohort_stats()` / `find_exemplars()` → `cap-formulate-recipe` |
| `corpus.recipe_yeasts` | 148 290 | 24 MB | `attenuation_pct`, `flocculation`, `temp_min/max_f`, `starter` | `nlq.common_practice()` → `wf-step-practice`<br>`nlq.cohort_stats()` / `find_exemplars()` → `cap-formulate-recipe` |

⚠️ Worth knowing: **`nlq.ingredient_practice()` only reads `corpus.recipe_misc`.** Its
own comment explains why — four substring sweeps over 33k dimension rows against
141 857 fact rows. It is the adjunct/spice path, not a general ingredient path.

### 5.2 Dimension tables — rebuilt by `corpus.f_rebuild_dims()`

| Table | Rows | Size | What kind of data | Read by — full chain |
|---|---|---|---|---|
| `corpus.fermentables` | 7 993 | 3.9 MB | Distinct fermentable strings with **observed** PPG/colour and min/max, plus `ref_malt_id` → the sourced side in `ref.malts` | `nlq.f_resolve_ingredient()` → `f_resolve_ingredient_loose()` → `nlq.f_cohort_ids()` → `find_cohort` / `find_exemplars` / `cohort_stats` → `cap-formulate-recipe` → `chat-agent`<br>…and → `brew.f_resolve_request()` → `cap-formulate-recipe` |
| `corpus.hops` | 6 593 | 3.3 MB | Distinct hop strings, observed alpha range, `forms[]`, `uses[]`, `ref_hop_id` → `ref.hops` | same `f_resolve_ingredient` chain; also read directly by `hopslist_load.py` |
| `corpus.miscs` | 16 112 | 7.6 MB | Distinct misc strings. `types[]` keeps **every** classification observed — the corpus files the same substance several ways | same `f_resolve_ingredient` chain |
| `corpus.yeasts` | 1 745 | 928 kB | Distinct yeast strings with `lab` and attenuation/temp ranges | same `f_resolve_ingredient` chain; `db/init/33` reads it to seed `brew.ingredients` |
| `corpus.styles` | 181 | 232 kB | Distinct style strings with cached vitals and a nullable `ref_style_id` bridge (**104 of 181 bridged**, 1 manually). `match_method` is `exact` or `manual` — `f_rebuild_styles` never overwrites `manual`. A NULL bridge means *no link established*, never *no guideline exists* | `corpus.f_rebuild_styles()` ⇐ `corpus_load.py`<br>`corpus.v_styles_unbridged` (view) → humans<br>⚠️ **not** read by `nlq.f_corpus_styles()`, which goes to `corpus.recipes.style_raw` directly |

### 5.3 Search index and views

| Object | Rows | Size | What it is | Read by — full chain |
|---|---|---|---|---|
| `corpus.recipe_search` | 174 554 | 85 MB | **Not** a second copy of the corpus — one GIN-indexed row per recipe (`ingredients text[]`, `style_key` trigram) so an arbitrary style + ingredients + parameters cohort is one query. Rebuilt by `corpus.f_rebuild_search()`; the fact tables stay authoritative | `nlq.f_cohort_ids()` → `nlq.find_cohort()` / `find_exemplars()` / `cohort_stats()` → `cap-formulate-recipe` → `chat-agent`<br>`brew.f_resolve_request()` → `cap-formulate-recipe`<br>`corpus.f_rebuild_styles()` ⇐ `corpus_load.py` |
| `corpus.v_recipe` | view | — | One row per recipe with the complete build as `jsonb` — the read-side answer to "a whole recipe in one place" | humans / ad-hoc |
| `corpus.v_styles_unbridged` | view | — | Corpus styles with no `ref.styles` link, commonest first — the manual bridging worklist | humans |

---

## 6. `brew` — the brewer's own data

Why it exists: the only schema that is *about the user*. The recipe path is live; the
brewday path is built but unfed.

| Table | Rows | Size | What kind of data | Written by | Read by — full chain |
|---|---|---|---|---|---|
| `brew.ingredients` | 302 | 392 kB | **The catalogue**: 120 yeast, 81 fermentable, 72 hop, 14 misc, 9 adjunct, 6 water_agent. `potential_ppg`, `color_lovibond`, `alpha_acid_pct`, attenuation range, `attrs jsonb` | seeded from `ref.malts`/`ref.hops`/`corpus.yeasts` by `db/init/27`, `28`, `31`, `32`, `33` | `brew.f_catalogue()` → `cap-formulate-recipe` → `chat-agent`; also → `recipe_eval.py`<br>`brew.f_compute_recipe()` → `brew.f_save_recipe()` / `f_fit_recipe()` → `f_fit_ibu()` / `f_fit_to_abv()` → `cap-formulate-recipe`<br>`brew.f_resolve_request()` → `cap-formulate-recipe` |
| `brew.recipes` | 113 | 104 kB | Saved recipes: `version` + `parent_recipe_id` (re-saving a name creates a linked new version), `style_id` → `ref.styles`, targets, `mash_profile`/`water_profile` jsonb. `additions jsonb` holds requested flavourings with **no honest PPG** — a line on the sheet with a method and a citation, never a term in the gravity equation | `brew.f_save_recipe()` ⇐ `cap-formulate-recipe` | `nlq.find_batches()` → *(no live caller — `brew.batches` is empty)*<br>direct → `recipe_eval.py` |
| `brew.recipe_items` | 723 | 144 kB | Recipe lines: `ingredient_id`, `stage`, `qty`, `unit`, `timing_min` | `brew.f_save_recipe()` ⇐ `cap-formulate-recipe` | `brew.f_dry_hop_rate_g_per_l()` → `nlq.find_batches()` → *(no live caller)*<br>direct → `recipe_eval.py` |
| `brew.batches` | **0** | 24 kB | Planned: one brewday per row — `batch_no`, `brewed_on`, `packaged_on`, actual `og`/`fg`, `status` | nothing yet | `brew.f_dry_hop_rate_g_per_l()` → `nlq.find_batches()`<br>FK target of `mem.memories.batch_id` |
| `brew.measurements` | **0** | 16 kB | Planned: timestamped gravity/temp/pH readings per batch, with `device` | nothing yet | nothing |
| `brew.sensory_notes` | **0** | 48 kB | Planned: BJCP-shaped tasting notes, `score`, `descriptors[]`, generated `fts` (GIN) | nothing yet | `nlq.find_batches()` (the descriptor search leg) |
| `brew.inventory` | **0** | 16 kB | Planned: what's on the shelf — `lot_code`, `qty`/`unit`, `acquired_on`, `best_before`, `location` | nothing yet | nothing |

The four empty tables are built and indexed but unfed;
`plans/archive/phase2/deferred/seed-batches.template.sql` is the intended shape.
`nlq.find_batches()` is the one `nlq` function with **no live caller at all**.

---

## 7. `obs` — observability

Why it exists: an agent run that cannot be traced cannot be evaluated. Every eval in
`scripts/stress/` reads these tables rather than the chat output.

| Table | Rows | Size | What kind of data | Written by | Read by — full chain |
|---|---|---|---|---|---|
| `obs.profiles` | 5 | 32 kB | Model + options per role: `compose`, `formulate`, `extract`, `creative`, `critique` — all currently `Qwen3.8-27B-GGUF:UD-Q4_K_M` with different sampling | `db/init/60`, `63_model_switch.sql` | `obs.f_step_config()` → `wf-step-llm` → **every** LLM step in `cap-formulate-recipe` and `cap-brainstorm-pairing`<br>direct → `chat-agent` (picks its own model) |
| `obs.prompts` | 23 | 240 kB | **Versioned prompt registry**, one active version per name; `sha256` set by the `f_prompt_hash` trigger. 5 names — `formulate.recipe/propose` is on **v11** | `db/init/62_obs_recipe_prompts.sql` | `obs.f_step_config()` → `wf-step-llm` → `cap-*` → `chat-agent` |
| `obs.steps` | 555 | 576 kB | One row per LLM/tool step: `kind`, `profile`, `model`, `model_loaded`, `prompt_sha256`, `input`/`output` jsonb, `verdict`, token counts, `latency_ms` | `obs.f_log_step()` ⇐ `wf-step-llm` | direct → `recipe_eval.py`; `docs/RECIPE-PIPELINE-V2.md` analysis |
| `obs.runs` | 221 | 112 kB | One per capability invocation: `session_id`, `turn_no`, `capability`, `status`, `budget`/`spent`. Measured: **129 `formulate.recipe`, 86 `brainstorm.pairing`, 6 `smoke`** | `obs.f_start_run()` / `f_finish_run()` ⇐ `cap-formulate-recipe`, `cap-brainstorm-pairing` | direct → `recipe_eval.py`, `grounding_eval.py` |
| `obs.retrievals` | 437 | 184 kB | What retrieval actually returned: `query`, `chunk_ids[]`, `top_k`, `mode`, `gap_terms[]` (terms the corpus could not cover) | `obs.f_log_retrieval()` ⇐ `wf-step-retrieve` | `obs.f_session_chunk_ids()` → `chat-agent` (so a turn knows what the session already saw)<br>`obs.f_session_chunk_ids()` → `grounding_eval.py` (grounding is checked against these ids)<br>direct → `recipe_eval.py`, `cap-formulate-recipe` |

---

## 8. `mem` — conversation and learned preferences

| Table | Rows | Size | What kind of data | Written by | Read by — full chain |
|---|---|---|---|---|---|
| `mem.chat_turns` | 734 | 568 kB | The real conversation log: `session_id`, `turn_no`, `role`, `content`, `tool_calls` jsonb, `chunk_ids[]` (what was retrieved for that turn), `latency_ms`, `model` | `chat-agent` | direct → `grounding_eval.py`, `recipe_eval.py`<br>FK source for `mem.memories.source_turn` |
| `mem.memories` | **0** | 32 kB | Designed as the learning layer: a `kind`/`content` claim with `confidence`, `status` lifecycle (`pending` → confirmed), `supersedes` self-FK, `source_turn` → `chat_turns`, optional `batch_id` → `brew.batches`, dedup by `content_sha256` | `mem.f_save_memory()` — granted to `mem_writer`, **never called from a live path** | nothing |
| `mem.memory_embeddings` | **0** | 32 kB | HNSW-indexed vectors over confirmed memories, same shape as `kb.chunk_embeddings` | nothing | nothing |

---

## 9. `public.n8n_chat_histories` — not ours

| Table | Rows | Size | What it is | Read by |
|---|---|---|---|---|
| `public.n8n_chat_histories` | 1 352 | 1.9 MB | n8n's LangChain Postgres Chat Memory node: `session_id`, `message jsonb`. Duplicates what `mem.chat_turns` records properly | n8n's own memory node. **No function, workflow SQL or eval in this repo reads it** |

⛔ **Outstanding security issue.** RLS **disabled**, **0** policies, `anon` holds the
full DML set including `DELETE` and `TRUNCATE`. Verified 2026-09-13: an anon-key request
to `http://localhost:8000/rest/v1/n8n_chat_histories` returns real rows. Blast radius is
`public` only — `kb` is not exposed through PostgREST (404). Architecture §13.1 **R6**;
cheapest fix:

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "REVOKE ALL ON public.n8n_chat_histories FROM anon, authenticated"
```

---

## 10. The functions

42 functions. This section gives each one the same treatment as a table: what it is
for, what it actually does, and what will surprise you.

**Conventions.** Every signature below is the real one from `pg_get_function_arguments`,
defaults included. `SECDEF` means `SECURITY DEFINER` — the function runs as its owner, so
a caller needs `EXECUTE` and no table grants at all. That is the mechanism behind §11:
`n8n_agent` can compute over `kb` and `corpus` while holding no privilege on either.

**33 of the 42 are `SECURITY DEFINER`, and all 33 pin `search_path`** (`measured`: zero
SECDEF functions have a NULL `proconfig`). The four with a
mutable `search_path` (`kb.promote_version`, `brew.f_abv`,
`brew.f_dry_hop_rate_g_per_l`, `obs.f_prompt_hash`) are exactly the four that are *not*
`SECURITY DEFINER`, which is why that advisor warning is not an escalation hole.

**Index.**

| Schema | Functions |
|---|---|
| `nlq` (15) | `search_knowledge` · `corpus_vocabulary_gap` · `corpus_coverage` · `f_cohort_ids` · `find_cohort` · `find_exemplars` · `cohort_stats` · `common_practice` · `ingredient_practice` · `ingredient_usage` · `f_resolve_ingredient(_loose)` · `f_corpus_styles` · `find_batches` · `f_refresh_corpus_lexemes` |
| `brew` (11) | `f_compute_recipe` · `f_fit_recipe` · `f_fit_to_abv` · `f_fit_ibu` · `f_save_recipe` · `f_resolve_request` · `f_catalogue` · `f_dry_hop_rate_g_per_l` · `f_abv` · `f_kg_to_lb` · `f_l_to_gal` |
| `ref` (2) | `f_style_bands` · `f_range_text` |
| `kb` (1) | `promote_version` |
| `mem` (1) | `f_save_memory` |
| `obs` (7) | `f_start_run` · `f_finish_run` · `f_log_step` · `f_log_retrieval` · `f_step_config` · `f_session_chunk_ids` · `f_prompt_hash` |
| `corpus` (5) | `f_rebuild_dims` · `f_rebuild_styles` · `f_rebuild_search` · `f_amount_value` · `f_amount_unit` |

---

### 10.1 `nlq` — the agent's read surface

The only schema `n8n_agent` can reach. Every one of these is `STABLE SECDEF` except
`f_refresh_corpus_lexemes`.

#### `nlq.search_knowledge()` — hybrid retrieval

```sql
nlq.search_knowledge(
  p_query_text   text,
  p_query_embed  vector,
  p_limit        int   DEFAULT 6,
  p_candidates   int   DEFAULT 40,
  p_rrf_k        int   DEFAULT 50,
  p_model        text  DEFAULT 'bge-m3',
  p_doc_type     text  DEFAULT NULL,
  p_rare_max_df  real  DEFAULT 0.02,
  p_per_doc      int   DEFAULT 3
) RETURNS TABLE(chunk_id, doc_slug, doc_title, heading_path, page_from, page_to,
                raw_content, image_refs, image_dir, authority, score)
```

**Why it exists.** One call has to answer "find me the passages that bear on this", and
no single retrieval method does that well. It runs **three legs** and fuses them by
Reciprocal Rank Fusion:

| Leg | Method | Catches |
|---|---|---|
| `kw` | `websearch_to_tsquery` over `chunks.fts` | ordinary keyword overlap |
| `rare` | a tsquery built from **only** the query lexemes whose `ndoc_frac ≤ p_rare_max_df` | the one distinctive term in an otherwise generic question |
| `vec` | `embedding <=> p_query_embed` (HNSW cosine) | paraphrase and synonym |

Each leg takes `p_candidates` rows; scores fuse as `Σ 1/(p_rrf_k + rank)`; `p_limit`
survive. Every leg joins `document_versions.is_current`, so a superseded ingest is
invisible without any filter in the caller.

Things worth knowing:

- **The rare leg builds its tsquery from `nlq.corpus_lexemes`**, so a term the library
  has never seen drops out of the query instead of matching nothing expensively. Lexemes
  are passed through `quote_literal` — an apostrophe would otherwise break the `::tsquery` parse.
- **`p_per_doc` sorts, it does not filter.** The final `ORDER BY (rn_doc > p_per_doc), score DESC`
  puts everything inside the per-document cap first, then backfills from the overflow.
  A question whose answer genuinely lives in one book still returns `p_limit` passages
  rather than being truncated to 3.
- It returns `raw_content`, not `content` — the embedded text is not the text shown.
- `authority` comes out with every row, so the caller can weight a guideline over a blog post.

*Reads* `kb.chunks`, `kb.chunk_embeddings`, `kb.documents`, `kb.document_versions`,
`nlq.corpus_lexemes` · *Called by* `wf-step-retrieve`, `cap-brainstorm-pairing`,
`scripts/ask.sh` · *Surfaces at* `chat-agent`

#### `nlq.corpus_vocabulary_gap()` — "do we even know this word?"

```sql
nlq.corpus_vocabulary_gap(
  p_query_text  text,
  p_near_sim    real DEFAULT 0.5,
  p_min_known   int  DEFAULT 2,
  p_rare_max_df real DEFAULT 0.02
) RETURNS TABLE(gap_terms text[], absent_terms text[], lex_count int, known_count int)
```

**Why it exists.** It decides whether to answer from the library or go to the web arm.
Getting it wrong is expensive in both directions: a false gap costs a 12-second web
fetch that returns nothing new; a missed gap means answering about something the library
has never heard of.

It is the most carefully tuned function in the database, and its own comments say why:

- `absent_terms` = query lexemes not in `nlq.corpus_lexemes` at all. Numeric-only lexemes
  are dropped (`~ '[a-z]'`) — a bare year says nothing about topic coverage.
- `novel` = absent **and** not within `p_near_sim` trigram similarity of any known word,
  which is what separates a new product name from a typo. Deliberately unindexed: 15 368
  lexemes against the 0–2 absent terms a question has is a trivial scan, and `%` would
  silently use the session's `pg_trgm.similarity_threshold` instead of `p_near_sim`.
- A **pair arm** catches two adjacent rare *capitalised* words whose phrase has no
  `phraseto_tsquery` match — product names are capitalised by convention.
- ⛔ **The `p_min_known` guard has an escape hatch, and it is load-bearing.** On a short
  query the guard is unsatisfiable, and the agent's rewrite is routinely short: *"What
  hops go with Talus?"* reached the retriever as the single word `Talus` — 1 lexeme,
  0 known, suppressed, killing the exact case the detector exists for. Below
  `p_min_known + 2` lexemes, capitalisation decides instead and only capitalised novel
  terms are returned. That is what makes `Talus` fire while a lowercase typo stays suppressed.
- ⚠️ **The documented cost:** a product name typed in lower case (`cryo pop`) is invisible
  to both arms, and that question reports no gap at all.
- ⚠️ **This function sees the agent's rewrite, never the user's sentence.** Every tuning
  decision above follows from that.

*Reads* `kb.chunks`, `kb.document_versions`, `nlq.corpus_lexemes` · *Called by*
`wf-step-retrieve`, `wf-step-retrieve-keywords`, `cap-formulate-recipe`,
`cap-brainstorm-pairing`, `wf1-ingest-book`, `grounding_eval.py`

#### `nlq.corpus_coverage()` — per-term hit counts

```sql
nlq.corpus_coverage(p_terms text[]) RETURNS TABLE(term text, fts_hits int)
```

Straight FTS count per term against current chunks. Cheaper and blunter than the gap
detector; used by the keyword retrieval variant to decide what to search for.

⛔ **It returns rows in input order, on purpose.** The body uses `WITH ORDINALITY` +
`ORDER BY`, not `SELECT DISTINCT`, because `DISTINCT` hash-aggregates and returns an
arbitrary order — `measured` 2026-09-17, a five-term input came back permuted. A caller
pairing the result positionally against its own list would mislabel coverage silently,
and a covered term routed to the web costs 12 s and returns nothing new. `min(ord)`
keeps the first occurrence of a duplicate.

*Reads* `kb.chunks`, `kb.document_versions` · *Called by* `wf-step-retrieve-keywords`

#### `nlq.f_cohort_ids()` — the relaxation ladder

```sql
nlq.f_cohort_ids(
  p_style text, p_ingredients text[] DEFAULT '{}',
  p_abv_min numeric DEFAULT NULL, p_abv_max numeric DEFAULT NULL,
  p_ibu_min numeric DEFAULT NULL, p_ibu_max numeric DEFAULT NULL,
  p_min_recipes int DEFAULT 30
) RETURNS TABLE(recipe_id bigint, rung int, rung_label text)
```

**Why it exists.** "Sweet stout with vanilla and lactose, 6–7% ABV" may match four
recipes, which is not a cohort. Rather than return noise or nothing, it **relaxes the
query in a defined order and reports which rung it landed on**.

| Rung | Kept | Label the caller must print |
|---|---|---|
| 1 | style + every ingredient + ABV/IBU limits | *exact: style, every ingredient, and the stated parameters* |
| 2 | style + every ingredient | *relaxed: ABV/IBU limits dropped* |
| 3 | style + **the rarest requested ingredient only** | *relaxed: kept only "vanilla" — the other requested ingredients are NOT in these recipes* |
| 4 | style only | *relaxed: style only — NONE of the requested ingredients is in these recipes* |
| 5 | the style's **head noun** only | *relaxed: widened to every "stout" — not the style asked for* |

Two details carry the design:

- **Rung 3 picks the rarest term, not the first.** Each term's selectivity is counted
  inside the narrow style set; the rarest is the defining one. In "sweet stout, vanilla,
  lactose" that is vanilla.
- **`pick` takes `min(rung)` among rungs with `≥ p_min_recipes` rows** — the tightest
  rung that still means something.
- Style matching is head-noun + all-words-present; `'beer'` as a head noun is rejected
  because it is a shrug, not a style.

⚠️ The `rung_label` is not decoration. It states what was *not* matched, and the calling
prompt is required to print it.

*Reads* `corpus.recipe_search`, `nlq.f_resolve_ingredient` · *Called by*
`nlq.find_cohort`, `nlq.find_exemplars`, `nlq.cohort_stats`

#### `nlq.find_cohort()` — the cohort's vitals

```sql
nlq.find_cohort(p_style, p_ingredients, p_abv_min, p_abv_max,
                p_ibu_min, p_ibu_max, p_min_recipes DEFAULT 30)
RETURNS TABLE(rung, rung_label, n_recipes, og, fg, abv, ibu, color_srm)
```

Medians for the cohort `f_cohort_ids` settled on. Each percentile carries its own
`FILTER` sanity window (OG 1.0–1.2, FG 0.98–1.1, ABV 0–20, IBU 0–150, SRM 0–80) so one
mistyped recipe cannot move a median. Batch size is clamped to 5–100 L — homebrew scale,
not a commercial pilot. `HAVING count(*) > 0` means an empty cohort returns **no row**
rather than a row of NULLs.

*Called by* `cap-formulate-recipe`, `nlq.find_exemplars`

#### `nlq.find_exemplars()` — whole recipes, behind a plausibility gate

```sql
nlq.find_exemplars(p_style, p_ingredients, …, p_min_recipes DEFAULT 30, p_limit DEFAULT 3)
RETURNS TABLE(recipe_id, rung, rung_label, n_considered, n_rejected, gate_note, exemplar)
```

**Why it exists.** Medians tell you the middle; a model writing a recipe needs to see
whole builds. But the corpus is self-reported, so some of those builds are nonsense —
and handing a model a nonsense exemplar is worse than handing it nothing.

Three gate rules, each rejecting a recipe that contradicts itself:

| Rule | Test | Meaning |
|---|---|---|
| `bad_ibu` | `ibu ≤ 0` while `boil_hops > 0` | bitterness the hop schedule contradicts |
| `bad_atten` | apparent attenuation `(og-fg)/(og-1)` outside **0.40–0.95** | an OG/FG pair no yeast produces — the window brackets Brettanomyces at the top and a stuck fermentation at the bottom |
| `bad_bill` | `sum(pct_bill)` outside **95–105**, or no fermentables | a grain bill that is not a whole grain bill |

⚠️ **`n_rejected` is part of the answer and must be shown.** It is the honesty signal:
"3 of 41 considered were discarded as implausible" tells the reader how much of the
corpus agreed with itself.

The 5–100 L batch filter selects what is *considered* and is deliberately **not** one of
the three gate rules, so a 400 L pilot batch is excluded without being counted as
"discarded as implausible".

⚠️ The correlated subqueries in `facts` are **the measured-fast shape**, not an
oversight: the gate must see the whole cohort or the rejection count is a lie, and
`'American IPA' + citra` is 9 340 recipes. Rewritten as grouped joins over the 605k-row
`recipe_hops` and 658k-row `recipe_fermentables`, that call went from 907 ms to 1 014 ms.

*Reads* all five `corpus.recipe_*` tables, `nlq.f_cohort_ids`, `find_cohort`,
`cohort_stats` · *Called by* `cap-formulate-recipe`

#### `nlq.cohort_stats()` — ingredient quantiles within a cohort

```sql
nlq.cohort_stats(p_style, p_ingredients, …, p_min_recipes DEFAULT 30, p_top DEFAULT 8)
RETURNS TABLE(section, item, n_recipes, pct_of_cohort, unit, p25, p50, p75, typical)
```

The cohort broken down by section (grain bill, hops, yeast, misc) with p25/p50/p75 per
item, plus a **rendered `typical` string** via `ref.f_range_text()`. Same 5–100 L filter
as `find_cohort`.

*Called by* `cap-formulate-recipe`, `nlq.find_exemplars`

#### `nlq.common_practice()` — what brewers brew for a style

```sql
nlq.common_practice(p_style text, p_top int DEFAULT 8)
RETURNS TABLE(section text, item text, pct_of_recipes numeric, typical text)
```

**Why it exists.** The `chat-agent` tool answers "what goes in a Czech dark lager?" from
174 554 real recipes rather than from the model's priors. Sections: an `overview` block
(count + typical OG/FG/ABV/IBU/SRM), then `grain bill`, `hops`, `yeast`, `misc`, each
ranked by how many recipes use the item.

- ⛔ **Returns nothing below 30 matching recipes** rather than a meaningless median.
- ⛔ **The answer must be attributed as "what brewers commonly do", never as what a book
  or guideline says.** This is observed practice; `ref.*` is the authority.
- **Hops are summed per recipe before rating.** The same variety appears at boil,
  whirlpool and dry hop; a g/L rate must count the beer once, not the additions. The
  dominant use is reported beside it, so *"Citra, 2.3 g/L, usually dry hop"* reads as one fact.
- Every percentile carries the same sanity windows as `find_cohort`.

*Called by* `wf-step-practice` → `chat-agent` (tool `common_practice`)

#### `nlq.ingredient_practice()` — how one adjunct is actually used

```sql
nlq.ingredient_practice(p_term text, p_style text DEFAULT NULL, p_top int DEFAULT 6)
RETURNS TABLE(term, stage, pct_at_stage, unit, n_additions, n_recipes, p25, p50, p75, typical)
```

Stage distribution and amount quantiles for one ingredient, **one row per (stage, unit)**.

- ⚠️ **It reads `corpus.recipe_misc` only** — adjuncts, spices, water agents, finings.
  Despite the general-sounding name it is not a hop or malt path.
- ⛔ **Units are never converted.** Beans, oz, tsp and g sit side by side as separate
  rows, because converting "2 vanilla beans" to grams would be an invention.
- Requires `≥ 5` additions per (stage, unit) group before reporting a quantile.
- The `typical` string is **rendered in SQL on purpose**: a 12B model cannot misread a
  unit that is spelled out, and a wide spread has to *read* as wide — hence
  `'varies widely: 4 g typical, but 2-12 is common'` when `p75/p25 ≥ 3`, or it gets
  taken for a target.
- ⛔ `WITH … AS MATERIALIZED` is load-bearing — see `ingredient_usage` below.

*Called by* `cap-formulate-recipe`, and by `brew.f_resolve_request()`

#### `nlq.ingredient_usage()` — which styles use an ingredient

```sql
nlq.ingredient_usage(p_term text, p_top int DEFAULT 10)
RETURNS TABLE(style_raw, n_recipes, unit, p25, p50, p75, typical)
```

The style-facing cut of the same `recipe_misc` data. Reachable only through
`ingredient_practice` — nothing calls it directly.

⛔ **`MATERIALIZED` is load-bearing and the measurement is in the body:** inlined (the
PG12+ default), the planner re-evaluates `f_resolve_ingredient` once *per row* of
`recipe_misc` — 141 857 rows × four substring sweeps over 33k dimension rows. **69 ms
with the keys resolved once, >60 s without.** Same query, same data.

#### `nlq.f_resolve_ingredient()` / `f_resolve_ingredient_loose()`

```sql
nlq.f_resolve_ingredient(p_term text)       RETURNS text[]
nlq.f_resolve_ingredient_loose(p_term text) RETURNS text[]
```

Term → matching `name_key`s, by substring `LIKE` across all four dimension tables
(`fermentables`, `hops`, `yeasts`, `miscs`) at once. Terms under 2 characters return `{}`.

`_loose` adds exactly one rule: if the exact match is empty **and** the term ends in `s`,
retry without the trailing character. That is the whole "plural" handling — deliberately
not a stemmer.

*Called by* `f_cohort_ids`, `ingredient_usage`, `ingredient_practice`,
`brew.f_resolve_request`

#### `nlq.f_corpus_styles()`

```sql
nlq.f_corpus_styles(p_style text) RETURNS TABLE(style_raw text)
```

The brewer's style words → the corpus's own style strings. Head-noun `ILIKE` match, then
keeps only the strings scoring the **maximum** number of word hits, so "sweet stout"
prefers `Sweet Stout` over `Stout`. Rejects `'beer'` as a head noun.

⚠️ It reads `corpus.recipes.style_raw` **directly, not `corpus.styles`** — the dimension
table is not on this path.

#### `nlq.find_batches()` — the brewer's own beers

```sql
nlq.find_batches(p_style_name, p_style_code, p_descriptor, p_brewed_after,
                 p_brewed_before, p_min_abv, p_max_abv, p_min_dry_hop_rate,
                 p_max_dry_hop_rate, p_limit DEFAULT 20)
RETURNS TABLE(batch_no, recipe_name, style_code, style_name, brewed_on,
              og, fg, abv, dry_hop_rate_g_per_l, descriptors, avg_score)
```

The one function pointed at `brew.*` rather than the corpus: find my batches by style,
tasting descriptor, date, ABV or dry-hop rate, with computed ABV and average tasting score.

⚠️ **No caller anywhere in the repo, and `brew.batches` is empty.** Built against a
schema that was never fed.

#### `nlq.f_refresh_corpus_lexemes()`

```sql
nlq.f_refresh_corpus_lexemes() RETURNS bigint   -- VOLATILE SECDEF
```

`REFRESH MATERIALIZED VIEW CONCURRENTLY nlq.corpus_lexemes`, returning the new row count.

⛔ **The only thing in `nlq` that writes**, which is why `50_roles.sql` revokes it from
`agent_ro` immediately after the blanket schema grant that would otherwise hand it back.
It belongs to the ingest path. `n8n_agent`'s `default_transaction_read_only` would block
it anyway — this is Layer 1 not relying on Layer 2.

*Called by* `wf1-ingest-book`, after chunks land

#### `nlq.corpus_lexemes` (materialized view)

`word`, `ndoc`, `ndoc_frac` — the library's vocabulary with document frequency, ~15 368
rows. Every "is this word known, and is it rare?" question in the system is one index
lookup against this. Feeds the rare leg of `search_knowledge` and both arms of
`corpus_vocabulary_gap`.

---

### 10.2 `brew` — recipe arithmetic and the one write surface

#### `brew.f_compute_recipe()` — the deterministic core

```sql
brew.f_compute_recipe(
  p_batch_size_l  numeric,
  p_items         jsonb,                     -- [{ingredient_id, qty_g, unit, stage, timing_min}]
  p_efficiency    numeric DEFAULT 0.72,
  p_attenuation   numeric DEFAULT 0.75,
  p_boil_volume_l numeric DEFAULT NULL       -- defaults to batch size
) RETURNS jsonb                              -- STABLE SECDEF
```

**Why it exists.** A language model must never be the thing that computes OG. This
function is the arithmetic, and the model's job is only to choose ingredients. Gravity
from `potential_ppg`, bitterness by **Tinseth against boil gravity**, colour by **Morey**.

**It returns its intermediate inputs alongside the results** — `fermentable_points`,
`unfermentable_points`, MCU, boil gravity — so a surprising figure can be *traced*
rather than re-derived. That is what makes `f_fit_recipe` possible.

Three behaviours that are easy to get wrong and are handled explicitly:

- ⛔ **`qty_g` is grams, and items not weighed in grams are excluded from gravity and
  colour rather than misread.** Since the catalogue gained countable rows, an item in
  `'each'` or `'ml'` would otherwise be read as that many grams — two vanilla beans
  would enter the mash as 2 g of sugar. A missing `unit` means grams, for rows written
  before the column existed.
- **Sugars are 100% efficient; only mashed grain gets `p_efficiency`.** `kind = 'adjunct'`
  bypasses brewhouse efficiency, because treating lactose as 72% efficient understates OG.
- **`attrs->>'fermentable' = false` routes points to `unfermentable_points`**, which
  survive into FG. This is how lactose raises OG *and* FG instead of turning into alcohol.
- Raises on a non-positive batch size rather than returning nonsense.

*Reads* `brew.ingredients` · *Called by* `cap-formulate-recipe`, `f_save_recipe`,
`f_fit_recipe`, `f_fit_ibu`

#### `brew.f_fit_recipe()` — scale the grist to hit a target OG

```sql
brew.f_fit_recipe(p_batch_size_l, p_items, p_target_og,
                  p_efficiency DEFAULT 0.72, p_attenuation DEFAULT 0.75,
                  p_boil_volume_l DEFAULT NULL) RETURNS jsonb
```

Computes once, reads `fermentable_points` and `unfermentable_points` back out of the
result, solves for the factor that closes the gap, and rescales **only** `kind =
'fermentable'` items. Returns `{items, scale_factor, computed}`.

- **Adjunct points are subtracted from the target before scaling**, because scaling grain
  cannot move them.
- If adjuncts alone already meet the target, it returns `scale_factor: 1` with
  `warning: 'target unreachable by scaling grain'` rather than a negative grist.
- ⛔ **The unit test here must match `f_compute_recipe`'s.** An item excluded from the
  gravity arithmetic for its unit but scaled here would have its quantity multiplied
  while contributing nothing.

⚠️ No live caller — `cap-formulate-recipe` reaches it through `f_fit_to_abv`.

#### `brew.f_fit_to_abv()` / `brew.f_fit_ibu()`

```sql
brew.f_fit_to_abv(p_batch_size_l, p_items, p_target_abv, …) RETURNS jsonb
brew.f_fit_ibu(p_batch_size_l, p_fit, p_ibu_lo, p_ibu_hi, …) RETURNS jsonb
```

`f_fit_to_abv` converts a target ABV to a target OG and delegates to `f_fit_recipe`.

`f_fit_ibu` takes the **output of a previous fit** (`p_fit`) and scales hop quantities
toward a band — aiming 5% inside the edge it missed (`lo × 1.05` / `hi × 0.95`) so a
rounding wobble does not put it straight back out. Only `kind = 'hop'` items in grams
are scaled, floored at 1 g. It returns the original object plus an `ibu_fit` block
saying `scaled`, `from`, `to`, `factor`.

⛔ **IBU 0 is refused, not scaled.** Nothing times zero reaches a band, so it returns
`scaled: false` with `reason: 'no addition contributes bitterness; check the boil times'`
and lets the recipe through — rather than dividing by zero or silently inventing a hop.

*Called by* `cap-formulate-recipe`

#### `brew.f_save_recipe()` — the only write surface

```sql
brew.f_save_recipe(
  p_name text, p_batch_size_l numeric, p_items jsonb,
  p_style_id bigint DEFAULT NULL, p_efficiency numeric DEFAULT 0.72,
  p_attenuation numeric DEFAULT 0.75, p_boil_volume_l numeric DEFAULT NULL,
  p_mash_profile jsonb DEFAULT NULL, p_notes text DEFAULT NULL,
  p_additions jsonb DEFAULT '[]'
) RETURNS jsonb                              -- VOLATILE SECDEF
```

**The only path that writes `brew.recipes` and `brew.recipe_items`.** `SECURITY DEFINER`,
so the caller needs no table grants — and still cannot read the brewer's batches.

- ⛔ **Targets are computed by `f_compute_recipe`, never supplied by the caller.** The
  model cannot write an OG it likes into the database.
- **Validates before inserting anything**: a blank name raises, an empty item array
  raises, and an `ingredient_id` not in `brew.ingredients` raises — *"a recipe
  referencing a malt nobody stocks is not a recipe."*
- **Re-saving a name creates a new version**, `version = max+1`, with
  `parent_recipe_id` pointing at the previous row. Nothing is ever overwritten.
- `unit` per item is written through from the caller. It **was hardcoded to `'g'`**,
  which meant "2 vanilla beans" and "200 ml rum" were not expressible at all — which is
  half of why a flavouring used to be smuggled in under a malt's id.
- `p_additions` lands in `brew.recipes.additions` — the requested flavourings that have
  no honest PPG. `f_compute_recipe` never reads that column.

*Called by* `cap-formulate-recipe`

#### `brew.f_resolve_request()` — one verdict per requested ingredient

```sql
brew.f_resolve_request(p_terms text[])
RETURNS TABLE(term, verdict, ingredient_id, ingredient_name, ingredient_kind,
              n_corpus_recipes, note)
```

**Why it exists.** Before a recipe is built, each thing the brewer named has to be
classified: can we compute with it, do we merely know of it, or have we never heard of it?

| Verdict | Condition | Meaning |
|---|---|---|
| `catalogued` | matched a `brew.ingredients` row | has published specs; can enter the arithmetic |
| `known_uncatalogued` | no match, **≥ 20** corpus recipes | real, widely used, but no specs — goes on the sheet as an addition |
| `thin` | no match, 1–19 corpus recipes | attested but barely |
| `unknown` | no match, 0 corpus recipes | not in evidence at all |

- **Matching is two-directional**, because the brewer's phrasing can be longer than the
  catalogue name (`Weyermann Pale Ale Malt` → `Pale Ale Malt`) or shorter (`lactose` →
  `Lactose (milk sugar)`).
- **Punctuation and ® are stripped from both sides**, so `CARAFA® Type 1` and
  `carafa type 1` are the same string.
- Ranking prefers an exact hit, then the supplier-qualified form the brewer wrote —
  which is what separates Weyermann's `Pale Ale Malt` from Viking's `Pale Ale Malt
  Organic` — then the longest name as the most specific.
- ⚠️ **The corpus count is popularity, not quality.** The function's own comment:
  *a high count means popular, never good.*

*Reads* `brew.ingredients`, `corpus.recipe_search`, `nlq.f_resolve_ingredient_loose`,
`nlq.ingredient_practice` · *Called by* `cap-formulate-recipe`

#### `brew.f_catalogue()` — what we can compute with

```sql
brew.f_catalogue(p_kind text DEFAULT NULL)
RETURNS TABLE(id, kind, role, name, supplier, potential_ppg, color_lovibond,
              alpha_acid_pct, attenuation_pct)
```

The catalogue as the prompt sees it. Its one piece of intelligence is the derived
**`role`** column: fermentables are classified `base` / `caramel` / `roast` from
`color_lovibond` plus a name regex (`chocolate|black|roast|carafa|patent`), so the model
can pick a roast malt without knowing Lovibond scales. Everything else reports its `kind`.

`attenuation_pct` surfaces `attenuation_min`. ⚠️ `33_brew_yeast.sql` writes the same
figure to `attenuation_min` and `_max` **deliberately**, so it reads as a point estimate
rather than a range. Without this column a yeast row reaches the prompt as a bare name,
and catalogued yeast exists precisely so FG stops being a guess.

*Called by* `cap-formulate-recipe`, `recipe_eval.py`

#### `brew.f_dry_hop_rate_g_per_l()`

```sql
brew.f_dry_hop_rate_g_per_l(p_batch_id bigint) RETURNS numeric   -- STABLE, not SECDEF
```

Sums `recipe_items` at `stage = 'dryhop'` (normalising `kg` → `g`) over the batch volume.
⚠️ `brew.batches` is empty, so this has no live input; its only caller is `nlq.find_batches`.

#### Pure helpers

| Function | Returns | Notes |
|---|---|---|
| `brew.f_abv(og, fg)` | numeric | The standard correction formula, not the `(og-fg)×131` approximation: `76.08·(og−fg)/(1.775−og) · (fg/0.794)`. IMMUTABLE |
| `brew.f_kg_to_lb(kg)` | numeric | IMMUTABLE |
| `brew.f_l_to_gal(l)` | numeric | IMMUTABLE. Both exist so `f_compute_recipe` can work in the US units the PPG/Tinseth/Morey formulas are defined in, while every stored figure stays metric |

---

### 10.3 `ref` — reference lookups

#### `ref.f_style_bands()` — the envelope a recipe must land in

```sql
ref.f_style_bands(p_style text) RETURNS jsonb   -- STABLE SECDEF
```

Returns `{styles[], srm_min, srm_max, abv_min, abv_max, ibu_min, ibu_max}` for a style
named **in the brewer's own words**, as the envelope of the `ref.styles` rows that best
match those words.

Four rules, each of which prevents a specific wrong answer:

- ⛔ **NULL when nothing matches.** The caller must let the recipe through rather than
  invent a band. A missing guideline is not a constraint.
- ⛔ **`'beer'` as a head noun returns nothing.** It is the sentinel the parse step
  substitutes when no style was named, and it would otherwise match *Fruit Beer*,
  *Spice Beer* and the pastry row alike — *"which is not a style, it is a shrug."*
- **Only rows with `has_vitals`** participate; prose-only BA entries cannot contribute a band.
- **An ambiguous style widens the band, never narrows it** — `min` of the mins, `max` of
  the maxes across every equally-good match. And if *any* matched row has a NULL end,
  that end comes back NULL rather than pretending the others bound it.
- **`srm_max ≥ 40` is returned as NULL**, because 40+ in the guides means "black", an
  open bound, not a ceiling.

*Reads* `ref.styles` · *Called by* `cap-formulate-recipe`

#### `ref.f_range_text()`

```sql
ref.f_range_text(lo numeric, hi numeric, unit text DEFAULT '%') RETURNS text  -- IMMUTABLE
```

Range → prose, with the open ends handled: `up to 6%`, `3% or more`, `3-6%`, or `4%` when
both ends are equal; NULL when both are NULL. Used wherever numbers become cards or
`typical` strings, so an open bound reads as open instead of silently becoming a number.

*Called by* `nlq.cohort_stats`, `ingest-hop-varieties`, `hopslist_load.py`

---

### 10.4 `kb` — the ingest gate

#### `kb.promote_version()`

```sql
kb.promote_version(p_version_id bigint)
RETURNS TABLE(version_id bigint, is_current boolean, total bigint, missing bigint)
```

**Why it exists.** A half-embedded document must never become the live one. This is the
gate every ingest path ends on.

It counts chunks for the version and how many lack a `bge-m3` embedding, and **only if
`total > 0 AND missing = 0`** does it demote the document's other versions and promote
this one. Otherwise it changes nothing.

Either way it **returns the counts**, so the caller can assert on them — and every ingest
workflow does, in an `Assert promoted` node. A silent no-op that reports `missing: 14` is
the designed failure mode.

⚠️ The `'bge-m3'` model name is hardcoded here, unlike `search_knowledge` where it is a
parameter. Not `SECURITY DEFINER` — ingest runs as the owner anyway.

*Called by* all 6 ingest workflows, `hopslist_load.py`

---

### 10.5 `mem` — the learning layer

#### `mem.f_save_memory()`

```sql
mem.f_save_memory(p_kind text, p_content text, p_confidence numeric,
                  p_batch_id bigint DEFAULT NULL, p_source_turn bigint DEFAULT NULL,
                  p_status text DEFAULT 'pending') RETURNS bigint  -- VOLATILE SECDEF
```

Inserts one claim into `mem.memories`, hashing `content` to `content_sha256` for dedup
and defaulting to `status = 'pending'` — a memory is proposed, not asserted.

**The single function `mem_writer` was created for.** §8.4 Layer 2 of the architecture is
built on this pairing: the writer credential can execute this and nothing that reads
`brew.batches`, while the read credential physically cannot write.

⚠️ **Never called from a live path.** `mem.memories` is empty.

---

### 10.6 `obs` — the tracing API

Five writers, two readers, one trigger. All `SECDEF` with a pinned `search_path` except
the trigger.

| Function | Signature | What it does |
|---|---|---|
| `f_start_run` | `(p_session_id, p_turn_no, p_capability, p_budget jsonb) → bigint` | Opens a run row, returns its id. `status` defaults to `running`; `budget` is the caps the capability was given |
| `f_finish_run` | `(p_run_id, p_status, p_spent jsonb) → void` | Closes it: final status, what was actually spent, `finished_at = now()` |
| `f_log_step` | `(p_run_id, p_seq, p_step_id, p_kind, p_profile, p_model, p_model_loaded, p_prompt_sha256, p_input, p_output, p_verdict, p_tokens_in, p_tokens_out, p_latency_ms) → bigint` | One row per LLM or tool step. 14 arguments because the whole point is that nothing about a step is reconstructed later |
| `f_log_retrieval` | `(p_session_id, p_query, p_chunk_ids, p_top_k, p_mode, p_gap_terms DEFAULT '{}') → bigint` | Records what retrieval returned *and* which terms it could not cover. Empty `session_id` is normalised to NULL |
| `f_step_config` | `(p_profile, p_prompt_name) → TABLE(model, options, body, sha256)` | Resolves a step's model + options from `obs.profiles` and its **active** prompt version from `obs.prompts`, in one call. The `LEFT JOIN` means an unknown prompt name yields a model with a NULL body rather than no row |
| `f_session_chunk_ids` | `(p_session_id, p_since timestamptz) → bigint[]` | The chunk ids a session has already been shown |
| `f_prompt_hash` | `() → trigger` | Sets `NEW.sha256 = sha256(NEW.body)` on `obs.prompts`. This is why a prompt's hash can never disagree with its body |

⚠️ **`f_session_chunk_ids` returns the ids from the single most recent retrieval**, not
the union across the session (`ORDER BY created_at DESC LIMIT 1`, `coalesce` to `{}`).
The name suggests otherwise. It is what `chat-agent` uses to avoid re-citing the passage
it just cited, and what `grounding_eval.py` checks claims against.

---

### 10.7 `corpus` — the rebuild trio and two parsers

All three rebuilds are `VOLATILE SECDEF` with `search_path = corpus, ref, public`, and
all three are called by `scripts/ingest/corpus_load.py` in this order after a load.

| Function | Returns | What it rebuilds |
|---|---|---|
| `f_rebuild_dims()` | `TABLE(dimension text, rows bigint)` | The four dimension tables from the four fact tables: distinct names with observed statistics, `forms[]`/`uses[]`/`types[]` aggregated. Reports a row count per dimension so the caller can assert |
| `f_rebuild_styles()` | `TABLE(styles, bridged, manual)` | `corpus.styles` — distinct style strings with cached vitals, then the `ref.styles` bridge by normalised name. ⛔ **Never overwrites a `manual` bridge**, and the return value separates `bridged` from `manual` so a rebuild that silently lost a human decision would be visible |
| `f_rebuild_search()` | `bigint` | `corpus.recipe_search` — one flattened, GIN-indexed row per recipe. The fact tables stay authoritative; this is an index, not a copy |

| Function | Returns | Notes |
|---|---|---|
| `corpus.f_amount_value(p_raw)` | numeric | IMMUTABLE. Leading number out of a free-text amount (`'2 cups'` → `2`); NULL if the string does not start with one |
| `corpus.f_amount_unit(p_raw)` | text | IMMUTABLE. The remainder, lowercased (`'2 cups'` → `cups`); NULL when empty |

Both are **generated columns** on `corpus.recipe_misc`, which is why they must be
IMMUTABLE. They are the reason `ingredient_practice` can group by unit at all — and the
reason it must never convert between them.

---

## 11. Access model

Defined in `db/init/50_roles.sql` — a psql script, not portable SQL (`\gexec` and
`:'agent_pw'`), so it only runs via `docker compose up db-init`.

### 11.1 The roles, as measured

| Role | Schema `USAGE` | Table privileges | Function `EXECUTE` | Session settings |
|---|---|---|---|---|
| `agent_ro` (group, NOLOGIN) | `nlq` | `SELECT` on `nlq` | all of `nlq` **except** `f_refresh_corpus_lexemes` (explicitly revoked — it is the ingest path's) | — |
| `n8n_agent` (login) | inherits `agent_ro` → `nlq` only | — | — | `default_transaction_read_only = on` (an injected `DELETE` errors), `statement_timeout = 10s` |
| `mem_writer` (login) | `brew`, `ref`, `mem`, `obs`, `nlq` | `INSERT, SELECT` on `mem.chat_turns` — **and nothing else** | `mem.f_save_memory`, `brew.f_catalogue`, `f_resolve_request`, `f_compute_recipe`, `f_fit_recipe`, `f_fit_ibu`, `f_fit_to_abv`, `f_save_recipe`, `ref.f_style_bands`; plus all of `obs.*` via default PUBLIC EXECUTE | `statement_timeout = 10s`, **not** read-only |
| `supabase_admin` / `postgres` | everything | owner | owner | **`postgres` is not a superuser in this stack** |

`kb`, `brew`, `ref`, `mem` and `corpus` are `REVOKE ALL … FROM PUBLIC`. A
"permission denied for schema kb" in n8n is this file working as designed —
`mem_writer` has no `kb` grant at all, and reaches knowledge only through `nlq`.

⚠️ **`mem_writer` is misleadingly named.** It is not the learning-layer writer its name
and `50_roles.sql` §5 comment suggest — it is the *capability-workflow* credential.
Its only table privilege is `INSERT, SELECT` on `mem.chat_turns`; everything else it
does goes through `SECURITY DEFINER` functions. The design property still holds: it
**cannot read `brew.batches`**, because no function it can execute selects from them.

### 11.2 Which credential each workflow actually uses

`measured` from the `credentials` block of every tracked workflow JSON.

| Credential | Workflows | Reach |
|---|---|---|
| `n8n_agent` | `wf-step-practice`, `wf-step-retrieve-keywords`, `wf-step-retrieve` (the read nodes) | `nlq` only, read-only |
| `Postgres — mem_writer` | `cap-formulate-recipe`, `cap-brainstorm-pairing`, `wf-step-llm`, `wf-step-retrieve` (the `obs.f_log_retrieval` write), `chat-agent` (the `mem.chat_turns` write) | `brew`/`ref`/`obs`/`mem`/`nlq` functions |
| `Postgres account` (owner) | all 5 structured `ingest-*`, `wf1-ingest-book`, `chat-agent` (LangChain chat-memory node → `public.n8n_chat_histories`) | everything |

The split inside a single workflow is the point: `wf-step-retrieve` reads through
`n8n_agent` and logs through `mem_writer`, so the retrieval query itself runs on a
connection that physically cannot write.

---

## 12. Search infrastructure

| Index | On | Type | Serves |
|---|---|---|---|
| `chunk_embeddings_hnsw_idx` | `kb.chunk_embeddings.embedding` | HNSW cosine, `m=16 ef_construction=64` | the vector leg of `nlq.search_knowledge` |
| `chunks_fts_idx` | `kb.chunks.fts` | GIN tsvector | the FTS leg of `nlq.search_knowledge`, `nlq.corpus_coverage` |
| `chunks_raw_trgm_idx` | `kb.chunks.raw_content` | GIN trigram | the rare-term leg of `nlq.search_knowledge` |
| `corpus_search_ing_idx` | `corpus.recipe_search.ingredients` | GIN array | `nlq.f_cohort_ids` |
| `corpus_search_style_idx` | `corpus.recipe_search.style_key` | GIN trigram | `nlq.f_cohort_ids` |
| `memory_embeddings_hnsw_idx` | `mem.memory_embeddings.embedding` | HNSW cosine | nothing yet |
| `styles/hops/malts/faults_name_trgm_idx` | `ref.*` name columns | GIN trigram | `ref.f_style_bands`, catalogue seeds |
| `sensory_notes_fts_idx`, `sensory_notes_desc_idx` | `brew.sensory_notes` | GIN tsvector / array | `nlq.find_batches` (unused) |

⚠️ `vector`, `pg_trgm` and `unaccent` are installed in the **`public`** schema.

---

## 13. Where the schema is defined

`db-init` applies a **hardcoded list** of files on every stack start (the `for f in …`
loop at `docker-compose.yml:182`). A new `.sql` must be added to that list, and the
catalog should be checked before assuming an object is missing.

| File | Defines |
|---|---|
| `00_extensions.sql` | `vector`, `pg_trgm`, `unaccent` |
| `10_kb.sql` | the `kb` schema + `promote_version` |
| `15_ref.sql` | `ref.styles`, `ref.hops`, `ref.faults`, `f_range_text` |
| `20_brew.sql` | the seven `brew` tables |
| `26_ref_malts.sql` | `ref.malts` |
| `27`–`33` | `brew.ingredients` catalogue seeds from `ref.malts` / `ref.hops` / `corpus.yeasts` (malt, derived sugars, misc, sugars, yeast) + `f_compute_recipe`, `f_fit_*`, `f_save_recipe` |
| `30_mem.sql` | the `mem` schema |
| `35_nlq_evidence.sql`, `40_nlq.sql` | `nlq` functions, `corpus_lexemes`, `search_knowledge` |
| `50_roles.sql` | `agent_ro`, `n8n_agent`, `mem_writer` |
| `60`–`63` | `obs` schema, prompt registry seeds, model profiles |
| `70`–`74` | `corpus` fact tables, dimensions, nlq-over-corpus, search index, style bridge |

---

## 14. Dead ends and gaps

Everything below is built and reachable in SQL but has **no chain to a user**.

| Thing | State |
|---|---|
| `brew.batches` / `measurements` / `sensory_notes` / `inventory` | Built, indexed, **empty**. `nlq.find_batches()` and `brew.f_dry_hop_rate_g_per_l()` read them and nothing calls either |
| `mem.memories` / `mem.memory_embeddings` | Full lifecycle design, **empty**. `mem.f_save_memory()` is granted to `mem_writer` but never called from a live path |
| `nlq.find_batches()` | The only `nlq` function with no caller anywhere in the repo |
| `nlq.ingredient_usage()` | Reachable only through `nlq.ingredient_practice()`; never called directly |
| `kb.ingest_log` | Written at every ingest stage, read by **no** function, workflow or script — humans only |
| `ref.malts` | No runtime reader. Reaches the agent only as `brew.ingredients` rows seeded at `db-init` time |
| `corpus.styles` | 104 of 181 bridged to `ref.styles` (1 manually); 77 have no guideline link. Read only by its own rebuild and `v_styles_unbridged` — `nlq.f_corpus_styles()` goes to `corpus.recipes.style_raw` instead |
| `public.n8n_chat_histories` | RLS off, 0 policies, `anon` holds DELETE/TRUNCATE — §9 |
| Mutable `search_path` | `kb.promote_version`, `brew.f_abv`, `brew.f_dry_hop_rate_g_per_l`, `obs.f_prompt_hash`. ⚠️ None is `SECURITY DEFINER`, so this is **not** the escalation hole — all seven SECURITY DEFINER functions do set `search_path` |
| `supabase_read_only_user` | Ships with no password upstream; the Supabase MCP read-path tools fail until it is given one, and `db-passwd.sh` skips it on every rotation |
