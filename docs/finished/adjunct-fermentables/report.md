# Adjunct fermentables — gap report

Measured 2026-10-11 against the running database, after Task 4 loaded the adjuncts.
Covers R6 / A6 (part 1) and A3 (part 2) of the [brief](brief.md).

## Part 1: test-brief ingredients

One row per distinct ingredient named in `evals/recipe_briefs.toml` (`needs.*`, `wanted`,
`excluded`, `inventory`): 47 names. **38 found, 7 added, 2 left out.**

- *found*: `ref` already held it before this work. Ids were read from `ref.ingredient`
  (`name ilike`). For a generic name (a malt type, a yeast type) the ids are the matching
  products, not an exhaustive or tagged set: `ref` has no ingredient tags yet (P3).
- Generic yeast names were matched on hopline's "Ajánlott sörtípusok" (recommended beer types)
  line, stored in each yeast's `raw`.
- *added*: loaded by this work (Task 4), ids 3392–3398.

| Name | Kind | Briefs | Status | `ref` id(s) | Reason or note |
|---|---|---|---|---|---|
| pilsner malt | fermentable | b02, b06, b07, b08, b09, b10, b11, b13, b14, b17 | found | 37, 64, 75, 59, 60 | Viking and Weyermann Pilsner Malt; Weyermann Bohemian, Eraclea and Extra Pale Premium Pilsner |
| pale ale malt | fermentable | b01, b04, b05, b12, b16, b18, b20 | found | 36, 63, 12, 13 | Viking and Weyermann Pale Ale Malt; Simpsons Finest Pale Ale Golden Promise and Maris Otter |
| Maris Otter | fermentable | b03, b15, b19 | found | 13 | Simpsons Finest Pale Ale Maris Otter |
| Munich malt | fermentable | b09, b10, b17 | found | 34, 35, 62, 81 | Viking Munich Light/Dark, Weyermann Munich Type 1/2 |
| Vienna malt | fermentable | b09, b12 | found | 14, 43 | Viking and Weyermann |
| wheat malt | fermentable | b02, b11, b13, b14 | found | 16, 74, 76 | Viking Wheat Malt, Weyermann Wheat Malt Pale/Dark |
| crystal malt | fermentable | b01, b03, b04, b15, b16, b18, b19, b20 | found | 18–25, 71, 9, 10, 55–57, 45, 46, 47, 48, 77, 79 | Viking Caramel series, Simpsons Crystal T50 and Extra Dark, Weyermann Caramunich 1–3 and the Cara crystal malts. Not Carafa (roasted) or Carapils/CaraBody (dextrin) |
| chocolate malt | fermentable | b03, b04, b20 | found | 26, 27 | Viking Chocolate Light/Dark Malt |
| roasted barley | fermentable | b03, b04, b05, b18, b19 | found | 38, 65 | Viking and Weyermann |
| Carafa Special | fermentable | b17 | found | 52, 53, 54 | Weyermann Carafa Special Type 1/2/3 |
| Special B | fermentable | b10 | left out | — | Hopline sells no Special B (R7), so there is no source in this work's scope. Nearest in `ref`: Weyermann Special W (68) |
| flaked oats | fermentable | b02, b03 | added | 3393 | Flaked Oats: hopline `400150`, extract from Palmer Table 18.5 |
| flaked corn | fermentable | b07 | added | 3392 | Flaked Corn: hopline `400270`, extract from Palmer Table 18.5 |
| flaked rice | fermentable | b06, b16 | added | 3395 | Flaked Rice: hopline `400100` (max 40 %), extract from Palmer Table 18.5 |
| flaked barley | fermentable | b05 | added | 3394 | Flaked Barley: hopline `400110`, extract from Palmer Table 18.5 |
| candi sugar | fermentable | b10 | added | 3396 | Brown Candi Sugar: hopline `400091-cs` (225 EBC), extract and `full` from Palmer's Table sugar row |
| lactose | fermentable | b04, b20 | added | 3397 | Lactose: hopline `400030-cs` (`none`), extract from Palmer Table 24.1 |
| honey | fermentable | b12, b19 | added | 3398 | Honey: Palmer Table 24.1 only (hopline sells none) |
| Cascade | hop | b12, b16, b20 | found | 464 | |
| Centennial | hop | b01, b16 | found | 466 | |
| Citra | hop | b02, b16 | found | 470, 471 | 471 is Citra LUPOMAX. Excluded in b16 |
| Columbus | hop | b01 | found | 472 | |
| East Kent Goldings | hop | b03, b04, b05, b15, b18, b19 | found | 474 | Name variant: stored as "East Kent Golding" |
| Fuggle | hop | b15 | found | 477 | |
| Galaxy | hop | b02 | found | 478 | |
| Hallertau Mittelfrüh | hop | b08, b09, b13, b14, b17 | found | 522 | |
| Magnum | hop | b06, b08 | found | 486 | |
| Mosaic | hop | b02, b16 | found | 488, 489 | 489 is Mosaic LUPOMAX. Excluded in b16 |
| Saaz | hop | b08, b11 | found | 497 | Excluded in b08 |
| Simcoe | hop | b01 | found | 499 | |
| Styrian Golding | hop | b10, b11 | found | 503 | |
| Tettnang | hop | b08 | found | 506 | Name variant: stored as "Tettnanger" |
| Willamette | hop | b07 | found | 512 | |
| American ale yeast | yeast | b01, b07, b12, b16, b20 | found | 1830, 1822, 1871, 1847 | SafAle US-05, U.S. West Coast Ale, M44 US West Coast, BRY-97 |
| American lager yeast | yeast | b06 | found | 1849, 1855 | Lallemand Diamond and NovaLager: hopline lists American Pilsner and Dark American Lager |
| English ale yeast | yeast | b03, b04, b15 | found | 1827, 1821, 1861, 1894, 1902 | SafAle S-04, British Ale, Windsor, YF-101 Queen of Hearts, YF-109 Caskaway |
| Irish ale yeast | yeast | b05, b18 | found | 1899, 1861 | YF-106 Redshamrock (Irish Ale), Windsor (Irish Red) |
| Scottish ale yeast | yeast | b19 | found | 1898, 1863 | YF-105 Haggis (Scottish Ale), M15 Empire Ale (Scottish heavy ales) |
| abbey ale yeast | yeast | b10 | found | 1845, 1817, 1872, 1841, 1825 | Abbaye, Abbey Monk Ale, M47 Belgian Abbey, "Rochefort" Trappist Ale, SafAle BE-256. In b10's inventory too |
| German ale yeast | yeast | b14 | found | 1901, 1816, 1903, 1826 | YF-108 Jawohl! (German Ale), Köln, YF-110 Kölschermeister, SafAle K-97 |
| German lager yeast | yeast | b08, b09, b17 | found | 1835, 1834, 1833, 1813, 1849 | SafLager W-34/70, S-23, S-189, German Lager, Diamond |
| New England ale yeast | yeast | b02 | found | 1853, 1842, 1874, 1859 | Lallemand New England, Conan "New England", M66 Hophead Ale, Verdant IPA |
| saison yeast | yeast | b11 | found | 1846, 1824, 1866, 1850 | Belle Saison, SafAle BE-134, M29 French Saison, Farmhouse |
| weizen yeast | yeast | b13 | found | 1832, 1831, 1864, 1852, 1923 | SafAle WB-06, W-68, M20 Bavarian Wheat, Munich Classic, YF-402 Herr Weizen |
| Lactobacillus | yeast | b14 | left out | — | A bacterium, so it would go in `ref.yeast`. Hopline sells cultures (LP-582, LP-652, Helveticus Pitch), but adding them means extending the yeast loader, which is separate work (user decision, 2026-10-11) |
| gypsum | water salt | b01, b02, b15, b16 | found | 3360 | |
| calcium chloride | water salt | b02, b03, b04 | found | 3361 | |

