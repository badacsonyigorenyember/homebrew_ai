# Books and articles in the knowledge base

The books and articles are loaded into `kb.chunk` by [`loaders/books.py`](../loaders/books.py) (design:
[DATABASE.md](DATABASE.md) §4, work: [`s4-books-kb`](finished/s4-books-kb/plan.md)). Only prose is
stored. Tables and formulas are cut out and go through the doc → calculation pass instead
(PROJECT.md §6.7). Page numbers are **PDF page numbers** (1-based), not the printed ones. For
*How to Brew* the PDF page is the printed page + 26. A Markdown source (a saved web page) has no
page: its `page` is null and it is cited by title and URL (§1c, s7: [`s7-kb-articles`](work/s7-kb-articles/plan.md)).

## 1. Books in `kb`

| Slug | Book | File | PDF pages | Skipped pages | Chunks | Ingested |
|---|---|---|---|---|---|---|
| `palmer-how-to-brew` | *How to Brew*, Palmer, fourth edition 2017 | `books/how_to_brew.pdf` | 612 | 1–26 (cover, praise, contents, preface, acknowledgments, abbreviations), 579–612 (bibliography, index) | 943 (tokens min 32, median 273, max 514; measured) | 2026-10-16 |
| `palmer-kaminski-water` | *Water: A Comprehensive Guide for Brewers*, Palmer & Kaminski, 2013 | `books/palmer_kaminski_water.pdf` | 273 | 1–18 (cover, contents, figure list, acknowledgments, foreword), 238–273 (last table page, index) | 357 (tokens min 35, median 319, max 514; measured) | 2026-10-16 |
| `white-zainasheff-yeast` | *Yeast: The Practical Guide to Beer Fermentation*, White & Zainasheff, 2010 | `books/white_zainasheff_yeast.pdf` | 325 | 1–21 (cover, contents, acknowledgments, foreword, blank pages), 305–325 (blank page, figure credits, references, index) | 454 (tokens min 31, median 298, max 514; measured) | 2026-10-16 |
| `mallett-malt` | *Malt: A Practical Guide from Field to Brewhouse*, Mallett, 2014 | `books/mallett_malt.pdf` | 335 | 1–16 (cover, contents, acknowledgments, foreword), 263–335 (bibliography, index) | 341 (tokens min 46, median 316, max 514; measured) | 2026-10-16 |
| `bjcp-exam-study-guide-2017` | *BJCP Beer Exam Study Guide*, BJCP, last revised December 2017 | `books/bjcp_exam_study_guide_2017.pdf` | 77 | 1–45 (sections I–III: introduction, judging and exam rules, exam questions, style guidelines); section IV, Ingredients and the Brewing Process, is kept | 85 (tokens min 59, median 313, max 510; measured) | 2026-10-16 |

Docling's hybrid chunker made 1,276 chunks for *How to Brew*. 132 fell on the skipped pages and
201 had fewer than 20 words once tables and formula placeholders were cut, leaving 943. A second
ingest from a fresh Docling run gave the same 943 chunks and the same fingerprint
(`md5(string_agg(text, '|' order by page, section_path, text))` = `4d8d4941c1b14cb61ba6ee195a58cc6b`),
though the saved Docling JSON differs byte for byte between runs.

*Water* took 2.5 minutes in Docling and made 440 chunks. 52 fell on the skipped pages and 31 had
fewer than 20 words once tables were cut, leaving 357 (fingerprint `ef0c023d3add16d1339077690da3be1a`;
a second ingest from a fresh Docling run gave the same). The PDF page is the printed page + 18.
Its edition line is just `2013`: the copyright page gives the year and no edition number.

*Yeast* took 2.1 minutes in Docling and made 526 chunks. 46 fell on the skipped pages and 26 had
fewer than 20 words once tables were cut, leaving 454 (fingerprint `39be2bdfe4ece6a181d29f1dba225c24`;
a second ingest with `--reuse-docling` gave the same). The PDF page is the printed page + 21. Its
edition line is `2010` (copyright page: year only). The foreword is by another author and sits in
the skipped front matter; the authors' own text starts with the Introduction on PDF page 22.

