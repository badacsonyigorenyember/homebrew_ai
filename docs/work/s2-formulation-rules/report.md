# s2-formulation-rules: data report

Written during Task 4 (2026-10-15). Loaded after the user's answers (section 6).

## 1. Questions for the user (Task 4 stop)

Short answers are fine.

1. **Sprau Malt's role.** a) adjunct (recommended), b) base, c) kilned. Hopline calls it a malted
   field bean, max 15 %. Answer: `a`.
2. **The 7 proposed 90-minute boils** (section 3). Answer: `all as proposed`, or `Viking Wheat 60`
   to set one back to 60.
3. **The style name to code table** (section 4, 247 rows, 21 dropped). Answer: `all as proposed`,
   or change rows: `Imperial Pilsner -> dropped`, `Barley wine -> 22C`.
4. **The basis of the 18 `max_pct` values** (section 5). Answer: `all as drafted`, or per value:
   `Honey: forum consensus`, `Lactose: user decision E`. Values the user cannot place get "user
   decision E, 2026-10-14". The source stays `user-supplied` for all 18.

## 2. Rows with no stated enzyme activity (R3: nothing guessed)

30 of 81 rows. The Weyermann catalogue states a level for 36 of its 37 malts (Acidulated says
only that it "increases enzyme activity by optimal mash pH"). For Viking, a level that maps to our
scale is printed for Munich Light/Dark (reduced), Red Ale (low), Red Active (strong), the eight
caramel malts and the two chocolate malts and Black Malt (zero). Caramel Pale ("negligible"),
Dextrin ("modest"), Golden Ale ("reduced"), Vienna ("slightly lower") and Wheat ("modest
alpha-amylase") are described in words that do not map to none/low/normal/high, so they stay
empty, as do the rest. The 7 adjuncts and sugars are not malts.

- Simpsons Malt Crystal Extra Dark
- Simpsons Malt Crystal T50
- Simpsons Malt DRC
- Simpsons Malt Finest Pale Ale Golden Promise
- Simpsons Malt Finest Pale Ale Maris Otter
- Viking Malt CaraBody Malt
- Viking Malt Caramel Pale Malt
- Viking Malt Cookie Malt
- Viking Malt Dextrin Malt
- Viking Malt Enzyme Malt
- Viking Malt Golden Ale Malt
- Viking Malt Lightly Peated Malt
- Viking Malt Pale Ale Malt
- Viking Malt Pilsner Malt
- Viking Malt Roasted Barley
- Viking Malt Rye Malt
- Viking Malt Smoked Malt (cherry wood)
- Viking Malt Smoked Malt (pear wood)
- Viking Malt Smoked Wheat Malt
- Viking Malt Sprau Malt
- Viking Malt Vienna Malt
- Viking Malt Wheat Malt
- Weyermann Acidulated Malt
- Brown Candi Sugar
- Flaked Barley
- Flaked Corn
- Flaked Oats
- Flaked Rice
- Honey
- Lactose

## 3. Proposed minimum boils above 60 minutes

Rule: role `base` and colour midpoint below 5 EBC. How to Brew p. 177: "A 90-min. boil is
recommended for pale lagers that use a majority of Pilsner malt"; p. 59: "60-90 minutes is
considered the norm". Every other row gets 60. Sprau is not listed because its role is open (as
`adjunct` it gets 60; as `base` with 4 EBC it would be proposed at 90).

| Row | EBC | Minutes |
|---|---|---|
| Viking Pilsner Malt | 3.0-4.2 | 90 |
| Viking Wheat Malt | 3.0-5.5 | 90 |
| Weyermann Pilsner Malt | 2.5-4.5 | 90 |
| Weyermann Extra Pale Premium Pilsner Malt | 2-3.5 | 90 |
| Weyermann Eraclea Pilsner Malt | 2.5-4.5 | 90 |
| Weyermann Bohemian Pilsner Malt | 3-5 | 90 |
| Weyermann Wheat Malt Pale | 3-5 | 90 |

## 4. Style name to code table

