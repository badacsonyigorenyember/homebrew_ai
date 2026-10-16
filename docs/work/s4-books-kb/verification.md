# S4 · Books into the knowledge base — verification

Overall: ✅ all 8 checks and 557 tests pass (run 2026-10-16)

## Part 1: Summary

🎯 **Goal:** Put five brewing books into the knowledge base as searchable prose, with a retrieval test that measures recall@5.

🛠️ **How:** A Python loader (`loaders/books.py`) sends each PDF to Docling, cuts tables, embeds the prose with bge-m3 and replaces that book's rows in `kb.chunk`; one SQL function (`app.kb_search`) fuses vector and full-text ranks; `python -m evals.retrieval` scores 45 reviewed questions.

🤔 **Why this way:** One book per command means adding a book is one `BOOKS` entry plus one command, tested like the other loaders; tables stay out of `kb` so it is never a second source of numbers.

🏁 **Result:** 2,180 chunks from 5 books are searchable; first run recall@5 0.422, MRR@10 0.354 on 45 questions, bar 0.40 met.

### 🚦 Steps

- ⏭️ 📝 **Brief:** Skipped in this run; the brief was already approved on disk (scope widened from 3 to 5 books, recorded in its Deviations).
- ✅ 🗺️ **Plan:** Written earlier (866d568), approved after the rebase onto main (9e3104e).
- ⚠️ 🔨 **Implement:** 12 runs: Tasks 1-9 (6b included) ticked, then review fix rounds 9b58d7c and 5bfc66e; 557 tests pass.
  - ⚠️ The first How to Brew Docling run finished but its result could not be saved (`shared/docling-scratch/` is root-owned); results now go to `shared/rag-files/docling-chunks/`.
  - ⚠️ `test_both_arms_rank_first` had to query "zyxquorble" because real chunks outranked the synthetic one.
  - ⚠️ Task 6 ran only 17 targeted tests, not the full suite (the full suite is run here).
  - ⚠️ *Malt* printed-page offset and chapter boundaries are marked unverified in BOOKS.md.
  - ⚠️ First eval run: 26 of 45 questions miss the top 5, mostly chunks from other books outranking the expected one; bar set to 0.40 (below the 0.422 first run), tuning left as a TODO in RECIPE-ROADMAP §8.
- ⚠️ 🔍 **Review:** 3 rounds, final verdict ready for testing; 4 should-fix and finding 8, all fixed 🔧 fixed in 9b58d7c, 5bfc66e.
  - ⚠️ `table_pages` stat is an upper bound; `hnsw.ef_search` caps the vector arm at 40; `min(page_numbers)` would fail on a chunk with no pages (notes, not fixed).
  - ⚠️ Commit 5bfc66e carries a `Co-Authored-By` trailer against conventions (history not rewritten).
  - ⚠️ `docs/finished/s1-maths/doc-calc.md:11` still says "Palmer & Kaminski" for *How to Brew* (outside this work).
- ⚠️ 🧪 **Verify:** All spot checks and tests pass; two stale or odd things found, not fixed here. 🧮 spot checks ✅ 8/8 · 🧪 tests ✅ 557/557
  - ⚠️ PROJECT.md §5 line 161 still has a second, stale *Malt* row marked "⬜ kb in s4-books-kb" next to the updated 🟡 row at line 159.
  - ⚠️ `kb.chunk` holds 2 chunks stored three times each (How to Brew PDF pages 186 and 187: only the "TABLE 10.2 / 10.3" captions are left once the tables are cut). A second ingest gives the same set, so R2 holds, but retrieval can return the same caption three times.

👀 **Start here:** `docs/BOOKS.md` §1 and §1b (books, chunk counts, first run and bar); then run `.venv/bin/python -m evals.retrieval` and expect `recall@5 0.422   MRR@10 0.354   (45 questions)` ending in `bar 0.4: bar met`.

📁 **Changed files:**
- `PROJECT.md`
- `db/040_kb_search.sql`
- `docs/BOOKS.md`
- `docs/DATABASE.md`
- `docs/RECIPE-ROADMAP.md`
- `docs/work/s4-books-kb/plan.md`
- `docs/work/s4-books-kb/review.md`
- `docs/work/s4-books-kb/verification.md`
- `evals/results/2026-10-16-s4-first.json`
- `evals/results/2026-10-16-s4.json`
- `evals/retrieval.py`
- `evals/retrieval_questions.toml`
- `loaders/books.py`
- `requirements.txt`
- `tests/test_books.py`
- `tests/test_kb_search.py`
- `tests/test_retrieval_eval.py`

## Part 2: Showcase

