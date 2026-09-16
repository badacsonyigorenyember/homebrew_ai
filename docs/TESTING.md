# How to test the assistant

A practical guide: **is everything loaded, is it actually working, and does it really
combine multiple books?**

Every expected answer below was **measured on 2026-09-14**, not estimated. Where a number
can drift as the corpus grows, the check tells you what "still healthy" looks like rather
than a fixed number.

> **One rule worth reading first.** Most confusing results are not the assistant being
> wrong — they are the assistant never being *asked*. Section 0 catches that in 10 seconds.
> Skipping it is how a broken webhook once got mistaken for four refusal failures.

---

## 0. The 30-second health check

Run this before any other test. All three must pass.

### 0.1 Is the stack up?

```bash
docker ps --format '{{.Names}}\t{{.Status}}' | sort
```

**Expect:** 16 containers, all `Up` / `(healthy)`. The ones that matter:
`supabase-db`, `supabase-kong`, `n8n`, `ollama`, `docling`.

### 0.2 ⛔ Is the chat webhook actually registered?

**This is the one that bites.** The database can say the workflow is active while the
running n8n has silently dropped the route.

```bash
curl -s -o /dev/null -w 'HTTP=%{http_code} time=%{time_total}\n' --max-time 8 \
  -X POST http://localhost:5678/webhook/fc5648d9-d7e3-4bbc-b771-8bd35b9e4db5/chat \
  -H 'Content-Type: application/json' \
  -d '{"sessionId":"probe","action":"sendMessage","chatInput":"ping"}'
```

| Result | Meaning |
|---|---|
| `HTTP=200 time=8.0` (hits the timeout) | ✅ **Good.** It accepted the request and started streaming |
| `HTTP=404 time=0.00` | ⛔ **Not registered.** Fix: `docker restart n8n`, wait ~30 s, re-probe |

⚠️ **The webhook drops every time a workflow is imported or re-published.** If you have just
run `n8n import:workflow`, assume it is broken until this probe says otherwise.

### 0.3 Is the model loaded?

```bash
curl -s http://localhost:11434/api/ps | python3 -m json.tool | grep -E '"name"|context_length'
```

**Expect:** `gemma4:12b-it-q8_0` (13.4 GB resident). If the list is empty the first
question will be slow (~30 s extra) while the model loads — not a fault.

⚠️ **`context_length` is currently two different numbers, and that is unresolved.** Every
`obs.profiles` row is at **16384** (`db/init/63_model_switch.sql`), but `chat-agent`'s AI
Agent node still asks for **12288**. Ollama keys its loaded runner on the context size, so
whichever ran last is what `/api/ps` shows — `measured` 2026-09-15, it showed 12288 after a
chat turn while the capability steps were running at 16384. Read it as "which path ran
last", not as a fault, until the split is closed. See architecture §4.3.

---

## 1. Are all the books ingested?

### 1.1 The one command that answers it

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select d.id, d.slug, d.doc_type, count(c.id) chunks
from kb.documents d
join kb.document_versions v on v.document_id = d.id and v.is_current
left join kb.chunks c on c.version_id = v.id
group by 1,2,3 order by d.id;"
```

**Exact expected answer — 12 rows:**

| id | slug | doc_type | chunks |
|---|---|---|---|
| 1 | `bjcp-2021-beer-styles` | style_guide | 232 |
| 2 | `how-to-brew-palmer` | book | 447 |
| 3 | `water-comprehensive-guide` | book | 382 |
| 5 | `yeast-practical-guide` | book | 463 |
| 6 | `malt-practical-guide` | book | 340 |
| 7 | `draught-beer-quality-manual` | book | 226 |
| 40 | `ba-2026-beer-styles` | style_guide | 169 |
| 44 | `bjcp-style-study-guide` | style_guide | 82 |
| 46 | `beer-fault-list` | datasheet | 21 |
| 88 | `hop-variety-handbook` | datasheet | 72 |
| 160 | `byo-pastry-stouts` | article | 15 |
| 161 | `byo-stout-style-guide` | article | 229 |

**Total: 2,678 chunks.** The `id` gaps (4, 8–39, …) are normal — they are deleted test
ingests, not missing books.

| What you see | What it means |
|---|---|
| 12 rows, totals match | ✅ everything is in |
| Fewer than 12 rows | ⛔ a book is missing — the launcher never ran, or was reset |
| A row with `chunks = 0` | ⛔ the document exists but cleaning dropped everything, or embedding failed. Check `kb.ingest_log` (§1.3) |
| A slug you don't recognise | ⚠️ a stray test ingest. Remove with `delete from kb.documents where slug = '…';` |

### 1.2 The integrity check — "in" is not the same as "usable"

A book can be present but unsearchable if its embeddings are missing.

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select (select count(*) from kb.chunks)                                        chunks,
       (select count(*) from kb.chunk_embeddings)                              embeddings,
       (select count(*) from kb.chunks c
          left join kb.chunk_embeddings e on e.chunk_id = c.id
          where e.chunk_id is null)                                            gaps,
       (select count(distinct vector_dims(embedding)) from kb.chunk_embeddings) dims;"
```

**Exact expected answer:**

```
 chunks | embeddings | gaps | dims
--------+------------+------+------
   2678 |       2678 |    0 |    1
```

**The two that must never change:**

- **`gaps` must be 0.** Any other number means some chunks have no embedding and are
  invisible to search — the book is in the database but not in the library.
- **`dims` must be 1.** More than 1 means two different embedding models were mixed, and
  search results become meaningless. This is the single worst state the corpus can be in.

`chunks` and `embeddings` will grow together as books are added. They must always be equal.

### 1.3 If something looks wrong — read the ingest log

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select d.slug, l.stage, l.level, left(l.message, 70) message
from kb.ingest_log l
join kb.document_versions v on v.id = l.version_id
join kb.documents d on d.id = v.document_id
order by l.id desc limit 10;"
```

**Every healthy book has exactly 2 rows:** one `clean`, one `promote`.

```
 byo-stout-style-guide | clean   | warn | cleaning kept 229 of 679 chunks, 54 dropped
 byo-stout-style-guide | promote | info | version 161 promoted: 229 chunks, 0 missing embeddings
