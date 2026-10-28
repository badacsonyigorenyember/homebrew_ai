# M7 · Doc → calc pass for steps 12–15

Status: **waiting for your review** (second pass, 2026-10-28, after your answers): §4 (style → water row,
now with one web-sourced row and basis labels), §5, §7, §11, §14, and the values marked `unsourced` / `judgement`.
Work: [brief.md](brief.md) · [plan.md](plan.md) (Task 1) · written 2026-10-28 (PROJECT.md §6.7, brief R1, A1)

**Source rule (your standing rule, 2026-10-28).** Where there is an open question of brewing
methodology, *How to Brew* (HTB, 2017) is the only source of truth if it covers the point; other
books, articles and the web are used only where HTB is silent (HTB is newer than *Yeast*, 2010,
and *Water*, 2013). This pass re-checked every section against HTB. §18 lists every switch.

Every formula, table and constant that steps 12–15 use is in this file with book, chapter and
page. Page numbers are **printed page / PDF page**: *How to Brew* (HTB) printed + 26 = PDF,
*Water* printed + 18 = PDF, *Yeast* printed + 21 = PDF ([`BOOKS.md`](../../BOOKS.md)). Web
sources have no page and are cited by section. Text was read with `pdftotext -layout`; the
arithmetic in the worked examples was run in a scratch script (not kept in the repo), so those
figures are measured, not copied. Tables are quoted only as far as the code needs them.

**Page numbers inside the books.** *Water*'s text points at "Table 14", "Table 15" and "Table 17
(p. 153)" where the PDF has Tables 18/19 and Table 17 on printed p. 118. The cross-references come
from another layout of the book; I cite the table by its caption and by the page I read it on.

## Decisions since the first pass (your answers, 2026-10-28)

All applied below; nothing is open except your review of the tables and values listed in the report.
- Q1 → A8 cites HTB Table 7.1 (p. 114): 1.050 SG / 12.4 °P, 0.75 billion/L/°P, 20 L = 180 billion cells (§10).
- Q2 → souring culture pitch from HTB p. 206: 100-200 billion cells per 19 L, **150 billion per 19 L used** (the middle: HTB says lower rates make off-flavours), scaled to the batch and
  counted in 100 billion packs (20 L: 158 billion, 2 packs); main yeast 1.0 billion/L/°P after souring (p. 212). Replaces "keep 1 pack" (§10, §13).
- Q3 → acid line target by colour: pale 5.2-5.4, amber 5.3-5.5, dark 5.4-5.6, no row 5.2-5.6 (§7).
- Q4 → hint positions kept; HTB caps added (§5).
- Q5 → souring in the fermenter after the boil, as planned (§13).
- Q6 → `ref.water_salt` baking soda left as stored (§1).
- Q7 → honey beer CO₂ = HTB American ales 2.2-2.7 (§4b, §14) -- **superseded by outside-review change 3 below: `specialty-honey-beer` gets the 2.5 default.**
- Outside review (your "apply all three", 2026-10-28): (1) alkalinity is dosed from the grist-based pH estimate, not the row's RA (§6, §7); (2) every
  style → row (and → CO₂ family) mapping carries a basis label `listed` / `inferred` / `judgement` / `web`, stored in `ref` and shown in step 12 and 15 (§4, §14); (3) `web-honey-beer` is dropped: honey
  beer takes its base style's row, `specialty-honey-beer` itself falls back to the no-row defaults and the 2.5 volumes default (§4b, §14).
- Earlier: 23A CO₂ = German wheat 3.3-4.5; lager diacetyl rest 6 days, ale 4 days (§11); dry yeast 10 billion/g (§10).

## 0. The brief's three assumptions

| Assumption (brief) | Result |
|---|---|
| *How to Brew*'s 8 style families cover every style once each is mapped to one | **Holds** for the 31 style codes in §14 (every one has a family; seven are judgement calls, marked; of those only 23A's choice changes the volumes, the lager and Kölsch calls give the same range as the alternative). **One exception:** `specialty-honey-beer` (BA, ranges 1.03–1.11 OG, 1–100 IBU, 1–100 SRM) has no family by its ranges; the BA text says it "may be brewed to a traditional style or may be experimental", so it follows its underlying (base) style. It stays out of the table and gets the no-row defaults (no salts) and the 2.5 volumes default (§4b, §14). |
| A sourced cell count per pack or per gram exists for the yeasts the briefs use *(unverified)* | **Holds generically, not per product.** HTB p. 108 gives about 10 billion viable cells per gram of dry yeast and 100 billion per liquid package (*Yeast* p. 124 and 140: 7–20 billion and 100 billion). `ref.yeast` and the hopline files hold no cell count and no maker's data sheet is in the repo, so §10 uses HTB's generic figures. For a souring culture HTB p. 206 gives a rate (100–200 billion per 19 L), which replaces "no source" (§10). |
| *Water*'s Tables 18–19 rows can be matched to a recipe from its style, colour and bitterness | **Holds for 30 of the 31 codes** (the 29 that step 4 returns for the briefs, plus 17D and 20C, §4); the 31st, 23A, has a web-sourced row. The row lists name 19 of them; ties and judgement calls are marked in §4. **Exception: 23A Berliner Weisse.** The book says its tables exclude sours (p. 119: "excluding sours and wood aged"), and HTB has no per-style rows (ch. 22: the brew cube numbers are "for frame of reference only"). 23A gets a web-sourced row instead (§4b). |

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

HTB Table 21.2 (ch. 21, p. 344 / PDF 370) and Table 8.2 (ch. 8) give the same figures (calcium chloride 72.0 Ca / 127.4 Cl, gypsum 61.5 / 147.4 per gallon); only baking soda differs: HTB prints HCO₃ 710.5 mg/L and 11.8 mEq/L (question 6).

Solubility limits the book gives (p. 117): gypsum about 2 g/L (stir hard), chalk 0.05 g/L. No
dosing rate in a recipe here reaches 1.9 g/L of gypsum (highest aim in §3: sulfate 400 mg/L =
0.72 g/L).

## 2. Kolbach residual alkalinity

Source (HTB first): *How to Brew* ch. 21, p. 342 / PDF 368 (same equation, same 1.4 / 1.7 factors, ppm as
CaCO₃, and the unit table 21.1, p. 339); *Water* ch. 4, "Residual Alkalinity", p. 53–54 / PDF 71–72 and ch. 7,
p. 124 / PDF 142 say the same.

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

