"""Books into the knowledge base (kb.chunk): Docling chunks, prose only, embedded with bge-m3.

Run:  .venv/bin/python -m loaders.books <slug>
To add a book: add one `Book` entry to BOOKS below, then run the command with its slug.
The steps (skip pages, checks, doc -> calc notes) are in docs/BOOKS.md.
"""

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Book:
    slug: str
    title: str
    edition: str
    publisher: str
    licence: str
    file_path: str  # relative to the repo root
    skip_pages: tuple[tuple[int, int], ...] = ()  # inclusive PDF page ranges left out
    ocr: bool = False
    notes: str | None = None


BOOKS: dict[str, Book] = {
    "palmer-how-to-brew": Book(
        slug="palmer-how-to-brew",
        title="How to Brew",
        edition="Fourth edition 2017",
        publisher="Brewers Publications",
        licence="© Brewers Publications, all rights reserved; personal copy, local use only",
        file_path="shared/rag-files/books/how_to_brew.pdf",
        # cover, praise, contents, preface, acknowledgments, abbreviations; bibliography and index
        skip_pages=((1, 26), (579, 612)),
        notes="Tables 18.5 and 24.1 in ref.fermentable; prose in kb.chunk; "
              "doc → calc notes in docs/BOOKS.md",
    ),
    "palmer-kaminski-water": Book(
        slug="palmer-kaminski-water",
        title="Water: A Comprehensive Guide for Brewers",
        edition="2013",  # the copyright page gives only the year
        publisher="Brewers Publications",
        licence="© Brewers Association, all rights reserved; personal copy, local use only",
        file_path="shared/rag-files/books/palmer_kaminski_water.pdf",
        # cover to foreword (contents, figure list, acknowledgments, foreword); last table page, index
        skip_pages=((1, 18), (238, 273)),
        notes="Prose in kb.chunk; tables and formulas not passed yet, see docs/BOOKS.md",
    ),
    "white-zainasheff-yeast": Book(
        slug="white-zainasheff-yeast",
        title="Yeast: The Practical Guide to Beer Fermentation",
        edition="2010",  # the copyright page gives only the year
        publisher="Brewers Publications",
        licence="© Brewers Association, all rights reserved; personal copy, local use only",
        file_path="shared/rag-files/books/white_zainasheff_yeast.pdf",
        # cover to foreword (contents, acknowledgments, foreword, blank pages); blank page, figure credits, references, index
        skip_pages=((1, 21), (305, 325)),
        notes="Prose in kb.chunk; tables and formulas not passed yet, see docs/BOOKS.md",
    ),
}

DOCLING_URL = "http://localhost:5001"
OLLAMA_URL = "http://localhost:11434"
EMBED_MODEL = "bge-m3"
EMBED_DIMS = 1024
MAX_TOKENS = 512
MIN_WORDS = 20
SCRATCH = ROOT / "shared" / "rag-files" / "docling-chunks"  # gitignored; shared/docling-scratch is root-owned

FORMULA_PLACEHOLDER = "<!-- formula-not-decoded -->"  # Docling leaves this for a formula
POLL_SECONDS = 10
GIVE_UP_SECONDS = 2 * 60 * 60


def docling_form(book: Book) -> dict:
    """The multipart fields for the hybrid chunk endpoint."""
    return {
        "convert_from_formats": "pdf",
        "convert_do_ocr": str(book.ocr).lower(),
        "convert_pdf_backend": "dlparse_v4",
        "convert_table_mode": "accurate",
        "convert_do_table_structure": "true",
        "convert_include_images": "false",
        "convert_image_export_mode": "placeholder",
        "convert_abort_on_error": "false",
        "chunking_tokenizer": "BAAI/bge-m3",  # the default is MiniLM, so this must be set
        "chunking_max_tokens": str(MAX_TOKENS),
        "chunking_merge_peers": "true",
        "chunking_include_raw_text": "true",
        "chunking_use_markdown_tables": "true",  # makes tables recognisable so they can be cut
    }


def check_result(result: dict) -> list[dict]:
    """The chunks, or RuntimeError: a failed conversion still reports task success, with none."""
    status = result["documents"][0]["status"]
    if status != "success":
        raise RuntimeError(f"Docling conversion status is {status!r}, not 'success'")
    chunks = result.get("chunks") or []
    if not chunks:
        raise RuntimeError("Docling returned no chunks")
    return chunks


def run_docling(book: Book) -> dict:
    """Send the PDF to Docling Serve, wait for the chunks, save and return the result."""
    pdf = ROOT / book.file_path
    with pdf.open("rb") as f:
        response = requests.post(f"{DOCLING_URL}/v1/chunk/hybrid/file/async",
                                 files={"files": (pdf.name, f, "application/pdf")},
                                 data=docling_form(book), timeout=300)
    response.raise_for_status()
    task_id = response.json()["task_id"]
    started = time.monotonic()
    while True:
        poll = requests.get(f"{DOCLING_URL}/v1/status/poll/{task_id}", timeout=60)
        poll.raise_for_status()
        status = poll.json()["task_status"]
        if status not in ("pending", "started"):
            break
        if time.monotonic() - started > GIVE_UP_SECONDS:
            raise RuntimeError(f"Docling task {task_id} still {status} after 2 h")
        time.sleep(POLL_SECONDS)
    result_response = requests.get(f"{DOCLING_URL}/v1/result/{task_id}", timeout=600)
    result_response.raise_for_status()
    result = result_response.json()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    (SCRATCH / f"{book.slug}.chunks.json").write_text(json.dumps(result), encoding="utf-8")
    return result


