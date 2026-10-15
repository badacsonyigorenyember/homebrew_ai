# S3 · Golden set (Task 6) — approved 2026-10-15

> **Status: approved by the user 2026-10-15** (report.md §5). Drafted by Claude from brewing
> judgement and the reviewed envelopes; every theme was approved as drafted, except y02 (US-05 in
> 10A), which the user set to ⚠️ through the yeast min check. The cases live in
> [`tests/fixtures/style_fit_golden.toml`](../../../tests/fixtures/style_fit_golden.toml); this page
> shows the same cases, one table per theme. `level()` is built to pass them in Task 8.

How to read a row: **style · ingredient · usage · dose → expected level**, and the *because* a
homebrewer can check. Cut points: [cut-points.md](cut-points.md).

Levels: ✅ required · 👍 typical · ➖ allowed · ⚠️ out of style · ⛔ changes style · — not rated.
✅ is a recipe-level check (R6), so no case expects it.

Counts: 53 cases; by theme c 6, m 8, a 7, f 4, h 4, y 8, t 5, i 9, u 2.


## c · Citra table (A4) (6)

RECIPE-ROADMAP §5's six Citra cases. 15B: hop aroma none–low, earthy/floral; 20B: very low–medium, citrus/resin. Citra oil 2.25 mL/100 g.

| Id | Style | Ingredient | Usage | Dose | Expected | Because |
|---|---|---|---|---|---|---|
| c01 | 15B | Citra | boil | 60 min, 1.0 g/L, 35 IBU | ➖ allowed | a 60-min hop gives bitterness only, its character does not carry; 35 IBU is inside 15B's 25-45 |
| c02 | 15B | Citra | whirlpool | 2.0 g/L | ⚠️ out of style | citrus/tropical vs 15B's 'earthy or floral' hops: wrong character (and 0.045 mL/L oil is medium, above 15B's low) |
| c03 | 15B | Citra | dry_hop | 8.0 g/L | ⚠️ out of style | wrong character, and 0.18 mL/L oil is very high, far above 15B's low hop aroma |
| c04 | 20B | Citra | boil | 60 min, 1.0 g/L, 50 IBU | ➖ allowed | bitterness only; 50 IBU is inside 20B's 35-75 |
| c05 | 20B | Citra | whirlpool | 2.0 g/L | 👍 typical | citrus matches 20B's 'citrusy or resiny'; 0.045 mL/L oil is medium, at 20B's max |
| c06 | 20B | Citra | dry_hop | 8.0 g/L | ⚠️ out of style | character matches, but 0.18 mL/L oil is very high, above 20B's medium hop aroma |

## m · M3 ingredient cases and 16A lactose (R8) (8)

The brief's ingredient deviations (⚠️) and the adjuncts/sugars the styles name (not ⚠️), all through the adjunct/sugar rule, no `style_rule` row.

| Id | Style | Ingredient | Usage | Dose | Expected | Because |
|---|---|---|---|---|---|---|
| m01 | 18B | Flaked Rice | mash | 15 % | ⚠️ out of style | b16: an adjunct 18B's characteristic ingredients do not name: not a usual ingredient of American Pale Ale |
| m02 | 17C | Honey | boil | 10 % | ⚠️ out of style | b19: 17C names base, crystal, roast and adjunct grains, no sugar or honey |
| m03 | 19C | Lactose | boil | 5 % | ⚠️ out of style | b20: 19C names no sugar; lactose makes a milk brown, not an American Brown Ale |
| m04 | 21C | Flaked Oats | mash | 20 % | 👍 typical | b02: 21C names Flaked Oats ('more flaked grains') |
| m05 | 1B | Flaked Rice | mash | 25 % | 👍 typical | b06: 1B names rice ('up to 40% rice or corn as adjuncts') |
| m06 | 1C | Flaked Corn | mash | 20 % | 👍 typical | b07: 1C names corn ('Up to 20% maize in the mash') |
| m07 | 31B | Honey | boil | 12 % | 👍 typical | b12: 31B names the role sugar and Honey (reviewed sugar row); rated although it has no sensory rows |
| m08 | 16A | Lactose | boil | 10 % | 👍 typical | 16A names Lactose; the adjunct/sugar rule says it, no style_rule row |

## a · Adjunct/sugar rule, more cases (7)

An adjunct or sugar is 👍 when the style's reviewed characteristic ingredients name it (or its role), else ⚠️.

