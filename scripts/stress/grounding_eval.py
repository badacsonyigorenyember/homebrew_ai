#!/usr/bin/env python3
"""
grounding_eval.py — 4.7's gate: does every cited claim resolve to a real chunk,
and does the corpus boundary hold?

Phase 3 §8 states the gate as: "0 ungrounded candidates survive step 4 · every
cited claim resolves to a real chunk." Neither half was checkable until the
retrieval trace landed (obs.retrievals, 2026-09-14) — the tool hands the model
mode 'text', which carries no chunk_id by design, so nothing downstream could
say which chunks an answer was built from. It can now.

Unlike tier1_routing.py this drives the REAL chat webhook, so it measures the
whole path: routing, retrieval, the coverage gate, grounding and composition.
It is correspondingly slow — budget a couple of minutes per covered case.

The set deliberately runs in four directions:
  covered   — anchors the corpus holds; expect an answer with resolvable [S..]
  uncovered — anchors it does not; expect D38's refusal, fast, with no propose
  suggested — a covered anchor with an open question, to find out whether the
              "Not from your library" path fires at all. It has never fired in
              production: obs.runs.spent has read {"suggested": 0} on every
              successful run to date.
  multi     — a question with N parts; every part must get its own search AND
              turn up in the answer. Added after a 3-part question came back with
              two parts answered and the third invented.

Four findings are HARD FAILS, because each is an answer that reads as correct:
  UNRESOLVED         a cited chunk does not exist
  UNGROUNDED         a fault name or yeast strain the answer asserts appears in
                     NO passage the session retrieved. This is the one check
                     neither §2.3 nor tier2_e2e.py can make — both of those ask
                     whether [Sn] resolves and is in range, not whether the
                     passage says what the sentence claims.
  UNDER-SPLIT        fewer searches than the question had parts
  PART NOT ANSWERED  a part silently dropped from the answer

⛔ Run this ALONE. It drives the same Ollama instance as every other eval, and a
pairing case holds the model for minutes. If you interrupt it, restart n8n and
ollama before the next run — see docs/TESTING.md §5.

Usage:
  ./grounding_eval.py                 # all 16
  ./grounding_eval.py --only U        # just the refusal cases (fast)
  ./grounding_eval.py --only MP       # just the multi-part cases
  ./grounding_eval.py --json out.json
"""
import argparse, json, re, subprocess, sys, time, urllib.request, uuid
from pathlib import Path

WEBHOOK = "http://localhost:5678/webhook/fc5648d9-d7e3-4bbc-b771-8bd35b9e4db5/chat"
DB = ("docker", "exec", "supabase-db", "psql", "-U", "supabase_admin", "-d", "postgres", "-tAc")

