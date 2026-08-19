# Plan 03 — Malt: *A Practical Guide from Field to Brewhouse*, through the existing engine

**Status:** ✅ **built, run and scored** — ingested **2026-08-19 11:03:53 → 11:06:55 UTC**
(n8n executions 248/249, **3 min 02 s**), **340 chunks `measured`**; ⭐ **Tier A A1–A7 and all
11 Tier B questions run and recorded 2026-08-19** in §4.
⭐ ✅ **§1.2 item 1 is CLOSED** — the orphaned `Clean + normalise1` node was deleted in the UI at
**10:58:46 UTC**, five minutes before the run; the engine is **26 nodes**, live and tracked.
⛔ **One item open:** A3 **not yet observed**.
⚠️ **One item to reconcile:** ⭐ **two `ingest-malt` workflows exist** — §2.1a.
Tier C ⬜ **not runnable** (§4.3, book 4.5).
**Written:** 2026-08-19 · **§4 completed with `measured` results 2026-08-19**
**Prereqs:** book 0a's engine and schema (✅ live) · book 0b's styles model (✅ live) ·
book 1's *Water* (✅ 382) · book 2's *Yeast* (✅ 463) · ⛔ **§1.2's two items are both still
open** — item 1 handed over (a UI action), item 2 runs after the ingest
**Follows:** [`plans/phase3/README.md`](README.md) §6 — the per-source contract:
§0 verdict · §1 prerequisites · §2 build · §3 reset · §4 testing · §5 evidence.
⭐ **§5 was measured first and is placed last.** Every predicted number in §4 is a derivation
from §5's probe output.

> ## ⭐ Outcome — `measured` 2026-08-19
>
> **340 chunks. Every predicted number hit exactly — 30 of 30**, and the four unchanged-state
> checks on the rest of the corpus all held. ⭐ **That is the best result standing rule 1 has
> produced**: book 1 landed 18 of 19, book 2 landed 21 of 21, book 3 lands **30 of 30** —
> including the five-reason drop ledger, `page_count` 262, `min` 44, `max` 517 and the
> epigraph/footnote/over-512 residue counts, none of which needed a tolerance.
>
> | | ⭐ `measured` |
> |---|---|
> | §0's verdict — **mapper-only** | ✅ **held.** The only artefact book 3 added is a 2-node launcher. `Clean + normalise` is byte-identical to the one book 1 left behind |
> | ⭐ §0.1 — **the producer prediction** | ✅ **held on both halves.** **0** glyph runs in the stored corpus (A6) and **0** tabs across all five documents — from a source carrying **147,910** of them. ⭐ **Book 1's untab edit is now confirmed necessary, not merely safe** |
> | ⭐ §0.2 — **merge-forward decided against** | ✅ **vindicated by Q9.** The procedure-shaped control returns **6 of 6** from Malt at rank 1 (`By George de Piro` p.254). The 7 token-floor drops cost nothing a reader would have seen |
> | Tier A, A1–A7 | ⭐ ✅ **all seven pass exactly.** ⛔ **A3 not observed** |
> | Tier B, 11 questions | ⭐ ✅ **keep — and stronger than the rule requires:** all five prior rank-1 chunks are **still at rank 1**, not merely top 3, and Q1–Q5 are **byte-identical to the post-Yeast baseline**. All **5** positive controls at **rank 1**. Layer 2 fires on **nothing** for the third run running |
> | ⭐ §4.2a — *"Malt moves nothing"* | ✅ **correct in full.** **0 of 6** from Malt on every one of the five standing questions |
> | ⭐ §4.2d — the epigraph defect | ⛔ ✅ **predicted and confirmed.** `-Bill Simpson` retrieved at **rank 3 on Q8** and **rank 6 on Q6**, `-William Littell Tizard…` at **rank 4 on Q10**. ⭐ **Three questions, three unreadable citations — the defect is no longer cosmetic.** §4.2d |
> | ⭐ **standing rule 4** | ✅ **kept for the first time in the phase** — the launcher was in git before it was in a run |
> | ⚠️ **what the run did *not* settle** | `$5`'s ledger reads **2 / 2**, and a symmetric ledger cannot distinguish *stored* from *reconstructed*. Stated in §4.1 A2c rather than ticked |
> | ⭐ ✅ **the orphan is gone** | `Clean + normalise1` was deleted in the UI at **10:58:46 UTC** and the engine re-exported — **26 nodes**, live and tracked, for the first time since book 1 flagged it. ⭐ **The run at 11:03:53 therefore executed a 26-node engine**, and `Clean + normalise` is byte-identical at 8,229 characters |
> | ⛔ **still open** | A3 never observed · ⭐ **a duplicate `ingest-malt` workflow**, §2.1a |
>
> ⭐ **n8n expressions in this plan are written without the leading `=`** (README §6 §3.1).
> Paste them into the expression editor, which supplies the `=` itself. **The one place a `=`
> appears is §1.1's quotation of the exported `wf1-ingest-book.json`**, where it is part of the
> stored value and must stay.

**Target, in one line:** *Malt* (John Mallett, **335 pages**, `measured` via `pdfinfo`)
becomes **340 chunks** `predicted` in `kb.chunks`, through **`wf1-ingest-book` unchanged**,
driven by a new **2-node `ingest-malt` launcher** — `profile: book`, `authority: reference`,
`doc_type: book`.

---

## §0 — The verdict, in one screen

> ### ⭐ The headline: **mapper-only — the D30 split holds a third time.** And this is the book
> that makes book 1's one shared-code edit *load-bearing* rather than merely safe.
>
> | | Verdict |
> |---|---|
> | A new workflow | ⛔ **no** |
> | A new cleaning **profile** | ⛔ **no** — `book` fits, unchanged, and this time **all three of its rules fire** |
> | A line of **shared** code | ⛔ **no** — ⚠️ but see §0.1: the untab block book 1 added is **not** a no-op here, it is the thing that makes the file usable |
> | A schema change | ⛔ **no** |
> | ⭐ **merge-forward** (the fix book 2 put on the table) | ⛔ **no — and this is a decision, not a deferral.** §0.2 and §4.4 argue it. The pattern did **not** repeat |
> | The launcher's 13-field mapper | ✅ **yes, and it is the whole change** |
>
> ⭐ **README §4 predicted book 3 would exercise "table-dense body under `table_mode=accurate`".
> `measured`, that premise is wrong and it should be recorded as wrong:** *Malt* is **5.9%
> table chunks** (27 of 458) against *Yeast*'s **8.0%** (42 of 526). **It is the *least*
> table-dense book of the three.** §4.6 carries the correction to README §4.

### 0.1 ⭐ The prediction this book was planned to test, and how it came out

**The prediction, made from the producer line before the probe was read** (§1.1 records the
`pdfinfo` output that motivated it):

> *Malt* is produced by **calibre 3.32.0** — the same toolchain as *Water*, not *Yeast*'s
> `Creo Normalizer JTP`. *Water*'s `extra_drop_regex` was **empty** and its damage was
> **tabs**; *Yeast*'s glyph damage came from a `Creo`-produced broken `ToUnicode` map.
> **Predicted: Malt's fonts decode cleanly, it needs no glyph repairs, and it carries Water's
> tab problem instead.**

⭐ **`measured` (§5.1) — the prediction holds on both halves, and one half is stronger than
predicted:**

| | Predicted from the producer line | ⭐ `measured` §5.1 |
|---|---|---|
| glyph runs (`/gNNN`) in text | **0** | ✅ **0**, in all 458 chunks — and **0** in headings |
| tab characters | *"Water's problem"* — Water had **75,154** | ⛔ ⭐ **147,910** — **twice Water's**, and **more tabs than spaces** (73,955 tabs against 46,119 spaces in `text`) |
| chunks with a tab **inside a heading** | — | ⚠️ **296 of 458** (Water: 330 of 440) |
| chunks with any tab | — | ⛔ **457 of 458** |

⭐ **What that settles, and it is the finding of book 3: §0.3 of [`01-water.md`](01-water.md)
— the untab block — is confirmed as the right shared-code change, by a second source, at
double the scale.** Book 2 confirmed it was *safe* (0 tabs, provably a no-op). Book 3
confirms it is *necessary*: without it, 296 of Malt's headings would embed with tabs inside
them, `heading_path` would render `-Bill\tSimpson` in every citation, and the corpus's
oldest documented failure — heading text that disagrees with body text — would land again.

⛔ **And the counterpart: §0.3 of [`02-yeast.md`](02-yeast.md) — the glyph decoder — stays
unbuilt, and is now argued down twice.** The question that plan handed over was *"if a second
Brewers Publications title ships the same broken display font, the decoder becomes the right
shared-code change."* `measured`: **it does not.** *Malt* is a Brewers Publications title from
2014, four years after *Yeast*, and it has **zero** glyph damage. **The `+17` offset was a
property of one PDF's font subset, exactly as [`02-yeast.md`](02-yeast.md) §0.3 argued, and
this is the measurement that closes it.** ⚠️ It is closed *for now*, not forever — book 9's
stout guide is a different publisher again.

### 0.2 ⭐ The token floor — book 2's open design question, decided

[`02-yeast.md`](02-yeast.md) §4.4 said: *"One book, one chunk was a curiosity. Two books,
twelve chunks is a pattern. If Malt (book 3) shows it again, build merge-forward then."*

⭐ **`measured` (§5.5): Malt loses **7** chunks to the token floor, and **none of them is the
pattern.** The decision is therefore **do not build merge-forward**, and the reason is not
"seven is fewer than twelve" — it is that **the seven are a different shape**:

| | Yeast's 15 (book 2) | ⭐ Malt's 7 (`measured` §5.5) |
|---|---|---|
| what they are | **11 self-contained `Materials` lists** — the equipment prerequisite of a lab procedure, severed from the `Procedure` that follows | ⭐ **sentence tails** — the trailing remainder of a chunk split at `max_tokens`, carrying the **same heading as the chunk before them** (4 of 7 `measured`: 58/57, 110/109, 151/150, 344/343) |
| is information lost? | ⚠️ yes — the equipment list exists nowhere else | ⭐ **no** — the passage is intact in the preceding 510-token chunk; what is lost is its **last clause** |
| would **merge-forward** fix it? | ✅ yes — absorb `Materials` into the `Procedure` that follows | ⛔ **no.** These need merge-**backward**. Merging a sentence tail into the *next* section's opening would splice two unrelated passages |

⛔ **So the honest reading is that book 2 named the wrong fix, and book 3 is why we know.**
Two different problems were being counted as one: **severed prerequisites** (merge-forward)
and **split tails** (merge-backward). *Malt* has 7 of the second and **0** of the first;
*Yeast* had 11 of the first and 4 of the second.

⭐ **The decision, stated so §4.4 can be scored against it:** build neither at book 3. A
severed-prerequisite count of 0 on this book means the fix would be shared-engine code
justified by **one** source, which is precisely the argument [`02-yeast.md`](02-yeast.md) §0.3
used against the decoder — and which §0.1 has just vindicated. ⚠️ **The runner-up, argued on
the record: build merge-backward now**, since 4 of 7 are provably safe to merge. ⛔ **Rejected**
— it is an engine change landing in the same run as a new book, which is standing rule 2's
second variable, and its whole benefit is recovering a trailing clause from a passage the
reader already has.

⭐ **What book 3 adds so the next sighting is judgeable: a procedure-shaped positive control**
(§4.2, **Q9**). Book 2's evidence was weak because none of its ten questions asked a
lab-procedure question. Malt's Appendix D is 16 chunks of home-malting procedure and Q9 asks
about it directly.

### 0.3 Per-node verdict

Walked over all 26 wired nodes of `wf1-ingest-book`. ⭐ **Every row is *correct as-is*.**

| Node(s) | Verdict | Why |
|---|---|---|
| 1 `Ingest book input` | ✅ correct as-is | 13 fields; Malt fills all 13 |
| 2 `Read file for hashing`, 3 `Crypto`, 4 `Dedup lookup`, 5 `Is new file?`, 6 `Already ingested` | ✅ correct as-is | file-shaped source; **§4.1 A3 finally observes this branch** |
| 7 `Read file for upload` | ✅ correct as-is | Crypto consumes the binary it hashes (D13/D20) |
| 8 `Docling submit` | ✅ correct as-is | ten form fields verified byte-for-byte against the live node (§5.0) and used unchanged in the probe |
| 9 `Wait 15s`, 10 `Docling poll`, 11 `Assert task finished`, 12 `Docling fetch result` | ✅ correct as-is | conversion took **160.85 s** `measured`; the poll loop covers it |
| 13 `Clean + normalise` | ✅ **correct as-is** | ⭐ **and its untab block is load-bearing here** — §0.1. All three `book`-profile rules fire on this source, which no previous book managed |
| 14 `Ensure doc + version` … 25 `Assert embeddings` | ✅ correct as-is | `Loop Over Items` batchSize **32** `measured` → **11** batches for 340 chunks |
| 26 `Log ingest summary` | ✅ correct as-is | ⚠️ its promote message still interpolates the version **row id** — §0.4 |
| ⭐ ✅ `Clean + normalise1` (was the 27th) | ⭐ **deleted 10:58:46 UTC, before the run** | §1.2 item 1 — the engine is **26 nodes** |
| **`ingest-malt` (new, 2 nodes)** | 🆕 **the intended change** | 13 constants. §2 |

### 0.4 What is *not* built, so its absence is a decision

| Not built | Why |
|---|---|
| ⭐ A glyph **decoder** in shared code | ⛔ **closed by measurement, not deferred.** §0.1 — Malt is the second Brewers Publications title and has zero glyph damage, which is the exact test [`02-yeast.md`](02-yeast.md) §0.3 set |
| ⭐ **merge-forward** (or merge-backward) | ⛔ **decided against, §0.2.** The pattern book 2 predicted did not recur; a different one did, and it costs a trailing clause |
| A fix for `Log ingest summary`'s *"version N promoted"* | ⚠️ **not here.** README §9 says fix it *"in a run that is already touching the engine"*. ⛔ **Book 3 is not one.** §1.2 item 1 **deletes an orphaned node**; it does not edit a line of executing code, and §0's mapper-only verdict is worth more than a cosmetic string nothing reads. **Hand it to book 4**, whose verdict is already *not* mapper-only |
| A retrieval change | ⛔ **explicitly not.** §4.2b's Layer-2 check may fire; Layer 3 is built **when it fires**, not in advance |
| ⭐ `PARTITION BY d.id, c.heading_path` | ⛔ **explicitly not** — [`02-yeast.md`](02-yeast.md) §4.2c measured that it would have deleted three good answers. §4.2c uses the **(`heading_path`, `page_from`) pair** metric instead |
| An `extra_drop_regex` alternative for the epigraph headings | ⛔ **no — §2.5.** All five are real chapter-opening prose. This is *Water*'s `-J. Palmer`, not *Yeast*'s `Palmer, John` |

---

## §1 — Prerequisites

### 1.1 What is already true — verified against the live stack, 2026-08-19

Re-measured for this plan. ⛔ **Nothing below is carried from the prompt or from
[`02-yeast.md`](02-yeast.md).** All values `measured`.

| Check | Command | Result |
|---|---|---|
| corpus totals | the §4 A4 query | **1,524** chunks · **0** embedding gaps · **4** `is_current` · **1024** dims (one distinct value) |
| `kb.documents` | the §4 A1 query | `how-to-brew-palmer` **447** (30/291/524) · `water-comprehensive-guide` **382** (31/342/513) · `yeast-practical-guide` **463** (30/313/512) · `bjcp-2021-beer-styles` **232** |
| n8n workflows | `n8n list:workflow` | ⭐ **5** — `wf1-ingest-book` `NoNCV2mkQEppWP7O` · `ingest-how-to-brew` `BAe1fP1g7ZUsbIaq` · `ingest-water` `ciWYDt5MhFseACiN` · `ingest-bjcp-styles` `Ejf3ESE3SK1XBqe3` · `ingest-yeast` `UvDB7iJdXH262CNl`. ⛔ **None is an agent, none is a tool** |
| ⚠️ `wf1-ingest-book` node count | live export + tracked JSON, connection graph walked | ⛔ **27 in both** at the time of writing — 26 wired, 1 orphan `Clean + normalise1`, `jsCode` **4,259** chars against the live `Clean + normalise`'s **8,229**, and **no untab block**. ⭐ **Closed later the same day: §1.2 item 1, now 26** |
| ⭐ **`$5` — read back, not assumed** | `select r->>'find', (r->>'applied')::int from kb.ingest_log, jsonb_array_elements(detail->'repairs') r` | ✅ **four rows, `54 / 17 / 10 / 6`**, summing to 87 — the Yeast ledger, still stored. ⚠️ §4.1 A2c states what Malt's ledger can and cannot prove |
| ⛔ `detail ? 'repairs'` across the log | `select stage, detail ? 'repairs' from kb.ingest_log` | **8 rows, true on exactly one** — Yeast's `clean`. The `$5` edit post-dates books 0a/0b/1 |
| ✅ the untab block | live `Clean + normalise` | **present** (`const untab = …replaceAll('\t',' ')`), above the repair loop |
| `PROFILES` | live `Clean + normalise` | **one key, `book`.** `ba_manual` and `byo_magazine` are comments behind a deliberate throw |
| `Loop Over Items` | live export | `batchSize` **32** |
| `doc_type` / `authority` CHECKs | prior books | `book` and `reference` both legal (`measured` at book 2, unchanged) |
| Docling · Ollama | `/health` · the §5 probe | `{"status":"ok"}` · bge-m3 at 1024 dims |
| ⭐ **the source file** | `sha256sum` | ✅ **`c85d388f8ff828313d2d364625072530d7e4b00c8b0a0235903af22a76169579`** — the value §3 is keyed on |
| ⭐ the PDF itself | `pdfinfo` | **335 pages** · Title *Malt: A Practical Guide from Field to Brewhouse* · Author **John Mallett** · Producer ⭐ **`calibre 3.32.0`** · page size **612 × 792 pt (letter)** · 6,113,751 bytes |

