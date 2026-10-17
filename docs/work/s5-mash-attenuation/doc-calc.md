# S5 · Doc → calc pass

Approved by the user 2026-10-17

Work: [brief.md](brief.md) · [plan.md](plan.md) · written 2026-10-17 (PROJECT.md §6.7, brief A1)

Status: approved by the user 2026-10-17 (was: waiting for approval of the transcribed rows (§2) and the derived numbers
(§3, §4)).

This is the doc → calculation pass for the new `app.mash_attenuation`. Every number was
recomputed with a scratch script (not kept in the repo), so it is measured, not copied from the
plan.

## 1. Sources

| Source | File | Licence | Cited by |
|---|---|---|---|
| Troester, *Effects of mash parameters on attenuation and efficiency* (2009), braukaiser.com | `shared/rag-files/articles/braukaiser_mash_parameters_2009.pdf` | CC BY-NC 3.0 | PDF page (the PDF's own pages, 23 in all) |
| Troester, *Mash Time Dependency of Wort Fermentability* (wiki) | `shared/rag-files/articles/braukaiser_mash_time_fermentability.md` | braukaiser.com | section name |
| Terrill, *Observations on Attenuations* (2017-04-21), seanterrill.com | `shared/rag-files/articles/terrill_observations_on_attenuations.md` | seanterrill.com | paragraph per strain |
| White & Zainasheff, *Yeast* | `shared/rag-files/books/white_zainasheff_yeast.pdf` | book | PDF page |

## 2. Troester's temperature series (read from an image, typed table)

Source: Troester 2009, appendix "Temperature series", **PDF p. 22**. The table is an image; the
rows below were typed from it (read at 300 dpi on 2026-10-17). These are the points behind
Figure 10 (PDF p. 11). Rows checked against the
image and approved by the user on 2026-10-17.
The attenuation column is assumed to be apparent attenuation, the same measure as
`ref.yeast.attenuation_pct`. **Unverified:** (OE − AE) / OE does not give this column for 10 of 11
rows, and the paper does not say which readings OE and AE are. Sample
numbers are Troester's; there is no sample 1, 3, 4 or 5 in this table.

| Sample | Start °C | End °C | Average °C | OE °P | AE °P | Attenuation % | Efficiency % |
|---|---|---|---|---|---|---|---|
| 2 | 70.5 | 68.6 | 70.5 | 13.1 | 2.6 | 80.2 | |
| 6 | 76.8 | 73.2 | 74.9 | 13.5 | 5.0 | 61.6 | |
| 7 | 71.0 | 68.0 | 69.3 | 14.0 | 2.1 | 83.2 | |
| 8 | 67.2 | 64.5 | 65.9 | 11.8 | 1.3 | 86.8 | |
| 9 | 67.8 | 64.4 | 65.9 | 11.2 | 0.9 | 89.6 | |
| 10 | 66.8 | 60.8 | 63.3 | 11.7 | 1.1 | 87.1 | |
| 11 | 63.4 | 60.8 | 61.9 | 10.2 | 1.2 | 83.8 | |
| 12 | 61.5 | 58.0 | 59.9 | 13.0 | 2.4 | 79.2 | 53.6 |
| 13 | 76.7 | 73.2 | 74.7 | 15.4 | 5.0 | 60.5 | 63.9 |
| 14 | 80.9 | 76.8 | 78.6 | 16.7 | 8.9 | 44.4 | 69.7 |
| 15 | 73.2 | 69.1 | 71.0 | 16.5 | 3.8 | 74.4 | 68.5 |

Text cross-check (PDF p. 11): "sample number 10, which achieved 87%" matches row 10 (87.1).

**Spot check against (OE − AE) / OE × 100 failed, so it is not used.** The plan expected each
row within 0.5; measured (computed minus table, points):

| Sample | 2 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| (OE − AE) / OE × 100 | 80.2 | 63.0 | 85.0 | 89.0 | 92.0 | 90.6 | 88.2 | 81.5 | 67.5 | 46.7 | 77.0 |
| Table attenuation | 80.2 | 61.6 | 83.2 | 86.8 | 89.6 | 87.1 | 83.8 | 79.2 | 60.5 | 44.4 | 74.4 |

Only sample 2 matches (the plan's example). The others are 1.4 to 7.0 points higher when computed
from OE and AE. The table's attenuation column is the **limit of attenuation** of a fast-ferment
test (the quantity Figure 10 plots); OE and AE are the measured plato values and evidently not
the pair that gave that percentage (the paper does not say which gravity readings are in
the OE and AE columns). The model uses the attenuation column only. OE and AE are kept in the table
for completeness and are not used by any number below. Recorded in the plan's Deviations.

## 3. Derivation

Rows are split by their average temperature (Troester: attenuation peaks, then "almost perfectly
linear" past the peak, PDF p. 11).

| Group | Samples | Average °C | Use |
|---|---|---|---|
| Plateau (the measured peak) | 10, 8, 9 | 63.3, 65.9, 65.9 | mean attenuation |
| Falling line | 7, 2, 15, 13, 6, 14 | 69.3 to 78.6 | least-squares line |
| Left out | 12, 11 | 59.9, 61.9 | below the 64 °C mash limit, on the rising side |

Measured:

| Quantity | Value |
|---|---|
| Least-squares line over the 6 falling rows | attenuation = 371.28 − 4.153 × T |
| Plateau (mean of 87.1, 86.8, 89.6) | 87.83 |
| Knee (line meets plateau): (371.28 − 87.83) / 4.153 | 68.24 °C |
| **Stored, rounded** | **knee 68.3 °C** (to 0.1), **slope 4.15 points per °C** (to 0.01) |

The stored knee is 0.06 °C above the derived 68.24 (the plan, and the user's decision, round the
knee to 68.3). Within the 0.1 tolerance in §4.

Cross-check against PDF p. 11: the text gives a slope of "~ 4 %/C" over a 12 °C range (measured
here: 4.15, over 69.3 to 78.6 = 9.3 °C of rows); the fitted line's start near 68 °C agrees with
the knee at 68.2.

## 4. Tolerance (R3)

Curve: `L(T) = 87.83 − 4.15 × max(0, T − 68.3)`, with the unrounded plateau 87.83.

| Sample | Average °C | Table % | Curve % | Table − curve |
|---|---|---|---|---|
| 10 | 63.3 | 87.1 | 87.83 | −0.73 |
| 8 | 65.9 | 86.8 | 87.83 | −1.03 |
| 9 | 65.9 | 89.6 | 87.83 | +1.77 |
| 7 | 69.3 | 83.2 | 83.44 | −0.24 |
| 2 | 70.5 | 80.2 | 78.46 | +1.74 |
| 15 | 71.0 | 74.4 | 76.38 | −1.98 |
| 13 | 74.7 | 60.5 | 61.01 | −0.51 |
| 6 | 74.9 | 61.6 | 60.18 | +1.42 |
| 14 | 78.6 | 44.4 | 44.82 | −0.42 |

(Residuals use the unrounded fit; with the stored 68.3 / 4.15 they move by under 0.2.)
The largest is sample 15 at 1.98 (the plan expected about 2.2).

Tolerances the tests use:
- every one of the nine rows within **2.5 points** of the curve;
- stored slope within **0.01** of the fitted slope magnitude;
- stored knee within **0.1 °C** of the derived knee.

Not claimed: samples 12 and 11 are 8.6 and 4.0 points under the flat part, which is why they are
excluded; the model does not describe mashes below 64 °C.

## 5. Reference temperature

*Yeast* gives no mash temperature for a strain's attenuation range; it says only that the range
is for the average wort (PDF p. 130; brief question 2, full-text search of the book on
2026-10-17). So the reference is **66.5 °C**, the middle of the 64 to 69 °C mash limits (brief
question 2, answer b). The middle of the yeast's range is taken as its attenuation at 66.5 °C.
This is an assumption, not a measurement.

## 6. The model

```
middle = (top + bottom) / 2                         -- of the yeast's attenuation_pct
mash   = clamp(mash_c, 64, 69)                      -- as today
result = middle - slope * (max(mash, knee) - max(ref, knee))
result = clamp(result, bottom, top)
ref = 66.5, knee = 68.3, slope = 4.15
```

Equivalent to `middle + L(mash) − L(66.5)` with Troester's curve L. Because 66.5 is below the knee
the last term is zero, so the sentence (R4) is: *up to 68.3 °C the attenuation is the middle of
the yeast's range; above 68.3 °C it is 4.15 points lower per °C, never outside the yeast's
range.*

Worked values (scratch computation):

| Range | Mash °C | Unclamped | Result |
|---|---|---|---|
| [78, 82] | 63 (clamped to 64) | 80 | 80 |
| [78, 82] | 64 | 80 | 80 |
| [78, 82] | 66.5 | 80 | 80 |
| [78, 82] | 68.3 | 80 | 80 |
| [78, 82] | 69 | 77.095 | 78 (range bottom) |
| [78, 82] | 70 (clamped to 69) | 77.095 | 78 |
| [70, 90] | 69 | 77.095 | 77.095 |

## 7. Assumptions and known limits

- A recipe's single mash temperature is read as Troester's *average* mash temperature. His
  mashes dropped about 4 °C over 60 min (PDF p. 11), so a held temperature may behave a little
  differently (he suspects this explains why single-infusion literature data, e.g. Briggs, is not
  linear past the peak, PDF p. 11 to 12).
- One all-Pilsner grist, wort pH 5.5, 60 min rest. The mash-time wiki shows fermentability still
  rising after a negative iodine test: apparent attenuation 77.9 % at 40 min to 82.0 % at 2 h 40
  at a mash of 66.6 °C, so the model holds for a rest of about 60 min.
- Rows below 64 °C (rising side) are not modelled.
- The table's attenuation is a fast-ferment limit with one yeast; real yeasts leave more
  (see §8).
- Under this model every mash from 64 to 68.3 °C predicts the same FG (the middle of the yeast's
  range); only 68.3 to 69 °C lowers it. A `dry` mash hint of 64 to 65 °C (RECIPE-ROADMAP, hint
  table) therefore does not change the predicted FG; M4 must not expect it to.
- Sample 13 differs most from what OE and AE give (§2); only the attenuation column is used.

## 8. Terrill (R7)

As far as the text says (44 batches, 17 grain bills, 10 to 19 °P; the data is in plots that are
images and were not saved, so **no numbers are taken from them**):

| Strain | What the text says |
|---|---|
| Wyeast 3522 | attenuation falls nearly linearly with temperature (R² 0.95, 8 points) |
| Wyeast 2206 | no strong correlation; the curve is within ±1.7 % ADF (10 points, 4.0 °C range) |
| Wyeast 1272 | more or less flat from 64 to 70 °C, drops sharply above |

- Lab ranges are comparative, not prescriptive: Wyeast's 72 to 77 % for these three strains was
  exceeded by almost all batches.
- From 66.5 to 70.0 °C the three strains' mean attenuations only range from 79 to 86 % ADF.

Known limit: the model uses one curve (Troester's, lager-type wort) for every strain. Strains
that are flat (2206, 1272 up to 70 °C) get a drop above 68.3 °C that they may not show; strains
like 3522 fall earlier and further. Per-strain behaviour is not modelled (no data).

## 9. Version log

`calc_version` is not changed: it covers `db/030_maths.sql` only, and this work does not touch
that file.
