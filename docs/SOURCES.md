# Source files: where each one lives and what it is for

Every file under `shared/rag-files/` (git-ignored, so only this list is versioned), what it is,
and its **fate**: how the project uses it and in which work item. Decided 2026-10-16, after all
of them were read. PROJECT.md §5 summarises; this file has the per-file detail.

## Fates

| Fate | Meaning |
|---|---|
| **kb** | Prose is chunked and embedded into `kb.chunk` for cited retrieval (tables are cut, DATABASE.md §4) |
| **calc** | A doc → calc pass turns its tables, formulas or measurements into data or code (PROJECT.md §6.7) |
| **check** | Used only to check something already built; nothing from it enters `ref` or `kb` |
| **oracle** | Run by hand to get expected values for tests; its formulas are not copied |
| **loaded** | Already loaded into `ref` |
| **later** | Kept for a Priority 2 feature; no work item uses it yet |
| **copy** | A readable copy of text that another file in this list already covers; not used on its own |

A file can have more than one fate (most books are calc first, then kb).

## Source priority (user rule, 2026-10-28)

For any question of brewing methodology, *How to Brew* (`books/how_to_brew.pdf`, 2017, the newest of
the books) is the only source of truth if it covers the point. *Water* (2013), *Yeast* (2010), the
BJCP study guide, the articles and web pages are used only where it is silent. Each value in
`app.*` output and in the `doc-calc.md` of the work says its source. Example (m7-process): mash pH,
pitch rate, diacetyl rest and dry-hop figures come from *How to Brew*; the style → water rows from
*Water* (HTB gives none); Berliner Weisse and honey beer water from the web (below).

## Web sources used for calculation values

Fetched or searched 2026-10-28 for [`m7-process`](work/m7-process/doc-calc.md) §4b. None is saved under
`shared/rag-files/`; they are cited by URL and carry no licence. "Search text only" means the page itself
was not read (or held nothing relevant) and only the search result's summary was seen.

| URL | Used for | Read |
|---|---|---|
| https://brewersfriend.com/homebrew/recipe/print/1109903 | Berliner Weisse target profile Ca 48, Mg 3, Na 0, Cl 47.7, SO₄ 50, HCO₃ 0 | fetched |
| https://forum.homebrewersassociation.org/t/water-profile-wheat-hefe/28606 | Bru'n Water users and M. Brungard: Ca 40-50, SO₄/Cl low, mash pH 5.4 or less; K. Troester (quoted): Weissbier RA about 0, Ca 50, SO₄ 57, Cl 43 | fetched |
| https://learningtohomebrew.com/?p=513155 | "soft water, balanced chloride:sulfate, keep both low" | search text only (the page held no water text) |
| https://brewersfriend.com/homebrew/recipe/print/745992 | Ca 100, Cl 50, SO₄ 100: **not used**, the stored profile is a Helles profile | fetched |
| https://brewersfriend.com/homebrew/recipe/print/14426 | a lambic profile (Ca 31, Cl 25, SO₄ 20): **not used**, a lambic, not a Berliner | fetched |
| https://getollie.com/blog/blonde-ale-brewing-guide | blonde ale water: Ca 50-100, Cl 50-75, SO₄ 50-100 (Newman, Maui Brewing); no carbonation figure | fetched |
| https://shop.theelectricbrewery.com/pages/water-adjustment | blonde ale target Ca 50, Mg 10, Na 16, Cl 70, SO₄ 70 | search text only |
| https://www.homebrewtalk.com/threads/thoughts-on-water-profile-for-honey-ale.410384/post-5186504 | one brewer's honey ale water; "50 ppm Ca from calcium chloride" | search text only (HTTP 403); not used for a value |

No source found for a honey-specific water profile or honey beer carbonation.

## Folders

| Folder | Holds |
|---|---|
| `books/` | Whole books and long guides |
| `styles/` | Style guidelines (structured) and style study aids |
| `hopline/` | The hopline.hu shop data (loaded) |
| `maltsters/` | Maltster catalogues and the substitution chart (loaded) |
| `water/` | Water-chemistry references and the Bru'n Water spreadsheet |
| `sensory/` | Off-flavour lists, sensory lexicons, the flavour wheel, the Cicerone syllabus |
| `articles/` | Blog posts, wiki pages and short papers, saved as Markdown or PDF |
| `recipes/` | The Brewer's Friend dump (set aside, D7) |

