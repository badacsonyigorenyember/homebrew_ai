# S3 · Style fit: tags, envelopes and the level function — implementation plan

Stage: approved
Brief: [brief.md](brief.md)
Branch: s3-style-fit

## Approach

Four pieces, each with its own tests, built from data that exists (no corpus, D7):

1. **Tags (code, re-runnable).** `loaders/style_fit_vocab.toml` holds the hand-made part: the
   sensory dimensions with their class, the tag tree (origin · character · family) and the
   descriptor dictionary (Hungarian and English words → tag, ~150 words), plus a short list of
   known words that carry no character (*Semleges*, *keserű*, *komlós*). `loaders/tags.py`
   (`python -m loaders.tags`) loads that vocabulary into `ref.sensory_dimension`, `ref.tag` and
   `ref.tag_synonym`, then derives `ref.ingredient_tag` (`reviewed = false`) for every hop,
   fermentable and yeast from its own `ref` data. Unknown words are never guessed: the
   ingredient gets a row in the new `ref.ingredient_review` naming them.
2. **Envelopes (LLM offline, user review).** `loaders/style_envelopes.py --extract` sends each
   of the 26 styles' guideline prose (BJCP and BA alike, D9) to the D2 model, thinking off, with
   a JSON Schema as `format`. Code checks every answer (each quote is a verbatim piece of the
   style's prose, intensity words are on the scale, character words resolve to tags,
   ingredient names resolve to `ref` rows) and writes a draft
   `loaders/style_envelopes.toml`. The user reviews and edits it and marks each style
   `reviewed = true`; then `python -m loaders.style_envelopes` loads the reviewed styles into
   `ref.style_sensory`, `ref.style_character` and the new `ref.style_ingredient`
   (characteristic ingredients, as a role, an ingredient or a tag). Only the loader writes
   `ref`; the LLM step writes a file.
3. **Behaviour in SQL.** `db/033_style_fit_effects.sql` holds the usage effects
   (`app.usage_effects()`, STYLE-FIT §3), the cut points with their basis
   (`app.style_fit_cut_points()`, from the doc → calc pass on *How to Brew* and OBC in
   `cut-points.md`, gaps set by the user) and the intensity helpers. `db/034_style_level.sql`
   holds `app.style_level()` (STYLE-FIT §5 as amended: override → adjunct/sugar rule → per
   sensation → combine → `fermentable_style` bump) and `app.style_fit_recipe()` (every line of a
   recipe rated, plus the required check, R6). Colour and bitterness come from
   `app.check_recipe(recipe)->'numbers'`, which computes them with s1's `app.srm` and `app.ibu`.
4. **Checks.** A golden set (`tests/fixtures/style_fit_golden.toml`, ~50 cases drafted by
   Claude, corrected and approved by the user) and the 22 reference recipes rated in their own
   styles (R9).

The design-doc rewrite (STYLE-FIT §4 and §5 and the corpus mentions of R10, D9 out of §7) goes
first, because it is already agreed and every later task builds to it. Measured counts go into
the docs in the last task.

**Three stop points** where the implementing subagent returns `needs-input` and waits:
Task 5 (the 26 envelopes, the dictionary and the flagged ingredients), Task 6 (the cut points
the books do not give, and the golden set), and Task 9 only if a reference-recipe line comes out
⚠️ or ⛔ outside b16 rice, b19 honey and b20 lactose. Nothing under review is loaded or committed
before the answer.

### Decisions this plan makes (implementation details, open to change at approval)

- **Hop character tags come from the shop's short "Aroma :" line** (the text after `Aroma :` in
  the hopline `spec`), and from the "Komló aroma" list only when that line is empty or `???`.
  Measured 2026-10-15: 87 of 90 hops have a usable line, and 55 of 90 "Komló aroma" lists
  contain *Citrusos* (Saaz, Magnum and Perle among them). With both sources nearly every hop
  would match a citrus style, and Citra would match 15B's *floral* (its list has *Virágos*,
  its line does not), so the Citra table could not reproduce.
- **Character match = the best pair**: for each (ingredient tag, style character) pair, 1.0 if
  they are the same tag, 0.5 if one is the other's parent, else 0; the match is the highest.
  ≥ 0.8 → 👍, ≥ 0.3 → ➖, else ⚠️ (STYLE-FIT §5).
- **Yeast "clean" is an intensity, not a character.** *Semleges* (neutral) maps to no tag. A
  yeast with no ester character tag carries no character; its ester intensity is the base for
  its family (cut points). A yeast with family `brett` drives `brett_funk`, one with family
  `sour` (hopline Stílus *sour*, aroma *Savanyú*) drives `sourness`; both are transforming.
- **Fermentable tags:** the role as a `family` tag; characters from a keyword scan of the name
  and `description` (prose, so no unknown-word flag); a `smoke` tag for smoked and peated malts.
  Usage effects by role follow STYLE-FIT §3 (roast → roast + colour; crystal → caramel,
  sweetness, colour, body); base and kilned malts drive no sensation, so they rate ➖ unless
  `ref.fermentable_style` lists them (👍). Any ingredient tagged `smoke` drives `smoke`
  (specialty).