Every distinct style name the maltsters print, case ignored (spellings joined with " / "), the
one `ref.beer_style` row it maps to (decision H: the closest style we use, BJCP 2021 preferred,
BA 2026 where BJCP has none), or **dropped** where no style we use fits. "Malts" counts the
malts that print the name. Codes were checked against `ref.beer_style`. Generic words (ales,
lagers, porters, stouts, brown ale, special beer) are dropped on purpose; named styles are
mapped even when the match is loose (for example Imperial Pilsner -> 5D, Oyster Stout -> 15B,
Barley wine -> 17D, Red Ale -> 19A, Bohemian Bock -> traditional-german-style-bock).

| Printed name | Code | Maps to | Malts |
|---|---|---|---|
| Alcohol-free beer | `non-alcohol-malt-beverage` | Non-Alcohol Malt Beverage (BA 2026) | 1 |
| Alcohol-reduced beer | **dropped** |  | 1 |
| ale-type beers | **dropped** |  | 8 |
| ales | **dropped** |  | 4 |
| Altbier | `7B` | Altbier (BJCP 2021) | 8 |
| Alternative Grain Beer | `31A` | Alternative Grain Beer (BJCP 2021) | 1 |
| Amber Ale | `19A` | American Amber Ale (BJCP 2021) | 1 |
| Amber Lager | `2B` | International Amber Lager (BJCP 2021) | 1 |
| Amber wheat | `bernsteinfarbenes-weizen` | Bernsteinfarbenes Weizen (BA 2026) | 1 |
| American (Light) Lager | `1A` | American Light Lager (BJCP 2021) | 2 |
| American Barley Wine / American Barley wine | `22C` | American Barleywine (BJCP 2021) | 3 |
| American Brown Ale | `19C` | American Brown Ale (BJCP 2021) | 4 |
| American Cream Ale | `1C` | Cream Ale (BJCP 2021) | 1 |
| American IPA | `21A` | American IPA (BJCP 2021) | 5 |
| American Lager | `1B` | American Lager (BJCP 2021) | 1 |
| American Pale Ale | `18B` | American Pale Ale (BJCP 2021) | 5 |
| American Pilsener | `american-style-pilsener` | American-Style Pilsener (BA 2026) | 2 |
| American Porter | `20A` | American Porter (BJCP 2021) | 8 |
| American Red Ale | `19A` | American Amber Ale (BJCP 2021) | 4 |
| American Stout | `20B` | American Stout (BJCP 2021) | 4 |
| American Strong Ale | `22B` | American Strong Ale (BJCP 2021) | 4 |
| American Wheat Beer | `1D` | American Wheat Beer (BJCP 2021) | 2 |
| American Wheat Wine | `22D` | Wheatwine (BJCP 2021) | 2 |
| American-Style India Pale Ale | `21A` | American IPA (BJCP 2021) | 1 |
| APA | `18B` | American Pale Ale (BJCP 2021) | 2 |
| Australian Sparkling Ale | `12B` | Australian Sparkling Ale (BJCP 2021) | 3 |
| Baltic Porter | `9C` | Baltic Porter (BJCP 2021) | 7 |
| Bamberg Weisse Rauchbier | `bamberg-style-weiss-rauchbier` | Bamberg-Style Weiss Rauchbier (BA 2026) | 1 |
| Bamberg Weisse Smoked beer | `bamberg-style-weiss-rauchbier` | Bamberg-Style Weiss Rauchbier (BA 2026) | 1 |
| Bamberg Weizen Rauchbier | `bamberg-style-weiss-rauchbier` | Bamberg-Style Weiss Rauchbier (BA 2026) | 1 |
| Bamberger Maerzen | `bamberg-style-maerzen-rauchbier` | Bamberg-Style Maerzen Rauchbier (BA 2026) | 4 |
| Bamberger Maerzen Rauchbier | `bamberg-style-maerzen-rauchbier` | Bamberg-Style Maerzen Rauchbier (BA 2026) | 2 |
| Bamberger Rauchbier | `6B` | Rauchbier (BJCP 2021) | 2 |
| Barley wine / Barley Wine | `17D` | English Barley Wine (BJCP 2021) | 4 |
| Barleywine | `17D` | English Barley Wine (BJCP 2021) | 2 |
| Bavarian Helles | `4A` | Munich Helles (BJCP 2021) | 2 |
| Belgian beers | **dropped** |  | 1 |
| Belgian Blond Ale | `25A` | Belgian Blond Ale (BJCP 2021) | 1 |
| Belgian Dark Strong Ale or Quadrupel | `26D` | Belgian Dark Strong Ale (BJCP 2021) | 5 |
| Belgian Dubbel | `26B` | Belgian Dubbel (BJCP 2021) | 3 |
| Belgian Golden Strong Ale | `25C` | Belgian Golden Strong Ale (BJCP 2021) | 4 |
| Belgian IPA | `21B` | Specialty IPA (BJCP 2021) | 3 |
| Belgian Pale Ale | `24B` | Belgian Pale Ale (BJCP 2021) | 5 |
| Belgian Tripel | `26C` | Belgian Tripel (BJCP 2021) | 2 |
| Belgian Trippel | `26C` | Belgian Tripel (BJCP 2021) | 1 |
| Berliner Weisse | `23A` | Berliner Weisse (BJCP 2021) | 2 |
| Bernsteinfarbenes Weissbier | `bernsteinfarbenes-weizen` | Bernsteinfarbenes Weizen (BA 2026) | 3 |
| Bernsteinfarbenes Weizen | `bernsteinfarbenes-weizen` | Bernsteinfarbenes Weizen (BA 2026) | 2 |
| Best Bitter | `11B` | Best Bitter (BJCP 2021) | 3 |
| Biére de Garde | `24C` | Bière de Garde (BJCP 2021) | 6 |
| Black Ale | `21B` | Specialty IPA (BJCP 2021) | 4 |
| Black IPA | `21B` | Specialty IPA (BJCP 2021) | 8 |
| Blonde Ale | `18A` | Blonde Ale (BJCP 2021) | 5 |
| Bock | `traditional-german-style-bock` | Traditional German-Style Bock (BA 2026) | 1 |
| Bock Beer | `traditional-german-style-bock` | Traditional German-Style Bock (BA 2026) | 1 |
| bocks | `traditional-german-style-bock` | Traditional German-Style Bock (BA 2026) | 3 |
| Bohemian Bock | `traditional-german-style-bock` | Traditional German-Style Bock (BA 2026) | 1 |
| Bohemian Pilsener | `3B` | Czech Premium Pale Lager (BJCP 2021) | 1 |
| Bohemian Pilsner | `3B` | Czech Premium Pale Lager (BJCP 2021) | 1 |
| Braunbier | `8A` | Munich Dunkel (BJCP 2021) | 1 |
| British Brown Ale | `13B` | British Brown Ale (BJCP 2021) | 8 |
| British Golden Ale | `12A` | British Golden Ale (BJCP 2021) | 4 |
| British Strong Ale | `17A` | British Strong Ale (BJCP 2021) | 4 |
| Brown Ale | **dropped** |  | 3 |
| Brown IPA | `21B` | Specialty IPA (BJCP 2021) | 7 |
| Brown Porter | `13C` | English Porter (BJCP 2021) | 6 |
| California Common | `19B` | California Common (BJCP 2021) | 3 |
| Chocolate Porter | `20A` | American Porter (BJCP 2021) | 2 |
| Classic Style Smoked beer | `32A` | Classic Style Smoked Beer (BJCP 2021) | 1 |
| Coconut Porter | `20A` | American Porter (BJCP 2021) | 3 |
| Cream Ale | `1C` | Cream Ale (BJCP 2021) | 3 |
| Czech Amber Lager | `3C` | Czech Amber Lager (BJCP 2021) | 4 |
| Czech Dark Lager | `3D` | Czech Dark Lager (BJCP 2021) | 4 |
| Czech Pale Lager | `3A` | Czech Pale Lager (BJCP 2021) | 2 |
| dark ales | **dropped** |  | 2 |
| Dark Bock | `6C` | Dunkles Bock (BJCP 2021) | 3 |
| Dark Doppelbock | `9A` | Doppelbock (BJCP 2021) | 1 |
| Dark Double Bock | `9A` | Doppelbock (BJCP 2021) | 2 |
| Dark Lager | `2C` | International Dark Lager (BJCP 2021) | 2 |
| dark lagers / Dark Lagers | `2C` | International Dark Lager (BJCP 2021) | 12 |
| Dark Mild | `13A` | Dark Mild (BJCP 2021) | 7 |
| dark strong styles | **dropped** |  | 1 |
| Dark wheat / Dark Wheat | `10B` | Dunkles Weissbier (BJCP 2021) | 4 |
| Dark Wheat beer | `10B` | Dunkles Weissbier (BJCP 2021) | 1 |
| Dortmunder Export | `5C` | German Helles Exportbier (BJCP 2021) | 2 |
| Double Bock | `9A` | Doppelbock (BJCP 2021) | 2 |
| Double IPA | `22A` | Double IPA (BJCP 2021) | 4 |
| Dry Stout | `15B` | Irish Stout (BJCP 2021) | 2 |
| Dubbel | `26B` | Belgian Dubbel (BJCP 2021) | 1 |
| Dunkel Weizen | `10B` | Dunkles Weissbier (BJCP 2021) | 2 |
| Dunkles Weissbier | `10B` | Dunkles Weissbier (BJCP 2021) | 1 |
| Dunkles Weizen | `10B` | Dunkles Weissbier (BJCP 2021) | 3 |
| Eisbock | `9B` | Eisbock (BJCP 2021) | 1 |
| English Ale | **dropped** |  | 1 |
| English Barley Wine | `17D` | English Barley Wine (BJCP 2021) | 4 |
| English Bitter | `11A` | Ordinary Bitter (BJCP 2021) | 3 |
| English Dark Mild Ale | `13A` | Dark Mild (BJCP 2021) | 6 |
| English IPA | `12C` | English IPA (BJCP 2021) | 2 |
| English Pale Mild Ale | `english-style-pale-mild-ale` | English-Style Pale Mild Ale (BA 2026) | 6 |
| English Porter | `13C` | English Porter (BJCP 2021) | 8 |
| English Summer Ale | `english-style-summer-ale` | English-Style Summer Ale (BA 2026) | 3 |
| Extra Special Bitter | `11C` | Strong Bitter (BJCP 2021) | 4 |
| Festbier | `4B` | Festbier (BJCP 2021) | 2 |
| Festival beer | `4B` | Festbier (BJCP 2021) | 1 |
| festival beers | `4B` | Festbier (BJCP 2021) | 3 |
| Flanders Red Ale | `23B` | Flanders Red Ale (BJCP 2021) | 8 |
| Foreign Extra Stout | `16D` | Foreign Extra Stout (BJCP 2021) | 5 |
| Franconian Red Beer | `franconian-style-rotbier` | Franconian-Style Rotbier (BA 2026) | 2 |
| Franconian Rotbier | `franconian-style-rotbier` | Franconian-Style Rotbier (BA 2026) | 3 |
| Fruit Lambic | `23F` | Fruit Lambic (BJCP 2021) | 6 |
| German Leichtbier | `5A` | German Leichtbier (BJCP 2021) | 1 |
| German Light Beer | `5A` | German Leichtbier (BJCP 2021) | 1 |
| German Pilsener | `5D` | German Pils (BJCP 2021) | 1 |
| German Pilsner | `5D` | German Pils (BJCP 2021) | 1 |
| German Rye beer / German Rye Beer | `27H` | Historical Beer: Roggenbier (BJCP 2021) | 3 |
| Golden Ale | `12A` | British Golden Ale (BJCP 2021) | 2 |
| Golden Bitter | `12A` | British Golden Ale (BJCP 2021) | 1 |
| Gose | `23G` | Gose (BJCP 2021) | 5 |
| Gotlandsdricke | `swedish-style-gotlandsdricke` | Swedish-Style Gotlandsdricke (BA 2026) | 1 |
| grodziskie | `27E` | Historical Beer: Piwo Grodziskie (BJCP 2021) | 1 |
| Gueuze | `23E` | Gueuze (BJCP 2021) | 6 |
| Hazy IPA | `21C` | Hazy IPA (BJCP 2021) | 4 |
| Hazy Pale Ale | `juicy-or-hazy-pale-ale` | Juicy or Hazy Pale Ale (BA 2026) | 3 |
| Hefeweizen | `10A` | Weissbier (BJCP 2021) | 1 |
| Helles Bock | `4C` | Helles Bock (BJCP 2021) | 3 |
| hoppy beers | **dropped** |  | 1 |
| Ice Bock | `9B` | Eisbock (BJCP 2021) | 1 |
| Imperial PA | `22A` | Double IPA (BJCP 2021) | 1 |
| Imperial Pilsener | `5D` | German Pils (BJCP 2021) | 3 |
| Imperial Pilsner | `5D` | German Pils (BJCP 2021) | 1 |
| Imperial Porter | `american-style-imperial-porter` | American-Style Imperial Porter (BA 2026) | 8 |
| Imperial Red Ale | `imperial-red-ale` | Imperial Red Ale (BA 2026) | 9 |
| Imperial Stout | `20C` | Imperial Stout (BJCP 2021) | 7 |
| India Pale Lager | `american-style-india-pale-lager` | American-Style India Pale Lager (BA 2026) | 5 |
| International Amber Lager | `2B` | International Amber Lager (BJCP 2021) | 5 |
| International Dark Lager | `2C` | International Dark Lager (BJCP 2021) | 3 |
| International Pale Lager | `2A` | International Pale Lager (BJCP 2021) | 2 |
| International Pilsener | `international-style-pilsener` | International-Style Pilsener (BA 2026) | 1 |
| IPA | `21A` | American IPA (BJCP 2021) | 3 |
| IPAs | `21A` | American IPA (BJCP 2021) | 2 |
| Irish Extra Stout | `15C` | Irish Extra Stout (BJCP 2021) | 6 |
| Irish Red Ale | `15A` | Irish Red Ale (BJCP 2021) | 4 |
| Irish Stout | `15B` | Irish Stout (BJCP 2021) | 5 |
| Italian Grape Ale | `29D` | Grape Ale (BJCP 2021) | 1 |
| Italian Lager | `2A` | International Pale Lager (BJCP 2021) | 1 |
| Italian Pilsner | `italian-style-pilsener` | Italian-Style Pilsener (BA 2026) | 1 |
| Japanese Lager | `2A` | International Pale Lager (BJCP 2021) | 1 |
| Juicy IPA | `21C` | Hazy IPA (BJCP 2021) | 4 |
| Juicy Pale Ale | `juicy-or-hazy-pale-ale` | Juicy or Hazy Pale Ale (BA 2026) | 3 |
| Kellerbeer | `27A` | Historical Beer: Kellerbier (BJCP 2021) | 1 |
| Kellerbier | `27A` | Historical Beer: Kellerbier (BJCP 2021) | 4 |
| Kentucky Common | `27B` | Historical Beer: Kentucky Common (BJCP 2021) | 2 |
| Koelsch style beer | `5B` | Kolsch (BJCP 2021) | 1 |
| Koelsch-style | `5B` | Kolsch (BJCP 2021) | 2 |
| Kristal Weizen | `south-german-style-kristal-weizen` | South German-Style Kristal Weizen (BA 2026) | 2 |
| Kristallweizen | `south-german-style-kristal-weizen` | South German-Style Kristal Weizen (BA 2026) | 1 |
| Kölsch Style | `5B` | Kolsch (BJCP 2021) | 1 |
| lagers | **dropped** |  | 3 |
| Lambic | `23D` | Lambic (BJCP 2021) | 3 |
| Leichtes Weizen | `german-style-leichtes-weizen` | German-Style Leichtes Weizen (BA 2026) | 5 |
| Lichtenhainer | `27C` | Historical Beer: Lichtenhainer (BJCP 2021) | 4 |
| Light Beer | `light-lager` | Light Lager (BA 2026) | 1 |
| Light Lager | `light-lager` | Light Lager (BA 2026) | 1 |
| Light Lagers | `light-lager` | Light Lager (BA 2026) | 1 |
| London Brown Ale | `27D` | Historical Beer: London Brown Ale (BJCP 2021) | 4 |
| Maerzen | `6A` | Marzen (BJCP 2021) | 3 |
| Malt Beverage (nonalcoholic malt beer) | `non-alcohol-malt-beverage` | Non-Alcohol Malt Beverage (BA 2026) | 1 |
| Mediterranean Style Lager | `2A` | International Pale Lager (BJCP 2021) | 1 |
| Mediterranean Style Pilsner | `italian-style-pilsener` | Italian-Style Pilsener (BA 2026) | 1 |
| Mexican Lager | `mexican-style-pale-lager` | Mexican-Style Pale Lager (BA 2026) | 1 |
| Milk Stout | `16A` | Sweet Stout (BJCP 2021) | 2 |
| Multi-grain beer | `31A` | Alternative Grain Beer (BJCP 2021) | 1 |
| Multigrain beer | `31A` | Alternative Grain Beer (BJCP 2021) | 1 |
| Munich Dunkel | `8A` | Munich Dunkel (BJCP 2021) | 5 |
| Munich Helles | `4A` | Munich Helles (BJCP 2021) | 1 |
| Munich-Style Helles | `4A` | Munich Helles (BJCP 2021) | 1 |
| NEIPA | `21C` | Hazy IPA (BJCP 2021) | 5 |
| Non-alcoholic Beer | `non-alcohol-malt-beverage` | Non-Alcohol Malt Beverage (BA 2026) | 1 |
| Oatmeal Stout | `16B` | Oatmeal Stout (BJCP 2021) | 7 |
| Old Ale | `17B` | Old Ale (BJCP 2021) | 5 |
| Ordinary Bitter | `11A` | Ordinary Bitter (BJCP 2021) | 4 |
| Oud Bruin | `23C` | Oud Bruin (BJCP 2021) | 4 |
| Oyster Stout | `15B` | Irish Stout (BJCP 2021) | 1 |
| Pale Ale | `international-style-pale-ale` | International-Style Pale Ale (BA 2026) | 1 |
| Pale Kellerbier | `27A` | Historical Beer: Kellerbier (BJCP 2021) | 1 |
| Pale Lager | `2A` | International Pale Lager (BJCP 2021) | 1 |
| Pale Lager with Smoke | `32A` | Classic Style Smoked Beer (BJCP 2021) | 1 |
| pale lagers | `2A` | International Pale Lager (BJCP 2021) | 8 |
| Pils | `5D` | German Pils (BJCP 2021) | 1 |
| Pilsener | `5D` | German Pils (BJCP 2021) | 1 |
| Piwo Grodziskie | `27E` | Historical Beer: Piwo Grodziskie (BJCP 2021) | 3 |
| Porter | **dropped** |  | 4 |
| porters | **dropped** |  | 4 |
| Pre-Prohibition Lager | `27F` | Historical Beer: Pre-Prohibition Lager (BJCP 2021) | 2 |
| Pre-Prohibition Porter | `27G` | Historical Beer: Pre-Prohibition Porter (BJCP 2021) | 2 |
| premium lagers | **dropped** |  | 1 |
| Quadrupel | `26D` | Belgian Dark Strong Ale (BJCP 2021) | 1 |
| Rauchbier | `6B` | Rauchbier (BJCP 2021) | 4 |
| Rauchbierbock | `bamberg-style-bock-rauchbier` | Bamberg-Style Bock Rauchbier (BA 2026) | 1 |
| Red Ale | `19A` | American Amber Ale (BJCP 2021) | 4 |
| Red IPA | `21B` | Specialty IPA (BJCP 2021) | 4 |
| Robust Porter | `robust-porter` | Robust Porter (BA 2026) | 7 |
| Russian Imperial Stout | `20C` | Imperial Stout (BJCP 2021) | 8 |
| Rye Ale (Roggenbier) | `27H` | Historical Beer: Roggenbier (BJCP 2021) | 1 |
| Rye IPA | `21B` | Specialty IPA (BJCP 2021) | 2 |
| Rye Lager | **dropped** |  | 1 |
| Saison | `25B` | Saison (BJCP 2021) | 2 |
| Sathi | `27I` | Historical Beer: Sahti (BJCP 2021) | 4 |
| Scandinavian Red | `7A` | Vienna Lager (BJCP 2021) | 1 |
| Scandinavian Red Lager | `7A` | Vienna Lager (BJCP 2021) | 1 |
| Schwarzbier | `8B` | Schwarzbier (BJCP 2021) | 5 |
| Scotch Ale | `17C` | Wee Heavy (BJCP 2021) | 4 |
| Scottish and English beers | **dropped** |  | 1 |
| Scottish Export | `14C` | Scottish Export (BJCP 2021) | 3 |
| Scottish Heavy | `14B` | Scottish Heavy (BJCP 2021) | 3 |
| Scottish Light | `14A` | Scottish Light (BJCP 2021) | 5 |
| Season | `25B` | Saison (BJCP 2021) | 2 |
| Session IPA | `session-india-pale-ale` | Session India Pale Ale (BA 2026) | 5 |
| Session Pale Ale | `session-beer` | Session Beer (BA 2026) | 5 |
| Smoked beer | `32A` | Classic Style Smoked Beer (BJCP 2021) | 3 |
| Smoked Porter | `smoke-porter` | Smoke Porter (BA 2026) | 4 |
| Smoked Wheat beer | `bamberg-style-weiss-rauchbier` | Bamberg-Style Weiss Rauchbier (BA 2026) | 1 |
| Sour Beers | `28D` | Straight Sour Beer (BJCP 2021) | 1 |
| Special beer | **dropped** |  | 1 |
| Specialty Smoked beer | `32B` | Specialty Smoked Beer (BJCP 2021) | 1 |
| Spelt beer | `31A` | Alternative Grain Beer (BJCP 2021) | 1 |
| Stout | **dropped** |  | 2 |
| stouts | **dropped** |  | 12 |
| Strong Ale | `strong-ale` | Strong Ale (BA 2026) | 2 |
| Strong Bitter | `11C` | Strong Bitter (BJCP 2021) | 3 |
| Strong Lager | **dropped** |  | 1 |
| Summer Ale | `english-style-summer-ale` | English-Style Summer Ale (BA 2026) | 4 |
| Sweet Stout | `16A` | Sweet Stout (BJCP 2021) | 3 |
| top fermented beers | **dropped** |  | 1 |
| Top-fermented beer | **dropped** |  | 1 |
| Trappist Single | `26A` | Belgian Single (BJCP 2021) | 3 |
| Tropical Stout | `16C` | Tropical Stout (BJCP 2021) | 3 |
| Vienna lager / Vienna Lager | `7A` | Vienna Lager (BJCP 2021) | 5 |
| Weissbeer | `10A` | Weissbier (BJCP 2021) | 1 |
| Weissbier | `10A` | Weissbier (BJCP 2021) | 4 |
| Weizenbock | `10C` | Weizenbock (BJCP 2021) | 7 |
| wheat beers | `10A` | Weissbier (BJCP 2021) | 1 |
| Wheat Bock / Wheat bock | `10C` | Weizenbock (BJCP 2021) | 4 |
| Wheat Wine | `22D` | Wheatwine (BJCP 2021) | 6 |
| White IPA | `21B` | Specialty IPA (BJCP 2021) | 2 |
| winter beers | `30C` | Winter Seasonal Beer (BJCP 2021) | 8 |
| Witbier | `24A` | Witbier (BJCP 2021) | 4 |

