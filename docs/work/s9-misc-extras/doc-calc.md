# S9 · Doc → calc pass: misc doses, filing and cut points

Status: waiting for your review
Plan: [plan.md](plan.md) Task 1 · Brief: [brief.md](brief.md) B3
Read 2026-10-18. Conversions: 1 US gal = 3.785 L, 5 gal = 18.93 L, 1 oz = 28.35 g.
*How to Brew* page numbers are PDF pages (printed page + 26, BOOKS.md §1). The recipe tables that
`kb` lost were read in the PDF with `pdftotext -layout`.

Nothing here is guessed. Where a source gives no number, the entry stays empty (R15). Where I
propose a value that no source gives, it says "set by the user" and waits for your yes.

## Summary of what each source states

| Source | States | Does not state |
|---|---|---|
| Janish, *Guide to Coffee Beers* (`janish-coffee-beers`) | Dry beans: 2 oz per 5 gal, 48 h, three separate tests. Cold brew: 4 oz coarse ground in 1,200 mL water, 16 h, per 5 gal. | A range. Which dose is "noticeable" is Janish's result text, not a threshold. The cold-brew contact time in the beer. |
| *How to Brew* p. 225 (`palmer-how-to-brew`, "Brewing with Spices") | Coffee and cocoa: 60–225 g per 5 gal (19 L). "Most spices, such as cinnamon, vanilla …": 1–10 g per batch, vanilla after fermentation. | A vanilla-only dose or form (bean, paste). A time for vanilla. |
| *How to Brew* pp. 240, 409 (recipes) | Orange peel: about 50 g, steeped 15 min after the boil (heat off), removed before fermentation. Two recipes, same figure. | A dose in g/L (the batch is the book's 5 gal, 19 L; the recipe header does not repeat it). A dried-peel dose. |
| BJCP 2021 (`ref.beer_style.raw`, introductions) | 30A is "Spice, Herb, or Vegetable". Specialty-Type ingredients are "yeast/bacteria, smoke, wood, fruit, spice, grain, or sugar". "Culinary rather than botanical definition". | Coffee, cocoa, chocolate or vanilla by name in 30A text or in the introductions. |
| BA 2026 (`ref.beer_style.raw`) | One style each for coffee, chocolate or cocoa, herb and spice, fruit, wood, smoke. | A vanilla style (vanilla appears only inside "Dessert Stout or Pastry Beer"). |

## A. BJCP filing: coffee, cacao and vanilla under 30A

**Stated.**
- Introductions, line 369: "Specialty Ingredients (yeast/bacteria, smoke, wood, fruit, spice,
  grain, or sugar)". Coffee, cocoa and vanilla are not named. The only help is line 375: "use the
  culinary rather than the botanical definition of ingredients".
- 30A (`ref.beer_style` BJCP 30A): Overall impression says "spices, herbs, or vegetables (SHVs)".
  Its text names no coffee, cocoa or vanilla. Its commercial examples are "Alesmith Speedway
  Stout, … Founders Breakfast Stout, … Young's Double Chocolate Stout". The record gives names
  only, not the ingredients.
- 30D: "Specialty Spice Beer", examples with honey and orange. 30C: "Fruit peel (e.g., oranges, lemon)
  may be used" with the spices (this is the only BJCP line that files a citrus peel).
- 33A (wood): "Toasted or charred wood can add vanilla, caramel, … coffee, chocolate, or cocoa".
  That is a flavour that wood gives, not a filing of coffee or vanilla as wood.
- `kb.chunk` search for coffee, cocoa, chocolate, vanilla in `bjcp-2021-introductions` and
  `bjcp-exam-study-guide-2017`: 0 chunks in the introductions; 2 chunks in the study guide
  (p. 51 chocolate malt, p. 73 lightstruck coffee analogy), neither about filing.
- *How to Brew* p. 225 calls vanilla a spice ("most spices, such as cinnamon, vanilla") and cocoa
  "a very popular brewing spice"; coffee and cocoa are "flavorings" (the exception to the spice
  dose).

