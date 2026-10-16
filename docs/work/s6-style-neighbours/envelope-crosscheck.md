# S6 · Barnes 2008 cross-check of the 21 envelopes

Written 2026-10-16 for Task 5 of [plan.md](plan.md). **Result: 62 keep, 3 change.** The three changes (D20, D40, D57) were applied to `loaders/style_envelopes.toml` in 2fdb99e; every other row is kept. This report lists every place where a 2008 flashcard (Barnes, `shared/rag-files/styles/barnes_bjcp_style_flashcards_2011.pdf`) reads differently from a style envelope, with the envelope's 2021 quote, a proposal and the decision. 2008 numbers and codes appear only in this report.

## How the cards were read

- **M1 · Scale.** Barnes' intensity words map to the s3 scale (R3 in `docs/finished/s3-style-fit/envelope-review.md`): none, very low (V. low, faint), low (Lt., mild), medium-low (Med. low), medium (= moderate), medium-high (Med. high), high (strong), very high (V. high). Finish: dry = high, med. dry = medium-high. Body: full = high.
- **Dimensions.** Aroma and flavour columns map as in the plan: malt, hop aroma (aroma Hops), hop flavour (flavour Hop Flavor), esters and phenols (yeast column by its character words), body, dryness/sweetness (finish, balance), sourness, brett, spice, smoke. Where an envelope has one row for a sensation, the card's aroma and flavour ranges are joined (union). In the stout and dark-lager cards the malt column is the roast level. Bitterness, colour, clarity, head, carbonation, texture, astringency, alcohol and diacetyl have no envelope dimension and are skipped.
- **M2 · Clean fermentation.** A card that says Clean, or lists fruity esters as unacceptable, matches the s3 'clean fermentation' rule (esters none–very low, phenols none–none; s3 question B). Not a difference.
- **M3 · Card silent.** An envelope row the card has no level for is listed under *Card silent*, not counted as a difference. (The plan counted any dimension on one side only; that would list rows where 2008 has nothing to compare. See Deviations in plan.md.)
- **M4 · Characters.** A character counts only when the card names it for that dimension and its word has a tag in `loaders/style_fit_vocab.toml` (or the envelope has a tag the card lacks). Words with no tag: noble, grainy, perfume-like, resinous, graham cracker-like, Munich/Vienna malt. Only the card's *Character* and *Optional* rows are read; *Unacceptable* rows count only for caramel and roast.
- **M5 · 2021 quote.** Taken from the style's 2021 entry (`shared/rag-files/styles/styles.json`); short phrases only.
- **M6 · Parent tags.** A card tag that is the parent or child of the envelope's tag (fruity vs lemon, stone-fruit) is not a difference.
- **Difference** = a min or max one step or more apart, a dimension or character the card names and the envelope lacks (or the envelope has and the card contradicts).

## Groups: decide by group, override by number

Every proposal belongs to one group. Accepting a group accepts all its rows.

| Group | Meaning | Proposal | Rows |
|---|---|---|---|
| K1 | 2008 and 2021 differ and the 2021 quote supports the envelope: a guideline change, not an envelope mistake. | keep | 53: D3, D4, D5, D6, D8, D9, D10, D12, D13, D14, D16, D17, D18, D19, D21, D22, D23, D24, D25, D26, D27, D28, D29, D30, D33, D34, D36, D37, D38, D41, D42, D43, D44, D45, D46, D47, D48, D49, D50, D51, D52, D53, D54, D55, D56, D58, D59, D60, D61, D62, D63, D64, D65 |
| K2 | The envelope is deliberately silent or empty (s3 rule, word without tag, ingredient row covers it). | keep | 3: D15, D31, D39 |
| U | 2021 states a different level for aroma and for flavour; the envelope row follows one of them and Barnes matches the other. | keep (you may flip the whole group to widen the row) | 6: D1, D2, D7, D11, D32, D35 |
| C1 | The 2021 text supports Barnes and the envelope misses it: an envelope mistake. | change (rows below) | 3: D20, D40, D57 |

