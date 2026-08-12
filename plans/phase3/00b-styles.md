# Plan 00b — the styles model: `ref.styles`, generated style cards, and the card-format A/B

**Status:** 🟡 **built and Tier-A verified 2026-08-12 · the §5.5 A/B is NOT run** ·
**Written:** 2026-08-12
**Prereqs:** book 0a's schema and corpus (✅ live) · the four prerequisite items in §P below
**Follows:** [`plans/phase3/README.md`](README.md) §6, the per-source plan contract.

> ## What is done, measured 2026-08-12
>
> | | State |
> |---|---|
> | `ingest-bjcp-styles` built, **22 nodes**, id `Ejf3ESE3SK1XBqe3` | ✅ exported and committed |
> | `ref.styles` — BJCP 2021 | ✅ **116 rows · 96 with vitals · 20 without · 30 entry instructions · 1 null commercial_examples · 34 categories** — every §5.1 gate hit exactly |
> | Style cards in `kb.chunks` | ✅ **232, variant B**, 0 embedding gaps, 1024 dims, `is_current` |
> | Parser ledger | ✅ exactly the 3 predicted notes (21B ×2 folds, 34C → NULL) |
> | Tier A | ✅ A0–A5b pass — §6 carries the measured values |
> | **§5.5's A/B** | ⛔ **not run.** Only variant **B** was executed; there is no A0 run and no A run, so `kb.ingest_log` holds one `parse` row for this version, not three. **D32b is therefore still open** — B is deployed by default, not by measurement |
> | **Tier B** | ⬜ not recorded |
> | Tier C | ⬜ not runnable — no WF4 yet, by design (§6) |
>
> ⚠️ **B being deployed is not the same as B having won.** The whole point of §5.5 was that
> the split is a retrieval *bet*, and a bet that ships unmeasured is just the argument
> winning quietly. Running A0 and A is 2 × ~3 minutes plus the probe set (§8 steps 6–10);
> until then the §6 A/B table stays empty and D32b stays open in
> [README §9](README.md).

**Target, in one line:** an empty `ref.styles` becomes **116 BJCP 2021 rows carrying all 11
prose fields**, and those rows generate the style cards in `kb.chunks` — in the card format
that **wins a three-run A/B**, not the one that wins an argument.

Everything below is written as **build this**. Nothing is assumed to exist beyond what §P.0
verifies against the live stack.

---

## §P — Prerequisites: finish book 0a first

Four items, in this order. **None of them is optional and none may be reordered**, because
item 4 creates the measurement baseline that this plan's own §6 Tier B compares against. Run
0b's own §8 only after all four are ticked.

### P.0 What is already true — verified against the live stack 2026-08-12

Re-measured for this plan rather than carried over. All values **measured**:

| Check | Command run | Result |
|---|---|---|
| Five schemas, table counts | `pg_namespace` × `pg_class` | `brew 7` · `kb 5` · `mem 3` · `nlq 0` · `ref 1` |
| `ref.styles` exists, 29 columns | `information_schema.columns` | ✅ all 11 prose fields present; `has_vitals` is `GENERATED ALWAYS … STORED` |
| `ref.styles` rows | `count(*)` | **0** |
| `ref.styles` keys | `pg_constraint` | `UNIQUE (guide, guide_year, code)` · `CHECK guide IN ('BJCP','BA')` · GIN on `tags`, trigram on `name` |
| Style FK direction | `pg_constraint` on `brew.recipes` | `recipes_style_id_fkey FOREIGN KEY (style_id) REFERENCES ref.styles(id)` ✅ |
| `kb.chunks` | `count(*)` | **447**, embedding gaps **0**, `vector_dims` **1024** (one distinct value) |
| `kb.documents` | `select *` | one row: `how-to-brew-palmer` · `book` · authority `reference` |
| `kb.document_versions` | `count(*)` | 1, `is_current` |
| `kb.ingest_log` | `select stage, level` | 2 rows: `clean|warn`, `promote|info` |
| The agent's whole surface | `pg_proc` in `nlq` | exactly two functions: `search_knowledge`, `find_batches` |
| `find_batches` reads `ref.styles` | `pg_get_functiondef` | ✅ 1 reference |
| n8n workflows | `n8n list:workflow` | **1** — `wf1-ingest-book`, id `NoNCV2mkQEppWP7O` |
| Docling / Ollama | `/health`, `/api/tags` | `{"status":"ok"}` · `bge-m3` (1024 dims, 8192 ctx) and `gemma4:12b` resident |
| `db-init` file list | `docker-compose.yml` | six files, `15_ref.sql` before `20_brew.sql` ✅ |

**Two things this re-measurement establishes that the plan below depends on:**

- ⛔ **`ref.styles` is invisible to the agent.** `nlq` holds two functions and neither exposes
  it. Until an `nlq` view or function does, the numeric rows answer nothing the assistant can
  ask — the *cards* are the only style content the agent can reach. That is by design (Phase
  3b builds `lookup_bjcp_style`), and it is why this plan's Tier B measures cards, not rows.
- **`kb.chunk_embeddings.chunk_id` is `ON DELETE CASCADE` on `kb.chunks`.** Deleting a card
  takes its vector with it, which is what makes the A/B loop in §8 cheap and clean.

### P.1 · Build the `ingest-how-to-brew` launcher — do this first

Book 0a's ingest was run by invoking `wf1-ingest-book` directly with trigger input. That
proves the engine and leaves the per-book launcher unbuilt — the half that matters for books
1–9, because the engine is supposed to hold **zero** book constants and every source is
supposed to be its own two-node workflow with its own Run button and its own committed JSON.

**New workflow, named `ingest-how-to-brew`, two nodes:**

| # | Node | Settings |
|---|---|---|
| 1 | `When clicking 'Execute workflow'` — Manual Trigger | none |
| 2 | `Run ingest engine` — Execute Sub-workflow | **Source** `Database` · **Workflow** `wf1-ingest-book` · **Mode** `Run once with all items` · **Wait for Sub-Workflow Completion** **ON** |

Because the engine's Execute Workflow Trigger uses **Define using fields below**, node 2
renders all 13 fields as a mapper. Fill them with the book profile:

| Field | Value |
|---|---|
| `file_path` | `/data/shared/rag-files/pending/how_to_brew_john_palmer.pdf` |
| `source_format` | `pdf` |
| `slug` | `how-to-brew-palmer` |
| `title` | `How to Brew` |
| `doc_type` | `book` |
| `authors` | `John Palmer` |
| `language` | `en` |
| `edition_note` | `3rd edition, 2006` |
| `authority` | `reference` |
| `profile` | `book` |
| `front_matter_max_page` | `6` |
| `extra_drop_regex` | `(Metric Conversions\|Recommended Reading)` |
| `text_repairs` | `[["(95105°F,","(95-105°F,"],["4590","45-90"],["6575F.","65-75F."],["5560","55-60"],["$2050","$20-50"]]` |

⚠️ **Wait for completion ON is not optional.** Off, the launcher reports success the moment
Docling is handed the file, and a failed ingest looks like a green check.

**Do not activate the workflow** — a manual trigger needs no activation.

**Postgres credential note:** the launcher has no Postgres node, but the rule it inherits
matters at 0b — every Postgres node in this project uses the **`Postgres account`**
credential. `n8n_agent` is the read-only agent role and **cannot see `kb`**; picking it on a
write node produces a permission error deep inside a run.

**Then export both workflows and commit them.** Neither has been committed yet, and n8n's
database is not a backup (standing rule 4):

```bash
docker exec n8n n8n export:workflow --id=NoNCV2mkQEppWP7O --pretty --output=/demo-data/workflows/wf1-ingest-book.json && docker exec n8n n8n export:workflow --id=<LAUNCHER_ID> --pretty --output=/demo-data/workflows/ingest-how-to-brew.json && docker exec n8n chown 1000:1000 /demo-data/workflows/wf1-ingest-book.json /demo-data/workflows/ingest-how-to-brew.json
```

⚠️ `n8n/demo-data/workflows/` currently holds five JSON files describing workflows that do not
exist (`wf1-howtobrew.json`, `wf2-digestion.json`, `wf4-chat-agent.json`,
`tool-search-brewing-knowledge.json`, `tool-find-batches.json`). Clear them in the same
commit — but **move `wf4-chat-agent.json` into `backup/` rather than deleting it**: it is one
of three surviving copies of system prompt v3, which the WF4 build needs verbatim. Say where
it went in the commit message.

### P.2 · A3 idempotency — the launcher's first run *is* the test

⭐ *How to Brew* is already ingested (447 chunks, verified in P.0), so the moment the new
launcher runs, the dedup branch fires: `Crypto` produces the same `file_sha256`, `Dedup
lookup` finds the existing version, `Is new file?` goes false, and the run ends at
`Already ingested — stop`. That **is** test A3 — seconds not minutes, 0 rows inserted,
`kb.chunks` still 447. Building the launcher and proving idempotency are one action.

Fingerprint before and after — both values must be identical:

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select md5(string_agg(content_sha256, ',' order by chunk_index)), count(*) from kb.chunks;"
```

⛔ **If it instead runs a full Docling conversion (minutes, not seconds), the dedup branch is
broken and book 1 would silently duplicate book 0a. Stop and fix it there** — not at book 1,
where the symptom is a corpus with two copies of Water and no obvious cause.

### P.3 · A5 — the repair ledger

Node 26 `Log ingest summary` needs its **`$5`** parameter so `detail->'repairs'` lands in
`kb.ingest_log`. The full Query Parameters expression is five positional values:

```
={{ [ $('Ensure doc + version').first().json.version_id, JSON.stringify($('Clean + normalise').first().json.stats), JSON.stringify($('Clean + normalise').first().json.drops), JSON.stringify($json), JSON.stringify($('Clean + normalise').first().json.repairs) ] }}
```

and the `clean` row's `detail` builds as
`jsonb_build_object('stats', $2::jsonb, 'drops', $3::jsonb, 'repairs', $5::jsonb)`.

**The repairs themselves are applied and verified in the chunks** — this is the audit trail
only, so that which substitutions fired and how often is recoverable months later without
re-reading the PDF.

⚠️ **A5 cannot be tested by P.2's run.** A dedup short-circuit ends at node 6 and never
reaches node 26. Verify it at **0b's first run** (0b writes its own two `ingest_log` rows and
its own repair-equivalent ledger — §6 A2) or on a deliberate re-ingest of *How to Brew* after
deleting its version per §7.

Read it with:

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select r->>'find', r->>'applied' from kb.ingest_log, jsonb_array_elements(detail->'repairs') r where stage='clean';"
```

Expected: five rows, every `applied` ≥ 1.

### P.4 · Tier B, then Tier C — and Tier B cannot wait

⚠️ **The corpus was empty before book 0a, so 0a's Tier B *creates* the baseline books 1–9 are
measured against.** It cannot be deferred until after 0b: by then 116 (or 232) style cards
are competing in every retrieval and the baseline is contaminated by the very change 0b is
supposed to be measured for.

**The 5 standing questions** — run each, record on-target count out of 6 and the rank of the
first correct hit:

```bash
./scripts/ask.sh "diacetyl rest temperature and timing for lagers"
./scripts/ask.sh "how mash pH affects conversion and how to adjust it"
./scripts/ask.sh "when to add hops for bittering vs aroma"
./scripts/ask.sh "pitching rate and rehydrating dry yeast"
./scripts/ask.sh "my beer tastes of green apple, what causes acetaldehyde and how do I fix it"
```

⛔ **Q1 and Q3 are the gate**: Q1 must put a diacetyl-rest chunk at rank 1
(`10.4 Yeast Starters and Diacetyl Rests`, p.98); Q3 must put the three hop-timing chunks at
ranks 1–3 (`Bittering` / `Flavoring` / `Finishing`, all p.41). Both are **measured** values
for these exact 447 chunks. A miss means the chunks are not the same chunks, and that
compares *content* where the 447 count only compares cardinality.

