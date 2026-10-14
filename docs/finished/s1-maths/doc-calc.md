# S1 · Doc → calc pass

Work: [brief.md](brief.md) · [plan.md](plan.md) · written 2026-10-14 (PROJECT.md §6.7, brief A1)

This is the doc → calculation pass for the maths library `db/030_maths.sql`. For each formula it
gives the source page, what it became (a function name), and the worked examples that become
tests. Every number below was recomputed from the PDFs with a scratch script (not kept in the
repo), so it is measured, not copied from the plan.

**Sources**
- **HTB** = Palmer & Kaminski, *How to Brew*, 4th ed. (`shared/rag-files/pending/how_to_brew.pdf`).
  Page numbers are the printed ones. The PDF page is the printed one + 26.
- **OBC** = Oregon Brew Crew BJCP class, *Recipe Formulation*, 2009, 6 pages
  (`shared/rag-files/pending/obc_recipe_formulation.pdf`). Cited by its own page 1–6.
- **BYO** = Bill Pierce, "Calculating Alcohol", <https://byo.com/articles/calculating-alcohol/>
  (not in the repo; used for the ABV formula only).

**Tolerances** (brief R7): OG ± 0.001, FG ± 0.002, ABV ± 0.1, IBU ± 1, SRM ± 1 (EBC ± 2). Looser
only where the book rounds more coarsely; each such case is named in its section.

**Units used in the tests** (kept as named constants at the top of `tests/test_maths.py`):
lb = 0.45359237 kg, gal = 3.785411784 L, oz = 28.349523125 g, extract % = PPG / 46 × 100
(HTB p. 290), EBC = 1.97 × °L (HTB p. 469).

## 1. Gravity from extract (R1, R2)

**Formula.** The mass gravity volume equation: mass of extract × PPG = gravity points × volume
(HTB p. 52). PKL is the same in kg and L. The maximum yield of a malt is %FGDB × the sucrose
reference, 46 PPG = 384 PKL (HTB p. 280: "80.7 % of 384 = 310 PKL"). A real brew gets
%FGDB × 46 × efficiency (HTB p. 290: 0.81 × 0.75 × 46 = 27.9 PPG).

**What it became.**
`app.gravity_points(kg, extract_pct, efficiency_pct, volume_l)` = kg × extract/100 × 384 × eff/100 / L.
`app.og(grist jsonb, efficiency_pct, volume_l)` sums it over items `{kg, extract_pct, mashed}`
and returns 1 + points/1000.

**R2: moisture. Answer: no correction.** HTB p. 280 explains that %FGDB is dry basis (malt holds
about 4 % moisture, 2–6 %) and then multiplies %FGDB directly by 46, with no moisture term, in
every example (p. 280, p. 290, tables 18.4 and 18.5). The moisture loss is left inside the
efficiency. So `ref.fermentable.extract_dbfg_pct` is used as stored, for malts and for sugars
(HTB table 24.1, p. 436, also gives sugars as PPG with no moisture term, "multiply the percent
solids by 46").

**Efficiency applies to mashed items only.** Extract and sugar go in at full yield: DME at 42 PPG
(HTB p. 53, p. 78) and OBC's table lists honey, sugars and extracts as "NA" at 75 % and 65 % (OBC
p. 2). So each item carries `mashed`; the caller sets it from `recipe_item.usage = 'mash'`.
Test: `test_efficiency_skips_unmashed`.

**Worked examples** (inputs as printed → expected, tolerance, test name)