**Alkalinity and RA columns are references only (outside review, 2026-10-28).** They are reported in step 12 as an `outside_row` note when the recipe's water falls outside them; they are never dosing targets. Alkalinity is dosed from the grist (§6, §7), on HTB p. 350 and p. 363 (brew cube numbers "for frame of reference only—do not use them as targets").

**Source note.** HTB has no per-style rows: ch. 22 (p. 363) says the brew cube numbers are "for frame of reference only—do not use them as targets for specific styles". These 16 rows therefore stay from *Water*, the only source HTB does not cover. Where HTB gives general limits (Table 8.1, p. 134; seasoning guidelines, p. 135) they cap the aims (§6).

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
codes (plus specialty-honey-beer) are the 29 that step 4 returns for b01–b24 and h01–h06 (measured with
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
| 23A Berliner Weisse | 30 · 2.5 · 5.5 | `web-berliner-weisse` | not in *Water* (sours excluded, p. 119) or HTB; web-sourced row, §4b |
| specialty-honey-beer (BA) | 70 · 50 · 50 | *(no row)* | ranges too wide for a band (1.03–1.11 OG, 1–100 SRM and IBU), and the BA text says honey beer follows its underlying style. A honey beer in a brief reaches step 12 as its base style (b12: 31B → 18A, measured); the style itself falls back to the no-row defaults (decision Q1) |

Every other `ref.beer_style` code (254 of 285, `specialty-honey-beer` among them) gets no row and no `co2_vol`
(decision Q1) -- except 23A, whose web-sourced row is below.

**Basis labels (outside review, 2026-10-28).** Every mapping carries one, stored in `ref.beer_style.water_basis` and carried into step 12's output (`target.basis`, and `target.fallback` = true unless the
basis is `listed`), so a recipe says when its row is a fallback. `listed` = the book's row names the style; `inferred` = read from the bands; `judgement` = a tie or call (the ones I marked above, as you
listed them); `web` = the web-sourced row.

| Basis | Styles |
|---|---|
| `listed` | 21A, 18B, 16B, 16A, 20B, 20C, 19C, 10A, 1C, 5B, 11B, 14B, 26B, 25A, 17C, 17D, 22C, 1B, 3B, 5D, 6A, 8B |
| `inferred` | mexican-style-amber-lager |
| `judgement` | 21C, session-india-pale-ale, 13C, 18A, 25B, 15B, 15A |
| `web` | 23A |

### 4b. One web-sourced row (23A) and the honey beer research that was dropped -- for your review

HTB and *Water* have no Berliner Weisse row (*Water* excludes sours, p. 119). You asked for web research. Stored as an extra row
in `ref.water_profile` with `table_no = 'web'`, `basis = 'web'`, and its own `ref.source` row (the URLs are in
[`SOURCES.md`](../../SOURCES.md)); it is not a Table 18/19 row and the tests that count the book's 16 rows count only `table_no in ('18','19')`.
Answer to your question "general row or a dedicated row per style": the table is keyed per style *group* (16 groups cover
30 styles); a style gets its own row only when no group fits, as 23A. Not decided here (the orchestrator answers
that in chat).

**23A Berliner Weisse -- `web-berliner-weisse`.** What the sources say (fetched 2026-10-28; none is a book):

| Source | What it gives | Weight |
|---|---|---|
| Brewer's Friend recipe "#1 Berliner Weisse" (brewersfriend.com/homebrew/recipe/print/1109903) | target profile Ca 48, Mg 3, Na 0, Cl 47.7, SO₄ 50, HCO₃ 0; no source named | one homebrewer's recipe |
| HomebrewersAssociation forum thread "Water profile wheat/hefe" (forum.homebrewersassociation.org/t/water-profile-wheat-hefe/28606) | Bru'n Water users: Ca 40-50, sulfate and chloride "20 or less"; M. Brungard: "both should be modest"; mash pH 5.4 or lower; K. Troester (quoted) for a Weissbier hell: RA about 0, Ca 50, SO₄ 57, Cl 43 | forum posts relaying named authorities |
| Learning to Homebrew, Berliner Weisse guide (learningtohomebrew.com/?p=513155) | "soft water with a balanced chloride-to-sulfate ratio... keep both levels low" | **search-result text only; the fetched page held no water text** (unverified) |
| Brewer's Friend recipe "Washingtonian Raw Weisse" | Ca 100, Cl 50, SO₄ 100 | **not used:** the stored profile is named "Braukaiser Edel Hell", a Helles profile, not a Berliner one |

Two sources agree (Ca about 40-50, Cl about 43-48, SO₄ 50-57 in the two that give numbers; low and balanced in the others). HTB overrides where it
speaks: Ca minimum 50 (Table 8.1, p. 134); "soft" structure Ca 50-100 (brew cube, p. 363); pale beer mash pH 5.2-5.4 (p. 365); Lactobacillus beers
5-8 IBU (p. 206). Proposed row:

| Code | Table | Ca | Alkalinity | SO₄ | Cl | RA | Acidify | Basis |
|---|---|---|---|---|---|---|---|---|
| `web-berliner-weisse` | web · ale · light · pale · 3-8 IBU | [50,100] | [0,40] | [20,60] | [40,60] | [-60,0] | yes | Ca: HTB; alkalinity 0 in the Brewer's Friend profile and "soft"; SO₄/Cl: BF profile (50/47.7), Troester (57/43), forum (low); RA: computed from Ca 50-100, alk 0-40 |

Mid aims: SO₄ 40, Cl 50 (ratio 0.8:1, "balanced"). With Ca at the HTB minimum, gypsum 40 and calcium chloride 50 give Ca 45, so
calcium is raised to 50 as in §6. b14 gets this row; it is `unverified` against any brewery source.

**`specialty-honey-beer` -- researched and dropped (outside review, 2026-10-28).** Your figures, checked (kept as a record):

