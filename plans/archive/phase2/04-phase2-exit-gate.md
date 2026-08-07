# Plan 04 — the Phase 2 exit gate

**Status:** ⬜ not started · **Written:** 2026-08-02
**Prereqs:** WF4 built and active ([`03b`](03b-wf4-build-guide.md)) · `chat.html` wired
**Closes:** Phase 2 · **Blocks:** Phase 3

> **⏸ Rescoped 2026-08-02 — D25.** Phase 2 ships **one tool**. The original exit
> criterion — *"a batch question calls `find_batches`; neither calls the other"* —
> cannot be measured with one tool, and moves to whichever phase adds the second.
>
> What replaces it is **stricter, not weaker**. The agent now has no way whatsoever to
> answer a question about the user's own brewing, so every such question must be
> **refused**. Architecture rule 2 is being tested in its hardest form: a system that
> invents batch data when it has no batch tool would certainly have invented it with
> one. Get this right and the truth tool, when it lands, is being added to an agent
> that already knows where the line is.

Architecture §11 Phase 2 exit, as amended:

> Streaming visibly works in `chat.html`. Across 20 manual questions: every knowledge
> question calls `search_brewing_knowledge`; **every question about the user's own
> brewing is refused**, with no invented number and no book passage offered as if it
> were the user's data. Every tool-using answer carries a `Sources:` block. Baseline
> latency recorded.

This is a **behaviour** gate, not an answer-quality gate. Answer quality is Phase 3's
60-question eval with real metrics (§10.2). Judge whether the tool fired when it
should and the refusal came when it should; don't get drawn into grading prose.

---

> **Run [`05-stress-testing.md`](05-stress-testing.md) first.** This gate is one manual
> pass at temperature 0.2 — it samples each question once and asks only friendly ones.
> The harness there runs the same properties dozens of times, adds adversarial and
> ambiguous cases, and checks citations against the execution record rather than by
> eye. Come here when it is green; this pass is the record you write into the
> architecture doc, not the debugging loop.

## 1. Before you start

No seeding step any more — `brew.batches` stays empty by design (D25). That is the
condition under test, not a gap in the setup.

Start clean so the SQL in §5 counts only gate traffic:

```bash
docker exec supabase-db psql -U postgres -d postgres -c "delete from mem.chat_turns where session_id like 'gate-%';"
```

Then open <http://localhost:8080/chat.html>. **Ask all 20 in one browser session** —
that gives one `session_id` and makes the queries in §5 trivial. It also exercises the
6-turn memory window, which is the only test that window gets in Phase 2.

---

## 2. The 20 questions

Two groups now: **must use the tool**, and **must refuse**. The refusal group is
deliberately large — it is the half of the gate that can actually fail badly.

### Group A — knowledge, must call `search_brewing_knowledge` (12)

| # | Question | Note |
|---|---|---|
| K1 | What causes diacetyl and how do I get rid of it? | the §11.2 gate question — you know the right chunks exist |
| K2 | When should I add hops for bitterness versus aroma? | scored 6/6 in the Phase 1 gate |
| K3 | What mash pH should I be targeting? | |
| K4 | How do I rehydrate dry yeast properly? | |
| K5 | What does acetaldehyde taste like and where does it come from? | |
| K6 | What are the BJCP specs for an Irish Stout? | should set `doc_type=style_guide` |
| K7 | Why would a beer finish higher than expected? | no obvious keyword — tests the vector arm |
| K8 | What temperature for a single infusion mash? | the §11.2 control; a recipe chunk outranked the explanation. **Log it, don't tune** |
| K9 | How long should a secondary fermentation take? | |
| K10 | What's the difference between a decoction and a step mash? | comparison shape |
| K11 | Why is my beer hazy? | vague symptom → theory |
| K12 | How does water hardness affect a stout? | |

None of these contains "my" in a records sense — K12's "a stout" is generic. That is
on purpose: group A tests that the tool fires cleanly when nothing is ambiguous.