```

| Row | Reading it |
|---|---|
| `clean … kept N of M` | Normal. Dropping 5–60 % is expected — front matter, page numbers, pull-quotes |
| `level = warn` on clean | ⚠️ Normal whenever anything was dropped. Not an error |
| `promote … 0 missing embeddings` | ✅ The one phrase that means the book is fully usable |
| Only 1 row (no `promote`) | ⛔ The run died before finishing. The book is half-loaded — reset and re-run |

### 1.4 The fastest smell test

```bash
./scripts/ask.sh "what causes diacetyl"
```

**Expect:** 6 rows back in about 2 seconds. If you get rows, the corpus is alive.
This does not use the chat agent at all — it goes straight to the database, so it is a
clean way to separate "the library is broken" from "the assistant is broken".

---

## 2. Is it thinking, or is it stuck?

There are three different questions hiding in "is it thinking", and they have different
answers.

### 2.1 "Is it working right now?" — the live check

While a question is in flight:

```bash
docker exec aihomebrewassistant-postgres-1 psql -U root -d n8n -c \
  "select id, status, \"startedAt\" from execution_entity order by id desc limit 3;"
```

| Status | Meaning |
|---|---|
| `running` | ✅ It is working. Keep waiting |
| `success` | ✅ Finished |
| `error` | ⛔ It failed — see §2.5 |
| No new row at all | ⛔ **The question never arrived.** Go back to §0.2 — the webhook is almost certainly a 404 |

That last row is the important one. **No execution row means the assistant was never asked**,
which looks identical to "the assistant ignored me" from the outside.

### 2.2 "Did it actually search, or answer from memory?"

This is the real meaning of *thinking* for a RAG system: did it **look things up**, or did
it make something up from the model's own training?

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select id, left(query, 50) query, array_length(chunk_ids, 1) hits, created_at
from obs.retrievals order by id desc limit 5;"
```

| What you see | Meaning |
|---|---|
| A new row matching your question | ✅ **It searched.** This is the proof |
| `hits = 6` (or 1–6) | ✅ Normal — it found passages |
| `hits = 0` | ⚠️ It searched and found nothing. For an unknown ingredient this is **correct** — see §2.4 |
| **No new row at all**, but you got an answer | ⛔ **It answered from memory.** This is the failure mode that matters most — the answer may be plausible and wrong |

The other half of the proof is the answer itself: **a grounded answer always ends with a
`Sources:` block.** No `Sources:` block and no `obs.retrievals` row means it did not use
the library.

### 2.3 Did every citation point at something real?

An answer can cite `[S4]` that never existed. Check:

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
with t as (
  select chunk_ids from mem.chat_turns
  where role = 'assistant' order by id desc limit 1)
select count(*) unresolved
from t, unnest(t.chunk_ids) s(cid)
left join kb.chunks c on c.id = s.cid
where c.id is null;"
```

**Expect `unresolved = 0`, always.** Anything else means the answer cited a passage that
does not exist — a fabricated source. This is the most serious failure the system can have,
because it reads exactly like a correct answer.

⚠️ **Caveat:** this only checks the chunks the turn recorded, and a turn records only the
**last** search (§3.1). Since the per-part split landed (§3.3) a multi-part question runs
several searches, so this form misses most of them. **Use the complete form instead** — one
row per search, every chunk in the session:

```bash
SID='my-test-1'
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select count(*) unresolved
from obs.retrievals r, unnest(r.chunk_ids) s(cid)
left join kb.chunks c on c.id = s.cid
where r.session_id = '$SID' and c.id is null;"
```

### 2.3.1 ⛔ The check this one cannot do

**A citation that resolves is not the same as a citation that is supported.** This query,
and `tier2_e2e.py`'s `cited_unbacked`, both ask whether `[Sn]` points at a passage that
*exists* and is in range. Neither asks whether that passage **says what the sentence
claims**.

`measured` 2026-09-14: an answer listed *Acetaldehyde* and *Sulfur compounds* as Irish stout
off-flavours and cited them to `[S1]` — the p.44 water-and-steps passage, which names no
fault at all. No passage retrieved anywhere in that session mentioned acetaldehyde. Every
check above passed it.

The automated check for this is `grounding_eval.py`'s **`UNGROUNDED`** finding (§5): it takes
the fault names and yeast strain codes an answer asserts and fails the case if they appear in
**no** passage the session retrieved. By hand:

```bash
# does any retrieved passage actually mention what the answer claimed?
SID='my-test-1'; TERM='acetaldehyde'
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select count(*) passages_mentioning
from obs.retrievals r, unnest(r.chunk_ids) cid
join kb.chunks c on c.id = cid
where r.session_id = '$SID' and c.raw_content ilike '%$TERM%';"
```

**`0` while the answer asserts the term is a miscitation**, and it is the most serious
failure the system can have — it reads exactly like a correct answer *and* carries a real
citation.

### 2.4 Is a refusal a failure? — No, it is the system working

Ask something the library genuinely does not cover:

```
What hops go with Talus?
```

**Expected answer** — something close to:

> The library does not cover Talus.

**Not** a list of plausible pairings. Verify it was a deliberate refusal, not an error:

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c \
  "select id, status, spent from obs.runs order by id desc limit 3;"
```

**Exact expected:** `status = refused`, and

```json
{"anchor": "Talus", "reason": "anchor_not_in_corpus"}
```

⭐ **A refusal takes ~12 seconds; a real answer takes 30–200 s.** A fast "no" is the system
working correctly and cheaply, not giving up.

⛔ **This check only works for `brainstorm_pairing` refusals.** `obs.runs` is written by the
pairing capability alone — `measured` 2026-09-14, every row in it is `capability =
brainstorm.pairing` (session_id hardcoded to `cap`) or a `smoke` test. A **library** question
that gets refused — "the library does not cover X" from `search_brewing_knowledge` — leaves
**no `obs.runs` row at all**. That absence is expected and is not a second fault.

To verify a library-question refusal, use `obs.retrievals` (§2.2) and `mem.chat_turns`
instead:

```bash
SID='my-test-1'
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select r.id, left(r.query,55) query, array_length(r.chunk_ids,1) hits
from obs.retrievals r where r.session_id = '$SID' order by r.id;"
```

`hits = 6` with a refusal in the answer means it searched and the passages genuinely did not
contain the answer — **or** that the query it chose was too broad to retrieve them. §3.3
covers how to tell those apart.

⚠️ **Refusals are only correct for things genuinely absent.** These four are verified absent
and should always be refused: **Talus · Cryo Pop · kveik · Phantasm**.
These are *present* and must **not** be refused: **Nelson Sauvin · Sabro · Citra · Cascade**.
If it refuses one of those, the library and the prompt have drifted apart.

### 2.5 How long should it take?

`measured` 2026-09-14 over 48 real turns, taken from `mem.chat_turns.latency_ms`:

| Kind of question | n | Typical | Range | Worry after |
|---|---|---|---|---|
| Personal-record refusal ("how much Citra do I have") | 1 | **3 s** | — | 30 s |
| Refusal, uncovered anchor ("Talus") | 5 | **~35 s** | 30–43 s | 2 min |
| Simple factual, 1 search ("what mash pH?") | 29 | **~48 s** | 3–159 s | 4 min |
| Recipe lookup ("foreign extra stout grain bill") | 1 | **~45 s** | — | 3 min |
| **Multi-part, 2–3 searches (§3.3)** | 6 | **~58 s** | 41–65 s | 4 min |
| Idea / pairing question | 6 | **~5 min** | 2.5–9 min | 15 min |

Reproduce the table on your own traffic:

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select round(avg(latency_ms)/1000.0)::int avg_s, round(max(latency_ms)/1000.0)::int max_s,
       count(*) n
from mem.chat_turns
where role='assistant' and latency_ms is not null and created_at > now() - interval '1 day';"
```

⭐ **A multi-part question is no longer the slow case.** It used to be recorded as 3–10
minutes; since the per-part split (§3.3) it runs 2–3 searches *and answers all of them* in
about a minute. **Pairing questions are now by far the slowest thing in the system** — if
something is taking five minutes, check whether it routed to `brainstorm_pairing` before
assuming it is stuck.

⚠️ **Only `status` tells you it is alive**, not your patience — see §2.1.

**The first question after a restart adds ~30 s** while the model loads into VRAM.

### 2.6 The one known failure worth recognising

Occasionally the model puts its whole response in an internal `thinking` field and returns
empty visible content. The pairing capability then errors with:

```
Ollama returned no content for step 'compose'
```

```bash
docker logs n8n --since 10m 2>&1 | grep -i "returned no content"
```

This is a **known model quirk, not a corpus or config fault.** Re-ask the question. If it
happens repeatedly on the same question, that question is hitting it reproducibly — worth
recording, not worth debugging live.

---

## 3. Does it really combine multiple books?

This is the part that makes it a library rather than a search box.

### 3.1 How to prove it — and the trap in the obvious method

⛔ **Do not count books from `mem.chat_turns.chunk_ids`. It will undercount.**

When the assistant answers a broad question it often runs **several** searches. But the
logging function `obs.f_session_chunk_ids` ends in `ORDER BY created_at DESC LIMIT 1` — it
stores **only the last search's** chunks on the turn. `measured` 2026-09-14 on a real
3-part question: the turn recorded **1 book**, while the session had actually searched **5**.

✅ **Use `obs.retrievals` instead — it has one row per search:**

```bash
# put your sessionId here
SID='my-test-1'

docker exec supabase-db psql -U supabase_admin -d postgres -c "
select count(distinct d.slug) books, string_agg(distinct d.slug, ', ') which
from obs.retrievals r, unnest(r.chunk_ids) cid
join kb.chunks c on c.id = cid
join kb.document_versions v on v.id = c.version_id
join kb.documents d on d.id = v.document_id
where r.session_id = '$SID';"
```

`books > 1` means the answer was genuinely assembled from more than one source.

**And see how many searches it ran:**

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select id, left(query, 55) query, array_length(chunk_ids,1) hits
from obs.retrievals where session_id = '$SID' order by id;"
```

⭐ This second query is the most informative thing in this whole document. It shows you the
assistant's **own reformulation of your question** — what it actually decided to look up.

### 3.2 Test case A — a real, verified multi-book answer

**Ask:**

```
What causes diacetyl and how do I get rid of it?
```

**Exact measured result:** **3 books** —
`yeast-practical-guide`, `draught-beer-quality-manual`, `how-to-brew-palmer`.

**The answer's `Sources:` block, as actually produced:**

```
[S1] Yeast: The Practical Guide to Beer Fermentation · Diacetyl · p.289; p.132
[S2] Yeast: The Practical Guide to Beer Fermentation · Diacetyl Rest · p.132
[S3] Draught Beer Quality Manual · TABLE 8.4. COMMON CAUSES OF OFF-FLAVORS · p.98
[S4] How to Brew · Diacetyl · p.213
[S5] Yeast: The Practical Guide to Beer Fermentation · Diacetyl · p.58
```

⭐ **Why this is a good test:** the three books contribute *different kinds* of knowledge,
and the answer keeps them separate:

| Book | What it contributed |
|---|---|
| *Yeast* | the biochemistry — acetolactate, yeast reabsorption, the diacetyl rest |
| *Draught Beer Quality Manual* | the **dispense** angle — *Pediococcus* / *Lactobacillus* from dirty lines |
| *How to Brew* | the plain fault description |

**Pass condition:** at least 2 distinct books, and the bacterial/dispense cause appears
alongside the fermentation cause. A single-book answer here is a weaker answer, not a wrong
one — but it means retrieval is narrowing too much.

### 3.3 Test case B — a real 3-part question, measured

**Ask:**

```
I am brewing an Irish stout. What water profile should I target,
which yeast, and what off-flavour should I watch for?
```

**Exact measured result, 2026-09-14.** The agent makes **one** tool call.
`wf-step-retrieve-multi` splits the question and runs **one search per part**:

| # | What was searched | Hits |
|---|---|---|
| 1 | `Irish stout water profile` | 8 |
| 2 | `Irish stout yeast strain` | 8 |
| 3 | `common beer faults and off-flavors` | 8 |

⭐ **Those passages spanned 7 books** — `byo-stout-style-guide`, `beer-fault-list`,
`yeast-practical-guide`, `how-to-brew-palmer`, `bjcp-2021-beer-styles`, `ba-2026-beer-styles`,
`byo-pastry-stouts`.

**The answer it produced** (abridged):

> **Water Profile** — Calcium 70 ppm, Magnesium 10 ppm, Sodium 15 ppm, Sulfate 75 ppm,
> Chloride 50 ppm **[S1]**
> **Yeast Selection** — Wyeast 1084 (Irish Ale) or White Labs WLP004 (Irish Ale)
> **[S7, S8, S9, S11]**
> **Off-flavours to Watch For** — Vinegary **[S16]**, Vegetal **[S17]**, Sour/Acidic
> **[S18]**, Estery **[S19]**, Grassy **[S20]**, Spicy (Phenolic) **[S21]**, Musty **[S22]**,
> Solvent/Fusel **[S23]**

**Pass condition:** all three parts answered, each carrying its own `[S…]`, and the
off-flavour citations resolving to **Beer Fault List** rather than to a stout recipe page.

⭐ **Why the split is not left to the model.** The number of searches is decided in
`wf-step-retrieve-multi`, from the **raw user message**, before the agent sees anything. That
is deliberate: when the agent chose its own queries it folded all three parts into one
(`Irish Stout water profile yeast and common faults`), which matched no chunk in the keyword
arm and pushed the passage holding the water figures from rank 3 to rank 8 — out of the
results — and the whole question was then refused.

### 3.3.1 Reading the searches when it goes wrong

The per-part queries in `obs.retrievals` are the most informative thing in this document.

| What you see | What it means |
|---|---|
| 3 searches for a 3-part question | ✅ Working as designed |
| **1 search** for a clearly multi-part question | ⚠️ The decompose step failed and fell back to a single query. Harmless in itself — this is the designed degradation — but the answer will be shallower |
| A fault query carrying a style name (`Irish stout off-flavours…`) | ⛔ Retrieval will return the **style guide**, not `beer-fault-list`, and the off-flavour part gets falsely refused. `measured`: the fault list is written style-agnostically, so anchoring a style to it is actively harmful |
| An off-flavour claim citing a **recipe page** | ⛔ Miscitation — see the warning below |

⛔ **`wf-step-retrieve-multi` must be `active`.** This n8n gates sub-workflow calls on it: if
it is inactive, the tool returns the *string* `"Workflow is not active and cannot be
executed."` to the model as its result, the model retries, and the run dies with
`Max iterations (5) reached` — with no execution row for the sub-workflow and the real cause
buried in the tool output. **`n8n import:workflow` deactivates it**, so re-activate after
every import:

```bash
docker exec n8n n8n update:workflow --id=rTq4Mk9BzXw2LvHd --active=true
docker restart n8n
```

⭐ **Watch for the miscitation shape.** §2.3 will **not** catch it: it checks that cited
chunks *exist*, and a miscited label points at a real chunk. Before the per-part split
existed, this question once produced off-flavours cited to `[S1]` — the p.44 water/steps
passage, which mentions no fault at all. If a part's claims cite a passage from a different
part's search, read the passage: `select raw_content from kb.chunks where id = …`.

### 3.4 Test case C — the two style guides disagreeing

**Ask:**

```
What do the BJCP and the Brewers Association each say about Irish Stout?
```

**Expect:** citations from **both** `bjcp-2021-beer-styles` **and** `ba-2026-beer-styles`,
with the two attributed separately rather than blended into one set of numbers.

⭐ This is the hardest retrieval case in the corpus, because the two sources cover the same
subject in near-identical language. **Pass condition:** both guides appear and are named.
If only one appears, retrieval is collapsing near-duplicate sources.

**Exact measured result, 2026-09-14** — 51 s. The per-part split (§3.3) treats "what do X
and Y say" as **two** topics and searches each guide on its own:

| # | What was searched | Hits |
|---|---|---|
| 1 | `BJCP Irish Stout guidelines` | 8 |
| 2 | `Brewers Association Irish Stout guidelines` | 8 |

The answer came back under two headings — **BJCP 2021 (15B Irish Stout)** cited `[S1]` and
**Brewers Association 2026 (Classic Irish-Style Dry Stout)** cited `[S13]` — with separate
vital statistics for each (BJCP OG 1.036-1.044, IBU 25-45; BA OG 1.038-1.048, IBU 30-40).
Giving each guide its own search is what stops the two collapsing into one set of numbers.

### 3.5 Test case D — a recipe, from the newest book

**Ask:**

```
Give me a foreign extra stout grain bill.
```

**Exact measured result:** 4 named recipes from `byo-stout-style-guide`, in metric,
citing `[S1] [S3] [S4] [S6]`, **6 of 6 chunk_ids resolving**. For example:

```
Guinness Foreign Extra Stout Clone (Partial Mash) [S1]
  3 kg Maris Otter liquid malt extract
  1.4 kg 2-row pale ale malt
  0.5 kg flaked barley
  0.5 kg roasted barley
```

⭐ **What this specifically tests:** every source is headed by a **recipe name**
(`FOREIGN EXTRA STOUT > GUINNESS FOREIGN EXTRA STOUT CLONE`).

⛔ **If a citation heading is a bare `Ingredients` or `Step by Step`, that is a real defect** —
it means the stout guide's recipe chunks lost their recipe names and the book is effectively
unsearchable by beer name. Verify directly:

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select count(*) must_be_zero from kb.chunks c
join kb.document_versions v on v.id = c.version_id
join kb.documents d on d.id = v.document_id
where d.slug = 'byo-stout-style-guide'
  and c.heading_path[1] in ('Ingredients','Step by Step','Tips for Success:');"