## 5. The 18 `max_pct` values (user decision E) and their bases

The value is decision E in every row. "Drafted basis" is what Task 4 found in the repo and the
sources; `unplaced` means nothing found states the value, and the loader refuses it until you
place it. "Evidence" lists what the sources do say, so you can place it or call it user decision E.

| Ingredient | Value | Drafted basis | Evidence (for the unplaced) |
|---|---|---|---|
| Viking Malt Caramel 100 Malt | 15 | How to Brew estimate, printed p. 230: caramel malts are typically added as 5%-15% of the total grain bill (15 is the top of that range) |  |
| Viking Malt Caramel 150 Malt | 15 | How to Brew estimate, printed p. 230: caramel malts are typically added as 5%-15% of the total grain bill (15 is the top of that range) |  |
| Viking Malt Caramel 200 Malt | 15 | How to Brew estimate, printed p. 230: caramel malts are typically added as 5%-15% of the total grain bill (15 is the top of that range) |  |
| Viking Malt Caramel 30 Malt | 20 | unplaced | Nothing states 20. How to Brew p. 230 says caramel malts are typically 5%-15%; Viking Caramel Pale (p. 25) is 'up to 30%'. Chart substitute Carahell is up to 15% (Weyermann p. 17: 10-15%). |
| Viking Malt Caramel 300 Malt | 10 | unplaced | Nothing states 10 for Viking. Chart substitute Special W is 'up to 30%' (Weyermann p. 39); How to Brew p. 230: 5%-15%. |
| Viking Malt Caramel 400 Malt | 10 | unplaced | Nothing states 10 for Viking. Chart substitute Caraaroma is 'up to 15%' (Weyermann p. 27). |
| Viking Malt Caramel 50 Malt | 20 | unplaced | Nothing states 20. How to Brew p. 230: 5%-15%. Chart substitute Carared has no limit printed (Weyermann p. 19). |
| Viking Malt Caramel 600 Malt | 10 | unplaced | Nothing states 10 for Viking. No Weyermann chart partner; How to Brew p. 230: 5%-15%. |
| Viking Malt Lightly Peated Malt | 100 | Viking catalogue, p. 44: 'can be considered as Pilsner Malt with a special aroma' (no limit stated) |  |
| Viking Malt Munich Dark Malt | 100 | Viking catalogue, p. 23: no limit is stated and the text calls it ideal for dark lagers, festival beers and bocks; its Weyermann chart substitute is 'up to 100%' (p. 6 for Munich Type 1, p. 7 for Type 2) |  |
| Viking Malt Munich Light Malt | 100 | Viking catalogue, p. 23: no limit is stated and the text calls it ideal for dark lagers, festival beers and bocks; its Weyermann chart substitute is 'up to 100%' (p. 6 for Munich Type 1, p. 7 for Type 2) |  |
| Viking Malt Smoked Wheat Malt | 100 | Viking catalogue, p. 42: 'even 100% dosages are used' for grodziskie |  |
| Brown Candi Sugar | 20 | unplaced | Hopline: usually 100 g per 10 L (about 5% of a typical 200 g/L grist, derived), 'can differ'. How to Brew p. 436 (table 24.1) gives no limit. |
| Flaked Barley | 20 | unplaced | How to Brew p. 232: 0.5-1 lb per 5 gal (225-450 g per 19 L). p. 244: a beta-glucan rest is advised above 20% flaked barley, oatmeal, rye or wheat (a handling threshold, not a maximum). |
| Flaked Corn | 20 | unplaced | How to Brew p. 232: 0.5-2 lb per 5 gal (225-910 g per 19 L); p. 179: American light lagers use rice or corn as about 30% of the fermentables. |
| Flaked Oats | 30 | Viking catalogue, p. 18: Oat Malt 'up to 20% (30%)' (malted oats, not flakes; the closest printed figure) |  |
| Honey | 20 | How to Brew estimate, printed p. 437: 11%-30% of the fermentables gives a distinct honey flavour (20 is inside that range; the book states no maximum) |  |
| Lactose | 10 | unplaced | Hopline: 300 g per 20 L is a good starting point (about 6-7% of a typical 4-5 kg grist, derived). How to Brew p. 436: used in milk stouts, no amount. |

## 6. User answers (2026-10-15) and what was loaded

1. Sprau Malt → `adjunct` (source `user-supplied`).
2. The 7 long boils of section 3 confirmed: `min_boil_min = 90`; every other row 60.
3. The style table of section 4 approved as proposed: 247 names, 21 dropped.
4. The drafted bases of section 5 confirmed; the 9 unplaced values (Caramel 30, 50, 300, 400, 600,
   Brown Candi Sugar, Flaked Barley, Flaked Corn, Lactose) are "user decision E, 2026-10-14". The
   source stays `user-supplied` for all 18.

Loaded: 81 fermentables, 27 substitute pairs, 623 malt-style rows (59 malts). The 63 untouched
`max_pct` values have the same checksum before and after (`4f978e4b...`); a second run leaves the
three tables unchanged (checksum `c8632bfc...`).
