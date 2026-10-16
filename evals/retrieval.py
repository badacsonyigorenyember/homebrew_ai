"""Retrieval eval: recall@5 and MRR@10 of app.kb_search over the book question set.

    python -m evals.retrieval [--save LABEL]
    python -m evals.retrieval --question "how long should a diacetyl rest be"

Questions are in evals/retrieval_questions.toml. An expected passage counts as found when a
result from the question's book contains the expected quote (after `normalise`).
Design: docs/work/s4-books-kb/plan.md Task 7.
"""

import argparse
import datetime
import json
import re
import tomllib
from pathlib import Path

from loaders import books
from loaders.db import connect

ROOT = Path(__file__).resolve().parent
QUESTIONS_FILE = ROOT / "retrieval_questions.toml"
RESULTS_DIR = ROOT / "results"
SEARCH_SQL = "select * from app.kb_search(%s, %s::extensions.vector, %s)"
TOP_K = 5  # recall is measured on the top 5
MRR_K = 10  # reciprocal rank looks at the top 10

# Set once from the first measured run (Task 9), before any tuning change; never moved
# afterwards without a Deviation line in the plan.
RECALL_AT_5_BAR: float | None = None

QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                        "–": "-", "—": "-"})


def search(conn, question: str, k: int = 5) -> list[dict]:
    """The top k chunks for a question: embed it with bge-m3, then app.kb_search."""
    vector, _ = books.embed(question)
    text = "[" + ",".join(str(x) for x in vector) + "]"
    cur = conn.execute(SEARCH_SQL, (question, text, k))
    names = [d.name for d in cur.description]
    return [dict(zip(names, row)) for row in cur.fetchall()]


def normalise(s: str) -> str:
    """Lower case, one space between words, curly quotes and dashes made plain."""
    return re.sub(r"\s+", " ", s.translate(QUOTES).lower()).strip()


def is_hit(result: dict, expect: dict, book: str) -> bool:
    return result["source_slug"] == book and normalise(expect["quote"]) in normalise(result["text"])


def ranks_found(results: list[dict], expects: list[dict], book: str) -> list[int | None]:
    """For each expected passage, the 1-based rank of the first result that hits it, or None."""
    return [next((i for i, r in enumerate(results, 1) if is_hit(r, e, book)), None)
            for e in expects]


def recall_at_k(results, expects, book, k) -> float:
    """Share of the expected passages found in the top k results."""
    found = [rank for rank in ranks_found(results, expects, book) if rank is not None and rank <= k]
    return len(found) / len(expects)


def reciprocal_rank(results, expects, book, k=10) -> float:
    """1 / rank of the first result that hits any expected passage; 0 if none in the top k."""
    ranks = [rank for rank in ranks_found(results, expects, book) if rank is not None and rank <= k]
    return 1 / min(ranks) if ranks else 0.0


def load_questions() -> list[dict]:
    with open(QUESTIONS_FILE, "rb") as f:
        return tomllib.load(f)["question"]


def run_questions(conn, questions: list[dict]) -> list[dict]:
    rows = []
    for q in questions:
        results = search(conn, q["question"], MRR_K)
        rows.append({
            "id": q["id"], "book": q["book"], "question": q["question"],
            "expect_pages": [e["page"] for e in q["expect"]],
            "ranks": ranks_found(results, q["expect"], q["book"]),
            "recall_at_5": recall_at_k(results, q["expect"], q["book"], TOP_K),
            "rr": reciprocal_rank(results, q["expect"], q["book"], MRR_K),
            "top5_chunk_ids": [r["chunk_id"] for r in results[:TOP_K]],
            "top5_pages": [r["page"] for r in results[:TOP_K]],
            "top5_scores": [round(r["score"], 5) for r in results[:TOP_K]],
        })
    return rows


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def summarise(rows: list[dict]) -> dict:
    def part(subset):
        return {"questions": len(subset), "recall_at_5": mean(r["recall_at_5"] for r in subset),
                "mrr_at_10": mean(r["rr"] for r in subset)}
    summary = part(rows)
    summary["per_book"] = {b: part([r for r in rows if r["book"] == b])
                           for b in sorted({r["book"] for r in rows})}
    summary["bar"] = RECALL_AT_5_BAR
    return summary


def print_report(rows: list[dict], summary: dict) -> None:
    print(f"recall@5 {summary['recall_at_5']:.3f}   MRR@10 {summary['mrr_at_10']:.3f}"
          f"   ({summary['questions']} questions)")
    for book, s in summary["per_book"].items():
        print(f"  {book:<28} recall@5 {s['recall_at_5']:.3f}   MRR@10 {s['mrr_at_10']:.3f}"
              f"   ({s['questions']})")
    print("misses (expected page, rank found; - = not in top 10):")
    for r in rows:
        if r["recall_at_5"] < 1:
            found = ", ".join(f"p{p}: {rank or '-'}" for p, rank in zip(r["expect_pages"], r["ranks"]))
            print(f"  {r['id']} [{r['book']}] {found}")
    if RECALL_AT_5_BAR is None:
        print("bar: not set yet")
    else:
        met = summary["recall_at_5"] >= RECALL_AT_5_BAR
        print(f"bar {RECALL_AT_5_BAR}: {'bar met' if met else 'bar not met'}")


def show_question(conn, question: str) -> None:
    for i, r in enumerate(search(conn, question, TOP_K), 1):
        text = " ".join(r["text"].split())[:200]
        print(f"{i}. {r['source_slug']} p{r['page']} | {r['section_path']} | "
              f"{r['score']:.4f}\n   {text}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Retrieval eval over the book question set.")
    parser.add_argument("--save", metavar="LABEL",
                        help="write evals/results/<date>-<LABEL>.json")
    parser.add_argument("--question", help="print the top 5 chunks for one question")
    args = parser.parse_args()
    conn = connect()
    try:
        if args.question:
            show_question(conn, args.question)
            return
        rows = run_questions(conn, load_questions())
    finally:
        conn.close()
    summary = summarise(rows)
    print_report(rows, summary)
    if args.save:
        path = RESULTS_DIR / f"{datetime.date.today()}-{args.save}.json"
        path.write_text(json.dumps({"summary": summary, "questions": rows}, indent=2) + "\n")
        print(f"saved {path}")


if __name__ == "__main__":
    main()