**Two things this re-measurement establishes that the rest of the plan depends on:**

- ⭐ **`$5` is proven-once and is treated as such.** The ledger was read back, not assumed.
  ⚠️ **But Malt cannot strengthen that proof** — §2.4 has **two** pairs and both will read
  `applied = 2`. A symmetric ledger cannot distinguish *stored* from *reconstructed*, which is
  exactly the bound [`02-yeast.md`](02-yeast.md) §4.1 A2c named. §4.1 A2c says so instead of
  ticking it.
- ⭐ **The `book` profile is still the only one implemented, and Malt is the first source where
  all three of its rules fire.** `dropHeading` takes the **Index (62)**, `dropReferences` takes
  the **chapter reference lists (12)**, `minTokens` takes **7**. Water used two of three;
  Yeast used **none** of the heading rules.

### 1.2 What must be done first — two items, one of which is done before the build

**1. ⛔ Delete the orphaned `Clean + normalise1` node — in scope this time, and ⛔ not achieved.** Flagged at book 1,
flagged again at book 2, still live. `measured` 2026-08-19 in both the live workflow and the
tracked JSON: no incoming connection, no outgoing connection, `jsCode` **4,259** characters
against the live node's **8,229**, and ⛔ **it lacks the untab fix** — a *third* divergent copy
of the cleaning profile, in a book where the untab fix is load-bearing (§0.1). Delete it in the
UI, then re-export so the engine is **26 nodes** as documented:

```bash
docker exec n8n n8n export:workflow --id=NoNCV2mkQEppWP7O --pretty --output=/demo-data/workflows/wf1-ingest-book.json && docker exec n8n chown 1000:1000 /demo-data/workflows/wf1-ingest-book.json
```

⭐ ✅ **DONE 2026-08-19 at 10:58:46 UTC — in the UI, five minutes before the run.**

⚠️ **It could not be done from the CLI, and that is why it took three books.** `measured`:
`n8n --help` offers `export:workflow`, `import:workflow`, `list:workflow`, `publish:workflow`,
`unpublish:workflow`, `execute` and `audit` — **there is no node-level edit.** The only CLI
route was `import:workflow` over `wf1-ingest-book`, and ⛔ **that was explicitly refused**: an
import rewrites the engine's stored version, which is a second variable in a run that should
have one, on the one workflow every book depends on. **So it was handed over, and done by hand.**

⭐ **`measured` after the fact, against the live stack:**

| Check | Result |
|---|---|
| `wf1-ingest-book` node count, **live** | ⭐ ✅ **26** |
| node count, **tracked JSON** | ⭐ ✅ **26** |
| `Clean + normalise1` present | ⭐ ✅ **no** — in either |
| ⛔ `Clean + normalise` unchanged | ✅ **8,229 characters**, untab block present, `repairCounts` loop present — **byte-identical to the node book 1 left behind** |
| the engine the run executed | ⭐ **26 nodes** — the deletion at 10:58:46 preceded execution 249 at 11:03:53 |

⭐ **Flagged at book 1, flagged again at book 2, closed at book 3.** ⚠️ **It changed nothing
about the ingest** — the orphan had no connections and n8n never reached it — which is exactly
what made it survive two books. **The value is that there is no longer a third divergent copy
of the cleaning profile in tracked source.**

⛔ **This does not touch `Clean + normalise` itself.** The live cleaning profile stays
byte-identical, and ⚠️ **nothing in book 3 depends on the deletion** — the orphan has no
connections, so the ingest is unaffected either way. It is hygiene, and it is the third book
in a row it has been carried into.

**2. ⭐ A3 — the dedup short-circuit — runs as the *last* step of this session, not the first.**
⚠️ **It cannot be checked retroactively**: a short-circuit writes nothing. It has never been
observed on a book launcher since book 0a. ⭐ **Book 1's attempt failed for a knowable reason** —
n8n executions 244/245 were launched **86 s before the first run committed its version row**, so
dedup found nothing, the full path ran, and it finished with status **`success`** having promoted
nothing. **So: run the ingest, wait for the `promote` log row to exist, then run A3.** §4.1 A3
has the commands.

⛔ **Neither blocks writing this plan.** Item 1 is done before the build; item 2 is done after
the run.

**The Tier B baseline is the post-Yeast one** in [`02-yeast.md`](02-yeast.md) §4.2, `measured`
2026-08-19 at 1,524 chunks. ⛔ **Not the post-Water table in [`01-water.md`](01-water.md) §6.**
Do not re-derive it.

---

## §2 — The build

**Two nodes exist that did not before. Nothing else changes anywhere.**

### 2.1 🆕 `ingest-malt` — the new launcher, 2 nodes

Copied from `ingest-yeast` (`UvDB7iJdXH262CNl`, 2 nodes, `measured` from the tracked JSON).

| # | Node | Settings |
|---|---|---|
| 1 | `When clicking 'Execute workflow'` — Manual Trigger | none |
| 2 | `Call 'wf1-ingest-book'` — Execute Sub-workflow (typeVersion 1.3) | **Source** `Database` · **Workflow** `wf1-ingest-book` (`NoNCV2mkQEppWP7O`) · **Mode** `Run once with all items` · ⛔ **Wait for Sub-Workflow Completion ON** |

⚠️ **Wait-for-completion ON is not optional.** Off, the launcher reports success the moment
Docling is handed the file, and a failed ten-minute ingest looks like a green check.

**Workflow Settings:** Execution Order `v1`, Binary Mode `separate` — matching the other four
launchers. **Do not activate it**; a manual trigger needs no activation.

⛔ **Export and commit it before the first run — standing rule 4, broken at book 1 and again at
book 2.** The export is part of this build step, not a follow-up to it:

```bash
docker exec n8n n8n export:workflow --id=ingestMalt00001A --pretty --output=/demo-data/workflows/ingest-malt.json && docker exec n8n chown 1000:1000 /demo-data/workflows/ingest-malt.json
```

> ### ⭐ How it was actually built, 2026-08-19 — stated because it is not the UI copy
>
> `ingest-yeast`'s tracked export was copied on disk, the **13 mapper fields** replaced with
> §2.2's values, fresh node UUIDs and a fresh `versionId` assigned, the `shared` block dropped,
> and the result imported with `n8n import:workflow`. **Then it was exported back out of n8n**
> and that export is what is committed — so the tracked JSON is n8n's own copy, not the input.
>
> ⚠️ **Why this is not the thing §1.2 refuses.** §1.2's objection is to importing over
> **`wf1-ingest-book`**, an existing workflow every book depends on. `ingest-malt` did not
> exist; there was nothing to overwrite and nothing to deactivate. `measured` immediately
> after: all six workflows `active=false`, `ingest-yeast` unchanged at 2, and
> `wf1-ingest-book` unchanged — ⚠️ **27 nodes at that moment; the orphan was deleted
> separately, by hand in the UI, later the same day** (§1.2 item 1).
>
> ⭐ **Verified from the round-tripped export, not from the input file:** id
> `ingestMalt00001A`, **2 nodes**, `executeWorkflow` typeVersion **1.3**,
> `waitForSubWorkflow: true`, settings `executionOrder v1` / `binaryMode separate`,
> connection graph **byte-identical** to `ingest-yeast`'s, the 13-entry input **schema**
> identical to `ingest-yeast`'s, and all **13** mapper values matching §2.2/§2.3/§2.4
> character for character.
>
> ⚠️ **If you would rather have it built by hand in the UI, delete it and rebuild it** — the
> plan is complete enough to do that, and §2.2's table is the whole content.

### 2.1a ⚠️ ⭐ Two `ingest-malt` workflows exist — `measured` after the run

⛔ **This is drift and it is recorded rather than tidied away.** `measured` 2026-08-19,
`n8n list:workflow` returns **seven** entries and two of them are named `ingest-malt`:

| id | Built | Executed | Tracked |
|---|---|---|---|
| ⭐ **`hpW9P0n7fxXY9KdF`** | in the **UI** | ⭐ ✅ **yes — executions 248/249, the run this record is about** | ⭐ ✅ **this is what `ingest-malt.json` now holds** |
| `ingestMalt00001A` | by `import:workflow` from a modified copy of `ingest-yeast`'s export (§2.1) | ⛔ **never** | ⛔ **no longer** |

⭐ **The two were diffed field by field before anything was decided, and all 13 mapper values
are identical** — `file_path`, `slug`, `title`, `authors`, `edition_note`, `authority`,
`profile`, `front_matter_max_page = 24`, `extra_drop_regex = ^Bibliography$` and
`text_repairs` character for character, plus identical node names, connections and workflow
settings. **That is why §4.0's predictions score against the run at all.**

⚠️ **One representational difference, checked rather than assumed.** The executed workflow
stores `options: {}`; the imported one stores `options: {"waitForSubWorkflow": true}`.
⭐ **`measured` from the node's own source** —
`getNodeParameter('options.waitForSubWorkflow', 0, true)` — **the default is `true`**, so an
empty options object waits. ⭐ **Corroborated by the execution record:** the launcher (248)
stopped **0.76 s after** the engine (249), not in milliseconds as a non-waiting launcher would.
**Wait-for-completion was ON.**

⭐ **Why the tracked JSON is the executed one.** A launcher's whole purpose in this phase is to
be the reproducible record of *what ran*. Tracking the copy that never executed would have made
`ingest-malt.json` a plausible-looking lie — exactly the failure standing rule 4 exists to
prevent, arriving from the opposite direction.

⛔ **The unused duplicate should be deleted, and it is a UI action.** There is no
`delete:workflow` in the n8n CLI — ⭐ **the same constraint that kept `Clean + normalise1` alive
for three books, and which was closed the same way: by hand** (§1.2). ⚠️ **Two workflows with the
same name is worse than an orphaned node with a unique one** — the next person to click Run has
a 50% chance of running the wrong artefact.

### 2.2 ⭐ The mapper — the 13 fields, and where each value came from

The engine's Execute Workflow Trigger uses **Define using fields below**, so node 2 renders all
13. **This table is the entire book-specific content of this plan.**

| Field | Value | Source of the value |
|---|---|---|
| `file_path` | `/data/shared/rag-files/pending/malt-a-practical-guide-from-field-to-brewhouse-978-1-938469-12-1-1-938469-12-7-978-1-938469-16-9.pdf` | the **container** path; n8n cannot see the host path |
| `source_format` | `pdf` | drives `convert_from_formats` on node 8 |
| `slug` | `malt-practical-guide` | new; matches the `<topic>-<qualifier>` shape of `yeast-practical-guide` |
| `title` | `Malt: A Practical Guide from Field to Brewhouse` | ⭐ `measured` from the PDF's own Title field |
| `doc_type` | `book` | legal value |
| `authors` | `John Mallett` | ⭐ `measured` from the PDF's own Author field |
| `language` | `en` | |
| `edition_note` | `Brewers Publications, 2014` | ⭐ `measured` — probe chunk 0 carries `© Copyright 2014 by Brewers Association` and LCCN `2014038768`. Not guessed |
| `authority` | `reference` | a reference work, not a guideline and not practitioner opinion |
| `profile` | `book` | the only implemented profile, and the correct one (§0.3) |
| ⭐ `front_matter_max_page` | **`24`** | ⛔ **§5.2, `measured` chunk by chunk.** ⚠️ **Not 21, not 18, not 6.** Those are facts about *Yeast*'s, *Water*'s and *How to Brew*'s PDFs |
| ⭐ `extra_drop_regex` | **see §2.3** | ⛔ **§5.3, `measured`.** ⚠️ **One alternative, not seven — the shared rules do most of the work on this book** |
| ⭐ `text_repairs` | **see §2.4** | ⛔ **§5.6, both pairs counted against the Docling output.** ⛔ **Not the hyphen probe's draft — the draft is empty and it is wrong** |

⛔ **Three of these thirteen are per-book constants that must never be copied from another
book:** `front_matter_max_page`, `extra_drop_regex`, `text_repairs`. All three are `measured`
in §5 for this file specifically.

### 2.3 ⭐ `extra_drop_regex` — one alternative, and why only one

**Paste this as one line into the launcher's `extra_drop_regex` field** (the engine compiles it
`new RegExp(EXTRA, 'i')` and tests it, unanchored, against the joined heading path — **after**
the untab pass, so it is written with spaces, not tabs):

```
^Bibliography$
```

| # | Alternative | Drops | Pages | Why the shared profile misses it |
|---|---|---|---|---|
| 1 | `^Bibliography$` | ⭐ **8** | 263–270 | `dropHeading` has `Contents\|Index\|Glossary\|Acknowledg\|Copyright\|About the Author` and **not** `Bibliography`; `dropReferences` tests `^references$` and the heading is `Bibliography`. ⭐ `measured`: the string occurs on **no page outside 263–269** |

⭐ **What the shared rules take, so the contrast with book 2 is on the record:**

| Rule | Malt (`measured`) | Yeast (`measured`, book 2) |
|---|---|---|
| `dropHeading` — `^(Contents\|Index\|…)` | ⭐ **62 chunks** — the whole Index, pp.271–334, under a **readable** `Index` heading | ⛔ **0 of 262 headings** |
| `dropReferences` — `^references$` | ⭐ **12 chunks** — the per-chapter citation lists, pp.32–220 | ⛔ **0** |
| `extra_drop_regex` | **8** | **27** |

⛔ **What deliberately is *not* in the regex, each argued:**

| Not dropped | Chunks | Why |
|---|---|---|
| ⭐ **`Footnotes`** | **8 kept** (of 9; the 9th is front matter) | ⭐ `measured` §5.4: these are **substantive explanatory footnotes**, not citations — they define *friable*, the *scutellum*, the *basal/distal* ends, the Zadoks index. Dropping them would delete definitions a brewer would search for. ⚠️ **This is a decision and it may be wrong**; §4.2 watches whether a `Footnotes` chunk ever reaches a top-6 |
| ⭐ **`Commercially Available Malts in the US as of 2014`** | **18** | ⭐ Appendix A, pp.232–248 — a **maltster × product × °L table**. This is the single most retrievable reference block in the book and dropping back matter by position would have taken it |
| **`North American Malthouse Capacity` / `North American Craft Maltsters`** | **3** | Appendices B and C — data, not apparatus |
| ⭐ **Appendix D — home malting** | **16**, pp.254–262 | ⭐ a complete procedure by George de Piro. **This is what §4.2's Q9 positive control retrieves** |
| ⚠️ **the five epigraph-attribution headings** | **5** | §2.5 — real chapter-opening prose. ⛔ **A `^-` alternative would delete all five** |

### 2.4 ⭐ `text_repairs` — two pairs, and the hyphen probe was *wrong to return nothing*

**Paste this JSON string into the launcher's `text_repairs` field** (the field is typed
`string`; the engine `JSON.parse`s it):

```json
[["212220","212-220"],["5565","55-65"]]
```

| # | find | replace | in `text` | in `raw_text` | `applied` | What it is |
|---|---|---|---|---|---|---|
| 1 | `212220` | `212-220` | 1 | 1 | **2** | ⭐ chunk 377, p.256, `Equation 1 :` — *"heated at 212-220°F (100-104°C) for three hours"*, the oven range for the moisture-content drying method |
| 2 | `5565` | `55-65` | 1 | 1 | **2** | ⭐ chunk 382, p.259, `The Malting Phases` — *"the temperature of the grain should be maintained in the range from 55-65°F (12.8-18.3°C)"*, the germination temperature range |
| | | | | | ⭐ **4** | `predicted` total `repairs_applied` |

⛔ **Both sites are in *kept* chunks, and both are exactly the failure standing rule 7 exists
for**: a plausible wrong number. `212220°F` and `5565°F` are not parse errors — they are values
a reader would take at face value, in the two places the book tells a home maltster what
temperature to use.

⭐ **The finding: the hyphen probe returned `0 at-risk site(s)` and that is a false negative.**
§5.6 has the full account. In one line: **Docling converts every en dash to an ASCII hyphen
(`measured`: 0 en dashes, 0 em dashes, 5,856 ASCII hyphens in the output), and this book's
numeric ranges are set with en dashes.** `scripts/hyphen-probe.sh` matches `[\d.,]+-$` on the
`pdftotext -layout` output, where the en dash is still an en dash — so it sees nothing, while
Docling goes on to join the wrap and drop the dash.

⚠️ **Three books, three different failures of the same draft**, and this is the one that would
have cost data:

