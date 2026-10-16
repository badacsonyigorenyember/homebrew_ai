# Verification: s7-kb-articles

Overall: ✅ all 10 checks and 571 tests pass

## Part 1: Summary

🎯 **Goal:** Put 12 saved web articles and short papers into `kb.chunk`, cited by title and URL, without dropping the books below the retrieval bar.

🛠️ **How:** A small Markdown branch in the s4 loader (`loaders/books.py`), an `ARTICLES` dict of 12 entries, `source_url` returned by `app.kb_search`, and an eval that reports books and articles apart.

🤔 **Why this way:** One loader with a few branches keeps §6.8 (readable over optimal); dropping reference sections by heading after Docling works for Markdown and PDF alike.

🏁 **Result:** 12 article sources with URLs and 258 chunks (205 Markdown with no page, 53 PDF), books unchanged at 2,180 chunks; books recall@5 0.422 / MRR@10 0.345 (bar 0.40 met), articles 0.867 / 0.608 (15 questions, no bar).

### 🚦 Steps

- ✅ 📝 **Brief:** Draft checked and revised, then the three user decisions folded in (articles "Report only", "Stop and report" below 0.40, Troester "Wiki page"). Approved, a85f0bd.
- ✅ 🗺️ **Plan:** 8 tasks, Docling Markdown behaviour measured live. Approved, 3e7cb0e.
  - ⚠️ Troester wiki URL could not be fetched (HTTP 500), so the plan carries it unverified.
- ⚠️ 🔨 **Implement:** 8 tasks done in 8 commits, plus one review-fix commit; 2 deviations recorded.
  - ⚠️ Task 1: Troester wiki URL returned HTTP 500 again.
  - ⚠️ Task 3: test wording changed without a Deviation line. 🔧 fixed in 99b0a9b
  - ⚠️ Task 5: Troester URL stored unverified (disclosed in BOOKS.md §1c).
  - ⚠️ Task 8: `test_returns_k_rows_with_source_and_page` failed once article chunks were loaded; test changed, Deviation recorded.
- ⚠️ 🔍 **Review:** Ready for testing, no must-fix; 2 should-fix (missing Deviation line, missing §8 entries for Tasks 3 and 6) 🔧 fixed in 99b0a9b. Four notes left open (missing-file test passes silently instead of skipping, A1 covered by two tests, weaker k-rows test, Troester URL unverified).
- ✅ 🧪 **Verify:** All acceptance criteria A1–A6 confirmed on the running stack; full suite green. 🧮 spot checks ✅ 10/10 · 🧪 tests ✅ 571/571

👀 **Start here:** Part 2, the `kb_search` example: an article hit now shows its title and URL where a book hit shows a page.

📁 **Changed files:**
- `PROJECT.md`
- `db/040_kb_search.sql`
- `docs/BOOKS.md`
- `docs/DATABASE.md`
- `docs/work/s7-kb-articles/brief.md`
- `docs/work/s7-kb-articles/plan.md`
- `docs/work/s7-kb-articles/review.md`
- `docs/work/s7-kb-articles/verification.md`
- `evals/results/2026-10-16-s7.json`
- `evals/retrieval.py`
- `evals/retrieval_questions.toml`
- `loaders/books.py`
- `tests/test_books.py`
- `tests/test_kb_search.py`
- `tests/test_retrieval_eval.py`

## Part 2: Showcase

| What | What it does |
|---|---|
| `loaders.books.ARTICLES` | 12 article entries (10 Markdown, 2 PDF) with `url` and `drop_sections` |
| `loaders.books.clean_markdown` | Drops the saved-page header lines and `[n]` markers before Docling |
| `app.kb_search` (`source_url`) | Search results carry the source URL |
| `evals.retrieval` | Reports books (with the 0.40 bar) and articles (no bar) apart; `cite()` shows title and URL for a page-less chunk |

