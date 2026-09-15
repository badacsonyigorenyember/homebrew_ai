#!/usr/bin/env python3
"""
recipe_eval.py — can the model formulate, and does the recipe survive arithmetic?

Every claim this project has made about model choice for `formulate.recipe` rests
on ONE case (R04, the pastry stout) run by hand, and one of those conclusions had
to be retracted. `recipe_cases.jsonl` holds six cases; five had never been run
against any model before this script existed. The point is that evaluating a
candidate model is one command, not an evening of curl.

⛔ IT SCORES THE SAVED RECIPE, NOT THE PROSE.

The model writes the answer text, so scoring the text asks the model to mark its
own homework — and its characteristic failure is describing a beer it did not
produce ("a deep black stout", OG/SRM says otherwise). Every number here comes
from `brew.recipes` / `brew.recipe_items` through SQL, which is the same
instrument §7.4 makes authoritative for the recipe itself:

    abv        brew.f_abv(target_og, target_fg)
    ibu/srm    recipes.target_ibu / target_srm
    roast_pct  sum(qty) role='roast' / sum(qty) role in (base,caramel,roast)
    has_*      brew.f_catalogue() kind/name over the saved items

R06 is the one exception and is marked so in the case file: it asks for a
jet-black stout with no roasted or dark malts, which is impossible, and the thing
being measured is whether the ANSWER names the conflict. A recipe check cannot
see that, so R06 gets a text check and no number check.

⛔ The model is read from `obs.steps`, never from config. A previous A/B compared
two models that both ran the SAME propose model — only the chat-agent node had
been switched, the capability's own LLM node had not — and the identical outputs
were the only clue anything was wrong. `obs.steps.model` on the `propose` step is
the model that actually formulated.

Cases run ONE AT A TIME on purpose. The stack runs a single model on a single
GPU; concurrency buys nothing and costs model reloads and meaningless latencies.

Usage:
  ./recipe_eval.py                  # all six, ~10 min
  ./recipe_eval.py --only R04       # just the known failure
  ./recipe_eval.py --json out.json
"""
import argparse, json, re, subprocess, sys, time, urllib.error, urllib.request, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
WEBHOOK = "http://localhost:5678/webhook/fc5648d9-d7e3-4bbc-b771-8bd35b9e4db5/chat"
DB = ("docker", "exec", "supabase-db", "psql", "-U", "supabase_admin", "-d", "postgres", "-tAc")


