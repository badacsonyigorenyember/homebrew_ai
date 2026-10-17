"""Step 4 (targets) in db/039_step4.sql, and the hint table it reads (db/037_step3.sql).

Acceptance A12 and R5, R6 of docs/work/m4-targets-blueprint/brief.md.
"""

import json
import tomllib
from pathlib import Path

import pytest

from loaders.db import connect

ROOT = Path(__file__).resolve().parent.parent
BRIEFS = {b["id"]: b for b in tomllib.loads((ROOT / "evals" / "recipe_briefs.toml").read_text())["brief"]}


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


def numbers(conn, code, stated=None, hints=None):
    row = conn.execute("select app.step4_numbers(%s, %s::jsonb, %s::jsonb)",
                       [code, json.dumps(stated or {}), json.dumps(hints or [])]).fetchone()
    return row[0]


def value(item):
    return None if item["value"] is None else float(item["value"])


def usable_style(conn, b):
    """The brief's style, or its first alternative when that style has no vitals (31B)."""
    for code in [b["style"], *b["alt_styles"]]:
        row = conn.execute("select og is not null, abv is not null from ref.beer_style where code = %s", [code]).fetchone()
        if row and row[0]:
            return code
    return b["style"]


def test_range_position(conn):
    def pos(r, f):
        return conn.execute("select app.range_position(%s::numrange, %s::numeric)", [r, f]).fetchone()[0]
    assert float(conn.execute("select app.range_position(ibu, 0.875) from ref.beer_style where code = '21A'").fetchone()[0]) == 66.25
    assert float(conn.execute("select app.range_position(ibu, 0.125) from ref.beer_style where code = '6A'").fetchone()[0]) == 18.75
    assert float(pos("[40,)", 0.875)) == 40
    assert pos(None, 0.5) is None


def test_og_for_abv_inverts_abv(conn):
    for abv in (3, 4, 6.5, 7, 10):
        for fg in (1.0045, 1.011, 1.018, 1.029):
            og = conn.execute("select app.og_for_abv(%s::numeric, %s::numeric)", [abv, fg]).fetchone()[0]
            got = conn.execute("select app.abv(%s::numeric, %s::numeric)", [og, fg]).fetchone()[0]
            assert abs(float(got) - abv) < 0.01, (abv, fg)
            fg_back = conn.execute("select app.fg_for_abv(%s::numeric, %s::numeric)", [og, abv]).fetchone()[0]
            got = conn.execute("select app.abv(%s::numeric, %s::numeric)", [og, fg_back]).fetchone()[0]
            assert abs(float(got) - abv) < 0.01, (abv, fg)


def test_midpoints_without_hints(conn):
    got = numbers(conn, "16A")
    assert [value(got[k]) for k in ("og", "fg", "ibu", "srm")] == [1.052, 1.018, 30, 35]
    assert all(got[k]["from"] == "midpoint" for k in ("og", "fg", "ibu", "srm"))


def test_hint_moves_ibu(conn):
    got = numbers(conn, "21A", hints=["bitter"])["ibu"]
    assert value(got) == 66.25 and got["from"] == "hint" and "bitter" in got["because"]
    assert value(numbers(conn, "6A", hints=["malty"])["ibu"]) == 18.75


def test_stated_wins(conn):
    got = numbers(conn, "5D", {"ibu": 50}, ["bitter"])["ibu"]
    assert value(got) == 50 and got["from"] == "stated"
    got = numbers(conn, "15A", {"srm": 20}, ["darker"])["srm"]
    assert value(got) == 20 and got["from"] == "stated"


def test_conflicting_hints_leave_default(conn):
    rows = conn.execute("select knob from app.hint_moves(%s::jsonb)", [json.dumps(["dry", "full", "chewy"])]).fetchall()
    assert not [r for r in rows if r[0] in ("mash_temp", "attenuation")]
    got = numbers(conn, "21A", hints=["bitter", "malty"])["ibu"]
    assert got["from"] == "midpoint" and value(got) == 55


def test_stated_abv_solves_og(conn):
    def abv_of(n):
        return float(conn.execute("select app.abv(%s::numeric, %s::numeric)", [n["og"]["value"], n["fg"]["value"]]).fetchone()[0])
    got = numbers(conn, "21A", {"abv": 6.5, "batch_l": 20})
    assert value(got["fg"]) == 1.011 and abs(abv_of(got) - 6.5) < 0.1
    assert got["og"]["from"] == "derived" and "6.5" in got["og"]["because"]
    got = numbers(conn, "23A", {"abv": 3}, ["session"])
    assert got["og"]["from"] == "derived" and abs(abv_of(got) - 3) < 0.1
    session = numbers(conn, "23A", hints=["session"])["og"]
    assert session["from"] == "hint" and value(got["og"]) != value(session)
    assert abs(abv_of(numbers(conn, "8B", {"abv": 7})) - 7) < 0.1
    got = numbers(conn, "session-india-pale-ale", {"abv": 4})
    assert abs(abv_of(got) - 4) < 0.1


def test_abv_out_of_range_moves_og(conn):
    got = numbers(conn, "15A")
    assert value(got["abv"]) >= 3.8 and 1.041 < value(got["og"]) < 1.045 and got["og"]["from"] == "derived"
    got = numbers(conn, "17C", hints=["stronger"])
    assert value(got["og"]) > 1.100 and value(got["abv"]) <= 10.0
    assert got["og"]["from"] == "derived" and "1.1225" in got["og"]["because"]


def test_derived_abv_inside_range(conn):
    for bid, b in BRIEFS.items():
        code = usable_style(conn, b)
        got = numbers(conn, code, b["stated"], b["hints"])
        if got["og"]["value"] is None:
            continue
        calc = float(conn.execute("select app.abv(%s::numeric, %s::numeric)", [got["og"]["value"], got["fg"]["value"]]).fetchone()[0])
        assert abs(value(got["abv"]) - calc) <= 0.1, bid
        if "abv" not in b["stated"]:
            inside = conn.execute("select abv @> %s::numeric from ref.beer_style where code = %s", [got["abv"]["value"], code]).fetchone()[0]
            assert inside, (bid, got["abv"])


def test_style_without_ranges(conn):
    got = numbers(conn, "31B")
    assert all(got[k]["value"] is None and got[k]["from"] == "none" for k in ("og", "fg", "abv", "ibu", "srm"))
    got = numbers(conn, "31B", {"ibu": 30})
    assert value(got["ibu"]) == 30 and got["ibu"]["from"] == "stated"
