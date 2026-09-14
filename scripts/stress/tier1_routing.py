#!/usr/bin/env python3
"""
tier1_routing.py — stress the agent's DECISION layer, without n8n in the way.

What this tests: does the model call the tool when it should, refuse when it should,
and extract a sane query argument — repeatedly, so flakiness at temperature 0.2 shows
up as a number instead of a surprise.

What it does NOT test: retrieval quality, output shaping, streaming, memory, or the
n8n wiring. That is tier 2 (`tier2_e2e.py`), which is slower and needs the chat
webhook. Iterate on the prompt here; confirm end to end there.

The system prompt, model, model options and tool description are read from the LIVE
n8n workflow, so this always tests what is actually deployed — not a copy that has
drifted. Nothing is mocked except the tool's return value, which is irrelevant to a
routing decision the model makes before it sees any result.

Usage:
  ./tier1_routing.py                     # 3 reps of every case
  ./tier1_routing.py -n 10               # 10 reps — flakiness shows up here
  ./tier1_routing.py -c knowledge,personal
  ./tier1_routing.py --temp 0.0          # is the flakiness sampling, or the prompt?
  ./tier1_routing.py --json out.json     # machine-readable, for diffing runs
"""
import argparse, json, re, subprocess, sys, time, urllib.request
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
N8N_DB_CONTAINER = "aihomebrewassistant-postgres-1"
OLLAMA = "http://localhost:11434/api/chat"
WORKFLOW = "chat-agent"


def load_deployed_config():
    """Read model, options, system prompt and tool description out of the live n8n DB."""
    raw = subprocess.run(
        ["docker", "exec", N8N_DB_CONTAINER, "psql", "-U", "root", "-d", "n8n", "-tAc",
         f"select nodes from workflow_entity"
         f" where name='{WORKFLOW}' and \"isArchived\" = false;"],
        capture_output=True, text=True, check=True).stdout.strip()
    if not raw:
        sys.exit(f"Workflow '{WORKFLOW}' not found in the n8n database.")
    # Archiving a workflow leaves its row in place, so the filter above is not enough:
    # two live workflows sharing a name return two JSON documents and json.loads dies
    # with 'Extra data'. Name the fault instead.
    if len(raw.splitlines()) > 1:
        sys.exit(f"{len(raw.splitlines())} live workflows are named '{WORKFLOW}'. "
                 "Delete the duplicates — archiving does not remove the row.")
    nodes = json.loads(raw)

    def find(suffix):
        hits = [n for n in nodes if n["type"].endswith(suffix)]
        if not hits:
            sys.exit(f"No '{suffix}' node in '{WORKFLOW}'. Has it been renamed?")
        return hits[0]

    agent, llm = find(".agent"), find(".lmChatOllama")

    # Phase 2 could only ever measure one tool. Two are bound now, so declare
    # both — a routing score taken against a single tool is not the score the
    # deployed agent gets. The model-visible arguments are exactly those the
    # node fills from $fromAI(); top_k, mode and session_id are set statically
    # and the model never sees them.
    tools = [n for n in nodes if n["type"].endswith("toolWorkflow")]
    if not tools:
        sys.exit(f"No '.toolWorkflow' node in '{WORKFLOW}'. Has it been renamed?")
    tool = tools[0]
    opts = llm.get("parameters", {}).get("options", {})
    sysmsg = agent["parameters"]["options"].get("systemMessage", "")
    # The System Message is stored as an n8n expression; strip the leading '=' and
    # resolve the one expression it contains so the model sees a real date.
    sysmsg = re.sub(r"^=", "", sysmsg)
    sysmsg = re.sub(r"\{\{[^}]*\$now[^}]*\}\}", time.strftime("%Y-%m-%d"), sysmsg)

    return {
        "model": llm["parameters"].get("model", "gemma4:12b"),
        "num_ctx": int(opts.get("numCtx", 2048)),
        "temperature": float(opts.get("temperature", 0.7)),
        "think": bool(opts.get("think", False)),
        "system": sysmsg,
        # The tool name the model actually sees is the NODE name, sanitised.
        "tool_name": re.sub(r"[^A-Za-z0-9_-]", "_", tool["name"]),
        "tool_desc": tool["parameters"].get("description", ""),
        "tools": [_declare(t) for t in tools],
    }


def _declare(node):
    """Build one OpenAI-style function declaration from a toolWorkflow node."""
    vals = (node["parameters"].get("workflowInputs") or {}).get("value") or {}
    props = {k: {"type": "string"} for k, v in vals.items()
             if isinstance(v, str) and "$fromAI(" in v}
    if not props:
        props = {"query": {"type": "string"}}
    return {"type": "function", "function": {
        "name": re.sub(r"[^A-Za-z0-9_-]", "_", node["name"]),
        "description": node["parameters"].get("description", ""),
        "parameters": {"type": "object", "properties": props,
                       "required": sorted(props)}}}


def ask(cfg, question, temperature):
    body = {
        "model": cfg["model"], "stream": False, "think": cfg["think"],
        "options": {"temperature": temperature, "num_ctx": cfg["num_ctx"]},
        "messages": [{"role": "system", "content": cfg["system"]},
                     {"role": "user", "content": question}],
        "tools": cfg["tools"],
    }
    t0 = time.time()
    req = urllib.request.Request(OLLAMA, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read())
    msg = d.get("message", {})
    tcs = msg.get("tool_calls") or []
    return {
        "called": bool(tcs),
        "tool": tcs[0]["function"]["name"] if tcs else None,
        "args": tcs[0]["function"]["arguments"] if tcs else None,
        "content": msg.get("content") or "",
        "ms": int((time.time() - t0) * 1000),
    }


REFUSAL = re.compile(r"don'?t have a tool|no record|do not have access|not in the library",
                     re.I)
