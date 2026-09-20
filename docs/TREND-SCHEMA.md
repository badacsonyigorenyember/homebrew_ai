# Trend schema — style-level brewing practice, and the traps in storing it

Written 2026-09-20, against the stack as it ran that day. Every number in §1 was
measured on this machine against the brewersfriend corpus, not estimated. The
measurements come first so the design can be argued with.

Goal, in the user's words: *"a table which would be used, and calculated by
bigger patches. That table could store the BJCP style ref, and all the specs we
gathered. Most common fermentables, percent they are used, common hop types, hop
pairings, etc."*

And the constraint that shapes the whole design, also theirs: *"we could see the
majority recipes are using 2-3 types of hops at max in 1 recipe, but all the
recipes are using 20ish. We don't want to run into this that the AI recipe
creation would suggest to use 20 type of hops in 1 recipe."*

---

## 0. TL;DR

A trend table that stores *"ingredient -> how often, how much"* **cannot
reconstruct a legal recipe**, no matter how accurate each row is. Marginal
frequency is not joint composition. This is measurable in two places, not one:

- **Hops.** American IPA has 713 distinct hop varieties. The top 12 presence
  rates sum to **230%**. The median recipe uses **3**.
- **Grist.** The 9 most common malt types' median grist percentages sum to
  **190%**. A grist must sum to 100%. The median recipe uses **4** fermentables.

The fix is to split trends into four kinds of fact that are never mixed —
**shape** (how many), **composition** (role shares that sum to 100), **choice +
amount** (conditional on presence), and **affinity** (lift, not co-occurrence) —
and to force the generator to read *shape first*, as a budget, before it ever
opens a popularity list.

Everything else here — the `ref.malts` -> `ref.fermentables` rename, the malt-type
taxonomy, the filtered corpus load — exists to make those four tables buildable
from data that is honest about where it came from.

---

## 1. What I measured

All figures from `recipes_full.txt` (brewersfriend, 179,455 recipes, CC0,
scraped pre-July-2020), filtered to `views > 500` unless stated.

### 1.1 The cardinality trap, both halves

`measured` 2026-09-19, American IPA, n=5,513 at `views>500`:

```
distinct HOPS per recipe : p25=2  median=3  p75=4  p95=6  max=12
FERMENTABLES per recipe  : p25=3  median=4  p75=5  p95=6  max=11
distinct hop varieties across the style: 713

top hops by presence rate:
  Citra 35%, Cascade 32%, Centennial 27%, Amarillo 25%, Simcoe 24%,
  Columbus 19%, Chinook 18%, Mosaic 17%, Magnum 11%, Galaxy 8%, ...
  >>> sum of top-12 presence rates = 230%
```

The same trap on the grist side, same style:

```
malt type          present   median % of grist
base_pale              76%              81.5%
crystal_medium         35%               5.3%
wheat                  28%               8.0%
crystal_light          27%               5.9%
dextrine               23%               4.3%
sugar                  22%               6.0%
munich                 22%               8.3%
oats                   14%               9.1%
base_pilsner           14%              61.3%
  >>> naive sum of those 9 medians = 190% of grist
```

Neither number is wrong. Each row is a correct conditional median. They simply
cannot be added, and a schema that presents them in one flat list invites exactly
that addition.

Cardinality varies by style and must therefore be stored per style, not assumed:

| style | median hops | median fermentables | varieties in style |
|---|---|---|---|
| American IPA | 3 | 4 | 713 |
| American Pale Ale | 2 | 3 | 496 |
| Saison | 2 | 4 | 290 |
| Irish Stout | 1 | 4 | 32 |

### 1.2 Lift separates real pairings from "both are popular"

`measured` 2026-09-19, American IPA, pairs with support >= 40:

| pair | support | lift | |
|---|---|---|---|
| Cascade + Willamette | 111 | 2.06x | real affinity |
| Amarillo + Simcoe | 587 | 1.72x | real affinity |
| Centennial + Mosaic | 137 | 0.53x | avoided |
| **Cascade + Mosaic** | **147** | **0.49x** | **avoided** |

Cascade+Mosaic co-occurs *more often* than Ahtanum+Chinook (147 vs 62), yet
brewers avoid combining them. Raw co-occurrence says "common pair"; lift says
"don't". That negative signal is unobtainable from counts alone and is what stops
the generator assembling a plausible-looking but incoherent hop bill.

`lift = P(A and B) / (P(A) * P(B))`. Stored only where `support >= 30`.

### 1.3 The view filter, and what it costs

| views > | recipes | styles reaching n>=50 |
|---|---|---|
| 0 | 179,288 | 162 |
| 250 | 71,074 | 138 |
| **500** | **36,271** | **114** |
| 1000 | 11,253 | 55 |
| 2000 | 3,872 | 16 |

`>1000` was the original request. It drops 107 of 162 trendable styles — Black
IPA (42), Red IPA (41), Best Bitter (32), Märzen (24), International Pale Lager
(45) all fall under the bar. **`>500` chosen**: still a 5x quality cut, keeps
roughly twice the styles.

### 1.4 Sample size — where the n>=30 gate comes from

`measured` 2026-09-19, bootstrap, 400 resamples per cell. Irish Stout /
roasted barley (truth: present in 70.1%, median 9.7% of grist):

| sample n | median grist | presence rate |
|---|---|---|
| 10 | ±2.9pp | ±25pp |
| 30 | ±1.5pp | ±15pp |
| 50 | ±1.0pp | ±12pp |
| 200 | ±0.5pp | ±5.2pp |

Two conclusions that the schema encodes:

1. **Amounts converge far faster than prevalence.** ~50 recipes gives a usable
   grist percentage; a claim about *how common* something is needs ~200.