```mermaid
flowchart LR
  A[Saved page .md / .pdf] --> B[clean_markdown: header, markers]
  B --> C[Docling chunker]
  C --> D[drop reference sections by heading]
  D --> E[bge-m3 embed]
  E --> F[(kb.chunk, page null for .md)]
  F --> G[app.kb_search with source_url]
```

**The 12 article sources in the database**

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select s.slug, s.url, count(c.*) from ref.source s join kb.chunk c on c.source_id = s.id where s.url is not null group by 1, 2 order by 1"
```

<details><summary>Output (12 rows)</summary>

```text
bjcp-2021-introductions|https://styles.bjcp.org/bjcp-2021-beer/|42
brunwater-water-knowledge|https://www.brunwater.com/water-knowledge|78
janish-coffee-beers|https://scottjanish.com/guide-to-coffee-beers/|18
janish-dry-hop-best-practices-tq|https://doi.org/10.1094/TQ-58-1-0402-01|27
janish-ph-hoppy-beers|https://scottjanish.com/a-look-at-ph-in-hoppy-beers/|9
janish-short-cool-dry-hopping|https://scottjanish.com/a-case-for-short-and-cool-dry-hopping/|14
janish-survivables-hot-side|https://scottjanish.com/survivables-unpacking-hot-side-hop-flavor/|17
mtf-berliner-weissbier|https://www.milkthefunk.com/wiki/Berliner_Weissbier|11
mtf-lactobacillus-fermentation|https://www.milkthefunk.com/wiki/Lactobacillus_Fermentation|7
terrill-observations-on-attenuations|http://seanterrill.com/2017/04/21/observations-on-attenuations/|4
troester-mash-parameters|https://braukaiser.com/wiki/index.php/Effects_of_mash_parameters_on_fermentability_and_efficiency_in_single_infusion_mashing|26
troester-mash-time-fermentability|http://braukaiser.com/wiki/index.php/Mash_Time_Dependency_of_Wort_Fermentability|5
```
</details>

**Asking how long and how cold to dry hop a hazy IPA**: book hits show a page, a Markdown article hit shows title and URL.

```bash
.venv/bin/python -m evals.retrieval --question "how long and how cold should I dry hop a hazy IPA" | cut -c1-200 | head -8
```

```text
1. palmer-how-to-brew p98 | Dry Hopping | 0.0323
   Dry hopping, where hops are added to the beer at the end of fermentation, is probably the best way to get fresh hop aroma into a beer. As the name implies, the hops are added dry. Many varieties of ho
2. janish-dry-hop-best-practices-tq p8 | Key Findings | 0.0303
   - The extraction of hop compounds during dry hopping can happen relatively quickly, generally 1-3 days. This is true even at temperatures cooler than fermentation temperatures. - Agitation of dry hops
3. janish-short-cool-dry-hopping | A Case for Short and Cool Dry Hopping | https://scottjanish.com/a-case-for-short-and-cool-dry-hopping/ | A Case for Short and Cool Dry Hopping > A Case for Short And Cool Dry Hopping > Dry Hopping and Polyphenols | 0.0303
   One of my biggest complaints with heavily-hopped hazy IPAs is an aggressive vegetal bitterness, sometimes referred to as “hop bite.” Part of this could be explained by a large portion of polyphenols m
4. janish-dry-hop-best-practices-tq p6 | Oxygen | 0.0303
   Oxygen introduction during dry hopping is one of the enemies of retaining that fresh, bright, and vibrant hop character. Unfortunately, this seems to be especially true for hazy IPAs
```

**Article chunks: no page, heading path as section**

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select s.slug, c.page is null as no_page, c.section_path from kb.chunk c join ref.source s on s.id=c.source_id where s.slug in ('janish-ph-hoppy-beers','mtf-berliner-weissbier') order by 1, c.id limit 6"
```

