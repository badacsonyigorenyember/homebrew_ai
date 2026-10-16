# BJCP 2021 specialty-entry rules vs D1

Source: *Introduction to Specialty-Type Beer* ("Entering" and "Judging" pages) in
`shared/rag-files/styles/bjcp_2021_introductions.md`, and the Entry Instructions of 28–34 in
`ref.beer_style.raw` (read 2026-10-16). Step 2: `db/022_step2.sql` (unchanged).

## D1 as in PROJECT.md §5
Both guides are scored together; the best fit is the **base style** by default (adjuncts and extras
ignored). A wanted adjunct with role `feature` (set by step 1) that has an entry in
`app.specialty_style()` gives the specialty code (BJCP: honey and molasses → 31B Alternative Sugar
Beer; BA: honey → Specialty Honey Beer), with the base style first among the alternatives. A
`background` adjunct leaves the base style.

## What BJCP 2021 says
- Specialty-Type Beer (categories 28–34) is a "transformation of a Base Style" by a process or by
  Specialty-Type Ingredients: yeast/bacteria, smoke, wood, fruit, spice, grain, sugar.
- A Base Style is a Classic Style (1–27) or "a broad style family"; Specialty-Type beers "may not be used
  as a Base Style" for other specialty beers unless the style's Entry Instructions allow it.
- Entry Instructions (31B and others): the entrant names the sugar, and gives "either a Base Style or the
  ingredients, specs, or target character". So the base style is declared with the specialty entry.
- Best fit: "a style representing the dominant ingredient"; with equal ingredients, the first style
  that qualifies.
- "If judges cannot detect it, they will believe it is absent": an ingredient that cannot be
  perceived does not go in a style that requires it. A single ingredient "should contribute a recognizable character".

## Point by point
| Point | BJCP 2021 | D1 / step 2 | Verdict |
|---|---|---|---|
| Base style by default | Classic Style or family is the base of a specialty entry | Best-fit style is the base; adjuncts ignored | Agrees |
| Specialty only when the ingredient shows | Perceptible, recognizable ingredient | Only `feature` (prominent) gives the specialty code | Agrees in intent; step 2 relies on step 1's role as the stand-in for "perceptible" (cannot see the beer) |
| Base style declared with the specialty entry | Required in most Entry Instructions | Base style is the first alternative, and the reason names it | Agrees |
| Specialty styles never a base style | Not allowed unless the style says so | Step 2 scores all styles, 28–34 included (no category filter in the code); a specialty style can win by name or number and then is the "base". Not measured: no brief or test in this work puts a 28–34 style first | Differs in code; effect unmeasured |
| Which ingredients have a specialty style | Yeast/bacteria, smoke, wood, fruit, spice, grain, sugar | Only honey and molasses (BJCP 31B) and honey (BA) | Narrower: fruit, spice, smoke, wood, alternative grain, other sugars (maple, brown sugar, agave) and sour/Brett processes stay on the base style even as `feature` |
| Several ingredients | The dominant one decides; equal → first qualifying style | First of the matching adjuncts in alphabetical order (`order by sp.adjunct`) | Differs; moot while only honey and molasses are listed |
| Role | n/a | Step 1 role `feature` / `background` | D1 addition, consistent with BJCP's "recognizable character" |

## Verdict
D1's core rule matches BJCP 2021: base style by default, specialty style only for an ingredient that
is a recognizable feature, base style kept as the alternative. The gaps are coverage, not
contradiction. Step 2 knows one specialty family (sugar: honey, molasses); BJCP lists seven, and
BJCP's "dominant ingredient" rule would need more than an alphabetical pick once more are listed. A specialty style
can also be returned as the base.

## Proposal (no change made; D1 and `db/` untouched)
Nothing is needed for s6, whose check set is the 83 classic styles. Possible changes, each its own work item if approved:
1. Leave D1 as is (honey/molasses only is a deliberate scope; widen when a recipe type needs it).
2. Widen `app.specialty_style()` to the other BJCP specialty ingredient families and add a
   "dominant ingredient" choice. This is a change to D1.
3. Keep specialty styles (28–34) from being the base style pick in step 2.

Recommendation: 1 for now; measure first whether 28–34 ever wins in a run (s6's runner shows it in the confusions).

## Decision
Declined (user, 2026-10-16, option a): D1 and step 2 stay as they are. The honey/molasses-only scope is deliberate; the s6 runner's confusions can show whether a 28–34 style ever wins as the base pick, and that data can justify widening the list or filtering 28–34 later as its own work item.