2. **The gate is hits, not style size.** Munich appears in 23% of American IPAs,
   so a style sample of 50 yields ~11 usable rows and ±51% relative error —
   five times worse than roasted barley at the same style-n. Every trend row
   therefore stores `n_with`, and nothing reports a number below 30.

Past ~500 the interval keeps shrinking but accuracy does not: the residual error
is systematic (self-reported, one community, pre-2020). Precision beyond that is
precision that cannot honestly be quoted.

### 1.5 ⛔ Corpus ppg and colour figures are site defaults, not measurements

`measured` 2026-09-20. The corpus *is* brewersfriend, so a per-ingredient spec
repeated across thousands of recipe rows is one row of that site's ingredient
database copied forward — not thousands of brewers agreeing.

| ingredient | top ppg | share of rows | n rows | |
|---|---|---|---|---|
| flaked oats | 33.0 | **99.3%** | 24,087 | site default |
| lactose | 41.0 | **98.9%** | 4,761 | site default |
| acidulated | 27.0 | **97.5%** | 9,792 | site default |
| corn sugar | 46.0 | 72.5% | 7,867 | genuine spread (two defaults over time) |

⚠ **Effective n for these figures is 1.** Any argument of the form "the corpus
says X across 9,792 rows" is invalid and this document must not make it. The
corpus is good evidence about *what brewers chose* — which ingredients, in what
proportion — and near-worthless as evidence about *ingredient specifications*,
because the brewer never typed those.

This is why `spec_source` distinguishes `corpus_default` from a real publisher,
and why corroboration by the corpus counts as one vote, not thousands.

### 1.6 Ingredient resolution against the existing refs

`measured` 2026-09-19 at `views>1000`:

**Hops -> `ref.hops` (268 rows): 92.5% of recipe-rows resolve.**

| | strings | rows |
|---|---|---|
| exact | 265 | 64.0% |
| via `alternatives[]` | 50 | 20.4% |
| fuzzy (0.87 cutoff) | 90 | 8.1% |
| unresolved | | 7.5% |

The `alternatives` column carries a fifth of the resolution unaided. The
unresolved tail is ~15 strings, hand-fixable: *Kent Goldings* -> East Kent
Golding, *Columbus (Tomahawk)* -> CTZ, *Ekuanot* (renamed from Equinox),
*Hallertau Hersbrucker*, *Domestic Hallertau*.

**Fermentables -> `ref.malts` (77 rows): 21.5%.** Structural, not algorithmic:

```
ref.malts = Weyermann (44) + Viking Malt (33)
```

Two European maltsters against an American homebrew corpus. Top unresolved:
*American - Pale 2-Row* (3,313), *Maris Otter* (1,609), *Flaked Oats* (1,212),
*Carapils* (1,187), *Caramel/Crystal 60L* (946). No fuzzy matcher invents a
Briess or Crisp row, and `27_brew_catalogue.sql` forbids inventing specs to fill
the gap. **Product-level resolution is therefore abandoned in favour of type.**

### 1.7 The malt-type taxonomy resolves 98.7%

~30 rules over name + the °L the recipe itself states. `measured` 2026-09-19,
146,343 fermentable rows at `views>500`:

| | rows | share |
|---|---|---|
| classified | 144,414 | **98.7%** |
| unclassified | 1,929 | 1.3% |

The 1.3% is mostly fruit (Cherry, Mango, Raspberry), which belongs in misc, not
the grist. Nothing is invented: every classification reads a value already
carried by the recipe row.

---

## 2. Decisions taken

| # | Decision | Rationale |
|---|---|---|
| D1 | Corpus filter is `views > 500` | §1.3 — keeps 114 trendable styles vs 55 |
| D2 | Script-block language filter only, never ASCII | 45 CJK/Cyrillic rows at `views>1000`; a strict ASCII filter would drop 364, mostly English (*Kölsch*, *Crème Brûlée*, *Jalapeño*) |
| D3 | Fermentables resolve to **type**, not product | §1.6 — `ref.malts` cannot represent the corpus |
| D4 | Hops resolve to `ref.hops` product | §1.6 — 92.5% works |
| D5 | Misc and yeast stored as raw rows | user request; no taxonomy attempted |
| D6 | Trends split four ways: shape / composition / choice+amount / affinity | §1.1 — a flat list is unusable |
| D7 | Pair strength is **lift**, not co-occurrence | §1.2 |
| D8 | Every trend row carries `n_with`; nothing reports below 30 | §1.4 |
| D9 | Trends are snapshotted, never mutated in place | user: *"not 1 by 1 recipes"* |
| D10 | `ref.malts` -> `ref.fermentables` | it must hold sugars, extracts, flaked adjuncts — none of which are malts |
| D12 | **Backward compatibility with the existing `nlq` surface is NOT a requirement** | user 2026-09-20: *"do not worry about what is used in the pipeline and what not. We are currently reworking things."* `trend.*` is designed for what it should be, not to preserve `common_practice`/`ingredient_practice` signatures |
| D11 | **brewersfriend is the source of record for now; Brewfather is the migration target** | user 2026-09-20, in two steps: *"I would like to go for a brewfather line"*, then *"for now, go with the brewersfriend values, not the brewfather. Later on, we could adjust the recipes."* Phased deliberately — see §3.7 |

---

## 3. `ref.fermentables`

### 3.1 Rename and column changes

`ref.malts` becomes `ref.fermentables`. This is not cosmetic: the table now has
to hold sugar (6% of corpus grist rows), lactose, DME/LME, and flaked adjuncts.