*Malt* took 2.3 minutes in Docling and made 458 chunks. 88 fell on the skipped pages and 29 had
fewer than 20 words once tables were cut, leaving 341 (fingerprint `8e977294269bdb739c3fa4fbe44f881e`;
a second ingest with `--reuse-docling` gave the same). The front matter is roman-numbered and
chapter 1 starts on PDF page 25 (unverified: printed page offset). Its edition line is `2014`
(copyright page: year only). The foreword is by another author. Appendix D (home malting, PDF
pages 254–262) is prose and is kept.

The *BJCP Beer Exam Study Guide* took 51 seconds in Docling and made 202 chunks. 111 fell on the
skipped pages 1–45 and 6 had fewer than 20 words once tables were cut, leaving 85 (fingerprint
`309e4923fc87bb4c0a6e58a48595c263`; a second ingest with `--reuse-docling` gave the same). Only
section IV is kept (PDF pages 46–77, printed page + 4); sections I–III are exam rules, judging
procedure and exam questions, not brewing knowledge. The PDF has a text layer without embedded
fonts, so no OCR. The licence is the guide's own copyright line (free to download); local use.

## 1b. First retrieval run and the recall@5 bar

First measured run, 2026-10-16 (`python -m evals.retrieval --save s4-first`, saved in
`evals/results/2026-10-16-s4-first.json`; 45 questions, 9 per book, before any tuning):
recall@5 **0.422**, MRR@10 **0.354**.

| Book | recall@5 | MRR@10 |
|---|---|---|
| `palmer-how-to-brew` | 0.444 | 0.347 |
| `palmer-kaminski-water` | 0.333 | 0.178 |
| `white-zainasheff-yeast` | 0.444 | 0.414 |
| `mallett-malt` | 0.556 | 0.583 |
| `bjcp-exam-study-guide-2017` | 0.333 | 0.250 |