Web pages were saved on 2026-10-16 as Markdown with their source URL in the header; reader
comments, site menus and sidebars were left out.

## Files

### `books/`

| File | What | Licence | Fate | Used by |
|---|---|---|---|---|
| `how_to_brew.pdf` | Palmer, *How to Brew*, 4th ed. 2017 | © Brewers Publications | loaded · calc · kb | s1-maths, adjunct-fermentables (done); m7-process (water, mash, carbonation chapters); s4-books-kb |
| `obc_recipe_formulation.pdf` | Oregon Brew Crew, *Recipe Formulation* | free | calc | s1-maths (done) |
| `palmer_kaminski_water.pdf` | Palmer & Kaminski, *Water* (273 pp) | © Brewers Publications | calc · kb | m7-process step 12; s4-books-kb |
| `white_zainasheff_yeast.pdf` | White & Zainasheff, *Yeast* (325 pp) | © Brewers Publications | calc · kb | m7-process step 14 (pitch rate, schedules); s4-books-kb |
| `mallett_malt.pdf` | Mallett, *Malt* (335 pp) | © Brewers Publications | kb | s4-books-kb. No calc: the malt data comes from the maltster catalogues |
| `bjcp_exam_study_guide_2017.pdf` | BJCP Beer Exam Study Guide, Dec 2017 (2015 guidelines), 77 pp | © BJCP, free | check · calc · kb | s6-style-neighbours (the 91 S0 style triples); m7-process (8-city water table, §IV.B); s4-books-kb (§IV only: sections I–III, exam rules and procedures, go in `skip_pages`); m8 (T14 recipe checklist) |

### `styles/`

| File | What | Licence | Fate | Used by |
|---|---|---|---|---|
| `styles.json` | BJCP 2021, 116 styles | © BJCP | loaded | style-loader (done) |
| `ba_styles.json` | Brewers Association 2026, 169 styles | © BA | loaded | style-loader (done) |
| `bjcp_2021_introductions.md` | The three BJCP 2021 introductions (guidelines, beer styles incl. glossary and colour reference, specialty-type beer incl. entry rules and "best fit") | © BJCP | check · kb | s6-style-neighbours (base style vs specialty rule); s7-kb-articles |
| `barnes_bjcp_style_flashcards_2011.pdf` | T. Barnes, *BJCP Style Flashcards*, c. 2011: BJCP **2008** guidelines as a sensory grid per style, 73 styles | personal and non-profit use | check | s6-style-neighbours (cross-check of the s3 envelopes). Never kb: 2008 numbers and codes would contradict 2021 |
| `bjcp_2008_style_comparison.pdf` | What sets neighbouring BJCP **2008** styles apart, 4 pp | unstated | check | s6-style-neighbours (words for the triple briefs). Never kb, as above |

### `water/`

| File | What | Licence | Fate | Used by |
|---|---|---|---|---|
| `brunwater_water_knowledge.md` | Brungard, Bru'n Water *Water Knowledge* (~17,000 words, updated 2020) | © Martin Brungard, all rights reserved | calc · kb | m7-process step 12; s7-kb-articles; m4: default profile ions (§4.2.1) |
| `brunwater_1.25.xlsx` | Bru'n Water 1.25 spreadsheet (free edition, sheets protected) | © Martin Brungard, all rights reserved | oracle | m7-process step 12: expected salt and mash-pH values for test cases, entered by hand. Its formulas are not copied |
| `bjcp_study_guide_water.md` | Web edition of the study guide's *Water* page (same 2017 text, 8-city ion table checked against the PDF) | © BJCP | copy | readable copy of the table for m7-process |

### `sensory/`