| Id | Style | Ingredient | Usage | Dose | Expected | Because |
|---|---|---|---|---|---|---|
| a01 | 21A | Lactose | boil | 5 % | ⚠️ out of style | 21A names no sugar: lactose in an IPA stays out of style (Task 5 decision A) |
| a02 | 26B | Brown Candi Sugar | boil | 10 % | 👍 typical | b10: 26B names Brown Candi Sugar ('caramelized sugar syrup or unrefined sugars') |
| a03 | 15B | Flaked Barley | mash | 20 % | 👍 typical | b05: 15B names the adjunct role ('May use unmalted grains for body') |
| a04 | 5D | Flaked Corn | mash | 10 % | ⚠️ out of style | 5D names no adjunct (German Pils is an all-malt beer) |
| a05 | 18A | Honey | boil | 12 % | 👍 typical | b12's recipe style: 18A names Honey ('sugar adjuncts') |
| a06 | specialty-honey-beer | Honey | boil | 15 % | 👍 typical | the BA style requires honey (reviewed sugar row); rated although it has no sensory rows |
| a07 | mexican-style-amber-lager | Flaked Corn | mash | 15 % | 👍 typical | b22: the BA style names corn and rice |

## f · `fermentable_style` bump (A8) (4)

Base and kilned malts drive no sensation (➖); a malt the maltster lists for the style moves to 👍. Hops and yeasts never move.

| Id | Style | Ingredient | Usage | Dose | Expected | Because |
|---|---|---|---|---|---|---|
| f01 | 6A | Weyermann Munich Malt Type 2 | mash | 50 % | 👍 typical | b09: a kilned malt drives no sensation (allowed), and Weyermann lists it for Maerzen: bumped to typical |
| f02 | 26B | Weyermann Munich Malt Type 2 | mash | 17 % | ➖ allowed | b10: the same malt, not listed for 26B in ref.fermentable_style: no bump |
| f03 | 21A | Magnum | boil | 60 min, 55 IBU | ➖ allowed | bittering only, 55 IBU inside 40-70; hops are never bumped |
| f04 | 5D | Fermentis SafLager W-34/70 | ferment | 12 °C | ➖ allowed | a lager yeast: esters none, phenols none, inside 5D; yeasts are never bumped |

## h · Hop character (4)

Late hops carry character: best pair of tags, 1.0 same → 👍, 0.5 parent/child → ➖, 0 → ⚠️.

| Id | Style | Ingredient | Usage | Dose | Expected | Because |
|---|---|---|---|---|---|---|
| h01 | 11B | East Kent Golding | whirlpool | 1.5 g/L | 👍 typical | floral matches 11B's 'floral, earthy, resiny, or fruity'; 0.013 mL/L oil is medium-low, under 11B's medium |
| h02 | 5D | Citra | whirlpool | 1.5 g/L | ⚠️ out of style | citrus/tropical vs 5D's 'flowery, spicy, or herbal hops': wrong character |
| h03 | 5D | Saaz | whirlpool | 2.5 g/L | 👍 typical | herbal matches 5D; 0.015 mL/L oil is medium-low, under 5D's medium-high |
| h04 | 26B | Styrian Golding | boil | 10 min, 1.0 g/L, 20 IBU | ➖ allowed | pepper is a child of 26B's 'spicy' (match 0.5, allowed); 0.0075 mL/L oil is very low, 20 IBU inside 15-25 |

## y · Yeast character and ester/phenol levels (8)

Yeast drives esters and phenols (E1–E4, P1–P3 of cut-points.md). Too much: above the max. Too little: more than one level below the min (yeast only; skipped for needs-review yeasts).

| Id | Style | Ingredient | Usage | Dose | Expected | Because |
|---|---|---|---|---|---|---|
| y01 | 10A | Lallemand Munich Classic | ferment | 19 °C | 👍 typical | weizen yeast: banana matches 10A's esters; phenols medium; esters medium-low are one level under 10A's min medium, which the one-level tolerance allows |
| y02 | 10A | Fermentis SafAle US-05 | ferment | 19 °C | ⚠️ out of style | clean ale yeast: esters very low and phenols none, more than one level below 10A's medium (min): too little banana and clove |
| y03 | 26B | Lallemand Abbaye | ferment | 21 °C | 👍 typical | Belgian yeast: spicy matches 26B's phenols; phenols medium at 26B's max; esters medium-low, one level under 26B's medium (tolerated) |
| y04 | 15B | Fermentis SafAle S-04 | ferment | 18 °C | 👍 typical | b05: fruity matches 15B's esters; medium-low is at 15B's max |
| y05 | 17C | Lallemand Windsor | ferment | 18 °C | ➖ allowed | b19: fruity is the parent of 17C's 'dried-fruit' (match 0.5); esters medium-low under 17C's medium |
| y06 | 18A | Lallemand Belle Saison | ferment | 24 °C | ⚠️ out of style | saison yeast in a clean ale: peppery phenols where 18A allows none |
| y07 | 21A | Lallemand New England | ferment | 19 °C | ⚠️ out of style | a fruity yeast: esters medium-low, above 21A's 'Low esters optional' (max low) |
| y08 | 25B | Lallemand Belle Saison | ferment | 26 °C | 👍 typical | b11: citrus and pepper match 25B; warm (26 C) esters medium and phenols medium-high, inside 25B |

