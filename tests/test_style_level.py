"""app.style_level step by step (Task 8 of s3-style-fit). Temporary rows are rolled back."""

import pytest
from psycopg.types.json import Jsonb

from loaders.db import connect


@pytest.fixture()
def conn():
    connection = connect()
    yield connection
    connection.rollback()
    connection.close()


def ingredient(conn, kind, name, producer=""):
    row = conn.execute(
        "select id from ref.ingredient where kind = %s and name = %s and producer = %s",
        (kind, name, producer),
    ).fetchone()
    assert row, name
    return row[0]


def level(conn, style, kind, name, usage, dose=None, producer=""):
    ing = ingredient(conn, kind, name, producer)
    return conn.execute(
        "select app.style_level(%s, %s, %s, %s)", (style, ing, usage, Jsonb(dose or {}))
    ).fetchone()[0]


@pytest.mark.stack
def test_unrated_style(conn):
    result = level(conn, "21B", "hop", "Citra", "dry_hop", {"g_per_l": 8})
    assert result["level"] is None
    assert result["because"].startswith("not rated")


@pytest.mark.stack
def test_override_wins(conn):
    before = level(conn, "15B", "hop", "Citra", "whirlpool", {"g_per_l": 2})
    assert before["level"] == "out_of_style"
    conn.execute(
        """insert into ref.style_rule (style_id, ingredient_id, usage, level, quote)
           select b.id, i.id, 'whirlpool', 'typical', 'test rule'
           from ref.beer_style b, ref.ingredient i
           where b.code = '15B' and i.kind = 'hop' and i.name = 'Citra'"""
    )
    after = level(conn, "15B", "hop", "Citra", "whirlpool", {"g_per_l": 2})
    assert after["level"] == "typical"
    assert "test rule" in after["because"]


@pytest.mark.stack
def test_adjunct_named_vs_not(conn):
    named = level(conn, "21C", "fermentable", "Flaked Oats", "mash", {"pct": 20})
    assert named["level"] == "typical"
    assert "characteristic ingredients" in named["because"]
    unnamed = level(conn, "18B", "fermentable", "Flaked Rice", "mash", {"pct": 15})
    assert unnamed["level"] == "out_of_style"
    assert "not a usual ingredient" in unnamed["because"]


@pytest.mark.stack
def test_silent_transforming_is_changes_style(conn):
    result = level(conn, "18B", "yeast", "Philly Sour", "ferment", {"ferm_c": 22}, "Lallemand")
    assert result["level"] == "changes_style"
    assert "transforming" in result["because"]


@pytest.mark.stack
def test_silent_specialty(conn):
    result = level(conn, "6A", "fermentable", "Beech Smoked Barley Malt", "mash", {"pct": 20}, "Weyermann")
    assert result["level"] == "out_of_style"
    assert "specialty smoke on" in result["because"]


@pytest.mark.stack
def test_too_much(conn):
    result = level(conn, "15B", "fermentable", "Roasted Barley", "mash", {"pct": 15}, "Weyermann")
    assert result["level"] == "out_of_style"
    assert "too much: roast index" in result["because"]
    # the colour check: SRM above the style's upper bound
    dark = level(conn, "18A", "fermentable", "Caraaroma", "mash", {"pct": 5, "srm": 9}, "Weyermann")
    assert dark["level"] == "out_of_style"
    assert "too much colour" in dark["because"]


@pytest.mark.stack
def test_yeast_too_little(conn):
    us05 = level(conn, "10A", "yeast", "SafAle US-05", "ferment", {"ferm_c": 19}, "Fermentis")
    assert us05["level"] == "out_of_style"
    assert "too little" in us05["because"]
    # one level short is tolerated
    abbaye = level(conn, "26B", "yeast", "Abbaye", "ferment", {"ferm_c": 21}, "Lallemand")
    assert abbaye["level"] != "out_of_style"
    assert "too little" not in abbaye["because"]
    # a yeast that needs review: the min check is skipped and said so
    conn.execute(
        """insert into ref.ingredient_review (ingredient_id, reason)
           select id, 'test' from ref.ingredient where kind = 'yeast' and name = 'SafAle US-05'"""
    )
    skipped = level(conn, "10A", "yeast", "SafAle US-05", "ferment", {"ferm_c": 19}, "Fermentis")
    assert skipped["level"] != "out_of_style"
    assert "min check skipped" in skipped["because"]