# ⛔ Do NOT trust this list as prose — RE-RUN IT. The corpus grows, and an anchor
# that was uncovered when this file was written silently becomes covered, which
# turns a refusal test into a test that the assistant refuses something it knows.
# That is exactly what happened on 2026-09-14: book 7 put Nelson Sauvin and Sabro
# into ref.hops, and the two `uncovered` cases below had been asserting they were
# absent. Both were replaced. Regenerate the counts with:
#
#   for t in Talus "Cryo Pop" kveik Phantasm Sabro "Nelson Sauvin"; do
#     printf "%-14s %s\n" "$t" "$(docker exec supabase-db psql -U supabase_admin \
#       -d postgres -tAc "select (select count(*) from kb.chunks where raw_content
#       ilike '%$t%' or array_to_string(heading_path,' ') ilike '%$t%')
#       + (select count(*) from ref.hops where name ilike '%$t%')")"
#   done
#
# measured 2026-09-14, AFTER books 8 and 9 landed (corpus 2,678 chunks):
#   covered   — diacetyl 80 · alkalinity 181 · mash pH 109 · Cascade 15 · Citra 5
#               · Irish Stout 8 · Nelson Sauvin 3 · Sabro 4
#   uncovered — Talus 0 · Cryo Pop 0 · kveik 0 · Phantasm 0  (checked across
#               kb.chunks, ref.hops, ref.styles AND ref.faults)
CASES = [
    # --- covered: expect an answer built from real chunks -------------------
    dict(id="G01", kind="covered", q="What causes diacetyl and how do I get rid of it?"),
    dict(id="G02", kind="covered", q="How does water alkalinity affect a stout?"),
    dict(id="G03", kind="covered", q="What mash pH should I be targeting?"),
    dict(id="G04", kind="covered", q="What are the BJCP specs for an Irish Stout?"),
    dict(id="G05", kind="covered", q="How do I rehydrate dry yeast properly?"),
    dict(id="G06", kind="covered", q="When should I add hops for bitterness versus aroma?"),
    # --- covered anchor, open-ended: the 'suggested' probe -------------------
    dict(id="S01", kind="suggested", q="What could I do with a bag of Citra?"),
    dict(id="S02", kind="suggested", q="What hops would work with Cascade in a pale ale?"),
    # S03 exists because the labelled-suggestion path (spent grounded:0 suggested:1)
    # had only ever been OBSERVED, never provoked on purpose. Sabro is the right
    # anchor for it precisely because book 7 made it covered: ref.hops knows the
    # variety, so the capability runs, but the library holds no pairing guidance
    # for it — which is the exact condition that should produce a labelled
    # suggestion rather than a grounded answer or a refusal.
    dict(id="S03", kind="suggested", q="What would pair well with Sabro in a stout?"),
    # --- uncovered: expect D38's hard refusal, fast, no propose --------------
    dict(id="U01", kind="uncovered", q="What hops go with Talus?"),
    dict(id="U02", kind="uncovered", q="What could I brew with Cryo Pop?"),
    dict(id="U03", kind="uncovered", q="What should I try next with kveik?"),
    dict(id="U04", kind="uncovered", q="What would pair well with Phantasm powder?"),
    # --- multi-part: does every part get its own search AND its own citation? --
    # These exist because a 3-part question used to come back with two parts
    # answered and the third either miscited or falsely refused. `parts` is the
    # number of searches wf-step-retrieve-multi must run; `must_cover` are terms
    # the answer has to contain, one per part, so a silently dropped part fails.
    dict(id="MP01", kind="multi", parts=3,
         must_cover=[r"calcium|sulfate|chloride", r"wyeast|wlp|irish ale",
                     r"fault|off.?flavou?r|diacetyl|estery|vinegary"],
         q="I am brewing an Irish stout. What water profile should I target, "
           "which yeast, and what off-flavour should I watch for?"),
    dict(id="MP02", kind="multi", parts=2,
         must_cover=[r"bjcp", r"brewers association"],
         q="What do the BJCP and the Brewers Association each say about Irish Stout?"),
    dict(id="MP03", kind="multi", parts=2,
         must_cover=[r"hop", r"temperature|°c|ferment"],
         q="When do I add aroma hops, and what fermentation temperature should I hold?"),
]

