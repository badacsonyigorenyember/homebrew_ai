# S3 · Style fit: tags, envelopes and the level function (P3, D9)

Status: draft
Slug: s3-style-fit · Branch: s3-style-fit
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) side track P3, checkpoint **G-S** ·
[STYLE-FIT.md](../../STYLE-FIT.md) · [RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §5
Needs: `s2-corpus` shipped (corpus popularity and intensity cut points)
s2-corpus abandoned 2026-10-14; revisit in this brief

## Why
Steps 3, 7–9 and 11 must answer "is this ingredient, used this way, in this style: required,
typical, allowed, out of style or style-changing?" without a hand-written row for every
ingredient × style pair. STYLE-FIT.md designs this; none of it is built. Ingredient deviations
(M3) and in-style choices (M5) wait for it.

## Goal
`level(style, ingredient, usage, dose)` returns one of the five levels with a "because", from
data: ingredient tags derived by code, style envelopes reviewed by you, usage effects in code.
The Citra table (RECIPE-ROADMAP §5) reproduces, and the golden test set passes.

## Scope
In:
- Tag vocabulary (`ref.tag`, parent tree) and the descriptor dictionary (`ref.tag_synonym`,
  ~150 words).
- Automatic tagging of hops (origin, page descriptors), fermentables (role from s2, name),
  yeasts (family, character from notes) into `ref.ingredient_tag`; unknown words flagged
  `needs_review`, never guessed.
- `ref.sensory_dimension` with its classes (core · specialty · transforming).
- Envelopes (`ref.style_sensory`, `ref.style_character`) for the 22 brief styles: BJCP prose
  extracted by an LLM offline, reviewed by you (D9).
- Usage effects and intensity cut points in code (STYLE-FIT.md §3, §4), cut points calibrated on
  s2's profiles.
- `level()` as in STYLE-FIT.md §5, and a golden test set of ~50 cases you approve.
- `ref.style_rule` overrides only where an envelope can't say it (e.g. 16A: lactose 👍).

Out:
- Envelopes for the other 263 styles (later, on demand). Misc ingredients and `ref.misc` rows
  (no brief uses a non-gravity extra). BA field parsing beyond the brief styles.

## Requirements
R1. Every hop has at least one character tag or is flagged `needs_review` (DATABASE.md §7 row 3).
R2. Tagging is code: re-running it gives the same tags; adding a synonym re-tags every ingredient
    that uses the word.
R3. Envelopes for the 22 brief styles hold a min–max level per dimension and the allowed
    characters, each with the quote it came from, and `reviewed = true` only after your review.
R4. The LLM extraction of BJCP prose is an offline job whose output you review before it enters
    `ref`; it never runs in the recipe pipeline.
R5. `level()` follows STYLE-FIT.md §5: override first, then per sensation, combine, popularity
    bump (≥ 15 % of the style's corpus recipes → 👍). It returns the level and a because text
    naming the sensation, quote or number used.
R6. "Required" is checked on a whole recipe from the style's characteristic ingredients as role
    requirements (e.g. 15B: roast present).
R7. A golden set of ~50 (style, ingredient, usage, dose → level) cases, approved by you, runs as
    tests; the RECIPE-ROADMAP §5 Citra table is part of it.
R8. D9 moves from PROJECT.md §7 to the relevant section with its *why*.

## Constraints
- STYLE-FIT.md is the design; a change to it needs your agreement first.
- PROJECT.md §6.3: unknown words and unrated ingredients say so; no guessed tags.
- Behaviour (usage effects, cut points) in code, data (tags, envelopes) in `ref` (DATABASE.md §8).
- The extraction LLM is the D2 model chosen in M1 *(if M1 has shipped; else the best pulled one)*.

## Assumptions
- hopline hop descriptions in `ref.ingredient.raw` hold enough descriptor words to tag most hops
  *(unverified)*.
- 22 envelopes take you about 1–2 hours to review *(estimate)*.

## Acceptance criteria
A1. Hop tag coverage: every hop tagged or flagged; the count of flagged hops is reported (R1).
A2. Tagging twice gives identical `ingredient_tag` rows (R2).
A3. 22 brief styles have envelopes with `reviewed = true` (R3, R4).
A4. The Citra table (Citra × 15B / 20B × 60 min / whirlpool / heavy dry hop) reproduces exactly
    from `level()` (R5, G-S).
A5. The golden set passes, and you approved it (R7).
A6. 15B without a roast malt fails the required check; with roasted barley it passes (R6).
A7. D9 is no longer in PROJECT.md §7 (R8).

## Open questions
1. Golden set: who writes the first draft? — options: a) generated from the brief styles and
   their typical ingredients, you correct it; b) you write it — recommend a.
2. Rice in 18B (b16) and honey in 17C (b19) must come out ⚠️ for M3. Is "specialty sensation"
   the right path for them, or an override row? — options: a) let the envelope decide, add an
   override only if it doesn't; b) override rows now — recommend a.

## Deviations
