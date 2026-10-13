# M2 · Step 2: pick the best-fit style

Status: approved
Slug: m2-best-fit-style · Branch: m2-best-fit-style
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) M2, checkpoint **G2** ·
[RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §3 step 2, §4 · PROJECT.md §5 (D1 and the R3 rule)
Needs: `m1-read-request` shipped

## Why
The style is the reference every later step designs against and compares with: targets come
from its ranges, ratios from its profile, deviations from its rules. A wrong style makes every
later step "correct" against the wrong thing. The pipeline must always pick one, and say when it
disagrees with the name the user used (b05: a "4 % imperial stout" fits 15B, not 20C).

## Goal
Step 2 picks a style for every brief by code, explains the pick, and flags a mismatch with the
named style. At least 18 of 20 briefs get their expected style or an accepted alternative.

## Scope
In:
- Scoring all 285 styles in `ref.beer_style` (BJCP 2021 116, BA 2026 169) from the step 1 brief
  (the named style, stated numbers, hint and flavour words) and the request text (adjunct
  prominence, a named guide).
- D1: both guides are scored and the best fit wins; where the two guides have the same style
  (5B Kölsch and German-Style Koelsch, 26B and Belgian-Style Dubbel), the BJCP one is used. The
  user can restrict the pick to BJCP only or BA only, in the request text or with the webhook's
  `guide` field.
- A BA ↔ BJCP pair list of equivalent styles: proposed by a script, reviewed by the user once,
  kept as a versioned SQL file.
- The R3 rule: the base style by default; the specialty code when the request makes an adjunct a
  stated, prominent feature, with the base style as the alternative (b12 → 31B, alt 18A).
- A mismatch output when the best fit is not the named style (b05).
- Brief check: two BA briefs, b21 and b22 (Open question 2).

Out:
- Ingredient rules and the Deviations box (M3). Asking the user to confirm (M8; here the mismatch
  is only reported). Sensory envelopes (s3); this step does not wait for them.

## Requirements
R1. Step 2 returns: the chosen style (`ref.beer_style.id`, guide, code, name), a score breakdown
    per signal, the top 5 candidates with scores, `alt_styles` where scores are close, and a
    `mismatch` entry (named style, its range that conflicts, the chosen style) or null.
R2. Scoring is deterministic code (where G0 put it): the same brief gives the same ranking every
    run. No LLM call; equal scores go BJCP first, then by code (Open question 3).
R3. Name signal: the named words match a style's name, code or `raw.tags`; known common names
    that a guide doesn't use ("milk stout" for 16A Sweet Stout, "West Coast IPA" for 21A) come from
    a small alias list in code, each alias with its source (style guide text or a book).
R4. Number signal: each stated ABV, OG, IBU or SRM inside the style's range scores; outside it
    scores by distance. A stated number that rules out the named style produces the mismatch.
R5. Word signal: hint and flavour words count against the style's text (overall impression,
    aroma, flavour, mouthfeel) and `raw.tags`, e.g. "roasty", "hoppy", "malty".
R6. Guide choice: with no restriction both guides are scored and the best fit wins, BJCP or BA,
    with no margin for either. When the winner has an equivalent in the other guide (the reviewed
    pair list), the BJCP style is returned. "BJCP only" or "BA only" scores only that guide; it
    comes from the webhook's `guide` field (`any`, `bjcp`, `ba`; default `any`) or from the
    request text ("BA style", "per BJCP"), read by code, and the field wins when both are given.
    The choice and the reason appear in the output.
R7. Specialty rule (R3, PROJECT.md §5): an adjunct the request makes prominent (b12 honey) picks
    the specialty code with the base style in `alt_styles`; an adjunct that is just used (b19
    honey in a wee heavy) keeps the base style.
R8. The output has a legal "unknown" result for a request no style fits, instead of a forced pick
    with a made-up reason.
R9. The step logs its input, output and timing in `run_step` (step 2).

## Constraints
- PROJECT.md §6.1 and §6.7: style ranges are read by SQL, never by the LLM.
- §6.8: one readable scoring function; signals and weights visible in it, not in a config table.
- The BA ↔ BJCP pair list is reviewed by the user before step 2 uses it. Not every BA style needs
  a pair.
- `ref.beer_style` columns: `guide`, `code`, `name`, `category`, `category_code`, `og`, `fg`,
  `ibu`, `srm`, `abv` (ranges), `characteristic_ingredients`, `raw` (checked on the catalog
  2026-10-12). BA rows have `category_code` NULL.

## Assumptions
- The BJCP `raw.tags` (e.g. 15B: `stout-family, bitter, roasty`) are enough for the word signal
  without s3's envelopes *(unverified; measured by G2)*.
- b01–b20 all expect BJCP codes (checked 2026-10-12); b21 and b22 are the only BA cases.

## Acceptance criteria
A1. The runner shows ≥ 18/20 of b01–b20 with the expected `style` or one of `alt_styles`, and
    b21 and b22 pick their BA style (R1–R7, G2).
A2. b05 picks 15B with a mismatch naming 20C and its ABV range; b12 picks 31B with 18A as an
    alternative; b19 picks 17C (R4, R7).
A3. Two runs on the same brief give identical output (R2).
A4. With "BA only", from the `guide` field or from the request text, b01 picks a BA style, and the
    output says why; when the field and the text disagree, the field wins. With no restriction, a
    BA best fit that has a reviewed BJCP pair returns the BJCP style (German-Style Koelsch → 5B)
    (R6).
A5. A request with no beer in it ("something nice") gives the unknown result (R8).
A6. Unit tests cover each signal on its own: they call each SQL function directly with literal
    inputs, without n8n or the pipeline (they need Postgres, so they keep the `stack` marker)
    (R3–R5).
A7. Every alias in code has a source line (R3).

## Open questions
Answered by the user on 2026-10-13:
1. How does BA win over BJCP? — Neither margin option: both guides are scored and the best fit
   wins; equivalent styles in both guides go to BJCP, through a reviewed pair list; "BJCP only" /
   "BA only" from the request text or the `guide` field (the field wins). Now R6 and A4.
2. Add BA briefs? — Yes: b21 (session IPA, 4 %) and b22 (Mexican amber lager), as written in the
   plan; A1 requires both to pass.
3. LLM tie-break? — Left out (R2).

## Deviations
- 2026-10-13 · Scope, R2, R6, A1, A4, A6, Constraints: the open questions were answered by the
  user. D1 under no restriction is now "best fit wins, BJCP for equivalent styles" with a
  user-reviewed pair list (was: BJCP wins unless BA is ahead by a margin); the BJCP-only / BA-only
  restriction comes from the `guide` field or the request text (was: a profile setting; profiles
  are M4); no LLM tie-break; b21 and b22 added to A1; A6's "without the stack" now means without
  n8n or the pipeline, since the signals are SQL functions (G0). Step 2 also reads the request
  text, for adjunct prominence (R7) and a named guide (R6).