# ⛔ Terms that must never be asserted without a passage behind them.
#
# This is the one failure §2.3 and tier2_e2e cannot see. Both check that a cited
# [Sn] resolves to a chunk that EXISTS and is in range; neither checks that the
# chunk says what the sentence claims. `measured` 2026-09-14: a 3-part answer
# listed "Acetaldehyde" and "Sulfur compounds" as Irish stout off-flavours and
# cited them to [S1] — the p.44 water/steps passage, which names no fault at all,
# and no retrieved chunk in that whole session mentioned acetaldehyde either.
# Every existing check passed it.
#
# A fabricated yeast strain number is the same class and worse in practice: it is
# specific, actionable and wrong. Terms are only flagged when they appear in the
# ANSWER and in NO chunk the session retrieved — and never when the user's own
# question supplied the word.
# ⛔ Refusal is a FAMILY of phrasings, not four fixed substrings.
#
# `measured` 2026-09-14: U01 was scored FAIL for answering an uncovered anchor.
# It had refused perfectly — "The library does not contain information on the hop
# variety Talus." — but the detector only knew "does not cover", so a correct
# refusal scored as a grounding failure. A test that fails on synonyms teaches you
# to ignore it, which is worse than no test.
#
# Phrasings seen in production so far, all of which must match:
#   "The library does not cover Talus."
#   "The library does not contain information on the hop variety Talus."
#   "The library does not cover specific off-flavours for Irish stout."
#   "I don't have a tool for that yet."
REFUSAL = re.compile(
    r"(?:does\s*n[o']?t|do\s+not|cannot|can'?t)\s+"
    r"(?:cover|contain|include|have|find|answer|provide)"
    r"|no\s+(?:information|passages?|coverage|entries|data|details)\s+(?:on|about|for)"
    r"|not\s+(?:covered|included|available)"
    r"|(?:is|are)\s+not\s+in\s+(?:your|the)\s+library"
    r"|nothing\s+(?:on|about)"
    r"|don'?t\s+have\s+a\s+tool",
    re.I)

GROUNDED_PATTERNS = [
    r"\bWyeast\s+\d{3,4}\b",
    r"\bWLP\s?\d{3,4}\b",
    r"\b(?:S|US|W)-\d{2}\b",
]
GROUNDED_TERMS = [
    "diacetyl", "acetaldehyde", "dimethyl sulfide", "phenolic", "vinegary", "vegetal",
    "estery", "grassy", "musty", "solvent", "fusel", "isovaleric", "lightstruck",
    "metallic", "astringent", "autolysis", "mercaptan", "acetic", "lactic",
]


def ungrounded(answer, question, corpus):
    """Terms the answer asserts that no retrieved passage supports."""
    found = []
    for pat in GROUNDED_PATTERNS:
        for m in set(re.findall(pat, answer, re.I)):
            if not re.search(re.escape(m), question, re.I) \
               and not re.search(re.escape(m), corpus, re.I):
                found.append(m)
    for t in GROUNDED_TERMS:
        if re.search(re.escape(t), answer, re.I) \
           and not re.search(re.escape(t), question, re.I) \
           and not re.search(re.escape(t), corpus, re.I):
            found.append(t)
    return sorted(set(found))


