# S3 · Style fit: tags, envelopes and the level function (P3, D9)

Status: approved
Slug: s3-style-fit · Branch: s3-style-fit
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) side track P3, checkpoint **G-S** ·
[STYLE-FIT.md](../../STYLE-FIT.md) · [RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §5
Needs: `s2-formulation-rules` shipped ✅ 2026-10-15 (fermentable `role` 81/81), `s1-maths`
shipped ✅ (SRM, IBU), `m1-read-request` shipped ✅ (D2 model). No corpus: `s2-corpus` was
abandoned 2026-10-14 (D7); this brief replaces the two things it was to supply with data that
exists (user's answers, 2026-10-15).

## Why
Steps 3, 7–9 and 11 must answer "is this ingredient, used this way, in this style: required,
typical, allowed, out of style or style-changing?" without a hand-written row for every
ingredient × style pair. STYLE-FIT.md designs this; none of it is built (measured 2026-10-15:
`ref.tag`, `tag_synonym`, `ingredient_tag`, `sensory_dimension`, `style_sensory`,
`style_character`, `style_rule` exist, owned by `postgres`, all 0 rows). Ingredient deviations
(M3) and in-style choices (M5) wait for it.

STYLE-FIT.md leaned on a recipe corpus for two things: the popularity bump in §5 step 4
(➖ → 👍 when ≥ 15 % of the style's corpus recipes use it) and the intensity cut points in §4
("calibrated on the corpus"). The corpus is not coming (D7, PROJECT.md §3): all 7 `corpus`
tables are empty. What exists instead: `ref.fermentable_style` (623 rows, 59 of 81 fermentables,
maltsters' "typically used for" lists, from s2-formulation-rules) and 22 user-approved reference
recipes (`tests/fixtures/reference_recipes.toml`, one per test brief).

## Goal
`level(style, ingredient, usage, dose)` returns one of the five levels with a "because", from
data that exists: ingredient tags derived by code, style envelopes reviewed by you, usage effects
and cut points in code, and no corpus. The Citra table (RECIPE-ROADMAP §5) reproduces, and the
golden test set passes.

## Scope
In:
- Tag vocabulary (`ref.tag`, parent tree) and the descriptor dictionary (`ref.tag_synonym`,
  ~150 words). The hop and yeast descriptors on hopline pages are Hungarian (*Citrusos*,
  *Gyümölcsös*, *Fűszeres*), so the dictionary maps Hungarian and English words.
- Automatic tagging into `ref.ingredient_tag`: hops (origin, hopline descriptors), fermentables
  (`ref.fermentable.role` from s2-formulation-rules, name), yeasts (`ref.yeast.type`, hopline
  style and aroma words); unknown words flagged `needs_review`, never guessed.
- `ref.sensory_dimension` with its classes (core · specialty · transforming).
- Envelopes (`ref.style_sensory`, `ref.style_character`) and each style's characteristic
  ingredients for **26 styles**: the 22 brief styles (`style` in `evals/recipe_briefs.toml`:
  20 BJCP + BA `session-india-pale-ale` and `mexican-style-amber-lager`), the 3 alternates
  (20C, 18A, BA `specialty-honey-beer`; 18A is also the style of b12's reference recipe) and 20B
  (needed by the Citra table). BJCP and BA prose alike is extracted by an LLM offline and
  reviewed by you (D9).
- Usage effects and intensity cut points in code (STYLE-FIT.md §3, §4). Cut points come from
  figures cited in *How to Brew* and the OBC *Recipe Formulation* PDF (a doc → calc pass); you
  set any the books don't give.
- `level()` as in STYLE-FIT.md §5, with two changes you agreed (2026-10-15):
  - **Adjunct/sugar rule:** a fermentable with role `adjunct` or `sugar` that the style's
    reviewed characteristic ingredients name is 👍; one they don't name is ⚠️ "not a usual
    ingredient of <style>".
  - **Step 4 (popularity bump) replaced:** a fermentable listed for the style in
    `ref.fermentable_style` moves ➖ → 👍, the because naming the list. No bump for hops or
    yeasts.
- A golden test set of ~50 cases: Claude drafts it from the brief styles and their typical
  ingredients, you correct and approve it.
- `ref.style_rule` overrides only where neither the envelope nor the adjunct/sugar rule can say
  it.
- STYLE-FIT.md §4 and §5 rewritten to the agreed design (cut points from the books; the
  adjunct/sugar rule; the `fermentable_style` bump), and the other docs that still describe the
  corpus route for style fit (R10).

Out:
- Loading a recipe corpus or any `corpus.*` table (D7: revisited only if test-brief results
  show a need).
- Envelopes for the other 259 styles (later, on demand). A BA field parser (later, when all 169
  BA styles are wanted). Misc ingredients and `ref.misc` rows (no brief uses a non-gravity
  extra).
- Popularity evidence for hops and yeasts (hopline's per-hop "Felhasználás" and per-yeast
  "Stílus" style lists would need a style-name map; later, if M5 needs it).
- M3's and M5's use of `level()` (their own briefs).

## Requirements
R1. Every hop has at least one character tag or is flagged `needs_review` (DATABASE.md §7 row 3).
R2. Tagging is code: re-running it gives the same tags; adding a synonym re-tags every ingredient
    that uses the word.
R3. Envelopes for the 26 styles hold a min–max level per dimension and the allowed characters,
    each with the quote it came from, plus the style's characteristic ingredients as roles or
    ingredients, each with its quote; `reviewed = true` only after your review.
R4. The LLM extraction of guideline prose (BJCP and the 3 BA styles, one path) is an offline job
    whose output you review before it enters `ref`; it never runs in the recipe pipeline.
R5. `level()` follows STYLE-FIT.md §5 as amended: override first; then the adjunct/sugar rule
    for `adjunct` and `sugar` fermentables; then per sensation; then combine; then ➖ → 👍 for a
    fermentable listed for the style in `ref.fermentable_style`. Nothing reads a corpus. A
    missing dose skips the dose check and the because says so. It returns the level and a
    because text naming the sensation, quote, number or list used.
R6. "Required" is checked on a whole recipe from the style's characteristic ingredients as role
    requirements (e.g. 15B: roast present).
R7. The intensity cut points (oil dose → hop aroma/flavour level, roast index → roast level;
    STYLE-FIT.md §4) live in code, each with its basis written next to it: the book and page it
    comes from, or "set by the user". Colour and bitterness use s1's `app.srm` and `app.ibu`
    against the style range.
R8. A golden set of ~50 (style, ingredient, usage, dose → level) cases, drafted by Claude and
    corrected and approved by you, runs as tests. It holds the RECIPE-ROADMAP §5 Citra table and
    M3's ingredient cases: rice in 18B (b16), honey in 17C (b19) and lactose in 19C (b20) give
    ⚠️; oats in 21C (b02), rice in 1B (b06), corn in 1C (b07) and honey in 31B (b12) do not;
    lactose in 16A gives 👍 without an override row.
R9. Every ingredient line of the 22 reference recipes gets a level in its recipe's
    `style_code`; none is ⚠️ or ⛔ except the brief's own ingredient deviations (b16 rice,
    b19 honey, b20 lactose), unless you accept it in a listed exception. This is the check on
    the cut points.
R10. D9 moves from PROJECT.md §7 to the relevant section with its *why* (decided: the LLM
    extracts BJCP and BA prose, you review). STYLE-FIT.md §4 and §5 describe the agreed design.
    WORKFLOW-ROADMAP (the s2 → s3 edge and its chain sentence, the S3 row's style count, the G-S
    bar's "D7 settled with measured profile counts"), RECIPE-ROADMAP §5 ("dose vs corpus",
    "ranks top in the corpus") and DATABASE.md (§2 rule diagram "dose ≤ corpus p90", §7 rows
    4–5, §8 cut-point row) describe the s3 approach without a corpus.

## Constraints
- STYLE-FIT.md is the design. The §4 and §5 changes above have your agreement (2026-10-15);
  any other change to it needs your agreement first.
- PROJECT.md §6.3: unknown words and unrated ingredients say so; no guessed tags.
- Behaviour (usage effects, cut points) in code, data (tags, envelopes) in `ref` (DATABASE.md §8).
- Deterministic logic is SQL functions in `db/*.sql`, applied with `psql` as `postgres`
  (PROJECT.md §4, G0; CLAUDE.md); one-off load jobs are Python in `loaders/`, giving the same
  rows when run twice.
- The extraction LLM is the D2 model, `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K`, thinking off
  (PROJECT.md §4).
- PROJECT.md §6.7 and CLAUDE.md: the LLM never computes a number; brewing maths stays in s1's
  functions.
- No corpus is loaded (D7).

## Assumptions
- Hop descriptors: measured 2026-10-15, all 90 hops have descriptor text on their hopline page
  (83 with the "Komló aroma" list, 47 distinct words in those lists; 88 with an "Aroma :" line).
  That these words tag most hops without review is *(unverified)*.
- Yeasts: measured 2026-10-15, 118 of 119 have a hopline "Stílus" value and 75 an "Aroma" word
  list; `ref.yeast.type` is ale 75, lager 17, kveik 20, brett 2, empty 5. That 44 yeasts with
  no aroma words still get a character tag from their style and type is *(unverified)*.
- BA guideline text in `ref.beer_style.raw` is prose under the same keys as BJCP (`aroma`,
  `flavor`, `mouthfeel`), measured for the 3 BA styles in scope.
- `ref.fermentable_style` lists 59 of 81 fermentables and no flakes or sugars (measured
  2026-10-15), so the bump never touches the adjunct/sugar rule's ingredients.
- *How to Brew* and the OBC *Recipe Formulation* PDF (both in `shared/rag-files/pending/`) give
  enough hop-rate and roast-proportion figures to set most cut points *(unverified)*.
- 26 envelopes take you about 1.5–2.5 hours to review *(estimate)*.

## Acceptance criteria
A1. Hop tag coverage: every hop tagged or flagged; the count of flagged hops is reported (R1).
A2. Tagging twice gives identical `ingredient_tag` rows; one added synonym re-tags its
    ingredients (R2).
A3. The 26 styles (3 of them BA, through the same extraction) have envelopes and characteristic
    ingredients with `reviewed = true`, each with its quote (R3, R4).
A4. The Citra table (Citra × 15B / 20B × 60 min / whirlpool / heavy dry hop) reproduces exactly
    from `level()` (R5, R7, G-S).
A5. The golden set passes, you approved it, and it contains the 7 M3 cases and the 16A lactose
    case of R8, with no `style_rule` row for any of them (R5, R8).
A6. 15B without a roast malt fails the required check; with roasted barley it passes (R6).
A7. Each cut point in code has a basis line (book and page, or "set by the user"); no code path
    reads a `corpus.*` table (R5, R7).
A8. A malt listed for a style in `ref.fermentable_style` and otherwise ➖ comes out 👍 with a
    because naming the list; a hop or yeast that is otherwise ➖ stays ➖ (R5).
A9. The reference-recipe check runs as a test: 0 ⚠️/⛔ outside b16 rice, b19 honey, b20 lactose
    and the exceptions you accepted (R9).
A10. D9 is no longer in PROJECT.md §7; STYLE-FIT.md §4 and §5 describe the book cut points, the
    adjunct/sugar rule and the `fermentable_style` bump; a grep of STYLE-FIT.md,
    WORKFLOW-ROADMAP.md, RECIPE-ROADMAP.md §5 and DATABASE.md §2, §7, §8 finds no corpus route
    for style fit and no "revisit in s3" note (R10).

## Open questions
None. The 5 questions of the 2026-10-15 revision were answered by the user (golden set drafted
by Claude; adjunct/sugar general rule; `fermentable_style` bump; cut points from the books; one
LLM path for BA).

## Deviations
- 2026-10-15 · Scope, R5, R7, R10: STYLE-FIT.md §4 and §5 change (cut points from *How to Brew*
  and OBC instead of the corpus; a general adjunct/sugar rule from the style's characteristic
  ingredients; step 4's corpus popularity bump replaced by `ref.fermentable_style`, fermentables
  only) — the corpus was abandoned (D7) and STYLE-FIT §3 gives flakes and sugars no sensation;
  agreed by the user 2026-10-15.
- 2026-10-15 · Scope, Constraints, R10: STYLE-FIT.md §6 is now in scope too: its "a style" row
  becomes "BJCP and BA: LLM extract + your review (BA parser later)" — it said "BA: parsed",
  which contradicts the decided D9; agreed by the user at plan approval 2026-10-15.
