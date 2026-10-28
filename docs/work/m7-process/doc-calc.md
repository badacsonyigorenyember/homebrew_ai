# M7 · Doc → calc pass for steps 12–15

Status: **waiting for your review** of §4 (style → water row), §5 (hints), §11 (fermentation schedule),
§14 (style → CO₂ family), and the values marked `unsourced` / `judgement` in §10 and §12.
Work: [brief.md](brief.md) · [plan.md](plan.md) (Task 1) · written 2026-10-28 (PROJECT.md §6.7, brief R1, A1)

Every formula, table and constant that steps 12–15 use is in this file with book, chapter and
page. Page numbers are **printed page / PDF page**: *How to Brew* (HTB) printed + 26 = PDF,
*Water* printed + 18 = PDF, *Yeast* printed + 21 = PDF ([`BOOKS.md`](../../BOOKS.md)). Web
sources have no page and are cited by section. Text was read with `pdftotext -layout`; the
arithmetic in the worked examples was run in a scratch script (not kept in the repo), so those
figures are measured, not copied. Tables are quoted only as far as the code needs them.

**Page numbers inside the books.** *Water*'s text points at "Table 14", "Table 15" and "Table 17
(p. 153)" where the PDF has Tables 18/19 and Table 17 on printed p. 118. The cross-references come
from another layout of the book; I cite the table by its caption and by the page I read it on.

## Questions for you

1. **23A Berliner Weisse, water row** (§4). The book's tables exclude sours, so I proposed no row (no
   salts, a pH estimate of the source water), as decision Q1 reads. Alternative: map it to
   `ale-medium-pale-soft` (soft, light-bodied, RA −30–0) so b14 gets calcium chloride and gypsum.
   Recommend: no row, because the book says so.
2. **23A, CO₂ family** (§14). German wheat beer 3.3–4.5 (my pick: a German wheat beer, high
   carbonation) or Belgian lambic 2.4–2.8 (the book's only sour family). Recommend: German wheat.
3. **Lager diacetyl rest length** (§11). 2 days (*Yeast* p. 113, as in the plan) or 6 days (HTB Table 6.2,
   "minimum 6 days"; p. 174 "at least four days"). Recommend: 2 days as planned, the plan's source;
   say if you want the longer.
4. **Dry yeast viable cells per gram** (§10). I used 7 billion (the bottom of *Yeast*'s printed 7–20
   billion), which gives 26 g of dry yeast for a 20 L, 12 °P ale (2.3 sachets). 20 billion gives 9 g;
   5 billion ("might be as low as") 36 g. Recommend: 7 billion, since no maker's data sheet is in
   the repo.
5. **`specialty-honey-beer`** (§4, §14). Only b12's alternative list names it; step 4 returns 18A.
   Proposed: no row, no CO₂ family, the 2.5 default. Alternative: give it a row and a family. Recommend:
   leave out.

## 0. The brief's three assumptions

| Assumption (brief) | Result |
|---|---|
| *How to Brew*'s 8 style families cover every style once each is mapped to one | **Holds** for the 31 style codes in §14 (every one has a family; seven are judgement calls, marked; of those only 23A's choice changes the volumes, the lager and Kölsch calls give the same range as the alternative). **One exception:** `specialty-honey-beer` (BA, ranges 1.03–1.11 OG, 1–100 IBU, 1–100 SRM) cannot be placed: its ranges say nothing about a family. See question 5. |
| A sourced cell count per pack or per gram exists for the yeasts the briefs use *(unverified)* | **Holds generically, not per product.** *Yeast* p. 124 gives 7–20 billion cells per gram of dry yeast ("as low as 5 billion" viable) and p. 140 ~100 billion cells per liquid package. `ref.yeast` and the hopline files hold no cell count, and I had no maker's data sheet, so §10 uses the book's generic figures. No source gives a count for a souring culture (decision Q3). |
| *Water*'s Tables 18–19 rows can be matched to a recipe from its style, colour and bitterness | **Holds for 30 of the 31 codes** (the 29 that step 4 returns for the briefs, plus 17D and 20C, §4). The row lists name 19 of them; ties and judgement calls are marked in §4. **Exception: 23A Berliner Weisse.** The book says its tables exclude sours (p. 119: "excluding sours and wood aged"), so 23A gets no row (decision Q1). That means b14 gets no salts (question 1). |

## 1. *Water* Table 17 and `ref.water_salt`

Source: *Water* ch. 7, Table 17, p. 118 / PDF 136 (per gram of salt in 1 L, and in 1 US gallon).

`ref.water_salt` stores mg/L per g/L (8 rows). Dividing by 3.785 L/gal reproduces the book's per
gallon column (computed):

| Salt | Stored (mg/L per g/L) | Per gallon (÷ 3.785) | Book, per gallon |
|---|---|---|---|
| Gypsum CaSO₄·2H₂O | Ca 232.8, SO₄ 557.9 | Ca 61.5, SO₄ 147.4 | 61.5, 147.4 |
| Calcium chloride CaCl₂·2H₂O | Ca 272.6, Cl 482.3 | Ca 72.0, Cl 127.4 | 72.0, 127.4 |
| Epsom MgSO₄·7H₂O | Mg 98.6, SO₄ 389.7 | Mg 26.1, SO₄ 103.0 | 26.0, 102.9 |
| Magnesium chloride | Mg 119.6, Cl 348.8 | Mg 31.6, Cl 92.2 | 31.6, 92.1 |
| Table salt NaCl | Na 393.4, Cl 606.6 | Na 103.9, Cl 160.3 | 103.9, 160.3 |
| Baking soda NaHCO₃ | Na 273.7, HCO₃ 726.3 | Na 72.3, HCO₃ 191.9 | 72.3, 188 (book: "@99%") |
| Chalk CaCO₃ | Ca 400.4, CO₃ 599.6 | Ca 105.8, CO₃ 158.4 | 106, 158 |
| Slaked lime Ca(OH)₂ | Ca 540.9, OH 459.1 | Ca 142.9, OH 121.3 | 143, 121 |

The stored values match the book within 0.1 mg/L except baking soda's bicarbonate (stored for 100 %
purity; the book's 710.5 mg/L per g/L is "@99 %"). Used as stored: **becomes** `test_table17_per_gallon`
(Task 3) and the ion arithmetic of `app.salt_ions`.

Solubility limits the book gives (p. 117): gypsum about 2 g/L (stir hard), chalk 0.05 g/L. No
dosing rate in a recipe here reaches 1.9 g/L of gypsum (highest aim in §3: sulfate 400 mg/L =
0.72 g/L).

## 2. Kolbach residual alkalinity

Source: *Water* ch. 4, "Residual Alkalinity", p. 53–54 / PDF 71–72, and the working form in
ch. 7, p. 124 / PDF 142.