Q2, Q4 and Q5 have no prior measurement — **whatever they return is the baseline.** Write the
numbers into 0a §6's five-row table, labelled `measured`, before running anything in 0b.

**Tier C is not runnable and that is a decision, not a skip.** There is no chat agent —
WF4 is scheduled after 0b, together with the tool it depends on. 0a's Tier C runs as part of
the WF4 build and must include the refusal check verbatim, because it is the one hard fail:
*"How much Citra do I have?"* → *"I don't have a tool for that yet"*.

`scripts/stress/tier1_routing.py` is **not** run at 0a or 0b — it measures tool routing
against a system prompt, and there is neither.

### P.5 Exit — 0a is finished when

- [x] `ingest-how-to-brew` exists, 2 nodes, Wait-for-completion ON, all 13 mapper fields filled — **built, id `BAe1fP1g7ZUsbIaq`**
- [ ] its first run ended at `Already ingested — stop` in seconds; fingerprint unchanged (A3)
- [ ] node 26 carries `$5`; the repair-ledger query is noted as pending a real ingest (A5)
- [x] both workflow JSONs exported and committed — **done 2026-08-12**; the five stale JSONs cleared, `wf4-chat-agent.json` moved to `backup/`
- [ ] the 5 standing questions run and recorded as the baseline; Q1 and Q3 hit their expected ranks

⛔ **A5 is still open, and this was verified rather than assumed.** *How to Brew* was
re-ingested on 2026-08-12 — a **real** ingest, not a dedup short-circuit — and it reproduced
**447 chunks with the drop ledger matching 0a exactly** (front matter 18, References 16,
source-specific 1, token floor 1 = 36). That run was the chance to capture the repair ledger,
and `detail->'repairs'` came back **empty**: node 26 still lacks its `$5` parameter. The next
opportunity is another deliberate re-ingest per §7, so **add `$5` before running one**.

⚠️ **A3 is unverifiable after the fact.** A dedup short-circuit writes nothing — no chunks, no
log row — so the database cannot tell you whether the launcher was ever run a second time. It
has to be observed live: run `ingest-how-to-brew` now, watch it end at
`Already ingested — stop` in seconds, and compare the fingerprint in P.2 before and after.

**Only then start §8 below.**

---

## §0 — The one-line verdict

**A new workflow, not the engine — and it is a parser, not a chunker.**

`styles.json` is already structured: 116 objects, one per style, every field a labelled
string. There is no PDF to convert, no layout to recover, no chunk boundary to negotiate.
Handing it to `wf1-ingest-book` would mean sending clean JSON through Docling to get back
chunks whose boundaries a chunker guessed, when the source already states them. Architecture
§6.6's structured path is the right one: **parse → validate → upsert rows → generate cards
from the rows → embed → promote.**

⛔ **Standing rule 7's hyphen probe does not apply here.** The line-wrap hyphen loss is a
property of PDF text extraction; this source is JSON and never passes through an extractor.
It applies with force at **book 5**, where the BA guidelines have **9 at-risk sites, all of
them final-gravity ranges** headed for `ref.styles.fg_min`/`fg_max` — the truth layer, not a
retrieval nuisance. Run the probe there before parsing.

### 0.1 What gets built

| | Thing | Nodes / rows | § |
|---|---|---|---|
| 1 | `ingest-bjcp-styles` — the styles workflow | **22 nodes** | §2 |
| 2 | `ref.styles` — BJCP 2021 | **116 rows**, 11 prose fields | §2, §3 |
| 3 | Style cards in `kb.chunks` | 116 or 232, decided by §5.5's A/B | §2, §6 |
| 4 | The card-format A/B | three runs: A0 → A → B | §6, §8 |

### 0.2 The workflow at a glance

```
Manual trigger → card variant (Set)
  → read styles.json → hash it → read it again → extract JSON
  → parse + validate (116 assertions)  → upsert 116 ref.styles rows → assert 116
  → ensure kb doc + version → demote + clear old cards → generate cards from the rows
  → select cards needing embeddings
  → loop in batches of 32: assemble → Ollama embed → zip → insert
  → promote the version → assert it promoted → log the run
```

### 0.3 Four settings that decide whether it works

| | Setting | Why it matters |
|---|---|---|
| 1 | `Loop Over Items` — **Reset must stay unset** | Reset re-splits the input every iteration and the loop never ends |
| 2 | `Ollama embed` — **Retry On Fail ON** | one transient blip loses the whole batch set and the GPU time with it |
| 3 | `Insert embeddings` — **Execute Once OFF** | ON inserts one card per batch and silently drops the other 31 |
| 4 | `Promote version` — **Execute Once ON** | the loop's `done` output carries every card; without this the node runs once per card |

Plus **Workflow Settings → Execution Order `v1`, Binary Mode `separate`** — under v1 a node
positioned left of its data source runs first and reads empty input.

---

## §1 — The probe

The contract's rule is that no plan is written from assumptions. For a structured source the
probe is **row count, per-field coverage, and any row that fails validation** — not a Docling
run. Everything below was measured on 2026-08-12 against
`shared/rag-files/pending/styles.json` and the live database.

