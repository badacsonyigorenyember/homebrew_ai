# S4 · Books into the knowledge base, with a retrieval eval — implementation plan

Stage: approved
Brief: [brief.md](brief.md)
Branch: s4-books-kb

## Approach
One Python loader, `loaders/books.py`, holds a `BOOKS` list (one entry per book: slug, title,
edition, publisher, licence, `file_path`, pages to skip) and one command,
`python -m loaders.books <slug>`. It sends the PDF to Docling Serve's hybrid chunk endpoint
(the settings the first build proved, archive `plans/archive/01-wf1-ingest-document.md` §2–3),
keeps only prose (markdown tables cut out, skipped pages and tiny leftovers dropped), embeds each
chunk with `bge-m3` through Ollama, upserts the book's `ref.source` row on its slug and, in one
transaction, deletes that book's `kb.chunk` rows and inserts the new ones. So a re-ingest
replaces one book only (R2), and a new book is one `BOOKS` entry plus one command (R7).

Retrieval is one SQL function, `app.kb_search(query_text, query_embedding, k)`, in
`db/040_kb_search.sql`: the 40 nearest chunks by cosine (HNSW) and the 40 best full-text matches
(GIN, any query word) are fused by reciprocal rank (k = 60). The caller embeds the question
first (the pipeline with an HTTP call to Ollama, as step 1 does; the eval in Python). The
eval, `python -m evals.retrieval`, runs a reviewed question set in
`evals/retrieval_questions.toml` and prints recall@5 and MRR@10. Expected chunks are named by
book and a short quote, not by chunk id, so they survive a re-ingest.

Tables are never stored in `kb` (DATABASE.md §4: only prose), whether or not a doc → calc pass
has turned them into data yet. `docs/BOOKS.md` records, per book, which pages hold tables and
formulas and which pass covers them (R3), and how to add a book (R7).

Page numbers are PDF page numbers (1-based, as Docling reports them), not printed page numbers.

## Files
| Path | New / changed | Purpose |
|---|---|---|
| `loaders/books.py` | new | `BOOKS` list; Docling call, prose filter, embedding, source upsert, per-book chunk replace; CLI |
| `tests/test_books.py` | new | unit tests on synthetic Docling output; stack tests for source upsert and per-book replace |
| `db/040_kb_search.sql` | new | `app.kb_search`: hybrid retrieval, reciprocal-rank fusion |
| `tests/test_kb_search.py` | new | stack tests on synthetic chunks, rolled back |
| `evals/retrieval.py` | new | `search()`, quote matching, recall@k, MRR, runner CLI, the recall@5 bar |
| `evals/retrieval_questions.toml` | new | ≥ 40 reviewed questions across the five books, ≥ 8 per book |
| `tests/test_retrieval_eval.py` | new | metric unit tests; test-set shape; every expected quote resolves to a chunk (stack) |
| `evals/results/<date>-s4-first.json`, `evals/results/<date>-s4.json` | new | first measured run, final run |
| `docs/BOOKS.md` | new | books in `kb`, how to add a book, doc → calc notes per book |
| `docs/DATABASE.md` | changed | §4: `app.kb_search`, page numbering, link to BOOKS.md; §7 row 7 |
| `requirements.txt` | changed | add `requests` (multipart upload to Docling) |
| `PROJECT.md` | changed | §4 vector search and Scripts rows, §5 book rows, §8 entries |

## Tasks

