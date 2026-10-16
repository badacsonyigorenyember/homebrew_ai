"""Retrieval eval metrics: pure functions, no stack needed."""

from evals.retrieval import is_hit, normalise, recall_at_k, reciprocal_rank


def result(text, book="water"):
    return {"source_slug": book, "text": text}


def expect(quote):
    return {"page": 1, "quote": quote}


def filler(n):
    return [result(f"unrelated chunk {i}") for i in range(n)]


def test_recall_at_5():
    expects = [expect("alpha beta gamma delta"), expect("epsilon zeta eta theta")]
    at_rank_3 = filler(2) + [result("see alpha beta gamma delta here")] + filler(3)
    assert recall_at_k(at_rank_3, expects, "water", 5) == 0.5
    at_rank_6 = filler(5) + [result("see alpha beta gamma delta here")]
    assert recall_at_k(at_rank_6, expects, "water", 5) == 0


def test_reciprocal_rank():
    expects = [expect("alpha beta gamma delta")]
    at_rank_2 = filler(1) + [result("alpha beta gamma delta")]
    assert reciprocal_rank(at_rank_2, expects, "water") == 0.5
    assert reciprocal_rank(filler(10), expects, "water") == 0


def test_is_hit_wrong_book():
    chunk = result("alpha beta gamma delta", book="yeast")
    assert not is_hit(chunk, expect("alpha beta gamma delta"), "water")
    assert is_hit(chunk, expect("alpha beta gamma delta"), "yeast")


def test_normalise_whitespace_and_quotes():
    assert normalise("It’s  a\n“Big”\tone – really—yes") == "it's a \"big\" one - really-yes"
    assert is_hit(result("It’s  a\nbig   one"), expect("it's a big one"), "water")


# --- the question set -------------------------------------------------------------------------

import pytest

from evals.retrieval import load_questions
from loaders.books import BOOKS
from loaders.db import connect


def test_question_set_shape():
    questions = load_questions()
    assert len(questions) >= 40
    ids = [q["id"] for q in questions]
    assert len(ids) == len(set(ids))
    for book in BOOKS:
        assert sum(q["book"] == book for q in questions) >= 8, book
    for q in questions:
        assert q["book"] in BOOKS, q["id"]
        assert q["expect"], q["id"]
        for e in q["expect"]:
            assert 4 <= len(e["quote"].split()) <= 12, (q["id"], e["quote"])


@pytest.mark.stack
def test_every_quote_resolves():
    """An unresolved quote would silently lower recall."""
    unresolved = []
    with connect() as conn:
        texts = {}
        for q in load_questions():
            if q["book"] not in texts:
                rows = conn.execute(
                    "select c.text from kb.chunk c join ref.source s on s.id = c.source_id"
                    " where s.slug = %s", (q["book"],)).fetchall()
                texts[q["book"]] = [normalise(r[0]) for r in rows]
            for e in q["expect"]:
                if not any(normalise(e["quote"]) in t for t in texts[q["book"]]):
                    unresolved.append((q["id"], e["quote"]))
    assert not unresolved


def _row(group, recall, book="water"):
    return {"id": "q", "book": book, "group": group, "recall_at_5": recall, "rr": recall,
            "expect_pages": [1], "ranks": [1]}


def test_summarise_bar_on_books_only():
    from evals.retrieval import summarise
    s = summarise([_row("books", 0.5), _row("articles", 0.0, "mtf")])
    assert s["bar_met"] is True
    assert s["groups"]["articles"]["recall_at_5"] == 0.0
    assert s["groups"]["books"]["recall_at_5"] == 0.5


def test_summarise_bar_not_met():
    from evals.retrieval import summarise
    s = summarise([_row("books", 0.3), _row("articles", 1.0, "mtf")])
    assert s["bar_met"] is False


def test_cite_without_page():
    from evals.retrieval import cite
    r = {"source_slug": "mtf", "page": None, "source_title": "Lacto", "source_url": "https://x.test/a"}
    assert cite(r) == "mtf | Lacto | https://x.test/a"


def test_cite_with_page():
    from evals.retrieval import cite
    assert cite({"source_slug": "water", "page": 12, "source_title": "T", "source_url": None}) == "water p12"
