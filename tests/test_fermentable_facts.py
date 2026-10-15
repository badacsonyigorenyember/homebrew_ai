"""Fermentable facts: schema (Task 2), loader and data (Tasks 3-4) of s2-formulation-rules."""

import copy

import psycopg
import pytest

from loaders import fermentable_facts as ff
from loaders.db import connect

W, V, S = "Weyermann", "Viking Malt", "Simpsons Malt"
SOURCES = {
    "malt-substitution-2025", "user-supplied", "weyermann-2026", "viking-malt-2023", "palmer-how-to-brew",
    "simpsons-malt-2025", "hopline-malts", "hopline-adjuncts",
}


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


@pytest.mark.stack
def test_schema(conn):
    columns = {
        r[0]
        for r in conn.execute(
            "select column_name from information_schema.columns "
            "where table_schema = 'ref' and table_name = 'fermentable'"
        )
    }
    assert {"enzyme_activity", "min_boil_min", "description", "description_ref"} <= columns

    # The check constraints reject bad values; the transaction is rolled back each time.
    for column, bad in (("enzyme_activity", "'medium'"), ("min_boil_min", "30")):
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(
                f"update ref.fermentable set {column} = {bad} "
                "where ingredient_id = (select min(ingredient_id) from ref.fermentable)"
            )
        conn.rollback()

    owners = {
        r[0]: r[1]
        for r in conn.execute(
            "select c.relname, pg_get_userbyid(c.relowner) from pg_class c "
            "join pg_namespace n on n.oid = c.relnamespace "
            "where n.nspname = 'ref' and c.relname in "
            "('fermentable_substitute', 'fermentable_substitutes', 'fermentable_style')"
        )
    }
    assert owners == {
        "fermentable_substitute": "postgres",
        "fermentable_substitutes": "postgres",
        "fermentable_style": "postgres",
    }
    kinds = dict(
        conn.execute(
            "select c.relname, c.relkind from pg_class c join pg_namespace n on n.oid = c.relnamespace "
            "where n.nspname = 'ref' and c.relname like 'fermentable_%'"
        ).fetchall()
    )
    assert kinds["fermentable_substitutes"] == "v"

    row = conn.execute(
        "select title, edition, publisher from ref.source where slug = 'malt-substitution-2025'"
    ).fetchone()
    assert row == ("PrimeTime Malt Substitution Chart", "2025 (short)", "Hops Shop BG")


# --- the data file (no database needed) ---------------------------------------------------------


@pytest.fixture(scope="module")
def data():
    return ff.read()


def fake_rows(data):
    """Every row of the file, with no max_pct, as fetch_rows would return it. The rows with a
    confirmed 90-minute boil get a colour that proposes it; the others have none."""
    return {
        (f["producer"], f["name"]): {
            "ebc": (3.0, 4.0) if (f["producer"], f["name"]) in LONG_BOILS else None,
            "max_pct": None,
            "max_pct_source": None,
        }
        for f in data["fermentable"]
    }


def by_key(data):
    return {(f["producer"], f["name"]): f for f in data["fermentable"]}


