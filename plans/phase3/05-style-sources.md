# Book 5 — BA 2026 + the BJCP Beer Style Study Guide

**Written:** 2026-09-14 · **Status:** ✅ ⭐ **BOTH SOURCES RUN 2026-09-14** — BA 2026 169 rows / 169 cards, Study Guide 82 chunks, 0 embedding gaps · **Unblocked by:**
D31, ratified 2026-09-14 ([`../agent/03-record.md`](../agent/03-record.md) §5) · **§2b decided
2026-09-14: option B**

Follows [`README.md`](README.md) §6's plan contract. ⛔ **Nothing here has been ingested.**
Standing rule 3: this plan exists to be approved before an engine run, not after.

---

## §0 — The verdict, in one screen

⛔ ⭐ **Probe first, and the probe moved the plan twice.** Both corrections are in the
direction that matters — they make the job *different*, not merely bigger.

| | ⭐ `measured` 2026-09-14 | README §4.3 said |
|---|---|---|
| **BA 2026** | **74 p** · 37,890 words · ⭐ **169 style entries** | *"~100"* cards |
| **Study Guide** | **72 p** · 32,791 words · Microsoft Word 2010 | *"~130"* prose chunks |
| ⛔ ⭐ **Study Guide shape** | ⭐ **87% of non-empty lines are table-cell shaped (<25 chars); 9% are prose-shaped (≥60)** | *"the one style source that goes through the prose engine"* |
| ⚠️ **BA ligatures** | ⭐ **214 sites** of `ﬂ`/`ﬁ` | not mentioned anywhere |

⭐ **The headline: §5.2's premise about the Study Guide is not safe.** It calls the Guide
*"the one style source that goes through the prose engine"* whose *"rationale is genuinely
unique content; nothing else in the corpus has it."* ⛔ **The probe says the rationale is a
minority of the document**, and that much of its longest prose is `Ingredients:` and
`Commercial Examples:` — ⭐ **structured fields `ref.styles` already has columns for**
(`characteristic_ingredients`, `commercial_examples`).

⚠️ **Held honestly: `pdftotext` fragments tables and Docling's hybrid chunker does not**, so
87% is an upper bound on fragmentation rather than a measurement of table-vs-prose. ⭐ **But
the 365 vital-statistics markers and the field-shaped long lines are robust either way**, and
they point at the same conclusion: running this Guide through the prose engine wholesale
produces a large number of chunks that **restate the cards**.

⛔ ⭐ **That is precisely defect (b) — D31's Layer 1 case, and §5.1's "highest-probability
retrieval defect in the whole plan."** Book 5 is the first source with a real scoping choice,
which is exactly why D31 gated it; ⭐ **the gate turns out to bind on the Study Guide, not on
BA 2026.**

---

## §1 — What is already true

| | |
|---|---|
| Corpus | 2,090 chunks · 6 documents · 0 embedding gaps |
| `ref.styles` | **116 rows**, all `BJCP` / 2021 · **232 cards** in `kb.chunks` (variant B, two per style) |
| ⭐ **Schema readiness** | ✅ **no DDL needed.** `ref.styles` is already keyed `(guide, guide_year, code)` and already carries every widened column §5.3 asked for — `history`, `characteristic_ingredients`, `style_comparison`, `entry_instructions`, `tags[]`, `commercial_examples[]`, `has_vitals` |
| D31 Layer 2 | ⭐ **does not fire** — largest corpus share is Yeast at **22.2%** against a 25% threshold |

⭐ **The schema finding is worth stating plainly because it removes a whole phase of work.**
§5.3 lists "move and rename" and "widen the row" as book-5 changes. **Both were already done
at book 0b.** Book 5 is rows and chunks only.

---

## §2 — The two paths, and why they must not run together

⛔ **Standing rule 2 forbids running these as one variable**, and §4.1 already says so:
*"BA 2026 is structured rows, the Study Guide is prose scoped to rationale — different paths,
and running them back to back would change two variables."*

### 2a — BA 2026 → `ref.styles` rows → generated cards