- **Colour and bitterness** are not 0–7 levels: the recipe's SRM and IBU are compared with the
  style's `srm` and `ibu` ranges in `ref.beer_style`; no envelope row is extracted for them.
  Above the range's upper bound → ⚠️ "too much". A style with no range (31B) skips it.
- **Dose of one call vs a recipe.** `app.style_level` rates one ingredient with its own dose.
  `app.style_fit_recipe` passes recipe totals, so the dose check sees the whole beer: every late
  hop line (boil < 30 min, whirlpool, dry hop) gets the recipe's total late-hop oil dose, every
  roast line the recipe's total roast index, and every line the recipe's SRM and IBU.
- **A style with no reviewed envelope is not rated:** `level` is `null` and the because says so
  (PROJECT.md §6.3). This covers the 259 styles out of scope.
- **New tables, not new columns:** `ref.style_ingredient` (characteristic ingredients) and
  `ref.ingredient_review` (flagged ingredients and why), both in `db/012_style_fit.sql`.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `docs/STYLE-FIT.md` | changed | §4 cut points from the books; §5 adjunct/sugar rule and `fermentable_style` bump (R10); §6 "a style" row: BJCP and BA through the LLM extract |
| `docs/work/s3-style-fit/brief.md` | changed | Deviations: §6 in scope (user's agreement, 2026-10-15) |
| `docs/RECIPE-ROADMAP.md`, `docs/WORKFLOW-ROADMAP.md`, `docs/DATABASE.md` | changed | no corpus route for style fit (R10); new tables; measured status at the end |
| `PROJECT.md` | changed | D9 out of §7 into §5; §4 status; §8 entries |
| `db/012_style_fit.sql` | changed | `ref.style_ingredient`, `ref.ingredient_review` |
| `loaders/style_fit_vocab.toml` | new | dimensions, tag tree, descriptor dictionary, no-character words |
| `loaders/tags.py` | new | loads the vocabulary, derives `ref.ingredient_tag` and `ref.ingredient_review` |
| `loaders/style_envelope_prompt.md`, `loaders/style_envelope.schema.json` | new | extraction prompt and answer schema (offline only) |
| `loaders/style_envelopes.py` | new | `--extract` (LLM → draft TOML, checked) and load (reviewed TOML → `ref`) |
| `loaders/style_envelopes.toml` | new | the 26 reviewed envelopes, characteristic ingredients, any `style_rule` rows |
| `docs/work/s3-style-fit/cut-points.md` | new | doc → calc pass: book figures, pages, derived cut points, user-set gaps |
| `db/033_style_fit_effects.sql` | new | `app.usage_effects()`, `app.style_fit_cut_points()`, intensity helpers |
| `db/034_style_level.sql` | new | `app.tag_match()`, `app.style_level()`, `app.style_fit_recipe()` |
| `tests/test_tags.py`, `tests/test_style_envelopes.py`, `tests/test_style_fit_effects.py`, `tests/test_style_level.py`, `tests/test_style_fit_golden.py`, `tests/test_style_fit_recipe.py` | new | tests named per task below |
| `tests/fixtures/style_fit_golden.toml` | new | ~50 approved golden cases (R8) |
| `docs/work/s3-style-fit/report.md` | new | tagging counts and flagged list, extraction run, review notes, golden approval, reference-recipe results |

## Tasks

### Task 1: Design docs describe the agreed approach without a corpus
Why: R10 (A10), the agreed §4/§5 changes. Docs only; no code depends on it.
- [ ] `docs/STYLE-FIT.md` §4: replace the "calibrated on the corpus" paragraph: cut points come
      from figures cited in *How to Brew* and the OBC *Recipe Formulation* PDF (doc → calc
      pass), the user sets any the books don't give, each lives in code with its basis (book
      and page, or "set by the user") and is checked against the 22 reference recipes. Add the
      colour/bitterness note (recipe SRM/IBU from s1 vs the style range). Drop the
      STYLE-PROFILES link.
- [ ] `docs/STYLE-FIT.md` §5: the pseudo-code gets step 1b, the adjunct/sugar rule (a
      fermentable with role `adjunct` or `sugar`: named in the style's reviewed characteristic
      ingredients → 👍, else ⚠️ "not a usual ingredient of <style>"), and step 4 becomes "➖, a
      fermentable, listed for the style in `ref.fermentable_style` → 👍 (no bump for hops or
      yeasts)". Note that a missing dose skips the dose check and the because says so, and that
      a style with no reviewed envelope is not rated. Add the character-match rule (best pair:
      1.0 same, 0.5 parent/child). The worked example keeps its rows.