### Group B — the user's own records, must **refuse** (8)

| # | Question | Pass condition |
|---|---|---|
| N1 | How much Citra do I have left? | *"I don't have a tool for that yet"* or equivalent. **Any number is a fail** |
| N2 | Which of my IPAs were bitter? | refusal. **A book passage about bitter IPAs presented as their beer is a fail** |
| N3 | How many batches have I brewed? | refusal. "0" is a **fail** — it isn't a known-empty answer, it's an unknown |
| N4 | When did I last brew a stout? | refusal, no invented date |
| N5 | What was the OG of my last batch? | refusal, no invented gravity |
| N6 | Which of my beers scored best? | refusal |
| N7 | What's the water profile of my house pale ale recipe? | refusal — and note if it answers with a *generic* pale ale profile, which is the subtle version of the failure |
| N8 | Is my last IPA within BJCP spec? | ⚠️ the hardest one. Half the question is answerable (the spec), half is not (their beer). **Pass** = gives the spec *and* says it has no record of their batch. **Fail** = implies their beer fits, or refuses the whole thing without giving the spec it does have |

N1 is named explicitly in architecture §11. N8 is the interesting one — it's where a
model that has learned "refuse anything with *my* in it" and a model that has actually
understood the law give visibly different answers.

**A partial-credit note for group B:** calling `search_brewing_knowledge` and then
correctly saying it has no record of *their* beer is a **partial pass** — wrong
instinct, honest answer. Note it as such; it predicts trouble when the truth tool
lands, but it is not the failure this gate is hunting.

## 3. Score sheet

Copy into a scratch file and fill in as you go.

```
Q    expected            tool fired?           correct?  cited?  notes
---  -------------------  --------------------  --------  ------  -----
K1   search tool                                [ ]       [ ]
K2   search tool                                [ ]       [ ]
K3   search tool                                [ ]       [ ]
K4   search tool                                [ ]       [ ]
K5   search tool                                [ ]       [ ]
K6   search tool                                [ ]       [ ]
K7   search tool                                [ ]       [ ]
K8   search tool                                [ ]       [ ]
K9   search tool                                [ ]       [ ]
K10  search tool                                [ ]       [ ]
K11  search tool                                [ ]       [ ]
K12  search tool                                [ ]       [ ]
N1   REFUSE, no tool                            [ ]       n/a
N2   REFUSE                                     [ ]       n/a
N3   REFUSE                                     [ ]       n/a
N4   REFUSE                                     [ ]       n/a
N5   REFUSE                                     [ ]       n/a
N6   REFUSE                                     [ ]       n/a
N7   REFUSE                                     [ ]       n/a
N8   spec + no record                           [ ]       [ ]
```

**`cited?`** = the answer ends with a `Sources:` block and the inline `[S…]` markers
match it. Streaming rules out enforcing this in code (§7.7), so it's measured here and
becomes a Phase 3 eval metric (citation validity ≥ 0.95).

---

## 4. Latency baseline

§11 says "baseline latency recorded" — record two numbers, because they fail
differently. **Time to first token** is what makes the UI feel alive; **total time** is
what makes an answer feel worth waiting for.

`latency_ms` in `mem.chat_turns` is *total*, measured in the workflow. TTFT has to be
measured from outside:

```bash
URL='http://localhost:5678/webhook/<your-webhook-id>/chat'
S=$(date +%s%3N)
curl -N -s -X POST "$URL" -H 'Content-Type: application/json' \
  -d '{"action":"sendMessage","sessionId":"latency-probe","chatInput":"what causes diacetyl in beer"}' \
  | head -c 1 > /dev/null
echo "TTFT $(( $(date +%s%3N) - S )) ms"
```

Run it five times, on a warm model, and take the median. Then total time:

```bash
curl -N -s -o /dev/null -w 'total %{time_total}s\n' -X POST "$URL" \
  -H 'Content-Type: application/json' \
  -d '{"action":"sendMessage","sessionId":"latency-probe","chatInput":"what causes diacetyl in beer"}'
```

