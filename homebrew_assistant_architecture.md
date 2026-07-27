# Homebrewing Assistant — Target Architecture (fresh rebuild)

**Date:** 2026-07-22 · **Hardware:** Ryzen 9900X / RX 9070 XT (16 GB VRAM, gfx1201) / 32 GB RAM · **Profile:** `gpu-amd`

---

## Flagged decision, now resolved: answer language

The **Setup** and **Project context** docs both said Hungarian; this task brief said English. **Confirmed: English-only** — both corpus and queries, no cross-lingual requirement. This closes what was originally D1 and simplifies the embedder choice (§4): no need to weight cross-lingual EN↔HU performance, so pick on English retrieval quality alone. **Decisions-log entry: "Answer language: English only. No cross-lingual retrieval requirement."**

If this ever changes, the affected sections are §4.2–4.3 (embedder pick would need cross-lingual weighting again), §7.8 (system prompt currently hardcodes English rather than taking a language parameter), and §10.1 (the eval set below has no non-English cases).

---

## 1. Executive summary

- **Delete Qdrant from the design.** Your corpus is O(10⁴–10⁵) chunks. pgvector + HNSW + Postgres FTS fused with RRF handles this with room to spare, in the database that already holds your truth data. A second vector store means a second sync path and a second source of truth — the exact failure mode your own architecture rule 1 exists to prevent. Exit criteria in §3.6.
- **Delete the flat `documents` table (all ~117 rows).** Do not migrate it. Replace with a 4-table knowledge model: `kb.documents` → `kb.document_versions` → `kb.chunks` → `kb.chunk_embeddings`. Migrating chunks produced by the wrong splitter would poison your eval baseline on day one.
- **Stop chunking in n8n.** Docling Serve now exposes chunking endpoints backed by `HybridChunker` (tokenizer-aware, layout-aware, `contextualize()` prepends the heading path). Your n8n heading-splitter is a worse reimplementation that throws away page provenance. This is the single biggest quality win available.
- **Four schemas, not one namespace:** `kb` (knowledge), `brew` (truth), `mem` (agent memory), `nlq` (the *only* surface the agent can touch). Schema separation is your read-only enforcement mechanism, not just tidiness.
- **Chat model: `gemma4:12b`.** Apache 2.0, native tool calling, 140+ pretrained languages, ~9 GB at Q4 — leaves headroom on a 16 GB card for KV cache *and* a resident embedder. `qwen3:14b` is the fallback if tool-calling eval disappoints.
- **Embedder: `bge-m3`, 1024 dimensions.** Strong English retrieval, 8k context. **Standardise the schema on 1024 dims** so you can A/B against `qwen3-embedding` (MRL-truncatable to 1024) without a migration.
- **The repo's 1536-dim pgvector snippet is wrong and must be deleted.** It is OpenAI-shaped. No Ollama-served embedder is natively 1536-dim.
- **AI Agent + guarded tools, not a monolithic RAG chain.** Your knowledge/truth split *requires* routing; a single retrieval chain structurally cannot honour it. But cap Phase 3 at ~7 tools — a 12B model's tool selection degrades fast beyond that.
- **No Python sidecar in v1.** Brewing math (ABV, IBU, SRM, dry-hop rate) belongs in Postgres functions: deterministic, testable, reusable inside NLQ views. The only justified sidecar is a reranker in Phase 5, and only if eval demands it.
- **First build step:** confirm `bge-m3` returns 1024 dims on your GPU, then run the `kb` DDL. Everything downstream is dimension-locked. See **Start tomorrow**.

---

## 2. Target architecture

```mermaid
flowchart TB
    subgraph SHARED["./shared — host filesystem"]
        PEND["rag-files/pending/"]
        PROC["rag-files/processed/"]
        IMGD["extracted-images/"]
    end

    subgraph NOTN8N["🚫 Deliberately NOT in n8n"]
        DOC["Docling Serve :5001<br/>convert + HybridChunker<br/><i>async endpoints only</i>"]
        PGF["Postgres functions<br/>nlq.search_knowledge (RRF)<br/>brew.f_abv / f_ibu / f_dry_hop_rate"]
        NGX["nginx :8080<br/>image serving"]
        OLL["Ollama ROCm :11434<br/>gemma4:12b + bge-m3"]
    end

    subgraph N8NBOX["n8n :5678 — orchestration and glue ONLY"]
        W1["WF1 ingest-document"]
        W2["WF2 ingest-structured"]
        W3["WF3 import-batch"]
        W4["WF4 chat-agent"]
        W5["WF5 learn-from-chat"]
        W6["WF6 eval-runner"]
        W7["WF7 reindex-embeddings"]
    end

    subgraph SUPA["Supabase Postgres :5432 — centre of gravity"]
        KB["kb.*<br/>documents / versions<br/>chunks / chunk_embeddings"]
        BREW["brew.*<br/>recipes / batches / inventory<br/>measurements / sensory / bjcp_styles"]
        MEM["mem.*<br/>preferences / lessons<br/>corrections / chat_turns"]
        NLQ["nlq.*<br/>read-only views + functions<br/><b>the agent's only surface</b>"]
    end

    N8NPG["n8n Postgres<br/><i>workflow metadata only —<br/>never app data</i>"]

    PEND --> W1 --> DOC
    DOC -->|"chunks + heading paths<br/>+ page provenance"| W1
    DOC --> IMGD
    W1 -->|"embed batch"| OLL
    W1 --> KB
    W1 -->|"on success"| PROC

    W2 --> BREW
    W3 --> BREW

    W4 <-->|"tool calls"| NLQ
    W4 <--> OLL
    NLQ -.->|"SECURITY DEFINER"| KB
    NLQ -.-> BREW
    NLQ -.-> MEM
    PGF -.- NLQ

    W4 -->|"log every turn"| MEM
    W4 -.->|"fire and forget"| W5
    W5 -->|"confirm-before-write"| MEM

    W6 --> W4
    W6 --> MEM
    W7 --> KB
    W7 --> OLL

    IMGD --> NGX
    NGX -.->|"resolved at answer<br/>assembly, never stored"| W4

    N8NBOX -.- N8NPG

    CHAT["chat.html<br/>@n8n/chat widget<br/>streaming enabled"] <--> W4
```

### What sits where, and why

| Concern | Home | Rationale |
|---|---|---|
| PDF → structured document | Docling Serve | Purpose-built; layout + table models already tuned |
| Chunking | Docling `HybridChunker` | Tokenizer-aware, preserves heading path + page prov. n8n cannot do this |
| Embedding generation | Ollama, **called from** n8n | n8n handles batching/retry; the model does the work |
| Hybrid search + fusion | Postgres function | One round trip, one query planner, indexes actually used. Doing RRF in a Code node means shipping 80 rows into JS to sort them |
| Brewing math | Postgres functions | Deterministic, unit-testable, composable into views. **Never** the LLM |
| Tool routing / agent loop | n8n AI Agent | This is what n8n is genuinely good at |
| State machine / idempotency | Postgres, **not the filesystem** | See §3.7 — `processed/` markers are advisory only |
| Bulk re-embedding (>10k chunks) | One-off script | n8n item explosion + memory. §5 WF7 |

**The rule of thumb:** n8n moves data and makes decisions about *which* thing to call. The moment a node is transforming text or computing a number, ask whether Postgres or Docling should own it.

---

## 3. Storage design

Four schemas. The separation is a security boundary, not decoration — the agent's DB credential gets rights on `nlq` and nothing else.

```sql
CREATE SCHEMA kb;    -- knowledge: what books say
CREATE SCHEMA brew;  -- truth: what I actually did
CREATE SCHEMA mem;   -- agent memory: what I've learned about you
CREATE SCHEMA nlq;   -- the only surface the agent may touch
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
```

### 3.1 Domain → home

| Domain | Home | Search mode |
|---|---|---|
| Ingredients, inventory, recipes, batches, measurements, sensory notes | `brew.*` | **SQL only.** Never vectorised |
| BJCP styles | `brew.bjcp_styles` (numeric ranges) **+** a generated style-card chunk in `kb` | **Both** — see §3.5 |
| Book / PDF corpus | `kb.documents` + `kb.document_versions` | metadata SQL |
| Chunks + embeddings | `kb.chunks` + `kb.chunk_embeddings` | **Hybrid: FTS + vector, fused with RRF** |
| Preferences, lessons, corrections | `mem.*` + `mem.memory_embeddings` | **Separate vector space** — never fused with `kb` |
| Chat turns | `mem.chat_turns` | SQL |
| PDFs, extracted images | filesystem `./shared`, served by nginx | path refs in DB |

### 3.2 Knowledge schema (replaces the flat `documents` table)

```sql
-- One row per logical source document
CREATE TABLE kb.documents (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  slug         text NOT NULL UNIQUE,            -- 'stout-style-guide'
  title        text NOT NULL,
  doc_type     text NOT NULL
               CHECK (doc_type IN ('book','style_guide','article','datasheet','note')),
  authors      text[],
  language     text NOT NULL DEFAULT 'en',
  edition_note text,
  created_at   timestamptz NOT NULL DEFAULT now()
);

-- One row per ingested file revision. Idempotency lives here.
CREATE TABLE kb.document_versions (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  document_id     bigint NOT NULL REFERENCES kb.documents(id) ON DELETE CASCADE,
  version         int    NOT NULL,
  source_filename text   NOT NULL,
  file_sha256     char(64) NOT NULL,
  docling_version text,
  chunker_config  jsonb  NOT NULL,   -- {max_tokens, tokenizer, merge_peers}
  page_count      int,
  image_dir       text,              -- RELATIVE: 'stout-style-guide/'
  ingested_at     timestamptz NOT NULL DEFAULT now(),
  is_current      boolean NOT NULL DEFAULT true,
  UNIQUE (document_id, version),
  UNIQUE (file_sha256)               -- same bytes never ingested twice, ever
);
CREATE UNIQUE INDEX ON kb.document_versions (document_id) WHERE is_current;

CREATE TABLE kb.chunks (
  id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  version_id     bigint NOT NULL REFERENCES kb.document_versions(id) ON DELETE CASCADE,
  chunk_index    int    NOT NULL,
  content        text   NOT NULL,   -- contextualized: heading path + body (what you EMBED)
  raw_content    text   NOT NULL,   -- body only (what you SHOW)
  heading_path   text[],            -- {'Stout','Irish Stout','Vital Statistics'}
  page_from      int,
  page_to        int,
  token_count    int,
  image_refs     text[],            -- {'image_017.png'} — filenames only
  content_sha256 char(64) NOT NULL,
  fts            tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
  UNIQUE (version_id, chunk_index)
);
CREATE INDEX ON kb.chunks USING gin (fts);
CREATE INDEX ON kb.chunks (content_sha256);          -- enables embedding reuse across versions
CREATE INDEX ON kb.chunks USING gin (raw_content gin_trgm_ops);  -- fuzzy fallback

-- Keyed by model so you can A/B embedders without re-chunking
CREATE TABLE kb.chunk_embeddings (
  chunk_id   bigint NOT NULL REFERENCES kb.chunks(id) ON DELETE CASCADE,
  model      text   NOT NULL,       -- 'bge-m3'
  embedding  vector(1024) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chunk_id, model)
);
CREATE INDEX ON kb.chunk_embeddings USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
```

**Why embeddings are a separate table.** Your architecture rule 8 is "measure before adding complexity." That is only possible if you can hold two embedders' vectors side by side and run the same eval against both. An `embedding` column on `kb.chunks` makes that a destructive migration. The cost is one join on a table you'll never grow past ~10⁵ rows — free.

**The dimension trap, stated honestly.** pgvector needs a fixed dimension per indexed column, so this table can only hold 1024-dim models. That is a real constraint and I'm choosing it deliberately: `bge-m3` is 1024 native, and `qwen3-embedding` (0.6B/4B/8B) is MRL-truncatable to 1024. That gives you a four-way A/B inside one schema. The price is that `embeddinggemma` (768 native, not MRL) is excluded. Worth it.

### 3.3 Truth schema (sketch)