| Source | Inputs | Expected | Check (measured) | Test |
|---|---|---|---|---|
| HTB p. 53 DME | 5 lb DME at 42 PPG, in 3 gal, not mashed | 1.070 (70 points) | 70.0 points | `test_og_palmer_dme_example` |
| HTB p. 53 DME, metric | 2.27 kg at 350 PKL in 11.4 L | 1.070 (book 69.7) | 69.7 points | same test, metric case |
| HTB table 18.4, p. 288, at 100 % | 6 gal: 6.5 lb lager 81 %, 0.5 lb each of caramel 15 (75 %), caramel 75 (74 %), chocolate (74 %), roast barley (78 %) | 1.052 | 1.0519 | `test_og_palmer_short_stout_max_yield` |
| same, at 73 % | same, efficiency 73 % | 1.038 (book "38 / 52 = 73 %") | 1.0379 | same test |
| HTB p. 290–291 Short Stout, US | 5 gal, 75 %: 7 lb lager 81 %, 0.5 lb × (75, 74, 74, 78 %) | 1.050 | 1.0495 | `test_og_palmer_short_stout_planned_us` |
| HTB p. 292 Short Stout, metric | 20 L, 75 %: 3.5 kg pale ale 80 % (307 PKL / 384), 4 × 0.225 kg (75, 74, 74, 78 %) | 1.050 | 1.0501 | `test_og_palmer_short_stout_planned_metric` |
| OBC Dubbel, p. 2 | 5 gal, 75 %. Table 100 % column: English pale 1.038 × 4.75 lb, Belgian pils 1.037 × 4.75 lb, Munich 1.038 × 1.25 lb, crystal 80L 1.033 × 0.75 lb (the "Caramunich 75L"), Special B 1.030 × 0.75 lb; candi sugar 1.047 × 0.75 lb, not mashed | 1.0745 (book 372.25 / 5, printed "1.075") | 1.0747 (373.5 points) | `test_og_obc_dubbel` |
| OBC Pils, p. 3 | 5 gal, 75 %: Belgian pils 1.037 × 8 lb, German Vienna 1.037 × 1 lb | 1.0504 (book 252 / 5; printed "1.050") | 1.0500 (249.75 points) | `test_og_obc_pils` |

All inside ± 0.001. Palmer's tables round PPG to whole numbers, which explains the 0.0005 spreads.
For the OBC rows the extract is the table's "points per pound per gallon at 100 %", so
`extract_pct` = points / 46 × 100. OBC's own 75 % column rounds each row to whole points (28,
28, 28, 25, 23), which is why the book's total is 372.25 and not 373.5.

## 2. Boil gravity and volumes (R10)