# R1, written out again here so a typo in the file shows up. Chart groups, then the R1 list.
EXPECTED_ROLES = {
    "base": [
        (W, "Extra Pale Premium Pilsner Malt"), (W, "Pilsner Malt"), (W, "Vienna Malt"), (W, "Pale Ale Malt"),
        (V, "Pilsner Malt"), (V, "Vienna Malt"), (V, "Pale Ale Malt"),
        (W, "Wheat Malt Pale"), (W, "Rye Malt Pale"), (W, "Spelt Malt"), (W, "Oak Smoked Wheat Malt"),
        (W, "Eraclea Pilsner Malt"), (W, "Bohemian Pilsner Malt"),
        (V, "Wheat Malt"), (V, "Rye Malt"), (V, "Smoked Wheat Malt"), (V, "Lightly Peated Malt"), (V, "Enzyme Malt"),
        (S, "Finest Pale Ale Golden Promise"), (S, "Finest Pale Ale Maris Otter"),
    ],
    "kilned": [
        (W, "Munich Malt Type 1"), (W, "Munich Malt Type 2"), (W, "Melanoidin Malt"), (W, "Abbey Malt"),
        (W, "Beech Smoked Barley Malt"), (V, "Munich Light Malt"), (V, "Munich Dark Malt"),
        (V, "Red Active Malt"), (V, "Red Ale Malt"),
        (W, "Wheat Malt Dark"), (W, "Acidulated Malt"), (V, "Smoked Malt (cherry wood)"), (V, "Smoked Malt (pear wood)"),
    ],
    "crystal": [
        (W, "Carapils"), (W, "Carahell"), (W, "Carabelge"), (W, "Carared"), (W, "Caraamber"),
        (W, "Caramunich Type 1"), (W, "Caramunich Type 2"), (W, "Caramunich Type 3"), (W, "Carabohemian"),
        (W, "Special W"), (W, "Caraaroma"),
        (V, "CaraBody Malt"), (V, "Caramel Pale Malt"), (V, "Golden Ale Malt"), (V, "Dextrin Malt"),
        (V, "Caramel 30 Malt"), (V, "Caramel 50 Malt"), (V, "Caramel 100 Malt"), (V, "Caramel 150 Malt"),
        (V, "Caramel 300 Malt"), (V, "Caramel 400 Malt"), (V, "Caramel 600 Malt"),
        (W, "Carawheat"), (V, "Caramel 200 Malt"), (S, "Crystal Extra Dark"), (S, "Crystal T50"), (S, "DRC"),
    ],
    "roast": [
        (W, "Carafa Type 1"), (W, "Carafa Type 2"), (W, "Carafa Type 3"), (W, "Carafa Special Type 1"),
        (W, "Carafa Special Type 2"), (W, "Carafa Special Type 3"), (W, "Roasted Barley"),
        (V, "Cookie Malt"), (V, "Chocolate Light Malt"), (V, "Chocolate Dark Malt"), (V, "Black Malt"),
        (V, "Roasted Barley"),
        (W, "Chocolate Wheat Malt"),
    ],
    "adjunct": [("", "Flaked Oats"), ("", "Flaked Barley"), ("", "Flaked Corn"), ("", "Flaked Rice"), (V, "Sprau Malt")],
    "sugar": [("", "Honey"), ("", "Brown Candi Sugar"), ("", "Lactose")],
}


def test_roles_match_r1(data):
    rows = by_key(data)
    assert len(rows) == 81
    counts = {role: len(keys) for role, keys in EXPECTED_ROLES.items()}
    assert counts == {"base": 20, "kilned": 13, "crystal": 27, "roast": 13, "adjunct": 5, "sugar": 3}
    for role, keys in EXPECTED_ROLES.items():
        for key in keys:
            assert rows[key].get("role") == role, key
    assert all("role" in f for f in rows.values())  # Sprau: adjunct, the user's answer of 2026-10-15
    assert rows[(V, "Sprau Malt")]["role_source"] == "user-supplied"
    chart = {k for k, f in rows.items() if f.get("role_source") == "malt-substitution-2025"}
    assert len(chart) == 7 + 9 + 22 + 12  # chart groups 1A, 1B, 1C, 1D


def test_max_pct_is_decision_e(data):
    given = {k: f["max_pct"] for k, f in by_key(data).items() if "max_pct" in f}
    assert given == {
        (V, "Munich Light Malt"): 100, (V, "Munich Dark Malt"): 100,
        (V, "Lightly Peated Malt"): 100, (V, "Smoked Wheat Malt"): 100,
        (V, "Caramel 30 Malt"): 20, (V, "Caramel 50 Malt"): 20,
        (V, "Caramel 100 Malt"): 15, (V, "Caramel 150 Malt"): 15, (V, "Caramel 200 Malt"): 15,
        (V, "Caramel 300 Malt"): 10, (V, "Caramel 400 Malt"): 10, (V, "Caramel 600 Malt"): 10,
        ("", "Flaked Oats"): 30, ("", "Flaked Barley"): 20, ("", "Flaked Corn"): 20,
        ("", "Honey"): 20, ("", "Brown Candi Sugar"): 20, ("", "Lactose"): 10,
    }
    assert {f["max_pct_source"] for f in data["fermentable"] if "max_pct" in f} == {"user-supplied"}
    assert all(f["max_pct_basis"] for f in data["fermentable"] if "max_pct" in f)
    assert "unplaced" not in {f["max_pct_basis"] for f in data["fermentable"] if "max_pct" in f}
    decision_e = {k for k, f in by_key(data).items() if f.get("max_pct_basis") == "user decision E, 2026-10-14"}
    assert decision_e == {
        (V, "Caramel 30 Malt"), (V, "Caramel 50 Malt"), (V, "Caramel 300 Malt"), (V, "Caramel 400 Malt"),
        (V, "Caramel 600 Malt"), ("", "Brown Candi Sugar"), ("", "Flaked Barley"), ("", "Flaked Corn"), ("", "Lactose"),
    }


