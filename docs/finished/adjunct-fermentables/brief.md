# Adjunct fermentables

Status: approved
Slug: adjunct-fermentables · Branch: adjunct-fermentables

## Why
`ref.fermentable` holds only the 74 grain malts from three maltsters. There are no flakes, sugars,
lactose or honey. Many mainstream styles depend on these: oats in oatmeal stout and hazy IPA,
corn and rice in American lagers and cream ale, candi sugar in Belgian strong ales, lactose in
sweet stout, honey in honey ales. Without them the pipeline can't build those recipes without
inventing an ingredient, which P5 forbids. Lactose and honey also change the gravity maths.
Lactose raises both OG and FG because yeast can't ferment it. Honey ferments almost completely.
Right now lactose sits in the `ref.misc` categories, and misc items never enter the OG/IBU/SRM
maths.

## Goal
`ref` holds the user's minimum set of adjunct fermentables (oats, candi sugar, corn, rice,
lactose, honey), plus any other ingredient the 20 approved test briefs need. Each one is sourced
and carries what the gravity, FG and colour maths need, including how much of its extract yeast
can ferment.

## Scope
In:
- The six minimum adjuncts, as fermentables (user decision, 2026-10-11).
- Any other ingredient the approved test briefs (`test-briefs`) need that `ref` lacks, and a gap
  report listing what was missing and what was added.
- What the maths needs to treat a fermentable that yeast can't fully ferment. Today that is
  lactose.
- Taking `lactose` out of the `ref.misc` categories, and updating DATABASE.md's rule that extras
  never enter the maths.
- A narrow doc→calc pass on Palmer's *How to Brew* (PROJECT.md §6.7): only the rows of tables
  18.5 and 24.1 that this work loads.

Out:
- Fruit and other extras whose gravity can't be counted reliably (user decision, 2026-10-11).
- Non-gravity extras (spices, herbs, coffee, vanilla, cacao, oak chips) and `ref.misc` rows. The
  test briefs ask for none.
- Process aids: rice hulls, finings, yeast nutrient, enzymes.
- Other adjuncts hopline sells (white candi, fructose, wheat, barley, rye and chit malt flakes,
  malt extracts), unless a test brief needs them (user decision, 2026-10-11).
- `fermentable.role` (filled by code in P3) and style-fit tags.
- The maths itself (P2). This work only stores the data it will read.

## Requirements
R1. `ref` holds at least one fermentable each for flaked oats, candi sugar, flaked corn, flaked
    rice, lactose and honey. Each has an `ingredient` row (kind `fermentable`) and a
    `fermentable` row.
R2. Every new row is sourced: a `ref.source` row, and `field_source` per stated field. A value
    no source states stays `NULL`, never a guess (DATABASE.md "Rules for `ref`").
R3. Each new fermentable has an extract and a colour wherever a source states them.
R4. Each fermentable has a fermentability **category** (user decision, 2026-10-11): `full`
    (sugars, honey), `normal` (grain and flakes, which follow the yeast's attenuation) or `none`
    (lactose). The category is taken from the source's stated fermentability. The existing 74
    malts get `normal` without being reloaded by hand.
R5. `lactose` is no longer a `ref.misc` category. DATABASE.md describes where lactose and honey
    live and how they enter the maths.
R6. A gap report in the work folder lists every ingredient the 20 approved test briefs need, and
    whether it was found in `ref` (with its id), added by this work, or left out (with the
    reason).
R7. Data that hopline.hu sells comes from hopline's own pages, as for malts, hops and yeasts.
    Every figure hopline doesn't print, and all of honey, comes from **one** reference: Palmer's
    *How to Brew*, Table 18.5 (flakes: extract % FGDB) and Table 24.1 (sugars: PPG and
    fermentability), copied as printed (user decision, 2026-10-11). The book gets a `ref.source`
    row.
R8. Loading is repeatable: running the loader twice gives the same rows.

## Constraints
- Database changes are `.sql` files applied with `psql` as `postgres` (CLAUDE.md, OPERATIONS.md
  §4). Never through MCP.
- Units are SI, and every row has a source (DATABASE.md "Rules for `ref`").
- Readable over optimal (PROJECT.md §6.8): an explicit SKU map like `malt_products.py`, not a
  generic config table.
- Brewing maths is code, not data or LLM (CLAUDE.md). Store only what sources state.
  Computed values (potential SG) are not stored.
- Starts after `test-briefs` is approved and its briefs are written (R6 depends on them).
- No git worktree. Plain branch `adjunct-fermentables` (CLAUDE.md).

## Assumptions
- hopline.hu sells, measured 2026-10-11 from its listing pages: flakes (oat `400150`, corn
  `400270`, rice `400100`, also wheat, barley, rye and chit malt), candi sugar (brown `400091-cs`,
  white `400081-cs`), fructose, lactose (`400030-cs`, `400031-cs`) and 7 malt extracts. It sells
  **no honey**.
- The brown candi sugar page prints a colour (225 EBC). A quick look found no extract or colour on
  the oat, corn or lactose pages. *(unverified: not every page checked)*
- Palmer's tables cover all six (measured 2026-10-11 in `shared/rag-files/pending/how_to_brew.pdf`):
  Table 18.5 prints FGDB for flaked oats 70 %, flaked corn 84 % and flaked rice 82 %. Table 24.1
  prints lactose 46 PPG (unfermentable), honey 38 PPG at 95 % and Belgian candi **syrup**
  32 PPG at ~50–80 %. The edition is the expanded 4th. *(unverified: the edition is read from the
  foreword text only)*
- hopline sells candi **sugar** (crystals), but Palmer lists only candi **syrup**. Which Palmer row,
  if any, fits hopline's candi sugar has to be settled in the plan. For example, table sugar
  (46 PPG, 100 %) may fit better than the syrup. *(unverified)*
- PPG converts to extract % by dividing by 46 (sucrose = 100 %), the same basis Palmer uses. This
  is a unit conversion, not a computed value. *(unverified: to confirm in the plan)*
- Honey's 95 % counts as `full`. The P2 maths can work from a category; if it needs a percentage
  later, that can replace the category. *(unverified: P2 not designed yet)*

## Acceptance criteria
A1. A query finds `ingredient` + `fermentable` rows for flaked oats, candi sugar, flaked corn,
    flaked rice, lactose and honey (R1).
A2. A query returns 0 new ingredient rows without a source, and every non-null new field has a
    `field_source` entry (R2).
A3. A query shows extract and colour filled for every new fermentable whose source states them.
    Each `NULL` is listed in the report with the reason (R3).
A4. A query shows the fermentability category `none` for lactose, `full` for honey and candi
    sugar, and `normal` for the flakes and the 74 malts (R4).
A5. `ref.misc`'s category check no longer accepts `lactose`, and DATABASE.md's rules describe
    lactose and honey as fermentables (R5).
A6. The gap report covers every ingredient named in the 20 approved test briefs. Each one is
    found, added or left out with a reason (R6).
A7. Spot check: every new row's values match their printed source (R2, R7).
A8. The loader is run twice with identical counts and values, and `pytest` passes in full (R8).

## Open questions
None. Answered by the user on 2026-10-11: honey from Palmer, one reference table (Palmer) for
figures hopline doesn't print (R7), only the six plus test-brief gaps (Scope), and fermentability
as a category (R4).

## Deviations