| File | What | Licence | Fate | Used by |
|---|---|---|---|---|
| `bjcp_study_guide_beer_characteristics.md` | Web edition of the study guide's *Beer Characteristics*: 25 characteristics with causes and fixes | © BJCP | copy · later | Same text as the PDF §IV.G (kb through s4). Source for `ref.fault` (Priority 2) |
| `bjcp_beer_fault_list_2012.pdf` | AHA/BJCP fault list: 24 faults, descriptors and fixes, 1 p | © BJCP | later | `ref.fault` (Priority 2), with the file above. Replaces the lost `beer_faults.json` |
| `ych_beer_sensory_ballot_2026.pdf`, `ych_hop_sensory_ballot_2026.pdf` | Yakima Chief Hops sensory ballots (V2, Feb 2026): aroma categories, each with its descriptors, plus off-notes and taste and mouthfeel scales | © YCH | check | `loaders/style_fit_vocab.toml`: a reference when `loaders.tags` flags an unknown hop word (of 107 words on the beer ballot, 22 are already in the vocabulary; most of the rest are descriptors the shop texts do not use, measured 2026-10-16) |
| `beer_flavour_wheel.pdf` | Beer flavour wheel (text layer is scrambled) | unstated | later | Vocabulary reference only |
| `cicerone_cbs_syllabus_v6.pdf` | Cicerone Certified Beer Server syllabus v6 (2024), 16 pp | © Cicerone | later | Serving and off-flavour basics (Priority 2) |

### `articles/`

| File | What | Licence | Fate | Used by |
|---|---|---|---|---|
| `braukaiser_mash_parameters_2009.pdf` | Troester, *Effects of mash parameters on attenuation and efficiency*, 23 pp: limit of attenuation vs mash temperature, time, pH, crush, thickness | CC BY-NC 3.0 | calc · kb | calc done by s5-mash-attenuation ([doc-calc](finished/s5-mash-attenuation/doc-calc.md)); s7-kb-articles |
| `braukaiser_mash_time_fermentability.md` | Troester, *Mash Time Dependency of Wort Fermentability* (wiki) | braukaiser.com | calc · kb | calc done by s5-mash-attenuation ([doc-calc](finished/s5-mash-attenuation/doc-calc.md)); s7-kb-articles |
| `terrill_observations_on_attenuations.md` | Terrill, *Observations on Attenuations* (2017): 44 batches, 3 strains, attenuation vs mash temperature; the plots are images, not saved | seanterrill.com | calc · kb | calc done by s5-mash-attenuation ([doc-calc](finished/s5-mash-attenuation/doc-calc.md); strain dependence not modelled); s7-kb-articles |
| `janish_dry_hop_best_practices_tq_2021.pdf` | Janish, *Dry Hop Best Practices*, MBAA TQ 58(1) 2021, 8 pp, posted by the author with MBAA's permission | © MBAA | calc · kb | m7-process step 14 (dry-hop timing and temperature); s7-kb-articles |
| `janish_short_cool_dry_hopping.md` | Janish, *A Case for Short and Cool Dry Hopping* | scottjanish.com | calc · kb | m7-process step 14; s7-kb-articles |
| `janish_survivables_hot_side.md` | Janish, *Survivables: Unpacking Hot-Side Hop Flavor* | scottjanish.com | kb | s7-kb-articles; cited by m5 step 8 and m8 (no hop oil data in `ref` to compute from) |
| `janish_ph_hoppy_beers.md` | Janish, *A Look at pH in Hoppy Beers* | scottjanish.com | kb | s7-kb-articles |
| `janish_coffee_beers.md` | Janish, *Guide to Coffee Beers* (infusion experiments) | scottjanish.com | kb | s7-kb-articles; m5 step 9 extras |
| `mtf_berliner_weissbier.md` | Milk The Funk wiki, *Berliner Weissbier* | not stated on the page | calc · kb | m7-process (b14 souring schedule); m5 open question on Lactobacillus; s7-kb-articles |
| `mtf_lactobacillus_fermentation.md` | Milk The Funk wiki, *Lactobacillus Fermentation* | not stated on the page | calc · kb | as above |

### `hopline/`, `maltsters/`, `recipes/`

Unchanged: loaded into `ref` (hopline, maltsters) or set aside (recipes, D7). See PROJECT.md §5.

## Not saved

- The study guide's web pages on wort production, hops, malt and yeast: same text as the PDF §IV,
  which s4 ingests.
- Scott Janish's "What We Know About Dry Hopping": not found on his site (2026-10-16).
- Milk The Funk's *Kettle Souring* page: empty on the wiki (2026-10-16).
