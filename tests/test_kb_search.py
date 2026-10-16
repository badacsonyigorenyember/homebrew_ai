"""app.kb_search: hybrid retrieval on synthetic chunks under a throwaway source, rolled back.

The query embedding is one-hot on dimension 0; real bge-m3 vectors are far from it, so the
synthetic chunks win whether or not real chunks are loaded.
"""

import pytest

from loaders.books import EMBED_DIMS, Book, replace_chunks, upsert_source
from loaders.db import connect

pytestmark = pytest.mark.stack

SEARCH = "select * from app.kb_search(%s, %s::extensions.vector, %s)"


def one_hot(dim):
    vector = [0.0] * EMBED_DIMS
    vector[dim] = 1.0
    return vector


def vec_text(vector):
    return "[" + ",".join(str(x) for x in vector) + "]"


def chunk(text, dim, page=1):
    return {"section_path": "Test", "page": page, "text": text, "tokens": 5,
            "embedding": one_hot(dim)}


def load(conn, rows):
    book = Book(slug="test-kb-search", title="Test", edition="1", publisher="P", licence="L",
                file_path="x.pdf")
    source_id = upsert_source(conn, book)
    replace_chunks(conn, source_id, rows)


def search(conn, query, k=5):
    cur = conn.execute(SEARCH, (query, vec_text(one_hot(0)), k))
    names = [d.name for d in cur.description]
    return [dict(zip(names, row)) for row in cur.fetchall()]


def run(rows, query, k=5):
    conn = connect()
    try:
        load(conn, rows)
        return search(conn, query, k)
    finally:
        conn.rollback()
        conn.close()


def test_both_arms_rank_first():
    rows = [chunk("A has zyxquorble in it", 0),       # both arms
            chunk("B has zyxquorble only", 5),        # words only
            chunk("C has nothing to match", 0)]       # embedding only
    rows[2]["embedding"][1] = 0.5                     # C is a little further from the query than A
    result = run(rows, "zyxquorble fermentation")
    texts = [r["text"] for r in result]
    assert texts[0].startswith("A")
    assert {t[0] for t in texts[:3]} == {"A", "B", "C"}
    assert result[0]["vec_rank"] == 1 and result[0]["fts_rank"] == 1


def test_any_query_word_matches():
    rows = [chunk("only the word zyxquorble here", 3)]
    result = run(rows, "zyxquorble wibblefrap glorptastic")
    hit = [r for r in result if r["text"].startswith("only the word")][0]
    assert hit["fts_rank"] is not None


def test_returns_k_rows_with_source_and_page():
    rows = [chunk(f"filler chunk number {i}", i, page=i + 1) for i in range(7)]
    result = run(rows, "filler", k=5)
    assert len(result) == 5
    assert all(r["source_slug"] and r["page"] is not None for r in result)


def test_no_match_still_returns_vector_hits():
    rows = [chunk("something unrelated", 0)]
    result = run(rows, "the and of")
    assert result and all(r["fts_rank"] is None for r in result)
    assert result[0]["vec_rank"] == 1