The **structured** path, and the one with no open question. Each entry is a consistent
labelled block plus a single vitals line:

```
South German-Style Dunkel Weizen
Color: Copper-brown to very dark
Clarity: If served with yeast, appearance may be very cloudy
Perceived Malt Aroma & Flavor: ...
Perceived Hop Aroma & Flavor: Not present
Perceived bitterness: Low
Fermentation Characteristics: ...
Body: Medium to full
Additional notes: ...
Original Gravity (°Plato) 1.048-1.056 (11.9-13.8 °Plato) • Apparent Extract/Final
Gravity (°Plato) 1.008-1.016 (2.1-4.1 °Plato) • Alcohol by Weight (Volume)
3.8%-4.3% (4.8%-5.4%) • Hop Bitterness (IBU) 10-15 • Color SRM (EBC) 10-25 (20-50 EBC)
```

**Field mapping** — proposed, and the two marked ⚠️ are where a careless run goes wrong:

| BA field | `ref.styles` column |
|---|---|
| entry heading | `name`; `code` synthesised, `guide='BA'`, `guide_year=2026` |
| section heading | `category` |
| Color + Clarity | `appearance` |
| Perceived Malt / Hop Aroma & Flavor | `aroma`, `flavor` |
| Perceived bitterness | folded into `flavor` |
| Fermentation Characteristics | `comments` |
| Body | `mouthfeel` |
| Additional notes | `characteristic_ingredients` |
| `Original Gravity` 1.048-1.056 | `og_min` / `og_max` |
| `Apparent Extract/Final Gravity` 1.008-1.016 | `fg_min` / `fg_max` |
| ⚠️ **`Alcohol by Weight (Volume) 3.8%-4.3% (4.8%-5.4%)`** | ⛔ **`abv_*` takes the PARENTHESISED pair — 4.8-5.4.** BA leads with **weight**, BJCP with volume. Taking the first number silently records every BA style ~20% weaker than it is |
| ⚠️ **`Color SRM (EBC) 10-25 (20-50 EBC)`** | ⛔ **`srm_*` takes the FIRST pair.** Same trap, opposite direction |

⭐ **Those two rows are the whole risk of path 2a**, and both are checkable with one query
after the run (§4, A3/A4).

⚠️ **214 ligature sites** (`ﬂavor`, `ﬁnish`) must be normalised to `fl`/`fi` in the shared
cleaning code. ⭐ **This is the same class of defect as *Draught*'s 21 PUA sites** — a producer
shipping presentation glyphs into stored text — and it belongs in the same shared text pass,
not in a BA-specific rule.

### 2b — the Study Guide → ⛔ **scoping decision required before any run**

⭐ **This is the part this plan will not decide alone.** §5.2 pre-committed to *"rationale prose
only; vital-statistics tables dropped as duplicates of the cards."* The probe says that
instruction is right in principle and **under-specified in practice**, because the Guide's
non-table content is itself substantially field-shaped.

### ✅ ⭐ **Decided 2026-09-14: option B** — ingest only the genuinely causal prose

⭐ **The decision was taken against a direct text comparison, not against the line-shape
heuristic in §0**, which was only ever an upper bound. The Guide turns out to be **field
labelled**, not free prose, which makes the scoping exact rather than a judgement call:

| field | n | total words | median | |
|---|---|---|---|---|
| ⭐ **`History:`** | **69** | **5,289** | 66 | ✅ **KEEP** |
| ⭐ **`Techniques:`** | **16** | **847** | 56 | ✅ **KEEP** |
| `Overall Impression:` | 71 | 1,732 | 18 | ⛔ drop |
| `Comments:` | 70 | 4,849 | 65 | ⛔ drop |
| `Ingredients:` | 70 | 5,917 | 67 | ⛔ drop |
| `Commercial Examples:` | 68 | 13,769 | 205 | ⛔ drop |
| the sensory grids | — | — | — | ⛔ drop |

⚠️ **The drop-column word counts are unreliable upward** — the crude label-to-next-label split
lets `Commercial Examples:` swallow the following style's tables, which is why its median is
205 against everyone else's ~66. ⭐ **The two KEEP rows are bounded by a following label and
are trustworthy**, which is the only part the prediction rests on.

