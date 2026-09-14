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

The set deliberately runs in both directions:
  covered   — anchors the corpus holds; expect an answer with resolvable [S..]
  uncovered — anchors it does not; expect D38's refusal, fast, with no propose
  suggested — a covered anchor with an open question, to find out whether the
              "Not from your library" path fires at all. It has never fired in
              production: obs.runs.spent has read {"suggested": 0} on every
              successful run to date.

Usage:
  ./grounding_eval.py                 # all 13
  ./grounding_eval.py --only U        # just the refusal cases (fast)
  ./grounding_eval.py --json out.json
"""
import argparse, json, subprocess, sys, time, urllib.request, uuid
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
]


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
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            text = r.read().decode("utf-8", "replace")
    except Exception as e:                      # a refusal still counts as a result
        return {"ok": False, "error": str(e), "s": round(time.time() - t0, 1), "raw": ""}
    return {"ok": True, "s": round(time.time() - t0, 1), "raw": text}


def check(case, sid, res):
    """Return (verdict, notes[]). Verdict is one of PASS / WARN / FAIL."""
    notes = []

    turn = sql(f"""select coalesce(array_length(chunk_ids,1),0), coalesce(latency_ms,-1),
                          coalesce(left(content,4000),'')
                   from mem.chat_turns
                   where session_id='{sid}' and role='assistant'
                   order by id desc limit 1;""")
    nchunks, latency, content = 0, -1, ""
    if turn:
        parts = turn.split("|", 2)
        nchunks, latency, content = int(parts[0]), int(parts[1]), parts[2]

    # Every chunk_id the turn recorded must exist. This is the literal gate.
    unresolved = sql(f"""select count(*) from (
        select unnest(chunk_ids) cid from mem.chat_turns
        where session_id='{sid}' and role='assistant') s
        left join kb.chunks c on c.id = s.cid where c.id is null;""") or "0"
    if int(unresolved):
        notes.append(f"UNRESOLVED chunk_ids: {unresolved}")

    runs = sql(f"""select status, coalesce(spent::text,'')
                   from obs.runs where session_id='{sid}' order by id desc limit 1;""")
    status, spent = (runs.split("|", 1) + [""])[:2] if runs else ("", "")

    if case["kind"] == "uncovered":
        # D38: refuse rather than manufacture something adjacent.
        refused = ("refused" in status) or ("nothing on" in content) or \
                  ("does not cover" in content) or ("can't answer" in content)
        if not refused:
            notes.append("NO REFUSAL — answered an anchor the corpus lacks")
        if nchunks and int(unresolved) == 0 and not refused:
            notes.append("cited chunks for an uncovered anchor")
        return ("PASS" if refused and not int(unresolved) else "FAIL"), notes

    # covered / suggested
    if not content.strip():
        notes.append("empty answer")
        return "FAIL", notes
    if nchunks == 0:
        notes.append("no chunk_ids recorded — retrieval trace did not join")
    if "[S" not in content:
        notes.append("no [S..] citation in the answer")
    if latency < 0:
        notes.append("latency_ms not logged")
    if case["kind"] == "suggested":
        notes.append(f"spent={spent or '(no obs run — answered via retrieval, not the capability)'}")

    bad = [n for n in notes if n.startswith(("UNRESOLVED", "no ", "empty", "latency"))]
    return ("PASS" if not bad else "WARN"), notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="prefix filter, e.g. U or G01")
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    cases = [c for c in CASES if c["id"].startswith(args.only)] if args.only else CASES
    print(f"{len(cases)} cases against {WEBHOOK}\n")

    out, tally = [], {"PASS": 0, "WARN": 0, "FAIL": 0}
    for c in cases:
        sid = f"ge-{c['id']}-{uuid.uuid4().hex[:8]}"
        res = ask(sid, c["q"])
        verdict, notes = check(c, sid, res)
        tally[verdict] += 1
        out.append({**c, "sid": sid, "s": res["s"], "verdict": verdict, "notes": notes})
        print(f"  {c['id']:4} {c['kind']:10} {verdict:5} {res['s']:6.1f}s  {c['q'][:44]:46}"
              + ("  <- " + "; ".join(notes) if notes else ""))

    print(f"\n  PASS {tally['PASS']}  WARN {tally['WARN']}  FAIL {tally['FAIL']}"
          f"   of {len(cases)}")
    cov = [o for o in out if o["kind"] == "uncovered"]
    if cov:
        print(f"  refusal latency: {[o['s'] for o in cov]}")
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=1))
        print(f"  wrote {args.json}")
    return 0 if not tally["FAIL"] else 1


if __name__ == "__main__":
    sys.exit(main())