def test_substitute_pairs(data):
    pairs = [frozenset((tuple(s["a"]), tuple(s["b"]))) for s in data["substitute"]]
    assert len(pairs) == len(set(pairs)) == 27
    chart = [
        ("Pilsner Malt", "Pilsner Malt"), ("Vienna Malt", "Vienna Malt"), ("Pale Ale Malt", "Pale Ale Malt"),
        ("Munich Malt Type 1", "Munich Light Malt"), ("Munich Malt Type 2", "Munich Dark Malt"),
        ("Melanoidin Malt", "Red Ale Malt"), ("Carapils", "CaraBody Malt"), ("Carahell", "Caramel 30 Malt"),
        ("Carared", "Caramel 50 Malt"), ("Caramunich Type 1", "Caramel 100 Malt"),
        ("Caramunich Type 3", "Caramel 150 Malt"), ("Special W", "Caramel 300 Malt"),
        ("Caraaroma", "Caramel 400 Malt"), ("Carafa Type 1", "Chocolate Dark Malt"),
        ("Carafa Type 2", "Black Malt"), ("Carafa Type 3", "Black Malt"),
        ("Roasted Barley", "Roasted Barley"), ("Wheat Malt Pale", "Wheat Malt"), ("Rye Malt Pale", "Rye Malt"),
    ]
    expected = {frozenset(((W, a), (V, b))) for a, b in chart}
    expected |= {
        frozenset(((W, "Eraclea Pilsner Malt"), (V, "Pilsner Malt"))),
        frozenset(((W, "Bohemian Pilsner Malt"), (V, "Pilsner Malt"))),
        frozenset(((S, "Crystal Extra Dark"), (W, "Caraaroma"))),
        frozenset(((S, "DRC"), (W, "Special W"))),
    }
    for golden in ("Finest Pale Ale Golden Promise", "Finest Pale Ale Maris Otter"):
        expected |= {frozenset(((S, golden), (W, "Pale Ale Malt"))), frozenset(((S, golden), (V, "Pale Ale Malt")))}
    assert set(pairs) == expected
    # No substitute for these rows.
    in_a_pair = {key for pair in pairs for key in pair}
    for key in [(V, "Caramel 200 Malt"), (V, "Smoked Malt (cherry wood)"), (V, "Smoked Malt (pear wood)"),
                (V, "Smoked Wheat Malt"), (W, "Beech Smoked Barley Malt"), (W, "Oak Smoked Wheat Malt"),
                (V, "Sprau Malt"), (S, "Crystal T50")]:
        assert key not in in_a_pair, key
    assert {s["source"] for s in data["substitute"]} == {"malt-substitution-2025", "user-supplied"}
    assert sum(s["source"] == "malt-substitution-2025" for s in data["substitute"]) == 19