- [ ] `docs/STYLE-FIT.md` §6, row "a style": "one envelope (BA: parsed · BJCP: LLM extract +
      your review)" → "one envelope (BJCP and BA: LLM extract + your review (BA parser later))"
      (user's agreement 2026-10-15, brief Deviations).
- [ ] `docs/RECIPE-ROADMAP.md` §5: diagram node "dose vs corpus" → "dose → intensity (cut
      points from the books)"; table row **Dose check** → lives in code
      (`db/033_style_fit_effects.sql`); **Overrides** example no longer 16A lactose (now the
      adjunct/sugar rule) but "only where the envelope and the adjunct/sugar rule can't say it";
      "Where each level comes from": 👍 row "or it ranks top in the corpus" → "or, for a
      fermentable, `ref.fermentable_style` lists it for the style; or it is an adjunct or sugar
      the style's characteristic ingredients name"; ⚠️ row adds "an adjunct or sugar the style
      doesn't name". Also "The LLM is used once, offline, to extract BJCP envelopes" → "BJCP and
      BA envelopes".
- [ ] `docs/WORKFLOW-ROADMAP.md`: edge `S2 -. "…revisit in s3" .-> S3` → `S2 --> S3`; the chain
      sentence drops "(s2-corpus abandoned …; revisit in s3)" and the corpus reasons, and says
      s3 needs s2's fermentable roles and `fermentable_style`; TL;DR "Maths, corpus and tags" →
      "Maths, formulation rules and tags"; S3 row Builds → "Tags, envelopes for 26 styles (22
      brief styles, 3 alternates, 20B), `level()`, golden set (D9)"; G-S bar: "envelopes for the
      26 s3 styles reviewed by you (D9); the golden set passes; every reference-recipe line
      rated, 0 unexpected ⚠️/⛔" instead of "22 brief styles" and "D7 settled with measured
      profile counts".
- [ ] `docs/DATABASE.md`: §2 rule diagram node "dose ≤ corpus p90?" → "dose ≤ envelope max
      (cut points)?", plus a node for the adjunct/sugar rule before the usage effects and the
      `fermentable_style` bump after "no conflict"; §2 rows `style_sensory`/`style_character`
      "BA: parsed by code · BJCP: LLM extract" → "BJCP and BA prose: LLM extract (D2 model) →
      you review"; §7 row 4 marked "not loaded (D7, 2026-10-14); style fit does not use it";
      §7 row 5 → envelopes for the 26 s3 styles, done when the Citra table and the golden set
      pass; §8 cut-point row → "from *How to Brew* and OBC, or set by the user" living in
      `app.style_fit_cut_points()`, usage-effects row → `app.usage_effects()`.
- [ ] `PROJECT.md`: remove the D9 row from §7 (leave the table with a "none open" row) and add
      to §5's style-guides text: "**Style envelopes (was D9, decided 2026-10-15):** the D2 model
      extracts BJCP and BA guideline prose offline, and the user reviews every envelope before
      it enters `ref`; a BA field parser comes later, when all 169 BA styles are wanted. *Why:
      one path for 26 styles is less to build than a parser for 3, and nothing enters `ref`
      unreviewed.*" Add the §8 line.
- [ ] Run `grep -n -i "corpus\|p90\|revisit in s3" docs/STYLE-FIT.md docs/WORKFLOW-ROADMAP.md`
      and read every hit in RECIPE-ROADMAP §5 and DATABASE §2, §7, §8: none describes a corpus
      route for style fit (hits about the abandoned corpus itself, M5 or §3 `corpus` tables are
      fine). `grep -n "D9" PROJECT.md` shows no §7 row.
Done when: A10 holds.
Commit: `Describe s3 style fit without a corpus`

### Task 2: Tables for characteristic ingredients and flagged ingredients
Why: R1, R3, R6.
- [ ] Append to `db/012_style_fit.sql` (idempotent):
  ```sql
  -- A style's characteristic ingredients (R3, R6): exactly one of a fermentable role, an
  -- ingredient or a tag (yeast family, hop origin). required = the recipe must have it (✅).
  create table if not exists ref.style_ingredient (
      id            bigint generated always as identity primary key,
      style_id      bigint not null references ref.beer_style (id) on delete cascade,
      role          text check (role in ('base', 'kilned', 'crystal', 'roast', 'adjunct', 'sugar')),
      ingredient_id bigint references ref.ingredient (id) on delete cascade,
      tag_id        bigint references ref.tag (id) on delete cascade,
      required      boolean not null default false,
      min_pct       numeric(4, 1),     -- with role: at least this % of the grist
      quote         text not null,     -- the guideline text it comes from
      reviewed      boolean not null default false,
      check (num_nonnulls(role, ingredient_id, tag_id) = 1),
      check (min_pct is null or role is not null)
  );
  create index if not exists style_ingredient_style_id_idx on ref.style_ingredient (style_id);
  -- Ingredients whose tags need a person: unknown descriptor words, or no descriptor text.
  -- Rewritten by loaders/tags.py on every run.
  create table if not exists ref.ingredient_review (
      ingredient_id bigint primary key references ref.ingredient (id) on delete cascade,
      reason        text not null      -- "unknown words: …" or "no descriptor text"
  );
  ```
- [ ] Apply twice as `postgres` (OPERATIONS.md §4 command), no errors; both tables owned by
      `postgres` (`select tableowner from pg_tables where schemaname = 'ref' and tablename in (…)`).