The three proposed changes (group C1), as they would go into the envelope file in Task 6:

- **D20** · 18A Blonde Ale malt characters: change to malt characters bready, toasty, biscuit.
- **D40** · 20B American Stout roast characters: change to roast characters roast, coffee, chocolate, acrid.
- **D57** · 25B Saison body: change max to medium.

## Per pair

### 10A Weissbier ↔ Weizen/Weissbier (card 15A)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D1 | esters | yeast aroma med–strong, flavour low–med high: low–high; banana | medium–high; banana | "Low to moderately strong banana and clove flavor" (flavour); "Moderate to strong esters and phenols" (aroma) | **keep** (U): 2021 itself has a weaker flavour floor than aroma; the envelope follows the aroma sentence. |  keep (agreed) |
| D2 | phenols | same yeast intensities as esters: low–high; clove | medium–high; clove, vanilla | same two sentences as esters | **keep** (U): as esters. |  keep (agreed) |
| D3 | malt | aroma low–med, flavour very low–med: very low–medium; bready, grainy wheat | low–medium; bready | "Low to moderate soft, somewhat bready, doughy, or grainy wheat flavor" | **keep** (K1): 2021 floor is low; Barnes' very low is 2008 wording. |  keep (agreed) |
| D4 | characters (optional) | optional low citrusy tartness, low bubblegum notes | none of these | "Bubblegum (strawberry with banana), sourness, or smoke are faults." | **keep** (K1): 2021 turned both into faults. |  keep (agreed) |

Card silent: sweetness (very low) is not on the card; hop words on the card (noble) have no tag.

### 11B Best Bitter ↔ Special/Best/Premium Bitter (card 8B)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D5 | malt and caramel characters | malt grainy, bready; optional caramel notes | malt bready, biscuit, toasty; caramel caramel, toffee | "The malt profile is typically bready, biscuity, or lightly toasty." "caramel or toffee flavors are optional" | **keep** (K1): 2021 added biscuit, toasty and toffee; 'grainy' has no tag. |  keep (agreed) |
| D6 | hop_aroma and hop_flavour characters | earthy, floral, herbal, resinous (UK varieties) | floral, earthy, resin, fruity | "typically with an earthy, resiny, fruity, or floral character" | **keep** (K1): 2021 lists fruity and drops herbal; 'resinous' has no tag, 'resiny' does. |  keep (agreed) |
| D7 | esters | aroma mild–med, flavour med low–med high: low–med-high; fruity | medium-low–medium-high; fruity | "Mild to moderate fruitiness." (aroma); "Moderately low to moderately high fruity esters." (flavour) | **keep** (U): aroma floor (mild = low) is lower than the flavour floor the envelope uses. |  keep (agreed) |

Card silent: none. Dryness (dry = high), body, malt, hop levels agree.

### 15A Irish Red Ale ↔ Irish Red Ale (card 9D)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D8 | esters | yeast none–very low; esters listed as unacceptable | none–low | "Low esters optional." | **keep** (K1): 2021 allows low esters; 2008 did not. |  keep (agreed) |

Card silent: sweetness (very low–medium): the card names caramel sweetness but no level. Hop origin (UK) has no envelope field.

### 15B Irish Stout ↔ Dry Stout (card 13A)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D9 | esters | aroma none–med low, flavour none–med: none–medium; fruity | none–medium-low; fruity | "Medium-low esters optional." "medium-low fruitiness" | **keep** (K1): 2021 caps at medium-low. |  keep (agreed) |
| D10 | dryness | finish dry: high | medium–high | "The finish can be dry and coffee-like to moderately balanced" | **keep** (K1): 2021 allows a balanced finish; 2008 said dry. |  keep (agreed) |

Card silent: sweetness (none–low) is not on the card. Roast aroma 'prominent' is not on the scale; flavour med = envelope medium.