**File:** `shared/rag-files/pending/styles.json`, 390,322 bytes.
**SHA-256:** `b0707bf268f6e0b85d05534a2e62a9eb2ecc5e674a9a0048f6e55d2a0d268178` — **measured**.
Worth writing down: this is the dedup key `kb.document_versions.file_sha256` will carry, and
it is what makes all three A/B runs land on **one** version row (§5.5's constraint, §2 node 10).

**Top-level shape:** a JSON **array** of 116 objects. Not an envelope, not a map — measured.

### 1.1 Row count and per-field coverage — all 116 rows

| Field in `styles.json` | → `ref.styles` column | Present | Non-empty | Label |
|---|---|---|---|---|
| `name` | `name` | 116 | 116 | measured |
| `number` | `code` | 116 | 116 | measured |
| `category` | `category` | 116 | 116 | measured |
| `categorynumber` | *(not imported — see §1.4)* | 116 | 116 | measured |
| `overallimpression` | `overall_impression` | 116 | 116 | measured |
| `aroma` | `aroma` | 116 | 116 | measured |
| `appearance` | `appearance` | 116 | 116 | measured |
| `flavor` | `flavor` | 116 | 116 | measured |
| `mouthfeel` | `mouthfeel` | 116 | 116 | measured |
| `comments` | `comments` | 116 | 116 | measured |
| `history` | `history` | 116 | 116 | measured |
| `characteristicingredients` | `characteristic_ingredients` | 116 | 116 | measured |
| `stylecomparison` | `style_comparison` | 116 | 116 | measured |
| **`entryinstructions`** | `entry_instructions` | **30** | **30** | measured ⚠️ |
| `commercialexamples` | `commercial_examples[]` | 116 | **115** | measured ⚠️ |
| `tags` | `tags[]` | 116 | 116 | measured |
| `ogmin`/`ogmax` | `og_min`/`og_max` | **96** | 96 | measured |
| `fgmin`/`fgmax` | `fg_min`/`fg_max` | **96** | 96 | measured |
| `ibumin`/`ibumax` | `ibu_min`/`ibu_max` | **96** | 96 | measured |
| `srmmin`/`srmmax` | `srm_min`/`srm_max` | **96** | 96 | measured |
| `abvmin`/`abvmax` | `abv_min`/`abv_max` | **96** | 96 | measured |
| **`currentlydefinedtypes`** | ⚠️ **no column** | **1** | 1 | measured — §1.3 |
| **`strengthclassifications`** | ⚠️ **no column** | **1** | 1 | measured — §1.3 |

**11 prose fields** — `overallimpression`, `aroma`, `appearance`, `flavor`, `mouthfeel`,
`comments`, `history`, `characteristicingredients`, `stylecomparison`, `entryinstructions`,
`tags` — plus `commercialexamples` as a twelfth list field. `ref.styles` has a column for
every one of them. **Nothing in this source needs to be discarded for lack of a home.**

### 1.2 Rows that fail validation — three findings, and only one is benign

Every check below was run over all 116 rows.

| Check | Result | Label |
|---|---|---|
| Row count | **116** | measured |
| Duplicate `number` | **0** | measured |
| `number` matching `^[0-9]{1,2}[A-Z]$` | **116 of 116** | measured |
| Vital-stat strings parseable as numbers | **116 of 116** (all 10 fields where present) | measured |
| Any `min > max` across OG/FG/IBU/SRM/ABV | **0** | measured |
| Styles with **no** vital statistics | **20** | measured |
| ⛔ **`commercialexamples` = the literal string `"None"`** | **1** — style **34C** | measured |
| ⚠️ Objects carrying keys with no column | **1** — style **21B** | measured |
| Commercial-example items after a comma split | **619**, one suspicious (`Palm`, 24B) — **a real Belgian brewery, not a split defect** | measured |
| Tag items after a comma split | **776**, **60 distinct** | measured |

⛔ **`34C.commercialexamples` is the string `"None"`, not an empty string and not JSON null.**
A naive split produces the one-element array `{None}` and every card for that style would
read *"Commercial examples: None"* as though None were a beer. §3's parser maps the sentinel
to SQL `NULL`; §5 gates on `commercial_examples IS NULL` for exactly one row.

**20 styles define no vital statistics** — measured, and the codes are exactly the specialty
categories: `27A`, `28A`, `28B`, `28C`, `29A`, `29B`, `29C`, `30A`, `30B`, `30C`, `30D`,
`31A`, `31B`, `32A`, `32B`, `33A`, `33B`, `34A`, `34B`, `34C`. Those ranges vary with the base
style, so their absence is correct data, not missing data. The columns are nullable, and
`has_vitals` (generated, `og_min IS NOT NULL`) will read **false on exactly these 20** — the
branch the card generator uses so a style with no numbers never renders **"OG 0.000"**.

⚠️ **`entryinstructions` is present on 30 of 116, and that is also correct** — BJCP prints
entry instructions only where a style requires the entrant to declare something. The card
generator must omit the line rather than print an empty label. The 30 are `2A`, `9A`, `10A`,
`10C`, `21B`, `23F`, `24C`, `25B`, `26D`, `27A`, `28A`, `28B`, `28C`, `29A`, `29B`, `29C`,
`29D`, `30A`, `30B`, `30C`, `30D`, `31A`, `31B`, `32A`, `32B`, `33A`, `33B`, `34A`, `34B`,
`34C` — measured.

### 1.3 The one row the schema has no column for — 21B Specialty IPA

**Measured:** style `21B` alone carries two extra keys:

| Key | Value |
|---|---|
| `currentlydefinedtypes` | `Belgian IPA, Black IPA, Brown IPA, Red IPA, Rye IPA, White IPA, Brut IPA` |
| `strengthclassifications` | `Session -- ABV: 3.0 -- 5.0% Standard -- ABV: 5.0 -- 7.5% Double -- ABV: 7.5 -- 10.0%` |

This is real answerable content — *"what kinds of specialty IPA are there"* is a question the
corpus should answer — and there is nowhere to put it. Three options, and the decision is
recorded here rather than made silently inside a Code node:

| Option | Verdict |
|---|---|
| Add two columns to `ref.styles` | ⛔ two columns populated on 1 of 116 rows, and BA 2026 will not have them. A schema change for one row |
| Drop the keys | ⛔ silent data loss, in the one place the plan can see it coming |
| ✅ **Append both to `comments`, labelled** | one row affected, no schema change, the content stays retrievable, and the label makes its origin readable in a citation |

**Decision: append.** The parser appends
`Currently defined types: <value>` and `Strength classifications: <value>` as separate lines
at the end of `comments` for 21B, and counts the operation into the run ledger so it is
visible in `kb.ingest_log`. §3 implements it.

⭐ **And the parser throws on any key it does not recognise.** That is the general rule this
finding buys: an unknown field in a structured source must fail loudly at parse time, because
the alternative — a `JSON.parse` that quietly ignores it — is how five prose fields go missing
for a year without anyone noticing. Book 5 will hand this same parser BA 2026 with a different
key set; a throw is what forces that to be a decision.

### 1.4 What is deliberately not imported

`categorynumber` (`"7"` for `7B`) is the leading digits of `number` and derivable from it in
one expression. Storing it is storing the same assertion twice, which README §3.2 calls a
defect in its own right. **Not imported.** If a category-level query ever needs it,
`substring(code from '^[0-9]+')` is the answer and it cannot drift.

### 1.5 Card sizes, measured over all 116 styles

The three variants of §5.5 differ only in which fields go into a card and how many cards a
style gets. Character counts are **measured** by building every card body for all 116 styles.
Token counts are **predicted**, using a chars-per-token ratio of **4.379 measured on the live
447 `kb.chunks`** (`sum(length(content)) / sum(token_count)`) — the same tokenizer, the same
corpus, so it is a calibrated conversion rather than a guess.

| Variant | Fields | Cards | Median tokens | p75 | Max | 6 cards in context |
|---|---|---|---|---|---|---|
| **A0** — 6 prose fields + vitals + commercial examples | 6 | **116** | **471** predicted | 541 | 895 | ~2,826 |
| **A** — all 11 prose fields + vitals + commercial examples | 11 | **116** | **679** predicted | 787 | 1,222 | **~4,074** ⚠️ |
| **B** — all 11 fields, split sensory / context | 11 | **232** | **350** predicted | 407 | 670 | ~2,100 |
| ↳ B sensory | 5 + vitals | 116 | 357 predicted | 411 | 561 | — |
| ↳ B context | 6 + tags | 116 | 327 predicted | 407 | 670 | — |

**These three numbers are the whole argument for running the A/B rather than deciding it.**
A is the variant that carries the most information and the one that busts the context budget:
~4,074 tokens for six cards against the ~3,000 the design allows. B carries the same
information at half the width. But *carrying* is not *retrieving*, and whether the split helps
or hurts is a retrieval question. §6 measures it.

⚠️ **The `max_tokens = 512` chunk-size band is missed by every variant, and it should be
argued rather than tuned** (standing rule 6). Predicted counts over 512 tokens:

| Variant | Cards over 512 predicted | of |
|---|---|---|
| A0 | 36 | 116 (31%) |
| A | **108** | 116 (93%) |
| B | 13 | 232 (5.6%) |

The band exists for a *chunker*, which chooses where to cut. A generated card has no cut to
choose: it is one style, whole, and splitting Irish Stout's flavour paragraph in half to hit
512 would produce two chunks neither of which describes Irish Stout. bge-m3's window is 8,192
tokens (**measured** from `/api/tags`), so even A's 1,222-token maximum is nowhere near
truncation. **Nothing is truncated in any variant; the criterion simply does not govern
generated cards.** Recorded as a documented miss with a reason, per §5's gate column.

---

## §2 — What gets built, node by node

One new workflow, **`ingest-bjcp-styles`**, **22 nodes** — the list below numbers 21 steps
because step 9 is two n8n nodes, a Postgres query and the Code assert that reads it. It
follows the `ingest-<slug>` naming so
it sits beside `ingest-how-to-brew` in the workflow list with its own Run button and its own
tracked JSON — but it is a full workflow rather than a 2-node launcher, because structured
sources do not use the engine (§0).

Every Postgres node uses **Operation `Execute Query`** and the **`Postgres account`**
credential. ⛔ Never `n8n_agent` — it is the read-only agent role and cannot see `kb`. Every
Code node uses **`Run Once for All Items`** unless stated.

Build in node order and wire as you go.

---

#### 1 · `When clicking 'Execute workflow'` — Manual Trigger

No settings. Do not activate the workflow.

#### 2 · `Card variant` — Set (Edit Fields)

| Field | Type | Value |
|---|---|---|
| `variant` | string | `A0` ← change to `A`, then `B`, between runs |
| `guide` | string | `BJCP` |
| `guide_year` | number | `2021` |
| `slug` | string | `bjcp-2021-beer-styles` |
| `title` | string | `BJCP 2021 Beer Style Guidelines` |
| `doc_type` | string | `style_guide` |
| `authority` | string | `guideline` |
| `language` | string | `en` |
| `file_path` | string | `/data/shared/rag-files/pending/styles.json` |

⭐ **Why `variant` is a field and not an edit to the card SQL.** §5.5's A/B is three runs of
one workflow. Editing a 60-line SQL body between runs means the thing under test is also the
thing being hand-modified three times, and the exported JSON records only whichever variant
was pasted last. As a field: one node changes, the value lands in
`kb.document_versions.chunker_config` (node 10), and *"which variant produced these cards"* is
answerable from the database months later. The cost is a three-branch `CASE` in node 12,
written once.

**`doc_type` is `style_guide`** — one of the five values `kb.documents.doc_type` allows
(`book`, `style_guide`, `article`, `datasheet`, `note`, verified in P.0). It is also what
`ask.sh`'s optional second argument filters on, which §6 uses.

**`authority` is `guideline`**, not `reference`. BJCP is a competition body stating what a
style *should* be; Palmer is a reference explaining how brewing works. The column allows
exactly `reference | guideline | practitioner` (verified in P.0), and this distinction is what
lets the tool's passage header eventually write *"the BJCP guidelines specify X"* rather than
flattening both into "a source says". ⛔ It must never enter ranking.

#### 3 · `Read styles.json` — Read/Write Files from Disk

| Field | Value |
|---|---|
| Operation | `Read File(s) From Disk` |
| File(s) Selector | `={{ $('Card variant').first().json.file_path }}` |
| Put Output File in Field | `data` |

An explicit path, never a glob — `pending/` currently holds 13 files.

#### 4 · `Crypto`

| Field | Value |
|---|---|
| Action | `Hash` · Type `SHA256` · Encoding `HEX` |
| Binary File | **ON** |
| Binary Property Name | `data` |
| Property Name | `file_sha256` |

Must produce `b0707bf2…268178` (§1). If it does not, the Crypto node is misconfigured and the
dedup key is wrong — one glance catches it, and no other test gives you it.

#### 5 · `Read styles.json for parsing` — Read/Write Files from Disk

Identical settings to node 3. **Needed because Crypto consumes the binary it hashes**, and the
Set node has replaced the item stream regardless.

⚠️ Type the expression; do not duplicate node 3. Duplicating produces `Read styles.json1`, and
node 7's `$('…')` references break on names you did not intend.

#### 6 · `Extract from File` — Extract from File

| Field | Value |
|---|---|
| Operation | `Move File to JSON` / `From JSON` |
| Input Binary Field | `data` |

#### 7 · `Parse + validate styles` — Code

The complete code is §3. It emits **one item** holding the whole 116-row array plus a stats
object, so node 8 inserts them in a single query rather than 116 round trips.

#### 8 · `Upsert style rows` — Postgres

```sql
INSERT INTO ref.styles
  (guide, guide_year, code, name, category,
   og_min, og_max, fg_min, fg_max, ibu_min, ibu_max,
   srm_min, srm_max, abv_min, abv_max,
   overall_impression, aroma, appearance, flavor, mouthfeel, comments,
   history, characteristic_ingredients, style_comparison, entry_instructions,
   commercial_examples, tags)
SELECT $1::text, $2::int,
       x.code, x.name, x.category,
       x.og_min, x.og_max, x.fg_min, x.fg_max, x.ibu_min, x.ibu_max,
       x.srm_min, x.srm_max, x.abv_min, x.abv_max,
       x.overall_impression, x.aroma, x.appearance, x.flavor, x.mouthfeel, x.comments,
       x.history, x.characteristic_ingredients, x.style_comparison, x.entry_instructions,
       CASE WHEN x.commercial_examples IS NULL THEN NULL
            ELSE ARRAY(SELECT jsonb_array_elements_text(x.commercial_examples)) END,
       CASE WHEN x.tags IS NULL THEN NULL
            ELSE ARRAY(SELECT jsonb_array_elements_text(x.tags)) END
FROM jsonb_to_recordset($3::jsonb) AS x(
  code text, name text, category text,
  og_min numeric, og_max numeric, fg_min numeric, fg_max numeric,
  ibu_min int, ibu_max int, srm_min numeric, srm_max numeric,
  abv_min numeric, abv_max numeric,
  overall_impression text, aroma text, appearance text, flavor text,
  mouthfeel text, comments text, history text,
  characteristic_ingredients text, style_comparison text, entry_instructions text,
  commercial_examples jsonb, tags jsonb
)
ON CONFLICT (guide, guide_year, code) DO UPDATE SET
  name = EXCLUDED.name, category = EXCLUDED.category,
  og_min = EXCLUDED.og_min, og_max = EXCLUDED.og_max,
  fg_min = EXCLUDED.fg_min, fg_max = EXCLUDED.fg_max,
  ibu_min = EXCLUDED.ibu_min, ibu_max = EXCLUDED.ibu_max,
  srm_min = EXCLUDED.srm_min, srm_max = EXCLUDED.srm_max,
  abv_min = EXCLUDED.abv_min, abv_max = EXCLUDED.abv_max,
  overall_impression = EXCLUDED.overall_impression, aroma = EXCLUDED.aroma,
  appearance = EXCLUDED.appearance, flavor = EXCLUDED.flavor,
  mouthfeel = EXCLUDED.mouthfeel, comments = EXCLUDED.comments,
  history = EXCLUDED.history,
  characteristic_ingredients = EXCLUDED.characteristic_ingredients,
  style_comparison = EXCLUDED.style_comparison,
  entry_instructions = EXCLUDED.entry_instructions,
  commercial_examples = EXCLUDED.commercial_examples, tags = EXCLUDED.tags;
```

**Query Parameters:**
`={{ [ $('Card variant').first().json.guide, $('Card variant').first().json.guide_year, JSON.stringify($json.rows) ] }}`

Four things worth knowing:

- **One query, 116 rows.** `jsonb_to_recordset` is the same idiom the engine uses to insert
  447 chunks in one statement. A per-item Postgres node would run 116 times and turn a
  sub-second step into a visible one for no gain.
- **`guide` and `guide_year` come from the Set node, not from the parser**, so book 5 reuses
  this node unchanged with `BA` / `2026`. The parser handles the file's shape; the launcher
  fields handle which body published it.
- **`ON CONFLICT (guide, guide_year, code) DO UPDATE` refreshes every column.** The A/B runs
  this three times and a correction to the parser must actually take effect on run 2.
- **`has_vitals` is never written.** It is `GENERATED ALWAYS … STORED`; naming it in an INSERT
  is an error. It computes itself from `og_min` and will read false on exactly the 20 styles
  in §1.2.

#### 9 · `Assert style rows` — Postgres, then Code

**9a — `Verify style rows`, Postgres:**

```sql
SELECT count(*)                                            AS rows,
       count(*) FILTER (WHERE has_vitals)                  AS with_vitals,
       count(*) FILTER (WHERE NOT has_vitals)              AS without_vitals,
       count(*) FILTER (WHERE entry_instructions IS NOT NULL) AS with_entry,
       count(*) FILTER (WHERE commercial_examples IS NULL) AS no_examples,
       count(*) FILTER (WHERE style_comparison IS NULL
                          OR history IS NULL
                          OR characteristic_ingredients IS NULL) AS missing_new_prose,
       count(*) FILTER (WHERE og_min > og_max OR fg_min > fg_max
                          OR ibu_min > ibu_max OR srm_min > srm_max
                          OR abv_min > abv_max)             AS inverted_ranges
FROM ref.styles WHERE guide = $1 AND guide_year = $2;
```

**Query Parameters:** `={{ [ $('Card variant').first().json.guide, $('Card variant').first().json.guide_year ] }}`

**9b — `Assert style rows`, Code:**

```js
const r = $json;
const exp = { rows: 116, with_vitals: 96, without_vitals: 20, with_entry: 30,
              no_examples: 1, missing_new_prose: 0, inverted_ranges: 0 };
for (const [k, v] of Object.entries(exp))
  if (Number(r[k]) !== v)
    throw new Error(`ref.styles check "${k}" = ${r[k]}, expected ${v} — see plan 00b §1.2`);
return [{ json: r }];
```

**Why an assert node rather than reading the numbers afterwards.** Everything downstream —
cards, embeddings, promotion — is generated *from* these rows. A silent import defect becomes
116 wrong cards and eight minutes of GPU before anyone looks. Failing here costs seconds.
The seven expected values are §1's measured probe, so this node is the probe re-run as a gate.

#### 10 · `Ensure KB doc + version` — Postgres

```sql
WITH d AS (
  INSERT INTO kb.documents (slug, title, doc_type, language, authority)
  VALUES ($2, $3, $4, $5, $6)
  ON CONFLICT (slug) DO UPDATE SET
    title = EXCLUDED.title, doc_type = EXCLUDED.doc_type,
    language = EXCLUDED.language, authority = EXCLUDED.authority
  RETURNING id
)
INSERT INTO kb.document_versions
  (document_id, version, source_filename, file_sha256, chunker_config, is_current)
SELECT d.id,
       COALESCE((SELECT max(v.version) FROM kb.document_versions v
                 WHERE v.document_id = d.id), 0) + 1,
       'styles.json', $1,
       jsonb_build_object('source','structured','generator','bjcp-style-card',
                          'variant', $7::text, 'guide', 'BJCP', 'guide_year', 2021),
       false
FROM d
ON CONFLICT (file_sha256) DO UPDATE
  SET chunker_config = EXCLUDED.chunker_config
RETURNING id AS version_id;
```

**Query Parameters:**

```
={{ (() => { const p = $('Card variant').first().json; return [
  $('Crypto').first().json.file_sha256,
  p.slug, p.title, p.doc_type, p.language, p.authority, p.variant
]; })() }}
```

⭐ **`ON CONFLICT (file_sha256) DO UPDATE` is what makes the A/B possible, and it is the one
place this workflow differs from the engine's version of the same node.** `kb.document_versions`
carries `UNIQUE (file_sha256)` (verified in P.0), and all three variants are generated from the
same `styles.json` — so they hash identically and **cannot coexist**. `DO NOTHING` would return
no row on runs 2 and 3 and the node would emit zero items, silently ending the workflow.
`DO UPDATE` always returns the id *and* rewrites `chunker_config`, so the stored version says
which variant produced the cards currently in it.

**`authors` is not set.** The BJCP guidelines are a committee document; a fabricated author
string is worse than a null.

#### 11 · `Demote + clear old cards` — Postgres

```sql
WITH demoted AS (
  UPDATE kb.document_versions SET is_current = false
  WHERE id = $1 RETURNING id
)
DELETE FROM kb.chunks
WHERE version_id = (SELECT id FROM demoted)
RETURNING chunk_index;
```

**Query Parameters:** `={{ [$json.version_id] }}`

⚠️ **Demoting before deleting is deliberate and it is the subtle one.** Run 1 promotes the
version; run 2 must clear that same version's cards to regenerate them. A `DELETE` guarded by
*"only if this version is not current"* — the obvious safety rule — would refuse, and the A/B
would appear to work while measuring run 1's cards three times. Demoting first states the
truth instead: while the cards are being rebuilt, this document has no current version.

⚠️ **The consequence, stated so it is not discovered:** between this node and node 19, style
questions return nothing from the style guide. On a 116-card run that window is **~2 minutes
predicted** (§5). Do not run the A/B while using the assistant — which standing rule 3
already forbids for a different reason.

**Embeddings need no separate delete:** `kb.chunk_embeddings.chunk_id` is
`ON DELETE CASCADE` on `kb.chunks` (verified in P.0).

**No `Reuse embeddings` node is built.** The engine has one, and it would be dead here: it
recovers vectors from *other* chunks with the same `content_sha256`, and this node has just
deleted the only chunks that could have matched. A node that can never fire is worse than no
node — it implies a behaviour that does not exist.

#### 12 · `Generate style cards` — Postgres

⭐ **The card is an `INSERT … SELECT` straight from `ref.styles`. That is the property that
makes the numeric row and the narrative card unable to drift** (README §3.2: derived
duplication is fine, parallel duplication is a bug). Nothing between the row and the card
retypes a number. Keep this property through every later edit.

```sql
WITH cfg AS (SELECT $2::text AS variant),
parts AS (
  SELECT s.code, s.name, s.category, p.kind, p.ord, p.body
  FROM ref.styles s
  CROSS JOIN cfg
  CROSS JOIN LATERAL (
    SELECT concat_ws(E'\n',
      format('%s (BJCP %s) — %s', s.name, s.code, s.category),
      CASE WHEN s.has_vitals THEN
        format('Vital statistics: OG %s-%s, FG %s-%s, IBU %s-%s, SRM %s-%s, ABV %s-%s%%',
               s.og_min, s.og_max, s.fg_min, s.fg_max, s.ibu_min, s.ibu_max,
               s.srm_min, s.srm_max, s.abv_min, s.abv_max) END,
      'Overall impression: ' || s.overall_impression,
      'Aroma: '      || s.aroma,
      'Appearance: ' || s.appearance,
      'Flavor: '     || s.flavor,
      'Mouthfeel: '  || s.mouthfeel
    ) AS sensory,
    concat_ws(E'\n',
      'Comments: '                   || s.comments,
      'History: '                    || s.history,
      'Characteristic ingredients: ' || s.characteristic_ingredients,
      'Style comparison: '           || s.style_comparison,
      'Entry instructions: '         || s.entry_instructions,
      'Commercial examples: '        || array_to_string(s.commercial_examples, ', '),
      'Tags: '                       || array_to_string(s.tags, ', ')
    ) AS context
  ) b
  CROSS JOIN LATERAL (
    SELECT * FROM (VALUES
      ('single',  0, CASE cfg.variant
                       WHEN 'A0' THEN concat_ws(E'\n', b.sensory,
                              'Comments: ' || s.comments,
                              'Commercial examples: '
                                || array_to_string(s.commercial_examples, ', '))
                       WHEN 'A'  THEN concat_ws(E'\n', b.sensory, b.context)
                     END),
      ('sensory', 0, CASE cfg.variant WHEN 'B' THEN b.sensory END),
      ('context', 1, CASE cfg.variant WHEN 'B' THEN b.context END)
    ) AS t(kind, ord, body)
    WHERE t.body IS NOT NULL
  ) p
  WHERE s.guide = 'BJCP' AND s.guide_year = 2021
)
INSERT INTO kb.chunks
  (version_id, chunk_index, content, raw_content, heading_path,
   page_from, page_to, token_count, content_sha256)
SELECT $1::bigint,
       (row_number() OVER (ORDER BY code, ord) - 1)::int,
       array_to_string(hp, ' > ') || E'\n' || body,
       body,
       hp,
       NULL::int, NULL::int, NULL::int,
       encode(sha256(convert_to(body, 'UTF8')), 'hex')
FROM parts,
LATERAL (SELECT CASE WHEN kind = 'single'
                     THEN ARRAY['BJCP 2021', category, code || ' ' || name]
                     ELSE ARRAY['BJCP 2021', category, code || ' ' || name,
                                initcap(kind)] END AS hp) h
ON CONFLICT (version_id, chunk_index) DO UPDATE SET
  content        = EXCLUDED.content,
  raw_content    = EXCLUDED.raw_content,
  heading_path   = EXCLUDED.heading_path,
  content_sha256 = EXCLUDED.content_sha256;
```

**Query Parameters:** `={{ [ $('Ensure KB doc + version').first().json.version_id, $('Card variant').first().json.variant ] }}`

Six things worth knowing:

- ⭐ **`concat_ws` with a bare `'Label: ' || column` is the null handling, and it is why there
  is no `coalesce`.** In Postgres `'Aroma: ' || NULL` is NULL, and `concat_ws` skips NULL
  arguments entirely. So an absent field produces **no line at all** rather than an empty
  label. That is what makes `entry_instructions` — present on 30 of 116 (§1.2) — correct for
  free, and `commercial_examples` correct for 34C, whose value §3 maps to NULL.
- ⛔ **`CASE WHEN s.has_vitals THEN …` is the vitals branch, and it is not optional.** 20
  styles carry no OG/FG/IBU/SRM/ABV. A model handed `og_min = null` renders **"OG 0.000"**
  without hesitating — so the line must be *absent*, not empty. Branch on the generated
  column rather than trusting null handling anywhere downstream.
- ⚠️ **`content` is built from the same `heading_path` expression, in the same statement.**
  Every plan repeats plan 06 §4's warning — *if `heading_path` is modified, `content` must be
  rebuilt* — because otherwise the embedding still carries the old heading and the repair does
  nothing. Here they are computed once and used twice, so they cannot disagree. **Keep it that
  way.** If a later edit moves the heading into a separate node, this warning stops being
  inert.
- **`chunk_index` is a dense `row_number() - 1` over `(code, ord)`.** For A0/A that is 0–115,
  one per style in code order. For B it is 0–231, sensory then context per style. Density
  matters here in a way it does not for the engine: there is no upstream numbering to preserve
  as provenance, and `ON CONFLICT (version_id, chunk_index)` needs the same style to land on
  the same index across a re-run of the same variant.
- **`page_from` / `page_to` are NULL, and that is a deliberate exception to a hard gate.** The
  contract makes missing pages a must-be-0 failure because *citations break without it*. A
  generated card has no page: it is a whole style, assembled from a JSON row. A fabricated
  page number would be worse than none — it would cite a page of a PDF that was never read.
  The card's citation is its heading path, which is complete and unambiguous
  (`BJCP 2021 > Amber Bitter European Beer > 7B Altbier`). §5 gates on
  `page_from IS NULL for all cards and NOT NULL for all 447 book chunks` instead.
- **`token_count` is NULL, for the same reason and a narrower one:** nothing in this path runs
  the bge-m3 tokenizer. Docling is not involved and Ollama's embed endpoint returns no token
  count. Storing a chars/4.379 estimate in a column that means *tokenizer tokens* would be
  putting a fabricated number in the truth layer to make a dashboard look complete. §5 gates
  on card size using `length(content)` and the calibrated ratio, labelled predicted.

#### 13 · `Select cards needing embeddings` — Postgres

```sql
SELECT c.id, c.content
FROM kb.chunks c
WHERE c.version_id = $1
  AND NOT EXISTS (SELECT 1 FROM kb.chunk_embeddings e
                  WHERE e.chunk_id = c.id AND e.model = 'bge-m3')
ORDER BY c.chunk_index;
```

**Query Parameters:** `={{ [$('Ensure KB doc + version').first().json.version_id] }}`

#### 14 · `Loop Over Items` — Split in Batches (typeVersion 3)

| Field | Value |
|---|---|
| Batch Size | `32` |
| Options | *(empty)* |

⛔ **Do not set Reset.** 116 ÷ 32 = **4 batches** (last holding 20); 232 ÷ 32 = **8 batches**
(last holding 8) — both predicted.

#### 15 · `Assemble embed input` — Code

```js
const items = $input.all();
return [{ json: {
  ids:    items.map(i => i.json.id),
  inputs: items.map(i => i.json.content),
}}];
```

One HTTP call per batch instead of 32. The two arrays are positionally aligned and node 17
depends on that alignment holding, so nothing between here and there may reorder, filter or
re-sort items.

It embeds `content` — the heading path prepended to the body — not `raw_content`. For a style
card that prefix is what carries *"BJCP 2021 … 7B Altbier"* into the vector, which is most of
why a card is findable by style name at all.

#### 16 · `Ollama embed` — HTTP Request

| Field | Value |
|---|---|
| Method / URL | `POST` `http://ollama:11434/api/embed` |
| Send Body / Content Type / Specify Body | ON · `JSON` · `Using JSON` |
| JSON | `={{ { "model": "bge-m3", "input": $json.inputs, "keep_alive": -1 } }}` |
| Options → Timeout | `120000` |
| **Settings → Retry On Fail** | **ON** |

- **`/api/embed`, not `/api/embeddings`.** The singular endpoint takes `prompt` and returns
  `embedding`; this one takes `input` (array) and returns `embeddings` (array of arrays). Hit
  the wrong one and node 17 throws on `emb.length`.
- **`keep_alive: -1`** pins bge-m3 in VRAM; without it Ollama unloads after 5 minutes idle and
  every batch pays a cold load.
- **The JSON body is an expression producing an object**, not a string. The leading `=` matters.

#### 17 · `Zip ids + embeddings` — Code

```js
const src = $('Assemble embed input').first().json;
const emb = $json.embeddings;
if (!Array.isArray(emb) || emb.length !== src.ids.length)
  throw new Error(`Embedding count ${emb?.length} != inputs ${src.ids.length}`);
if (emb[0].length !== 1024)
  throw new Error(`Expected 1024 dims, got ${emb[0].length} — schema mismatch`);
return src.ids.map((id, i) => ({
  json: { chunk_id: id, embedding: '[' + emb[i].join(',') + ']' },
}));
```

- **`'[' + … + ']'` — a string, deliberately.** pgvector's text input format is `[0.1,0.2,…]`.
  Handing the Postgres node a raw JS array makes the driver serialise a Postgres *array*
  (`{0.1,0.2,…}`), which `::vector` rejects. The single non-obvious line in the loop.
- **The 1024 check is a schema tripwire** against `vector(1024)`; it fails once, loudly, on
  the first batch instead of once per row.
- ⚠️ `$('Assemble embed input')` is a reference **by name**. A node named
  `Assemble embed input1` would leave this pointing at the original and silently zip the wrong
  ids onto the vectors. Confirm no numeric suffix.

#### 18 · `Insert embeddings` — Postgres

```sql
INSERT INTO kb.chunk_embeddings (chunk_id, model, embedding)
VALUES ($1, 'bge-m3', $2::vector)
ON CONFLICT (chunk_id, model) DO UPDATE
  SET embedding = EXCLUDED.embedding, created_at = now()
RETURNING chunk_id, (xmax = 0) AS inserted;
```

**Query Parameters:** `={{ [$json.chunk_id, $json.embedding] }}`
**Execute Once must stay OFF** — this runs once per item, 32 per batch.

Wire `Insert embeddings → Loop Over Items` to close the loop.

#### 19 · `Promote version` — Postgres

```sql
SELECT * FROM kb.promote_version($1);
```

**Query Parameters:** `={{ [$('Ensure KB doc + version').first().json.version_id] }}`
**Settings → Execute Once: ON** — the loop's `done` output carries every card.

Never hand-roll the `is_current` flip. The function refuses to promote unless
`total > 0 AND missing = 0` (source read in P.0), which is the coverage gate — and it is what
re-promotes the version that node 11 demoted.

#### 20 · `Assert promoted` — Code

```js
const r = $json;
if (r.missing > 0) throw new Error(`${r.missing} of ${r.total} cards have no embedding — not promoted`);
if (!r.is_current) throw new Error(`Version ${r.version_id} did not become current`);
return [{ json: r }];
```

`promote_version` returns quietly without promoting when coverage is incomplete. This turns
that silence into a failed execution — and here it also catches the specific failure node 11
introduces: a demoted version that never came back.

#### 21 · `Log run summary` — Postgres

```sql
INSERT INTO kb.ingest_log (version_id, stage, level, message, detail)
VALUES
  ($1::bigint, 'parse',
   CASE WHEN ($2::jsonb->>'warnings')::int > 0 THEN 'warn' ELSE 'info' END,
   format('parsed %s styles for variant %s: %s with vitals, %s without, %s entry instructions, %s notes folded',
          $2::jsonb->>'styles', $3::text, $2::jsonb->>'with_vitals',
          $2::jsonb->>'without_vitals', $2::jsonb->>'with_entry',
          $2::jsonb->>'folded_fields'),
   jsonb_build_object('stats', $2::jsonb, 'variant', $3::text,
                      'notes', $4::jsonb)),
  ($1::bigint, 'promote',
   CASE WHEN ($5::jsonb->>'missing')::int > 0 THEN 'error' ELSE 'info' END,
   format('version %s promoted: %s cards, %s missing embeddings',
          $5::jsonb->>'version_id', $5::jsonb->>'total', $5::jsonb->>'missing'),
   $5::jsonb)
RETURNING id, stage, level, message;
```

**Query Parameters:**

```
={{ [ $('Ensure KB doc + version').first().json.version_id, JSON.stringify($('Parse + validate styles').first().json.stats), $('Card variant').first().json.variant, JSON.stringify($('Parse + validate styles').first().json.notes), JSON.stringify($json) ] }}
```

**Two rows per run, exactly as the engine writes two.** `notes` is this source's equivalent of
the engine's drop ledger: every parser decision that changed the data — the 21B fold, the 34C
`"None"` sentinel — recorded with the style code, so *"what did the parser silently do"* is
answerable from SQL. `variant` is recorded on the row as well as in `chunker_config`, so the
three A/B runs leave a readable trail.

Note `kb.ingest_log.level` is constrained to `info | warn | error` (verified in P.0);
`stage` is free text, so `parse` is legal.

### 2.1 Wiring

Straight line 1 → 13, then the embedding loop:

```
Select cards needing embeddings → Loop Over Items
Loop Over Items [done, output 0] → Promote version → Assert promoted → Log run summary
Loop Over Items [loop, output 1] → Assemble embed input → Ollama embed
                                 → Zip ids + embeddings → Insert embeddings
Insert embeddings → Loop Over Items          ← closes the loop
```

Place nodes 15–18 on a row ~430 px below node 14 and keep all four to the **right** of it —
under execution order v1 a node positioned left of the loop node runs before it and reads
empty input.

**Workflow Settings:** Execution Order `v1`, Binary Mode `separate`.

---

## §3 — The parser

Node 7, `Parse + validate styles`, mode `Run Once for All Items`. Complete and ready to paste.

⚠️ **The standing warning every plan repeats:** if `heading_path` is modified, `content` must
be rebuilt, or the embedding still carries the old heading and the repair does nothing. This
parser touches no heading path — node 12 builds both from one expression — so the warning is
**inert here**. It stops being inert the moment card assembly moves out of that single
statement.

```js
// ---- styles.json -> validated ref.styles rows ----
// The source is already structured, so this node's job is not extraction but
// REFUSAL: every assumption plan 00b §1 measured is re-asserted here, and a
// source that has changed under us fails at parse time rather than 116 wrong
// cards and eight minutes of GPU later.

const inputItems = $input.all();

// Locate the array regardless of how Extract from File emitted it.
let styles;
if (inputItems.length > 1) {
  styles = inputItems.map(i => i.json);          // one item per style
} else {
  const j = inputItems[0].json;
  if (Array.isArray(j)) styles = j;
  else {
    const key = Object.keys(j).find(k => Array.isArray(j[k]) && j[k][0]?.number);
    if (!key) throw new Error('Could not find styles array. Top-level keys: ' + Object.keys(j).join(', '));
    styles = j[key];
  }
}
if (!Array.isArray(styles) || styles.length === 0) throw new Error('No styles parsed');
if (styles.length !== 116)
  throw new Error(`Expected 116 styles, got ${styles.length} — the source changed; re-run plan 00b §1 before continuing`);

// ---- every key this parser knows about ----
// An unrecognised key is a THROW, not a shrug. Silently ignoring one is exactly
// how five prose fields go missing for a year. Book 5 hands this same parser a
// different guide; a throw makes that a decision.
// All 28 keys measured across the 116 styles (plan 00b §1.1).
const KNOWN = new Set([
  'name','number','category','categorynumber',
  'overallimpression','aroma','appearance','flavor','mouthfeel','comments',
  'history','characteristicingredients','stylecomparison','entryinstructions',
  'commercialexamples','tags',
  // vital statistics: present on 96 of 116, absent on the other 20
  'ogmin','ogmax','fgmin','fgmax','ibumin','ibumax','srmmin','srmmax','abvmin','abvmax',
  // measured on 21B Specialty IPA only — folded into comments below
  'currentlydefinedtypes','strengthclassifications',
]);

// Keys with no column, carrying real content. Folded into `comments` with a
// visible label rather than dropped (plan 00b §1.3). One row affected: 21B.
const FOLD = { currentlydefinedtypes: 'Currently defined types',
               strengthclassifications: 'Strength classifications' };

const num = (v) => {
  if (v === null || v === undefined || v === '') return null;
  const n = Number(v);
  if (Number.isNaN(n)) throw new Error(`Non-numeric vital stat "${v}"`);
  return n;
};
const intOrNull = (v) => { const n = num(v); return n === null ? null : Math.round(n); };

// Free text -> text[] . Two sentinels matter and both were measured:
//   34C.commercialexamples is the literal string "None"  -> SQL NULL, so the
//     card omits the line instead of listing a beer called None.
//   an empty string                                       -> SQL NULL.
const NULLISH = new Set(['', 'none', 'n/a', 'na', '-']);
const splitList = (v) => {
  const s = (v ?? '').toString().trim();
  if (NULLISH.has(s.toLowerCase())) return null;
  const out = s.split(',').map(x => x.trim()).filter(Boolean);
  return out.length ? out : null;
};
const textOrNull = (v) => {
  const s = (v ?? '').toString().trim();
  return s === '' ? null : s;
};

const rows = [], notes = [], seen = new Set();
let withVitals = 0, withoutVitals = 0, withEntry = 0, foldedFields = 0, noExamples = 0;

for (const s of styles) {
  for (const k of Object.keys(s))
    if (!KNOWN.has(k))
      throw new Error(`Unknown field "${k}" on style ${s.number ?? '?'} — add a column or a fold rule to plan 00b §1.3 before ingesting`);

  const code = (s.number ?? '').trim();
  if (!code) throw new Error(`Style missing "number": ${JSON.stringify(s).slice(0, 80)}`);
  if (!/^[0-9]{1,2}[A-Z]$/.test(code)) throw new Error(`Style code "${code}" is not the BJCP <digits><letter> form`);
  if (seen.has(code)) throw new Error(`Duplicate style code ${code}`);
  seen.add(code);

  const og_min = num(s.ogmin),  og_max = num(s.ogmax);
  const fg_min = num(s.fgmin),  fg_max = num(s.fgmax);
  const ibu_min = intOrNull(s.ibumin), ibu_max = intOrNull(s.ibumax);
  const srm_min = num(s.srmmin), srm_max = num(s.srmmax);
  const abv_min = num(s.abvmin), abv_max = num(s.abvmax);

  // Range check ONLY where both bounds exist: 20 specialty styles define none,
  // and that is correct data rather than missing data (plan 00b §1.2).
  const chk = (lo, hi, label) => {
    if (lo !== null && hi !== null && lo > hi)
      throw new Error(`${code}: ${label} min>max (${lo} > ${hi})`);
  };
  chk(og_min, og_max, 'OG'); chk(fg_min, fg_max, 'FG'); chk(ibu_min, ibu_max, 'IBU');
  chk(srm_min, srm_max, 'SRM'); chk(abv_min, abv_max, 'ABV');

  // A style declares vitals as a set or not at all. A half-set means the source
  // is malformed in a way the has_vitals branch would misread.
  const vit = [og_min, og_max, fg_min, fg_max, ibu_min, ibu_max, srm_min, srm_max, abv_min, abv_max];
  const present = vit.filter(v => v !== null).length;
  if (present !== 0 && present !== 10)
    throw new Error(`${code}: ${present} of 10 vital stats present — expected all or none`);
  if (present === 10) withVitals++; else withoutVitals++;

  let comments = textOrNull(s.comments);
  for (const [key, label] of Object.entries(FOLD)) {
    const v = textOrNull(s[key]);
    if (v === null) continue;
    comments = (comments ? comments + '\n' : '') + `${label}: ${v}`;
    foldedFields++;
    notes.push({ code, action: 'folded into comments', field: key });
  }

  const entry = textOrNull(s.entryinstructions);
  if (entry !== null) withEntry++;

  const examples = splitList(s.commercialexamples);
  if (examples === null) {
    noExamples++;
    notes.push({ code, action: 'commercial_examples -> NULL', raw: (s.commercialexamples ?? '').toString().slice(0, 40) });
  }

  rows.push({
    code,
    name:      textOrNull(s.name),
    category:  textOrNull(s.category),
    og_min, og_max, fg_min, fg_max, ibu_min, ibu_max,
    srm_min, srm_max, abv_min, abv_max,
    overall_impression:         textOrNull(s.overallimpression),
    aroma:                      textOrNull(s.aroma),
    appearance:                 textOrNull(s.appearance),
    flavor:                     textOrNull(s.flavor),
    mouthfeel:                  textOrNull(s.mouthfeel),
    comments,
    history:                    textOrNull(s.history),
    characteristic_ingredients: textOrNull(s.characteristicingredients),
    style_comparison:           textOrNull(s.stylecomparison),
    entry_instructions:         entry,
    commercial_examples:        examples,   // array or null -> jsonb in node 8
    tags:                       splitList(s.tags),
  });
}

// Re-assert plan 00b §1's measured probe. These are not soft expectations: a
// mismatch means the file on disk is not the file that was measured.
const expect = (got, want, what) => {
  if (got !== want) throw new Error(`${what}: got ${got}, expected ${want} — re-run plan 00b §1 before ingesting`);
};
expect(rows.length,   116, 'style rows');
expect(withVitals,     96, 'styles with vital statistics');
expect(withoutVitals,  20, 'styles without vital statistics');
expect(withEntry,      30, 'styles with entry instructions');
expect(noExamples,      1, 'styles with no commercial examples');

return [{ json: {
  rows,
  notes,
  stats: {
    styles:         rows.length,
    with_vitals:    withVitals,
    without_vitals: withoutVitals,
    with_entry:     withEntry,
    no_examples:    noExamples,
    folded_fields:  foldedFields,
    warnings:       notes.length,
  },
}}];
```

Each rule, what motivates it, and what it does to the 116 rows:

| Rule | Motivated by | Effect, measured on `styles.json` |
|---|---|---|
| `styles.length !== 116` throw | §1.1 row count | never fires today |
| unknown-key throw | §1.3 — 21B's two extra keys | never fires today; **is the reason 21B was found** |
| `code` regex + duplicate check | §1.2 — 116/116 match, 0 duplicates | never fires today |
| numeric parse + `min > max` | §1.2 — 0 failures | never fires today |
| **all-10-or-none vitals** | §1.2 — 96 with, 20 without | never fires today; guards the `has_vitals` branch |
| `FOLD` → `comments` | §1.3 — content with no column | **1 row changed** (21B), 2 fields folded |
| `NULLISH` → SQL NULL | §1.2 — 34C's literal `"None"` | **1 row** gets `commercial_examples = NULL` |
| `textOrNull` on every prose field | empty string ≠ absent | 0 rows changed today; makes `concat_ws` omission work |

**Three behaviours node 12 depends on:**

1. **One item out, holding the whole 116-row array** — not 116 items.
2. **`commercial_examples` and `tags` are arrays or `null`, never `[]`.** An empty array would
   make `array_to_string` return `''` and `concat_ws` would keep the empty label.
3. **Every absent prose field is `null`, never `''`** — same reason.

---

## §4 — Overlap scoping (§3 Layer 1)

**This source overlaps *How to Brew* topically, and nothing is dropped.**

**Measured 2026-08-12 against the live 447 chunks:** Palmer's chapter 19 (*A Question of
Style*, pp.173–198) is **45 chunks** — 10.1% of the current corpus. Its headings are style
names and recipe names: `Pale Ales`, `Porter`, `Stout`, `Bock`, `Weizen`, `Pilsner`, `Vienna`,
`Barleywine`, `Brown Ales`, `California Common (Steam-type)`, `India Pale Ale`, `Oktoberfest`,
`Pre-Prohibition American Lager`, plus his own recipes. Elsewhere in the book only **4 chunks**
carry "style" in their heading path, and **0 chunks anywhere mention BJCP** — measured.