```sql
ALTER TABLE ref.malts RENAME TO fermentables;

-- maltster is NOT NULL with UNIQUE (maltster, name). Flaked oats has no
-- maltster. Generic commodity fermentables take NULL.
ALTER TABLE ref.fermentables ALTER COLUMN maltster DROP NOT NULL;

-- ⛔ potential_ppg was numeric(5,1) -- ONE value. Almost every commodity
-- fermentable is published as a RANGE (33-35, 34-36, 43-45). Storing the
-- midpoint discards information that was deliberately supplied.
ALTER TABLE ref.fermentables ADD COLUMN potential_ppg_min numeric(5,1);
ALTER TABLE ref.fermentables ADD COLUMN potential_ppg_max numeric(5,1);

-- Fermentability. brew.ingredients already carries this as a BOOLEAN in
-- attrs->>'fermentable', read by 29_brew_formulate.sql:88 ("This is why a
-- lactose stout finishes high"). A boolean cannot hold "honey is 92%".
-- Stored here as reference data; the boolean stays derived from it, so the
-- calculator does not change.
ALTER TABLE ref.fermentables ADD COLUMN fermentability_pct numeric(5,2);

-- Where the numbers came from. Never let a colour-derived guess be
-- indistinguishable from a published spec. Same discipline as
-- corpus.styles.match_method.
ALTER TABLE ref.fermentables ADD COLUMN spec_source text
  CHECK (spec_source IN ('brewersfriend','brewfather','maltster','user_reference','corpus_default','manual'));
ALTER TABLE ref.fermentables ADD COLUMN spec_note text;
```

The existing `potential_ppg` stays for the 77 maltster rows that have a single
published figure. New commodity rows use the min/max pair.

### 3.2 New rows

Under D11 every row below is **today's brewersfriend catalogue value**, read from
<https://www.brewersfriend.com/fermentables/> on 2026-09-20 (1,515 fermentables).
`spec_source = 'brewersfriend'`. The Brewfather figure goes in `spec_note` wherever
it differs, so §3.7's migration is a set of UPDATEs and not a re-derivation.

⚠ This supersedes the 2020 corpus defaults used in earlier drafts. Where the two
differ the live catalogue wins, because D11 selects the publisher, not the
snapshot. The `Recipes` count beside each row is brewersfriend's own usage figure
and is recorded only to show which row is the canonical one when names collide.

**Flaked adjuncts and acidulated**

| name | ppg | °L | bf type | bf recipes |
|---|---|---|---|---|
| Flaked Oats | **33** | **2** | Raw | 212,976 |
| Flaked Barley | **32** | **2** | Raw | 57,103 |
| Flaked Wheat | **34** | **2** | Raw | 78,964 |
| Flaked Corn | **40** | **1** | Raw | 48,986 |
| Flaked Rye | **36** | **3** | Raw | 13,481 |
| Acidulated Malt | **27** | **3** | Acidulated malt | 88,177 |
| Oat Malt | **28** | **2** | Base malt | 12,649 |

`Flaked Maize` is a separate, near-unused row (37 ppg, 177 recipes); `Flaked Corn`
is the canonical one. Oat Malt is included because §3.5 showed the malted/flaked
distinction matters and `ref.fermentables` had only Viking's 27.7.

Acidulated usage rate is 1–5% of grist (lowers mash pH via lactic acid); this
belongs in the taxonomy's sanity envelope (§4), not in this table.

**Rice** — the six-variety table drafted earlier is dropped at the user's
instruction. brewersfriend carries these as **two distinct fermentables**:

| name | ppg | °L | bf type | bf recipes |
|---|---|---|---|---|
| Rice | **35.5** | **1** | Raw | 1,614 |
| Flaked Rice | **40** | **1** | Raw | 18,384 |

⚠ **An earlier draft of this document got this wrong twice.** It recorded a single
"Rice Flakes" row at 35.5, and then cited the gap between that and the corpus's
40.0 as evidence that site defaults drift. They are not the same ingredient: 35.5
is `Rice`, 40 is `Flaked Rice`, and the corpus's 40.0 was `Flaked Rice` all along.
Nothing drifted. The drift argument is withdrawn.

Both rows load. Brewfather's 32 (1.032 sg) / 2 EBC goes in `Flaked Rice`'s
`spec_note`, since that is the row it corresponds to.

Rice Syrup Solids (37 ppg, 1 °L) and Brown Rice Syrup — Gluten Free (44 ppg, 2 °L)
also exist and match the figures supplied earlier; both load as sugars.

**Sugars** — the only rows carrying `fermentability_pct`.

| name | ppg | ferm % | °L | bf recipes |
|---|---|---|---|---|
| Cane Sugar | **46** | 95–100 | **0** | 59,084 |
| Corn Sugar — Dextrose | **42** | 100 | **1** | 81,672 |
| Brown Sugar | **45** | 95–100 | **15** | 29,012 |
| Belgian Candi Sugar — Clear/Blond (0L) | **38** | 90–100 | **0** | 16,363 |
| Belgian Candi Sugar — Amber/Brown (60L) | **38** | 90–100 | **60** | 6,090 |
| Belgian Candi Sugar — Dark (275L) | **38** | 90–100 | **275** | 5,648 |
| Belgian Candi Syrup — D-90 | **32** | 90–100 | **90** | 3,008 |
| **Lactose (Milk Sugar)** | **41** | **0** | **1** | 45,660 |
| Honey | **35** | 90–95 | **2** | 42,679 |
| Rice Syrup Solids | **37** | 100 | **1** | 2,788 |
| Brown Rice Syrup — Gluten Free | **44** | 100 | **2** | 1,035 |

⚠ Candi **sugar** is 38 and candi **syrup** is 32 — a real distinction in the
catalogue, not a duplicate. The supplied 35–36 matched neither.

`fermentability_pct` is the one field brewersfriend does **not** publish, so those
values remain `user_reference` while ppg and colour become `brewersfriend`. A row
may therefore carry two sources; `spec_note` records which field came from where.

**Extracts**

