"""Book loader: turning a Docling chunk result into prose rows (synthetic chunks only)."""

import pytest

from dataclasses import replace

from loaders.books import (ARTICLES, BOOKS, EMBED_DIMS, ROOT, SOURCES, Book, check_result,
                           chunk_rows, clean_markdown, docling_form, parse_embedding,
                           replace_chunks, strip_tables, upsert_source)
from loaders.db import connect

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


MD_DOC = """# Doc

Source: https://example.test/doc  
Some Author, example.test.  
Saved 2026-10-16 for local reference.

Intro text [2] with a marker.

## Part One

Prose.
"""

MD_ARTICLE = Book(slug="a", title="A", edition="1", publisher="P", licence="L",
                  file_path="x.md", url="https://example.test/doc",
                  drop_sections=("See Also", "References"))


def test_clean_markdown_drops_header_and_markers():
    out = clean_markdown(MD_DOC)
    assert out.startswith("# Doc\n")
    for gone in ("Source:", "Some Author", "Saved 2026", "[2]"):
        assert gone not in out
    assert "Intro text with a marker." in out and "## Part One" in out


def test_clean_markdown_requires_header():
    with pytest.raises(ValueError):
        clean_markdown("# Doc\n\nJust prose.\n")
    with pytest.raises(ValueError):
        clean_markdown("# Doc\n\nSource: http://x\nno saved line\n")


def test_markdown_rows():
    path = ["Doc", "Part One"]
    chunks = [chunk(0, PROSE, pages=(), headings=path),
              chunk(1, PROSE, pages=(), headings=["Doc", "Part One", "See Also", "External Resources"]),
              chunk(2, PROSE, pages=(), headings=["Doc", "References"])]
    rows, stats = chunk_rows(chunks, MD_ARTICLE)
    assert len(rows) == 1
    assert rows[0]["page"] is None and rows[0]["section_path"] == "Doc > Part One"
    assert stats["dropped_section"] == 2


def test_chunk_rows_drops_pdf_section_case_insensitive():
    book = replace(BOOK, drop_sections=("References",))
    rows, stats = chunk_rows([chunk(0, PROSE, pages=(8,), headings=["REFERENCES"]),
                              chunk(1, PROSE, pages=(8,), headings=["Findings"])], book)
    assert [r["section_path"] for r in rows] == ["Findings"]
    assert stats["dropped_section"] == 1


def test_chunk_rows_pdf_without_page_raises():
    with pytest.raises(ValueError):
        chunk_rows([chunk(0, PROSE, pages=())], BOOK)


def test_docling_form_markdown():
    assert docling_form(MD_ARTICLE)["convert_from_formats"] == "md"
    assert docling_form(BOOK)["convert_from_formats"] == "pdf"


def test_sources_slugs_distinct():
    assert not set(BOOKS) & set(ARTICLES)
    assert len(SOURCES) == 17
    assert all(a.url for a in ARTICLES.values())


def test_article_urls_match_source_lines():
    for slug, art in ARTICLES.items():
        path = ROOT / art.file_path
        if art.file_path.endswith(".md") and slug != "bjcp-2021-introductions" and path.exists():
            line = next(l for l in path.read_text(encoding="utf-8").splitlines()
                        if l.startswith("Source:"))
            assert line.removeprefix("Source:").strip() == art.url, slug


# --- stack tests: database writes, always rolled back ---

def synthetic_rows(n, tag="r"):
    return [{"section_path": f"S{i}", "page": i + 1, "text": f"{tag} prose number {i}",
             "tokens": 5, "embedding": [0.01 * (i + 1)] * EMBED_DIMS} for i in range(n)]


def chunk_count(conn, source_id=None):
    if source_id is None:
        return conn.execute("select count(*) from kb.chunk").fetchone()[0]
    return conn.execute("select count(*) from kb.chunk where source_id = %s",
                        (source_id,)).fetchone()[0]


def throwaway_source(conn, slug):
    return upsert_source(conn, Book(slug=slug, title=slug, edition="1", publisher="P",
                                    licence="L", file_path="x.pdf"))


@pytest.mark.stack
def test_upsert_source_keeps_id():
    conn = connect()
    try:
        before = conn.execute("select id, edition from ref.source where slug = %s",
                              ("palmer-how-to-brew",)).fetchone()
        book = replace(BOOKS["palmer-how-to-brew"], edition="Changed edition for test")
        assert upsert_source(conn, book) == before[0]
        edition = conn.execute("select edition from ref.source where id = %s",
                               (before[0],)).fetchone()[0]
        assert edition == "Changed edition for test" != before[1]
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.stack
def test_replace_chunks_only_touches_its_book():
    conn = connect()
    try:
        a = throwaway_source(conn, "test-book-a")
        b = throwaway_source(conn, "test-book-b")
        others_before = chunk_count(conn) - chunk_count(conn, a) - chunk_count(conn, b)
        assert replace_chunks(conn, a, synthetic_rows(3)) == 3
        replace_chunks(conn, b, synthetic_rows(3, "b"))
        assert replace_chunks(conn, a, synthetic_rows(2)) == 2
        assert chunk_count(conn, a) == 2
        assert chunk_count(conn, b) == 3
        assert chunk_count(conn) - 2 - 3 == others_before
    finally:
        conn.rollback()
        conn.close()


@pytest.mark.stack
def test_replace_chunks_twice_same_rows():
    fingerprint = ("select count(*), md5(string_agg(text, '|' order by page, section_path, text)) "
                   "from kb.chunk where source_id = %s")
    conn = connect()
    try:
        a = throwaway_source(conn, "test-book-a")
        rows = synthetic_rows(4)
        replace_chunks(conn, a, rows)
        first = conn.execute(fingerprint, (a,)).fetchone()
        replace_chunks(conn, a, rows)
        assert conn.execute(fingerprint, (a,)).fetchone() == first
    finally:
        conn.rollback()
        conn.close()


def test_strip_tables_removes_formula_placeholder():
    text = "Before the formula.\n\n<!-- formula-not-decoded -->\n\nAfter the formula."
    assert strip_tables(text) == "Before the formula.\n\nAfter the formula."