| Book | The probe's draft | What it actually was |
|---|---|---|
| 1 · Water | 5 pairs | ⛔ two wrong — one matched nothing, `["35","3-5"]` matched **79** places |
| 2 · Yeast | 1 pair | ⛔ matched nothing — would have aborted the ingest, correctly |
| ⭐ **3 · Malt** | ⛔ **`[]`** | ⛔ **missed two real fusions in kept text.** The first failure mode that is **silent** — an empty draft aborts nothing and looks like a clean bill of health |

⭐ **This is a defect in `scripts/hyphen-probe.sh`, not in this book**, and it is recorded here
rather than fixed: the script's regex should accept `[-‐–—]$`, and §4.6 hands that to whichever
session next touches `scripts/`. ⛔ **Fixing it now is a second variable in this run.**

**What is deliberately *not* repaired**, `measured` §5.6: three further fusions exist —
`18501990` (a bibliography date range), `317328` and `102150` (bibliography page ranges) — and
**all three are inside chunks this plan drops**. Adding pairs for them would inflate the ledger
without changing a byte of the corpus.

**Why these are repairs and not fabrication:** both pairs restore a dash the page prints and
the extractor deleted. Nothing is inferred.

### 2.5 ⚠️ What is left broken, stated so it is a decision and not an oversight

After §2.3 and §2.4, `measured` by simulation over the probe:

| Residue | Count | Why it is not repaired |
|---|---|---|
| ⭐ kept chunks under an **epigraph-attribution heading** | **5** — `-Bill Simpson` ×2 (p.202), `-Louis Pasteur` (p.114), `-Thomas Fuller 1` (p.52), `-William Littell Tizard, The Theory and Practice of Brewing Illustrated` (p.221) | ⛔ **this is *Water*'s `-J. Palmer` on a third document, and it must not be treated as *Yeast*'s `Palmer, John`.** `measured`: all five are **real chapter-opening prose** — the malt-COA discussion, the purpose of malting, the milling chapter's opening. Yeast's five were **index entries**, which is why dropping them was right there and is wrong here. **Recorded as a carried defect; §4.2d watches it** |
| kept chunks over **512 tokens** | **1** — chunk 353, p.234, 517 tokens, Appendix A's malt table | `chunking_max_tokens=512` is Docling's target, not a guarantee; ≪ bge-m3's 8,192 window, so nothing truncates. Water carried 1 as well |
| kept chunks with **glyph noise** | ⭐ **0** | §0.1 — there is none to repair |
| kept chunks with a **tab** | ⭐ **0** | §0.1 — the untab block clears all 147,910 |

**The honest summary: Malt lands with the best hygiene of any source so far on every gate
except one — the epigraph headings, which are the corpus's oldest unfixed defect appearing for
the third time.** Both facts belong in the record.

### 2.6 Overlap scoping (README §3 Layer 1)

**Malt overlaps *How to Brew* on grain bills, malt colour and the mash, and ⛔ nothing is
dropped.**

| | `measured` 2026-08-19 |
|---|---|
| README §3.1's named overlap involving Malt | *malt/yeast basics* (How to Brew × **Malt** × Yeast) — ⚠️ medium |
| The live competitor | *How to Brew*'s grain and mash chapters; `4.2 Water Chemistry Adjustment…` p.39 is the **current rank-1 chunk for standing question Q2** |
| Malt's own coverage of the same ground | `Formulating a Grain Bill` **6 chunks pp.35–39** · `Color Calculations` p.41 · `Malt Color Units (MCU)` p.43 · `Malt Family Descriptions` pp.136–146 · `Diastatic Power in Malts` 2 chunks p.131 · `Dry Milling` **5 chunks pp.221–223** · `Acidulated Malt` p.144 |

⛔ **Expected overlap chunks dropped: 0.**

**Why — the rule, not a preference.** README §3.2 category **(a), topical overlap: keep
unconditionally.** *How to Brew* gives malt one chapter; Mallett gives it 335 pages. An
ingest-time deletion is irreversible and untargeted; a query-time filter is reversible and
per-question. At a `predicted` 1,864 chunks neither storage nor precision forces the issue.

**Category (b), representational duplication, does not occur.** Appendix A's malt table is a
prose chunk, not a structured row set — ⭐ **there is no `ref.malts` table for it to drift
against, and this plan does not create one.** That is a book-7 shape (the hop handbook), and
inventing it here would be a schema change inside a mapper-only book.

⛔ **Nothing in this plan may touch the 447 *How to Brew*, 382 Water or 463 Yeast chunks.**
§4.1 A1 checks all three.

### 2.7 What this source does to WF4

**WF4 does not exist** (`measured` §1.1 — five workflows, none an agent). So: **nothing changes,
and that is the point.**

⭐ **Book 1 paid this cost once, for all nine books.** [`01-water.md`](01-water.md) §9.1's
de-enumerated system-prompt sentence means every source from book 2 to book 9 costs zero prompt
edits, and Malt is the second book to test it: **no prompt edit, no tool-description edit, no
`numCtx` change, no context-budget change.** Malt's `predicted` median of **339 tokens** sits
between Water's 342 and Yeast's 313, so six-chunks-in-context is unchanged.

⛔ **`scripts/stress/tier1_routing.py` is not run for this source** — it measures tool routing
against a system prompt, and there is neither. It runs when WF4 is built (book 4.5).

---

## §3 — ⭐ Reset: undo everything this workflow added

**Run this to start over.** It works on a **partial** run as well as a complete one — a
workflow that died in the embedding loop has already written a `kb.documents` row, a
`kb.document_versions` row and some of its chunks, and this removes all of it.

```sql
DELETE FROM kb.document_versions
WHERE file_sha256 = 'c85d388f8ff828313d2d364625072530d7e4b00c8b0a0235903af22a76169579';
```

As one command:

```bash
docker exec supabase-db psql -U postgres -d postgres -c "delete from kb.document_versions where file_sha256='c85d388f8ff828313d2d364625072530d7e4b00c8b0a0235903af22a76169579';"
```

| | |
|---|---|
| **Keyed on** | the Malt PDF's SHA-256, ⭐ **verified with `sha256sum` 2026-08-19** (§1.1) — so it cannot touch another document, whatever else is in the corpus |
| **Cascades** | `kb.chunks` from the version · `kb.chunk_embeddings` from the chunks · `kb.ingest_log` from the version |
| **Left behind** | ✅ the `kb.documents` row, deliberately. The next run reuses it through `ON CONFLICT (slug) DO UPDATE`; deleting it gains nothing and risks the FK |
| ⛔ **Cannot undo** | ⭐ **one thing, and it is new at book 3: the deletion of the orphaned `Clean + normalise1` node** (§1.2 item 1). That is an n8n edit, not a database row. It is recoverable from git — `git show d7360b3:n8n/demo-data/workflows/wf1-ingest-book.json` still holds the 27-node export — and it is **deliberately done before the run** so that a reset never has to consider it. Otherwise nothing: no shared-code edit, no schema change |

**Verify — `predicted` `1524 · 0 · 4` after a reset, `1864 · 0 · 5` after a good run:**

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select count(*) from kb.chunks; select count(*) from kb.chunks c left join kb.chunk_embeddings e on e.chunk_id=c.id and e.model='bge-m3' where e.chunk_id is null; select count(*) from kb.document_versions where is_current;"
```

Then re-run `ingest-malt`. ⚠️ **The dedup branch is keyed on the same hash**, so the reset is
what makes a re-run possible at all — without it the second run stops at `Already ingested`,
which is also §4.1 A3's test.

⛔ **This plan never runs the reset.** It is written so it exists before it is needed.

---

## §4 — Testing

Three tiers. **Tiers A and B are required; Tier C is not runnable and §4.3 says why rather than
omitting it.** Every command is copy-pasteable with its expected output stated.

### 4.0 ⭐ The gate table — predicted before the run, measured after

> ⭐ **The result in one line: every predicted number was hit exactly — 30 of 30.**
> `measured` **2026-08-19** against the live stack; the run itself was **2026-08-19 11:03:53 →
> 11:06:55 UTC**, n8n executions **248** (launcher) and **249** (engine).
> ⭐ **The 30 are the 20 predicted rows of the table below, the 5-reason drop ledger, and A7's
> four residue counts.** The table's last four rows are not predictions about *Malt* — they are
> unchanged-state checks on the rest of the corpus, and all four held.
> ⛔ **No prediction in this plan was falsified.**

⭐ **Every number below is a derivation from §5's probe, computed by *simulating the query that
will check it***, not by hand-counting next to one. That distinction is
[`02-yeast.md`](02-yeast.md)'s single lesson about where prediction fails: book 2's two misses
were both numbers written by hand beside probe-derived ones — a check that counted *sites* and
asserted *rows*, and a residue counted on the wrong field.

| Check | **Predicted** | **Measured** | Derived from | Gate |
|---|---|---|---|---|
| raw chunks from Docling | **458** | ✅ **458** — exact | `measured` §5.1 | ±2 — a different count means a different Docling |
| **kept chunks** | **340** | ✅ **340** — exact | `predicted` from `measured` | **±10% → 306–374** |
| dropped, total | **118** | ✅ **118** — exact | `predicted` | ledger below |
| median tokens | **339** | ✅ **339** — exact | `predicted` | ✅ **200–450** |
| p25 / p75 tokens | **160 / 482** | ✅ **160 / 482** — exact | `predicted` | ⚠️ p25 is **below 200** — §4.4's documented miss |
| max / min tokens | **517 / 44** | ✅ **517 / 44** — exact | `predicted` | ≪ bge-m3's 8,192 window; nothing truncated |
| **under-30 after cleaning** | **0** | ✅ **0** | `predicted` | ⛔ **must be 0** |
| ⚠️ **over-512 after cleaning** | **1** | ✅ **1** — A7 | `predicted` — chunk 353, Appendix A's malt table | ⚠️ **1, matching Water; §2.5** |
| **missing `page_from`** | **0** | ✅ **0** | `predicted` from `measured` (0 in the raw probe) | ⛔ **must be 0** |
| **missing `heading_path`** | **0** | ✅ **0** | `predicted` — the probe's **one** headingless chunk is 137, p.108, and it dies on the token floor | ⛔ **must be 0** |
| ⭐ **tabs in kept `content` / `raw_content`** | **0 / 0** | ⭐ ✅ **0 / 0**, and `heading_path` **0** too — A6 | `predicted` — the untab block clears **147,910** | ⛔ **must be 0.** §0.1 |
| `page_count` (`max(page_to)` over **kept**) | ⭐ **262** | ✅ **262** — exact, and `max(page_to)` over kept reads 262 independently | `predicted` | ⚠️ **not 335.** §4.4 |
| **embedding coverage** | **340/340** | ✅ **340/340**, dims **1024** | `predicted` | ⛔ **100%**, all 1024 dims |
| `kb.ingest_log` rows | **2** | ✅ **2** — `clean\|warn` and `promote\|info` | `predicted` | ⛔ **must be 2** |
| ⚠️ `detail->'repairs'` entries | **2**, applied **2 / 2** | ✅ **2**, applied **2 / 2** — ⚠️ symmetric; see A2c | `predicted` §2.4 | ⛔ must be present — ⚠️ **a symmetric ledger; §4.1 A2c states what it cannot prove** |
| `repairs_applied` total | **4** | ✅ **4** — exact | `predicted` | ⛔ non-zero |
| `is_current` versions, whole corpus | **5** | ✅ **5** | `predicted` | exactly 5 |
| `kb.chunks` total | **1,864** | ✅ **1,864** — exact | `predicted` | |
| ⭐ **corpus share, Malt** | ⭐ **18.2%** | ✅ **18.2%** (340/1,864) — ⭐ **and no document is above 25%** | `predicted` | ⭐ **under 25% — and it takes the whole corpus under it.** §4.5 |
| *How to Brew* untouched | **447 \| 447 \| 0 \| 0** | ✅ **447 \| 447 \| 0 \| 0** | `measured` §1.1 | ⛔ **must be unchanged** |
| Water untouched | **382 \| 382 \| 0 \| 0** | ✅ **382 \| 382 \| 0 \| 0** | `measured` §1.1 | ⛔ **must be unchanged** |
| Yeast untouched | **463 \| 463 \| 0 \| 0** | ✅ **463 \| 463 \| 0 \| 0** | `measured` §1.1 | ⛔ **must be unchanged** |
| style cards untouched | **232** | ✅ **232** | `measured` §1.1 | ⛔ unchanged |
| `file_sha256` | `c85d388f…169579` | ✅ `c85d388f8ff8…` on the one `is_current` version | `measured` §1.1 | ⛔ must match, or the file is not the one probed |

**The drop ledger — `predicted` before the run:**

| Reason | Predicted | Measured | Pages predicted | From |
|---|---|---|---|---|
| ⭐ `front-matter heading` | ⭐ **62** | ✅ **62** (pp.271–334) | 271–334 | §5.3 — the **Index**, under a readable heading. ⚠️ The reason string says *front-matter*; the content is back matter. That is the shared rule's label, not a misclassification |
| `front matter (p1-p24)` | **29** | ✅ **29** (pp.3–23) | 3–23 | §5.2 |
| `chapter References list` | **12** | ✅ **12** (pp.32–220) | 32–220 | §5.4 |
| `source-specific heading` | **8** | ✅ **8** (pp.263–269) | 263–269 | §2.3 — one alternative, `^Bibliography$` |
| `under 30 tokens, no table` | **7** | ✅ **7** (pp.47–254) | 47–254 | §5.5 |
| `empty raw_text` · `page-number-only` | **0 · 0** | ✅ **absent** | — | §5.1 |
| **total** | **118** | ✅ **118** | | |

⭐ **`measured` — five reasons, five exact counts, five exact page bands, nothing
unauthorised.** ⚠️ **Note what did *not* need explaining this time:** book 2's `front matter`
band read pp.2–20 against a rule of p1–p21 because no chunk happened to *begin* on p.21. Malt's
reads **pp.3–23** against a rule of **p1–p24** for the same reason — chunk 28 begins on p.23 and
ends on p.24 — ⭐ **and this plan predicted the band as 3–23, not 3–24.**

⚠️ **A ledger that does not read 62/29/12/8/7 means something upstream changed.** The three
most likely mistakes, each visible in one glance:

| Symptom | Cause |
|---|---|
| `front matter` reads **28**, not 29 | `front_matter_max_page` left at Yeast's **21** or set to 23 — chunk 28 (`Footnotes`, pp.23–24) survives |
| `source-specific heading` reads **0** | `extra_drop_regex` left empty — the **Bibliography is then in the corpus**, and `page_count` catches it independently (it would read **270**, not 262) |
| `front-matter heading` reads **0** | the profile is not `book` |

**Runtime — `predicted`, and built from book 2's *measured* run, not from book 1's inherited
estimate:**

| Stage | Predicted | Measured | Basis |
|---|---|---|---|
| read + hash + dedup | < 1 s | ✅ | Yeast `measured` 0.03 s |
| ⭐ **Docling conversion** | ⭐ **~165 s** — 11 poll cycles | ⭐ ✅ **~165 s** — the run's dominant cost, as predicted | ⭐ `measured` **160.85 s** in §5's probe — same service, same ten fields, same file |
| poll loop overhead | ≤ 15 s | | `Wait 15s` granularity |
| clean + repairs | < 1 s | | Yeast `measured` 0.03 s |
| insert 340 chunks | < 1 s | | one `jsonb_to_recordset` statement |
| **embed** | ⭐ **11 batches, ~12 s** | ✅ **absorbed in the 3 min total** | ⭐ **derived**: Yeast `measured` 15 batches / 15.3 s; `batchSize` **32** (`measured` §1.1), 340 / 32 → 11 |
| promote + assert + log | < 1 s | | |
| **total** | ⭐ **~3 min** | ⭐ ✅ **3 min 02 s** — 11:03:53 → 11:06:55 UTC | `predicted` |

⭐ **The runtime estimate was right, and that is worth stating because the last two were not.**
Book 1 carried *"~5–9 min to embed"* and book 2 measured **16 s**; book 2 replaced the estimate
with one derived from an execution record, and book 3 predicted **~3 min** and `measured`
**3 min 02 s**. ⭐ **An estimate derived from a measured run held; an estimate inherited between
plans did not.** That is the same lesson as standing rule 5, one layer out.

⛔ **Past ~6 minutes, suspect a hang.** That is roughly twice the predicted run and it replaces
the *"past 20 minutes"* figure that books 0a–1 carried — a threshold three times too loose to
catch anything. ⚠️ **The first suspect is `keep_alive: -1` missing from `Ollama embed`**, which
would show as embed time going from **12 s to minutes**. §3's reset makes starting over cheap.

⛔ **Do not "fix" the poll loop by shortening `Wait 15s`.** ⭐ **165 of the predicted ~185
seconds are Docling**, and that is a property of the file.

### 4.1 Tier A — pipeline (SQL, deterministic)

⭐ **All seven blocks were run 2026-08-19 against the live stack.** Results are recorded inline
under each command, labelled `measured`. ⭐ **A1, A2, A2b, A2c, A4, A5, A6 and A7 all pass
exactly — no block returned a column that missed its predicted value.** ⛔ **A3 was *not
observed*.**

**A1 · rows by document, embedding coverage, null pages and headings** — plan 06 §7.6's query,
unmodified. ⛔ **It must include a row for every existing document** — that is the check that
this ingest touched nothing else:

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select d.slug, count(*) chunks, count(e.chunk_id) embedded, count(*) filter (where c.page_from is null) no_page, count(*) filter (where c.heading_path is null or cardinality(c.heading_path)=0) no_heading, min(c.token_count) min_tok, percentile_disc(0.5) within group (order by c.token_count) median_tok, max(c.token_count) max_tok from kb.chunks c join kb.document_versions v on v.id=c.version_id and v.is_current join kb.documents d on d.id=v.document_id left join kb.chunk_embeddings e on e.chunk_id=c.id and e.model='bge-m3' group by d.slug order by 1;"
```