**Reading (mine).** Nothing in BJCP 2021 states that coffee, cacao or vanilla belong in 30A. The
three best-supported readings: vanilla is a culinary spice (HTB calls it one; BA's herb and spice
text includes "seeds, fruits"); cocoa is called a brewing spice by HTB; coffee and chocolate stouts
are among 30A's examples, which suggests the BJCP expects them there, but the record does not say
what is in them.

**Proposed rule.** Spice, herb, coffee, cacao, vanilla → 30A is **set by the user, 2026-10-18**,
with this support: vanilla (HTB p. 225 calls it a spice), cacao (HTB p. 225 "brewing spice"),
coffee (HTB p. 225 "flavorings" beside spices; 30A examples are stouts, unverified as coffee).
Fruit → 29A and smoke → 32A follow the style names; wood → 33A follows "wood-based additives (e.g.,
chips, staves …)" in 33A's characteristic ingredients.

## B. BA codes per category

| Category | BA code | Line that supports it (`ref.beer_style` BA, `characteristicingredients`) |
|---|---|---|
| fruit | `american-style-fruit-beer` | "Fruit or fruit extracts, used as an adjunct … provide harmonious fruit character" |
| spice | `herb-and-spice-beer` | "any beer brewed with herbs or spices derived from leaves, roots, seeds, fruits, vegetables, flowers" |
| herb | `herb-and-spice-beer` | same line |
| vanilla | `herb-and-spice-beer` | same line ("seeds, fruits"); no BA style names vanilla as a style of its own. Reading, not stated. |
| coffee | `coffee-beer` | "Coffee beers incorporate coffee in any form." |
| cacao | `chocolate-or-cocoa-beer` | "beers of any classic style which incorporate dark chocolate or cocoa in any form" |
| wood | `wood-and-barrel-aged-beer` | "aged in either a wooden barrel or in contact with wood chips, spirals, strips" |
| smoke | `smoke-beer` | "Any style of beer can be smoked." |
| other | none | no row (the plan gives `other` no style) |

Note: BA's `dessert-stout-or-pastry-beer` names "chocolate, coffee, coconut, vanilla" but it is a
style for a type of beer, not for an ingredient; not used. All eight codes exist in `ref.beer_style`
(measured). The BJCP codes for step 2: fruit 29A; spice, herb, coffee, cacao, vanilla 30A; wood
33A; smoke 32A.

## C. Doses

"Anchor" = one dose a source reports as giving a noticeable result. "Range" = a usual range.
"Recipe" = an amount in one recipe.

| # | Figure | Quote | Where | Arithmetic | What it stands for |
|---|---|---|---|---|---|
| C1 | Coffee, dry beans, 2 oz / 5 gal, 48 h | "2 ounces for 48 hours of contact time for the dry bean beer" | Janish, Cold Brew vs. Dry Bean (repeated in two more tests, "2 ounces (56 grams) per 5-gallons for 48 hours") | 2 × 28.35 = 56.7 g; 56.7 / 18.93 = **3.0 g/L**; 48 h = **2880 min** | Anchor, whole beans. Janish reports a "robust fruity coffee punch" aroma; I read that as noticeable. |
| C2 | Coffee, cold brew, 4 oz / 5 gal, 16 h | "4 ounces of coffee (coarsely ground in 1,200 mL water)" and "16 hours of cold brew extraction" | Janish, same section | 4 × 28.35 = 113.4 g; 113.4 / 18.93 = **6.0 g/L** of dry coffee. 1,200 mL water is added too (0.063 L per L of beer). | Anchor, cold brew: "coffee flavor was where it shined". Extraction time 16 h = 960 min is before the liquid goes in; contact time in the beer is not stated. |
| C3 | Coffee and cocoa, usual range | "anywhere from a couple of ounces to a half pound (60–225 g) per 5 gal. (19 L) batch" | HTB p. 225 | 60 / 18.93 = **3.17**; 225 / 18.93 = **11.89 g/L** | Range for "flavorings, such as cocoa and coffee", any form. |
| C4 | Spices incl. vanilla | "Most spices, such as cinnamon, vanilla, ginger, and cloves, should be used in small amounts, for example, 1–10 g per batch." | HTB p. 225 | 1 / 18.93 = **0.053**; 10 / 18.93 = **0.528 g/L** | Range for spices in general. Vanilla is named but has no figure of its own. "Delicate spices like vanilla should be used after fermentation." |
| C5 | Orange peel, 50 g | "~1.75 oz. (50 g) orange peel (Steep 15 minutes)"; "After the boil, heat off; … hot steep for 15 minutes before chilling" | HTB p. 409 (Casual Wit) and p. 240 (Oud Geestigbier), same 50 g | 50 / 18.93 = **2.64 g/L**; 15 min | Recipe amount (fresh peel, two oranges, "without white pith"). Two recipes agree. Batch assumed the book's 5 gal (19 L); the recipe header does not say. |