| Your figure | Check | Verdict |
|---|---|---|
| Ca 50-100 | HTB Table 8.1: 50-150, minimum 50; blonde-ale guidance (Newman, Maui Brewing, via getollie.com/blog/blonde-ale-brewing-guide, fetched): Ca 50-100 | holds |
| SO₄ 60-90 | HTB: 50-400 (drier, crisper, p. 133-134); same Newman guidance: SO₄ 50-100 | holds |
| Cl 50-60 | HTB: 50-150 (fuller, sweeter); Newman: Cl 50-75 | holds |
| SO₄ : Cl 1.2-1.5 : 1 | HTB: balanced about 1:1, hoppy 5:1 (p. 134). Computed from your ranges: 60/60 = 1.0 up to 90/50 = 1.8, middle 75/55 = 1.36 | consistent at the middle only: the ratio range is **narrower** than the two ranges allow (the hint positions 12.5 % / 87.5 % give 1.09 and 1.68, outside 1.2-1.5; positions kept by your decision) |
| Mg 5-15 | HTB Table 8.1: 0-30, "5 ppm minimum... usually fully supplied by the malt extract" | holds (no Mg salt is dosed, §6) |
| Na 0-30 | HTB: 0-100 (> 100 minerally); Bru'n: below 60 in practice | holds (stricter than HTB) |
| CO₂ 2.5-2.8 | HTB p. 155: 2.5 for "most American and European pale ales"; p. 159: American ales 2.2-2.7; nothing for honey | **not in HTB**; 2.5-2.7 overlaps. Decided: HTB's American ales 2.2-2.7 |
| why (yeast health, flocculation; crisp finish to cut sweetness; roundness after honey ferments out) | HTB p. 133-134 on Ca, sulfate, chloride | holds as flavour/process reasoning; I found **no source for a honey-specific water profile**: web search returned blonde-ale guidance (Newman; The Electric Brewery: Ca 50, Mg 10, Na 16, Cl 70, SO₄ 70, a balanced blonde) and one homebrewtalk thread (not fetched, HTTP 403; snippet only) |
| origin of your figures | not traceable | the BA text says honey beer "may be brewed to a traditional style or may be experimental" -- a honey beer's water should follow the underlying style; this row is only the fallback |

**Why no `web-honey-beer` row:** no honey-specific source exists (web search found only blonde-ale guidance and one forum thread), and the BA text says honey beer "may be brewed to a traditional style"
-- it follows its underlying style. The pipeline already classifies to the base style (b12: 31B → 18A, measured), so a honey beer's water comes from that style's row. `specialty-honey-beer` itself,
if it ever reaches step 12, gets the no-row defaults (decision Q1: no salts, pH estimate of the source water). CO₂: the 2.5 volumes default (§14): HTB's American ales family would assume one underlying
style, which the BA text says is not so. The check above stays here as a record of what was verified.

## 5. Hints → aim

