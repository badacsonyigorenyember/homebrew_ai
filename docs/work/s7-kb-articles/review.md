# Review: s7-kb-articles

Diff: main...s7-kb-articles at 6c1b163  ·  Verdict: ready for testing

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | tests/test_kb_search.py:90 | Task 3 said `test_returns_source_url` checks that **every** row carries the throwaway URL; the test checks only the throwaway source's rows (`mine`). The change is right (real article rows carry their own URL, book rows null), but plan.md has no Deviation line for it. | Conventions: any difference from the plan is recorded under Deviations. Only the record is missing; the test still fails if `source_url` is not returned. |
| 2 | should-fix | PROJECT.md:238 (§8) | §8 has dated entries for Tasks 1, 2, 4, 5, 7 and 8, but none for Task 3 (`db/040_kb_search.sql` changed to drop + create, applied to the running DB as `postgres`) or Task 6 (eval reports books and articles apart, `cite()`). Their effects are mentioned in §4 and in the Task 8 entry only in passing. | CLAUDE.md: a dated §8 entry every time something is implemented. The applied DB change is the one most worth having in the log. |
| 3 | note | tests/test_books.py:142 | `test_article_urls_match_source_lines` passes with no assertion when a file is missing, where the plan said to skip it. All ten files are present here, so it ran and checked every URL. | A checkout without `shared/rag-files/` shows a pass, not a skip. Harmless now. |
| 4 | note | tests/test_books.py:107 | A1 is covered by two tests together: `test_clean_markdown_drops_header_and_markers` (header lines, `[n]` markers) and `test_markdown_rows` (page null, heading path, left-out sections, on synthetic chunks). No single test runs one document through both steps. | Coverage of A1 is complete across the pair; the real-data side is backed by the Task 4 SQL leak checks (re-run below: 0 rows). |
| 5 | note | tests/test_kb_search.py:74 | `test_returns_k_rows_with_source_and_page` now checks `page` on its own rows only, which always have pages. Deviation recorded (Task 8). | The test now mainly guards that `k` rows come back and the `page` column is returned; it no longer checks real rows. Accepted in the plan. |
| 6 | note | loaders/books.py:105 | Troester's mash-parameters URL (the braukaiser.com wiki page) returned HTTP 500 on 2026-10-16 and is stored unverified; this is stated in BOOKS.md §1c and PROJECT.md §8 Task 1. User chose "Wiki page". | Citation may point to a page that does not resolve; already disclosed. |

## What was checked

- **Plan:** all 8 tasks done as written apart from finding 1. Edition strings: Troester PDF
  `2008` matches the PDF's byline, Terrill `2017-04-21` its credit line, TQ `vol. 58, no. 1, 2021`;
  the other saved pages give no publication date (the only date in the Janish hot-side page is a
  quoted tweet), so `saved 2026-10-16` follows the plan's rule.
- **Brief:** R1–R6 and A1–A6 met. Re-queried the DB (as `postgres`, read only):
  - A2: 12 article sources, each with a URL and chunks (258 in all: 42, 78, 18, 27, 9, 14, 17, 11,
    7, 4, 26, 5); books unchanged at 943 / 357 / 454 / 341 / 85 = 2,180, URL null.
  - `page` is null for all 205 Markdown chunks and set for all 53 PDF chunks.
  - Header-line, `[n]`-marker and left-out-section checks over all article chunks: 0 rows.
  - `app.kb_search`: owner `postgres`, ACL null, result columns include `source_url` after
    `source_title`. `db/040_kb_search.sql` keeps "Idempotent: safe to re-run" and is safe to
    re-run (drop if exists + create).
  - Troester PDF: chunks on pp. 1–20; the conclusion chunk spans pp. 20–21 (stored as 20), so the
    conclusion is kept; p. 21 "Tables" (2 words), p. 22 and the p. 23 "Sources" list are out.
  - A6: saved result shows books 0.422 / 0.345 (bar met), articles 0.867 / 0.608, no bar line for
    articles; recorded in BOOKS.md §1d and PROJECT.md §4/§8.
- **Scope:** every changed path is in the plan's Files table; q01–q45 untouched (TOML diff is the
  header comment plus q46–q60 appended).
- **Correctness:** `clean_markdown` drops lines 2 through the `Saved` line and raises when the block
  is missing; `chunk_rows` raises for a page-less PDF chunk, skips the page check for Markdown, drops
  by exact heading match ignoring case; `upsert_source` never wipes a URL; `summarise` judges the
  bar on the books group only and `mean([])` is 0.0; `cite` falls back to title and URL only for a
  page-less chunk.
- **Readability:** the Markdown path is a few branches in the same loader and entries are plain
  `Book` literals; nothing table-driven.
- **Tests:** each critical behaviour in the plan's table has its test and would fail if the
  behaviour broke (subject to findings 3 and 5).
- **Safety:** no secrets; the DB change is a `.sql` file; the results JSON holds no chunk text;
  quotes are 4–12 words (enforced by `test_question_set_shape`).
- **Records:** commits are one line each with no body; PROJECT.md §4, §5 and §8 updated, apart
  from finding 2.