### Task 1: Loader that turns a Docling chunk result into prose rows
Why: R1, R2, R7; the pure part of the loader, tested without the stack.
- [ ] Add `requests>=2.32` to `requirements.txt` (already in `.venv`; `urllib` has no multipart).
- [ ] Write `loaders/books.py` with a module docstring that says how to run it and how to add a
      book (point at `docs/BOOKS.md`, written in Task 4). Contents, in this order:
  - `@dataclass(frozen=True) class Book`: `slug`, `title`, `edition`, `publisher`, `licence`,
    `file_path` (relative to the repo root), `skip_pages: tuple[tuple[int, int], ...] = ()`
    (inclusive PDF page ranges left out: contents, index, reading lists), `ocr: bool = False`,
    `notes: str | None = None`. `BOOKS: dict[str, Book]`, first entry only:
    `palmer-how-to-brew`, title `How to Brew`, edition `Fourth edition 2017`, publisher
    `Brewers Publications` (as in `db/011_ref_sources.sql`), `file_path`
    `shared/rag-files/books/how_to_brew.pdf`, licence
    `© Brewers Publications, all rights reserved; personal copy, local use only`, notes
    `Tables 18.5 and 24.1 in ref.fermentable; prose in kb.chunk; doc → calc notes in docs/BOOKS.md`.
  - Constants `DOCLING_URL = "http://localhost:5001"`, `OLLAMA_URL = "http://localhost:11434"`,
    `EMBED_MODEL = "bge-m3"`, `EMBED_DIMS = 1024`, `MAX_TOKENS = 512`, `MIN_WORDS = 20`,
    `SCRATCH = ROOT / "shared" / "docling-scratch"` (gitignored).
  - `docling_form(book) -> dict`: the multipart fields, exactly:
    `convert_from_formats=pdf`, `convert_do_ocr=<book.ocr>`, `convert_pdf_backend=dlparse_v4`,
    `convert_table_mode=accurate`, `convert_do_table_structure=true`,
    `convert_include_images=false`, `convert_image_export_mode=placeholder`,
    `convert_abort_on_error=false`, `chunking_tokenizer=BAAI/bge-m3`,
    `chunking_max_tokens=512`, `chunking_merge_peers=true`, `chunking_include_raw_text=true`,
    `chunking_use_markdown_tables=true`. (Default tokenizer is MiniLM: it must be set. Markdown
    tables make tables recognisable so they can be cut. No `to_formats` on chunk endpoints.)
  - `check_result(result: dict) -> list[dict]`: returns `result["chunks"]`; raises
    `RuntimeError` naming the reason when `documents[0].status` is not `success` or there are no
    chunks. (A failed conversion still reports task `success` with `chunks: []`.)
  - `run_docling(book) -> dict`: `POST /v1/chunk/hybrid/file/async` with the PDF as `files`,
    poll `GET /v1/status/poll/{task_id}` every 10 s while `task_status` is `pending` or
    `started` (give up after 2 h), then `GET /v1/result/{task_id}`. Save the result to
    `SCRATCH / f"{book.slug}.chunks.json"` and return it.
  - `strip_tables(text) -> str`: drop every line whose stripped form starts with `|` (markdown
    table rows, header separator included), then collapse runs of blank lines. Prose lines are
    kept byte for byte.
  - `chunk_rows(chunks, book) -> list[dict]`: for each chunk in `chunk_index` order:
    `text = strip_tables(raw_text).strip()`; `page = min(page_numbers)`;
    `section_path = " > ".join(headings or [])`; drop it when `page` is in `book.skip_pages`
    or `text` has fewer than `MIN_WORDS` words; also count tables cut and the pages they were
    on. Returns rows `{section_path, page, text}` plus a stats dict (chunks in, kept, dropped by
    skip page, dropped as too short, pages with tables cut).
  - `embed_text(row) -> str`: `section_path + "\n\n" + text` (heading context helps the vector
    arm; `kb.chunk.text` keeps the prose only, so citations and `fts` see the book's words).
  - `parse_embedding(body: dict) -> tuple[list[float], int]`: the single vector and
    `prompt_eval_count`; raises `ValueError` unless there is exactly one vector of `EMBED_DIMS`.
  - `embed(text) -> tuple[list[float], int]`: `POST /api/embed` with
    `{"model": EMBED_MODEL, "input": text, "truncate": false, "keep_alive": -1}`, one text per call
    so `tokens` is that chunk's own count (`prompt_eval_count`, as bge-m3 counts what was embedded).
    `truncate: false` makes an over-long chunk fail instead of being cut silently.
- [ ] Write `tests/test_books.py` (unit part, synthetic chunks only; no book text in the repo):
  - `test_check_result_raises_on_failed_document`: `documents[0].status = "failure"`, 0 chunks → `RuntimeError`.
  - `test_check_result_raises_on_no_chunks`: `success` with `chunks: []` → `RuntimeError`.
  - `test_strip_tables_keeps_prose`: prose + 4-line markdown table + prose → both prose paragraphs, no `|` line.
  - `test_chunk_rows_drops_table_only_chunk`: a chunk that is only a table is dropped and counted.
  - `test_chunk_rows_skip_pages`: a chunk whose first page is in a skip range is dropped; one outside is kept.
  - `test_chunk_rows_page_and_section`: `page_numbers [12, 13]` → page 12; headings joined with ` > `.
  - `test_parse_embedding_rejects_wrong_dims`: 768 floats → `ValueError`; 1024 → vector and count.
  - `test_docling_form_sets_bge_m3_tokenizer`: form has `chunking_tokenizer = BAAI/bge-m3`, `chunking_use_markdown_tables = true`.
- [ ] Run `.venv/bin/pytest tests/test_books.py -m "not stack"`, expect all pass.
Done when: the unit tests pass and `python -m loaders.books --help` prints the usage.
Commit: `Add book loader: Docling chunks to prose rows`

### Task 2: Source upsert and per-book chunk replace
Why: R1, R2, R7 (re-ingest replaces one book only; the source row keeps its id).
- [ ] In `loaders/books.py` add:
  - `upsert_source(conn, book) -> int`: `insert into ref.source (slug, title, edition, publisher, licence, file_path, notes) … on conflict (slug) do update set` the same columns (`notes` only when the entry has one: `coalesce(excluded.notes, ref.source.notes)`), `returning id`. The `palmer-how-to-brew` row already exists and `ref.ingredient` rows point at it (honey), so its id must not change.
  - `replace_chunks(conn, source_id, rows) -> int`: `delete from kb.chunk where source_id = %s`, then insert each row (`source_id, section_path, page, text, tokens, embedding`; the embedding passed as the text `'[f1,f2,…]'` cast to `extensions.vector`). No commit inside: the caller's `with connect() as conn:` commits it all at once, so a failed run leaves the old chunks.
  - `main()`: `argparse` with `slug` (choices = `BOOKS`) and `--reuse-docling` (read `SCRATCH/<slug>.chunks.json` instead of calling Docling; for re-runs after changing `skip_pages`). Flow: Docling (or reuse) → `check_result` → `chunk_rows` → `embed` each row → one transaction: `upsert_source`, `replace_chunks`. Print the stats, the chunk count, min / median / max `tokens`, and the PDF pages where tables were cut.
- [ ] Add stack tests to `tests/test_books.py` (marked `stack`, each ends with `conn.rollback()`):
  - `test_upsert_source_keeps_id`: upsert a `Book` with slug `palmer-how-to-brew` and a changed edition → same id as before, edition changed (rolled back).
  - `test_replace_chunks_only_touches_its_book`: insert a throwaway source `test-book-a` and `test-book-b`, `replace_chunks` 3 synthetic rows into each (embedding = 1024 floats), then `replace_chunks` 2 rows into `a` → `a` has 2, `b` still 3, every other source's count unchanged (counted before and after).
  - `test_replace_chunks_twice_same_rows`: the same rows twice → same count and same `md5(string_agg(text, '|' order by page, section_path, text))`.
- [ ] Run `.venv/bin/pytest tests/test_books.py`, expect all pass with the stack up.
Done when: the tests pass; `select count(*) from kb.chunk` is still 0 (the tests rolled back).
Commit: `Add book source upsert and per-book chunk replace`

### Task 3: Hybrid retrieval function
Why: R4, A3.
- [ ] Write `db/040_kb_search.sql` (header like `db/014_kb.sql`: what it is, the apply command, idempotent). One function:
  ```sql
  create or replace function app.kb_search(
      query_text      text,
      query_embedding extensions.vector(1024),
      k               integer default 5,
      candidates      integer default 40,
      rrf_k           integer default 60)
  returns table (chunk_id bigint, source_slug text, source_title text, section_path text,
                 page integer, text text, score double precision, vec_rank integer, fts_rank integer)
  language sql stable
  set search_path = public, extensions
  ```
  Body, as readable CTEs with a comment each:
  - `vec`: `select id from kb.chunk order by embedding <=> query_embedding limit candidates` in a subquery, `row_number()` over that order outside it (so the HNSW index serves the inner `order by … limit`).
  - `words`: `replace(plainto_tsquery('english', query_text)::text, ' & ', ' | ')` cast to `tsquery`, so a chunk matching any query word counts (a whole question ANDed matches almost nothing).
  - `fts`: chunks with `fts @@ words`, ordered by `ts_rank_cd(fts, words) desc, id`, `limit candidates`, then numbered.
  - `fused`: full outer join of `vec` and `fts` on id; `score = coalesce(1.0 / (rrf_k + vec_rank), 0) + coalesce(1.0 / (rrf_k + fts_rank), 0)`.
  - Final select joins `kb.chunk` and `ref.source`, `order by score desc, chunk_id limit k`.
- [ ] Apply: `docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/040_kb_search.sql`; check the owner: `select proowner::regrole from pg_proc where proname = 'kb_search'` → `postgres`.
- [ ] Write `tests/test_kb_search.py` (stack, synthetic chunks under a throwaway source, rolled back; works whether or not real chunks are loaded). Query embedding = one-hot on dimension 0; real bge-m3 vectors are far from it.
  - `test_both_arms_rank_first`: chunk A has the one-hot embedding and the word `zyxquorble`; chunk B has only the word; chunk C only the embedding. Query `"zyxquorble fermentation"` → A first, B and C in the top 5, A's `vec_rank` and `fts_rank` both 1.
  - `test_any_query_word_matches`: a chunk with only one of the three query words is returned by the full-text arm (`fts_rank` not null).
  - `test_returns_k_rows_with_source_and_page`: 7 synthetic chunks, `k = 5` → 5 rows, each with `source_slug`, `page` not null.
  - `test_no_match_still_returns_vector_hits`: a query whose words are all stopwords → rows come from the vector arm only (`fts_rank` null).
- [ ] Run `.venv/bin/pytest tests/test_kb_search.py`, expect all pass.
Done when: tests pass and the function is owned by `postgres`.
Commit: `Add app.kb_search hybrid retrieval`

### Task 4: Ingest *How to Brew* and write the book notes
Why: R1, R2, R3, A1, A2 (first book), and the docs for R7.
- [ ] Probe first: `python -m loaders.books palmer-how-to-brew` (612 pages; expect several minutes in Docling, roughly 10–20 at the first build's 229 s per 248 pages). Read the printed stats and look at `shared/docling-scratch/palmer-how-to-brew.chunks.json`: which PDF pages are the contents, index, glossary or reading lists (look also with `pdftotext -f N -l N`). Check what formulas look like in the chunk text; if Docling leaves a placeholder line (for example `<!-- formula-not-decoded -->`), strip it in `strip_tables` too and add a unit test for it (Deviation line).
- [ ] Set `skip_pages` for the book from that probe, re-run with `--reuse-docling`. Check:
  `select count(*), min(tokens), percentile_disc(0.5) within group (order by tokens), max(tokens), count(*) filter (where text like '%|%|%') from kb.chunk c join ref.source s on s.id = c.source_id where s.slug = 'palmer-how-to-brew'` — expect hundreds of chunks, no chunk over ~600 tokens unexplained, table-like rows 0 (inspect any hit).
- [ ] Second ingest without `--reuse-docling` (a fresh Docling run). Before and after, record count and `md5(string_agg(text, '|' order by page, section_path, text))` for the book: both unchanged (A1, R2). If Docling is not deterministic, stop and record what differs.
- [ ] Write `docs/BOOKS.md`:
  1. **Books in `kb`**: table of slug, title / edition, file, PDF pages, skipped pages, chunks, ingested (date), measured.
  2. **Adding a book** (R7): put the PDF in `shared/rag-files/books/`; check it has a text layer (`pdffonts FILE` lists fonts; if none, set `ocr=True`); add one `Book` entry to `BOOKS` in `loaders/books.py`; run `python -m loaders.books <slug>`; look at the stats, set `skip_pages`, re-run with `--reuse-docling`; check the counts query (this book has chunks, other books' counts unchanged); write the book's doc → calc note below; add the book to PROJECT.md §5.
  3. **Doc → calc notes per book** (R3): for *How to Brew*, the PDF pages where the loader cut tables (from its stats) and the formula pages, each marked with the pass that turned it into data or code (`s1-maths` [doc-calc.md](finished/s1-maths/doc-calc.md) sections, `adjunct-fermentables` Tables 18.5 / 24.1) or "not passed yet (m7-process)". A cut table is never in `kb` either way.
- [ ] Update `docs/DATABASE.md` §4 (`app.kb_search`; `page` is the PDF page; `tokens` is bge-m3's count of the embedded text, heading path included; link BOOKS.md) and §7 row 7; link BOOKS.md from PROJECT.md §5. PROJECT.md: §5 *How to Brew* row (chunk count, measured), §4 vector search row, Scripts row (`loaders/books.py`, its tests), §8 entry.
Done when: the book has chunks, the second ingest left count and fingerprint unchanged, BOOKS.md has the How to Brew row and notes.
Commit: `Ingest How to Brew into kb, add docs/BOOKS.md`

### Task 5: Ingest *Water*
Why: R1, A1, A2.
The PDF is `shared/rag-files/books/palmer_kaminski_water.pdf` (checked 2026-10-16).
- [ ] Read title, edition and publisher from the PDF's copyright page; add the `Book` entry (slug `palmer-kaminski-water`, same licence wording with its publisher). Follow BOOKS.md §2 step by step; fix BOOKS.md where it was wrong or unclear (Deviation line).
- [ ] Record `How to Brew`'s count before and after: unchanged.
- [ ] Add the book's row and doc → calc note to BOOKS.md: its table and formula pages, all "not passed yet (m7-process)" unless a pass exists. PROJECT.md §5 row, §8 entry.
Done when: the book has chunks and How to Brew's count is unchanged.
Commit: `Ingest Water into kb`

### Task 6: Ingest *Yeast* by following the docs (A6)
Why: R7, A6, A1, A2.
The PDF is `shared/rag-files/books/white_zainasheff_yeast.pdf` (checked 2026-10-16).
- [ ] Before touching anything, record every book's chunk count. Then follow BOOKS.md §2 literally, with no step from outside it (slug `white-zainasheff-yeast`). Note any step that was missing or wrong, fix BOOKS.md, and record it as a Deviation line.
- [ ] After: Yeast has a `ref.source` row with `file_path` and chunks; How to Brew and Water counts are unchanged (A6).
- [ ] Second ingest of Yeast with `--reuse-docling`: count and fingerprint unchanged (A1).
- [ ] BOOKS.md row and doc → calc note; PROJECT.md §5 row, §8 entry (A6 result with the counts).
Done when: A6 holds as measured, and `select s.slug, count(*) from kb.chunk c join ref.source s on s.id = c.source_id group by 1` shows three books.
Commit: `Ingest Yeast into kb following docs/BOOKS.md`

### Task 6b: Ingest *Malt* and the BJCP exam study guide
Why: R1, R7, A1 (books four and five).
- [ ] Record every book's chunk count. Follow BOOKS.md §2 for `shared/rag-files/books/mallett_malt.pdf` (slug `mallett-malt`, Brewers Publications) and then `shared/rag-files/books/bjcp_exam_study_guide_2017.pdf` (slug `bjcp-exam-study-guide-2017`, title *BJCP Beer Exam Study Guide*, edition `Last revised December 2017`, publisher `Beer Judge Certification Program`, licence `© 1998-2017 the authors and the BJCP; free to download; local use`). For the study guide, `skip_pages` covers the front matter and sections I–III (exam rules, judging procedure, exam questions); only section IV, Ingredients and the Brewing Process, is kept. Its S0 style-triple table is a table, so it is cut anyway (it is s6-style-neighbours' data).
- [ ] After each: the new book has chunks, the other books' counts are unchanged.
- [ ] BOOKS.md rows and doc → calc notes (*Malt*: no pass, malt data comes from the maltster catalogues; study guide: the §IV.B water table goes to m7-process). PROJECT.md §5 rows, §8 entry.
Done when: `select s.slug, count(*) from kb.chunk c join ref.source s on s.id = c.source_id group by 1` shows five books, and the first three kept their counts.
Commit: `Ingest Malt and the BJCP study guide into kb`

### Task 7: Retrieval eval runner and metrics
Why: R4, R6, A3.
- [ ] Write `evals/retrieval.py`:
  - `search(conn, question, k=5) -> list[dict]`: `loaders.books.embed(question)`, then `select * from app.kb_search(%s, %s::extensions.vector, %s)`.
  - `normalise(s)`: lower case, runs of whitespace to one space, curly quotes and dashes to plain.
  - `is_hit(result, expect, book) -> bool`: `result.source_slug == book` and `normalise(expect.quote)` is in `normalise(result.text)`.
  - `recall_at_k(results, expects, book, k)`: share of the question's expected passages hit in the top k. `reciprocal_rank(results, expects, book, k=10)`: 1 / rank of the first hit, 0 if none in the top 10.
  - `RECALL_AT_5_BAR: float | None = None` with a comment: set once from the first measured run (Task 9), before any tuning change; never moved afterwards without a Deviation line.
  - CLI: `python -m evals.retrieval` runs every question (k = 10 for MRR, recall from the top 5) and prints recall@5, MRR@10, both per book, the misses (question id, expected page, ranks found), and "bar met / not met" when the bar is set. `--save LABEL` writes `evals/results/<date>-<LABEL>.json` (summary + per question: ranks of each expected passage, top 5 chunk ids, pages, scores). `--question "…"` prints the top 5 (source, page, section, score, first 200 characters) for a single question (A3).
- [ ] Write `tests/test_retrieval_eval.py` (unit): `test_recall_at_5` (2 expects, 1 hit at rank 3 → 0.5; hit at rank 6 → 0), `test_reciprocal_rank` (first hit at rank 2 → 0.5; none → 0), `test_is_hit_wrong_book` (quote matches but other book → no hit), `test_normalise_whitespace_and_quotes`.
- [ ] Run `.venv/bin/pytest tests/test_retrieval_eval.py`, expect pass. Run `python -m evals.retrieval --question "how long and at what temperature should a diacetyl rest be"` → 5 rows, each with source and page (A3).
Done when: tests pass and the A3 command prints 5 cited chunks.
Commit: `Add retrieval eval runner and metrics`

### Task 8: Retrieval test set, reviewed by the user
Why: R5, A4.
**Needs from the user:** a review of every question (blocking; ask with the passages shown).
- [ ] Pick passages before running any retrieval, so the set is not shaped by what retrieval finds: per book, 9 chunks spread over the book (every Nth chunk in page order, skipping ones with no answerable brewing fact). For each, write a question a brewer would ask, in their own words (avoid copying the passage's distinctive phrase where a natural question would not use it), and an `expect` with `page` and a `quote`: 4–12 words copied exactly from the chunk that answer the question. Add a second `expect` where the answer is in two places. Mix kinds: process (how/when), cause (why does…), ingredient, troubleshooting.
- [ ] `evals/retrieval_questions.toml`: header comment (what it is, how expects match, that only short quotes are kept, who reviewed it and when), then `[[question]]` with `id` (`q01`…), `book` (slug), `question`, and `[[question.expect]]` `page`, `quote`. ≥ 40 questions, ≥ 8 per book.
- [ ] Add to `tests/test_retrieval_eval.py`: `test_question_set_shape` (unit: ≥ 40, ≥ 8 per book, unique ids, every book a `BOOKS` slug, quotes 4–12 words) and `test_every_quote_resolves` (stack: each quote, normalised, is in at least one chunk of its book; an unresolved quote would silently lower recall).
- [ ] Show the user each question with its book, page and the full chunk text it points to (from the DB, in the conversation, not in a committed file). Apply their edits; write the review date in the header.
- [ ] Run `.venv/bin/pytest tests/test_retrieval_eval.py`, expect pass.
Done when: ≥ 40 questions, reviewed by the user, every quote resolves.
Commit: `Add reviewed retrieval test set`

### Task 9: First measured run, the bar, and the record
Why: R6, A5, G7 (retrieval part).
**Needs from the user:** the recall@5 bar, chosen from the first run.
- [ ] `python -m evals.retrieval --save s4-first`. Report recall@5, MRR@10, per book, and the misses to the user. Ask for the bar; recommend the first run's recall@5 rounded down to the nearest 0.05, so later changes cannot quietly lose recall.
- [ ] Set `RECALL_AT_5_BAR` with a comment (date, first-run value). Record first-run numbers and the bar in PROJECT.md §8 and BOOKS.md. Commit this before any tuning change.
- [ ] If the bar is above the first run, tuning is new work: stop and ask the user before changing anything (`candidates`, `rrf_k`, `MAX_TOKENS`, `MIN_WORDS`), and add tasks with a Deviation line. Otherwise, `python -m evals.retrieval --save s4` as the final run: bar met (A5).
- [ ] Full suite: `.venv/bin/pytest`, expect all pass; record the count and time in PROJECT.md §4 Scripts row. PROJECT.md: §4 vector search row 🟢 with counts, Eval guidance row (used), §8 entry with recall@5, MRR and the bar.
Done when: the bar is committed before any tuning, the final run meets it, PROJECT.md holds the numbers.
Commit: `Record first retrieval run and the recall@5 bar`

## Critical behaviour and its tests
| Behaviour | Test | Task |
|---|---|---|
| A failed Docling conversion is never loaded as an empty book | `tests/test_books.py::test_check_result_raises_on_failed_document`, `::test_check_result_raises_on_no_chunks` | 1 |
| Tables never reach `kb`; prose around them is kept | `tests/test_books.py::test_strip_tables_keeps_prose`, `::test_chunk_rows_drops_table_only_chunk` | 1 |
| Skipped pages (contents, index) stay out | `tests/test_books.py::test_chunk_rows_skip_pages` | 1 |
| Chunks are sized with the bge-m3 tokenizer, and every stored embedding has 1024 dims | `tests/test_books.py::test_parse_embedding_rejects_wrong_dims`, `::test_docling_form_sets_bge_m3_tokenizer` | 1 |
| Upserting a book's source keeps its id (ingredient rows point at Palmer) | `tests/test_books.py::test_upsert_source_keeps_id` | 2 |
| Re-ingesting one book replaces only its chunks, with no duplicates | `tests/test_books.py::test_replace_chunks_only_touches_its_book`, `::test_replace_chunks_twice_same_rows` | 2 |
| Retrieval fuses vector and full-text ranks and returns k cited chunks | `tests/test_kb_search.py` (4 tests) | 3 |
| recall@5 and MRR are computed correctly | `tests/test_retrieval_eval.py::test_recall_at_5`, `::test_reciprocal_rank`, `::test_is_hit_wrong_book` | 7 |
| Every expected passage in the test set exists in `kb` | `tests/test_retrieval_eval.py::test_every_quote_resolves` | 8 |

## Approved exceptions

## Deviations
- 2026-10-16 · Tasks 5, 6, 6b, 8: books renamed and moved out of `books/pending/` (paths in the
  tasks); Task 6b adds *Malt* and section IV of the BJCP exam study guide; the question set is
  ≥ 40, ≥ 8 per book, 9 passages picked per book — brief R5/A1/A4 changed with the user's go-ahead
  ([SOURCES.md](../../SOURCES.md)).
