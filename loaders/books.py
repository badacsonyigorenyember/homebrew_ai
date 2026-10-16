"""Books and articles into the knowledge base (kb.chunk): Docling chunks, prose only,
embedded with bge-m3.

Run:  .venv/bin/python -m loaders.books <slug>
To add a book: add one `Book` entry to BOOKS below, then run the command with its slug.
To add an article (a PDF or a saved Markdown page): add one entry to ARTICLES, with its `url`
and the `drop_sections` to leave out, then run the same command.
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
    url: str | None = None  # where an article can be read; books have none
    drop_sections: tuple[str, ...] = ()  # heading texts whose chunks are left out (any level)


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
    "mallett-malt": Book(
        slug="mallett-malt",
        title="Malt: A Practical Guide from Field to Brewhouse",
        edition="2014",  # the copyright page gives only the year
        publisher="Brewers Publications",
        licence="© Brewers Association, all rights reserved; personal copy, local use only",
        file_path="shared/rag-files/books/mallett_malt.pdf",
        # cover to foreword (contents, acknowledgments, foreword); bibliography and index
        skip_pages=((1, 16), (263, 335)),
        notes="Prose in kb.chunk; malt data comes from the maltster catalogues, see docs/BOOKS.md",
    ),
    "bjcp-exam-study-guide-2017": Book(
        slug="bjcp-exam-study-guide-2017",
        title="BJCP Beer Exam Study Guide",
        edition="Last revised December 2017",
        publisher="Beer Judge Certification Program",
        licence="© 1998-2017 the authors and the BJCP; free to download; local use",
        file_path="shared/rag-files/books/bjcp_exam_study_guide_2017.pdf",
        # sections I-III (introduction, judging and exam, style guidelines); only section IV is kept
        skip_pages=((1, 45),),
        notes="Section IV (ingredients and brewing process) only; prose in kb.chunk, see docs/BOOKS.md",
    ),
}

ARTICLES: dict[str, Book] = {
    "troester-mash-parameters": Book(
        slug="troester-mash-parameters",
        title="Effects of mash parameters on the limit of attenuation and conversion efficiency in single infusion mashing",
        edition="2008",
        publisher="braukaiser.com",
        licence="CC BY-NC 3.0, Kai Troester, braukaiser.com; local use only",
        file_path="shared/rag-files/articles/braukaiser_mash_parameters_2009.pdf",
        url="https://braukaiser.com/wiki/index.php/Effects_of_mash_parameters_on_fermentability_and_efficiency_in_single_infusion_mashing",
        skip_pages=((22, 23),),  # appendix tables and the "Sources" list
        notes="Article prose in kb.chunk (s7-kb-articles)",
    ),
    "troester-mash-time-fermentability": Book(
        slug="troester-mash-time-fermentability",
        title="Mash Time Dependency of Wort Fermentability",
        edition="saved 2026-10-16",
        publisher="braukaiser.com",
        licence="© Kai Troester, braukaiser.com; licence not stated; local use only",
        file_path="shared/rag-files/articles/braukaiser_mash_time_fermentability.md",
        url="http://braukaiser.com/wiki/index.php/Mash_Time_Dependency_of_Wort_Fermentability",
        notes="Article prose in kb.chunk (s7-kb-articles)",
    ),
    "terrill-observations-on-attenuations": Book(
        slug="terrill-observations-on-attenuations",
        title="Observations on Attenuations",
        edition="2017-04-21",
        publisher="seanterrill.com",
        licence="© Sean Terrill, seanterrill.com; licence not stated; local use only",
        file_path="shared/rag-files/articles/terrill_observations_on_attenuations.md",
        url="http://seanterrill.com/2017/04/21/observations-on-attenuations/",
        notes="Article prose in kb.chunk (s7-kb-articles)",
    ),
    "janish-dry-hop-best-practices-tq": Book(
        slug="janish-dry-hop-best-practices-tq",
        title="Dry Hop Best Practices: Using Science as a Guide for Process and Recipe Development",
        edition="vol. 58, no. 1, 2021",
        publisher="MBAA Technical Quarterly",
        licence="© MBAA; posted by the author with MBAA's permission; local use only",
        file_path="shared/rag-files/articles/janish_dry_hop_best_practices_tq_2021.pdf",
        url="https://doi.org/10.1094/TQ-58-1-0402-01",
        skip_pages=((1, 1),),  # MBAA cover
        drop_sections=("References",),
        notes="Article prose in kb.chunk (s7-kb-articles)",
    ),
    "janish-short-cool-dry-hopping": Book(
        slug="janish-short-cool-dry-hopping",
        title="A Case for Short and Cool Dry Hopping",
        edition="saved 2026-10-16",
        publisher="scottjanish.com",
        licence="© Scott Janish, scottjanish.com; licence not stated; local use only",
        file_path="shared/rag-files/articles/janish_short_cool_dry_hopping.md",
        url="https://scottjanish.com/a-case-for-short-and-cool-dry-hopping/",
        drop_sections=("Footnotes",),
        notes="Article prose in kb.chunk (s7-kb-articles)",
    ),
    "janish-survivables-hot-side": Book(
        slug="janish-survivables-hot-side",
        title="Survivables: Unpacking Hot-Side Hop Flavor",
        edition="saved 2026-10-16",
        publisher="scottjanish.com",
        licence="© Scott Janish, scottjanish.com; licence not stated; local use only",
        file_path="shared/rag-files/articles/janish_survivables_hot_side.md",
        url="https://scottjanish.com/survivables-unpacking-hot-side-hop-flavor/",
        drop_sections=("Footnotes",),
        notes="Article prose in kb.chunk (s7-kb-articles)",
    ),
    "janish-ph-hoppy-beers": Book(
        slug="janish-ph-hoppy-beers",
        title="A Look at pH in Hoppy Beers",
        edition="saved 2026-10-16",
        publisher="scottjanish.com",
        licence="© Scott Janish, scottjanish.com; licence not stated; local use only",
        file_path="shared/rag-files/articles/janish_ph_hoppy_beers.md",
        url="https://scottjanish.com/a-look-at-ph-in-hoppy-beers/",
        drop_sections=("Footnotes",),
        notes="Article prose in kb.chunk (s7-kb-articles)",
    ),
    "janish-coffee-beers": Book(
        slug="janish-coffee-beers",
        title="Guide to Coffee Beers",
        edition="saved 2026-10-16",
        publisher="scottjanish.com",
        licence="© Scott Janish, scottjanish.com; licence not stated; local use only",
        file_path="shared/rag-files/articles/janish_coffee_beers.md",
        url="https://scottjanish.com/guide-to-coffee-beers/",
        notes="Article prose in kb.chunk (s7-kb-articles)",
    ),
    "mtf-berliner-weissbier": Book(
        slug="mtf-berliner-weissbier",
        title="Berliner Weissbier",
        edition="saved 2026-10-16",
        publisher="Milk The Funk Wiki",
        licence="Milk The Funk Wiki; licence not stated on the page; local use only",
        file_path="shared/rag-files/articles/mtf_berliner_weissbier.md",
        url="https://www.milkthefunk.com/wiki/Berliner_Weissbier",
        drop_sections=("External History Resources", "Video Presentations", "See Also", "References"),
        notes="Article prose in kb.chunk (s7-kb-articles)",
    ),
    "mtf-lactobacillus-fermentation": Book(
        slug="mtf-lactobacillus-fermentation",
        title="Lactobacillus Fermentation",
        edition="saved 2026-10-16",
        publisher="Milk The Funk Wiki",
        licence="Milk The Funk Wiki; licence not stated on the page; local use only",
        file_path="shared/rag-files/articles/mtf_lactobacillus_fermentation.md",
        url="https://www.milkthefunk.com/wiki/Lactobacillus_Fermentation",
        drop_sections=("See Also", "References"),
        notes="Article prose in kb.chunk (s7-kb-articles)",
    ),
    "brunwater-water-knowledge": Book(
        slug="brunwater-water-knowledge",
        title="Water Knowledge",
        edition="saved 2026-10-16",
        publisher="Bru'n Water",
        licence="© Martin Brungard, all rights reserved; local use only",
        file_path="shared/rag-files/water/brunwater_water_knowledge.md",
        url="https://www.brunwater.com/water-knowledge",
        drop_sections=("5. References",),
        notes="Article prose in kb.chunk (s7-kb-articles)",
    ),
    "bjcp-2021-introductions": Book(
        slug="bjcp-2021-introductions",
        title="BJCP 2021 Beer Style Guidelines: introductions",
        edition="saved 2026-10-16",
        publisher="Beer Judge Certification Program",
        licence="© Beer Judge Certification Program; local use only",
        file_path="shared/rag-files/styles/bjcp_2021_introductions.md",
        url="https://styles.bjcp.org/bjcp-2021-beer/",
        notes="Article prose in kb.chunk (s7-kb-articles)",
    ),
}

SOURCES = BOOKS | ARTICLES  # every slug the command accepts

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
        "convert_from_formats": "md" if book.file_path.endswith(".md") else "pdf",
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


def clean_markdown(text: str) -> str:
    """A saved page without its header block (Source, credit, Saved lines) and `[n]` markers."""
    lines = text.splitlines()
    head = lines[1:10]
    saved = next((i for i, line in enumerate(head) if line.startswith("Saved ")), None)
    if saved is None or not any(line.startswith("Source:") for line in head[:saved]):
        raise ValueError("Markdown file has no Source: ... Saved header block after its title")
    body = "\n".join([lines[0]] + lines[saved + 2:])
    return re.sub(r" ?\[\d+\]", "", body) + "\n"


def run_docling(book: Book) -> dict:
    """Send the file to Docling Serve, wait for the chunks, save and return the result."""
    path = ROOT / book.file_path
    if path.suffix == ".md":
        upload = (path.name, clean_markdown(path.read_text(encoding="utf-8")).encode("utf-8"),
                  "text/markdown")
    else:
        upload = (path.name, path.read_bytes(), "application/pdf")
    response = requests.post(f"{DOCLING_URL}/v1/chunk/hybrid/file/async",
                             files={"files": upload}, data=docling_form(book), timeout=300)
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
             "dropped_short": 0, "dropped_section": 0, "table_chunks": 0,
             "table_pages": set()}
    is_markdown = book.file_path.endswith(".md")
    drop = {name.lower() for name in book.drop_sections}
    rows = []
    for c in sorted(chunks, key=lambda c: c["chunk_index"]):
        raw = c["raw_text"]
        text = strip_tables(raw).strip()
        if c["page_numbers"]:
            page = min(c["page_numbers"])
        elif is_markdown:
            page = None
        else:
            raise ValueError(f"PDF chunk {c['chunk_index']} of {book.slug} has no page")
        if text != raw.strip():
            stats["table_chunks"] += 1
            stats["table_pages"].update(c["page_numbers"])
        headings = c.get("headings") or []
        if page is not None and any(lo <= page <= hi for lo, hi in book.skip_pages):
            stats["dropped_skip_page"] += 1
        elif any(h.strip().lower() in drop for h in headings):
            stats["dropped_section"] += 1
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
        insert into ref.source (slug, title, edition, publisher, licence, file_path, notes, url)
        values (%s, %s, %s, %s, %s, %s, %s, %s)
        on conflict (slug) do update set
            title = excluded.title, edition = excluded.edition,
            publisher = excluded.publisher, licence = excluded.licence,
            file_path = excluded.file_path,
            notes = coalesce(excluded.notes, ref.source.notes),
            url = coalesce(excluded.url, ref.source.url)
        returning id
        """,
        (book.slug, book.title, book.edition, book.publisher, book.licence,
         book.file_path, book.notes, book.url),
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
        description="Load one book or article into kb.chunk (see docs/BOOKS.md).")
    parser.add_argument("slug", choices=sorted(SOURCES))
    parser.add_argument("--reuse-docling", action="store_true",
                        help="read shared/rag-files/docling-chunks/<slug>.chunks.json instead of Docling")
    args = parser.parse_args()
    book = SOURCES[args.slug]

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
          f"dropped by section {stats['dropped_section']}, "
          f"dropped as too short {stats['dropped_short']}")
    print(f"tokens min {min(tokens)}, median {statistics.median(tokens)}, max {max(tokens)}")
    print(f"chunks where a table or formula was cut: {stats['table_chunks']}")
    print(f"PDF pages where tables were cut: {sorted(stats['table_pages'])}")


if __name__ == "__main__":
    main()