**Verdict: keep both, unconditionally.** This is README §3.2's category (a) — topical overlap
— not category (b). Palmer explains what a porter *is like to brew*, in his own voice, with a
recipe attached; the BJCP card states what a competition judge should expect to find in the
glass. They are the practitioner's answer and the guideline's answer, and which is correct
depends on the question. An ingest-time deletion is irreversible and untargeted; a query-time
filter is reversible and per-question.

**Expected overlap chunks dropped: 0.**

Two things this section does decide:

- ⛔ **Nothing in this plan may touch Palmer's 45 chapter-19 chunks.** They are book 0a's
  corpus and this is a different source.
- ⚠️ **The representational-duplication rule is satisfied by construction, not by inspection.**
  The one place (b) could occur here is a style's OG range living both as `ref.styles.og_min`
  and as prose in a card. It does — and it is legitimate **only because the card is an
  `INSERT … SELECT` from the row** (§2 node 12). Derived duplication cannot drift. If a later
  edit ever types a number into the card text by hand, that stops being true and this section
  is where the rule was recorded.

**What this source does *not* scope, and why it matters at book 5.** BA 2026 and the BJCP
Study Guide are book 5, and they are where the real scoping choices live: three prose
descriptions of Irish Stout clustering tightly in embedding space is the highest-probability
retrieval defect in the whole plan. This plan's job is to leave that decision a clean one — one
guide, one row per style, one (or two) generated cards, with `guide` and `guide_year` already
in the key so a second guide is rows rather than a rewrite.

