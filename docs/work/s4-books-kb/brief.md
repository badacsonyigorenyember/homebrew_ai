# S4 · Books into the knowledge base, with a retrieval eval (P7)

Status: approved
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
a fixed retrieval test set measures recall@5 above a bar set from the first measured run. A
further book can be added later with one small, documented step.

## Scope
In:
- Ingestion as a Python loader in `loaders/`: PDF → Docling Serve (structured Markdown +
  HybridChunker) → bge-m3 embeddings → `kb.chunk`, with `ref.source` rows (title, edition,
  licence, `file_path`). Python, because adding a book later is then one source entry and one
  command, tested like the other loaders, and the first build found the Docling poll loop awkward
  in n8n.
- Hybrid retrieval: vector (HNSW, cosine) + full text (GIN), fused, as one function the pipeline
  calls.
- A retrieval test set: questions with the chunks that answer them, built and checked with the
  `retrieval-evaluation-metrics` skill; recall@5, MRR reported.
- Re-ingesting one book replaces its chunks only.
- Adding a further book later is a small, documented step that does not re-ingest the others.

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
R6. An eval run prints recall@5 and MRR, and the result is recorded in PROJECT.md §8. The
    recall@5 bar is set from the first measured run and written down before the first tuning
    change; later runs are judged against that fixed bar.
R7. Adding a further book later takes one source entry and one command, written down in the
    docs, and leaves the other books' chunks untouched.

## Constraints
- PROJECT.md §6.1: book text is knowledge, retrieved and cited; numbers come from SQL.
- §6.7: doc → calculation pass first.
- Embedding model `bge-m3` (1024 dims) matches `kb.chunk.embedding vector(1024)`.
- Pipeline lives in n8n; one-off load jobs may be Python (`loaders/`), PROJECT.md §4. Ingestion
  is such a load job; retrieval is what the pipeline calls.

## Assumptions
- Docling Serve and Ollama run on the GPU as in the first build *(Docling 🟢 per PROJECT.md §4)*.
- The first build reached ~2.7k chunks from 11 sources; three books give fewer *(estimate)*.

## Acceptance criteria
A1. Three books in `ref.source` with `file_path`; `kb.chunk` rows for each; a second ingest leaves
    counts unchanged (R1, R2).
A2. Each book's doc → calc notes exist (R3).
A3. The retrieval function returns 5 chunks with source and page for a test question (R4).
A4. The test set has ≥ 30 reviewed questions (R5).
A5. recall@5 and MRR of the first measured run are recorded, the recall@5 bar is written down
    from it before any tuning change, and the final run meets that bar (R6, G7).
A6. The docs say how to add a book; following them for one book adds its `ref.source` row and
    chunks, and the other books' chunk counts are unchanged (R7).

## Open questions

## Deviations
- 2026-10-16 · Scope, Constraints: ingestion is a Python loader in `loaders/`, not n8n — user
  asked for whichever way makes adding more books later easy.
- 2026-10-16 · R7, A6 added: adding a further book is one source entry plus one documented
  command, without re-ingesting the others — same user answer.
- 2026-10-16 · R6, A5: recall@5 bar is set from the first measured run and fixed before the first
  tuning change (was "an agreed bar") — user chose "set after first run".
