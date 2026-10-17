"""Send each recipe brief to the pipeline, read the run back from the database, grade it.

    python -m evals.run [--brief b01] [--model NAME] [--save --label m0]

Design: docs/work/m0-harness/plan.md Task 7. The database is the record; the HTTP answer
is only the handle (it is 200 even when the run failed, so `ok` is read from the body).
"""

import argparse
import datetime
import json
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

from evals import grade
from loaders.db import connect

ROOT = Path(__file__).resolve().parent.parent
BRIEFS_FILE = ROOT / "evals" / "recipe_briefs.toml"
RESULTS_DIR = ROOT / "evals" / "results"
PIPELINE_URL = "http://localhost:5678/webhook/recipe-pipeline"
GRADED_STEPS = (2, 3, 4, 5)


def load_briefs() -> list[dict]:
    return tomllib.loads(BRIEFS_FILE.read_text(encoding="utf-8"))["brief"]


def send(request, brief_id, model=None, think=False, url=PIPELINE_URL, timeout=1800,
         temperature=None, seed=None) -> dict:
    """POST one request. A bad answer or a timeout comes back as {"ok": False, "error": ...}."""
    body = {"request": request, "brief_id": brief_id, "think": think}
    if model:
        body["model"] = model
    if temperature is not None:
        body["temperature"] = temperature
    if seed is not None:
        body["seed"] = seed
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                return {"ok": False, "error": f"HTTP {response.status}"}
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def read_run(conn, run_id) -> dict:
    """The app.run row and the outputs of its passed steps (latest try of each)."""
    row = conn.execute(
        "select finished_at, ok from app.run where id = %s", (run_id,)
    ).fetchone()
    steps = {}
    for step, output in conn.execute(
        "select distinct on (step) step, output from app.run_step "
        "where run_id = %s and ok order by step, try desc", (run_id,)
    ).fetchall():
        steps[step] = output
    conn.commit()
    llm = conn.execute(
        "select llm from app.run_step where run_id = %s and step = 1 and ok "
        "order by try desc limit 1", (run_id,)
    ).fetchone()
    conn.commit()
    return {"finished": bool(row and row[0]), "ok": bool(row and row[1]), "steps": steps,
            "llm": llm[0] if llm else None}


def read_facts(conn, steps: dict) -> dict:
    """What the step 4 and 5 graders need from the database (three queries): the ranges of the
    style step 4 used, app.abv of its OG and FG, the rules, and the yeast band run back through
    app.mash_attenuation. Missing steps give no facts, so the grader fails them."""
    facts = {}
    s4, s5 = steps.get(4), steps.get(5)
    try:
        t = s4["targets"]
        row = conn.execute(
            "select og, fg, abv, ibu, srm from ref.beer_style where code = %s order by id limit 1",
            (s4["style"]["code"],)).fetchone()
        ranges = {k: None if r is None or r.isempty else [r.lower, r.upper]
                  for k, r in zip(("og", "fg", "abv", "ibu", "srm"), row)} if row else {}
        abv = conn.execute("select app.abv(%s::numeric, %s::numeric)",
                           (t["og"]["value"], t["fg"]["value"])).fetchone()[0]
        facts["step4"] = {"ranges": ranges, "abv": abv}
    except (TypeError, KeyError):
        pass
    try:
        middle = s5["attenuation"]["yeast_middle_pct"]
        band = conn.execute(
            "select app.mash_attenuation(numrange(%s::numeric - 3, %s::numeric + 3), %s::numeric)",
            (middle, middle, s4["mash_c"]["value"])).fetchone()[0]
        rules = [{"rule": r, "checked": c, "sentence": t_}
                 for r, c, t_ in conn.execute(
                     "select rule, checked, sentence from app.formulation_rules()").fetchall()]
        facts["step5"] = {"rules": rules, "band_attenuation": band}
    except (TypeError, KeyError):
        pass
    conn.commit()
    return facts


def grade_result(brief: dict, answer: dict, steps: dict, llm=None, facts=None) -> dict:
    """Grade one run. `answer` holds run_id, ok and error; a run that is not ok never passes."""
    graded = grade.grade_run(brief, steps, facts)
    ran = {n: n in steps for n in (1, *GRADED_STEPS)}
    run_ok = bool(answer.get("ok"))
    return {
        "id": brief["id"], "run_id": answer.get("run_id"), "run_ok": run_ok,
        "error": answer.get("error"), "failed_step": answer.get("failed_step"),
        "step1": graded["step1"], "step2": graded["step2"], "step3": graded["step3"],
        "step4": graded["step4"], "step5": graded["step5"],
        "ran": ran, "passed": run_ok and graded["passed"], "llm": llm,
    }


