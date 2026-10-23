"""R13 fit test: does one Ollama call for steps 6-9 fit in num_ctx, and does its answer pass the check?

    python -m evals.fit_test [--runs evals/results/2026-10-18-s9.json] [--num-ctx 8192]
                             [--brief b01] [--tag TEXT] [--save]

Design: docs/work/m5-choose-ingredients/plan.md Task 5. For each brief it reads the stored outputs
of steps 0, 1, 2 and 4 of a past run, rebuilds step 5, builds the candidate table and its prompt in
the database, and asks the model as step 1 does (one retry with the check's errors). The model is
unloaded before every call, so a cached prompt prefix cannot shrink `prompt_eval_count`.
A call fits when prompt tokens + the output budget fit in `num_ctx` and Ollama logged no
truncation. A brief passes when every try it made fits and the last try's proposal has no errors.
"""

import argparse
import datetime
import json
import re
import statistics
import subprocess
import sys
import time
import urllib.error

from evals import benchmark, run
from loaders.db import connect

CHOOSE_NUM_CTX = 32768  # the value the pipeline runs at, set by the fit test (docs/work/m5-choose-ingredients/fit-test.md)
NUM_PREDICT = 4096
PROMPT_FILE = run.ROOT / "shared" / "prompts" / "choose.system.md"
CONTRACT_FILE = run.ROOT / "shared" / "contracts" / "choose.proposal.schema.json"
DEFAULT_RUNS = run.RESULTS_DIR / "2026-10-18-s9.json"
RETRY = "That answer failed these checks: {errors}. Answer the same request again, as JSON in the same shape."


def fits(prompt_tokens: int, num_ctx: int, truncated: bool) -> bool:
    return not truncated and prompt_tokens + NUM_PREDICT <= num_ctx


def brief_passes(tries: list[dict]) -> bool:
    """Every try fits, and the last try's proposal has no errors."""
    return bool(tries) and all(t["fits"] for t in tries) and not tries[-1]["errors"]


def truncation_logged(log_text: str) -> bool:
    """A line that says truncat..., except llama.cpp's routine `truncated = 0` on a finished slot."""
    return any("truncat" in line.lower() and not re.search(r"truncated\s*=\s*0\b", line)
               for line in log_text.splitlines())


def ollama_log_since(started: str) -> str:
    done = subprocess.run(["docker", "logs", "ollama", "--since", started],
                          capture_output=True, text=True)
    return done.stdout + done.stderr


def read_inputs(conn, run_id: int) -> tuple[dict, dict, dict, dict]:
    """Outputs of steps 0, 1, 2 and 4 of one stored run: profile, brief, style, targets."""
    rows = {s: o for s, o in conn.execute(
        "select step, output from app.run_step where run_id = %s and step in (0, 1, 2, 4) and ok",
        (run_id,)).fetchall()}
    return rows[0], rows[1], rows[2], rows[4]


def build_prompt(conn, run_id: int) -> tuple[str, dict]:
    profile, brief, style, targets = read_inputs(conn, run_id)
    j = json.dumps
    frame = conn.execute("select app.step5_frame(%s::jsonb, %s::jsonb, %s::jsonb)",
                         (j(brief), j(profile), j(targets))).fetchone()[0]
    tbl = conn.execute("select app.choose_table(%s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb)",
                       (j(brief), j(style), j(targets), j(frame))).fetchone()[0]
    text = conn.execute("select app.choose_prompt(%s::jsonb, %s::jsonb)", (j(tbl), j(brief))).fetchone()[0]
    return text, tbl


def rejected_answer(body: str) -> dict:
    """This Ollama refuses a prompt longer than num_ctx with HTTP 400 (measured 2026-10-18), instead of
    truncating it. The refusal names the prompt's token count; it counts as a try that does not fit."""
    match = re.search(r"request \((\d+) tokens\)", body)
    return {"prompt_eval_count": int(match.group(1)) if match else 0, "_rejected": body[:300],
            "message": {"content": ""}}


def ask(model, messages, contract, num_ctx, seed=42, temperature=0) -> tuple[dict, str]:
    """One unloaded-start call; returns (Ollama's answer, the processor split while loaded)."""
    benchmark.unload_all()
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    t0 = time.time()
    try:
        answer = benchmark.ollama_post("/api/chat", {
            "model": model, "messages": messages, "stream": False, "think": False, "format": contract,
            "options": {"temperature": temperature, "seed": seed, "num_ctx": num_ctx, "num_predict": NUM_PREDICT}})
    except urllib.error.HTTPError as e:
        answer = rejected_answer(e.read().decode("utf-8", "replace"))
    answer["_wall_ms"] = round((time.time() - t0) * 1000)
    split = benchmark.processor_split(benchmark.ollama("ps"), model)
    answer["_truncated"] = truncation_logged(ollama_log_since(started))
    return answer, split