def sql(q):
    out = subprocess.run([*DB, q], capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(out.stderr.strip())
    return out.stdout.strip()


# ---------------------------------------------------------------------------
# Probe — the check that stops this eval inventing a score table
# ---------------------------------------------------------------------------
def probe(attempts=3):
    """Abort unless chat-agent's webhook is actually registered.

    ⛔ This is not defensive padding. `measured` 2026-09-14: an import dropped
    chat-agent's webhook registration, every POST 404'd in ~2 ms, and
    grounding_eval scored 4 FAILs against an agent it had never reached. A score
    table produced that way is worse than no table — it reads as a model result.

    A 200 arrives as soon as the headers do, because the chat trigger streams, so
    there is no need to read the body to know the route exists.
    """
    body = json.dumps({"sessionId": f"probe-{uuid.uuid4().hex[:8]}",
                       "action": "sendMessage", "chatInput": "ping"}).encode()
    for i in range(attempts):
        req = urllib.request.Request(WEBHOOK, data=body,
                                     headers={"Content-Type": "application/json"})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                if r.status == 200:
                    return round(time.time() - t0, 2)
                why = f"HTTP {r.status}"
        except urllib.error.HTTPError as e:
            why = f"HTTP {e.code} in {time.time() - t0:.2f}s"
        except Exception as e:
            why = f"{type(e).__name__}: {e}"
        print(f"  probe attempt {i + 1}/{attempts} failed — {why}")
        if i < attempts - 1:
            time.sleep(5 * (i + 1))          # backoff; n8n may still be coming up
    sys.exit(
        "\n⛔ ABORTING — the chat webhook is not answering, so no case can reach the\n"
        "   agent and every score would be a FAIL against something never asked.\n"
        f"   {WEBHOOK}\n"
        "   A 404 in ~0.00s means an import/publish dropped the registration:\n"
        "     docker restart n8n\n"
        "   Then re-run. Do NOT interpret a score table produced without this probe.")


def ask(session_id, question, timeout=900):
    """Drive one question through the chat webhook and return the raw stream."""
    body = json.dumps({"sessionId": session_id, "action": "sendMessage",
                       "chatInput": question}).encode()
    req = urllib.request.Request(WEBHOOK, data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    # ⛔ A socket timeout is NOT enough — urlopen's timeout applies per read, and
    # the chat trigger streams, so a stuck run trickles bytes forever and the cap
    # never fires. Formulate is slower than a retrieval answer (parse, retrieve,
    # propose, sometimes a second propose, compose), hence the wider default.
    deadline = t0 + timeout
    try:
        with urllib.request.urlopen(req, timeout=min(120, timeout)) as r:
            buf = []
            while True:
                if time.time() > deadline:
                    raise TimeoutError(f"wall-clock {timeout}s exceeded, still streaming")
                block = r.read(65536)
                if not block:
                    break
                buf.append(block)
            return {"ok": True, "s": round(time.time() - t0, 1),
                    "raw": b"".join(buf).decode("utf-8", "replace")}
    except Exception as e:
        return {"ok": False, "s": round(time.time() - t0, 1), "raw": "",
                "error": f"{type(e).__name__}: {e}"}


# ---------------------------------------------------------------------------
# Linking a case to the recipe it produced
# ---------------------------------------------------------------------------
def link_run(session_id, watermark):
    """Find the formulate run this case caused. Returns (run_row|None, note).

    ⚠️ `cap-formulate-recipe` hardcodes `'cap'` as the session_id it passes to
    obs.f_start_run, so obs.runs CANNOT be filtered by session. It does thread
    the real session_id into `Step 2 · retrieve`, which logs it to
    obs.retrievals — so the session is tied to the run through its retrieval,
    inside the run's own start/finish window.

    Two guards matter:
      · `finished_at IS NOT NULL`. Abandoned runs sit at status='running' with a
        NULL finish, and `coalesce(finished_at, now())` turns those into an
        open-ended window that swallows every later retrieval — it matched 8 runs
        for a session that caused exactly 1.
      · `id > watermark`, captured immediately before the request, so a stale run
        can never be picked up.

    This is deliberately NOT "the newest recipe": if anything else touches the
    stack mid-run, that guess is silently wrong. Here a surprise is reported.
    """
    rows = sql(f"""
        select r.id, coalesce(r.status,''), coalesce(r.spent->>'recipe_id',''),
               coalesce(r.spent->'gate'->>'attempt',''),
               coalesce((select string_agg(u, ' · ')
                         from jsonb_array_elements_text(r.spent->'gate'->'unresolved') u), '')
        from obs.runs r
        where r.capability='formulate.recipe'
          and r.id > {watermark}
          and r.finished_at is not null
          and exists (select 1 from obs.retrievals t
                      where t.session_id='{session_id}'
                        and t.created_at between r.started_at and r.finished_at)
        order by r.id;""")
    if not rows:
        return None, ("no formulate run — the agent never called the capability, or it "
                      "errored before finishing")
    lines = rows.splitlines()
    if len(lines) > 1:
        return None, (f"{len(lines)} formulate runs matched this session "
                      f"({', '.join(l.split('|')[0] for l in lines)}) — something else is "
                      f"driving the stack; the link is ambiguous, not guessed")
    rid, status, recipe_id, attempt, unresolved = lines[0].split("|", 4)
    return {"run_id": int(rid), "status": status,
            "recipe_id": int(recipe_id) if recipe_id else None,
            "attempt": int(attempt) if attempt else None,
            "unresolved": unresolved}, ""


def measure(recipe_id):
    """Every scored number, straight out of SQL. Never parsed from the answer."""
    row = sql(f"""
        with it as (
          select c.kind, c.role, lower(c.name) nm, ri.qty
          from brew.recipe_items ri
          join brew.f_catalogue() c on c.id = ri.ingredient_id
          where ri.recipe_id = {recipe_id})
        select round(brew.f_abv(r.target_og, r.target_fg), 2),
               coalesce(r.target_ibu, -1),
               coalesce(r.target_srm, -1),
               coalesce(round(100.0 * coalesce((select sum(qty) from it where role='roast'), 0)
                        / nullif((select sum(qty) from it
                                  where role in ('base','caramel','roast')), 0), 1), -1),
               (select count(*) from it where kind='hop') > 0,
               (select bool_or(nm like '%lactose%') from it),
               coalesce((select string_agg(distinct nm, ' | ') from it), '')
        from brew.recipes r where r.id = {recipe_id};""")
    if not row:
        return None
    abv, ibu, srm, roast, hop, lac, names = row.split("|", 6)
    return {"abv": float(abv), "ibu": int(ibu), "srm": float(srm),
            "roast_pct": float(roast), "has_hop": hop == "t",
            "has_lactose": lac == "t", "names": names}


def propose_model(run_id):
    """The model that ACTUALLY ran propose, and whether it needed the retry.

    seq 3 is the first propose, seq 4 the retry the style-band gate fires. Read
    the last one — that is the attempt whose items were saved.
    """
    rows = sql(f"""select seq, coalesce(model,''), coalesce(verdict,'')
                   from obs.steps where run_id={run_id} and step_id='propose'
                   order by seq;""")
    if not rows:
        return "(no propose step)", 0, ""
    parsed = [l.split("|", 2) for l in rows.splitlines()]
    models = {p[1] for p in parsed if p[1]}
    name = parsed[-1][1] or "(unrecorded)"
    if len(models) > 1:
        name = "MIXED:" + ",".join(sorted(models))
    return name, len(parsed), parsed[-1][2]


def step_latency(run_id):
    """Per-case latency as the pipeline measured it, not as the socket saw it."""
    row = sql(f"""select coalesce(sum(latency_ms), 0),
                         coalesce(string_agg(step_id || ' ' || latency_ms, ' · '
                                  order by seq), '')
                  from obs.steps where run_id={run_id};""")
    total, breakdown = row.split("|", 1)
    return int(total), breakdown


def answer_text(session_id, fallback):
    got = sql(f"""select coalesce(content,'') from mem.chat_turns
                  where session_id='{session_id}' and role='assistant'
                  order by id desc limit 1;""")
    return got or fallback


# ---------------------------------------------------------------------------
# R06's text check
# ---------------------------------------------------------------------------
# "jet-black stout using absolutely no roasted or dark malts" cannot be built.
# The 12B's real failure is shipping a beer and never noticing it contradicts the
# brief — so the question is whether the answer SAYS SO.
#
# Both halves are required IN THE SAME SENTENCE, because either alone is noise:
# a bare impossibility marker catches "you cannot use roasted malts" (the model
# merely restating the constraint it was given), and a bare colour word catches
# every stout answer ever written. Requiring the colour goal next to the marker
# is what separates "this brief conflicts with itself" from both.
CONFLICT = re.compile(
    r"cannot|can'?t|could\s+not|couldn'?t|not\s+possible|impossible|unachievable"
    r"|not\s+achievable|contradict\w*|conflict\w*|mutually\s+exclusive"
    r"|no\s+way\s+to|by\s+definition|requires?\s+(?:some|a\s+degree\s+of)"
    r"|trade.?off|compromise|will\s+not\s+be|won'?t\s+be|falls?\s+short",
    re.I)
COLOUR_GOAL = re.compile(r"jet.?black|black|colou?r|dark(?:ness)?|\bsrm\b|\bebc\b", re.I)


def flags_contradiction(answer):
    """True if some sentence names the colour-versus-no-roast conflict."""
    for sentence in re.split(r"(?<=[.!?;:])\s+|\n", answer):
        if CONFLICT.search(sentence) and COLOUR_GOAL.search(sentence):
            return True, sentence.strip()[:160]
    return False, ""


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def score(expect, m, answer):
    """Return (notes[], shown{}). Empty notes means PASS. Driven by the keys the
    case actually declares, so a new key in the case file is a loud KeyError
    rather than a check that silently never runs."""
    notes, shown = [], {}
    for key, want in expect.items():
        if key == "answer_flags_contradiction":
            ok, sentence = flags_contradiction(answer)
            shown["flags"] = "yes" if ok else "no"
            if ok != want:
                notes.append("ANSWER DOES NOT NAME THE CONFLICT — the brief is impossible "
                             "and the reply presents a recipe as if it were not"
                             if want else "flagged a conflict that was not asked about")
            elif ok:
                shown["said"] = sentence
            continue

        if m is None:                       # no recipe to measure against
            notes.append(f"{key}: no recipe saved")
            continue

        if key in ("abv", "ibu", "srm", "roast_pct"):
            got = m[key]
            shown[key] = got
            lo, hi = want
            if got < 0:
                notes.append(f"{key} not recorded")
            elif not (lo <= got <= hi):
                notes.append(f"{key} {got} outside [{lo}, {hi}]")
        elif key in ("has_hop", "has_lactose"):
            got = m[key]
            shown[key] = "y" if got else "n"
            if got != want:
                notes.append(f"{key} is {got}, wanted {want}")
        elif key == "name_contains":
            for term in want:
                if term.lower() not in m["names"]:
                    notes.append(f"no ingredient matching {term!r} — "
                                 f"grist was: {m['names']}")
        elif key == "name_excludes":
            for term in want:
                if term.lower() in m["names"]:
                    notes.append(f"EXCLUSION IGNORED — used {term!r} after being told "
                                 f"it was unavailable")
        else:
            raise KeyError(f"case declares an expect key this scorer does not know: {key}")
    return notes, shown


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="prefix filter, e.g. R04")
    ap.add_argument("--cases", default=str(HERE / "recipe_cases.jsonl"))
    ap.add_argument("--timeout", type=int, default=900, help="wall-clock cap per case")
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    cases = [json.loads(l) for l in Path(args.cases).read_text().splitlines() if l.strip()]
    if args.only:
        cases = [c for c in cases if c["id"].startswith(args.only)]
    if not cases:
        sys.exit(f"no cases matched --only {args.only!r}")

    print(f"{len(cases)} case(s) against {WEBHOOK}")
    print("probing the webhook before anything is scored...")
    print(f"  registered (headers in {probe()}s)\n")

    out, tally = [], {"PASS": 0, "FAIL": 0, "ERROR": 0}
    t_suite = time.time()
    for c in cases:
        sid = f"re-{c['id']}-{uuid.uuid4().hex[:8]}"
        # Captured BEFORE the request so no earlier run can ever be linked here.
        watermark = int(sql("select coalesce(max(id), 0) from obs.runs;"))

        res = ask(sid, c["q"], args.timeout)
        rec = {"id": c["id"], "cat": c["cat"], "sid": sid, "s": res["s"]}

        if not res["ok"]:
            # An explicit ERROR row. Never a FAIL: nothing was measured, so there
            # is no evidence about the model either way.
            verdict, notes = "ERROR", [f"NOT ASKED — {res['error']}"]
            rec.update(verdict=verdict, notes=notes, model="", shown={})
        else:
            run, why = link_run(sid, watermark)
            answer = answer_text(sid, res["raw"])
            if run is None:
                # R06 is scored on prose, so it is still checkable without a run.
                if "answer_flags_contradiction" in c["expect"]:
                    notes, shown = score(c["expect"], None, answer)
                    notes.append(why)
                else:
                    notes, shown = [why], {}
                verdict = "FAIL" if answer.strip() else "ERROR"
                rec.update(verdict=verdict, notes=notes, model="", shown=shown)
            else:
                m = measure(run["recipe_id"]) if run["recipe_id"] else None
                model, tries, verd = propose_model(run["run_id"])
                ms, breakdown = step_latency(run["run_id"])
                notes, shown = score(c["expect"], m, answer)
                if run["attempt"] and run["attempt"] > 1:
                    notes.append(f"RETRIED propose (attempt {run['attempt']}) — "
                                 f"the style-band gate fired")
                if run["unresolved"]:
                    notes.append(f"gate left unresolved: {run['unresolved']}")
                if run["status"] != "ok":
                    notes.append(f"run status {run['status']!r}")
                hard = [n for n in notes if not n.startswith(("RETRIED", "gate left"))]
                verdict = "PASS" if not hard else "FAIL"
                rec.update(verdict=verdict, notes=notes, model=model, shown=shown,
                           run_id=run["run_id"], recipe_id=run["recipe_id"],
                           attempt=run["attempt"], propose_calls=tries,
                           propose_verdict=verd, steps_ms=ms, steps=breakdown,
                           measured=m)

        tally[rec["verdict"]] += 1
        out.append(rec)
        vals = " ".join(f"{k}={v}" for k, v in rec["shown"].items() if k != "said")
        print(f"  {rec['id']:4} {rec['cat']:13} {rec['verdict']:5} "
              f"{rec['s']:6.1f}s {rec.get('steps_ms', 0)/1000:6.1f}s(steps)  "
              f"{rec['model'] or '-'}")
        print(f"       {vals}")
        for n in rec["notes"]:
            print(f"       {'⚠️ ' if n.startswith(('RETRIED', 'gate left')) else '⛔ '}{n}")

    print(f"\n  PASS {tally['PASS']}  FAIL {tally['FAIL']}  ERROR {tally['ERROR']}"
          f"   of {len(cases)}   suite {time.time() - t_suite:.0f}s")

    models = sorted({o["model"] for o in out if o.get("model")})
    print(f"  propose model (from obs.steps, NOT config): {', '.join(models) or '(none ran)'}")
    if len(models) > 1:
        print("  ⛔ more than one model ran propose across this suite — the result is not"
              "\n     a single model's score. Check the capability's LLM node.")
    retried = [o["id"] for o in out if o.get("attempt") and o["attempt"] > 1]
    if retried:
        print(f"  retried propose: {', '.join(retried)}  "
              f"({len(retried)}/{len(cases)} needed a second attempt)")
    if tally["ERROR"]:
        print("  ⛔ ERROR means the case was never measured — that part of the run is"
              "\n     INVALID, not failed. Re-run those cases before drawing conclusions.")

    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=1))
        print(f"  wrote {args.json}")
    return 0 if not (tally["FAIL"] or tally["ERROR"]) else 1


if __name__ == "__main__":
    sys.exit(main())