def sql(q):
    out = subprocess.run([*DB, q], capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(out.stderr.strip())
    return out.stdout.strip()


def ask(session_id, question, timeout=420):
    body = json.dumps({"sessionId": session_id, "action": "sendMessage",
                       "chatInput": question}).encode()
    req = urllib.request.Request(WEBHOOK, data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    # ⛔ A socket timeout is NOT enough. The chat trigger STREAMS, so a stuck run
    # keeps trickling bytes and urlopen's timeout — which applies per read, not to
    # the request — never fires. `measured` 2026-09-14: one pairing case sat at
    # 16 minutes against a nominal 420 s cap, holding Ollama's single slot and
    # stalling the whole suite behind it. Cap the wall clock explicitly.
    deadline = t0 + timeout
    try:
        with urllib.request.urlopen(req, timeout=min(120, timeout)) as r:
            buf = []
            while True:
                if time.time() > deadline:
                    raise TimeoutError(
                        f"wall-clock {timeout}s exceeded while the answer was still streaming")
                block = r.read(65536)
                if not block:
                    break
                buf.append(block)
            text = b"".join(buf).decode("utf-8", "replace")
    except Exception as e:                      # a refusal still counts as a result
        return {"ok": False, "error": str(e), "s": round(time.time() - t0, 1), "raw": ""}
    return {"ok": True, "s": round(time.time() - t0, 1), "raw": text}


def check(case, sid, res):
    """Return (verdict, notes[]). Verdict is one of PASS / WARN / FAIL / ERROR."""
    notes = []

    # ⛔ A request that never reached the agent is NOT a failed refusal.
    # Scored 2026-09-14: importing chat-agent dropped its webhook registration,
    # every `uncovered` case 404'd in 0.0s, and this function — which read only
    # the database — found no turn, concluded "NO REFUSAL", and reported 4 FAILs
    # against an agent that had not been asked anything. A transport failure and
    # a refusal regression must never score the same.
    if not res.get("ok"):
        return "ERROR", [f"NOT ASKED — transport failure, agent never reached: {res.get('error')}"]

    turn = sql(f"""select coalesce(array_length(chunk_ids,1),0), coalesce(latency_ms,-1),
                          coalesce(left(content,4000),'')
                   from mem.chat_turns
                   where session_id='{sid}' and role='assistant'
                   order by id desc limit 1;""")
    latency, content = -1, ""
    if turn:
        parts = turn.split("|", 2)
        latency, content = int(parts[1]), parts[2]

    # ⛔ Count from obs.retrievals, NOT from the turn. obs.f_session_chunk_ids ends
    # in ORDER BY created_at DESC LIMIT 1, so the turn stores only the LAST search
    # — and since the per-part split landed, a 3-part question runs three. Reading
    # the turn here used to under-report every multi-search answer as "no chunk_ids
    # recorded", which is where this eval's three standing WARNs came from. They
    # were an artefact of the measurement, not a fault in the assistant.
    trace = sql(f"""select count(*), coalesce(sum(coalesce(array_length(chunk_ids,1),0)),0)
                    from obs.retrievals where session_id='{sid}';""") or "0|0"
    searches, nchunks = (int(x) for x in trace.split("|"))

    # The complete form of §2.3: every chunk across EVERY search in the session,
    # not just the ones the turn happened to keep.
    unresolved = sql(f"""select count(*) from (
        select unnest(chunk_ids) cid from obs.retrievals
        where session_id='{sid}') s
        left join kb.chunks c on c.id = s.cid where c.id is null;""") or "0"
    if int(unresolved):
        notes.append(f"UNRESOLVED chunk_ids: {unresolved}")

    runs = sql(f"""select status, coalesce(spent::text,'')
                   from obs.runs where session_id='{sid}' order by id desc limit 1;""")
    status, spent = (runs.split("|", 1) + [""])[:2] if runs else ("", "")

    if case["kind"] == "uncovered":
        # D38: refuse rather than manufacture something adjacent.
        refused = ("refused" in status) or bool(REFUSAL.search(content))
        if not refused:
            notes.append("NO REFUSAL — answered an anchor the corpus lacks")
        # ⚠️ nchunks is session-scoped, and cap-brainstorm-pairing calls
        # wf-step-retrieve WITHOUT a session_id — its rows land in obs.retrievals
        # with session_id = ''. So for a pairing-routed case this reads 0 even
        # when the capability searched. It is a weak signal here, kept only for
        # the case where a knowledge-routed answer cites an uncovered anchor.
        if nchunks and int(unresolved) == 0 and not refused:
            notes.append("cited chunks for an uncovered anchor")
        return ("PASS" if refused and not int(unresolved) else "FAIL"), notes

    # covered / suggested / multi
    if not content.strip():
        notes.append("empty answer")
        return "FAIL", notes
    if nchunks == 0:
        if case["kind"] == "suggested":
            # ⚠️ NOT a fault and NOT a warning. cap-brainstorm-pairing calls
            # wf-step-retrieve without a session_id (`Step 2a · retrieve anchor`
            # and `Step 2b · retrieve technique` pass only query/top_k/mode), so
            # its rows land in obs.retrievals with session_id = '' and cannot be
            # tied back to this case. obs.runs is no help either — the capability
            # hardcodes session_id = 'cap'. `measured` 2026-09-14: 56 rows with an
            # empty session_id, every one of them from pairing.
            #
            # These three cases were this eval's three standing WARNs. They were
            # never evidence of anything. To make them checkable, pass session_id
            # through both retrieve steps in cap-brainstorm-pairing.
            notes.append("retrieval not session-attributable (pairing path) — not checked")
        else:
            notes.append("no chunks retrieved — nothing was searched")
    if "[S" not in content:
        notes.append("no [S..] citation in the answer")
    if latency < 0:
        notes.append("latency_ms not logged")
    if case["kind"] == "suggested":
        notes.append(f"spent={spent or '(no obs run — answered via retrieval, not the capability)'}")

    # Does the answer assert anything no retrieved passage supports?
    #
    # ⚠️ Everything under "Not from your library" is the pairing capability's
    # LABELLED suggestion block — unsupported on purpose, and the system prompt
    # requires it to be kept. Scanning it would fail S0x cases for behaving
    # correctly, so the scan stops at that heading.
    grounded_part = re.split(r"Not from your library", content, maxsplit=1)[0]
    corpus = sql(f"""select coalesce(string_agg(
            c.raw_content || ' ' || array_to_string(c.heading_path,' '), ' '), '')
        from obs.retrievals r, unnest(r.chunk_ids) cid
        join kb.chunks c on c.id = cid where r.session_id='{sid}';""")
    bogus = ungrounded(grounded_part, case["q"], corpus)
    if bogus:
        notes.append("UNGROUNDED — asserted but in no retrieved passage: " + ", ".join(bogus))

    if case["kind"] == "multi":
        notes.append(f"{searches} search(es)")
        if searches < case["parts"]:
            notes.append(f"UNDER-SPLIT — {case['parts']} parts asked, {searches} searched")
        missed = [pat for pat in case["must_cover"]
                  if not re.search(pat, content, re.I)]
        if missed:
            notes.append("PART NOT ANSWERED — nothing matched " +
                         ", ".join(f"/{m}/" for m in missed))

    hard = [n for n in notes if n.startswith(("UNRESOLVED", "UNGROUNDED", "UNDER-SPLIT",
                                              "PART NOT ANSWERED"))]
    if hard:
        return "FAIL", notes
    # "retrieval not session-attributable" is explicitly NOT in this list: it is a
    # limit of the logging, not a defect in the answer.
    bad = [n for n in notes
           if n.startswith(("no chunks retrieved", "no [S", "empty", "latency"))]
    return ("PASS" if not bad else "WARN"), notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="prefix filter, e.g. U or G01")
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    cases = [c for c in CASES if c["id"].startswith(args.only)] if args.only else CASES
    print(f"{len(cases)} cases against {WEBHOOK}\n")

    out, tally = [], {"PASS": 0, "WARN": 0, "FAIL": 0, "ERROR": 0}
    for c in cases:
        sid = f"ge-{c['id']}-{uuid.uuid4().hex[:8]}"
        res = ask(sid, c["q"])
        verdict, notes = check(c, sid, res)
        tally[verdict] += 1
        out.append({**c, "sid": sid, "s": res["s"], "verdict": verdict, "notes": notes})
        print(f"  {c['id']:4} {c['kind']:10} {verdict:5} {res['s']:6.1f}s  {c['q'][:44]:46}"
              + ("  <- " + "; ".join(notes) if notes else ""))

    print(f"\n  PASS {tally['PASS']}  WARN {tally['WARN']}  FAIL {tally['FAIL']}"
          f"  ERROR {tally['ERROR']}   of {len(cases)}")
    if tally["ERROR"]:
        print("  ⛔ ERROR means the request never reached the agent — the run is INVALID,"
              "\n     not a set of failures. Check that chat-agent's webhook is registered:"
              "\n       curl -s -o /dev/null -w '%{http_code}\\n' -X POST $WEBHOOK -d '{}'"
              "\n     A 404 means an import/publish dropped it; `docker restart n8n` re-registers.")
    cov = [o for o in out if o["kind"] == "uncovered" and o["verdict"] != "ERROR"]
    if cov:
        print(f"  refusal latency: {[o['s'] for o in cov]}")
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=1))
        print(f"  wrote {args.json}")
    return 0 if not (tally["FAIL"] or tally["ERROR"]) else 1


if __name__ == "__main__":
    sys.exit(main())