| name | ppg | °L | bf recipes |
|---|---|---|---|
| Dry Malt Extract — Pilsen | **42** | **2** | 17,520 |
| Dry Malt Extract — Extra Light | **42** | **3** | 16,987 |
| Dry Malt Extract — Light | **42** | **4** | 56,148 |
| Dry Malt Extract — Munich | **42** | **8** | 2,259 |
| Dry Malt Extract — Amber | **42** | **10** | 15,492 |
| Dry Malt Extract — Dark | **44** | **30** | 8,657 |
| Dry Malt Extract — Wheat | **42** | **3** | 15,302 |
| Liquid Malt Extract — Pilsen | **35** | **2** | 13,820 |
| Liquid Malt Extract — Extra Light | **37** | **3** | 8,417 |
| Liquid Malt Extract — Light | **35** | **4** | 40,961 |
| Liquid Malt Extract — Munich | **35** | **8** | 6,479 |
| Liquid Malt Extract — Amber | **35** | **10** | 16,407 |
| Liquid Malt Extract — Dark | **35** | **30** | 8,697 |
| Liquid Malt Extract — Wheat | **35** | **3** | 9,676 |

⚠ The supplied ranges were wrong in a structured way worth noting: DME is a flat
**42** across almost every grade (44 for Dark), not 43–45, and LME is a flat
**35** (37 for Extra Light), not 35–37 with grade-dependent spread. Colour, not
ppg, is what varies across grades. Branded rows go higher — Briess DME sits at
43–45 — so the supplied figures look like Briess values generalised to the
category.

### 3.3 Lactose — settled by D11 (brewersfriend)

Three figures existed:

| source | ppg | °L |
|---|---|---|
| user, initial | ~46 | 0–1 |
| **brewersfriend.com** | **41** | **1** |
| **Brewfather** | **35** (1.035) | **0 EBC** |

The corpus's 41.0 is not independent evidence — it *is* brewersfriend's default
(§1.5), so this is two sources, not three-thousand-and-two.

It also barely matters. Lactose is 0% fermentable, so its points land entirely on
FG, but the gap between 35 and 41 is small at real dosing — `measured` via
`brew.f_compute_recipe`'s own arithmetic:

```
 250 g lactose in 20 L  ->  diff = 0.63 pts on FG
 500 g lactose in 20 L  ->  diff = 1.25 pts on FG     <- typical milk stout
1000 g lactose in 20 L  ->  diff = 2.50 pts on FG
```

At typical dosing the two sources disagree by roughly one hydrometer tick.

**Resolution: 41 ppg, `spec_source = 'brewersfriend'`.** This row has now been
settled three times — 35–41 as a range, then 35 under the first reading of D11,
now 41 under its phased form. The churn is itself the argument for §3.7: a
`spec_note` carrying the alternative makes each flip a one-row UPDATE instead of
a re-derivation. Brewfather's 35 goes in `spec_note`.

Colour 1 °L (Brewfather's 0 EBC and brewersfriend's 1 °L are the same claim —
colourless), and the practical gap remains ~1.25 pts on FG at typical dosing.

### 3.4 Acidulated — settled by D11

**27 ppg, 3 °L, `spec_source = 'brewersfriend'`.** The user's earlier 33–35 /
1.7–3.0 goes in `spec_note`.

⚠ An earlier draft called this "not cushioned", which was wrong. Acidulated is
capped at 1–5% of grist by its own usage rate, and that dose limit cushions it
harder than lactose's fermentability gap. `measured` 2026-09-20:

```
1% of a 5 kg grist ( 50 g)  ->  diff = 0.11 pts on OG
3% of a 5 kg grist (150 g)  ->  diff = 0.32 pts on OG   <- typical
5% of a 5 kg grist (250 g)  ->  diff = 0.53 pts on OG   <- maximum dose
```

Half a gravity point at maximum dose. The 25% headline gap never mattered.

Usage rate 1–5% of grist belongs in the taxonomy's sanity envelope (§4), not here.

### 3.5 Brewfather's own figures are already in this database — for §3.7

`75_corpus_recipes.sql` loaded 10 Brewfather BeerJSON exports, and
`corpus.recipe_fermentables` carries `yield_potential_value` (as sg) and
`color_value` (as SRM) per row — Brewfather's catalogue values, not the brewer's.
25 rows, `measured` 2026-09-20:

```
Oats, Flaked        (generic)   1.0368 sg   1 SRM      -> 36.8 ppg
Maris Otter         Crisp       1.038  sg   2.79 SRM   -> 38.0 ppg
Carapils            Briess      1.0336 sg   1.5 SRM    -> 33.6 ppg
Caramunich II       Weyermann   1.0348 sg   63 SRM     -> 34.8 ppg
Pilsen Malt         BestMalz    1.0381 sg   1.78 SRM   -> 38.1 ppg
```

Conversion: `ppg = (sg - 1) * 1000`. Colour is SRM, so `°L` is the same number.

Under D11's phased form these are **not** loaded as primary values. They are the
target of the §3.7 migration, and they matter now because they are a local,
checkable Brewfather source needing no external lookup — which is what makes that
migration cheap when it happens.

### 3.6 Flaked oats — settled by D11

**33 ppg, 2 °L, `spec_source = 'brewersfriend'`.** Brewfather's 36.8 / 1.0 goes
in `spec_note`.

The precedence question this row raised — does a blanket sourcing policy override
an explicit per-row instruction? — is now moot: D11's phased form and the user's
explicit value agree. `measured` impact either way was 0.57 pts on OG at 10% of
grist, a typical oatmeal stout.

Worth keeping on record: the corpus carries *both* conventions under different
names — `Flaked Oats` at 33.0 (23,922 rows) and `Oats, Flaked` at 37.0 (124 rows)
— so the split is real in the wild, and Brewfather sits with the second. §3.7 will
have to choose a name as well as a number.