#### ⭐ Why the drops are drops: every one is already a column, fully populated

`measured` 2026-09-14 against `ref.styles` where `guide='BJCP'`:

```
rows 116 · overall_impression 116 · comments 116 · history 116
          · characteristic_ingredients 116 · commercial_examples 115 · style_comparison 116
```

⛔ **The Study Guide is a BJCP publication about BJCP 2021 styles, so four of its five labelled
fields restate rows the database already holds** — and those rows are already rendered into
the 232 cards competing in every retrieval. That is defect (b) exactly.

#### ⭐ Why `History:` is a keep and not a drop — the test that decided it

Both sources have a history for Doppelbock. **They are not the same text:**

| | |
|---|---|
| `ref.styles.history` (from `styles.json`) | *"…Breweries adopted beer names ending in '-ator' after a 19th century court ruling that no one but Paulaner was allowed to use the name Salvator."* |
| ⭐ **Study Guide** | the **etymology** of *Salvator* — "Savior", with a wink at the beer's sustaining qualities — the brewery's secularisation, the copyright, whether competitors were paying tribute or trading on popularity, ⭐ **who coined "doppelbock" and when** (Munich consumers, 18th century), and the Christmas/Easter brewing tradition |

⭐ **That is expansion, not restatement**, and it is the *why* D31's Layer 1 explicitly protects.
**`History:` is the source's genuine unique value, and it is the only field of its five that is.**

#### ⛔ ⭐ A field the plan never anticipated: `Techniques:`

*"Double or even triple decoction mash is traditional, starting with a protein rest, ultimately
raising the mash temperature to the high end of starch conversion temperatures…"*

⭐ **`ref.styles` has no column for this and nothing else in the corpus carries it** — it is
causal process content keyed to a style. ⚠️ **But it appears only 16 times, not ~70**, so it is
a minority field and must not be described as a systematic gain.

#### ⚠️ One honest wrinkle in the drop list

`Comments:` is **partial** overlap, not total. The Guide shares the DB row's opening but adds
material the DB lacks — the Starkbier tax category and the 16 °P threshold, for Doppelbock.
⛔ **It is still dropped.** Layer 1's rule is about a *second prose representation of the same
row*, and a near-duplicate chunk that competes in every top-6 is not worth one extra clause.
⭐ **Recorded rather than silently discarded** (standing rule 6) — if a later retrieval-share
measurement shows the gap costs answers, this is the row to revisit.

⛔ **Option A was rejected** — ~365 vital-stat sites restating the cards is defect (b) at scale,
on the very source D31 was written for. **Option C (defer the Guide) is no longer needed:** the
scoping is exact because the source is labelled, so B's extraction is a field filter, not a
judgement pass.

---

## §3 — Reset

```sql
-- rows and their generated cards, both scoped by guide
DELETE FROM kb.chunks WHERE version_id IN (
  SELECT v.id FROM kb.document_versions v JOIN kb.documents d ON d.id=v.document_id
  WHERE d.slug IN ('ba-2026-beer-styles','bjcp-style-study-guide'));
DELETE FROM ref.styles WHERE guide='BA' AND guide_year=2026;
```

⭐ **Rollback is clean by construction** — `ref.styles` is keyed `(guide, guide_year, code)`, so
BA 2026 deletes without touching the 116 BJCP rows, and the cards are regenerated from the
rows by the same `INSERT … SELECT`, so they cannot be orphaned.

---

## §4 — Testing

### Tier A — assertions, to be predicted **before** the run

