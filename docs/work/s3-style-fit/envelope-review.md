# S3 · Envelope review pack (Task 5)

A style's **envelope** says, for each sensation the guideline describes (hop aroma, roast,
esters…), the lowest and highest level the style allows and the characters it allows (citrus,
earthy, banana…), each backed by a quote from the guideline. Levels use one 0–7 scale:
**none · very low · low · medium-low · medium · medium-high · high · very high**. Next to it
sit the style's **characteristic ingredients**: a malt class (role), a named product, a hop
origin or a yeast family. Below, each of the 26 drafts from the local LLM is shown as it is
now, with what is wrong, the unknown words, and the fixes I propose. Nothing here is applied
yet; nothing is `reviewed = true`. The same fixes in loadable form:
[envelope-review-proposals.toml](envelope-review-proposals.toml) (`# fix N` = fix N below).

## Rules used in every style (so the sections below stay short)

- **R1 · Fruit and spice rows are for additions.** Yeast fruitiness goes under *esters*, yeast
  pepper or clove under *phenols*. The style's silence on *fruit* and *spice* is what marks a
  fruit or spice addition as "specialty"; a wrong *fruit* row would let them through.
- **R2 · No characters on body, sweetness or dryness.** Crystal malt drives these; a listed
  "creamy" would mark every crystal malt "wrong character" (the 16A, 16B and 17C reference
  recipes would fail).
- **R3 · Finish and body words.** Finish: sweet = low, medium = medium, medium-dry =
  medium-high, dry = high, very dry = very high. Body: light = low, medium-light = medium-low,
  medium-full = medium-high, full = high. Hints/touch = very low, light/mild = low.
- **R4 · Hop characters:** copied when the text lists typical descriptors, empty when it says
  "any variety"; "same descriptors as aroma" copies the aroma list.
- **R5 · Ingredients:** a malt class becomes a role (pale → base, crystal/caramel → crystal,
  dark/roasted → roast, Munich/amber → kilned, flaked/unmalted grain → adjunct). A product only
  where `ref` has exactly one (Flaked Rice, Lactose…). Hops → origin tag, yeast → family tag.
  `required = true` only for the one thing the style cannot be without, never for "A or B".
- Words dropped as "intensity" (medium-light, full, sweet, dry) or "texture" (soft, smooth,
  silky, chewy) are not flavours: no tag fits them, and the level already says it.

## Three questions that cut across styles

- **A · A text that says just "sugar"** (11B, 16A, 16B, 1C, 21A, 25B, 18A). `ref` has three
  sugars: Brown Candi Sugar, Honey, Lactose. (a) Name the role `sugar`: every sugar is 👍 there,
  lactose in an IPA too. (b) Name only the `ref` sugars that fit the style (18A: Honey, the b12
  reference recipe needs it; 26B: Brown Candi Sugar; 16A: Lactose), nothing elsewhere until
  `ref` has a plain sugar. **Recommend (b):** lactose in a bitter or IPA should stay ⚠️.
- **B · "Clean fermentation profile"** (1B, 1C, 5D, 6A, 8B, 18A, 18B, 21A, Mexican lager).
  Add phenols none–none and cap esters (very low for lagers). **Recommend yes:** without it a
  Belgian or weizen yeast in a Pils comes out 👍, because a silent core sensation never conflicts.
- **C · 31B and Specialty Honey Beer say "same as the base beer".** (a) Rate them on the base
  style's envelope (later work). (b) No sensory rows, only the sugar row; the Task 5 test must
  then allow 0 sensory rows for these two (a plan change). (c) A placeholder row the text does
  not support. **Recommend (b).**

What the fixes make true for the tests (brief R8, R9): 16A names Lactose, 1B Flaked Rice, 1C
Flaked Corn, 21C Flaked Oats, 15B a required roast role, 31B the role sugar; 18B names no rice,
17C no sugar, 19C no lactose. Reference recipes: 15B's Flaked Barley, the Mexican lager's
Flaked Corn, 26B's Brown Candi Sugar and 18A's Honey are named, and 5D's Tettnanger and 25B's
Saaz find a matching hop character.

---

## 1/26 · 10A Weissbier

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| esters | medium–high | banana, clove | "Moderate to strong esters and phenols, typically…" |
| phenols | medium–high | clove | "Moderate to strong esters and phenols, typically…" |
| malt | low–medium | bready | "Low to moderate soft, somewhat bready, doughy, o…" |
| fruit | low–medium-high | banana, clove | "Low to moderately strong banana and clove flavor…" |
| sweetness | very low–very low | – | "Low to moderate soft, somewhat bready, doughy, o…" |
| dryness | medium–medium | – | "Wellrounded, flavorful palate with a relatively…" |
| body | medium-low–medium | creamy | "Medium-light to medium body; never heavy. Fluffy…" |

Ingredients: none (all three were rejected by the code check).

**Problems:**
- Code: 3 ingredients rejected (two set both role and ingredient, one ingredient and tag).
- Clove is a phenol, not an ester. The *fruit* row is yeast banana/clove (R1). Body "creamy" (R2).
- Missing: hop aroma and hop flavour ("Light floral, spicy, or herbal hops optional"), and the
  weizen yeast and wheat malt.

**Unknown words:**

| Word | Resolution |
|---|---|
| doughy | new synonym `doughy → bready` |
| grainy, soft, fluffy, dry | drop: no grain tag / texture / intensity |