### 16A Sweet Stout ↔ Sweet Stout (card 13B)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D11 | roast | aroma mild, flavour med–high: low–high; roast, coffee, chocolate | medium–high; coffee, chocolate, roast | "Mild roasted grain aroma" (aroma); "flavors dominate the palate" (flavour) | **keep** (U): aroma floor is mild; the envelope follows the flavour, where roast dominates. |  keep (agreed) |

Card silent: none. Sweetness, esters, hops and body agree.

### 16B Oatmeal Stout ↔ Oatmeal Stout (card 13C)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D12 | esters | yeast low–med; fruity | low–medium-high; fruity | "Low to medium-high fruitiness." | **keep** (K1): 2021 is wider than 2008. |  keep (agreed) |
| D13 | hop_aroma | none–low | none–medium-low; earthy, floral | "Medium-low earthy or floral hop aroma optional." | **keep** (K1): 2021 allows more hop aroma. |  keep (agreed) |
| D14 | dryness | balance medium sweet–medium dry, in italics '(or very dry)' | medium-low–medium-high | "Medium-sweet to medium-dry finish" | **keep** (K1): the 2021 finish is the core Barnes range; the italic extra is dropped. |  keep (agreed) |
| D15 | malt (dimension on the card only) | malt med; oats: nutty, grainy, earthy | no malt row (roast row only) | "Oats can add a toasty-nutty, grainy, or earthy flavor." | **keep** (K2): the 16B ingredient rows already require Flaked Oats; nutty or earthy oats need no character. |  keep (agreed) |

Card silent: none.

### 17C Wee Heavy ↔ Strong Scotch Ale (card 9E)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D16 | malt characters | kettle caramelisation, nutty; level rich | high; bready, toasty, biscuit | "Strong bready-toasty malt, with a high caramel and toffee aspect." | **keep** (K1): 2021 words differ; the level (high) agrees. |  keep (agreed) |
| D17 | roast | roast/smoke malt very low–med low: very low–med-low | none–low; roast | "Faint hint of roast is sometimes noted." | **keep** (K1): 2021 caps at a faint hint. |  keep (agreed) |
| D18 | hop_flavour | low–med low | none–medium-low; earthy, floral, orange, spicy | "Medium-low hop flavor optional" | **keep** (K1): 'optional' makes none valid. |  keep (agreed) |
| D19 | smoke (dimension on the card only) | optional peaty, earthy and/or smoky, very low–med low | no smoke row | the 2021 entry has no smoke wording | **keep** (K1): 2021 dropped peaty/smoky; smoke is a specialty dimension, so silence marks smoke as out of style. |  keep (agreed) |

Card silent: none. Esters (dried fruit), sweetness, dryness, body, hop_aroma agree.

### 18A Blonde Ale ↔ Blonde Ale (card 6B)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D20 | malt characters | optional light-character malt: bread, toast, biscuit, wheat | bready only | "light character malt flavor (e.g., bread, toast, biscuit, wheat)" | **change to malt characters bready, toasty, biscuit** (C1): the envelope's own entry lists toast and biscuit; wheat has no tag. |  change (agreed) |
| D21 | caramel | caramel flavour unacceptable | none–low; caramel, honey | "Caramel flavors usually absent; if present, they are typically low-color caramel" | **keep** (K1): 2021 allows a little caramel. |  keep (agreed) |
| D22 | esters | low–med, optional | none–medium; fruity | "Low to medium fruity esters optional" | **keep** (K1): 'optional' makes none valid. |  keep (agreed) |
| D23 | hop_aroma | low–med | none–medium; citrus, floral, fruity, spicy | "May have a low to medium hop aroma" | **keep** (K1): 'may have' makes none valid. |  keep (agreed) |

Card silent: phenols (none–none) is the s3 'clean fermentation' rule (see M2).