Janish and HTB agree on the order of magnitude for coffee: C1 is 0.95 of C3's lower end, C2 is
inside C3's range (6.0 is 1.89 × C3's lower end).

## D. Cut points

The plan reads a dose against the row's own sourced dose `[lower, upper]`: below `M1 × lower` is
subtle, above `M2 × upper` is aggressive, else noticeable. For a single anchor, lower = upper = the
anchor.

**What the sources allow.** None gives a number for "subtle" or "aggressive". BJCP 30A and 29A only
say the character ranges "from subtle to aggressive"; BA says "ranging from subtle to intense".
The only second source for any ratio is C3 against C1/C2.

| Id | Proposed | Basis |
|---|---|---|
| M1 | **0.5** | Set by the user, 2026-10-18. Half the sourced lower dose reads as subtle. No source gives it; for orientation, 0.5 × C1 = 1.5 g/L is half of HTB's lower end (3.17). |
| M2 | **2.0** | Set by the user, 2026-10-18, with a cross-check: HTB's top coffee dose (11.89 g/L) is 1.98 × Janish's cold brew anchor (6.0 g/L), so 2 × the upper dose reaches the highest dose in any source for coffee. For vanilla it gives aggressive above 1.06 g/L; for the peel above 5.28 g/L. |
| M3 | **subtle 2 (low), noticeable 4 (medium), aggressive 6 (high)** | Set by the user, 2026-10-18. The 0–7 scale of `loaders/style_envelopes.py` `SCALE` (none 0, very low 1, low 2, medium-low 3, medium 4, medium-high 5, high 6, very high 7). One word per level, leaving 1, 3, 5 and 7 unused. Alternative: aggressive 7 ("very high"); I kept 6 so that 7 stays out of reach of a dose word. |

Effect of the proposal (g/L, for orientation):

| Entry | subtle below | noticeable | aggressive above |
|---|---|---|---|
| coffee, whole beans (3.0) | 1.5 | 1.5 to 6.0 | 6.0 |
| coffee, cold brew (6.0) | 3.0 | 3.0 to 12.0 | 12.0 |
| vanilla bean (0.05 to 0.53) | 0.026 | 0.026 to 1.06 | 1.06 |
| orange peel (2.64) | 1.32 | 1.32 to 5.28 | 5.28 |

Weak points, said plainly: M1 has no source at all. M2 is checked only on coffee. A point anchor
makes the noticeable band very wide (a factor of 4), because the source gives no spread.

## E. The entries (Task 11)

Sources (both in `ref.source`): `janish-coffee-beers`, `palmer-how-to-brew`. All doses g of dry
product per L of beer. A blank stays empty.