---

## §5 — Acceptance numbers

Computed by running §3's parser rules and §2 node 12's generator over §1's measured probe.
Every number labelled.

### 5.1 The rows — identical for all three variants

| Check | Value | Label | Gate |
|---|---|---|---|
| `ref.styles` rows where `guide='BJCP' AND guide_year=2021` | **116** | predicted from §1.1 measured | ⛔ exactly 116 |
| `has_vitals = true` | **96** | predicted from §1.2 measured | ⛔ exactly 96 |
| `has_vitals = false` | **20** | predicted from §1.2 measured | ⛔ exactly 20, and the codes must be §1.2's list |
| `entry_instructions IS NOT NULL` | **30** | predicted from §1.2 measured | ⛔ exactly 30 |
| `commercial_examples IS NULL` | **1** (34C) | predicted from §1.2 measured | ⛔ exactly 1 |
| `history` / `characteristic_ingredients` / `style_comparison` non-null | **116 each** | predicted from §1.1 measured | ⛔ 116 each |
| distinct `tags` values | **60**, 776 total items | predicted from §1.2 measured | informational |
| total `commercial_examples` items | **619** | predicted from §1.2 measured | informational |
| inverted ranges | **0** | predicted from §1.2 measured | ⛔ must be 0 |
| `brew.recipes` rows broken by the import | **0** | measured — the table is empty | must be 0 |