**Predicted — five rows:**

| slug | chunks | embedded | no_page | no_heading | min | median | max |
|---|---|---|---|---|---|---|---|
| `bjcp-2021-beer-styles` | **232** | **232** | 232 — by design, §00b | **0** | — | — | — |
| `how-to-brew-palmer` | **447** | **447** | **0** | **0** | 30 | 291 | 524 |
| ⭐ `malt-practical-guide` | **340** | **340** | ⛔ **0** | ⛔ **0** | **44** | **339** | **517** |
| `water-comprehensive-guide` | **382** | **382** | **0** | **0** | 31 | 342 | 513 |
| `yeast-practical-guide` | **463** | **463** | **0** | **0** | 30 | 313 | 512 |

⛔ **The three existing book rows are as important as the Malt row.** `447 | 447 | 0 | 0`,
`382 | 382 | 0 | 0`, `463 | 463 | 0 | 0`, and `232` for the style cards.

⭐ **`measured` 2026-08-19 — five rows, and every predicted cell hit:**

| slug | chunks | embedded | no_page | no_heading | min | median | max | |
|---|---|---|---|---|---|---|---|---|
| `bjcp-2021-beer-styles` | **232** | **232** | 232 — by design | **0** | — | — | — | ✅ unchanged |
| `how-to-brew-palmer` | **447** | **447** | **0** | **0** | 30 | 291 | 524 | ⛔ ✅ **untouched** |
| ⭐ `malt-practical-guide` | **340** | **340** | ⛔ **0** | ⛔ **0** | **44** | **339** | **517** | ✅ **exact** |
| `water-comprehensive-guide` | **382** | **382** | **0** | **0** | 31 | 342 | 513 | ⛔ ✅ **untouched** |
| `yeast-practical-guide` | **463** | **463** | **0** | **0** | 30 | 313 | 512 | ⛔ ✅ **untouched** |

⛔ **The ingest touched nothing that was already there.** All three prior books are unchanged in
every column, including their min/median/max.

**A2 · the log has 2 rows, with a drop ledger *and* a repair ledger:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select stage, level, message, jsonb_array_length(detail->'drops') drops, jsonb_array_length(detail->'repairs') repairs, detail->'stats'->>'repairs_applied' applied from kb.ingest_log where version_id=(select id from kb.document_versions where file_sha256='c85d388f8ff828313d2d364625072530d7e4b00c8b0a0235903af22a76169579') order by id;"
```

**Predicted:** a `clean | warn` row reading *cleaning kept 340 of 458 chunks, 118 dropped*, with
`drops` **118**, `repairs` **2** and `applied` **4**; and a `promote | info` row.

⭐ **`measured` — exactly that:**

| stage | level | message | drops | repairs | applied |
|---|---|---|---|---|---|
| `clean` | `warn` | *cleaning kept 340 of 458 chunks, 118 dropped* | **118** | **2** | **4** |
| `promote` | `info` | *version 6 promoted: 340 chunks, 0 missing embeddings* | — | — | — |

⚠️ **The promote message reads *"version 6"* and `kb.document_versions.version` for Malt is
**1** — `measured`.** It interpolates the version **row id**, not the version number, and has
done since book 0a. Known, nothing reads it, ⛔ **not fixed here** (§0.4), handed to book 4.

**A2b · the drop ledger by reason — §4.0's table, read back from the database:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select d->>'reason' reason, count(*) n, min((d->>'page_from')::int) p_from, max((d->>'page_from')::int) p_to from kb.ingest_log, jsonb_array_elements(detail->'drops') d where stage='clean' and version_id=(select id from kb.document_versions where file_sha256='c85d388f8ff828313d2d364625072530d7e4b00c8b0a0235903af22a76169579') group by 1 order by 2 desc;"
```

**Predicted exactly:** `front-matter heading` **62** (pp.271–334) · `front matter (p1-p24)`
**29** (pp.3–23) · `chapter References list` **12** (pp.32–220) · `source-specific heading`
**8** (pp.263–269) · `under 30 tokens, no table` **7** (pp.47–254).
**Anything else is a rule firing that this plan did not authorise.**

⭐ **`measured` — five reasons, five exact counts, nothing unauthorised:**

| reason | n | p_from | p_to | |
|---|---|---|---|---|
| `front-matter heading` | **62** | 271 | 334 | ✅ exact |
| `front matter (p1-p24)` | **29** | 3 | 23 | ✅ exact, and the predicted band exactly |
| `chapter References list` | **12** | 32 | 220 | ✅ exact |
| `source-specific heading` | **8** | 263 | 269 | ✅ exact |
| `under 30 tokens, no table` | **7** | 47 | 254 | ✅ exact |

⭐ **All three `book`-profile rules fired, on one book, for the first time in the phase** — 62
by `dropHeading`, 12 by `dropReferences`, 7 by `minTokens` — with `extra_drop_regex` doing 8
and the page rule 29. §2.3's contrast with book 2 is confirmed by measurement.

**A2c · ⭐ read the repair ledger — and read it for what it cannot prove:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select r->>'find' find, r->>'replace' replace, (r->>'applied')::int applied from kb.ingest_log, jsonb_array_elements(detail->'repairs') r where stage='clean' and version_id=(select id from kb.document_versions where file_sha256='c85d388f8ff828313d2d364625072530d7e4b00c8b0a0235903af22a76169579') order by 3 desc;"
```

**Predicted: 2 rows — `212220 → 212-220` applied **2**, and `5565 → 55-65` applied **2**,
summing to 4.**

⛔ **State the bound before the result, because it is the whole value of running this.**
[`02-yeast.md`](02-yeast.md) §4.1 A2c proved `$5` is *stored* rather than *reconstructed* by
the **asymmetry** of its four counts — 54 / 17 / 10 / 6, none equal, none a multiple of a
common factor. ⭐ **Malt's ledger is `2 / 2`, and a symmetric ledger cannot make that argument.**
A passing A2c here proves the key is written and the array has the right **length and
contents**; it does **not** independently re-prove that the counts are per-pair.

⚠️ **That is a fact about this book, not a gap in the test, and it must not be repaired by
inventing a third pair.** Standing rule 6 — argue it, do not tune it. **What A2c *does* add:
`$5` has now produced a row on two consecutive books rather than one**, and the `find` strings
are book-specific, so a reconstruction from `stats` alone remains impossible.

⭐ **`measured` — two rows, exactly as predicted:**

| find | replace | applied | predicted |
|---|---|---|---|
| `212220` | `212-220` | **2** | 2 ✅ |
| `5565` | `55-65` | **2** | 2 ✅ |
| | **total** | **4** | 4 ✅ |

⛔ **Read with the bound stated above, not ticked.** Two pairs, two identical counts: this
confirms the array is stored with the right length and the right book-specific `find` strings,
and it is **weaker evidence than book 2's** `54 / 17 / 10 / 6`. ⭐ **The honest summary across
the two books: `$5` has now been observed storing a ledger twice, and the *asymmetry* argument
rests entirely on book 2.** A third book with distinct per-pair counts would settle it; Malt
could not, and saying so is the point.

**A3 · ⭐ idempotency — the dedup short-circuit, observed live, as the LAST step of the session**

⛔ **This is the point of doing it last.** Book 1's attempt failed only because it was launched
**86 s before the first run committed its version row**. **Wait for the `promote` log row to
exist (A2), then run this.**

Fingerprint, run `ingest-malt` a **second** time, fingerprint again:

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select md5(string_agg(content_sha256, ',' order by chunk_index)), count(*) from kb.chunks;"
```

⛔ **Expected: an identical hash both times, count `1864`, and the run ends at `Already
ingested` in seconds** — the path is `Read file for hashing → Crypto → Dedup lookup →
Is new file? → Already ingested`, five nodes, no HTTP, no Docling.

⛔ **If it instead runs a full Docling conversion, that is a defect and it must be recorded.**
A broken dedup branch does not error; it mints a second version, and a book would land twice
with no error anywhere.

⛔ **A3 cannot be checked retroactively. If it is not run, it is recorded as *not observed*,
never as passed.**

⛔ **`measured` result: NOT OBSERVED.** `measured` from n8n's execution table 2026-08-19:
`hpW9P0n7fxXY9KdF` has exactly **one** execution — id **248**, 11:03:53 → 11:06:55 — and
`ingestMalt00001A` has **none**. There is no second run to have short-circuited.

⭐ **The difference from books 1 and 2 is that the obstacle is now gone, not merely named.**
Book 1's attempt failed because it raced the first run's commit; book 2 never attempted it.
⭐ **Book 3's `promote` row exists** (A2, log id 10), so the conditions A3 needs are satisfied
and the check is a single click away. ⛔ **It has still not been run, and it is recorded as *not
observed*.** §4.6.

**A4 · corpus totals:**

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select 'chunks', count(*)::text from kb.chunks union all select 'gaps', count(*)::text from kb.chunks c left join kb.chunk_embeddings e on e.chunk_id=c.id and e.model='bge-m3' where e.chunk_id is null union all select 'current', count(*)::text from kb.document_versions where is_current union all select 'dims', (select string_agg(distinct vector_dims(embedding)::text,',') from kb.chunk_embeddings);"
```

**Predicted:** `chunks 1864` · `gaps 0` · `current 5` · `dims 1024`. ⛔ **One value for `dims`** —
two means a second model got in and every comparison downstream is garbage.

⭐ **`measured`: `chunks 1864` · `gaps 0` · `current 5` · `dims 1024` — all four exact, and
`dims` is a single value.** ✅

**A5 · ⭐ the two repairs are in the stored text — and this check counts *occurrences*, not rows**

⭐ **Deliberately written with `sum()` rather than `count(*) filter`.**
[`02-yeast.md`](02-yeast.md) §4.1 A5 missed because it stated a **site** count and asserted a
**row** count. Counting occurrences on both fields makes the check reconcile with A2c's
`applied` arithmetically:

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select sum((length(c.content)-length(replace(c.content,'212-220','')))/7) r1_content, sum((length(c.raw_content)-length(replace(c.raw_content,'212-220','')))/7) r1_raw, sum((length(c.content)-length(replace(c.content,'55-65','')))/5) r2_content, sum((length(c.raw_content)-length(replace(c.raw_content,'55-65','')))/5) r2_raw, count(*) filter (where position('212220' in c.content)>0 or position('212220' in c.raw_content)>0) unrepaired_1, count(*) filter (where position('5565' in c.content)>0 or position('5565' in c.raw_content)>0) unrepaired_2 from kb.chunks c join kb.document_versions v on v.id=c.version_id and v.is_current join kb.documents d on d.id=v.document_id where d.slug='malt-practical-guide';"
```

**Predicted: `1 | 1 | 1 | 1 | 0 | 0`** — and `r1_content + r1_raw + r2_content + r2_raw = 4`,
⛔ **which must equal A2c's `applied` total.** The last two columns are the gate: a non-zero
`unrepaired_*` means a repair did not fire on a chunk that survived cleaning.

⭐ **`measured`: `1 | 1 | 1 | 1 | 0 | 0` — all six exact, and the four occurrence counts sum to
`4`, reconciling with A2c's `applied` total exactly.**

⭐ **This is the check book 2 got wrong, written the way book 2's record said to write it.**
[`02-yeast.md`](02-yeast.md) §4.1 A5 stated a **site** count and asserted a **row** count, and
missed by 3. Book 3 counted occurrences with `sum()` over both fields instead of rows with
`count(*) filter`, and it reconciles arithmetically with the ledger. ⭐ **A lesson from a
previous book's failure, applied and confirmed.**

**A6 · ⭐ the untab block did its job, and there is no glyph residue to find**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select d.slug, count(*) filter (where c.content like '%'||chr(9)||'%') content_tab, count(*) filter (where c.raw_content like '%'||chr(9)||'%') raw_tab, count(*) filter (where array_to_string(c.heading_path,' ') like '%'||chr(9)||'%') head_tab, count(*) filter (where c.content ~ '/g[0-9]+') body_glyph, count(*) filter (where array_to_string(c.heading_path,' ') ~ '/g[0-9]+') head_glyph, count(*) filter (where array_to_string(c.heading_path,' ') ~* '(index|references|bibliography|contents)') plain_backmatter from kb.chunks c join kb.document_versions v on v.id=c.version_id and v.is_current join kb.documents d on d.id=v.document_id group by 1 order by 1;"
```

**Predicted: 0 in every column, for all five documents.**

⚠️ ⭐ **`measured`: 0 in every column for Malt, and the one non-zero row in the table is
*Yeast*'s known glyph residue** — which is the correct result, not a failure:

| slug | content_tab | raw_tab | head_tab | body_glyph | head_glyph | plain_backmatter |
|---|---|---|---|---|---|---|
| `bjcp-2021-beer-styles` | 0 | 0 | 0 | 0 | 0 | 0 |
| `how-to-brew-palmer` | 0 | 0 | 0 | 0 | 0 | 0 |
| ⭐ `malt-practical-guide` | ⭐ **0** | ⭐ **0** | ⭐ **0** | **0** | **0** | ⛔ **0** |
| `water-comprehensive-guide` | 0 | 0 | 0 | 0 | 0 | 0 |
| `yeast-practical-guide` | 0 | 0 | 0 | ⚠️ **15** | ⚠️ **11** | 0 |

⭐ **`head_tab` = 0 is the measurement §0.1 exists for.** 296 of Malt's 458 probe chunks carried
a tab **inside a heading** and **not one survived** — book 1's untab block cleared 147,910 tab
characters and left the corpus with zero. ⭐ **It is now confirmed on two files: provably a
no-op on one (book 2), provably load-bearing on another (book 3).**

⛔ **`plain_backmatter` = 0 confirms §2.3**: no Index, References, Bibliography or Contents
chunk survived under a readable heading. ⚠️ **Yeast's 15/11 is its documented residue**
([`02-yeast.md`](02-yeast.md) §4.1 A6) and is unchanged by this ingest — a fourth
untouched-state check nobody asked for.

⭐ **Two columns carry the weight here.** `head_tab` = **0** is the check on §0.1 — 296 probe
chunks had a tab in a heading and none may survive. `plain_backmatter` = **0** is the check on
§2.3 — a non-zero value means an Index, References or Bibliography chunk survived under a
readable heading. ⚠️ **`plain_backmatter` is a stricter pattern than book 2's** because it adds
`bibliography`, which is the alternative this book's `extra_drop_regex` exists for.

**A7 · ⭐ the epigraph headings are the size §2.5 says, and no larger:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select count(*) filter (where c.heading_path[1] like '-%') epigraph_head, count(*) filter (where array_to_string(c.heading_path,' ') = 'Footnotes') footnotes, count(*) filter (where c.token_count > 512) over_512, max(c.page_to) page_count from kb.chunks c join kb.document_versions v on v.id=c.version_id and v.is_current join kb.documents d on d.id=v.document_id where d.slug='malt-practical-guide';"
```

**Predicted: `5 | 7 | 1 | 262`.**

⭐ **`measured`: `5 | 7 | 1 | 262` — all four exact.**

⭐ **The `footnotes` column is the one worth pausing on**, because it is the only number in
this plan that scores a *judgement* rather than a rule. §2.3 kept the `Footnotes` chunks against
the obvious reading that they are apparatus like `References`. The count landing at exactly 7
confirms the arithmetic (9 exist, 1 dies on the page rule, 1 on the token floor); ⚠️ **whether
keeping them was *right* is answered by §4.2, and the answer there is "not yet visible" — no
`Footnotes` chunk reached any top-6.**

⚠️ **`footnotes` reads 7, not 8** — `measured` by simulation: 9 `Footnotes` chunks exist, chunk
28 dies on the page rule and chunk 214 dies on the token floor. ⭐ **This number is the one
§2.3's keep-the-footnotes decision is scored on**, and §4.2 watches whether any of the seven
ever retrieves.

### 4.2 Tier B — retrieval (`scripts/ask.sh`, deterministic)

**The before-baseline is [`02-yeast.md`](02-yeast.md) §4.2's post-Yeast table**, `measured`
2026-08-19 at 1,524 chunks. ⛔ **Not the post-Water one in [`01-water.md`](01-water.md) §6.**

⭐ **Eleven questions, not ten** — the 5 standing + **5** positive controls + 1 style question.
The eleventh is **Q9**, the procedure-shaped control [`02-yeast.md`](02-yeast.md)'s closing
section asked for. Run with `scripts/ask.sh`, unfiltered, 6/40/50 defaults untouched.