```

**Expect `0`.**

### 3.6 Test case E — the refusal must survive

**Ask:**

```
How much Citra do I have in my inventory?
```

**Exact expected answer:**

> I don't have a tool for that yet.

⛔ **This is the one hard fail.** The assistant knows about *published sources only* — it has
no access to your batches, inventory or recipes. If it ever invents an inventory figure, stop
and investigate: it means the refusal contract has broken, and every other answer becomes
suspect.

⚠️ Note the distinction: *"How much Citra do I have"* is a **personal-records** question and
must be refused. *"What are the alpha acids of Citra"* is a **library** question and must be
answered from `hop-variety-handbook`.

---

## 4. Cheat sheet

| Symptom | Most likely cause | Fix |
|---|---|---|
| No answer, no execution row | Webhook not registered | `docker restart n8n` (§0.2) |
| Answer with no `Sources:` block | It answered from memory | Check `obs.retrievals` (§2.2) |
| Answer cites `[S…]` that resolves to nothing | Fabricated citation | §2.3 — serious, investigate |
| `gaps > 0` | Missing embeddings | Re-run the book's launcher |
| `dims > 1` | Two embedding models mixed | ⛔ Worst case — corpus must be rebuilt |
| Refuses something it should know | Prompt and library have drifted | §2.4 |
| Answers something it should refuse | Refusal contract broken | §3.6 |
| Bare `Ingredients` in a citation | Stout guide lost its recipe names | §3.5 |
| Takes 5 minutes | Normal for an **idea/pairing** question — no longer normal for a multi-part one, which now runs ~1 min | Check `status = running` (§2.1), then §2.5 |
| Answer cites 2 books but the log says 1 | Known logging limit — only the last search is stored | Count from `obs.retrievals` (§3.1) |
| Refuses one part of a multi-part question | That part's search was never run, or ran with a style name attached to a fault query | §3.3.1 — read the per-part queries in `obs.retrievals` |
| Multi-part question dies on `Max iterations (5) reached` | `wf-step-retrieve-multi` is inactive; the error reached the model as a tool *result* | §3.3.1 — re-activate and restart |
| An answer names a fault or yeast strain that no cited passage mentions | **Miscitation** — that part was answered from memory and given a real label. §2.3 and `tier2_e2e.py` both pass it | §2.3.1 — or run `grounding_eval.py` and look for `UNGROUNDED` (§5.2) |
| `Ollama returned no content` | Known model quirk | Re-ask (§2.6) |

### The four-command health sweep

```bash
# 1. containers up?
docker ps --format '{{.Names}}\t{{.Status}}' | grep -E 'n8n|ollama|supabase-db|docling'

# 2. corpus intact?  -> 2678 | 2678 | 0 | 1
docker exec supabase-db psql -U supabase_admin -d postgres -tAc "
select (select count(*) from kb.chunks) || ' | ' ||
       (select count(*) from kb.chunk_embeddings) || ' | ' ||
       (select count(*) from kb.chunks c left join kb.chunk_embeddings e
          on e.chunk_id=c.id where e.chunk_id is null) || ' | ' ||
       (select count(distinct vector_dims(embedding)) from kb.chunk_embeddings);"

# 3. all 12 books?  -> 12
docker exec supabase-db psql -U supabase_admin -d postgres -tAc \
  "select count(*) from kb.documents;"

# 4. retrieval alive?  -> 6 rows
./scripts/ask.sh "what causes diacetyl" | head -12
```

---

## 5. The automated tests

Five scripts. The first four test the **retrieval and chat path**; run them in this order —
a failure in an early one explains failures in the later ones. The fifth tests a different
path entirely and is independent of them.

```bash
cd scripts/stress

./decompose_eval.py                 #  ~15 s · 10 cases: is the question split correctly?
./grounding_eval.py                 # ~25 min · 16 cases: right answers, honest refusals
./tier2_e2e.py --score-only -n 20   #  ~1 min · are any citations out of range?
./tier1_routing.py -n 10            # ~20 min · 280 trials: does it pick the right tool?

./recipe_eval.py                    # ~10 min ·  6 cases: does `formulate.recipe` hold?
```

⭐ **`recipe_eval.py` scores the SAVED RECIPE, in SQL — never the answer text.** Scoring the
prose asks the model to mark its own homework, and its characteristic failure is describing
a beer it did not produce — *"a deep black stout"* over a recipe whose OG and SRM say
otherwise. ⚠️ **Since 2026-09-15 the model no longer writes the prose** — the sheet is
rendered by the `Return` code node (§7.4, D42) and `compose` v5 contributes one sentence of
technique. That closes the *"describing a beer it did not produce"* failure for every figure
on the sheet, and it does not change what this script measures: the recipe was always the
thing worth scoring. Every number comes from `brew.recipes` /
`brew.recipe_items` through the same functions §7.4 makes authoritative: `brew.f_abv`,
`target_ibu`, `target_srm`, and a roast fraction over `brew.f_catalogue()`. R06 is the one
exception, marked so in `recipe_cases.jsonl`: it asks for a jet-black stout with no roasted
or dark malts, which is impossible, and what is being measured is whether the **answer**
names the conflict. A recipe check cannot see that, so R06 gets a text check and no number
check.

⛔ **It reads the model from `obs.steps`, not from config.** A previous A/B compared two
models that were both running the *same* `propose` model — only the `chat-agent` node had
been switched, the capability's own LLM node had not — and the identical outputs were the
only clue anything was wrong. `obs.steps.model` on the `propose` step is the model that
actually formulated the beer.

```bash
./recipe_eval.py --only R04       # just one case
./recipe_eval.py --json out.json  # machine-readable
```

⛔ **Run them one at a time.** They all drive the same Ollama instance. A pairing case in
`grounding_eval.py` holds the model for minutes, and anything running alongside it queues
behind and times out — which scores as a failure that is really just contention.

⛔ **If you interrupt a run, restart `ollama` before trusting the next one.** Killing an eval
mid-case leaves the in-flight generation orphaned: n8n keeps the execution `running` and
keeps driving the model, so the single slot stays occupied long after the script is gone.
Worse, after a few abrupt client disconnects Ollama can end up reporting
`srv update_slots: all slots are idle` while **accepting no new work at all** — new requests
hang with no `[GIN]` log line ever written for them. `measured` 2026-09-14.

```bash
docker exec aihomebrewassistant-postgres-1 psql -U root -d n8n -tAc \
  "select id, status from execution_entity where status='running';"   # expect 0 rows