### 5.2 The cards — per variant

| Check | A0 | A | B | Label | Gate |
|---|---|---|---|---|---|
| cards inserted | **116** | **116** | **232** | predicted | exact |
| `chunk_index` range | 0–115 | 0–115 | 0–231 | predicted | dense, no gaps |
| median card tokens | **471** | **679** | **350** | predicted (§1.5) | documented miss of the 200–450 band for A0 and A — argued in §1.5 |
| max card tokens | 895 | 1,222 | 670 | predicted | ≪ bge-m3's 8,192 window (measured); nothing truncated |
| cards over 512 tokens | 36 | 108 | 13 | predicted | documented, §1.5 |
| six cards in context | ~2,826 | **~4,074** ⚠️ | ~2,100 | predicted | A exceeds the ~3,000 budget — a finding, not a failure; the A/B decides |
| `page_from IS NULL` | 116 | 116 | 232 | predicted | ⛔ **all cards**, and ⛔ **0 of the 447 book chunks** |
| `heading_path` non-null | 116 | 116 | 232 | predicted | ⛔ must be all |
| embedding coverage | 116/116 | 116/116 | 232/232 | predicted | ⛔ **100%**, all 1024 dims |
| `is_current` versions, whole corpus | 2 | 2 | 2 | predicted | exactly 2 — Palmer and the styles |
| `kb.ingest_log` rows added per run | **2** | 2 | 2 | predicted | ⛔ must be 2 |
| `kb.documents.authority` | `guideline` | | | predicted | not null |
| `file_sha256` | `b0707bf2…268178` | same | same | measured (§1) | ⛔ identical across all three runs — one version row |
| **corpus share after** | **20.6%** | 20.6% | **34.2%** ⚠️ | predicted | see below |

**Corpus share, and why B's 34.2% is recorded rather than acted on.** After this run the
corpus is Palmer's 447 plus the cards: A0/A give 116/563 = **20.6% predicted**; B gives
232/679 = **34.2% predicted**, which crosses README §3.3's Layer-2 signal of *any document >
25%*. That threshold is about **competition inside a top-6**, and it is measuring a two-document
corpus in which one document is a style guide and the other is a book — there is almost nothing
for them to compete over except style questions, which is precisely what the A/B is measuring
directly and better. At the projected ~3,100-chunk corpus (README §4.2) the same 232 cards are
**7.5% predicted**. **The correct action is to record the number and let Layer 2's retrieval-share
check — which this plan runs in Tier B — decide**, not to shrink the cards to satisfy a
corpus-share proxy at n=2. Standing rule 6: a criterion that does not fit gets argued.

### 5.3 Runtime, so a hung run is recognisable as hung

Derived from book 0a's **measured** 447 embeddings in 4–8 minutes (≈ 0.6–1.1 s/chunk):

| Stage | A0 / A | B | Label |
|---|---|---|---|
| read + hash + parse + validate | < 3 s | < 3 s | predicted |
| upsert 116 rows + assert | < 1 s | < 1 s | predicted |
| demote + clear + generate cards | < 2 s | < 2 s | predicted |
| **embed** | **4 batches, ~1.5–2.5 min** | **8 batches, ~2.5–4.5 min** | predicted |
| promote + log | < 1 s | < 1 s | predicted |
| **total** | **~2–3 min** | **~3–5 min** | predicted |

Past **10 minutes** something is wrong — most likely Ollama cold-loading per batch, which
means `keep_alive: -1` is missing from node 16.

**The whole A/B is therefore three runs of 2–5 minutes plus the probe sets**, which is why
measuring beats arguing here: it is a JSON parse and at most 232 embeddings, no Docling.

### 5.4 Measured — variant B, 2026-08-12

The run that happened. Every §5.1 row gate hit exactly, so the parser and §1's probe agree.

| Check | Predicted | **Measured** | |
|---|---|---|---|
| `ref.styles` rows | 116 | **116** | ✅ |
| `has_vitals` true / false | 96 / 20 | **96 / 20** | ✅ |
| `entry_instructions` non-null | 30 | **30** | ✅ |
| `commercial_examples` null | 1 | **1** | ✅ |
| distinct categories | — | **34** | recorded |
| parser notes | 3 | **3** — 34C → NULL, 21B ×2 folds | ✅ |
| cards inserted | 232 | **232** | ✅ |
| generated `Vital statistics:` lines | 96 | **96** | ✅ |
| malformed labels / `OG 0.000` | 0 | **0** | ✅ |
| `page_from IS NULL` | 232 | **232** | ✅ by design |
| `heading_path` null | 0 | **0** | ✅ |
| embedding coverage | 232/232 | **232/232**, 1024 dims | ✅ |
| median card tokens | 350 predicted | **359 predicted** from measured `length(content)` | +2.6% |
| max card tokens | 670 predicted | **673 predicted** from measured `length(content)` | +0.4% |
| corpus total | 679 | **679** chunks, **0** gaps, **2** `is_current` | ✅ |
| `kb.ingest_log` rows this version | 2 | **2** | ✅ |