- mEq/L RA = mEq/L alkalinity − [(mEq/L Ca) / 3.5 + (mEq/L Mg) / 7]
- In ppm as CaCO₃ (what Tables 18/19 use): **RA = alkalinity − Ca / 1.4 − Mg / 1.7**
- Alkalinity of a salt (as CaCO₃, ppm) from its ions: HCO₃ × 50 / 61.017, CO₃ × 50 / 30.005,
  OH × 50 / 17.007 (equivalent weight of the ion; 50 is CaCO₃'s). ppm ÷ 50 = mEq/L.
  Computed: baking soda 11.90 mEq/L per g/L (the book uses 11.9 mmol/g·L, p. 132 / PDF 150);
  slaked lime 26.99 mEq/L alkalinity per g/L (book "27").
- ΔRA of slaked lime per g/L = 26.99 − (26.99 / 3.5) = **19.28 mEq/L** (book 19.3, Table 17,
  p. 118 and ch. 6 "Adding Calcium Hydroxide", p. 105 / PDF 123). This is the factor the code
  uses when it lists slaked lime's effect; it is the same arithmetic as RA of the resulting water.
- The tables assume Mg = 15 mg/L for every profile (p. 119); our default profile has Mg = 0, so
  RA is computed with the profile's own Mg (0 unless the brewer sets it).
- Worked examples (book, p. 124–125 / PDF 142–143), computed: 125 − 101/1.4 − 15/1.7 = **44.2**
  (book 44); 125 − 150/1.4 − 15/1.7 = **9.0** (book 9); with 0.5 g/gal gypsum Ca = 70 + 30.75 =
  100.75. These two are test cases (`test_pale_ale_option_1`).

**Becomes:** `app.residual_alkalinity(ions)` → `{alkalinity_ppm, ra_ppm, ra_meq_l}`.
Not used: Z alkalinity and Z RA (p. 74–77): they need the source water's pH, which the profile
does not have (see §17).

## 3. Tables 18a/b and 19a/b: the 16 rows

Source: *Water* ch. 7, "Choosing a Water for the Style", Tables 18a/b (p. 121 / PDF 139) and
19a/b (p. 122–123 / PDF 140–141), band definitions p. 120 / PDF 138. Column pairs a/b are
joined row by row (same order in both halves). All numbers in mg/L, alkalinity and RA as
CaCO₃.

**Bands** (p. 120): strength Light = OG 30–45, Medium 45–65, Strong 65+ (gravity points); colour
Pale 0–9 SRM, Amber 9–18, Brown 18–35, Black 35+ (Brown and Black are one row group,
"brown/black"); bitterness Soft 10–20 IBU, Moderate 20–35, Assertive 36–100; total alkalinity
Low 0–40, Moderate 40–120, High 120–200.

**Acidify** (p. 120): *Yes* = acid is generally needed for mash pH and/or sparge acidification
is recommended; *Maybe* = acid generally not needed for mash pH, sparge acidification may help;
*No* = acid generally not needed for mash or sparge.

How odd cells are stored (the user reviews this with §4):
- A single number (light lager Ca "50") is stored as a minimum, `[50,)`, because the book's
  Pilsner example calls it "50 Ca (minimum)" (p. 129 / PDF 147).
- A bracketed outlier (Dortmunder Export: Ca "(75–150)", alkalinity "(40–80)", RA "(−30–30)";
  light lager "soft (assertive)") is **left out** of the stored range. The outlier style is named
  in `styles` and gets the row (§4) with the main range.
- `numrange`, closed ends: `[lo,hi]`. Unbounded sides only for the Ca minimum.

| Code (proposed) | Table | Type · strength · colour · bitterness | Ca | Alkalinity | SO₄ | Cl | RA | Acidify | Styles (book) |
|---|---|---|---|---|---|---|---|---|---|
| `lager-light-pale` | 18 | lager · light · pale · soft *(assertive)* | [50,) | [0,40] | [0,50] | [50,100] | [−60,0] | yes | Lite American Lager, Standard American Lager, Munich Helles, (Bohemian Pils) |
| `lager-medium-pale` | 18 | lager · medium · pale · moderate, assertive | [50,75] *(75–150)* | [0,40] *(40–80)* | [50,150] | [50,100] | [−60,0] *(−30–30)* | yes | American Premium Lager, German Pils, Classic American Pils, (Dortmunder Export) |
| `lager-medium-amber` | 18 | lager · medium · amber · soft, moderate | [50,75] | [40,120] | [0,100] | [50,150] | [0,60] | maybe | Vienna, Oktoberfest |
| `lager-medium-brown-black` | 18 | lager · medium · brown/black · soft, moderate | [50,75] | [80,120] | [0,50] | [50,150] | [40,80] | no | American Dark, Munich Dunkel, Schwarzbier |
| `lager-strong-amber` | 18 | lager · strong · amber · soft, moderate | [50,75] | [40,80] | [0,100] | [50,150] | [0,60] | maybe | Helles/Maibock, Traditional Bock, Doppelbock |
| `lager-strong-brown-black` | 18 | lager · strong · brown/black · soft, moderate | [50,100] | [80,150] | [0,100] | [50,100] | [60,120] | no | Traditional Bock, Doppelbock, Eisbock, Baltic Porter |
| `ale-light-pale` | 19 | ale · light · pale · moderate | [50,100] | [0,80] | [100,200] | [50,100] | [−60,0] | yes | Blonde Ale, American Wheat, Standard Bitter, Best Bitter |
| `ale-light-amber` | 19 | ale · light · amber · soft, moderate | [50,150] | [40,120] | [100,200] | [50,100] | [0,60] | maybe | English Mild, Scottish 60/70/80, Standard Bitter, Best Bitter |
| `ale-light-brown-black` | 19 | ale · light · brown/black · moderate | [50,75] | [80,150] | [50,150] | [50,100] | [30,90] | maybe | English Brown, Brown Porter, Dry Stout |
| `ale-medium-pale-soft` | 19 | ale · medium · pale · soft, moderate | [50,100] | [0,80] | [0,50] | [0,100] | [−30,0] | yes | Weizen, Witbier, Cream Ale, Blonde Ale, Kölsch |
| `ale-medium-pale-assertive` | 19 | ale · medium · pale · moderate, assertive | [50,150] | [40,120] | [100,400] | [0,100] | [−30,30] | maybe | American Pale Ale, American XPA, Saison, American IPA, Double IPA |
| `ale-medium-amber` | 19 | ale · medium · amber · moderate, assertive | [50,150] | [40,120] | [100,300] | [50,100] | [0,60] | no | Altbier, California Common, ESB, Irish Red, American Amber, English IPA, Roggenbier, Belgian Pale, Saison |
| `ale-medium-brown-black` | 19 | ale · medium · brown/black · moderate, assertive | [50,75] | [80,160] | [50,150] | [50,150] | [60,120] | no | American Brown, English Brown, Brown Porter, Robust Porter, Dry Stout, Sweet Stout, Oatmeal Stout, Foreign Extra Stout, American Stout, Dunkelweizen |
| `ale-strong-pale` | 19 | ale · strong · pale · moderate | [50,100] | [0,40] | [50,100] | [50,100] | [−30,0] | maybe | Belgian Blonde, Golden Strong, Tripel |
| `ale-strong-amber` | 19 | ale · strong · amber · moderate, assertive | [50,100] | [40,120] | [50,100] | [50,150] | [0,60] | no | Strong Scotch Ale, Bière de Garde, Dubbel, Old Ale, Barleywine |
| `ale-strong-brown-black` | 19 | ale · strong · brown/black · moderate–assertive | [50,75] | [120,200] | [50,150] | [50,150] | [120,200] | no | Baltic Porter, Foreign Extra Stout, American Stout, Russian Imperial Stout, Weizenbock, Belgian Dark Strong, Old Ale |

Other book facts the code uses (p. 119–120): no sodium or magnesium range is given; sodium
should not exceed 100 mg/L; the authors assumed 15 mg/L Mg in all RA figures; porters/stouts and
similar dark lagers want about 30 mg/L Mg (taken as a note only; no Mg salt, §6).

**Becomes:** `ref.water_profile` (16 rows, `db/049_process_ref.sql`); tests
`test_water_rows_are_the_books` (spot checks: medium ale pale moderate–assertive SO₄ [100,400]
and RA [−30,30]; light lager Ca from 50; strong ale brown/black alkalinity [120,200]).

## 4. Style → row table (**for your review**)

Source for the mapping: the row's own style list (§3, column "Styles") where it names the style;
otherwise the bands at the midpoints of the style's `ref.beer_style` ranges (OG as gravity
points, SRM, IBU) with lager or ale from the style. "listed" = the book's list names it. The 31
codes are the 29 that step 4 returns for b01–b24 and h01–h06 (measured with
`tests.test_step4.step4` on 2026-10-28) plus 17D (h06's brief style; step 4 returns 22C for it)
and 20C (b05's alternative). 30A and 31B never reach step 12 (step 4 returns their base styles:
30A → 20B, 31B → 18A). Note: the plan's list had 20C and 17D where step 4 actually returns 22C
for h06; both are mapped.

| Style code · name | Midpoints (OG pts · SRM · IBU) | Row | Why |
|---|---|---|---|
| 21A American IPA | 63 · 10 · 55 | `ale-medium-pale-assertive` | listed ("American IPA") |
| 21C Hazy IPA | 72.5 · 5 · 42.5 | `ale-medium-pale-assertive` | **judgement.** Not listed; the bands give *strong* (OG), but the book puts IPA and Double IPA in this row "regardless of gravity" because of their hopping (p. 120), and Hazy IPA is an IPA |
| session-india-pale-ale (BA) | 30 · 7.5 · 37.5 | `ale-medium-pale-assertive` | **judgement.** The bands give *light/pale/assertive*, a combination no row has (`ale-light-pale` is moderate and SO₄ 100–200). Same reason as 21C: the book's "IPA" place |
| 18B American Pale Ale | 52.5 · 7.5 · 40 | `ale-medium-pale-assertive` | listed; the book's own worked example (p. 124) |
| 16B Oatmeal Stout | 55 · 31 · 32.5 | `ale-medium-brown-black` | listed ("Oatmeal Stout") |
| 16A Sweet Stout | 52 · 35 · 30 | `ale-medium-brown-black` | listed ("Sweet Stout") |
| 20B American Stout | 62.5 · 35 · 55 | `ale-medium-brown-black` | listed (also in `ale-strong-brown-black`); bands: medium (62.5 < 65) |
| 15B Irish Stout | 40 · 32.5 · 35 | `ale-light-brown-black` | bands: light / brown-black / moderate; the book lists "Dry Stout" in this row and in `ale-medium-brown-black`. b05 asks for an imperial stout and step 4 returns 15B (a style-fit matter, not changed here) |
| 20C Imperial Stout | 95 · 35 · 70 | `ale-strong-brown-black` | listed ("Russian Imperial Stout") |
| 13C English Porter | 46 · 25 · 26.5 | `ale-medium-brown-black` | listed ("Brown Porter", also in `ale-light-brown-black`). **Tie:** OG midpoint 46 is just over the 45 line between light and medium; light would be the other row |
| 19C American Brown Ale | 52.5 · 26.5 · 25 | `ale-medium-brown-black` | listed ("American Brown") |
| 10A Weissbier | 48.5 · 4 · 11.5 | `ale-medium-pale-soft` | listed ("Weizen") |
| 1C Cream Ale | 48.5 · 3.5 · 14 | `ale-medium-pale-soft` | listed |
| 5B Kölsch | 47 · 4.25 · 24 | `ale-medium-pale-soft` | listed |
| 18A Blonde Ale | 46 · 4.5 · 21.5 | `ale-medium-pale-soft` | listed in this row and in `ale-light-pale`. **Tie:** OG midpoint 46, just over the line between light and medium |
| 11B Best Bitter | 44 · 12 · 32.5 | `ale-light-amber` | listed (also in `ale-light-pale`); bands: light / amber / moderate |
| 14B Scottish Heavy | 37.5 · 16 · 15 | `ale-light-amber` | listed ("Scottish 60/70/80") |
| 15A Irish Red Ale | 41 · 11.5 · 23 | `ale-medium-amber` | listed ("Irish Red"). The bands would give light, but a listed name wins |
| 25B Saison | 56.5 · 13.5 · 27.5 | `ale-medium-amber` | listed in two rows (`ale-medium-pale-assertive` and this one). **Tie:** the bands (medium, amber, moderate) pick this one |
| 26B Belgian Dubbel | 68.5 · 13.5 · 20 | `ale-strong-amber` | listed ("Dubbel") |
| 25A Belgian Blond Ale | 68.5 · 5 · 22.5 | `ale-strong-pale` | listed ("Belgian Blonde") |
| 17C Wee Heavy | 100 · 19.5 · 26 | `ale-strong-amber` | listed ("Strong Scotch Ale") |
| 17D English Barley Wine | 100 · 15 · 52.5 | `ale-strong-amber` | listed ("Barleywine") |
| 22C American Barleywine | 100 · 13.5 · 75 | `ale-strong-amber` | listed ("Barleywine"); bitterness is above the row's, the book gives no separate row |
| 1B American Lager | 45 · 2.75 · 13 | `lager-light-pale` | listed ("Standard American Lager"); bands agree |
| 3B Czech Premium Pale Lager | 52 · 4.75 · 37.5 | `lager-light-pale` | listed ("Bohemian Pils"); the book places it here although its OG is *medium* (p. 120) |
| 5D German Pils | 47 · 3 · 31 | `lager-medium-pale` | listed |
| 6A Märzen | 57 · 12.5 · 21 | `lager-medium-amber` | listed ("Oktoberfest"); bands agree |
| mexican-style-amber-lager (BA) | 48.5 · 11 · 18.5 | `lager-medium-amber` | bands (medium / amber / soft); Vienna-like |
| 8B Schwarzbier | 49 · 24.5 · 27.5 | `lager-medium-brown-black` | listed |
| 23A Berliner Weisse | 30 · 2.5 · 5.5 | *(no row)* | the tables exclude sours (p. 119). Decision Q1 gives no salts and the source-water pH estimate. **Question 1** |
| specialty-honey-beer (BA) | 70 · 50 · 50 | *(no row)* | its ranges span the whole scale (1.03–1.11 OG, 1–100 SRM and IBU), so no band can be read. Only b12's alternative list names it; step 4 returns 18A. **Question 5** |

Every other `ref.beer_style` code (254 of 285, `specialty-honey-beer` among them) gets no row and no `co2_vol`
(decision Q1). Of the 31 codes in this table, 30 have a row; the test
`test_every_brief_style_has_a_row_and_co2` will name 23A explicitly as the one without.

## 5. Hints → aim

Source: step 1's hint vocabulary (contract `step1.output.schema.json`): `bitter, hoppy, juicy,
dry, crisp, full, chewy, malty, darker, stronger, session`.

- *Water* ch. 7, "Sulfate", p. 115 / PDF 133: sulfate "can make the hop character more
  assertive, or dryer"; "Chloride", p. 115: "a rounder, fuller, sweeter quality to the malt
  character". "Sulfate-to-Chloride Ratio", p. 116 / PDF 134: the ratio "is said to greatly
  influence the hoppy-to-malty or dryness-to-fullness balance"; useful ratio 9 to 0.5; at least
  50 mg/L of each to be noticed; "Pale and light lagers... are more sensitive to sulfate".
- Bru'n Water *Water Knowledge* §2.5.2 "Major Ions in brewing": "Sulfate provides a sharper, dryer
  edge to highly hopped beers"; chloride "accentuates fullness and sweetness"; "Brewers of juicy
  IPAs have reported... around 150 ppm chloride and 75 ppm sulfate".
- The 87.5 % / 12.5 % positions are RECIPE-ROADMAP §7's (the user's 2026-10-17 decision, the
  same positions step 4 uses for its knobs, `app.hint_knob`).

| Hint | Side | Passage |
|---|---|---|
| `bitter` | sulfate | Water p. 115 (sulfate accentuates hops) |
| `hoppy` | sulfate | same |
| `dry` | sulfate | Water p. 115 ("dryer"); p. 116 ("dryness-to-fullness") |
| `crisp` | sulfate | Bru'n §2.5.2 ("sharper, dryer edge"); p. 116 |
| `juicy` | chloride | Bru'n §2.5.2 (juicy IPA: chloride-led) |
| `malty` | chloride | Water p. 115, 116 ("malty" balance) |
| `full` | chloride | Water p. 115 ("fuller"), p. 116 ("fullness") |
| `chewy` | chloride | same as `full` (body) |
| `darker`, `stronger`, `session` | none | they move colour, gravity and strength, not the ion balance |

Rule (Approach step 12, item 2): sulfate and chloride aims start at the **middle** of the row's
ranges. One or more sulfate-side hints (and no chloride-side hint) move sulfate to 87.5 % and
chloride to 12.5 % of their ranges; chloride-side hints (and no sulfate-side hint) the reverse;
both sides at once leave the middle and say so. A hint never moves an aim outside the row's range.
The book's 87.5 / 12.5 are not from *Water*; *Water* gives only the direction. A hint pair seen
in the briefs: b02 `juicy, hoppy` (both sides, so the middle), b11 `dry, full, chewy` (both).

**Becomes:** `app.water_aim(row, hints)` → `moved_by`; `test_aim_moves_with_hints`.

## 6. Salt order and limits

- **Order** (Approach step 12 items 3–5): gypsum for sulfate and calcium chloride for chloride,
  each `(aim − source water) / (mg/L per g/L)`; never below 0 (p. 117: these are the only two
  calcium salts that add flavour ions without alkalinity). Then calcium: if below the row's
  minimum, both salts rise in proportion until it is reached or sulfate or chloride reaches its
  row maximum; then "calcium below the row" is said.
- **Calcium above the row maximum is reported, not corrected.** The sulfate and chloride aims are
  the book's ranges for the flavour ions; the calcium that comes with them can exceed the row's
  Ca range (computed: `lager-medium-pale` with `bitter`: sulfate 137.5 and chloride 56.25 give Ca
  89 against [50,75]). The tables say their combinations "may not produce a residual
  alkalinity value that is within the listed RA range. That's ok" (p. 119). The output carries
  an `outside_row` note per ion instead of dropping a salt.
- **No magnesium salt.** *Water* p. 119: "no particular recommendations for magnesium...
  the vast majority of this came from the malt"; only the 30 mg/L porter note. Epsom and
  magnesium chloride stay in `ref.water_salt` unused.
- **Sodium ≤ 100 mg/L**: *Water* p. 116, 119 ("We are generally recommending not exceeding
  100 ppm"); Bru'n §2.5.2 (100 ppm practical maximum). Baking soda is used while the
  resulting sodium stays at or below 100 mg/L (the source water's own sodium counts).
- **Lime over chalk.** *Water* p. 117 / PDF 135 and Table 17: chalk "largely ineffective"
  in the mash, "Don't Use"; Bru'n §4.3.1 (avoid chalk) and §4.3.2 (pickling lime is readily
  soluble). Slaked lime's alkalinity is counted at its Kolbach ΔRA (19.28 mEq/L per g/L), the
  form the Foreign Extra Stout example uses (p. 130–132 / PDF 148–150), and the form *Water*
  confirms for additions to the water (ch. 6, p. 105–106 / PDF 123–124).
- **Alkalinity only in the strike water.** Not a book rule; it follows from the book's
  mash-pH frame (the alkalinity must be in the mash) and from Bru'n §4.3.1 on the mash being the
  place alkalinity matters. Sparge water takes the same gypsum and calcium chloride per litre
  (flavour ions are for the whole beer) and no alkalinity (the book warns about sparge water
  alkalinity raising pH and extracting tannin, Table 18/19 "Acidify" note, p. 120). Marked
  **judgement**; the reason is in the step's `because`.
- **How much alkalinity.** When RA is below the row's range (dark rows on distilled water), add
  alkalinity to the strike water, aimed at the **middle of the RA range**: baking soda while the
  resulting sodium is ≤ 100 mg/L, slaked lime for the rest. RA needed = middle − current RA in mEq/L,
  ÷ (11.90 − 0 for baking soda: only the HCO₃ term, calcium unchanged; ÷ 19.28 for lime).
  Above the range nothing is added and the acid line says acid would be needed (§7).

**The three worked examples** (book, computed):

| Example | Book | Computed | Test |
|---|---|---|---|
| Pilsner (p. 129 / PDF 147): 30 mg/L Ca from CaCl₂ in 10 gal (37.854 L) | 4.17 g; 4.2 g gives 53.5 mg/L Cl | 4.166 g; 53.51 mg/L Cl | `test_pilsner_example` (± 0.02 g, ± 0.2 mg/L) |
| American pale ale option 1 (p. 124–125 / PDF 142–143) | RA 44 at Ca 101; 9 at Ca 150 | 44.2; 9.0 | `test_pale_ale_option_1` (± 1) |
| Foreign Extra Stout 1a (p. 131 / PDF 149): RA 1.32 → 3 mEq/L | 0.087 g/L slaked lime | 0.08705 g/L | `test_foreign_extra_stout_lime` (± 0.002); the total alkalinity back-calculated, 183.8 mg/L, is the second check |

## 7. Mash pH estimate

Source: *Water* ch. 5, "The Hypothesis for Predicting Mash pH", p. 77–78 / PDF 95–96, Table 9
(p. 67 / PDF 85), Table 5 (p. 56 / PDF 74) and the conclusions list (p. 73 / PDF 91); ch. 7 golden
rule 4 (p. 124 / PDF 142): "The target mash pH range is **5.2-5.6**, measured at room temperature."

**Method** (zero-sum, the book's step list 1–6, with average buffer capacities instead of
titration curves; brief Out):

    pH = 5.4 + (Σ kg × alk_i + V_strike × RA_mEq/L) / (Σ kg × buffer_i)

where for each mashed fermentable alk_i is its alkalinity (+) or acidity (−) in mEq/kg **re pH 5.4**
and buffer_i its buffer capacity in mEq/(pH·kg), both from Table 9 below; V_strike is the strike
water in litres and RA the strike water's Kolbach RA in mEq/L (can be negative). The water adds
no buffer term (a deliberate simplification, no source gives one at the strike water's
alkalinities that is not pH-dependent). A positive sum puts the pH above 5.4 (p. 77, step 6).

**Table 9** (Troester "T" and Bies "B"; the last two columns, p. 67): the figures used are the
**mean of T and B** where both are measured; where only one is, that one. The two sets differ a
lot for caramel malts (e.g. caramel 20 acidity −5.3 vs −22.2); the mean is the plan's choice.

| Row | °L | Alkalinity(+)/acidity(−) re 5.4, mEq/kg (T, B) | Buffer mEq/(pH·kg) (T, B) |
|---|---|---|---|
| 2-row base | 2 | B only: 16.1 | B only: 40.3 |
| Munich | 10 | 4.9, 4.4 → **4.65** | 35.0, 36.9 → **35.95** |
| caramel 20 | 20 | −5.3, −22.2 → **−13.75** | 29.6, 37.6 → **33.6** |
| caramel 40 | 40 | −14.3, −41.4 → **−27.85** | 37.6, 46.5 → **42.05** |
| caramel 60 | 60 | −35.9, −33.8 → **−34.85** | 48.5, 46.3 → **47.4** |
| caramel 120 | 120 | −31.5, −43.3 → **−37.4** | 48.4, 59.3 → **53.85** |
| roasted barley | 300 | −27.9, −47.5 | 38.8, 48.5 |
| black malt | 500 | −32.4, −43.4 | 41.5, 43.4 |

**Classes** (`app.malt_acidity(role, ebc)`; one `case`). Colour is the midpoint of the ingredient's
`ebc` range (a range with no lower end uses its upper end); °L is taken as SRM = EBC ÷ 1.97, which
*How to Brew* ch. 15 calls "nearly identical" for malt (p. 234–235 / PDF 260–261; EBC = SRM ×
1.97). A class is the nearest Table 9 row by °L (boundaries at the midpoints 6, 15, 30, 50, 90):

| Class | Chosen by | alk (mEq/kg) | buffer |
|---|---|---|---|
| `base` | `role` base; `role` adjunct (Bru'n §2.4 "Grain Acidity": "Flaked malt and grain should be considered base malts"); any kilned/crystal below 6 °L (no Table 9 row between base and Munich) | 16.1 | 40.3 |
| `munich` | kilned/crystal 6 ≤ °L < 15 | 4.65 | 35.95 |
| `caramel-20` | 15 ≤ °L < 30 | −13.75 | 33.6 |
| `caramel-40` | 30 ≤ °L < 50 | −27.85 | 42.05 |
| `caramel-60` | 50 ≤ °L < 90 | −34.85 | 47.4 |
| `caramel-120` | °L ≥ 90 (kilned/crystal) | −37.4 | 53.85 |
| `roast` | `role` roast, **one class**: the stored roast colours (900–1500 EBC for roasted barley and black malt) do not separate Table 9's 300 and 500 °L rows, so the mean of the four figures | −37.8 | 43.05 |

`role` sugar is not mashed and is skipped. Not covered by Table 9: acidulated malt
(role kilned, 1.5–5 EBC) is treated as `base` (its acid is not measured there; the estimate is
then too high, i.e. on the safe side for the "acid needed" line); smoked and Sprau malts as above.
The 5.4 reference pH and the use of average buffer capacities are the book's own simplifications
(p. 73: "for small magnitudes of pH change, the buffering capacity can be approximated by an
average value").

**Hand-worked case** (A10; the number `test_pale_grist_needs_acid` checks):
4.0 kg `base` malt, strike water 12 L (ratio 3 L/kg) from distilled water with the light-lager
aim: sulfate 25 (middle of [0,50]), chloride 75 (middle of [50,100]). Gypsum 25 / 557.9 =
0.04481 g/L, calcium chloride 75 / 482.3 = 0.15550 g/L, Ca = 0.04481 × 232.8 + 0.15550 × 272.6 =
52.82 mg/L (already ≥ 50, no extra), alkalinity 0.
RA = 0 − 52.82 / 1.4 = −37.73 mg/L as CaCO₃ = **−0.7546 mEq/L**.
Σ mEq = 4.0 × 16.1 + 12 × (−0.7546) = 64.40 − 9.06 = 55.34; Σ buffer = 4.0 × 40.3 = 161.2.
**pH = 5.4 + 55.34 / 161.2 = 5.743** → above 5.6, so the acid line fires. (b08's case through the
step, German Pils with `bitter`, gives about 5.70, also above 5.6.) The test checks within 0.02
of 5.743 by feeding the function the grist and strike ions directly, so the figure does not
depend on how the salts round.

**A dark grist on distilled water** (`test_dark_grist_on_distilled_is_low`): 4.0 kg base,
1.0 kg caramel-60, 1.0 kg roast, no alkalinity, ions zero: Σ mEq = 64.4 − 34.85 − 37.8 = −8.25
and Σ buffer = 161.2 + 47.4 + 43.05 = 251.65 → pH = 5.367, **below 5.4**. Worth knowing for
Task 3: the plan's example of "b05-style" grist (80 % base, 10 % caramel, 10 % roast) gives
**5.47** on a strong-brown/black aim with Ca 60, i.e. *not* below 5.4. That test will use the
darker grist above; I record it as a plan detail in the Deviations when Task 3 is written.

**Becomes:** `app.malt_acidity`, `app.mash_ph_estimate`, tests `test_pale_grist_needs_acid`,
`test_dark_grist_on_distilled_is_low`, `test_ph_terms_add_up`. Marked **unverified against Bru'n
Water** (§16).

## 8. Water-to-grist ratio, total water, strike temperature

**Ratio: 3 L/kg.** *How to Brew* ch. 17, p. 262 / PDF 288: "Generally, I recommend a water-to-grist
ratio of 1.25–2 qt./lb. (2.5–4 L/kg)". The book's single-infusion example (p. 268–269 /
PDF 294–295) uses **3 L/kg**, "the typical water-to-grist ratio for single infusion mashing is
1.5 qt./lb. (i.e., roughly 3 L/kg)" (p. 267 / PDF 293). *Water* Table 5 (p. 56) notes "a typical
initial grist ratio of near 4" (p. 55); 3 L/kg is the middle of HTB's range and the one with a worked
example. Chosen: **3 L/kg** (`app.water_volumes.ratio_l_kg`).

**Volumes** (decision 5): mashed kg = fermentables whose `role` is not `sugar`; total water =
`app.preboil_volume` (s1) + mashed kg × `grain_abs_l_kg` (profile; default 1.0 L/kg);
strike = mashed kg × 3; sparge = total − strike; when that is below 0, strike = total and sparge 0
(said in `because`). Not a book formula: the arithmetic of the brewer profile. The book's sparge
and absorption are not tabulated in the passages used.

**Strike water temperature.** HTB ch. 17, "Dry Grain Infusion Calculations", p. 268 / PDF 294:

    Tw = [(S / R) × (T2 − T1)] + T2        S = 0.4 (heat capacity of grain relative to water)
    R = Rv × ρ                             ρ = 0.985 kg/L (Table 17.3 and sidebar, p. 266–267)

Metric form with Rv = `ratio_l_kg`: **Tw = (0.4 / (0.985 × ratio)) × (T2 − T1) + T2**. The plan wrote
this as "(0.41 ÷ r)": 0.4 / 0.985 = 0.4061, so 0.41 is the rounded constant; the code uses the
exact form (difference at 3 L/kg: 0.06 °C; I record it in the Deviations when Task 5 is written).
T2 = the first mash step's temperature; the grain is mashed with the mash tun pre-heated and
no heat loss (the book says the same, p. 267).

**Grain temperature T1 = 21 °C.** Sourced: HTB p. 268 / PDF 294, "Quick and easy mashing": "assuming
that your grain is at room temperature (70 °F [21 °C])" and the worked example "We will assume that
the dry grain is at room temperature, i.e., 70 °F (21 °C)" (p. 268). One figure, from the book
(not `unsourced`).

**Worked example** (p. 268–269 / PDF 294–295), computed: 4.54 kg at 3 L/kg, T1 = 21 °C, T2 = 67 °C:
R = 3 × 0.985 = 2.955; Tw = (0.4 / 2.955) × 46 + 67 = **73.23 °C** (book: 73.2, "73 °C"). With the
rounded 0.41 constant: 73.29. `test_strike_temp_example` checks 73.2 ± 0.5. Volume 13.6 L = 4.54 × 3.

**Becomes:** `app.water_volumes(profile, step10)`, `app.strike_temp(ratio, grain_c, target_c)`,
`test_volumes_add_up`, `test_strike_c_targets_first_step`, `test_strike_temp_example`. Mash-out
(§9) is not part of the strike calculation.

## 9. Mash rests

All rests sit **below the starch range** so rule 10's FG model (the temperature of `mash_c`) is
unchanged (brief R3, A11). The saccharification rest is `step10.mash_c`, **60 min** (HTB Table
17.1, p. 263 / PDF 289: 30–60 min; s5's model assumes a 60 min rest, `s5-mash-attenuation` doc-calc
§4).

| Rest | °C | Minutes | Trigger | Source |
|---|---|---|---|---|
| Ferulic acid | **43** | **30** | style 10A Weissbier, 10B Dunkles Weissbier, 10C Weizenbock (the German wheat beers; `ref.beer_style.code` `10A`, `10B`, `10C`, all present) | *Yeast* ch. 3, p. 33 / PDF 54: "a ferulic acid rest around 110 °F (43 °C)"; HTB ch. 17, p. 264 / PDF 290: 104 °F (40 °C) with a half hour rest "to enhance the phenolic character" in Bavarian wheat beers, and Table 17.2, p. 265: 10–20 min at 40 °C. 43 °C is *Yeast*'s figure; the time is HTB's 30 min. The two books differ by 3 °C; both are inside the 35–45 °C esterase/phytase range HTB gives (p. 274 / PDF 300, 95–113 °F for the phytase/beta-glucanase/ferulic acid rest) |
| Beta-glucan | **45** | **20** | `role = 'adjunct'` (flaked and unmalted grains) above 20 % of the grist by mass | HTB ch. 16, p. 244 / PDF 270: "Resting the mash at 104–118 °F (40–48 °C) for 20 min... is recommended to improve lautering when using more than 20 % of unmalted or flaked barley, oatmeal, rye, or wheat" ("optional" at 10–20 %); Table 16.2, p. 249 / PDF 275: beta-glucanase preferred 40–48 °C. 45 °C is the middle of 40–48 |
| Protein | — | — | **not used** | HTB p. 245 / PDF 271: needed only for "moderately modified malts, or... well-modified malts with more than 20 % of unmalted wheat, rye, or oats", and warns a long (> 30 min) protein rest at 50 °C removes body and foam. Our data has no modification column (`ref.fermentable` has `enzyme_activity` but no Kolbach index), so there is no rule the data can test; skipped (plan: "where the doc-calc pass finds a rule our data can test") |
| Mash-out | **77** | **10** | always | HTB ch. 16, "Mash-Out", p. 252 / PDF 278: raise "to 170 °F (77 °C) prior to lautering". The book says it is "not needed" for 3–4 L/kg mashes and "may be helpful" for > 25 % wheat/rye/oats; the plan includes it (decision 3). **The 10 minutes are `unsourced`:** no page gives a time |

Ordering in the output: neutral rests (ferulic, then beta-glucan if both) by temperature
ascending, then the saccharification rest, then the mash-out. A beta-glucan rest and a ferulic
rest at once (a weizen with > 20 % flaked oats) keep both: 43 °C and 45 °C are two rests 2 °C
apart, so the code **merges them into the one rest at 43 °C for 30 min** when both fire (judgement:
both are inside the 40–48 °C beta-glucanase range). Flaked share is by mass of `role = 'adjunct'`
over all mashed fermentables.

**Becomes:** `app.mash_rests(style_code, grist, mash_c)`; tests `test_rests_are_neutral_and_sourced`
(every rest but saccharification is < 55 °C or the 77 °C mash-out, with a `source`),
`test_weizen_gets_ferulic_rest`, `test_flaked_over_20_gets_beta_glucan_rest`,
`test_single_infusion_otherwise`.

## 10. Pitch rate

Source: *Yeast*, "Pitching Rates", p. 121–124 / PDF 142–145; "average liquid package",
p. 140 / PDF 161.

    cells to pitch = rate × 10⁶ × wort mL × °P          (p. 123 / PDF 144)

- **Rate**: 0.75 million cells/mL/°P for ales, 1.5 for lagers (p. 122 / PDF 143: "We prefer slightly
  lower rates for ales (0.75 million) and slightly higher for lagers (1.5 million)"). The book
  adds that British ales and German weizen are "often around 0.5 to 0.75" and that a fresh
  laboratory culture "can use up to a 50 percent lower pitching rate" (same page). Both are
  **not used**: the code keeps the two rates the plan names (conservative: more cells), and says so
  in `because`.
- **Ale rate for everything not lager** (kveik, brett, no-type yeasts included); lager = `ref.yeast.type =
  'lager'`.
- **Worked example** (p. 123 / PDF 144): 0.75 × 10⁶ × 20 000 mL × 12 °P = **180 billion cells**
  (a lager at the same wort: 360 billion). `test_yeast_book_example`.
- **Liquid yeast**: packs = cells ÷ **100 billion**, rounded up (p. 140 / PDF 161: "the average liquid
  yeast package for homebrewers has about 100 billion cells"). 180 billion → 2 packs.
- **Dry yeast**: grams = cells ÷ viable cells per gram, rounded up to 1 g. The book (p. 124 / PDF
  145): "Most dry yeast contains about **7 billion to 20 billion** cells per gram... but that is not the
  number of viable cells per gram you will have once you rehydrate... Find out from your supplier how
  many viable cells per gram you can expect (which might be as low as 5 billion)". No maker's data
  sheet is in the repo. **Chosen: 7 billion cells/g**, the bottom of the book's printed range:
  the pitch cannot be under-sized by a generous count, and 5 billion is the book's unsupported
  "might be". Judgement; the reason goes into `because`. At 7 billion/g a 180 billion-cell ale
  pitch is 26 g, i.e. 2.3 of the usual 11.5 g sachets: higher than home brewers' usual 1 sachet,
  but the book's own formula (it assumes repitched slurry; fresh dry yeast could use less, p. 122)
  - **question 4**.
- **Souring culture** (`ref.yeast.type = 'lacto'`): no source gives a cell count; `1 pack`,
  `cells_billion` null, "no sourced pitch rate" (decision Q3).
- Wort volume for the cell count: the batch volume (fermenter volume `numbers.batch_l`); °P =
  `app.sg_to_plato(og)`.

**Becomes:** `app.pitch_rate`; tests `test_yeast_book_example`, `test_dry_yeast_in_grams`,
`test_liquid_yeast_in_packs`, `test_souring_culture_keeps_one_pack`.

## 11. Fermentation schedule (**for your review**)

Source: *Yeast* ch. 4 (temperature control) and "Diacetyl Rest", "Lagering"; *How to Brew* ch. 6 (fermentation
phases, Table 6.2) and the lager section on p. 174. Values marked `unsourced` have no page; the proposed
value is given.

**Main temperature M** = step 6's `ferm_c` raised to at least the yeast range's lower bound + 1 °C,
so a start 1–2 °C below it is still inside the range. **Start S** = max(M − 2, lower bound).
**End raise E** = min(M + 3, upper bound). Source for S and the 18–36 h rise: *Yeast* ch. 4,
"Temperature Control", p. 97 / PDF 118: "the optimal starting temperature for the majority of
fermentations is just a couple degrees (1 to 3 °F / 1 to 2 °C) below your target... slowly raise or
allow the temperature to rise to your target fermentation temperature over the course of 18 to 36
hours. Once it reaches fermentation temperature, hold... until at least the last one-third to
one-fourth of fermentation. At that time raise the temperature several degrees or more (4 to 10 °F /
2 to 5 °C) over the course of a day or two." HTB agrees: p. 94 Table 6.2 raise ales 3–6 °C (5–10 °F);
p. 95 sidebar. The overlap of the two raises (2–5 and 3–6) starts at 3 °C: **E = M + 3** (judgement,
the lowest figure both books allow), never above the yeast's upper bound.

| Phase (`phase`) | Applies to | °C | Days | Source |
|---|---|---|---|---|
| `ferment` start | every main yeast | S | 1 | *Yeast* p. 97 (rise over 18–36 h; 1 day is the middle) |
| `ferment` hold | ale, kveik, brett and no-type yeasts | M | 2 | HTB Table 6.2, p. 94 / PDF 120: the rest starts "~day 3 of 4"; the high-growth phase is 1–3 days for ales (p. 91 / PDF 117) |
| `rest` (end raise) | ale, kveik, brett and no-type | E | 4 | HTB Table 6.2: "Leave for minimum 4 days (up to 8)" for ales; *Yeast* p. 113: "a two-day rest at fermentation temperature" |
| `ferment` hold | lager (`type = 'lager'`) | M | 3 | HTB Table 6.2: the lager rest starts "day 4 of 6"; high-growth phase 2–5 days for lagers (p. 91) |
| `rest` (diacetyl) | lager | R = least(upper bound, 18), at least M | 2 | *Yeast* ch. 5, "Diacetyl Rest", p. 113 / PDF 134: "raise the temperature into the 65 to 68 °F (18 to 20 °C) range for a two-day period near the end of the fermentation". The upper bound caps it so A4 holds: 10 of 17 lager yeasts top out at or below 15 °C (measured 2026-10-27). HTB gives longer rests: "minimum 6 days (up to 12)" (Table 6.2, p. 94) and "at least four days, if not a week" (p. 174 / PDF 200). **Question 3: 2 days (Yeast, the plan) or 6** |
| `souring` | culture with `ref.yeast.type = 'lacto'` | 35 | 1 | see §13 |
| `dry_hop` | step 10 dry hops | least(14, last ferment temp) | 2 (contact) | see §12 |
| `crash` | ale, kveik, brett, no-type | 2 | 7 | HTB p. 95 / PDF 121 "Cold conditioning": "cool... to about 5–8 °C below the fermentation temperature... colder being better", "only have to cold condition for a week or two"; 2 °C is HTB's lagering floor (p. 174, 35 °F); *Yeast* p. 114–115: near freezing; "very little happens once you take the yeast below 4 °C". 7 days is the low end of "a week or two". Judgement: HTB describes this as cold conditioning, not a crash |
| `lager` | lager | 2 | 14 | HTB p. 174 / PDF 200: cool "by not more than 10 °F (6 °C) a day down to about 35 °F (2 °C)"; "The lagering time can be 2–4 weeks, although I recommend shorter times (1–2 weeks) if you plan on priming and bottle conditioning". Packaging here is by priming, so the upper end of the shorter figure: 14 days |

Notes on the rows:
- **Kveik** (20 rows, 20–42 °C), **brett** (2), and the **3 yeasts with no `type`** use the ale schedule.
  Kveik fermenting much faster is not in *Yeast* or HTB; ale durations are therefore `unsourced` for
  kveik. They are conservative (longer).
- **A4**: every `souring`, `ferment` and `rest` step lies inside its yeast's `temp_c`. `dry_hop`,
  `crash` and `lager` are conditioning below any yeast's range and are exempt (plan, step 14).
  A lager yeast whose M exceeds 18 keeps R = M (no raise).
- **Slow cooling.** *Yeast* p. 115 / PDF 136 describes lagering as cooling 0.5–1 °C a day, to
  about 4 °C. HTB p. 174 allows up to 6 °C a day. Home refrigerators do the latter; HTB's figure is
  used and *Yeast*'s slow rate is in the `why` text of the `lager` step as the commercial method.
- **Total days**: ale 1 + 2 + 4 = 7 days at temperature, then dry hop 2 and crash 7; lager 1 + 3
  + 2 = 6 days, then lager 14. (HTB p. 102: "Maturation can take anywhere from two days to two
  weeks" for ale.)

**Becomes:** `app.ferment_schedule`; tests `test_every_ferment_temp_in_range`,
`test_every_lager_has_diacetyl_rest`, `test_ramp_shape`, `test_b13_weizen_schedule`.

## 12. Dry hop and secondary extras

**Dry hop** (step 10 hops with `usage = 'dry_hop'`): after the last `ferment`/`rest` step.
Sources: Janish, *Dry Hop Best Practices*, MBAA TQ 58(1), 2021, summary list (PDF p. 8 of
`shared/rag-files/articles/janish_dry_hop_best_practices_tq_2021.pdf`): extraction "generally
1–3 days... even at temperatures cooler than fermentation"; "Duration of dry hopping for no longer
than 3 days"; "Dry hop at cool temperatures, 50–58 °F (10–14 °C), to improve foam and to reduce
excessive hydrocarbon extraction, polyphenols, and hop creep". Janish, *A Case for Short and
Cool Dry Hopping* (web): "the majority of the 4MMP extracted into the beer the first two days"; the
Sapwood practice of starting post-fermentation dry hopping "around 58 °F" (14 °C).
- Temperature: **14 °C** (top of Janish's 10–14 °C: least cooling needed), or the last
  fermentation temperature if that is lower (a lager).
- Contact: **2 days** (inside "no longer than 3 days"; the 4MMP and monoterpene alcohols extract in
  the first two days). Day: the first day after the last `ferment`/`rest` step.
- Amounts: grams as step 10 has them. Agitation, burping, oxygen purging are not modelled.
- Janish's sulphur/hazy remarks (myrcene, hop creep) are the reasons, not extra computed values.

**Secondary extras** (step 10 extras with `usage = 'secondary'`): day = the first day after the
last `ferment`/`rest` step; contact = `ref.misc.time_min` in days (coffee beans 2880 min = 2 days,
Janish *Coffee Beers*, in `ref.misc.field_source`); none (vanilla) → "until it tastes right",
`contact_days` null, `unknown`. Orange peel is `whirlpool` (step 13), cold brew coffee `packaging`
(step 15).

**Becomes:** `app.step14_ferment` (`dry_hops`, `secondary`); tests `test_dry_hop_after_fermentation`,
`test_secondary_extras`.

## 13. Souring (b14, a souring culture is in the recipe)

Source: Milk The Funk, *Berliner Weissbier* (web), "General Best Practices" and the MTF recipe
steps 6–7; *Lactobacillus Fermentation* (web).
- "Pitch Lactobacillus between **90 °F and 110 °F (32–43 °C)** depending on your Lactobacillus
  strain or blend for **~1–4 days**" (Best Practices).
- Recipe: "Chill the wort down to 95 °F (35 °C)... Allow it to sour for **24 hours**"; then "chill the
  soured wort down to ~70 °F (21 °C) and pitch" the yeast; "After 2 weeks a stable gravity should be
  reached" (steps 6–7).
- *Lactobacillus Fermentation*: tests at ~90 °F (32 °C), 2 weeks, pure Lactobacillus does not ferment
  wort to completion (only ~0.5 °P): so the main yeast is needed.
- Method: pre-souring **in the fermenter after the boil** (the recipe's no-boil/no-hops route is not
  used: hops inhibit L. plantarum, "Do not use any hops if using a hop sensitive species", a
  caution carried in `because`).
- The overlap of the MTF band (32–43 °C) and the chosen culture's `temp_c` (YF-998/999: 15–35 °C)
  is 32–35 °C. **Souring temperature = the overlap's top, 35 °C** (MTF recipe's figure). Days: **1**
  (the recipe's 24 h; the 1–4 day range is in the text). If the overlap is empty, no souring step
  is made and `because` says so.
- Then cool to the main yeast's start temperature S (the next `ferment` step) and pitch it.

**Becomes:** the `souring` step of `app.ferment_schedule`; test `test_b14_souring_first`.

## 14. CO₂ volumes and priming sugar

Source: HTB ch. 10, "Priming", p. 155–161 / PDF 181–187.

**Families** (p. 159 / PDF 185, "a list of typical volumes of CO₂ for various beer styles"):

| Family code | Book name | Volumes |
|---|---|---|
| `british-ales` | British ales | [1.5, 2.0] |
| `porter-stout` | Porter and stout | [1.7, 2.3] |
| `belgian-ales` | Belgian ales | [1.9, 2.4] |
| `american-ales` | American ales | [2.2, 2.7] |
| `european-lagers` | European lagers | [2.2, 2.7] |
| `belgian-lambic` | Belgian lambic | [2.4, 2.8] |
| `american-wheat` | American wheat beer | [2.7, 3.3] |
| `german-wheat` | German wheat beer | [3.3, 4.5] |

The recipe's volumes = the **middle** of the style's family range (`ref.beer_style.co2_vol` =
the family's range; step 15 takes its midpoint).

**Style → family table (for your review):**

| Style | Family | Why |
|---|---|---|
| 21A American IPA | `american-ales` | American ale |
| 21C Hazy IPA | `american-ales` | American ale |
| session-india-pale-ale | `american-ales` | American ale |
| 18B American Pale Ale | `american-ales` | American ale |
| 18A Blonde Ale | `american-ales` | American ale |
| 19C American Brown Ale | `american-ales` | American ale |
| 1C Cream Ale | `american-ales` | American ale |
| 22C American Barleywine | `american-ales` | American ale |
| 16B Oatmeal Stout | `porter-stout` | named |
| 16A Sweet Stout | `porter-stout` | named |
| 20B American Stout | `porter-stout` | named |
| 15B Irish Stout | `porter-stout` | named |
| 20C Imperial Stout | `porter-stout` | named |
| 13C English Porter | `porter-stout` | named |
| 11B Best Bitter | `british-ales` | named |
| 14B Scottish Heavy | `british-ales` | British Isles ale |
| 15A Irish Red Ale | `british-ales` | **judgement:** Irish red, the nearest family |
| 17C Wee Heavy | `british-ales` | Scottish ale |
| 17D English Barley Wine | `british-ales` | English ale |
| 26B Belgian Dubbel | `belgian-ales` | named |
| 25A Belgian Blond Ale | `belgian-ales` | named |
| 25B Saison | `belgian-ales` | **judgement:** Belgian (modern saisons are carbonated higher; the book has no row for it) |
| 5D German Pils | `european-lagers` | named |
| 3B Czech Premium Pale Lager | `european-lagers` | European lager |
| 6A Märzen | `european-lagers` | European lager |
| 8B Schwarzbier | `european-lagers` | European lager |
| 1B American Lager | `european-lagers` | **judgement:** the book has no American lager family; lager, and the range equals American ales' |
| mexican-style-amber-lager | `european-lagers` | **judgement:** same reason |
| 5B Kölsch | `european-lagers` | **judgement:** German, lagered; same range as American ales |
| 10A Weissbier | `german-wheat` | named |
| 23A Berliner Weisse | `german-wheat` | **judgement.** The book names neither Berliner Weisse nor sours but lambic; Berliner is a German wheat beer with high carbonation, so German wheat (3.3–4.5) was chosen over lambic (2.4–2.8). **Question 2** |
| specialty-honey-beer | *(no family, 2.5 default)* | see question 5 |

Checked: every style above maps to exactly one family (30 styles + the honey exception).

**Default** (decision Q1): a style with no `co2_vol` gets **2.5 volumes**, from HTB p. 155 / PDF 181:
"medium carbonation seems to work pretty well for everything"; "¾ cup of corn sugar for a 5 gal.
(19 L) batch... will produce about 2.5 volumes of CO₂... pretty typical of most American and
European pale ales". `from: default`.

**Priming sugar formula** (sidebar "Volumes of CO₂ per Gram of Sugar", p. 156–157 / PDF 182–183):

    weight (g) = (target CO₂ − residual CO₂) × litres of beer × (342.3 / 4) / gas volume
                 = (target − residual) × litres × 85.575 / gas volume        (table sugar, sucrose)

with the gas volume constant (L/mol) and the residual CO₂ from Table 10.3 (p. 161 / PDF 187)
for **the highest temperature of the beer after fermentation** ("the amount of residual CO₂ in
the beer before priming is given by the highest temperature after fermentation", p. 158 / PDF 184);
that temperature is step 14's `max_temp_c`, the highest temperature of the souring, `ferment`
and `rest` steps (the crash, lagering and dry hop only cool). Elevation is the book's 100 m
(table note); no correction.

Worked example: 2.5 volumes, 19 L, 21 °C (gas 24.5, residual 0.80): (2.5 − 0.80) × 19 × 85.575 /
24.5 = **112.8 g** (cane sugar, Table 10.1 p. 158: 113 g). Corn sugar: ÷ 0.91 × 3.68 / 3.49 →
**131 g** (Table 10.1: 131 g). Tests use cane sugar. Table sugar is the only sugar the step
reports (Table 10.1 lists others; the tables say the conversion to corn sugar is × 1.16, p. 159).

**Table 10.3** (p. 161 / PDF 187, all 26 rows as data; temperature °C, gas volume constant L/mol,
residual CO₂ volumes; the g/L columns are computed by the formula and checked in the test against
the three spot values: 5 °C 2.5 vol → 4.4, 21 °C 2.5 → 6.0, 30 °C 4.5 → 13.1 g/L):

| °C | gas | resid. | | °C | gas | resid. | | °C | gas | resid. |
|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 23.1 | 1.32 | | 14 | 23.9 | 0.99 | | 23 | 24.6 | 0.75 |
| 6 | 23.2 | 1.27 | | 15 | 24.0 | 0.96 | | 24 | 24.7 | 0.73 |
| 7 | 23.3 | 1.23 | | 16 | 24.0 | 0.93 | | 25 | 24.8 | 0.72 |
| 8 | 23.4 | 1.19 | | 17 | 24.1 | 0.90 | | 26 | 24.9 | 0.70 |
| 9 | 23.5 | 1.16 | | 18 | 24.2 | 0.87 | | 27 | 25.0 | 0.68 |
| 10 | 23.5 | 1.12 | | 19 | 24.3 | 0.84 | | 28 | 25.0 | 0.67 |
| 11 | 23.6 | 1.08 | | 20 | 24.4 | 0.82 | | 29 | 25.1 | 0.65 |
| 12 | 23.7 | 1.05 | | 21 | 24.5 | 0.80 | | 30 | 25.2 | 0.64 |
| 13 | 23.8 | 1.02 | | 22 | 24.5 | 0.77 | | | | |

(5–30 °C, 26 rows.) A temperature below 5 or above
30 °C raises; a fractional temperature takes the nearest whole °C row (plan).

**Becomes:** `ref.beer_style.co2_family`, `co2_vol`; `app.residual_co2`, `app.priming_sugar_g`;
tests `test_palmer_cane_sugar`, `test_table_10_3_cells`, `test_residual_rows`, `test_co2_from_style`,
`test_default_co2`.

## 15. The BJCP 8-city table (check only)

Source: `shared/rag-files/water/bjcp_study_guide_water.md`, "Famous Brewing Waters" (ppm, from
Palmer's *How to Brew*); the guide's own PDF is `books/bjcp_exam_study_guide_2017.pdf` §IV.B. Cities'
RA computed from Kolbach (bicarbonate × 50 / 61.017 for alkalinity; computed here, nothing stored):

| City | Ca | Mg | SO₄ | Cl | Alkalinity (CaCO₃) | RA | SO₄ : Cl |
|---|---|---|---|---|---|---|---|
| Plzen | 10 | 3 | 4 | 4 | 2 | −6.4 | 1.0 |
| Dortmund | 225 | 40 | 120 | 60 | 180 | −4.0 | 2.0 |
| Munich | 109 | 21 | 79 | 36 | 140 | 49.9 | 2.2 |
| Vienna | 163 | 68 | 216 | 39 | 199 | 42.7 | 5.5 |
| Burton | 352 | 24 | 820 | 16 | 262 | −3.3 | 51 |
| Dublin | 118 | 4 | 54 | 19 | 261 | 174.8 | 2.8 |
| Edinburgh | 100 | 18 | 105 | 45 | 131 | 49.1 | 2.3 |
| London | 52 | 32 | 32 | 34 | 85 | 29.3 | 0.9 |

**Test expectations only** (`test_targets_agree_with_bjcp_cities`, Task 4; the city numbers are
read from the file at test time and never stored; each is a comparison between the aims of the
mapped styles' rows, not a copy of a city's ions):
1. Pilsen (3B, `lager-light-pale`) has a lower sulfate aim than Burton (21A, `ale-medium-pale-assertive`).
2. Dortmund (5D, `lager-medium-pale`): sulfate aim > chloride aim (the city's SO₄ : Cl is 2).
3. Burton (21A): sulfate aim ≫ chloride aim (city 51 : 1; the row 100–400 vs 0–100).
4. RA order: the city RAs run Pilsen (−6.4) < Vienna (42.7) < Munich (49.9) ≈ Edinburgh (49.1) < Dublin
   (174.8); the mapped rows' RA midpoints run 3B (−30) < 6A (30) < 8B (60). The test compares only
   those three (Pilsen, Vienna, Munich) and checks the row midpoints keep the same order.
5. Edinburgh (14B, `ale-light-amber`): RA range [0,60] contains the city's 49.1.
6. London (13C, `ale-medium-brown-black`): sulfate aim below Burton's (the city has 32 vs 820).
Where a city and its row disagree (Dublin's RA 174.8 is above 15B's row [30,90]; London's RA 29.3 is
below 13C's row [60,120]) the test does not compare them. Dublin fits the strong dark row ([120,200])
but Irish Stout maps to the light dark row (§4); recorded here so the disagreement is on file.

## 16. Bru'n Water 1.25

Oracle only (`water/brunwater_1.25.xlsx`; © all rights reserved, formulas not copied). I have not
opened the spreadsheet or entered a case: **the mash-pH estimate is unverified against Bru'n
Water.** If you enter the §7 hand case (4.0 kg Pilsner malt, 12 L, Ca 52.8, SO₄ 25, Cl 75, alkalinity
0) and send me its mash pH, Task 3 adds `test_brunwater_oracle` (± 0.15). The plan says do not wait
for it. Bru'n Water *Water Knowledge* (web) is used as a source only for the points named in §5,
§6 and §7.

## 17. Not used

- **Titration curves** (*Water* Figures 17–21, ch. 5): the zero-sum estimate uses average buffer
  capacities (Table 9) instead, as the brief allows.
- **Z alkalinity and Z RA** (ch. 5, p. 73–77; ch. 6 option 1b/1d): they need the source water's pH
  (`app.brewer_profile` has none; default is distilled). Kolbach RA is used throughout (the book
  says "the most straightforward is to use Kolbach", p. 132).
- **Acid tables** (ch. 6, Appendix B), sparge-water acidification amounts, Sauermalz dose (2 % of the
  grist, p. 130 / PDF 148): step 12 says when acid would be needed, never how much (brief Scope Out, A10).
- **Magnesium salts** (§6). **Water softening, boiling, dilution** (ch. 6): source water is distilled.
- **Kegging and force-carbonation tables** (HTB Table 10.4, p. 167, and the kegging text; brief Out): priming only.
- **Priming with sugars other than table sugar** (Table 10.1's other rows).
- **Yeast starters, cell counts of harvested slurry, rehydration** (*Yeast* ch. 7, p. 124 ff.).
- **Multi-step mash profiles and decoction** (brief Out; RECIPE-ROADMAP §8 Later TODO).
- **Protein rest** (§9) and **dry-hop agitation / burping** (§12).