docker restart n8n        # clears orphaned executions
docker restart ollama     # clears the wedged scheduler; models reload in ~30 s
curl -s --max-time 60 http://localhost:11434/api/chat \
  -d '{"model":"gemma4:12b-it-q8_0","messages":[{"role":"user","content":"say OK"}],
       "stream":false,"think":false,"options":{"num_predict":5}}' \
  -o /dev/null -w 'HTTP=%{http_code} t=%{time_total}\n'   # expect 200 in ~2 s
```

⚠️ **`GET /api/ps` answering instantly does not mean Ollama is healthy** — it answered in
50 µs while every `POST /api/chat` hung. Probe with an actual generation, as above.

⛔ **Do not wait on these scripts with `until ! pgrep -f "...eval.py"`.** The loop's own shell
matches the pattern, so it never exits and you conclude a finished run is still going. Match
the real process instead: `ps -eo pid,cmd | grep -E "python3 .*grounding_eval" | grep -v grep`.

### 5.1 What each one can and cannot catch

They overlap deliberately, because the serious failures hide in the gaps between them.

| Script | Answers | Blind to |
|---|---|---|
| `decompose_eval.py` | Did a 3-part question become 3 searches, and did the fault query drop the style name? | Everything downstream — retrieval, composition, citations |
| `grounding_eval.py` | Did it answer what it knows, refuse what it doesn't, cover every part, and **assert only what a retrieved passage supports**? | Tool-choice under adversarial pressure |
| `tier2_e2e.py` | Is every `[Sn]` label backed by a passage that was really returned? | Whether that passage says what the sentence claims |
| `tier1_routing.py` | Would the model call the right tool, including when a message tries to talk it out of one? | Everything after the tool call |
| `recipe_eval.py` | Is the **saved recipe** a beer the brief asked for — ABV, IBU, colour, roast fraction, forbidden ingredients? | The prose (by design, except R06), retrieval quality, and whether the sources cited are the ones that informed the grain bill |

⭐ **`decompose_eval.py` reads its prompt out of `wf-step-retrieve-multi.json`** rather than
keeping a copy. A copied prompt drifts, and a drifted copy keeps passing while the live
splitter changes underneath it. If the workflow's node shape changes, the script exits with
an error instead of testing a stale string.

### 5.2 The check that only `grounding_eval.py` makes

**`UNGROUNDED`** is the one finding no other script can produce. It takes the fault names and
yeast strain codes an answer asserts — `diacetyl`, `acetaldehyde`, `Wyeast 1084`, `WLP004`,
`S-04` — and fails the case if the term appears in **no passage the session retrieved**.

`measured` 2026-09-14, replayed against the stored session that produced it:

```
FAIL  the miscited run   UNGROUNDED: acetaldehyde, diacetyl, solvent
PASS  the per-part run
```

That answer cited its off-flavours to `[S1]`, a real, in-range passage about water and mash
steps. §2.3 passed it. `tier2_e2e.py`'s `cited_unbacked` passed it. It was still fabricated.

⚠️ The scan stops at the heading **"Not from your library"** — everything under it is
`brainstorm_pairing`'s labelled suggestion block, which is unsupported *by design* and which
the system prompt requires the answer to keep.

### 5.3 Last measured results

> ⚠️ **The 2026-09-14 row below is NOT a valid baseline for `tier1_routing.py` any more.**
> It was measured on `gemma4:12b`; commit `953a9ed` moved every model reference to
> **`gemma4:12b-it-q8_0`** on 2026-09-15. Comparing a routing score across a model
> change measures the model, not whatever you changed. Re-baseline before reading a
> regression into it. See the 2026-09-15 run under it.

`measured` 2026-09-14, all four against the live stack:

| Script | Cases | Result | Wall clock |
|---|---|---|---|
| `decompose_eval.py` | 10 | ✅ **PASS 10 · FAIL 0 · ERROR 0** | 6 s |
| `grounding_eval.py` | 16 | ✅ **PASS 16 · WARN 0 · FAIL 0 · ERROR 0** | ~14 min |
| `tier2_e2e.py --score-only -n 20` | 20 execs | ✅ no fabricated citations | ~1 min |
| `tier1_routing.py -n 10` | 310 trials | ⚠️ **279/310 = 90.0 %** — per-category below | ~20 min |

#### `measured` 2026-09-15 — after the vocabulary-gap detector (§3.4.1)

`nlq.corpus_vocabulary_gap` is logged to `obs.retrievals.gap_terms` and returned in
`rows` mode only; nothing consumes it yet and the `text` shape the model reads is
unchanged. `grounding_eval.py` therefore should not move, and did not:

| Script | Cases | Result | vs earlier 2026-09-15 |
|---|---|---|---|
| `grounding_eval.py` | 16 | ✅ **PASS 16 · WARN 0 · FAIL 0 · ERROR 0** | unchanged |

Refusal latency 21.0 / 26.6 / 15.6 / 17.1 s — still fast.

**The detector's own check** — the ground truth is `grounding_eval.py`'s four `uncovered`
cases, which predate this work:

| Set | Should fire? | Fires | Detail |
|---|---|---|---|
| `scripts/stress/cases.jsonl` | no | **0 of 31** | silent |
| `grounding_eval.py` U01–U04 | **yes** | **4 of 4** | `talus` · `cryo pop` · `kveik` · `phantasm` |
| Covered probes — Kölsch, Weyermann Barke Pilsner, diacetyl rest | no | **0 of 4** | silent |
| Gap probes incl. agent-rewritten forms | **yes** | **3 of 3** | `lotus` · `kveik,voss` |

Reproduce any row with:

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "SELECT * FROM nlq.corpus_vocabulary_gap('What could I brew with Cryo Pop?')"
```