**Proposed fixes:**
1. esters `characters` = `["banana"]`.
2. phenols `characters` = `["clove", "vanilla"]` ("Light vanilla optional").
3. Remove the `fruit` row.
4. dryness `min`/`max` = `medium-high` ("relatively dry finish").
5. body `characters` = `[]`, quote = "Medium-light to medium body; never heavy."
6. Add hop_aroma none–low `["floral", "spicy", "herbal"]`, "Light floral, spicy, or herbal hops optional."
7. Add hop_flavour none–very low, same characters, "Very low floral, spicy, or herbal hop flavor optional."
8. Add `tag = "wheat"` (weizen yeast family), `required = true`.
9. Add `Weyermann|Wheat Malt Pale` and `Viking Malt|Wheat Malt`, not required ("at least half
   the grist" cannot be stored: `min_pct` only goes with a role).
10. Add `role = "base"` ("Pilsner malt.").

**Verdict:** ready after fixes.

## 2/26 · 11B Best Bitter

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| malt | low–medium | bready, biscuit | "Low to medium maltiness with a dry finish. The m…" |
| caramel | low–medium | caramel, toffee | "Low to moderate caramel or toffee flavors are op…" |
| hop_flavour | low–medium | earthy, resin, fruity, floral | "Moderate to low hop flavor, typically with an ea…" |
| hop_aroma | none–medium | floral, earthy, resin, fruity | "Hop aroma can range from moderate to none, typic…" |
| esters | medium-low–medium-high | fruity | "Moderately low to moderately high fruity esters." |
| dryness | medium–medium | – | "Low to medium maltiness with a dry finish." |
| body | medium-low–medium | – | "Medium-light to medium body." |

Ingredients: `pale ale malt`? req · `amber malt`? req · `crystal malt`? req · `sugar`? ·
`caramel malt`? · `dark malt`? · `corn`? · `wheat`? · tag `GB` · tag `british`? req (? = not resolved)

**Problems:**
- Code: none. Sensations are sound; dryness "dry finish" is too low (R3).
- 8 of 10 ingredients are unresolved names; the "or" list is marked required (R5).

**Unknown words:**

| Word | Resolution |
|---|---|
| lightly toasty | map to `toasty` (+ synonym `toast → toasty`) |
| pale ale malt, amber malt, crystal malt, caramel malt, dark malt | roles, fixes 2–3 |
| corn | ingredient `|Flaked Corn` |
| wheat | drop: wheat malt is a base malt, a row changes nothing |
| british | tag `english-ale` |
| sugar | Question A |
| dry | drop: intensity |

**Proposed fixes:**
1. dryness `min`/`max` = `high`.
2. Roles `base`, `kilned` (amber malt; `ref` has none), `crystal`, none required, "Pale ale, amber, or crystal malts."
3. Role `roast`, not required, "May use a touch of caramel or dark malt for color adjustment."
4. `ingredient = "|Flaked Corn"`, "May use corn or wheat."
5. `tag = "english-ale"`, not required, "Characterful British yeast."
6. "Most contain sugar": no row (Question A).

**Verdict:** needs your judgment on: Question A.

## 3/26 · 15A Irish Red Ale

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| malt | low–medium | toffee | "Low to moderate malt aroma, either neutral-grain…" |
| caramel | very low–medium | toffee | "Moderate to very little caramel malt flavor and…" |
| roast | low–low | – | "The palate often is fairly neutral and grainy, o…" |
| hop_aroma | none–low | earthy, floral | "Low earthy or floral hop aroma optional." |
| hop_flavour | none–low | earthy, floral | "A light earthy or floral hop flavor is optional." |
| sweetness | very low–medium | – | "Moderate to very little caramel malt flavor and…" |
| body | medium-low–medium | – | "Medium-light to medium body, although examples c…" |
| dryness | medium–high | – | "Medium-dry to dry finish." |
| esters | none–low | – | "Low esters optional." |

Ingredients: `roasted barley`? req · `Viking Malt|Black Malt` req · `pale base malt`? req · `caramel malts`?

**Problems:**
- Code: none. Caramel lists only toffee, so a crystal malt (tag caramel) gets half a match.
- Roast has no character. "roasted barley" exists twice in `ref` (Viking, Weyermann).
- "Generally has a bit of roasted barley or black malt" is not a must; both are marked required.

**Unknown words:**

| Word | Resolution |
|---|---|
| lightly caramel | map to `caramel` |
| toast | map to `toasty` (new synonym `toast → toasty`) |
| roasted grain | new synonym `roastedgrain → roast` |
| neutral-grainy | drop: no grain tag |
| roasted barley, pale base malt, caramel malt(s) | roles, fixes 5–6 |
| dry | drop: intensity |

**Proposed fixes:**
1. malt `characters` = `["caramel", "toasty", "toffee"]`.
2. caramel `characters` = `["caramel", "toffee"]`.
3. roast `characters` = `["roast"]` (low–low stays: "a light taste of roasted grain").
4. dryness `min` = `medium-high` ("Medium-dry to dry").
5. Roasted barley and Black Malt → one `role = "roast"`, not required.
6. `role = "base"` ("Pale base malt."); `role = "crystal"`, not required.

**Verdict:** ready after fixes.

## 4/26 · 15B Irish Stout

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| roast | medium–medium | roast, chocolate | "Moderate roasted grain or malt flavor with a med…" |
| sweetness | none–medium | caramel | "The finish can be dry and coffee-like to moderat…" |
| dryness | none–medium | – | "The finish can be dry and coffee-like to moderat…" |
| body | medium-low–medium | creamy | "Medium-light to medium-full body, with a somewha…" |
| esters | none–medium-low | – | "Medium-low esters optional." |
| hop_aroma | none–low | earthy, floral | "Low earthy or floral hop aroma optional." |
| hop_flavour | none–medium | earthy | "Balancing factors may include some creaminess, m…" |
| fruit | none–medium-low | – | "Balancing factors may include some creaminess, m…" |

Ingredients: `roasted barley`? · `pale malt`? · `unmalted grains`?

**Problems:**
- Code: none. Sweetness "a touch" is not medium; dryness "none" contradicts "dry"; body stops at
  medium but the text says medium-full; "creamy" and "caramel" break R2; *fruit* breaks R1.
- Missing: the required roast role (test A6). The reference recipe's 20 % Flaked Barley needs
  "unmalted grains" named, or it comes out ⚠️.
- Citra check holds: hop aroma earthy/floral max low, hop flavour earthy → Citra whirlpool ⚠️.

**Unknown words:**

| Word | Resolution |
|---|---|
| coffee-like | new synonym `coffeelike → coffee` |
| chocolaty, dark chocolate, unsweetened chocolate | synonyms `chocolaty`, `darkchocolate → chocolate` |
| roasted grain | synonym `roastedgrain → roast` |
| bittersweet, malty sweetness, moderately balanced | drop: taste/balance words |
| medium-light, medium-full, medium-low, dry | drop: intensity |
| roasted barley, pale malt, unmalted grains | roles, fixes 7–9 |

**Proposed fixes:**
1. roast `characters` = `["roast", "coffee", "chocolate"]`.
2. sweetness `max` = `low`, `characters` = `[]`.
3. dryness `min` = `medium`, `max` = `high`.
4. body `max` = `medium-high`, `characters` = `[]`.
5. esters `characters` = `["fruity"]` (takes over "medium-low fruitiness").
6. Remove the `fruit` row.
7. `role = "roast"`, `required = true`, "Dark roasted malts or grains, enough to make the beer black in color."
8. `role = "base"` ("Pale malt.").
9. `role = "adjunct"`, "May use unmalted grains for body."

**Verdict:** ready after fixes.

## 5/26 · 16A Sweet Stout

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| roast | medium–high | coffee, chocolate, roast | "Dark, roasted, coffee or chocolate flavors domin…" |
| sweetness | medium–high | – | "Medium to high sweetness provides a counterpoint…" |
| fruit | low–medium-high | – | "Fruitiness can be low to moderately high." |
| hop_aroma | low–low | floral, earthy | "Low floral or earthy hop aroma optional." |
| esters | low–medium | – | "Low to moderate fruity esters." |
| hop_flavour | low–low | floral, earthy | "Low floral or earthy hop flavor optional." |
| body | medium–high | creamy | "Medium-full to full-bodied and creamy." |

Ingredients: role `base` req · role `kilned` req · role `adjunct` · `|Lactose`

**Problems:**
- Code: none. *fruit* is yeast fruitiness (R1); body "creamy" (R2) would fail the reference
  recipe's Caramunich; body min is medium-full, not medium; the optional hops start at low.
- "dark malts or grains" is a roast role, not kilned.
- Lactose is named, so it is 👍 without an override (R8). ✔

**Unknown words:**

| Word | Resolution |
|---|---|
| fruitiness, fruity esters | new synonyms `fruitiness`, `fruityesters → fruity` |
| roasted grain | synonym `roastedgrain → roast` |
| dark, sweetness, residual sweetness, cream-like sweetness, full-bodied | drop: intensity |

**Proposed fixes:**
1. esters `min`–`max` = low–medium-high, `characters` = `["fruity"]`, quote "Fruitiness can be low to moderately high."
2. Remove the `fruit` row.
3. hop_aroma and hop_flavour `min` = `none` ("optional").
4. body = medium-high–high, `characters` = `[]`.
5. Role `kilned` → `roast` (required stays true).
6. "sugar adjuncts": no role `sugar` row (Question A); the adjunct role stays.

**Verdict:** needs your judgment on: Question A (under (b), honey in 16A is ⚠️).

## 6/26 · 16B Oatmeal Stout

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| malt | low–medium-high | earthy, floral | "Mild grainy, roasty, coffee-like character with…" |
| roast | low–medium | earthy, nutty | "Similar to the aroma, with a mild roasted coffee…" |
| fruit | low–medium-high | – | "Low to medium-high fruitiness." |
| hop_aroma | none–medium-low | earthy, floral | "Medium-low earthy or floral hop aroma optional." |
| hop_flavour | none–medium-low | earthy, floral | "Medium-low earthy or floral hop flavor optional." |
| sweetness | medium–medium | – | "Medium-sweet to medium-dry finish, which affects…" |
| dryness | medium–medium | – | "Medium-sweet to medium-dry finish, which affects…" |
| body | medium–high | creamy | "Medium-full to full body, with a smooth, silky,…" |

Ingredients: role `base` req · role `crystal` req · role `roast` req · `chocolate malts`? ·
`oatmeal`? req ≥5% · `malted oats`? req ≥5% · `brewing sugars`? · `syrups`? · tag `english-ale` req

**Problems:**
- Code: `min_pct` on two named products (only a role may carry it).
- Malt row: its quote is roast/coffee and "earthy, floral" are hop words; the text gives no malt level.
- Roast characters are wrong (earthy, nutty). *fruit* (R1); body "creamy" (R2).
- Roast stays low–medium although the text says "mild": the reference recipe (5 % chocolate +
  3 % roasted barley) has more roast than the 15B one, so 16B's max must not sit below 15B's.

**Unknown words:**

| Word | Resolution |
|---|---|
| roasty, roasted coffee | synonym `roasty → roast`; map to `roast`, `coffee` |
| coffee-like, milk chocolate | synonyms `coffeelike → coffee`, `milkchocolate → chocolate` |
| fruitiness | synonym `fruitiness → fruity` |
| grainy, grainy-nutty, toasty-nutty, coffee-and-cream, malty, malty sweetness, full, full-bodied, medium-full, smooth, silky, velvety, oily slickness, sweetness, dry | drop: oat/balance notes (malt row removed), intensity, texture |
| oatmeal, malted oats / chocolate malts | `|Flaked Oats` (malted oats is not in `ref`) / drop: role roast covers it |
| brewing sugars, syrups | Question A |

**Proposed fixes:**
1. Remove the `malt` row.
2. roast `characters` = `["roast", "coffee", "chocolate"]`.
3. `fruit` → esters low–medium-high `["fruity"]`.
4. sweetness and dryness = medium-low–medium-high ("Medium-sweet to medium-dry").
5. body = medium-high–high, `characters` = `[]`.
6. Role `crystal` `required = false`.
7. `ingredient = "|Flaked Oats"`, `required = true`, no `min_pct` (5 % cannot be stored on a product).
8. Remove "chocolate malts". 9. Remove "malted oats".
10. `english-ale` `required = false` (American versions exist).

**Verdict:** needs your judgment on: Question A; roast max medium (fix 2).

## 7/26 · 17C Wee Heavy

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| malt | high–high | – | "Strong bready-toasty malt, with a high caramel a…" |
| caramel | high–high | caramel, toffee, toasty | "Strong bready-toasty malt, with a high caramel a…" |
| roast | low–low | roast | "Faint hint of roast is sometimes noted." |
| esters | low–medium | dried-fruit | "Low to moderate dark or dried fruit esters and a…" |
| hop_aroma | very low–low | earthy, floral, spicy | "Very low earthy, floral, orange-citrus, or spicy…" |
| hop_flavour | medium-low–medium-low | – | "Medium-low hop flavor optional, with similar des…" |
| sweetness | medium–medium | – | "giving a sweet to medium-dry finish." |
| body | medium–high | creamy | "Medium-full to full-bodied, sometimes with a thi…" |
| dryness | medium–medium | – | "giving a sweet to medium-dry finish." |

Ingredients: `scottish pale ale malt`? req · `crystal malt`? · `darker grains`? · `peat-smoked malt`?

**Problems:**
- Code: none. Toasty is malt, not caramel. Hops are "Very low … optional" (max very low);
  hop flavour "optional" starts at none and has the aroma's descriptors. Body "creamy" (R2).
- "No peat-smoked malt" is a ban, not an ingredient. Smoke is a specialty sensation and 17C is
  silent on it, so smoked malt is already ⚠️.
- "including adjuncts" is not extracted. Honey is a sugar, so b19's honey stays ⚠️ (R8). ✔

**Unknown words:**

| Word | Resolution |
|---|---|
| bready-toasty, toasty bread, toasted breadcrumbs | map to `bready`, `toasty` |
| english biscuits, graham crackers, ladyfingers | map to `biscuit` (+ synonym `cracker → biscuit`) |
| caramelized sugar, butterscotch | synonyms `caramelizedsugar → caramel`, `butterscotch → toffee` |
| plums, dark or dried fruit esters / orange-citrus / grainy roast | synonym `plums → dried-fruit` / map to `orange` / map to `roast` |
| nougat, sweet, medium-dry, full-bodied, chewy, thick | drop: no tag fits / intensity / texture |
| scottish pale ale malt, crystal malt, darker grains | roles, fix 6 |

**Proposed fixes:**
1. malt `characters` = `["bready", "toasty", "biscuit"]`.
2. caramel `characters` = `["caramel", "toffee"]`.
3. roast `min` = `none` (max low stays: b19 has 2 % roasted barley).
4. hop_aroma = none–very low `["earthy", "floral", "orange", "spicy"]`; hop_flavour = none–medium-low, same characters.
5. sweetness = medium-low–high, dryness = low–medium-high ("sweet to medium-dry"); body = medium-high–high, `characters` = `[]`.
6. Roles `base` ("Scottish pale ale malt"), `adjunct` ("including adjuncts"), `crystal`, `roast`; none required.
7. Remove "peat-smoked malt".

**Verdict:** ready after fixes.

## 8/26 · 18B American Pale Ale

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| hop_aroma | medium–medium-high | citrus, floral, pine, resin, tropical, stone-fruit, berry, melon | "Moderate to moderately-high hop aroma from Ameri…" |
| malt | low–medium | bready, biscuit, caramel | "Low to moderate neutral to grainy maltiness supp…" |
| esters | none–medium | fruity | "Fruity esters optional, up to moderate in streng…" |
| caramel | none–low | caramel | "Caramel flavors are often absent or fairly restr…" |
| fruit | none–medium | fruity | "Fruity yeast esters can be moderate to none, alt…" |
| dryness | medium–medium | – | "Medium to dry finish." |
| body | medium-low–medium | – | "Medium-light to medium body." |

Ingredients: `neutral pale malt`? req · tag `US` req · tag `ale` req · `specialty malts`? req

**Problems:**
- Code: none. Missing hop flavour ("same intensities and descriptors apply"): without it a
  10-minute hop is never checked. *fruit* duplicates esters (R1). Dryness (R3).
- Missing phenols none (Question B). All four ingredients marked required; "New World" hops missing.
- No rice is named, so b16's Flaked Rice stays ⚠️ (R8). ✔

**Unknown words:**

| Word | Resolution |
|---|---|
| spice | new synonym `spice → spicy` |
| toast | synonym `toast → toasty` |
| neutral, grainy, medium, medium-light, dry | drop: no tag / intensity |
| neutral pale malt, specialty malts | roles, fix 6 |

**Proposed fixes:**
1. hop_aroma `characters` + `spicy`; malt `characters` + `toasty`.
2. Add hop_flavour medium–medium-high, same list, "Hop and malt character similar to aroma (same intensities and descriptors apply)."
3. Remove the `fruit` row.
4. Add phenols none–none, "Clean fermentation profile." (Question B).
5. dryness = medium–high ("Medium to dry").
6. `role = "base"` ("Neutral pale malt."), `role = "crystal"` ("Small amounts of various specialty malts."), not required.
7. Remove the two unresolved names.
8. Tags `US`, `NZ`, `AU`, not required.
9. Tag `ale` → `american-ale` and `english-ale`, not required.

**Verdict:** ready after fixes. (The hop list makes Cascade 👍; a hop with only earthy/grassy tags comes out ⚠️, although the text says none of the listed characters is required.)

## 9/26 · 19C American Brown Ale

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| malt | medium–medium-high | chocolate, caramel, nutty, toasty | "Medium to moderately-high malty-sweet or maltyri…" |
| caramel | medium–medium-high | chocolate, caramel | "Medium to moderately-high malty-sweet or maltyri…" |
| roast | medium–medium-high | chocolate | "Medium to moderately-high malty-sweet or maltyri…" |
| hop_flavour | low–medium | citrus, fruity, tropical | "Light to moderate hop flavor, sometimes citrusy,…" |
| hop_aroma | low–medium | citrus, fruity, tropical | "Hop aroma is typically low to moderate, of almos…" |
| esters | very low–medium | fruity | "Very low to moderate fruity esters." |
| body | medium–medium-high | – | "Medium to medium-full body." |
| dryness | medium–medium | – | "Medium to medium-dry finish with an aftertaste o…" |

Ingredients: `pale malt`? req · `|Crystal` req · `darker malts`? req · `chocolate`? ·
`American hops`? · `continental hops`? · `New World hops`?

**Problems:**
- Code: none, but `|Crystal` resolved to **the hop Crystal**, not crystal malt.
- Roast medium–medium-high comes from the general malt sentence; the text says "Should not have
  a roasted character suggestive of a Porter or Stout." Chocolate is not a caramel character.
- Hops: "of almost any type that complements the malt" (R4), so no fixed character list.
- No lactose is named, so b20's lactose stays ⚠️ (R8). ✔

**Unknown words:**

| Word | Resolution |
|---|---|
| malty-sweet, malty-rich | drop: intensity |
| pale malt, darker malts | roles, fix 5 |
| chocolate | drop: covered by role roast |
| American / continental / New World hops | tag `US`; the others drop (naming changes nothing) |

**Proposed fixes:**
1. caramel `characters` = `["caramel"]`.
2. roast = low–medium `["chocolate"]`, quote "Should not have a roasted character suggestive of a Porter or Stout."
3. hop_flavour and hop_aroma `characters` = `[]`.
4. dryness = medium–medium-high.
5. Roles `base`, `crystal` (replaces the hop), `roast`; none required.
6. Remove "chocolate".
7. Tag `US`, not required; remove the other two hop names.

**Verdict:** needs your judgment on: the roast range in fix 2 (my reading; the text gives no level word).

## 10/26 · 1B American Lager

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| malt | low–medium-low | – | "Relatively neutral palate with a crisp, dry fini…" |
| hop_aroma | none–low | spicy, floral | "Light spicy or floral hop aroma optional." |
| hop_flavour | none–medium-low | floral, spicy, herbal | "Moderately low hop flavor optional, with a flora…" |
| dryness | high–high | – | "Relatively neutral palate with a crisp, dry fini…" |
| body | low–medium-low | – | "Low to medium-low body." |

Ingredients: `two- or six-row barley`? req · `rice`? · `corn`? · `lager yeast`? req

**Problems:**
- Code: none. Sensations are sound. Missing esters and phenols (Question B).
- Rice and corn must be named as products: the test needs `Flaked Rice` (R8, b06).

**Unknown words:**

| Word | Resolution |
|---|---|
| grainy, sweet, corn-like | drop: no grain or corn tag (corn is named as an ingredient) |
| dry | drop: intensity |
| two- or six-row barley | role `base` |
| rice, corn | `|Flaked Rice`, `|Flaked Corn` |
| lager yeast | tag `lager` |

**Proposed fixes:**
1. Add esters none–low ("While a clean fermentation profile is desirable, a light amount of yeast character is not a fault.") and phenols none–none ("Clean fermentation profile.").
2. `role = "base"`, not required.
3. `|Flaked Rice` and `|Flaked Corn`, not required ("up to 40 %" is a maximum, which cannot be stored).
4. `tag = "lager"`, `required = true`.

**Verdict:** ready after fixes.

## 11/26 · 1C Cream Ale

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| malt | low–medium-low | – | "Medium-low to low malt notes, with a sweet, corn…" |
| hop_aroma | none–medium-low | floral, spicy, herbal | "Medium-low hop aroma optional, using any variety…" |
| esters | none–low | fruity | "Low fruity esters optional." |
| sweetness | low–medium | – | "Low to moderate malty sweetness, varying with gr…" |
| fruit | low–medium | – | "A low to moderate corny flavor is commonly found" |
| hop_flavour | low–medium-low | floral, spicy, herbal | "Low to medium-low hop flavor of any variety, but…" |
| body | low–medium | – | "Generally light and crisp, although body can rea…" |
| dryness | low–medium | – | "Finish can vary from somewhat light, dry, and cr…" |

Ingredients: `American six-row malt`? req · `North American two-row`? · `maize`? · `sugar`? ·
`rustic American`? · `Continental`? · `Clean ale yeast`? req

**Problems:**
- Code: none. The *fruit* row is corn flavour, not fruit (R1). Dryness "dry … to faintly sweet"
  spans more than low–medium (R3). Missing phenols (Question B).
- Maize must be `Flaked Corn` (R8, b07).

**Unknown words:**

| Word | Resolution |
|---|---|
| crackery | new synonym `crackery → biscuit` (for later styles; not on this row's quote) |
| sweet, corn-like, corny, grainy, neutral, malty | drop: no grain or corn tag |
| light, crisp, smooth, dry, faintly sweet | drop: intensity/texture |
| American six-row malt, North American two-row | role `base` |
| maize | `|Flaked Corn` |
| rustic American, Continental | tag `US` |
| Clean ale yeast | tag `ale` |
| sugar | Question A |

**Proposed fixes:**
1. Remove the `fruit` row.
2. Add phenols none–none, "Clean fermentation profile, but low fruity esters are optional."
3. dryness = medium-low–high.
4. One `role = "base"`, not required.
5. `|Flaked Corn`, "Up to 20% maize in the mash".
6. Tag `US`, not required.
7. Tag `ale`, not required ("or a mix of ale and lager").
8. "up to 20% sugar in the boil": no row (Question A).

**Verdict:** needs your judgment on: Question A.

## 12/26 · 21A American IPA

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| hop_aroma | high–very high | citrus, floral, pine, resin, tropical, stone-fruit, berry, melon | "A prominent to intense hop aroma often featuring…" |
| malt | low–medium-low | – | "Low to medium-low clean, grainy maltiness suppor…" |
| fruit | none–low | – | "Generally clean fermentation profile, but light…" |
| hop_flavour | medium–very high | citrus, floral, pine, resin, tropical, stone-fruit, berry, melon | "Medium to very high hop flavor (same descriptors…" |
| caramel | none–low | – | "Low to medium-low clean and grainy maltiness, po…" |
| roast | none–low | – | "Low to medium-low clean and grainy maltiness, po…" |
| dryness | medium–medium | – | "Dry to medium-dry finish." |
| esters | none–low | – | "Low esters optional." |
| body | medium-low–medium | – | "Medium-light to medium body, with a smooth textu…" |

Ingredients: `pale base malt`? req · tag `american`? req · role `sugar` · role `crystal` · tag `US`

**Problems:**
- Code: none. *fruit* duplicates esters (R1). The roast row's quote is about toast; the text says
  nothing about roast (silence is fine; the colour range still catches a black IPA).
- Missing "spice" in the hop lists, the caramel character, phenols (Question B).
- Brett yeast: 21A is silent on brett funk, so it comes out ⛔ (golden case). ✔

**Unknown words:**

| Word | Resolution |
|---|---|
| spice / light caramel | new synonym `spice → spicy` / map to `caramel` |
| toast, clean, grainy, light fruitiness | drop: malt not caramel (synonym `toast → toasty` for later) / no tag / covered by esters |
| pale base malt / american | role `base` / tags `american-ale`, `english-ale` |

**Proposed fixes:**
1. hop_aroma and hop_flavour `characters` + `spicy`.
2. Remove the `fruit` row.
3. caramel `characters` = `["caramel"]`.
4. Remove the `roast` row.
5. dryness = medium-high–high.
6. Add phenols none–none, "Generally clean fermentation profile, but light fruitiness acceptable."
7. `role = "base"`, not required.
8. Tags `american-ale`, `english-ale`, not required.
9. Tags `US`, `NZ`, `AU`, not required. Role `sugar` ("sugar additions") removed (Question A).

**Verdict:** needs your judgment on: Question A. (The hop list is kept so Citra is 👍; the text
also says "any varieties are acceptable", so a purely earthy hop showing ⚠️ is a known edge.)

## 13/26 · 21C Hazy IPA

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| hop_aroma | very high–very high | stone-fruit, tropical, citrus, fruity | "Intense hop aroma, with stone fruit, tropical fr…" |
| malt | low–medium | – | "Low to medium malt flavor, same descriptors as a…" |
| esters | none–medium | fruity | "Neutral to fruity fermentation profile, supporti…" |
| hop_flavour | high–very high | fruity | "High to very high fruity hop flavor, same descri…" |
| dryness | low–medium | – | "often masked by the fuller body and soft, off-dr…" |
| body | medium–medium | – | "Medium to medium-full body." |

Ingredients: `flaked grains`? req · `caramel or specialty malts`? · `American or New World hops`? req ·
`Neutral to estery yeast`? req · `chloride-rich water`?

**Problems:**
- Code: none. Hop flavour lists only "fruity" although "same descriptors as aroma": Citra (citrus)
  would get half a match (➖). Body stops at medium; text says medium-full.
- Missing caramel none ("no caramel or toast"). Water is not an ingredient row.
- "flaked grains" must become products: the test needs `Flaked Oats` (R8, b02).

**Unknown words:**

| Word | Resolution |
|---|---|
| lightly bready | map to `bready` |
| grainy, fuller, soft, medium, off-dry | drop: no tag / intensity |
| flaked grains | `|Flaked Oats`, `|Flaked Barley` (fix 5) |
| American or New World hops | tags `US`, `NZ`, `AU` |
| Neutral to estery yeast | tag `ale` |
| caramel or specialty malts, chloride-rich water | drop: "less" of them / not an ingredient |

**Proposed fixes:**
1. hop_aroma `min` = `high`; malt `characters` = `["bready"]`.
2. hop_flavour `characters` = aroma's list.
3. Add caramel none–none, "Clean, neutral, grainy, or lightly bready malt in the background; no caramel or toast."
4. dryness = medium-low–medium; body `max` = `medium-high`.
5. `|Flaked Oats` and `|Flaked Barley`, not required (alternative: `role = "adjunct"`, which also
   makes Flaked Rice and Corn 👍, but then the test's "names Flaked Oats" needs rewording).
6. Tags `US`, `NZ`, `AU`, not required.
7. Tag `ale`, not required.
8. Remove "caramel or specialty malts" and "chloride-rich water".

**Verdict:** needs your judgment on: fix 5 (two named flakes vs the adjunct role).

## 14/26 · 23A Berliner Weisse

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| sourness | medium–medium-high | – | "A moderate to moderately-high sharply sour chara…" |
| fruit | none–medium | lemon, floral, fruity, honey | "Can have up to a moderately fruitiness, often le…" |
| malt | low–medium | bready | "A light bread dough malt flavor supports the sou…" |
| dryness | high–high | – | "Very dry finish." |
| body | low–low | – | "Light body, but never thin." |
| brett_funk | none–low | fruity, floral, funky | "Any Brett character is restrained, and is typica…" |

Ingredients: `Pilsner malt`? req · `Viking Malt|Wheat Malt` · `top-fermenting yeast`? req · `LAB`? req · `Brett`? req

**Problems:**
- Code: none. Fruitiness here comes from fermentation (fruited versions are 29A), so esters (R1).
- Brett lists "funky" although the text says "not funky". Malt "light" is low, not medium.
- Missing "No hop aroma." and "No hop flavor." (dry hopping should show ⚠️).

**Unknown words:**

| Word | Resolution |
|---|---|
| tart apple, apricot, peach, apricot-peach, citrus-lemon | synonyms `apple`, `apricot`, `peach`; map to `orchard-fruit`, `stone-fruit`, `lemon` |
| fruitiness | synonym `fruitiness → fruity` |
| hay, gentle wildflower, cider | aged notes, not on this row's quote: drop (synonym `hay → grassy` for later) |
| bread dough, raw bread dough, sourdough bread, doughy | map to `bready` (+ synonym `doughy`) |
| grainy, light, very dry, restrained | drop: no tag / intensity |
| sharply sour, lactic sourness, crisp acidity | drop: the sourness row already says it |
| Pilsner malt / top-fermenting yeast / LAB / Brett | role `base` / tags `ale`, `sour`, `brett` |

**Proposed fixes:**
1. `fruit` → esters none–medium `["lemon", "orchard-fruit", "stone-fruit", "floral"]`.
2. malt `max` = `low`.
3. dryness = very high.
4. brett_funk `characters` = `["fruity", "floral"]`.
5. Add hop_aroma none–none ("No hop aroma.") and hop_flavour none–none ("No hop flavor.").
6. `role = "base"`; add `Weyermann|Wheat Malt Pale` next to the Viking one.
7. Tags `ale`, `sour`, `brett`, none required.

**Verdict:** ready after fixes.

## 15/26 · 25B Saison

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| esters | medium–high | stone-fruit | "The fruity esters are moderate to high, and ofte…" |
| spice | low–medium-high | – | "Low to moderately-high spicy notes are often lik…" |
| hop_aroma | low–medium | spicy, floral, earthy, fruity | "Hops are low to moderate and have a continental…" |
| malt | low–medium | – | "Malt is low to medium, with a soft, grainy palat…" |
| hop_flavour | low–medium | spicy, floral, earthy, fruity | "hop flavor is low to medium, both with similar c…" |
| dryness | very high–very high | – | "Very high attenuation, never with a sweet or hea…" |
| body | low–medium | – | "Light to medium-low body." |
| sourness | low–medium | – | "Sourness is totally optional, and if present at…" |

Ingredients: 9 unresolved names (`pale base malt`, `wheat`, `oats`, `spelt`, `rye`,
`sugary adjuncts`, `continental hops` req, `spicy-fruity Belgian Saison yeast` req, `spices and herbs`)

**Problems:**
- Code: none. The "black pepper" row is yeast phenols, not added spice (R1); the real spice row
  ("Spices and herbs … allowable") is missing. Body max is medium-low per its quote.
- The reference recipe's Saaz (tagged *herbal* only) at 10 min would be ⚠️ wrong character:
  "continental character (spicy, floral, earthy, or fruity)" does not list herbal.

**Unknown words:**

| Word | Resolution |
|---|---|
| black pepper / citrus fruit / pome fruit | synonyms `blackpepper → pepper` / `citrusfruit → citrus` / `pomefruit → orchard-fruit` |
| lightly grainy | drop: no grain tag |
| pale base malt / wheat, oats, spelt, rye | role `base` / role `adjunct` (the flakes; the malts need no row) |
| continental hops / Saison yeast / spices and herbs | tags `DE`, `CZ`, `SI`, `FR` / tag `saison` / the new spice row (fix 3) |
| sugary adjuncts | Question A |

**Proposed fixes:**
1. esters `characters` = `["citrus", "orchard-fruit", "stone-fruit"]`.
2. `spice` row → phenols low–medium-high `["pepper"]` ("not clove": a clove yeast gets ⚠️).
3. Add spice none–low, "Spices and herbs are uncommon, but allowable if they don't dominate."
4. hop_aroma and hop_flavour `characters` + `herbal` (judgment: herbal is a continental trait).
5. body `max` = `medium-low`.
6. sourness `min` = `none`.
7. `role = "base"`. 8. `role = "adjunct"`, "Cereal grains, such as wheat, oats, spelt, or rye."
9. Tags `DE`, `CZ`, `SI`, `FR`, not required.
10. `tag = "saison"`, `required = true`.

**Verdict:** needs your judgment on: Question A; fix 4 (or accept Saaz as a listed exception).

## 16/26 · 26B Belgian Dubbel

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| malt | medium–medium-high | chocolate | "Moderate to moderately strong, rich malty aroma,…" |
| caramel | medium–medium | – | "Moderate to moderately strong, rich malty aroma,…" |
| roast | medium–medium | chocolate | "Moderate to moderately strong, rich malty aroma,…" |
| esters | medium–medium | dried-fruit, banana | "Moderate fruity esters, often dark or dried frui…" |
| phenols | low–medium | spicy, pepper | "Low to moderate spicy, peppery phenols." |
| hop_flavour | none–low | spicy, herbal, floral | "Hops typically absent, but can have a low spicy,…" |
| hop_aroma | none–low | spicy, herbal, floral | "Hops typically absent, but can have a low spicy,…" |
| sweetness | low–medium | – | "Can taste somewhat sweet due to restrained bitte…" |
| body | medium–medium-high | – | "Smooth, medium to medium-full body." |
| dryness | medium–medium | – | "Malty-rich, sometimes sweet flavor, that finishe…" |

Ingredients: `caramelized sugar syrup`? · `unrefined sugars`? · `Belgian yeast`? req · `Continental hops`? req

**Problems:**
- Code: none. Roast "medium" contradicts "Never roasted or burnt." Caramel is "hints", not medium.
- The reference recipe uses 10 % Brown Candi Sugar: unless named it comes out ⚠️ (R9).

**Unknown words:**

| Word | Resolution |
|---|---|
| caramelized sugar | synonym `caramelizedsugar → caramel` |
| toast | synonym `toast → toasty` |
| plums, dark or dried fruit | synonym `plums → dried-fruit` |
| pome fruit | synonym `pomefruit → orchard-fruit` |
| rich malty, malty-rich, malty aftertaste, sweet | drop: intensity |
| fairly dry, moderately dry, medium to medium-full | drop: intensity |
| caramelized sugar syrup, unrefined sugars | `|Brown Candi Sugar` |
| Belgian yeast / Continental hops | tag `belgian` / tags `DE`, `CZ`, `SI` |

**Proposed fixes:**
1. malt `characters` = `["chocolate", "caramel", "toasty"]`.
2. caramel = low–low `["caramel"]`.
3. roast = none–none, `characters` = `[]`, quote "Never roasted or burnt."
4. esters `characters` = `["dried-fruit", "orchard-fruit", "banana"]`.
5. dryness = medium-high ("moderately dry").
6. `|Brown Candi Sugar`, "with caramelized sugar syrup or unrefined sugars and yeast providing much of the complexity".
7. `tag = "belgian"`, `required = true`.
8. Tags `DE`, `CZ`, `SI`, not required.

**Verdict:** ready after fixes.

## 17/26 · 31B Alternative Sugar Beer

**Envelope now:** empty (no sensations, no ingredients; the model found nothing in 3 s).

**Problems:**
- The text says "Same as the base beer" for every sensation and "Characteristic ingredients: -".
- Tests need: 31B names the role `sugar` or Honey (R8, b12 honey not ⚠️).
- The Task 5 test wants ≥ 1 sensory row per style; 31B has none the text supports (Question C).

**Unknown words:** none.

**Proposed fixes** (hand entries, a proposal):
1. `role = "sugar"`, `required = true`, "A tasteful integration of sugar and beer, but still recognizable as beer." (Any sugar is the point of the style; the text names honey, molasses and unfermentable sugars.)
2. `|Honey`, not required, "Same as the base beer, except that some additional fermentables (e.g., honey, molasses) may add a flavor, which should be a pleasant, balanced combination with the beer."
3. No sensory rows (Question C (b)).

**Verdict:** needs your judgment on: Question C.

## 18/26 · 5D German Pils

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| hop_aroma | medium–medium-high | spicy, herbal | "Moderate to moderately-high flowery, spicy, or h…" |
| malt | low–medium | honey | "Low to medium grainy, sweet, or doughy malt char…" |
| hop_flavour | medium–medium-high | spicy, herbal | "Malt and hop flavors similar to aroma (same desc…" |
| dryness | high–high | – | "leading into a dry, crisp finish." |
| body | medium-low–medium-low | – | "Medium-light body." |

Ingredients: `Continental Pilsner malt`? req · `Traditional German hops`? req · `Clean German lager yeast`? req

**Problems:**
- Code: none. "flowery" was left unknown, so floral is missing: the reference recipe's
  Tettnanger (tagged floral only) in the whirlpool would be ⚠️.
- Missing esters and phenols (Question B).

**Unknown words:**

| Word | Resolution |
|---|---|
| flowery | new synonym `flowery → floral` |
| doughy, toasted cracker | synonyms `doughy → bready`, `cracker → biscuit` |
| grainy, sweet, crisp, dry, medium-light | drop: no tag / intensity |
| Continental Pilsner malt / German hops / lager yeast | role `base` / tag `DE` / tag `lager` |

**Proposed fixes:**
1. hop_aroma and hop_flavour `characters` = `["floral", "spicy", "herbal"]`.
2. malt `characters` = `["honey", "bready", "biscuit"]`.
3. Add esters none–very low and phenols none–none, "Clean fermentation profile."
4. `role = "base"`. 5. Tag `DE`, not required. 6. Tag `lager`, `required = true`.

**Verdict:** ready after fixes.

## 19/26 · 6A Märzen

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| malt | medium–high | bready, toasty | "Moderate to high rich malt flavor often initiall…" |
| hop_aroma | none–very low | floral, herbal, spicy | "Very low floral, herbal, or spicy hop aroma opti…" |
| hop_flavour | none–low | floral, herbal, spicy | "a low floral, herbal, or spicy hop flavor is opt…" |
| dryness | medium–high | – | "the finish is moderately-dry to dry" |
| body | medium–medium | creamy | "Medium body, with a smooth, creamy texture that…" |

Ingredients: `Munich malt`?

**Problems:**
- Code: none. Body "creamy" (R2). Dryness min (R3).
- Missing: "Noticeable sweet caramel, dry biscuit, or roasted flavors are inappropriate" (caramel
  and roast none), and esters/phenols (Question B; "Clean lager fermentation character").

**Unknown words:**

| Word | Resolution |
|---|---|
| somewhat toasty, light bread crust | map to `toasty`, `bready` (already listed) |
| rich, complex, elegant | drop: praise, not a flavour |
| smooth, fuller, medium, moderately-dry, dry, without a sweet or cloying impression | drop: intensity/texture |
| Munich malt | role `kilned` |

**Proposed fixes:**
1. dryness `min` = `medium-high`.
2. body `characters` = `[]`.
3. Add caramel none–none and roast none–none, "Noticeable sweet caramel, dry biscuit, or roasted flavors are inappropriate."
4. Add esters none–very low and phenols none–none, "Clean lager fermentation character."
5. `role = "kilned"`, not required.

**Verdict:** ready after fixes.

## 20/26 · 8B Schwarzbier

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| malt | low–medium | roast, bready, coffee | "Light to moderate malt flavor, which can have a…" |
| roast | low–medium | roast, coffee | "Light to moderate roasted malt flavors can give…" |
| caramel | none–very low | – | "The malt can be clean and neutral or moderately…" |
| hop_flavour | low–medium | spicy, floral, herbal | "Light to moderate spicy, floral, or herbal hop f…" |
| hop_aroma | none–medium-low | spicy, floral, herbal | "A moderately low spicy, floral, or herbal hop ar…" |
| dryness | medium–medium | – | "Dry finish." |
| sweetness | none–low | – | "Some residual sweetness is acceptable but not tr…" |
| body | medium-low–medium | – | "Medium-light to medium body." |

Ingredients: `German Munich malt`? req · `Pilsner malts`? req · `huskless dark roasted malts`? req · tag `DE` · tag `lager`

**Problems:**
- Code: none. Roast and coffee sit under malt. "Dry finish" is high (R3).
- Missing esters/phenols (Question B; "Clean lager character.").

**Unknown words:**

| Word | Resolution |
|---|---|
| dark chocolate | synonym `darkchocolate → chocolate` |
| dark caramel | map to `caramel` |
| roastiness | map to `roast` |
| malt, smooth, medium, medium-light, dry, residual sweetness | drop: intensity |
| German Munich malt / Pilsner malts / huskless dark roasted malts | roles `kilned` / `base` / `roast` |

**Proposed fixes:**
1. malt `characters` = `["bready"]`.
2. roast `characters` = `["roast", "coffee", "chocolate"]`.
3. caramel `characters` = `["caramel"]`.
4. dryness = high.
5. Add esters none–very low and phenols none–none, "Clean lager character."
6. Roles `kilned`, `base` (not required) and `roast` (`required = true`), one quote: "German Munich malt and Pilsner malts for the base, with huskless dark roasted malts that add roast flavors without burnt flavors."

**Verdict:** ready after fixes.

## 21/26 · Mexican-Style Amber Lager (BA)

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| malt | medium-low–medium-high | caramel, bready | "Medium-low to medium-high caramel and bready mal…" |
| roast | low–low | – | "light roast and light corn and/or rice flavors m…" |
| hop_flavour | none–low | – | "None to low with attributes typical of noble-typ…" |
| body | low–medium-low | – | "Light to medium-light body with light creaminess" |
| dryness | medium–medium | – | "Medium to medium-high carbonation with a dry fin…" |
| esters | none–low | fruity | "low fruity esters may be present" |

Ingredients: `corn`? · `rice`? · `specialty malts`?

**Problems:**
- Code: none. Caramel sits inside malt: a caramel row is missing (the reference recipe has
  Caramunich). Hop aroma is missing (the BA aroma field has the same "None to low" sentence).
- The reference recipe's 15 % Flaked Corn must be named (R9). Missing phenols (Question B).

**Unknown words:**

| Word | Resolution |
|---|---|
| typical of noble-type hops | drop: not a character word (lists stay empty) |
| light, light creaminess, dry | drop: intensity/texture |
| corn, rice | `|Flaked Corn`, `|Flaked Rice` |
| specialty malts | role `crystal` |

**Proposed fixes:**
1. malt `characters` = `["bready"]`; add caramel medium-low–medium-high `["caramel"]`, same quote.
2. Add hop_aroma none–low, same quote as hop flavour.
3. dryness = high.
4. Add phenols none–none, "Clean fermentation profile; low fruity esters may be present; sulfur may be present at very low levels."
5. `|Flaked Corn` and `|Flaked Rice`, "The presence of corn and/or rice to lighten body may be noticeable."
6. `role = "crystal"` (specialty malts).
7. Remove the three unresolved names.

**Verdict:** ready after fixes.

## 22/26 · Session India Pale Ale (BA)

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| malt | low–medium | – | "A low to medium maltiness should be present in a…" |
| hop_aroma | medium–high | – | "Hop aroma and flavor are medium to high, exhibit…" |
| hop_flavour | medium–high | – | "Hop aroma and flavor are medium to high, exhibit…" |
| body | low–medium | – | "Mouthfeel: Low to medium" |
| esters | low–medium | fruity | "Fruity esters are low to medium." |

Ingredients: none.

**Problems:**
- Code: none. The body quote includes the label "Mouthfeel:", which is not part of the guideline text.
- The BA text names no ingredients; the Task 5 test wants ≥ 1 per style. And nothing names
  adjuncts, so oats in a hazy session IPA would be ⚠️, although the text says it follows the
  underlying IPA style.

**Unknown words:**

| Word | Resolution |
|---|---|
| wide range of attributes, assertive, maltiness | drop: no character (hop lists stay empty, R4) |

**Proposed fixes:**
1. body quote = "Low to medium".
2. `role = "base"`, not required, "A low to medium maltiness should be present in aroma and flavor." (only to satisfy the test; the text names no ingredient).

**Verdict:** needs your judgment on: fix 2, and whether oats should be allowed (that needs a role row the text does not give).

## 23/26 · 20C Imperial Stout

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| roast | low–medium | roast, coffee, chocolate | "Light to moderately strong roast can have a coff…" |
| caramel | low–low | – | "sometimes with a light caramel sweetness or toas…" |
| esters | low–medium | dried-fruit | "Low to moderately strong esters often perceived…" |
| hop_aroma | very low–medium-high | – | "Very low to fairly aggressive hops, often Englis…" |
| malt | medium–medium | bready, caramel | "The maltiness balances and supports the other fl…" |
| dryness | low–medium | – | "The palate and finish can be fairly dry to moder…" |
| body | high–very high | – | "Full to very full-bodied and chewy, with a velve…" |

Ingredients: role `base` req · role `roast` req · role `adjunct` · tag `ale` · tag `US`

**Problems:**
- Code: none. "moderately strong" is medium-high, not medium (roast and esters). "fairly dry" is
  medium-high (R3). Hop flavour missing ("same descriptors apply"). English hops missing.

**Unknown words:**

| Word | Resolution |
|---|---|
| dark chocolate / slightly burnt grain, tar | synonyms `darkchocolate → chocolate`, `burnt → acrid`; map to `acrid` |
| plums, prunes, figs, dark or dried fruits | synonyms `plums`, `prunes`, `figs → dried-fruit` |
| black currants | synonym `blackcurrants → berry` |
| caramel sweetness / toast, toasty maltiness | map to `caramel` / `toasty` |
| black licorice, bittersweet | drop: no tag fits |
| English, American | drop: origins, not characters (tags `GB`, `US` as ingredients) |
| full, very full, chewy, velvety, luscious, fairly dry, moderately sweet | drop: intensity/texture |

**Proposed fixes:**
1. roast `max` = `medium-high`, `characters` + `acrid` ("slightly burnt grain").
2. caramel `characters` = `["caramel"]`.
3. esters `max` = `medium-high`, `characters` = `["dried-fruit", "berry"]`.
4. Add hop_flavour very low–medium-high, "Like the aroma, a complex mix of roast, fruit, hops, and alcohol (same descriptors apply)."
5. malt `characters` + `toasty`.
6. dryness `max` = `medium-high`.
7. Add tag `GB`, not required.

**Verdict:** ready after fixes.

## 24/26 · 18A Blonde Ale

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| malt | low–medium | bready, caramel, biscuit | "Light to moderate malty aroma, generally neutral…" |
| caramel | none–low | caramel, honey | "Caramel flavors usually absent; if present, they…" |
| fruit | low–medium | fruity | "Low to medium fruity esters optional, but are we…" |
| hop_aroma | low–medium | citrus, floral, fruity, spicy | "May have a low to medium hop aroma, and can refl…" |
| hop_flavour | low–medium | – | "Light to moderate hop flavor (any variety), but…" |
| body | medium-low–medium | – | "Medium-light to medium body." |
| dryness | low–medium | – | "Finishes medium-dry to slightly malty; an impres…" |

Ingredients: `Viking Malt|Wheat Malt` · `sugar adjuncts`? · `Kölsch yeast`? · `lager yeast`?

**Problems:**
- Code: none. *fruit* is yeast esters (R1). Malt lists caramel and biscuit, which its quote does
  not say. Dryness "medium-dry to slightly malty" (R3). Missing phenols (Question B).
- The b12 reference recipe is 18A with 12 % Honey: unless Honey is named, R9 fails.

**Unknown words:**

| Word | Resolution |
|---|---|
| toast, grainy, wheat | drop on this row (not in its quote); synonym `toast → toasty` |
| sugar adjuncts | `|Honey` (Question A (b)) |
| Kölsch yeast / lager yeast | tag `ale` (Kölsch is family ale) / tag `lager` |

**Proposed fixes:**
1. malt `characters` = `["bready"]`.
2. esters none–medium `["fruity"]`, "Low to medium fruity esters optional, but are welcome."
3. Remove the `fruit` row.
4. hop_aroma `min` = `none` ("May have").
5. dryness = medium-low–medium-high.
6. Add phenols none–none, "Clean fermentation profile."
7. Add `Weyermann|Wheat Malt Pale` next to the Viking one.
8. `|Honey`, "Generally all-malt, but can include wheat malt or sugar adjuncts."
9. Tags `american-ale`, `english-ale`, `ale`, `lager`, none required.

**Verdict:** needs your judgment on: Question A (fix 8 is what keeps b12's honey in style).

## 25/26 · Specialty Honey Beer (BA)

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| sweetness | low–medium | honey | "Honey character should be present in aroma and f…" |

Ingredients: `|Honey` req · `malted barley`? req

**Problems:**
- Code: none. The only sensation row is honey *character*, not sweetness, and "low–medium" is
  not in the text ("Varies depending on intention of brewer Very low to very high").
- Honey is a sugar: the sugar rule decides it before any sensation, so the row has no effect.

**Unknown words:**

| Word | Resolution |
|---|---|
| malted barley | role `base` |

**Proposed fixes:**
1. Remove the sweetness row (Question C (b)).
2. `role = "base"`, not required. Honey stays `required = true`.

**Verdict:** needs your judgment on: Question C.

## 26/26 · 20B American Stout

**Envelope now:**

| Sensation | min–max | characters | quote |
|---|---|---|---|
| roast | medium–very high | coffee | "Moderate to very high roasted flavors, often tas…" |
| hop_aroma | very low–medium | citrus, resin | "Medium to very low hop aroma, often with a citru…" |
| malt | low–medium | caramel | "Low to medium malt sweetness, often with rich ch…" |
| hop_flavour | low–high | citrus, resin | "Low to high hop flavor, generally citrusy or res…" |
| dryness | medium–medium | – | "Medium to dry finish, occasionally with a lightl…" |
| body | medium–high | – | "Medium to full body." |

Ingredients: role `base` req · role `roast` · role `crystal`

**Problems:**
- Code: none. Roast lists only coffee (Black Malt, tagged roast only, gets half a match). The "malt" row is
  about malt *sweetness*. Esters missing ("Medium esters optional."); adjuncts not extracted.
- Citra check holds: hop aroma citrus/resin, max medium → whirlpool 👍, heavy dry hop ⚠️ (if the
  Task 6 cut points put 8 g/L above medium).

**Unknown words:**

| Word | Resolution |
|---|---|
| roasted coffee, roasted coffee beans, slightly burnt coffee grounds | map to `coffee` (Weyermann Roasted Barley has coffee; Viking's and Black Malt only roast) |
| dark chocolate, dark or bittersweet chocolate, rich chocolate | map to `chocolate` |
| burnt, charcoal | drop: "acceptable at low levels" but "should not seem … acrid" |

**Proposed fixes:**
1. roast `characters` = `["roast", "coffee", "chocolate"]`.
2. `malt` row → `sweetness`, `characters` = `[]`.
3. dryness = medium–high.
4. Add esters none–medium, "Medium esters optional."
5. Add `role = "adjunct"`, "Adjuncts or additives may be present in low quantities to add complexity."
6. Add tags `US`, `american-ale`, not required.

**Verdict:** ready after fixes.

---

## Vocabulary and flagged ingredients

The 50 ingredients flagged by `python -m loaders.tags` (report.md §1), with a proposal each.
The additions are in the `[vocab]` part of the proposals toml.

| Ingredient | Flag | Proposal |
|---|---|---|
| Columbus, Tomahawk | *édesgyökér* (licorice) | synonym `edesgyoker → spicy` (no licorice tag; anise-like spice) |
| Ella | *csillagánizs* (star anise) | synonym `csillaganizs → spicy` |
| Hallertau Blanc, Nelson Sauvin | *fehérbor* (white wine) | synonym `feherbor → fruity` (as *fehérszőlő* already is) |
| Lotus | *curry* | synonym `curry → spicy` |
| Superdelic | *cukorka* (candy) | `no_character` (no candy tag; a sweetness impression) |
| Abbey Monk Ale, Espe | *konyak* (cognac) | `no_character` (an alcohol note; alternative: `dried-fruit`) |
| Sterling | no descriptor text (page says "???") | leave flagged: no source for its character; it rates on origin only, and it is the golden set's "needs-review hop" |
| CBC-1 | no family (Stílus "conditioning") | `yeast_family_override`: `cbc1 = "ale"` (a neutral ale strain) |
| Suava Ale | no family (no Stílus, no type) | `suavaale = "american-ale"` (its shop text: IPA, Hazy IPA, American IPA) |
| 38 YeastFlow yeasts (YF-101 … YF-999) | no aroma text | (a) accept family only; the flag stays as an honest "no character data" (**recommend**). (b) later: scan the shop description too (a code change in `loaders/tags.py`; e.g. YF-401 says *Lágy észterprofil*) |

After these, a re-run would flag 39 (Sterling and the 38 YeastFlow strains). Note: the 10A
reference recipe's YF-401 Mr. Weizen (an *American* wheat strain, no banana/clove tag) rates ➖
in 10A, not 👍; Lallemand Munich Classic (banana) or SafAle W-68 (clove) are tagged weizen yeasts
for the golden set's "weizen yeast in 10A".

**Judgment items:**
- **SafAle US-05 → `american-ale` override.** The shop says only "Ale" (*semleges*), but its own
  text recommends it for *erősen komlózott amerikai ale sörök*, and STYLE-FIT §2 uses it as the
  example. **Recommend keep.** Dropping it makes US-05 plain `ale`.
- **Acidulated Malt tagged `sour`.** It comes from "Maximum 5 %, and 10 % in sour beers" in its
  description: a beer type, not a taste. Proposal: add *sour beers* to `no_character`, so the
  scan skips it; the `fruity` tag ("a fruity-acidic note") stays. Today the tag has no effect
  (kilned malts drive no sensation), so this only keeps the tags truthful.

**English synonyms** proposed for words the draft left unknown and later styles will reuse (30):
toast, doughy, cracker, crackery, biscuity, roasty, roasted grain, coffee-like, chocolaty, dark
chocolate, milk chocolate, burnt, charcoal, plums, prunes, figs, pome fruit, apple, peach,
apricot, citrus fruit, black currants, flowery, spice, black pepper, caramelized sugar,
butterscotch, fruitiness, fruity esters, hay (tags in the proposals toml). Words dropped above
(intensity, texture, grain) get no synonym: no tag fits them.