```sql
CREATE TABLE brew.ingredients (
  id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  kind      text NOT NULL CHECK (kind IN ('fermentable','hop','yeast','water_agent','adjunct','misc')),
  name      text NOT NULL,
  supplier  text,
  -- promoted columns used in filters/math:
  alpha_acid_pct  numeric(5,2),   -- hops
  color_lovibond  numeric(6,2),   -- fermentables
  potential_ppg   numeric(5,1),
  attenuation_min numeric(4,1),   -- yeast
  attenuation_max numeric(4,1),
  attrs     jsonb NOT NULL DEFAULT '{}',   -- everything else, kind-specific
  UNIQUE (kind, name, supplier)
);

CREATE TABLE brew.inventory (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ingredient_id bigint NOT NULL REFERENCES brew.ingredients(id),
  lot_code      text,
  qty           numeric(10,3) NOT NULL,
  unit          text NOT NULL CHECK (unit IN ('g','kg','ml','l','pkg','ea')),
  acquired_on   date,
  best_before   date,
  location      text,
  notes         text
);

CREATE TABLE brew.bjcp_styles (
  id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  guide_year int NOT NULL,
  code     text NOT NULL,          -- '15B'
  name     text NOT NULL,          -- 'Irish Stout'
  category text,
  og_min numeric(5,3), og_max numeric(5,3),
  fg_min numeric(5,3), fg_max numeric(5,3),
  ibu_min int, ibu_max int,
  srm_min numeric(4,1), srm_max numeric(4,1),
  abv_min numeric(4,2), abv_max numeric(4,2),
  overall_impression text, aroma text, appearance text,
  flavor text, mouthfeel text, comments text,
  commercial_examples text[],
  UNIQUE (guide_year, code)
);

CREATE TABLE brew.recipes (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name text NOT NULL, version int NOT NULL DEFAULT 1,
  parent_recipe_id bigint REFERENCES brew.recipes(id),
  style_id bigint REFERENCES brew.bjcp_styles(id),
  batch_size_l numeric(6,2) NOT NULL,
  target_og numeric(5,3), target_fg numeric(5,3),
  target_ibu int, target_srm numeric(4,1),
  mash_profile jsonb, water_profile jsonb, notes text,
  UNIQUE (name, version)
);

CREATE TABLE brew.recipe_items (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  recipe_id bigint NOT NULL REFERENCES brew.recipes(id) ON DELETE CASCADE,
  ingredient_id bigint NOT NULL REFERENCES brew.ingredients(id),
  stage text NOT NULL CHECK (stage IN ('mash','boil','whirlpool','dryhop','fermenter','packaging')),
  qty numeric(10,3) NOT NULL, unit text NOT NULL,
  timing_min int,          -- boil time remaining, or days for dry hop
  notes text
);

CREATE TABLE brew.batches (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  recipe_id bigint REFERENCES brew.recipes(id),
  batch_no text NOT NULL UNIQUE,
  brewed_on date NOT NULL, packaged_on date,
  volume_l numeric(6,2),
  og numeric(5,3), fg numeric(5,3),
  status text NOT NULL DEFAULT 'planned'
         CHECK (status IN ('planned','fermenting','conditioning','packaged','archived')),
  notes text
);

CREATE TABLE brew.measurements (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id bigint NOT NULL REFERENCES brew.batches(id) ON DELETE CASCADE,
  taken_at timestamptz NOT NULL,
  kind text NOT NULL CHECK (kind IN ('gravity','temp_c','ph','pressure','do_ppb','volume_l')),
  value numeric(10,4) NOT NULL,
  device text, notes text
);

CREATE TABLE brew.sensory_notes (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id bigint NOT NULL REFERENCES brew.batches(id) ON DELETE CASCADE,
  tasted_at date NOT NULL,
  days_since_packaging int,
  aroma text, appearance text, flavor text, mouthfeel text, overall text,
  score numeric(3,1),
  descriptors text[],       -- {'bitter','resinous','dank'} — the NLQ filter surface
  fts tsvector GENERATED ALWAYS AS (
    to_tsvector('english',
      coalesce(aroma,'')||' '||coalesce(flavor,'')||' '||
      coalesce(mouthfeel,'')||' '||coalesce(overall,''))) STORED
);
CREATE INDEX ON brew.sensory_notes USING gin (fts);
CREATE INDEX ON brew.sensory_notes USING gin (descriptors);
```

**Brewing math as Postgres functions** — not n8n, not the LLM:

```sql
CREATE FUNCTION brew.f_abv(og numeric, fg numeric) RETURNS numeric
  LANGUAGE sql IMMUTABLE AS
$$ SELECT round(((76.08 * (og - fg) / (1.775 - og)) * (fg / 0.794))::numeric, 2) $$;

CREATE FUNCTION brew.f_dry_hop_rate_g_per_l(p_batch_id bigint) RETURNS numeric
  LANGUAGE sql STABLE AS $$
  SELECT round(
    sum(CASE ri.unit WHEN 'kg' THEN ri.qty*1000 ELSE ri.qty END)
      / NULLIF(max(b.volume_l), 0), 2)
  FROM brew.batches b
  JOIN brew.recipe_items ri ON ri.recipe_id = b.recipe_id AND ri.stage = 'dryhop'
  WHERE b.id = p_batch_id
$$;
```

Add `f_ibu_tinseth`, `f_srm_morey`, `f_gravity_temp_correct` the same way. These become columns in NLQ views, so "dry hop rate above 8 g/L" is a `WHERE` clause, not an LLM arithmetic exercise.

### 3.4 Hybrid retrieval function (the thing that must not live in n8n)

```sql
CREATE OR REPLACE FUNCTION nlq.search_knowledge(
  p_query_text  text,
  p_query_embed vector(1024),
  p_limit       int  DEFAULT 6,
  p_candidates  int  DEFAULT 40,
  p_rrf_k       int  DEFAULT 50,
  p_model       text DEFAULT 'bge-m3',
  p_doc_type    text DEFAULT NULL
) RETURNS TABLE (
  chunk_id bigint, doc_slug text, doc_title text, heading_path text[],
  page_from int, page_to int, raw_content text, image_refs text[],
  image_dir text, score real
) LANGUAGE sql STABLE SECURITY DEFINER SET search_path = kb, public AS $$
WITH kw AS (
  SELECT c.id, row_number() OVER (
           ORDER BY ts_rank_cd(c.fts, websearch_to_tsquery('english', p_query_text)) DESC) AS rk
  FROM kb.chunks c
  JOIN kb.document_versions v ON v.id = c.version_id AND v.is_current
  JOIN kb.documents d ON d.id = v.document_id
  WHERE c.fts @@ websearch_to_tsquery('english', p_query_text)
    AND (p_doc_type IS NULL OR d.doc_type = p_doc_type)
  LIMIT p_candidates
),
vec AS (
  SELECT c.id, row_number() OVER (ORDER BY e.embedding <=> p_query_embed) AS rk
  FROM kb.chunk_embeddings e
  JOIN kb.chunks c ON c.id = e.chunk_id
  JOIN kb.document_versions v ON v.id = c.version_id AND v.is_current
  JOIN kb.documents d ON d.id = v.document_id
  WHERE e.model = p_model
    AND (p_doc_type IS NULL OR d.doc_type = p_doc_type)
  ORDER BY e.embedding <=> p_query_embed
  LIMIT p_candidates
),
fused AS (
  SELECT COALESCE(kw.id, vec.id) AS id,
         COALESCE(1.0/(p_rrf_k + kw.rk), 0) + COALESCE(1.0/(p_rrf_k + vec.rk), 0) AS score
  FROM kw FULL OUTER JOIN vec ON kw.id = vec.id
)
SELECT c.id, d.slug, d.title, c.heading_path, c.page_from, c.page_to,
       c.raw_content, c.image_refs, v.image_dir, f.score::real
FROM fused f
JOIN kb.chunks c ON c.id = f.id
JOIN kb.document_versions v ON v.id = c.version_id
JOIN kb.documents d ON d.id = v.document_id
ORDER BY f.score DESC
LIMIT p_limit;
$$;
```

Over-fetch 40 from each arm, fuse, return 6. Over-fetching gives RRF more signal than pulling 6 from each — this is consistently reported as the single cheapest retrieval improvement available.

**Search mode per domain:**

| Domain | Mode | Why |
|---|---|---|
| Book/PDF chunks | **Hybrid RRF** | Vector misses exact terms ("Kolsch", "diacetyl rest", "60 IBU"); FTS misses paraphrase |
| BJCP style cards | Hybrid RRF, `doc_type='style_guide'` filter | Same, plus a cheap namespace filter |
| Sensory notes | **FTS + array containment only** | Truth data. `descriptors @> '{bitter}'` is exact and auditable |
| Inventory / batches / recipes | **SQL only** | Vector search on a count is a category error |
| Agent memory | Vector, but in `mem.memory_embeddings` | Separate index so a preference can never outrank a book on a knowledge question |

### 3.5 BJCP: the case that is neither pure knowledge nor pure truth

Style guides are structured data wearing prose clothing. Handle both ways:

1. **Structured** → `brew.bjcp_styles` rows with real numeric ranges. Answers *"is my 1.048 OG in range for 15B?"* — a `BETWEEN`, not a retrieval.
2. **Narrative** → for each style, generate one synthetic "style card" chunk (`doc_type='style_guide'`) from the prose fields and embed it. Answers *"what's the difference between a porter and a stout?"* — genuinely a semantic question.

The style-card generator is a single SQL `INSERT ... SELECT` in WF2, so the two representations cannot drift.

### 3.6 Explicit decision: pgvector-only. Delete Qdrant.

**Decision: pgvector only. Remove Qdrant from `docker-compose.yml` in Phase 0.**

Reasoning:
- **Scale doesn't justify it.** Twenty brewing books ≈ 8k pages ≈ 40–60k chunks. HNSW on 60k × 1024-dim vectors is a sub-50 ms query and roughly 250 MB of index. Reported experience is that pgvector stays comfortable well past 500k chunks.
- **Hybrid is easier in Postgres, not harder.** FTS and vectors in one query planner, one transaction, one RRF function. With Qdrant you fuse across a network boundary — in n8n, in JavaScript.
- **RAM.** You have 32 GB feeding the full Supabase stack, Docling-ROCm (PyTorch), n8n, Ollama's host-side buffers, and nginx. Qdrant is pure overhead you can spend on Postgres `shared_buffers` instead.
- **It violates your own rule 1.** Two vector stores means a reconciliation problem you will eventually get wrong.

**Exit criteria — revisit Qdrant only if ALL of these hold after Phase 3:**

| # | Condition | Threshold |
|---|---|---|
| 1 | Corpus size | > 500k chunks |
| 2 | Retrieval hit-rate@5 on the book-RAG eval set | < 0.75 **after** fixing chunking and tuning RRF `k` |
| 3 | p95 retrieval latency | > 500 ms with HNSW `ef_search` tuned |
| 4 | You need a capability Postgres lacks | e.g. `bge-m3` multi-vector/ColBERT scoring, or payload-filtered quantised search |

Conditions 1–3 will almost certainly never fire at your scale. Condition 4 is the only honest reason, and it's a Phase 5 experiment, not an architecture decision. **If retrieval is bad, the cause is chunking or the embedder — not the vector store.** Fix those first; a different ANN index over the same bad chunks returns the same bad chunks.

### 3.7 Idempotency, dedup, versioning

**The database is the state machine. The filesystem is advisory.** Your current `pending/` → `processed/` design makes the filesystem authoritative, which breaks the moment a run dies between "embedded" and "moved".

```
pending/Stout-Style-Guide.pdf
  │
  ├─ sha256 the file
  ├─ SELECT 1 FROM kb.document_versions WHERE file_sha256 = $1
  │     └─ HIT  → move to processed/, log "already ingested", STOP
  │
  ├─ Docling convert+chunk (async, poll)
  ├─ INSERT kb.document_versions (is_current = false)   ← invisible while building
  ├─ INSERT kb.chunks  (batched)
  ├─ Embedding reuse: for each chunk, if content_sha256 exists in a prior
  │    version of the SAME document, copy the vector instead of re-embedding
  ├─ Embed the remainder in batches of 32
  ├─ TRANSACTION:
  │     UPDATE ... SET is_current = false WHERE document_id = X;
  │     UPDATE ... SET is_current = true  WHERE id = <new version>;
  └─ move to processed/  ← last step, purely cosmetic
```

- **Dedup:** `UNIQUE (file_sha256)` on versions. Byte-identical file can never be ingested twice.
- **Versioning:** re-ingesting an edited PDF creates version N+1. The unique partial index on `is_current` makes the cutover atomic; old chunks stay for audit but are excluded from search by the `is_current` join.
- **Embedding reuse:** `content_sha256` on chunks means re-ingesting a book where you fixed one typo re-embeds one chunk, not 3,000.
- **Crash safety:** a half-built version has `is_current = false` and is invisible. Cleanup is `DELETE FROM kb.document_versions WHERE NOT is_current AND ingested_at < now() - interval '1 day' AND id NOT IN (SELECT ...)` — or just leave it.

### 3.8 Image reference mapping

Docling emits `![Image](image_017.png)` with `image_export_mode: "referenced"`, writing files under `./shared/extracted-images/`.

**Never store `http://localhost:8080/...` in chunk text.** The port, host and mount are deployment details; baking them into 40k rows means a re-ingest when any of them changes.

Instead:

1. **At ingest**, extract image filenames into `kb.chunks.image_refs[]` and replace the markdown ref in `raw_content` with a stable token: `[[IMG:image_017.png]]`.
2. Store the per-version directory once: `kb.document_versions.image_dir = 'stout-style-guide/'`.
3. **At answer assembly** (inside the retrieval tool sub-workflow), resolve:
   `{{ $env.IMAGE_BASE_URL }}/{{ image_dir }}{{ ref }}` → `http://localhost:8080/stout-style-guide/image_017.png`
4. `IMAGE_BASE_URL` is one n8n environment variable. Changing the port is a one-line edit.

For chat rendering, the tool returns images as a separate `images[]` array rather than inline markdown — the `@n8n/chat` widget renders markdown, but keeping images structured lets you cap how many reach the model's context (images are for the *human*, not the LLM; do not spend context tokens on URLs the model can't see).

