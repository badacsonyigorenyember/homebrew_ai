#!/usr/bin/env python3
"""
decompose_eval.py — does the question splitter split correctly?

`wf-step-retrieve-multi` decides how many searches a question gets. That decision
used to belong to the agent, which complied about two runs in three; moving it
into the workflow is what made multi-part questions answerable. It is now the
single point where a 3-part question becomes three searches — and nothing else
tested it.

This drives the decompose step ALONE, straight to Ollama. It does not touch n8n,
the agent, or the corpus, so it runs in seconds rather than the ~50 s per case a
full agent run costs. Use it as the fast gate before the slow ones:

    ./decompose_eval.py            # ~10 s
    ./grounding_eval.py            # ~10 min
    ./tier1_routing.py -n 10       # ~20 min

⛔ The prompt is READ FROM THE WORKFLOW, not copied here. A copy would drift, and
a drifted copy tests nothing — it would keep passing while the live splitter
changed underneath it. If the workflow's node shape changes this script fails
loudly rather than silently testing a stale string.

Two rules carry most of the weight, both learned the hard way on 2026-09-14:

  parts    A question asking for N things must yield N queries, and a question
           asking for one thing must yield exactly ONE. Over-splitting is a real
           failure, not a harmless one: it spends a search per invented topic.

  faults   A fault query must NOT carry the beer style name. `beer-fault-list` is
           written style-agnostically, so "Irish stout off-flavours" retrieves the
           style guide and the off-flavour part gets falsely refused, while
           "common beer faults and off-flavors" retrieves the fault list. This is
           the exception to repeating the style in every query, and it is the one
           the model gets wrong when the prompt does not spell it out.

Usage:
  ./decompose_eval.py              # one pass
  ./decompose_eval.py -n 5         # 5 passes, to see run-to-run variance
  ./decompose_eval.py --json out.json
"""
import argparse, json, re, sys, time, urllib.request
from pathlib import Path

OLLAMA = "http://localhost:11434/api/chat"
WORKFLOW = (Path(__file__).resolve().parents[2]
            / "n8n/demo-data/workflows/wf-step-retrieve-multi.json")

# Matches a query that is about faults rather than about a style's recipe.
FAULT_Q = re.compile(r"fault|off.?flavou?r|taint", re.I)
# Style/ingredient names that must never be attached to a fault query.
STYLE_WORDS = re.compile(r"irish|stout|lager|pilsner|pils|saison|ipa|porter|weiss|witbier", re.I)


def load_prompt():
    """Pull the live decompose prompt out of the workflow's Code node."""
    if not WORKFLOW.exists():
        sys.exit(f"decompose_eval: workflow not found at {WORKFLOW}")
    wf = json.loads(WORKFLOW.read_text())
    try:
        code = next(n for n in wf["nodes"]
                    if n["name"] == "Build decompose prompt")["parameters"]["jsCode"]
    except StopIteration:
        sys.exit("decompose_eval: no 'Build decompose prompt' node — workflow shape changed")
    m = re.search(r"content: (\".*?\") \+ subject", code, re.S)
    if not m:
        sys.exit("decompose_eval: could not find the prompt literal in the Code node "
                 "— the `content: \"...\" + subject` shape changed")
    model = re.search(r"model: '([^']+)'", code)
    return json.loads(m.group(1)), (model.group(1) if model else "gemma4:12b")


