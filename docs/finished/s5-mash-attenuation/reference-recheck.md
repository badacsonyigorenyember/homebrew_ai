# S5 · Reference recipes re-checked

Measured 2026-10-17 with a scratch script over the 22 recipes of `tests/fixtures/reference_recipes.toml`,
before and after the new `app.mash_attenuation` (Troester's curve) was applied.

| Brief | Style | Mash °C | Yeast range | Before att % | Before FG | Before rule 10 | After att % | After FG | After rule 10 |
|---|---|---|---|---|---|---|---|---|---|
| b01 | 21A | 65 | [78,82] | 81.20 | 1.0116 | pass | 80.00 | 1.0123 | pass |
| b02 | 21C | 65 | [78,83] | 82.00 | 1.0131 | pass | 80.50 | 1.0141 | pass |
| b03 | 16B | 67 | [74,82] | 77.20 | 1.0125 | pass | 78.00 | 1.0121 | pass |
| b04 | 16A | 67 | [74,82] | 77.20 | 1.0185 | pass | 78.00 | 1.0182 | pass |
| b05 | 15B | 66 | [74,82] | 78.80 | 1.0086 | pass | 78.00 | 1.0089 | pass |
| b06 | 1B | 64 | [80,84] | 84.00 | 1.0072 | pass | 82.00 | 1.0081 | pass |
| b07 | 1C | 65 | [78,82] | 81.20 | 1.0091 | pass | 80.00 | 1.0097 | pass |
| b08 | 5D | 67 | [80,84] | 81.60 | 1.0086 | pass | 82.00 | 1.0085 | pass |
| b09 | 6A | 67 | [80,84] | 81.60 | 1.0105 | pass | 82.00 | 1.0103 | pass |
| b10 | 26B | 67 | [77,83] | 79.40 | 1.0125 | pass | 80.00 | 1.0121 | pass |
| b11 | 25B | 68 | [86,94] | 87.60 | 1.0070 | pass | 90.00 | 1.0056 | pass |
| b12 | 18A | 68 | [78,82] | 78.80 | 1.0081 | pass | 80.00 | 1.0077 | fail |
| b13 | 10A | 66 | [74,79] | 77.00 | 1.0112 | pass | 76.50 | 1.0114 | pass |
| b14 | 23A | 68 | [86,90] | 86.80 | 1.0036 | pass | 88.00 | 1.0033 | pass |
| b15 | 11B | 66 | [74,82] | 78.80 | 1.0093 | pass | 78.00 | 1.0097 | pass |
| b16 | 18B | 67 | [78,82] | 79.60 | 1.0107 | pass | 80.00 | 1.0105 | pass |
| b17 | 8B | 68 | [80,84] | 80.80 | 1.0130 | pass | 82.00 | 1.0122 | pass |
| b18 | 15A | 67 | [71,75] | 72.60 | 1.0112 | pass | 73.00 | 1.0111 | pass |
| b19 | 17C | 68 | [65,72] | 66.40 | 1.0289 | pass | 68.50 | 1.0271 | pass |
| b20 | 19C | 66 | [78,82] | 80.40 | 1.0139 | pass | 80.00 | 1.0141 | pass |
| b21 | session-india-pale-ale | 66 | [78,82] | 80.40 | 1.0075 | pass | 80.00 | 1.0077 | pass |
| b22 | mexican-style-amber-lager | 68 | [78,84] | 79.20 | 1.0101 | pass | 81.00 | 1.0092 | fail |

Changed: b12 (FG 1.0081 to 1.0077, target range 1.0080 to 1.0130) and b22 (FG 1.0101 to 1.0092,
target range 1.0100 to 1.0120) go from pass to fail. All other statuses are unchanged.

Decision (user, 2026-10-17): b12 and b22 mashed at 69 °C instead of 68 °C (fixture `mash_c` changed). Re-measured:

| Brief | Mash °C | Attenuation % | FG | Target FG range | Rule 10 |
|---|---|---|---|---|---|
| b12 | 69 | 78.00 | 1.0084 | 1.0080 to 1.0130 | pass |
| b22 | 69 | 78.09 | 1.0106 | 1.0100 to 1.0120 | pass |

All 22 recipes pass rule 10.
