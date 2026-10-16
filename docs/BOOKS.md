# Books in the knowledge base

The books are loaded into `kb.chunk` by [`loaders/books.py`](../loaders/books.py) (design:
[DATABASE.md](DATABASE.md) §4, work: [`s4-books-kb`](work/s4-books-kb/plan.md)). Only prose is
stored. Tables and formulas are cut out and go through the doc → calculation pass instead
(PROJECT.md §6.7). Page numbers are **PDF page numbers** (1-based), not the printed ones. For
*How to Brew* the PDF page is the printed page + 26.

## 1. Books in `kb`

| Slug | Book | File | PDF pages | Skipped pages | Chunks | Ingested |
|---|---|---|---|---|---|---|
| `palmer-how-to-brew` | *How to Brew*, Palmer & Kaminski, fourth edition 2017 | `books/how_to_brew.pdf` | 612 | 1–26 (cover, praise, contents, preface, acknowledgments, abbreviations), 579–612 (bibliography, index) | 943 (tokens min 32, median 273, max 514; measured) | 2026-10-16 |
| `palmer-kaminski-water` | *Water: A Comprehensive Guide for Brewers*, Palmer & Kaminski, 2013 | `books/palmer_kaminski_water.pdf` | 273 | 1–18 (cover, contents, figure list, acknowledgments, foreword), 238–273 (last table page, index) | 357 (tokens min 35, median 319, max 514; measured) | 2026-10-16 |

Docling's hybrid chunker made 1,276 chunks for *How to Brew*. 132 fell on the skipped pages and
201 had fewer than 20 words once tables and formula placeholders were cut, leaving 943. A second
ingest from a fresh Docling run gave the same 943 chunks and the same fingerprint
(`md5(string_agg(text, '|' order by page, section_path, text))` = `4d8d4941c1b14cb61ba6ee195a58cc6b`),
though the saved Docling JSON differs byte for byte between runs.

*Water* took 2.5 minutes in Docling and made 440 chunks. 52 fell on the skipped pages and 31 had
fewer than 20 words once tables were cut, leaving 357 (fingerprint `ef0c023d3add16d1339077690da3be1a`;
a second ingest from a fresh Docling run gave the same). The PDF page is the printed page + 18.
Its edition line is just `2013`: the copyright page gives the year and no edition number.

## 2. Adding a book

1. Put the PDF in `shared/rag-files/books/`.
2. Check it has a text layer: `pdffonts FILE` lists fonts. If it lists none, set `ocr=True` on the entry.
3. Add one `Book` entry to `BOOKS` in `loaders/books.py` (slug, title, edition, publisher, licence,
   `file_path`; read the first three from the PDF's copyright page, `pdftotext -f 4 -l 4 FILE -`
   usually shows it. The page may give only a year: use that as the edition).
4. Run `.venv/bin/python -m loaders.books <slug>`. A long book takes 10–20+ minutes in Docling; the
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
| 4 Kits | 75–88 | 75, 77–78, 80–83 | 78–79 |
| 5 Hops | 89–110 | 89, 93–95, 100–101, 104, 107 | 92, 102, 104–106 |
| 6 Yeast | 111–130 | 111, 113, 120, 122–123 | – |
| 7 Yeast management | 131–154 | 131, 140–142, 145, 152 | 134 |
| 8 Water, extract | 155–164 | 155, 160, 162 | 161 |
| 9 Full-volume boil | 165–178 | 165–166, 176 | – |
| 10 Priming | 179–196 | 179, 184–187, 193–194 | 183 |
| 11 Lager | 197–206 | 197, 201, 205 | – |
| 12 Strong beers | 207–216 | 207, 209–210, 213 | – |
| 13 Fruit, spices | 217–230 | 217–219, 221–225, 227–228 | – |
| 14 Sour beers | 231–246 | 231, 233–234, 238–242 | – |
| 15 Malt, adjuncts | 247–264 | 247, 251, 263 | – |
| 16 Mash | 265–284 | 265, 268, 275 | – |
| 17 Mashing methods | 285–304 | 285, 289, 291, 293 | 292, 294–297, 300–301 |
| 18 Extraction, yield | 305–322 | 305, 307, 309, 312, 314–315, 317 | 311, 314, 316–321 |
| 19 Lautering | 323–340 | 323, 328–329, 333–338 | 329–331 |
| 20 First all-grain | 341–358 | 341, 344–345, 357 | 353 |
| 21 RA, mash pH | 359–382 | 365, 370–371, 373, 377, 380–381 | 360, 363, 368–370, 374 |
| 22 Water for style | 383–400 | 383–384, 388, 391, 394–397 | 392–396 |
| 23 Styles, recipes | 401–452 | 401, 406–423, 425–451 | – |
| 24 Developing recipes | 453–466 | 453, 462–464 | – |
| 25 Is my beer ruined | 467–486 | 467–468 | – |
| App A hydrometers | 487–492 | 487, 490–491 | 489 |
| App B colour | 493–502 | 493–494, 496, 498–499 | – |
| App C clarity | 503–510 | 503, 509 | – |
| App D chillers | 511–520 | 511, 515–516 | – |
| App E lauter tun | 521–538 | 521 | – |
| App F sparging | 539–552 | 539, 545–547 | 542–543 |
| App G metallurgy | 553–564 | 553 | – |
| App H conversions | 565–572 | 565, 567–570 | – |
| App I gluten-free | 573–578 | 573 | – |

Which cut table or formula page belongs to which `s1-maths` section has not been mapped page by
page (unverified). The chapters that are water, pH and mash tables (8, 16, 21, 22) are the main
"not passed yet" ones.

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