Source (HTB first): step 1's hint vocabulary (contract `step1.output.schema.json`): `bitter, hoppy, juicy,
dry, crisp, full, chewy, malty, darker, stronger, session`.

- HTB ch. 8, p. 133 / PDF 159: "Chloride accentuates the maltiness of the beer, making the beer seem fuller and sweeter.
  Sulfate accentuates the hop character of the beer, making the beer taste drier and crisper"; p. 134: hoppy beers like IPA a
  sulfate-to-chloride ratio of 5:1, malty beers (bock, Oktoberfest) 1:1 or 0.5:1, "not a rule, however, it is a guideline"; ch. 22, p. 364:
  hoppy 4:1, balanced, malty on the brew cube.
- Where HTB is silent on a hint (`juicy`): Bru'n Water *Water Knowledge* §2.5.2: "Brewers of juicy IPAs have reported... around 150 ppm
  chloride and 75 ppm sulfate" (chloride-led).
- *Water* (ch. 7, p. 115-116) says the same and is no longer needed for the direction.
- The 87.5 % / 12.5 % positions are RECIPE-ROADMAP §7's (the user's 2026-10-17 decision, the
  same positions step 4 uses for its knobs, `app.hint_knob`). They are not HTB's (HTB gives ratios); kept by your decision, with HTB's caps added.

| Hint | Side | Passage |
|---|---|---|
| `bitter` | sulfate | HTB p. 133 (sulfate accentuates hop character) |
| `hoppy` | sulfate | same |
| `dry` | sulfate | HTB p. 133 ("drier") |
| `crisp` | sulfate | HTB p. 133 ("crisper") |
| `juicy` | chloride | Bru'n §2.5.2 (HTB silent) |
| `malty` | chloride | HTB p. 133-134 ("maltiness", malty beers 1:1 or 0.5:1) |
| `full` | chloride | HTB p. 133 ("fuller") |
| `chewy` | chloride | same as `full` (body) |
| `darker`, `stronger`, `session` | none | they move colour, gravity and strength, not the ion balance |

Rule (Approach step 12, item 2): sulfate and chloride aims start at the **middle** of the row's
ranges. One or more sulfate-side hints (and no chloride-side hint) move sulfate to 87.5 % and
chloride to 12.5 % of their ranges; chloride-side hints (and no sulfate-side hint) the reverse;
both sides at once leave the middle and say so. A hint never moves an aim outside the row's range.
Hint pairs in the briefs: b02 `juicy, hoppy` (both sides, so the middle), b11 `dry, full, chewy` (both).
HTB caps apply to every aim: sulfate ≤ 400, chloride ≤ 150, sulfate + chloride ≤ 500 (p. 135); no row range exceeds them (largest
row: sulfate 400, chloride 150, aims at 87.5 % stay below 500 together).

**Becomes:** `app.water_aim(row, hints)` → `moved_by`; `test_aim_moves_with_hints`.

## 6. Salt order and limits

- **Calcium floor and caps** (HTB Table 8.1, p. 134; seasoning guidelines, p. 135): calcium at least 50 ppm (same as the row minimum), sulfate ≤ 400, chloride ≤ 150, sulfate + chloride ≤ 500, "exceeding 200 [calcium] can taste minerally".
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
- **No magnesium salt.** HTB Table 8.1 (p. 134): magnesium 5 ppm minimum, range 0-30, "usually fully supplied by the malt extract"; *Water* p. 119 agrees
  ("the vast majority of this came from the malt"). Epsom and magnesium chloride stay in `ref.water_salt` unused.
- **Sodium ≤ 100 mg/L**: HTB Table 8.1 (p. 134, range 0-100) and p. 133 ("at high concentrations (>100 ppm) it tends to give an overall minerally character");
  *Water* p. 116, 119 and Bru'n §2.5.2 agree. Baking soda is used while the
  resulting sodium stays at or below 100 mg/L (the source water's own sodium counts).
- **Lime over chalk.** *Water* p. 117 / PDF 135 and Table 17: chalk "largely ineffective"
  in the mash, "Don't Use"; Bru'n §4.3.1 (avoid chalk) and §4.3.2 (pickling lime is readily
  soluble). HTB Table 21.2 (p. 344) lists chalk as "does not raise mash pH effectively". Slaked lime's alkalinity is counted at its Kolbach ΔRA (19.28 mEq/L per g/L), the
  form the Foreign Extra Stout example uses (p. 130–132 / PDF 148–150), and the form *Water*
  confirms for additions to the water (ch. 6, p. 105–106 / PDF 123–124).
- **Alkalinity only in the strike water.** (Where it goes; how much is above.) Not a book rule; it follows from the book's
  mash-pH frame (the alkalinity must be in the mash) and from Bru'n §4.3.1 on the mash being the
  place alkalinity matters. Sparge water takes the same gypsum and calcium chloride per litre
  (flavour ions are for the whole beer) and no alkalinity (the book warns about sparge water
  alkalinity raising pH and extracting tannin, Table 18/19 "Acidify" note, p. 120). Marked
  **judgement**; the reason is in the step's `because`.
- **How much alkalinity -- from the grist, not the row (outside review, 2026-10-28).** Alkalinity (baking soda while the resulting sodium stays ≤ 100 mg/L, then slaked lime) goes into the **strike
  water only**, and only until the §7 mash pH estimate reaches the **bottom of the colour target** (pale 5.2-5.4, amber 5.3-5.5, dark 5.4-5.6; 5.2-5.6 without a row). With
  Σ_malt = Σ kg × alk_i, K = 40 × grist kg, V = strike litres and RA₀ = the RA of the strike water with its flavour salts (mEq/L):

      RA needed (mEq/L) = ((target_low − 5.4) × K − Σ_malt) / V        ΔRA = RA needed − RA₀          (dose only when ΔRA > 0)
      baking soda g/L = ΔRA / 11.90 (HCO₃ alkalinity; no hardness effect), capped so Na ≤ 100 mg/L; the rest as lime g/L = ΔRA₍rest₎ / 19.28.

  When the estimate is already at or above the bottom of the target nothing is added; above the top, the acid line says acid would be needed (§7). The row's alkalinity and RA ranges are
  **reported references only**: step 12 adds an `outside_row` note when the recipe's water is outside them, never dosing to them. Basis: HTB p. 350 (the zero-sum method) and p. 363 ("for frame of
  reference only—do not use them as targets"). **The pH model, with its judgement buffer of 40 mEq/(pH·kg) (§7), now drives dosing and is still unverified against Bru'n Water (§16).**
  Worked example (computed): 4.0 kg Pilsen malt, 1.0 kg caramel 60L, 1.0 kg roast (Σ_malt = −49.58 mEq, K = 240), 18 L strike water, no ions, dark target low 5.4: RA needed = 49.58 / 18 =
  **2.754 mEq/L**, baking soda 2.754 / 11.903 = **0.2314 g/L** (Na 63.3 mg/L ≤ 100) in the strike water, 4.2 g in all; the estimate then reads 5.400. A pale 4 kg Pilsen grist (§7) needs none (5.57 is above the
  pale target). `test_alkalinity_follows_grist` checks both; the Foreign Extra Stout lime figure (0.087 g/L for ΔRA 1.68) stays as the unit test of the lime arithmetic.

**The three worked examples** (book, computed):

| Example | Book | Computed | Test |
|---|---|---|---|
| Pilsner (p. 129 / PDF 147): 30 mg/L Ca from CaCl₂ in 10 gal (37.854 L) | 4.17 g; 4.2 g gives 53.5 mg/L Cl | 4.166 g; 53.51 mg/L Cl | `test_pilsner_example` (± 0.02 g, ± 0.2 mg/L) |
| American pale ale option 1 (p. 124–125 / PDF 142–143) | RA 44 at Ca 101; 9 at Ca 150 | 44.2; 9.0 | `test_pale_ale_option_1` (± 1) |
| Foreign Extra Stout 1a (p. 131 / PDF 149): RA 1.32 → 3 mEq/L | 0.087 g/L slaked lime | 0.08705 g/L | `test_foreign_extra_stout_lime` (± 0.002); the total alkalinity back-calculated, 183.8 mg/L, is the second check |

## 7. Mash pH estimate

Source (HTB first): *How to Brew* ch. 21, p. 338-351 / PDF 364-377: "Mash pH is Water Chemistry plus Malt Chemistry" (p. 349-350), Table 21.4 (p. 351 / PDF
377), the RA-to-pH rule of thumb (p. 342 / PDF 368), mash pH targets (p. 341 and, by colour, p. 365 / PDF 391). *Water* ch. 5 (Table 9, titration
curves) is **no longer used** for the malt figures (§18).

**Method** (HTB p. 350: base-malt alkalinity × kg + specialty-malt acidity × kg + water RA (mEq/L) × litres = 0 means the target pH is hit;
a surplus or deficit is the gap), made into a pH estimate with HTB's own buffer figure:

    pH = 5.4 + (Σ kg × alk_i + V_strike × RA_mEq/L) / (40 × Σ kg)

- alk_i: mEq/kg of alkalinity (+) or acidity (−) of mashed fermentable *i* **to target pH 5.4**, HTB Table 21.4, column 5.4 (below).
- **Buffer: 40 mEq per pH unit per kg of grist.** HTB p. 342: the RA change that moves the mash pH by 0.1 is "very nearly equal to 200/Rv" ppm as CaCO₃
  (50 ppm at Rv = 4 L/kg). 200/Rv ppm = 4/Rv mEq/L; times Rv litres per kg of grist = 4 mEq per kg per 0.1 pH = **40 mEq/(pH·kg)**, independent of the
  ratio. HTB calls it "my own experiments"; it is applied here to the whole mash (malt and water together). **Judgement**: it is the only buffer figure HTB gives.
- V_strike = strike water in litres; RA = its Kolbach RA in mEq/L (negative with hardness). A positive sum puts the pH above 5.4.

**Table 21.4 (HTB p. 351), the 5.4 column** (Briess 2015 data, "single data points"; HTB: "for information only"):

| Malt | °L | mEq/kg | Malt | °L | mEq/kg |
|---|---|---|---|---|---|
| Pilsen Malt | 1.5 | 9.2 | Caramel 40L | 40 | −30.4 |
| Brewers Malt | 1.9 | 5.0 | Special Roast | 40 | −13.0 |
| Pale Ale Malt | 2.9 | 3.4 | Caramel 60L | 61 | −43.4 |
| Red Wheat Malt | 2.8 | 11.1 | Caramel 80L | 80 | −45.1 |
| Goldpils Vienna | 3.5 | 7.2 | Caramel 120L | 120 | −60.4 |
| Ashburne Mild | 4.4 | 2.6 | Extra Special Malt | 126 | −67.5 |
| Bonlander Munich | 12 | 2.6 | Roasted Barley | 292 | −38.6 |
| Aromatic Munich | 16 | 0 | Chocolate Malt | 416 | −39.7 |
| Victory | 28 | −0.9 | Dark Chocolate | 458 | −48.8 |
| Caramel 20L | 19 | −21.3 | Black Malt | 471 | −36.0 |
| | | | Black Barley | 514 | −51.8 |

**Classes** (`app.malt_acidity(role, ebc)`, a `values` list and a nearest-row pick). °L ≈ SRM = EBC ÷ 1.97 (HTB p. 234-235, "nearly identical"); colour is the midpoint of the
ingredient's `ebc` range (no lower end: its upper end).
- `role` base, kilned, crystal, adjunct: the **non-roast row with the nearest °L** (the 16 rows above the Special Roast / Roasted Barley split: Pilsen... Extra Special).
  Flaked and unmalted adjuncts count as base (Bru'n §2.4 "Grain Acidity": "Flaked malt and grain should be considered base malts"; HTB is silent).
- `role` roast: **one class, −42.98 mEq/kg** (mean of the five roast rows: the stored roast colours, 450-760 °L, sit beyond Table 21.4's 292-514 °L rows and do not separate them).
- `role` sugar is not mashed and is skipped.
This estimate now also drives the alkalinity dose (§6). Not covered by Table 21.4: acidulated malt (treated like its nearest row, so the estimate is too high: the safe side for the acid line) and smoked/Sprau malts (same).

**Targets** (HTB p. 341: "the commonly agreed target range for mash pH is 5.2-5.6, as measured at room temperature"; p. 365: pale 5.2-5.4, amber 5.3-5.5, dark 5.4-5.6, "general
guidelines"). The acid line compares the estimate with the target of the water row's colour (pale / amber / brown-black); a style with no row: 5.2-5.6. Question 3.

**Hand-worked case** (A10; checked by `test_pale_grist_needs_acid`): 4.0 kg Pilsen malt (HTB Table 21.4, 9.2 mEq/kg), strike water 12 L (3 L/kg) from distilled water
with the light-lager aim: sulfate 25, chloride 75. Gypsum 25 / 557.9 = 0.04481 g/L, calcium chloride 75 / 482.3 = 0.15550 g/L, Ca = 52.82 mg/L (≥ 50), alkalinity 0.
RA = −52.82 / 1.4 = −37.73 mg/L as CaCO₃ = **−0.7546 mEq/L**. Σ mEq = 4.0 × 9.2 + 12 × (−0.7546) = 36.80 − 9.06 = 27.74; Σ buffer = 40 × 4.0 = 160.
**pH = 5.4 + 27.74 / 160 = 5.573.** That is inside the general 5.2-5.6 but **above the pale target 5.2-5.4**, so the acid line fires (colour-specific target, your decision). b08's case
through the step (German Pils with `bitter`, Ca about 89): 4.9 kg, 14.7 L: pH about **5.53**, above 5.4, acid line fires. The test checks the function with the grist and strike ions given
directly, within 0.02 of 5.573.

**A dark grist on distilled water** (`test_dark_grist_on_distilled_is_low`): 4.0 kg Pilsen malt, 1.0 kg Caramel 60L (−43.4), 1.0 kg roast (−42.98), no alkalinity,
ions zero: Σ mEq = 36.8 − 43.4 − 42.98 = −49.58, Σ buffer = 240, pH = **5.193**, below 5.4. The plan's b05-style grist (80 % base, 10 % caramel, 10 % roast, 8 kg,
24 L, Ca 60, RA −0.857 mEq/L) gives **5.30**, below 5.4 as the plan assumed, so the plan's original test grist stands (my first-round note about 5.47 came
from *Water* Table 9 and no longer applies).

**Becomes:** `app.malt_acidity`, `app.mash_ph_estimate`, tests `test_pale_grist_needs_acid`, `test_dark_grist_on_distilled_is_low`, `test_ph_terms_add_up`. Marked
**unverified against Bru'n Water** (§16).

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
17.1, p. 263 / PDF 289: 30-60 min; s5's model assumes a 60 min rest, `s5-mash-attenuation` doc-calc §4). All figures are HTB's.

| Rest | °C | Minutes | Trigger | Source |
|---|---|---|---|---|
| Ferulic acid | **40** | **30** | style 10A Weissbier, 10B Dunkles Weissbier, 10C Weizenbock | HTB ch. 17, p. 264 / PDF 290: "104 °F, 145 °F, 158 °F (40 °C, 63 °C, 70 °C) mash, using a half hour rest at each temperature... The time at 104 °F (40 °C) serves as a ferulic acid rest" for Bavarian wheat beers; Table 17.2, p. 265: 10-20 min at 40 °C (the text's half hour is used). *Yeast*'s 43 °C (p. 33) is no longer used |
| Beta-glucan | **45** | **20** | `role = 'adjunct'` above 20 % of the grist by mass | HTB ch. 16, p. 244 / PDF 270: "Resting the mash at 104-118 °F (40-48 °C) for 20 min... recommended... when using more than 20 % of unmalted or flaked barley, oatmeal, rye, or wheat" (optional at 10-20 %); Table 16.2, p. 249 / PDF 275. 45 is the middle of 40-48 |
| Protein | -- | -- | **not used** | HTB p. 245 / PDF 271: only for moderately modified malts or more than 20 % unmalted wheat, rye or oats; a long (> 30 min) rest at 50 °C removes body and foam. No modification column in `ref.fermentable`, so no rule the data can test |
| Mash-out | **77** | **10** | always | HTB ch. 16, "Mash-Out", p. 252 / PDF 278: raise "to 170 °F (77 °C) prior to lautering"; "not needed" at 3-4 L/kg, "may be helpful" above 25 % wheat/rye/oats; the plan includes it (decision 3). **The 10 minutes are `unsourced`:** HTB gives no time |

Ordering: neutral rests by temperature ascending, saccharification rest, mash-out. A weizen with a beta-glucan trigger as well keeps **one** rest at 40 °C for 30 min
(inside both HTB ranges, judgement). Flaked share is by mass of `role = 'adjunct'` over all mashed fermentables.

**Becomes:** `app.mash_rests(style_code, grist, mash_c)`; tests `test_rests_are_neutral_and_sourced` (every rest but saccharification is below 55 °C or the 77 °C mash-out, with a
`source`), `test_weizen_gets_ferulic_rest`, `test_flaked_over_20_gets_beta_glucan_rest`, `test_single_infusion_otherwise`.

## 10. Pitch rate

Source (HTB first): *How to Brew* ch. 7, "What Is the Pitching Rate and Why Does It Matter?" p. 111-114 / PDF 137-140, Tables 7.1-7.3 (p. 114-116), and p. 108 / PDF 134 for cells per gram. *Yeast*
("Pitching Rates", p. 121-124) is **no longer used**.

    cells to pitch = rate (billion cells / L / °P) × wort litres × °P            (1 °P = 4 gravity points, HTB p. 111)

- **Rate**: HTB p. 111-113 gives rates **for fresh yeast** ("only half as much fresh yeast is needed" as repitched): ales 0.5-1.0 billion cells per litre per °P (0.5 Belgian,
  0.75 "balanced... dry stout, English pale ale", 1.0 "very clean... American pale ale"), lagers 1.0-1.5 (1.25 Kölsch and California common, 1.5 Dortmunder, Munich dunkel,
  American lagers and the cleanest lagers). The code keeps two rates, **0.75 for ale yeasts and 1.5 for lager yeasts** (HTB's balanced-ale and moderate-lager figures; the
  same numbers the plan took from *Yeast*, which gives them for repitched yeast). A per-style rate (HTB's list above) is a later refinement. Kveik, brett and no-type yeasts use the ale rate.
- **Worked example**: HTB Table 7.1 (p. 114 / PDF 140): 1.050 SG (12.4 °P), rate 0.75: **9 billion cells per litre** → 20 L = **180 billion cells** (a lager rate 1.5: 19 → 380). The same
  arithmetic as *Yeast*'s 0.75 × 20 000 mL × 12 °P = 180 billion. `test_yeast_book_example` uses HTB's Table 7.1 (brief A8 now cites it).
- **Liquid yeast**: packs = cells ÷ **100 billion**, rounded up (HTB p. 108 and 111: "typically contain about 100 billion cells per package"; *Yeast* p. 140 agrees).
- **Dry yeast**: grams = cells ÷ **10 billion viable cells per gram**, rounded up to 1 g. HTB p. 108 / PDF 134: "dry yeast has about 10 billion cells per gram, so a 10 g packet contains about
  100 billion viable yeast cells" (after rehydration). *Yeast* p. 124 gives 7-20 billion and "as low as 5". Your Q4 answer was 7 billion unless HTB gives its own figure; HTB does, so **10** is used
  and 7 is reported here. At 10 billion/g a 180 billion-cell ale pitch is 18 g (about 2 sachets of 10 g); at 7, 26 g.
- **Souring culture** (`ref.yeast.type = 'lacto'`): HTB p. 206 / PDF 232: "The suggested pitching rate for Lactobacillus is between **100 and 200 billion cells per 5 gal. (19 L)**"; lower rates "produce more
  off-flavors". **150 billion per 19 L** (the middle), scaled to the batch: 150 × batch_L / 19 billion (20 L: 158 billion); a culture package counts as 100 billion (HTB p. 108, liquid), so
  packs = ⌈cells ÷ 100⌉ = **2 packs** for 20 L. Replaces decision Q3 ("keep 1 pack"; your answer 2026-10-28). The 100 billion per pack is HTB's figure for a yeast package, assumed for a lacto package
  (`unverified` for YF-998/999).
- **Main yeast after souring**: HTB p. 211-212: "the pitching rate for the yeast fermentation should be higher than normal... for ales that would normally pitch 0.75... you would instead pitch 1.0".
  Applied when a souring culture is in the recipe (ale yeasts 1.0; a lager yeast keeps 1.5).
- Wort volume for the cell count: the batch volume (`numbers.batch_l`); °P = `app.sg_to_plato(og)`.

**Becomes:** `app.pitch_rate`; tests `test_yeast_book_example`, `test_dry_yeast_in_grams`, `test_liquid_yeast_in_packs`, `test_souring_culture_pitch` (b14: YF-998 pitch 150 × L / 19 billion cells, 2 packs; main yeast rate 1.0).

## 11. Fermentation schedule (**for your review**)

Source (HTB first): *How to Brew* ch. 6 "Yeast and Fermentation" (adaptation, high-growth and maturation phases, Table 6.2, cold conditioning), the lager chapter's "Lagering" (p. 174);
*Yeast* only where HTB is silent (marked).

**Main temperature M** = step 6's `ferm_c` raised to at least the yeast range's lower bound + 1 °C. **Ale start S** = max(M − 2, lower bound): HTB p. 90 / PDF 116 "pitched into the wort when the wort
temperature is at or slightly below the intended fermentation temperature" (example: range 20-23 °C, pitch at 18-20 °C). **Lager start = M**: HTB p. 174 / PDF 200, lager summary item 2, "Pitch at your target
fermentation temperature". The 1-2 °C offset and the 18-36 h rise are *Yeast* p. 97 and are not in HTB (kept for ales as a consistent reading of "slightly below"; no separate rise step).

**Diacetyl / maturation rest** (HTB Table 6.2, p. 94 / PDF 120, and p. 93-94): *lager*: when "day 4 of 6" / 2-5 gravity points from FG, raise by **14-18 °F (8-10 °C)**, leave for **minimum 6 days (up to 12)**;
*ale*: "~day 3 of 4", raise by **5-10 °F (3-6 °C)**, leave **minimum 4 days (up to 8)**. This is your Q3 answer (6 days lagers, 4 days ales), confirmed against HTB: it reads the same. Inside HTB:
p. 172 says a diacetyl rest raises the temperature "by 5 °F [3 °C]" and p. 174 "10-15 °F (5-10 °C)... for at least four days, if not a week"; Table 6.2 is the one table and is used. *Yeast* (18-20 °C,
2 days, p. 113) is no longer used.

| Phase | Applies to | °C | Days | Source |
|---|---|---|---|---|
| `ferment` start | ale, kveik, brett, no-type | S | 1 | HTB p. 90 (first day is mostly adaptation, "high-growth phase... on day 2") |
| `ferment` hold | ale, kveik, brett, no-type | M | 2 | HTB Table 6.2: rest at "~day 3 of 4"; high-growth phase 1-3 days for ales (p. 91) |
| `rest` | ale, kveik, brett, no-type | E = least(M + 3, upper bound) | 4 | HTB Table 6.2: raise 3-6 °C (lowest figure), "minimum 4 days (up to 8)" |
| `ferment` hold | lager (`type = 'lager'`) | M | 4 | HTB Table 6.2: rest at "day 4 of 6"; high-growth 2-5 days for lagers (p. 91) |
| `rest` (diacetyl) | lager | R = least(upper bound, M + 8) | 6 | HTB Table 6.2: raise 8-10 °C (lowest figure), "minimum 6 days (up to 12)". The upper bound keeps A4: 10 of 17 lager yeasts top out at or below 15 °C (measured 2026-10-27) |
| `souring` | culture with `ref.yeast.type = 'lacto'` | 35 | 1.5 | see §13 |
| `dry_hop` | step 10 dry hops | 14 | 3 (contact) | see §12 |
| `crash` | ale, kveik, brett, no-type | greatest(2, M − 8) | 7 | HTB ch. 6 "Cold Conditioning", p. 95 / PDF 121: "slowly cooling the beer down by 2 °F (1 °C) per day to about 9-15 °F (5-8 °C) below the fermentation temperature"; "only have to cold condition for a week or two" (the low end, 7 days). HTB calls this cold conditioning, not a crash. *Yeast*'s 2 °C is no longer used for ales |
| `lager` | lager | 2 | 14 | HTB p. 174 / PDF 200: cool "by not more than 10 °F (6 °C) a day down to about 35 °F (2 °C)"; "The lagering time can be 2-4 weeks, although I recommend shorter times (1-2 weeks) if you plan on priming and bottle conditioning". Packaging here is by priming, so 14 days |

Notes:
- **Kveik** (20 rows, 20-42 °C), **brett** (2), and the **3 yeasts with no `type`** use the ale schedule. HTB and *Yeast* are silent on kveik; its shorter fermentations are not modelled
  (`unsourced`; the ale durations are conservative).
- **A4**: every `souring`, `ferment` and `rest` step lies inside its yeast's `temp_c`. `dry_hop`, `crash` and `lager` are conditioning below any yeast's range and are exempt. A lager yeast whose M plus
  8 exceeds its upper bound rests at the bound.
- **Total days**: ale 1 + 2 + 4 = 7 days at temperature, then dry hop 3 and cold conditioning 7; lager 4 + 6 = 10 days, then lagering 14. HTB p. 102: ale maturation "from two days to two weeks".
- Cooling rates (HTB p. 95: 1 °C/day for cold conditioning; p. 174: up to 6 °C/day for lagering) are in the step's `why` text, not modelled.

**Becomes:** `app.ferment_schedule`; tests `test_every_ferment_temp_in_range`, `test_every_lager_has_diacetyl_rest`, `test_ramp_shape` (ale: S < M ≤ E, lager: start = M),
`test_b13_weizen_schedule`.

## 12. Dry hop and secondary extras

**Dry hop** (step 10 hops with `usage = 'dry_hop'`): after the last `ferment`/`rest` step. Source (HTB first): *How to Brew* ch. 4, p. 72 / PDF 98: "Dry hops for IPAs are generally added to give **3-5 days
of contact time at temperatures of 50-70 °F (10-21 °C)**. Allow less contact time at warmer temperatures. The hops should be removed after this period".
- Temperature **14 °C**, or the last fermentation temperature if lower: inside HTB's 10-21 °C. HTB gives no single value; the point inside is from Janish, *Dry Hop Best Practices*, MBAA TQ 58(1),
  2021 (PDF p. 8): "Dry hop at cool temperatures, 50-58 °F (10-14 °C)" and Sapwood's post-fermentation 58 °F (*A Case for Short and Cool Dry Hopping*).
- Contact **3 days**: the low end of HTB's 3-5 (less contact at warmer temperatures); Janish agrees ("no longer than 3 days"). (Previously 2 days from Janish alone.)
- Day: the first day after the last `ferment`/`rest` step. Amounts: grams as step 10 has them. Agitation and oxygen purging are not modelled.

**Secondary extras** (step 10 extras with `usage = 'secondary'`): day = the first day after the last `ferment`/`rest` step; contact = `ref.misc.time_min` in days (coffee beans 2880 min = 2 days,
Janish *Coffee Beers*, in `ref.misc.field_source`); none (vanilla) → "until it tastes right", `contact_days` null, `unknown`. HTB p. 193 on fruit/spices after primary is the same idea; no
contact times in HTB for coffee or vanilla. Orange peel is `whirlpool` (step 13), cold brew coffee `packaging` (step 15).

**Becomes:** `app.step14_ferment` (`dry_hops`, `secondary`); tests `test_dry_hop_after_fermentation`, `test_secondary_extras`.

## 13. Souring (b14, a souring culture is in the recipe)

Source (HTB first): *How to Brew* "Brewing Sour Beers", p. 206-212 / PDF 232-238.
- **Temperature**: "Lactobacilli grow best between 90-115 °F (32-46 °C), but will still grow well at typical ale fermentation temperatures" (p. 206). Kettle souring chills to 100-110 °F (38-43 °C)
  (p. 211) but the culture rows (YF-998/999) only reach 35 °C, so the **souring step is 35 °C, the top of the overlap with the culture's `temp_c`** (A4). If the overlap is empty, no souring step.
- **Time**: "The wort should take **18-36 hours** to sour to a pH of 3.5-ish" (p. 211): **1.5 days** (the middle). (MTF's 24 h is no longer used.)
- **Order**: "Bacteria first, yeast second" (p. 210): souring in the fermenter after the boil, then the main yeast at its start temperature (HTB kettle souring boils *after* souring, which would
  change step 13's boil; the plan does not; your decision). Hops inhibit lactobacilli: "Berliner weiss, usually only have 5-8 IBUs" (p. 206), carried in `because`.
- **Pre-acidify**: HTB p. 207 and 211 recommend 88 % lactic acid to pH 4.5-4.8 (about 5 mL): the step text says "pre-acidify to pH 4.5-4.8 (amount not computed)"; no acid amount is stored (A10).
- **Pitch**: culture 100-200 billion cells per 19 L (p. 206), main yeast 1.0 billion/L/°P instead of 0.75 after souring (p. 212) -- see §10.
- Pure *Lactobacillus* does not ferment wort fully (HTB p. 206: "only consume a small amount of sugars... about 2-4 gravity points"; MTF *Lactobacillus Fermentation*, ~0.5 °P): so the main yeast is needed.
Milk The Funk (Berliner Weissbier page: 90-110 °F, 1-4 days, 95 °F for 24 h) is kept only as a cross-check; HTB covers the point.

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
| 23A Berliner Weisse | `german-wheat` | **your answer (2026-10-28):** German wheat 3.3-4.5 volumes (the book names neither Berliner Weisse nor sours but lambic) |
| specialty-honey-beer | *(no family)* | **outside review:** no single underlying style (BA text), so the 2.5 default of the next paragraph, `from: default` |

Checked: every style above maps to exactly one family (31 codes); specialty-honey-beer has none.

**Basis labels** (stored in `ref.beer_style.co2_basis`, shown in step 15's `co2.basis`): `listed` = the family names the style or its class ("Porter and stout", "German wheat beer"); `inferred` = by
region or type; `judgement` = the calls marked above (15A, 25B, 1B, mexican amber lager, 5B, 23A).

| Basis | Styles |
|---|---|
| `listed` | 16B, 16A, 20B, 15B, 20C, 13C, 10A |
| `inferred` | 21A, 21C, session-india-pale-ale, 18B, 18A, 19C, 1C, 22C, 11B, 14B, 17C, 17D, 26B, 25A, 5D, 3B, 6A, 8B |
| `judgement` | 15A, 25B, 1B, mexican-style-amber-lager, 5B, 23A |

**Default** (decision Q1): a style with no `co2_vol` (specialty-honey-beer among them) gets **2.5 volumes**, from HTB p. 155 / PDF 181:
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

Oracle only (`water/brunwater_1.25.xlsx`; © all rights reserved, formulas not copied). The spreadsheet
was not opened and no case was entered, so **the mash-pH estimate is checked only against the book's
figures (the §7 hand cases, `test_pale_grist_needs_acid`, `test_dark_grist_on_distilled_is_low`) and is
unverified against Bru'n Water**; no `test_brunwater_oracle` was added (Task 3 did not wait for it). If you
enter the §7 hand case (4.0 kg Pilsner malt, 12 L, Ca 52.8, SO₄ 25, Cl 75, alkalinity 0) and send its mash pH,
the test can be added later (± 0.15). Bru'n Water *Water Knowledge* (web) is used as a source only for the
points named in §5, §6 and §7.

## 17. Not used

- **Titration curves and Table 9** (*Water* ch. 5): replaced by HTB Table 21.4 and HTB's 40 mEq/(pH·kg) (§7).
- **Z alkalinity and Z RA** (*Water* ch. 5, p. 73–77; ch. 6 option 1b/1d): they need the source water's pH
  (`app.brewer_profile` has none; default is distilled). Kolbach RA is used throughout (the book
  says "the most straightforward is to use Kolbach", p. 132).
- **Acid tables** (ch. 6, Appendix B), sparge-water acidification amounts, Sauermalz dose (2 % of the
  grist, p. 130 / PDF 148): step 12 says when acid would be needed, never how much (brief Scope Out, A10).
- **Magnesium salts** (§6). **Water softening, boiling, dilution** (ch. 6): source water is distilled.
- **Kegging and force-carbonation tables** (HTB Table 10.4, p. 167, and the kegging text; brief Out): priming only.
- **Priming with sugars other than table sugar** (Table 10.1's other rows).
- **Yeast starters, cell counts of harvested slurry, rehydration** (HTB ch. 7, *Yeast*).
- **Multi-step mash profiles and decoction** (brief Out; RECIPE-ROADMAP §8 Later TODO).
- **Protein rest** (§9) and **dry-hop agitation / burping** (§12).

## 18. Source rule: every switch to *How to Brew* (second pass, 2026-10-28)

Your rule: HTB is the only source of truth for brewing methodology where it covers the point; other sources only where it does not. Every doc-calc item was re-checked against HTB. Switched to HTB:

| Item | Was | Now (HTB, printed page) |
|---|---|---|
| Diacetyl rest, lager | *Yeast* p. 113: 18-20 °C, 2 days | Table 6.2 p. 94: raise 8-10 °C (8 used), min 6 days; "day 4 of 6" |
| Diacetyl rest, ale | *Yeast*: 2 days at fermentation temperature | Table 6.2: raise 3-6 °C (3 used), min 4 days; "day 3 of 4" |
| Lager start temperature | *Yeast* p. 97: 1-2 °C below M, 18-36 h rise | p. 174: pitch at the target fermentation temperature |
| Ale start | *Yeast* p. 97 | p. 90: "at or slightly below" the fermentation temperature (offset 2 °C kept, rise step dropped) |
| Cold conditioning, ales | 2 °C, 7 days (HTB lagering floor) | p. 95: 5-8 °C below the fermentation temperature, a week or two |
| Dry hop contact | 2 days (Janish) | p. 72: 3-5 days, 10-21 °C (3 days, 14 °C inside the range from Janish) |
| Ferulic rest | 43 °C, 30 min (*Yeast* p. 33 + HTB time) | p. 264: 40 °C, 30 min |
| Pitch rate | *Yeast* p. 121-124 (0.75 / 1.5, repitched yeast) | ch. 7 p. 111-114, Table 7.1: 0.75 / 1.5 billion/L/°P for fresh yeast (same numbers) |
| Dry yeast cells per gram | 7 billion (*Yeast* p. 124) | p. 108: 10 billion viable (7 reported) |
| Liquid package | 100 billion (*Yeast* p. 140) | p. 108: 100 billion (same) |
| Souring: temperature and time | MTF: 35 °C, 24 h | p. 206, 211: 32-46 °C grows best, 18-36 h (35 °C, 1.5 days) |
| Souring culture pitch | none (Q3: 1 pack) | p. 206: 100-200 billion per 19 L; main yeast 1.0 after souring, p. 212 (150 used) |
| Mash pH: malt figures | *Water* Table 9 (Troester/Bies mean) | ch. 21 Table 21.4 p. 351 (Briess/Hansen & Geurts 2015) |
| Mash pH: buffer | *Water* Table 9 per class | p. 342: 200/Rv ppm per 0.1 pH = 40 mEq/(pH·kg) |
| Mash pH: target | *Water* ch. 7: 5.2-5.6 | p. 341/365: 5.2-5.6 overall; pale 5.2-5.4, amber 5.3-5.5, dark 5.4-5.6 (your decision) |
| Sulfate / chloride direction | *Water* p. 115-116 | p. 133-134 (same direction; ratios 5:1 / 1:1 / 0.5:1 not applied; your decision) |
| Calcium floor, ion caps, no Mg salt, Na ≤ 100 | *Water* p. 116, 119 | Table 8.1 p. 134, p. 135 |
| RA formula | *Water* p. 53, 124 | p. 342 (same) |

Already HTB, unchanged: priming and CO₂ (ch. 10), 8 CO₂ families, strike equation and ratio (ch. 17), rests (ch. 16-17), mash-out, saccharification time (Table 17.1), lagering (p. 174).
**Not covered by HTB, so the other source stays:** the 16 style → water rows (*Water* Tables 18/19; HTB p. 363 refuses per-style targets), the 87.5 / 12.5 hint positions (your decision), flaked grain acidity (Bru'n),
the 14 °C dry hop point (Janish), kveik schedules (none), the web rows (§4b), and `ref.water_salt` (HTB's 710.5 vs the stored 726.3 left as it is, your decision).

**Outside review (2026-10-28), not HTB switches:** alkalinity dosing now follows the grist (§6); basis labels on both mappings (§4, §14); `web-honey-beer` dropped (§4b).