```text
janish-ph-hoppy-beers|t|A Look at pH in Hoppy Beers > A Look at pH in Hoppy Beers
janish-ph-hoppy-beers|t|A Look at pH in Hoppy Beers > A Look at pH in Hoppy Beers > How Dry Hopping Rates Increase Beer pH
janish-ph-hoppy-beers|t|A Look at pH in Hoppy Beers > A Look at pH in Hoppy Beers > How Dry Hopping Rates Increase Beer pH
janish-ph-hoppy-beers|t|A Look at pH in Hoppy Beers > A Look at pH in Hoppy Beers > Dry Hopping pH Calculator
janish-ph-hoppy-beers|t|A Look at pH in Hoppy Beers > A Look at pH in Hoppy Beers > Does it Matter?
janish-ph-hoppy-beers|t|A Look at pH in Hoppy Beers > A Look at pH in Hoppy Beers > Does it Matter?
```

**The retrieval eval, books and articles apart**

```bash
.venv/bin/python -m evals.retrieval | head -4
```

```text
books    recall@5 0.422   MRR@10 0.345   (45 questions)
bar 0.4: bar met
articles recall@5 0.867   MRR@10 0.608   (15 questions)
  bjcp-2021-introductions            recall@5 1.000   MRR@10 1.000   (2)
```

Article misses: q56 and q59 (Terrill and Milk The Funk Lactobacillus, 0.000 each). Books: s4 was 0.422 / 0.354, now 0.422 / 0.345.

## Part 3: Spot checks

### ✅ C1 · 12 article sources, each with URL and chunks (A2)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*), min(n), sum(n) from (select count(c.*) n from ref.source s join kb.chunk c on c.source_id = s.id where s.url is not null group by s.id) t"
```

| Expected | Actual | Result |
|---|---|---|
| 12 sources, each ≥ 1 chunk | `12\|4\|258` | ✅ pass |

### ✅ C2 · Books unchanged at 2,180 chunks (A2)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select string_agg(slug||':'||n, ' ' order by slug), sum(n) from (select s.slug, count(*) n from kb.chunk c join ref.source s on s.id=c.source_id where s.url is null group by 1) t"
```

| Expected | Actual | Result |
|---|---|---|
| 943 / 357 / 454 / 341 / 85, total 2180 | `bjcp-exam-study-guide-2017:85 mallett-malt:341 palmer-how-to-brew:943 palmer-kaminski-water:357 white-zainasheff-yeast:454\|2180` | ✅ pass |

### ✅ C3 · No header lines or left-out sections in article chunks (A1, R1)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from kb.chunk c join ref.source s on s.id=c.source_id where s.url is not null and (c.text like '%Source: http%' or c.text ~ '(^|\n)Saved 20' or c.section_path ~* '(footnotes|references|see also|external (history )?resources|video presentations)')"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C4 · No `[n]` markers in Milk The Funk chunks (R1)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from kb.chunk c join ref.source s on s.id=c.source_id where s.slug like 'mtf-%' and c.text ~ ' ?\[[0-9]+\]'"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C5 · Markdown chunks have no page, PDF chunks have one (R1)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) filter (where page is null), count(*) filter (where page is not null and s.slug in ('troester-mash-parameters','janish-dry-hop-best-practices-tq')) from kb.chunk c join ref.source s on s.id=c.source_id where s.url is not null"
```

| Expected | Actual | Result |
|---|---|---|
| 205 page-less (10 Markdown sources), 53 PDF chunks with a page | `205\|53` | ✅ pass |

### ✅ C6 · PDF reference lists are out (A1, R1)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from kb.chunk c join ref.source s on s.id=c.source_id where s.slug in ('troester-mash-parameters','janish-dry-hop-best-practices-tq') and c.text ~* 'doi:|J\. Am\. Soc\. Brew|Narziss, 2005'"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C7 · Re-ingesting one article leaves every other source unchanged (A3)

Ran `.venv/bin/python -m loaders.books janish-ph-hoppy-beers --reuse-docling`, comparing before and after: fingerprint `md5(string_agg(text, '|' order by section_path, text))` of the article, and an md5 of every other source's `slug:count`.

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select md5(string_agg(text, '|' order by section_path, text)), count(*) from kb.chunk c join ref.source s on s.id=c.source_id where s.slug='janish-ph-hoppy-beers'"
```