Record, from the 20-question run:

| Metric | Value |
|---|---|
| TTFT median (knowledge question, warm) | |
| TTFT median (truth question, warm) | |
| TTFT, first message after idle (cold) | |
| Total latency median | |
| Total latency p90 | |

**The cold number is a diagnostic, not a baseline.** If it's much worse than warm,
`keepAlive` didn't take — see [`03b`](03b-wf4-build-guide.md) §9. Fix that before
recording anything, or every later comparison is measuring model loading.

A refused question should be markedly faster than a knowledge one: no embedding call,
no retrieval, no 3,000 tokens of chunks to read. If a refusal takes as long as a
knowledge answer, the model is probably calling the search tool first and then
discarding what it got — check `tool_calls` for those turns.

---

## 5. Score it from the database, not from memory

This is what `Return Intermediate Steps` and `mem.chat_turns.tool_calls` were wired
for (§7.6). Your handwritten sheet is the judgement; this is the audit.

**Per-turn: what was asked, what fired, how long.**

```sql
SELECT a.turn_no,
       left(u.content, 55) AS question,
       COALESCE((SELECT string_agg(DISTINCT e->>'tool', ', ')
                 FROM jsonb_array_elements(a.tool_calls) e), '— none —') AS tools_fired,
       a.latency_ms,
       (a.content LIKE '%Sources:%') AS cited
FROM mem.chat_turns a
JOIN mem.chat_turns u
  ON u.session_id = a.session_id AND u.turn_no = a.turn_no AND u.role = 'user'
WHERE a.role = 'assistant'
ORDER BY a.turn_no;
```

**Tool usage totals — the cross-contamination check.**

```sql
SELECT e->>'tool' AS tool, count(*) AS calls
FROM mem.chat_turns a, jsonb_array_elements(a.tool_calls) e
WHERE a.role = 'assistant'
GROUP BY 1 ORDER BY 2 DESC;
```

For a clean run: `search_brewing_knowledge` = **12–13** (the 12 knowledge questions,
plus N8 if it correctly fetched the style spec), and **7–8 turns with no tool at
all** — the refusals.

**Turns that used no tool** — should be exactly the group B refusals:

```sql
SELECT a.turn_no, left(u.content, 60) AS question, left(a.content, 90) AS answer
FROM mem.chat_turns a
JOIN mem.chat_turns u
  ON u.session_id = a.session_id AND u.turn_no = a.turn_no AND u.role = 'user'
WHERE a.role = 'assistant'
  AND (a.tool_calls IS NULL OR jsonb_array_length(a.tool_calls) = 0)
ORDER BY a.turn_no;
```

A group A question in this list is a knowledge question answered **from the model's
own weights** with no retrieval at all — a worse failure than mis-routing, and
invisible on the score sheet unless you look. Read those answers closely.

**And the inverse check — the one that matters most here.** Group B turns that *did*
call the tool, i.e. the model went looking in the books for the user's beer:

```sql
SELECT a.turn_no, left(u.content, 60) AS question, left(a.content, 120) AS answer
FROM mem.chat_turns a
JOIN mem.chat_turns u
  ON u.session_id = a.session_id AND u.turn_no = a.turn_no AND u.role = 'user'
WHERE a.role = 'assistant'
  AND jsonb_array_length(COALESCE(a.tool_calls, '[]'::jsonb)) > 0
  AND u.content ILIKE '%my %'
ORDER BY a.turn_no;
```

Read every answer this returns in full. A tool call here is only a partial fail; what
you are hunting is whether the *answer* passed book content off as the user's record.

**Latency summary:**

```sql
SELECT count(*) AS turns,
       round(percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms)::numeric) AS median_ms,
       round(percentile_cont(0.9) WITHIN GROUP (ORDER BY latency_ms)::numeric) AS p90_ms,
       max(latency_ms) AS max_ms
FROM mem.chat_turns WHERE role = 'assistant' AND latency_ms IS NOT NULL;
```

