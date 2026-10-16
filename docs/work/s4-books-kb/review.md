# Review: s4-books-kb

Diff: main...s4-books-kb at 80c9435  ·  Verdict: ready for testing

Checked: every plan task against the code and commits; brief R1–R7 and A1–A6; scope; `loaders/books.py`,
`db/040_kb_search.sql`, `evals/retrieval.py` and their tests; the DB as it stands (`kb_search` owned
by `postgres`; 943 / 357 / 454 / 341 / 85 chunks, 0 table-like rows, no null page, section or
tokens); `plainto_tsquery` → OR rewrite on a hyphenated question; the two result files (same
summary, `bar` null in the first and 0.4 in the final); no book text committed apart from the
short quotes (`shared/rag-files/**` is gitignored, results hold ids, pages and scores only); commit
subjects are one line each, ≤ 60 characters. `pytest` on the three new test files: 22 passed, stack
tests included.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | docs/BOOKS.md:156, plan Task 4 | The plan says each *How to Brew* table and formula page is marked with the pass that covered it (`s1-maths` section) or "not passed yet". The chapter table lists the pages, but they are not marked, and the text says the mapping "has not been mapped page by page (unverified)". The plan has no Deviation line for this. | R3/A2 is only partly met for *How to Brew*: a reader can't tell which cut pages `s1-maths` already covers. Either do the mapping or record a Deviation. |
| 2 | should-fix | docs/DATABASE.md:300, :471 | §4 still says "Measured 2026-10-16: *How to Brew* 943 chunks", and §7 row 7 says "the other four books follow". All five books are loaded (2,180 chunks). | DATABASE.md states the wrong `kb` contents. CLAUDE.md asks for measured facts. |
| 3 | should-fix | PROJECT.md:124 | Plan Tasks 4 and 9 put `loaders/books.py`, its tests and the eval in the §4 Scripts row. The row has the new test count (557, 168 s), but it doesn't mention `loaders/books.py`, `evals/retrieval.py` or `tests/test_books.py` / `test_kb_search.py` / `test_retrieval_eval.py`. | PROJECT.md is the entry point. The new loader and eval can't be found from the Scripts row, where every other loader is listed. |
| 4 | should-fix | docs/BOOKS.md:13 | *How to Brew* is listed as by "Palmer & Kaminski". It is John Palmer's book (PROJECT.md §5 says so). | Wrong attribution in the citation docs. `ref.source` has no author column, so no data is affected. |
| 5 | note | loaders/books.py:178 | `table_pages` gets every page of a chunk whose text changed in `strip_tables`. That includes all pages of a chunk that spans several pages, and a change from blank-line collapsing alone. | The table-page lists in BOOKS.md §3 are upper bounds, not exact pages. That is safe for R3 (nothing is under-reported). |
| 6 | note | db/040_kb_search.sql:24 | When the HNSW index serves the vector arm, it returns at most `hnsw.ef_search` rows (default 40, iterative scan off). `candidates` > 40 then adds no vector candidates unless `ef_search` is raised in the same session. | Matters for the tuning TODO (RECIPE-ROADMAP §8 Later), which names `candidates`. No effect at the default 40. |
| 7 | note | loaders/books.py:177 | `min(c["page_numbers"])` raises on a chunk with no page numbers. A chunk is skipped by its first page only. | Neither happened on the five books (all ingests completed). The first-page rule is documented in BOOKS.md §2 step 5. |

## Fix of findings 1–4

| # | Earlier finding | Status |
|---|---|---|
| 1 | *How to Brew* cut pages not mapped to a pass | Resolved. The table and formula page lists in BOOKS.md §3 now carry `(s1 §n)` or `(adjuncts)` on every page the cited `s1-maths` and `adjunct-fermentables` pages cover; unmarked pages are "not passed yet", with m7-process as owner for the water, pH, mash and process chapters. |
| 2 | DATABASE.md §4 and §7 stale | Resolved. Both say all five books, 2,180 chunks (counts per book re-measured from `kb.chunk`: 943 / 357 / 454 / 341 / 85). |
| 3 | PROJECT.md Scripts row lacked the loader and eval | Resolved. The row names `loaders/books.py`, `evals/retrieval.py`, and the three test files. |
| 4 | Wrong author for *How to Brew* | Resolved. BOOKS.md §1 says Palmer. |
| 6 | note: `ef_search` caps the vector arm | Added to the retrieval-tuning TODO in RECIPE-ROADMAP §8 Later. |