| | Assertion |
|---|---|
| **A1** | `ref.styles` gains **169** rows at `guide='BA'` — the probe's entry count, exact |
| **A2** | the 116 BJCP rows are **unchanged**; `brew.recipes.style_id`'s FK still resolves |
| **A3** | ⛔ **no BA style has `abv_max` < 6 where BJCP's twin exceeds it** — the by-weight trap |
| **A4** | ⛔ **`srm_max` ≤ 100 on every row** — the EBC trap. An SRM of 50 with an EBC of 100 misread is the visible signature |
| **A5** | **0** rows with `has_vitals = true` and any null vital |
| **A6** | ⭐ **0 `ﬂ`/`ﬁ` codepoints** anywhere in `ref.styles` or the generated cards |
| **A7** | 0 embedding gaps |
| ⭐ **A8** | ⭐ **169 BA cards, not 338** — `count(*) = 169` for the BA document, and ⛔ **0 cards whose `heading_path` ends in `Context`** |
| ⭐ **A9** | Study Guide lands **25–40** chunks. ⛔ **If it lands >60, the field filter leaked** — the most likely culprit is `Commercial Examples:` running on into the next style's tables, which is exactly what inflated its word count in the probe |
| ⭐ **A10** | ⛔ **0 Study Guide chunks containing `Commercial Examples:`, `Ingredients:` or `Overall Impression:`** — the direct test that option B's drop list was applied |
| ⭐ **A11** | **69** chunks trace to a `History:` section and **16** to `Techniques:`, ±merging |

### Tier B — retrieval, the re-baseline

⛔ **Book 5 changes the style layer, so the standing regression questions must be re-run.**
§4.1's warning about reworking styles at book 5 applies to *adding* to them too: the top-6
competition changes.

⭐ **The question this book exists to answer**, and it could not be asked before it ran:

> *"BJCP 15B and BA's Irish-Style Dry Stout state different numbers. Does the agent surface
> **both, attributed**, or silently average them?"*

### ✅ ⭐ `measured` 2026-09-14 — **it surfaces both, attributed. It does not average.**

The disagreement is real and was confirmed in `ref.styles` before the question was asked:

| | OG | IBU | ABV |
|---|---|---|---|
| **BJCP 15B** Irish Stout | 1.036–1.044 | 25–45 | 3.80–5.00 |
| **BA 2026** Classic Irish-Style Dry Stout | 1.038–1.048 | 30–40 | 4.10–5.30 |

Asked *"What are the target numbers for an Irish Stout — OG, IBU and ABV?"*, the live agent
returned **both rows, under separate headings, each carrying its own `[S…]`**, and a Sources
block naming the two guides separately. ⭐ **Every number it printed matches the database
exactly.** It also volunteered BA's Export-Style Stout as a third, distinct entry rather than
folding it in.

| | ⭐ `measured` |
|---|---|
| citations | **6**, ⭐ **0 unresolved** — 4.7's grounding gate holds on book 5 |
| distinct sources cited | ⭐ **2** — `ba-2026-beer-styles` **and** `bjcp-2021-beer-styles` |
| latency | **27.8 s** — the retrieval path, not the 126 s capability path |

⭐ **This is D31 Layer 4 and requirement §5.5 — *"where sources disagree, present both rather
than averaging them"* — working in production for the first time**, and it is the payoff for
building the agent at 4.5 rather than after book 5 (§4.2). ⚠️ **One question, not a suite:**
the merge/conflict eval proper is still owed, and this is its first passing case, not its
completion.

### Tier C — ⭐ **runnable for the first time**

⭐ **WF4 exists and 4.7's gate is now measurable** ([`../agent/03-record.md`](../agent/03-record.md)
§2.1), so book 5 is the first source that can be scored end to end as it lands. ⭐ **And the
retroactive backlog for books 0a–4 is still uncollected** — five plans × five questions,
already written in each plan's §4.

---

## §5 — Predictions to record before running

⚠️ **Deliberately left open — these are the numbers the next session must commit to *before*
the engine runs**, per standing rule 1 and the A1-style discipline books 1–4 used:

### ⭐ `measured` 2026-09-14 — against the predictions below

