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
CLASSES_FILE = ROOT / "evals" / "needs_classes.toml"
GRADED_STEPS = (2, 3, 4, 5, 6, 7, 8, 9)
CHOOSE_STEPS = (6, 7, 8, 9)
FORM_WORDS = ("lupomax",)  # a hop's form word: Citra and Citra LUPOMAX are siblings (app.hop_form_word)


def load_briefs() -> list[dict]:
    return tomllib.loads(BRIEFS_FILE.read_text(encoding="utf-8"))["brief"]


def load_classes() -> list[dict]:
    return tomllib.loads(CLASSES_FILE.read_text(encoding="utf-8"))["class"]


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
    rows = conn.execute(
        "select distinct on (step) step, llm, input from app.run_step "
        "where run_id = %s and ok order by step, try desc", (run_id,)
    ).fetchall()
    conn.commit()
    llms = {step: llm for step, llm, _ in rows if llm}
    inputs = {step: inp for step, _, inp in rows if step in CHOOSE_STEPS}
    return {"finished": bool(row and row[0]), "ok": bool(row and row[1]), "steps": steps,
            "llm": llms.get(1), "llms": llms, "inputs": inputs}


def read_facts(conn, steps: dict, inputs: dict | None = None) -> dict:
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
    if inputs and all(n in inputs and n in steps for n in CHOOSE_STEPS):
        facts["choose"] = read_choose_facts(conn, steps, inputs)
    return facts


def _stripped(name: str) -> str:
    """A product name without its form words, so Citra and Citra LUPOMAX compare equal."""
    return " ".join(w for w in grade.normalise(name).split() if w not in FORM_WORDS)


def read_choose_facts(conn, steps: dict, inputs: dict) -> dict:
    """What the step 6-9 graders need (see grade.py): the ref facts of every picked id, the excluded
    ids with their siblings, the style used's lager, family and sourness rules, and the logged
    step inputs. Read from `ref`, never from the candidate table functions."""
    ids = sorted({p["ingredient_id"] for n in CHOOSE_STEPS for p in grade._picks(n, steps[n])})
    tags = {t[0]: (t[1], t[2]) for t in conn.execute(
        "select id, name, parent_id from ref.tag where facet = 'family'").fetchall()}

    def with_parents(tag_id):
        names = []
        while tag_id in tags:
            names.append(tags[tag_id][0])
            tag_id = tags[tag_id][1]
        return names

    family = {}
    for ing, tag_id in conn.execute(
            "select ingredient_id, tag_id from ref.ingredient_tag").fetchall():
        family.setdefault(ing, set()).update(with_parents(tag_id))
    refs = {}
    for (i, kind, name, ytype, role, max_pct, elo, ehi, usages, dlo, dhi) in conn.execute(
            "select i.id, i.kind, i.name, y.type, f.role, f.max_pct, lower(f.ebc), upper(f.ebc), "
            "m.usages, lower(m.dose_g_per_l), upper(m.dose_g_per_l) from ref.ingredient i "
            "left join ref.yeast y on y.ingredient_id = i.id left join ref.fermentable f on f.ingredient_id = i.id "
            "left join ref.misc m on m.ingredient_id = i.id where i.id = any(%s)", (ids,)).fetchall():
        num = lambda x: None if x is None else float(x)
        refs[i] = {"kind": kind, "name": name, "type": ytype, "family": sorted(family.get(i, ())), "role": role,
                   "max_pct": num(max_pct), "ebc": None if elo is None else [num(elo), num(ehi)],
                   "usages": list(usages or []),
                   "dose": None if dlo is None and dhi is None else [num(dlo), num(dhi)]}
    # excluded products and their siblings by name
    everything = conn.execute("select id, kind, name from ref.ingredient").fetchall()
    excluded = {r["ingredient_id"]: r for w in steps[5]["excluded"] for r in w["refs"]}
    excluded_ids = set(excluded)
    for i, kind, name in everything:
        if any(kind == e["kind"] and _stripped(name) == _stripped(e["name"]) for e in excluded.values()):
            excluded_ids.add(i)
    # the style used: lager, required yeast families, sourness (guidance off switches the first two off)
    code, guidance = steps[4]["style"]["code"], inputs[6]["guidance"]
    row = conn.execute("select id, guide, category, raw ->> 'tags' from ref.beer_style where code = %s "
                       "order by id limit 1", (code,)).fetchone()
    lager, families, souring = False, [], False
    if row:
        style_id, guide, category, tag_text = row
        if guidance:
            lager = (guide == "BJCP" and "bottom-fermented" in (tag_text or "")) or \
                    (guide == "BA" and "lager" in (category or "").lower())
            yeast_tags = {n for (i,) in conn.execute("select y.ingredient_id from ref.yeast y").fetchall()
                          for n in family.get(i, ())}
            families = sorted({tags[t][0] for (t,) in conn.execute(
                "select tag_id from ref.style_ingredient where style_id = %s and required "
                "and tag_id is not null", (style_id,)).fetchall()
                if t in tags and tags[t][0] in yeast_tags})
        souring = conn.execute(
            "select exists (select 1 from ref.style_sensory where style_id = %s and dimension = 'sourness' "
            "and min_level >= 1 and reviewed)", (style_id,)).fetchone()[0]
    conn.commit()
    return {"inputs": {n: inputs[n] for n in CHOOSE_STEPS}, "refs": refs, "excluded_ids": excluded_ids,
            "style": {"lager": lager, "families": families, "souring": souring}}