| File | Name | Form | Category | Usages | time_min | dose_g_per_l | Refs |
|---|---|---|---|---|---|---|---|
| `coffee-whole-beans.toml` | Coffee, whole beans | dry-beaned whole beans | coffee | secondary | 2880 | [3.0, 3.0] | time and dose: Janish, "Cold Brew vs. Dry Bean" (web page, no page number); description: same |
| `coffee-cold-brew.toml` | Coffee, cold brew | coarse ground, cold-steeped 16 h, added as liquid | coffee | packaging | (empty) | [6.0, 6.0] | dose: Janish "Cold Brew vs. Dry Bean"; usage: Janish "Bangun Recipe" ("Added … post-fermentation in purged keg prior to racking") |
| `vanilla-bean.toml` | Vanilla bean | whole bean | vanilla | secondary | (empty) | [0.05, 0.53] | dose: HTB p. 225 (spices, 1–10 g per batch); usage: HTB p. 225 ("after fermentation") |
| `orange-peel.toml` | Orange peel | fresh peel, no pith | spice | whirlpool | 15 | [2.64, 2.64] | dose and time: HTB p. 409 and p. 240 recipe notes |

Descriptions (one to three sentences, from the source) and descriptors (existing tags, no new
tags needed):

| File | Description | Descriptors | Aliases |
|---|---|---|---|
| coffee-whole-beans | "Whole roasted beans added to the finished beer, like a dry hop. Janish used 2 oz per 5 gal for 48 hours; the aroma was big and fruity, with less saturated coffee flavour." | `coffee` | coffee, coffee beans, whole bean coffee, dry-beaned coffee |
| coffee-cold-brew | "Coarse ground coffee steeped cold in a little water for 16 hours, then added to the beer. Janish used 4 oz per 5 gal; it gave a saturated coffee flavour with a fainter nose." | `coffee` | cold brew, cold brew coffee |
| vanilla-bean | "A delicate spice, used after fermentation. How to Brew gives 1 to 10 g per batch for most spices including vanilla; the book gives no vanilla-only dose." | `vanilla` | vanilla, vanilla beans, vanilla pod |
| orange-peel | "Thin peel of washed oranges, without the white pith, hot-steeped 15 minutes after the boil. About 50 g for a 5 gal batch in How to Brew's witbier recipes." | `orange`, `citrus` | orange peel, orange zest |

Aliases are what a brewer types (b23 wants "coffee", "vanilla beans"; b24 "orange peel"); no source
gives them. "coffee" will find both coffee entries; step 5 and 3 handle two products as they do two
hops of one name.

Three judgement calls to confirm: orange peel as category `spice` (24A and 30C treat the peel as a
spice, HTB's recipe is "Fruit and Spice Specialty"; the alternative `fruit` would make b24's 18B
verdict depend on 18B's `fruit` row); cold brew usage `packaging` from Janish's Bangun recipe (the
experiments do not say when the liquid went in); the cold-brew `time_min` left empty (the 16 h is
extraction, not contact).

## F. Not taken

| Figure | Where | Why not |
|---|---|---|
| 1 oz (28 g) cold brew in 300 mL, and 1 oz (28 g) beans | Janish, Bangun recipe | Batch size not stated (a unitank batch), so no g/L. |
| 25% coarse grinds + 75% beans: 56 g beans + 14 g ground | Janish | A suggestion Janish has not tried ("I wonder"); a blend of two forms. |
| Espresso shots | Janish (Tim Wendelboe) | No dose given. |
| "Add cold or hot steeped coffee, hot steep only minutes" | HTB p. 225 | Timing advice; the hot-steep form has no dose. Not an entry. |
| Cocoa 60–225 g, cocoa powder 0.5 lb in the porter | HTB p. 225 and recipe | No cacao entry in this work (only the brief's products). C3 is used only for the M2 cross-check. |
| Fruit 0.5–2 lb/gal (60–240 g/L) | HTB p. ~219 | No fruit entry; fruit sugar waits for M6. |
| Dried Curaçao orange peel | BJCP 24A | No dose. |
| Vanilla extract | none | A liquid extract is dosed in mL and "waits" (R14). |
| BA `dessert-stout-or-pastry-beer` as a category style | BA | A style of beer, not of an ingredient. |