> ### ⭐ The verdict: **keep — and by a wider margin than the rule asks for.**
> `measured` 2026-08-19 against the live **1,864**-chunk corpus, `scripts/ask.sh`, unfiltered,
> 6/40/50 defaults untouched.
>
> - ⭐ **All five prior rank-1 chunks are still at rank 1**, not merely inside the top 3.
> - ⭐ **Q1–Q5 are byte-identical to the post-Yeast baseline** — same six chunks, same order,
>   on every one of the five.
> - ⭐ **Malt returns 0 of 6 on all five.** §4.2a's *"Malt moves nothing"* is correct in full.
> - ⭐ **All five positive controls reach rank 1.**
> - ⭐ **Layer 2 fires on nothing**, for the third consecutive run.
> - ⛔ **One predicted defect appeared, exactly where predicted** — §4.2d.

**The keep/roll-back rule, unchanged and restated:**

| Outcome | Action |
|---|---|
| prior rank-1 chunk still top 3 on all five | **keep**, log the shift |
| falls out of top 6 on **one** | keep, log as a defect |
| falls out of top 6 on **two or more** | ⛔ **reset** (§3) |

⭐ **`measured`: prior rank-1 still at rank 1 on all five → keep.** Zero logged defects in the
keep rule's terms, no reset.

#### ⭐ 4.2a Predicted movement — written **before** the run, per question

⭐ **The overall prediction is the strongest one in this plan and the easiest to falsify:
*Malt moves nothing.*** It is the first source in the phase that is topically disjoint from
**all five** standing questions — diacetyl, mash pH, hop timing, pitching rate and
acetaldehyde. Yeast owned two of the five by construction; Malt owns none.

| # | Question | Prior rank-1 (`measured`, post-Yeast) | ⭐ **Prediction** | Malt's candidate chunks |
|---|---|---|---|---|
| **Q1** | *diacetyl rest temperature and timing for lagers* | yeast p.133 `Diacetyl Rest`; how-to-brew p.98 at rank 3 | **no change, 0 of 6 from Malt** | — |
| **Q2** | *how mash pH affects conversion and how to adjust it* | how-to-brew p.39 `4.2 Water Chemistry Adjustment…`; 3 htb / 3 water | ⚠️ **the only one with a candidate. `predicted` 0–1 of 6, and rank 1 does not move** | `Acidulated Malt` p.144 · `Quantifying Wort Fermentability` pp.40–41 |
| **Q3** | *when to add hops for bittering vs aroma* | how-to-brew p.41 `Bittering`/`Flavoring`/`Finishing`, ranks 1–3 | **no change, 0 of 6. ⛔ This is the gate; it must hold** | — |
| **Q4** | *pitching rate and rehydrating dry yeast* | how-to-brew p.205; 4 htb / 2 yeast | **no change, 0 of 6** | — |
| **Q5** | *my beer tastes of green apple, what causes acetaldehyde and how do I fix it* | how-to-brew p.212 `Acetaldehyde`; 5 htb / 1 yeast | **no change, 0 of 6** | ⚠️ `Off-Flavors` p.88 is about **kilning** off-flavours, not fermentation ones |

##### ⭐ Scored — `measured` 2026-08-19, prediction by prediction

| # | Prior rank-1 (post-Yeast) | ⭐ **New rank-1 `measured`** | Malt of 6 | Top-6 vs baseline | Prediction |
|---|---|---|---|---|---|
| **Q1** | yeast p.133 `Diacetyl Rest` | **yeast p.133** — unchanged | ⭐ **0** | ✅ **byte-identical** (133, 135, 98, 132, 99, 98) | ✅ **correct** |
| **Q2** | how-to-brew p.39 `4.2 Water Chemistry Adjustment…` | **how-to-brew p.39** — unchanged | ⭐ **0** | ✅ **byte-identical** (39, 140, 75, 134, 63, 74) | ✅ **correct — and at the safe end of the 0–1 range** |
| **Q3** | how-to-brew p.41 `Bittering` | **how-to-brew p.41 `Bittering`** — unchanged | ⭐ **0** | ✅ **byte-identical** (41, 41, 41, 76, 40, 77) | ✅ **correct — the gate holds** |
| **Q4** | how-to-brew p.205 | **how-to-brew p.205** — unchanged | ⭐ **0** | ✅ **byte-identical** (205, 167, 62, 168, 63, 92) | ✅ **correct** |
| **Q5** | how-to-brew p.212 `Acetaldehyde` | **how-to-brew p.212** — unchanged | ⭐ **0** | ✅ **byte-identical** (212, 213, 215, 290, 218, 85) | ✅ **correct** |

⭐ **340 new chunks displaced nothing, anywhere, on any of the five.** That is a stronger
result than book 2's and it was the prediction: *Malt* is the first source in the phase
topically disjoint from every standing question, so the correct outcome was **no movement at
all**, and it is what happened.

⚠️ **State plainly what this does and does not show.** It shows the ingest is inert with
respect to the existing regression set — which is exactly what a well-scoped source should be.
⛔ **It does not show Malt retrieves well**; that is §4.2b's job, and it is where the evidence
is.

⭐ **And it retires a worry rather than confirming one.** [`02-yeast.md`](02-yeast.md)'s closing
item 5 warned *"do not predict Malt takes Q2 on depth alone — check whether one Malt chunk
answers both halves."* `measured`: Malt takes **0 of 6** on Q2, and the phrase *"mash pH"*
occurs **0** times in the book. **The warning was right and the plan acted on it.**

⛔ **If Q1, Q3, Q4 or Q5 moves at all, stop and look at the drop ledger before blaming
retrieval.** Malt has no hop, yeast or fermentation-fault content; a Malt chunk in those top-6s
would mean something was chunked or embedded wrong.

⭐ **`measured`, "mash pH" occurs as a phrase **0** times in the whole book** (§5.1), which is
why Q2's prediction is *0–1* rather than *contested*. ⭐ **And [`02-yeast.md`](02-yeast.md)'s
closing item 5 is applied rather than ignored: do not predict Malt takes Q2 on depth alone.**
Q2 is a compound question — *how it affects conversion* **and** *how to adjust it* — and
Palmer's rank-1 chunk answers both in one place. Malt answers neither half directly.

#### ⭐ 4.2b The five positive controls — each states its document, its rank, and its expected chunk

| # | Question | Must reach | Expected chunk (`measured` present in §5) |
|---|---|---|---|
| **Q6** | *"what is diastatic power and how does it affect starch conversion"* | `malt-practical-guide` in the **top 3** | `Diastatic Power in Malts` 2 chunks p.131 · `Enzyme Action` 3 chunks pp.132–133 · `Carbohydrate Enzymes` p.199 |
| **Q7** | *"how are caramel and crystal malts made"* | `malt-practical-guide` in the **top 3** | `Making Specialty Malts` 4 chunks pp.99–102 · `Caramel Malts` 2 chunks · `Caramel/Crystal Malts` p.140 |
| **Q8** | *"what does the Kolbach index or S/T ratio tell a brewer about malt modification"* | `malt-practical-guide` in the **top 3** | `Protein Modification` p.198 · `Malt Analysis` 3 chunks pp.194–195 · `Carbohydrate Modification` p.197. ⭐ `measured`: `Kolbach` **5** occurrences, `S/T` **21** |
| ⭐ **Q9** | ⭐ **procedure-shaped** — *"how do I steep and germinate barley to malt it at home"* | `malt-practical-guide` in the **top 3** | ⭐ `The Malting Phases` **7 chunks pp.257–259** · `By George de Piro` 4 chunks pp.254–255 · `Steeping` pp.77–80 · `Germination` pp.80–83 |
| **Q10** | *"how finely should malt be crushed and what does the husk do"* | `malt-practical-guide` in the **top 3** | `Dry Milling` **5 chunks pp.221–223** · `Wet Milling` p.226 · `Grist Analysis` pp.229–230 |

⭐ **Q9 is the one book 2's record asked for and the one to read hardest.** Its whole purpose is
to make §0.2's token-floor decision judgeable: **if a procedure question retrieves Malt's
procedure chunks at rank 1, then losing 7 sentence tails cost nothing that a reader would have
seen.** ⚠️ **It is also the honest form of a test book 2 could not run** — Yeast's 11 severed
`Materials` lists were never probed by a procedure question, so its evidence was recorded as
weak on purpose.

⭐ **Q6 is deliberately a question *How to Brew* can also answer** (Palmer covers diastatic
power in the grains chapter). **A top-6 carrying both books is the correct result**, and
[`02-yeast.md`](02-yeast.md) §4.2a records that book 2's equivalent nomination was **wrong** —
its shared control turned out to be Q7/Q8, not the one the plan named. So this is a
prediction that has already failed once and is worth making again.

##### ⭐ The 5 positive controls — `measured`: all five at **rank 1**

| # | Question | Required | ⭐ **Measured** | Malt of 6 | |
|---|---|---|---|---|---|
| **Q6** | diastatic power | malt, top 3 | ⭐ **rank 1** — `Diastatic Power in Malts` p.131, and **rank 2** is the same heading's second chunk | **3** | ✅ |
| **Q7** | caramel / crystal malts | malt, top 3 | ⭐ **rank 1** — `Caramel/Crystal Malts` p.140; `Making Specialty Malts` p.99 at 2, `Caramel Malts` p.97 at 3 | **4** | ✅ |
| **Q8** | Kolbach / S/T ratio | malt, top 3 | ⭐ **rank 1** — `Protein Modification` p.198; `Certificates of Analysis…` p.203 at 2 | **4** | ✅ |
| ⭐ **Q9** | ⭐ **home malting procedure** | malt, top 3 | ⭐ **rank 1** — `By George de Piro` p.254, **Appendix D** | ⭐ **6** | ✅ |
| **Q10** | crush and husk | malt, top 3 | ⭐ **rank 1** — `Dry Milling` p.221 | **5** | ✅ |

⭐ **Three books running, every positive control lands at rank 1 rather than merely inside the
top 3** — Water 4 of 4, Yeast 4 of 4, Malt 5 of 5. [`02-yeast.md`](02-yeast.md) §4.2a said this
was *"now the pattern to expect at book 3, and a control that only reaches rank 2 or 3 there
should be looked at rather than ticked."* **None did.**

⭐ **Q6's shared-control prediction is correct, and it is the one book 2 got wrong.** `measured`:
Q6 splits **3 Malt / 3 How to Brew** — `Diastatic Power in Malts` p.131 ×2 and `-Bill Simpson`
p.202 against `Barley Malt Defined` pp.112–113 and `14.6 Manipulating the Starch Conversion
Rest` p.134. ⭐ **The 20-page answer and the 335-page answer in one context window, on the
question the plan nominated in advance** — which is §2.6's keep-both rule producing exactly
what it was argued to produce. Q10 splits 5/1 the same way at lower amplitude.

⭐ **Q9 is the control this plan was written to add, and its result decides §0.2.** `measured`:
**6 of 6 from Malt**, rank 1 `By George de Piro` p.254, and the top-6 spans Appendix D
(pp.254, 258) *and* the body's own malting chapters (pp.71, 76, 76, 80). ⛔ **The seven chunks
the token floor deleted were sentence tails, and a procedure question does not miss them.**
Book 2 accepted the same loss on weak evidence because none of its ten questions asked a
procedure question; **book 3 asked one and the loss is invisible to it.** §4.4.

#### ⭐ 4.2c Layer 2 — the retrieval-share check, with ownership declared **before** the run

**The eleventh question, which Malt does not own:**

```bash
./scripts/ask.sh "what should an Irish Stout taste like"
```

⛔ **Flag any question where ≥ 3 of 6 results come from one document that does not own it.**

⭐ **[`02-yeast.md`](02-yeast.md) §4.2b's finding was that *"does not own it"* is the only
unmeasured term in the rule** — five of book 2's ten questions were resolved by adjudicating
ownership as *shared* **after** seeing the results. **So book 3 declares it first.** The table
below is a prediction and can be wrong:

| # | Question | ⭐ **Declared owner, before the run** | Firing condition |
|---|---|---|---|
| Q1 | diacetyl rest | **shared — `yeast-practical-guide` + `how-to-brew-palmer`** | ≥ 3 of 6 from water, malt or styles |
| Q2 | mash pH | **shared — `how-to-brew-palmer` + `water-comprehensive-guide`** | ≥ 3 of 6 from yeast, malt or styles |
| Q3 | hop timing | **`how-to-brew-palmer`, sole** | ≥ 3 of 6 from anything else |
| Q4 | pitching rate | **shared — `how-to-brew-palmer` + `yeast-practical-guide`** | ≥ 3 of 6 from water, malt or styles |
| Q5 | acetaldehyde | **`how-to-brew-palmer`, sole** | ≥ 3 of 6 from anything else |
| Q6 | diastatic power | ⭐ **shared — `malt-practical-guide` + `how-to-brew-palmer`** | ≥ 3 of 6 from water, yeast or styles |
| Q7 | caramel/crystal malts | ⭐ **`malt-practical-guide`, sole** | ≥ 3 of 6 from anything else |
| Q8 | Kolbach / S/T ratio | ⭐ **`malt-practical-guide`, sole** | ≥ 3 of 6 from anything else |
| Q9 | home malting procedure | ⭐ **`malt-practical-guide`, sole** | ≥ 3 of 6 from anything else |
| Q10 | crush and husk | ⭐ **shared — `malt-practical-guide` + `how-to-brew-palmer`** | ≥ 3 of 6 from water, yeast or styles |
| Q11 | Irish Stout | **`bjcp-2021-beer-styles`** | ⭐ **≥ 3 of 6 from Malt is the headline failure this check exists for** |

⭐ **Record the result for all eleven even if it fires nothing.** It has fired on nothing twice.
A recorded null is what makes the first real firing legible.

⭐ **Concentration is measured on the (`heading_path`, `page_from`) *pair*, not on the heading
string.** ⛔ **This is not a preference — it is [`02-yeast.md`](02-yeast.md) §4.2c's measured
conclusion.** Heading-only read **4 of 6** on Yeast's flocculation question and would have
justified deleting three genuinely different answers; the pair metric read **1** there and
**4** on Water's Q8, which is the case that actually mattered.

⛔ **Do not build `PARTITION BY d.id, c.heading_path`.** For each of the 11 questions record:

| Record | Threshold |
|---|---|
| max results sharing one **(`heading_path`, `page_from`) pair** | ⭐ **≥ 4 of 6 on one pair is the finding**, and it is a design question at its second sighting |
| max results sharing one `heading_path` (any page) | context only — Yeast hit 4 here on four different pages and it was **not** a defect |
| max results sharing one **page** (any heading) | context only — Q3's 3-of-6 on p.41 is the documented expected result |

⚠️ **Malt's most likely candidate is Q7** — `Making Specialty Malts` is 4 chunks over pp.99–102,
four different pages, which is the *Flocculation* shape rather than the *reverse-osmosis* shape.
⭐ **Predicting that is the point**: if Q7 reads 4 on the heading and ≤ 2 on the pair, the pair
metric has separated the two cases on a second document and can be adopted.

##### ⭐ `measured` 2026-08-19 — all 11 questions, and Layer 2 fires on **nothing**

| # | Question | htb | water | yeast | ⭐ malt | styles | ⭐ Declared owner | Fires? |
|---|---|---|---|---|---|---|---|---|
| Q1 | diacetyl rest | 3 | 0 | **3** | ⭐ **0** | 0 | shared yeast+htb | ✅ no |
| Q2 | mash pH | 3 | **3** | 0 | ⭐ **0** | 0 | shared htb+water | ✅ no |
| Q3 | hop timing | **6** | 0 | 0 | ⭐ **0** | 0 | htb sole | ✅ no |
| Q4 | pitching rate | **4** | 0 | 2 | ⭐ **0** | 0 | shared htb+yeast | ✅ no |
| Q5 | acetaldehyde | **5** | 0 | 1 | ⭐ **0** | 0 | htb sole | ✅ no |
| Q6 | diastatic power | **3** | 0 | 0 | **3** | 0 | ⭐ shared malt+htb | ✅ no |
| Q7 | caramel/crystal | 0 | 0 | 0 | **4** | 2 | malt sole | ✅ no |
| **Q8** | Kolbach / S/T | 0 | ⚠️ **2** | 0 | **4** | 0 | malt sole | ✅ no |
| Q9 | home malting | 0 | 0 | 0 | ⭐ **6** | 0 | malt sole | ✅ no |
| Q10 | crush and husk | 1 | 0 | 0 | **5** | 0 | shared malt+htb | ✅ no |
| **Q11** | **Irish Stout** | 1 | 0 | 0 | ⭐ **0** | **5** | styles | ✅ **no** |

⛔ **Layer 2 does not fire. Layer 3 is not built.** ⭐ **Third consecutive recorded null**, now
at five documents and 1,864 chunks.

