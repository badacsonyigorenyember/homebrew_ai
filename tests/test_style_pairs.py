"""app.style_pair(): the decided BA to BJCP pairs (db/021_style_pairs.sql).

The list must equal the paired rows of style-pairs.md, the file Claude decided them in.
"""

import re
from pathlib import Path

import pytest

from loaders.db import connect

ROOT = Path(__file__).resolve().parent.parent
NAME = "m2-best-fit-style"
FILE = next(
    (p / "style-pairs.md" for p in (ROOT / "docs" / "work" / NAME, ROOT / "docs" / "finished" / NAME)
     if (p / "style-pairs.md").exists()),
    None,
)


def file_rows():
    """(ba_code, bjcp_code or None) for every table row of style-pairs.md."""
    rows = []
    for line in FILE.read_text().splitlines():
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        pair = re.match(r"(\d+[A-Z])\b", cells[2])
        rows.append((cells[0].strip("`"), pair.group(1) if pair else None))
    return rows


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def codes(conn, slug):
    rows = conn.execute(
        "select b.code from ref.beer_style b join ref.source s on s.id = b.source_id where s.slug = %s",
        (slug,),
    ).fetchall()
    return {code for (code,) in rows}


@pytest.mark.stack
def test_pair_codes_exist(conn):
    pairs = conn.execute("select ba_code, bjcp_code from app.style_pair()").fetchall()
    assert {a for a, _ in pairs} - codes(conn, "ba-2026") == set()
    assert {b for _, b in pairs} - codes(conn, "bjcp-2021") == set()


@pytest.mark.stack
def test_each_ba_style_paired_once(conn):
    ba = [a for (a,) in conn.execute("select ba_code from app.style_pair()").fetchall()]
    assert len(ba) == len(set(ba)), "a BA code is paired twice"


@pytest.mark.stack
def test_pair_list_matches_file(conn):
    assert FILE is not None, "style-pairs.md not found in docs/work or docs/finished"
    rows = file_rows()
    assert {a for a, _ in rows} == codes(conn, "ba-2026"), "style-pairs.md must list all BA codes"
    decided = {(a, b) for a, b in rows if b}
    in_sql = set(conn.execute("select ba_code, bjcp_code from app.style_pair()").fetchall())
    assert in_sql == decided