def test_enzyme_medium_is_normal(data):
    rows = by_key(data)
    assert rows[(W, "Munich Malt Type 1")]["enzyme_activity"] == "normal"  # printed "medium", p. 6
    assert rows[(W, "Wheat Malt Dark")]["enzyme_activity"] == "normal"  # printed "medium", p. 13
    assert "medium" not in {f.get("enzyme_activity") for f in data["fermentable"]}
    # Acidulated's line states no level; the Viking rows with only vague words stay empty.
    for key in [(W, "Acidulated Malt"), (V, "Caramel Pale Malt"), (V, "Golden Ale Malt"), (V, "Dextrin Malt"),
                (V, "Pilsner Malt"), (V, "Enzyme Malt")]:
        assert "enzyme_activity" not in rows[key], key
    # The Viking words the plan names.
    assert rows[(V, "Munich Light Malt")]["enzyme_activity"] == "low"
    assert rows[(V, "Caramel 400 Malt")]["enzyme_activity"] == "none"
    assert rows[(W, "Pilsner Malt")]["enzyme_activity"] == "high"


def test_propose_min_boil():
    assert ff.propose_min_boil("base", (3.0, 4.0)) == 90  # Pilsner, midpoint 3.5
    assert ff.propose_min_boil("base", (5.5, 7.5)) == 60  # Pale Ale, midpoint 6.5
    assert ff.propose_min_boil("base", (4, 6)) == 60  # midpoint 5 is not below 5
    assert ff.propose_min_boil("crystal", (2, 4)) == 60  # only base malts
    assert ff.propose_min_boil("base", None) == 60
    assert ff.propose_min_boil("base", (None, None)) == 60
    assert ff.propose_min_boil("base", (None, 8)) == 60  # open range "(,8]" uses 8
    assert ff.propose_min_boil("base", (None, 4)) == 90  # open range uses its one bound
    assert ff.propose_min_boil(None, (3, 4)) == 60  # no role yet


def test_every_value_names_a_source(data):
    ff.check(data, fake_rows(data), SOURCES, allow_unplaced=True)  # sources, enzyme and role fields
    for f in data["fermentable"]:
        if "role" in f:
            assert f["role_source"] and f["role_note"]
        if "enzyme_activity" in f:
            assert f["enzyme_source"] and f["enzyme_ref"]
    for s in data["substitute"]:
        assert s["source"] and s["note"]


LONG_BOILS = {
    (V, "Pilsner Malt"), (V, "Wheat Malt"), (W, "Pilsner Malt"), (W, "Extra Pale Premium Pilsner Malt"),
    (W, "Eraclea Pilsner Malt"), (W, "Bohemian Pilsner Malt"), (W, "Wheat Malt Pale"),
}


def test_style_names_are_mapped(data):
    mapping = data["style_names"]
    assert len(mapping) == 247 and sum(code == "" for code in mapping.values()) == 21
    assert all(name == name.lower() for name in mapping)
    for f in data["fermentable"]:
        for printed in f.get("style_names", []):
            assert printed.lower() in mapping, printed
        assert ("style_names" in f) == ("styles_source" in f)
    assert "style_names" not in by_key(data)[("", "Honey")]  # adjuncts print no style list we load


def test_descriptions_in_file(data):
    for f in data["fermentable"]:
        assert 40 < len(f["description"]) < 500, f["name"]
        assert f["description_source"] and f["description_ref"]
    rows = by_key(data)
    assert rows[(W, "Special W")]["description_ref"] == "p. 39"
    assert rows[("", "Lactose")]["description_ref"].startswith("https://www.hopline.hu/")


def test_long_boils_are_the_confirmed_seven(data):
    assert {k for k, f in by_key(data).items() if f.get("min_boil_min", 60) > 60} == LONG_BOILS


def test_check_rejects_unknown_style(data):
    rows = fake_rows(data)
    bad = copy.deepcopy(data)
    bad["fermentable"][0]["style_names"] = ["No Such Style"]
    bad["fermentable"][0]["styles_source"] = "user-supplied"
    with pytest.raises(ValueError, match="not in the \\[style_names\\] table"):
        ff.check(bad, rows, SOURCES)
    bad = copy.deepcopy(data)
    bad["style_names"]["pils"] = "no-such-code"
    with pytest.raises(ValueError, match="not in ref.beer_style"):
        ff.check(bad, rows, SOURCES, style_codes={"5D"})


