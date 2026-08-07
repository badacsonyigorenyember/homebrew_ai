# Plan 02 — the retrieval gate, and closing Phase 1

**Status:** WF1 built and run ✅ · mechanical criteria 4/5 ✅ · **Next:** §4 the gate ·
**Blocks:** Phase 2 (WF4 chat agent), and every phase after it
**Written:** 2026-08-01 · **Prereqs:** `01a-wf1-build-guide.md` complete ✅

Companion to `01-wf1-ingest-document.md` §7. That file says *what* the gate is;
this one is the command-by-command *how*, plus the close-out chores that actually
end Phase 1.

**Target:** decide — with evidence, not vibes — whether the 447 chunks of
*How to Brew* are good enough to build a chat agent on top of. Then close Phase 1.

---

## 0. Where you are — verified live 2026-08-01

| Check | Value | |
|---|---|---|
| `kb.chunks` total | **563** (116 BJCP + 447 book) | ✅ |
| Embedding gaps (`bge-m3`) | **0** | ✅ |
| `is_current` versions | **2** (BJCP v1, book v1 = id 40) | ✅ |
| Book chunks | 447 · median 291 tok · min 30 · max 524 | ✅ |
| `under_30` / `no_heading` / `no_page` | **0 / 0 / 0** | ✅ |
| WF1 in n8n | `HowToBrew`, id `fVLL8o9qwpyXpmPs` | ⚠️ **not in the repo** |
| PDF location | still `pending/` — node 26 was skipped | ⚠️ |
| `kb.ingest_log` | **empty** — node 16 was never built | ⚠️ |

**447, not the 448 plan 01 §5 predicted.** One extra chunk was dropped. The reason
is **not recoverable** — the drop ledger would have been in `kb.ingest_log` and node
16 was skipped. Don't chase it (§7.4).

**⚠️ WF1 exists only inside the n8n container's database.** One `docker compose down
-v` and the build guide is the only surviving copy. §7.1 is the first chore for a
reason.

---

## 1. The one new tool — `scripts/ask.sh`

`nlq.search_knowledge` takes `p_query_embed vector(1024)`. You cannot type a question
into psql — the query has to be embedded by `bge-m3` first, and the resulting 1024
floats handed to Postgres as a pgvector literal. That two-step is the whole reason
this gate needs a script instead of a SQL snippet.

Save as `scripts/ask.sh`, `chmod +x`:

```bash
#!/usr/bin/env bash
# ask.sh "<question>" [doc_type] — embed with bge-m3, then call nlq.search_knowledge.
# doc_type is optional: 'book' | 'style_guide'. Omit to search the whole corpus.
set -euo pipefail
Q="$1"; DT="${2:-}"
EMB=$(curl -s http://localhost:11434/api/embed \
        -d "{\"model\":\"bge-m3\",\"input\":$(jq -Rn --arg q "$Q" '$q'),\"keep_alive\":-1}" \
      | jq -c '.embeddings[0]')
[ "$(echo "$EMB" | jq 'length')" = "1024" ] || { echo "bad embedding" >&2; exit 1; }
DTSQL=$([ -n "$DT" ] && echo "'$DT'" || echo NULL)
QESC=$(echo "$Q" | sed "s/'/''/g")
echo "=============================================================="
echo "Q: $Q"
echo "=============================================================="
docker exec -i supabase-db psql -U postgres -d postgres -X -q <<SQL
\pset format aligned
\pset border 2
SELECT row_number() OVER () AS n, doc_slug, page_from AS pg,
       round(score::numeric,4) AS score,
       left(array_to_string(heading_path,' > '), 55) AS heading
FROM nlq.search_knowledge('$QESC', '$EMB'::vector, 6, 40, 50, 'bge-m3', $DTSQL);
\pset format unaligned
\pset tuples_only on
SELECT E'\n--- ' || row_number() OVER () || '. [' || doc_slug || ' p.' ||
       COALESCE(page_from::text,'?') || '] ' || array_to_string(heading_path,' > ') ||
       E'\n' || left(regexp_replace(raw_content, '[[:space:]]+', ' ', 'g'), 420)
