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

## 3. Envelope review and load (Task 5, 2026-10-15)

The user went through all 26 styles one at a time against [`envelope-review.md`](envelope-review.md)
and approved exactly the proposals in it ([`envelope-review-proposals.toml`](envelope-review-proposals.toml)).
Applied to `loaders/style_envelopes.toml` (every style `reviewed = true`, `unknown` and `problems`
empty) and `loaders/style_fit_vocab.toml` (34 synonyms; no-character words "cukorka", "konyak",
"sour beers"; yeast-family overrides `cbc1 = "ale"`, `suavaale = "american-ale"`; the US-05 override kept).

Decisions:
- Rules R1-R5: all five applied.
- A (a text that says just "sugar"): only the `ref` sugars that fit the style; no role `sugar` except 31B.
- B ("clean fermentation profile"): phenols none, esters capped.
- C (31B and Specialty Honey Beer, "same as the base beer"): the sugar row only, no sensory rows.
  The test allows 0 sensory rows for those two (plan Deviations).
- All 26 style packs approved as proposed. Two choices: 16B roast max medium, 19C roast low-medium;
  25B adds herbal; 21C names the two flakes (Flaked Oats and Flaked Barley), not the adjunct role;
  Session IPA: base role only.
- Vocabulary, flagged table and 30 English synonyms approved. YeastFlow 38: family only (no
  character guessed). US-05 override kept. Acidulated Malt: `sour` dropped through the
  "sour beers" no-character word.
- Earlier decisions that still hold: golden set generated and corrected by the user; adjunct/sugar
  rule; `fermentable_style` bump (fermentables only); cut points from the books; BA through the
  same LLM path.

Result (measured):
- `python -m loaders.tags` after the vocabulary change: 239 synonyms; **39 ingredients flagged**
  (1 hop, Sterling, and 38 YeastFlow yeasts with no descriptor text), as the pack expected.
- `python -m loaders.style_envelopes` run twice: both print `loaded 26 reviewed styles, skipped 0
  unreviewed: {'sensory': 189, 'character': 237, 'ingredient': 116, 'rule': 0}`.
- `ref.style_ingredient` 116 rows, `ref.ingredient_review` 39, `ref.style_rule` 0.
- Full `pytest`: 451 passed, 1 failed (the known `test_db_enzyme_and_boil`).


## 4. Cut points (Task 6, 2026-10-15)

Doc → calc pass on *How to Brew* (Palmer, 2017) and the OBC *Recipe Formulation* PDF
(`pdftotext -layout`); figures, pages, arithmetic and the reference-recipe check per cut point in
[`cut-points.md`](cut-points.md). The drafts were committed unapproved (fa8119d) for the
walk-through; the user then answered item by item.

Approved by the user 2026-10-15, every value as proposed:
- Oil dose (mL hop oil per L) O1–O7: 0.003 / 0.008 / 0.012 / 0.025 / 0.05 / 0.08 / 0.15. O1–O6 from
  HTB pp. 71–72 and its recipes (pp. 394, 399–402); O7 from the p. 72 range, value set by the user.
- Roast index (Σ % × EBC) R1–R7: 700 / 1500 / 4000 / 5500 / 12000 / 16000 / 22000. R1–R5 from HTB
  pp. 230–231, 388, 404, 410–413; R6, R7 set by the user.