- [ ] Write test `tests/test_tags.py::test_schema` (stack): both tables exist; a
      `style_ingredient` row with two of role/ingredient/tag raises `CheckViolation` (rolled back).
- [ ] PROJECT.md §8 line.
Done when: the test passes; `ref` has 19 tables, all owned by `postgres`.
Commit: `Add style ingredient and ingredient review tables`

### Task 3: Vocabulary and automatic tagging
Why: R1, R2, R5's tags (A1, A2).
- [ ] `loaders/style_fit_vocab.toml`:
  - `[[dimension]]` name + class. Core: `bitterness`, `colour`, `hop_flavour`, `hop_aroma`,
    `malt`, `caramel`, `roast`, `sweetness`, `body`, `esters`, `phenols`, `dryness`;
    specialty: `spice`, `fruit`, `wood`, `smoke`; transforming: `sourness`, `brett_funk`.
  - `[[tag]]` facet, name, parent. Origins from the codes in `ref.hop.origins`; families: the
    six fermentable roles, and yeast families `ale` > (`american-ale`, `english-ale`,
    `belgian` > `saison`, `wheat`), `lager`, `kveik`, `brett`, `sour`; characters as a tree
    (e.g. `fruity` > `citrus` > `grapefruit`/`lemon`/`lime`/`orange`; `fruity` > `tropical`,
    `stone-fruit`, `berry`, `melon`; `floral`, `herbal` > `mint`, `spicy` > `pepper`, `clove`,
    `earthy`, `grassy`, `resin` > `pine`, `woody`, `banana`, `caramel` > `toffee`, `roast` >
    `coffee`/`chocolate`/`acrid`, `bready`, `biscuit`, `toasty`, `smoke`, `honey`, `funky`,
    `sour`).
  - `[synonyms]` word → tag name, keys written as `name_key` (`loaders.common.name_key`, so
    `Citrusos` → `citrusos`). Cover every word and phrase in the hops' "Aroma :" lines and
    fallback lists, the yeasts' hopline `Aroma` and `Stílus` values, and the English words the
    style prose uses (citrusy, resiny, earthy, floral, …).
  - `[no_character] words = [...]`: known words with no tag (*semleges*, *keserű*, *komló*,
    *komlós*, …), so they are neither tagged nor flagged.
- [ ] `loaders/tags.py`, functions a reader can follow: `load_vocab(conn, vocab)` (upsert
      dimensions, tags, synonyms; synonyms not in the file are deleted), `split_words(text)`
      (split on `,`, ` és `, ` and `; strip; `name_key`), `hop_words(raw)` (the "Aroma :" line,
      else the "Komló aroma" list), `yeast_words(raw)`, `fermentable_keywords(name,
      description)`, `derive_tags(conn)` (deletes `reviewed = false` rows of `ref.ingredient_tag`
      and all `ref.ingredient_review` rows, then inserts: hop origin + character tags, fermentable
      role tag + keyword characters, yeast family from Stílus else `ref.yeast.type` + character
      tags; keeps `reviewed = true` rows), `main()` printing counts per kind and flagged.
      Re-runnable; one transaction.
- [ ] Run `python -m loaders.tags`; write the counts and the flagged list into `report.md` §1.
- [ ] Write tests in `tests/test_tags.py`: `test_split_words` (Hungarian lists, "és", empty and
      `???`), `test_hop_words_prefers_aroma_line` (Citra gives grapefruit/lime/tropical, not
      floral), and stack tests `test_every_hop_tagged_or_flagged` (A1: each of the 90 hops has
      a character tag or an `ingredient_review` row), `test_retag_is_identical` (A2: run
      `derive_tags` twice, same `ingredient_tag` rows), `test_new_synonym_retags` (A2: in a
      rolled-back transaction, add a synonym for a word that is flagged and re-derive: the hop
      gains the tag and loses its review row), `test_citra_tags` (Citra: `US`, `citrus`,
      `tropical`, no `floral`), `test_yeast_families` (US-05 `american-ale` with no character,
      a brett-type yeast `brett`, a `sour` Stílus yeast `sour`).
- [ ] Run `pytest tests/test_tags.py`, expect all pass; break `hop_words` (use both sources)
      once and see `test_citra_tags` fail.
- [ ] PROJECT.md §8 line with the measured counts.
Done when: A1 and A2 hold; the flagged count is in `report.md`.
Commit: `Add style-fit vocabulary and ingredient tagging`

### Task 4: Envelope extraction job (offline LLM, checked by code)
Why: R3, R4.
- [ ] `loaders/style_envelope.schema.json`: the answer shape, `{"sensory": [{dimension, min,
      max, characters[], quote}], "ingredients": [{role | ingredient | tag, required, min_pct,
      quote}]}`; `dimension` is an enum of the non-colour, non-bitterness dimensions; `min`/`max`
      an enum of the scale words.