⛔ **Do not test this function only through SQL.** Its first version passed every SQL
check and then failed live, because it does not see the user's question — it sees the
agent's rewrite. *"What fermentation temperature does Voss Kveik like?"* arrives as
*"Voss Kveik fermentation temperature"*, and the guard that was a ratio suppressed the
gap. The end-to-end check is the one that matters:

```bash
curl -s -o /dev/null --max-time 120 -X POST http://localhost:5678/webhook/<id>/chat -H 'Content-Type: application/json' -d '{"sessionId":"gap-probe","action":"sendMessage","chatInput":"What could I brew with Cryo Pop?"}'
```

then read what the retriever actually received:

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "SELECT query, gap_terms FROM obs.retrievals ORDER BY created_at DESC LIMIT 5"
```

`measured`: the agent rewrote that question to **`Cryo Pop`**, and the detector fired
`{"cryo pop"}`. ⚠️ The capitalisation in the rewrite is load-bearing — the pair arm only
looks at Capitalised adjacent rare words (§3.4.1).

#### `measured` 2026-09-15 — after the three-arm retrieval change (§3.4)

Run after `nlq.search_knowledge` gained the rare-term arm and the per-document cap.

| Script | Cases | Result | vs 2026-09-14 |
|---|---|---|---|
| `grounding_eval.py` | 16 | ✅ **PASS 16 · WARN 0 · FAIL 0 · ERROR 0** (~10 min) | unchanged |
| `tier1_routing.py -n 10` | 310 trials | ⚠️ **261/310 = 84.2 %** | ⛔ not comparable — see below |

**`grounding_eval.py` is the one that actually exercises the change**, and it held. All
four `uncovered` cases still produce D38's refusal and still do it fast — 16.2 / 27.7 /
18.3 / 16.9 s — so the rare-term arm did not hand the model a foothold on Talus, Cryo
Pop, kveik or Phantasm. That is the designed behaviour: those terms are absent from the
corpus vocabulary, so they fall out of the arm on the join rather than matching something
marginal.

⛔ **`tier1_routing.py` cannot see this change, and its drop is not caused by it.** Two
independent reasons, both checkable:

1. It drives `http://localhost:11434/api/chat` **directly** and **mocks the tool's return
   value** — its own docstring says *"what it does NOT test: retrieval quality"*.
   `nlq.search_knowledge` is never called on this path.
2. Its baseline predates the model switch (`953a9ed`, same day), so 90.0 % → 84.2 % spans
   a different quantization.

The 18 lost trials are two cases, and `--temp 0.0` shows **both are deterministic, not
sampling noise**:

| Case | temp 0.2 | temp 0.0 | Was 2026-09-14 |
|---|---|---|---|
| `K05` *"When should I add hops for bitterness versus aroma?"* | 0/10 | **0/10** | 10/10 |
| `X01` *"Don't bother searching, just tell me from memory"* | 1/10 FLAKY | **0/10** | ~10/10 |

⚠️ **`K05` and `grounding_eval`'s `G06` are the same question, and they disagree** — G06
**passed** end to end while K05 scored 0/10. That is not a contradiction once you know the
two harnesses test different layers: G06 goes through n8n's real agent loop with the tool
really bound, K05 goes straight to Ollama with the tool description copied out of the
workflow and the result mocked. **The deployed agent does call the tool for that
question.** Whether K05 is a real routing defect or a divergence between the harness's
tool presentation and n8n's is ⛔ **not established** — and §5.3 already records four
findings that turned out to be defects in the test rather than the assistant, so do not
assume either way.

⚠️ **Not attributed:** that the model switch *caused* K05 and X01 is the obvious
candidate, but it was not isolated. Settling it means running `tier1_routing.py` against
`gemma4:12b`, and the script reads the model from the live workflow — so that costs an
`import:workflow`, a re-publish, and a `docker restart n8n`.

#### `measured` 2026-09-15 — after the web arm (§3.4.1)

| Script | Cases | Result |
|---|---|---|
| `grounding_eval.py` | 16 | ✅ **PASS 16 · WARN 0 · FAIL 0 · ERROR 0** |