def test_check_rejects_unknown_name(data):
    rows = fake_rows(data)
    bad = copy.deepcopy(data)
    bad["fermentable"][0]["name"] = "No Such Malt"
    with pytest.raises(ValueError, match="not in ref.ingredient"):
        ff.check(bad, rows, SOURCES, allow_unplaced=True)


def test_check_rejects_bad_values(data):
    rows = fake_rows(data)
    pilsner = next(i for i, f in enumerate(data["fermentable"]) if f["name"] == "Pilsner Malt" and f["producer"] == W)

    def broken(**changes):
        bad = copy.deepcopy(data)
        bad["fermentable"][pilsner].update(changes)
        return bad

    for changes, message in [
        ({"role": "malt"}, "role"),
        ({"enzyme_activity": "medium"}, "enzyme_activity"),
        ({"role_source": "no-such-source"}, "not in ref.source"),
        ({"min_boil_min": 120}, "was not proposed"),  # the proposal is 90
        ({"max_pct": 100, "max_pct_source": "user-supplied", "max_pct_basis": "x"}, "max_pct"),
    ]:
        existing = dict(rows)
        if "max_pct" in changes:  # a row that already holds a catalogue value is not one of the 18
            existing[(W, "Pilsner Malt")] = {"ebc": None, "max_pct": 100, "max_pct_source": "weyermann-2026"}
        with pytest.raises(ValueError, match=message):
            ff.check(broken(**changes), existing, SOURCES, allow_unplaced=True)

    # A long boil that is proposed passes.
    rows[(W, "Pilsner Malt")] = {"ebc": (2.5, 4.5), "max_pct": None, "max_pct_source": None}
    ff.check(broken(min_boil_min=90), rows, SOURCES, allow_unplaced=True)


def test_check_rejects_bad_pairs_and_unplaced(data):
    rows = fake_rows(data)
    bad = copy.deepcopy(data)
    bad["substitute"].append({"a": list(bad["substitute"][0]["b"]), "b": list(bad["substitute"][0]["a"]),
                              "source": "user-supplied", "note": "x"})
    with pytest.raises(ValueError, match="listed twice"):
        ff.check(bad, rows, SOURCES, allow_unplaced=True)
    bad = copy.deepcopy(data)
    bad["substitute"][0]["b"] = bad["substitute"][0]["a"]
    with pytest.raises(ValueError, match="itself"):
        ff.check(bad, rows, SOURCES, allow_unplaced=True)
    # Loading never accepts a max_pct whose basis is still "unplaced".
    bad = copy.deepcopy(data)
    next(f for f in bad["fermentable"] if "max_pct" in f)["max_pct_basis"] = "unplaced"
    with pytest.raises(ValueError, match="unplaced"):
        ff.check(bad, rows, SOURCES)


@pytest.mark.stack
def test_style_codes_exist(conn, data):
    codes = ff.fetch_style_codes(conn)
    assert {c for c in data["style_names"].values() if c} <= codes


@pytest.mark.stack
def test_file_matches_the_database(conn, data):
    """The file's names are the 81 rows of ref.fermentable, and every check against the DB passes."""
    rows = ff.fetch_rows(conn)
    assert set(by_key(data)) == set(rows) and len(rows) == 81
    ff.check(data, rows, ff.fetch_sources(conn), style_codes=ff.fetch_style_codes(conn))


# --- the loaded database (Task 4) ---------------------------------------------------------------


def label(producer, name):
    return f"{producer} {name}".strip()


def db_rows(conn, columns):
    return {
        label(p, n): rest
        for p, n, *rest in conn.execute(
            f"select i.producer, i.name, {columns} from ref.fermentable f "
            "join ref.ingredient i on i.id = f.ingredient_id"
        )
    }


@pytest.mark.stack
def test_db_roles(conn, data):
    rows = db_rows(conn, "f.role")
    assert len(rows) == 81 and all(r[0] is not None for r in rows.values())
    for role, keys in EXPECTED_ROLES.items():
        for key in keys:
            assert rows[label(*key)] == [role], key
    counts = dict(conn.execute("select role, count(*) from ref.fermentable group by role").fetchall())
    assert counts == {"base": 20, "kilned": 13, "crystal": 27, "roast": 13, "adjunct": 5, "sugar": 3}
    assert rows["Viking Malt Sprau Malt"] == ["adjunct"]