### 3.7 ⚠ The Brewfather migration is deferred, not cancelled

D11 is phased on purpose: *"Later on, we could adjust the recipes."* Loading
brewersfriend values now keeps the corpus, the trend tables and the user's
existing Brewfather recipes on **one** line rather than two half-migrated ones.

What makes the later switch cheap, and must therefore be built now:

1. **Every row carries the alternative in `spec_note`.** Flipping a fermentable
   is a one-row UPDATE, never a re-derivation. §3.3 was re-settled three times in
   one day; this is not hypothetical.
2. **`spec_source` distinguishes the lines**, so `WHERE spec_source =
   'brewersfriend'` enumerates exactly what the migration must revisit.
3. ⛔ **Specs are *not* copied into `trend.*`.** Trend rows reference
   `ferm_type`, and types reference `ref.fermentables`. A spec change must never
   require a trend rebuild — if it does, the indirection in §4 has been
   short-circuited and that is a bug.

⚠ The migration also changes *names*, not only numbers (§3.6), so it is a mapping
exercise and not a numeric sweep. It needs its own spec when the time comes.

### 3.8 Sugars and extracts — resolved from the live catalogue

O8 is closed. Read from <https://www.brewersfriend.com/fermentables/> on
2026-09-20; every §3.2 row is now a catalogue value rather than a general-reference
range. What the reconciliation changed:

| row | supplied | brewersfriend | |
|---|---|---|---|
| Dark candi sugar | 35–36 | **38** | supplied matched neither sugar (38) nor syrup (32) |
| DME, all light grades | 43–45 | **42** | flat across grades; 44 only for Dark |
| LME light | 35–37 | **35** | flat; 37 only for Extra Light |
| Honey | 30–36 | **35** | ✓ inside the supplied range |
| Cane sugar | ~46 | **46** | ✓ |
| Corn sugar / dextrose | 42–46 | **42** | ✓ contained |
| Rice syrup solids | 37–40 | **37** | ✓ contained |
| Brown rice syrup | 44 | **44** | ✓ exact |
| Flaked barley | 32 | **32** | ✓ exact |
| Flaked wheat | 34–36 | **34** | ✓ contained |
| Flaked corn | 37–40 | **40** | ✓ contained |
| Acidulated | 27 | **27** | ✓ exact |
| Lactose | 41 | **41** | ✓ exact |
| Flaked oats | 33 | **33** | ✓ exact |

⚠ The DME/LME finding is structural, not a rounding difference: **colour varies
across grades, ppg does not.** The supplied 43–45 / 35–37 spreads look like Briess
figures (which do sit at 43–45) generalised to the generic category. Anything else
in this document that assumed grade-dependent extract should be re-read.

Only `fermentability_pct` remains un-sourced from brewersfriend — the catalogue
does not publish it — so those values stay `user_reference`.

## 4. The malt-type taxonomy## 4. The malt-type taxonomy### 3.8 Sugars and extracts — resolved from the live catalogue

O8 is closed. Read from <https://www.brewersfriend.com/fermentables/> on
2026-09-20; every §3.2 row is now a catalogue value rather than a general-reference
range. What the reconciliation changed:

| row | supplied | brewersfriend | |
|---|---|---|---|
| Dark candi sugar | 35–36 | **38** | supplied matched neither sugar (38) nor syrup (32) |
| DME, all light grades | 43–45 | **42** | flat across grades; 44 only for Dark |
| LME light | 35–37 | **35** | flat; 37 only for Extra Light |
| Honey | 30–36 | **35** | ✓ inside the supplied range |
| Cane sugar | ~46 | **46** | ✓ |
| Corn sugar / dextrose | 42–46 | **42** | ✓ contained |
| Rice syrup solids | 37–40 | **37** | ✓ contained |
| Brown rice syrup | 44 | **44** | ✓ exact |
| Flaked barley | 32 | **32** | ✓ exact |
| Flaked wheat | 34–36 | **34** | ✓ contained |
| Flaked corn | 37–40 | **40** | ✓ contained |
| Acidulated | 27 | **27** | ✓ exact |
| Lactose | 41 | **41** | ✓ exact |
| Flaked oats | 33 | **33** | ✓ exact |

⚠ The DME/LME finding is structural, not a rounding difference: **colour varies
across grades, ppg does not.** The supplied 43–45 / 35–37 spreads look like Briess
figures (which do sit at 43–45) generalised to the generic category. Anything else
in this document that assumed grade-dependent extract should be re-read.

Only `fermentability_pct` remains un-sourced from brewersfriend — the catalogue
does not publish it — so those values stay `user_reference`.

## 4. The malt-type taxonomy## 4. The malt-type taxonomy

⚠ **brewersfriend publishes its own type vocabulary**, `measured` 2026-09-20 over
all 1,515 catalogue rows:

```
Base malt 545 · Crystal malt 294 · Roasted malt 192 · Specialty malt 149
Fruit 71 · Extract 66 · Raw 65 · Sugar 56 · Gluten-free malt 26
Smoked malt 14 · Honey 9 · Acidulated malt 8 · Puree 8 · Other 7 · Juice 5
```

Fifteen types against this document's twenty-two, and they agree on structure: the
split this schema needs beyond theirs is **colour banding inside Crystal** (294
rows in one bucket is useless for a trend) and separating Munich/Vienna out of
Base. Their vocabulary is worth adopting as the `role` layer, with the extra
resolution layered under it — it is published, stable, and already tags every row
the loader will see.

`corpus.fermentable_types`, ~22 seeded rows. Each type carries the role it fills,
a sanity envelope, and a **substitute** pointing into `ref.fermentables` so a
generated recipe can be expressed in malts that are actually purchasable.

