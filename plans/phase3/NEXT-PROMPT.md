# Prompt for the next session

Paste everything below the line into a fresh Claude Code session started in
`/home/gorenyember/AI Homebrew Assistant`.

---

Read `@plans/phase3/README.md` (the contract) and `@plans/phase3/00b-styles.md` (the most
recent worked example of a per-source plan, including its §P prerequisite block).

**Two things, in order.** First walk me through **closing the three open items from books 0a
and 0b** — the evidence that was never recorded, spelled out below. Then write me the
detailed plan for **book 1 — Water** at `plans/phase3/01-water.md`.

Follow README §6 exactly for the Water plan: the nine sections in order (§0 verdict · §1
probe · §2 node by node · §3 cleaning profile · §4 overlap scoping · §5 acceptance numbers ·
§6 three tiers of tests · §7 rollback · §8 run procedure · §9 WF4 impact), plus the seven
standing rules. Three of those rules matter most here:

- **Rule 1, measure then plan.** Water is a PDF, so §1 is a **real Docling probe** — submit
  it to the live service with the engine's exact ten form fields and measure before writing
  anything. Raw chunk count, chunks/page, median/max/p25/p75 tokens, count under 30, count
  over 512, chunks with no `page_from`, **the top 20 headings by frequency**, the front-matter
  page range, and three real chunks verbatim.
- **Rule 7, the hyphen probe.** Run `./scripts/hyphen-probe.sh` on the Water PDF before
  planning the launcher. A prior measurement found **5 at-risk sites** — pH `5.6-6.0`,
  `(65-70°C)`, `0.005-0.010`, `50-70%` — but **re-run it and read every site**; the output is
  a draft and table columns produce false positives.
- **Rule 5.** Every number labelled `predicted` or `measured`. No unlabelled numbers.

**Write it as a build-from-nothing document** for anything new, and as a *parameterisation*
for what already exists — Water is the first book that genuinely exercises D30's promise that
a new source is one Set node, not a new workflow. If the plan ends up changing more than the
launcher's mapper and (possibly) one cleaning-profile branch, say so loudly, because that
means the split does not hold.

## What is already true — verify, don't assume

Measured against the live stack on 2026-08-12. **Re-verify rather than trusting this list.**

- **`kb.chunks` holds 679 rows** — *How to Brew* **447** and BJCP style cards **232**.
  0 embedding gaps, 1024 dims, **2** `is_current` versions.
- **`ref.styles` holds 116 BJCP 2021 rows** — 96 with vitals, 20 without, 30 with entry
  instructions, 1 with null commercial examples, 34 categories.
- `kb.documents.authority` is in use with two values: `reference` (*How to Brew*) and
  `guideline` (the style guide). Water is **`reference`**.
- **Three n8n workflows exist**, all exported and committed:

  | Workflow | id | Nodes |
  |---|---|---|
  | `wf1-ingest-book` — the engine | `NoNCV2mkQEppWP7O` | 26 live + **1 orphan, see below** |
  | `ingest-how-to-brew` — launcher | `BAe1fP1g7ZUsbIaq` | 2 |
  | `ingest-bjcp-styles` — styles | `Ejf3ESE3SK1XBqe3` | 22 |

- Postgres nodes use the **`Postgres account`** credential. `n8n_agent` is the read-only
  agent role and **cannot see `kb`** — never pick it on a write node.
- There is **no WF4 and no search tool yet**, so Tier C is not runnable for any source. That
  is a decision, not a skip, and the Water plan must say so in §6.

## Close the three open items first

Put these at the top of the Water plan as a prerequisite block, in this order, and walk me
through them before starting Water's own probe. **The order is forced** — see the ⚠️ under
item 3.

### 1 · A5 — wire node 26's `$5`, before any new ingest

`wf1-ingest-book`'s `Log ingest summary` still lacks its fifth query parameter, so
`detail->'repairs'` is absent from `kb.ingest_log`. This was already missed once: *How to
Brew* was genuinely re-ingested on 2026-08-12 — a real Docling run, 447 chunks reproduced
with an identical 36-drop ledger — and the repair ledger still came back empty.

Query Parameters must read, positionally:

```
={{ [ $('Ensure doc + version').first().json.version_id, JSON.stringify($('Clean + normalise').first().json.stats), JSON.stringify($('Clean + normalise').first().json.drops), JSON.stringify($json), JSON.stringify($('Clean + normalise').first().json.repairs) ] }}
```

and the `clean` row's `detail` builds as
`jsonb_build_object('stats', $2::jsonb, 'drops', $3::jsonb, 'repairs', $5::jsonb)`.

⭐ **Do this before Water's ingest, not after.** Water is the next real ingest and it has 5
hyphen repairs of its own; if `$5` is still missing then, the same evidence is lost a second
time and the only way back is another 10-minute re-ingest.

### 2 · A3 — watch the launcher short-circuit, live

