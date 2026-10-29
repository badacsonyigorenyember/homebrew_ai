"""Water rows and CO2 volumes in ref (db/049_process_ref.sql); docs/work/m7-process Task 2.

The expected lists are copied from doc-calc.md §4 and §14; the family ranges are How to Brew p. 159.
"""

from decimal import Decimal as D

import pytest
from psycopg.types.range import Range

from loaders.db import connect
from tests.test_step4 import BRIEFS, step4

pytestmark = pytest.mark.stack

FAMILIES = {
    "british-ales": (D("1.5"), D("2.0")),
    "porter-stout": (D("1.7"), D("2.3")),
    "belgian-ales": (D("1.9"), D("2.4")),
    "american-ales": (D("2.2"), D("2.7")),
    "european-lagers": (D("2.2"), D("2.7")),
    "belgian-lambic": (D("2.4"), D("2.8")),
    "american-wheat": (D("2.7"), D("3.3")),
    "german-wheat": (D("3.3"), D("4.5")),
}

WATER_BASIS = {
    "listed": {"21A", "18B", "16B", "16A", "20B", "20C", "19C", "10A", "1C", "5B", "11B", "14B", "26B", "25A",
               "17C", "17D", "22C", "1B", "3B", "5D", "6A", "8B"},
    "inferred": {"mexican-style-amber-lager"},
    "judgement": {"21C", "session-india-pale-ale", "13C", "18A", "25B", "15B", "15A"},
    "web": {"23A"},
}
CO2_BASIS = {
    "listed": {"16B", "16A", "20B", "15B", "20C", "13C", "10A"},
    "inferred": {"21A", "21C", "session-india-pale-ale", "18B", "18A", "19C", "1C", "22C", "11B", "14B", "17C",
                 "17D", "26B", "25A", "5D", "3B", "6A", "8B"},
    "judgement": {"15A", "25B", "1B", "mexican-style-amber-lager", "5B", "23A"},
}


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def row(conn, code):
    return conn.execute("select ca, alkalinity, so4, cl, ra from ref.water_profile where code = %s", [code]).fetchone()


def test_water_rows_are_the_books(conn):
    assert conn.execute("select count(*) from ref.water_profile where table_no in ('18', '19')").fetchone()[0] == 16
    ca, alk, so4, cl, ra = row(conn, "ale-medium-pale-assertive")
    assert (so4, ra) == (Range(100, 400, "[]"), Range(-30, 30, "[]"))
    ca = row(conn, "lager-light-pale")[0]
    assert ca.lower == 50 and ca.upper is None
    assert row(conn, "ale-strong-brown-black")[1] == Range(120, 200, "[]")


def brief_styles(conn):
    """Style codes per brief: step 4's style and every listed alternative that has ranges."""
    out = {}
    for bid, b in BRIEFS.items():
        codes = {step4(conn, b)["style"]["code"]}
        for alt in b["alt_styles"]:
            if conn.execute("select og is not null from ref.beer_style where code = %s", [alt]).fetchone()[0]:
                codes.add(alt)
        out[bid] = codes
    return out


def test_every_brief_style_has_a_row_and_co2(conn):
    """A9. specialty-honey-beer has ranges but follows its base style (doc-calc §4b): no row, no volumes."""
    for bid, codes in brief_styles(conn).items():
        for code in codes - {"specialty-honey-beer"}:
            got = conn.execute("select water_profile, water_basis, co2_vol, co2_basis from ref.beer_style where code = %s",
                               [code]).fetchone()
            assert all(v is not None for v in got), (bid, code, got)
    assert conn.execute("select water_profile from ref.beer_style where code = '23A'").fetchone()[0] == "web-berliner-weisse"


def test_basis_labels(conn):
    water = {}
    co2 = {}
    for code, wb, cb in conn.execute("select code, water_basis, co2_basis from ref.beer_style"):
        if wb:
            water.setdefault(wb, set()).add(code)
        if cb:
            co2.setdefault(cb, set()).add(code)
    assert water == WATER_BASIS
    assert co2 == CO2_BASIS
    # a mapped style has all three water columns or none, and the same for the CO2 ones
    bad = conn.execute("""select code from ref.beer_style
        where (water_profile is null) <> (water_basis is null)
           or (co2_vol is null) <> (co2_basis is null) or (co2_vol is null) <> (co2_family is null)""").fetchall()
    assert bad == []


def test_co2_inside_its_family(conn):
    seen = 0
    for code, family, vol in conn.execute("select code, co2_family, co2_vol from ref.beer_style where co2_vol is not null"):
        seen += 1
        assert (vol.lower, vol.upper) == FAMILIES[family], code
    assert seen == 31
    assert conn.execute("select count(*) from ref.beer_style where code = 'specialty-honey-beer' and co2_vol is not null").fetchone()[0] == 0


def test_rows_have_a_source(conn):
    rows = conn.execute("""select p.code, s.slug, p.page from ref.water_profile p
                           left join ref.source s on s.id = p.source_id""").fetchall()
    assert len(rows) == 17
    for code, slug, page in rows:
        assert slug and page, code
        assert slug == ("web-berliner-weisse-water" if code == "web-berliner-weisse" else "palmer-kaminski-water")
