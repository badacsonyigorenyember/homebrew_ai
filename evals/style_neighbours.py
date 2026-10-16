"""Style-neighbour eval: does step 2 tell apart styles the BJCP exam lists as easy to confuse?

    python -m evals.style_neighbours [--save]

evals/style_neighbours.toml holds 91 study-guide triples and 83 briefs (one per style). Each brief
goes to app.step2_best_style in two runs:
  Run A  the brief as written, `named` empty. All 83 briefs.
  Run B  the same brief with the triple's family noun (ale, lager, ...) as `named`. Only styles
         in a triple whose three styles share one family; the other triples run in A only.
`named` is a boost on the style's name, not a filter, so Run B shows step 2's real behaviour when a
user writes a family word. No pass bar: the numbers are read by a person.
Design: docs/work/s6-style-neighbours/plan.md Task 3.
"""

import argparse
import datetime
import json
import tomllib
from pathlib import Path

from loaders.db import connect

ROOT = Path(__file__).resolve().parent
CHECK_FILE = ROOT / "style_neighbours.toml"
RESULTS_DIR = ROOT / "results"
# The pipeline default: both guides are scored, and a BA winner with a BJCP pair comes back as the pair.
GUIDE = "any"
STEP2_SQL = "select app.step2_best_style(%s::jsonb, %s, %s)"


def load() -> tuple[list[dict], list[dict]]:
    """(triples, briefs) from the check file."""
    with open(CHECK_FILE, "rb") as f:
        data = tomllib.load(f)
    return data["triple"], data["brief"]


def step1_brief(b: dict, family: str | None = None) -> dict:
    """The step 1 brief the brief's sentence should produce; `named` is the family noun in Run B."""
    return {
        "named": family, "stated": dict(b["stated"]), "hints": list(b["hints"]),
        "wanted": [], "excluded": [], "inventory": [], "unknown": list(b["unknown"]),
        "guidance": True,
    }


def run_b_family(triples: list[dict]) -> dict[str, str]:
    """code -> family noun, for every style in a single-family triple."""
    return {code: t["family"] for t in triples if t["family"] for code in t["codes"]}


def ba_pairs(conn) -> dict[str, str]:
    """BA code -> BJCP pair, as step 2 swaps them (a pair that is a BJCP catch-all is kept as BA)."""
    rows = conn.execute(
        "select ba_code, bjcp_code from app.style_pair() "
        "where bjcp_code not in (select code from app.bjcp_catch_all())").fetchall()
    return dict(rows)


def measure(conn, b: dict, family: str | None = None, pairs: dict[str, str] | None = None) -> dict:
    """Run step 2 on one brief. `pairs` is ba_pairs(conn), read once per run."""
    pairs = ba_pairs(conn) if pairs is None else pairs
    (out,) = conn.execute(STEP2_SQL, (json.dumps(step1_brief(b, family)), b["request"], GUIDE)).fetchone()
    style = out["style"]
    picked = None
    if style:
        picked = style["code"] if style["guide"] == "BJCP" else f"BA {style['code']}"
    top3 = []
    for c in out["candidates"][:3]:
        if c["guide"] == "BJCP":
            top3.append(c["code"])
        else:
            top3.append(pairs.get(c["code"], f"BA {c['code']}"))
    return {"code": b["code"], "picked": picked, "top3": top3,
            "right_first": picked == b["code"], "in_top3": b["code"] in top3}


def summarise(results: list[dict]) -> dict:
    n = len(results)
    return {
        "n": n,
        "right_first": sum(r["right_first"] for r in results),
        "in_top3": sum(r["in_top3"] for r in results),
        "no_style": sum(r["picked"] is None for r in results),
        "ba_picks": sum(bool(r["picked"]) and r["picked"].startswith("BA ") for r in results),
    }


def confusions(triples: list[dict], results: list[dict]) -> list[dict]:
    """Per triple, for each of its styles: ok, the partner picked instead, other <code>, or none."""
    by_code = {r["code"]: r for r in results}
    rows = []
    for t in triples:
        row = {"id": t["id"], "styles": {}}
        for code in t["codes"]:
            r = by_code.get(code)
            if r is None:
                continue
            if r["picked"] is None:
                row["styles"][code] = "none"
            elif r["picked"] == code:
                row["styles"][code] = "ok"
            elif r["picked"] in t["codes"]:
                row["styles"][code] = r["picked"]
            else:
                row["styles"][code] = f"other {r['picked']}"
        rows.append(row)
    return rows


