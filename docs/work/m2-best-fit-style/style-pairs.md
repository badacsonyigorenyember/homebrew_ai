# BA to BJCP style pairs: for your review

Step 2 scores BA 2026 and BJCP 2021 styles together. When the best fit is a BA style that is
**the same beer** as a BJCP style, step 2 returns the BJCP style instead (R6). This file is the
proposed list of those pairs. Only the rows you confirm go into `db/021_style_pairs.sql` (Task 3).

**How the pairs were proposed.** Claude read each style's full guideline text in `ref.beer_style`
(overall impression, aroma, appearance, flavour, mouthfeel, ingredients, history, comments,
style comparison, commercial examples and the OG/FG/ABV/IBU/SRM ranges) and compared the beers,
not the names (your rule, 2026-10-13). No script and no name matching.

- **A pair means the same beer:** the same or a very similar sensory profile, ingredients and
  process, and compatible vital statistics. The vitals are a cross-check; where they disagree
  noticeably, the reason says so.
- **Not a pair:** a narrower or broader neighbour, a regional variant with a different
  character, a BA style that covers two BJCP styles (or the other way round), or a beer BJCP has
  no style for. These rows show `—`.
- **Catch-alls.** A BA style that is one specific case inside a broader BJCP catch-all
  (chocolate beer inside 30A, honey beer inside 31B, smoked Helles inside 32A) stays `—`, and the
  reason names the catch-all. A BA catch-all is paired with a BJCP catch-all only when both are
  defined by the same feature (Brett Beer and 28A), and then at most at medium confidence.
- **Two rows are `—` on purpose:** `session-india-pale-ale` (brief b21) and
  `mexican-style-amber-lager` (brief b22). Their briefs expect the BA pick, and a pair would turn
  it into a BJCP one. On content alone `mexican-style-amber-lager` is close to 2B.
- **Stored names.** A few BA rows carry a cut-off name from the loader (`Export`, `Lager`,
  `Weizen`, `India Pale Ale` twice, `or Oud Red Ale`, …). The reason gives the full BA name read
  from the guideline text. The codes are correct.
- **21B.** BJCP's Black, Red, White and other IPA types live inside 21B Specialty IPA, but the
  21B row in `ref.beer_style` holds only the Brut IPA text and vitals, so no BA style is paired to
  21B.

**Counts:** 109 BA styles paired, 60 unpaired (`—`), 169 in all.
Confidence: **low 4** (all paired), **medium 54** (23 paired, 31 unpaired),
**high 111** (82 paired, 29 unpaired). The sections run low → medium → high, so the
rows that most need your eye come first; within a section, paired rows come first, by BA name.

**What to write in `confirm`** (every row):

- `ok`: the proposal is right (the pair, or `—` = stays unpaired)
- a BJCP code, for example `6A`: pair it with that style instead (also on a `—` row)
- `drop`: no pair for this row

Ranges are written low–high; `30+` is an open upper end. An empty BJCP range means the style has
no vital statistics (most BJCP specialty styles).

## 1. Low confidence: look at these first (4 rows)

| BA code | BA name | proposed BJCP | confidence | why | ABV BA | ABV BJCP | IBU BA | IBU BJCP | confirm |
|---|---|---|---|---|---|---|---|---|---|
| `american-style-fruit-beer` | American-Style Fruit Beer | 29A Fruit Beer | low | Catch-all for non-sour beer with fruit and clean ale/lager yeast; 29A is BJCP's catch-all for fruit on a base style. Same defining feature, but BA splits fruit beers three ways and 29A covers all of them. | 2.5–12 |  | 5–70 |  |  |
| `experimental-beer` | Experimental Beer | 34C Experimental Beer | low | Catch-all for unique techniques or combinations of categories; 34C Experimental Beer is BJCP's equivalent "fits nowhere else" bucket. |  |  |  |  |  |
| `herb-and-spice-beer` | Herb and Spice Beer | 30A Spice, Herb, or Vegetable Beer | low | Catch-all for any beer showing herbs or spices; 30A is BJCP's catch-all for spices, herbs or vegetables. Same defining feature, but 30A also takes vegetables, chili and pumpkin, which BA splits off. |  |  |  |  |  |
| `smoke-beer` | Smoke Beer | 32A Classic Style Smoked Beer | low | Catch-all for any style with smoke; 32A Classic Style Smoked Beer is BJCP's catch-all for smoked base styles. Same defining feature, but smoked beers with other specialty ingredients would be 32B. |  |  |  |  |  |

## 2. Medium confidence (54 rows: 23 paired, 31 unpaired)

