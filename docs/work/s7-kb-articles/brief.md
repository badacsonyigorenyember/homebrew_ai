# S7 · Web articles and short papers into the knowledge base

Status: draft
Slug: s7-kb-articles · Branch: s7-kb-articles
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) side track P7, after S4 ·
[`s4-books-kb`](../../finished/s4-books-kb/brief.md) · [SOURCES.md](../../SOURCES.md)
Needs: `s4-books-kb` shipped (its loader, `app.kb_search`, the retrieval eval and its bar).
Before: `m8-recipe-sheet-chat`, which cites these articles.

## Why
Some of the best material for the recipe sheet's "why" is not in the books: when and how cold to
dry-hop (Janish), how hot-side hop character survives, pH in hoppy beers, coffee infusion,
Berliner Weisse and Lactobacillus souring (Milk The Funk), mash temperature and fermentability
(Troester, Terrill), brewing water (Bru'n Water *Water Knowledge*), and BJCP's own introduction to
the 2021 guidelines and to specialty-type beers. They were saved on 2026-10-16, mostly as Markdown
pages without page numbers, so s4's PDF path does not take them as they are.

## Goal
The 12 article sources listed in SOURCES.md with fate **kb** are in `kb.chunk`, retrievable and
cited by title and URL, and the retrieval eval covers them without lowering the books' result
below s4's bar.

## Scope
In:
- The s4 loader takes a Markdown file as well as a PDF; a Markdown source has no page numbers
  (`kb.chunk.page` null) and its headings give the section path.
- One source entry per article, with its URL in `ref.source.url`, and the licence as the page
  states it (or "not stated").
- The sources, all under `shared/rag-files/`: `articles/` (2 Troester, 1 Terrill, 5 Janish (one is
  the TQ paper PDF), 2 Milk The Funk), `water/brunwater_water_knowledge.md`,
  `styles/bjcp_2021_introductions.md`.
- Questions for the new sources added to the retrieval test set and reviewed by you.

Out:
- Files whose fate is **copy**, **check**, **oracle** or **later** (SOURCES.md): the BJCP study
  guide web copies, the 2008 style aids, the Bru'n Water spreadsheet, the sensory ballots, the
  flavour wheel, the Cicerone syllabus. Fetching more web pages. Web search (SearXNG).

## Requirements
R1. A Markdown source is chunked and embedded like a PDF, with `page` null and the heading path as
    `section_path`; the source header lines (URL, credit, saved date) are not chunk text.
R2. Each of the 12 sources is a `ref.source` row with title, `url` (the page URL; for the TQ PDF,
    the URL it was downloaded from), licence and `file_path`.
R3. Adding an article is one source entry and one command, documented in `docs/BOOKS.md` next to
    the books (s4 R7); re-ingesting one replaces only its chunks.
R4. `app.kb_search` results for an article show its title and URL in place of a page.
R5. The test set gains at least one reviewed question per new source (≥ 12), with expected quotes,
    in the same file and format as s4's.
R6. The eval run reports recall@5 and MRR for books and articles separately; the books' recall@5
    stays at or above s4's fixed bar.

## Constraints
- DATABASE.md §4: only prose in `kb`; tables cut, as for the books.
- The articles are copyrighted (Troester's PDF is CC BY-NC 3.0; others all rights reserved or not
  stated): local use only, every chunk cited with source and URL; no article text in the repo
  beyond the short expected quotes.
- PROJECT.md §6.8: the Markdown path is a small branch in the same loader, not a second loader.

## Assumptions
- Docling Serve's chunk endpoint accepts Markdown input with the same chunker settings
  *(unverified; check with one file first)*.
- The saved pages hold the article text only: comments, menus and sidebars were removed when saved
  *(checked by eye on 2026-10-16, not by a test)*.

## Acceptance criteria
A1. A unit test feeds a small Markdown document through the loader's chunk step: rows have
    `page` null, heading-based `section_path`, and no header lines (R1).
A2. `select slug, url, count(*) from ref.source s join kb.chunk c on c.source_id = s.id …` lists
    the 12 sources, each with a URL and chunks; the books' counts are unchanged (R2, R3).
A3. A `--question` run shows an article hit with title and URL (R4).
A4. The test set has ≥ 12 new reviewed questions, one or more per new source (R5).
A5. The eval run's books recall@5 is at or above s4's bar; articles' recall@5 and MRR are recorded
    in PROJECT.md §8 (R6).

## Open questions
1. Bar for articles? — options: a) report only this time; b) the same bar as the books —
   recommend a: 12 questions are too few for a stable bar.
2. The Bru'n Water page is ~17,000 words of one author's water chemistry, close to *Water*.
   Ingest both? — options: a) yes, both, cited separately; b) only *Water* — recommend a: different
   explanations of the same topic help retrieval, and both are cited.

## Deviations