def run_brief(conn, brief: dict, model=None, think=False, timeout=1800) -> dict:
    answer = send(brief["request"], brief["id"], model, think, timeout=timeout)
    steps, llm, facts, run_ok = {}, None, None, bool(answer.get("ok"))
    if answer.get("run_id") is not None:
        stored = read_run(conn, answer["run_id"])
        steps, llm = stored["steps"], stored.get("llm")
        facts = read_facts(conn, steps)
        if not (stored["finished"] and stored["ok"]):
            run_ok = False
            answer = {**answer, "error": answer.get("error") or "run not finished ok"}
    return grade_result(brief, {**answer, "ok": run_ok}, steps, llm, facts)


def table(results: list[dict]) -> str:
    def cell(r, n):
        if not r["ran"][n]:
            return "not run"
        return "pass" if r[f"step{n}"] else "FAIL"

    lines = [f"{'brief':<6} {'run':<8} {'step 1':<26} {'step 2':<8} {'step 3':<8} {'step 4':<8} {'step 5':<8} result"]
    for r in results:
        if r["run_ok"]:
            run_col = "ok"
        else:
            run_col = f"failed at step {r['failed_step'] or '?'}: {r['error']}"
        if not r["ran"][1]:
            step1 = "not run"
        elif r["step1"]["ok"]:
            step1 = "pass"
        else:
            step1 = "fail: " + ",".join(f for f, v in r["step1"].items() if f != "ok" and not v)
        lines.append(f"{r['id']:<6} {'ok' if r['run_ok'] else 'FAILED':<8} {step1:<26} "
                     f"{cell(r, 2):<8} {cell(r, 3):<8} {cell(r, 4):<8} {cell(r, 5):<8} {'pass' if r['passed'] else 'FAIL'}"
                     + ("" if r["run_ok"] else f"  [{run_col}]"))
    return "\n".join(lines)


def totals(results: list[dict]) -> dict:
    n = len(results)
    out = {"step1": {"passed": sum(r["ran"][1] and r["step1"]["ok"] for r in results), "total": n,
                     "not_run": sum(not r["ran"][1] for r in results)}}
    for step in GRADED_STEPS:
        out[f"step{step}"] = {
            "passed": sum(r["ran"][step] and r[f"step{step}"] for r in results), "total": n,
            "not_run": sum(not r["ran"][step] for r in results),
        }
    out["briefs"] = {"passed": sum(r["passed"] for r in results), "total": n}
    return out


def format_totals(t: dict) -> str:
    parts = []
    for step in (1, *GRADED_STEPS):
        s = t[f"step{step}"]
        parts.append(f"step {step} {s['passed']}/{s['total']} ({s['not_run']} not run)")
    parts.append(f"briefs {t['briefs']['passed']}/{t['briefs']['total']}")
    return "; ".join(parts)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.run")
    parser.add_argument("--brief", help="run only this brief id, e.g. b01")
    parser.add_argument("--model")
    parser.add_argument("--think", action="store_true", help="let the model think first")
    parser.add_argument("--timeout", type=int, default=1800, help="seconds per brief")
    parser.add_argument("--save", action="store_true", help="write evals/results/<date>-<label>.json")
    parser.add_argument("--label", default="run")
    args = parser.parse_args(argv)

    briefs = [b for b in load_briefs() if not args.brief or b["id"] == args.brief]
    if not briefs:
        parser.error(f"no brief {args.brief}")
    conn = connect()
    try:
        results = [run_brief(conn, b, args.model, args.think, args.timeout) for b in briefs]
    finally:
        conn.close()
    t = totals(results)
    print(table(results))
    print(format_totals(t))
    if args.save:
        date = datetime.date.today().isoformat()
        path = RESULTS_DIR / f"{date}-{args.label}.json"
        RESULTS_DIR.mkdir(exist_ok=True)
        doc = {"date": date, "label": args.label, "model": args.model or "pipeline default",
               "results": results, "totals": t}
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"saved {path}")
    return 0 if t["briefs"]["passed"] == t["briefs"]["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