def gap(results_a: list[dict], results_b: list[dict]) -> dict:
    """B minus A on the codes Run B covers (never A's whole set against B's subset)."""
    in_b = {r["code"] for r in results_b}
    a = summarise([r for r in results_a if r["code"] in in_b])
    b = summarise(results_b)
    return {"a": a, "b": b, "right_first": b["right_first"] - a["right_first"],
            "in_top3": b["in_top3"] - a["in_top3"]}


def name_scores(conn, family: str, codes: list[str]) -> dict[str, float]:
    """code -> how much the family noun lifts that style's name (app.style_name_score, 0 to 1)."""
    rows = conn.execute(
        "select s.code, app.style_name_score(%s, s.name, (select array_agg(a.alias) "
        "from app.style_alias() a where a.guide = s.guide and a.code = s.code)) "
        "from ref.beer_style s where s.guide = 'BJCP' and s.code = any(%s)", (family, codes)).fetchall()
    return {code: round(float(score), 2) for code, score in rows}


def run(conn, briefs: list[dict], families: dict[str, str] | None = None) -> list[dict]:
    """One run. With `families`, only the briefs whose code is in it, each named by its noun."""
    pairs = ba_pairs(conn)
    if families is None:
        return [measure(conn, b, None, pairs) for b in briefs]
    return [measure(conn, b, families[b["code"]], pairs) for b in briefs if b["code"] in families]


def pct(x: int, n: int) -> str:
    return f"{x}/{n} {100 * x / n:.0f}%"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--save", action="store_true", help="write evals/results/<date>-s6.json")
    args = parser.parse_args()

    triples, briefs = load()
    families = run_b_family(triples)
    with connect() as conn:
        run_a = run(conn, briefs)
        run_b = run(conn, briefs, families)
        scores = {t["id"]: name_scores(conn, t["family"], t["codes"]) for t in triples if t["family"]}
    a_all = summarise(run_a)
    g = gap(run_a, run_b)
    mixed = [t["id"] for t in triples if not t["family"]]

    print(f"guide: {GUIDE}   briefs: {len(briefs)}   triples: {len(triples)} "
          f"({len(triples) - len(mixed)} single-family, {len(mixed)} mixed: A only)")
    print(f"{'':<28}{'right first':>14}{'top 3':>14}{'no style':>10}{'BA picks':>10}")
    for label, s in (("Run A, all briefs", a_all), ("Run A, Run B briefs", g["a"]), ("Run B (family named)", g["b"])):
        print(f"{label:<28}{pct(s['right_first'], s['n']):>14}{pct(s['in_top3'], s['n']):>14}"
              f"{s['no_style']:>10}{s['ba_picks']:>10}")
    n_b = g["b"]["n"]
    print(f"{'gap B - A':<28}{g['right_first']:>+8} ({100 * g['right_first'] / n_b:+.0f} pts)"
          f"{g['in_top3']:>+8} ({100 * g['in_top3'] / n_b:+.0f} pts)")

    conf_a = {c["id"]: c["styles"] for c in confusions(triples, run_a)}
    conf_b = {c["id"]: c["styles"] for c in confusions(triples, run_b)}
    print("\nper triple (ok = right first; a code = that style was picked instead)")
    for t in triples:
        a_text = "  ".join(f"{c}:{v}" for c, v in conf_a[t["id"]].items())
        print(f"#{t['id']:<4}{' / '.join(t['codes'])}  A  {a_text}")
        if t["family"]:
            b_text = "  ".join(f"{c}:{v}" for c, v in conf_b[t["id"]].items())
            lifts = "  ".join(f"{c}={v}" for c, v in scores[t["id"]].items())
            print(f"{'':<5}{'':<13}B  {b_text}   [\"{t['family']}\" name score {lifts}]")
        else:
            print(f"{'':<5}{'':<13}mixed: A only")

    if args.save:
        RESULTS_DIR.mkdir(exist_ok=True)
        path = RESULTS_DIR / f"{datetime.date.today().isoformat()}-s6.json"
        path.write_text(json.dumps({
            "guide": GUIDE, "run_a_all": a_all, "gap": g, "mixed_triples": len(mixed),
            "run_a": run_a, "run_b": run_b,
            "confusions_a": confusions(triples, run_a), "confusions_b": confusions(triples, run_b),
            "family_name_scores": scores,
        }, indent=2) + "\n")
        print(f"\nsaved {path}")


if __name__ == "__main__":
    main()