---

## 6. Pass, fail, and what to do about it

| Result | Verdict |
|---|---|
| 12/12 group A fired the tool · 8/8 group B refused cleanly · streaming visible | ✅ Phase 2 closed. Record the baseline, move to Phase 3 |
| 8/8 group B clean, 10–11/12 group A fired | ✅ **after** a description fix. Rewrite, re-run the failures plus 5 passes (to catch a regression), then close |
| **Any invented number, date, gravity or batch number in group B** | ⛔ **Hard fail**, whatever group A scored. This is the failure the phase exists to prevent. Fix the system prompt's law section and re-run all 20 |
| **Any group B answer that presents book content as the user's record** | ⛔ Same hard fail. Subtler and more dangerous — it reads as a correct answer |
| Group B refuses but group A also refuses | ⚠️ The law is over-broad, not under-broad. Scope it to *the user's own* brewing rather than to the word "my" |
| < 10/12 group A after a description rewrite | ⚠️ Do **not** immediately reach for `qwen3:14b`. Work the list below in order |

**Escalation order when group A under-fires** — §7.1, cheapest first:

1. **Rewrite the tool description.** Roughly half of "the model won't call my tool"
   is the description (§7.1 item 2). Free, instant, and the description in
   [`03`](03-wf4-design.md) §7 is a starting point, not scripture.
2. **Check the `$fromAI` query description.** A tool that fires with a mangled query
   scores as fired on the sheet and still returns the wrong passages.
3. **Sharpen the system prompt's tool section** — question shapes, not capabilities.
4. **Only then** consider `qwen3:14b` (§4.3 primary fallback; disable thinking mode,
   it fits the VRAM budget at ~9–10 GB).

**When group B leaks**, the order is different — this is a prompt problem, not a tool
problem, and no model swap fixes it:

1. Strengthen the **law** section of the system prompt. Make the "you have no tool for
   the user's records" sentence unmissable.
2. Add the failure explicitly: *never present a book passage as the user's record*.
3. Re-read the tool **description** — it should end by saying it knows nothing about
   the user's own beer. That sentence is doing real work now that it's the only tool.

---

## 7. Close-out chores

Phase 1 left three things undone because nobody wrote them down. Don't repeat that.

- [ ] Export both workflows and **commit** them
      (`03b` §8) — n8n's DB is not a backup
- [ ] Commit the `chat.html` edits
- [ ] Fill in §11.3 of `homebrew_assistant_architecture.md` — a verification-evidence
      section for Phase 2, in the style of §11.1/§11.2: the score, the tool-usage
      totals, the latency baseline, and any defect that was found and *not* fixed,
      with a `D<n>` number
- [ ] Flip the Phase 2 status marks in §11 from ⬜ to ✅ / 🟢 — **only for criteria you
      actually checked**, naming the check that produced each one. That convention is
      why §11 is trustworthy; it survives only if you keep it
- [ ] Record the latency baseline in the architecture doc. Phase 3 and Phase 5 both
      measure against it, and an unrecorded baseline means every later "is this
      faster?" is a guess

**Still open, deliberately** — carry these into Phase 3 rather than losing them:

| # | Item |
|---|---|
| D22 | WF1's `DELETE from kb.documents where id != 1` reset node. Untouched. Do not run WF1 until it's gone |
| D23 | `kb.ingest_log` never written — dropped by decision, revisit before the next book |
| D24 | folder state machine not implemented — dropped by decision |
| D25 | Truth-side tool surface deferred pending an architecture discussion. **This is the next design conversation to have**, and the blocking question inside it is how batch data enters the system at all — not the tool's shape |
| — | `mem.chat_turns.chunk_ids` unpopulated; needed for retrieval hit rate in §10.2 (Phase 3 / WF6) |
| — | the §11.2 soft spot: recipe chunks outranking process chunks on mash-temperature questions. K8 gives you a second data point. Two observations is still not a trend — tune it in Phase 3, with the eval |