FROM nlq.search_knowledge('$QESC', '$EMB'::vector, 6, 40, 50, 'bge-m3', $DTSQL);
SQL
```

Three things it does deliberately:

- **`jq -Rn --arg`** builds the JSON string rather than interpolating it. Questions
  contain apostrophes (`Palmer's`) and quotes; naive interpolation produces malformed
  JSON and a confusing 400.
- **It prints twice** — a ranked summary table first, then the snippets. You judge
  from the table (is the *heading* right?) and confirm from the snippets. Reading six
  400-char blocks cold is how you lose the thread.
- **`keep_alive: -1`** keeps `bge-m3` resident, same as WF1. Query embedding is ~40 ms
  warm and ~2 s cold; you are about to do this a dozen times.

The parameters `6, 40, 50` are `p_limit`, `p_candidates`, `p_rrf_k` — the §3.4
defaults. **Do not tune them during the gate.** You are measuring the corpus, not the
retrieval function. Tuning comes after, and only if §6 sends you there.

**Verify** — this must print a table of 6 rows, all `how-to-brew-palmer`:

```bash
./scripts/ask.sh "diacetyl rest temperature and timing for lagers"
```

---

## 2. Mechanical criteria — 4 of 5 already pass

Plan 01 §7's checklist. Run these to confirm nothing drifted; the expected values are
**measured**, not predicted.

### 2.1 Chunk quality — expect `447 | 30 | 291 | 524 | 4 | 0 | 0 | 0`

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select count(*) chunks, min(token_count) min_tok, percentile_disc(0.5) within group (order by token_count) median, max(token_count) max_tok, count(*) filter (where token_count > 512) over_512, count(*) filter (where token_count < 30) under_30, count(*) filter (where heading_path is null or cardinality(heading_path)=0) no_heading, count(*) filter (where page_from is null) no_page from kb.chunks c join kb.document_versions v on v.id=c.version_id where v.source_filename like 'how_to_brew%';"
```

`under_30`, `no_heading`, `no_page` all **0** — three criteria met. `over_512` is 4;
see §3, which is not the story plan 01 tells.

### 2.2 Corpus health — expect `chunks 563 · gaps 0 · current 2`

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select 'chunks', count(*)::text from kb.chunks union all select 'gaps', count(*)::text from kb.chunks c left join kb.chunk_embeddings e on e.chunk_id=c.id and e.model='bge-m3' where e.chunk_id is null union all select 'current', count(*)::text from kb.document_versions where is_current;"
```

`gaps 0` is the 100%-coverage criterion. `current 2` is correct — one per *document*,
not one globally; `promote_version` scopes the flip to the document.

### 2.3 Embedding width — expect `1024`

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select distinct vector_dims(embedding) from kb.chunk_embeddings;"
```

One row. Two rows means a model mixed in and every downstream comparison is garbage.

### 2.4 ⬜ Idempotency — the one criterion not yet proven

The §7 criterion is *"re-running WF1 on the same file inserts nothing."* The file is
still in `pending/`, so no move is needed first. Record the fingerprint, re-run, compare:

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select md5(string_agg(content_sha256, ',' order by chunk_index)), count(*) from kb.chunks c join kb.document_versions v on v.id=c.version_id where v.source_filename like 'how_to_brew%';"
```

```bash
docker exec -e N8N_RUNNERS_BROKER_PORT=5699 -e N8N_RUNNERS_BROKER_LISTEN_ADDRESS=127.0.0.1 n8n n8n execute --id=fVLL8o9qwpyXpmPs
```

**Verify:** the run finishes in **seconds, not minutes** — that is the actual signal.
It must stop at `Already ingested — stop`. If it sits there for four minutes it went to
Docling, which means the dedup branch is broken regardless of what the row counts say.
Then re-run the fingerprint query: **both values unchanged**, and §2.2 still reads 563.

The broker-port override is required while the n8n server is up — see memory.

---