def check(conn, content, contract_text, tbl) -> list[str]:
    return conn.execute("select coalesce(errors, '{}') from app.choose_read_answer(%s, %s::json, %s::jsonb)",
                        (content, contract_text, json.dumps(tbl))).fetchone()[0]


def try_record(n, answer, split, num_ctx, errors) -> dict:
    prompt_tokens = answer.get("prompt_eval_count", 0)
    return {
        "try": n, "prompt_tokens": prompt_tokens, "output_tokens": answer.get("eval_count", 0),
        "done_reason": answer.get("done_reason"), "load_ms": round(answer.get("load_duration", 0) / 1e6),
        "llm_ms": round((answer.get("total_duration", 0) - answer.get("load_duration", 0)) / 1e6),
        "truncated": answer["_truncated"], "rejected": "_rejected" in answer, "processor": split,
        "fits": fits(prompt_tokens, num_ctx, answer["_truncated"]), "errors": errors,
    }


def one_brief(conn, model, user_text, tbl, system, contract, num_ctx) -> list[dict]:
    contract_text = json.dumps(contract)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user_text}]
    tries = []
    for n in (1, 2):
        answer, split = ask(model, messages, contract, num_ctx)
        content = answer.get("message", {}).get("content", "")
        errors = ([f"rejected by Ollama: {answer['_rejected']}"] if "_rejected" in answer
                  else check(conn, content, contract_text, tbl))
        tries.append(try_record(n, answer, split, num_ctx, errors))
        if not errors or "_rejected" in answer:
            break
        messages = messages + [{"role": "assistant", "content": content},
                               {"role": "user", "content": RETRY.format(errors="; ".join(errors))}]
    return tries


def summarise(results: list[dict]) -> dict:
    llm = [t["llm_ms"] for r in results for t in r["tries"] if t["fits"]]
    return {
        "briefs": len(results), "passed": sum(r["passed"] for r in results),
        "fit_all": sum(all(t["fits"] for t in r["tries"]) for r in results),
        "max_prompt_tokens": max((t["prompt_tokens"] for r in results for t in r["tries"]), default=0),
        "median_llm_ms": statistics.median(llm) if llm else None,
        "processors": sorted({t["processor"] for r in results for t in r["tries"]}),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(DEFAULT_RUNS))
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--brief")
    ap.add_argument("--tag", default="")
    ap.add_argument("--model", default="hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K")
    ap.add_argument("--save", action="store_true")
    args = ap.parse_args(argv)

    stored = json.load(open(args.runs, encoding="utf-8"))["results"]
    stored = [r for r in stored if not args.brief or r["id"] == args.brief]
    system = PROMPT_FILE.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT_FILE.read_text(encoding="utf-8"))
    conn = connect()
    results = []
    for r in stored:
        user_text, tbl = build_prompt(conn, r["run_id"])
        tries = one_brief(conn, args.model, user_text, tbl, system, contract, args.num_ctx)
        rec = {"id": r["id"], "run_id": r["run_id"], "prompt_chars": len(system) + len(user_text),
               "tries": tries, "passed": brief_passes(tries)}
        results.append(rec)
        t = tries[-1]
        print(f"{rec['id']} tries={len(tries)} prompt_tokens={t['prompt_tokens']} out={t['output_tokens']} "
              f"fits={all(x['fits'] for x in tries)} passed={rec['passed']} llm_ms={t['llm_ms']} "
              f"load_ms={t['load_ms']} {t['processor']} errors={t['errors'][:3]}", flush=True)
    summary = summarise(results)
    print(json.dumps(summary))
    if args.save:
        label = f"{datetime.date.today()}-m5-fit"
        path = run.RESULTS_DIR / f"{label}.json"
        doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"date": str(datetime.date.today()), "options": {}}
        doc["model"] = args.model
        doc["prompt_sha256"] = benchmark.sha256(PROMPT_FILE)
        doc["options"][f"{args.num_ctx}{args.tag}"] = {"num_ctx": args.num_ctx, "num_predict": NUM_PREDICT,
                                                       "summary": summary, "results": results}
        path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        print("saved", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
