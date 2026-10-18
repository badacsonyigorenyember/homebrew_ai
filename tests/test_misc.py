"""Misc extras (s9-misc-extras). Stack tests roll back; nothing is left in the database."""

import psycopg
import pytest

from loaders.db import connect

pytestmark = pytest.mark.stack

FLAVOUR = ("spice", "herb", "fruit", "wood", "coffee", "cacao", "vanilla", "smoke", "other")
PROCESS = ("fining", "nutrient", "enzyme", "acid", "other-process")


@pytest.fixture
def conn():
    connection = connect()
    yield connection
    connection.rollback()
    connection.close()


def new_ingredient(conn, name):
    source_id = conn.execute("select min(id) from ref.source").fetchone()[0]
    return conn.execute(
        "insert into ref.ingredient (kind, name, name_key, source_id, raw)"
        " values ('misc', %s, %s, %s, '{}') returning id",
        (name, name, source_id),
    ).fetchone()[0]


def insert_misc(conn, ingredient_id, purpose, category, usages):
    conn.execute(
        "insert into ref.misc (ingredient_id, purpose, category, usages) values (%s, %s, %s, %s)",
        (ingredient_id, purpose, category, usages),
    )


def test_misc_columns_and_checks(conn):
    columns = dict(conn.execute(
        "select column_name, data_type from information_schema.columns"
        " where table_schema = 'ref' and table_name = 'misc'"
    ).fetchall())
    assert columns == {
        "ingredient_id": "bigint", "category": "text", "purpose": "text", "usages": "ARRAY",
        "time_min": "integer", "dose_g_per_l": "numrange", "description": "text",
        "field_source": "jsonb",
    }
    owner = conn.execute("select tableowner from pg_tables where schemaname = 'ref' and tablename = 'misc'").fetchone()[0]
    assert owner == "postgres"

    # every category under its own purpose is accepted
    for number, (purpose, categories) in enumerate((("flavour", FLAVOUR), ("process", PROCESS))):
        for category in categories:
            insert_misc(conn, new_ingredient(conn, f"ok {number} {category}"), purpose, category, ["boil"])

    bad = [
        ("flavour category under process", "process", "spice", ["boil"]),
        ("process category under flavour", "flavour", "enzyme", ["boil"]),
        ("fining under flavour", "flavour", "fining", ["boil"]),
        ("unknown usage", "flavour", "spice", ["dry-hop"]),
        ("empty usages", "flavour", "spice", []),
        ("unknown purpose", "taste", "spice", ["boil"]),
    ]
    for label, purpose, category, usages in bad:
        conn.execute("savepoint s")
        with pytest.raises(psycopg.errors.CheckViolation):
            insert_misc(conn, new_ingredient(conn, label), purpose, category, usages)
        conn.execute("rollback to savepoint s")

    for label, column, value in (("negative time", "time_min", -1), ("negative dose", "dose_g_per_l", "[-1,2]")):
        conn.execute("savepoint s")
        with pytest.raises(psycopg.errors.CheckViolation):
            ingredient_id = new_ingredient(conn, label)
            conn.execute(
                f"insert into ref.misc (ingredient_id, purpose, category, usages, {column})"
                " values (%s, 'flavour', 'spice', array['boil'], %s)",
                (ingredient_id, value),
            )
        conn.execute("rollback to savepoint s")


# ---------------------------------------------------------------- resolver (Task 5)

from pathlib import Path  # noqa: E402

from tests.test_extra_ingredients import load_fixtures  # noqa: E402


def resolve(conn, word):
    return conn.execute(
        "select ingredient_id, kind, name, rule from app.resolve_ingredient(%s)", (word,)
    ).fetchall()


def test_misc_kind_words_find_misc_products(conn):
    load_fixtures(conn)
    assert [(r[1], r[2]) for r in resolve(conn, "Fixture Spice")] == [("misc", "Fixture Spice")]
    assert [(r[1], r[2]) for r in resolve(conn, "fixture spice seed")] == [("misc", "Fixture Spice")]
    assert [(r[1], r[2]) for r in resolve(conn, "herb fixture no dose")] == [("misc", "Fixture No Dose")]
    # a misc kind word restricts to misc, so another kind's name finds nothing
    assert resolve(conn, "herb Citra") == []


# ---------------------------------------------------------------- style level (Task 6)

from psycopg.types.json import Jsonb  # noqa: E402

MISC_DIMENSIONS = {
    "spice": "spice", "herb": "spice", "coffee": "spice", "cacao": "spice", "vanilla": "spice",
    "fruit": "fruit", "wood": "wood", "smoke": "smoke",
}


def ingredient_id(conn, name):
    return conn.execute("select id from ref.ingredient where name = %s", (name,)).fetchone()[0]


def level(conn, style, name, usage, dose=None):
    return conn.execute(
        "select app.style_level(%s, %s, %s, %s)",
        (style, ingredient_id(conn, name), usage, Jsonb(dose or {})),
    ).fetchone()[0]


def set_spice_envelope(conn, style, min_level, max_level):
    conn.execute(
        "update ref.style_sensory set min_level = %s, max_level = %s"
        " where dimension = 'spice' and style_id = (select id from ref.beer_style where code = %s)",
        (min_level, max_level, style),
    )