```sql
CREATE TABLE corpus.fermentable_types (
  type_key        text PRIMARY KEY,   -- 'crystal_medium'
  role            text NOT NULL       -- base|character|colour|adjunct|sugar|extract
                  CHECK (role IN ('base','character','colour','adjunct','sugar','extract')),
  lov_min         numeric(6,1),       -- the classifier's colour band
  lov_max         numeric(6,1),
  typical_pct_min numeric(5,2),       -- sanity envelope, NOT a trend
  typical_pct_max numeric(5,2),
  substitute_id   bigint REFERENCES ref.fermentables(id),
  substitute_basis text CHECK (substitute_basis IN ('exact','colour_ppg','sourced','manual')),
  substitute_note text
);
```

`substitute_basis` is the point of the table. A colour-derived stand-in must
never read as a published equivalence.

### 4.1 The substitution map

16 of 22 types resolve cleanly into the existing 77 rows:

| type | substitute | basis |
|---|---|---|
| base_pilsner | Weyermann Pilsner Malt (1.8 °L) | exact |
| base_pale | Weyermann Pale Ale Malt (2.9 °L) | colour_ppg |
| vienna | Weyermann Vienna Malt (3.2) | exact |
| munich | Weyermann Munich Malt Type 1 (6.1) | exact |
| wheat | Weyermann Wheat Malt pale (1.9) | exact |
| rye | Weyermann Rye Malt pale (3.1) | exact |
| dextrine | Weyermann CARAFOAM® (2.1) | exact |
| crystal_light | Weyermann CARAHELL® (9.9) | colour_ppg |
| crystal_medium | Weyermann CARAAMBER® (26.9) | colour_ppg |
| crystal_dark | Weyermann CARABOHEMIAN® (74.0) | colour_ppg |
| crystal_extra_dark | Weyermann CARAAROMA® (151.2) | colour_ppg |
| chocolate | Viking Chocolate Light (150.5) | colour_ppg |
| black | Viking Black Malt (525.2) | colour_ppg |
| roast_barley | Viking / Weyermann Roasted Barley | exact |
| kilned_specialty | Weyermann Melanoidin Malt (26.9) | colour_ppg |
| smoked | Weyermann Beech Smoked Barley (2.8) | exact |

The remaining 6 — oats, acidulated, adjunct_starch, sugar, sugar_lactose,
extract — point at the §3.2 rows.

⚠ **Flavour equivalence is not asserted anywhere.** Colour and ppg are measured;
flavour is not. A `substitute_basis = 'sourced'` row requires a citation in
`substitute_note`. A cell stays NULL rather than carrying an uncited claim.

---

## 5. The filtered corpus load

Eight tables, prefixed `bf_` because **`corpus.recipes` is already taken** by the
BeerJSON tables from `75_corpus_recipes.sql` (10 Brewfather exports, live). Two
unrelated corpora cannot share a name.

```
corpus.bf_recipes       36,271  views>500, script-clean
                                + views, style_raw, ref_style_id bridge
corpus.bf_fermentables 146,343  ferm_type FK + pct_of_grist
                                + the ppg/°L the recipe stated, raw name kept
corpus.bf_hops         141,179  ref_hop_id FK (92.5%), raw name kept
corpus.bf_miscs          all    raw rows (D5)
corpus.bf_yeasts         all    raw rows (D5)
```

Raw strings are kept on every child row. An unresolved string is honest; a
fabricated resolution is not — the rule `70_corpus.sql` established and this
schema inherits.

⛔ **Never vectorised.** These rows are unvalidated, self-reported and carry no
publisher. Embedding them into `kb.*` would hand retrieval 36,000 documents that
look like knowledge and are not. The `kb.chunks` knowledge-only rule covers this
schema for the same reason it covers `brew.*`.

### 5.1 Style folding

`style_raw` bridges to `ref.styles` exactly as `74_corpus_styles.sql` did —
`match_method` in `('exact','manual')`, NULL where no link is established.

This recovers counts the raw strings split: `Imperial IPA` (345) + `Double IPA`
(77), `Weizen/Weissbier` (182) + `Weissbier` (65), `Dry Stout` + `Irish Stout`.
Some of the §1.3 casualties come back for free.

---

## 6. The trend schema

One schema, `trend`. Four kinds of fact, never mixed.