## Part 2: NULLs in the new rows (A3)

Measured values of the 7 new `ref.fermentable` rows. Every filled field has a `field_source`
entry (Task 4, A2). Every `NULL` below is a value no source in this work states.

| Id | Name | Extract % | EBC | Max % | Fermentability | Each `NULL` and why |
|---|---|---|---|---|---|---|
| 3393 | Flaked Oats | 70.0 (Palmer) | NULL | NULL | normal | Colour: neither hopline's page nor Table 18.5 prints one. Max %: no source states one |
| 3392 | Flaked Corn | 84.0 (Palmer) | NULL | NULL | normal | Colour: neither hopline's page nor Table 18.5 prints one. Max %: no source states one |
| 3395 | Flaked Rice | 82.0 (Palmer) | NULL | 40.0 (hopline) | normal | Colour: neither hopline's page nor Table 18.5 prints one |
| 3394 | Flaked Barley | 70.0 (Palmer) | NULL | NULL | normal | Colour: neither hopline's page nor Table 18.5 prints one. Max %: no source states one |
| 3396 | Brown Candi Sugar | 100.0 (Palmer) | 225 (hopline) | NULL | full (Palmer) | Max %: no source states one |
| 3397 | Lactose | 100.0 (Palmer) | NULL | NULL | none (hopline) | Colour: Table 24.1 has no colour column, and the lactose page prints none. Max %: no source states one |
| 3398 | Honey | 82.6 (Palmer) | NULL | NULL | full (Palmer) | Colour: Table 24.1 has no colour column, and hopline sells no honey. Max %: no source states one; Palmer's NHB percentages (p. 437) are flavour bands, not a grist maximum |

`normal` fermentability needs no source: it means "follows the yeast's attenuation", as for
every malt (plan, Approach).