# An [S1] marker is only legitimate if a tool actually ran.
CITATION = re.compile(r"\[S\d+\]")
# Asking the user to narrow a one-word question is a legitimate no-tool response;
# it is not the same as answering from memory.
CLARIFY = re.compile(r"please specify|could you clarify|which .{0,30}\?|what specific",
                     re.I)


def score(case, res):
    """Return (ok, reasons[]). A case can fail for more than one reason."""
    bad = []
    want = case.get("tool")
    if want is not False and want != "either" and not res["called"]:
        bad.append("tool not called")
    if want is False and res["called"]:
        bad.append("tool called on a personal question")

    if case.get("refuse") and not REFUSAL.search(res["content"]):
        bad.append("no refusal wording")

    # Fabricated provenance: [S1] in an answer that called no tool.
    if not res["called"] and CITATION.search(res["content"]):
        bad.append("cited [S] with no tool call")

    if case.get("forbid") and re.search(case["forbid"], res["content"]):
        bad.append("leaked forbidden content")

    # A missing tool call is not one failure mode but two, and they are not
    # equally bad: refusing to answer is safe-but-unhelpful, while answering the
    # brewing question anyway is an unsourced fabrication. The score cannot tell
    # them apart — measured 2026-09-14, prompt v2 scored exactly what v3 scored
    # while answering "mash pH?" with a bare "5.2-5.8" and no tool call. Report
    # the distinction separately rather than folding it into the total.
    if want is True and not res["called"] and res["content"].strip():
        if not REFUSAL.search(res["content"]) and not CLARIFY.search(res["content"]):
            bad.append("ANSWERED FROM MEMORY")

    if res["called"]:
        a = res["args"] or {}
        q = a.get("query") or a.get("question")
        if not isinstance(q, str) or not q.strip():
            bad.append("empty/missing query arg")
        elif len(q) > 200:
            bad.append("query arg absurdly long")
    return (not bad), bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--reps", type=int, default=3)
    ap.add_argument("-c", "--cats", default="")
    ap.add_argument("--temp", type=float, default=None,
                    help="override temperature; use 0.0 to separate sampling noise from prompt bugs")
    ap.add_argument("--cases", default=str(HERE / "cases.jsonl"))
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    cfg = load_deployed_config()
    temp = args.temp if args.temp is not None else cfg["temperature"]
    cases = [json.loads(l) for l in Path(args.cases).read_text().splitlines() if l.strip()]
    if args.cats:
        keep = set(args.cats.split(","))
        cases = [c for c in cases if c["cat"] in keep]

    print(f"tools={[t['function']['name'] for t in cfg['tools']]}")
    print(f"model={cfg['model']}  num_ctx={cfg['num_ctx']}  temp={temp}  "
          f"tool={cfg['tool_name']}  system_prompt={len(cfg['system'])} chars")
    if cfg["num_ctx"] > 32768:
        print(f"  ⚠ num_ctx {cfg['num_ctx']} looks like a typo (expected 12288)")
    print(f"{len(cases)} cases x {args.reps} reps = {len(cases)*args.reps} calls\n")

    results, cat_stats, lat = [], defaultdict(lambda: [0, 0]), []
    for c in cases:
        passes, reasons = 0, []
        for _ in range(args.reps):
            r = ask(cfg, c["q"], temp)
            lat.append(r["ms"])
            ok, why = score(c, r)
            passes += ok
            reasons += why
            results.append({"id": c["id"], "cat": c["cat"], "ok": ok, "why": why,
                            "called": r["called"], "tool": r["tool"], "args": r["args"],
                            "content": r["content"][:400], "ms": r["ms"]})
        rate = passes / args.reps
        cat_stats[c["cat"]][0] += passes
        cat_stats[c["cat"]][1] += args.reps
        flag = "PASS" if rate == 1 else ("FLAKY" if rate > 0 else "FAIL")
        uniq = sorted(set(reasons))
        print(f"  {c['id']:4} {c['cat']:12} {passes}/{args.reps} {flag:6} {c['q'][:44]:46}"
              + ("  <- " + "; ".join(uniq) if uniq else ""))

    picks = defaultdict(int)
    for r in results:
        picks[r["tool"] or "(no tool)"] += 1
    print("\n--- tool selection (the number two bound tools make measurable) ---")
    for name, n in sorted(picks.items(), key=lambda kv: -kv[1]):
        print(f"  {name:28} {n:3}/{len(results)}")

    print("\n--- by category ---")
    for cat, (p, t) in sorted(cat_stats.items()):
        print(f"  {cat:12} {p:3}/{t:<3} {p/t:6.1%}")
    tot_p = sum(p for p, _ in cat_stats.values())
    tot_t = sum(t for _, t in cat_stats.values())
    lat.sort()
    print(f"\n  TOTAL        {tot_p}/{tot_t} {tot_p/tot_t:.1%}")
    print(f"  latency      median {lat[len(lat)//2]} ms   p90 {lat[int(len(lat)*0.9)]} ms   max {lat[-1]} ms")

    flaky = [c["id"] for c in cases
             if 0 < sum(r["ok"] for r in results if r["id"] == c["id"]) < args.reps]
    if flaky:
        print(f"\n  ⚠ FLAKY (nondeterministic): {', '.join(flaky)}")
        print("    Re-run with --temp 0.0. Still flaky => the prompt is genuinely ambiguous.")

    if args.json:
        Path(args.json).write_text(json.dumps(
            {"config": {k: v for k, v in cfg.items() if k != "system"},
             "temp": temp, "reps": args.reps, "results": results}, indent=1))
        print(f"\n  wrote {args.json}")

    return 0 if tot_p == tot_t else 1


if __name__ == "__main__":
    sys.exit(main())
