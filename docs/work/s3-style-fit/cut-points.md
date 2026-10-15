# S3 · Cut points (Task 6) — approved 2026-10-15

> **Status: approved by the user 2026-10-15** (every value as proposed; report.md §4). Each value
> goes into `app.style_fit_cut_points()` (Task 7) with its basis: the book and page, or "set by
> the user, 2026-10-15".

A **cut point** turns a dose into a level on the 0–7 scale (none · very low · low · medium-low ·
medium · medium-high · high · very high). Each scale has 7 ascending thresholds; the level is how
many of them the dose reaches. Above the style envelope's **max** → ⚠️ "too much". The **min**
is checked with a one-level tolerance (user, 2026-10-15; see "Min check" below): more than one
level below it → ⚠️ "too little", per ingredient for yeasts only, on recipe totals for hops and
roast. In the reference-recipe lines below "wrong side" means above the max; recipes below a
style's min are listed under "Min check" at the end.

Sources (doc → calc pass, `pdftotext -layout`, printed page numbers):
- **HTB** = Palmer, *How to Brew* (4th ed., 2017), `shared/rag-files/pending/how_to_brew.pdf`.
- **OBC** = Oregon Brew Crew, *Recipe Formulation*, `shared/rag-files/pending/obc_recipe_formulation.pdf`.
- Neither book puts a figure on a 0–7 scale. The derived values below map book doses (rates,
  grist shares, the book's own recipes) onto the BJCP intensity words of the style they belong to.

Conventions in the arithmetic:
- HTB's recipes put **23 L** into the fermenter (p. 377: "six gallons (23 L) of wort at the target
  OG"); its rules of thumb are per 5 gal (19 L). Hop oil uses the `ref.hop` midpoint of the named
  hop (median of all 89 hops: 1.6 mL/100 g); colour uses the book's stated °L × 1.97 = EBC
  (`app.ebc_from_srm`).
- "Reference recipes" = the 22 user-approved recipes in `tests/fixtures/reference_recipes.toml`,
  rated on paper with the proposed values. A recipe is on the **wrong side** if its dose reaches a
  level above its style's max. Result: **none is on the wrong side.**

## Summary

| Id | Scale | Level reached | Value | Basis |
|---|---|---|---|---|
| O1 | oil mL/L | very low | 0.003 | HTB p. 71 (derived) |
| O2 | oil mL/L | low | 0.008 | HTB p. 71 (derived) |
| O3 | oil mL/L | medium-low | 0.012 | HTB p. 72 (derived) |
| O4 | oil mL/L | medium | 0.025 | HTB pp. 71–72 (derived) |
| O5 | oil mL/L | medium-high | 0.05 | HTB p. 71, pp. 399–400 (derived) |
| O6 | oil mL/L | high | 0.08 | HTB p. 72, pp. 401–402 (derived) |
| O7 | oil mL/L | very high | 0.15 | HTB p. 72 range; value set by the user, 2026-10-15 |
| R1 | roast index | very low | 700 | HTB p. 231 (derived) |
| R2 | roast index | low | 1500 | HTB p. 231 (derived) |
| R3 | roast index | medium-low | 4000 | HTB p. 230 (derived) |
| R4 | roast index | medium | 5500 | HTB pp. 230, 404 (derived) |
| R5 | roast index | medium-high | 12000 | HTB pp. 231, 410–413 (derived) |
| R6 | roast index | high | 16000 | set by the user, 2026-10-15 |
| R7 | roast index | very high | 22000 | set by the user, 2026-10-15 |
| E1 | esters base | lager family | 0 | OBC p. 6 (qualitative); value set by the user, 2026-10-15 |
| E2 | esters base | no ester character | 1 | set by the user, 2026-10-15 |
| E3 | esters base | an ester character | 3 | set by the user, 2026-10-15 |
| E4 | esters step | warm fermentation | +1 above 21 °C | HTB p. 443 (21 °C); step size set by the user, 2026-10-15 |
| P1 | phenols base | a phenolic character | 4 | set by the user, 2026-10-15 |
| P2 | phenols tags | which tags are phenolic | clove, pepper, phenolic, spicy | set by the user, 2026-10-15 |
| P3 | phenols step | warm fermentation | +1 above 21 °C | HTB p. 443; step set by the user, 2026-10-15 |
| — | character match | 👍 / ➖ | ≥ 0.8 / ≥ 0.3 | decided, STYLE-FIT §5 |

Not covered by any scale (as planned): **caramel** (crystal malts drive caramel, sweetness, body
and colour, but no caramel dose scale exists, so a crystal malt is never "too much" caramel; its
colour is still checked through the recipe SRM); **sourness, brett funk, smoke, spice** are
present/absent only (STYLE-FIT §4).

---

## How the two dose scales are computed

- **Oil dose** (hop aroma and hop flavour): Σ over late hop lines (boil < 30 min, whirlpool, dry
  hop) of g/L × the hop's `total_oil_ml_100g` midpoint ÷ 100 → mL of hop oil per litre of beer.
  Example: Citra (1.5–3 → 2.25 mL/100 g) at 2 g/L = 0.045 mL/L.
- **Roast index** (roast): Σ over roast-role malts of % of grist × EBC midpoint. Example:
  Weyermann Roasted Barley (1000–1300 → 1150 EBC) at 5 % = 5750.
- Note on colour: `ref` roast malts are darker than the ones HTB names (HTB's roast barley is
  300 °L ≈ 590 EBC in its recipes, 500 °L ≈ 985 EBC on p. 231; Weyermann's is 1150 EBC). The
  same grist share therefore gives a higher index with `ref` malts. The book anchors below use the
  book's own colours.

## Citra table on paper (A4)

Citra midpoint oil 2.25 mL/100 g; 20B hop aroma max medium, 15B max low.

| Use | Oil dose | Level | 15B (max low) | 20B (max medium) |
|---|---|---|---|---|
| whirlpool 2 g/L | 0.045 | medium (O4 ≤ 0.045 < O5) | ⚠️ (too much, and wrong character) | 👍 at max, character citrus |
| dry hop 8 g/L | 0.18 | very high (≥ O7) | ⚠️ | ⚠️ too much |

The table holds for any O5 in (0.045, 0.18]. O5 = 0.05 leaves a 10 % margin.

---

## O1 · oil, very low — 0.003 mL/L

- **Measures:** the smallest late-hop dose that gives any hop aroma or flavour.
- **Value:** 0.003 mL oil per L (e.g. 0.2 g/L of a 1.6 mL/100 g hop).
- **Source:** HTB p. 71, finishing hops "0.25–4.0 oz. (7–120 g)". Smallest addition:
  7 g ÷ 23 L × 1.0 mL/100 g ÷ 100 = 0.0030.
- **Reference recipes:** binding only for a style with max *none*: 23A (b14) has no late hops. ✓

## O2 · oil, low — 0.008 mL/L

- **Measures:** where a late addition stops being "very low".
- **Value:** 0.008 mL/L.
- **Source:** HTB p. 71, flavouring additions "0.25–0.5 oz. (7–15 g)". Top of that:
  15 g ÷ 19 L × 1.0 ÷ 100 = 0.0079.
- **Reference recipes:** binding for max *very low*: b09 6A (Märzen, hop aroma max very low) has
  one 10-min Hallertau addition = **0.0068** → very low ✓ (15 % below O2). b17 8B is also 0.0068
  (max medium-low). 17C and 10A (max very low on one dimension) have no late hops. ✓

## O3 · oil, medium-low — 0.012 mL/L

- **Measures:** a modest, clearly noticeable hop aroma (British bitter level).
- **Value:** 0.012 mL/L.
- **Source:** HTB p. 72, dry hopping rates for British pale ales "0.5–1 lb. per barrel" (imperial,
  163.7 L) = 1.39–2.77 g/L. Low end with East Kent Golding (0.85): 1.39 × 0.85 ÷ 100 = 0.0118.
- **Reference recipes:** binding for max *low* (1B, 10A, 15A, 15B, 16A, 26B, Mexican lager, 6A
  flavour): highest is b09 at 0.0068 ✓, b22 0.0045 ✓.

## O4 · oil, medium — 0.025 mL/L

- **Measures:** a moderate hop aroma (American pale ale's lower end).
- **Value:** 0.025 mL/L.
- **Source:** HTB p. 72, top of the British pale ale dry-hop rate: 2.77 × 0.85 ÷ 100 = 0.0236;
  HTB p. 71, "A total of 1–2 oz. (30–60 g) is typical" for finishing: 60 g ÷ 23 L × 1.0 ÷ 100 =
  0.026.
- **Check:** HTB's American pale ale "Lady Liberty" (p. 394), 30 g Cascade at 15 min + 30 g
  steeped, 23 L: 60 × 1.15 ÷ 100 ÷ 23 = 0.030 → medium, inside 18B's medium–medium-high ✓.
- **Reference recipes:** binding for max *medium-low* (16B, 1C, 8B aroma): b17 0.0068 ✓.
- Note: b08 5D (0.0165) comes out medium-low, under 5D's min *medium*. One level short of the min: tolerated.

## O5 · oil, medium-high — 0.05 mL/L

- **Measures:** a strong hop aroma short of IPA level.
- **Value:** 0.05 mL/L.
- **Source:** HTB p. 71, finishing range up to "4.0 oz. (120 g)": 120 ÷ 23 × 1.0 ÷ 100 = 0.052.
  HTB's English IPA "Victory & Chaos" (pp. 399–400): 60 g First Gold + 60 g East Kent Golding
  steeped/dry, 23 L: (60 × 1.1 + 60 × 0.85) ÷ 100 ÷ 23 = 0.051 → medium-high ✓ ("moderate to
  high" for English IPA).
- **Citra table:** whirlpool 2 g/L = 0.045 stays medium (≤ 20B's max) ✓; must be > 0.045.
- **Reference recipes:** binding for max *medium* (11B, 18A, 19C, 25B, 20B, 15B flavour, 8B
  flavour): highest b11 0.0060, b20 0.0057 ✓ (b16 18B, 0.0415, has max medium-high).

## O6 · oil, high — 0.08 mL/L

- **Measures:** IPA-level hop aroma.
- **Value:** 0.08 mL/L.
- **Source:** HTB p. 72, today's IPAs dry hopped "0.5–1 oz./gal. (7.5–15 g/L)". Low end with a
  Cascade-class hop (1.15): 7.5 × 1.15 ÷ 100 = 0.086. HTB's American IPA "Rushmore"
  (pp. 401–402): 45 g each of Cascade, Amarillo, Centennial at 15 min, steeped and dry, 23 L:
  (45 × 1.15 + 45 × 1.7 + 45 × 1.85) ÷ 100 ÷ 23 = 0.092 → high ✓ (21A: high–very high).
- **Reference recipes:** binding for max *medium-high* (18B, 5D, 20C): b16 18B **0.0415** ✓
  (48 % below), b08 0.0165 ✓.

## O7 · oil, very high — 0.15 mL/L

- **Measures:** heavy modern dry hopping (hazy / double IPA).
- **Value:** 0.15 mL/L. **Basis: HTB p. 72 range; value set by the user, 2026-10-15.**
- **Source:** HTB p. 72, "0.5–1 oz./gal. (7.5–15 g/L)" × the median `ref` hop oil 1.6 =
  0.12–0.24. 0.15 ≈ 9.5 g/L of a median hop.
- **Why 0.15:** inside the book's modern-IPA range, and well above the session IPA reference.
- **Citra table:** dry hop 8 g/L = 0.18 → very high ✓.
- **Reference recipes:** binding for max *high* (session IPA, 20B flavour): b21 **0.0774** ✓
  (48 % below). b02 21C (0.225) and b01 21A (0.097) are within their max *very high*. ✓

## R1 · roast, very low — index 700

- **Measures:** a roast malt used for colour only: barely tasted.
- **Value:** 700 (% of grist × EBC).
- **Source:** HTB p. 231, black malt for colour, "1–2 oz./5 gal. (30–60 g/19 L)". 30 g in a
  ~4.5 kg grist = 0.67 % × 1083 EBC (550 °L) = 722.
- **Reference recipes:** binding for max *none* (6A b09, 26B b10): neither has a roast malt ✓.
  OBC p. 5 for scale: an alt with 2 % chocolate and 1 % black malt "but it's brown".

## R2 · roast, low — index 1500

- **Measures:** roast you can taste a little; colour highlights.
- **Value:** 1500.
- **Source:** HTB p. 231, top of the same black-malt range: 60 g ÷ 4.5 kg = 1.33 % × 1083 = 1444.
- **Check:** HTB p. 388, Irish red gets "about 3% by weight roasted malt": 3 × 591 (300 °L) =
  1773; its recipe "Fuil Croi" (p. 389) = 150 g roast barley in 4.15 kg = 3.6 % × 591 = 2135 →
  low ✓ (15A: roast low).
- **Reference recipes:** no style in the 26 has roast max *very low*. ✓

## R3 · roast, medium-low — index 4000

- **Measures:** a clear roast note that does not lead.
- **Value:** 4000.
- **Source:** HTB p. 230, roasted malts "typically 1%–5% of the grain bill"; 4 % of HTB's
  500 °L roast barley (p. 231) = 4 × 985 = 3940.
- **Reference recipes:** binding for max *low*: **b18 15A = 3450** (2 % roasted barley +
  1.5 % Carafa Special 1) → low ✓ (14 % below R3); b19 17C = 2100 ✓.

## R4 · roast, medium — index 5500

- **Measures:** moderate roast (dry stout, porter).
- **Value:** 5500.
- **Source:** HTB p. 230 top of 1–5 %, with black malt 550 °L: 5 × 1083 = 5417. HTB p. 404,
  black IPA: "the roast malt additions should be 5% or less of the grain bill", not dominated by
  roast: 5 % de-bittered black (500 °L) = 4925 → medium-low ✓.
- **Reference recipes:** no style in the 26 has roast max *medium-low*. b05 15B = 5750 → medium,
  which meets 15B's min *medium*. ✓

## R5 · roast, medium-high — index 12000

- **Measures:** roast stronger than any of the book's stouts.
- **Value:** 12000.
- **Source:** every HTB stout and porter lands at medium: "Mill Run" Irish stout (p. 412) 10 243
  (10.9 % roast barley 300 °L + 4.8 % dark chocolate 400 °L; the recipe prints "4.3 kg" for
  6.25 lb pale malt, read as 2.8 kg); imperial stout "Namorada Bela" (p. 413) 10 403; "Palmer's
  Porter" (p. 410) 8662. HTB p. 231, roast barley for stout "0.5–1 lb. per 5 gal." at 500 °L in
  Mill Run's 4.1 kg grist = 5.5–10.9 % × 985 = 5400–10 740. R5 sits just above.
- **Reference recipes:** binding for max *medium* (15B, 16B, 19C, 8B): **b03 16B = 7950** ✓
  (34 % below), b05 5750, b20 4500, b17 3450 ✓. 10 % Weyermann Roasted Barley in 15B = 11 500 →
  still medium (golden case i03).

## R6 · roast, high — index 16000

- **Measures:** strongly roasted (big American or imperial stout).
- **Value:** 16000. **Basis: set by the user, 2026-10-15** (not in the books).
- **Why 16000:** about 14 % of a 1150 EBC roast malt; one clear step above R5.
- **Reference recipes:** binding for max *medium-high* (20C): no 20C reference recipe. ✓

## R7 · roast, very high — index 22000

- **Measures:** aggressive, acrid roast.
- **Value:** 22000. **Basis: set by the user, 2026-10-15** (not in the books).
- **Why 22000:** about 19 % of a 1150 EBC roast malt; only 20B allows very high.
- **Reference recipes:** binding for max *high* (16A): b04 16A = 7700 ✓.

## E1 · esters, lager family — 0

- **Measures:** the ester level a lager yeast gives at lager temperatures.
- **Value:** 0 (none), for any yeast with family `lager`, whatever its character tags.
- **Source:** OBC p. 6, a lager strain "that can ferment well in the mid 50 degree range"; other
  yeasts give too many esters there. The 0 itself: **set by the user, 2026-10-15**.
- **Reference recipes:** lagers in 1B, 5D, 6A, 8B, Mexican lager (b06, b08, b09, b17, b22) → 0,
  all ≤ max ✓. A rule choice: SafLager S-23 (tagged fruity, estery) also gets 0.

## E2 · esters, ale with no ester character — 1

- **Measures:** a "clean" ale yeast (US-05, BRY-97, the YeastFlow strains without descriptors).
- **Value:** 1 (very low). **Basis: set by the user, 2026-10-15** (not in the books).
- **Why 1:** clean ales are not ester-free; 1 keeps them inside every style whose max is
  very low or more.
- **Reference recipes:** b01 21A, b07 1C, b12 18A, b16 18B, b18 15A, b20 19C, b21 → 1 ✓.
  At 3 this would put b01, b07 and b18 on the wrong side (max low).

## E3 · esters, an ester character — 3

- **Measures:** a yeast with an ester character tag (any tag under `fruity` or `estery`: banana,
  citrus, stone-fruit, tropical…).
- **Value:** 3 (medium-low). **Basis: set by the user, 2026-10-15** (not in the books; the plan's proposal was 4).
- **Why 3:** at 4, **b05 15B** (SafAle S-04, tagged fruity; 15B esters max medium-low) is
  on the wrong side. With 3 every reference recipe passes; estery styles (10A, 25B, 26B) are
  never "too much", and medium-low is within one level of their min *medium*.
- **Reference recipes:** b02, b03, b04, b05, b14, b15, b19 → 3 ✓; b10 26B → 3 ✓.

## E4 · esters, warm fermentation — +1 above 21 °C

- **Measures:** extra esters from a warm fermentation.
- **Value:** +1 when `ferm_c` > 21 °C. The plan proposed "> the midpoint of the yeast's
  `temp_c`".
- **Source:** HTB p. 443, "fermentations above 70°F (21°C) tend to produce a lot of esters";
  HTB p. 91, "High temperatures can also promote an excess of esters". The +1: **set by the user, 2026-10-15**.
- **Why 21 °C (the book, chosen by the user):** with the midpoint rule **b05 15B** is on the wrong side
  (S-04 at 18 °C, midpoint 17.5 → 3 + 1 = 4 > max 3). With 21 °C: b11 25B (Belle Saison,
  26 °C) → 4 ≤ 6 ✓; b10 26B (Abbaye, 21 °C) no step ✓.

## P1 · phenols, a phenolic character — 4

- **Measures:** a yeast with a phenolic character tag (clove, pepper…; see P2).
- **Value:** 4 (medium); a yeast with none → 0. **Basis: set by the user, 2026-10-15** (not in the books).
- **Why 4:** 26B allows phenols up to medium and b10's Abbaye is tagged `spicy`; any
  phenolic yeast in a style with phenols *none* (1B, 1C, 5D, 6A, 8B, 18A, 18B, 21A, Mexican
  lager) is ⚠️. OBC p. 6 names esters and phenols as the dubbel's hallmark (no figure).
- **Reference recipes:** b10 26B → 4 ≤ 4 ✓; b11 25B (Belle Saison, pepper) → 4 ≤ 5 ✓.

## P2 · phenols, which tags count — clove, pepper, phenolic, spicy

- **Measures:** which yeast character tags mean "phenolic".
- **Value:** `clove`, `pepper`, `phenolic` (the plan's list) **plus `spicy`** (their parent).
  **Basis: set by the user, 2026-10-15.**
- **Why `spicy`:** on yeasts "spicy" is the phenol (HTB p. 88: "phenols cause the
  spicy notes"). Without it Abbaye, BE-134, BE-256, M21 Belgian Wit and M31 Tripel count as
  non-phenolic.
- **Reference recipes:** only b10 changes (0 → 4, still ≤ 26B's max) ✓.

## P3 · phenols, warm fermentation — +1 above 21 °C

- **Measures:** extra phenols from a warm fermentation.
- **Value:** +1 when `ferm_c` > 21 °C, on yeasts with a phenolic character only. The plan had
  no warm step for phenols. **Basis: HTB p. 443; step set by the user, 2026-10-15.**
- **Source:** HTB p. 443, the same sentence: above 21 °C, "a lot of esters and phenolics".
- **Why:** the book names both; costs nothing.
- **Reference recipes:** b11 25B (26 °C) → 5 ≤ 5 ✓ (at the max); b10 at 21 °C no step ✓.

## Min check · one-level tolerance

- **Measures:** whether a beer has too little of a sensation the style needs.
- **Rule (user, 2026-10-15):** ⚠️ "too little" when the level is **more than one level below**
  the envelope's min (level < min − 1).
  - **Yeast, per ingredient** in `level()`: esters and phenols, because the yeast is their only
    source. Skipped for a yeast flagged needs-review (`ref.ingredient_review`); the because says so.
  - **Hops and roast, on the recipe total** in `app.style_fit_recipe` (Task 9): the recipe's oil
    dose and roast index against the style min. Never per hop or roast-malt line.
- **Basis:** set by the user, 2026-10-15 (golden case y02: US-05 in 10A is ⚠️).
- **Reference recipes, yeast:** none is more than one level short (b10 26B esters 3 vs min 4,
  b21 esters 1 vs min 2: one short, tolerated); b13 10A's YF-401 is needs-review, so skipped. ✓
- **Reference recipes, recipe totals:** three are more than one level short and go to Task 9's
  stop point: **b07 1C** and **b12 18A** (no late hops; hop flavour 0 vs min low) and **b22**
  Mexican amber lager (no roast malt; roast 0 vs min low). The other five below a min (b08, b11,
  b15, b17, b20) are one level short, tolerated.
