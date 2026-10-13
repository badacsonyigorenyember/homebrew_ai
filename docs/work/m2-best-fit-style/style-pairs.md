# BA to BJCP style pairs: for your review

The script proposed a BJCP equivalent for each BA 2026 style by name. Fill the **decision**
column of every row you want paired:

- `keep`: the proposed BJCP style is the same style as the BA one
- a BJCP code (for example `5B`): that BJCP style is the match (also for a row with no proposal)
- `drop` or empty: no pair, the BA style stays a BA style

When step 2's best fit is a BA style that has a pair, step 2 returns the BJCP style instead.
Where several BJCP styles are proposed, write the one code you want.

| BA code | BA name | proposed BJCP | match | ABV BA | ABV BJCP | decision |
|---|---|---|---|---|---|---|
| `adambier` | Adambier |  |  | [9.0,11.0] |  |  |
| `aged-beer` | Aged Beer | 33A Wood-Aged Beer<br>33B Specialty Wood-Aged Beer | BA name inside BJCP name |  | <br> |  |
| `american-belgo-style-ale` | American-Belgo-Style Ale | 18B American Pale Ale | BJCP name inside BA name |  | [4.5,6.2] |  |
| `american-style-amber-lager` | American-Style Amber Lager | 1B American Lager | BJCP name inside BA name | [4.8,5.4] | [4.2,5.3] |  |
| `american-style-amber-red-ale` | American-Style Amber/Red Ale | 18B American Pale Ale<br>19A American Amber Ale | BJCP name inside BA name | [4.4,6.1] | [4.5,6.2]<br>[4.5,6.2] |  |
| `american-style-barley-wine-ale` | American-Style Barley Wine Ale | 18B American Pale Ale | BJCP name inside BA name | [8.5,12.2] | [4.5,6.2] |  |
| `american-style-black-ale` | American-Style Black Ale | 18B American Pale Ale | BJCP name inside BA name | [6.3,7.6] | [4.5,6.2] |  |
| `american-style-brown-ale` | American-Style Brown Ale | 18B American Pale Ale<br>19C American Brown Ale | BJCP name inside BA name | [4.2,6.3] | [4.5,6.2]<br>[4.3,6.2] |  |
| `american-style-cream-ale` | American-Style Cream Ale | 18B American Pale Ale | BJCP name inside BA name | [4.3,5.7] | [4.5,6.2] |  |
| `american-style-dark-lager` | American-Style Dark Lager | 1B American Lager | BJCP name inside BA name | [4.1,5.6] | [4.2,5.3] |  |
| `american-style-fruit-beer` | American-Style Fruit Beer | 29A Fruit Beer | BJCP name inside BA name | [2.5,12.0] |  |  |
| `american-style-fruited-sour-ale` | American-Style Fruited Sour Ale | 18B American Pale Ale | BJCP name inside BA name |  | [4.5,6.2] |  |
| `american-style-imperial-porter` | American-Style Imperial Porter | 20A American Porter | BJCP name inside BA name | [7.0,12.0] | [4.8,6.5] |  |
| `american-style-imperial-stout` | American-Style Imperial Stout | 20B American Stout<br>20C Imperial Stout | BJCP name inside BA name | [7.0,12.0] | [5.0,7.0]<br>[8.0,12.0] |  |
| `american-style-india-pale-ale` | American-Style India Pale Ale | 21A American IPA | same words | [6.3,7.5] | [5.5,7.5] |  |
| `american-style-india-pale-lager` | American-Style India Pale Lager | 21A American IPA | BJCP name inside BA name | [5.6,7.9] | [5.5,7.5] |  |
| `american-style-lager` | American-Style Lager | 1A American Light Lager<br>1B American Lager | BA name inside BJCP name | [4.1,5.1] | [2.8,4.2]<br>[4.2,5.3] |  |
| `american-style-light-lager` | American-Style Light Lager | 1A American Light Lager | same words | [3.5,4.4] | [2.8,4.2] |  |
| `american-style-malt-liquor` | American-Style Malt Liquor |  |  | [6.3,7.6] |  |  |
| `american-style-pale-ale` | American-Style Pale Ale | 18B American Pale Ale<br>19A American Amber Ale<br>19C American Brown Ale<br>21A American IPA<br>22B American Strong Ale | same words | [4.4,5.4] | [4.5,6.2]<br>[4.5,6.2]<br>[4.3,6.2]<br>[5.5,7.5]<br>[6.3,10.0] |  |
| `american-style-pilsener` | American-Style Pilsener |  |  | [4.9,6.0] |  |  |
| `american-style-sour-ale` | American-Style Sour Ale | 18B American Pale Ale | BJCP name inside BA name |  | [4.5,6.2] |  |
| `american-style-stout` | American-Style Stout | 20B American Stout | same words | [5.7,8.0] | [5.0,7.0] |  |
| `american-style-strong-pale-ale` | American-Style Strong Pale Ale | 18B American Pale Ale<br>22B American Strong Ale | BJCP name inside BA name | [5.6,6.4] | [4.5,6.2]<br>[6.3,10.0] |  |
| `american-style-wheat-beer` | American-Style Wheat Beer | 1D American Wheat Beer | same words | [3.5,5.6] | [4.0,5.5] |  |
| `american-style-wheat-wine-ale` | American-Style Wheat Wine Ale | 18B American Pale Ale | BJCP name inside BA name | [8.5,12.2] | [4.5,6.2] |  |
| `australian-style-pale-ale` | Australian-Style Pale Ale | 12B Australian Sparkling Ale | BA name inside BJCP name | [4.0,6.0] | [4.5,6.0] |  |
| `baltic-style-porter` | Baltic-Style Porter | 9C Baltic Porter | same words | [7.6,9.3] | [6.5,9.5] |  |
| `bamberg-style-bock-rauchbier` | Bamberg-Style Bock Rauchbier | 6B Rauchbier | BJCP name inside BA name | [6.3,7.6] | [4.8,6] |  |
| `bamberg-style-helles-rauchbier` | Bamberg-Style Helles Rauchbier | 6B Rauchbier | BJCP name inside BA name | [4.8,5.6] | [4.8,6] |  |
| `bamberg-style-maerzen-rauchbier` | Bamberg-Style Maerzen Rauchbier | 6A Marzen<br>6B Rauchbier | BJCP name inside BA name | [5.1,6.0] | [5.6,6.3]<br>[4.8,6] |  |
| `bamberg-style-weiss-rauchbier` | Bamberg-Style Weiss Rauchbier | 6B Rauchbier | BJCP name inside BA name | [4.9,5.6] | [4.8,6] |  |
| `belgian-style-blonde-ale` | Belgian-Style Blonde Ale | 24B Belgian Pale Ale<br>25A Belgian Blond Ale | BJCP name inside BA name | [6.3,7.9] | [4.8,5.5]<br>[6.0,7.5] |  |
| `belgian-style-dubbel` | Belgian-Style Dubbel | 26B Belgian Dubbel | same words | [6.3,7.6] | [6.0,7.6] |  |
| `belgian-style-fruit-beer` | Belgian-Style Fruit Beer | 29A Fruit Beer | BJCP name inside BA name | [2.5,12.0] |  |  |
| `belgian-style-fruit-lambic` | Belgian-Style Fruit Lambic | 23F Fruit Lambic | BJCP name inside BA name | [4.0,9.0] | [5.0,7.0] |  |
| `belgian-style-lambic` | Belgian-Style Lambic | 23D Lambic | BJCP name inside BA name | [5.0,8.0] | [5.0,6.5] |  |
| `belgian-style-quadrupel` | Belgian-Style Quadrupel |  |  | [10.0,14.2] |  |  |
| `belgian-style-session-ale` | Belgian-Style Session Ale | 24B Belgian Pale Ale | BJCP name inside BA name | [2.1,5.0] | [4.8,5.5] |  |
| `belgian-style-speciale-belge` | Belgian-Style Speciale Belge |  |  | [5.0,6.2] |  |  |
| `belgian-style-strong-blonde-ale` | Belgian-Style Strong Blonde Ale | 24B Belgian Pale Ale<br>25A Belgian Blond Ale | BJCP name inside BA name | [7.1,11.2] | [4.8,5.5]<br>[6.0,7.5] |  |
| `belgian-style-strong-dark-ale` | Belgian-Style Strong Dark Ale | 26D Belgian Dark Strong Ale | same words | [7.1,11.2] | [8.0,12.0] |  |
| `belgian-style-table-beer` | Belgian-Style Table Beer |  |  | [0.5,2.0] |  |  |
| `belgian-style-tripel` | Belgian-Style Tripel | 26C Belgian Tripel | same words | [7.1,10.1] | [7.5,9.5] |  |
| `belgian-style-witbier` | Belgian-Style Witbier | 24A Witbier | BJCP name inside BA name | [4.0,5.5] | [4.5,5.5] |  |
| `berliner-style-weisse` | Berliner-Style Weisse | 23A Berliner Weisse | same words | [2.8,5.0] | [2.8,3.8] |  |
| `bernsteinfarbenes-weizen` | Bernsteinfarbenes Weizen |  |  | [4.8,5.4] |  |  |
| `breslau-style-schoeps` | Breslau-Style Schoeps |  |  | [6.0,7.0] |  |  |
| `brett-beer` | Brett Beer | 28A Brett Beer | same words |  |  |  |
| `british-style-barley-wine-ale` | British-Style Barley Wine Ale |  |  | [8.5,12.2] |  |  |
| `british-style-imperial-stout` | British-Style Imperial Stout | 20C Imperial Stout | BJCP name inside BA name | [7.0,12.0] | [8.0,12.0] |  |
| `british-style-india-pale-ale` | British-Style India Pale Ale |  |  | [4.5,7.1] |  |  |
| `brown-porter` | Brown Porter |  |  | [4.4,6.0] |  |  |
| `california-common-beer` | California Common Beer | 19B California Common | same words | [4.6,5.7] | [4.5,5.5] |  |
| `chili-pepper-beer` | Chili Pepper Beer |  |  | [2.5,13.3] |  |  |
| `chocolate-or-cocoa-beer` | Chocolate or Cocoa Beer |  |  |  |  |  |
| `classic-australian-style-pale-ale` | Classic Australian-Style Pale Ale |  |  | [4.0,6.0] |  |  |
| `classic-english-style-pale-ale` | Classic English-Style Pale Ale |  |  | [4.4,5.3] |  |  |
| `classic-irish-style-dry-stout` | Classic Irish-Style Dry Stout | 15B Irish Stout | BJCP name inside BA name | [4.1,5.3] | [3.8,5.0] |  |
| `coffee-beer` | Coffee Beer |  |  |  |  |  |
| `contemporary-style-gose` | Contemporary-Style Gose | 23G Gose | BJCP name inside BA name | [4.4,5.4] | [4.2,4.8] |  |
| `czech-style-amber-lager` | Czech-Style Amber Lager | 3C Czech Amber Lager | same words | [4.4,5.8] | [4.4,5.8] |  |
| `czech-style-dark-lager` | Czech-Style Dark Lager | 3D Czech Dark Lager | same words | [4.4,5.8] | [4.4,5.8] |  |
| `czech-style-pale-lager` | Czech-Style Pale Lager | 3A Czech Pale Lager<br>3B Czech Premium Pale Lager | same words | [4.6,5.1] | [3.0,4.1]<br>[4.2,5.8] |  |
| `dessert-stout-or-pastry-beer` | Dessert Stout or Pastry Beer |  |  | [7.0,13.0] |  |  |
| `double-hoppy-red-ale` | Double Hoppy Red Ale |  |  | [6.1,7.9] |  |  |
| `dutch-style-kuit-kuyt-or-koyt` | Dutch-Style Kuit, Kuyt or Koyt |  |  | [4.7,7.9] |  |  |
| `english-style-brown-ale` | English-Style Brown Ale |  |  | [4.2,6.0] |  |  |
| `english-style-dark-mild-ale` | English-Style Dark Mild Ale | 13A Dark Mild | BJCP name inside BA name | [3.4,4.4] | [3.0,3.8] |  |
| `english-style-pale-mild-ale` | English-Style Pale Mild Ale |  |  | [3.4,4.4] |  |  |
| `english-style-summer-ale` | English-Style Summer Ale |  |  | [3.7,5.1] |  |  |
| `european-style-dark-lager` | European-Style Dark Lager |  |  | [4.8,5.3] |  |  |
| `experimental-beer` | Experimental Beer | 34C Experimental Beer | same words |  |  |  |
| `experimental-india-pale-ale` | Experimental India Pale Ale | 34C Experimental Beer | BJCP name inside BA name | [6.3,10.6] |  |  |
| `export` | Export | 14C Scottish Export | BA name inside BJCP name | [5.1,6.1] | [3.9,6.0] |  |
| `export-style-stout` | Export-Style Stout |  |  | [5.6,8.0] |  |  |
| `extra-special-bitter` | Extra Special Bitter |  |  | [4.8,5.8] |  |  |
| `field-beer` | Field Beer |  |  | [2.5,13.3] |  |  |
| `finnish-style-sahti` | Finnish-Style Sahti |  |  | [7.0,8.5] |  |  |
| `franconian-style-rotbier` | Franconian-Style Rotbier |  |  | [4.8,5.4] |  |  |
| `french-style-biere-de-garde` | French-Style Bière de Garde | 24C Bière de Garde | BJCP name inside BA name | [4.4,8.0] | [6.0,8.5] |  |
| `fresh-hop-beer` | Fresh Hop Beer |  |  |  |  |  |
| `fruit-wheat-beer` | Fruit Wheat Beer | 29A Fruit Beer | BJCP name inside BA name | [2.5,12.0] |  |  |
| `german-style-altbier` | German-Style Altbier | 7B Altbier | BJCP name inside BA name | [4.6,5.6] | [4.3,5.5] |  |
| `german-style-doppelbock` | German-Style Doppelbock | 9A Doppelbock | BJCP name inside BA name | [6.6,7.9] | [7.0,10.0] |  |
| `german-style-eisbock` | German-Style Eisbock | 9B Eisbock | BJCP name inside BA name | [8.6,14.3] | [9.0,14.0] |  |
| `german-style-heller-bock-maibock` | German-Style Heller Bock/Maibock |  |  | [6.3,8.1] |  |  |
| `german-style-koelsch` | German-Style Koelsch | 5B Kolsch | BJCP name inside BA name | [4.8,5.3] | [4.4,5.2] |  |
| `german-style-leichtbier` | German-Style Leichtbier | 5A German Leichtbier | same words | [2.5,3.7] | [2.4,3.6] |  |
| `german-style-leichtes-weizen` | German-Style Leichtes Weizen |  |  | [2.5,3.5] |  |  |
| `german-style-maerzen` | German-Style Maerzen | 6A Marzen | BJCP name inside BA name | [5.1,6.0] | [5.6,6.3] |  |
| `german-style-oktoberfest-festbier` | German-Style Oktoberfest/Festbier | 4B Festbier | BJCP name inside BA name | [5.1,6.1] | [5.8,6.3] |  |
| `german-style-pilsener` | German-Style Pilsener |  |  | [4.6,5.3] |  |  |
| `german-style-rye-ale` | German-Style Rye Ale |  |  | [4.9,5.6] |  |  |
| `german-style-schwarzbier` | German-Style Schwarzbier | 8B Schwarzbier | BJCP name inside BA name | [3.8,4.9] | [4.4,5.4] |  |
| `ginjo-beer-or-sake-yeast-beer` | Ginjo Beer or Sake-Yeast Beer |  |  | [4.3,10.2] |  |  |
| `gluten-free-beer` | Gluten-Free Beer |  |  |  |  |  |
| `golden-or-blonde-ale` | Golden or Blonde Ale | 18A Blonde Ale | BJCP name inside BA name | [4.1,5.1] | [3.8,5.5] |  |
| `grodziskie` | Grodziskie | 27E Historical Beer: Piwo Grodziskie | BA name inside BJCP name | [2.5,3.3] | [2.5,3.3] |  |
| `herb-and-spice-beer` | Herb and Spice Beer | 30A Spice, Herb, or Vegetable Beer | BA name inside BJCP name |  |  |  |
| `historical-beer` | Historical Beer | 27A Historical Beer: Kellerbier<br>27B Historical Beer: Kentucky Common<br>27C Historical Beer: Lichtenhainer<br>27D Historical Beer: London Brown Ale<br>27E Historical Beer: Piwo Grodziskie<br>27F Historical Beer: Pre-Prohibition Lager<br>27G Historical Beer: Pre-Prohibition Porter<br>27H Historical Beer: Roggenbier<br>27I Historical Beer: Sahti | BA name inside BJCP name |  | <br>[4.0,5.5]<br>[3.5,4.7]<br>[2.8,3.6]<br>[2.5,3.3]<br>[4.5,6.0]<br>[4.5,6.0]<br>[4.5,6.0]<br>[7.0,11.0] |  |
| `imperial-red-ale` | Imperial Red Ale |  |  | [8.0,10.6] |  |  |
| `india-pale-ale` | India Pale Ale | 12C English IPA<br>21A American IPA<br>21B Specialty IPA<br>21C Hazy IPA<br>22A Double IPA | BA name inside BJCP name | [7.6,10.6] | [5.0,7.5]<br>[5.5,7.5]<br>[6.0,7.5]<br>[6.0,9.0]<br>[7.5,10.0] |  |
| `india-pale-ale-2` | India Pale Ale | 12C English IPA<br>21A American IPA<br>21B Specialty IPA<br>21C Hazy IPA<br>22A Double IPA | BA name inside BJCP name | [7.6,10.6] | [5.0,7.5]<br>[5.5,7.5]<br>[6.0,7.5]<br>[6.0,9.0]<br>[7.5,10.0] |  |
| `international-light-lager` | International Light Lager |  |  | [4.1,5.1] |  |  |
| `international-style-pale-ale` | International-Style Pale Ale | 2A International Pale Lager | BA name inside BJCP name | [4.4,6.6] | [4.5,6.0] |  |
| `international-style-pilsener` | International-Style Pilsener |  |  | [4.6,5.3] |  |  |
| `irish-style-red-ale` | Irish-Style Red Ale | 15A Irish Red Ale | same words | [4.0,4.8] | [3.8,5.0] |  |
| `italian-style-pilsener` | Italian-Style Pilsener |  |  | [4.6,5.3] |  |  |
| `juicy-or-hazy-india-pale-ale` | Juicy or Hazy India Pale Ale | 21C Hazy IPA | BJCP name inside BA name | [6.3,7.5] | [6.0,9.0] |  |
| `juicy-or-hazy-pale-ale` | Juicy or Hazy Pale Ale |  |  | [4.4,5.4] |  |  |
| `juicy-or-hazy-strong-pale-ale` | Juicy or Hazy Strong Pale Ale |  |  | [5.6,6.4] |  |  |
| `kellerbier-or-zwickelbier` | Kellerbier or Zwickelbier |  |  |  |  |  |
| `kentucky-common-beer` | Kentucky Common Beer | 27B Historical Beer: Kentucky Common | BA name inside BJCP name | [4.0,5.5] | [4.0,5.5] |  |
| `lager` | Lager | 1A American Light Lager<br>1B American Lager<br>27F Historical Beer: Pre-Prohibition Lager<br>2A International Pale Lager<br>2B International Amber Lager<br>2C International Dark Lager<br>3A Czech Pale Lager<br>3B Czech Premium Pale Lager<br>3C Czech Amber Lager<br>3D Czech Dark Lager<br>7A Vienna Lager | BA name inside BJCP name | [4.1,5.1] | [2.8,4.2]<br>[4.2,5.3]<br>[4.5,6.0]<br>[4.5,6.0]<br>[4.5,6.0]<br>[4.2,6.0]<br>[3.0,4.1]<br>[4.2,5.8]<br>[4.4,5.8]<br>[4.4,5.8]<br>[4.7,5.5] |  |
| `leipzig-style-gose` | Leipzig-Style Gose | 23G Gose | BJCP name inside BA name | [4.4,5.4] | [4.2,4.8] |  |
| `light-lager` | Light Lager | 1A American Light Lager | BA name inside BJCP name | [3.5,4.4] | [2.8,4.2] |  |
| `maerzen-oktoberfest` | Maerzen/Oktoberfest | 6A Marzen | BJCP name inside BA name | [5.1,6.0] | [5.6,6.3] |  |
| `mexican-style-amber-lager` | Mexican-Style Amber Lager |  |  | [4.0,5.5] |  |  |
| `mexican-style-dark-lager` | Mexican-Style Dark Lager |  |  | [4.5,5.8] |  |  |
| `mexican-style-light-lager` | Mexican-Style Light Lager |  |  | [3.2,4.2] |  |  |
| `mexican-style-pale-lager` | Mexican-Style Pale Lager |  |  | [4.5,5.0] |  |  |
| `mixed-culture-brett-beer` | Mixed-Culture Brett Beer | 28A Brett Beer<br>34B Mixed-Style Beer | BJCP name inside BA name |  | <br> |  |
| `munich-style-dunkel` | Munich-Style Dunkel | 8A Munich Dunkel | same words | [4.8,5.3] | [4.5,5.6] |  |
| `munich-style-helles` | Munich-Style Helles | 4A Munich Helles | same words | [4.8,5.6] | [4.7,5.4] |  |
| `new-zealand-style-india-pale-ale` | New Zealand-Style India Pale Ale |  |  | [6.3,7.5] |  |  |
| `new-zealand-style-pale-ale` | New Zealand-Style Pale Ale |  |  | [4.0,6.0] |  |  |
| `non-alcohol-malt-beverage` | Non-Alcohol Malt Beverage |  |  |  |  |  |
| `oatmeal-stout` | Oatmeal Stout | 16B Oatmeal Stout | same words | [3.8,6.1] | [4.2,5.9] |  |
| `old-ale` | Old Ale | 17B Old Ale | same words | [6.3,9.1] | [5.5,9.0] |  |
| `ordinary-bitter` | Ordinary Bitter | 11A Ordinary Bitter | same words | [3.0,4.2] | [3.2,3.8] |  |
| `other-belgian-style-ale` | Other Belgian-Style Ale | 24B Belgian Pale Ale | BJCP name inside BA name |  | [4.8,5.5] |  |
| `other-strong-ale-or-lager` | Other Strong Ale or Lager |  |  |  |  |  |
| `pilsener` | Pilsener |  |  | [4.9,6.0] |  |  |
| `pumpkin-spice-beer` | Pumpkin Spice Beer |  |  | [2.5,12.0] |  |  |
| `pumpkin-squash-beer` | Pumpkin/Squash Beer |  |  | [2.5,12.0] |  |  |
| `rice-lager` | Rice Lager |  |  | [4.0,6.0] |  |  |
| `robust-porter` | Robust Porter |  |  | [5.1,6.6] |  |  |
| `rye-beer` | Rye Beer |  |  |  |  |  |
| `saison` | Saison | 25B Saison | same words | [4.5,6.5] | [3.5,9.5] |  |
| `scotch-ale-or-wee-heavy` | Scotch Ale or Wee Heavy | 17C Wee Heavy | BJCP name inside BA name | [6.6,8.5] | [6.5,10.0] |  |
| `scottish-style-export-ale` | Scottish-Style Export Ale | 14C Scottish Export | BJCP name inside BA name | [4.1,6.0] | [3.9,6.0] |  |
| `scottish-style-heavy-ale` | Scottish-Style Heavy Ale | 14B Scottish Heavy | BJCP name inside BA name | [3.5,4.1] | [3.3,3.9] |  |
| `scottish-style-light-ale` | Scottish-Style Light Ale | 14A Scottish Light | BJCP name inside BA name | [2.8,3.5] | [2.5,3.3] |  |
| `session-beer` | Session Beer |  |  | [0.5,5.0] |  |  |
| `session-india-pale-ale` | Session India Pale Ale |  |  | [0.5,5.0] |  |  |
| `smoke-beer` | Smoke Beer | 32A Classic Style Smoked Beer<br>32B Specialty Smoked Beer | BA name inside BJCP name |  | <br> |  |
| `smoke-porter` | Smoke Porter |  |  |  |  |  |
| `south-german-style-hefeweizen` | South German-Style Hefeweizen |  |  | [4.9,5.6] |  |  |
| `south-german-style-kristal-weizen` | South German-Style Kristal Weizen |  |  | [4.9,5.6] |  |  |
| `south-german-style-weizenbock` | South German-Style Weizenbock | 10C Weizenbock | BJCP name inside BA name | [7.0,9.5] | [6.5,9.0] |  |
| `special-bitter-or-best-bitter` | Special Bitter or Best Bitter | 11B Best Bitter | BJCP name inside BA name | [4.2,4.8] | [3.8,4.6] |  |
| `specialty-beer` | Specialty Beer | 21B Specialty IPA<br>28C Wild Specialty Beer<br>29C Specialty Fruit Beer<br>30D Specialty Spice Beer<br>32B Specialty Smoked Beer<br>33B Specialty Wood-Aged Beer<br>34A Commercial Specialty Beer | BA name inside BJCP name | [2.5,25.0] | [6.0,7.5]<br><br><br><br><br><br> |  |
| `specialty-honey-beer` | Specialty Honey Beer |  |  | [2.5,12.0] |  |  |
| `specialty-saison` | Specialty Saison | 25B Saison | BJCP name inside BA name | [5.0,9.3] | [3.5,9.5] |  |
| `spontaneous-fermented-ale` | Spontaneous Fermented Ale |  |  | [5.0,8.9] |  |  |
| `strong-ale` | Strong Ale | 17A British Strong Ale<br>22B American Strong Ale<br>25C Belgian Golden Strong Ale<br>26D Belgian Dark Strong Ale | BA name inside BJCP name | [7.0,11.3] | [5.5,8.0]<br>[6.3,10.0]<br>[7.5,10.5]<br>[8.0,12.0] |  |
| `swedish-style-gotlandsdricke` | Swedish-Style Gotlandsdricke |  |  | [5.5,6.5] |  |  |
| `sweet-stout-or-cream-stout` | Sweet Stout or Cream Stout | 16A Sweet Stout | BJCP name inside BA name | [3.2,6.3] | [4.0,6.0] |  |
| `traditional-belgian-style-gueuze` | Traditional Belgian-Style Gueuze | 23E Gueuze | BJCP name inside BA name | [5.0,8.0] | [5.0,8.0] |  |
| `traditional-german-style-bock` | Traditional German-Style Bock |  |  | [6.3,7.6] |  |  |
| `vienna-style-lager` | Vienna-Style Lager | 7A Vienna Lager | same words | [4.8,5.4] | [4.7,5.5] |  |
| `weizen` | Weizen |  |  | [4.8,5.4] |  |  |
| `west-coast-style-india-pale-ale` | West Coast-Style India Pale Ale |  |  | [6.3,7.5] |  |  |
| `west-coast-style-pilsener` | West Coast-Style Pilsener |  |  | [5.0,6.0] |  |  |
| `wild-beer` | Wild Beer | 28C Wild Specialty Beer | BA name inside BJCP name |  |  |  |
| `wood-and-barrel-aged-beer` | Wood- and Barrel-Aged Beer | 33A Wood-Aged Beer | BJCP name inside BA name |  |  |  |
| `wood-and-barrel-aged-sour-beer` | Wood- and Barrel-Aged Sour Beer | 33A Wood-Aged Beer | BJCP name inside BA name |  |  |  |
| `or-oud-red-ale` | or Oud Red Ale |  |  | [4.8,6.6] |  |  |
