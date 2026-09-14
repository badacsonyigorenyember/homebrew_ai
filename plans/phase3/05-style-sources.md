# Book 5 — BA 2026 + the BJCP Beer Style Study Guide

**Written:** 2026-09-14 · **Status:** ⬜ **probed and planned, not run** · **Unblocked by:**
D31, ratified 2026-09-14 ([`../agent/03-record.md`](../agent/03-record.md) §5)

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

Three options, with the evidence for each:

| | Option | ⭐ Verdict |
|---|---|---|
| **A** | **Ingest wholesale through the engine** | ⛔ **No.** ~365 vital-stat sites restating the cards is defect (b) at scale, on the source D31 was written for |
| **B** | ⭐ **Ingest only the genuinely causal prose** — history, the *why* passages (the Paulaner/Salvator origin passage is the type specimen) — and drop tables, `Ingredients:` and `Commercial Examples:` | ⭐ **recommended**, and it is what §5.2 actually means. ⚠️ **Cost: likely far fewer than the ~130 chunks §4.3 projects** — possibly **under 60** |
| **C** | **Defer the Guide; run BA 2026 alone** | ⭐ **The honest fallback** if B's extraction proves fiddly. BA is the source book 5 exists for — it is what makes disagreement measurable, which is §4.2's reason the agent was built at 4.5 |

⛔ **Do not pick A because it is the least work.** It is the one option D31 was ratified to
prevent.

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

### Tier B — retrieval, the re-baseline

⛔ **Book 5 changes the style layer, so the standing regression questions must be re-run.**
§4.1's warning about reworking styles at book 5 applies to *adding* to them too: the top-6
competition changes.

⭐ **The question this book exists to answer**, and it cannot be asked before it runs:

> *"BJCP 15B and BA's Irish-Style Dry Stout state different numbers. Does the agent surface
> **both, attributed**, or silently average them?"*

That is Layer 4, it is the merge/conflict eval §4.2 deferred to book 5, and it is the first
point in the project where the cases can be written from **real** disagreements.

### Tier C — ⭐ **runnable for the first time**

⭐ **WF4 exists and 4.7's gate is now measurable** ([`../agent/03-record.md`](../agent/03-record.md)
§2.1), so book 5 is the first source that can be scored end to end as it lands. ⭐ **And the
retroactive backlog for books 0a–4 is still uncollected** — five plans × five questions,
already written in each plan's §4.

---

## §5 — Predictions to record before running

⚠️ **Deliberately left open — these are the numbers the next session must commit to *before*
the engine runs**, per standing rule 1 and the A1-style discipline books 1–4 used:

| | `predicted` |
|---|---|
| BA rows | **169** (from the probe; the one number already measured) |
| BA cards in `kb.chunks` | 169 × variant-B card count — ⬜ **decide 1 or 2 per style first** |
| Study Guide chunks | ⬜ **cannot be predicted until §2b's option is chosen** |
| Corpus after | ⬜ — ⚠️ **note that §4.3's ~2,344 running total already assumes ~100 BA cards, not 169** |

⛔ **Do not start the run until §2b is decided and these rows are filled in.**
