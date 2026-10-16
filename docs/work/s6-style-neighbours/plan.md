# S6 · Neighbouring styles: step 2 checks and an envelope cross-check — implementation plan

Stage: verify
Brief: [brief.md](brief.md)
Branch: s6-style-neighbours

## Approach
Three separate outputs, none of which changes step 2:

1. **Check set and runner.** One TOML file, `evals/style_neighbours.toml`, holds the 91 study-guide
   triples (study-guide id, names as printed, BJCP 2021 codes) and 83 briefs (one per distinct
   code). Each brief is the user's sentence plus the step 1 brief it should produce: `named` empty,
   1–2 `stated` numbers, 2–4 descriptive words split into `hints` (step 1's hint words) and
   `unknown` (any other word, as step 1 files words that fit no field). Tests check the set
   against the study guide and against `ref.beer_style`. `evals/style_neighbours.py` sends each
   brief to `app.step2_best_style(brief, request, 'any')` in two runs and reports right-first,
   top 3 and the confusions per triple for both, side by side, with the gap. No pass bar
   (decision 2).
   - **Run A**: the brief as written, `named` empty. All 83 briefs.
   - **Run B**: the same brief with the triple's family noun as `named`. Only briefs in a triple
     whose three styles share one family (measured 2026-10-16: 50 triples, 61 briefs); the other
     41 triples run only in A and are marked `mixed` and counted.
2. **Specialty-entry note.** A short markdown note comparing the BJCP 2021 *Introduction to
   Specialty-Type Beer* with the D1 base-style rule; any change is put to the user.
3. **Envelope cross-check.** A report, written by hand from the Barnes flashcards, of every
   dimension where a 2008 card differs from one of the 21 envelopes that have a 2008 counterpart.
   The user decides each one; agreed changes go into `loaders/style_envelopes.toml` and are loaded
   with the s3 flow.

**Guide `any`** (user, "1b"): the pipeline default. Step 2 itself returns a BA winner that has a
BJCP pair as that pair; a BA code that comes back as the pick counts as a miss and is named
(`BA <code>`). For top 3, the runner reads the first three `candidates` and writes a BA code as its
BJCP pair by the same rule step 2 uses (`app.style_pair()`, pair not in `app.bjcp_catch_all()`).

**Family noun** (user, "2c"). A style's family comes from its BJCP 2021 family tag in
`ref.beer_style.raw` (`app.style_tags`), turned into the noun a user would write:
amber-ale, brown-ale, pale-ale, strong-ale → `ale`; amber-lager, dark-lager, pale-lager, pilsner →
`lager`; bock → `bock`; ipa → `ipa`; porter → `porter`; stout → `stout`; wheat-beer → `wheat`.
The tags `bockfamily` and `dark-lagerfamily` (typos in the data) read the same; `specialty-family`
is ignored. Styles with no family tag (23B, 23C, 25A–26D) have no noun. A triple is single-family
when one noun fits all three styles; that noun is stored on the triple. BJCP files lambics and
Berliner Weisse under wheat-beer, so their noun is `wheat`; that is BJCP's grouping, kept as is.

**How `named` scores, and so how to read Run B** (measured 2026-10-16, `db/022_step2.sql` step 2):
`named` is a boost, not a filter. Every style gets `4 × app.style_name_score(named, name,
aliases)`: the share of the style's name words matched times the share of named words found. A
family noun therefore lifts only styles whose *name* holds the word, and unevenly: "stout" adds 2
to Irish Stout but 1.33 to Foreign Extra Stout; "bock" adds 2 to Helles Bock and Dunkles Bock and
0 to Doppelbock and Eisbock; "wheat" lifts only American Wheat Beer; "lager" lifts neither German
Pils nor Munich Helles; "ale" lifts 24 BJCP styles. Run B is step 2's real behaviour when a user
writes a family word, not a pick restricted to the family. To make that visible, Run B's per-triple
lines show each style's name score for the noun next to the pick.

**The request text** never holds a style name, alias or family noun (R1 applies to Run A's text).
With the guide passed, step 2 does not read the request at all; it documents what the brief stands
for. Run B passes the same request; the family noun enters only as `named`.

## Files
| Path | New / changed | Purpose |
|---|---|---|
| `evals/style_neighbours.toml` | new | 91 `[[triple]]` and 83 `[[brief]]` (R1, R2) |
| `evals/style_neighbours.py` | new | runner: `python -m evals.style_neighbours [--save]` (R3) |
| `tests/test_style_neighbours.py` | new | check-set tests (A1, A2) and runner unit tests |
| `evals/results/<date>-s6.json` | new | first measured run (R3, R4) |
| `docs/work/s6-style-neighbours/specialty-entry.md` | new | 2021 specialty-entry text vs D1 (R7) |
| `docs/work/s6-style-neighbours/envelope-crosscheck.md` | new | Barnes 2008 vs the 21 envelopes, with the user's decisions (R5) |
| `loaders/style_envelopes.toml` | changed (only if the user agrees to changes) | agreed envelope fixes (R6) |
| `PROJECT.md` | changed | §8 lines; §5 study-guide and 2008-aids status text |

`db/022_step2.sql` must not change (A4).

## Tasks

### Task 1: The 91 study-guide triples, with their BJCP 2021 codes
Why: R1, A1 (the triples and the 83 styles everything else is built on).
- [x] Extract the S0 table from `shared/rag-files/books/bjcp_exam_study_guide_2017.pdf` (pages
      30–33 as printed; `pdftotext -layout` into the scratchpad, never into the repo). IDs run 1–110;
      19 are "Pairing removed": 8, 19, 20, 33, 36, 40, 43, 45, 55, 72, 83, 97–104. 91 remain.
- [x] Create `evals/style_neighbours.toml`. Header comment: what the file is, the source (study
      guide 2017, question S0, 91 triples), that briefs paraphrase the BJCP 2021 guidelines, the
      fields, and "checked by `tests/test_style_neighbours.py`". One `[[triple]]` per remaining ID:
      `id` (integer, the study-guide ID), `names` (three strings exactly as printed, accents kept),
      `codes` (three BJCP 2021 codes in the same order), `family` (the shared family noun, or
      `""` when the styles span families; rule in Approach, written into the header comment).
      Codes are by name in `ref.beer_style` (guide `BJCP`), accents folded (Märzen = Marzen 6A,
      Kölsch = Kolsch 5B), except four names mapped by hand: `Vienna` → 7A Vienna Lager,
      `English Barleywine` → 17D English Barley Wine, `Trappist Single` → 26A Belgian Single,
      `Belgian IPA` → 21B Specialty IPA (Belgian IPA is one of its types).
- [x] Write `tests/test_style_neighbours.py` with:
      `test_triples_are_the_91` (91 triples, ids unique, none of the 19 removed ids, each with 3
      names and 3 distinct codes), `test_83_distinct_styles` (the union of codes has 83 members),
      and stack test `test_triple_names_match_2021` (every name, accent-folded and case-folded,
      equals the `ref.beer_style` name of its code, except the four hand-mapped names above, which
      must map to exactly those codes); stack test `test_triple_family_from_2021_tags` (each
      `family` equals the noun derived from the three styles' 2021 family tags by the Approach
      mapping, `""` when none is shared; expect 50 single-family and 41 mixed triples);
      `test_family_is_a_family_word_only` (A1: every non-empty `family` is one of ale, lager, bock,
      ipa, porter, stout, wheat; stack: it is no BJCP 2021 style name and no alias, after
      `app.style_words`); `test_one_family_per_style` (a style in several single-family triples
      gets the same noun in each).
- [x] Run `.venv/bin/pytest tests/test_style_neighbours.py`, expect all to pass.
- [x] PROJECT.md §8 line.
Done when: the tests pass.
Commit: `Add the 91 BJCP exam style triples`

### Task 2: One brief per triple style (83)
Why: R1, R2, decision 1 (A1, A2).
- [x] Add 83 `[[brief]]` to `evals/style_neighbours.toml`, one per distinct code, ordered by code.
      Fields: `code`, `partners` (sorted codes of every style that shares a triple with it),
      `request`, `named = ""`, `stated` (table, keys only from `abv`, `og`, `ibu`, `srm`),
      `hints` (only words from step 1's hint list: bitter, hoppy, juicy, dry, crisp, full, chewy,
      malty, darker, stronger, session), `unknown` (the other descriptive words, one word each).
- [x] How to write each brief (put these rules in the header comment, R2):
      - one or two stated numbers, each inside the style's BJCP 2021 range in `ref.beer_style`;
        pick the number that sets it apart from its partners where one does (Scottish Light vs
        Heavy vs Export by ABV, Helles Bock vs Doppelbock by OG);
      - two to four descriptive words, each taken from the style's own 2021 entry in
        `ref.beer_style.raw` (overall impression, aroma, appearance, flavor, mouthfeel, comments,
        style comparison, characteristic ingredients, tags); prefer words that set it apart from
        its partners. `shared/rag-files/styles/bjcp_2008_style_comparison.pdf` may suggest which
        words do, but a word is used only if it is also in the 2021 entry;
      - a word of 4 letters or more for `unknown` (step 2 drops shorter ones, `app.brief_words`);
        no negated words ("not sweet");
      - the request is one sentence a user would write, holding the numbers and words and
        nothing that names the style: no BJCP 2021 style name or alias, no study-guide name, no
        family noun (the list in `test_no_style_name_in_request`);
      - paraphrase only; no phrase of more than a few words copied from the guidelines.
- [x] Add to `tests/test_style_neighbours.py`:
      - `test_one_brief_per_triple_style` (A1): brief codes are unique and equal the 83 triple codes;
      - `test_partners_match_triples` (A1): each `partners` equals the derivation from `[[triple]]`;
      - `test_brief_shape` (A2): `named` is empty; 1–2 `stated` keys, all in abv/og/ibu/srm;
        `hints` within the hint list; 2–4 words in `hints` + `unknown`, each one lower-case word
        (`^[a-z][a-z-]*$`); every word and every stated number (`f"{v:g}"`) is found in the request;
      - stack `test_stated_numbers_in_2021_range` (A2): each stated value lies in the style's
        numrange (`select %s::numeric <@ abv` etc.);
      - stack `test_words_from_2021_entry` (R2): each word scores > 0 in
        `app.style_word_score(array[word], app.style_tags(raw), <all raw text fields above>)`
        for its own style (same stem rule step 2 uses);
      - stack `test_no_style_name_in_request` (A1, Run A text): the accent-folded, lower-cased request holds no
        BJCP 2021 style name and no alias from `app.style_alias()` as a phrase, nor its own
        study-guide name, nor (as a whole word) a family noun from a list in the test: stout,
        porter, bock, lager, ale, ipa, pils, pilsner, weisse, weissbier, weizen, lambic, gueuze,
        barleywine, saison, kolsch, helles, dunkel, marzen, festbier;
      - stack `test_briefs_fit_step1_contract`: each built brief (the runner's `step1_brief()`,
        Task 3, or the same dict built here until then) has no errors from
        `extensions.jsonschema_validation_errors` against `shared/contracts/step1.output.schema.json`
        (as `tests/test_contracts.py` does).
- [x] Run `.venv/bin/pytest tests/test_style_neighbours.py`, expect all to pass. Do not run step 2
      on the briefs while writing them (the set must not be fitted to the scorer).
- [x] PROJECT.md §8 line.
Done when: 83 briefs exist and every test above passes.
Commit: `Add 83 style-neighbour briefs`

### Task 3: Runner and the first measured run
Why: R3, R4 (A3, A4).
- [x] Create `evals/style_neighbours.py` (`python -m evals.style_neighbours [--save]`), modelled on
      `evals/retrieval.py`. Functions, each small and readable:
      - `load()` → triples and briefs from the TOML;
      - `GUIDE = "any"`, a named constant with a one-line why;
      - `step1_brief(b, family=None)` → the step 1 brief dict: `named` = `family` (None in Run A),
        `stated`, `hints`, `unknown`, `wanted`/`excluded`/`inventory` empty lists, `guidance` true;
      - `run_b_family(triples)` → code → family noun, for every style in a single-family triple;
      - `measure(conn, b, family=None)` → `{code, picked, top3, right_first, in_top3}` from
        `select app.step2_best_style(%s::jsonb, %s, %s)`: `picked` is `style.code`, written
        `BA <code>` when `style.guide` is BA, None when step 2 returns no style; `top3` the first
        three `candidates`, a BA code written as its BJCP pair (`app.style_pair()`, pair not in
        `app.bjcp_catch_all()`, read once per run) or else `BA <code>`;
      - `summarise(results)` → n, right-first share, top-3 share, count with no style, count of BA
        picks;
      - `confusions(triples, results)` → per triple, for each of its three styles: `ok`, the
        partner code picked instead, or `other <code>` (BA picks named) / `none`;
      - `name_scores(conn, family, codes)` → per style, `app.style_name_score(family, name,
        aliases)` (aliases from `app.style_alias()`), shown on Run B's triple lines;
      - `main()` prints the guide, then a side-by-side table: Run A on all 83, Run A on the Run B
        briefs, Run B, and the gap B − A on those same briefs (right-first and top 3, as `x/n` and
        %); then one line per triple with A's confusions and, for single-family triples, B's
        confusions and name scores; `mixed` triples are marked "A only" and counted.
        `--save` writes `evals/results/<date>-s6.json` (guide, both summaries, the gap, per-brief
        results of both runs, per-triple confusions, the mixed count).
      No pass bar and no exit code on the numbers (decision 2).
- [x] Unit tests in `tests/test_style_neighbours.py` (no stack, hand-made results):
      `test_summarise_first_and_top3` (right first counts only `picked == code`; top 3 counts the
      code in `top3`; a None pick and a `BA …` pick count as wrong),
      `test_confusions_partner_other_none` (a partner pick names the partner, a non-partner pick
      is `other`, a BA pick is `other BA <code>`, no style is `none`),
      `test_run_b_only_single_family` (`run_b_family` holds exactly the styles of triples with a
      non-empty `family`, 61 codes on the real file), `test_gap_on_same_briefs` (the gap compares
      Run A and Run B on the same codes, never A's 83 against B's subset).
      Stack tests: `test_measure_one_brief` (`measure()` returns all five keys, `picked` a code,
      `BA <code>` or None, at most 3 `top3`); `test_ba_candidate_written_as_pair` (a brief whose
      top candidates include a paired BA style shows the BJCP pair in `top3`; pick the brief by
      running step 2 in the test, not from a hard-coded score).
- [x] Run `.venv/bin/pytest tests/test_style_neighbours.py`, expect all to pass.
- [x] Run `.venv/bin/python -m evals.style_neighbours --save` once with the stack up. Do not
      change any brief after seeing the result (if a brief is found to break a Task 2 rule,
      fix it, re-run, and say so in a Deviations line).
- [x] Check A4: `git diff main -- db/022_step2.sql` is empty.
- [x] PROJECT.md §8 line with the measured numbers: Run A right-first and top 3 on 83; Run A and
      Run B on the Run B briefs and the gap; no-style and BA-pick counts; mixed triples (A only);
      the triples with the most confusions; the results path; and "no pass bar; tuning step 2 is
      decided from this result, not in this work".
Done when: the result file exists and its numbers are in PROJECT.md §8.
Commit: `Add style-neighbour runner and first run`

### Task 4: BJCP 2021 specialty-entry rules against D1 — may STOP
Why: R7 (A6).
- [x] Read `shared/rag-files/styles/bjcp_2021_introductions.md` (*Introduction to
      Specialty-Type Beer*: "Base Style", "Best Fit", the judging notes on base style) and the
      entry instructions of the specialty styles step 2 can pick (31B in `ref.beer_style.raw`,
      `app.specialty_style()` in `db/022_step2.sql`).
- [x] Write `docs/work/s6-style-neighbours/specialty-entry.md` (one page): the D1 rule as in
      PROJECT.md §5; what BJCP 2021 says, quoting short phrases only (< 15 words each);
      point by point agrees / differs (at least: base style by default; specialty when the
      ingredient is perceptible; base style declared as the alternative; specialty styles never
      a base style; which specialty adjuncts `app.specialty_style()` covers vs the
      Specialty-Type Ingredients BJCP lists); verdict.
- [x] If the verdict proposes a change to D1 or to step 2: return `needs-input` with the
      proposal as a question (options, recommendation). Change nothing in PROJECT.md §5 or
      `db/`. After the answer, record the decision in the note ("approved", or "declined" with
      the user's reason). A change the user approves is its own work item, not done here.
- [x] PROJECT.md §8 line (verdict and the user's decision if any).
Done when: the note exists with a verdict, and any proposal has the user's decision (A6).
Commit: `Add specialty-entry note for D1`

### Task 5: Barnes 2008 cross-check report — STOP
Why: R5 (A5).
- [x] The 21 envelopes and their 2008 cards (all found in
      `shared/rag-files/styles/barnes_bjcp_style_flashcards_2011.pdf`, checked 2026-10-16):
      10A↔15A Weizen/Weissbier, 11B↔8B Special/Best/Premium Bitter, 15A↔9D Irish Red Ale,
      15B↔13A Dry Stout, 16A↔13B Sweet Stout, 16B↔13C Oatmeal Stout, 17C↔9E Strong Scotch Ale,
      18A↔6B Blonde Ale, 18B↔10A American Pale Ale, 19C↔10C American Brown Ale,
      1B↔1B Standard American Lager, 1C↔6A Cream Ale, 20B↔13E American Stout,
      20C↔13F Russian Imperial Stout, 21A↔14B American IPA, 23A↔17A Berliner Weisse,
      25B↔16C Saison, 26B↔18B Belgian Dubbel, 5D↔2A German Pilsner (Pils),
      6A↔3B Oktoberfest/Märzen, 8B↔4C Schwarzbier. Not compared: 21C, 31B, and the three BA styles.
- [x] For each pair, read the card (`pdftotext -layout` of its page into the scratchpad) and the
      style's `[[style.sensory]]` rows. Map the card to the envelope dimensions: aroma and flavour
      malt → `malt` (roast and caramel characters → `roast`, `caramel`), aroma hops → `hop_aroma`,
      hop flavour → `hop_flavour`, yeast fruit → `esters`, yeast spice/clove → `phenols`,
      finish → `dryness`/`sweetness`, body → `body`; sourness, brett and spice where the card
      has them. Read Barnes' intensity words on the envelope scale with s3's rule R3
      (`docs/finished/s3-style-fit/envelope-review.md`): none, very low, low, medium-low,
      medium (= moderate), medium-high, high, very high. Characters: Barnes' words through
      `loaders/style_fit_vocab.toml` to tag names; a word with no tag is listed as such.
      Bitterness, colour, clarity, head and carbonation have no envelope dimension: skip them.
- [x] Write `docs/work/s6-style-neighbours/envelope-crosscheck.md`: the mapping rules above, then
      per pair a table of the dimensions that differ only: dimension · Barnes (2008) words ·
      envelope min–max and characters · the envelope's 2021 quote (short) · proposal ·
      decision (empty). A difference is: a min or max a step or more apart, a dimension on one side
      and not the other, or a character tag on one side and not the other. Proposal is one of
      *keep* (the 2021 quote supports the envelope; the 2008 text differs, a guideline change)
      or *change to …* (the 2021 quote supports Barnes, an envelope mistake), with one line why.
      A pair with no difference says so. End with a count of differences and proposed changes.
      Short words from the cards only; no 2008 numbers or codes go anywhere but this report.
- [x] Return `needs-input`: the report path and the proposed changes, asking the user to decide
      each difference (they may approve the proposals as a block and name exceptions). Change
      nothing in `loaders/style_envelopes.toml` before the answer.
- [x] After the answer: fill the decision column for every row.
- [x] PROJECT.md §8 line (pairs compared, differences, proposed and agreed changes).
Done when: every difference has the user's decision in the report (A5, first half).
Commit: `Add Barnes envelope cross-check report`

### Task 6: Apply the agreed envelope changes
Why: R6 (A5, second half).
- [x] If the user agreed to no change: write "No change agreed" in the report, skip the rest,
      and fold this task's §8 line into Task 5's commit.
- [x] Otherwise edit `loaders/style_envelopes.toml` for each agreed change, with a
      `# s6 fix N` comment matching the report row. Each changed row keeps `reviewed = true` on
      its style and a `quote` that is a phrase from the style's 2021 text (the s3 test
      `test_26_styles_reviewed` checks the quote is in `raw`). New character words need a tag
      name or a synonym in `loaders/style_fit_vocab.toml` (then `.venv/bin/python -m loaders.tags`).
- [x] Load twice: `.venv/bin/python -m loaders.style_envelopes`, then again.
- [x] Run `.venv/bin/pytest tests/test_style_envelopes.py tests/test_style_fit_golden.py
      tests/test_style_fit_recipe.py tests/test_style_level.py`, expect all to pass
      (`test_reload_is_identical` covers "loaded twice with identical results"). A golden case or
      reference-recipe line that fails is not fixed by editing the golden set: stop and return
      `needs-input` with the case, the change that broke it, and options (drop the change, or the
      user amends the case).
- [x] Run `.venv/bin/pytest`, expect all to pass.
- [x] PROJECT.md §8 line (changes applied, row counts of `ref.style_sensory` /
      `ref.style_character` before and after, golden set green); §5 row "BJCP 2008 style aids"
      status → done for s6.
Done when: the agreed changes are loaded and the full suite passes (A5).
Commit: `Apply agreed envelope fixes from Barnes check`

## Critical behaviour and its tests
| Behaviour | Test | Task |
|---|---|---|
| The triples and their codes match the study guide and `ref` (a wrong code makes every confusion wrong) | `test_triples_are_the_91`, `test_83_distinct_styles`, `test_triple_names_match_2021` | 1 |
| Each triple's family noun follows BJCP's family tags and is a family word only, never a style name | `test_triple_family_from_2021_tags`, `test_family_is_a_family_word_only`, `test_one_family_per_style` | 1 |
| No brief gives its style away by name or alias | `test_no_style_name_in_request`, `test_brief_shape` (`named` empty) | 2 |
| Every brief number and word comes from the style's 2021 entry, numbers in range | `test_stated_numbers_in_2021_range`, `test_words_from_2021_entry`, `test_brief_shape` | 2 |
| The briefs are valid step 1 output, so step 2 reads them as in the pipeline | `test_briefs_fit_step1_contract` | 2 |
| Right-first, top 3 and confusions are counted correctly; BA picks are misses and named | `test_summarise_first_and_top3`, `test_confusions_partner_other_none`, `test_measure_one_brief`, `test_ba_candidate_written_as_pair` | 3 |
| Run B covers only single-family triples, and the gap compares like with like | `test_run_b_only_single_family`, `test_gap_on_same_briefs` | 3 |
| Step 2 is unchanged | `git diff main -- db/022_step2.sql` empty | 3 |
| Envelope changes load the same twice, and the golden set and reference recipes stay green | `test_style_envelopes.py::test_reload_is_identical`, `test_26_styles_reviewed`, `test_style_fit_golden.py`, `test_style_fit_recipe.py` | 6 |

## Approved exceptions

## Deviations
- 2026-10-16 · Approach, Tasks 1 and 3: guide `any` instead of `bjcp` (BA picks are named misses,
  BA candidates in the top 3 read as their BJCP pair), and two runs side by side: A without and B
  with the triple's family noun as `named`, plus the gap; mixed triples A only, marked and counted.
  Triples get a `family` field from BJCP's 2021 family tags; how `named` scores is stated in the
  Approach — the user's answers "1b" and "2c" at plan review.
- 2026-10-16 · Task 2: `test_no_style_name_in_request` also bars the family noun `wheat` (it is a family noun in the Approach list, missing from the task's list). Words are checked through `app.brief_words` first, so a hint like `darker` is read as step 2 reads it (tag `dark-color`).
- 2026-10-16 · Tasks 1-3: 83 distinct styles and briefs, not 84 — the 84 counted printed names, and
  "Vienna" (hand-mapped) and "Vienna Lager" are both 7A. Run B stays at 61 briefs (measured).
- 2026-10-16 · Task 5: an envelope row that the 2008 card has no level for is listed as "card silent" and not counted as a difference; card tags that are parent or child of the envelope tag are not differences; differences are grouped (K1, K2, U, C1) so the user can decide by group — the plan's "dimension on one side only" rule would have counted rows with nothing to compare (implementation detail, no change to scope).
