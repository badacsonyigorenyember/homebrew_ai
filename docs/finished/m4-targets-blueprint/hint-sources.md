# Hint table sources (m4-targets-blueprint, Task 2)

One line per row of `app.hint_knob()` (`db/037_step3.sql`). A row is sourced only when a passage in
`kb.chunk` states that knob for that hint; otherwise it is `unsourced` and used marked as such.
The positions (0.875 / 0.125) and the exact mash values (64.5 / 68.5 °C) are the user's decision of
2026-10-17 and are not themselves sourced. 18 rows: 15 sourced, 3 unsourced.

| Hint | Knob | Source | Passage |
|---|---|---|---|
| bitter | ibu (up) | *unsourced* | none found that ties a "bitter" wish to the top of the IBU range |
| bitter | bu_gu (up) | bjcp-exam-study-guide-2017, p60 | "characterize the bitterness of a given style is the BU:GU ratio" |
| hoppy, juicy | late_hop_share (up) | janish-survivables-hot-side, Unpacking Hot-Side Hop Flavor | "contribute to the final flavor and aroma of late hopped beer" |
| dry, crisp | mash_temp (down) | palmer-how-to-brew, p277 | "lower mash temperature ... yields a lighter-bodied, more attenuated beer" |
| dry, crisp | attenuation (up) | palmer-how-to-brew, p134 | "Produces a drier beer than American ale. High attenuation" |
| full, chewy | mash_temp (up) | palmer-how-to-brew, p277 | "higher mash temperature ... yields a more dextrinous, less attenuated beer" |
| full, chewy | attenuation (down) | bjcp-exam-study-guide-2017, p77 | "residual sugars can result from flocculent or low-attenuating yeast strains" |
| malty | ibu (down) | palmer-how-to-brew, p447 | Bock: "only enough hop bitterness to just balance the sweetness of the malt" |
| malty | munich_share (up) | palmer-how-to-brew, p255 | "Munich malt has an amber color and gives a very malty flavor" |
| malty | bu_gu (down) | palmer-how-to-brew, p447 | same Bock passage |
| darker | srm (up) | mallett-malt, p143 | "Black malt provides a huge color addition to beer" |
| stronger | og (up) | *unsourced* | none searched beyond "stronger beer"; no passage found |
| session | og (down) | *unsourced* | no passage found |

Notes:
- The "sugar at most 10 % of the grist" part of the dry / crisp attenuation intent has no passage
  of its own; the row's source covers only the high-attenuation yeast. BJCP study guide p70 says
  completely fermentable adjuncts lower body, which is the reason for a cap, not a figure.
- The malty IBU / BU:GU rows rest on one style description (Bock), not a general statement.

## Unsourced rows to source before G6

1. bitter · ibu (up)
2. stronger · og (up)
3. session · og (down)