### 18B American Pale Ale ↔ American Pale Ale (card 10A)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D24 | hop_aroma | med–high; usually citrusy, optional grassy | medium–medium-high; citrus, floral, pine, resin and more | "Moderate to moderately-high hop aroma" | **keep** (K1): 2021 caps at moderately high. |  keep (agreed) |
| D25 | hop_flavour | med–high; usually citrusy | medium–medium-high | "same intensities and descriptors apply" | **keep** (K1): as hop_aroma. |  keep (agreed) |
| D26 | malt | aroma low–med, flavour low–med high: low–med-high | low–medium; bready, toasty, biscuit, caramel | "Low to moderate neutral to grainy maltiness" | **keep** (K1): 2021 caps at moderate. |  keep (agreed) |
| D27 | caramel | very low–low, optional | none–low; caramel | "Caramel flavors are often absent" | **keep** (K1): 'often absent' makes none valid. |  keep (agreed) |
| D28 | dryness | finish medium dry–dry: medium-high–high | medium–high | "Medium to dry finish." | **keep** (K1): 2021 allows a medium finish. |  keep (agreed) |
| D29 | hop characters (optional) | optional grassy dry-hop notes | no grassy | "Fresh dry-hop aroma optional." (no 'grassy' in the 2021 entry) | **keep** (K1): 2021 drops the wording. |  keep (agreed) |

Card silent: phenols (none–none) is the s3 'clean fermentation' rule (see M2).

### 19C American Brown Ale ↔ American Brown Ale (card 10C)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D30 | malt | flavour med–high: medium–high | medium–medium-high; chocolate, caramel, nutty, toasty | "Medium to moderately-high malty-sweet or maltyrich flavor" | **keep** (K1): 2021 caps at moderately high. |  keep (agreed) |
| D31 | hop_flavour characters | optional citrusy flavour | no characters | "sometimes citrusy, fruity, or tropical, although any hop flavor that complements" | **keep** (K2): s3 R4: characters stay empty when the text says any hop that fits is fine. |  keep (agreed) |