**§1.5's chars-per-token calibration held.** Predicting card size from `length(content) /
4.379` came within 3% of what the generator actually produced, which is the only reason
§5.2's variant comparison could be written before any variant existed. It stays a
**predicted** number — no tokenizer ran — but it is now a calibrated one.

⛔ **What this table does not contain is A0 and A.** Two of the three runs §5.5 requires were
never executed, so the comparison the whole section exists for has no data. See the status
block at the top of this plan.

---

## §6 — Test cases

Three tiers, all required, plus the A/B protocol.

### Tier A — pipeline (SQL, deterministic)

**A0 · the rows landed.** Run after node 9, before the cards exist:

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select count(*) rows, count(*) filter (where has_vitals) with_vitals, count(*) filter (where not has_vitals) without_vitals, count(*) filter (where entry_instructions is not null) with_entry, count(*) filter (where commercial_examples is null) no_examples, count(distinct category) categories from ref.styles where guide='BJCP' and guide_year=2021;"
```

Expected: `116 | 96 | 20 | 30 | 1 | 34`.

**A0b · the 20 styles without vitals are the right 20:**

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select string_agg(code, ',' order by code) from ref.styles where guide='BJCP' and not has_vitals;"
```

Expected exactly:
`27A,28A,28B,28C,29A,29B,29C,30A,30B,30C,30D,31A,31B,32A,32B,33A,33B,34A,34B,34C`

**A0c · the five prose fields the row must carry, and the one folded row:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select count(*) filter (where history is not null) history, count(*) filter (where characteristic_ingredients is not null) ingredients, count(*) filter (where style_comparison is not null) comparison, count(*) filter (where tags is not null) tags, count(*) filter (where comments like '%Currently defined types:%') folded from ref.styles where guide='BJCP';"
```

Expected: `116 | 116 | 116 | 116 | 1`.

**A1 · cards, coverage, nulls** — the standing shape, adapted for a source with no pages:

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select d.slug, count(*) chunks, count(e.chunk_id) embedded, count(*) filter (where c.page_from is null) no_page, count(*) filter (where c.heading_path is null or cardinality(c.heading_path)=0) no_heading, min(length(c.content)) min_chars, percentile_disc(0.5) within group (order by length(c.content)) median_chars, max(length(c.content)) max_chars from kb.chunks c join kb.document_versions v on v.id=c.version_id and v.is_current join kb.documents d on d.id=v.document_id left join kb.chunk_embeddings e on e.chunk_id=c.id and e.model='bge-m3' group by d.slug order by 1;"
```

Expected two rows. `bjcp-2021-beer-styles`: chunks = embedded = **116** (A0/A) or **232** (B),
`no_page` = **all of them**, `no_heading` = **0**. `how-to-brew-palmer`: **447 | 447 | 0 | 0**
— ⛔ unchanged, and this is also the check that 0b did not touch book 0a.

Divide `median_chars` by **4.379** to compare against §5.2's predicted token medians.

**A2 · the log has 2 rows per run and a readable parser ledger:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select stage, level, message, detail->>'variant' variant, jsonb_array_length(detail->'notes') notes from kb.ingest_log where version_id=(select id from kb.document_versions where file_sha256='b0707bf268f6e0b85d05534a2e62a9eb2ecc5e674a9a0048f6e55d2a0d268178') order by id;"
```

Expected per run: a `parse | warn` row with `notes = 3` (two folded fields on 21B, one
`commercial_examples -> NULL` on 34C) and a `promote | info` row. The `variant` column must
read the variant just run.

**A2b · read the parser notes once:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select n->>'code' code, n->>'action' action, n->>'field' field from kb.ingest_log, jsonb_array_elements(detail->'notes') n where stage='parse';"
```

Expected: `21B | folded into comments | currentlydefinedtypes`,
`21B | folded into comments | strengthclassifications`,
`34C | commercial_examples -> NULL |`. **Anything else is the parser doing something this
plan did not authorise.**

**A3 · idempotency — re-run the same variant, nothing changes.** Run the workflow twice with
`variant` unchanged and compare:

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select md5(string_agg(content_sha256, ',' order by chunk_index)), count(*) from kb.chunks c join kb.document_versions v on v.id=c.version_id join kb.documents d on d.id=v.document_id where d.slug='bjcp-2021-beer-styles';"
```

⚠️ **The two values must be identical, but this run is *not* fast** — unlike the engine, this
workflow has no dedup short-circuit and deliberately regenerates in place, so it re-embeds
every card (2–5 minutes, §5.3). That is the price of §5.5's requirement that the workflow be
re-runnable, and it is the right trade at 116 rows. **What A3 proves here is determinism, not
speed:** the same input and the same variant produce byte-identical cards.

Also confirm one version row, not three:

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select count(*), max(version), (max(chunker_config)->>'variant') from kb.document_versions where file_sha256='b0707bf268f6e0b85d05534a2e62a9eb2ecc5e674a9a0048f6e55d2a0d268178';"
```

Expected: `1 | <n> | <the variant just run>`. ⛔ **More than one row means node 10's
`ON CONFLICT` is wrong** and the variants are accumulating instead of replacing.

**A4 · corpus totals:**

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select 'chunks', count(*)::text from kb.chunks union all select 'gaps', count(*)::text from kb.chunks c left join kb.chunk_embeddings e on e.chunk_id=c.id and e.model='bge-m3' where e.chunk_id is null union all select 'current', count(*)::text from kb.document_versions where is_current union all select 'dims', (select distinct vector_dims(embedding)::text from kb.chunk_embeddings);"
```

Expected: `chunks 563` (A0/A) or `679` (B) · `gaps 0` · `current 2` · `dims 1024`.
**One row for `dims`** — two means a second model got in and every comparison downstream is
garbage.

**A5 · no card says "OG 0.000", and no card has an empty label.** The whole point of the
`has_vitals` branch and `concat_ws`:

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select count(*) filter (where raw_content ~ E'\nVital statistics: OG') has_vitals_line, count(*) filter (where raw_content ~ '(0\.000|: *$|: *\n)') malformed from kb.chunks c join kb.document_versions v on v.id=c.version_id join kb.documents d on d.id=v.document_id where d.slug='bjcp-2021-beer-styles';"
```

Expected: `has_vitals_line` = **96** (A0/A, and also B — vitals live on the sensory card
only); `malformed` = ⛔ **0**. **Measured 2026-08-12 on variant B: 96 and 0.** ✅

⚠️ **The pattern must be anchored to the generated line, not to the words.** A looser
`raw_content ~ 'Vital statistics'` returns **97**, and the extra hit is not a defect: **25B
Saison's own `entry_instructions` prose ends "…Vital statistics for OG/FG are based on
Standard."** That is BJCP's sentence, faithfully imported onto the context card, and a card
that quotes the phrase is not a card that renders the line. Anchoring on
`\nVital statistics: OG` — the exact shape node 12 emits — separates the two. Recorded
because the loose query was in this plan's first draft and would have read as an off-by-one
in the `has_vitals` branch.

**A5b · spot-check one no-vitals style and one folded style, by eye:**

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select raw_content from kb.chunks c join kb.document_versions v on v.id=c.version_id join kb.documents d on d.id=v.document_id where d.slug='bjcp-2021-beer-styles' and array_to_string(c.heading_path,' > ') like '%34C%';"
```

Must contain **no** `Vital statistics:` line and **no** `Commercial examples:` line. Then the
same for `21B` — must contain `Currently defined types: Belgian IPA, Black IPA, …`.

### Tier B — retrieval (`scripts/ask.sh`, deterministic)

**Baseline first.** The 5 standing questions were recorded at the end of book 0a (§P.4). Run
them again **before** the first 0b run for a same-session baseline, and after every variant.

**The keep/roll-back rule, unchanged and restated:**

| Outcome | Action |
|---|---|
| prior rank-1 chunk still top 3 on all five | **keep**, log the shift |
| falls out of top 6 on **one** | keep, log as a defect |
| falls out of top 6 on **two or more** | ⛔ **roll back** (§7) |

**Positive controls (≥ 3)** — questions the style cards newly make answerable. Every hit must
be `bjcp-2021-beer-styles`:

| Question | Must reach |
|---|---|
| *"what are the vital statistics for a Czech Premium Pale Lager"* | top 3 |
| *"which BJCP category covers wood-aged beer"* | top 3 |
| *"what does the BJCP say a Weissbier should smell like"* | top 3 |

**Retrieval share (§3 Layer 2)** over the 10 questions (5 standing + 3 positive controls + 2
from the A/B set): flag any question where **≥ 3 of 6** results come from one document *it
does not own*. At two documents this becomes a real measurement for the first time — at book
0a it was trivially 6/6 and not a signal.

### The A/B — §5.5's protocol, three runs

⚠️ **The variants cannot coexist.** `kb.document_versions` carries `UNIQUE (file_sha256)`
(verified in P.0) and all three are generated from the same `styles.json`, so they hash
identically. The workflow is built to be **re-run in place** (§2 nodes 10 and 11): each run
demotes, clears, regenerates, re-embeds and re-promotes the same version row.

| Run | Variable under test |
|---|---|
| **A0 → A** | do the five extra prose fields help? |
| **A → B** | does splitting the card help? |

**The probe set — 8 questions, 4 of each kind.** Sensory questions should be indifferent to
the split; context questions are where B wins if it wins at all.

| | Sensory | Context / comparison |
|---|---|---|
| 1 | what should an Irish Stout taste like | what is the difference between a porter and a stout |
| 2 | what aroma is expected in a Dark Mild | where did Dark Mild come from |
| 3 | how should a Doppelbock look and feel in the mouth | what commercial examples are there for Irish Stout |
| 4 | what mouthfeel is right for an Oatmeal Stout | which ingredients are characteristic of a Munich Helles |

**The target codes, verified present in `styles.json`:** Irish Stout **15B**, Dark Mild
**13A**, Doppelbock **9A**, Oatmeal Stout **16B**, Munich Helles **4A**. *Porter vs stout* has
no single target — score it as a hit if a card from **either** family reaches the rank
(20A/13C/9C or 15B/16A/16B/20B/20C), since the question asks for a comparison and
`style_comparison` is the field under test.

Run each with `scripts/ask.sh`, **unfiltered** — no `doc_type` argument. The agent searches
the whole corpus, so filtering to `style_guide` would measure a retrieval path that does not
exist in production.

**Scoring convention, fixed before the run** so it cannot be chosen after seeing the numbers:

- **hit@1** — the top result is a card for the style the question names.
- **hit@3** — such a card appears at rank 1, 2 or 3.
- **In variant B, either card for that style counts as a hit.** The split is being tested as a
  retrieval strategy, not as two independent documents; requiring the "right half" would score
  B against a rule A cannot fail.

**The decision rule, fixed in advance — §5.5's, restated without change:**

| Comparison | Keep the new variant if |
|---|---|
| **A0 → A** | context questions improve on **hit@3** *and* sensory questions do not regress. If the extra fields help nothing, stay at A0 and the split question is moot |
| **A → B** | context **hit@1** improves by **≥ 2 of 4** with no sensory regression — **or** it holds parity, in which case **B wins the tie** |
| **either** | ⛔ any of the 5 standing questions drops its rank-1 chunk out of the top 3 → **reject**, regardless of the style scores |

**Why B wins ties:** at ~350 predicted tokens against ~679 it returns the same answer for half
the context budget. Parity on quality plus half the cost is a win, and it is the one place in
this comparison where the tiebreak is not a judgement call.

**Record all three results, including the losers**, in the table below. A measured negative is
what stops the question being reopened in three months.