**Formulas.** Pre-boil volume = batch + losses + boil-off rate × time (a mass balance; the
`app.brewer_profile` fields). Boil gravity points = OG points × batch / pre-boil volume (HTB
p. 291: "multiply the post-boil gravity by the post-boil volume ... divide by the pre-boil
volume"; the book's example is 250 gal.° / 6 gal. = 1.042 and / 7 gal. = 1.036). For an extract
beer the boil gravity is the extract mass × PPG / boil volume (HTB p. 78).

**What it became.** `app.preboil_volume(batch_l, boil_min, boil_off_l_h, losses_l)` and
`app.boil_gravity(og, postboil_l, preboil_l)`. The caller passes the post-boil volume, which is
batch + losses (not the batch volume); the book's 5 gal in the example is its post-boil volume.

| Source | Inputs | Expected | Test |
|---|---|---|---|
| HTB p. 291 | 5 gal at 1.050, boil 6 gal | 1.042 (41.67 points); 7 gal gives 1.036 (35.71) | `test_boil_gravity_book_example` |
| HTB p. 78 Joe Ale | 5.5 lb DME at 42 PPG in 6 gal; metric 2.5 kg at 350 PKL (91.15 %) in 23 L | 1.038 (book 38.5 and 38); measured 38.5 and 38.04 | `test_boil_gravity_joe_ale` (± 0.001) |
| brief A7 | 20 L batch, 60 min, 3 L/h, 2 L losses | 25 L | `test_preboil_volume_example` |

The pre-boil volume has no book example; it is arithmetic and is tested as such (brief A7).
`test_boil_gravity_book_example` (the p. 291 numbers) is a second `boil_gravity` check that the
plan's Task 2 does not list; it is named here so the test is cited, and plan Task 2 gets the same
line as a deviation.

## 3. SG ↔ °Plato (A7)

**Formula.** SG = 259 / (259 − °P) (HTB p. 285, in the extract-to-gravity model). Inverse:
°P = 259 − 259 / SG. The brief asks only for the round trip.

**Table A.2 (HTB p. 465) is not this formula.** It is ASBC's table. At 1.080 the formula gives
19.19 °P and the table gives 19.3. It is noted here and not tested.

**What it became.** `app.sg_to_plato(sg)` and `app.plato_to_sg(plato)`.
Test: `test_plato_round_trip` at SG 1.010, 1.050, 1.100, each within 0.001.

## 4. FG and fermentability (R3)

**Formula.** Apparent attenuation = (OG − FG) / (OG − 1) (HTB p. 108; the printed line has a
stray "− 1" inside the brackets, and the worked example 1.040 → 1.010 = 75 % shows the intended
form). So FG = OG − attenuation × (OG − 1). Fermentability of sugars (HTB table 24.1, p. 436):
corn sugar, table sugar, candi-like sugars ferment 100 %; lactose and maltodextrin are not
fermented.

**What it became.** `app.fg(grist jsonb, efficiency_pct, volume_l, attenuation_pct)`. Items add
`fermentability`: `full` adds 0 FG points, `none` adds all its points, `normal` adds
(1 − attenuation) of its points. So a 100 % candi grist has FG 1.000.

**HTB table 4.3 (p. 55), "assuming 75 % fermentability".** The 7 FG cells equal
FG = 1 + 0.25 × (OG − 1) within 0.0005 (largest differences at OG 1.030, 1.050, 1.070, 1.090:
0.0005). Tolerance ± 0.002.

| OG | 1.030 | 1.040 | 1.050 | 1.060 | 1.070 | 1.080 | 1.090 |
|---|---|---|---|---|---|---|---|
| FG printed | 1.007 | 1.010 | 1.012 | 1.015 | 1.018 | 1.020 | 1.022 |
| Formula | 1.0075 | 1.0100 | 1.0125 | 1.0150 | 1.0175 | 1.0200 | 1.0225 |

Tests: `test_fg_table_4_3`, `test_fg_all_candi_is_one`, `test_fg_lactose_only_is_og`,
`test_fg_unknown_fermentability_raises`, and the three-grist comparison
`test_lactose_raises_fg_candi_lowers_it` (A3). No book gives a lactose or candi FG number, so
those follow from the stated rule and are not "reproductions".

## 5. ABV (R9)

**Source of the formula.** HTB table 9.1 (p. 150) says it is "based on the work of Balling" and
prints no formula. The Balling form published in BYO (Bill Pierce, "Calculating Alcohol",
URL above) is:

- OE = °P of OG, AE = °P of FG (via `sg_to_plato`, HTB's 259 formula)
- RE = 0.1886 × OE + 0.8114 × AE
- ABW = (OE − RE) / (2.0665 − 0.010665 × OE)
- ABV = 1.259 × ABW

**The fit, measured on all 140 cells of table 9.1** (OG 1.030 to 1.075 in steps of 0.005, FG
0.998 to 1.024 in steps of 0.002, as printed to 0.1 %):

| Formula | Cells outside ± 0.1 | Worst difference |
|---|---|---|
| Balling form above, ABV = 1.259 × ABW (**used**) | **0 of 140** | 0.088 |
| BYO's other form, ABV = ABW × FG / 0.794 | 29 | 0.201 |
| Plain 131.25 × (OG − FG) | 65 | 0.194 |

The plan's source check had said 56 cells for 131.25; the re-run here counts 65 (worst 0.194).
It does not change the choice. Recorded as a plan deviation.

**What it became.** `app.abv(og, fg)` using the first row. Test: `test_abv_table_9_1`, all 140
cells typed in as a literal table from p. 150, each within 0.1.

**Table 4.3's ABV row (p. 55) is not tested.** It disagrees with table 9.1 and no formula
reproduces it. For OG/FG 1.060/1.015 table 4.3 prints 6.1 % and table 9.1's formula gives 5.79 %;
the other cells: 1.030/1.007 prints 2.9 against 2.95; 1.040/1.010 prints 4 against 3.85;
1.050/1.012 prints 5 against 4.89; 1.070/1.018 prints 7.2 against 6.70; 1.080/1.020 prints 8.4
against 7.74; 1.090/1.022 prints 9.7 against 8.79. Table 9.1 is the dedicated ABV table (the
note under 4.3 says "a more complete table is presented in chapter 9"), so it wins.

## 6. IBU (R4, A8)

**Formula** (HTB p. 80, Tinseth):
- utilisation U = f(G) × f(t), with f(G) = 1.65 × 0.000125^(Gb − 1) and
  f(t) = (1 − e^(−0.04 t)) / 4.15; t in minutes.
- BU (mg/L) = grams × alpha% × U × 1000 / final litres (the metric form, "factor 10 for g/L",
  p. 78, which is grams × α/100 × U × 1000 / L).
- Gb is the **pre-boil** gravity (HTB p. 78: "the utilization factor depends on the gravity of the
  wort before the boil"), and the volume in the BU equation is the **final** volume after the
  boil.

**What it became.** `app.tinseth_utilisation(boil_sg, minutes)`,
`app.ibu_addition(grams, alpha_pct, minutes, usage, boil_sg, volume_l)` and
`app.ibu(hops jsonb, boil_sg, volume_l)`. The closed form reproduces HTB's table 5.5 (p. 81):
all 160 cells (16 times × 10 gravities) within 0.0005 (printed to 0.001). Tolerance 0.001.
Test: `test_tinseth_table_5_5`.

**Joe Ale** (HTB p. 78–79). Boil gravity 1.038, 5 gal / 19 L final, boil 6 gal / 23 L. The
printed recipe header shows 30 g and 45 g, but the metric calculation uses 28 g Mt Hood 8 % 60
min and 42 g Hersbrucker 4 % 15 min, so those are the inputs.

| Case | Expected (book) | Measured | Test |
|---|---|---|---|
| 28 g, 8 %, 60 min, Gb 1.038, 19 L | 30.3 | 30.29 | `test_ibu_joe_ale_metric` |
| 42 g, 4 %, 15 min | 11.2 | 11.27 | same |
| total | 41–42 ("41 or 42") | 41.56 | same, ± 1 |
| 1 oz, 8 %, 60 min, 5 gal (US) | 30.8 | 30.79 | `test_ibu_joe_ale_us` |
| 1.5 oz, 4 %, 15 min, 5 gal | 11.4 | 11.46 | same |

The book interpolates table 5.5 by hand ("0.257", "0.127"), which is the reason for the ± 1
IBU tolerance. The closed form gives 0.2569 at 60 min and 0.1275 at 15 min.

**Whirlpool and dry hop = 0 IBU.** The book gives no figure for either (confirmed by reading
chapter 5), so both count as 0 IBU now. A cited model is a late-game follow-up (RECIPE-ROADMAP
§8 "Later"). Test: `test_whirlpool_and_dry_hop_add_no_ibu` (A8). Zero hops gives 0 IBU:
`test_ibu_no_hops_is_zero`. An unknown usage raises: `test_ibu_unknown_usage_raises`.

## 7. Colour (R5)

**Formulas.**
- MCU = °L × lb / gal (HTB p. 469, "Estimated color = [(8 × 2) + (2 × 4)] / 5"; p. 472).
  Malt colour in °L is used as SRM-equivalent (HTB p. 468: they share a standard, "nearly
  identical"), so the function takes **EBC** and converts: °L ≈ EBC / 1.97.
- SRM = 1.49 × MCU^0.69 (Morey, as printed in HTB table B.3, p. 470). Constants are Palmer's
  as printed. Morey's article (1.4922, 0.6859) is not in the repo and is unverified; on every
  example below it agrees within ± 1 SRM.
- EBC = 1.97 × SRM (HTB p. 469, "the actual conversion factor is 1.97").

**What it became.** `app.mcu(kg, ebc, volume_l)` = (EBC / 1.97) × (kg / 0.45359237) /
(L / 3.785411784), `app.grist_mcu`, `app.srm`, `app.srm_from_ebc`, `app.ebc_from_srm`.

| Source | Inputs | Expected | Measured | Test |
|---|---|---|---|---|
| HTB p. 469 | 8 lb at 2 °L + 2 lb at 4 °L, 5 gal | 4.8 MCU (book calls it "4.8 SRM") | 4.8 | `test_mcu_palmer_simple` (MCU ± 0.01) |
| HTB p. 472 Shay Steam | 6 lb LME 5 °L, 0.75 lb crystal 40, 0.25 lb maltodextrin 0 °L (MCU 6 + 6 + 0), total 12 | Morey 8 SRM | 8.28 | `test_srm_shay_steam` (± 1) |
| HTB p. 473 Port O' Palmer | 6 lb LME 5 °L, 0.5 lb crystal 60, 0.5 lb chocolate 350, 0.25 lb black 500; 72 MCU | Morey 28 SRM | 28.49 | `test_srm_port_o_palmer` (± 1) |
| HTB p. 473, option 2 | chocolate 1 lb: 107 MCU | Morey 37 SRM | 37.45 | `test_srm_port_o_palmer_more_chocolate` (± 1) |
| OBC Pils, p. 5 | 8 lb Belgian pils 2 °L + 1 lb Vienna 4 °L, 5 gal | 4 MCU, "around 4 SRM" | 4.0 MCU, Morey 3.88 SRM | `test_mcu_obc_pils` (MCU ± 0.01, SRM within 1 of 4) |
| OBC Dubbel, p. 5 | rows below, 5 gal | **40.5 MCU** (book prints 43; see below) | 40.5 | `test_mcu_obc_dubbel` (MCU ± 0.01) |

HTB's tables do not print the Morey SRM as a decimal: the examples are rounded to a whole SRM,
which is the reason for the ± 1 tolerance (looser than the book would justify only by the
rounding).

## 8. Cases that are not a plain reproduction

1. **OBC Dubbel MCU sum error** (OBC p. 5). Rows: pale 4.75 lb × 3 = 14.25, pils 4.75 × 2 = 9.5,
   Munich 1.25 × 8 = 10, Caramunich 0.75 × 75 = 56.25, Special B 0.75 × 120 = 90, candi
   0.75 × 30 = **22.5**. The book prints 35.25 in the candi row, which is that row's *extract*
   total from the gravity table (0.75 × 47), copied into the colour table by mistake. The book's
   total, 215.25 / 5 = 43 MCU, is therefore wrong. The rows give 202.5 / 5 = **40.5 MCU**, and
   that is what `test_mcu_obc_dubbel` asserts.
2. **OBC SRM is Daniels' range table, not Morey** (OBC p. 5). OBC reads SRM from a Daniels MCU →
   SRM ranges table ("17 or 18" for the Dubbel at 43 MCU, "around 4" for the Pils). Morey gives
   19.2 (at 40.5 MCU; 20.0 at the book's 43) for the Dubbel and 3.9 for the Pils. **Written up as
   Daniels' model, not tested** (brief A2, user's answer 2026-10-14). The Pils is covered by the
   "within 1 of 4" check above because Morey and OBC agree there.
3. **OBC IBU is Daniels' stepped table, not Tinseth** (OBC p. 3–4). IBU = oz × α% × U% /
   (gal × 1.34), with U% from a 6-row boil time table (0–9 min 5 %, 10–29 12 %, 30–44 19 %,
   45–59 22 %, 60–74 24 %, 75–90 27 %). OBC gives no boil gravity or boil volume. Recomputed
   with Daniels' own formula: Dubbel 16.12 + 9.31 = 25.4 (book "25"), Pils 168 + 99.8 + 17.5 =
   285.3 / 6.7 = 42.6 (book 42.5). Tinseth on the same inputs, at OG: Dubbel 21.2 (60 min
   Goldings 12.5 + 20 min Mt Hood 8.7), Pils 40.4. **Written up as Daniels' model, not tested**
   (brief A2).
4. **Mt Hood 20 / 30 min conflict** (OBC p. 3–4). The Dubbel plan says "a second at 20 minutes",
   and the arithmetic then says "Mt Hoods for 30 minutes" with 12 % utilisation. 12 % is the
   10–29 min step in the same table (30 min would be 19 %), so 20 min is the time the numbers
   use and "30 minutes" is a slip in the prose. Matters only for the untested IBU; the Tinseth
   figure above uses 20.
5. **Table 4.3's ABV row** (HTB p. 55): see section 5. Its FG row is tested.
6. **Table A.2 against the 259 formula** (HTB p. 465): see section 3. Not tested.
7. **Port O' Palmer option 1** (HTB p. 473): "add 1.5 lb of dark DME ... about 12 points to both
   the OG and the MCU total ... 30, 25, 32 SRM". "About 12" is an approximate input (the
   book does not give the DME colour), so it is **not tested**. Morey at 72 + 12 = 84 MCU gives
   31.7, vs the printed 32.
8. **Option 3** of the same page ("MCU total almost the same") gives no number and is not tested.
9. **Palmer's rounded tables.** Table 5.5 is hand-interpolated in the Joe Ale text (see section 6),
   tables 18.4 and 18.5 round PPG to whole numbers (section 1), and MCU → SRM examples round to
   whole SRM (section 7). These are the cases where the tolerance is wider than the arithmetic.

## 9. calc_version

`app.calc_version()` returns `'maths-1'` (stored in `app.recipe.calc_version`).

**Bump rule.** Any change to a formula or a constant in `db/030_maths.sql` bumps the version in
the same commit (`maths-2`, ...), with a line in the log below saying what changed and why. A
change to comments, tests or this file does not bump it.

| Version | Date | Change |
|---|---|---|
| `maths-1` | 2026-10-14 | First version: Palmer gravity (46 PPG = 384 PKL, no moisture term), SG ↔ °P = 259 formula, FG by attenuation and fermentability, ABV by the Balling form (1.259 × ABW), Tinseth IBU on pre-boil gravity and final volume (whirlpool and dry hop = 0), Morey colour 1.49 × MCU^0.69, EBC = 1.97 × SRM. |

## 10. Coverage of the plan's "Critical behaviour" table

Every example in the plan's table appears above with its expected value: OG (section 1), boil gravity
and pre-boil volume (2), °P round trip (3), FG (4), ABV (5), Tinseth and Joe Ale (6), whirlpool
and dry hop at 0 (6), MCU and Morey colour (7). The solver round trips and the n8n check have no
book value; they are tests of the forward functions (plan tasks 6 and 7).
