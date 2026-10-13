"""Measure the role step 1 gives an adjunct, through the real pipeline.

    python -m evals.roles [--sets clear ambiguous] [--ids r01 ...] [--settings gated hot]
                          [--runs 3] [--save --label m2-role-gate]

Design: docs/work/m2-adjunct-role/plan.md Task 5. `gated` is temperature 0, seed 42 (the
pipeline's settings); `hot` is temperature 0.8 with seeds 1, 2, 3 (report only). The gate
(brief R6) is computed from the gated runs. Held-out wordings run only in a full run.
"""

import argparse
import datetime
import json
import re
import statistics
import sys
import tomllib

from evals import benchmark, grade, run
from loaders.db import connect

WORDINGS_FILE = run.ROOT / "evals" / "role_wordings.toml"
SETTINGS = {"gated": {"temperature": 0, "seeds": [42]},
            "hot": {"temperature": 0.8, "seeds": [1, 2, 3]}}


def load_wordings() -> list[dict]:
    return tomllib.loads(WORDINGS_FILE.read_text(encoding="utf-8"))["wording"]


def select(wordings, sets, ids) -> list[dict]:
    """The wordings to run. Held-out ones only when neither sets nor ids narrow the run."""
    full = not sets and not ids
    chosen = []
    for w in wordings:
        if w["set"] == "held_out" and not full:
            continue
        if sets and w["set"] not in sets:
            continue
        if ids and w["id"] not in ids:
            continue
        chosen.append(w)
    return chosen


def _forms(adjunct: str) -> list[str]:
    word = grade.normalise(adjunct)
    forms = [word, word + "s", word + "es"]
    if word.endswith("y"):
        forms.append(word[:-1] + "ies")
    return forms


def scored_role(brief, adjunct):
    """The role of the wanted items that contain the adjunct as a whole word.

    None if there is no such item, "mixed" if they disagree."""
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(f) for f in _forms(adjunct)) + r")\b")
    found = set()
    for entry in (brief or {}).get("wanted") or []:
        if isinstance(entry, dict) and pattern.search(grade.normalise(entry.get("item", ""))):
            found.add(entry.get("role"))
    if not found:
        return None
    return found.pop() if len(found) == 1 else "mixed"


def summarise_runs(role_list, expected, run_ids, llm_ms) -> dict:
    """One wording under one setting. `right_every_run` is None for an unscored wording."""
    return {
        "roles": role_list, "run_ids": run_ids,
        "right_every_run": all(r == expected for r in role_list) if expected else None,
        "consistent": len(set(role_list)) == 1,
        "llm_ms": statistics.median(llm_ms) if llm_ms else None,
    }


def gate(wordings) -> dict:
    """The four R6 points on the gated results, and `met` (all four)."""
    def gated(w):
        return w["settings"]["gated"]

    by_id = {w["id"]: w for w in wordings}
    b12_b19 = all(i in by_id and gated(by_id[i])["right_every_run"] for i in ("r01", "r15"))
    clear = [w for w in wordings if w["set"] == "clear"]
    clear_right = sum(bool(gated(w)["right_every_run"]) for w in clear)
    held = [w for w in wordings if w["set"] == "held_out"]
    held_right = sum(bool(gated(w)["right_every_run"]) for w in held)
    inconsistent = [w["id"] for w in wordings if not gated(w)["consistent"]]
    points = {
        "b12_b19": {"ok": b12_b19, "value": "b12 feature and b19 background in every run"},
        "clear": {"ok": clear_right >= 20, "value": f"{clear_right}/{len(clear)}"},
        "consistent": {"ok": not inconsistent, "value": f"inconsistent: {inconsistent}"},
        "held_out": {"ok": held_right >= 9, "value": f"{held_right}/{len(held)}"},
    }
    return {**points, "met": all(p["ok"] for p in points.values())}


def word_rule(conn, request, adjunct) -> str:
    on = conn.execute("select app.adjunct_is_prominent(%s, %s)", (request, adjunct)).fetchone()[0]
    conn.commit()
    return "feature" if on else "background"