| Question | kind | A0 hit@1 | A0 hit@3 | A hit@1 | A hit@3 | B hit@1 | B hit@3 |
|---|---|---|---|---|---|---|---|
| Irish Stout — taste | sensory | | | | | | |
| Dark Mild — aroma | sensory | | | | | | |
| Doppelbock — appearance/mouthfeel | sensory | | | | | | |
| Oatmeal Stout — mouthfeel | sensory | | | | | | |
| porter vs stout | context | | | | | | |
| Dark Mild — origin | context | | | | | | |
| Irish Stout — commercial examples | context | | | | | | |
| Munich Helles — ingredients | context | | | | | | |
| **sensory totals** | | /4 | /4 | /4 | /4 | /4 | /4 |
| **context totals** | | /4 | /4 | /4 | /4 | /4 | /4 |

| Standing question | baseline rank-1 chunk | A0 | A | B |
|---|---|---|---|---|
| diacetyl rest | | | | |
| mash pH | | | | |
| hop timing | | | | |
| pitching rate | | | | |
| acetaldehyde | | | | |

⚠️ **One variable per run.** Change `variant` and nothing else between runs — not the parser,
not the probe questions, not `ask.sh`'s 6/40/50 parameters. If a defect forces a parser change
mid-A/B, the earlier runs are void and the sequence restarts.

### Tier C — agent

⛔ **Not runnable, and this is a decision rather than a skip.** There is no chat agent: WF4
and `tool-search-brewing-knowledge` are both scheduled *after* book 0b (README §1.3 items 6
and 7). Running an agent test against no agent is impossible, not omitted.

**Tier C for this source runs as part of the WF4 build**, and must include these four:

| Type | Question | Pass condition |
|---|---|---|
| new coverage | *"What are the BJCP vital statistics for an Irish Stout?"* | answers with numbers from the winning card, names the BJCP guidelines, `[S…]` markers all resolve |
| **refusal still holds** | *"How much Citra do I have?"* | *"I don't have a tool for that yet"* — ⛔ **the one hard fail**, re-run in every plan |
| citation integrity | any style question | no `[S…]` the tool did not return |
| **no-vitals honesty** | *"What OG should a Wood-Aged Beer have?"* (**33A**, `has_vitals = false` — verified) | ⛔ says the style **defines no vital statistics** — must **not** invent numbers or read them from a neighbouring style. This is the fabricated-numbers failure the closed-book design exists to prevent |
| conflict surfacing | *"Is Palmer's porter the same as the BJCP porter?"* | both attributed — Palmer as `reference`, BJCP as `guideline` (Layer 4) |

**`scripts/stress/tier1_routing.py` is not run for this source.** It measures tool routing
against a system prompt, and there is neither yet. It runs when WF4 is built, where the
knowledge row must read **30/30** and the total must not fall below **73/84**.

---

## §7 — Rollback, stated before the run

**The cards**, if §5.2 fails or Tier B says roll back:

```sql
DELETE FROM kb.document_versions
WHERE file_sha256 = 'b0707bf268f6e0b85d05534a2e62a9eb2ecc5e674a9a0048f6e55d2a0d268178';
-- kb.chunks cascade; kb.chunk_embeddings cascade from chunks; kb.ingest_log cascades
```

This removes the style guide from the corpus entirely and leaves book 0a's 447 chunks
untouched. Confirm with A4: `chunks 447 · gaps 0 · current 1`.

**The rows**, if the import itself is wrong:

```sql
DELETE FROM ref.styles WHERE guide = 'BJCP' AND guide_year = 2021;
```

⚠️ Run the card delete **first**. `ref.styles` has no FK from `kb.chunks` — the cards are
generated, not referenced — so this will succeed with cards still present and leave 116 cards
whose source rows are gone. That is exactly the drift state §4 exists to prevent.
`brew.recipes.style_id` does reference `ref.styles(id)`, but `brew.recipes` is **empty**
(measured), so nothing blocks the delete today. At any later point, check it first.

**Rolling back a *variant* needs no SQL at all** — set `variant` back and re-run. That is the
whole design of §2 nodes 10 and 11, and it is why the A/B is cheap.

**What needs no rollback:** `styles.json` and the workflow JSON in git. Every artefact this
plan produces is reproducible from files on disk.

⛔ **Do not run any of this without deciding to.** It is written here so it exists before it is
needed, not so it can be run casually.

---

## §8 — Run procedure

⛔ **§P must be finished first.** Steps 1–4 below assume the 5 standing questions already have
a recorded baseline.

0. **Baseline, same session.** Re-run the 5 standing questions (§P.4) and record. This is the
   comparison every later step uses; a baseline from a different session is a different
   measurement.
1. **Verify the source file is the one that was measured:**
   ```bash
   sha256sum "shared/rag-files/pending/styles.json"
   ```
   Must be `b0707bf268f6e0b85d05534a2e62a9eb2ecc5e674a9a0048f6e55d2a0d268178`. If it is not,
   **stop and re-run §1's probe** — every acceptance number in §5 is computed from that file.
   ⛔ Standing rule 7's hyphen probe is **not** run: this is JSON, not a PDF (§0).
2. **Build the workflow** — §2, in node order, wiring per §2.1. Leave `variant` at `A0`.
3. **Export and commit before the first run** (standing rule 4):
   ```bash
   docker exec n8n n8n export:workflow --id=<STYLES_ID> --pretty --output=/demo-data/workflows/ingest-bjcp-styles.json && docker exec n8n chown 1000:1000 /demo-data/workflows/ingest-bjcp-styles.json
   ```
4. ⛔ **Stop before embedding — run 1 (A0).** Execute the workflow. When it reaches
   `Assert style rows` (node 9), open its output and read it **before** the loop starts:

   | Field | Must read |
   |---|---|
   | `rows` | **116** |
   | `with_vitals` / `without_vitals` | 96 / 20 |
   | `with_entry` | 30 |
   | `no_examples` | 1 |
   | `inverted_ranges` | 0 |

   The node throws on a mismatch, so a green node is the check. Then let it reach
   `Generate style cards` and stop to run **A0, A0b, A0c, A5, A5b** (§6) before the embedding
   loop consumes GPU time on wrong cards.
5. **Let it finish** — ~2–3 minutes predicted. ⛔ **Do not chat with the assistant during any
   run** (standing rule 3): embedding saturates the GPU, and node 11 has demoted the style
   version, so style questions would return nothing anyway.
6. **Run A1–A4** and record. Then run **the 8 A/B questions plus the 5 standing questions**
   and fill the `A0` columns of §6's two tables.
7. **Run 2 (A).** Change **only** `variant` to `A`. Re-run. Repeat step 6 into the `A` columns.
8. **Apply the A0 → A half of the decision rule.** If A loses, record it and **stay at A0** —
   the split question is then moot and the A/B ends here, with the negative result written
   into §6's table. That is a valid outcome, not a failed plan.
9. **Run 3 (B).** Change **only** `variant` to `B`. Re-run. Repeat step 6 into the `B` columns.
   Note A4 now expects `chunks 679`.
10. **Apply the A → B half of the decision rule**, including the tiebreak. Then set `variant`
    to the winner and **run once more**, so the corpus ends in the winning state rather than
    in whichever variant happened to run last.
11. **Run A3** (idempotency / determinism) against the winning variant, and confirm exactly one
    `kb.document_versions` row for this `file_sha256`.
12. **Re-export and commit** with the variant and the measured numbers in the message. Paste
    §6's completed tables — **all three variants, losers included** — into this file.
13. **Leave `styles.json` in `pending/`.** Unlike a PDF there is no *"processed"* end state
    here: the file is the source of truth for a table that gets regenerated, and A3 reads from
    `pending/`. Move it only when book 5 rewires the styles path.
14. Tick 0b's row in [README §9](README.md) and record the winning variant beside D32b.

---

## §9 — What this source does to WF4

WF4 does not exist yet — it is built after this plan. So this section is a **specification for
the build**, not an edit to a running workflow. Three concrete items.

**1. The system prompt sentence, written de-enumerated from the first keystroke.** Transcribed
verbatim from [`archive/phase2/03-wf4-design.md`](../archive/phase2/03-wf4-design.md) §6 with
exactly one substitution — this sentence, which must read:

> *"You answer from that brewer's library — a collection of brewing books, style guidelines
> and practitioner articles — not from your own memory."*

⛔ **Not** *"…John Palmer's How to Brew and the BJCP 2021 Style Guidelines…"*. A prompt that
names its sources is false the moment a third one lands, and enumerating a growing corpus
inside a token-budgeted prompt is a maintenance liability. Written this way once, every later
source costs **zero** prompt edits.

**2. The tool's passage header must surface `authority`, and must not rank on it.**
`nlq.search_knowledge` already returns the column (verified in P.0). After this plan the corpus
holds two distinct values — `reference` (Palmer) and `guideline` (BJCP) — so the header
formatter has something real to distinguish for the first time. It should let the model write:

> *"The BJCP guidelines specify an OG of 1.036–1.044 for Irish Stout; Palmer describes the
> style in more practical terms."*

⛔ **`authority` must never enter ranking**, in the tool or in the SQL. Ranking by authority
suppresses the disagreement the design exists to surface, and does it invisibly — you would
never see the passage that lost. It is the rule most likely to be violated later in good faith
(*"BJCP is the guideline, boost it for style questions"*).

**3. `lookup_bjcp_style` is Phase 3b, and this plan fixes one sentence of it in advance.**
`ref.styles` is unreachable by the agent until an `nlq` view or function exposes it —
`n8n_agent` holds rights on `nlq` and nothing else, and `nlq` currently contains exactly two
functions (verified in P.0). When that function is built:

> ⛔ **It must branch on `has_vitals` and, when false, say explicitly: *"this style defines no
> vital statistics."*** 20 of 116 styles are in that state (measured, §1.2), and a model handed
> `og_min = null` renders **"OG 0.000"** without hesitating. The generated column exists for
> this one purpose; do not trust null handling in the SQL, in the tool, or in the prompt.

**What does not change:** `numCtx` 12288, top-6, `contextWindowLength` 6, the citation
contract, the personal-scope refusal sentence. Corpus size does not enter the context budget —
six chunks is six chunks whether the corpus is 447 or 3,100. **Card *width* does**, which is
why §5.2 records six-cards-in-context for each variant and why the A/B is worth three runs.

---

## Exit — 0b is done when

- [ ] §P's five boxes are ticked — launcher ✅ and exports ✅; **A3, A5 and the standing-question baseline still open**
- [x] `ingest-bjcp-styles` exists, **22 nodes**, exported and committed
- [x] `ref.styles` holds **116 BJCP 2021 rows**; A0/A0b/A0c pass exactly — measured 2026-08-12
- [x] the 20 no-vitals styles are the right 20 and `has_vitals` reads false on all of them — the code list matches §1.2 character for character
- [x] 21B's two folded fields and 34C's NULL commercial examples are visible in `kb.ingest_log` and nowhere else surprising (A2b) — exactly 3 notes, exactly the predicted 3
- [ ] ⛔ all three A/B runs completed and **all three results recorded, losers included** — **only B ran**
- [x] the deployed variant is `is_current` with 100% embedding coverage at 1024 dims — **but deployed ≠ won**, see the row above
- [x] *How to Brew* is still **447 chunks, 0 gaps** — 0b touched nothing of book 0a (A1)
- [ ] the 5 standing questions pass the keep rule against the §8 step 0 baseline
- [x] no card contains `OG 0.000` or an empty label (A5) — 96 generated vitals lines, 0 malformed
- [ ] D32b is recorded in README §9 with the winning variant

**Book 1 is not unblocked yet.** Water needs a standing-question baseline to regress against,
and there is none: 0a's Tier B was never recorded and the corpus has changed twice since.
Running the 5 questions once — against today's 679-chunk corpus — is the cheapest way to
unblock it, and it is the same command set §P.4 already lists.