⚠️ **This cannot be checked retroactively.** A dedup short-circuit writes nothing — no chunks,
no log row — so the database cannot tell you whether it ever happened. Run
`ingest-how-to-brew` and watch: it must end at `Already ingested — stop` in **seconds, not
minutes**. Fingerprint before and after must be identical:

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select md5(string_agg(content_sha256, ',' order by chunk_index)), count(*) from kb.chunks;"
```

If it instead runs a full Docling conversion, the dedup branch is broken and **Water would
silently duplicate rather than dedup** — stop and fix it before book 1.

### 3 · The card-format A/B — run A0 and A, then settle D32b

Only variant **B** was ever executed, so B is deployed **by default, not by measurement**.
`kb.ingest_log` holds one `parse` row for the styles version, not three. D32b is open.

Run it per `00b-styles.md` §6 and §8 steps 6–10: set the `variant` field on
`ingest-bjcp-styles`'s `Card variant` node to `A0`, re-run, record; then `A`, re-run, record;
then set the winner and run once more so the corpus ends in the winning state. Each cycle is
~2–5 minutes. **Change nothing else between runs** — one variable.

- The decision rule is **already fixed in advance** in README §5.5 and restated in `00b` §6.
  **Do not restate it in a way that changes it.**
- **Record all three results including the losers.** A measured negative is what stops the
  question being reopened in three months.
- The 8-question probe set and the scoring convention are in `00b` §6 — including that in
  variant B either card for the style counts as a hit.

⚠️ **This is why the order is forced: the A/B changes the corpus, so the standing-question
baseline below cannot be taken until the winner is deployed.** Take it first and book 1 is
measured against a corpus that no longer exists.

### 4 · The Tier B baseline — the actual blocker for book 1

There is **no recorded baseline anywhere**, and the corpus has changed twice since book 0a.
Every later source's keep/roll-back rule compares a prior rank-1 chunk against a new one, and
there is no prior. Five commands, run against the **winning variant's** corpus:

```bash
./scripts/ask.sh "diacetyl rest temperature and timing for lagers"
./scripts/ask.sh "how mash pH affects conversion and how to adjust it"
./scripts/ask.sh "when to add hops for bittering vs aroma"
./scripts/ask.sh "pitching rate and rehydrating dry yeast"
./scripts/ask.sh "my beer tastes of green apple, what causes acetaldehyde and how do I fix it"
```

For each, record **the rank-1 chunk's heading and page**, the on-target count out of 6, and
the rank of the first correct hit. Two have known expected results from an earlier
measurement and act as a correctness check on the corpus itself: **Q1 should put
`10.4 Yeast Starters and Diacetyl Rests` (p.98) at rank 1**, and **Q3 should put
`Bittering` / `Flavoring` / `Finishing` (all p.41) at ranks 1–3**. Q2, Q4 and Q5 have no
prior — whatever they return *is* the baseline.

**Write the table into `00b-styles.md` §6**, labelled `measured` with the date, and tick the
README §9 status board.

### 5 · Housekeeping, while you are in there

- ⚠️ **`wf1-ingest-book` carries an orphaned `Clean + normalise1` node** — no incoming or
  outgoing connections, and its code **differs** from the live `Clean + normalise`. It is
  harmless to execution but it is a second, divergent copy of the cleaning profile sitting in
  tracked JSON, which is exactly the drift the schema rules forbid. Delete it in the UI and
  re-export so the engine is 26 nodes as documented.
- `n8n/demo-data/workflows/` still holds four JSONs describing workflows that do not exist:
  `wf1-howtobrew.json`, `wf2-digestion.json`, `tool-search-brewing-knowledge.json`,
  `tool-find-batches.json`. Clear them — but **move `wf4-chat-agent.json` into `backup/`
  rather than deleting it**: it is one of three surviving copies of system prompt v3, which
  the WF4 build needs verbatim. Say where it went in the commit message.

## What book 1 is, and is not

**Is:** *Water — A Comprehensive Guide for Brewers* (Palmer & Kaminski, 273 pages), at
`shared/rag-files/pending/john_palmer_colin_kaminski-water_a_comprehensive_g.pdf`, through the
existing engine with a new **2-node `ingest-water` launcher**, `profile: book`,
`authority: reference`, `doc_type: book`. The container path is
`/data/shared/rag-files/pending/…` — n8n does not see the host path.

**Is not:** a new workflow, a new cleaning profile, or a schema change. If the probe says
otherwise, that is a finding worth arguing in §0 — not a reason to quietly build one.

## The things most likely to go wrong

- ⛔ **Nothing in Water's plan may drop a Palmer chunk.** Palmer's chapter 15 is the shallow
  half of the water pair and **measured: his chapter 19 alone is 45 chunks**. README §3.2's
  rule is that topical overlap is kept unconditionally — the 20-page answer and the 273-page
  answer are different answers, and which is correct depends on the question. §4 must say
  **expected overlap chunks dropped: 0** and explain why.
- **This is the first source where retrieval share is a real measurement.** At one document it
  was trivially 6/6; at two it was nearly so. With three documents, README §3.3's Layer-2
  check — *≥ 3 of 6 from one document on a question it does not own* — finally discriminates.
  Run it and record it, even if it fires nothing.
- **Corpus share becomes meaningful too.** Water at a predicted ~490 chunks against a ~1,170
  total is ~42%, which crosses the 25% signal. Expect it, argue it rather than tuning it
  (standing rule 6), and remember Layer 3 is the designated fix and is built **only** when
  Layer 2 fires — not when the proxy does.
- **The front-matter page range and `extra_drop_regex` are per-book constants** and must come
  from the probe, not from *How to Brew*'s values. `front_matter_max_page = 6` is a fact about
  Palmer's PDF, not about books.
- **`text_repairs` entries that match nothing throw**, by design. Every pair must come from
  the probe output for *this* file.

## How to work

Verify claims against the live stack rather than trusting this prompt or the plan documents —
both have been wrong before, including in ways that cost a re-ingest. `docker compose` runs
from this checkout only, never a worktree. **Do not ingest or embed anything while I am
chatting with the assistant** — embedding saturates the GPU. Do not run destructive SQL;
write it in §7 and let me trigger it. Export and commit every workflow JSON before running
it, not after.