```sql
-- =========================================================
-- SNAPSHOT — D9. Rebuilds write a NEW snapshot; nothing
-- mutates in place, so a finalised patch stays finalised
-- and two patches can be diffed.
-- =========================================================
CREATE TABLE trend.snapshot (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  built_at      timestamptz NOT NULL DEFAULT now(),
  corpus_filter text NOT NULL,        -- 'views>500 script-clean'
  n_recipes     int  NOT NULL,
  is_current    boolean NOT NULL DEFAULT false,
  notes         text
);
CREATE UNIQUE INDEX trend_snapshot_one_current
  ON trend.snapshot (is_current) WHERE is_current;

-- =========================================================
-- SHAPE — read FIRST, as a budget, before any ingredient.
-- This table is what makes 20 hops unreachable.
-- =========================================================
CREATE TABLE trend.style_profile (
  snapshot_id   bigint NOT NULL REFERENCES trend.snapshot(id) ON DELETE CASCADE,
  ref_style_id  bigint NOT NULL REFERENCES ref.styles(id),
  n_recipes     int NOT NULL,

  ferm_count_p25        numeric(4,1),
  ferm_count_p50        numeric(4,1),
  ferm_count_p75        numeric(4,1),

  hop_variety_count_p25 numeric(4,1),
  hop_variety_count_p50 numeric(4,1),   -- <<< the guard
  hop_variety_count_p75 numeric(4,1),
  hop_addition_count_p50 numeric(4,1),  -- 3 varieties can be 6 additions

  og_p25 numeric(6,4), og_p50 numeric(6,4), og_p75 numeric(6,4),
  fg_p25 numeric(6,4), fg_p50 numeric(6,4), fg_p75 numeric(6,4),
  abv_p25 numeric(5,2), abv_p50 numeric(5,2), abv_p75 numeric(5,2),
  ibu_p25 numeric(6,2), ibu_p50 numeric(6,2), ibu_p75 numeric(6,2),
  srm_p25 numeric(6,2), srm_p50 numeric(6,2), srm_p75 numeric(6,2),

  PRIMARY KEY (snapshot_id, ref_style_id)
);

-- =========================================================
-- COMPOSITION — roles are mutually exclusive and exhaustive,
-- so role_pct sums to ~100 BY CONSTRUCTION. This is the
-- answer to the 190%-grist problem in §1.1.
-- =========================================================
CREATE TABLE trend.style_grist_template (
  snapshot_id  bigint NOT NULL REFERENCES trend.snapshot(id) ON DELETE CASCADE,
  ref_style_id bigint NOT NULL REFERENCES ref.styles(id),
  role         text   NOT NULL,   -- base|character|colour|adjunct|sugar

  slots_p25    numeric(4,1),      -- how many DISTINCT types of this role
  slots_p50    numeric(4,1),
  slots_p75    numeric(4,1),

  role_pct_p25 numeric(5,2),      -- share of grist taken by the whole role
  role_pct_p50 numeric(5,2),
  role_pct_p75 numeric(5,2),

  n_with       int NOT NULL,
  PRIMARY KEY (snapshot_id, ref_style_id, role)
);

-- =========================================================
-- CHOICE + AMOUNT — every amount is CONDITIONAL ON PRESENCE.
-- A row here can never be summed with its siblings.
-- =========================================================
CREATE TABLE trend.style_fermentable (
  snapshot_id   bigint NOT NULL REFERENCES trend.snapshot(id) ON DELETE CASCADE,
  ref_style_id  bigint NOT NULL REFERENCES ref.styles(id),
  ferm_type     text   NOT NULL REFERENCES corpus.fermentable_types(type_key),
  role          text   NOT NULL,

  n_with         int NOT NULL,          -- D8: the gate
  presence_rate  numeric(5,4) NOT NULL,
  rank_in_role   int,

  pct_of_grist_p25 numeric(5,2),        -- GIVEN present
  pct_of_grist_p50 numeric(5,2),
  pct_of_grist_p75 numeric(5,2),

  PRIMARY KEY (snapshot_id, ref_style_id, ferm_type)
);

CREATE TABLE trend.style_hop (
  snapshot_id   bigint NOT NULL REFERENCES trend.snapshot(id) ON DELETE CASCADE,
  ref_style_id  bigint NOT NULL REFERENCES ref.styles(id),
  ref_hop_id    bigint NOT NULL REFERENCES ref.hops(id),

  n_with        int NOT NULL,
  presence_rate numeric(5,4) NOT NULL,
  rank          int,

  share_of_hop_mass_p25 numeric(5,2),   -- GIVEN present
  share_of_hop_mass_p50 numeric(5,2),
  share_of_hop_mass_p75 numeric(5,2),

  pct_bittering numeric(5,4),           -- how this hop is USED in this style
  pct_flavour   numeric(5,4),
  pct_aroma     numeric(5,4),
  pct_dryhop    numeric(5,4),
  timing_min_p50 numeric(6,1),

  PRIMARY KEY (snapshot_id, ref_style_id, ref_hop_id)
);

-- =========================================================
-- AFFINITY — lift, not co-occurrence (§1.2). Negative lift
-- is the useful half: it is the only signal that says
-- "these are both popular and brewers still avoid them".
-- =========================================================
CREATE TABLE trend.style_hop_pair (
  snapshot_id  bigint NOT NULL REFERENCES trend.snapshot(id) ON DELETE CASCADE,
  ref_style_id bigint NOT NULL REFERENCES ref.styles(id),
  hop_a_id     bigint NOT NULL REFERENCES ref.hops(id),
  hop_b_id     bigint NOT NULL REFERENCES ref.hops(id),

  support      int NOT NULL,            -- recipes containing both; >= 30 only
  lift         numeric(6,3) NOT NULL,
  confidence   numeric(5,4),            -- P(B|A)

  PRIMARY KEY (snapshot_id, ref_style_id, hop_a_id, hop_b_id),
  CONSTRAINT hop_pair_ordered CHECK (hop_a_id < hop_b_id),
  CONSTRAINT hop_pair_supported CHECK (support >= 30)
);
```

Reads go through views pinned to `is_current`, so callers never name a snapshot
id.

### 6.1 The n>=30 gate is structural, not advisory

`trend.style_hop_pair` enforces `support >= 30` as a CHECK constraint — a row
below the gate cannot exist. For the other tables the gate is a reporting rule,
because the *count itself* is worth storing even when the number is not: "only
8 recipes, no reliable figure" is a more useful answer than silence, and is
exactly what `ref.styles.has_vitals` established as the house pattern.

---

## 7. How the generator reads it

The order is the design. Shape is consumed as a budget *before* any popularity
list is opened, which is what makes the failure mode unreachable.

1. `trend.style_profile` -> **budget: 4 fermentables, 3 hop varieties.**
2. `trend.style_grist_template` -> base 80% / crystal 8% / colour 5% / adjunct 7%;
   base slots = 1, crystal slots = 1.
3. For each role, draw `slots_p50` types from `trend.style_fermentable` weighted
   by `presence_rate`; allocate the role's `role_pct` across its slots;
   **normalise to exactly 100%**.