@pytest.mark.stack
def test_missing_dose_skips_and_says_so(conn):
    result = level(conn, "18B", "hop", "Simcoe", "whirlpool")
    assert result["level"] == "typical"
    assert "dose not given, dose check skipped" in result["because"]


@pytest.mark.stack
def test_wrong_character(conn):
    result = level(conn, "5D", "hop", "Citra", "whirlpool", {"g_per_l": 1.5})
    assert result["level"] == "out_of_style"
    assert "wrong character" in result["because"]


@pytest.mark.stack
def test_fermentable_style_bump_only_for_fermentables(conn):
    bumped = level(conn, "6A", "fermentable", "Munich Malt Type 2", "mash", {"pct": 50}, "Weyermann")
    assert bumped["level"] == "typical"
    assert "listed for" in bumped["because"]
    plain = level(conn, "26B", "fermentable", "Munich Malt Type 2", "mash", {"pct": 17}, "Weyermann")
    assert plain["level"] == "allowed"
    # a yeast and a hop that are otherwise "allowed" stay allowed (the table only holds malts)
    assert level(conn, "5D", "yeast", "SafLager W-34/70", "ferment", {"ferm_c": 12}, "Fermentis")["level"] == "allowed"
    assert level(conn, "21A", "hop", "Magnum", "boil", {"minutes": 60, "ibu": 55})["level"] == "allowed"
    # the bump never lifts out_of_style
    smoked = level(conn, "10A", "fermentable", "Oak Smoked Wheat Malt", "mash", {"pct": 20}, "Weyermann")
    assert smoked["level"] == "out_of_style"


@pytest.mark.stack
def test_boil_needs_minutes(conn):
    ing = ingredient(conn, "hop", "Magnum")
    with pytest.raises(Exception, match="needs dose.minutes"):
        conn.execute("select app.style_level('21A', %s, 'boil', '{}')", (ing,))


@pytest.mark.stack
def test_unknown_style_raises(conn):
    ing = ingredient(conn, "hop", "Magnum")
    with pytest.raises(Exception, match="unknown style code"):
        conn.execute("select app.style_level('nope', %s, 'dry_hop', '{}')", (ing,))
    conn.rollback()
    with pytest.raises(Exception, match="unknown ingredient id"):
        conn.execute("select app.style_level('21A', -1, 'dry_hop', '{}')")
    conn.rollback()
    with pytest.raises(Exception, match="not valid for a hop"):
        conn.execute("select app.style_level('21A', %s, 'mash', '{}')", (ing,))


@pytest.mark.stack
def test_null_srm_names_the_colourless_fermentable(conn):
    # the recipe SRM is null when a fermentable has no colour: the because says that
    result = level(conn, "17C", "fermentable", "Roasted Barley", "mash", {"pct": 1, "ibu": 26}, "Viking Malt")
    assert "a fermentable has no colour" in result["because"]
    assert "dose not given" not in result["because"].split("colour:")[1]


@pytest.mark.stack
def test_needs_review_only_for_flagged_yeasts(conn):
    clean = level(conn, "1C", "yeast", "SafAle US-05", "ferment", {"ferm_c": 19}, "Fermentis")
    assert "needs review" not in clean["because"]
    conn.execute(
        """insert into ref.ingredient_review (ingredient_id, reason)
           select id, 'test' from ref.ingredient where kind = 'yeast' and name = 'SafAle US-05'"""
    )
    flagged = level(conn, "1C", "yeast", "SafAle US-05", "ferment", {"ferm_c": 19}, "Fermentis")
    assert flagged["because"].count("no character tags (needs review).") <= 1


@pytest.mark.stack
def test_too_much_text_is_rounded(conn):
    result = level(conn, "5D", "hop", "Magnum", "boil", {"minutes": 60, "ibu": 48.638715818210258, "g_per_l": 1}, "")
    assert "too much bitterness: 49 IBU" in result["because"]
    result = level(conn, "17C", "fermentable", "Roasted Barley", "mash",
                   {"pct": 2, "srm": 26.6789, "roast_index": 0}, "Viking Malt")
    assert "too much colour: 26.7 SRM" in result["because"]