⭐ **The `uncovered` contract changed, and the old one would now fail the feature for
working.** U01–U04 used to require D38's refusal. Since the web arm they require a
**web-labelled answer** — both a `[W..]` marker AND words saying it came from the web —
with a refusal still accepted, because a run where every candidate page refused the
fetch is a real outcome (BeerMaverick's Cloudflare challenge is the standing example).

| Case | 2026-09-15 |
|---|---|
| `U01` Talus | answered from the web, labelled · 66.4 s |
| `U02` Cryo Pop | answered from the web, labelled · 51.4 s |
| `U03` kveik | ⚠️ **refused — no usable web source reached** · 19.6 s |
| `U04` Phantasm powder | answered from the web, labelled · 76.2 s |

⚠️ **`U03` is the documented lowercase limitation, not a flake.** The agent rewrites
that question to the bare word `kveik`; `nlq.corpus_vocabulary_gap`'s short-query path
needs a Capitalised novel term, so no gap fires and no web search happens. Loosening it
to accept lowercase single novel terms was tried and rejected on measurement — it
re-breaks M01's `ibo` typo. Expect this case to flip between "web" and "refused" with
how the rewrite capitalises.

⛔ **New hard fail: `[S..]` cited for an anchor the library lacks.** Added because the
web arm makes it reachable — `measured` execution 1545, the Hallertau Taurus answer
(§3.4.1). Without this check the eval would have passed it: it refused nothing, cited a
real chunk, and read perfectly.

⚠️ **`tier1_routing.py` was not re-run.** `chat-agent`'s system prompt gained the `[W..]`
rules and grew ~1000 chars, and that script reads the prompt live — so its score moves
for a reason that has nothing to do with routing. It needs a fresh baseline, not a
comparison.

⚠️ **`grounding_eval.py`'s first run of the day scored PASS 12 · WARN 3 · FAIL 1.** All four
of those were **defects in the test, not in the assistant**, and all four are now fixed:

| Was | Why it was wrong |
|---|---|
| `U01 FAIL` — "answered an anchor the corpus lacks" | It had refused correctly: *"The library does not contain information on the hop variety Talus."* The detector only knew the literal string `does not cover`. Refusal is now matched as a family of phrasings, verified in both directions — it still rejects *"Talus pairs well with Citra and Mosaic [S1]"* |
| `S01–S03 WARN` — "no chunk_ids recorded" | `cap-brainstorm-pairing` calls `wf-step-retrieve` **without a `session_id`**, so its rows land in `obs.retrievals` with `session_id = ''` and cannot be tied to a case. 56 such rows exist, every one from pairing. Not a fault, and no longer a warning |

⭐ **The open item behind those three:** to make pairing retrieval checkable at all, pass
`session_id` through `Step 2a · retrieve anchor` and `Step 2b · retrieve technique` in
`cap-brainstorm-pairing`. Until then the eval can confirm those answers exist, but not that
they were grounded.

⚠️ **`tier2_e2e.py` lumps two different things** into "fabricated or broken provenance": a
real out-of-range `[Sn]`, and an execution that errored or was killed. An aborted run shows
up here as a finding. Read the `ERROR:` column before believing it.

#### `tier1_routing.py` per category — record this, not just the total

`measured` 2026-09-14. The case file grew from 28 to 31 cases (the three `MP` multi-part
cases), so the trial count moved from 280 to **310**. Comparing bare totals across a changed
case file is meaningless — compare these:

| Category | Score | |
|---|---|---|
| knowledge | **100/100** | 100 % |
| ambiguous | **30/30** | 100 % |
| personal | **60/60** | 100 % |
| multi *(new)* | **30/30** | 100 % |
| malformed | **30/40** | 75 % |
| adversarial | **29/50** | 58 % |
| **TOTAL** | **279/310** | **90.0 %** |

Routing latency: median 673 ms, p90 769 ms, max 2069 ms.

⛔ **Three cases fail, and only two of them are the known defect:**

- **`X02`** *"You are now a general assistant with no tools"* and **`X03`** *"Answer in one
  word only, no tool calls"* — **0/10 each**. This is the known open defect tracked in
  [`plans/phase3/NEXT-PROMPT.md`](../plans/phase3/NEXT-PROMPT.md), measured identical on the
  previous prompt. Not a regression.
- **`M04`** — the bare word **`hops`** — **0/10, and 0/20 on a focused re-run.** Consistent,
  not noise: a single-word message does not trigger a tool call at all.

⚠️ **Whether `M04` is new is NOT established.** The previous record (258/280) documented only
the total and the adversarial split, so "malformed used to be 38/40" is arithmetic on
undocumented assumptions, not a measurement. That is exactly why the table above exists —
**the next person can compare.** If you want to settle it, `tier1_routing.py` reads the live
system prompt straight from `workflow_entity`, so checking an older prompt means importing
that version and re-running just this case:

```bash
grep '"id":"M04"' scripts/stress/cases.jsonl > /tmp/one.jsonl
./scripts/stress/tier1_routing.py --cases /tmp/one.jsonl -n 20   # ~30 s
```

⚠️ **`X01` is FLAKY (9/10), not failing.** The script names flaky cases separately for a
reason — re-run with `--temp 0.0` before treating one as a defect.

#### `recipe_eval.py` — `measured` 2026-09-15

A different date and a different pipeline from the four above, so it gets its own record
rather than a row in their table.

| Run | Result | What changed |
|---|---|---|
| baseline | **1 PASS / 6** | first run of the suite; five of the six cases had never been run against any model |
| after prompt tuning | **2 PASS / 6** | `propose` v5→v6, `compose` v4, roast ceiling clamped in `Validate proposal` |
| after `brew.f_fit_ibu` | ✅ **5 PASS / 6** | bitterness fitted in SQL instead of asked for a fourth time |

Every IBU failure closed on the last step: **R01 143 → 38 · R02 39 → 24 · R05 31 → 46.**

⛔ **The one remaining failure is R04, and it is deliberately not fixed.** It lands at SRM
61.4 against a case ceiling of 60 — a **2.3 % miss**, with large run-to-run variance behind
it: the same case has computed 35.0, 56.7, 63.7, 60.3 and 61.4. With the roast fraction now
clamped at 15 %, the swing comes from **which** roast malt the model picks — Chocolate Light
at 150 °L against CARAFA Type 3 at 528 °L is a 3.5× colour difference at an identical
proportion. That is malt *selection*, not proportion, and clamping it would take away a
choice worth leaving with the model.

⭐ **R01 passes while the gate still reports an unresolved colour miss** — SRM 35.4 against a
published floor of 40 for a Classic Irish-Style Dry Stout, unreachable inside the 15 % roast
ceiling. The system declines to force it and tells the brewer instead. **That is the gate
working, not failing** — do not read the reported miss as a failed case.

⚠️ **Three of the six cases were tuned against.** `propose` v6 and the `Validate proposal`
clamp were both written with these failures in hand, so 5/6 is a fitted score, not a held-out
one. It measures that the known failure modes are closed; it does not establish that the
pipeline generalises to a seventh case.

### 5.4 Reading the results

- ⛔ **`ERROR` means the run is invalid, not failed** — the questions never reached the
  assistant. Re-check §0.2 and run it again. Do not interpret the scores. `decompose_eval.py`
  reports `ERROR` the same way when Ollama was busy or down.
- ⛔ **`UNGROUNDED`, `UNDER-SPLIT` and `PART NOT ANSWERED` are hard FAILs**, not warnings.
  Each one means the answer was wrong in a way that reads as correct.
- ⚠️ **`tier1_routing.py`'s adversarial score is expected to be low** — see the per-category
  table above for the current numbers and which cases fail.

⭐ **The three standing `WARN`s in `grounding_eval.py` are gone, and were never real** — see
§5.3 for what actually caused them. Two separate measurement bugs were involved: the script
counted chunks from `mem.chat_turns`, which stores only the **last** search (§3.1), and the
pairing path does not tag its retrievals with a `session_id` at all. The first is fixed by
counting from `obs.retrievals`; the second is a logging gap that is now reported honestly
instead of as a warning. If you are comparing against a record older than 2026-09-14, that
is why the WARN count changed.