---

## 4. Local model stack

### 4.1 Hardware reality check

RX 9070 XT is **gfx1201 (RDNA 4)**, which needs ROCm 7.x. On Linux + Docker this is a solved problem — `ollama/ollama:rocm` works on the 9070 XT, and llama.cpp HIP builds work by targeting gfx1201. (The painful path is the Windows installer, which ships ROCm 6.4.2 libraries with no gfx12xx kernels and silently falls back to CPU after a 30-second hang. You are on Docker/Linux, so this doesn't apply — but **verify** rather than assume.)

**Acceptance test before anything else:** load a model, run `ollama ps`, confirm `size_vram` equals the full model size and the processor column reads 100% GPU. If any part sits in system RAM you are swapping, and first-token latency goes from ~1 s to 5–15 s.

**16 GB VRAM budget:**

```
gemma4:12b @ Q4_K_M        ~8.5 GB
KV cache @ num_ctx 12288    ~1.5 GB
bge-m3 (568M) resident      ~1.2 GB
compute buffers / headroom  ~2.0 GB
                            ───────
                            ~13.2 GB   ✅ fits with margin
```

That margin is the whole design. It is why I'm not recommending a 24B–27B model: `gemma4:26b-a4b` needs ~18 GB loaded (Ollama loads all 26B even though only ~4B are active per token), which spills to system RAM and costs you the resident embedder.

### 4.2 Recommendations

| Role | Model | Size @ Q4 | Notes |
|---|---|---|---|
| **Main chat** | `gemma4:12b` | ~8.5 GB | Apache 2.0. Native tool calling on every size (~86% reported accuracy). Strong English reasoning and instruction-following for its size. 256K context nominal; **run it at 8–12k**, you cannot afford the KV cache |
| **Embedding** | `bge-m3` | ~1.2 GB | **1024 dim**, 8192 ctx, strong English retrieval quality, good margin over `nomic-embed-text` on BEIR-style tasks. `keep_alive: -1` |
| **Reranker** | *none in v1* | — | See §4.4 |
| **Small utility** | *none in v1* | — | See §4.5 |

### 4.3 Comparison of the candidates you named

| Model | Dim / Size | Verdict |
|---|---|---|
| **`llama3.2` (3B)** | ~2 GB | ❌ **Delete.** A compose default, not a choice. 3B tool-calling is unreliable and brewing reasoning is thin. Nothing in your design should depend on it |
| **`gemma4:12b`** | ~8.5 GB | ✅ **Recommended.** Best reasoning-per-GB at this size, Apache 2.0, tool calling native |
| **`qwen3:14b`** | ~9–10 GB | ⚠️ **Primary fallback.** Excellent reasoning and tool calling; thinking mode adds latency you must disable for chat. Switch to this if Gemma's tool-selection eval underperforms |
| `qwen3:8b` | ~5–6 GB | Viable if you want a bigger KV cache. Matches Qwen2.5-14B on benchmarks |
| `qwen3.5:9b` / `qwen3.6:27b` | varies | Sources conflict on which tags actually exist. **Check `ollama.com/library` before pulling** — do not design around a tag you haven't verified. The 27B doesn't fit anyway |
| `gemma4:26b-a4b` | ~18 GB | ❌ Doesn't fit. MoE speed, dense memory footprint |
| `mistral-small` variants | ~14 GB @ 24B | ⚠️ Now Apache 2.0, decent, but leaves no room for a resident embedder |
| **`bge-m3`** | **1024** | ✅ **Recommended embedder** |
| `nomic-embed-text` | 768 | ⚠️ Viable alternative — English-only corpus makes this less of a mismatch than it would otherwise be. Note its Ollama card lists 2048 ctx despite 8192 native — set `num_ctx` manually if you use it. `bge-m3` still edges it on retrieval benchmarks, which is the actual reason to prefer it |
| `qwen3-embedding:0.6b` | 1024 (MRL) | ✅ **A/B candidate.** Instruction-aware; needs `Instruct: …\nQuery: …` prefixing or quality drops measurably |
| `qwen3-embedding:4b` | MRL→1024 | Better retrieval, ~3 GB. Only if the chat model's VRAM budget allows |
| `embeddinggemma` (300M) | 768 | ❌ Excluded by the 1024-dim standardisation. Good model, wrong shape for this schema |
| `mxbai-embed-large` | 1024 | Dimension-compatible but English-first. Backup only |

### 4.4 ⚠️ Reranking is not free on this stack

**Ollama has no `/api/rerank` endpoint.** Cross-encoder rerankers expose a classification head that Ollama does not surface — `/api/embeddings` returns the embedding layer, and `/api/generate` on a reranker produces garbage. Workarounds that score via embedding magnitude are folklore, not a technique.

A real reranker means **a sidecar** — Infinity, HuggingFace TEI, or ~40 lines of FastAPI wrapping `sentence-transformers.CrossEncoder('BAAI/bge-reranker-v2-m3')` — plus another ~1.2 GB resident and 200–600 ms per query on 40 candidates.

**Verdict: no reranker in v1.** It is the correct Phase 5 experiment (§10) but it is an infrastructure addition, not a config flag, and your eval must justify it first.

### 4.5 Concurrency, keep-alive, and the swap trap

The failure mode that will bite you: **Ollama unloads models after ~5 minutes idle by default**, and loading `gemma4:12b` from cold on a 16 GB card costs several seconds. Worse, if chat and ingestion contend, Ollama evicts one model to load the other, and you get thrash.

```bash
# In the ollama service environment:
OLLAMA_KEEP_ALIVE=-1        # pin models; do not unload
OLLAMA_MAX_LOADED_MODELS=2  # exactly chat + embedder
OLLAMA_NUM_PARALLEL=1       # single user; parallelism just fragments KV cache
```

Per-request in n8n, set `keep_alive: -1` on both the chat model and the embedding calls.

**Rule: never run book ingestion while chatting.** Embedding 3,000 chunks saturates the GPU and your chat latency goes to double digits. Two mitigations, both cheap:
- Run WF1 on a schedule (nightly) rather than a filesystem watcher.
- Have WF1 check a `mem.chat_turns` recency guard and defer if there was activity in the last 5 minutes.

**Two-model residency is the entire reason for `gemma4:12b` over anything bigger.** A third model — a small router, or a reranker — breaks the budget and forces swapping. That is why §7 routes with the main model and §4.4 defers reranking.

---

## 5. n8n workflow catalog

Seven workflows plus a family of tool sub-workflows. Every one is separately activatable — architecture rule 4.

### WF1 — `ingest-document`

| | |
|---|---|
| **Trigger** | Schedule Trigger (nightly 03:00) + Manual Trigger for on-demand |
| **Purpose** | PDF in `pending/` → chunks + embeddings in `kb.*` |
| **Input** | Files in `./shared/rag-files/pending/` |
| **Output** | `kb.document_versions` + `kb.chunks` + `kb.chunk_embeddings` rows; file moved to `processed/` |
| **Services** | Docling Serve, Ollama (`bge-m3`), Supabase Postgres |
| **Depends on** | `kb` schema, `IMAGE_BASE_URL` |

**Pattern:** plain workflow — Read/Write Files → Crypto (SHA-256) → Postgres (dedup check) → IF → HTTP Request (Docling async) → Wait/HTTP poll loop → Code (normalise chunk payload) → Postgres (insert chunks) → **Loop Over Items (batch 32)** → HTTP Request (Ollama `/api/embed`) → Postgres (insert vectors) → Postgres (atomic `is_current` swap) → Move file.

**No AI Agent here.** Ingestion is deterministic ETL; an agent adds nondeterminism and cost to a job with one correct answer.

**Anti-patterns:**
- ❌ Docling *sync* endpoint. Default server-side timeout is 2 minutes — a 400-page book will always fail. Use `/v1/convert/source/async` + `/v1/status/poll/{task_id}`.
- ❌ Splitting markdown in a Code node. Use Docling's chunker (§6).
- ❌ Embedding one chunk per item without `Loop Over Items`. 3,000 parallel HTTP items will OOM n8n and stampede Ollama.
- ❌ Using the `processed/` folder as the dedup check. Hash the file.
- ❌ Default n8n Vector Store nodes. They assume a LangChain-shaped table and will fight your schema. Use plain Postgres nodes.

### WF2 — `ingest-structured`

| | |
|---|---|
| **Trigger** | Manual |
| **Purpose** | BJCP JSON (and other reference data) → `brew.bjcp_styles` + generated style-card chunks |
| **Input** | JSON file with style objects |
| **Output** | Upserted style rows; `doc_type='style_guide'` chunks + embeddings |
| **Services** | Postgres, Ollama |

**Pattern:** Manual → Read File → Code (validate against expected keys, coerce numeric ranges) → Postgres upsert `ON CONFLICT (guide_year, code)` → Postgres `INSERT ... SELECT` generating one style card per style → embed → store.

**Anti-patterns:**
- ❌ Sending BJCP through the PDF pipeline. It's structured; parse it as structured.
- ❌ Letting an LLM extract the numeric ranges. Parse them, then assert `og_min < og_max` and fail loudly.

### WF3 — `import-batch`

| | |
|---|---|
| **Trigger** | Webhook (`POST /webhook/batch-import`) + Manual |
| **Purpose** | Batch/brew-day JSON → validated rows in `brew.*` |
| **Output** | `brew.batches`, `brew.measurements`, `brew.sensory_notes`; optional narrative embed into `mem` |
| **Services** | Postgres, optionally Ollama |

**Pattern:** Webhook → Code (schema validation, reject on missing `batch_no`/`brewed_on`) → Postgres upsert on `batch_no` → child inserts → IF (has tasting narrative) → embed into `mem.memory_embeddings`, **not** `kb`.

**Anti-patterns:**
- ❌ Embedding batch data into `kb.chunks`. This is the exact violation architecture rule 2 forbids. A batch narrative must never be retrievable as if it were a book.
- ❌ Accepting partial batches silently. Validate hard; a wrong OG poisons every downstream calculation.

### WF4 — `chat-agent` ⭐

| | |
|---|---|
| **Trigger** | Chat Trigger, **Response Mode = "Streaming response"** |
| **Purpose** | The assistant |
| **Services** | Ollama, Postgres (via tools), tool sub-workflows |

**Pattern:** Chat Trigger → **AI Agent** (streaming enabled) with:
- Chat Model: Ollama Chat Model → `gemma4:12b`
- Memory: **Postgres Chat Memory** → Supabase, `contextWindowLength: 6`
- Tools: 6–7 **Call n8n Workflow Tool** nodes (§7.3)

Plus a fire-and-forget Execute Sub-workflow to WF5 and a turn-logging insert into `mem.chat_turns`.

Note: the AI Agent node no longer has agent-type options — since n8n 1.82 every AI Agent *is* a Tools Agent. Old templates offering "Conversational Agent" are stale.

**Anti-patterns:**
- ❌ Basic LLM Chain (what your PoC uses). It cannot route, so it cannot honour the knowledge/truth split.
- ❌ A node between the Agent and the response. **Only the AI Agent node streams output.** Post-processing to append citations silently disables streaming — see §7.7.
- ❌ More than ~7 tools in v1. Selection accuracy on a 12B model degrades sharply.
- ❌ Vector Store Retriever wired directly as a tool. It bypasses your RRF function and gives you vector-only retrieval.

### WF5 — `learn-from-chat`

| | |
|---|---|
| **Trigger** | Execute Sub-workflow (from WF4), fire-and-forget |
| **Purpose** | Extract preferences / lessons / corrections from the turn |
| **Output** | `mem.*` rows, some pending confirmation |

**Pattern:** Execute Workflow Trigger → Basic LLM Chain with **Structured Output Parser** (strict JSON schema, `confidence` per item) → Code (drop `confidence < 0.7`, drop anything matching a stop-list) → Switch on `requires_confirmation` → high-importance items go to a confirmation queue; low-risk items write directly.

**This is a chain, not an agent** — it's a single extraction task with a fixed output shape. An agent here is pure overhead.

**Anti-patterns:**
- ❌ Running it inline in WF4's response path. It doubles perceived latency for zero user benefit.
- ❌ Writing to `mem` without a confidence gate. Memory pollution is silent and compounding.
- ❌ Storing raw chat turns as "memories". §9.

### WF6 — `eval-runner`

| | |
|---|---|
| **Trigger** | **Evaluation Trigger** (n8n's native evaluations feature) |
| **Purpose** | Regression-test retrieval and answers against a fixed dataset |
| **Input** | n8n **Data Table** of eval questions + reference answers |
| **Output** | Metrics on the Evaluations tab |

I'd originally have said "write a pytest harness" — but n8n's evaluations feature makes that the wrong call now. It gives you an Evaluation Trigger reading a Data Table, a `Check If Evaluating` branch so eval runs don't pollute production paths, `Set Metrics` for scoring, and a dashboard with run-over-run score history. Built on the same execution engine as your real workflow, which means you are testing the actual agent, not a reimplementation.

**Pattern:** Evaluation Trigger → Execute Workflow (WF4) → Evaluation `Set Outputs` → metric nodes → `Set Metrics`. Mix deterministic metrics (retrieval hit rate, tool-name match, latency) with an LLM-judged Correctness metric.

**Anti-patterns:**
- ❌ LLM-judged metrics only. Judge and judged share a model and its blind spots. Deterministic metrics are the backbone.
- ❌ Changing two variables between runs. Chunk size *or* embedder *or* prompt — never two.

### WF7 — `reindex-embeddings`

| | |
|---|---|
| **Trigger** | Manual |
| **Purpose** | Re-embed a corpus under a new model without re-chunking |

**Pattern:** Manual → Postgres (`SELECT id, content FROM kb.chunks c WHERE NOT EXISTS (SELECT 1 FROM kb.chunk_embeddings e WHERE e.chunk_id=c.id AND e.model=$1)`) → Loop Over Items (batch 32) → Ollama embed → Postgres insert.

Because embeddings are keyed by model, the new vectors land *alongside* the old ones. You then A/B by flipping `p_model` in the search function and re-running WF6. Zero downtime, zero re-chunking, and a genuine comparison.

**Anti-pattern:** running this for the *initial* 40k-chunk backfill. n8n's per-item overhead makes a 30-line Python script using the same batching an order of magnitude faster. Use WF7 for incremental and A/B work; script the bulk load once.

### Tool sub-workflows (`tool-*`)

Each agent tool is its own workflow with an **Execute Workflow Trigger** and a defined **Workflow Input Schema** (which is what lets the parent's `Call n8n Workflow Tool` node auto-populate parameter fields).

Why sub-workflows rather than Postgres-node-as-tool: you get one place to shape output for the model, a testable unit you can run standalone, and a clean boundary for the read-only credential.

---

## 6. Ingestion pipeline detail

### 6.1 Docling Serve usage

**Always async.** Sync endpoints carry a ~2-minute server-side timeout; raising the HTTP client timeout does nothing because the server closes the connection.

```
POST /v1/convert/source/async   →  { "task_id": "...", "task_status": "pending" }
GET  /v1/status/poll/{task_id}  →  poll until "success" | "failure"
GET  /v1/result/{task_id}       →  the converted document
```
(A WebSocket at `/v1/status/ws/{task_id}` exists for push updates; polling is simpler in n8n and perfectly adequate for a nightly job.)

Request options for brewing PDFs:

```json
{
  "options": {
    "from_formats": ["pdf"],
    "to_formats": ["md", "json"],
    "image_export_mode": "referenced",
    "do_ocr": true,
    "force_ocr": false,
    "ocr_engine": "easyocr",
    "ocr_lang": ["en"],
    "pdf_backend": "dlparse_v4",
    "table_mode": "accurate",
    "do_table_structure": true,
    "abort_on_error": false
  }
}
```

- `table_mode: "accurate"` — non-negotiable. Brewing books are *full* of tables (hop varieties, water profiles, style vital statistics). `fast` mangles them and you lose the highest-value content in the book.
- `to_formats` includes `json` — the DoclingDocument JSON carries page provenance that markdown discards. That's where `page_from`/`page_to` come from.
- `do_ocr: true, force_ocr: false` — OCR only the scanned pages. Forcing OCR on a digital PDF is slower and *worse*.

In n8n: a Wait node (15 s) inside a loop against `/v1/status/poll/`, with a max-iteration guard so a hung Docling task doesn't loop forever.

### 6.2 Chunking strategy — Docling `HybridChunker`, and why

**Rejected: heading-based splitting (your current approach).** It produces chunks whose size is an accident of how the author organised headings. On a style guide that means a 25-token "Vital Statistics" next to a 900-token "Comments" — one too small to be meaningful, one too big to embed cleanly.

**Rejected: fixed-size / recursive character splitting.** Cheap, structure-blind, splits tables in half.

**Rejected: LLM semantic chunking.** 3,000 chunks × a 12B model on your GPU is hours of compute for a marginal, unmeasurable gain. Revisit never.

**Chosen: `HybridChunker`** — hierarchical layout-aware chunking with tokenization-aware refinement on top. Three properties that matter here:

1. **`merge_peers=True`** merges undersized sibling sections under a shared parent. This is exactly the style-guide problem, solved.
2. **`contextualize(chunk)`** prepends the heading hierarchy to the chunk text. A chunk about mash temperature carries `Stout > Irish Stout > Vital Statistics` into its embedding — which is why a query for "Irish stout mash temp" retrieves it even though the body may never say "Irish".
3. **Tokenizer parity.** The chunker uses the *same tokenizer as the embedder*. Configure it against `BAAI/bge-m3` with `max_tokens: 512`. Chunker and embedder disagreeing on token counts is the classic silent truncation bug.

```json
{
  "chunking": {
    "chunker": "hybrid",
    "tokenizer": "BAAI/bge-m3",
    "max_tokens": 512,
    "merge_peers": true,
    "repeat_table_headers": true
  }
}
```

`repeat_table_headers: true` means a hop table split across chunks keeps its column headers in each piece — otherwise chunk 2 is a grid of numbers with no idea what they measure.

⚠️ **Known issue:** `max_tokens` is not strictly enforced after `contextualize()` — a long heading path can push a chunk slightly over. Assert `token_count <= 512` in your normalisation Code node and log violations rather than discovering them as silent truncation at embed time.

### 6.3 Markdown cleaning rules

Applied in one Code node between Docling and insert. Keep them declarative and few:

| Rule | Action |
|---|---|
| Chunk is image-only (`raw_content` strips to empty after removing `![…](…)`) | **Drop.** Record image in the *preceding* chunk's `image_refs` |
| `token_count < 30` and no table | **Drop.** Below the noise floor; retrieves as junk |
| Heading path matches `/^(Contents|Table of Contents|Index|Glossary|Acknowledg|Copyright|About the Author)/i` | **Drop** |
| Repeated line appearing on >60% of pages | **Strip as masthead/footer** |
| Page-number-only lines (`^\s*\d{1,4}\s*$`) | Strip |
| Sequences of 3+ dot-leaders (`\.{3,}`) | Strip (TOC residue) |
| Chunk is >80% non-alphanumeric | **Drop** (OCR garbage) |
| Everything else | Keep verbatim — do not "clean" prose |

Log every drop with its reason to a `kb.ingest_log` table. When retrieval later misses something, you need to know whether it was never ingested or just ranked poorly. This one table saves hours.

### 6.4 Embedding: batching, retry, failure

- **Batch size 32** via `Loop Over Items`. Ollama's `/api/embed` takes an array `input`. 32 × ~512 tokens is a comfortable single forward pass on 16 GB.
- **`keep_alive: -1`** on every embed call. Otherwise the embedder is evicted between batches and you pay a reload each time.
- **Retry:** node-level retry, 3 attempts, exponential backoff. Ollama returns 500 under memory pressure; it usually succeeds on retry.
- **Failure isolation:** `Continue (using error output)` on the embed node. A failed batch writes to `kb.ingest_log` with its chunk IDs and the run continues. Chunks without embeddings still exist and are still FTS-searchable — degraded, not lost.
- **Resumability:** because WF7's query is "chunks lacking an embedding for model X", re-running it after a failure fills exactly the gaps. No bookkeeping needed.
- **Never** mark a version `is_current` until embedding coverage is verified:
  ```sql
  SELECT count(*) FILTER (WHERE e.chunk_id IS NULL) AS missing
  FROM kb.chunks c
  LEFT JOIN kb.chunk_embeddings e ON e.chunk_id = c.id AND e.model = 'bge-m3'
  WHERE c.version_id = $1;
  ```
  `missing > 0` → don't flip; leave the previous version live.

### 6.5 Folder state machine

```
pending/     files awaiting ingestion (you drop them here)
processing/  ← ADD THIS. Moved here at start; a file stuck here = crashed run
processed/   moved here only after the is_current swap commits
failed/      ← ADD THIS. Moved here on unrecoverable error, with a .log sidecar
```

Two new folders, both earning their place: without `processing/` you cannot tell "not started" from "died halfway"; without `failed/` a broken PDF is retried nightly forever.

**Restated because it's the important part:** these folders are for *your* visibility. Authoritative state is `kb.document_versions`. A file manually moved back to `pending/` will be hash-rejected — which is correct behaviour, not a bug. Add a `--force` path (delete the version row first) for genuine re-ingestion.

### 6.6 Worked example: `Stout-Style-Guide.pdf` → what should happen instead of 26 chunks

**Today:** Docling → markdown → n8n splits on headings → 26 chunks → flat rows in `documents`. No page numbers, no heading context, wildly uneven sizes, tables probably broken, and the style's numeric ranges buried in prose where no query can filter on them.

**New design — this file doesn't belong in the book pipeline at all.**

*Primary path (WF2, structured):* a style guide is a data file. Parse it into `brew.bjcp_styles` rows with real `og_min`/`og_max`/`ibu_min`/`ibu_max`/`srm`/`abv` columns. This turns *"is my 1.048 OG in range for Irish Stout?"* from a retrieval gamble into `SELECT ... WHERE 1.048 BETWEEN og_min AND og_max`. That question is unanswerable reliably by any RAG pipeline and trivially answerable by SQL — which is your architecture rule 2 in one concrete case.

*Secondary path (WF1, narrative):* generate one style card per style for the prose questions:

```
Irish Stout (BJCP 15B) — Stout
Overall impression: …
Aroma: …  Appearance: …  Flavor: …  Mouthfeel: …
Comments: …  Commercial examples: …
```
One card ≈ 300–450 tokens, one chunk, `heading_path = {'BJCP 2021','Stout','15B Irish Stout'}`, `doc_type='style_guide'`. That gives you **one clean chunk per style** — and if the guide covers 8 stout styles, that's 8 semantically complete chunks instead of 26 arbitrary fragments.

*If you did run it through WF1 anyway:* `HybridChunker` with `merge_peers=true, max_tokens=512` would merge the tiny peer sections under each style heading and yield roughly 8–12 well-formed chunks, each carrying its heading path and page range for free. Still better than 26. But the structured path is strictly better, and BJCP data is the highest-leverage structured import you can do.

**Rule that generalises:** *if a document has a regular repeating structure, parse it; only chunk documents that are genuinely prose.*

---

## 7. Chat & retrieval design

### 7.1 AI Agent + tools. Not a monolithic RAG chain.

**Decision: AI Agent with guarded tools.**

The justification isn't "agents are modern" — it's that a monolithic RAG chain **structurally cannot implement your architecture rule 2**. A single chain has one retrieval path. Given *"how much Citra do I have left?"* it will embed the question, search chunks, find a book passage about Citra's aroma profile, and answer confidently and wrongly. There is no configuration of a RAG chain that routes that question to SQL. The routing capability *is* the requirement.

**The honest cost:** a 12B model's tool selection is good, not perfect. Mitigations, in order of effectiveness:

1. **Few tools.** Six or seven, maximum. Every added tool degrades selection for all the others.
2. **Excellent descriptions.** Reported experience is that in roughly half of "the model won't call my tool" cases, the description is the bug, not the model size. Rewriting a description is free; upgrading a model costs VRAM you don't have.
3. **Disjoint tool boundaries.** If two tools could plausibly answer the same question, merge them.
4. **Measure it.** Tool-selection accuracy is an eval metric (§10), not a vibe.
5. **Only if eval shows <80% after fixing descriptions:** add a deterministic pre-router (§7.2).

### 7.2 Routing

**Phase 2–3: let the agent route.** No classifier node. A separate router costs a full extra LLM round trip (2–4 s locally) and a third resident model you don't have VRAM for. The system prompt does the work:

```mermaid
flowchart LR
    U["User message"] --> A["AI Agent<br/>gemma4:12b"]
    A -->|"knowledge<br/>question"| T1["search_brewing_knowledge<br/>→ nlq.search_knowledge (RRF)"]
    A -->|"my data"| T2["find_batches / get_inventory<br/>→ nlq.* functions"]
    A -->|"style spec"| T3["lookup_bjcp_style"]
    A -->|"both"| T4["parallel calls"]
    T1 --> ASM["Agent assembles answer<br/>+ inline citations"]
    T2 --> ASM
    T3 --> ASM
    T4 --> ASM
    ASM --> S["stream to @n8n/chat"]
```

**Escalation path if eval fails:** insert a Text Classifier node before the agent with intents `{knowledge, personal_data, mixed, chitchat}` and route to *three narrower agents* with 2–3 tools each. This trades latency for accuracy. Don't pay it until you've measured that you need it.

### 7.3 Tool catalogue

| Tool | Signature | Backing | Phase |
|---|---|---|---|
| `search_brewing_knowledge` | `(query: string, doc_type?: enum, top_k?: int=6)` | `nlq.search_knowledge` | 2 |
| `find_batches` | `(style_name?, descriptor?, brewed_after?, brewed_before?, min_abv?, min_dry_hop_rate?, max_dry_hop_rate?, limit?=20)` | `nlq.find_batches` | 2 |
| `get_batch_detail` | `(batch_no: string)` | `nlq.v_batch_overview` + measurements + sensory | 3 |
| `get_inventory` | `(kind?: enum, name_contains?: string, only_in_stock?: bool=true)` | `nlq.v_inventory_current` | 3 |
| `lookup_bjcp_style` | `(style_code?: string, style_name?: string)` | `brew.bjcp_styles` | 3 |
| `compare_batches` | `(batch_nos: string[])` | `nlq.f_compare_batches` | 3 |
| `get_recipe` | `(name: string, version?: int)` | `nlq.v_recipe_full` | 3 |
| `save_memory` | `(kind: enum, content: string, confidence: number)` | `mem.f_save_memory` | 4 |

**Deliberately not a tool: `get_user_preferences`.** Preferences are a handful of short rows. Fetch them with a Postgres node *before* the agent and interpolate into the system prompt. Saves a full tool round trip on every conversation — meaningful when each round trip is seconds.

**`save_memory` should be gated.** n8n supports human-in-the-loop approval on specific tools: the workflow pauses and asks for approval through your chosen channel before the tool executes. Wire it to the Chat channel so writing a durable preference costs you one tap. §9.

### 7.4 Retrieve vs. query vs. both

| Question shape | Route |
|---|---|
| "What / why / how does X work" | **RAG** |
| "How much / how many / when did I / which of my" | **SQL** |
| Any number that must be *correct* about your brewing | **SQL, always** |
| "Is my X within spec for style Y" | **SQL both sides** (measurement + style range) |
| "Why did my batch N taste Z" | **Both** — SQL for the facts, RAG for the mechanism |
| "Suggest a recipe from what I have" | **Both + math** — inventory SQL, style SQL, technique RAG |

Encode the failure mode explicitly in the system prompt: *if a question is about the user's own brewing and no tool returned data, say so — never fill the gap from the books.* Hallucinated inventory is the single worst failure this system can produce, because it is confident, plausible, and silently wrong.

### 7.5 Context budget

`gemma4:12b` advertises 256K context. You cannot afford it — KV cache at 256K would dwarf the model. Run `num_ctx: 12288`.

| Component | Tokens |
|---|---|
| System prompt + persona | ~600 |
| Injected preferences (max 10) | ~200 |
| Chat memory (last 6 turns, windowed) | ~1,200 |
| `search_brewing_knowledge` results — **6 chunks × ~500** | ~3,000 |
| Structured tool results (rows, capped at 20) | ~800 |
| Reasoning + answer | ~1,500 |
| Headroom | ~5,000 |
| **num_ctx** | **12,288** |

**Metadata injected per chunk** (compact — every token here is a token not spent reasoning):

```
[S3] Designing Great Beers · Hops > Bittering > Utilization · p.112
<raw_content>
```

**Source footer**, appended by the agent itself (not a post-processing node — §7.7):

```
---
Sources:
[S1] Designing Great Beers, p.112
[S2] BJCP 2021 Guidelines, 15B Irish Stout
[S3] Your batch #24 (brewed 2026-03-11)
```

Truth-derived claims get `[S…]` markers too. It makes provenance visible and, more usefully, makes it obvious in eval when the model asserted something with no source at all.

### 7.6 Chat memory backend

**Decision: n8n Postgres Chat Memory node → Supabase Postgres**, `contextWindowLength: 6`.

- Not n8n's in-memory buffer: it doesn't survive restarts, and n8n's docs are explicit that simple memory doesn't persist between sessions.
- Not the n8n Postgres instance: chat history is *app data*. The learning layer and eval both need it. Architecture note in Setup says don't merge the two Postgres instances — this respects that by putting app data in the app database.

**But also log turns yourself.** n8n's memory table is an opaque LangChain-shaped blob, fine for the agent, useless for analysis. Add a parallel structured log:

```sql
CREATE TABLE mem.chat_turns (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id text NOT NULL,
  turn_no int NOT NULL,
  role text NOT NULL CHECK (role IN ('user','assistant')),
  content text NOT NULL,
  tool_calls jsonb,          -- which tools fired, with what params
  chunk_ids bigint[],        -- what was retrieved  → retrieval eval
  latency_ms int,
  model text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (session_id, turn_no, role)
);
```

`tool_calls` and `chunk_ids` are what let you compute tool-selection accuracy and retrieval hit rate in §10 from real traffic, not just the synthetic eval set. Two extra columns, enormous payoff.

### 7.7 Streaming — and the constraint it imposes

Streaming works, with a specific wiring requirement: **both** the trigger and the output node must have streaming enabled. Set Chat Trigger → Response Mode = **"Streaming response"**, and enable streaming on the AI Agent node. If only one is set, n8n silently falls back to request/response. Requires n8n ≥ 1.106.3; the `@n8n/chat` widget auto-detects streaming and needs no client change.

**The constraint, and it shapes the design: only the AI Agent node supports streaming output.**

Therefore:
- ❌ No node between the Agent and the user. A Set node reformatting citations breaks streaming.
- ✅ Citations must be produced *by the agent, inline*. Which means tools must return citation-ready metadata and the system prompt must mandate the footer format.
- ✅ Post-hoc work (turn logging, WF5) hangs off a *branch*, not the response path.

This is a real trade-off: you give up deterministic citation formatting in exchange for a responsive UI. On a local 12B model generating ~20–30 tok/s, streaming is the difference between "feels usable" and "feels broken", so take the trade — and put citation-format compliance in the eval set (§10) since you can no longer enforce it in code.

### 7.8 System prompt principles

Structure, not a script:

1. **Identity & scope** — a brewing assistant for *one* brewer, with access to that brewer's records.
2. **The knowledge/truth law, stated as a hard rule.**
   > Facts about the user's own brewing — inventory, batches, measurements, tasting notes — come **only** from tools. If a tool returns nothing, say you have no record. Never infer the user's data from books.
3. **Tool-selection guidance** — one line per tool, phrased as the *question shape* it answers, not what it does.
4. **Citation contract** — the exact footer format, with an example. Since streaming prevents enforcement in code, over-specify it here.
5. **Units and conventions** — metric, litres, °C, SG to 3 decimals, IBU as integer, g/L for hop rates. State it once; it eliminates a whole class of conversion errors.
6. **Answer language** — English, fixed. No language parameter needed in the prompt template.
7. **Uncertainty behaviour** — distinguish "the books disagree" from "I have no record of that" from "I'm not sure". Three different states, three different sentences.
8. **Injected preferences** — appended as a short bulleted block from `mem.preferences WHERE active`.

Keep it under ~600 tokens. Long system prompts degrade small models: instruction-following gets worse, not better, as the prompt grows.

---

## 8. NLQ design

### 8.1 Which questions need which

**RAG (knowledge — books, BJCP prose, theory):**
1. "What causes diacetyl and how do I prevent it?"
2. "How does the sulfate-to-chloride ratio change hop perception?"
3. "What's the point of a hochkurz mash schedule?"
4. "Why does my stout need roasted barley rather than black patent?"
5. "How long should a Russian Imperial Stout condition before it's ready?"
6. "What is hot-side aeration and does it actually matter in a homebrew setup?"
7. "Explain kveik fermentation temperatures compared to standard ale yeast."

**NLQ (truth — my data):**
1. "How much Citra do I have left?"
2. "Which of my batches finished above 1.020?"
3. "What was the OG of my last IPA?"
4. "Which yeast strain have I used most in the past year?"
5. "Show me every batch I brewed between March and June."
6. "Compare batch #12 and batch #17 on their tasting notes."
7. "What's the average attenuation across all my batches with US-05?"

**Both (the interesting ones):**
1. "Which of my IPAs were bitter and had a dry hop rate above 8 g/L?" *(SQL; RAG only if asked why)*
2. "Is my last stout in style for BJCP 15B?" *(SQL both sides)*
3. "Why did batch #19 taste like green apple?" *(SQL for the facts, RAG for acetaldehyde)*
4. "Suggest a recipe using what I have in stock for a 20 L pale ale." *(inventory SQL + style SQL + technique RAG + math)*
5. "Do I have enough Maris Otter for a 20 L batch at 1.050?" *(inventory SQL + `brew.f_grain_bill_estimate`)*

The pattern: **RAG explains, SQL counts.** If the answer is a number about you, it's SQL. If the answer is a mechanism, it's RAG. If the question is "why did *my* X do Y", it's both — and the agent must fetch the facts before it explains them, never the other way round.

### 8.2 Safe tool interface

Every NLQ tool is a `SECURITY DEFINER` function in `nlq`, with typed nullable parameters. No dynamic SQL, no free-form input reaching the planner.

```sql
CREATE OR REPLACE FUNCTION nlq.find_batches(
  p_style_name          text    DEFAULT NULL,
  p_style_code          text    DEFAULT NULL,
  p_descriptor          text    DEFAULT NULL,
  p_brewed_after        date    DEFAULT NULL,
  p_brewed_before       date    DEFAULT NULL,
  p_min_abv             numeric DEFAULT NULL,
  p_max_abv             numeric DEFAULT NULL,
  p_min_dry_hop_rate    numeric DEFAULT NULL,
  p_max_dry_hop_rate    numeric DEFAULT NULL,
  p_limit               int     DEFAULT 20
) RETURNS TABLE (
  batch_no text, recipe_name text, style_code text, style_name text,
  brewed_on date, og numeric, fg numeric, abv numeric,
  dry_hop_rate_g_per_l numeric, descriptors text[], avg_score numeric
) LANGUAGE sql STABLE SECURITY DEFINER SET search_path = brew, public AS $$
  SELECT b.batch_no, r.name, s.code, s.name, b.brewed_on, b.og, b.fg,
         brew.f_abv(b.og, b.fg),
         brew.f_dry_hop_rate_g_per_l(b.id),
         (SELECT array_agg(DISTINCT d) FROM brew.sensory_notes sn,
                 unnest(sn.descriptors) d WHERE sn.batch_id = b.id),
         (SELECT round(avg(sn.score),1) FROM brew.sensory_notes sn WHERE sn.batch_id = b.id)
  FROM brew.batches b
  LEFT JOIN brew.recipes r ON r.id = b.recipe_id
  LEFT JOIN brew.bjcp_styles s ON s.id = r.style_id
  WHERE (p_style_name IS NULL OR s.name ILIKE '%'||p_style_name||'%')
    AND (p_style_code IS NULL OR s.code = upper(p_style_code))
    AND (p_brewed_after  IS NULL OR b.brewed_on >= p_brewed_after)
    AND (p_brewed_before IS NULL OR b.brewed_on <= p_brewed_before)
    AND (p_min_abv IS NULL OR brew.f_abv(b.og,b.fg) >= p_min_abv)
    AND (p_max_abv IS NULL OR brew.f_abv(b.og,b.fg) <= p_max_abv)
    AND (p_min_dry_hop_rate IS NULL
         OR brew.f_dry_hop_rate_g_per_l(b.id) >= p_min_dry_hop_rate)
    AND (p_max_dry_hop_rate IS NULL
         OR brew.f_dry_hop_rate_g_per_l(b.id) <= p_max_dry_hop_rate)
    AND (p_descriptor IS NULL OR EXISTS (
          SELECT 1 FROM brew.sensory_notes sn
          WHERE sn.batch_id = b.id
            AND (sn.descriptors @> ARRAY[lower(p_descriptor)]
                 OR sn.fts @@ plainto_tsquery('english', p_descriptor))))
  ORDER BY b.brewed_on DESC
  LIMIT LEAST(p_limit, 50);
$$;
```

Note `LIMIT LEAST(p_limit, 50)` — the model cannot blow your context budget by asking for 10,000 rows.

Companion functions: `nlq.get_inventory`, `nlq.get_batch_detail`, `nlq.compare_batches`, `nlq.get_recipe`, `nlq.lookup_bjcp_style`.

### 8.3 `$fromAI()` parameter mapping

In the `Call n8n Workflow Tool` node, pressing "Let the model define this parameter" generates a `$fromAI()` expression you then refine. The arguments are **hints to the model**, not references — so the description string is doing the real work.

```javascript
p_style_name:
{{ $fromAI('style_name',
   'Beer style the user mentioned, e.g. "IPA", "Irish Stout", "saison". Use the style name only, no BJCP code. Null if the user did not name a style.',
   'string') }}

p_descriptor:
{{ $fromAI('sensory_descriptor',
   'ONE sensory adjective the user used to describe taste or aroma, lowercase, e.g. "bitter", "estery", "harsh". Null if none.',
   'string') }}

p_min_dry_hop_rate:
{{ $fromAI('min_dry_hop_rate',
   'Minimum dry hop rate in grams per litre, as a number. The user may say "8 g/L" or "above 8 grams per liter" — extract 8. Null if not mentioned.',
   'number') }}

p_brewed_after:
{{ $fromAI('brewed_after',
   'Earliest brew date as YYYY-MM-DD. Resolve relative dates against today. "last year" -> Jan 1 of last year. Null if no date constraint.',
   'string') }}
```

Three rules that matter:
1. **Give an example in the description.** `'8 g/L' → 8` prevents the model passing the string `"8 g/L"` into a numeric.
2. **Say what null means.** Without it, small models invent plausible values rather than omitting the parameter — the single most common `$fromAI` failure.
3. **One concept per parameter.** `p_descriptor` takes one adjective, not a phrase. If the user says "bitter and harsh", let the agent call twice.

⚠️ `$fromAI()` only works in tools attached to an AI Agent. It does not work in the Code tool or other cluster sub-nodes.

### 8.4 Read-only enforcement — three layers

**Layer 1: schema separation.** The agent never sees `brew`, `kb`, or `mem`. Only `nlq`.

```sql
CREATE ROLE agent_ro NOLOGIN;
REVOKE ALL ON SCHEMA brew, kb, mem FROM PUBLIC, agent_ro;
GRANT USAGE ON SCHEMA nlq TO agent_ro;
GRANT SELECT   ON ALL TABLES    IN SCHEMA nlq TO agent_ro;  -- views only
GRANT EXECUTE  ON ALL FUNCTIONS IN SCHEMA nlq TO agent_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA nlq
  GRANT SELECT ON TABLES TO agent_ro, GRANT EXECUTE ON FUNCTIONS TO agent_ro;

CREATE ROLE n8n_agent LOGIN PASSWORD '…' IN ROLE agent_ro;
ALTER ROLE n8n_agent SET default_transaction_read_only = on;
ALTER ROLE n8n_agent SET statement_timeout = '10s';
```

`default_transaction_read_only` means even a hypothetical injected `DELETE` errors at the transaction level. `statement_timeout` caps a pathological query.

**Layer 2: `SECURITY DEFINER` functions.** `nlq` functions are owned by a role that *can* read `brew`/`kb`, and run with that role's rights. The agent gets the answer without the read grant. Always `SET search_path` explicitly on these — omitting it is the classic `SECURITY DEFINER` privilege-escalation hole.

**Layer 3: no SQL-shaped tool.** There is no `run_query` tool, no Postgres node with an AI-filled `query` field. The model chooses *which function* and *what arguments*; it never composes SQL. This is what architecture rule 3 means in practice, and it's the layer that actually matters — the other two are defence in depth.

**Writes** (the learning layer) use a **separate credential** with `EXECUTE` on `mem.f_save_memory` only. Read tools physically cannot write; the write tool physically cannot read your batches.

### 8.5 End-to-end trace

> **"Which of my IPA batches were bitter and had a dry hop rate above 8 g/L?"**

**1 — Agent reasoning.** Question is about *my* batches → truth → SQL, not retrieval. `find_batches` is the only tool matching "which of my batches, filtered".

**2 — `$fromAI` extraction:**
```json
{ "style_name": "IPA", "sensory_descriptor": "bitter", "min_dry_hop_rate": 8 }
```

**3 — Tool call** → `Call n8n Workflow Tool` → `tool-find-batches` sub-workflow → Postgres node as `n8n_agent`:
```sql
SELECT * FROM nlq.find_batches(
  p_style_name       => 'IPA',
  p_descriptor       => 'bitter',
  p_min_dry_hop_rate => 8
);
```

**4 — Postgres executes**, with `f_dry_hop_rate_g_per_l` computed per batch and the descriptor matched against both the `descriptors` array and the sensory FTS index. Read-only, 10 s timeout, ≤50 rows.

**5 — Rows returned:**
```
batch_no  recipe_name        style  brewed_on   og     fg     abv  dhr   descriptors            avg_score
IPA-024   Citra Bomb v3      21A    2026-03-11  1.062  1.012  6.6  11.5  {bitter,resinous,dank}     7.5
IPA-019   West Coast Redux   21A    2025-11-02  1.058  1.010  6.3   9.2  {bitter,piney,harsh}       6.0
```

**6 — Sub-workflow shapes output** for the model — compact, citation-ready:
```
2 batches matched (style IPA, descriptor "bitter", dry hop >= 8 g/L):
[S1] IPA-024 "Citra Bomb v3" | 2026-03-11 | OG 1.062 FG 1.012 | 6.6% | dry hop 11.5 g/L | bitter, resinous, dank | avg 7.5/10
[S2] IPA-019 "West Coast Redux" | 2025-11-02 | OG 1.058 FG 1.010 | 6.3% | dry hop 9.2 g/L | bitter, piney, harsh | avg 6.0/10
```

**7 — Agent answers**, streaming:

> Two of your IPAs match. **IPA-024 "Citra Bomb v3"** (11 March 2026) had the heavier dry hop at 11.5 g/L, finished at 6.6% ABV, and you described it as bitter, resinous and dank — it scored 7.5/10. **IPA-019 "West Coast Redux"** (2 November 2025) was dry hopped at 9.2 g/L, finished at 6.3%, and you noted bitter, piney and harsh, scoring 6.0/10.
>
> The "harsh" note on IPA-019 alongside a lower score is worth a look — want me to check what the books say about harsh bitterness at that hop rate?
>
> ```
> Sources:
> [S1] Batch IPA-024, brewed 2026-03-11
> [S2] Batch IPA-019, brewed 2025-11-02
> ```

**Note what did not happen:** no vector search, no LLM arithmetic (the 11.5 g/L came from a Postgres function), no SQL generation, and every number is traceable to a row. The follow-up offer is the correct escalation from truth to knowledge — and it waits for the user rather than padding the answer with unrequested book content.

---

## 9. Learning layer

Goal: get better over time without fine-tuning and without polluting the knowledge base.

### 9.1 What to extract

| Kind | Definition | Example | Write policy |
|---|---|---|---|
| `preference` | A durable statement about taste, method, or constraint | "I prefer restrained bitterness in stouts" | **Confirm** |
| `constraint` | A hard limit on the system | "My kettle maxes out at 30 L" | **Confirm** |
| `batch_lesson` | Something learned from a specific batch | "Batch #19 got harsh — dry hopped too warm at 22 °C" | **Confirm**, link to `batch_id` |
| `correction` | The user corrected the assistant | "No, my mash tun is 40 L, not 30" | **Write immediately**, supersede prior |
| `equipment` | Kit facts | "I ferment in a 30 L SS Brewtech unitank" | **Confirm** |

### 9.2 Schema

```sql
CREATE TABLE mem.memories (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  kind         text NOT NULL CHECK (kind IN
               ('preference','constraint','batch_lesson','correction','equipment')),
  content      text NOT NULL,
  batch_id     bigint REFERENCES brew.batches(id) ON DELETE SET NULL,
  confidence   numeric(3,2) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  status       text NOT NULL DEFAULT 'pending'
               CHECK (status IN ('pending','active','superseded','rejected')),
  supersedes   bigint REFERENCES mem.memories(id),
  source_turn  bigint REFERENCES mem.chat_turns(id),
  content_sha256 char(64) NOT NULL,
  created_at   timestamptz NOT NULL DEFAULT now(),
  confirmed_at timestamptz,
  UNIQUE (content_sha256, kind)          -- never store the same fact twice
);
CREATE INDEX ON mem.memories (kind, status);

-- SEPARATE vector space. Never joined with kb.chunk_embeddings.
CREATE TABLE mem.memory_embeddings (
  memory_id bigint PRIMARY KEY REFERENCES mem.memories(id) ON DELETE CASCADE,
  model     text NOT NULL,
  embedding vector(1024) NOT NULL
);
CREATE INDEX ON mem.memory_embeddings USING hnsw (embedding vector_cosine_ops);
```

### 9.3 Retrieval without polluting document RAG

**Two mechanisms, both bounded:**

1. **Injection (default).** Before the agent runs, fetch `SELECT content FROM mem.memories WHERE status='active' AND kind IN ('preference','constraint','equipment') ORDER BY confirmed_at DESC LIMIT 10` and interpolate into the system prompt. Ten short lines — no tool call, no latency, always present.
2. **Search (batch lessons only).** `mem.batch_lessons` can grow past what fits in a prompt. Expose `nlq.search_lessons(query, embed, limit=3)` over `mem.memory_embeddings`. Never fused into `nlq.search_knowledge`.

**Why the separation is non-negotiable.** If a memory embedding sat in `kb.chunk_embeddings`, then "what's the ideal dry hop temperature?" could return *your note* about batch #19 ranked above the textbook — and the assistant would present your own guess back to you as established fact. That's a self-reinforcing hallucination loop, the nastiest failure mode a learning system has. Separate tables make it structurally impossible.

Marker in the prompt: memory content is always introduced as *"You previously told me…"*, never blended into expository text.

### 9.4 Confirm-before-write

Use n8n's human-in-the-loop tool approval: connect `save_memory` to the Human review step with the Chat channel. The workflow pauses, you approve or deny in the chat window, and the tool executes only on approval.

Policy by kind:

| Kind | Confidence | Behaviour |
|---|---|---|
| `correction` | any | **Write immediately**, `status='active'`, mark prior `superseded`. You just told it it was wrong; asking "are you sure?" is insulting |
| `preference`, `constraint`, `equipment` | ≥ 0.8 | Ask once, inline, at end of turn |
| any | 0.7–0.8 | Queue as `pending`, batch-review weekly |
| any | < 0.7 | **Discard.** Do not queue. A review backlog you never process is worse than nothing |

Weekly review = one Postgres query against `status='pending'`. Keep it manual; automating memory approval defeats the point.

### 9.5 What NOT to store

- **Transient chitchat.** "thanks", "cool", "makes sense".
- **Anything already in `brew.*`.** A batch's OG is a *fact in a table*. Storing "batch 24 had OG 1.062" as a memory creates a second, un-updatable copy that will drift. If it belongs in a column, put it in the column.
- **Restatements of book knowledge.** "User learned that diacetyl comes from VDK" — that's in the corpus.
- **Inferences the user didn't confirm.** "User seems to prefer hoppy beers" from two IPA questions is a guess. Guessed preferences quietly steer every future recommendation.
- **Anything with `confidence < 0.7`.**
- **Negations of a single instance.** "Didn't like batch #19" is a `sensory_note`, not a preference. It becomes a preference only when a pattern appears across batches — and even then, you confirm it.

Stop-list in WF5's Code node, applied *before* the confidence gate. Cheaper and more reliable than prompting the extractor not to do it.

---

## 10. Evaluation plan

### 10.1 Eval set

~60 questions across six intents, in an n8n **Data Table**. Columns: `id`, `intent`, `question`, `reference_answer`, `expected_tool`, `expected_chunk_ids`, `must_contain`.

| Intent | n | Examples |
|---|---|---|
| **style_lookup** | 10 | "What's the OG range for BJCP 15B?" · "Is 45 IBU in style for an Irish Stout?" · "Which styles allow roasted barley?" |
| **recipe_help** | 10 | "How much Maris Otter for 20 L at 1.050?" · "What hop schedule gets me 40 IBU in a 20 L boil?" · "Suggest a yeast for a 1.070 stout" |
| **inventory** | 8 | "How much Citra do I have?" · "Do I have enough base malt for a 20 L batch?" · "What's expiring in the next 3 months?" |
| **batch_analysis** | 12 | "Which IPAs were bitter with dry hop > 8 g/L?" · "Compare #12 and #17" · "Average attenuation with US-05?" · "Was my last stout in style?" |
| **book_rag** | 12 | "What causes diacetyl?" · "Explain sulfate-to-chloride ratio" · "What is hot-side aeration?" |
| **language_quality** | 8 | Complex multi-clause questions checking fluency, unit conventions, and citation formatting |

Plus **10 adversarial cases** — the ones that actually catch regressions:

- "How much Simcoe do I have?" *(you own none → must say "no record", not invent)*
- "What did I think of batch #99?" *(doesn't exist → must say so)*
- "What's the ideal dry hop rate?" *(no single answer → must not fabricate precision)*
- "Delete all my batches." *(must refuse; also verifies read-only actually holds)*
- "My mash tun is 40 L, not 30." *(must record a correction)*

### 10.2 Metrics

| Metric | How | Type | Gate |
|---|---|---|---|
| **Retrieval hit rate@5** | `expected_chunk_ids ∩ chunk_ids` from `mem.chat_turns` | deterministic | ≥ **0.85** |
| **Retrieval hit rate@1** | same, top result only | deterministic | ≥ 0.60 |
| **Tool-selection accuracy** | `tool_calls[0].name == expected_tool` | deterministic | ≥ **0.90** |
| **Truth-query correctness** | exact match on numeric/row answers vs SQL ground truth | deterministic | **1.00 — no tolerance** |
| **Hallucination rate on batch data** | any claim about user data not present in tool output | LLM judge + spot check | **0.00** |
| **Citation validity** | every `[S…]` resolves to a real returned source | deterministic (regex + set) | ≥ 0.95 |
| **Answer correctness** | n8n built-in AI Correctness metric (1–5 vs reference) | LLM judge | ≥ 4.0 mean |
| **Helpfulness** | n8n built-in | LLM judge | ≥ 4.0 mean |
| **Language quality** | judge scores fluency + unit conventions | LLM judge | ≥ 4.0 |
| **p50 / p95 latency** | execution time | deterministic | ≤ 8 s / ≤ 20 s |

**Truth-query correctness has no tolerance band.** A wrong inventory number isn't a low score, it's a bug — the whole architecture exists to make that class of error impossible. If it's ever below 1.00, stop feature work and find out why.

**Weight deterministic metrics above judged ones.** Your judge is a local model sharing the generator's blind spots. LLM-judged scores are a trend line, not a gate.

### 10.3 How to run it

**In n8n, via the Evaluations feature.** WF6 uses an Evaluation Trigger over a Data Table, calls the real WF4, and records with `Set Metrics`. The `Check If Evaluating` operation branches so eval runs skip WF5 (you don't want the eval set writing memories).

Three reasons this beats an external script: you test the *actual production workflow* rather than a reimplementation; the Evaluations tab gives run-over-run score history for free; and there's no export/import step to drift.

Complement it with **production metrics from `mem.chat_turns`** — a weekly query over `tool_calls` and `chunk_ids` from real conversations catches drift the fixed set never will.

**Discipline: change one variable per run.** Chunk size, *or* embedder, *or* prompt, *or* `rrf_k`. Two changes and the result is uninterpretable. This is the most commonly ignored and most consequential rule in the whole plan.

### 10.4 Baselines before adding complexity

Establish the Phase 2 baseline (`bge-m3`, `HybridChunker@512`, RRF `k=50`, top-6, no reranker, no Qdrant) and record it. Then:

| Addition | Only if | And first try |
|---|---|---|
| **Reranker** (§4.4) | hit@5 ≥ 0.85 **but** hit@1 < 0.60 — good recall, bad ordering | tune `rrf_k` (try 20 and 60); over-fetch 80 instead of 40 |
| **Qdrant** (§3.6) | all four exit criteria met | re-chunk at 384 or 768 tokens; A/B `qwen3-embedding` via WF7 |
| **Pre-router** (§7.2) | tool accuracy < 0.80 after rewriting descriptions | rewrite the descriptions — usually the actual fix |
| **Bigger chat model** | correctness < 4.0 with tool accuracy ≥ 0.90 | `num_ctx`, prompt length, chunk count |
| **More tools** | a whole intent class is unanswerable | widen an existing tool's parameters |

**The ordering matters.** Each row's "try first" is cheaper than the addition and fixes the problem more often. Reaching for infrastructure before tuning is how a two-service stack becomes a six-service stack that isn't any better.

---

## 11. Phased rollout

> **Build status — 2026-07-27.** Phase 0 ✅ complete and verified against the live
> DB. Phase 1 🟡 in progress: WF2 (structured/BJCP) done, WF1 (document) not started.
> Phases 2–5 ⬜ not started. Status marks below are **verified**, not asserted —
> each ✅ names the check that produced it. See §11.1 for the defect ledger.

### Phase 0 — Schema and demolition *(one evening)* — ✅ **COMPLETE**

**Goal:** a clean foundation and a smaller compose file.

Build: ✅ verify `bge-m3` returns 1024 dims on GPU · ✅ create `kb`/`brew`/`mem`/`nlq` schemas · ✅ `kb` DDL + HNSW index (`chunk_embeddings_hnsw_idx`, `vector_cosine_ops`, m=16, ef_construction=64) · ✅ `nlq.search_knowledge` · ✅ `agent_ro`/`n8n_agent` roles.

Deprecate: ✅ `DROP TABLE documents` (`to_regclass('public.documents')` → NULL) · ✅ delete the 1536-dim snippet (`nods_page_section` → NULL) · ✅ remove Qdrant and Open WebUI from compose (neither appears as a service) · ⬜ deactivate the demo Basic LLM Chain workflow *(Phase 2 deletes it outright — see §12 #6)*.

**Exit:** ✅ **both criteria met.**
- `nlq.search_knowledge` exists as `SECURITY DEFINER` with `search_path=kb, public`, executes without error, and returns fused results (evidence in §11.1).
- The read-only boundary holds at the grant level: `has_table_privilege('n8n_agent','brew.batches','SELECT')` → `false`, `has_schema_privilege('n8n_agent','kb','USAGE')` → `false`, `nlq` USAGE → `true`. `n8n_agent` also carries `default_transaction_read_only=on` and `statement_timeout=10s`.
- ⚠️ **Still owed:** a *live login* test as `n8n_agent`. Catalog privileges prove the grants; they do not prove the credential works, that the password is what n8n holds, or that `default_transaction_read_only` actually rejects a write. Do this before Phase 2 wires the agent.

### Phase 1 — One document, end to end *(a weekend)* — 🟡 **IN PROGRESS**

**Goal:** one PDF correctly in the database. No chat.

Build: ⬜ WF1 · ⬜ Docling async + poll · ⬜ chunking config against `bge-m3` · ⬜ cleaning rules + `kb.ingest_log` · ⬜ embedding loop (batch 32) · ⬜ folder state machine · ✅ **WF2 for BJCP** — 116 BJCP 2021 styles in `brew.bjcp_styles`, 116 style cards in `kb.chunks`, 116 `bge-m3` embeddings at 1024 dims, coverage 100%, re-run inserts nothing (D17).

Deprecate: ⬜ the n8n heading-splitter Code node *(blocked on WF1 — it is what replaces it)*.

**Exit:** ingest one real brewing book. Then: chunk count within ±20% of `page_count × 2.5`; zero chunks under 30 tokens; every chunk has a non-empty `heading_path` and a `page_from`; embedding coverage 100%; **re-running WF1 on the same file inserts nothing**; a hand-written SQL call to `nlq.search_knowledge('diacetyl rest', …)` returns something you'd have picked yourself.

That last one is the real gate. Read the top 6 chunks for five questions. If they're wrong, fix chunking now — every later phase inherits this.

⚠️ **The retrieval gate cannot be met by the current corpus.** 116 BJCP style cards are *style* knowledge, not *process* knowledge. `search_knowledge('diacetyl rest temperature for lagers', …)` returns lager style cards — correct behaviour over the corpus that exists, and useless as a quality signal. Judge retrieval only after WF1 puts a real book in `kb.chunks`; until then the style cards can verify **mechanics** (§11.1) but not **relevance**.

### Phase 1.1 — Fix the WF2 defect ledger *(before WF1 copies it)*

WF2 works and its output is correct, but four defects (D13–D16) sit in the node graph. WF1 will be built from the same patterns, so fix them in WF2 first rather than duplicating them:

| # | Node | Defect | Fix |
|---|------|--------|-----|
| D13 | any hashing node | Crypto node emits **MD5** into `file_sha256`; `char(64)` pads it silently, so it looks fine | Set `type: SHA256` explicitly in every hashing node. Audit existing rows — a padded MD5 is a false dedup key |
| D14 | Generate style cards, Verify coverage | Re-derive `version_id` via `ORDER BY version DESC LIMIT 1` instead of taking `$1` | One source of truth per run: the `version_id` returned by *Ensure KB doc + version*, threaded as `$1` |
| D15 | ingest chain | Parallel branches feeding a shared downstream node — n8n orders branches by **node position**, not data dependency | Keep ingest chains strictly linear |
| D16 | Verify coverage | Sets `is_current` without clearing the prior version | Flip in one statement; `document_versions_one_current_idx` (unique partial on `document_id WHERE is_current`) already exists to catch this |
| — | Clear old cards | Deletes from a **live** version mid-run | Build the new version, then flip `is_current` (D16). Never delete from the version that is currently serving |

**Exit:** WF2 re-run produces a byte-identical `kb.chunks` set, `file_sha256` is a genuine 64-hex SHA-256, and no node references a version it did not receive as a parameter.

### Phase 2 — Minimal agent, two tools *(a weekend)* — ⬜ not started

**Goal:** prove routing works before scaling the tool set.

Build: WF4 with Chat Trigger (streaming) → AI Agent (`gemma4:12b`) → Postgres Chat Memory → **exactly two tools**: `search_brewing_knowledge`, `find_batches` · `mem.chat_turns` logging · system prompt v1 · seed 3–5 real batches by hand · point `chat.html` at the new webhook.

Deprecate: the demo workflow — **delete it now**, not "later".

**Exit:** streaming visibly works in `chat.html`. A knowledge question calls the search tool; a batch question calls `find_batches`; **neither calls the other** across 20 manual questions. "How much Citra do I have?" (no tool yet) produces "I don't have a tool for that" — *not* an invented number. Baseline latency recorded.

### Phase 3 — Full tool set and NLQ *(1–2 weeks)* — ⬜ not started

**Goal:** every intent class answerable, with measurement.

Build: remaining `nlq` functions + tools (7 total) · brewing math functions · WF3 batch import · WF6 + the 60-question eval set + adversarial cases · system prompt v2 with the citation contract.

**Exit:** all §10.2 gates met. Specifically tool accuracy ≥ 0.90, truth correctness = 1.00, citation validity ≥ 0.95. Record the baseline — this is the number every future change is measured against.

### Phase 4 — Learning layer *(a weekend)* — ⬜ not started

Build: `mem.memories` + `mem.memory_embeddings` · WF5 extraction chain with structured output · confidence gate + stop-list · `save_memory` with human approval · preference injection into the system prompt.

**Exit:** ten conversations produce ≥ 3 correctly-extracted preferences and **zero junk memories**. Injected preferences visibly change a recommendation. **Re-run the Phase 3 eval — scores must not regress.** Memory that degrades general answers is a net negative.

### Phase 5 — Optional, evidence-driven *(only if §10.4 says so)* — ⬜ not started

Candidates in order of likely value: A/B `qwen3-embedding` via WF7 (cheap, no new infra) → tune `rrf_k` and over-fetch → reranker sidecar → re-chunk at a different `max_tokens` → Qdrant (last resort).

**Exit:** each addition is kept only if it moves a gated metric by ≥ 5% relative. Otherwise revert. A change that doesn't move a number is a change that added maintenance for nothing.

### 11.1 Verification evidence — 2026-07-27

Everything above marked ✅ was checked against the running Supabase instance
(`postgres`, port 5432), not inferred from the migration files.

**`nlq.search_knowledge` — mechanics confirmed, relevance not yet testable.**

The function is live and both retrieval arms provably contribute. The proof uses a
deliberately *mismatched* pair — the FTS text and the query embedding describe
different things — so each arm's contribution is separable in the output:

```sql
-- embedding is bge-m3("diacetyl rest temperature for lagers"); text is unrelated
SELECT doc_title, heading_path[array_length(heading_path,1)] AS leaf, score
FROM nlq.search_knowledge('roasted barley dry stout', :'q'::vector(1024), 6);
```

| leaf | score | arm |
|---|---|---|
| 2A International Pale Lager | 0.01961 | vector rank 1 |
| 15A Irish Red Ale | 0.01961 | **FTS rank 1** |
| 2C International Dark Lager | 0.01923 | vector rank 2 |
| 15B Irish Stout | 0.01923 | **FTS rank 2** |
| 3A Czech Pale Lager | 0.01887 | vector rank 3 |
| 3C Czech Amber Lager | 0.01852 | vector rank 4 |

Lagers come from the embedding, Irish styles from the text — interleaved exactly as
RRF should. The scores decode cleanly: `1/(50+1)=0.01961`, `1/(50+2)=0.01923`, and
so on.

**Read `0.0196` as a warning, not a pass.** Every score here is a *single-arm* score.
A chunk found by both arms would score ≈ `0.039`. Across the whole style-card corpus
there is currently **no query where both arms agree on the same chunk** — the FTS arm
returns 0 hits for process-shaped queries (`'diacetyl rest temperature for lagers'` →
0 rows matching `c.fts`), because style cards contain no process vocabulary. RRF is
therefore running degenerate-to-vector-only most of the time. That is a corpus
property, not a bug, and it will resolve when WF1 lands a real book. Until then:

> **Do not tune `p_rrf_k` against this corpus.** With one arm empty, `rrf_k` only
> rescales a monotonic list — it cannot change the ordering, so any "improvement"
> you measure is noise. `rrf_k` tuning belongs in Phase 5 (§10.4), after Phase 1.

**Read-only boundary — grants confirmed, credential not.** See the Phase 0 exit note.
The outstanding test is a real connection:

```bash
psql "postgresql://n8n_agent:<pw>@localhost:5432/postgres" \
  -c "SELECT * FROM brew.batches LIMIT 1;" \
  -c "SELECT count(*) FROM nlq.search_knowledge('stout', array_fill(0::real,ARRAY[1024])::vector, 3);" \
  -c "CREATE TABLE should_fail(x int);"
```

Expected: statement 1 `permission denied for schema brew`, statement 2 succeeds,
statement 3 `cannot execute CREATE TABLE in a read-only transaction`. All three must
hold; passing only the first two means the write ban is untested.

---

## 12. Deprecation list

Delete or stop using, in this order:

| # | Thing | Action | When |
|---|---|---|---|
| 1 | Supabase `documents` table (~117 rows) | **`DROP TABLE`.** Do not migrate — wrong chunking, no provenance | Phase 0 |
| 2 | The 1536-dim pgvector snippet (`nods_page_section`) | **Delete the file.** OpenAI-shaped; no Ollama embedder is 1536-dim | Phase 0 |
| 3 | Qdrant service + volume | **Remove from compose.** §3.6 | Phase 0 |
| 4 | Open WebUI | **Remove from compose.** Costs RAM you need; `chat.html` is the interface | Phase 0 |
| 5 | `llama3.2` as the chat model | **`ollama rm`.** A compose default, never a decision | Phase 0 |
| 6 | Demo "Chat Trigger → Basic LLM Chain → Ollama" workflow | **Delete.** Not deactivate — delete, so it can't be copied from | Phase 2 |
| 7 | n8n Code node markdown heading-splitter | **Delete.** Docling `HybridChunker` replaces it | Phase 1 |
| 8 | Filesystem-as-state-machine (`pending`/`processed` as dedup) | Keep folders as UI; **`file_sha256` is authoritative** | Phase 1 |
| 9 | Any n8n Vector Store node pointed at Supabase | **Don't adopt.** Assumes a LangChain table shape that fights your schema | — |
| 10 | `homebrew-rag` (FastAPI + Chroma + BM25) | Already reference-only. **Keep it that way** — do not partially port it | — |
| 11 | Single-Postgres temptation | Two instances, permanently. n8n metadata ≠ app data | — |
| 12 | Embedding anything from `brew.*` into `kb.*` | Architectural prohibition. Add a comment on `kb.chunks` saying so | — |

On #10: the `homebrew-rag` experiment does contain one idea worth stealing — BM25 + dense hybrid. You are stealing it, as `nlq.search_knowledge`. Steal the *idea*, not the *code*; a second Python service with its own Chroma store would reintroduce exactly the split-brain problem you're deleting Qdrant to avoid.

---

## 13. Risks and open decisions

### 13.1 Top five risks

**R1 — ROCm/gfx1201 instability.** *Likelihood: medium. Impact: total.*
RDNA 4 needs ROCm 7.x. There are open reports of `rocminfo`/Ollama hanging during HSA discovery on some ROCm 7.1.x combinations, and the Windows path is broken by default. Linux + `ollama/ollama:rocm` in Docker is the known-good route.
→ **Mitigate:** pin an exact working image digest, not `:latest`. Verify with `ollama ps` (must read 100% GPU). Keep a documented rollback to the last working tag. Keep a CPU-only embedding fallback for ingestion — slow but unblocks you.

**R2 — 32 GB RAM exhaustion.** *Likelihood: high. Impact: high.*
Full Supabase stack (Postgres, Kong, GoTrue, PostgREST, Realtime, Storage, Studio, Edge Functions) + Docling-ROCm (PyTorch) + n8n + Ollama host buffers + nginx. It adds up fast, and OOM manifests as random container restarts that look like application bugs.
→ **Mitigate:** deprecations #3 and #4 buy ~2 GB. Set explicit `mem_limit` per service so the OOM killer picks a victim you chose. Never ingest while chatting (§4.5). Watch Postgres `shared_buffers` — the default is likely too small once HNSW is in play.

**R3 — 12B tool-selection reliability.** *Likelihood: medium. Impact: high.*
The whole design assumes correct routing. If the model calls `search_brewing_knowledge` for an inventory question, you get a confident wrong answer — the exact failure the architecture exists to prevent.
→ **Mitigate:** ≤7 tools, disjoint boundaries, descriptions written as question-shapes. Measure it as a gated metric. Hard system-prompt rule that user-data claims require tool output. Escalation path in §7.2. And a nice property: because tools are read-only, a *wrong* tool call is a wasted round trip, not a data loss event.

**R4 — Embedding model lock-in.** *Likelihood: medium. Impact: medium.*
Re-embedding 40k chunks is hours. Changing dimension is a schema migration.
→ **Mitigate:** already designed around — `kb.chunk_embeddings` keyed by model, 1024-dim standard covering `bge-m3` and MRL-truncated `qwen3-embedding`, `content_sha256` for reuse, WF7 for zero-downtime A/B. Residual risk is a future model that's only good at 768 or 2048; accepted.

**R5 — Silent retrieval degradation.** *Likelihood: medium. Impact: medium.*
Retrieval quality decays invisibly as the corpus grows — nothing errors, answers just get vaguer, and there's no alarm to notice it.
→ **Mitigate:** `mem.chat_turns.chunk_ids` plus a weekly eval run (§10.3) is the only real defence. Treat a slow decline in hit-rate@5 over successive eval runs as a signal to re-tune chunking or `rrf_k`, not noise.

### 13.2 Open decisions — with my recommendation

| # | Decision | Recommendation | Rationale | Decide by |
|---|---|---|---|---|
| **D1** | Answer language (Setup/Project said HU, brief said EN) | **✅ Resolved: English only** | No cross-lingual requirement; simplifies D2/D4 to English-only criteria | **Closed** |
| **D2** | Embedding model + dimension *(open item in your log)* | **`bge-m3`, 1024 dim** | Strong English retrieval, 8k ctx, dimension-compatible with `qwen3-embedding` for A/B | Phase 0 — **blocks everything** |
| **D3** | pgvector-only vs + Qdrant *(open item)* | **pgvector only; delete Qdrant** | §3.6, with four exit criteria that won't fire at your scale | Phase 0 |
| **D4** | Chat LLM *(open item)* | **`gemma4:12b`**, fallback `qwen3:14b` | Apache 2.0, native tool calling, best reasoning-per-GB, leaves VRAM for a resident embedder | Phase 2 |
| **D5** | Chat UI long-term *(open item)* | **`chat.html` + `@n8n/chat`; drop Open WebUI** | Streaming supported; one UI to maintain; Open WebUI can't call your tool-based agent without extra plumbing | Phase 0 |
| **D6** | Chat memory backend | **n8n Postgres Chat Memory → Supabase**, plus your own `mem.chat_turns` | Agent memory and analytics are different jobs; n8n's blob serves the first, your table the second | Phase 2 |
| **D7** | Chunk size | **512 tokens, `merge_peers=true`** | Matches `bge-m3` comfortably; A/B 384 and 768 in Phase 5 | Phase 1 |
| **D8** | Reranker | **No in v1** | Ollama has no rerank endpoint; needs a sidecar. Revisit only on the §10.4 signal | Phase 5 |
| **D9** | Python sidecar | **None in v1** | Brewing math → Postgres functions. Only a reranker would justify one | — |
| **D10** | Cloud fallback | **None** | Local-first is a project requirement and 16 GB is adequate. Revisit only if D4's fallback also fails eval | — |
| **D11** | Docling `table_mode` | **`accurate`** | Brewing books are table-dense; `fast` destroys the highest-value content | Phase 1 |
| **D12** | Ingestion scheduling | **Nightly + chat-recency guard** | Prevents GPU contention with chat | Phase 1 |

**Proposed Decisions-log entries** (commit these; D2/D3/D4 close three of your four open items — D5 closes the fourth):

```
2026-07-22  D1  Answer language: English only. No cross-lingual retrieval
                requirement. Supersedes "Hungarian user-facing answers" in
                the original Project context doc.
2026-07-22  D2  Embedding model: bge-m3, 1024 dim. Schema standardised on 1024
                to permit A/B against MRL-truncated qwen3-embedding.
2026-07-22  D3  pgvector only. Qdrant removed from compose. Exit criteria: §3.6.
2026-07-22  D4  Chat model: gemma4:12b (Q4_K_M). Fallback qwen3:14b.
                llama3.2 removed.
2026-07-22  D5  Chat UI: chat.html + @n8n/chat with streaming. Open WebUI removed.
2026-07-22  D6  Chat memory: n8n Postgres Chat Memory on Supabase (window 6),
                plus mem.chat_turns for analytics and eval.
2026-07-22  D7  Chunking: Docling HybridChunker, tokenizer=BAAI/bge-m3,
                max_tokens=512, merge_peers=true. n8n heading-splitter deleted.
2026-07-22  D8  No reranker in v1 (Ollama has no rerank endpoint; sidecar required).
2026-07-22  D9  No Python sidecar in v1. Brewing math lives in Postgres functions.
2026-07-22  D10 Flat `documents` table dropped, not migrated.
2026-07-27  D13 file_sha256 must be SHA-256, not MD5. n8n Crypto node
                defaults to MD5; char(64) pads silently. Explicit
                type: SHA256 required in every hashing node.
2026-07-27  D14 One source of truth for version_id per run: the value
                returned by "Ensure KB doc + version", passed as $1.
                No re-deriving via ORDER BY version DESC LIMIT 1.
2026-07-27  D15 No parallel branches into a shared downstream node.
                n8n orders branches by node position, not data
                dependency. Ingest chains are linear.
2026-07-27  D16 is_current flip must clear the prior version in the same
                statement (unique partial index on document_id WHERE
                is_current).
2026-07-27  D17 WF2 complete: 116 BJCP 2021 styles in brew.bjcp_styles,
                116 style cards in kb.chunks, 116 bge-m3 embeddings at
                1024 dims, verified aligned and idempotent.
2026-07-27  D18 Phase 0 closed. nlq.search_knowledge and the
                agent_ro/n8n_agent/mem_writer roles were already applied
                by db-init — the "still open" status was stale. RRF
                fusion verified live (§11.1). Residual: no live-login
                test of the n8n_agent credential.
2026-07-27  D19 Retrieval relevance is NOT gated on the BJCP corpus.
                116 style cards carry no process vocabulary, so the FTS
                arm returns 0 for process queries and RRF degenerates to
                vector-only. rrf_k tuning deferred to Phase 5, after WF1
                lands a real book.
```

---

## Start tomorrow

> **⚠️ Superseded 2026-07-27.** This section was the Phase 0 kickoff and is done:
> `bge-m3` confirmed at 1024 dims, `kb` schema live, HNSW index built (§11.1).
> It is kept as the reference DDL, not as an instruction. **The current next
> action is Phase 1.1 → WF1** — see the top of §11.

**Confirm the embedding dimension, then create the `kb` schema.** Everything downstream is dimension-locked — this is the one decision you cannot cheaply reverse, so make it first and make it real rather than on paper.

```bash
# 1. Pull the embedder and confirm it's on the GPU
docker compose --profile gpu-amd exec ollama ollama pull bge-m3
docker compose --profile gpu-amd exec ollama ollama ps      # expect 100% GPU

# 2. Confirm the dimension is actually 1024 — do not take my word for it
curl -s http://localhost:11434/api/embed \
  -d '{"model":"bge-m3","input":"Irish stout mash temperature","keep_alive":-1}' \
  | python3 -c "import sys,json; print(len(json.load(sys.stdin)['embeddings'][0]))"
# expected: 1024
```

If that prints `1024`, run this against **Supabase** Postgres (port 5432 — *not* the n8n instance):

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS kb;

CREATE TABLE kb.documents (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  slug       text NOT NULL UNIQUE,
  title      text NOT NULL,
  doc_type   text NOT NULL
             CHECK (doc_type IN ('book','style_guide','article','datasheet','note')),
  authors    text[],
  language   text NOT NULL DEFAULT 'en',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE kb.document_versions (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  document_id     bigint NOT NULL REFERENCES kb.documents(id) ON DELETE CASCADE,
  version         int NOT NULL,
  source_filename text NOT NULL,
  file_sha256     char(64) NOT NULL,
  docling_version text,
  chunker_config  jsonb NOT NULL DEFAULT '{}',
  page_count      int,
  image_dir       text,
  ingested_at     timestamptz NOT NULL DEFAULT now(),
  is_current      boolean NOT NULL DEFAULT false,
  UNIQUE (document_id, version),
  UNIQUE (file_sha256)
);
CREATE UNIQUE INDEX ON kb.document_versions (document_id) WHERE is_current;

CREATE TABLE kb.chunks (
  id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  version_id     bigint NOT NULL REFERENCES kb.document_versions(id) ON DELETE CASCADE,
  chunk_index    int NOT NULL,
  content        text NOT NULL,
  raw_content    text NOT NULL,
  heading_path   text[],
  page_from      int,
  page_to        int,
  token_count    int,
  image_refs     text[],
  content_sha256 char(64) NOT NULL,
  fts            tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
  UNIQUE (version_id, chunk_index)
);
COMMENT ON TABLE kb.chunks IS
  'KNOWLEDGE ONLY. Never insert data derived from brew.* — see architecture rule 2.';
CREATE INDEX ON kb.chunks USING gin (fts);
CREATE INDEX ON kb.chunks (content_sha256);

CREATE TABLE kb.chunk_embeddings (
  chunk_id   bigint NOT NULL REFERENCES kb.chunks(id) ON DELETE CASCADE,
  model      text NOT NULL,
  embedding  vector(1024) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chunk_id, model)
);
CREATE INDEX ON kb.chunk_embeddings USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

CREATE TABLE kb.ingest_log (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  version_id bigint REFERENCES kb.document_versions(id) ON DELETE CASCADE,
  stage      text NOT NULL,
  level      text NOT NULL CHECK (level IN ('info','warn','error')),
  message    text NOT NULL,
  detail     jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
```

Then, in the same session, `DROP TABLE IF EXISTS public.documents CASCADE;`.

That's the whole first step. The old table is gone, the new foundation exists, and the dimension is verified rather than assumed. Everything in Phase 0's remaining checklist — `nlq.search_knowledge`, the roles, the compose cleanup — builds on exactly this and can wait for the next sitting.
