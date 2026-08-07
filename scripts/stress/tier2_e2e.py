#!/usr/bin/env python3
"""
tier2_e2e.py — score the FULL pipeline from n8n's own execution records.

Tier 1 asks "would the model call the tool?". This asks "did the whole thing actually
work?" — did the tool node run, what did retrieval return, is every [S] label in the
answer backed by a passage that was really retrieved, and how long did it take.

Two modes:

  --score-only        Decode the last N `chat-agent` executions and grade them. Works
                      on whatever you ran — the editor chat pane, chat.html, anything.
                      No webhook needed. Start here.

  --drive cases.jsonl Push the case set through the production chat webhook, then
                      score. REQUIRES the Chat Trigger's "Make Chat Publicly
                      Available" to be ON and the workflow published, otherwise the
                      webhook 404s.

The check that matters most is `cited_unbacked`: an [S1] in an answer where no tool
ran, or an [S7] when only 6 passages came back. That is fabricated provenance, and it
is the one failure that reads exactly like a correct answer.

Usage:
  ./tier2_e2e.py --score-only -n 20
  ./tier2_e2e.py --drive scripts/stress/cases.jsonl --webhook http://localhost:5678/webhook/<id>/chat
"""
import argparse, json, re, subprocess, sys, time, urllib.request
from pathlib import Path

N8N_DB = "aihomebrewassistant-postgres-1"
N8N_CT = "n8n"
N8N_DIR = "/usr/local/lib/node_modules/n8n"
WORKFLOW = "chat-agent"
CITATION = re.compile(r"\[S(\d+)\]")


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw).stdout


def recent_executions(n):
    out = sh(["docker", "exec", N8N_DB, "psql", "-U", "root", "-d", "n8n", "-tAc",
              f"""select e.id, e.status, e.mode from execution_entity e
                  join workflow_entity w on w.id=e."workflowId"
                  where w.name='{WORKFLOW}' order by e.id desc limit {n};"""])
    rows = []
    for line in out.strip().splitlines():
        if line.strip():
            i, status, mode = line.split("|")
            rows.append({"id": int(i), "status": status, "mode": mode})
    return list(reversed(rows))


DECODER = r"""
const f=require("flatted"),fs=require("fs");
const d=f.parse(fs.readFileSync(process.argv[2],"utf8").trim());
const rd=(d.resultData&&d.resultData.runData)||{};
const out={nodes:Object.keys(rd),question:null,answer:null,toolRuns:0,toolOutput:null,toolPassages:0,error:null};
if(d.resultData&&d.resultData.error)out.error=d.resultData.error.message;
for(const [name,runs] of Object.entries(rd)){
  for(const r of runs){
    if(r.error)out.error=out.error||r.error.message;
    const main=r.data&&r.data.main&&r.data.main[0]&&r.data.main[0][0]&&r.data.main[0][0].json;
    if(main&&main.chatInput)out.question=main.chatInput;
    if(main&&typeof main.output==="string")out.answer=main.output;
    const ai=r.data&&r.data.ai_tool;
    if(ai){out.toolRuns++;try{
      const full=JSON.stringify(ai[0][0].json);
      // Count [Sn] labels on the FULL string; truncating first undercounts and
      // manufactures false "unbacked citation" findings.
      const m=full.match(/\[S(\d+)\]/g)||[];
      const mx=m.reduce((a,x)=>Math.max(a,parseInt(x.slice(2))),0);
      out.toolPassages=Math.max(out.toolPassages,mx);
      out.toolOutput=full.slice(0,600);
    }catch(e){}}
  }
}
console.log(JSON.stringify(out));
"""


