# S7 · Web articles and short papers into the knowledge base

Status: approved
Slug: s7-kb-articles · Branch: s7-kb-articles
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) side track P7, after S4 ·
[`s4-books-kb`](../../finished/s4-books-kb/brief.md) · [SOURCES.md](../../SOURCES.md) ·
[BOOKS.md](../../BOOKS.md)
Needs: `s4-books-kb` shipped (done 2026-10-16: `loaders/books.py`, `app.kb_search`, the retrieval
eval and its recall@5 bar of 0.40).
Before: `m8-recipe-sheet-chat`, which cites these articles.

## Why
Some of the best material for the recipe sheet's "why" is not in the books: when and how cold to
dry-hop (Janish), how hot-side hop character survives, pH in hoppy beers, coffee infusion,
Berliner Weisse and Lactobacillus souring (Milk The Funk), mash temperature and fermentability
(Troester, Terrill), brewing water (Bru'n Water *Water Knowledge*), and BJCP's own introduction to
the 2021 guidelines and to specialty-type beers. They were saved on 2026-10-16: 10 as Markdown
pages without page numbers, 2 as PDFs. s4's loader takes PDFs only, and fails on a chunk with no
page (Docling returns an empty page list for Markdown).

## Goal
The 12 article sources listed in SOURCES.md with fate **kb** are in `kb.chunk`, retrievable and
cited by title and URL, and the retrieval eval covers them without lowering the books' result
below s4's bar.

## Scope
In:
- The s4 loader (`loaders/books.py`) takes a Markdown file as well as a PDF; a Markdown source has
  no page numbers (`kb.chunk.page` null) and its headings give the section path.
- One source entry per article, with its URL in `ref.source.url`, and the licence as SOURCES.md
  states it (or "not stated").
- The 12 sources, all under `shared/rag-files/`:
  - `articles/`, Markdown: `braukaiser_mash_time_fermentability.md`,
    `terrill_observations_on_attenuations.md`, `janish_short_cool_dry_hopping.md`,
    `janish_survivables_hot_side.md`, `janish_ph_hoppy_beers.md`, `janish_coffee_beers.md`,
    `mtf_berliner_weissbier.md`, `mtf_lactobacillus_fermentation.md`
  - `articles/`, PDF (the existing PDF path): `braukaiser_mash_parameters_2009.pdf` (23 pp),
    `janish_dry_hop_best_practices_tq_2021.pdf` (8 pp)
  - `water/brunwater_water_knowledge.md`, `styles/bjcp_2021_introductions.md`
- Reference lists, footnotes and link sections left out of `kb` (they exist in 8 of the 12:
  Janish "Footnotes", Milk The Funk "See Also", "External Resources" and "References", Bru'n
  Water "5. References", the reference pages of both PDFs).
- `app.kb_search` returns the source URL.
- Questions for the new sources added to the retrieval test set and reviewed by you.

Out:
- Files whose fate is **copy**, **check**, **oracle** or **later** (SOURCES.md): the BJCP study
  guide web copies, the 2008 style aids, the Bru'n Water spreadsheet, the sensory ballots, the
  flavour wheel, the Cicerone syllabus. Fetching more web pages. Web search (SearXNG).
- The doc → calc passes on these sources (s5-mash-attenuation, m7-process). Their tables are cut
  from `kb` either way, as for the books.
- Tuning retrieval (the RECIPE-ROADMAP §8 TODO from s4). If the books fall below the bar, s7
  stops and reports; tuning is its own work item (R6).
- The s4 verify notes on duplicated *How to Brew* caption chunks and the stale PROJECT.md §5
  *Malt* row.

## Requirements
R1. A Markdown source is chunked and embedded like a PDF, with `page` null and the heading path as
    `section_path`. Not chunk text: the source header lines (title line, `Source:` URL, credit,
    saved date), Milk The Funk's inline reference markers (`[2]`), and the sections named in the
    source entry as left out (footnotes, references, see-also and external-link sections).
R2. Each of the 12 sources is a `ref.source` row with title, `url`, licence and `file_path`. The
    URL is the `Source:` line of the saved page; for `bjcp_2021_introductions.md` (16 pages in one
    file) the base URL `https://styles.bjcp.org/bjcp-2021-beer/`; for the TQ paper its DOI link
    `https://doi.org/10.1094/TQ-58-1-0402-01` (printed on the paper); for Troester's PDF the
    braukaiser.com wiki page of the same article, found during the work (its download URL was not
    recorded).
R3. Adding an article is one source entry and one command, documented in `docs/BOOKS.md` next to
    the books (s4 R7); re-ingesting one replaces only its chunks.
R4. `app.kb_search` results carry the source URL; for a chunk with no page, the eval's
    `--question` output shows the title and URL in place of a page.
R5. The test set gains at least one reviewed question per new source (≥ 12), with expected quotes,
    in the same file (`evals/retrieval_questions.toml`) and format as s4's; an expected passage
    from a Markdown source has a quote and no page.
R6. The eval run reports recall@5 and MRR@10 for books and articles separately; the books'
    recall@5 on s4's 45 questions stays at or above s4's bar (0.40). The articles get no bar this
    time: their numbers are reported only. If the books' recall@5 falls below 0.40 once the
    articles are in, the work stops and reports; it does not tune retrieval or move the bar.

## Constraints
- DATABASE.md §4: only prose in `kb`; tables cut, as for the books.
- The sources are copyrighted (Troester's PDF CC BY-NC 3.0; the TQ paper © MBAA; the rest all
  rights reserved or not stated): local use only, every chunk cited with source and URL; no
  article text in the repo beyond the short expected quotes (4–12 words, as in s4).
- PROJECT.md §6.8: the Markdown path is a small branch in the same loader, not a second loader.
- CLAUDE.md: the `app.kb_search` change is a `.sql` file in the repo, applied with `psql` as
  `postgres` (OPERATIONS.md §4), not through the read-only Supabase MCP.
- Embedding model `bge-m3` (1024 dims) and Docling Serve chunker settings as in s4.

## Assumptions
- Docling Serve's hybrid chunk endpoint takes Markdown (`convert_from_formats=md`) with the same
  chunker settings. *Checked 2026-10-16 with a small test file:* status success, headings give the
  heading path, `page_numbers` is an empty list, the header lines come back as text, a table stays
  inline in the prose chunk (so the existing table cut applies).
- The saved pages hold the article text only: comments, menus and sidebars were removed when saved
  *(checked by eye on 2026-10-16, not by a test)*. Reference and link sections were kept, hence R1.
- Adding article chunks can push book chunks out of the top 5. The books' first run (0.422) is
  only 0.022 above the bar *(measured in s4; the effect of the articles is unmeasured)*.

## Acceptance criteria
A1. A unit test feeds a small Markdown document through the loader's chunk step: rows have
    `page` null, heading-based `section_path`, no header lines, no `[n]` markers, and no row from a
    left-out section (R1).
A2. `select s.slug, s.url, count(c.*) from ref.source s join kb.chunk c on c.source_id = s.id
    group by 1, 2` lists the 12 sources, each with a URL and chunks; the five books still hold
    2,180 chunks with the same per-book counts (R2, R3).
A3. Re-ingesting one article with its documented command leaves every other source's chunk count
    unchanged (R3).
A4. A `--question` run shows an article hit with title and URL (R4).
A5. The test set has ≥ 12 new reviewed questions, one or more per new source (R5).
A6. The eval run's books recall@5 on s4's 45 questions is at or above 0.40; articles' recall@5
    and MRR@10 are printed separately, with no pass/fail line for them, and recorded in
    PROJECT.md §8 (R6).

## Open questions

## Deviations
- 2026-10-16 · R6: articles' recall@5 and MRR@10 are reported only, with no bar — user chose
  "Report only" (about 12 questions are too few for a stable bar).
- 2026-10-16 · R6, Scope: if the books' recall@5 falls below 0.40, the work stops and reports;
  retrieval tuning is its own work item — user chose "Stop and report".
- 2026-10-16 · R2: Troester's PDF takes the URL of the braukaiser.com wiki page of the same
  article, found during the work — user chose "Wiki page".