## t · Transforming and specialty sensations (5)

A style silent on a transforming sensation (sourness, brett funk) → ⛔; on a specialty one (smoke, spice…) → ⚠️.

| Id | Style | Ingredient | Usage | Dose | Expected | Because |
|---|---|---|---|---|---|---|
| t01 | 21A | Fermentis SafBrew BR-8 | ferment | 20 °C | ⛔ changes style | brett yeast: brett funk is transforming and 21A is silent on it (a wild specialty, 28A) |
| t02 | 23A | Lallemand Philly Sour | ferment | 22 °C | 👍 typical | 23A wants sourness; stone-fruit matches 23A's esters; warm esters medium at 23A's max |
| t03 | 18B | Lallemand Philly Sour | ferment | 22 °C | ⛔ changes style | sourness is transforming and 18B is silent on it: a sour pale ale is another style |
| t04 | 6A | Weyermann Beech Smoked Barley Malt | mash | 20 % | ⚠️ out of style | smoke is a specialty sensation and 6A is silent on it: a smoked Maerzen (Rauchbier, 6B) |
| t05 | 10A | Weyermann Oak Smoked Wheat Malt | mash | 20 % | ⚠️ out of style | specialty smoke on 10A; Weyermann lists it for 10A, but the bump only lifts allowed, never out_of_style |

## i · Intensity cut points and style ranges (9)

Roast index and oil dose against the envelope max (R1–R7, O1–O7); IBU and SRM against the style range.

| Id | Style | Ingredient | Usage | Dose | Expected | Because |
|---|---|---|---|---|---|---|
| i01 | 15A | Weyermann Roasted Barley | mash | 5 % | ⚠️ out of style | roast index 5750 is medium, above 15A's low roast: too much |
| i02 | 15A | Weyermann Roasted Barley | mash | 2 % | 👍 typical | roast index 2300 is low, at 15A's max; coffee/roast matches |
| i03 | 15B | Weyermann Roasted Barley | mash | 10 % | 👍 typical | the classic dry-stout dose: roast index 11500 is medium, at 15B's max; coffee/roast matches |
| i04 | 15B | Weyermann Roasted Barley | mash | 15 % | ⚠️ out of style | roast index 17250 is high, above 15B's medium: too much |
| i05 | 26B | Weyermann Carafa Special Type 2 | mash | 2 % | ⚠️ out of style | roast index 2300 is low; 26B: 'Never roasted or burnt' |
| i06 | 19C | Viking Malt Chocolate Dark Malt | mash | 5 % | 👍 typical | b20: chocolate matches 19C's roast; index 4500 is medium-low, under 19C's medium |
| i07 | 18B | Galaxy | dry_hop | 8.0 g/L | ⚠️ out of style | IPA-level dry hop: 0.32 mL/L oil is very high, above 18B's medium-high |
| i08 | 1B | Magnum | boil | 60 min, 30 IBU | ⚠️ out of style | 30 IBU is above 1B's 8-18: too bitter |
| i09 | 18A | Weyermann Caraaroma | mash | 5 %, 9 SRM | ⚠️ out of style | 9 SRM is above 18A's 3-6: too dark |

## u · Not rated and no dose (2)

What the because says when data is missing.

| Id | Style | Ingredient | Usage | Dose | Expected | Because |
|---|---|---|---|---|---|---|
| u01 | 21B | Citra | dry_hop | 8.0 g/L | — not rated | not rated: 21B (Specialty IPA) has no reviewed envelope |
| u03 | 18B | Simcoe | whirlpool | (none) | 👍 typical | citrus/pine match 18B; dose not given, so the dose check is skipped and the because says so |