| BA code | BA name | proposed BJCP | confidence | why | ABV BA | ABV BJCP | IBU BA | IBU BJCP | confirm |
|---|---|---|---|---|---|---|---|---|---|
| `american-style-brown-ale` | American-Style Brown Ale | 19C American Brown Ale | medium | Same caramel-chocolate American brown ale with hops; but BA wants medium roast and IBU 30–45, while 19C says no porter-like roast and IBU 20–30. | 4.2–6.3 | 4.3–6.2 | 30–45 | 20–30 |  |
| `american-style-strong-pale-ale` | American-Style Strong Pale Ale | 21A American IPA | medium | Hop-forward, dry, high-bitterness pale ale at 5.6–6.4 % / 40–50 IBU, which sits inside 21A American IPA (5.5–7.5 %, 40–70 IBU) with the same sensory profile; BA keeps it apart from its own IPA. | 5.6–6.4 | 5.5–7.5 | 40–50 | 40–70 |  |
| `belgian-style-quadrupel` | Belgian-Style Quadrupel | 26D Belgian Dark Strong Ale | medium | Very strong, dark, dark-sugar and dried-fruit Belgian ale; 26D is "also known as a Belgian Quad", but BA's quad runs stronger (10.0–14.2 % vs 8.0–12.0 %). | 10–14.2 | 8–12 | 25–50 | 20–35 |  |
| `bernsteinfarbenes-weizen` | Bernsteinfarbenes Weizen | 10A Weissbier | medium | Amber (SRM 9–13) Weissbier with caramel-bready malt and muted banana/clove; sits between 10A (SRM 2–6) and 10B (14–23), but 10A lists the amber Schneider Weisse Original. | 4.8–5.4 | 4.3–5.6 | 10–15 | 8–15 |  |
| `brett-beer` | Brett Beer | 28A Brett Beer | medium | Any base fermented with Brett and no bacteria — the same definition as the 28A Brett Beer catch-all ("No Lacto"); BA also allows fruit and wood inside the style, which BJCP sends to 28C. |  |  |  |  |  |
| `classic-australian-style-pale-ale` | Classic Australian-Style Pale Ale | 12B Australian Sparkling Ale | medium | Dry, estery Australian pale ale with yeast in suspension and mild hops — the Coopers type that 12B describes; BA is broader and its esters/carbonation are less specified. | 4–6 | 4.5–6 | 15–35 | 20–35 |  |
| `classic-english-style-pale-ale` | Classic English-Style Pale Ale | 11C Strong Bitter | medium | Gold-copper, estery, medium-bitter English pale ale; BJCP has no own English pale ale and 11C says British pale ale "roughly approximates a strong bitter"; BA ABV 4.4–5.3 straddles 11B and 11C. | 4.4–5.3 | 4.6–6.2 | 20–40 | 30–50 |  |
| `double-hoppy-red-ale` | Double Hoppy Red Ale | 22B American Strong Ale | medium | Strong caramel-malty red ale with high hops and bitterness; 22B names "modern Double Red Ales", though a hoppier one could be a Red IPA (21B). | 6.1–7.9 | 6.3–10 | 45–80 | 50–100 |  |
| `english-style-summer-ale` | English-Style Summer Ale | 12A British Golden Ale | medium | Straw-gold, refreshing British pale ale with biscuity malt and balanced hops; 12A says golden ales are also called "Summer Ales", but 12A is more hop-forward and bitter than BA's balanced, wheat-containing version. | 3.7–5.1 | 3.8–5 | 20–30 | 20–45 |  |
| `german-style-rye-ale` | German-Style Rye Ale | 27H Historical Beer: Roggenbier | medium | Weizen-yeast rye beer (≥30 % rye) with banana/clove and toffee-chocolate in darker versions — the 27H Roggenbier profile; BA also allows pale versions (SRM 4–25 vs 14–19). | 4.9–5.6 | 4.5–6 | 10–15 | 10–20 |  |
| `india-pale-ale-2` | India Pale Ale | 21C Hazy IPA | medium | Stored name "India Pale Ale" (code india-pale-ale-2) is BA's Juicy or Hazy Imperial or Double IPA: the 21C hazy, juicy, soft-bitter profile, but stronger (7.6–10.6 % vs 6.0–9.0 %). | 7.6–10.6 | 6–9 | 30–80 | 25–60 |  |
| `international-light-lager` | International Light Lager | 1B American Lager | medium | Despite the name it is a 4.1–5.1 % adjunct lager with absent malt sweetness and very low hops and bitterness — the 1B profile, not the drier and more bitter 2A. | 4.1–5.1 | 4.2–5.3 | 9–18 | 8–18 |  |
| `juicy-or-hazy-strong-pale-ale` | Juicy or Hazy Strong Pale Ale | 21C Hazy IPA | medium | Hazy, juicy, soft-bitter pale ale at 5.6–6.4 % — the 21C Hazy IPA profile at its lower strength (21C starts at 6.0 %). | 5.6–6.4 | 6–9 | 15–40 | 25–60 |  |
| `kellerbier-or-zwickelbier` | Kellerbier or Zwickelbier | 27A Historical Beer: Kellerbier | medium | Unfiltered, young-served lager or ale of European origin — 27A Kellerbier's idea, but BA also includes ales (Kölsch, Alt) while 27A is limited to German lagers. |  |  |  |  |  |
| `lager` | Lager | 1B American Lager | medium | Stored name "Lager" is BA's Contemporary American-Style Lager: the 1B adjunct lager with a little more hop aroma and all-malt versions allowed; IBU and ABV identical to the traditional style. | 4.1–5.1 | 4.2–5.3 | 5–16 | 8–18 |  |
| `maerzen-oktoberfest` | Maerzen/Oktoberfest | 6A Marzen | medium | Stored name "Maerzen/Oktoberfest" is BA's American-Style Märzen/Oktoberfest: the 6A toasty amber lager with a more pronounced hop character; 6A says US craft Oktoberfests are based on it. | 5.1–6 | 5.6–6.3 | 20–30 | 18–24 |  |
| `mexican-style-dark-lager` | Mexican-Style Dark Lager | 2C International Dark Lager | medium | Dark adjunct lager with Munich/Vienna malt, toast/caramel/toffee and low hops — the regional dark variant of the 2C international dark lager; BA ABV up to 5.8. | 4.5–5.8 | 4.2–6 | 12–28 | 8–20 |  |
| `mexican-style-light-lager` | Mexican-Style Light Lager | 1A American Light Lager | medium | Same very light, dry, corn/rice adjunct light lager with very low hops (vitals almost identical to 1A); a Mexican regional take of the same beer. | 3.2–4.2 | 2.8–4.2 | 8–17 | 8–12 |  |
| `mixed-culture-brett-beer` | Mixed-Culture Brett Beer | 28B Mixed-Fermentation Sour Beer | medium | Brett plus bacteria on any base, sour and funky — the same definition as the 28B Mixed-Fermentation Sour Beer catch-all; BA also allows fruit inside the style, which BJCP sends to 28C. |  |  |  |  |  |
| `new-zealand-style-india-pale-ale` | New Zealand-Style India Pale Ale | 21A American IPA | medium | Hop-dominant, bitter, dry IPA with New Zealand hops; vitals sit inside 21A, which allows New World hops; the hop origin is the only difference. | 6.3–7.5 | 5.5–7.5 | 50–70 | 40–70 |  |
| `rice-lager` | Rice Lager | 2A International Pale Lager | medium | Pale lager with ≥15 % rice and a clean dry finish; 31A says rice-based international lager is not an alternative-grain beer, so BJCP files it under 2A (Asahi Super Dry); BA allows an expressive rice character 2A does not describe. | 4–6 | 4.5–6 | 15–30 | 18–25 |  |
| `scottish-style-light-ale` | Scottish-Style Light Ale | 14A Scottish Light | medium | Same low-gravity, caramel-malty Scottish ale with low bitterness; but BA allows low peat smoke (14A: none) and is paler (SRM 6–15 vs 17–25). | 2.8–3.5 | 2.5–3.3 | 9–20 | 10–20 |  |
| `strong-ale` | Strong Ale | 17A British Strong Ale | medium | Same malty, caramel-sweet British strong ale with low hops and complex esters; BA's ABV range runs into barley-wine strength (7.0–11.3 vs 5.5–8.0). | 7–11.3 | 5.5–8 | 30–60 | 30–60 |  |
| `american-style-black-ale` | American-Style Black Ale | — | medium | Black IPA: hoppy, bitter, black with restrained roast. In BJCP it is the Black IPA type inside 21B Specialty IPA, but the 21B row in ref.beer_style holds only the Brut IPA text and vitals. | 6.3–7.6 |  | 40–70 |  |  |
| `american-style-fruited-sour-ale` | American-Style Fruited Sour Ale | — | medium | Fruited American sour ale without Brett; one case inside the 28C Wild Specialty Beer catch-all (wild/sour beer with any specialty ingredient), so unpaired. |  |  |  |  |  |
| `american-style-india-pale-lager` | American-Style India Pale Lager | — | medium | Hop-forward pale lager at IPA strength; BJCP has no own style (21A lets an IPL in "if it has a similar character", otherwise 34B Mixed-Style). | 5.6–7.9 |  | 30–70 |  |  |
| `american-style-sour-ale` | American-Style Sour Ale | — | medium | Clean-acid American sour (lactic/acetic, no Brett), any colour and base; spans 28D Straight Sour Beer (pale, lactic only) and 28B Mixed-Fermentation Sour Beer (usually with Brett), so no single pair. |  |  |  |  |  |
| `australian-style-pale-ale` | Australian-Style Pale Ale | — | medium | Modern Australian pale ale with tropical/stone-fruit hops; nearest is 18B American Pale Ale, but BA bitterness runs lower (15–40 vs 30–50 IBU) and the hop origin defines it. | 4–6 |  | 15–40 |  |  |
| `bamberg-style-bock-rauchbier` | Bamberg-Style Bock Rauchbier | — | medium | Beechwood-smoked Bock; BJCP has no own style, it is entered under the 32A Classic Style Smoked Beer catch-all with Bock as base. | 6.3–7.6 |  | 20–30 |  |  |
| `bamberg-style-helles-rauchbier` | Bamberg-Style Helles Rauchbier | — | medium | Beechwood-smoked Helles; BJCP has no own style, it is entered under the 32A Classic Style Smoked Beer catch-all with Helles as base. | 4.8–5.6 |  | 18–25 |  |  |
| `bamberg-style-weiss-rauchbier` | Bamberg-Style Weiss Rauchbier | — | medium | Smoked Weissbier; BJCP has no own style, it is entered under the 32A Classic Style Smoked Beer catch-all (Schlenkerla Rauchbier Weizen is a 32A example). | 4.9–5.6 |  | 10–15 |  |  |
| `belgian-style-fruit-beer` | Belgian-Style Fruit Beer | — | medium | Belgian-yeast beer with fruit, acidity optional; one case inside the 29A Fruit Beer catch-all (28C when sour/Brett), so unpaired. | 2.5–12 |  | 5–70 |  |  |
| `chili-pepper-beer` | Chili Pepper Beer | — | medium | Any style with chili peppers; one case inside the 30A Spice, Herb, or Vegetable Beer catch-all, so unpaired. | 2.5–13.3 |  | 5–70 |  |  |
| `chocolate-or-cocoa-beer` | Chocolate or Cocoa Beer | — | medium | Any style with chocolate or cocoa; one case inside the 30A Spice, Herb, or Vegetable Beer catch-all (30A lists Young's Double Chocolate Stout), so unpaired. |  |  |  |  |  |
| `coffee-beer` | Coffee Beer | — | medium | Any style with coffee; one case inside the 30A Spice, Herb, or Vegetable Beer catch-all (30A lists Founders Breakfast Stout), so unpaired. |  |  |  |  |  |
| `dessert-stout-or-pastry-beer` | Dessert Stout or Pastry Beer | — | medium | Strong, sweet, dark beer with culinary additions (chocolate, vanilla, maple, nuts, sugars); would be 30D, 29C or 30A depending on the additions, so no single pair. | 7–13 |  | 20–65 |  |  |
| `european-style-dark-lager` | European-Style Dark Lager | — | medium | Broad dark lager with chocolate and noticeable roast and IBU up to 35: sits between 8A Munich Dunkel (no roast) and 8B Schwarzbier (BA has its own Schwarzbier style); not the same beer as either. | 4.8–5.3 |  | 20–35 |  |  |
| `experimental-india-pale-ale` | Experimental India Pale Ale | — | medium | White, red, brown, Brut, Brett, lager and fruited IPAs; in BJCP these are types inside 21B Specialty IPA, but the 21B row in ref.beer_style holds only the Brut IPA text. | 6.3–10.6 |  | 30–100 |  |  |
| `field-beer` | Field Beer | — | medium | Beer with vegetables, nuts or coconut; one case inside the 30A Spice, Herb, or Vegetable Beer catch-all (nuts are not even named there), so unpaired. | 2.5–13.3 |  | 5–70 |  |  |
| `fruit-wheat-beer` | Fruit Wheat Beer | — | medium | Wheat beer (≥30 % wheat) with fruit; one case inside the 29A Fruit Beer catch-all, so unpaired. | 2.5–12 |  | 10–35 |  |  |
| `international-style-pale-ale` | International-Style Pale Ale | — | medium | Catch-all for pale ales from around the world that fit no other pale ale style; no single BJCP style (18B is the American one). | 4.4–6.6 |  | 20–42 |  |  |
| `juicy-or-hazy-pale-ale` | Juicy or Hazy Pale Ale | — | medium | Hazy, juicy, soft-bitter pale ale at 4.4–5.4 %; BJCP's only hazy style is 21C Hazy IPA (6.0–9.0 %), and 18B American Pale Ale is clear and bitter. | 4.4–5.4 |  | 5–30 |  |  |
| `light-lager` | Light Lager | — | medium | Stored name "Light Lager" is BA's Contemporary American-Style Light Lager: like 1A but with more evident hops and colour up to medium amber (SRM 1.5–12, IBU 5–20 vs 1A 2–3 SRM, 8–12 IBU), so broader than 1A. | 3.5–4.4 |  | 5–20 |  |  |
| `new-zealand-style-pale-ale` | New Zealand-Style Pale Ale | — | medium | New Zealand pale ale with tropical/grassy NZ hops; nearest is 18B American Pale Ale, but BA bitterness runs lower (15–40 vs 30–50 IBU) and the hop origin defines it. | 4–6 |  | 15–40 |  |  |
| `or-oud-red-ale` | or Oud Red Ale | — | medium | Stored name "or Oud Red Ale" is BA's Belgian-Style Flanders Oud Bruin or Oud Red Ale: one BA style covering two BJCP styles, 23B Flanders Red Ale and 23C Oud Bruin, so no single pair. | 4.8–6.6 |  | 5–18 |  |  |
| `pilsener` | Pilsener | — | medium | Stored name "Pilsener" is BA's Contemporary American-Style Pilsener: diverges from the pre-Prohibition beer (27F) by modern hop varieties and all-malt grists; no BJCP style is this beer. | 4.9–6 |  | 25–50 |  |  |
| `pumpkin-spice-beer` | Pumpkin Spice Beer | — | medium | Pumpkin/squash beer with pie spices; one case inside the 30B Autumn Seasonal Beer catch-all (harvest-themed spiced beers), so unpaired, although 30B's examples are all pumpkin ales. | 2.5–12 |  | 5–35 |  |  |
| `pumpkin-squash-beer` | Pumpkin/Squash Beer | — | medium | Unspiced pumpkin/squash beer; one case inside the 30A Spice, Herb, or Vegetable Beer catch-all, so unpaired. | 2.5–12 |  | 5–35 |  |  |
| `rye-beer` | Rye Beer | — | medium | Beer with evident rye character; one case inside the 31A Alternative Grain Beer catch-all (1D sends American rye beers there), so unpaired. |  |  |  |  |  |
| `smoke-porter` | Smoke Porter | — | medium | Smoked porter of any base; BJCP has no own style, it is entered under the 32A Classic Style Smoked Beer catch-all (Alaskan Smoked Porter is a 32A example). |  |  |  |  |  |
| `specialty-beer` | Specialty Beer | — | medium | Beer with unusual fermentables (grains, tubers, syrups); spans 31A Alternative Grain Beer and 31B Alternative Sugar Beer, so no single pair. | 2.5–25 |  | 1–100 |  |  |
| `specialty-honey-beer` | Specialty Honey Beer | — | medium | Beer with honey as an added fermentable; one case inside the 31B Alternative Sugar Beer catch-all (which also takes molasses, maple, etc.), so unpaired. The plan's specialty list already maps honey to 31B / specialty-honey-beer per guide. | 2.5–12 |  | 1–100 |  |  |
| `wood-and-barrel-aged-beer` | Wood- and Barrel-Aged Beer | — | medium | Any style aged on wood, with or without spirit barrels; spans 33A Wood-Aged Beer and 33B Specialty Wood-Aged Beer, so no single pair. |  |  |  |  |  |
| `wood-and-barrel-aged-sour-beer` | Wood- and Barrel-Aged Sour Beer | — | medium | Wood-aged sour beer without Brett; BJCP would file it under 28B or 28C depending on the wood, so no single pair. |  |  |  |  |  |

## 3. High confidence (111 rows: 82 paired, 29 unpaired)

| BA code | BA name | proposed BJCP | confidence | why | ABV BA | ABV BJCP | IBU BA | IBU BJCP | confirm |
|---|---|---|---|---|---|---|---|---|---|
| `american-style-amber-lager` | American-Style Amber Lager | 2B International Amber Lager | high | Same smooth amber lager with caramel/toast malt and restrained to moderate hops; BJCP's own 2B examples (Brooklyn Lager, Yuengling Lager) are this beer. | 4.8–5.4 | 4.5–6 | 18–30 | 8–25 |  |
| `american-style-amber-red-ale` | American-Style Amber/Red Ale | 19A American Amber Ale | high | Same amber-to-red American ale: caramel maltiness with American hops and medium-high bitterness; vitals match. | 4.4–6.1 | 4.5–6.2 | 25–45 | 25–40 |  |
| `american-style-barley-wine-ale` | American-Style Barley Wine Ale | 22C American Barleywine | high | Same strong, malty, caramel/toffee barley wine with high American hop bitterness; vitals match. | 8.5–12.2 | 8–12 | 60–100 | 50–100 |  |
| `american-style-cream-ale` | American-Style Cream Ale | 1C Cream Ale | high | Same pale, crisp, corn-adjunct, warm-fermented then lagered American ale with low bitterness; vitals match. | 4.3–5.7 | 4.2–5.6 | 10–22 | 8–20 |  |
| `american-style-dark-lager` | American-Style Dark Lager | 2C International Dark Lager | high | Same dark mass-market lager: low caramel/chocolate/roast, low bitterness, light body, high carbonation; 2C lists Shiner Bock. | 4.1–5.6 | 4.2–6 | 14–24 | 8–20 |  |
| `american-style-imperial-stout` | American-Style Imperial Stout | 20C Imperial Stout | high | Same strong, black, roasty, very bitter stout with American hops — the American interpretation of 20C; vitals overlap. | 7–12 | 8–12 | 50–80 | 50–90 |  |
| `american-style-india-pale-ale` | American-Style India Pale Ale | 21A American IPA | high | Same hop-forward, bitter American IPA with supporting malt; vitals match. | 6.3–7.5 | 5.5–7.5 | 50–70 | 40–70 |  |
| `american-style-lager` | American-Style Lager | 1B American Lager | high | Same very pale, crisp, highly carbonated adjunct (corn/rice) lager with very low malt and hop character; vitals match. | 4.1–5.1 | 4.2–5.3 | 5–15 | 8–18 |  |
| `american-style-light-lager` | American-Style Light Lager | 1A American Light Lager | high | Same very light-bodied, very highly attenuated, low-calorie adjunct lager with almost no malt or hop flavour; vitals match. | 3.5–4.4 | 2.8–4.2 | 4–10 | 8–12 |  |
| `american-style-pale-ale` | American-Style Pale Ale | 18B American Pale Ale | high | Same hop-forward American pale ale with low caramel and medium-high bitterness; vitals match. | 4.4–5.4 | 4.5–6.2 | 30–50 | 30–50 |  |
| `american-style-pilsener` | American-Style Pilsener | 27F Historical Beer: Pre-Prohibition Lager | high | Same pre-Prohibition American pilsener: up to 25 % corn/rice, crisp malt, medium-high noble-type hops, IBU 25–40 — what 27F Pre-Prohibition Lager describes; vitals match. | 4.9–6 | 4.5–6 | 25–40 | 25–40 |  |
| `american-style-stout` | American-Style Stout | 20B American Stout | high | Same roasty, coffee-like, bitter stout with American citrus/resin hops; BA ABV a little higher (5.7–8.0 vs 5.0–7.0). | 5.7–8 | 5–7 | 35–60 | 35–75 |  |
| `american-style-wheat-beer` | American-Style Wheat Beer | 1D American Wheat Beer | high | Same ≥30 % wheat beer with clean ale or lager yeast and no clove/banana; BA also allows darker malts in the text, but its SRM range (2–10) stays pale. | 3.5–5.6 | 4–5.5 | 10–35 | 15–30 |  |
| `american-style-wheat-wine-ale` | American-Style Wheat Wine Ale | 22D Wheatwine | high | Same strong, ≥50 % wheat, bready-honey-caramel sipping ale without weizen yeast; vitals match. | 8.5–12.2 | 8–12 | 45–85 | 30–60 |  |
| `baltic-style-porter` | Baltic-Style Porter | 9C Baltic Porter | high | Same strong, smooth, cold-fermented dark lager with caramel, dark-sugar and dried-fruit malt and low roast; vitals match. | 7.6–9.3 | 6.5–9.5 | 35–40 | 20–40 |  |
| `bamberg-style-maerzen-rauchbier` | Bamberg-Style Maerzen Rauchbier | 6B Rauchbier | high | Same beechwood-smoked Märzen from Bamberg: toasted malt sweetness balanced with smooth smoke; 6B is defined as the Märzen-based Rauchbier. BA colour starts paler (SRM 4 vs 12). | 5.1–6 | 4.8–6 | 18–25 | 20–30 |  |
| `belgian-style-blonde-ale` | Belgian-Style Blonde Ale | 25A Belgian Blond Ale | high | Same golden, moderately strong, fruity, lightly spicy Belgian blond with low-medium bitterness; vitals overlap. | 6.3–7.9 | 6–7.5 | 15–40 | 15–30 |  |
| `belgian-style-dubbel` | Belgian-Style Dubbel | 26B Belgian Dubbel | high | Same malty, dark-fruit, caramel Belgian dubbel with low clove phenols; BA colour range is darker (SRM 16–36 vs 10–17). | 6.3–7.6 | 6–7.6 | 20–40 | 15–25 |  |
| `belgian-style-fruit-lambic` | Belgian-Style Fruit Lambic | 23F Fruit Lambic | high | Same lambic/gueuze with fruit (kriek, framboise, etc.), sour and funky; vitals overlap. | 4–9 | 5–7 | 10–15 | 0–10 |  |
| `belgian-style-lambic` | Belgian-Style Lambic | 23D Lambic | high | Same spontaneously fermented, sour, funky Brussels wheat beer with aged hops; BA allows higher IBU (11–23 vs 0–10) and ABV (to 8.0). | 5–8 | 5–6.5 | 11–23 | 0–10 |  |
| `belgian-style-speciale-belge` | Belgian-Style Speciale Belge | 24B Belgian Pale Ale | high | Same amber, fruity, lightly phenolic, moderately bitter Belgian pale ale; 24B is "A Spéciale Belge Ale"; BA ABV a little higher (5.0–6.2 vs 4.8–5.5). | 5–6.2 | 4.8–5.5 | 20–30 | 20–30 |  |
| `belgian-style-strong-blonde-ale` | Belgian-Style Strong Blonde Ale | 25C Belgian Golden Strong Ale | high | Same very pale, strong, fruity, lightly phenolic Belgian ale brewed with pale candi sugar and deceptive strength; vitals overlap. | 7.1–11.2 | 7.5–10.5 | 20–50 | 22–35 |  |
| `belgian-style-strong-dark-ale` | Belgian-Style Strong Dark Ale | 26D Belgian Dark Strong Ale | high | Same strong, dark, rich, fruity Belgian ale brewed with dark candi sugar; BA allows soft roast where 26D has none. | 7.1–11.2 | 8–12 | 20–50 | 20–35 |  |
| `belgian-style-tripel` | Belgian-Style Tripel | 26C Belgian Tripel | high | Same strong, pale, spicy-fruity Belgian tripel with firm bitterness and a dry finish; vitals overlap. | 7.1–10.1 | 7.5–9.5 | 20–50 | 20–40 |  |
| `belgian-style-witbier` | Belgian-Style Witbier | 24A Witbier | high | Same hazy wheat beer with unmalted wheat, coriander and orange peel, low bitterness; vitals match. | 4–5.5 | 4.5–5.5 | 10–17 | 8–20 |  |
| `berliner-style-weisse` | Berliner-Style Weisse | 23A Berliner Weisse | high | Same very pale, low-alcohol, highly carbonated lactic wheat beer with no hop character; BA ABV reaches 5.0 vs 3.8. | 2.8–5 | 2.8–3.8 | 3–6 | 3–8 |  |
| `british-style-barley-wine-ale` | British-Style Barley Wine Ale | 17D English Barley Wine | high | Same strong, very malty, estery English barley wine with English hops and vinous age notes; vitals match. | 8.5–12.2 | 8–12 | 40–65 | 35–70 |  |
| `british-style-imperial-stout` | British-Style Imperial Stout | 20C Imperial Stout | high | Strong, very dark stout with rich toffee/caramel malt, esters and restrained roast — the English interpretation that 20C covers alongside the American one; BA IBU 45–65 vs 50–90. | 7–12 | 8–12 | 45–65 | 50–90 |  |
| `british-style-india-pale-ale` | British-Style India Pale Ale | 12C English IPA | high | Same hoppy, bitter, estery British IPA with English hop character and optional Burton sulfate; vitals overlap closely. | 4.5–7.1 | 5–7.5 | 35–63 | 40–60 |  |
| `brown-porter` | Brown Porter | 13C English Porter | high | Same brown English porter: caramel and chocolate, no strong roast or burnt malt, medium bitterness; vitals overlap. | 4.4–6 | 4–5.4 | 20–30 | 18–35 |  |
| `california-common-beer` | California Common Beer | 19B California Common | high | Same toasty-caramel, firmly bitter amber beer fermented warm with lager yeast; vitals match. | 4.6–5.7 | 4.5–5.5 | 35–45 | 30–45 |  |
| `classic-irish-style-dry-stout` | Classic Irish-Style Dry Stout | 15B Irish Stout | high | Same black, dry stout with coffee-like roasted barley and dry-roast bitterness; vitals match. | 4.1–5.3 | 3.8–5 | 30–40 | 25–45 |  |
| `czech-style-amber-lager` | Czech-Style Amber Lager | 3C Czech Amber Lager | high | Same polotmavé lager: complex biscuit/toast/caramel malt, noble hops, low diacetyl; vitals identical. | 4.4–5.8 | 4.4–5.8 | 20–35 | 20–35 |  |
| `czech-style-dark-lager` | Czech-Style Dark Lager | 3D Czech Dark Lager | high | Same tmavé lager: rich caramel/bread/chocolate malt, light roast, noble hops; vitals identical. | 4.4–5.8 | 4.4–5.8 | 18–35 | 18–34 |  |
| `czech-style-pale-lager` | Czech-Style Pale Lager | 3B Czech Premium Pale Lager | high | Same Pilsner-type Czech lager at 11–13 °P: bready-biscuity malt, late noble (Saaz-type) hops, decoction, low diacetyl allowed; BA's IBU floor (20) sits below 3B's (30). | 4.6–5.1 | 4.2–5.8 | 20–45 | 30–45 |  |
| `english-style-brown-ale` | English-Style Brown Ale | 13B British Brown Ale | high | Same malty British brown ale with toasty/biscuit malt and low bitterness, not porter-roasty; vitals match. | 4.2–6 | 4.2–5.9 | 12–25 | 20–30 |  |
| `english-style-dark-mild-ale` | English-Style Dark Mild Ale | 13A Dark Mild | high | Same dark, low-gravity, malt-focused British mild with caramel/roast notes and low bitterness; BA ABV a little higher (3.4–4.4 vs 3.0–3.8). | 3.4–4.4 | 3–3.8 | 10–24 | 10–25 |  |
| `export` | Export | 5C German Helles Exportbier | high | Stored name "Export" is BA's Dortmunder/European-Style Export: pale, medium body, balanced malt and noble hops, medium bitterness — the Dortmunder that 5C describes; vitals match. | 5.1–6.1 | 5–6 | 23–30 | 20–30 |  |
| `export-style-stout` | Export-Style Stout | 16D Foreign Extra Stout | high | Same stronger black stout with prominent coffee-like roast and dry-roasted bitterness; 16D is "also known as ... Export Stout"; BA IBU starts lower (30 vs 50). | 5.6–8 | 6.3–8 | 30–60 | 50–70 |  |
| `extra-special-bitter` | Extra Special Bitter | 11C Strong Bitter | high | Same stronger British bitter with biscuit/toast/nutty malt and English hops; 11C names "ESB" as this beer; vitals match. | 4.8–5.8 | 4.6–6.2 | 30–45 | 30–50 |  |
| `finnish-style-sahti` | Finnish-Style Sahti | 27I Historical Beer: Sahti | high | Same strong, sweet, unboiled Finnish farmhouse beer with juniper and baker's-yeast banana/clove; vitals overlap. | 7–8.5 | 7–11 | 3–16 | 0–15 |  |
| `french-style-biere-de-garde` | French-Style Bière de Garde | 24C Bière de Garde | high | Same toasty-malty, lagered French farmhouse ale in blond to brown; BA ABV starts lower (4.4 vs 6.0). | 4.4–8 | 6–8.5 | 20–30 | 18–28 |  |
| `german-style-altbier` | German-Style Altbier | 7B Altbier | high | Same copper, bitter, malty Düsseldorf ale with Munich-malt toast and noble hops, cool-fermented and lagered; BA allows a touch of roast (7B: none). | 4.6–5.6 | 4.3–5.5 | 25–52 | 25–50 |  |
| `german-style-doppelbock` | German-Style Doppelbock | 9A Doppelbock | high | Same very malty, strong bock with toasted malt, caramel/toffee and dark-fruit notes and low bitterness; BA's ABV range is lower (6.6–7.9 vs 7.0–10.0). | 6.6–7.9 | 7–10 | 17–27 | 16–26 |  |
| `german-style-eisbock` | German-Style Eisbock | 9B Eisbock | high | Same freeze-concentrated doppelbock: very high sweet malt, dark fruit, no hops, alcohol warmth; vitals match. | 8.6–14.3 | 9–14 | 26–33 | 25–35 |  |
| `german-style-heller-bock-maibock` | German-Style Heller Bock/Maibock | 4C Helles Bock | high | Same pale, strong, bready-toasty German bock with noble hops and no caramel/roast; BA ABV reaches 8.1 vs 7.4. | 6.3–8.1 | 6.3–7.4 | 20–38 | 23–35 |  |
| `german-style-koelsch` | German-Style Koelsch | 5B Kolsch | high | Same pale, crisp, delicately fruity top-fermented and cold-aged Cologne ale with noble hops and medium bitterness; vitals match. | 4.8–5.3 | 4.4–5.2 | 22–30 | 18–30 |  |
| `german-style-leichtbier` | German-Style Leichtbier | 5A German Leichtbier | high | Same pale, light-bodied, low-alcohol German lager with medium bitterness; vitals identical. | 2.5–3.7 | 2.4–3.6 | 16–24 | 15–28 |  |
| `german-style-maerzen` | German-Style Maerzen | 6A Marzen | high | Same toasty-bready, malty amber lager with muted bitterness; BA's colour range starts paler (SRM 4 vs 8). | 5.1–6 | 5.6–6.3 | 18–25 | 18–24 |  |
| `german-style-oktoberfest-festbier` | German-Style Oktoberfest/Festbier | 4B Festbier | high | Same golden Wiesn beer: clean, soft, bready malt, low bitterness, pale gold; vitals match. | 5.1–6.1 | 5.8–6.3 | 23–29 | 18–25 |  |
| `german-style-pilsener` | German-Style Pilsener | 5D German Pils | high | Same pale, crisp, bitter German lager with pronounced late noble-hop aroma; BA IBU reaches 50, 5D 40. | 4.6–5.3 | 4.4–5.2 | 25–50 | 22–40 |  |
| `german-style-schwarzbier` | German-Style Schwarzbier | 8B Schwarzbier | high | Same very dark German lager with mild roast and no burnt or roast bitterness; BA's ABV range is a little lower (3.8–4.9 vs 4.4–5.4). | 3.8–4.9 | 4.4–5.4 | 22–30 | 20–35 |  |
| `golden-or-blonde-ale` | Golden or Blonde Ale | 18A Blonde Ale | high | Same easy-drinking, pale, malt-leaning American ale with low-medium hops and bitterness; 18A is "sometimes known as Golden Ale"; vitals match. | 4.1–5.1 | 3.8–5.5 | 15–25 | 15–28 |  |
| `grodziskie` | Grodziskie | 27E Historical Beer: Piwo Grodziskie | high | Same low-gravity, oak-smoked wheat ale with clean bitterness and no sourness; vitals match. | 2.5–3.3 | 2.5–3.3 | 20–30 | 20–35 |  |
| `imperial-red-ale` | Imperial Red Ale | 22B American Strong Ale | high | Same imperial-strength red ale: big caramel malt, high hops and very high bitterness; 22B describes "imperial strength versions of American amber or red ales". | 8–10.6 | 6.3–10 | 55–85 | 50–100 |  |
| `india-pale-ale` | India Pale Ale | 22A Double IPA | high | Stored name "India Pale Ale" (code india-pale-ale) is BA's American-Style Imperial or Double IPA: same intensely hoppy, very bitter, strong pale ale; vitals match. | 7.6–10.6 | 7.5–10 | 65–100 | 60–100 |  |
| `international-style-pilsener` | International-Style Pilsener | 2A International Pale Lager | high | Same international pale adjunct lager (corn/rice/sugar), low to medium hops, often sold as "pilsner"; 2A says it is "often confusingly labeled as a Pilsner". | 4.6–5.3 | 4.5–6 | 15–40 | 18–25 |  |
| `irish-style-red-ale` | Irish-Style Red Ale | 15A Irish Red Ale | high | Same caramel-toasty Irish red ale with a light roast-barley finish and medium bitterness; vitals match. | 4–4.8 | 3.8–5 | 20–28 | 18–28 |  |
| `juicy-or-hazy-india-pale-ale` | Juicy or Hazy India Pale Ale | 21C Hazy IPA | high | Same hazy, juicy, fruit-forward IPA with soft bitterness and fuller body; 21C is "also known as New England IPA"; vitals match. | 6.3–7.5 | 6–9 | 20–50 | 25–60 |  |
| `kentucky-common-beer` | Kentucky Common Beer | 27B Historical Beer: Kentucky Common | high | Same corn-grist, sweet-malty, highly carbonated amber saloon ale from Louisville; BA allows a very slight tartness (27B: none). | 4–5.5 | 4–5.5 | 15–30 | 15–30 |  |
| `leipzig-style-gose` | Leipzig-Style Gose | 23G Gose | high | Same tart, lightly salted, coriander-spiced wheat beer with lactic sourness and very low bitterness; vitals match. | 4.4–5.4 | 4.2–4.8 | 5–15 | 5–12 |  |
| `mexican-style-pale-lager` | Mexican-Style Pale Lager | 2A International Pale Lager | high | Same pale adjunct lager with low hops and a dry finish; 2A names Corona Extra and lets entrants specify "Mexican lager". | 4.5–5 | 4.5–6 | 15–22 | 18–25 |  |
| `munich-style-dunkel` | Munich-Style Dunkel | 8A Munich Dunkel | high | Same brown Munich lager: chocolate/bread/biscuit malt from dark Munich malt, minimal roast, noble hops; vitals match. | 4.8–5.3 | 4.5–5.6 | 16–25 | 18–28 |  |
| `munich-style-helles` | Munich-Style Helles | 4A Munich Helles | high | Same pale malt-forward Munich lager: pronounced bready malt, no caramel, low noble hops, low bitterness; vitals match. | 4.8–5.6 | 4.7–5.4 | 15–25 | 16–22 |  |
| `oatmeal-stout` | Oatmeal Stout | 16B Oatmeal Stout | high | Same full, silky stout with oatmeal, coffee/chocolate/caramel roast and medium bitterness; vitals match. | 3.8–6.1 | 4.2–5.9 | 20–40 | 25–40 |  |
| `old-ale` | Old Ale | 17B Old Ale | high | Same aged, malty, estery English strong ale with oxidative, vinous character and optional Brett/acidity; vitals match. | 6.3–9.1 | 5.5–9 | 30–60 | 30–60 |  |
| `ordinary-bitter` | Ordinary Bitter | 11A Ordinary Bitter | high | Same low-gravity, bitter British session ale with low-medium malt sweetness, esters and low cask carbonation; vitals overlap closely. | 3–4.2 | 3.2–3.8 | 20–35 | 25–35 |  |
| `robust-porter` | Robust Porter | 20A American Porter | high | Same black, roasty, cocoa-and-caramel porter with medium-high bitterness; 20A is "sometimes called Robust Porter"; vitals overlap. | 5.1–6.6 | 4.8–6.5 | 25–40 | 25–50 |  |
| `saison` | Saison | 25B Saison | high | Stored name "Saison" is BA's Classic French & Belgian-Style Saison: same dry, highly attenuated, fruity-peppery farmhouse ale; BA allows traces of Brett (25B sends Brett saisons to 28A). | 4.5–6.5 | 3.5–9.5 | 20–38 | 20–35 |  |
| `scotch-ale-or-wee-heavy` | Scotch Ale or Wee Heavy | 17C Wee Heavy | high | Same strong, aggressively malty, caramel-rich Scottish ale with very low hops; BA allows peat smoke, 17C does not. | 6.6–8.5 | 6.5–10 | 25–35 | 17–35 |  |
| `scottish-style-export-ale` | Scottish-Style Export Ale | 14C Scottish Export | high | Same sweet-malt and caramel Scottish 80/- ale with low-medium bitterness; BA allows low peat smoke where 14C has none. | 4.1–6 | 3.9–6 | 15–25 | 15–30 |  |
| `scottish-style-heavy-ale` | Scottish-Style Heavy Ale | 14B Scottish Heavy | high | Same malty, caramel, low-bitterness Scottish 70/- ale; BA allows low peat smoke where 14B has none. | 3.5–4.1 | 3.3–3.9 | 12–20 | 10–20 |  |
| `south-german-style-hefeweizen` | South German-Style Hefeweizen | 10A Weissbier | high | Same pale, cloudy, highly carbonated ≥50 % wheat beer with banana esters and clove phenols; vitals match. | 4.9–5.6 | 4.3–5.6 | 10–15 | 8–15 |  |
| `south-german-style-kristal-weizen` | South German-Style Kristal Weizen | 10A Weissbier | high | The filtered version of the same Weissbier; 10A says "Kristall versions are filtered for brilliant clarity". | 4.9–5.6 | 4.3–5.6 | 10–15 | 8–15 |  |
| `south-german-style-weizenbock` | South German-Style Weizenbock | 10C Weizenbock | high | Same bock-strength wheat beer, pale or dark, with banana-clove yeast and rich malt; vitals match. | 7–9.5 | 6.5–9 | 15–35 | 15–30 |  |
| `special-bitter-or-best-bitter` | Special Bitter or Best Bitter | 11B Best Bitter | high | Same medium-strength British bitter: more malt than an ordinary, medium bitterness, esters, low carbonation; BA ABV starts a little higher (4.2 vs 3.8). | 4.2–4.8 | 3.8–4.6 | 28–40 | 25–40 |  |
| `sweet-stout-or-cream-stout` | Sweet Stout or Cream Stout | 16A Sweet Stout | high | Same black, full-bodied sweet stout with chocolate/caramel, mild roast, low bitterness, lactose allowed; 16A gives "Cream" stout as its historical name. | 3.2–6.3 | 4–6 | 15–25 | 20–40 |  |
| `traditional-belgian-style-gueuze` | Traditional Belgian-Style Gueuze | 23E Gueuze | high | Same blend of young and old lambic: dry, sour, funky, spontaneously fermented; BA IBU 11–23 vs 0–10. | 5–8 | 5–8 | 11–23 | 0–10 |  |
| `traditional-german-style-bock` | Traditional German-Style Bock | 6C Dunkles Bock | high | Same dark, all-malt bock: sweet, toasted/nutty malt, no caramel or roast, very low hops; vitals match. | 6.3–7.6 | 6.3–7.2 | 20–30 | 20–27 |  |
| `vienna-style-lager` | Vienna-Style Lager | 7A Vienna Lager | high | Same amber Vienna lager: lightly toasted malt, light sweetness, low noble hops, clean dry finish; vitals match. | 4.8–5.4 | 4.7–5.5 | 20–26 | 18–30 |  |
| `weizen` | Weizen | 10B Dunkles Weissbier | high | Stored name "Weizen" is BA's South German-Style Dunkel Weizen: same dark wheat beer with chocolate/caramel malt and banana-clove yeast; vitals match. | 4.8–5.4 | 4.3–5.6 | 10–15 | 10–18 |  |
| `west-coast-style-india-pale-ale` | West Coast-Style India Pale Ale | 21A American IPA | high | Same dry, very pale, sharply bitter IPA; 21A says "West Coast IPA ... is really just a type of American IPA". | 6.3–7.5 | 5.5–7.5 | 50–75 | 40–70 |  |
| `adambier` | Adambier | — | high | Strong, dark, hoppy, often barrel-aged and soured Dortmund ale; BJCP has no Adambier. | 9–11 |  | 30–50 |  |  |
| `aged-beer` | Aged Beer | — | high | Any beer aged over a year in non-wood vessels; BJCP has no such style. |  |  |  |  |  |
| `american-belgo-style-ale` | American-Belgo-Style Ale | — | high | Catch-all for Belgian yeast in non-Belgian styles or American hops in Belgian styles; no single BJCP style (21B Belgian IPA or 34B Mixed-Style). |  |  |  |  |  |
| `american-style-imperial-porter` | American-Style Imperial Porter | — | high | Strong black porter with caramel/cocoa and no roast-barley bite, ale-fermented; BJCP has none (20A tops at 6.5 %, 9C Baltic Porter is a lager). | 7–12 |  | 35–50 |  |  |
| `american-style-malt-liquor` | American-Style Malt Liquor | — | high | Strong (6.3–7.6 %), very dry, unhopped pale adjunct lager; no BJCP style covers it. | 6.3–7.6 |  | 12–23 |  |  |
| `belgian-style-session-ale` | Belgian-Style Session Ale | — | high | Catch-all for Belgian beers at 2.1–5 % that fit no other Belgian style; no single BJCP style. | 2.1–5 |  | 5–35 |  |  |
| `belgian-style-table-beer` | Belgian-Style Table Beer | — | high | Very low-alcohol (0.5–2.0 %) Belgian tafelbier, often sweetened; no BJCP style. | 0.5–2 |  | 5–15 |  |  |
| `breslau-style-schoeps` | Breslau-Style Schoeps | — | high | Strong, malty, up to 80 % wheat ale without weizen yeast; BJCP has no such style. | 6–7 |  | 20–30 |  |  |
| `contemporary-style-gose` | Contemporary-Style Gose | — | high | Gose with fruit, spices, dark malts or other added ingredients; BJCP files these under catch-alls (29A Fruit Beer, 30A, 29B), not under 23G. | 4.4–5.4 |  | 5–30 |  |  |
| `dutch-style-kuit-kuyt-or-koyt` | Dutch-Style Kuit, Kuyt or Koyt | — | high | Historic Dutch oat (≥45 %) and wheat ale; BJCP has no such style. | 4.7–7.9 |  | 25–35 |  |  |
| `english-style-pale-mild-ale` | English-Style Pale Mild Ale | — | high | Light-amber, malt-led mild; BJCP describes only the dark mild (13A says pale versions exist but are not covered). | 3.4–4.4 |  | 10–20 |  |  |
| `franconian-style-rotbier` | Franconian-Style Rotbier | — | high | Red-amber Franconian lager with toasted/caramel malt; BJCP has no Rotbier (nearest 7A Vienna Lager, but darker and sweeter). | 4.8–5.4 |  | 22–28 |  |  |
| `fresh-hop-beer` | Fresh Hop Beer | — | high | Any style brewed with freshly harvested hops; BJCP has no such style. |  |  |  |  |  |
| `german-style-leichtes-weizen` | German-Style Leichtes Weizen | — | high | Light (2.5–3.5 %) Hefeweizen; 10A's ABV starts at 4.3 and 5A says Leicht versions of Weissbier go to 34B Mixed-Style. | 2.5–3.5 |  | 10–15 |  |  |
| `ginjo-beer-or-sake-yeast-beer` | Ginjo Beer or Sake-Yeast Beer | — | high | Beer fermented with sake yeast or koji; BJCP has no such style (31A says sake is not intended there). | 4.3–10.2 |  | 12–35 |  |  |
| `gluten-free-beer` | Gluten-Free Beer | — | high | Defined by gluten-free ingredients, not by sensory profile; BJCP has no such style. |  |  |  |  |  |
| `historical-beer` | Historical Beer | — | high | Catch-all for historical beers not defined elsewhere (chicha, sorghum beers); BJCP's 27 has only named historical styles, each its own row. |  |  |  |  |  |
| `italian-style-pilsener` | Italian-Style Pilsener | — | high | A German-type pils dry-hopped with noble hops; BJCP has no such style (Tipopils is a 34B Mixed-Style example), and 5D German Pils is late-hopped, not dry-hopped. | 4.6–5.3 |  | 25–50 |  |  |
| `mexican-style-amber-lager` | Mexican-Style Amber Lager | — | high | Unpaired on purpose: brief b22 expects this BA pick. On content alone it is close to 2B International Amber Lager (2B lists Dos Equis Amber). | 4–5.5 |  | 12–25 |  |  |
| `non-alcohol-malt-beverage` | Non-Alcohol Malt Beverage | — | high | Any style below 0.5 % ABV; BJCP has no such style. |  |  |  |  |  |
| `other-belgian-style-ale` | Other Belgian-Style Ale | — | high | Catch-all for Belgian beers outside the defined styles; no single BJCP style. |  |  |  |  |  |
| `other-strong-ale-or-lager` | Other Strong Ale or Lager | — | high | Any style brewed above its normal strength; BJCP has no such style. |  |  |  |  |  |
| `session-beer` | Session Beer | — | high | Catch-all for lower-strength (≤5 %) versions of any style; no BJCP style. | 0.5–5 |  | 10–35 |  |  |
| `session-india-pale-ale` | Session India Pale Ale | — | high | Unpaired on purpose: brief b21 expects this BA pick. BJCP has no session IPA (18B mentions them only as a comparison). | 0.5–5 |  | 20–55 |  |  |
| `specialty-saison` | Specialty Saison | — | high | Saison with dark malts, fruit, spices, wood or special yeasts; BJCP has no own style (catch-alls 28A/29/30/33). | 5–9.3 |  | 20–40 |  |  |
| `spontaneous-fermented-ale` | Spontaneous Fermented Ale | — | high | Stored name is BA's Contemporary Belgian-Style Spontaneous Fermented Ale: gueuze-inspired but with specialty malts, spices or fruit, so it is not 23E; BJCP catch-alls only. | 5–8.9 |  | 11–23 |  |  |
| `swedish-style-gotlandsdricke` | Swedish-Style Gotlandsdricke | — | high | Juniper and birch-smoked Gotland farmhouse ale with baker's yeast; BJCP has no such style. | 5.5–6.5 |  | 15–25 |  |  |
| `west-coast-style-pilsener` | West Coast-Style Pilsener | — | high | Pilsener dry-hopped with Pacific Northwest/Southern Hemisphere IPA hops; BJCP has no such style (34B Mixed-Style catch-all). | 5–6 |  | 30–50 |  |  |
| `wild-beer` | Wild Beer | — | high | Spontaneously fermented beer from local airborne microbes, not lambic; BJCP has no such style (28 uses cultured microbes). |  |  |  |  |  |
