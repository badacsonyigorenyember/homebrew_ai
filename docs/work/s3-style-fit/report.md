# S3 · Style fit: report

Measured results of the work, by plan task. Sections are added as the tasks are done.

## 1. Tagging (Task 3, 2026-10-15)

`python -m loaders.tags` loads `loaders/style_fit_vocab.toml` and derives the ingredient tags
(one transaction, re-runnable; run twice, same rows: `test_retag_is_identical`).

Vocabulary loaded: 18 dimensions (12 core, 4 specialty, 2 transforming), 69 tags, 205 synonyms.

Tag rows derived (`ref.ingredient_tag`, all `reviewed = false`), 803 in all:

| Kind | Facet | Rows | Ingredients |
|---|---|---|---|
| hop | origin | 89 | 89 of 90 |
| hop | character | 252 | 89 of 90 |
| fermentable | family (role) | 81 | 81 of 81 |
| fermentable | character (keyword scan) | 154 | 70 of 81 |
| yeast | family | 117 | 117 of 119 |
| yeast | character | 110 | 55 of 119 |

Flagged in `ref.ingredient_review`: **50** (8 hops, 42 yeasts). Nothing was guessed for these:

```
hop Columbus: unknown words: édesgyökér
hop Ella: unknown words: csillagánizs
hop Hallertau Blanc: unknown words: fehérbor
hop Lotus: unknown words: curry
hop Nelson Sauvin: unknown words: fehérbor
hop Sterling: no descriptor text
hop Superdelic: unknown words: cukorka
hop Tomahawk: unknown words: édesgyökér
yeast Abbey Monk Ale: unknown words: konyak
yeast CBC-1: no yeast family (Stílus 'conditioning', type None)
yeast Espe: unknown words: konyak
yeast Suava Ale: no yeast family (Stílus None, type None)
(and 38 YeastFlow yeasts YF-101 to YF-999: no descriptor text)
```

Reading the list:
- The 8 hops: 6 have a word the dictionary does not know (*édesgyökér* licorice, *csillagánizs*
  star anise, *fehérbor* white wine, *curry*, *cukorka* candy); Sterling has no descriptor text
  at all (its page says "???").
- The yeasts: 38 YeastFlow strains (YF-1xx to YF-9xx) have a Stílus but no aroma text on the shop
  page, so they carry a family tag and no character; *konyak* (cognac) is unknown on two others;
  CBC-1 (Stílus "conditioning") and Suava Ale (no Stílus, no type) have no family.
- Added to the dictionary after the first run, because they are plain: *gyógynövény*, *tropical
  fruit*, *papaja*, *drupe*, *csonthéjas gyümölcsös*, *cseresznye*, *szeder*, *málna*, *édes
  citrus*, *csokoládé*, *fahéj*, *őrölt bors* (flagged 17 hops before, 8 now).

Choices the user may want to look at in Task 5 (all in `loaders/style_fit_vocab.toml`):
- `[yeast_family_override]` has one entry: SafAle US-05 is "Ale" on the shop page and
  `american-ale` in STYLE-FIT §2. Other "Ale" yeasts are family `ale`.
- Fermentable characters come from a keyword scan of the name and description, so a word used
  in passing counts (Acidulated Malt gets `sour` from "10 % in sour beers").
- A yeast without a shop Aroma field is read by scanning the product text after "Aroma" for
  known words (6 yeasts); it is not flagged for unknown words there.
- The Hungarian *mint* ("as") would have tagged yeast product text as mint; the dictionary has
  only *minty*.

## 2. Envelope extraction (Task 4, 2026-10-15)

`python -m loaders.style_envelopes --extract loaders/style_envelopes.toml` (D2 model
`hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K`, think off, temperature 0, seed 42, `num_ctx` 8192).
Nothing was written to `ref`; the draft is `loaders/style_envelopes.toml`, 26 styles, all
`reviewed = false`, not committed.

- Run time: 3935 s (66 min) for 26 styles; 3 to 324 s per style, about 150 s typical. A first
  single-style run on 20B (before the prompt got the dimension meanings and the one-passage
  quote rule) took 348 s and put alcohol and carbonation under `spice`.
- Tries: 14 styles passed on the first try, 12 needed the second (a quote that was not verbatim, a
  repeated dimension or min above max; the problem list is sent back). The second try fixed all
  but two styles.
- Problems left (the user fixes these in review): **10A** 3 (an ingredient with both role and
  ingredient set, twice; an ingredient with both ingredient and tag set) and **16B** 2 (`min_pct`
  on an ingredient that is not a role: oatmeal, malted oats).
- Unknown words kept for review: 8 to 29 per style (character words not in the dictionary and
  ingredient names not in `ref`); 313 in all (sum of the `unknown=` column of the run).
- **31B** (Alternative Sugar Beer): 0 sensory entries and 0 ingredients in 3 s. Its guideline text
  says "same as the base beer" for every sensation and names no characteristic ingredients with
  levels, so the model found nothing to extract. It needs hand entries (the role `sugar`, or
  Honey) in review.
- **specialty-honey-beer** (BA): 1 sensory entry, 2 ingredients; the BA text is thin ("varies").