def grade_result(brief: dict, answer: dict, steps: dict, llm=None, facts=None, llms=None, classes=None) -> dict:
    """Grade one run. `answer` holds run_id, ok and error; a run that is not ok never passes.
    `llm` is step 1's, `llms` the llm of every step that has one; `calls` adds up their tries."""
    graded = grade.grade_run(brief, steps, facts, load_classes() if classes is None else classes)
    ran = {n: n in steps for n in (1, *GRADED_STEPS)}
    run_ok = bool(answer.get("ok"))
    llms = llms if llms is not None else ({1: llm} if llm else {})
    return {
        "id": brief["id"], "run_id": answer.get("run_id"), "run_ok": run_ok,
        "error": answer.get("error"), "failed_step": answer.get("failed_step"),
        **{f"step{n}": graded[f"step{n}"] for n in (1, *GRADED_STEPS)},
        "needs": graded["needs"], "needs_ok": graded["needs_ok"], "problems": graded["problems"],
        "ran": ran, "passed": run_ok and graded["passed"], "llm": llm,
        "calls": sum(int((x or {}).get("tries") or 0) for x in llms.values()),
    }


def run_brief(conn, brief: dict, model=None, think=False, timeout=1800) -> dict:
    answer = send(brief["request"], brief["id"], model, think, timeout=timeout)
    steps, llm, llms, facts, run_ok = {}, None, None, None, bool(answer.get("ok"))
    if answer.get("run_id") is not None:
        stored = read_run(conn, answer["run_id"])
        steps, llm, llms = stored["steps"], stored.get("llm"), stored.get("llms")
        facts = read_facts(conn, steps, stored.get("inputs"))
        if not (stored["finished"] and stored["ok"]):
            run_ok = False
            answer = {**answer, "error": answer.get("error") or "run not finished ok"}
    return grade_result(brief, {**answer, "ok": run_ok}, steps, llm, facts, llms)


def needs_summary(needs: dict) -> str:
    """covered/total of the needs words, with the gaps and the absent words named."""
    verdicts = [(w, v) for words in needs.values() for w, v in words.items()]
    covered = sum(v == "covered" for _, v in verdicts)
    absent = [w for w, v in verdicts if v.startswith("absent")]
    gaps = [w for w, v in verdicts if v not in ("covered",) and not v.startswith("absent")]
    text = f"{covered}/{len(verdicts)}"
    if absent:
        text += " absent: " + ", ".join(absent)
    if gaps:
        text += " GAP: " + ", ".join(gaps)
    return text


def table(results: list[dict]) -> str:
    def cell(r, n):
        if not r["ran"][n]:
            return "not run"
        return "pass" if r[f"step{n}"] else "FAIL"

    steps = " ".join(f"{'step ' + str(n):<8}" for n in GRADED_STEPS)
    lines = [f"{'brief':<6} {'run':<8} {'step 1':<26} {steps} {'calls':<6} result   needs"]
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
        cells = " ".join(f"{cell(r, n):<8}" for n in GRADED_STEPS)
        lines.append(f"{r['id']:<6} {'ok' if r['run_ok'] else 'FAILED':<8} {step1:<26} {cells} "
                     f"{r.get('calls', 0):<6} {'pass' if r['passed'] else 'FAIL':<8} "
                     f"{needs_summary(r.get('needs') or {})}"
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
    out["needs"] = {"passed": sum(bool(r.get("needs_ok")) for r in results), "total": n,
                    "gaps": sum(v not in ("covered",) and not v.startswith("absent")
                                for r in results for words in (r.get("needs") or {}).values() for v in words.values())}
    out["calls"] = {"total": sum(r.get("calls", 0) for r in results), "runs": n}
    out["briefs"] = {"passed": sum(r["passed"] for r in results), "total": n}
    return out


def format_totals(t: dict) -> str:
    parts = []
    for step in (1, *GRADED_STEPS):
        s = t[f"step{step}"]
        parts.append(f"step {step} {s['passed']}/{s['total']} ({s['not_run']} not run)")
    parts.append(f"needs {t['needs']['passed']}/{t['needs']['total']} ({t['needs']['gaps']} gaps)")
    parts.append(f"LLM calls {t['calls']['total']} in {t['calls']['runs']} runs")
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
    for r in results:
        for step, found in (r.get("problems") or {}).items():
            print(f"{r['id']} step {step}: " + "; ".join(found))
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