- Esters: lager 0, no ester character 1, an ester character 3 (the plan's 4 failed b05), +1 above
  21 °C (HTB p. 443; the plan's "above the yeast's midpoint" failed b05).
- Phenols: a phenolic character 4 (`clove`, `pepper`, `phenolic`, and `spicy`), else 0; +1 above
  21 °C.
- Min check, one-level tolerance (chosen through golden case y02): more than one level below the
  envelope's min → ⚠️ "too little"; per ingredient for yeasts (skipped for needs-review yeasts), on
  recipe totals for hops and roast (Task 9). STYLE-FIT §4–§5 updated.
- Step 0: a style with reviewed characteristic-ingredient rows but no sensory rows (31B, BA
  Specialty Honey Beer) is rated.

Paper check against the 22 reference recipes: no recipe above a max. Below a min by more than one
level: no yeast (b13's YF-401 is needs-review, skipped); recipe totals **b07 1C**, **b12 18A**
(no late hops, hop flavour min low) and **b22** Mexican amber lager (no roast malt, roast min low)
→ Task 9's stop point. Citra table holds (whirlpool 2 g/L = 0.045 → medium; dry hop 8 g/L = 0.18
→ very high).

## 5. Golden set (Task 6, 2026-10-15)

[`tests/fixtures/style_fit_golden.toml`](../../../tests/fixtures/style_fit_golden.toml), shown by
theme in [`golden-review.md`](golden-review.md): **53 cases** (Citra table 6, M3 cases and 16A
lactose 8, adjunct/sugar rule 7, `fermentable_style` bump 4, hop character 4, yeast 8,
transforming/specialty 5, intensity and style ranges 9, not rated / no dose 2).

The user approved it 2026-10-15: every theme as drafted, except
- **y02** (SafAle US-05 in 10A): ➖ → ⚠️ "too little" banana and clove (the yeast min check);
- **u02** (Sterling, needs review): dropped. The user removed Sterling from `ref` ("It is from
  Saaz, and not really available on hopline as well"): `db/035_drop_sterling.sql`, excluded in
  `loaders.hop_products.EXCLUDED` (9908734). Measured after: 89 hops, `ref.ingredient_review` 38
  (the YeastFlow yeasts, no hop).

## 6. Reference recipes against the style fit (Task 9, 2026-10-15)

`app.style_fit_recipe` is written (db/034) and `tests/test_style_fit_recipe.py` exists; nothing is
committed. Run over the 22 reference recipes (SRM and IBU are the recipe's computed numbers from
`app.check_recipe`):

### Lines outside b16 rice, b19 honey, b20 lactose

| Recipe | Style | Lines | Level | Because | Measured vs range |
|---|---|---|---|---|---|
| b08 | 5D German Pils | Magnum, Hallertau Mittelfrüh | out_of_style | too much bitterness | 48.6 IBU vs 22-40 (brief asks for ~50 IBU: a stated deviation) |
| b18 | 15A Irish Red Ale | Caramel 100, Roasted Barley, Carafa Special Type 1 | out_of_style | too much colour | 18.7 SRM vs 9-14 (brief asks for 20 SRM: a stated deviation) |
| b10 | 26B Belgian Dubbel | Caramunich Type 3 | out_of_style | too much colour | 19.2 SRM vs 10-17 (no stated deviation; fixture target says 13.5) |

### Recipe totals more than one level below a style min (`too_little`)

| Recipe | Style | Sensation | Measured | Min |
|---|---|---|---|---|
| b07 | 1C Cream Ale | hop flavour | none (0) | low (2) |
| b12 | 18A Blonde Ale | hop flavour | none (0) | low (2) |
| b22 | Mexican-Style Amber Lager | roast | none (0) | low (2) |

### Decisions (user, 2026-10-15) and result

1. b08, b18: accepted in `ACCEPTED_LINES` as the briefs' own deviations (about 50 IBU, 20 SRM).
2. b10: Brown Candi Sugar 10 → 7 %, Pilsner Malt 70 → 73 %. Computed SRM 19.2 → 16.7 (style 10-17); OG 1.0685 unchanged; IBU 19.9 unchanged.
3. b07: added Willamette, 15 min, 15 g (IBU 13.7 → 18.5, style 8-20; hop flavour now low). b12: added Cascade, 15 min, 15 g (IBU 21.3 → 27.7, style 15-28).
4. b22 / Mexican-Style Amber Lager: roast `min` low → none (quote: "light roast ... may be present"); reloaded, 26 styles; the 53 golden cases still pass.

After these: `tests/test_style_fit_recipe.py` 5 passed, `ACCEPTED_TOTALS` empty; full `pytest` 530 passed, 1 failed (the known `test_db_enzyme_and_boil`) (measured).