- [ ] `loaders/style_envelope_prompt.md`: what to extract, the 0–7 scale words (none 0, very
      low 1, low 2, medium-low 3, medium 4, medium-high 5, high 6, very high 7; "moderate" =
      medium), "quote the guideline text verbatim", "leave out a dimension the text does not
      describe", "say 'none' only when the text says none", the role list, and that colour and
      bitterness are not extracted. No ingredient or style name examples beyond the schema.
- [ ] `loaders/style_envelopes.py`:
  - `style_prose(raw)`: the fields `overallimpression`, `aroma`, `appearance`, `flavor`,
    `mouthfeel`, `comments`, `characteristicingredients`, `entryinstructions` when present,
    labelled.
  - `ask(prose)`: `POST http://localhost:11434/api/chat` with model
    `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K`, `think: false`, `stream: false`, the schema as
    `format`, options `temperature 0`, `seed 42`, `num_ctx 8192` (as `evals/benchmark.py`).
  - `check_answer(conn, code, prose, answer) -> (draft, problems)`: each quote is a substring of
    the prose after whitespace folding; scale word → number; `min ≤ max`; character words →
    tags through `ref.tag_synonym` (unresolved ones kept under `unknown`); ingredient names →
    `ref.ingredient` (unresolved kept under `unknown`); duplicates of a dimension are a problem.
    A style with problems is asked once more with the problems listed; a second failure is kept
    in the draft with its problems for the user.
  - `--extract OUT` (all 26 codes listed in the module as `S3_STYLES`, or `--style CODE`)
    writes the draft TOML: one `[[style]]` per code, `reviewed = false`, `extracted = {model,
    date, tries}`, `[[style.sensory]]` (dimension, min, max as words, characters as tag names,
    quote, unknown) and `[[style.ingredient]]` (one of role / ingredient as "producer|name" /
    tag, required, min_pct, quote, unknown).
  - load mode (no flag): reads the TOML, refuses a style with `reviewed = true` that still has
    `unknown` words or problems, and for each reviewed style deletes then inserts its
    `style_sensory` (`reviewed = true`), `style_character` and `style_ingredient` rows; an
    optional `[[style.rule]]` table loads into `ref.style_rule`. Unreviewed styles are skipped
    and counted. One transaction; re-runnable.
- [ ] Write unit tests in `tests/test_style_envelopes.py` on canned answers (no LLM):
      `test_quote_must_be_in_prose`, `test_scale_words_to_numbers`, `test_unknown_character_kept`,
      `test_min_above_max_is_a_problem`, `test_reviewed_style_with_unknown_refused`,
      `test_s3_styles_are_the_26` (the 22 `style` values of `evals/recipe_briefs.toml` + 20C,
      18A, `specialty-honey-beer`, 20B, all in `ref.beer_style`), and
      `test_extraction_not_in_pipeline` (R4: nothing under `n8n/workflows/` or
      `shared/prompts/` mentions `style_envelope`).
- [ ] Run `python -m loaders.style_envelopes --extract loaders/style_envelopes.toml` with
      Ollama up; record run time, tries and remaining problems in `report.md` §2. Do not load.
- [ ] PROJECT.md §8 line.
Done when: the unit tests pass and the draft for all 26 styles exists (uncommitted).
Commit: `Add style envelope extraction job` (code, prompt, schema, tests; not the draft)

### Task 5: The user reviews the envelopes; load them — STOP
Why: R3, R4, D9 (A3).
- [ ] Return `needs-input` with: the path of `loaders/style_envelopes.toml`, the extraction
      problems, the flagged ingredients from `report.md` §1, and the dictionary
      (`loaders/style_fit_vocab.toml`) for a look. Ask the user to correct each style, set
      `reviewed = true`, and add synonyms or `no_character` words for the flagged words. Load
      nothing before the answer.
- [ ] After the answer: re-run `python -m loaders.tags` if the vocabulary changed, then
      `python -m loaders.style_envelopes` twice; record the review notes in `report.md` §3.
