# S7 · Web articles and short papers into the knowledge base — implementation plan

Stage: shipped
Brief: [brief.md](brief.md)
Branch: s7-kb-articles

## Approach
The s4 loader, `loaders/books.py`, gets a small Markdown branch, not a second loader (§6.8). The
`Book` entry gains two optional fields, `url` and `drop_sections`, and a second dict, `ARTICLES`,
holds the 12 sources. The command stays `python -m loaders.books <slug>` for any slug in
`BOOKS` or `ARTICLES`. The dataclass keeps the name `Book`; renaming it is outside the brief.

A Markdown file is cleaned **before** Docling by one pure function, `clean_markdown`. It drops the
saved-page header (the lines from `Source:` to `Saved …`) and the `[n]` reference markers.
Docling's chunker then runs with the s4 settings and `convert_from_formats=md`. Left-out sections
are dropped **after** Docling, by heading: a chunk is dropped when any heading in its path matches
one of the entry's `drop_sections`, ignoring case. The same rule works for the PDFs, so the TQ
paper's `REFERENCES` section goes the same way. A Markdown chunk has no page (`page` null). A PDF
chunk with no page still fails.

*Measured 2026-10-16 against the running Docling Serve:*
- A test Markdown file with the full s4 form gave status success. The heading path held every
  ancestor (`Doc Title > Part One > See Also > External Resources`) and `page_numbers` was `[]`.
  The header lines came back as their own text, the `[2]` marker stayed in the text, and an HTML
  comment line was dropped by Docling.
- The TQ PDF gave 33 chunks. Page 1 is the MBAA cover, and the last three chunks, on page 8, have
  the heading path `['REFERENCES']`. Page 8 also holds the paper's key findings and best
  practices, so a page skip would lose prose there.

`app.kb_search` gains a `source_url` column. The return type changes, so `db/040_kb_search.sql`
drops the function and creates it again; it is edited in place, as the other `db/` files are. The
eval splits its summary into books (s4's 45 questions, with the 0.40 bar) and articles (reported
only). An expected passage from a Markdown source has a quote and no page.

## Files
| Path | New / changed | Purpose |
|---|---|---|
| `loaders/books.py` | changed | `url`, `drop_sections` on `Book`; `ARTICLES` (12 entries); `clean_markdown`; Markdown branch in `docling_form`, `run_docling`, `chunk_rows`; `url` in `upsert_source`; CLI over books and articles |
| `tests/test_books.py` | changed | unit tests for the Markdown path and the section drop; stack test for the URL upsert |
| `db/040_kb_search.sql` | changed | `app.kb_search` also returns `source_url` |
| `tests/test_kb_search.py` | changed | the URL comes back |
| `evals/retrieval.py` | changed | books and articles reported separately, bar on books only; page-less expects; `--question` shows title and URL for a chunk with no page |
| `evals/retrieval_questions.toml` | changed | 15 reviewed article questions appended (q46–q60); s4's 45 untouched |
| `tests/test_retrieval_eval.py` | changed | group summary, cite, question-set shape for articles |
| `evals/results/<date>-s7.json` | new | the final eval run |
| `docs/BOOKS.md` | changed | articles in `kb`, how to add an article, the s7 eval numbers |
| `docs/DATABASE.md` | changed | §4: Markdown sources have no page; `kb_search` returns the URL; article chunk counts |
| `PROJECT.md` | changed | §4 vector search, Scripts and Eval guidance rows, §5 articles row, §8 entries |

## Tasks