def test_misc_cut_points_and_effects(conn):
    points = conn.execute("select app.style_fit_cut_points() -> 'misc_dose'").fetchone()[0]
    assert (points["subtle_below"]["id"], points["subtle_below"]["ratio"]) == ("M1", 0.5)
    assert (points["aggressive_above"]["id"], points["aggressive_above"]["ratio"]) == ("M2", 2.0)
    levels = points["levels"]
    assert (levels["id"], levels["subtle"], levels["noticeable"], levels["aggressive"]) == ("M3", 2, 4, 6)
    for entry in (points["subtle_below"], points["aggressive_above"], levels):
        assert entry["basis"].startswith("set by the user, 2026-10-18")
    rows = conn.execute(
        "select applies_to, dimension, usage, carries_character from app.usage_effects() where kind = 'misc'"
    ).fetchall()
    assert {r[0]: r[1] for r in rows} == MISC_DIMENSIONS
    assert len(rows) == 8
    assert all(r[2] is None and r[3] is False for r in rows)


def test_flavour_misc_dose_words_in_25b(conn):
    load_fixtures(conn)
    set_spice_envelope(conn, "25B", 0, 7)
    # Fixture Spice: sourced dose 0.5-1.0 g/L, so subtle below 0.25, aggressive above 2.0
    for usage in ("whirlpool", "secondary"):
        result = level(conn, "25B", "Fixture Spice", usage, {"g_per_l": 0.8})
        assert result["level"] == "allowed"
        assert "noticeable" in result["because"] and "0.5" in result["because"] and "1.0" in result["because"]
    subtle = level(conn, "25B", "Fixture Spice", "secondary", {"g_per_l": 0.2})
    assert subtle["level"] == "allowed" and "subtle" in subtle["because"]
    assert "set by the user, 2026-10-18" in subtle["because"]
    aggressive = level(conn, "25B", "Fixture Spice", "secondary", {"g_per_l": 2.5})
    assert aggressive["level"] == "allowed" and "aggressive" in aggressive["because"]
    assert "set by the user, 2026-10-18" in aggressive["because"]
    # the points themselves belong to the band
    assert "subtle" not in level(conn, "25B", "Fixture Spice", "secondary", {"g_per_l": 0.25})["because"]
    assert "aggressive" not in level(conn, "25B", "Fixture Spice", "secondary", {"g_per_l": 2.0})["because"]


def test_too_much_against_the_envelope(conn):
    load_fixtures(conn)
    # 25B allows spice up to low (2): a noticeable (4) dose is too much, a subtle (2) one is not
    too_much = level(conn, "25B", "Fixture Spice", "secondary", {"g_per_l": 0.8})
    assert too_much["level"] == "out_of_style" and "too much" in too_much["because"]
    assert level(conn, "25B", "Fixture Spice", "secondary", {"g_per_l": 0.2})["level"] == "allowed"


def test_tags_never_change_the_level(conn):
    load_fixtures(conn)
    set_spice_envelope(conn, "25B", 0, 7)
    for g in (0.2, 0.8, 2.5):
        a = level(conn, "25B", "Fixture Spice", "secondary", {"g_per_l": g})
        b = level(conn, "25B", "Fixture Spice Citrus", "secondary", {"g_per_l": g})
        assert a["level"] == b["level"]


def test_typical_when_the_envelope_asks_for_it(conn):
    load_fixtures(conn)
    set_spice_envelope(conn, "25B", 0, 7)
    assert level(conn, "25B", "Fixture Spice", "secondary", {"g_per_l": 0.8})["level"] == "allowed"
    set_spice_envelope(conn, "25B", 1, 7)
    assert level(conn, "25B", "Fixture Spice", "secondary", {"g_per_l": 0.8})["level"] == "typical"


def test_silent_specialty_dimension_is_out_of_style(conn):
    load_fixtures(conn)
    result = level(conn, "18B", "Fixture Spice", "secondary", {"g_per_l": 0.8})
    assert result["level"] == "out_of_style"
    assert "specialty spice" in result["because"]


def test_no_dose_cases(conn):
    load_fixtures(conn)
    set_spice_envelope(conn, "25B", 0, 7)
    none = level(conn, "25B", "Fixture No Dose", "boil", {"g_per_l": 1.0})
    assert none["level"] == "allowed" and "no sourced dose" in none["because"]
    given_nothing = level(conn, "25B", "Fixture Spice", "secondary")
    assert given_nothing["level"] == "allowed" and "dose not given" in given_nothing["because"]


def test_category_other_has_no_dimension(conn):
    load_fixtures(conn)
    result = level(conn, "25B", "Fixture Other", "secondary", {"g_per_l": 1.0})
    assert result["level"] is None
    assert "no added-character dimension" in result["because"]


def test_process_aids_are_allowed_everywhere(conn):
    load_fixtures(conn)
    styles = [r[0] for r in conn.execute(
        "select b.code from ref.beer_style b where exists"
        " (select 1 from ref.style_sensory s where s.style_id = b.id and s.reviewed) limit 5")]
    no_envelope = conn.execute(
        "select b.code from ref.beer_style b where not exists"
        " (select 1 from ref.style_sensory s where s.style_id = b.id and s.reviewed)"
        " and not exists (select 1 from ref.style_ingredient si where si.style_id = b.id and si.reviewed)"
        " limit 1").fetchone()[0]
    for style in styles + [no_envelope]:
        for name, usage in (("Fixture Irish Moss", "boil"), ("Fixture Enzyme", "ferment")):
            result = level(conn, style, name, usage)
            assert result["level"] == "allowed", (style, name)
            assert "no flavour effect" in result["because"]


def test_misc_usage_must_belong_to_the_row(conn):
    load_fixtures(conn)
    for name, usage in (("Fixture Spice", "boil"), ("Fixture Irish Moss", "secondary")):
        with pytest.raises(psycopg.errors.RaiseException, match="is not a usage of"):
            level(conn, "25B", name, usage)
        conn.rollback()
        load_fixtures(conn)