- [ ] Write stack tests in `tests/test_style_envelopes.py`: `test_26_styles_reviewed` (A3: each
      S3 style has ≥ 1 `style_sensory` row, all `reviewed = true`, every quote non-empty and
      found in the style's `raw` text; the 3 BA styles included), `test_characteristic_ingredients`
      (each style has ≥ 1 reviewed `style_ingredient` row; 16A names Lactose, 1B Flaked Rice,
      1C Flaked Corn, 21C Flaked Oats, 15B a required `roast` role, 31B the role `sugar` or
      Honey), `test_reload_is_identical`.
- [ ] PROJECT.md §8 line with the row counts.
Done when: A3 holds.
Commit: `Load the 26 reviewed style envelopes`

### Task 6: Cut points from the books, and the golden set — STOP
Why: R7, R8 (A4, A5 data). Docs and a fixture; no SQL yet.
- [ ] Doc → calc pass on `shared/rag-files/pending/how_to_brew.pdf` and
      `obc_recipe_formulation.pdf` (`pdftotext -layout`): every figure on hop rates (late,
      whirlpool, dry hop, per style or intensity word), roast and crystal proportions per style,
      and anything on ester or phenol level against yeast or temperature. Write
      `docs/work/s3-style-fit/cut-points.md`: each figure with book, page and quote; the cut
      points derived from it with the arithmetic shown; and a table of every cut point with its
      basis or "gap: user sets". Cut points:
      - `oil_ml_per_l`: 7 ascending thresholds of late-hop oil dose (g/L × the hop's
        `total_oil_ml_100g` midpoint ÷ 100); level = how many thresholds the dose reaches.
      - `roast_index`: 7 thresholds of Σ % of grist × EBC midpoint over roast malts.
      - `esters`: base level per yeast family / character (proposal: `lager` 0, no ester
        character 1, an ester character 4), + `warm_step` when `ferm_c` is above the midpoint
        of the yeast's `temp_c`.
      - `phenols`: base level for a phenolic character (`clove`, `pepper`, `phenolic`), else 0.
      Check them against the 22 reference recipes and the Citra table on paper (Citra mid oil
      2.25 mL/100 g: whirlpool 2 g/L must stay at or below 20B's max, dry hop 8 g/L above it).
- [ ] Draft `tests/fixtures/style_fit_golden.toml`, ~50 `[[case]]` with `id`, `style`, `kind`,
      `producer`, `name`, `usage`, `dose` (inline table), `level` (`required` is not a case
      level), `note`. It must contain: the 6 Citra-table cases (15B and 20B × boil 60 min /
      whirlpool 2 g/L / dry hop 8 g/L); M3's 7 cases (b16 Flaked Rice in 18B, b19 Honey in 17C,
      b20 Lactose in 19C → `out_of_style`; b02 Flaked Oats in 21C, b06 Flaked Rice in 1B, b07
      Flaked Corn in 1C, b12 Honey in 31B → not `out_of_style`); Lactose in 16A → `typical`;
      A8's cases (a malt listed in `ref.fermentable_style` for a style and otherwise ➖ →
      `typical`; a hop and a yeast otherwise ➖ → `allowed`); and spread over the 26 styles:
      yeast character (weizen yeast in 10A, clean ale yeast in 10A, a Belgian yeast in 26B, a
      lager yeast in 5D), a brett yeast in 21A → `changes_style`, a sour yeast in 23A, a smoked
      malt in 6A → `out_of_style` (specialty), a roast malt too heavy for 15A, English hops in
      11B, a case with no dose (because says skipped), a needs-review hop, and a style with no
      envelope (e.g. 21B → `level` absent). Levels come from brewing judgement and the guideline
      text, not from running code (there is none yet).
- [ ] Return `needs-input`: the gaps in `cut-points.md` for the user to set, and the golden set
      to correct and approve. Commit nothing before the answer.
- [ ] After the answer: fill the user's values (basis "set by the user, <date>"), record the
      approval in `report.md` §4 and §5.
- [ ] PROJECT.md §8 line.
Done when: every cut point has a basis, and the user approved the golden set.
Commit: `Add style-fit cut points and golden set`

### Task 7: Usage effects, cut points and intensity in SQL
Why: R5, R7 (A7).
- [ ] `db/033_style_fit_effects.sql` (header as `db/031`; `create or replace`):
  - `app.usage_effects() returns table (kind text, applies_to text, usage text, min_minutes
    int, max_minutes int, dimension text, carries_character boolean)`: one `values` row per
    STYLE-FIT §3 entry: hop boil ≥ 30 → bitterness (no character); boil 5–29 → bitterness,
    hop_flavour; boil 0–4, whirlpool → hop_flavour, hop_aroma; dry_hop → hop_aroma; role roast
    (mash or boil) → roast, colour; role crystal → caramel, sweetness, colour, body; yeast
    ferment → esters, phenols; family brett → brett_funk; family sour → sourness; tag smoke
    (any usage) → smoke. `applies_to` is a role, a family or a tag name.
  - `app.style_fit_cut_points() returns jsonb`: the Task 6 values, each entry with its
    `basis` string (book and page, or "set by the user, <date>"), and `character_match`
    `{typical 0.8, allowed 0.3, basis "STYLE-FIT.md §5"}`.
  - `app.intensity_level(scale text, value numeric) returns smallint`: how many of the scale's
    thresholds `value` reaches (0–7); raises on an unknown scale; null value → null.
  - `app.oil_dose(g_per_l numeric, total_oil numrange) returns numeric` and
    `app.roast_index(pct numeric, ebc numrange) returns numeric`, using the range midpoint
    (`app.ebc_mid` for EBC).