def decode(exec_id):
    raw = sh(["docker", "exec", N8N_DB, "psql", "-U", "root", "-d", "n8n", "-tAc",
              f'select data from execution_data where "executionId"={exec_id};']).strip()
    if not raw:
        return None
    Path("/tmp/_e.raw").write_text(raw)
    subprocess.run(["docker", "cp", "/tmp/_e.raw", f"{N8N_CT}:/tmp/_e.raw"],
                   capture_output=True)
    # The decoder must live INSIDE the n8n module dir: node resolves `require`
    # relative to the script's own path, so a copy in /tmp cannot find `flatted`.
    Path("/tmp/_dec.cjs").write_text(DECODER)
    subprocess.run(["docker", "cp", "/tmp/_dec.cjs", f"{N8N_CT}:{N8N_DIR}/_stress_dec.cjs"],
                   capture_output=True)
    out = sh(["docker", "exec", N8N_CT, "node", f"{N8N_DIR}/_stress_dec.cjs", "/tmp/_e.raw"])
    try:
        return json.loads(out.strip().splitlines()[-1])
    except Exception:
        return None


def grade(d):
    """Return a dict of findings for one decoded execution."""
    ans = d.get("answer") or ""
    labels = {int(m) for m in CITATION.findall(ans)}
    tool_ran = d.get("toolRuns", 0) > 0

    # How many passages did the tool actually return? The sub-workflow labels them
    # [S1]..[Sn] in its response string.
    returned = int(d.get("toolPassages") or 0)

    unbacked = sorted(l for l in labels if l > returned)
    return {
        "tool_ran": tool_ran,
        "passages": returned,
        "cited": sorted(labels),
        "cited_unbacked": unbacked,
        "has_sources_block": "Sources:" in ans,
        "error": d.get("error"),
    }


def drive(webhook, cases_path, pause):
    cases = [json.loads(l) for l in Path(cases_path).read_text().splitlines() if l.strip()]
    print(f"driving {len(cases)} cases through {webhook}\n")
    for c in cases:
        body = json.dumps({"action": "sendMessage",
                           "sessionId": f"stress-{c['id']}-{int(time.time())}",
                           "chatInput": c["q"]}).encode()
        req = urllib.request.Request(webhook, data=body,
                                     headers={"Content-Type": "application/json"})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                r.read()
            print(f"  {c['id']:4} {int((time.time()-t0)*1000):6} ms  {c['q'][:50]}")
        except Exception as e:
            print(f"  {c['id']:4} FAILED: {e}")
            if "404" in str(e):
                sys.exit("\n404 => the Chat Trigger is not public. Turn on "
                         "'Make Chat Publicly Available', then PUBLISH the workflow.")
        time.sleep(pause)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--drive", default="")
    ap.add_argument("--webhook", default="")
    ap.add_argument("-n", "--num", type=int, default=20)
    ap.add_argument("--pause", type=float, default=1.0,
                    help="seconds between requests; OLLAMA_NUM_PARALLEL=1 so they queue anyway")
    args = ap.parse_args()

    if args.drive:
        if not args.webhook:
            sys.exit("--drive needs --webhook")
        drive(args.webhook, args.drive, args.pause)

    rows = recent_executions(args.num)
    if not rows:
        sys.exit("no executions found")

    print(f"\n{'exec':>6} {'mode':10} {'tool':5} {'psg':>3} {'cites':10} {'src':4} question")
    print("-" * 104)
    bad = []
    for r in rows:
        d = decode(r["id"])
        if not d:
            continue
        g = grade(d)
        flag = ""
        if g["error"]:
            flag = f"ERROR: {g['error'][:40]}"
            bad.append((r["id"], flag))
        elif g["cited_unbacked"]:
            flag = f"UNBACKED {g['cited_unbacked']}"
            bad.append((r["id"], flag))
        elif g["cited"] and not g["tool_ran"]:
            flag = "CITED WITHOUT TOOL"
            bad.append((r["id"], flag))
        print(f"{r['id']:>6} {r['mode']:10} {'yes' if g['tool_ran'] else 'NO':5} "
              f"{g['passages']:>3} {str(g['cited'])[:10]:10} "
              f"{'yes' if g['has_sources_block'] else '-':4} "
              f"{(d.get('question') or '?')[:40]:42} {flag}")

    print()
    if bad:
        print(f"  ⚠ {len(bad)} execution(s) with fabricated or broken provenance:")
        for i, f in bad:
            print(f"    exec {i}: {f}")
        return 1
    print("  no fabricated citations found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