def decompose(prompt, model, question, timeout=180):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt + question}],
        "options": {"temperature": 0, "num_predict": 200},
        "stream": False,
        # Mirrors the workflow. Without it gemma4 answers inside `thinking` and
        # returns empty content — see docs/TESTING.md §2.6.
        "think": False,
        "format": {"type": "object",
                   "properties": {"queries": {"type": "array", "items": {"type": "string"}}},
                   "required": ["queries"]},
    }
    req = urllib.request.Request(OLLAMA, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    # A transport failure must not take the whole suite down with a traceback and
    # lose every result before it. The usual cause is contention: a slow agent run
    # (grounding_eval's pairing cases take minutes) holds the model, and these
    # calls queue behind it. Run this BEFORE the slow evals, not alongside them.
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = json.loads(r.read())
    except Exception as e:
        return None, round(time.time() - t0, 1), (
            f"NOT ASKED — {type(e).__name__}: {e}. Is ollama busy with another eval?")
    content = raw.get("message", {}).get("content") or ""
    took = round(time.time() - t0, 1)
    if not content.strip():
        # The §2.6 quirk. Worth naming exactly, because an empty split degrades to
        # a single search and looks like "the model just chose not to split".
        return None, took, "EMPTY content — model answered in `thinking`; is think:false still set?"
    try:
        return [str(q).strip() for q in json.loads(content)["queries"] if str(q).strip()], took, None
    except Exception as e:
        return None, took, f"unparseable: {e}: {content[:120]}"


CASES = [
    # id, question, expected part count, [regexes each matching >=1 query]
    dict(id="D01", parts=3, hits=[r"water", r"yeast", r"fault|off.?flavou?r"],
         q="I am brewing an Irish stout. What water profile should I target, "
           "which yeast, and what off-flavour should I watch for?"),
    dict(id="D02", parts=1, hits=[r"diacetyl"],
         q="What causes diacetyl and how do I get rid of it?"),
    dict(id="D03", parts=1, hits=[r"foreign extra stout|grain bill"],
         q="Give me a foreign extra stout grain bill."),
    dict(id="D04", parts=2, hits=[r"bjcp", r"brewers association|\bba\b"],
         q="What do the BJCP and the Brewers Association each say about Irish Stout?"),
    dict(id="D05", parts=1, hits=[r"mash pH"],
         q="what mash pH should I target"),
    dict(id="D06", parts=1, hits=[r"citra"],
         q="What are the alpha acids of Citra?"),
    dict(id="D07", parts=2, hits=[r"water", r"yeast"],
         q="For a Czech pilsner, what water profile and which yeast should I use?"),
    # A fault question with a style in it, but only ONE part: the style must still
    # be stripped from the query, and it must not be split into two.
    dict(id="D08", parts=1, hits=[r"fault|off.?flavou?r"],
         q="What off-flavours should I watch for in a lager?"),
    dict(id="D09", parts=2, hits=[r"hop", r"ferment|temperature"],
         q="When do I add aroma hops, and what fermentation temperature should I hold?"),
    # Deliberately wordy but single-topic — over-splitting here wastes a search.
    dict(id="D10", parts=1, hits=[r"alkalinity|water"],
         q="I keep reading about water alkalinity and I do not really understand how it "
           "affects my beer. Can you explain it?"),
]


def check(case, queries):
    """Return notes[]. Empty notes means the case passed."""
    notes = []
    if len(queries) != case["parts"]:
        notes.append(f"expected {case['parts']} part(s), got {len(queries)}: {queries}")

    for pat in case["hits"]:
        if not any(re.search(pat, q, re.I) for q in queries):
            notes.append(f"no query matched /{pat}/")

    # The fault rule, checked on every case that produced a fault query.
    for q in queries:
        if FAULT_Q.search(q) and STYLE_WORDS.search(q):
            notes.append(f"fault query carries a style name — retrieval will return the "
                         f"style guide, not beer-fault-list: {q!r}")

    if len(queries) > 3:
        notes.append(f"more than 3 queries ({len(queries)}) — the workflow truncates to 3, "
                     f"so the tail is silently dropped")
    return notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=1, help="passes over the case set")
    ap.add_argument("--only", default="", help="prefix filter, e.g. D01")
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    prompt, model = load_prompt()
    cases = [c for c in CASES if c["id"].startswith(args.only)] if args.only else CASES
    print(f"{len(cases)} cases x {args.n} pass(es) against {model} via {OLLAMA}")
    print(f"prompt read from {WORKFLOW.name} ({len(prompt)} chars)\n")

    out, failed, total, errors = [], 0, 0, 0
    for p in range(args.n):
        if args.n > 1:
            print(f"--- pass {p + 1}")
        for c in cases:
            queries, took, err = decompose(prompt, model, c["q"])
            total += 1
            notes = [err] if err else check(c, queries)
            errored = bool(err) and err.startswith("NOT ASKED")
            ok = not notes
            failed += 0 if ok else 1
            if errored:
                errors += 1
            out.append({**{k: c[k] for k in ("id", "parts", "q")},
                        "pass": p + 1, "queries": queries, "s": took,
                        "verdict": "PASS" if ok else ("ERROR" if errored else "FAIL"),
                        "notes": notes})
            print(f"  {c['id']:4} {'PASS' if ok else ('ERR ' if errored else 'FAIL'):4} {took:5.1f}s  "
                  f"{c['q'][:44]:46} -> {queries}")
            for n in notes:
                print(f"       ⛔ {n}")

    print(f"\n  PASS {total - failed}  FAIL {failed - errors}  ERROR {errors}   of {total}")
    if errors:
        print("  ⛔ ERROR means the splitter was never reached — the run is INVALID, not"
              "\n     failed. Ollama was busy or down. Do not interpret the scores; re-run"
              "\n     this on its own, before the slow evals.")
    if args.n > 1:
        by = {}
        # Errored passes carry no split at all — counting them would report
        # "variance" for a case that was simply never asked.
        for o in out:
            if o["verdict"] == "ERROR":
                continue
            by.setdefault(o["id"], set()).add(tuple(o["queries"] or []))
        unstable = {k: len(v) for k, v in by.items() if len(v) > 1}
        if unstable:
            print(f"  ⚠️  run-to-run variance (distinct splits per case): {unstable}")
        else:
            print("  ✅ every case produced an identical split on every pass")
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=1))
        print(f"  wrote {args.json}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