## 3. ⚠️ The over-512 chunks — plan 01 §6 is wrong about why

Plan 01 §6 says the 4 over-512 chunks are an artifact of `contextualize()` prepending
the heading path *after* the chunker packed to `max_tokens`, and amends the criterion to
score against `raw_text`. **Measured 2026-08-01, both halves of that are wrong.**

`bge-m3` token counts, measured by re-embedding the stored text and reading Ollama's
`prompt_eval_count` (includes 2 special tokens):

| `chunk_index` | Docling `num_tokens` | measured `raw_content` | measured `content` | heading overhead |
|---|---|---|---|---|
| 369 | 524 | **527** | 541 | +14 |
| 65 | 521 | **529** | 539 | +10 |
| 376 | 519 | **530** | 539 | +9 |
| 272 | 513 | **542** | 550 | +8 |

Calibrated against 8 random mid-size chunks, `num_tokens` tracks the **raw** count
(mean delta ~0, scatter ±16), *not* the contextualized one. Contextualization adds
**+6 to +21** tokens on top of the stored `token_count` — it is not included in it.

Two consequences:

1. **The stored `token_count` understates what gets embedded** by ~10 tokens across
   the board. Harmless, but don't read `token_count` as "tokens sent to the embedder".
2. **The amended criterion still fails.** Raw text alone is 527–542 on these four, so
   *"zero chunks whose `raw_text` exceeds 512"* is **not** satisfied either. Plan 01's
   §11 deferred item needs rewriting a second time.

