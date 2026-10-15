You read the guideline text of one beer style and write down its sensory envelope as JSON.

Answer only with JSON of the given shape. The guideline text is the only source: do not use
what you know about the style from elsewhere.

## sensory

One entry per sensation the text describes. The sensations are the `dimension` values in the
schema. Leave out a dimension the text does not describe. Colour and bitterness are not
extracted; ignore them. Use a dimension only for what its name means:
- hop_flavour, hop_aroma: hop taste and hop smell
- malt: grainy, bready, toasty, biscuity malt character
- caramel: caramel, toffee, burnt-sugar character
- roast: roasted, coffee, chocolate, burnt-grain character
- sweetness, body, dryness: residual sweetness, fullness of body, how dry the finish is
- esters, phenols: fruity yeast esters; clove, smoky or medicinal yeast phenols
- spice, fruit, wood, smoke: spice, fruit, wood-aged or smoked character from additions
- sourness, brett_funk: acidity; wild-yeast funk
Things that have no dimension (alcohol, carbonation, head, clarity, astringency) are left out.

For each entry:
- `min` and `max`: the lowest and highest intensity the text allows, on this scale:
  none (0), very low (1), low (2), medium-low (3), medium (4), medium-high (5), high (6),
  very high (7). "Moderate" means medium. A single word ("low") gives the same word for min and
  max. A range ("low to medium") gives its two ends. Write "none" only when the text says the
  sensation is absent or must not be there.
- `characters`: the descriptor words the text uses for that sensation, copied as the text writes
  them, in lower case. An empty list when the text gives none.
- `quote`: one continuous passage of the guideline text, usually one sentence, copied character
  for character. Never join two passages and never change a word. If the text states the level
  in two places, quote the one that states it most clearly.

Give each dimension at most once. When the text mentions a dimension in several places, use the
place that states its level and make min and max cover everything the text allows.

## ingredients

The specific characteristic ingredients the text names for the style. Skip general words that
fit every beer (yeast, hops, water, malt on its own). Leave the list empty when the text names
none. For each one set exactly one of:
- `role`: a class of fermentable: base, kilned, crystal, roast, adjunct or sugar
- `ingredient`: a named product
- `tag`: a hop origin (a country code) or a yeast family

and leave the other two null. `required` is true only when the text says the style must have it.
`min_pct` is the minimum share of the grist when the text gives one, else null (only with a
role). `quote` is the part of the text that names it, verbatim.