Card silent: hop_aroma level (card gives none); roast (card: no roast, 'Porter-like' unacceptable; the envelope's chocolate roast is the 2021 reading).

### 1B American Lager ↔ Standard American Lager (card 1B)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D32 | malt | aroma none–low, flavour low: none–low | low–medium-low | "Low malt aroma optional" (aroma); "moderately-low to low grainy or corn-like flavor" (flavour) | **keep** (U): min: aroma may be absent; max: 2021 flavour says moderately low. |  keep (agreed) |
| D33 | hop_flavour | none–low | none–medium-low; floral, spicy, herbal | "Moderately low hop flavor optional" | **keep** (K1): 2021 allows moderately low. |  keep (agreed) |
| D34 | body | very light | low–medium-low | "Low to medium-low body." | **keep** (K1): 2021 floor is low. |  keep (agreed) |

Card silent: none. Dryness (crisp, dry), esters, hop_aroma agree.

### 1C Cream Ale ↔ Cream Ale (card 6A)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D35 | malt | aroma faint, flavour low–med: very low–medium | low–medium-low | "Low to moderate malty sweetness" "low to moderate corny flavor" | **keep** (U): 2021 flavour reaches moderate; the envelope follows the aroma sentence (medium-low to low). |  keep (agreed) |
| D36 | hop_aroma | none–low | none–medium-low; floral, spicy, herbal | "Medium-low hop aroma optional" | **keep** (K1): 2021 allows medium-low. |  keep (agreed) |
| D37 | esters | faint, optional | none–low; fruity | "Low fruity esters optional." | **keep** (K1): 2021 allows low. |  keep (agreed) |
| D38 | dryness | somewhat dry to faintly sweet: medium-low–medium-high | medium-low–high | "somewhat light, dry, and crisp to faintly sweet" | **keep** (K1): 2021 says dry and crisp. |  keep (agreed) |

Card silent: hop_flavour (the card's flavour column is blank); sweetness; phenols (s3 clean rule, M2).

### 20B American Stout ↔ American Stout (card 13E)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D39 | caramel (dimension on the card only) | malt: rich chocolate or caramel | no caramel row | "often with rich chocolate or caramel flavors" | **keep** (K2): caramel is a core dimension: silence rules nothing out, and the sentence sits under the sweetness row. |  keep (agreed) |
| D40 | roast characters | optional low burnt or charcoal notes | roast, coffee, chocolate | "Burnt or charcoal aromas are acceptable at low levels." | **change to roast characters roast, coffee, chocolate, acrid** (C1): 20C already has acrid; 'burnt' reads as acrid in the vocabulary. |  change (agreed) |

Card silent: none. Roast, hops, sweetness, dryness, body, esters agree.

### 20C Imperial Stout ↔ Russian Imperial Stout (card 13F)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D41 | roast | aroma low–high, flavour low–very high: low–very high | low–medium-high; roast, coffee, chocolate, acrid | "Light to moderately strong roast" | **keep** (K1): 2021 caps the roast at moderately strong. |  keep (agreed) |
| D42 | caramel | light–med: low–medium | low–low; caramel | "sometimes with a light caramel sweetness" | **keep** (K1): 2021 says light. |  keep (agreed) |
| D43 | esters | aroma low–med high, flavour low–high: low–high | low–medium-high; dried-fruit, berry | "Low to moderately strong esters" | **keep** (K1): 2021 caps at moderately strong. |  keep (agreed) |
| D44 | hop_aroma | low–very high | very low–medium-high | "Very low to fairly aggressive hops" | **keep** (K1): 2021 wording. |  keep (agreed) |
| D45 | hop_flavour | med-low–very high | very low–medium-high | "(same descriptors apply)" | **keep** (K1): 2021 reads flavour as aroma. |  keep (agreed) |
| D46 | dryness | balance and finish medium sweet–medium dry: medium-low–medium-high | low–medium-high | "fairly dry to moderately sweet" | **keep** (K1): 2021 allows a sweeter finish. |  keep (agreed) |

Card silent: malt (the card's malt column is the roast level; characters bready, toasty, caramel agree).

### 21A American IPA ↔ American IPA (card 14B)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D47 | hop_aroma | med-high–high | high–very high; citrus, floral, pine, resin, spicy, tropical, stone-fruit, berry, melon | "A prominent to intense hop aroma" | **keep** (K1): 2021 wording is stronger. |  keep (agreed) |
| D48 | hop_flavour | med–high | medium–very high | "Medium to very high hop flavor" | **keep** (K1): 2021 wording is stronger. |  keep (agreed) |
| D49 | hop characters (optional) | optional grassy dry hops; perfume-like (no tag) | no grassy | "citrus, floral, pine, resin, spice, tropical fruit, stone fruit, berry, or melon" (no grassy) | **keep** (K1): 2021 drops grassy. |  keep (agreed) |
| D50 | malt | aroma low–med low, flavour low–med: low–medium | low–medium-low | "Low to medium-low clean, grainy maltiness" | **keep** (K1): 2021 caps at medium-low. |  keep (agreed) |
| D51 | esters | aroma none–med low, flavour low: none–medium-low | none–low | "Low esters optional." | **keep** (K1): 2021 caps at low. |  keep (agreed) |

Card silent: phenols (none–none) is the s3 'clean fermentation' rule (see M2).

### 23A Berliner Weisse ↔ Berliner Weisse (card 17A)

No difference found. Card 'fruity' is the parent of the envelope's lemon, orchard-fruit, stone-fruit (M6).

### 25B Saison ↔ Saison (card 16C)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D52 | esters | aroma high (flavour blank): high | medium–high; citrus, orchard-fruit, stone-fruit | "The fruity esters are moderate to high" | **keep** (K1): the card gives one level, high. |  keep (agreed) |
| D53 | spice | aroma 'med. spice' (other: none–med); spices unacceptable if overwhelming | none–low | "Spices and herbs optional, but must not dominate." | **keep** (K1): 2021 says must not dominate. |  keep (agreed) |
| D54 | phenols | low peppery phenols: low | low–medium-high; pepper | "Low to moderately-high spicy notes are often like black pepper" | **keep** (K1): 2021 reaches moderately high. |  keep (agreed) |
| D55 | hop_aroma | low–med high | low–medium; spicy, floral, earthy, fruity, herbal | "Hops are low to moderate" | **keep** (K1): 2021 caps at moderate. |  keep (agreed) |
| D56 | malt | aroma light, flavour low–med low: low–medium-low | low–medium | "Malt is low to medium, with a soft, grainy palate." | **keep** (K1): 2021 reaches medium. |  keep (agreed) |
| D57 | body | light–medium: low–medium | low–medium-low | "Stronger versions can have up to medium body" | **change max to medium** (C1): 2021 and the card agree on medium; the envelope stops at medium-low. |  change (agreed) |

Card silent: none.

### 26B Belgian Dubbel ↔ Belgian Dubbel (card 18B)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D58 | malt | aroma high, flavour med–med-full: medium–high | medium–medium-high; chocolate, caramel, toasty | "Moderate to moderately strong, rich malty aroma" | **keep** (K1): 2021 caps at moderately strong. |  keep (agreed) |
| D59 | phenols | optional very low–med; clove, spice, peppery | low–medium; spicy, pepper | "Low to moderate spicy, peppery phenols." | **keep** (K1): 2021 floor is low and it does not list clove. |  keep (agreed) |
| D60 | body | med–full: medium–high | medium–medium-high | "Smooth, medium to medium-full body." | **keep** (K1): 2021 caps at medium-full. |  keep (agreed) |

Card silent: sweetness (low–medium): the card says malty sweetness, no level.

### 5D German Pils ↔ German Pilsner (card 2A)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D61 | hop_flavour | low–high; German noble | medium–medium-high; floral, spicy, herbal | "Malt and hop flavors similar to aroma (same descriptors and intensities)." | **keep** (K1): 2021 sets flavour equal to aroma, moderate to moderately high; 'noble' has no tag. |  keep (agreed) |
| D62 | dryness | finish dry–med dry: medium-high–high | high | "leading into a dry, crisp finish" | **keep** (K1): 2021 says dry. |  keep (agreed) |

Card silent: hop_aroma level (the card gives characters but no level). Esters none: M2.

### 6A Marzen ↔ Oktoberfest/Märzen (card 3B)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D63 | hop_aroma | none | none–very low; floral, herbal, spicy | "Very low floral, herbal, or spicy hop aroma optional." | **keep** (K1): 2021 allows very low. |  keep (agreed) |
| D64 | dryness | finish moderately dry: medium-high | medium-high–high | "the finish is moderately-dry to dry" | **keep** (K1): 2021 reaches dry. |  keep (agreed) |

Card silent: malt level (aroma 'rich' is not on the scale, flavour blank; 'Munich/Vienna malt' has no tag). Caramel and roast none match the card's unacceptable list.

### 8B Schwarzbier ↔ Schwarzbier (card 4C)

| # | Dimension | Barnes (2008) | Envelope now (2021) | 2021 quote | Proposal | Decision |
|---|---|---|---|---|---|---|
| D65 | hop_aroma | none–low | none–medium-low; spicy, floral, herbal | "A moderately low spicy, floral, or herbal hop aroma is optional." | **keep** (K1): 2021 allows moderately low. |  keep (agreed) |

Card silent: dryness (the card says the finish dries out slowly, no level). Malt, roast, hop_flavour, body agree.

## Count

- Pairs compared: 21. Pairs with at least one difference: 20. Pairs with none: 1 (23A).
- Differences: 65. Proposed *keep*: 62 (K1 53, K2 3, U 6). Proposed *change*: 3 (C1).
- Not compared (no 2008 counterpart): 21C, 31B and the three BA styles.

## Decisions

2026-10-16, user: K1 keep all 53, K2 keep all 3, U keep all 6, C1 apply all 3 (D20, D40, D57). The three changes go into `loaders/style_envelopes.toml` in Task 6.