⭐ **The ownership declaration was made before the run and it did not need a single
adjudication.** [`02-yeast.md`](02-yeast.md) §4.2b's complaint was that five of book 2's ten
questions were resolved by calling ownership *shared* **after** seeing the results, making the
rule *"not yet a measurement."* `measured` at book 3: **no question required a post-hoc
ownership call.** Every ≥ 3-of-6 in the table above belongs to a document the plan named as an
owner **in advance** — Q3's 6 to Palmer, Q6's 3/3 to the pair the plan nominated, Q7/Q8/Q9's to
Malt, Q11's 5 to the style cards. ⭐ **The rule is now a measurement rather than a judgement,
and that is book 3's contribution to it.**

⭐ **Q11 is again the number that matters, and it is again a null — but for a new reason.**
Water crossed 25% and took 0 of 6; Yeast crossed 30% and took 0 of 6; ⭐ **Malt takes 0 of 6
without ever crossing the line at all**, and its top-6 is byte-identical to the post-Yeast
baseline. §4.5.

⚠️ **The closest thing to a firing is Q8, and it is 2 of 6, not 3.** *Water* takes ranks 4 and 5
(`Refinement of RA` p.73, `Malt Color` p.77) on a malt-modification question it does not own.
⛔ **Below threshold, so it is not a firing** — recorded because `Malt Color` in a water book is
precisely the near-miss shape worth watching, and because book 2's equivalent near-miss (Q8,
3 of 6) had to be argued away.

#### 4.2d ⭐ The epigraph headings — the carried defect, watched

⚠️ **Water's `-J. Palmer` retrieved at rank 4 on two questions** and was recorded as a known
cost. ⭐ **Malt has five chunks of the same shape** (§2.5), and unlike Yeast's `Palmer, John`
they are **not dropped**, because they are real chapter openers.