@pytest.mark.stack
def test_db_max_pct(conn, data):
    assert conn.execute("select count(*) from ref.fermentable where max_pct is null").fetchone()[0] == 0
    expected = {label(*k): f["max_pct"] for k, f in by_key(data).items() if "max_pct" in f}
    assert len(expected) == 18
    loaded = dict(
        conn.execute(
            "select i.producer || ' ' || i.name, f.max_pct from ref.fermentable f join ref.ingredient i "
            "on i.id = f.ingredient_id where f.field_source->>'max_pct' = 'user-supplied'"
        ).fetchall()
    )
    assert {k.strip(): float(v) for k, v in loaded.items()} == {k: float(v) for k, v in expected.items()}
    assert all(f["max_pct_basis"] != "unplaced" for f in data["fermentable"] if "max_pct" in f)


@pytest.mark.stack
def test_db_enzyme_and_boil(conn, data):
    rows = db_rows(conn, "f.min_boil_min, f.enzyme_activity")
    assert {k for k, (boil, _) in rows.items() if boil > 60} == {label(*k) for k in LONG_BOILS}
    assert all(boil == 90 for boil, _ in rows.values() if boil > 60)
    no_enzyme = {k for k, (_, enzyme) in rows.items() if enzyme is None}
    report = open("docs/work/s2-formulation-rules/report.md", encoding="utf-8").read()
    section = report.split("## 2.")[1].split("## 3.")[0]
    listed = {line[2:].strip() for line in section.splitlines() if line.startswith("- ")}
    assert no_enzyme == listed and len(listed) == 30


@pytest.mark.stack
def test_db_substitutes(conn):
    pairs = {
        frozenset((label(a_p, a_n), label(b_p, b_n)))
        for a_p, a_n, b_p, b_n in conn.execute(
            "select a.producer, a.name, b.producer, b.name from ref.fermentable_substitute s "
            "join ref.ingredient a on a.id = s.fermentable_id join ref.ingredient b on b.id = s.substitute_id"
        )
    }
    assert len(pairs) == 27
    assert frozenset(("Weyermann Eraclea Pilsner Malt", "Viking Malt Pilsner Malt")) in pairs
    assert frozenset(("Simpsons Malt DRC", "Weyermann Special W")) in pairs
    assert not any("Simpsons Malt Crystal T50" in pair for pair in pairs)
    # The view lists every pair from both sides.
    both = conn.execute(
        "select count(*) from ref.fermentable_substitutes v join ref.fermentable_substitutes w "
        "on w.fermentable_id = v.substitute_id and w.substitute_id = v.fermentable_id"
    ).fetchone()[0]
    assert both == 54
    # Pairs do not chain: the view holds exactly the 27 stored pairs, once per direction.
    assert conn.execute("select count(*) from ref.fermentable_substitutes").fetchone()[0] == 54


@pytest.mark.stack
def test_db_descriptions(conn):
    missing = conn.execute(
        "select count(*) from ref.fermentable where description is null or description_ref is null "
        "or field_source->>'description' is null"
    ).fetchone()[0]
    assert missing == 0
    assert conn.execute("select count(*) from ref.fermentable where description is not null").fetchone()[0] == 81
    orphans = conn.execute(
        "select count(*) from ref.fermentable_style y left join ref.beer_style b on b.id = y.style_id "
        "where b.id is null"
    ).fetchone()[0]
    assert orphans == 0
    assert conn.execute("select count(*) from ref.fermentable_style").fetchone()[0] > 0


@pytest.mark.stack
def test_load_is_idempotent(conn, data):
    checksum = (
        "select md5(string_agg(t::text, '|' order by t::text)) from (select f::text from ref.fermentable f "
        "union all select s::text from ref.fermentable_substitute s "
        "union all select y::text from ref.fermentable_style y) t"
    )
    try:
        before = conn.execute(checksum).fetchone()[0]
        ff.load(conn, data)
        assert conn.execute(checksum).fetchone()[0] == before
    finally:
        conn.rollback()