| Expected | Actual | Result |
|---|---|---|
| Same fingerprint and other-source counts before and after | before and after both `e9bee0aa94a984ac6ae6baed9c70c0e9\|9`; others `e560aacf62196be4a0b3f256174b994e` both times | ✅ pass |

### ✅ C8 · An article hit shows title and URL (A4)

```bash
.venv/bin/python -m evals.retrieval --question "how long and how cold should I dry hop a hazy IPA" | grep -c "https://scottjanish.com/a-case-for-short-and-cool-dry-hopping/"
```

| Expected | Actual | Result |
|---|---|---|
| ≥ 1 line with an article title and URL | 1 | ✅ pass |

### ✅ C9 · 15 reviewed article questions, one or more per source (A5)

```bash
python3 -c "
import tomllib,collections
d=tomllib.load(open('evals/retrieval_questions.toml','rb'))['question']
c=collections.Counter(q['book'] for q in d[45:]); print(len(d), sum(c.values()), len(c), min(c.values()))"
```

| Expected | Actual | Result |
|---|---|---|
| 60 total, ≥ 12 new, 12 sources, min 1 | `60 15 12 1` | ✅ pass |

### ✅ C10 · Books recall@5 at or above 0.40, articles reported without a bar (A6, R6)

```bash
.venv/bin/python -m evals.retrieval | head -3
```

| Expected | Actual | Result |
|---|---|---|
| books ≥ 0.40, bar met; articles line with no bar line | `books recall@5 0.422 MRR@10 0.345`, `bar 0.4: bar met`, `articles recall@5 0.867 MRR@10 0.608` | ✅ pass |

`app.kb_search` was also checked: owner `postgres`, ACL null, `source_url` in the result columns.

## Part 4: Regression tests

Command: `.venv/bin/pytest -q` (stack up)  ·  Result: ✅ 571 passed in 165.68s

| Test | Protects | Result |
|---|---|---|
| tests/test_books.py::test_clean_markdown_drops_header_and_markers | Header lines and `[n]` markers never reach `kb` | ✅ |
| tests/test_books.py::test_clean_markdown_requires_header | A file saved without the header fails instead of leaking it | ✅ |
| tests/test_books.py::test_markdown_rows | Markdown rows: no page, heading path, left-out sections dropped | ✅ |
| tests/test_books.py::test_chunk_rows_drops_pdf_section_case_insensitive | PDF reference sections dropped by heading, neighbours kept | ✅ |
| tests/test_books.py::test_chunk_rows_pdf_without_page_raises | A page-less PDF chunk still fails (s4 behaviour) | ✅ |
| tests/test_books.py::test_docling_form_markdown | Markdown goes to Docling as Markdown | ✅ |
| tests/test_books.py::test_sources_slugs_distinct | No slug clash; every article has a URL | ✅ |
| tests/test_books.py::test_article_urls_match_source_lines | Each article is cited by the URL its saved page names (ran, all files present) | ✅ |
| tests/test_books.py::test_upsert_source_writes_url | Upsert writes the URL and never wipes one | ✅ |
| tests/test_books.py::test_replace_chunks_only_touches_its_book | Re-ingest replaces only its own chunks | ✅ |
| tests/test_kb_search.py::test_returns_source_url | Retrieval results carry the source URL | ✅ |
| tests/test_retrieval_eval.py::test_summarise_bar_on_books_only | The bar is judged on books alone | ✅ |
| tests/test_retrieval_eval.py::test_summarise_bar_not_met | Books under the bar fail even with perfect articles | ✅ |
| tests/test_retrieval_eval.py::test_cite_without_page | A page-less hit is cited by title and URL | ✅ |
| tests/test_retrieval_eval.py::test_cite_with_page | A paged hit is cited by page | ✅ |
| tests/test_retrieval_eval.py::test_question_set_shape | Question set shape: ≥ 12 article questions, page rules, quote length | ✅ |
| tests/test_retrieval_eval.py::test_every_quote_resolves | Every expected quote exists in `kb` | ✅ |

Failures: none.