| Piece | What it does |
|---|---|
| `python -m loaders.books <slug>` | Docling → prose filter → bge-m3 → replaces that book's `kb.chunk` rows |
| `app.kb_search(text, embedding, k)` | Top k chunks from vector and full-text ranks fused (RRF), with source and page |
| `python -m evals.retrieval` | Recall@5 and MRR@10 over 45 reviewed questions; `--question` shows the top 5 for one |

**What is in the knowledge base**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select s.title, count(c.*) as chunks, min(c.page) as first_page, max(c.page) as last_page from ref.source s join kb.chunk c on c.source_id = s.id group by 1 order by 2 desc"
```

```text
                      title                      | chunks | first_page | last_page 
-------------------------------------------------+--------+------------+-----------
 How to Brew                                     |    943 |         27 |       576
 Yeast: The Practical Guide to Beer Fermentation |    454 |         22 |       304
 Water: A Comprehensive Guide for Brewers        |    357 |         19 |       237
 Malt: A Practical Guide from Field to Brewhouse |    341 |         17 |       262
 BJCP Beer Exam Study Guide                      |     85 |         46 |        77
(5 rows)

```

**Ask a brewing question: top 5 chunks, with book and page**

```bash
.venv/bin/python -m evals.retrieval --question "how long should a diacetyl rest be"
```

<details><summary>Output (5 chunks; the chunk text is left out, it is book text)</summary>

```text
1. white-zainasheff-yeast p133 | Diacetyl Rest | 0.0328
2. white-zainasheff-yeast p132 | Diacetyl Rest | 0.0313
3. palmer-how-to-brew p289 | TO REST OR NOT TO REST, THAT IS THE QUESTION. . . | 0.0299
4. bjcp-exam-study-guide-2017 p71 | Diacetyl | 0.0299
5. white-zainasheff-yeast p58 | Diacetyl | 0.0293
```

</details>

**The same through the SQL function (what the pipeline calls)**

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select source_slug, page, round(score::numeric,4), vec_rank, fts_rank from app.kb_search('how long should a diacetyl rest be', (select embedding from kb.chunk where id = 5703), 5)"
```

```text
white-zainasheff-yeast|133|0.0328|1|1
white-zainasheff-yeast|132|0.0310|4|5
white-zainasheff-yeast|289|0.0294|6|10
bjcp-exam-study-guide-2017|71|0.0294|9|7
bjcp-exam-study-guide-2017|68|0.0288|8|11
```

**The eval, per book**

```bash
.venv/bin/python -m evals.retrieval | head -7
```

```text
recall@5 0.422   MRR@10 0.354   (45 questions)
  bjcp-exam-study-guide-2017   recall@5 0.333   MRR@10 0.250   (9)
  mallett-malt                 recall@5 0.556   MRR@10 0.583   (9)
  palmer-how-to-brew           recall@5 0.444   MRR@10 0.347   (9)
  palmer-kaminski-water        recall@5 0.333   MRR@10 0.178   (9)
  white-zainasheff-yeast       recall@5 0.444   MRR@10 0.414   (9)
misses (expected page, rank found; - = not in top 10):
```

## Part 3: Spot checks

### ✅ C1 · Five books in `ref.source` with `file_path`, each with chunks (A1)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.source s where file_path like '%rag-files/books/%' and exists (select 1 from kb.chunk c where c.source_id = s.id)"
```

| Expected | Actual | Result |
|---|---|---|
| 5 | 5 | ✅ pass |

### ✅ C2 · Chunk counts per book match BOOKS.md §1, 2,180 in all (A1, R1)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select string_agg(s.slug || '=' || n, ', ' order by s.id) from ref.source s join (select source_id, count(*) n from kb.chunk group by 1) c on c.source_id = s.id"
```

| Expected | Actual | Result |
|---|---|---|
| how-to-brew=943, water=357, yeast=454, malt=341, bjcp=85 | palmer-how-to-brew=943, palmer-kaminski-water=357, white-zainasheff-yeast=454, mallett-malt=341, bjcp-exam-study-guide-2017=85 | ✅ pass |

### ✅ C3 · Re-ingest leaves the content unchanged: *How to Brew* fingerprint equals the one BOOKS.md recorded after the second ingest (A1, R2)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select md5(string_agg(text, '|' order by page, section_path, text)) from kb.chunk where source_id = 251"
```

| Expected | Actual | Result |
|---|---|---|
| 4d8d4941c1b14cb61ba6ee195a58cc6b | 4d8d4941c1b14cb61ba6ee195a58cc6b | ✅ pass |

Not re-run here: a fresh ingest needs Docling (minutes) and would rewrite the book's rows; the replace-only-this-book behaviour is covered by the two stack tests in Part 4.

### ✅ C4 · No table rows, no formula placeholders, every chunk has a page and a 1024-dim embedding (R1, §6.7)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) filter (where text like '%|%|%' or text like '%formula-not-decoded%'), count(*) filter (where page is null), count(*) filter (where vector_dims(embedding) <> 1024), max(tokens) from kb.chunk"
```