def strip_tables(text: str) -> str:
    """Drop markdown table rows (lines starting with `|`) and Docling's formula placeholders,
    then collapse runs of blank lines."""
    kept = [line for line in text.splitlines()
            if not line.strip().startswith("|") and line.strip() != FORMULA_PLACEHOLDER]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept))


def chunk_rows(chunks: list[dict], book: Book) -> tuple[list[dict], dict]:
    """Prose rows {section_path, page, text} from Docling chunks, plus a stats dict."""
    stats = {"chunks_in": len(chunks), "kept": 0, "dropped_skip_page": 0,
             "dropped_short": 0, "table_pages": set()}
    rows = []
    for c in sorted(chunks, key=lambda c: c["chunk_index"]):
        raw = c["raw_text"]
        text = strip_tables(raw).strip()
        page = min(c["page_numbers"])
        if text != raw.strip():
            stats["table_pages"].update(c["page_numbers"])
        if any(lo <= page <= hi for lo, hi in book.skip_pages):
            stats["dropped_skip_page"] += 1
        elif len(text.split()) < MIN_WORDS:
            stats["dropped_short"] += 1
        else:
            rows.append({"section_path": " > ".join(c.get("headings") or []),
                         "page": page, "text": text})
    stats["kept"] = len(rows)
    return rows, stats


def embed_text(row: dict) -> str:
    """What is embedded: heading path plus prose (kb.chunk.text keeps the prose only)."""
    return row["section_path"] + "\n\n" + row["text"]


def parse_embedding(body: dict) -> tuple[list[float], int]:
    """The single vector and prompt_eval_count from an Ollama /api/embed answer."""
    vectors = body["embeddings"]
    if len(vectors) != 1 or len(vectors[0]) != EMBED_DIMS:
        raise ValueError(f"expected one vector of {EMBED_DIMS} floats, got "
                         f"{[len(v) for v in vectors]}")
    return vectors[0], body["prompt_eval_count"]


def embed(text: str) -> tuple[list[float], int]:
    """Embed one text with bge-m3; an over-long text fails instead of being cut."""
    response = requests.post(f"{OLLAMA_URL}/api/embed", timeout=300,
                             json={"model": EMBED_MODEL, "input": text,
                                   "truncate": False, "keep_alive": -1})
    response.raise_for_status()
    return parse_embedding(response.json())


def upsert_source(conn, book: Book) -> int:
    """Insert or update the book's ref.source row on its slug; the id stays the same."""
    return conn.execute(
        """
        insert into ref.source (slug, title, edition, publisher, licence, file_path, notes)
        values (%s, %s, %s, %s, %s, %s, %s)
        on conflict (slug) do update set
            title = excluded.title, edition = excluded.edition,
            publisher = excluded.publisher, licence = excluded.licence,
            file_path = excluded.file_path,
            notes = coalesce(excluded.notes, ref.source.notes)
        returning id
        """,
        (book.slug, book.title, book.edition, book.publisher, book.licence,
         book.file_path, book.notes),
    ).fetchone()[0]


def replace_chunks(conn, source_id: int, rows: list[dict]) -> int:
    """Delete the book's chunks and insert `rows` (section_path, page, text, tokens, embedding).

    No commit here: the caller's `with connect() as conn:` commits it all at once, so a
    failed run leaves the old chunks.
    """
    conn.execute("delete from kb.chunk where source_id = %s", (source_id,))
    for row in rows:
        vector = "[" + ",".join(str(x) for x in row["embedding"]) + "]"
        conn.execute(
            """
            insert into kb.chunk (source_id, section_path, page, text, tokens, embedding)
            values (%s, %s, %s, %s, %s, %s::extensions.vector)
            """,
            (source_id, row["section_path"], row["page"], row["text"], row["tokens"], vector),
        )
    return len(rows)


def main() -> None:
    import argparse
    import statistics

    from loaders.db import connect

    parser = argparse.ArgumentParser(
        description="Load one book into kb.chunk (see docs/BOOKS.md).")
    parser.add_argument("slug", choices=sorted(BOOKS))
    parser.add_argument("--reuse-docling", action="store_true",
                        help="read shared/rag-files/docling-chunks/<slug>.chunks.json instead of Docling")
    args = parser.parse_args()
    book = BOOKS[args.slug]

    if args.reuse_docling:
        result = json.loads((SCRATCH / f"{book.slug}.chunks.json").read_text(encoding="utf-8"))
    else:
        result = run_docling(book)
    rows, stats = chunk_rows(check_result(result), book)

    for i, row in enumerate(rows, 1):
        row["embedding"], row["tokens"] = embed(embed_text(row))
        if i % 100 == 0:
            print(f"embedded {i}/{len(rows)}", flush=True)

    with connect() as conn:
        source_id = upsert_source(conn, book)
        replace_chunks(conn, source_id, rows)

    tokens = [row["tokens"] for row in rows]
    print(f"chunks in {stats['chunks_in']}, kept {stats['kept']}, "
          f"dropped on skip pages {stats['dropped_skip_page']}, "
          f"dropped as too short {stats['dropped_short']}")
    print(f"tokens min {min(tokens)}, median {statistics.median(tokens)}, max {max(tokens)}")
    print(f"PDF pages where tables were cut: {sorted(stats['table_pages'])}")


if __name__ == "__main__":
    main()
