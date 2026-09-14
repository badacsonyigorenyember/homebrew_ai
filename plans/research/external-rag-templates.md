# External templates and skills — evaluation record

**Dated 2026-09-13.** Six third-party resources were evaluated against this
stack. This file records what was taken, what was rejected, and why, so the
rejections are not re-litigated. Nothing here is committed work — the two
"extractable" items in §2 are candidates that must clear the Phase 3 eval before
they touch the retrieval path.

| # | Resource | Outcome |
|---|---|---|
| 1 | [WASD-Team/n8n-claude-skill](https://github.com/WASD-Team/n8n-claude-skill) | **Adopted**, rewritten as `.claude/skills/n8n-workflows/` |
| 2 | [realraelrr/docling-skill](https://github.com/realraelrr/docling-skill) | Rejected — §3.1 |
| 3 | [n8n template 8008 · enriched retrieval](https://n8n.io/workflows/8008-smarter-rag-agents-with-enriched-retrieval-and-modular-workflows/) | Not imported; two ideas extracted — §2 |
| 4 | [n8n template 6345 · Supabase + Cohere](https://n8n.io/workflows/6345-answer-questions-from-documents-with-rag-using-supabase-openai-and-cohere-reranker/) | Rejected — §3.2 |
| 5 | [Pendia/Book-to-AI-Skill](https://github.com/Pendia/Book-to-AI-Skill) | Rejected — §3.3 |
| 6 | [kopias/rag-pipeline-vector-db](https://github.com/kopias/rag-pipeline-vector-db) | Rejected — §3.4 |

---

## 1. What was adopted

Template 8008 and the WASD skill were the only two with anything this stack does
not already have. The skill became `.claude/skills/n8n-workflows/`, rewritten
rather than vendored: upstream declares no licence, its node reference covers
Telegram/Slack/Google Sheets that this repo never uses, and at least one of its
claims is false here. Provenance and per-claim evidence tags are in that
skill's `SKILL.md`.

Two findings came out of checking it against `n8n/demo-data/workflows/`:

- **`$input` appears in 14 Code nodes** and may not survive a programmatic
  write-back. Unverified; test procedure in the skill's
  `reference/api-and-mcp-writeback.md`. This is the one item with a deadline —
  it must be settled before the first MCP-driven workflow edit.
- **The Postgres typeVersion 2.6 hazard does not apply.** All 23 nodes
  parameterise through `options.queryReplacement`; no `query` field contains
  `{{ }}`, so 2.6's rewrite has nothing to act on. No migration needed.

---

## 2. Extracted from template 8008 — candidates, not decisions

Template 8008 is Supabase + Gemini `text-embedding-004` (768-dim) + Cohere,
writing to n8n's generic flat `documents` table. It cannot be imported: the
dimension lock is 1024 (`kb.chunk_embeddings.embedding vector(1024)`, HNSW
cosine), the four-table `kb` model exists specifically to replace that flat
table, and the stack is local-first while the template is cloud-API-bound. Its
"modular sub-workflows" selling point already exists here as `wf-step-retrieve`
and `wf-step-llm` composed by `cap-brainstorm-pairing`.

Two ideas survive the translation.

### 2.1 Reranking — a real gap

`nlq.search_knowledge` fuses FTS and vector results with RRF and stops
(`db/init/40_nlq.sql`). A cross-encoder rerank over the fused top-k is the
standard next lift, and it is the single highest-value item on this list.

Shape that fits this stack:

- **Model:** `bge-reranker-v2-m3`, the natural pair for the `bge-m3` embedder
  already resident in Ollama.
- **Serving is the open question.** Ollama exposes embeddings and generation but
  **no rerank endpoint**, so this needs a second service — Text Embeddings
  Inference or Infinity both expose `/rerank`. Verify current Ollama support
  before assuming another container is required. VRAM budget matters: 16 GB is
  already carrying `gemma4:12b` and `bge-m3` resident.
- **Placement:** widen `nlq.search_knowledge`'s `top_k`, rerank in
  `wf-step-retrieve` between `Search knowledge` and `Return rows`, return the
  trimmed set. This keeps the SQL function pure and the rerank swappable.
- **Cohere is wrong here** — cloud API, against the local-first premise.

### 2.2 LLM chunk-metadata enrichment — proposed, with a caveat

The template runs an asynchronous pass that asks an LLM to tag each chunk with
topics, audience level, risks, and a summary, then filters retrieval on those
tags.

**This conflicts with an existing architectural decision.** `kb.documents`
carries an explicit rule that `authority` must never enter ranking, because
boosting the reference source "suppresses exactly the disagreement this corpus
exists to surface, and does it invisibly — you would never see the passage that
lost." LLM-generated tags used as a retrieval filter are the same hazard in
different clothing, with the added problem that the tags are themselves model
output and unauditable.

If it is pursued, it belongs in **presentation**, not ranking — the same
resolution §5.6 already reached for `authority`. Enriched metadata that helps a
reader understand *why* two sources disagree is useful; metadata that silently
decides which source they see is not.

Note also that `kb.chunks` already carries real structural metadata that the
template synthesises with an LLM — `heading_path`, `page_from`/`page_to`,
`token_count`, `image_refs` — obtained deterministically from Docling. Much of
the template's enrichment is redundant here.

### 2.3 Evaluation gate

Neither idea goes in on intuition. Both change retrieval, and the Phase 3 eval
workflow exists precisely to measure that. `obs.runs` / `obs.steps` already
record step inputs and outputs, so a before/after comparison is available
without new instrumentation.

---

## 3. Rejected, with reasons

### 3.1 realraelrr/docling-skill

Covers neither of the two Docling surfaces this stack uses. It does not cover
the **docling-serve HTTP client** — but `docker-compose.yml:79-105` runs
docling-serve on :5001 and `wf1-ingest-book` drives it via submit → poll →
fetch. It does not cover **chunking** — but `HybridChunker` output is what fills
`kb.chunks`. What it adds instead is a local-CLI sidecar contract
(`source.md` / `source.manifest.json` / `source.evidence.json`) and CJK
normalisation, neither of which is needed.

The already-enabled `/docling` skill covers the remote Service Client for
self-hosted docling-serve *and* chunking, so it is strictly better here.

### 3.2 n8n template 6345

Architecturally a subset of 8008 without the enrichment pipeline, older, and it
requires community nodes. Same 768-dim and flat-`documents` incompatibilities.
Nothing in it that 8008 does not have.

### 3.3 Pendia/Book-to-AI-Skill

Answers a different question than the one asked. It compiles a book into a
`SKILL.md` plus per-chapter prose summaries — curated static context, not
chunks and embeddings. It produces no vectors and performs no retrieval.

Two conflicts beyond the mismatch. It is lossy by construction: an LLM summary
cannot carry `page_from`/`page_to`, `heading_path`, or `image_refs`, so
citation-backed answers are gone. And collapsing each book to a summary destroys
cross-source disagreement, which is the thing this corpus exists to expose. Its
extraction path for technical books is `docling`, already in use.

### 3.4 kopias/rag-pipeline-vector-db

Self-excluding. Its own frontmatter says not to use it for multi-hop or agentic
pipelines, or for a chunking-first build. `cap-brainstorm-pairing` is five steps
with two retrievals and three LLM calls, and chunking is among the most
deliberate parts of ingest. It teaches the single-LLM-call QRAG topology to
someone starting from zero, and duplicates the already-enabled `rag-pipeline-gen`
skill.
