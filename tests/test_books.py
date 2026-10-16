"""Book loader: turning a Docling chunk result into prose rows (synthetic chunks only)."""

import pytest

from loaders.books import (BOOKS, EMBED_DIMS, Book, check_result, chunk_rows, docling_form,
                           parse_embedding, strip_tables)

PROSE = "word " * 25  # 25 words, above MIN_WORDS

BOOK = Book(slug="t", title="T", edition="1", publisher="P", licence="L", file_path="x.pdf",
            skip_pages=((1, 3),))


def chunk(index, text, pages=(10,), headings=None):
    return {"chunk_index": index, "raw_text": text, "text": text, "headings": headings,
            "page_numbers": list(pages)}


def test_check_result_raises_on_failed_document():
    result = {"documents": [{"status": "failure"}], "chunks": []}
    with pytest.raises(RuntimeError):
        check_result(result)


def test_check_result_raises_on_no_chunks():
    with pytest.raises(RuntimeError):
        check_result({"documents": [{"status": "success"}], "chunks": []})


def test_strip_tables_keeps_prose():
    text = "First paragraph.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n\nSecond paragraph."
    out = strip_tables(text)
    assert "First paragraph." in out and "Second paragraph." in out
    assert not any(line.strip().startswith("|") for line in out.splitlines())


def test_chunk_rows_drops_table_only_chunk():
    table = "| a | b |\n|---|---|\n| 1 | 2 |"
    rows, stats = chunk_rows([chunk(0, PROSE), chunk(1, table, pages=(11,))], BOOK)
    assert len(rows) == 1
    assert stats["dropped_short"] == 1
    assert 11 in stats["table_pages"]


def test_chunk_rows_skip_pages():
    rows, stats = chunk_rows([chunk(0, PROSE, pages=(2,)), chunk(1, PROSE, pages=(4,))], BOOK)
    assert [r["page"] for r in rows] == [4]
    assert stats["dropped_skip_page"] == 1


def test_chunk_rows_page_and_section():
    rows, _ = chunk_rows([chunk(0, PROSE, pages=(13, 12), headings=["Hops", "Bittering"])], BOOK)
    assert rows[0]["page"] == 12
    assert rows[0]["section_path"] == "Hops > Bittering"


def test_parse_embedding_rejects_wrong_dims():
    with pytest.raises(ValueError):
        parse_embedding({"embeddings": [[0.1] * 768], "prompt_eval_count": 5})
    vector, tokens = parse_embedding({"embeddings": [[0.1] * EMBED_DIMS], "prompt_eval_count": 5})
    assert len(vector) == EMBED_DIMS and tokens == 5


def test_docling_form_sets_bge_m3_tokenizer():
    form = docling_form(BOOKS["palmer-how-to-brew"])
    assert form["chunking_tokenizer"] == "BAAI/bge-m3"
    assert form["chunking_use_markdown_tables"] == "true"
