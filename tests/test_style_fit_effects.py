"""Usage effects, cut points and intensity helpers (Task 7 of s3-style-fit)."""

import json
import re
from decimal import Decimal
from pathlib import Path

import pytest

from loaders.db import connect

ROOT = Path(__file__).resolve().parent.parent
SCALES = ("oil_ml_per_l", "roast_index")


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def cut_points(conn):
    value = conn.execute("select app.style_fit_cut_points()").fetchone()[0]
    return json.loads(value) if isinstance(value, str) else value


def entries(node, path=""):
    """Every dict that has a `basis`, with its path."""
    if isinstance(node, dict):
        if "basis" in node:
            yield path, node
        for key, child in node.items():
            yield from entries(child, f"{path}/{key}")
    elif isinstance(node, list):
        for index, child in enumerate(node):
            yield from entries(child, f"{path}[{index}]")


@pytest.mark.stack
def test_every_cut_point_has_a_basis(conn):
    found = list(entries(cut_points(conn)))
    assert len(found) == 7 + 7 + 4 + 3 + 1 + 1
    for path, entry in found:
        basis = entry["basis"]
        assert re.search(r"p\. ?\d+", basis) or basis.startswith(("set by the user", "decided, STYLE-FIT")), path


@pytest.mark.stack
def test_thresholds_ascend(conn):
    points = cut_points(conn)
    for scale in SCALES:
        values = [p["value"] for p in points[scale]]
        assert len(values) == 7
        assert values == sorted(set(values))
        assert [p["level"] for p in points[scale]] == list(range(1, 8))


@pytest.mark.stack
def test_intensity_level_bounds(conn):
    points = cut_points(conn)
    for scale in SCALES:
        values = [Decimal(str(p["value"])) for p in points[scale]]
        level = lambda v: conn.execute("select app.intensity_level(%s, %s)", (scale, v)).fetchone()[0]
        assert level(values[0] / 2) == 0
        for index, threshold in enumerate(values, start=1):
            assert level(threshold) == index
        assert level(values[-1] * 10) == 7
        assert level(None) is None
    with pytest.raises(Exception, match="unknown intensity scale"):
        conn.execute("select app.intensity_level('nonsense', 1)")
    conn.rollback()


@pytest.mark.stack
def test_dose_helpers(conn):
    oil = conn.execute("select app.oil_dose(2, '[1.5,3]'::numrange)").fetchone()[0]
    roast = conn.execute("select app.roast_index(5, '[1000,1300]'::numrange)").fetchone()[0]
    assert oil == Decimal("0.045")
    assert roast == 5750


@pytest.mark.stack
def test_usage_effects_match_style_fit(conn):
    def effects(usage, minutes=None):
        rows = conn.execute(
            """select dimension, carries_character from app.usage_effects()
               where kind = 'hop' and usage = %s
                 and (%s::int is null or (coalesce(min_minutes, 0) <= %s and %s <= coalesce(max_minutes, 100000)))""",
            (usage, minutes, minutes, minutes),
        ).fetchall()
        return sorted(rows)

    assert effects("dry_hop") == [("hop_aroma", True)]
    assert effects("boil", 60) == [("bitterness", False)]
    assert effects("boil", 15) == [("bitterness", False), ("hop_flavour", True)]
    assert effects("boil", 0) == [("hop_aroma", True), ("hop_flavour", True)]
    assert effects("whirlpool") == [("hop_aroma", True), ("hop_flavour", True)]
    dimensions = {r[0] for r in conn.execute("select name from ref.sensory_dimension")}
    assert {r[0] for r in conn.execute("select dimension from app.usage_effects()")} <= dimensions


def test_no_corpus_in_style_fit():
    files = sorted((ROOT / "db").glob("033_*.sql")) + sorted((ROOT / "db").glob("034_*.sql"))
    files += [ROOT / "loaders" / "tags.py", ROOT / "loaders" / "style_envelopes.py"]
    assert len(files) >= 3
    for path in files:
        assert "corpus." not in path.read_text(encoding="utf-8"), path
