"""Step 4 (targets) in db/039_step4.sql, and the hint table it reads (db/037_step3.sql).

Acceptance A12 and R5, R6 of docs/work/m4-targets-blueprint/brief.md.
"""

import pytest

from loaders.db import connect


pytestmark = pytest.mark.stack


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def hint_rows(conn):
    return conn.execute("select hint, side, knob, direction, position, mash_c, intent, source from app.hint_knob()").fetchall()


def test_hint_rows_sourced_or_marked(conn):
    """A12: every row cites a ref.source slug and a place, or is marked unsourced."""
    slugs = {r[0] for r in conn.execute("select slug from ref.source").fetchall()}
    for hint, _side, knob, _dir, _pos, _mash, _intent, source in hint_rows(conn):
        if source == "unsourced":
            continue
        slug, sep, place = source.partition(", ")
        assert slug in slugs and sep and place, f"{hint}/{knob}: bad source {source!r}"


def test_hint_positions(conn):
    """R5: up knobs 0.875, down knobs 0.125 (og, ibu, srm); mash 64.5 down, 68.5 up; nothing else."""
    for hint, _side, knob, direction, position, mash_c, _intent, _source in hint_rows(conn):
        if knob in ("og", "ibu", "srm"):
            assert position == (0.875 if direction == 1 else 0.125), f"{hint}/{knob}"
        else:
            assert position is None, f"{hint}/{knob} has a position"
        if knob == "mash_temp":
            assert mash_c == (68.5 if direction == 1 else 64.5), f"{hint}/{knob}"
        else:
            assert mash_c is None, f"{hint}/{knob} has a mash_c"


def test_malty_lowers_ibu(conn):
    rows = [r for r in hint_rows(conn) if r[0] == "malty" and r[2] == "ibu"]
    assert len(rows) == 1 and rows[0][3] == -1