**Why it actually happens — all four contain markdown tables:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select c.chunk_index, c.token_count, (length(c.raw_content) - length(replace(c.raw_content,'|',''))) pipe_count, left(array_to_string(c.heading_path,' > '),40) heading from kb.chunks c join kb.document_versions v on v.id=c.version_id where v.source_filename like 'how_to_brew%' and c.token_count > 512 order by c.token_count desc;"
```

Expect pipe counts of 48/52/64/128 — recipe tables and a water report.
`HybridChunker` will not split a table mid-row, so a table whose serialization exceeds
the budget emerges oversized. That is correct behaviour: splitting it would produce two
half-tables, each worse than one long one.

**This is not a defect, and it is not worth fixing.** The real risk a token cap guards
against is *silent truncation at embed time*, and the widest chunk here is 550 against
bge-m3's **8192**-token window. Restate the criterion as what you actually care about:

> **≤ 1% of chunks exceed `max_tokens`, every one of them explained (unsplittable
> table), and no chunk's embedded `content` approaches the embedder's context window.**

Scored: 4/447 = **0.9%**, all tables, max 550 / 8192. ✅ Met.

---

## 4. The gate — five questions

This is the real Phase 1 exit and the only part of this plan that needs *you*. Run each,
read the top 6, and answer one question: **would I have picked these myself?**

```bash
./scripts/ask.sh "diacetyl rest temperature and timing for lagers"
./scripts/ask.sh "how mash pH affects conversion and how to adjust it"
./scripts/ask.sh "when to add hops for bittering vs aroma"
./scripts/ask.sh "pitching rate and rehydrating dry yeast"
./scripts/ask.sh "my beer tastes of green apple, what causes acetaldehyde and how do I fix it"
```

Each is answerable from a known chapter, so a miss is a **chunking defect, not a corpus
gap** — that is the whole design of this question set.

| # | Question | Should retrieve from |
|---|---|---|
| 1 | diacetyl rest | Ch 10 — Brewing Lager Beer |
| 2 | mash pH | Ch 15 — Understanding the Mash pH |
| 3 | hop timing | Ch 5 — Hops |
| 4 | pitching / rehydrating | Ch 6 — Yeast |
| 5 | acetaldehyde | Ch 21 — Is My Beer Ruined? |

### How to score it

Per question, count how many of the 6 you would have chosen. Record it:

| # | on-target /6 | rank of first correct hit | verdict |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

**Pass = every question has a genuinely useful chunk at rank 1 or 2, and ≥ 3 of 6
on-target.** Rank matters more than count: the agent gets all six, but a 12B model
weights the top of the list heavily, and §7.5 budgets only ~3,000 tokens for them.

**Two already run 2026-08-01, for calibration:**

- **Q1** → rank 1 and 3 are `10.4 Yeast Starters and Diacetyl Rests` (p.98), rank 2
  `10.5 When to Lager`. Ranks 5–6 drift to a lager recipe and a protein rest. **4/6,
  first hit rank 1.** Clear pass.
- **Q3** → ranks 1/2/3 are `Bittering`, `Flavoring`, `Finishing` (all p.41), ranks 4/6
  the boil-procedure hop additions. **6/6, first hit rank 1.** As good as this gets.

**No BJCP style cards appeared in either.** That is the D19 failure mode being
displaced by the new corpus, which is exactly what Phase 1 was for.

---

## 5. The control question

```bash
./scripts/ask.sh "what temperature for a single infusion mash"
```

Plan 01 §7 calls for this specifically: it must return **process text, not style cards**.

**Run 2026-08-01 — passes the stated test, but read the result carefully.** No style
cards. However rank 1 is `American Pale Ale` (p.180) and ranks 3/4/6 are recipes with
`Mash Schedule` tables; the actual explanation, `16.1 Single Temperature Infusion`
(p.149), lands at **rank 2**.

That is a pass, but it is the **soft spot to watch**: recipe chunks are mostly markdown
table scaffolding — long pipe-and-dash separator runs with little prose — and they
compete well on FTS for terms like "mash" and "single". If the agent later cites recipe
tables when asked for explanations, this is the cause, and §6's `doc_type` filter or a
table-scaffolding cleanup is the fix. **Do not act on it now.** One observation is not
a defect; note it and re-check during the Phase 3 eval.

---

## 6. If the gate fails — fix in this order

Do not jump to the bottom of this list. Each step is cheaper and more likely than the one
after it, and the expensive ones require a re-ingest that invalidates everything above.

| # | Symptom | Fix | Cost |
|---|---|---|---|
| 1 | Right chapter, wrong chunk within it | Nothing — this is fine. The agent gets 6 | — |
| 2 | Style cards outrank book prose | Pass `doc_type='book'` as `ask.sh`'s 2nd arg to confirm, then have the WF4 tool expose the filter | minutes |
| 3 | Junk (TOC, references, tables of nothing) in the top 6 | A cleaning rule under-matched. Fix node 13's regex, force a re-ingest | ~10 min + re-embed |
| 4 | Relevant text exists but never ranks | Raise `p_candidates` 40 → 80, re-test. Cheapest retrieval win available (§3.4) | seconds |
| 5 | Answers split across chunk boundaries mid-explanation | Re-chunk at a different `max_tokens`. **Last resort** — full re-ingest, new embeddings, and every number in §2 changes | ~10 min + 5 min embed |

**Forcing a re-ingest** (needed for 3 and 5) means defeating the dedup branch, since
the `file_sha256` is unchanged. Delete the version and let WF1 rebuild it:

```bash
docker exec supabase-db psql -U postgres -d postgres -c "delete from kb.document_versions where id = 40;"
```

`kb.chunks` and `kb.chunk_embeddings` cascade from `version_id`. The BJCP version is
untouched. Confirm §2.2 reads `chunks 116` before re-running WF1.

---

## 7. Close-out chores

### 7.1 Export WF1 to the repo — do this first

WF1 is not in git. The repo convention (and memory) is **edit the file, then import** —
but the file does not exist yet, so export once to create it:

```bash
docker exec n8n n8n export:workflow --id=fVLL8o9qwpyXpmPs --pretty --output=/demo-data/workflows/wf1-howtobrew.json && docker exec n8n chown 1000:1000 /demo-data/workflows/wf1-howtobrew.json
```

**Verify** it landed in the working tree and holds all ~27 nodes:

```bash
jq '.name, (.nodes|length)' n8n/demo-data/workflows/wf1-howtobrew.json
```

Then commit it alongside this plan. From here on, `wf1-howtobrew.json` is the source of
truth, not the browser editor.

### 7.2 Move the PDF to `processed/`

Node 26 was skipped, which plan 01a explicitly allowed — the folder is the human record
of what is ingested, and you only want to move the file once the gate passes. Do it
**after** §4, and after §2.4 (the idempotency re-run reads from `pending/`):

```bash
mv "shared/rag-files/pending/how_to_brew_john_palmer.pdf" shared/rag-files/processed/
```

`file_sha256` stays authoritative for dedup either way (deprecation list #8).

### 7.3 Tick deprecation #7 — already satisfied

The n8n Code-node heading-splitter is gone: `n8n list:workflow` returns only `Digestion`
and `HowToBrew`, and neither contains it. No work, just flip the ⬜ in §12 of the
architecture doc.

```bash
docker exec n8n n8n list:workflow
```

### 7.4 Accept 447, and build node 16 before the next book

The missing 448th chunk is unexplainable because `kb.ingest_log` is empty — the optional
`Log ingest summary` node was never built, so the drop ledger was never written. Getting
it now would require a forced re-ingest (§6) purely to satisfy curiosity about one chunk.
**Not worth it.**

But plan 01 §5's whole argument for logging drops was *"the log is how you tell 'cleaning
worked' from 'cleaning ate the book'"* — and this is precisely the situation it was meant
to cover. **Build node 16 before ingesting the Stout guide**, so the second book arrives
with a ledger. It is one Postgres node; the SQL and parameters are in `01a` §16.

### 7.5 Documentation corrections

Now that the gate has produced evidence, fold it back. These are plan 01 §11's deferred
items plus what §3 above found:

- [ ] **Plan 01 §6 / §11** — replace the contextualization explanation of the over-512
      chunks with §3's measurement, and restate the criterion as the ≤1%-explained form.
      The `raw_text` amendment does **not** hold.
- [ ] **Architecture §6.2** — correct with the verified endpoint shape from plan 01 §2:
      multipart `/v1/chunk/hybrid/file/async`, flat `convert_*`/`chunking_*` form fields,
      `to_formats` does not exist on chunk endpoints, tokenizer must be set explicitly.
- [ ] **Architecture §6.4** — it assumes chunk text carries parseable image refs. It does
      not, at any configuration. Note that this corpus is text and tables only (§3 Option A).
- [ ] **Architecture §11 Phase 1** — flip WF1, Docling async, chunking config, embedding
      loop, folder state machine from ⬜ to ✅, and remove the ⚠️ note saying the retrieval
      gate cannot be met by the current corpus. It can now.
- [ ] **Architecture §11.1** — add the gate results table from §4 as verification evidence.

### 7.6 Deferred, still

- [ ] Prove D15 empirically — truncate `brew.bjcp_styles`, run the *old* graph, confirm
      it generates 0 cards. Recoverable; the fingerprint in plan 01 §0 verifies the rebuild.

---

## 8. Exit — what "Phase 1 done" means

- [x] zero chunks under 30 tokens
- [x] every chunk has a non-empty `heading_path` **and** a `page_from`
- [x] embedding coverage 100% at 1024 dims
- [x] over-512 understood and bounded (§3) — criterion restated
- [ ] re-running WF1 on the same file inserts nothing (§2.4)
- [ ] exactly one `is_current` version per document (§2.2 — confirm after §2.4)
- [ ] **the five questions return chunks you would have picked (§4)**
- [ ] WF1 exported and committed (§7.1)

When these are ticked, Phase 1 is closed and **Phase 2 is unblocked**: WF4, Chat Trigger
→ AI Agent (`gemma4:12b`) → Postgres Chat Memory → exactly two tools
(`search_brewing_knowledge`, `find_batches`). Architecture §7 and §11 Phase 2.

**Do not ingest the Stout guide first.** Plan 01 §9 fixes Phase 1 at *How to Brew* alone
so the gate stays attributable, and the next corpus growth is scheduled for Phase 3,
*before* the eval baseline. The corpus you just gated is the corpus WF4 gets built against.