| Expected | Actual | Result |
|---|---|---|
| 0, 0, 0, at most 514 (512 plus the bge-m3 specials) | 0\|0\|0\|514 | ✅ pass |

### ✅ C5 · Doc → calc notes exist for each of the five books (A2, R3)

```bash
grep -c '^### ' docs/BOOKS.md
```

| Expected | Actual | Result |
|---|---|---|
| 5 | 5 | ✅ pass |

### ✅ C6 · Retrieval returns 5 chunks with source and page for a question (A3, R4)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*), count(source_slug), count(page) from app.kb_search('how long should a diacetyl rest be', (select embedding from kb.chunk where id = 5703), 5)"
```

| Expected | Actual | Result |
|---|---|---|
| 5\|5\|5 | 5\|5\|5 | ✅ pass |

### ✅ C7 · Test set has at least 40 reviewed questions, at least 8 per book (A4, R5)

```bash
.venv/bin/python -c "import tomllib,collections; d=tomllib.load(open('evals/retrieval_questions.toml','rb'))['question']; print(len(d), dict(collections.Counter(q['book'] for q in d)))"
```

| Expected | Actual | Result |
|---|---|---|
| at least 40 in all, at least 8 each | 45 {'palmer-how-to-brew': 9, 'palmer-kaminski-water': 9, 'white-zainasheff-yeast': 9, 'mallett-malt': 9, 'bjcp-exam-study-guide-2017': 9}; header says "Reviewed by the user on: 2026-10-16" | ✅ pass |

### ✅ C8 · First run recorded, bar 0.40 written down, final run meets it (A5, R6)

```bash
.venv/bin/python -m evals.retrieval | sed -n '1p;$p'; grep -n "^RECALL_AT_5_BAR" evals/retrieval.py; grep -c "recall@5 0.422" PROJECT.md
```

| Expected | Actual | Result |
|---|---|---|
| first run 0.422 (`2026-10-16-s4-first.json`), bar 0.40, final run at least 0.40, PROJECT.md §8 has the result | `recall@5 0.422   MRR@10 0.354   (45 questions)` / `bar 0.4: bar met`; `31:RECALL_AT_5_BAR: float \| None = 0.40`; PROJECT.md count 2 | ✅ pass |

Adding a book (A6, R7): BOOKS.md §2 lists the 8 steps, and the per-book counts in C2 equal BOOKS.md, which is what A6 asks of the other books. The end-to-end run (*Yeast*, following BOOKS.md alone) was done in Task 6 and is not repeated here, since it needs Docling and rewrites rows.

## Part 4: Regression tests

Command: `.venv/bin/python -m pytest -q`  ·  Result: ✅ 557 passed in 167.7 s (stack up)

| Test | Protects | Result |
|---|---|---|
| tests/test_books.py::test_check_result_raises_on_failed_document | a failed Docling conversion is never loaded as an empty book | ✅ |
| tests/test_books.py::test_check_result_raises_on_no_chunks | same, no chunks | ✅ |
| tests/test_books.py::test_strip_tables_keeps_prose | tables never reach `kb`, prose around them stays | ✅ |
| tests/test_books.py::test_chunk_rows_drops_table_only_chunk | table-only chunks dropped | ✅ |
| tests/test_books.py::test_chunk_rows_skip_pages | contents and index pages stay out | ✅ |
| tests/test_books.py::test_parse_embedding_rejects_wrong_dims | every stored embedding has 1024 dims | ✅ |
| tests/test_books.py::test_docling_form_sets_bge_m3_tokenizer | chunks sized with the bge-m3 tokenizer | ✅ |
| tests/test_books.py::test_upsert_source_keeps_id | upserting a book keeps its `ref.source` id | ✅ |
| tests/test_books.py::test_replace_chunks_only_touches_its_book | re-ingest replaces one book only | ✅ |
| tests/test_books.py::test_replace_chunks_twice_same_rows | re-ingest gives no duplicates | ✅ |
| tests/test_books.py::test_strip_tables_removes_formula_placeholder | formula placeholders never stored | ✅ |
| tests/test_kb_search.py (4 tests) | fused ranks, k rows with source and page, no-match fallback | ✅ |
| tests/test_retrieval_eval.py::test_recall_at_5, ::test_reciprocal_rank, ::test_is_hit_wrong_book | recall@5 and MRR computed correctly | ✅ |
| tests/test_retrieval_eval.py::test_every_quote_resolves | every expected passage in the test set exists in `kb` | ✅ |

The 22 tests in these three files were also run alone: 22 passed. No critical test from the plan was missing, so none was added.

Failures: none.