26 of 45 questions missed. In the top 5 of many misses, chunks from another book outranked the
expected one (for example *How to Brew* on off-flavour and malt questions). The bar
`RECALL_AT_5_BAR` in [`evals/retrieval.py`](../evals/retrieval.py) is **0.40**: the first run's
recall@5 rounded down to the nearest 0.05 (user's decision, 2026-10-16). No retrieval setting was
tuned; a tuning TODO is in [RECIPE-ROADMAP](RECIPE-ROADMAP.md) §8 Later.

## 1c. Articles in `kb`

Ten Markdown sources, ingested 2026-10-16 with `python -m loaders.books <slug>` (205 chunks;
`page` is null, `ref.source.url` is set). The saved page's header lines and the Milk The Funk
`[n]` markers are cleaned off before Docling, and the sections named in the "Left out" column are
dropped by heading afterwards. All figures measured. The books still hold 2,180 chunks (943 / 357 /
454 / 341 / 85).

| Slug | File (under `shared/rag-files/`) | URL | Left out | Chunks (tokens min / median / max) | Table chunks cut |
|---|---|---|---|---|---|
| `troester-mash-time-fermentability` | `articles/braukaiser_mash_time_fermentability.md` | http://braukaiser.com/wiki/index.php/Mash_Time_Dependency_of_Wort_Fermentability | – | 5 (88 / 111 / 473) | 1 |
| `terrill-observations-on-attenuations` | `articles/terrill_observations_on_attenuations.md` | http://seanterrill.com/2017/04/21/observations-on-attenuations/ | – | 4 (390 / 475 / 514) | 0 |
| `janish-short-cool-dry-hopping` | `articles/janish_short_cool_dry_hopping.md` | https://scottjanish.com/a-case-for-short-and-cool-dry-hopping/ | Footnotes (2 chunks) | 14 (161 / 362 / 498) | 1 |
| `janish-survivables-hot-side` | `articles/janish_survivables_hot_side.md` | https://scottjanish.com/survivables-unpacking-hot-side-hop-flavor/ | Footnotes (2 chunks) | 17 (183 / 415 / 509) | 0 |
| `janish-ph-hoppy-beers` | `articles/janish_ph_hoppy_beers.md` | https://scottjanish.com/a-look-at-ph-in-hoppy-beers/ | Footnotes (1 chunk) | 9 (238 / 392 / 470) | 0 |
| `janish-coffee-beers` | `articles/janish_coffee_beers.md` | https://scottjanish.com/guide-to-coffee-beers/ | – | 18 (86 / 385 / 502) | 1 |
| `mtf-berliner-weissbier` | `articles/mtf_berliner_weissbier.md` | https://www.milkthefunk.com/wiki/Berliner_Weissbier | External History Resources, Video Presentations, See Also, References (7 chunks) | 11 (106 / 303 / 510) | 3 |
| `mtf-lactobacillus-fermentation` | `articles/mtf_lactobacillus_fermentation.md` | https://www.milkthefunk.com/wiki/Lactobacillus_Fermentation | See Also, References (3 chunks) | 7 (70 / 187 / 481) | 1 |
| `brunwater-water-knowledge` | `water/brunwater_water_knowledge.md` | https://www.brunwater.com/water-knowledge | 5. References (2 chunks) | 78 (72 / 374 / 514) | 0 |
| `bjcp-2021-introductions` | `styles/bjcp_2021_introductions.md` | https://styles.bjcp.org/bjcp-2021-beer/ | – | 42 (39 / 290 / 515) | 2 |

Re-running `janish-ph-hoppy-beers` with `--reuse-docling` gave the same 9 chunks and the same
fingerprint (`md5(string_agg(text, '|' order by section_path, text))` =
`e9bee0aa94a984ac6ae6baed9c70c0e9`), and no other source's count changed.

The two PDF articles (Troester's mash-parameters paper and Janish's TQ dry-hop paper) are loaded by
the next step of s7; they are added here when they are.

The Troester articles are cited by their braukaiser.com wiki pages. The wiki page of the
mash-parameters paper (`https://braukaiser.com/wiki/index.php/Effects_of_mash_parameters_on_fermentability_and_efficiency_in_single_infusion_mashing`)
was not reachable on 2026-10-16 (HTTP 500), so that URL is unverified.

## 2. Adding a book

1. Put the PDF in `shared/rag-files/books/`.
2. Check it has a text layer: `pdffonts FILE` lists fonts (poppler may print "Syntax Error" lines
   first; they are harmless). If it lists none, set `ocr=True` on the entry.
3. Add one `Book` entry to `BOOKS` in `loaders/books.py` (slug, title, edition, publisher, licence,
   `file_path`; read the first three from the PDF's copyright page, `pdftotext -f 3 -l 4 FILE -`
   usually shows it, on page 3 or 4. The page may give only a year: use that as the edition. Leave
   `skip_pages` empty for the first run).
4. Run `.venv/bin/python -m loaders.books <slug>`, in the background if your tool times out. Docling
   took 2–3 minutes for the 273- and 325-page books and longer for a 612-page one; the
   run saves Docling's answer to `shared/rag-files/docling-chunks/<slug>.chunks.json` (gitignored).
5. Read the printed stats, and look at the saved JSON and `pdftotext -f N -l N FILE` to find the
   contents, index, bibliography and reading-list pages (`for p in $(seq 1 N); do pdftotext -f $p -l $p FILE - | head -3; done`
   shows where chapters start and the index begins). A chunk is dated by its first page, so if the
   index starts on the page after the last table, check that the last kept page has no index text
   (look for table-like rows in step 6). Set `skip_pages` and re-run with
   `--reuse-docling` (no new Docling run; the database is rewritten for this book only).
6. Check the counts:
   ```sql
   select s.slug, count(*), min(tokens), percentile_disc(0.5) within group (order by tokens),
          max(tokens), count(*) filter (where text like '%|%|%') as table_like
   from kb.chunk c join ref.source s on s.id = c.source_id group by 1;
   ```
   This book has chunks, no table-like rows, and the other books' counts are unchanged.
7. Write the book's doc → calc note in §3.
8. Add the book to PROJECT.md §5.

Run the SQL with `docker exec -i supabase-db psql -U postgres -d postgres` (OPERATIONS.md §4).

## 2b. Adding an article

A web page or short paper, cited by URL. Slugs must differ from every book's.

1. **Markdown (a saved web page).** Save it under `shared/rag-files/articles/` (or `water/`,
   `styles/`) with a header block: line 1 is the `# ` title, then a `Source:` line, the credit
   line(s), and a line starting `Saved ` (all within the first 10 lines). `clean_markdown` raises
   `ValueError` for a file without them, so a header can't leak into `kb`.
2. Find the sections to leave out (references, footnotes, link lists): `grep -n '^#' FILE`.
3. Add one `ARTICLES` entry in `loaders/books.py` with `url` (the page's `Source:` URL) and
   `drop_sections` (heading texts, matched case-insensitively anywhere in a chunk's heading path).
4. Run `.venv/bin/python -m loaders.books <slug>`. Docling takes seconds for a page. Expect
   `dropped by section` > 0 when `drop_sections` is set.
5. Run the §2 step 6 check, plus these (each should return 0 rows for the new slug):
   ```sql
   -- header lines leaked
   select 1 from kb.chunk c join ref.source s on s.id = c.source_id
    where s.slug = :'slug' and (text like '%Source: http%' or text ~ '^Saved 20');
   -- a left-out section kept
   select 1 from kb.chunk c join ref.source s on s.id = c.source_id
    where s.slug = :'slug'
      and section_path ~* '(footnotes|references|see also|external (history )?resources|video presentations)';
   -- Markdown with a page
   select 1 from kb.chunk c join ref.source s on s.id = c.source_id
    where s.slug = :'slug' and c.page is not null;
   -- [n] reference markers left in the text
   select 1 from kb.chunk c join ref.source s on s.id = c.source_id
    where s.slug = :'slug' and text ~ ' ?\[[0-9]+\]';
   ```
6. Add the article to §1c and to PROJECT.md §5.

**PDF.** Follow §2, adding `url` to the entry. Use `drop_sections` for a references heading and
`skip_pages` for cover or appendix pages.

## 3. Doc → calc notes per book

A cut table is never in `kb`, whether or not a pass has turned it into data yet.

### *How to Brew*

Passes so far:
- `s1-maths` ([doc-calc.md](finished/s1-maths/doc-calc.md)): gravity from extract, boil gravity and
  volumes, SG ↔ °Plato, FG, ABV (table 9.1), IBU (Tinseth, table 5.5), colour (Morey).
- `adjunct-fermentables`: Table 18.5 (flaked adjuncts, PDF p. 316) and Table 24.1 (sugars, PDF
  p. 462) are in `ref.fermentable`.
- Everything else below is **not passed yet**; water chemistry (chapters 8, 21, 22) and mash
  and process tables go to m7-process.

Pages where the loader cut a markdown table or Docling left a formula placeholder
(`<!-- formula-not-decoded -->`), by chapter (194 table pages and 43 formula pages outside the
skipped ranges, measured 2026-10-16). Formulas that Docling did not mark are still in the prose
and are not listed.

| Chapter | PDF pages | Table pages | Formula pages |
|---|---|---|---|
| 1 First Batch | 31–50 | 31, 36 | – |
| 2 Cleaning | 51–68 | 51, 63–66 | – |
| 3 Malt | 69–74 | 69 | – |
| 4 Kits | 75–88 | 75, 77, 78 (s1 §1), 80, 81 (s1 §4), 82–83 | 78–79 (s1 §1) |
| 5 Hops | 89–110 | 89, 93–95, 100–101, 104 (s1 §6), 107 (s1 §6) | 92, 102, 104–106 (s1 §6) |
| 6 Yeast | 111–130 | 111, 113, 120, 122–123 | – |
| 7 Yeast management | 131–154 | 131, 140–142, 145, 152 | 134 (s1 §4) |
| 8 Water, extract | 155–164 | 155, 160, 162 | 161 |
| 9 Full-volume boil | 165–178 | 165–166, 176 (s1 §5) | – |
| 10 Priming | 179–196 | 179, 184–187, 193–194 | 183 |
| 11 Lager | 197–206 | 197, 201, 205 | – |
| 12 Strong beers | 207–216 | 207, 209–210, 213 | – |
| 13 Fruit, spices | 217–230 | 217–219, 221–225, 227–228 | – |
| 14 Sour beers | 231–246 | 231, 233–234, 238–242 | – |
| 15 Malt, adjuncts | 247–264 | 247, 251, 263 | – |
| 16 Mash | 265–284 | 265, 268, 275 | – |
| 17 Mashing methods | 285–304 | 285, 289, 291, 293 | 292, 294–297, 300–301 |
| 18 Extraction, yield | 305–322 | 305, 307, 309, 312, 314 (s1 §1), 315 (adjuncts), 317 (s1 §2) | 311 (s1 §3), 314 (s1 §1), 316 (s1 §1), 317 (s1 §2), 318 (s1 §1), 319–321 |
| 19 Lautering | 323–340 | 323, 328–329, 333–338 | 329–331 |
| 20 First all-grain | 341–358 | 341, 344–345, 357 | 353 |
| 21 RA, mash pH | 359–382 | 365, 370–371, 373, 377, 380–381 | 360, 363, 368–370, 374 |
| 22 Water for style | 383–400 | 383–384, 388, 391, 394–397 | 392–396 |
| 23 Styles, recipes | 401–452 | 401, 406–423, 425–451 | – |
| 24 Developing recipes | 453–466 | 453, 462 (s1 §4; adjuncts), 463–464 | – |
| 25 Is my beer ruined | 467–486 | 467–468 | – |
| App A hydrometers | 487–492 | 487, 490, 491 (s1 §3) | 489 |
| App B colour | 493–502 | 493, 494 (s1 §7), 496 (s1 §7), 498 (s1 §7), 499 (s1 §7) | – |
| App C clarity | 503–510 | 503, 509 | – |
| App D chillers | 511–520 | 511, 515–516 | – |
| App E lauter tun | 521–538 | 521 | – |
| App F sparging | 539–552 | 539, 545–547 | 542–543 |
| App G metallurgy | 553–564 | 553 | – |
| App H conversions | 565–572 | 565, 567–570 | – |
| App I gluten-free | 573–578 | 573 | – |

Marks: `(s1 §n)` = the page is covered by section n of the `s1-maths`
[doc-calc.md](finished/s1-maths/doc-calc.md) (checked against the book pages that file cites,
printed page + 26 = PDF page); `(adjuncts)` = `adjunct-fermentables` read it. Section 3 (SG ↔ °P)
read table A.2 (p. 491) only to compare it with the formula, and it is not a source. **Pages with
no mark are not passed yet.** Their owner is m7-process for chapters 8 and 16–22 and Appendices
D–F (water, pH, mash and process tables); the other chapters have no owner yet. The mapping is by
the cited page only: s1-maths may also use a figure from a marked page's neighbour that the
loader did not flag (unverified).

### *Water*

Nothing is passed yet: no formula or table from this book is in `ref` or code. Its tables
(water profiles, acid doses, salt contributions, malt acidity data) and formulas (residual
alkalinity, mash pH prediction, salt and acid calculations in Appendix C) go to m7-process, with
the water chemistry of *How to Brew* chapters 8, 21 and 22. The seven salts already in
`ref.water_salt` come from IUPAC atomic masses, not from this book.

Pages where the loader cut a markdown table or Docling left a formula placeholder, by chapter
(59 table pages and 14 formula pages outside the skipped ranges, measured 2026-10-16; the formula
list is by the chunk's first page):

| Chapter | PDF pages | Table pages | Formula pages |
|---|---|---|---|
| 1 A whole book on brewing water | 19–30 | – | – |
| 2 Where your water comes from | 31–41 | 34 | – |
| 3 How to read a water report | 42–62 | 42–43, 45–46, 58–59, 61 | – |
| 4 Residual alkalinity and the mash | 63–75 | 66–68, 70–71, 74–75 | 66–67, 70 |
| 5 RA, malt acidity, mash pH | 76–97 | 79–80, 85–86 | – |
| 6 Controlling alkalinity | 98–126 | 103–106, 108–114, 125 | 103, 105, 108–111 |
| 7 Adjusting water for style | 127–156 | 128–131, 136–141, 151–152, 156 | 151 |
| 8 Source water treatment | 157–176 | 162, 169–170 | 169 |
| 9 Brewery process waters | 177–189 | 183–184 | 183 |
| 10 Wastewater treatment | 190–204 | 191–192, 197 | – |
| App A chemistry glossary | 205–216 | – | – |
| App B acidification | 217–227 | 219 | – |
| App C ion, salt, acid calculations | 228–234 | 231–233 | 231–232 |
| App D charge balance | 235–237 | 235–237 | – |

The pages that matter most for m7-process are chapters 4–7 and Appendices B–D. Docling marks few
formulas, so most equations are still in the prose, undecoded (unverified).

### *Yeast*

Nothing is passed yet: no formula or table from this book is in `ref` or code. Its tables (strain
overviews, nutrient and aeration data, pitching-rate and propagation tables, lab media recipes,
the troubleshooting charts) go to m7-process and the later yeast work; `ref.yeast` comes from the
shop's catalogue and the makers' sources, not from this book.

Pages where the loader cut a markdown table or Docling left a formula placeholder, by part (52
table pages and 2 formula pages outside the skipped ranges, measured 2026-10-16; the contents
pages 4–11 were cut too but are skipped; the formula list is by the chunk's first page):

| Part | PDF pages | Table pages | Formula pages |
|---|---|---|---|
| 1 Importance of yeast and fermentation | 22–37 | – | – |
| 2 Biology, enzymes, esters | 38–61 | 45–46, 49–50, 53–55 | 45, 55 |
| 3 Choosing the right yeast | 62–85 | 73–76, 78–79 | – |
| 4 Fermentation | 86–141 | 100–103, 117, 124–128 | – |
| 5 Yeast growth, handling, storage | 142–193 | 150–151, 161–164, 187–188 | – |
| 6 Your own yeast lab | 194–281 | 213–214, 230–235, 242–245, 248–249, 266 | – |
| 7 Troubleshooting | 282–304 | 299–304 | – |

Pages 299–304 are the troubleshooting charts (problem-by-factor grids), cut whole; their
captions stay in `kb`. Docling marks few formulas, so most equations are still in the prose
(unverified).

### *Malt*

Nothing is passed yet: no formula or table from this book is in `ref` or code. Malt data (colour,
extract, diastatic power per malt) comes from the maltster catalogues, not from this book's
Appendix A listing, which was cut as tables. The grain-bill and colour-calculation tables in
chapter 2 (MCU, SRM) are covered by `s1-maths` colour (Morey), not by this book.

Pages where the loader cut a markdown table, by chapter (29 table pages in total, 27 outside the
skipped ranges 1–16 and 263–335, measured 2026-10-16; Docling left no formula placeholder in the
kept pages). Chapter page ranges are read from the page headers (unverified at the boundaries):

| Chapter | PDF pages | Table pages | Formula pages |
|---|---|---|---|
| 1–6 | 25–135 | 37–40 (ch. 2, grain bill and colour calculations) | – |
| 7 Malt family descriptions | 136–149 | 148–149 (flavour descriptor lists) | – |
| 8–12 | 150–231 | – | – |
| App A commercially available malts | 232–248 | 232–248 | – |
| App B malthouse capacities | 249–251 | 249–250 | – |
| App C craft maltsters | 252–253 | 252–253 | – |
| App D home malting | 254–262 | – | – |

### *BJCP Beer Exam Study Guide*

Nothing is passed yet. The §IV.B water table (famous brewing waters, ion levels, PDF pages 46–48)
goes to m7-process with the water chemistry of *How to Brew* and *Water*. The style-triple table
of question S0 (PDF page 21) is in the skipped sections and is `s6-style-neighbours` data.

Table pages in the kept range 46–77: 46, 47, 48 (section IV.B Water). Formula pages: 46 (one
placeholder in the same section; measured 2026-10-16).