def measure(conn, wording, setting, runs) -> dict:
    """Send one wording `runs` times under one setting; read step 1's answer back."""
    cfg = SETTINGS[setting]
    seeds = cfg["seeds"]
    role_list, run_ids, llm_ms = [], [], []
    for n in range(runs):
        seed = seeds[n % len(seeds)]
        answer = run.send(wording["request"], f"role-{wording['id']}",
                          temperature=cfg["temperature"], seed=seed)
        if answer.get("run_id") is None:
            raise RuntimeError(f"{wording['id']}: no run id ({answer.get('error')})")
        stored = run.read_run(conn, answer["run_id"])
        llm = stored["llm"]
        if llm is None or llm.get("temperature") != cfg["temperature"] or llm.get("seed") != seed:
            raise RuntimeError(f"{wording['id']}: sent temperature {cfg['temperature']} seed "
                               f"{seed}, step 1 logged {llm and (llm.get('temperature'), llm.get('seed'))}")
        role_list.append(scored_role(stored["steps"].get(1), wording["adjunct"]))
        run_ids.append(answer["run_id"])
        llm_ms.append(llm.get("llm_ms"))
    summary = summarise_runs(role_list, wording["expected"], run_ids, [m for m in llm_ms if m])
    return {**summary, "model": llm.get("model")}


def table(results, settings) -> str:
    lines = [f"{'id':<5} {'set':<10} {'expect':<10} {'rule':<10} " + " ".join(f"{s:<34}" for s in settings)]
    for w in results:
        cells = []
        for s in settings:
            r = w["settings"][s]
            mark = "" if r["right_every_run"] is None else (" ok" if r["right_every_run"] else " WRONG")
            cells.append(f"{','.join(str(x) for x in r['roles'])}{mark}")
        lines.append(f"{w['id']:<5} {w['set']:<10} {w['expected'] or '-':<10} {w['word_rule']:<10} "
                     + " ".join(f"{c:<34}" for c in cells))
    return "\n".join(lines)


def verdict_text(g) -> str:
    rows = [f"  {'PASS' if g[k]['ok'] else 'FAIL'}  {k}: {g[k]['value']}"
            for k in ("b12_b19", "clear", "consistent", "held_out")]
    return "\n".join(["Gate (R6):", *rows, f"Verdict: {'MET' if g['met'] else 'NOT MET'}"])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.roles")
    parser.add_argument("--sets", nargs="+", choices=["clear", "ambiguous", "held_out"])
    parser.add_argument("--ids", nargs="+")
    parser.add_argument("--settings", nargs="+", choices=list(SETTINGS), default=list(SETTINGS))
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--label", default="m2-role")
    args = parser.parse_args(argv)

    chosen = select(load_wordings(), args.sets, args.ids)
    if not chosen:
        parser.error("no wording selected")
    conn = connect()
    results = []
    try:
        for w in chosen:
            row = {**w, "word_rule": word_rule(conn, w["request"], w["adjunct"]), "settings": {}}
            for s in args.settings:
                row["settings"][s] = measure(conn, w, s, args.runs)
            results.append(row)
            print(f"{w['id']} done", file=sys.stderr, flush=True)
    finally:
        conn.close()
    print(table(results, args.settings))
    g = gate(results) if "gated" in args.settings else None
    if g:
        print(verdict_text(g))
    if args.save:
        date = datetime.date.today().isoformat()
        path = run.RESULTS_DIR / f"{date}-{args.label}.json"
        run.RESULTS_DIR.mkdir(exist_ok=True)
        doc = {"date": date, "label": args.label,
               "model": results[0]["settings"][args.settings[0]]["model"],
               "prompt_sha256": benchmark.sha256(benchmark.PROMPT_FILE),
               "contract_sha256": benchmark.sha256(benchmark.CONTRACT_FILE),
               "settings": {s: SETTINGS[s] for s in args.settings}, "runs": args.runs,
               "wordings": results, "gate": g}
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"saved {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
