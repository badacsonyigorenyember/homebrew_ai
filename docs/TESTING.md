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

**Expect:** `gemma4:12b` and `context_length: 12288`. If the list is empty the first
question will be slow (~30 s extra) while the model loads — not a fault.

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
**last** search (§3.1). If the assistant searched more than once, some cited passages are
not covered by this check. For a complete check across every search in the turn, use
`obs.retrievals` — or run `tier2_e2e.py` (§5), which reads n8n's own execution records.

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

Measured 2026-09-14:

| Kind of question | Typical | Worry after |
|---|---|---|
| Refusal ("Talus") | **~12 s** | 60 s |
| Simple factual ("what mash pH?") | **15–40 s** | 3 min |
| Recipe lookup ("foreign extra stout grain bill") | **~45 s** | 3 min |
| Multi-part question (§3.3) | **3–10 min** | 15 min |
| Idea / pairing question | **2–9 min** | 15 min |

⚠️ **A 3-part question is genuinely slow** — it makes several searches and writes a long
answer. `status = running` means it is fine. Judge by the status, not by your patience.

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

**Exact measured result, 2026-09-14 (after the multi-part prompt rule)** — it now searches
with **short single-topic queries**. Two runs of the identical question, so you can see the
variance for yourself:

| Run | What the assistant searched for | Hits |
|---|---|---|
| 1 | `Irish stout water profile` · `Irish stout yeast strain` | 8 · 8 |
| 2 | `Irish stout water profile` | 8 |

Both answered water and yeast correctly. Neither searched for off-flavours — see observation
2 below.

⭐ The water figures live in **one** chunk — `byo-stout-style-guide` p.44
`IRISH STOUT > Step by Step`. A short query puts it at **rank 1**; the older combined query
(`Irish Stout water profile yeast and common faults`) pushed it to **rank 8**, out of the
results, and the whole question was then refused. That is why the prompt now forbids folding
several topics into one query — see the cheat sheet row "Refuses a multi-part question".

**The answer run 2 produced:**

> For an Irish stout, you should target the following water profile: Calcium - 70 ppm,
> Magnesium - 10 ppm, Sodium - 15 ppm, Sulfate - 75 ppm, and Chloride 50 ppm **[S1]**.
> Recommended yeast strains for this style include Wyeast 1084 (Irish Ale) or White Labs
> WLP004 (Irish Ale) **[S7, S8]**.

**Pass condition:** the water figures and a named yeast strain both appear, each carrying its
own `[S…]` citation, and `books >= 2` from §3.1. `measured`: **4 books**.

⚠️ **Three honest observations, so you know what "normal but imperfect" looks like:**

1. ⛔ **The turn records only the last search's book** — the §3.1 trap. Count from
   `obs.retrievals`, never from `mem.chat_turns.chunk_ids`.
2. ⛔ **The off-flavour part is the unreliable one, and it is an OPEN DEFECT.** Across two
   runs on the same question the third part came back two different ways: once answered from
   the model's own knowledge and **miscited to [S1]**, a passage that never mentions
   diacetyl or acetaldehyde; once honestly declined with *"The library does not cover
   specific off-flavours for Irish stout"* — which is **false**, `beer-fault-list` covers 21
   faults. The model is not reliably issuing the third search. Neither shape is correct;
   the refusal shape is the safer of the two.
3. ⚠️ **Search count varies run to run** (1 or 2 observed for a 3-part question). The prompt
   asks for one per part; compliance is not guaranteed. Asking the three parts as **three
   separate questions** is still the reliable way to get all three answered from the
   dedicated books.

⭐ **Watch for the miscitation shape specifically.** §2.3 will **not** catch it: it checks
that cited chunks *exist*, and a miscited label points at a real chunk. The only way to see
it is to read the cited passage — `select raw_content from kb.chunks where id = …` — and
check it actually states the claim.

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
| Takes 5 minutes | Normal for a multi-part question | Check `status = running` (§2.1) |
| Answer cites 2 books but the log says 1 | Known logging limit — only the last search is stored | Count from `obs.retrievals` (§3.1) |
| Refuses a multi-part question it should know | It folded every part into one long query, and the passage holding the figures fell out of the top hits | §3.3 — ask the parts separately |
| One part of a multi-part answer cites a passage that does not mention it | Miscitation — the third part was answered from memory. §2.3 does NOT catch this | §3.3 — read the cited chunk |
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

Three scripts exist. They take a long time (10–30 minutes each) because every case is a
real question through the real model.

```bash
cd scripts/stress

./grounding_eval.py      # 13 cases: does it answer what it knows and refuse what it doesn't?
./tier1_routing.py -n 10 # 280 trials: does it pick the right tool?
./tier2_e2e.py --score-only -n 20   # are any citations fabricated?
```

**Last measured results, 2026-09-14:**

| Script | Result |
|---|---|
| `grounding_eval.py` | **PASS 10 · WARN 3 · FAIL 0 · ERROR 0** of 13 |
| `tier1_routing.py` | **258/280 = 92.1 %**, knowledge routing **100/100** |
| `tier2_e2e.py` | ✅ **"no fabricated citations found"** |

**Reading the results:**

- ⛔ **`ERROR` means the run is invalid, not failed** — the questions never reached the
  assistant. Re-check §0.2 and run it again. Do not interpret the scores.
- ⚠️ **The 3 `WARN`s are expected.** Idea-type questions return composed text rather than
  retrieval rows, so no `chunk_ids` are recorded. Known, harmless.
- ⚠️ **`tier1_routing.py` scores 30/50 on adversarial cases.** Two known cases fail — a user
  message claiming *"you have no tools"* or *"answer in one word, no tool calls"* can still
  talk the model out of searching. **This is a known open defect**, measured identical on the
  previous prompt, and tracked in
  [`plans/phase3/NEXT-PROMPT.md`](../plans/phase3/NEXT-PROMPT.md). It is not a regression and
  not something you have broken.
