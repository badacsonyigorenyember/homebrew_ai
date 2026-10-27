"""Re-run steps 10-11 on the logged picks of a results file (SQL only, no LLM, nothing saved to the run).

    python -m evals.revalidate evals/results/2026-10-26-m6-9b.json [--save --label m6-10b-revalidate]

For each brief the last try of its run that has a step 11 row: `app.step10_compute` on the logged step
10 input, then `app.step11_validate` on the logged step 11 input with that new step 10. `before` is
the logged step 11 `passed`, `after` the re-run's. Only SELECTs and function calls: no `app.run`,
`run_step` or recipe writes. Design: docs/work/m6-compute-validate/plan.md Task 10b.
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

from loaders.db import connect

RESULTS_DIR = Path(__file__).resolve().parent.parent / "evals" / "results"


def totals(rows: list[dict]) -> dict:
    """Passed counts before and after, for b01-b20 and for all briefs."""
    def count(keep, key):
        return sum(bool(r[key]) for r in rows if keep(r))
    first20 = lambda r: r["id"].startswith("b") and r["id"] <= "b20"
    return {"b01_b20": {"before": count(first20, "before"), "after": count(first20, "after")},
            "all": {"before": count(lambda r: True, "before"), "after": count(lambda r: True, "after")}}


def call(conn, fn, *args):
    marks = ", ".join("%s::jsonb" for _ in args)
    return conn.execute(f"select app.{fn}({marks})", [json.dumps(a) for a in args]).fetchone()[0]


def revalidate_run(conn, run_id: int) -> dict | None:
    """The last try with a step 11 row, re-run; None when the run has none."""
    row = conn.execute("select try, input, output from app.run_step where run_id = %s and step = 11 "
                       "and output is not null order by try desc limit 1", (run_id,)).fetchone()
    if row is None:
        return None
    try_, in11, out11 = row
    in10, = conn.execute("select input from app.run_step where run_id = %s and step = 10 and try = %s",
                         (run_id, try_)).fetchone()
    step10 = call(conn, "step10_compute", in10["profile"], in10["targets"], in10["step6"], in10["step7"],
                  in10["step8"], in10["step9"], in10["brief"])
    step11 = call(conn, "step11_validate", step10, in11["brief"], in11["targets"], in11["frame"], in11["picks"])
    return {"try": try_, "before": bool(out11["passed"]), "after": bool(step11["passed"]),
            "failures": [f["text"] for f in step11["failures"]],
            "fermentables": [{"name": f["name"], "kg": f["kg"], "pct": f["pct"]} for f in step10["fermentables"]],
            "hops": [{"name": h["name"], "g": h["g"]} for h in step10["hops"]],
            "extras": [{"name": e["name"], "g": e["g"]} for e in step10["extras"]],
            "numbers": step10["numbers"], "rounding": step10.get("rounding")}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.revalidate")
    parser.add_argument("results", help="a results file from evals.run --save")
    parser.add_argument("--save", action="store_true", help="write evals/results/<date>-<label>.json")
    parser.add_argument("--label", default="revalidate")
    args = parser.parse_args(argv)
    source = json.loads(Path(args.results).read_text(encoding="utf-8"))
    conn = connect()
    rows = []
    try:
        for r in source["results"]:
            done = revalidate_run(conn, r["run_id"]) if r.get("run_id") else None
            conn.rollback()
            if done is None:
                continue
            rows.append({"id": r["id"], "run_id": r["run_id"], **done})
    finally:
        conn.close()
    for r in rows:
        print(f"{r['id']} try {r['try']}: before {'pass' if r['before'] else 'fail'}, "
              f"after {'pass' if r['after'] else 'fail'}")
        for text in r["failures"]:
            print(f"    {text}")
        print("    " + ", ".join(f"{f['name']} {float(f['kg']):g} kg" for f in r["fermentables"]))
        print("    " + ", ".join(f"{h['name']} {float(h['g']):g} g" for h in r["hops"]))
    t = totals(rows)
    print(f"b01-b20 before {t['b01_b20']['before']} after {t['b01_b20']['after']}; "
          f"all before {t['all']['before']} after {t['all']['after']}")
    if args.save:
        date = datetime.date.today().isoformat()
        path = RESULTS_DIR / f"{date}-{args.label}.json"
        doc = {"date": date, "label": args.label, "source": Path(args.results).name, "results": rows, "totals": t}
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"saved {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