### Task 1: The loader takes a Markdown source and drops named sections
Why: R1, R2 (entries), R3, A1. This is the pure part, tested without the stack.
- [x] `loaders/books.py`, `Book`: add `url: str | None = None` and
      `drop_sections: tuple[str, ...] = ()`, which holds the heading texts whose chunks are left
      out (matched case-insensitively anywhere in the chunk's heading path). Update the module
      docstring: books **and articles**, and adding an article is one `ARTICLES` entry plus the
      same command (see docs/BOOKS.md).
- [x] Add `ARTICLES: dict[str, Book]` with the 12 entries below and
      `SOURCES = BOOKS | ARTICLES`. All files are under `shared/rag-files/`.
      - **title**: the page's `#` title line, or the title printed on the PDF.
      - **edition**: the date the page or PDF gives (read it from the file), else
        `saved 2026-10-16`.
      - **publisher**: the site or journal.
      - **licence**: as in the table; every licence ends `; local use only`.
      - **notes**: `Article prose in kb.chunk (s7-kb-articles)`.

      | Slug | File | URL | Licence | `drop_sections` / `skip_pages` |
      |---|---|---|---|---|
      | `troester-mash-parameters` | `articles/braukaiser_mash_parameters_2009.pdf` | `https://braukaiser.com/wiki/index.php/Effects_of_mash_parameters_on_fermentability_and_efficiency_in_single_infusion_mashing` | `CC BY-NC 3.0, Kai Troester, braukaiser.com` | `skip_pages=((22, 23),)`: appendix tables and the "Sources" list (pdftotext, 2026-10-16) |
      | `troester-mash-time-fermentability` | `articles/braukaiser_mash_time_fermentability.md` | its `Source:` line | `© Kai Troester, braukaiser.com; licence not stated` | – |
      | `terrill-observations-on-attenuations` | `articles/terrill_observations_on_attenuations.md` | its `Source:` line | `© Sean Terrill, seanterrill.com; licence not stated` | – |
      | `janish-dry-hop-best-practices-tq` | `articles/janish_dry_hop_best_practices_tq_2021.pdf` | `https://doi.org/10.1094/TQ-58-1-0402-01` | `© MBAA; posted by the author with MBAA's permission` | `skip_pages=((1, 1),)` (MBAA cover), `drop_sections=("References",)` |
      | `janish-short-cool-dry-hopping` | `articles/janish_short_cool_dry_hopping.md` | its `Source:` line | `© Scott Janish, scottjanish.com; licence not stated` | `("Footnotes",)` |
      | `janish-survivables-hot-side` | `articles/janish_survivables_hot_side.md` | its `Source:` line | as above | `("Footnotes",)` |
      | `janish-ph-hoppy-beers` | `articles/janish_ph_hoppy_beers.md` | its `Source:` line | as above | `("Footnotes",)` |
      | `janish-coffee-beers` | `articles/janish_coffee_beers.md` | its `Source:` line | as above | – |
      | `mtf-berliner-weissbier` | `articles/mtf_berliner_weissbier.md` | its `Source:` line | `Milk The Funk Wiki; licence not stated on the page` | `("External History Resources", "Video Presentations", "See Also", "References")` |
      | `mtf-lactobacillus-fermentation` | `articles/mtf_lactobacillus_fermentation.md` | its `Source:` line | as above | `("See Also", "References")` |
      | `brunwater-water-knowledge` | `water/brunwater_water_knowledge.md` | its `Source:` line | `© Martin Brungard, all rights reserved` | `("5. References",)` |
      | `bjcp-2021-introductions` | `styles/bjcp_2021_introductions.md` | `https://styles.bjcp.org/bjcp-2021-beer/` | `© Beer Judge Certification Program` | – |

      The slug `bjcp-2021` is taken by the style guidelines, so this one is
      `bjcp-2021-introductions`.

      The Troester URL was found on 2026-10-16 by searching the braukaiser.com wiki. The search
      snippet matches the PDF's first paragraph, and the page was last edited on 25 February 2009.
      A direct fetch of the page returned HTTP 500 that day. Fetch it once more; if it still fails,
      keep the URL and note in BOOKS.md that it was not reachable on that date.
- [x] `clean_markdown(text: str) -> str`. Keep line 1, the `# ` title. Drop the lines from
      line 2 through the first line that starts with `Saved `. Raise `ValueError` if that block
      has no `Source:` line or no `Saved ` line within the first 10 lines, because a file saved
      another way must not leak its header into `kb`. Then remove the reference markers with
      `re.sub(r" ?\[\d+\]", "", text)`. Measured 2026-10-16: only the two Milk The Funk files
      have such markers (26 and 7), and no file has Markdown links.
- [x] `docling_form`: set `convert_from_formats` to `"md"` for a `.md` file, else `"pdf"`; keep
      the other fields (the full form with `md` was measured to work).
      `run_docling`: for `.md`, upload `clean_markdown(file text).encode()` as `(name, bytes,
      "text/markdown")`; for PDFs, change nothing.
- [x] `chunk_rows`:
  - `page = min(page_numbers)` when the list is not empty. When it is empty: `None` for a `.md`
    source, and `ValueError` for a PDF source.
  - Apply the skip-page check only when `page` is not `None`.
  - Drop a chunk whose heading path has a `drop_sections` entry (case-insensitive), counting it in
    `stats["dropped_section"]`.
  - Add `stats["table_chunks"]`, the number of chunks that had a table or formula cut.
  - `main`: `choices=sorted(SOURCES)`, and print the two new counts.
- [x] Tests in `tests/test_books.py`, all unit:
  - `test_clean_markdown_drops_header_and_markers`: a small inline document (header block,
    `[2]` marker, sections) keeps its title, and loses the `Source:`, credit and `Saved` lines and
    the marker.
  - `test_clean_markdown_requires_header`: no `Source:` or `Saved` line raises `ValueError`.
  - `test_markdown_rows` (A1): the cleaned document's synthetic Docling chunks are shaped like
    the measured output (full heading path, `page_numbers: []`). Fed to `chunk_rows` with an
    article entry dropping `See Also` and `References`, the rows have `page` `None` and the path
    `Doc > Part One`; no row comes from `See Also > External Resources` or `References`; and
    `dropped_section == 2`.
  - `test_chunk_rows_drops_pdf_section_case_insensitive`: a PDF chunk under `['REFERENCES']`
    with `drop_sections=("References",)` is dropped, and its neighbour is kept.
  - `test_chunk_rows_pdf_without_page_raises`.
  - `test_docling_form_markdown`: `.md` gives `md`, `.pdf` gives `pdf`.
  - `test_sources_slugs_distinct`: no slug is in both `BOOKS` and `ARTICLES`, and every article
    has a `url`.
  - `test_article_urls_match_source_lines`: for each Markdown entry except
    `bjcp-2021-introductions`, the URL equals the file's `Source:` URL. Skip the test if the file
    is missing, since `shared/rag-files/` is gitignored.
- [x] Run `.venv/bin/pytest tests/test_books.py -m "not stack"`, expect all to pass.
Done when: the unit tests pass, and `python -m loaders.books --help` lists the 17 slugs.
Commit: `Load Markdown articles in the books loader`

### Task 2: Source upsert writes the URL
Why: R2.
- [x] `upsert_source`: insert `url` too, and on conflict set
      `url = coalesce(excluded.url, ref.source.url)`. The books have no URL in their entries and
      no URL in the database (measured), and a later entry without a URL must not wipe one.
- [x] Stack test `test_upsert_source_writes_url` (rolled back): a throwaway article with a URL
      gets it in `ref.source.url`; upserting it again without a URL keeps the URL.
- [x] Run `.venv/bin/pytest tests/test_books.py`, expect all to pass.
Done when: the tests pass.
Commit: `Write the source URL on upsert`

### Task 3: `app.kb_search` returns the source URL
Why: R4.
- [x] `db/040_kb_search.sql`: before `create`, add
      `drop function if exists app.kb_search(text, extensions.vector, integer, integer, integer);`
      with a comment saying it is needed because the return type changed (s7). Then make it
      `create function` (not `or replace`), add `source_url text` after `source_title` in
      `returns table`, and `s.url` in the final select. Keep the header line "Idempotent: safe to
      re-run".
      Checked 2026-10-16: no object depends on the function, its ACL is the default (null), and
      its owner is `postgres`. Only `evals/retrieval.py` and `tests/test_kb_search.py` call it;
      no n8n workflow does.
- [x] Apply: `docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/040_kb_search.sql`,
      twice (idempotent). Then check that `pg_proc` shows owner `postgres` and a null ACL.
- [x] `tests/test_kb_search.py`: give the throwaway `Book` in `load` the URL
      `https://example.test/kb`; add `test_returns_source_url` (every row of the throwaway source carries that URL; real book rows have no URL, so the other rows are not checked).
- [x] `docs/DATABASE.md` §4: the `kb_search` bullet names the returned columns, including
      `source_url`.
- [x] Run `.venv/bin/pytest tests/test_kb_search.py tests/test_retrieval_eval.py`, expect all to
      pass (the eval reads the columns by name).
Done when: the tests pass, and the function is applied and owned by `postgres`.
Commit: `Return the source URL from kb_search`

### Task 4: Ingest the ten Markdown sources and document adding an article
Why: R1, R2, R3, A2, A3.
- [x] Before the ingest, save the A2 counts:
      `select s.slug, count(*) from kb.chunk c join ref.source s on s.id = c.source_id group by 1`.
      Expect the five books at 943 / 357 / 454 / 341 / 85.
- [x] For each of the ten Markdown slugs, run `.venv/bin/python -m loaders.books <slug>`. Note
      the printed stats: chunks in, kept, dropped by section, dropped as too short, table chunks.
      Expect `dropped_section` > 0 for the six sources with `drop_sections`.
- [x] Check with SQL (run as `postgres`, OPERATIONS.md §4) that each of these returns 0 rows for
      the article slugs:
      - `text like '%Source: http%'` or `text ~ '^Saved 20'`
      - `text ~ ' ?\[[0-9]+\]'` for the `mtf-%` slugs
      - `section_path ~* '(footnotes|references|see also|external (history )?resources|video presentations)'`
      - `page is not null` for the Markdown slugs
      - the BOOKS.md §2 step 6 `table_like` column
      If one shows up, fix the cause in Task 1's code, with a Deviation line.
- [x] A3: re-run one article with `--reuse-docling` (`janish-ph-hoppy-beers`). Every other
      source's count is unchanged, and this source has the same fingerprint before and after
      (`md5(string_agg(text, '|' order by section_path, text))`).
- [x] `docs/BOOKS.md`:
  - Intro: say the file covers books and articles, and that a Markdown source has no page.
  - New §1c "Articles in `kb`": one row per source with slug, source, file, URL, left-out
    sections or pages, chunks (with token min / median / max), table chunks cut, and the ingest
    date, all measured.
  - New §2b "Adding an article": for Markdown, save the page with the header block (title,
    `Source:`, credit, `Saved` line), add one `ARTICLES` entry with `url` and `drop_sections`
    (look for reference, footnote and link sections with `grep -n '^#' FILE`), run the command,
    then run the §2 step 6 check and the SQL checks above. For a PDF, follow §2, adding `url`.
- [x] `docs/DATABASE.md` §4: article chunk counts, and `page` is null for a Markdown source.
Done when: the ten sources have chunks and URLs, the checks return no rows, and the books still
hold 2,180 chunks with the same per-book counts.
Commit: `Ingest the Markdown articles into kb`

### Task 5: Ingest the two PDF articles
Why: R1, R2, A2.
- [x] Run `.venv/bin/python -m loaders.books troester-mash-parameters` and
      `… janish-dry-hop-best-practices-tq`. Check the stats. The TQ paper should show 3 chunks
      dropped by section (measured) and its cover page skipped. For Troester, look at the saved
      JSON for pages 21–23: if prose was lost or the "Sources" list kept, change `skip_pages` (or
      use `drop_sections=("Sources",)`), re-run with `--reuse-docling`, and add a Deviation line.
- [x] Run the Task 4 SQL checks for these two slugs (the page check doesn't apply: every PDF
      chunk has a page), plus `text ~* 'doi:|J\. Am\. Soc\. Brew|Narziss, 2005'` → 0 rows.
- [x] Run the full A2 query
      `select s.slug, s.url, count(c.*) from ref.source s join kb.chunk c on c.source_id = s.id group by 1, 2`:
      12 article rows, each with a URL and chunks, and the books unchanged.
- [x] Add both to BOOKS.md §1c.
Done when: A2 holds for all 12 articles.
Commit: `Ingest the PDF articles into kb`

### Task 6: The eval reports books and articles separately, and cites page-less chunks
Why: R4, R6, A4.
- [x] `evals/retrieval.py`:
  - Docstring: books and articles.
  - Each row gets `group`: `"books"` if `q["book"] in books.BOOKS`, else `"articles"`.
  - `expect_pages` uses `e.get("page")`.
  - `summarise` returns the overall numbers, `groups: {"books": …, "articles": …}`,
    `per_book` (per source), `bar`, and `bar_met`, computed on the **books** group only.
  - `print_report` prints a books line followed by the bar line, then an articles line with no
    bar line, then per source, then the misses (`p<page>` or `md` when there is no page).
  - New `cite(result) -> str`: `"<slug> p<page>"` when the result has a page, else
    `"<slug> | <title> | <url>"`. `show_question` uses it.
  - The bar constant and its comment stay as they are.
- [x] Unit tests in `tests/test_retrieval_eval.py`:
  - `test_summarise_bar_on_books_only`: books rows at recall 0.5 and article rows at 0.0 give
    `bar_met` true, with the articles reported at 0.0.
  - `test_summarise_bar_not_met`: books at 0.3 give `bar_met` false, even with articles at 1.0.
  - `test_cite_without_page`: shows the title and URL.
  - `test_cite_with_page`.
- [x] Run `.venv/bin/pytest tests/test_retrieval_eval.py`, expect all to pass. Run
      `.venv/bin/python -m evals.retrieval --question "how long and how cold should I dry hop a hazy IPA"`.
      At least one article hit must show its title and URL (A4); if none does, try a question
      worded from a Janish heading. Keep the output for the Task 8 record.
Done when: the tests pass and A4 is shown.
Commit: `Report books and articles apart in the retrieval eval`

### Task 7: Article questions, reviewed by the user
Why: R5, A5.
**Needs from the user:** a review of every new question (blocking; ask with the passages shown).
- [x] Pick the passages **before** running any retrieval for them. Take one chunk per source,
      plus a second for the three longest (Bru'n Water ~17,500 words, BJCP introductions ~8,800
      words, Troester PDF 23 pp): 15 in all. Spread them in chunk order and skip chunks with no
      answerable brewing fact. Write each question as a brewer would ask it, as in s4 Task 8.
      Each `expect` has a `quote` of 4–12 words copied exactly from the chunk. Add a `page` only
      for the two PDF sources; Markdown expects have no `page`.
- [x] Append the questions as `q46`…`q60` to `evals/retrieval_questions.toml`, in s4's format
      (`book` = the article slug). **Do not edit q01–q45.** Update the header comment: articles
      included, Markdown expects have no page, and a second "Reviewed by the user on:" line for
      the article questions.
- [x] `tests/test_retrieval_eval.py::test_question_set_shape`:
  - every `book` is in `BOOKS` or `ARTICLES`
  - ≥ 8 per book (unchanged), ≥ 1 per article, ≥ 12 article questions
  - an expect for a `.md` source has no `page`, and one for a PDF source has a `page`
  - quotes are 4–12 words
- [x] Show the user each new question with its source, page or section, and the full chunk text,
      from the DB, in the conversation (not in a committed file). Apply their edits and write the
      review date.
- [x] Run `.venv/bin/pytest tests/test_retrieval_eval.py`, expect all to pass, including the
      stack test `test_every_quote_resolves`. Run `git diff` on the TOML: only additions after
      q45 and the header change.
Done when: 15 reviewed article questions are in, and every quote resolves.
Commit: `Add reviewed article retrieval questions`

### Task 8: The eval run, the books bar, and the record
Why: R6, A6.
- [x] Run `.venv/bin/python -m evals.retrieval --save s7`. Read the books line: recall@5 on
      q01–q45 and the bar.
- [x] **If books recall@5 < 0.40: stop.** Don't change any retrieval setting, the bar, or any
      question. Commit the saved result and a PROJECT.md §8 line with the numbers. Add a
      Deviation line, then report `needs-input` with the books and articles numbers and the books
      misses that are new against `evals/results/2026-10-16-s4.json` (brief R6: tuning is its own
      work item).
- [x] If the bar is met, record:
  - BOOKS.md: a new §1d "Eval with articles (s7)" with books and articles recall@5 and MRR@10,
    per source, and the date.
  - PROJECT.md §4: the vector search row (article chunk counts, `source_url`), the Eval guidance
    row (s7 run), and the Scripts row (full `.venv/bin/pytest` count and time with the stack up,
    measured).
  - PROJECT.md §5: the articles row goes 🟡 (kb done, calc still in s5 and m7), with the chunk
    total.
  - PROJECT.md §8: a dated entry with books recall@5 / MRR@10 against the bar, the articles'
    numbers (no bar), and the chunk counts.
- [x] Run the full suite with `.venv/bin/pytest`, expect all to pass.
Done when: the books bar is met (or work stopped as above), and the numbers are in BOOKS.md and
PROJECT.md.
Commit: `Record the retrieval eval with articles`

## Critical behaviour and its tests
| Behaviour | Test | Task |
|---|---|---|
| A saved page's header lines and Milk The Funk's `[n]` markers never reach `kb` | `tests/test_books.py::test_clean_markdown_drops_header_and_markers` | 1 |
| A file saved without the expected header fails instead of leaking it | `tests/test_books.py::test_clean_markdown_requires_header` | 1 |
| Markdown rows have no page and a heading section path; left-out sections are dropped, child headings included | `tests/test_books.py::test_markdown_rows` | 1 |
| A reference section in a PDF is dropped by heading, whatever its case, and the prose beside it is kept | `tests/test_books.py::test_chunk_rows_drops_pdf_section_case_insensitive` | 1 |
| A PDF chunk without a page still fails (s4 behaviour kept) | `tests/test_books.py::test_chunk_rows_pdf_without_page_raises` | 1 |
| Markdown goes to Docling as Markdown | `tests/test_books.py::test_docling_form_markdown` | 1 |
| Each article is cited by the URL its saved page names | `tests/test_books.py::test_article_urls_match_source_lines`, `::test_sources_slugs_distinct` | 1 |
| Upsert writes the URL and never wipes one | `tests/test_books.py::test_upsert_source_writes_url` | 2 |
| Retrieval results carry the source URL | `tests/test_kb_search.py::test_returns_source_url` | 3 |
| Re-ingesting one source replaces only its chunks | `tests/test_books.py::test_replace_chunks_only_touches_its_book` (s4), A3 run | 2, 4 |
| The 0.40 bar is judged on the books alone; articles are never gated | `tests/test_retrieval_eval.py::test_summarise_bar_on_books_only`, `::test_summarise_bar_not_met` | 6 |
| A page-less hit is cited by title and URL | `tests/test_retrieval_eval.py::test_cite_without_page` | 6 |
| Every article question's quote exists in `kb` | `tests/test_retrieval_eval.py::test_every_quote_resolves` (s4) | 7 |

## Approved exceptions

## Deviations
- 2026-10-16 · Task 8: `tests/test_kb_search.py::test_returns_k_rows_with_source_and_page` now queries a unique word and checks the page on its own rows only — with article chunks loaded (page null), real vector hits entered the top 5 and broke the old assertion.
- 2026-10-16 · Task 3: `test_returns_source_url` checks the URL only on the throwaway source's rows, not every row — real book rows have no URL, so "every row" could never hold.