| | `predicted` | ⭐ `measured` | |
|---|---|---|---|
| BA rows | **169** | ⭐ **169** | ✅ **exact** |
| BA cards | **169**, one per style | ⭐ **169**, 0 `Context` cards | ✅ **exact** |
| Study Guide chunks | **25 – 40** | ⛔ ⭐ **82** | ⛔ **falsified — see below** |
| Corpus after | ~2,290 | ⭐ **2,341** | ⚠️ off by the same 42 |
| BA embedding gaps | 0 | **0** | ✅ |
| Study Guide embedding gaps | 0 | **0** | ✅ |
| A10 dropped-field labels | 0 | ⭐ **0** | ✅ **the filter held** |
| A11 History / Techniques | 69 / 16 | ⭐ **67 / 15** | ⚠️ −2 / −1, the sub-8-word stubs |

⛔ ⭐ **A9 is falsified, and the fault is in the prediction's METHOD, not the data.**
25–40 came from dividing 5,900 kept words by the corpus's observed 180–250 words per chunk —
⭐ **but `Insert passages` maps one passage to one chunk**, and the passages average **72
words**. The prediction estimated a *merged* chunking that this path never performs.

⚠️ **That matters more than the number.** A9 was written as *"if it lands >60, the field
filter leaked"* — ⛔ **it landed at 82 and the filter did not leak.** A10 is **0**, and the
parse node asserts the ban independently before any insert. ⭐ **A badly-constructed assertion
does not just miss; it points at the wrong cause.** The lesson is the one §2.1 of the agent
record already drew: an assertion written against an imagined data shape is worse than none.

⚠️ **A11's −2/−1** is the extractor's `len(body.split()) < 8` stub filter, working as intended.

⭐ **D31 Layer 2, re-measured after the load:** largest corpus share is Yeast at **19.8%**
(was 22.2% — the corpus grew), against a 25% threshold. ⛔ **Layer 3 stays unbuilt**, which is
the ratified policy working rather than being skipped.

---

| | `predicted` | basis |
|---|---|---|
| **BA rows** | ⭐ **169** | the probe's `Original Gravity` entry count, exact |
| ⭐ **BA cards in `kb.chunks`** | ⭐ **169 — ONE card per style, not two** | see below |
| **Study Guide chunks** | ⭐ **25 – 40** | 6,136 kept words ÷ the corpus's observed 180–250 words per chunk |
| **Corpus after** | ⭐ **~2,290** (2,090 + 169 + ~32) | ⚠️ **§4.3's ~2,344 assumed ~100 BA cards and ~130 Guide chunks. Both were wrong, in opposite directions, and they nearly cancel** |

### ⭐ Why BA gets one card per style and BJCP gets two

BJCP uses **variant B** — `measured`: every style has a `… > Sensory` and a `… > Context`
card, 116 × 2 = 232. ⭐ **Variant B splits *disjoint* fields**, which is the whole reason §5.2
calls splitting legitimate and duplicating a defect.

⛔ **BA 2026 has no context half.** Its entry is `Color`, `Clarity`, `Perceived Malt Aroma &
Flavor`, `Perceived Hop Aroma & Flavor`, `Perceived bitterness`, `Fermentation
Characteristics`, `Body`, `Additional notes` — ⭐ **sensory almost end to end**. There is no
history, no style comparison, no entry instructions. A BA "Context" card would carry
`Additional notes` alone, and frequently nothing at all.

⭐ **A near-empty second card is not a split, it is 169 low-content chunks competing in every
top-6** — the same defect as duplication, arrived at from the other side. **One card per BA
style.** ⚠️ **This is a deliberate divergence from BJCP's shape, justified by the source's
field inventory and not by convenience** — and it costs nothing in consistency, because
§5.5's card-format A/B ⛔ **was never run**, so variant B was itself chosen without
measurement.

⛔ **Still to settle before the engine runs** — neither blocks planning, both block the run:

| | |
|---|---|
| **BA `code`** | BA publishes no style codes. A code must be **synthesised and stable**, because `(guide, guide_year, code)` is the key and a reshuffle on re-import would orphan cards. ⭐ **Propose: a slug of the style name** |
| **The ligature normalisation** | 214 `ﬂ`/`ﬁ` sites belong in the **shared** cleaning code with *Draught*'s PUA map, not in a BA-only rule — ⚠️ **which makes it the text pass's variable, not book 5's** (standing rule 2) |
