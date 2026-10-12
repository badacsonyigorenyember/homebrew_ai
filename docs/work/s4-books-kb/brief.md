# S4 · Books into the knowledge base, with a retrieval eval (P7)

Status: draft
Slug: s4-books-kb · Branch: s4-books-kb
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) side track P7, checkpoint **G7**
(retrieval part) · [RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §8 P7 · [DATABASE.md](../../DATABASE.md) §4 ·
PROJECT.md §6.6
Needs: `m0-harness` shipped; the doc → calc passes of `s1-maths` and `m7-process` done for the
books they read

## Why
The recipe sheet (M8) should say *why* each choice was made and cite a book, and Priority 2
(brewing Q&A) needs the same retrieval. `kb.chunk` exists with its HNSW and GIN indexes but is
empty. Only prose belongs there: tables and formulas go through the doc → calculation pass first,
so `kb` never becomes a second, unchecked source of numbers.

## Goal
*How to Brew*, *Water* and *Yeast* are chunked, embedded and searchable by hybrid retrieval, and
a fixed retrieval test set measures recall@5 above a bar you agree.

## Scope
In:
- Ingestion: PDF → Docling Serve (structured Markdown + HybridChunker) → bge-m3 embeddings →
  `kb.chunk`, with `ref.source` rows (title, edition, licence, `file_path`).
- Hybrid retrieval: vector (HNSW, cosine) + full text (GIN), fused, as one function the pipeline
  calls.
- A retrieval test set: questions with the chunks that answer them, built and checked with the
  `retrieval-evaluation-metrics` skill; recall@5, MRR reported.
- Re-ingesting one book replaces its chunks only.

Out:
- The other §5 sources (Stout Style Guide, BYO, Draught Beer Quality Manual) until these three
  pass. Web search (SearXNG). A chat Q&A feature (Priority 2). Corpus data (never in `kb`).

## Requirements
R1. Each book is a `ref.source` row; its chunks keep section path, page, text and token count.
R2. Ingesting a book twice gives the same chunks (no duplicates); re-ingesting replaces only that
    book's chunks.
R3. Tables and formulas already turned into data or code by a doc → calc pass are noted per book;
    the pass's write-up says which pages they were.
R4. Retrieval takes a question and returns the top k chunks with scores and their source and page,
    from fused vector and full-text ranks.
R5. A test set of at least 30 questions across the three books, each with its expected chunk(s),
    reviewed by you, lives in `evals/`.
R6. An eval run prints recall@5 and MRR, and the result is recorded in PROJECT.md §8.

## Constraints
- PROJECT.md §6.1: book text is knowledge, retrieved and cited; numbers come from SQL.
- §6.7: doc → calculation pass first.
- Embedding model `bge-m3` (1024 dims) matches `kb.chunk.embedding vector(1024)`.
- Pipeline lives in n8n; one-off load jobs may be Python (`loaders/`), PROJECT.md §4.

## Assumptions
- Docling Serve and Ollama run on the GPU as in the first build *(Docling 🟢 per PROJECT.md §4)*.
- The first build reached ~2.7k chunks from 11 sources; three books give fewer *(estimate)*.

## Acceptance criteria
A1. Three books in `ref.source` with `file_path`; `kb.chunk` rows for each; a second ingest leaves
    counts unchanged (R1, R2).
A2. Each book's doc → calc notes exist (R3).
A3. The retrieval function returns 5 chunks with source and page for a test question (R4).
A4. The test set has ≥ 30 reviewed questions (R5).
A5. recall@5 and MRR are recorded and meet the agreed bar (R6, G7).

## Open questions
1. Ingestion in n8n or a Python loader? — options: a) a Python loader in `loaders/` (one-off load
   job, tested like the others); b) an n8n workflow — recommend a: PROJECT.md §4 keeps one-off
   extract/load jobs in Python, and the first build found the Docling poll loop awkward in n8n.
2. The recall@5 bar? — options: a) ≥ 0.8; b) set after the first measured run — recommend b, then
   fix it before the first tuning change.

## Deviations
