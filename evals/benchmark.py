"""The D2 benchmark for step 1: one model configuration per call, summary, markdown table.

    python -m evals.benchmark --model TAG [--think] [--runs 3] [--save]
    python -m evals.benchmark --table evals/results/<date>-m1-benchmark.json

Design: docs/work/m1-read-request/plan.md Task 5. Every configuration runs the same prompt and
contract (their sha256 is stored). Quality decides; speed only breaks a tie.
"""

import argparse
import datetime
import hashlib
import json
import math
import re
import statistics
import subprocess
import sys
import urllib.request

from evals import grade, run
from loaders.db import connect

NUM_CTX = 8192
OLLAMA = "http://localhost:11434"
PROMPT_FILE = run.ROOT / "shared" / "prompts" / "step1.system.md"
CONTRACT_FILE = run.ROOT / "shared" / "contracts" / "step1.output.schema.json"
BAR = 19  # briefs right out of 20, in every run


def ollama(*args) -> str:
    return subprocess.run(["docker", "exec", "ollama", "ollama", *args],
                          capture_output=True, text=True, check=True).stdout


def ollama_post(path, body, timeout=1800) -> dict:
    req = urllib.request.Request(OLLAMA + path, data=json.dumps(body).encode("utf-8"),
                                 method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def unload_all() -> None:
    for line in ollama("ps").splitlines()[1:]:
        if line.strip():
            ollama("stop", line.split()[0])


def load(model: str) -> None:
    """Load the model at the pipeline's context, so the first real call does not reload it."""
    ollama_post("/api/generate", {"model": model, "prompt": "", "options": {"num_ctx": NUM_CTX}})


def processor_split(ps_text: str, model: str) -> str:
    """The PROCESSOR column of `ollama ps` for one model ("100% GPU", "15%/85% CPU/GPU")."""
    for line in ps_text.splitlines()[1:]:
        if line.split() and line.split()[0] == model:
            match = re.search(r"\d+%(?:/\d+%)? (?:CPU/GPU|GPU/CPU|CPU|GPU)", line)
            return match.group(0) if match else "unknown"
    return "not loaded"


def model_details(model: str) -> dict:
    d = ollama_post("/api/show", {"model": model}, timeout=60).get("details", {})
    return {"quantization_level": d.get("quantization_level"),
            "parameter_size": d.get("parameter_size")}


def percentile(values, p) -> float:
    """Nearest rank."""
    ordered = sorted(values)
    return ordered[max(1, math.ceil(p / 100 * len(ordered))) - 1]


def _all_right(r) -> bool:
    return bool(r["run_ok"] and r["ran"][1] and r["step1"]["ok"])


def summarise(runs: list[list[dict]]) -> dict:
    """`runs`: one list of runner results per pass over the briefs."""
    results = [r for one in runs for r in one]
    fields = {}
    for f in grade.STEP1_FIELDS:
        right = sum(bool(r["run_ok"] and r["ran"][1] and r["step1"].get(f)) for r in results)
        fields[f] = right / len(results)
    seconds = [r["llm"]["llm_ms"] / 1000 for r in results if r.get("llm")]
    return {
        "all_right": [sum(_all_right(r) for r in one) for one in runs],
        "briefs": len(runs[0]),
        "fields": fields,
        "median_s": statistics.median(seconds) if seconds else None,
        "p90_s": percentile(seconds, 90) if seconds else None,
        "retries": sum(1 for r in results if r.get("llm") and r["llm"].get("tries") == 2),
        "failed_runs": sum(not r["run_ok"] for r in results),
    }


def meets_bar(summary: dict) -> bool:
    return all(n >= BAR for n in summary["all_right"])


def pick_best(configs: dict) -> str:
    """Most right in total, then the higher worst run, then the lower median time."""
    def key(name):
        s = configs[name]["summary"]
        return (-sum(s["all_right"]), -min(s["all_right"]), s["median_s"] or math.inf)
    return min(configs, key=key)


def markdown_table(configs: dict) -> str:
    fields = list(grade.STEP1_FIELDS)
    head = ["model", "quant", "think", "split", "all right per run", *fields, "median s", "p90 s",
            "retries"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for c in configs.values():
        s = c["summary"]
        cells = [c["model"], c.get("quantization_level") or "?", "on" if c["think"] else "off",
                 c.get("split", "?"), " / ".join(f"{n}/{s['briefs']}" for n in s["all_right"]),
                 *(f"{s['fields'][f]:.0%}" for f in fields),
                 "-" if s["median_s"] is None else f"{s['median_s']:.1f}",
                 "-" if s["p90_s"] is None else f"{s['p90_s']:.1f}", str(s["retries"])]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_config(doc, key, config):
    """Store one configuration with the hashes of the prompt and contract it ran with."""
    config = {**config, "prompt_sha256": sha256(PROMPT_FILE), "contract_sha256": sha256(CONTRACT_FILE)}
    doc["configs"][key] = config


def results_path():
    return run.RESULTS_DIR / f"{datetime.date.today().isoformat()}-m1-benchmark.json"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.benchmark")
    parser.add_argument("--model")
    parser.add_argument("--think", action="store_true")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--table", metavar="PATH", help="print the markdown table of a saved file")
    args = parser.parse_args(argv)

    if args.table:
        print(markdown_table(json.loads(open(args.table, encoding="utf-8").read())["configs"]))
        return 0
    if not args.model:
        parser.error("--model is required")

    briefs = run.load_briefs()
    unload_all()
    load(args.model)
    split = processor_split(ollama("ps"), args.model)
    details = model_details(args.model)
    print(f"{args.model} think={'on' if args.think else 'off'} split={split}", flush=True)
    conn = connect()
    runs = []
    try:
        for i in range(args.runs):
            runs.append([run.run_brief(conn, b, args.model, args.think) for b in briefs])
            print(f"run {i + 1}: {sum(_all_right(r) for r in runs[-1])}/{len(briefs)} right",
                  flush=True)
    finally:
        conn.close()
        unload_all()
    summary = summarise(runs)
    config = {"model": args.model, "think": args.think, "split": split, **details,
              "num_ctx": NUM_CTX, "summary": summary, "runs": runs}
    print(json.dumps(summary, indent=2))
    print("meets the bar" if meets_bar(summary) else "below the bar")
    if args.save:
        path = results_path()
        run.RESULTS_DIR.mkdir(exist_ok=True)
        doc = (json.loads(path.read_text(encoding="utf-8")) if path.exists()
               else {"date": datetime.date.today().isoformat(), "configs": {}})
        add_config(doc, f"{args.model}|{'think' if args.think else 'no-think'}", config)
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"saved {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