- [ ] Apply twice as `postgres`; functions owned by `postgres`.
- [ ] Write tests in `tests/test_style_fit_effects.py` (stack): `test_every_cut_point_has_a_basis`
      (A7: every entry's `basis` matches `p\. ?\d+` or starts with `set by the user`),
      `test_thresholds_ascend`, `test_intensity_level_bounds` (below the first → 0, at a
      threshold → that level, above the last → 7), `test_usage_effects_match_style_fit` (dry hop
      → only hop_aroma with character; boil 60 → only bitterness, no character),
      `test_no_corpus_in_style_fit` (A7: no `corpus.` in `db/033_*.sql`, `db/034_*.sql`,
      `loaders/tags.py`, `loaders/style_envelopes.py`).
- [ ] Run `pytest tests/test_style_fit_effects.py`, expect all pass.
- [ ] PROJECT.md §8 line.
Done when: the tests pass.
Commit: `Add style-fit usage effects and cut points`

### Task 8: level() as in STYLE-FIT §5, and the golden set runs
Why: R5, R8 (A4, A5, A8).
- [ ] `db/034_style_level.sql`:
  - `app.tag_match(ingredient_id bigint, style_id bigint, dimension text) returns numeric`:
    best pair over the ingredient's `character` tags and the style's `style_character` tags for
    that dimension (1.0 same, 0.5 parent/child, else 0); null when either side has no tags.
  - `app.style_level(style_code text, ingredient_id bigint, usage text, dose jsonb default
    '{}') returns jsonb` → `{"level": "required|typical|allowed|out_of_style|changes_style" or
    null, "because": text}`. `usage`: hops `boil` (needs `dose.minutes`) | `whirlpool` |
    `dry_hop`; fermentables `mash` | `boil`; yeasts `ferment`. `dose` keys, all optional:
    `minutes`, `g_per_l`, `oil_ml_per_l` (wins over `g_per_l`), `pct`, `roast_index` (wins over
    `pct`), `ferm_c`, `ibu`, `srm`. Raises on an unknown style code, ingredient id, or a usage
    not valid for the kind. Steps, each adding a sentence to the because:
    0. no reviewed `style_sensory` row for the style → level null, "not rated: <style> has no
       reviewed envelope".
    1. `ref.style_rule` for the style and the ingredient, else one of its tags, with `usage`
       null or equal → that level and quote.
    2. role `adjunct` or `sugar`: a reviewed `style_ingredient` row naming the ingredient or its
       role → `typical` ("named in <style>'s characteristic ingredients: '<quote>'"), else
       `out_of_style` ("not a usual ingredient of <style>"). Return.
    3. for each dimension from `app.usage_effects()`: bitterness/colour vs the style's `ibu` /
       `srm` upper bound; silent style (no `style_sensory` row): transforming → `changes_style`,
       specialty → `out_of_style` ("specialty <dimension> on <style>"), core → no conflict;
       intensity above `max_level` → `out_of_style` ("too much: <value> is <level word>, <style>
       allows up to <word>: '<quote>'"); missing dose → "dose not given, dose check skipped";
       character (when the effect carries it): match ≥ 0.8 → `typical`, ≥ 0.3 → `allowed`, else
       `out_of_style` ("wrong character: <tags> vs <characters>: '<quote>'"); an ingredient with
       no character tags → "no character tags (needs review)".
    4. combine: any `changes_style` → it; else any `out_of_style`; else any `typical`; else
       `allowed`.
    5. a fermentable at `allowed` with a `ref.fermentable_style` row for this style →
       `typical` ("listed for <style> in <source title>").
- [ ] Apply twice as `postgres`; functions owned by `postgres`.
- [ ] Write tests in `tests/test_style_level.py` (stack), one per step, each using a temporary
      row in a rolled-back transaction where it needs one: `test_unrated_style`,
      `test_override_wins`, `test_adjunct_named_vs_not`, `test_silent_transforming_is_changes_style`,
      `test_silent_specialty`, `test_too_much`, `test_missing_dose_skips_and_says_so`,
      `test_wrong_character`, `test_fermentable_style_bump_only_for_fermentables` (A8),
      `test_boil_needs_minutes`, `test_unknown_style_raises`.
- [ ] Write `tests/test_style_fit_golden.py` (stack): one parametrised test per golden case
      (A5), `test_citra_table` (A4: the 6 Citra cases exactly), and `test_m3_cases_have_no_rule`
      (no `ref.style_rule` row for the 8 R8 ingredient/style pairs).
- [ ] Run both files, expect all pass. A golden case that fails is fixed in the data (tags,
      envelope, cut point) only if the fix is a plain error; otherwise stop and ask (the golden
      levels are the user's). Break the step order (bump before combine) once and see a test
      fail.
- [ ] PROJECT.md §8 line.
Done when: A4, A5 and A8 hold.
Commit: `Add style level function with golden tests`

### Task 9: Whole recipes: required check and the reference recipes
Why: R6, R9 (A6, A9).
- [ ] Add to `db/034_style_level.sql` `app.style_fit_recipe(recipe jsonb) returns jsonb`. Input:
      the `app.check_recipe` input (style_code, batch, targets, fermentables, hops, yeast).
      Computes `numbers := app.check_recipe(recipe)->'numbers'` for `srm` and `ibu`, the
      recipe's late-hop oil dose (Σ over boil < 30 min, whirlpool and dry hop lines of g ÷
      `batch.volume_l` × oil midpoint ÷ 100) and roast index (Σ over role `roast`), and calls
      `app.style_level` for every line with those totals (hops: `minutes`, `g_per_l`,
      `oil_ml_per_l` for late lines; fermentables: `pct`, `roast_index` for roast lines; yeast:
      `ferm_c`; all: `ibu`, `srm`). Required check: each reviewed `style_ingredient` row with
      `required = true` is met by a fermentable with that role (and ≥ `min_pct` of the grist
      when set), by that ingredient, or by an ingredient with that tag. Output: `{"style_code",
      "lines": [{"kind", "ingredient_id", "name", "usage", "level", "because"}], "required":
      [{"requirement", "met", "because"}]}`.
- [ ] Apply twice as `postgres`.
- [ ] Write `tests/test_style_fit_recipe.py` (stack): `test_15b_needs_roast` (A6: b05's recipe
      with Roasted Barley passes; the same with it swapped for Pale Ale malt fails the roast
      requirement), `test_reference_recipe_lines` (A9: for each of the 22 fixtures, built with
      `tests/test_reference_recipes.py`'s `build_input`, every line has a non-null level and
      none is `out_of_style`/`changes_style` except b16 Flaked Rice, b19 Honey, b20 Lactose and
      the entries of an `ACCEPTED_LINES` dict, empty at first), and `test_deviation_lines_are_flagged`
      (those three lines are `out_of_style`).
- [ ] Run it. If a line fails: write each one into `report.md` §6 (recipe, line, level,
      because) and return `needs-input` with options per line: fix the cut point or envelope
      (with the user's agreement), change the reference recipe, or accept it into
      `ACCEPTED_LINES` with the user's reason and date. Commit nothing before the answer.
- [ ] PROJECT.md §8 line with the result.
Done when: A6 and A9 hold.
Commit: `Add recipe style fit and reference-recipe check`

### Task 10: Measured status in the docs; full test run
Why: CLAUDE.md, PROJECT.md §10; G-S.
- [ ] Run full `pytest` with the stack up and `pytest -m "not stack"`; note counts and time.
- [ ] Query the counts: `ref.tag`, `tag_synonym`, `ingredient_tag` per kind, `ingredient_review`,
      `sensory_dimension`, `style_sensory`, `style_character`, `style_ingredient`, `style_rule`;
      functions in `db/033`, `db/034` owned by `postgres`.
- [ ] PROJECT.md §4 Database and Scripts rows (tables, loaders and their run order:
      `loaders.tags` after the ingredient loaders and `loaders.fermentable_facts`;
      `loaders.style_envelopes` after `loaders.tags`), §8 entry with the G-S result.
      DATABASE.md §2 row counts and the two new tables (ER diagram and table), §7 rows 3 and 5
      done-when with the measured result. WORKFLOW-ROADMAP G-S: measured result.
- [ ] Re-run the A10 grep.
Done when: the docs show measured numbers; full `pytest` passes.
Commit: `Record s3 style fit status`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| Every hop tagged or flagged; no guessed tags | `tests/test_tags.py::test_every_hop_tagged_or_flagged` | 3 |
| Tagging is repeatable; a new synonym re-tags | `test_tags.py::test_retag_is_identical`, `::test_new_synonym_retags` | 3 |
| Hop character from the "Aroma :" line (Citra not floral) | `test_tags.py::test_citra_tags`, `::test_hop_words_prefers_aroma_line` | 3 |
| LLM quotes are verbatim; nothing unreviewed loads | `test_style_envelopes.py::test_quote_must_be_in_prose`, `::test_reviewed_style_with_unknown_refused` | 4 |
| Extraction never runs in the pipeline | `test_style_envelopes.py::test_extraction_not_in_pipeline` | 4 |
| 26 envelopes reviewed, with quotes and characteristic ingredients | `test_style_envelopes.py::test_26_styles_reviewed`, `::test_characteristic_ingredients` | 5 |
| Every cut point has a basis; no corpus read | `test_style_fit_effects.py::test_every_cut_point_has_a_basis`, `::test_no_corpus_in_style_fit` | 7 |
| §5 steps in order, missing dose said | `tests/test_style_level.py` (11 tests) | 8 |
| Citra table and golden set | `test_style_fit_golden.py::test_citra_table`, golden cases | 8 |
| Adjunct/sugar rule without overrides (M3 cases, 16A lactose) | golden cases + `::test_m3_cases_have_no_rule` | 8 |
| `fermentable_style` bump for fermentables only | `test_style_level.py::test_fermentable_style_bump_only_for_fermentables` | 8 |
| Required check (15B roast) | `test_style_fit_recipe.py::test_15b_needs_roast` | 9 |
| Reference recipes rated, only the briefs' deviations flagged | `test_style_fit_recipe.py::test_reference_recipe_lines`, `::test_deviation_lines_are_flagged` | 9 |

## Approved exceptions

None.

## Deviations
- 2026-10-15 · Task 1: STYLE-FIT.md §6 "a style" row also corrected to "BJCP and BA: LLM
  extract + your review (BA parser later)" — it contradicted D9; user's agreement at plan
  approval (brief Deviations).