4. Draw `hop_variety_count_p50` hops from `trend.style_hop` by `presence_rate`;
   consult `trend.style_hop_pair` to prefer `lift > 1` and reject `lift < 1`.
5. Map each `ferm_type` to a purchasable row via
   `corpus.fermentable_types.substitute_id`.
6. Hand to `brew.f_compute_recipe` -> OG/FG/ABV/IBU/SRM. The model never does
   the arithmetic (architecture §7.4).
7. Check against `ref.styles` min/max; iterate.

Twenty hops is unreachable: the budget is spent at step 1.

---

## 8. What else this work must touch

### 8.1 The three broken `nlq` functions — not a design constraint

`nlq.common_practice`, `nlq.ingredient_practice` and `nlq.f_corpus_styles` fail
today, because they reference `corpus.recipe_misc` and `corpus.recipe_yeasts`
(dropped) and a `corpus.recipes` reshaped to BeerJSON:

```
postgres=# select nlq.common_practice('stout');
ERROR:  column c.style_raw does not exist
```

`measured` 2026-09-20, they are referenced by seven nodes across three workflows
— `wf-step-practice`, `cap-formulate-recipe` (including Step 3 · propose and
Step 3b · re-propose) and `chat-agent`.

⚠ **Per D12 this does not constrain the schema.** An earlier draft treated these
signatures as something `trend.*` had to preserve, and then as "the integration
point". Both readings are withdrawn: the pipeline is being reworked, so `trend.*`
is designed for what the generator in §7 actually needs, and the old functions are
replaced rather than repointed.

What remains true is **operational**, and will bite during that rework:

⚠ `chat-agent` has `settings.availableInMCP = false`, so it can only be edited as
tracked JSON plus `n8n import:workflow` — which **deactivates** the workflow,
requires a re-publish, and *still* leaves the webhook unregistered until
`docker restart n8n`. Probe the webhook before trusting any eval that follows:

```bash
curl -s -o /dev/null -w '%{http_code} %{time_total}\n' --max-time 8 \
  -X POST http://localhost:5678/webhook/<id>/chat \
  -H 'Content-Type: application/json' \
  -d '{"sessionId":"probe","action":"sendMessage","chatInput":"ping"}'
```

⚠ An inactive workflow also cannot be called as a sub-workflow: `executeWorkflow`
returns the *string* "Workflow is not active and cannot be executed" as the tool's
result, which the model then retries until `Max iterations (5) reached`, burying
the real cause.

### 8.2 Housekeeping
1. ✅ **`recipes_full.txt` (180 MB) was untracked in the repo root.** Gitignored
   2026-09-20.
2. ⚠ **`db-init`'s file list does not glob.** Every new `.sql` here must be added
   to `docker-compose.yml` or it silently never runs. The five dropped corpus
   files (`70`–`74`) are still on disk and stay dropped.

---

## 9. Open decisions

| # | Question | Default if unanswered |
|---|---|---|
| O1 | ~~Acidulated ppg~~ — **settled §3.4**: 27 ppg, 3 °L | closed |
| O2 | ~~Lactose ppg~~ — **settled §3.3**: 41, per D11 | closed |
| O3 | ~~Rice~~ — **settled §3.2**: two rows, `Rice` 35.5 and `Flaked Rice` 40 | closed |
| O4 | ~~Flaked oats single vs range~~ — superseded by O6 | closed |
| O5 | ~~Repoint or drop the `nlq` functions~~ — **moot under D12**, §8.1 | closed |
| O6 | ~~Flaked oats~~ — **settled §3.6**: 33 ppg, 2 °L | closed |
| O7 | ~~Acidulated Brewfather lookup~~ — no longer blocking; wanted for `spec_note` | deferred to §3.7 |
| O8 | ~~Sugars and extracts~~ — **settled §3.8** from the live catalogue | closed |

---

## 10. Verification

The design is implemented correctly when all of these hold:

1. `ref.fermentables` exists, `ref.malts` does not, and the 77 original rows are
   unchanged.
2. Every §3.2 row is present with a non-NULL `spec_source`, and no row
   carries `spec_source = 'corpus_default'` as its sole basis.
3. `corpus.fermentable_types` has 22 rows, each with a `substitute_id` and a
   `substitute_basis`; no row asserts a flavour equivalence without a citation.
4. The loader classifies **>= 98%** of `bf_fermentables` rows to a type
   (baseline §1.7: 98.7%) and resolves **>= 92%** of `bf_hops` rows to
   `ref.hops` (baseline §1.6: 92.5%).
5. ~~For every style in `trend.style_grist_template`, `sum(role_pct_p50)` is
   within 100 ± 5.~~ — **superseded, RULING 12, 2026-09-20**: no style's
   `sum(role_pct_p50)` may exceed 100; undershoot is expected and is
   normalised away by the generator per §7 step 3 ("normalise to exactly
   100%"), so no consumer depends on the stored sum reaching 100. `measured`
   2026-09-20 after Ruling 11's zero-fill fix, 73 styles: **0 exceeding 100**,
   24 within the original ±5 band, min 78.50 / median 92.40 / max 99.35. The
   original wording is kept above, struck through, because it is what the
   design was checked against before the corpus showed medians of
   mostly-absent roles don't add to 100 — the ceiling half of the criterion is
   what actually catches the double-counting failure in §0, and that half
   still holds exactly.
6. `select max(hop_variety_count_p50) from trend.style_profile` is <= 6.
   *(American IPA measured 3; any style claiming more than 6 is a bug.)*
7. No `trend.style_hop_pair` row has `support < 30` — enforced by CHECK.
8. The `nlq` surface exposes whatever the reworked pipeline needs; the three
   broken functions are gone rather than left failing (D12).
9. A full rebuild produces a new `trend.snapshot` row and leaves the previous
   snapshot's rows byte-identical.