| Check | Expected |
|---|---|
| a chunk whose `heading_path` starts with `-` in any of the 66 returned rows | ⚠️ **plausible on Q8** — `-Bill Simpson` p.202 is the malt-COA chunk and Q8 asks about COA values. `predicted`: **it appears, and that is a correct answer under an unreadable citation** |
| a `Footnotes` chunk in any top-6 | `predicted` **0** — but §2.3 kept them deliberately, so **record it either way** |
| the over-512 chunk (Appendix A's malt table) in any top-6 | `predicted` **plausible on Q7** |

⭐ **If a `-Bill Simpson` chunk retrieves, that is the third document showing the defect, and
the fix stops being cosmetic.** ⛔ **It is still not fixed in this book** — repairing
`heading_path` requires rebuilding `content` (plan 06 §4's standing warning), which is a
shared-code change. **Record it; hand it to book 4.**

##### ⛔ ⭐ `measured` 2026-08-19 — the prediction is confirmed, on **three** questions

| Check | ⭐ `measured` |
|---|---|
| ⛔ **an epigraph heading in the 66 returned rows** | ⛔ **yes, three times** — `-Bill Simpson` p.202 at **rank 3 on Q8** and **rank 6 on Q6**; `-William Littell Tizard, The Theory and Practice of Brewing Illustrated` p.221 at **rank 4 on Q10** |
| a `Footnotes` chunk in any top-6 | ✅ **none** — `predicted` 0, and 0 it is. ⚠️ §2.3's keep decision is therefore **unvalidated in either direction**, not vindicated |
| the over-512 chunk (Appendix A) in any top-6 | ✅ **none** — `predicted` *"plausible on Q7"*; it did not appear |

⛔ **This is the finding book 3 was told to watch for, and it came out the bad way.** §4.2d
predicted *"plausible on Q8 — `-Bill Simpson` p.202 is the malt-COA chunk and Q8 asks about COA
values; `predicted`: it appears, and that is a correct answer under an unreadable citation."*
`measured`: **it appears at rank 3**, and the prediction understated it — it also reaches Q6,
and a *second* epigraph chunk reaches Q10.

⭐ **What that changes, stated as a decision and not a shrug.** The defect has now been observed
on **three documents** — Water's `-J. Palmer` (rank 4, twice), and Malt's two — and for the
first time it is **retrieving on a question the source owns**, i.e. in the answers a user would
actually receive. ⛔ **It is no longer cosmetic.** Every one of the three hits is a *correct*
passage rendered under a citation that names a person who did not write it:

> `[malt-practical-guide p.202] -Bill Simpson` — a passage by **John Mallett** about reading a
> malt certificate of analysis, attributed in the citation line to the author of the chapter's
> epigraph.

⚠️ **Still not fixed here, and the reason is unchanged**: repairing `heading_path` without
rebuilding `content` is plan 06 §4's named failure, so it is a shared-code change and book 3's
verdict is mapper-only. ⭐ **Book 4 is already editing the cleaning node for `ba_manual`, and
this is the run to fix it in.** §4.6 hands it over with the three measured sites attached.

##### ⭐ 4.2e Concentration on the (`heading_path`, `page_from`) pair — `measured` for all 11

| # | max on one **(heading, page)** pair | max on one `heading_path` | max on one **page** |
|---|---|---|---|
| Q1 | **2** — how-to-brew p.98 `10.4 Yeast Starters…` | 2 | 2 |
| Q2 | 1 | 2 — `Refinement of RA` (pp.74, 75) | 1 |
| Q3 | 1 | 1 | ⚠️ **3** — p.41, three distinct headings, the documented expected result |
| Q4 | 1 | 2 — `Working With Dry Yeast` (pp.167, 168) | 1 |
| Q5 | 1 | 1 | 1 |
| Q6 | **2** — malt p.131 `Diastatic Power in Malts` | 2 | 2 |
| Q7 | 1 | 1 | 1 |
| Q8 | 1 | 1 | 1 |
| Q9 | 1 | 1 | 2 — p.76, two distinct headings |
| Q10 | 1 | 2 — `Dry Milling` (pp.221, 223) | 2 |
| Q11 | 1 | 1 | n/a — cards have no page |

⭐ **Maximum concentration on one (heading, page) pair across 11 questions: 2.** The threshold
was **≥ 4**. ⛔ **Water's Q8 shape has now failed to reproduce on two consecutive books** —
Yeast's max was 2, Malt's is 2, against Water's 4.

⭐ **And the metric earned its keep by *not* firing where the old one would have.** The
heading-only count reaches 2 on four questions here and never 4, so on this book the two metrics
happen to agree — ⚠️ **which is a weaker validation than book 2's, and worth saying.** Book 2's
case was decisive because the two metrics **disagreed** (4 vs 1) and the pair metric was right.
Book 3 adds a second document on which the pair metric is **stable and low**, and no case where
it separates them. ⛔ **So the recommendation is unchanged and its evidence is unchanged: do not
build `PARTITION BY d.id, c.heading_path`.** The pattern it would fix has been seen once, on one
question, on one book, and has not recurred in 21 questions since.

### 4.3 Tier C — agent

⛔ **Not runnable, and this is a decision rather than a skip.** There is no chat agent and no
search tool: **WF4 and `tool-search-brewing-knowledge` are both unbuilt** (README §1.3 items 6
and 7). ⭐ **Re-verified rather than carried, `measured` 2026-08-19:** `n8n list:workflow`
returns **five** workflows and **none of them is an agent, and none is a tool.** Running an
agent test against no agent is impossible, not omitted.

⭐ **It has a date: README §4.2 schedules the agent as book 4.5** — after book 4, before book 5.
**So this section is a deposit, not a deferral**, and book 3's deposit is the five questions
below.

| Type | Question | Pass condition |
|---|---|---|
| new coverage | *"What is diastatic power and why does a high-adjunct grist need it?"* | answers with numbers from Malt, **names the source**, every `[S…]` resolves |
| ⛔ **refusal still holds** | *"How much Citra do I have?"* | *"I don't have a tool for that yet"* — ⛔ **the one hard fail, re-run in every plan** |
| citation integrity | any malt question | no `[S…]` the tool did not return |
| ⭐ **citation legibility** | *"What does a malt certificate of analysis actually tell me?"* | ⭐ **checks §4.2d directly** — if the answer cites `-Bill Simpson`, the epigraph-heading defect has reached the user, which is the evidence book 4 needs to justify fixing it |
| ⭐ **numeric honesty** | *"What temperature should I hold barley at during germination if I malt at home?"* | ⭐ says **55-65°F**, not `5565°F` — the end-to-end proof that §2.4's repairs reached the model, not just the database |

**`scripts/stress/tier1_routing.py` is not run for this source** (§2.7).

### 4.4 The documented misses — argued, not tuned

⭐ Standing rule 6.

**1 · p25 is 160 tokens, below §11's 200–450 band — and this is now three books out of four.**
`measured` on the probe. The **median (339) and p75 (482) are comfortably inside**; the low
quartile is pulled down by the appendices and the short definitional sections of the
malt-family chapters.

⭐ **The trend is the argument, not the number.** `measured` across the corpus: *How to Brew*
p25 **179**, Water **198**, Yeast **173**, Malt **160** — ⛔ **four books, and the band's lower
bound is met by none of them.** [`02-yeast.md`](02-yeast.md) §4.4 said *"three books missing a
band the same way is an argument about the band"* and named book 4 as the place to revisit it.
⭐ **Book 3 is the fourth data point and it strengthens the case rather than settling it here**:
§11's 200–450 band was set from one book, and it now describes **zero** of four. ⛔ **Raising
`chunking_max_tokens` does not fix a low p25** — it makes long chunks longer and leaves short
ones alone. **No action, and none taken. Book 4 revises the criterion or drops it.**

**2 · ⭐ 7 chunks lost to the token floor — and the pattern book 2 predicted did not recur.**
§0.2 has the argument in full. In one line: **all 7 are sentence tails, 0 are severed
prerequisites**, so **merge-forward is not built**, and the fix book 2 named turns out to
address a different problem from the one book 3 has.

| Option | Verdict |
|---|---|
| Lower `minTokens` to 20 | ⛔ **no.** It lives in the shared `book` profile; changing it rewrites *How to Brew*'s ledger and breaks the 447-chunk fixture the phase rests on |
| Add a per-book `min_tokens` field | ⛔ **no** — an engine change for a fix that is the wrong shape. A 15-token chunk reading *"Reprinted with permission from Zymurgy."* is not worth retrieving whatever the floor is |
| **Merge-forward** (book 2's proposal) | ⛔ **not built, and the reason is measured: it would fix 0 of Malt's 7** |
| **Merge-backward** | ⚠️ **the runner-up.** It would fix 4 of 7. ⛔ **Rejected here** — engine code landing with a new book is standing rule 2's second variable, and the recovered text is a trailing clause of a passage the reader already has |
| ✅ **Accept the loss at book 3** | ✅ **recommended, and taken** |

⭐ **What makes this judgeable rather than asserted: §4.2b's Q9.** Book 2 accepted the same loss
with weak evidence because none of its ten questions asked a procedure question. **Q9 asks one.**

**3 · `page_count` will read 262, not 335.** Not a miss, a definition: the field is
`max(page_to)` over **kept** chunks, and pp.263–335 are the Bibliography and the Index.
⛔ **A `page_count` of 270 means the Bibliography survived** (`extra_drop_regex` empty);
⛔ **335 means the Index survived** (wrong profile).

**4 · ⚠️ One chunk over 512 tokens.** Chunk 353, p.234, 517 tokens — a page of Appendix A's malt
table. Water carried one at 513. ⛔ **Not a gate failure**: the gate is *under-30 must be 0*,
and 517 is ≪ bge-m3's 8,192 window, so nothing truncates. Recorded because §4.0 asserts it.

### 4.5 Corpus share — ⭐ and Malt is the book that takes the whole corpus back under the line

| | `predicted` | ⭐ **`measured` 2026-08-19** |
|---|---|---|
| Malt chunks | **340** | ✅ **340** |
| Corpus after | **1,864** (1,524 + 340) | ✅ **1,864** |
| ⭐ **Malt's share** | ⭐ **18.2%** — ⛔ **does not cross README §3.3's 25% signal** | ⭐ ✅ **18.2%** (340 / 1,864) |
| How to Brew · Yeast · Water · styles after | ⭐ **24.0% · 24.8% · 20.5% · 12.4%** | ✅ **24.0% · 24.8% · 20.5% · 12.4%** |

⭐ **`predicted`: after book 3, *no document in the corpus is above 25%*.** Books 1 and 2 each
crossed the line and each returned **0 of 6** on the style question — a proxy that fired twice
and proxied for nothing. **Book 3 is the run where the proxy stops firing at all**, because a
fifth document was added, which is precisely the mechanism §4.5 of book 2 described: *"three of
the four documents sit at or above the 25% line, and that is a fact about having four
documents, not about any of them being over-represented."*

⛔ **That is an argument for reading the proxy differently, not for tuning it** (standing rule
6). The measurement that matters is **retrieval** share (§4.2c), and it is the one to record.

⭐ **Malt is also the least densely chunked book in the corpus by a wide margin** — `measured`
**340 kept chunks for 335 pages = 1.02 per page**, against *Yeast* 1.42, *Water* 1.40 and
*How to Brew* 1.80. ⚠️ **README §4.3 projected ~600 for Malt.** That is wrong by 76%, and the
reason is measured: **118 of 458 raw chunks are dropped, 62 of them the Index alone** — Malt has
the largest back matter of any source in the phase. §4.6 corrects the table.

⭐ **`measured` 2026-08-19 — and book 3 turns a two-book result into a three-book one from the
*other* direction.** Books 1 and 2 each **crossed** the 25% line and each returned **0 of 6** on
the style question: the proxy fired, the thing it proxies for did not happen. ⭐ **Book 3 does
not cross it, returns 0 of 6 on the style question anyway, and takes the whole corpus back
under the line.**

⛔ **So the proxy has now been informative zero times out of three.** It fired twice on correct
behaviour, and on the run where it stayed silent retrieval behaved exactly as it did when it was
firing. ⚠️ **That is an argument about the proxy, not a reason to delete it** — standing rule 6 —
and the case it was really written for is still ahead at **book 5**, where BA 2026 and the BJCP
Study Guide are *not* topically disjoint from what is already in the corpus. ⭐ **Recorded so
book 5 can weigh it: corpus share has predicted retrieval share three times and been wrong
three times.**

### 4.6 Exit — book 3 is done when

- [✅] §1.2 item 1 — the orphan **deleted** and the engine re-exported at **26 nodes**
  - ⭐ **done 2026-08-19 10:58:46 UTC, in the UI**, five minutes before the run. `measured`:
    **26 nodes live and 26 tracked**, no `Clean + normalise1` in either, and
    `Clean + normalise` byte-identical at 8,229 characters. ⭐ **Flagged at book 1, flagged
    again at book 2, closed at book 3** — and it took a UI action because the n8n CLI has no
    node-level edit
- [⛔] §1.2 item 2 — **A3 observed live** after the `promote` row exists
  - ⛔ **not observed.** `measured`: `hpW9P0n7fxXY9KdF` has exactly **one** execution (248).
    ⭐ **Unlike books 1 and 2 the obstacle is gone** — the `promote` row exists (A2), so the
    check is a single click away. It is recorded as *not observed*, never as passed. §4.1 A3
- [✅] `ingest-malt` exists, 2 nodes, Wait-for-completion ON, all **13** mapper fields filled,
      `front_matter_max_page = 24`, `extra_drop_regex = ^Bibliography$`, `text_repairs` from
      §2.4, ⭐ **exported and committed BEFORE its first run** (standing rule 4, broken at
      book 1 and again at book 2)
  - ⭐ **done 2026-08-19, and this is the first book where the rule was kept.** `ingest-malt.json`
    is n8n's own export, verified field by field (§2.1), committed before any execution existed
- [✅] the run's `stats` read **458 raw → 340 kept, 118 dropped, 4 repairs applied**, and the
      drop ledger reads **62 / 29 / 12 / 8 / 7** by reason
  - ⭐ **all nine numbers exact**, and the five page bands exact too. §4.1 A2/A2b
- [✅] A2c returns **2 repair rows, `2 / 2`** — ⚠️ **read with §4.1 A2c's stated bound, not
      ticked**
  - ✅ **2 / 2 exact.** ⚠️ **And the bound is recorded rather than skipped:** a symmetric ledger
    cannot distinguish *stored* from *reconstructed*, so book 2's asymmetry argument is not
    re-proved here. §4.1 A2c
- [✅] A1 reads **340 | 340 | 0 | 0** for Malt, and ⛔ **447 | 447 | 0 | 0**,
      **382 | 382 | 0 | 0**, **463 | 463 | 0 | 0**, **232** unchanged for the rest
  - ⭐ **all five rows exact**, including min/median/max on all four books
- [✅] A5's four occurrence counts sum to **4** and reconcile with A2c; ⛔ **0 unrepaired**
  - ⭐ **`1 | 1 | 1 | 1 | 0 | 0`, summing to 4.** Written with `sum()` rather than
    `count(*) filter` **because book 2's equivalent check missed on exactly that** — a lesson
    from a previous book applied and confirmed
- [✅] ⭐ A6 reads **0 tabs in every column, for all five documents** — including `head_tab`,
      which is §0.1's real gate — and **0 glyph, 0 plain_backmatter**
  - ⭐ **0 in every column for Malt.** 296 probe chunks carried a tab **inside a heading** and
    none survived; 147,910 tabs cleared. ⚠️ Yeast's 15/11 glyph residue is unchanged — a fourth
    untouched-state check
- [✅] A7 reads **5 | 7 | 1 | 262**
  - ⭐ **all four exact**
- [⛔] A3 stops at `Already ingested` in seconds with an identical fingerprint at **1,864**.
      ⛔ **If not run, recorded as *not observed*, not as passed**
  - ⛔ **not observed** — see above
- [✅] the 5 standing questions pass the keep rule, and §4.2a's *"Malt moves nothing"*
      prediction is scored — including Q3, the declared gate
  - ⭐ **keep, and stronger than the rule asks:** all five prior rank-1 chunks are still at
    **rank 1**, and all five top-6s are **byte-identical** to the post-Yeast baseline
  - ⭐ **the prediction is correct in full — 0 of 6 from Malt on every one of the five**
- [✅] all 5 positive controls reach the top 3 in `malt-practical-guide`. ⚠️ **Two books running,
      every control landed at rank 1; a control reaching only rank 2 or 3 is looked at, not
      ticked**
  - ⭐ **all five at rank 1.** Three books running now: Water 4/4, Yeast 4/4, Malt 5/5
  - ⭐ **Q6's shared-control prediction is correct** (3 Malt / 3 *How to Brew*) — the one book 2
    got wrong
- [✅] ⭐ **Q9's result is read as the verdict on §0.2** — the procedure control is why the
      token-floor decision is judgeable this time
  - ⭐ **6 of 6 from Malt, rank 1 `By George de Piro` p.254 — Appendix D, the section the token
    floor cut into.** The 7 lost chunks are invisible to a question built to find them.
    **§0.2's decision stands and is now tested rather than argued**
- [✅] the Layer-2 retrieval share is recorded for all **11** questions, **including a null**,
      and ⛔ **scored against §4.2c's ownership table declared before the run** — the whole
      point is that the declaration can be wrong
  - ⭐ **Layer 2 fires on nothing — third consecutive null**, at five documents and 1,864 chunks
  - ⭐ **the declaration needed zero post-hoc adjudications**, which is what book 2 asked book 3
    to fix. The rule is now a measurement rather than a judgement
- [✅] §4.2c's **(`heading_path`, `page_from`) pair** concentration is recorded for all 11
  - ⭐ **max 2, against a threshold of 4.** Water's Q8 shape has now failed to reproduce twice.
    ⚠️ Recorded honestly: on this book the pair and heading metrics **agree**, so this is a
    weaker validation of the metric than book 2's, where they disagreed
- [⚠️] §4.2d recorded: did a `-` epigraph heading retrieve? did a `Footnotes` chunk?
  - ⛔ **yes — three times.** `-Bill Simpson` at **rank 3 on Q8** and **rank 6 on Q6**;
    `-William Littell Tizard…` at **rank 4 on Q10**. ⭐ **The predicted defect appeared, and the
    prediction understated it.** Three documents now show it and it is **no longer cosmetic**
  - ✅ **no `Footnotes` chunk retrieved** — §2.3's keep decision is unvalidated in either
    direction, not vindicated
- [✅] corpus share recorded at **18.2%** and argued, not tuned (§4.5)
  - ⭐ **and no document in the corpus is above 25% for the first time since book 0b**
- [✅] `ingest-malt.json` committed with the measured numbers in the message
  - ⚠️ **committed twice, and the second commit matters:** the tracked JSON was replaced with
    the workflow that **actually executed**. §2.1a
- [✅] README §9's book 3 row ticked — Plan, Probed, Built, Tier A, Tier B; Tier C stays
      `⬜ n/a — no WF4`. ⭐ **README §4.3's projected-corpus table corrected** — it carried
      **~600** for Malt against this plan's **340**, and the end state moves ~2,965 → **~2,705**
- [✅] ⛔ **§5 is not edited after the run.** It is the pre-run evidence and its value is that it
      was written before the outcome was known. New measurements go in §4, labelled `measured`
  - ⭐ **§5 is byte-identical to the version committed in `a9bcefb`, before the run**
- [✅] ⭐ **§0's verdict recorded either way** — *"book 3 was mapper-only"* is the evidence D30
      was designed to produce, and it only counts if it is written down first
  - ⭐ **it held.** The only artefact book 3 added to n8n is a 2-node launcher; `Clean +
    normalise` is byte-identical to the one book 1 left behind
- [✅] ⭐ **§0.1's and §0.2's two closed questions recorded as closed**
  - ⭐ **§0.1 confirmed twice over:** 0 glyph runs in the stored corpus, and 0 tabs from a source
    carrying 147,910 — the decoder stays unbuilt and the untab edit is confirmed **necessary**
  - ⭐ **§0.2 confirmed by Q9** — merge-forward is not built, and the evidence against it is
    stronger after the run than before it
- [⛔] ⭐ **NEW — the duplicate `ingest-malt` workflow is deleted**
  - ⛔ **not done, handed over.** Two workflows are named `ingest-malt`; the unused one
    (`ingestMalt00001A`) never ran and there is no `delete:workflow` in the n8n CLI. §2.1a

**Handed to whoever next touches `scripts/`:** ⛔ **`hyphen-probe.sh` has a false-negative
bug.** Its regex requires a trailing ASCII `-`; Docling normalises en dashes to hyphens *after*
extraction, so an en-dashed range that wraps is invisible to the probe and fused by Docling.
§2.4 and §5.6 have the two sites this cost. **The fix is one character class: `[-‐–—]$`.**

---

## §5 — Evidence: what was measured before the plan was written

⭐ **Standing rule 1, and the section every number above is derived from.** Everything below was
`measured` on **2026-08-19** by submitting the file to the **live** Docling service. No number
in this plan is extrapolated from *Water*, *Yeast* or *How to Brew*.

### 5.0 The submission — the engine's ten form fields, byte for byte

**File:** `shared/rag-files/pending/malt-a-practical-guide-from-field-to-brewhouse-978-1-938469-12-1-1-938469-12-7-978-1-938469-16-9.pdf`
— 6,113,751 bytes, **335 pages** (`pdfinfo`).
**Container path:** `/data/shared/rag-files/pending/malt-a-practical-guide-from-field-to-brewhouse-978-1-938469-12-1-1-938469-12-7-978-1-938469-16-9.pdf`
**SHA-256:** `c85d388f8ff828313d2d364625072530d7e4b00c8b0a0235903af22a76169579` — **`measured`.**
This is the value `Crypto` must produce, the dedup key `kb.document_versions.file_sha256` will
carry, and what §3 is keyed on.

The ten fields below were **diffed against the live `Docling submit` node**, not copied from
plan 02:

```bash
curl -s -X POST http://localhost:5001/v1/chunk/hybrid/file/async \
  -F "files=@shared/rag-files/pending/malt-a-practical-guide-from-field-to-brewhouse-978-1-938469-12-1-1-938469-12-7-978-1-938469-16-9.pdf" \
  -F "convert_from_formats=pdf" \
  -F "convert_image_export_mode=referenced" \
  -F "convert_do_ocr=false" \
  -F "convert_pdf_backend=dlparse_v4" \
  -F "convert_table_mode=accurate" \
  -F "chunking_tokenizer=BAAI/bge-m3" \
  -F "chunking_max_tokens=512" \
  -F "chunking_include_raw_text=true" \
  -F "chunking_use_markdown_tables=true"
```

**`documents[0].status`: `success`. `processing_time`: 160.85 s — `measured`.**

### 5.1 The headline numbers

| Measure | **Measured** | Reads as |
|---|---|---|
| raw chunk count | **458** | vs Yeast 526 raw / 463 kept, Water 440 / 382, *How to Brew* 483 / 447 |
| pages covered | **3 – 335** | pp.1–2 carry no extractable text |
| **chunks per page** | **1.38** | prose. Yeast 1.62, Water 1.61, *How to Brew* 1.95. ⭐ **the lowest of the four** |
| median `num_tokens` | **306** | ✅ inside §11's 200–450 band |
| **p25 / p75** | **171 / 475** | ⚠️ **p25 is below the band** — §4.4's first documented miss |
| max / min | **517 / 6** | |
| count **over 512** | **1** | chunk 353, p.234 — Appendix A's malt table; **survives cleaning** |
| count **under 30** | **9** | §5.5 lists all nine; **7 survive to the token floor** |
| ⭐ **chunks with no `page_from`** | **0** | ⛔ the must-be-0 gate, hit exactly. Citations are safe |
| ⚠️ **chunks with no headings** | **1** | ⭐ chunk 137, p.108, a quote fragment — **dropped by the token floor**, so `missing_heading` after cleaning is **0** |
| distinct headings | **216** | §5.3 |
| heading depth | ⭐ **1, on all 458** | `heading_path` is never nested in this book — no `A > B` citations |
| chunks containing a table | ⭐ **27 (5.9%)** | ⛔ **README §4 calls this book *"table-dense"*. It is the least table-dense of the three:** Yeast 42 (8.0%), of which 25 survive here against Yeast's 34 |
| ⭐ **glyph runs `/gNNN`** | ⭐ **0**, in text **and** headings, in all 458 chunks | ⭐ **§0.1's prediction confirmed** — against Yeast's 42 chunks and 16 distinct runs |
| ⛔ **tab characters** | ⛔ ⭐ **147,910** — `text` 73,955 · `raw_text` 73,158 · **headings 797** | ⛔ **against Water's 75,154.** ⭐ **More tabs than spaces** (46,119 spaces in `text`). **457 of 458** chunks carry one; **296 of 458** carry one **inside a heading** |
| chars per token | **4.081** raw / **4.268** kept | vs Yeast's 4.289/4.211 and Water's 4.191. The size predictions are calibrated, not guessed |

**What this table decides:** the file needs no format-specific handling and no new profile —
but it is the file that **proves book 1's untab edit was necessary rather than merely safe**.
0 missing pages, 0 glyph damage, 1 headingless chunk that the token floor removes, 1 over-band
chunk that is a table.

### 5.2 The front-matter page range — ⭐ `front_matter_max_page = 24`

⛔ **A fact about Mallett's PDF, not about books.** *How to Brew* uses **6**, Water **18**,
Yeast **21**. Every chunk with `page_to <= 30` was read:

| Chunks | Pages | Heading | What it is | Keep? |
|---|---|---|---|---|
| 0, 1 | 3–5 | `John Mallett` | title page + publisher block + copyright + CIP + credits | ⛔ drop |
| 2 | 5 | `Malthouse Tour-Floor Malting in Great Britain` | ⚠️ **a TOC line promoted to a heading**, not the tour itself (which is pp.71–74) | ⛔ drop |
| 3–9 | 6–8 | `Table of Contents`, `6. Malt Chemistry`, `7. Malt Family Descriptions`, … | the TOC, chunked under its own entries | ⛔ drop |
| 10, 11 | 10–11 | `Acknowledgments` | front matter — ⚠️ also matched by `dropHeading`, but the page rule fires first | ⛔ drop |
| 12–17 | 12–16 | `Foreword` | signed by a fellow brewer; why the book exists | ⛔ drop |
| 18–23 | 17–20 | `Introduction` | ⚠️ *"As I first thought about how to structure this book…"* — about the book | ⛔ drop |
| 24–27 | 21–23 | `About This Book` | a chapter-by-chapter roadmap | ⛔ drop |
| **28** | **23–24** | ⚠️ **`Footnotes`** | ⭐ **the Introduction's footnote**, about the author's Siebel training | ⛔ **drop — and this is what decides 24 over 23** |
| **29** | **25–26** | **`Harry Harlan-the 'Indiana Jones' of Barley`** | ⭐ **chapter 1, first real content** | ✅ **keep** |

**`front_matter_max_page = 24`.** The rule is `pageTo <= FRONT_MAX`; chunk 28 spans pp.23–24
and is caught, chunk 29 spans pp.25–26 and is not. **Drops exactly 29 chunks and not one more**
— verified by simulation (§5.7).

⚠️ **Why 24 and not 23.** At 23, chunk 28 survives: an anecdotal footnote to a section that was
itself dropped, kept under the heading `Footnotes` with no parent. ⭐ `measured`: **no kept
chunk begins on p.24**, so 24 costs nothing and removes an orphan. ⛔ **It is not 25**, because
chunk 29 spans pp.25–26 and a cut at 25 would not catch it anyway — a page rule cannot separate
them, which is why the boundary sits at the last page of the front matter rather than the first
page of chapter 1.

⚠️ **Unlike Yeast, nothing real is stranded inside the front matter.** Yeast kept
`Fermentor vs. Fermenter` (p.23) and two author bios; Malt's pp.3–24 are entirely apparatus.
**That is why one page rule does the whole job here and Yeast needed a heading alternative.**

### 5.3 ⭐ The headings — 216 distinct, all of them readable

**Top 20 by frequency.** ⭐ **Every one is plain text.** Tabs are shown normalised, as the
untab pass will leave them.

| n | Heading | pp. | Verdict |
|---|---|---|---|
| **62** | `Index` | 271–334 | ⛔ **dropped by `dropHeading`** — ⭐ the shared rule, working, for the first time since Water |
| **18** | `Commercially Available Malts in the US as of 2014` | 232–248 | ✅ **kept — Appendix A**, the malt spec table. §2.3 |
| **12** | `References` | 32–220 | ⛔ **dropped by `dropReferences`** — per-chapter citation lists |
| 9 | `Footnotes` | 23–220 | ✅ **7 kept** — substantive explanatory notes. §2.3, §5.4 |
| 8 | `Harry Harlan-the 'Indiana Jones' of Barley` | 25–32 | ✅ chapter 1 |
| **8** | `Bibliography` | 263–269 | ⛔ **dropped by `extra_drop_regex`** — the one alternative. §2.3 |
| 7 | `The Malting Phases` | 257–259 | ✅ ⭐ **Appendix D — §4.2b's Q9 target** |
| 6 | `Foreword` | 12–15 | ⛔ dropped by page |
| 6 | `Introduction` | 17 | ⛔ dropped by page |
| 6 | `Formulating a Grain Bill` | 35–39 | ✅ core content |
| 6 | `Early 19th Century` | 57 | ✅ |
| 5 | `Germination` | 80–83 | ✅ |
| 5 | `Dry Milling` | 221–223 | ✅ ⚠️ §4.2b's Q10 target |
| 4 | `About This Book` | 21 | ⛔ dropped by page |
| 4 | `Jen Talley, Auburn Alehouse (Auburn, CA)` | 46–47 | ✅ a brewer sidebar |
| 4 | `Conclusion` | 50–262 | ✅ ⚠️ four chapters end with one; the heading says nothing |
| 4 | `A Time for Malting` | 61–65 | ✅ |
| 4 | `Making Specialty Malts` | 99–102 | ✅ ⚠️ §4.2c's predicted concentration site |
| 4 | `Barley Immigration` | 181 | ✅ |
| 4 | `Grist Analysis` | 229–230 | ✅ |

⭐ **The measurement that decides §0.1 and §2.3, stated as a number:**

| Rule | Headings it matches in *Malt* | in *Yeast* (book 2) |
|---|---|---|
| `dropHeading` — `^(Contents\|Index\|Glossary\|Acknowledg\|Copyright\|About the Author)` | ⭐ **2 distinct** — `Index` (62 chunks) and `Acknowledgments` (2, already caught by page) | ⛔ **0 of 262** |
| `dropReferences` — `^references$` on the trimmed heading | ⭐ **1 distinct** — `References` (12 chunks) | ⛔ **0** |

⚠️ **Note what `dropHeading` does *not* catch:** `Table of Contents` (p.6) — the pattern is
`^Contents`, anchored, and the heading begins with *Table*. ⭐ **It does not matter here**
because the page rule takes it, but it is a live trap for any future source whose TOC sits
outside the front-matter page band.

⭐ **Five headings are epigraph attributions**, `measured` — the chapter-opening pull quote's
byline becomes the heading for the chapter's first prose:

| Chunks | p. | Heading | What is under it |
|---|---|---|---|
| 65 | 52 | `-Thomas Fuller 1` | *"Humans have been malting grains for thousands of years…"* |
| 147 | 114 | `-Louis Pasteur` | *"The purpose of a barley seed is to create a new barley plant…"* |
| 307, 308 | 202 | `-Bill Simpson` | ⭐ the malt-COA discussion — *"Deciphering the information in a malt COA takes practice."* |
| 337 | 221 | `-William Littell Tizard, The Theory and Practice of Brewing Illustrated` | the milling chapter's opening |

⛔ **All five are kept.** §2.5 argues it; §4.2d watches it.

### 5.4 The back matter — 118 chunks, and the shared rules take 74 of them

⭐ *Malt* has the largest back matter of any source in the phase, and it is the half of the file
the shared rules handle **best** — the opposite of *Yeast*.

| Chunks | pp. | Heading | What it is | Disposition |
|---|---|---|---|---|
| 351–368 | 232–248 | `Commercially Available Malts in the US as of 2014` | Appendix A — maltster × product × °L | ✅ **kept, 18** |
| 369 | 249–250 | `North American Malthouse Capacity by Location` | Appendix B | ✅ kept |
| 370, 371 | 252–253 | `North American Craft Maltsters` | Appendix C | ✅ kept |
| 372–387 | 254–262 | `By George de Piro`, `Moisture Content Determinations`, `Equation 1 :`, `Equation 2 :`, `The Malting Phases`, `Acrospire Removal`, `Conclusion` | ⭐ **Appendix D — home malting, a complete procedure** | ✅ **kept, 16** (1 to the token floor) |
| 388–395 | 263–270 | `Bibliography` | the bibliography | ⛔ `extra_drop_regex` |
| 396–457 | 271–335 | `Index` | the Index | ⛔ `dropHeading` |

**And the in-body apparatus, which is not back matter at all:**

| Heading | Chunks | pp. | Disposition |
|---|---|---|---|
| `References` | 12 | 32–220 | ⛔ `dropReferences` — numbered citation lists at chapter ends |
| ⭐ `Footnotes` | 9 | 23–220 | ⭐ **8 survive the reference rule; 7 survive everything.** `measured`, they are **definitions**, not citations: *"The property of being easily crumbled or pulverized. Fully modified malt should be friable…"* (p.50), *"The scutellum is a thin shield…"* (p.134), *"The basal end is where the kernel was attached to the barley plant"* (p.134) |

⭐ **The `Footnotes`/`References` split is the finding that makes §2.3 one alternative instead
of two.** They look like the same thing and are not: `References` is bibliography, `Footnotes`
is glossary. A rule that took both would have deleted seven definitions of terms
(`friable`, `scutellum`, `Zadoks index`, `S/T`) that appear nowhere else in the book.

### 5.5 The nine chunks under 30 tokens — and only seven reach the floor

The profile drops a chunk under 30 tokens **unless it contains a table**. **None of the nine
contains a table.** Two die earlier:

| idx | p. | tok | Heading | `raw_text` | Dies on |
|---|---|---|---|---|---|
| 1 | 5 | 6 | `John Mallett` | `Later Developments` | the **page rule** |
| 117 | 91 | 18 | `References` | `1. Personal conversation at Bell's Eccentric Café, December 7, 2012.` | **`dropReferences`** |
| **58** | **47** | **18** | `Jen Talley, Auburn Alehouse (Auburn, CA)` | `malt.'` | ⭐ **token floor** |
| **110** | **88** | **17** | `Off-Flavors` | `enzymatic potential than their pale brethren.` | ⭐ token floor |
| **137** | **108** | **22** | ⚠️ *(none)* | `- good, mild, soft Water, which is the radix of all moist nourishment.'` | ⭐ **token floor — and it is the book's only headingless chunk** |
| **151** | **116** | **22** | `Carbohydrates` | ` consumes the easily available monosaccharides before spending energy on larger molecules.` | ⭐ token floor |
| **214** | **149** | **22** | `Footnotes` | `* A greater discussion of caramel malt can be found in the Specialty malts chapter.` | ⭐ token floor |
| **344** | **226** | **18** | `Wet Milling` | `lengthy process of the classic multi-step continental mashing regime.` | ⭐ token floor |
| **372** | **254** | **15** | `By George de Piro` | `Reprinted with permission from Zymurgy.` | ⭐ token floor |

⭐ **The evidence for §0.2's decision, `measured` — four of the seven are the tail of the chunk
immediately before them, under the identical heading:**

| idx | p. | tok | Heading | Content |
|---|---|---|---|---|
| 343 | 226 | 511 | `Wet Milling` | *"When considering the goal of proper milling is minimal damage to the husk material while still crushing the endosperm…"* |
| **344** | **226** | **18** | **`Wet Milling`** | ⛔ **dropped** — *"lengthy process of the classic multi-step continental mashing regime."* |
| 345 | 226–228 | 509 | `Steep-Conditioned Wet Milling` | ✅ kept — a **different section** |

⛔ **This is the pairing that kills merge-forward.** Yeast's chunk 301 (`Materials`, 24 tok) was
followed by chunk 302 (`Procedure`, 273 tok) **about the same test** — merging forward produced
one coherent unit. Malt's chunk 344 is followed by a **different section**; merging forward
would splice the tail of *Wet Milling* onto the opening of *Steep-Conditioned Wet Milling*.
**The fix these need is merge-backward, and they need it much less** — the sentence they
complete is the last of a 511-token passage that is kept in full.

The other three: 137 is the tail of a period quotation, 214 is a cross-reference (*"see the
Specialty malts chapter"*), 372 is a reprint-permission line. ⭐ **All three are correct drops
by any reading.**

### 5.6 ⭐ The hyphen probe — standing rule 7, and the draft is a **false negative**

```bash
./scripts/hyphen-probe.sh shared/rag-files/pending/malt-a-practical-guide-from-field-to-brewhouse-978-1-938469-12-1-1-938469-12-7-978-1-938469-16-9.pdf
```

**Output:**

```
0 at-risk site(s)

text_repairs: []
```

⛔ **Checked against the Docling output, and it is wrong.** ⭐ **Two real fusions exist in kept
text**, and the probe's own extraction cannot see them:

| Site | `pdftotext -layout` says | ⭐ **Docling produces** | In a kept chunk? |
|---|---|---|---|
| p.256, `Equation 1 :` | `…heated at 212–` ⏎ `220°F (100–104°C)…` | ⛔ **`212220°F`** — 2 occurrences (`text` + `raw_text`) | ✅ **yes**, chunk 377 |
| p.259, `The Malting Phases` | `…maintained in the range from 55–` ⏎ `65°F (12.8–18.3°C).` | ⛔ **`5565°F`** — 2 occurrences | ✅ **yes**, chunk 382 |

⭐ **Why the probe missed them, in one measurement:**

| | `measured` |
|---|---|
| en dashes in the `pdftotext -layout` output | **643** · em dashes **49** |
| ⭐ en dashes in the **Docling** output | ⭐ **0** · em dashes **0** · ASCII hyphens **5,856** |

**Docling normalises every en and em dash to an ASCII hyphen — and it does so *after* joining
the wrapped line and dropping the dash.** `hyphen-probe.sh` matches `(\S*?[\d.,]+)-$`, an
**ASCII** hyphen, against the `pdftotext` output where the character is still `–`. So the probe
sees a clean file and Docling silently fuses two temperature ranges. ⛔ **This is the first
failure mode of the three that is *silent*** — Water's draft was wrong loudly (79 false sites),
Yeast's was wrong loudly (matched nothing, which aborts the ingest by design), and Malt's is
wrong quietly.

**Three independent sweeps were run before settling on two pairs:**

| Sweep | Result |
|---|---|
| ⭐ **broadened probe** — **any** line ending in `-`, `‐`, `–` or `—` whose next line starts with a digit | ⭐ **11 sites.** Four are word hyphens joined correctly (`mid-20th`, `semi-`, `self-`, `mid-1900s`); **five are in the Bibliography or References**, which this plan drops (`1850–1990`, `317–328`, `102–150`, `3–17–2013`); ⛔ **two are real and in kept text** — the two above |
| the Docling output swept for **surviving** un-joined wraps — digit, hyphen, newline, digit | **0 sites** |
| every **4+ digit run** in the Docling output, read for implausible values | ⭐ **157 distinct, 5 suspicious.** `212220` and `5565` (kept, repaired); `18501990`, `317328`, `102150` (all in dropped chunks). Every other hit is a year, an ISBN (`938469`), a ZIP (`80306`), an LCCN (`2014038768`) or a legitimate quantity (`5000` lb, `3120.0` °L) |

⛔ **A 4-digit sweep alone would not have been enough either** — it cannot see a fusion whose
result is under four digits (`5-`⏎`8` → `58`). The broadened line-wrap sweep is the one that
covers that case, and it is what §4.6 hands forward as the script fix.

### 5.7 The simulation — every §4 number, derived

§2's rules run over the `measured` 458-chunk probe, in the live node's exact order:

| Rule | Motivated by | **Predicted effect on Malt** |
|---|---|---|
| untab (shared, from book 1) | §5.1 — **147,910** tabs | ⭐ **rewrites 457 of 458 chunks and 296 headings.** Not a no-op |
| `text_repairs` | **§2.4** — 2 verified pairs | **drops nothing**; `predicted` **4** field-level replacements |
| `!raw` — empty `raw_text` | hygiene | **0** — `measured`, none are empty |
| `pageTo <= 24` — front matter | **§5.2**, read chunk by chunk | **29** — title/copyright 2, TOC-as-heading 1, TOC 7, acknowledgements 2, foreword 6, introduction 6, about-this-book 4, footnote 1 |
| `dropHeading` | §5.3, all 216 headings read | ⭐ **62** — the Index. **The first source since Water where this rule does real work** |
| `extraRe` — `^Bibliography$` | **§2.3** | **8** |
| `dropReferences` | §5.3, §5.4 | ⭐ **12** — the per-chapter citation lists |
| `tokens < 30 && !hasTable` | §5.5, all nine read | **7** (2 of the 9 die earlier) |
| `^\s*\d{1,3}\s*$` — page-number-only | hygiene | **0** — `measured` |

**`predicted` ledger: 118 dropped, 340 kept, of 458 raw.**

⚠️ **The repair loop runs over *every* chunk, including the ones about to be dropped**, so
`repairs_applied` describes the book rather than the survivors. ⭐ **Here both repair sites
happen to be in kept chunks**, so `applied` **4** and the stored-text occurrence count **4**
coincide — ⛔ **which they did not on Yeast**, and §4.1 A5 is written to reconcile them
explicitly rather than assume they must.

### 5.8 Three real chunks, verbatim

⭐ *"The only way to see what cleaning actually has to do."* **Tabs are shown as `<T>`.**

**(a) The chunk carrying repair 1 — chunk 377, pp.256–257, 290 tokens, heading
`Equation<T>1 :`:**

> `(weight<T>of<T>moist<T>grain-weight<T>of<T>dry<T>grain)<T>/<T>weight<T>of<T>moist<T>grain<T>x<T>100<T>= %<T>moisture<T>content`
> `Using<T>the<T>drying<T>method,<T>a<T>sample<T>is<T>accurately<T>weighed<T>and<T>then<T>placed<T>in an<T>oven<T>on<T>a<T>baking<T>sheet<T>or<T>similar<T>device<T>in<T>a<T>thin<T>layer<T>and<T>heated<T>at<T>`**`212220°F`**`<T>(100-104°C)<T>for<T>three<T>hours…`

⭐ **Three things at once, and they are §0's whole argument:** the tab damage that book 1's
untab block exists for, the fused temperature range the hyphen probe reported as absent, and a
heading that itself contains a tab. **Without the untab block this chunk embeds as
`Equation<T>1 :` and cites as `Malt > Equation	1 :`.**

**(b) A body chunk with no damage but the tabs — chunk 131, p.104, 400 tokens, heading
`Other<T>Processes`:**

> `Indirectly<T>heated<T>kilns<T>are<T>relatively<T>new<T>in<T>the<T>history<T>of<T>malting.<T>Prior<T>to<T>the introduction<T>of<T>cleaner<T>tasting<T>fuels<T>(such<T>as<T>coal<T>or<T>coke),<T>kilned<T>malts<T>had<T>a discernible<T>smoky<T>character… When<T>most<T>beer<T>drinkers think<T>of<T>a<T>smoky<T>beer,<T>they<T>think<T>of<T>Bamberg.`

⭐ **This is what 457 of 458 chunks look like.** No glyphs, no fusions, nothing to repair — and
**every word separated by a tab.** It is the ordinary case, which is why the untab block is
load-bearing rather than exceptional.

**(c) The epigraph-heading chunk — chunk 307, pp.202–203, 511 tokens, heading
`-Bill<T>Simpson`:**

> `Deciphering<T>the<T>information<T>in<T>a<T>malt<T>COA<T>takes<T>practice.<T>Much<T>of<T>the<T>insight into<T>how<T>malt<T>will<T>perform<T>in<T>the<T>brewhouse<T>relies<T>on<T>the<T>complex<T>relationships and<T>balances<T>between<T>analytical<T>values…`

⭐ **This one chunk is the argument for §2.5 in a single screen.** Its heading is a person's
name and its body is the best passage in the book on reading a malt certificate of analysis.
⛔ **Dropping it — which a `^-` alternative would do — would delete the answer to §4.2b's Q8.**
It is *Water*'s `-J. Palmer` exactly, and the right response is the same one book 1 took:
record it, watch it retrieve, and fix it in the layer that can rebuild `content`.

---

## What book 3 hands to book 4

⭐ **Revised 2026-08-19, after the run.** The six items below were written before Tier B; items
1, 2 and 4 are now **measured** rather than predicted, and two more were produced by the run
itself.

**Book 4 — the *Draught Beer Quality Manual*, 124 p — is the first source since book 0a whose
verdict is *not* mapper-only:** a new `ba_manual` cleaning profile for a two-column layout.

> ### ⭐ Book 3 in one line
>
> **340 chunks. Thirty numbers `predicted` from a probe and thirty hit exactly** — the best
> result standing rule 1 has produced. Tier B **keep**, with all five prior rank-1 chunks still
> at **rank 1**, all five positive controls at **rank 1**, and Layer 2 firing on **nothing** for
> the third run running. ⭐ **Two open design questions closed by measurement** — the glyph
> decoder and merge-forward — and ⭐ **one standing rule kept for the first time in the phase.**
> ⭐ **And a three-book hygiene debt was finally paid**: the orphaned `Clean + normalise1` node,
> flagged at book 1 and again at book 2, was deleted before the run — the engine is **26 nodes**
> for the first time since the phase started tracking it. ⛔ **Two things are open and neither is
> the ingest:** A3 was never observed, and there are now **two** workflows named `ingest-malt`.

⛔ **What book 4 inherits, stated so it is not rediscovered:**

1. ⭐ **The glyph decoder is closed, and the untab block is confirmed.** §0.1 — two calibre
   books need untab, one `Creo` book needed glyph repairs and no second book reproduced it.
   **The shared-code ledger for the whole phase is one edit, and it was the right one.**
2. ⭐ **Merge-forward is decided against, and the reason is a distinction worth keeping:**
   severed prerequisites (merge-forward) and split tails (merge-backward) are two problems, not
   one. §0.2. **Book 4 reopens it only if it shows severed prerequisites.**
3. ⛔ **`hyphen-probe.sh` has a false-negative bug** — §5.6. **Book 4 is a two-column PDF, where
   line wrapping is denser per page than anywhere in the corpus so far.** ⚠️ **Run the broadened
   sweep, not just the script**, and consider fixing the script in book 4's run, which is
   already touching shared code.
   ⭐ **This is now the phase's only *code* defect that is still open** — §1.2 item 1 closed the
   orphan, so `scripts/` is where the remaining drift lives.
4. ⛔ ⭐ **The epigraph-heading defect retrieved, on three questions — fix it at book 4.**
   `measured` §4.2d: `-Bill Simpson` at **rank 3 on Q8** and **rank 6 on Q6**,
   `-William Littell Tizard…` at **rank 4 on Q10**. ⭐ **This is the condition book 3 set, and it
   was met:** three documents now show it, and for the first time it retrieves on questions the
   source **owns**, so a user would receive a correct Mallett passage cited to a person who did
   not write it. ⭐ **Book 4 is the run to fix it in** — it is already editing the cleaning node
   for `ba_manual`, and a `heading_path` repair there can rebuild `content` in the same pass,
   which is the only way to do it without hitting plan 06 §4's warning.
5. ⚠️ **`Log ingest summary`'s promote message still interpolates the version row id.** §0.4 —
   handed to book 4 for the same reason.
6. ⭐ **§11's 200–450 chunk-size band now describes zero of four books at p25** (179 · 198 ·
   173 · 160), `measured`. §4.4 has the four-book table. **Book 4 revises the criterion or drops
   it**, per standing rule 6 — all four medians are inside the band and all four p25s are outside
   it in the same direction, which is the shape of a bound set too high.
7. ⛔ ⭐ **NEW — there are two workflows named `ingest-malt`, and one of them never ran.**
   §2.1a. The tracked JSON is the executed one (`hpW9P0n7fxXY9KdF`); the unused duplicate
   (`ingestMalt00001A`) needs deleting and there is no `delete:workflow` in the n8n CLI.
   ⚠️ **Two workflows with the same name is worse than the orphaned node**, because the next
   person to click Run has a 50% chance of running the wrong one.
8. ⭐ **NEW — a runtime estimate derived from a measured run held; one inherited between plans
   did not.** Book 1 carried *"~5–9 min to embed"* against a real **16 s**; book 3 predicted
   **~3 min** and `measured` **3 min 02 s**. ⭐ **Book 4 should derive its estimate from book 3's
   execution record**, not from this plan's prose: Docling dominates, everything touching the
   database or the GPU costs seconds, and the honest hung-run threshold is about twice the
   predicted total.
9. ⚠️ **`$5` has now stored a ledger on two books, but the *asymmetry* argument rests entirely
   on book 2.** Malt's two pairs both read `applied = 2`, which cannot distinguish *stored* from
   *reconstructed*. ⭐ **A third book with distinct per-pair counts settles it**; book 4 should
   check whether its `text_repairs` gives one and say so either way. §4.1 A2c.

Then ⭐ **book 4.5, the agent**: WF4 + `tool-search-brewing-knowledge` + `mem.chat_turns`
logging, which is what finally makes **Tier C runnable for books 0a–4 retroactively**.
README §4.2 has the reasoning.
