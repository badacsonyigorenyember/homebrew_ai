"""The ingredient intake (s8-ingredient-intake): the file checks need no database; the tests
that load into ref (later tasks) use the stack and roll back."""

import json
import shutil
import tomllib
from pathlib import Path

import pytest

from loaders import extra_ingredients as extra
from loaders import tags

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures" / "ingredients"
TEMPLATES = REPO / "shared" / "ingredients" / "_templates"


@pytest.fixture(scope="module")
def known():
    return extra.known_from_files(tags.read_vocab())


def check_folder(root, known):
    sources, ingredients = extra.read_folder(root)
    return extra.check_files(sources, ingredients, known)


def shown(path: Path) -> str:
    """The path as the checker prints it: relative to the repo when inside it."""
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


@pytest.fixture
def work(tmp_path):
    """A copy of the fixtures that a test may break."""
    root = tmp_path / "ingredients"
    shutil.copytree(FIXTURES, root)
    return root


def edit(root, rel, old, new):
    path = root / rel
    text = path.read_text()
    assert old in text, f"{old!r} not in {rel}"
    path.write_text(text.replace(old, new))
    return path


def toml_text(fields: dict) -> str:
    """A flat dict as TOML: JSON strings, numbers and lists are valid TOML values."""
    return "".join(f"{key} = {json.dumps(value)}\n" for key, value in fields.items())


def test_fixtures_pass(known):
    assert check_folder(FIXTURES, known) == []
    sources, ingredients = extra.read_folder(FIXTURES)
    assert [s.fields["slug"] for s in sources] == ["fixture-data-sheet"]
    assert len(ingredients) == 14
    assert "fixture-data-sheet" not in known.source_notes  # it comes from sources/, not from ref


@pytest.mark.parametrize("kind, fixture", [
    ("fermentable", "fermentable/fixture-crystal.toml"),
    ("hop", "hop/fixture-hop.toml"),
    ("yeast", "yeast/fixture-ale.toml"),
    ("yeast", "yeast/fixture-lacto.toml"),
    ("misc-flavour", "misc/fixture-spice.toml"),
    ("misc-flavour", "misc/fixture-coffee-beans.toml"),
    ("misc-flavour", "misc/fixture-fruit.toml"),
    ("misc-flavour", "misc/fixture-vanilla-extract.toml"),
    ("misc-process", "misc/fixture-irish-moss.toml"),
    ("misc-process", "misc/fixture-enzyme.toml"),
    ("source", "sources/fixture-data-sheet.toml"),
])
def test_template_filled_from_fixture_passes(known, work, kind, fixture):
    template = tomllib.loads((TEMPLATES / f"{kind}.toml").read_text())
    filled = tomllib.loads((FIXTURES / fixture).read_text())
    assert set(filled) <= set(template), f"template lacks {set(filled) - set(template)}"
    path = work / fixture
    path.write_text(toml_text({**template, **filled}))
    assert check_folder(work, known) == []
    path.write_text(toml_text(template))  # the empty template itself must be refused
    assert any(e.startswith(shown(path)) for e in check_folder(work, known))


# (id, file, old text, new text, file the error names, field the error names)
REFUSALS = [
    ("missing-role", "fermentable/fixture-crystal.toml", 'role = "crystal"\n', "", None, "role"),
    ("missing-origins", "hop/fixture-hop.toml", 'origins = ["US"]\n', "", None, "origins"),
    ("missing-type", "yeast/fixture-ale.toml", 'type = "ale"\n', "", None, "type"),
    ("missing-producer", "yeast/fixture-ale.toml", 'producer = "Fixture Yeasts"\n', "", None, "producer"),
    ("missing-descriptors-hop", "hop/fixture-hop.toml", 'descriptors = ["citrus", "pine"]', "descriptors = []", None, "descriptors"),
    ("missing-attenuation", "yeast/fixture-ale.toml", "attenuation_pct = [74, 78]", "attenuation_pct = []", None, "attenuation_pct"),
    ("bad-role", "fermentable/fixture-crystal.toml", 'role = "crystal"', 'role = "crystall"', None, "role"),
    ("bad-fermentability", "fermentable/fixture-crystal.toml", 'fermentability = ""', 'fermentability = "partly"', None, "fermentability"),
    ("bad-purpose", "hop/fixture-hop.toml", 'purpose = "dual"', 'purpose = "both"', None, "purpose"),
    ("bad-flocculation", "yeast/fixture-ale.toml", 'flocculation = "medium"', 'flocculation = "sticky"', None, "flocculation"),
    ("bad-type", "yeast/fixture-ale.toml", 'type = "ale"', 'type = "wine"', None, "type"),
    ("bad-form", "yeast/fixture-ale.toml", 'form = "dry"', 'form = "powder"', None, "form"),
    ("bad-enzyme", "fermentable/fixture-crystal.toml", 'enzyme_activity = "none"', 'enzyme_activity = "lots"', None, "enzyme_activity"),
    ("range-low-above-high", "fermentable/fixture-crystal.toml", "ebc = [230, 270]", "ebc = [270, 230]", None, "ebc"),
    ("figure-without-ref", "hop/fixture-hop.toml", 'alpha_pct_ref = "fixture sheet p. 3"\n', "", None, "alpha_pct"),
    ("description-without-ref", "hop/fixture-hop.toml", 'description_ref = "fixture sheet p. 3"', 'description_ref = ""', None, "description_ref"),
    ("unknown-source", "fermentable/fixture-crystal.toml", 'source = "fixture-data-sheet"', 'source = "nowhere"', None, "source"),
    ("field-source-unknown", "hop/fixture-hop.toml", 'purpose = "dual"', 'purpose = "dual"\npurpose_source = "nowhere"', None, "purpose_source"),
    ("source-without-edition", "sources/fixture-data-sheet.toml", 'edition = "test fixture"\n', "", None, "edition"),
    ("source-slug-not-file-name", "sources/fixture-data-sheet.toml", 'slug = "fixture-data-sheet"', 'slug = "other"', None, "slug"),
    ("fermentability-without-ref", "fermentable/fixture-crystal.toml", 'fermentability = ""', 'fermentability = "none"', None, "fermentability_ref"),
    ("unknown-descriptor", "fermentable/fixture-crystal.toml", '"caramel"', '"zzword"', None, "descriptors"),
    ("unknown-origin", "hop/fixture-hop.toml", 'origins = ["US"]', 'origins = ["XX"]', None, "origins"),
    ("hop-named-like-a-loader-hop", "hop/fixture-hop.toml", 'name = "Fixture Hop"', 'name = "Citra"', None, "name"),
    ("folder-differs-from-kind", "hop/fixture-hop.toml", 'kind = "hop"', 'kind = "yeast"', None, "kind"),
    ("unknown-key", "hop/fixture-hop.toml", 'purpose = "dual"', 'purpose = "dual"\ncolour = 3', None, "colour"),
    ("bad-toml", "hop/fixture-hop.toml", 'purpose = "dual"', 'purpose = = "dual"', None, "toml"),
    ("misc-missing-purpose", "misc/fixture-spice.toml", 'purpose = "flavour"\n', "", None, "purpose"),
    ("misc-missing-usages", "misc/fixture-spice.toml", 'usages = ["whirlpool", "secondary"]\n', "", None, "usages"),
    ("misc-flavour-without-descriptors", "misc/fixture-spice.toml", 'descriptors = ["spicy"]', "descriptors = []", None, "descriptors"),
    ("misc-process-with-descriptors", "misc/fixture-irish-moss.toml", 'purpose = "process"', 'purpose = "process"\ndescriptors = ["spicy"]', None, "descriptors"),
    ("misc-category-not-of-purpose", "misc/fixture-spice.toml", 'category = "spice"', 'category = "fining"', None, "category"),
    ("misc-unknown-usage", "misc/fixture-spice.toml", '"secondary"]', '"bottle"]', None, "usages"),
    ("misc-both-doses", "misc/fixture-spice.toml", 'dose_g_per_l = [0.5, 1.0]', 'dose_g_per_l = [0.5, 1.0]\ndose_ml_per_l = [1, 2]', None, "dose_ml_per_l"),
    ("misc-sugar-on-non-fruit", "misc/fixture-spice.toml", 'purpose = "flavour"', 'purpose = "flavour"\nsugar_pct = 5', None, "sugar_pct"),
    ("misc-dose-without-ref", "misc/fixture-spice.toml", 'dose_g_per_l_ref = "fixture sheet p. 5"\n', "", None, "dose_g_per_l_ref"),
    ("misc-time-not-whole", "misc/fixture-coffee-beans.toml", "time_min = 2880", "time_min = 1.5", None, "time_min"),
    ("misc-dose-out-of-range", "misc/fixture-spice.toml", "dose_g_per_l = [0.5, 1.0]", "dose_g_per_l = [0.5, 2000]", None, "dose_g_per_l"),
]


@pytest.mark.parametrize("case", REFUSALS, ids=[c[0] for c in REFUSALS])
def test_refusal(known, work, case):
    _, rel, old, new, _, field = case
    path = edit(work, rel, old, new)
    errors = check_folder(work, known)
    assert any(e.startswith(f"{shown(path)}: {field}") for e in errors), errors


def test_two_files_one_product_refused(known, work):
    copy = work / "hop" / "fixture-hop2.toml"
    shutil.copy(work / "hop" / "fixture-hop.toml", copy)
    errors = check_folder(work, known)
    first = shown(work / "hop" / "fixture-hop.toml")
    assert any(e.startswith(f"{shown(copy)}: name") and first in e for e in errors), errors


def test_misc_file_is_checked(known, work):
    misc = work / "misc" / "honey.toml"
    misc.write_text(toml_text({"kind": "misc", "name": "Honey"}))
    errors = check_folder(work, known)
    for field in ("purpose", "category", "usages", "source", "description"):
        assert any(e.startswith(f"{shown(misc)}: {field}") for e in errors), (field, errors)


def test_misc_waits_reasons(known):
    _, ingredients = extra.read_folder(FIXTURES)
    reasons = {i.stem: extra.misc_waits(i) for i in ingredients if i.folder == "misc"}
    assert "mL/L" in reasons["fixture-vanilla-extract"]
    assert "changes the numbers (enzyme)" in reasons["fixture-enzyme"]
    assert "decided with M6" in reasons["fixture-fruit"]
    assert [k for k, v in reasons.items() if v] == ["fixture-enzyme", "fixture-fruit", "fixture-vanilla-extract"]
    assert reasons["fixture-spice"] is None


def test_all_errors_reported(known, work):
    one = edit(work, "hop/fixture-hop.toml", 'purpose = "dual"', 'purpose = "both"')
    two = edit(work, "yeast/fixture-ale.toml", 'type = "ale"', 'type = "wine"')
    errors = check_folder(work, known)
    assert any(e.startswith(shown(one)) for e in errors)
    assert any(e.startswith(shown(two)) for e in errors)


# ---------------------------------------------------------------- with the database (stack)

from loaders.db import connect  # noqa: E402

COUNT_TABLES = ["ref.source", "ref.ingredient", "ref.fermentable", "ref.hop", "ref.yeast", "ref.misc", "ref.ingredient_alias"]


@pytest.fixture
def conn():
    connection = connect()
    connection.read_only = True
    yield connection
    connection.rollback()
    connection.close()


def counts(conn):
    return {t: conn.execute(f"select count(*) from {t}").fetchone()[0] for t in COUNT_TABLES}


def db_check(conn, root, mutate_known=None):
    """All errors for a folder, as `--check` finds them."""
    sources, ingredients = extra.read_folder(root)
    known = extra.known_from_db(conn, extra.known_from_files(tags.read_vocab()))
    if mutate_known:
        mutate_known(known)
    return extra.check_files(sources, ingredients, known) + extra.check_aliases(conn, ingredients)


@pytest.mark.stack
def test_check_writes_nothing(conn, work, capsys):
    before = counts(conn)
    edit(work, "hop/fixture-hop.toml", 'purpose = "dual"', 'purpose = "sideways"')
    assert extra.main(["--check", str(work)]) == 1
    assert "hop/fixture-hop.toml: purpose" in capsys.readouterr().out
    assert extra.main(["--check", str(FIXTURES)]) == 0
    out = capsys.readouterr().out
    assert out.startswith("ok: 15 files (fermentable 1, hop 1, yeast 2, misc 10, sources 1)")
    assert out.count("\nwaits: ") == 3
    assert counts(conn) == before


@pytest.mark.stack
def test_clash_with_db_row(conn, work):
    edit(work, "yeast/fixture-ale.toml", 'name = "Fixture Ale FA-1"', 'name = "SafAle US-05"')
    edit(work, "yeast/fixture-ale.toml", 'producer = "Fixture Yeasts"', 'producer = "Fermentis"')
    errors = db_check(conn, work, lambda k: k.loader_keys.clear())
    assert any("clashes with Fermentis SafAle US-05 loaded by another loader" in e for e in errors)


@pytest.mark.stack
def test_alias_finding_another_product_refused(conn, work):
    edit(work, "hop/fixture-hop.toml", '"fixture hop variety"', '"citra"')
    errors = db_check(conn, work)
    assert any("hop/fixture-hop.toml: aliases" in e and "Citra" in e for e in errors)


@pytest.mark.stack
def test_alias_on_two_files_refused(conn, work):
    edit(work, "hop/fixture-hop.toml", '"fixture hop variety"', '"fixture crystal"')
    errors = db_check(conn, work)
    assert any("aliases" in e and "is also an alias in" in e for e in errors)


@pytest.mark.stack
def test_alias_equal_to_another_files_name_refused(conn, work):
    edit(work, "hop/fixture-hop.toml", '"fixture hop variety"', '"Fixture Ale FA-1"')
    errors = db_check(conn, work)
    assert any("hop/fixture-hop.toml: aliases" in e and "Fixture Ale FA-1" in e for e in errors)


@pytest.mark.stack
@pytest.mark.parametrize("alias", ["crystal fixture", "Fixture Crystal Malt", "malt crystal fixture"])
def test_alias_same_words_other_order_or_kind_word_refused(conn, work, alias):
    edit(work, "hop/fixture-hop.toml", '"fixture hop variety"', json.dumps(alias))
    errors = db_check(conn, work)
    assert any("hop/fixture-hop.toml: aliases" in e and "is also an alias in" in e for e in errors)


@pytest.mark.stack
def test_alias_equal_to_another_files_name_without_kind_word_refused(conn, work):
    edit(work, "yeast/fixture-ale.toml", 'name = "Fixture Ale FA-1"', 'name = "Fixture Ale FA-1 Yeast"')
    edit(work, "yeast/fixture-lacto.toml", '"fixture lacto"', '"fixture ale fa-1"')
    errors = db_check(conn, work)
    assert any("yeast/fixture-lacto.toml: aliases" in e and "is the name of" in e for e in errors)


@pytest.mark.stack
def test_source_slug_of_db011_refused(conn, work):
    (work / "sources" / "bjcp-2021.toml").write_text(
        toml_text({"slug": "bjcp-2021", "title": "BJCP", "edition": "2021"})
    )
    errors = db_check(conn, work)
    assert any("sources/bjcp-2021.toml: slug" in e and "already a source" in e for e in errors)


# ---------------------------------------------------------------- the load (stack, always rolled back)
# Never load tests/fixtures/ingredients/ outside these tests: the rows are invented.

import json as _json  # noqa: E402

from loaders import adjuncts, fermentable_facts, hops, malts, yeasts  # noqa: E402

HOPLINE = REPO / "shared" / "rag-files" / "hopline"
CATALOGUE = REPO / "shared" / "rag-files" / "maltsters" / "malt_catalogue.json"


@pytest.fixture
def rw():
    """A read-write connection whose work is always rolled back."""
    connection = connect()
    yield connection
    connection.rollback()
    connection.close()


def load_fixtures(conn):
    sources, ingredients = extra.read_folder(FIXTURES)
    loaded = extra.load(conn, sources, ingredients)
    return ingredients, loaded  # a liquid extract is in ingredients but not in loaded["ids"]


def intake_snapshot(conn):
    """Every intake row with its kind row and aliases, plus the intake sources, as comparable text."""
    out = {}
    out["source"] = [r[0] for r in conn.execute(
        "select row_to_json(s)::text from ref.source s where notes like 'intake:%' order by slug")]
    out["ingredient"] = [r[0] for r in conn.execute(
        "select row_to_json(i)::text from ref.ingredient i where raw ? 'intake' order by id")]
    for table in ("fermentable", "hop", "yeast", "misc"):
        out[table] = [r[0] for r in conn.execute(
            f"select row_to_json(t)::text from ref.{table} t join ref.ingredient i on i.id = t.ingredient_id "
            "where i.raw ? 'intake' order by t.ingredient_id")]
    out["alias"] = [r[0] for r in conn.execute(
        "select row_to_json(a)::text from ref.ingredient_alias a join ref.ingredient i on i.id = a.ingredient_id "
        "where i.raw ? 'intake' order by a.ingredient_id, a.alias")]
    return out


@pytest.mark.stack
def test_load_twice_same_rows(rw):
    before = counts(rw)
    load_fixtures(rw)
    first_counts, first = counts(rw), intake_snapshot(rw)
    assert first_counts["ref.ingredient"] == before["ref.ingredient"] + 13  # 4 + 9 misc (the vanilla extract waits)
    assert first_counts["ref.misc"] == before["ref.misc"] + 9
    assert first_counts["ref.source"] == before["ref.source"] + 1
    assert first_counts["ref.ingredient_alias"] == before["ref.ingredient_alias"] + 5
    load_fixtures(rw)
    assert counts(rw) == first_counts
    assert intake_snapshot(rw) == first


@pytest.mark.stack
def test_reload_after_editing_files(rw, work):
    def load_work():
        sources, ingredients = extra.read_folder(work)
        assert extra.check_files(sources, ingredients, extra.known_from_files(tags.read_vocab())) == []
        return extra.load(rw, sources, ingredients)

    load_work()
    crystal = ("select f.ebc, f.field_source, i.raw->'intake'->'fields'->'ebc' from ref.fermentable f "
               "join ref.ingredient i on i.id = f.ingredient_id where i.name = 'Fixture Crystal 120'")
    assert rw.execute(crystal).fetchone()[0] is not None
    edit(work, "fermentable/fixture-crystal.toml", "ebc = [230, 270]", "ebc = []")
    edit(work, "fermentable/fixture-crystal.toml", 'ebc_ref = "fixture sheet p. 1"', 'ebc_ref = ""')
    edit(work, "hop/fixture-hop.toml", '["fixture hop variety"]', "[]")
    load_work()
    ebc, field_source, raw_ebc = rw.execute(crystal).fetchone()
    assert ebc is None and "ebc" not in field_source and raw_ebc == []
    assert rw.execute("select count(*) from ref.ingredient_alias a join ref.ingredient i on i.id = a.ingredient_id "
                      "where i.name = 'Fixture Hop'").fetchone()[0] == 0


@pytest.mark.stack
def test_alias_equal_to_another_files_name_rolls_back(rw):
    sources, ingredients = extra.read_folder(FIXTURES)
    for item in ingredients:
        if item.folder == "hop":
            item.fields["aliases"] = ["Fixture Ale FA-1"]
    with pytest.raises(RuntimeError, match="by an alias"):
        extra.load(rw, sources, ingredients)


@pytest.mark.stack
def test_field_source_covers_filled_fields(rw):
    ingredients, loaded = load_fixtures(rw)
    for item in ingredients:
        if item.path not in loaded["ids"]:
            continue
        kind = item.folder
        row = rw.execute(
            f"select to_jsonb(t) from ref.{kind} t join ref.ingredient i on i.id = t.ingredient_id "
            "where i.raw->'intake'->>'path' = %s", (item.path,)).fetchone()[0]
        not_figures = {"ingredient_id", "field_source", "description_ref"}
        if kind == "fermentable" and not item.fields.get("fermentability"):
            not_figures.add("fermentability")  # the column default, not a filled field
        filled_columns = {k for k, v in row.items() if v is not None and k not in not_figures}
        assert set(row["field_source"]) == filled_columns, item.path
        assert all(slug == "fixture-data-sheet" for k, slug in row["field_source"].items() if k != "min_boil_min")
        raw = rw.execute("select raw from ref.ingredient where raw->'intake'->>'path' = %s", (item.path,)).fetchone()[0]
        assert raw["intake"]["path"] == item.path
        assert raw["intake"]["text"] == item.text
        assert raw["intake"]["fields"] == item.fields
    crystal = rw.execute(
        "select field_source from ref.fermentable f join ref.ingredient i on i.id = f.ingredient_id "
        "where i.name = 'Fixture Crystal 120'").fetchone()[0]
    assert crystal["min_boil_min"] == "palmer-how-to-brew"


@pytest.mark.stack
def test_intake_fermentable_usable(rw):
    load_fixtures(rw)
    ingredient_id, role, description = rw.execute(
        "select f.ingredient_id, f.role, f.description from ref.fermentable f join ref.ingredient i "
        "on i.id = f.ingredient_id where i.name = 'Fixture Crystal 120'").fetchone()
    assert role == "crystal" and description
    level = rw.execute("select app.style_level('21A', %s, 'mash')", (ingredient_id,)).fetchone()[0]
    assert level["level"] is not None, level


@pytest.mark.stack
def test_hopline_loaders_leave_intake_rows(rw):
    files = {name: HOPLINE / f"hopline_{name}.json" for name in ("malts", "adjuncts", "hops", "yeasts")}
    if not all(p.exists() for p in files.values()) or not CATALOGUE.exists():
        pytest.skip("shared/rag-files is absent")
    load_fixtures(rw)
    before = intake_snapshot(rw)
    read = lambda p: _json.loads(p.read_text(encoding="utf-8"))  # noqa: E731
    malts.load(rw, malts.build(read(files["malts"]), read(CATALOGUE)))
    adjuncts.load(rw, adjuncts.build(read(files["adjuncts"])))
    fermentable_facts.load(rw, fermentable_facts.read())
    hops.load(rw, hops.build(read(files["hops"])))
    yeasts.load(rw, yeasts.build(read(files["yeasts"])))
    assert intake_snapshot(rw) == before


@pytest.mark.stack
def test_intake_rows_tagged(rw):
    load_fixtures(rw)
    vocab = tags.read_vocab()
    tags.load_vocab(rw, vocab)
    tags.derive_tags(rw, vocab)

    def tags_of(name):
        return {(facet, tag) for facet, tag in rw.execute(
            "select t.facet, t.name from ref.ingredient_tag it join ref.tag t on t.id = it.tag_id "
            "join ref.ingredient i on i.id = it.ingredient_id where i.name = %s", (name,))}

    hop = tags_of("Fixture Hop")
    assert {("origin", "US"), ("character", "citrus"), ("character", "pine")} <= hop
    assert ("family", "ale") in tags_of("Fixture Ale FA-1")
    assert ("family", "sour") in tags_of("Fixture Lacto LB-1")
    assert {("character", "caramel"), ("character", "dried-fruit")} <= tags_of("Fixture Crystal 120")
    flagged = rw.execute(
        "select count(*) from ref.ingredient_review r join ref.ingredient i on i.id = r.ingredient_id "
        "where i.raw ? 'intake'").fetchone()[0]
    assert flagged == 0


@pytest.mark.stack
def test_every_alias_resolves(rw):
    ingredients, loaded = load_fixtures(rw)
    for item in ingredients:
        if item.path not in loaded["ids"]:
            continue
        ingredient_id = loaded["ids"][item.path]
        for word in [item.fields["name"], *item.fields.get("aliases", [])]:
            found = [r[0] for r in rw.execute("select ingredient_id from app.resolve_ingredient(%s)", (word,))]
            assert found == [ingredient_id], (item.path, word, found)


@pytest.mark.stack
def test_alias_finding_something_else_rolls_back(rw):
    sources, ingredients = extra.read_folder(FIXTURES)
    for item in ingredients[:2]:  # the fermentable and the hop: --check refuses this, the load must too
        item.fields["aliases"] = ["zz shared alias"]
    with pytest.raises(RuntimeError, match="aliases"):
        extra.load(rw, sources, ingredients)


@pytest.mark.stack
def test_summary_counts(rw):
    ingredients, loaded = load_fixtures(rw)
    vocab = tags.read_vocab()
    tags.load_vocab(rw, vocab)
    tags.derive_tags(rw, vocab)
    s = extra.summary(rw, ingredients, loaded)
    assert s["ref_counts"] == dict(rw.execute("select kind, count(*) from ref.ingredient group by kind"))
    assert s["loaded"] == {"fermentable": 1, "hop": 1, "yeast": 2, "misc": 9}
    assert s["new_sources"] == ["fixture-data-sheet"]
    assert s["aliases_checked"] == 5 and s["flagged"] == []
    assert len(s["tagged"]) == 11  # everything but the two process aids
    assert len(s["waits_for_maths"]) == 3
    assert any("Fixture Lacto LB-1" in line for line in s["waits_for_maths"])
    assert any("Fixture Enzyme" in line and "changes the numbers (enzyme)" in line for line in s["waits_for_maths"])
    assert any("Fixture Fruit" in line and "decided with M6" in line for line in s["waits_for_maths"])
    assert len(s["waits"]) == 1 and "Fixture Vanilla Extract" in s["waits"][0] and "mL/L" in s["waits"][0]


@pytest.mark.stack
def test_main_loads_tags_and_prints_summary(rw, monkeypatch, capsys):
    class NoCommit:
        """The test connection, with commit, rollback and close turned off so the run stays rollbackable."""
        def __getattr__(self, name):
            return getattr(rw, name)
        def __setattr__(self, name, value):
            setattr(rw, name, value)
        def commit(self):
            pass
        def rollback(self):
            pass
        def close(self):
            pass
    monkeypatch.setattr(extra, "connect", lambda: NoCommit())
    assert extra.main([str(FIXTURES)]) == 0
    out = capsys.readouterr().out
    assert "loaded: fermentable 1, hop 1, yeast 2, misc 9" in out
    assert "waits (not loaded)" in out and "Fixture Vanilla Extract" in out
    assert "sources added: fixture-data-sheet" in out
    assert "waits for maths" in out and "Fixture Lacto LB-1" in out
    assert rw.execute("select count(*) from ref.ingredient where raw ? 'intake'").fetchone()[0] == 13


@pytest.mark.stack
def test_g10_counts_ignore_intake_rows(rw):
    """With the fixtures loaded, the filtered G10 queries still count the hopline catalogue only."""
    load_fixtures(rw)
    hops_n = rw.execute("select count(*) from ref.ingredient where kind = 'hop' and not raw ? 'intake'").fetchone()[0]
    ferm_n = rw.execute(
        "select count(*) from ref.fermentable f join ref.ingredient i on i.id = f.ingredient_id "
        "where not i.raw ? 'intake'"
    ).fetchone()[0]
    assert (hops_n, ferm_n) == (89, 81)
    assert rw.execute("select count(*) from ref.ingredient where kind = 'hop'").fetchone()[0] == 90


def spotcheck_statements(*headings):
    """The SQL under each named \\echo heading of the spot-check pack."""
    text = (REPO / "db" / "checks" / "ref_spotcheck.sql").read_text(encoding="utf-8")
    parts = text.split("\\echo '== ")[1:]
    found = {}
    for part in parts:
        title, _, body = part.partition(" ==")[0], None, part.partition("\n")[2]
        found[title] = body.split("\\echo")[0].strip().rstrip(";")
    return [found[h] for h in headings]


@pytest.mark.stack
def test_spotcheck_lists_intake_rows(rw):
    load_fixtures(rw)
    per_kind, with_source = spotcheck_statements(
        "Intake rows per kind (shared/ingredients/; 0 until a real item is added)", "Intake rows with their source"
    )
    assert dict(rw.execute(per_kind).fetchall()) == {"fermentable": 1, "hop": 1, "yeast": 2, "misc": 9}
    rows = rw.execute(with_source).fetchall()
    assert len(rows) == 13  # fermentable, hop, ale yeast, lacto culture, 9 misc
    assert {r[3] for r in rows} == {"fixture-data-sheet"} and {r[4] for r in rows} == {"test fixture"}
    assert all(r[5].startswith("tests/fixtures/ingredients/") for r in rows)


@pytest.mark.stack
def test_spotcheck_lists_intake_misc_rows(rw):
    load_fixtures(rw)
    (misc_rows,) = spotcheck_statements("Intake misc rows")
    rows = rw.execute(misc_rows).fetchall()
    assert len(rows) == 9
    by_name = {r[0]: r for r in rows}
    purpose, category, usages, time_min, dose, source, file = by_name["Fixture Coffee Beans"][1:]
    assert (purpose, category, usages, time_min) == ("flavour", "coffee", ["secondary"], 2880)
    assert source == "fixture-data-sheet" and file.startswith("tests/fixtures/ingredients/misc/")
    assert by_name["Fixture No Dose"][5] is None  # no dose


@pytest.mark.stack
def test_misc_rows_load(rw):
    """Fixtures load as misc rows: figures, field_source, own dose and time per form (A14, A15)."""
    ingredients, loaded = load_fixtures(rw)

    def row(name):
        return rw.execute(
            "select m.purpose, m.category, m.usages, m.time_min, m.dose_g_per_l, m.description, m.field_source "
            "from ref.misc m join ref.ingredient i on i.id = m.ingredient_id where i.name = %s", (name,)).fetchone()

    spice = row("Fixture Spice")
    assert spice[:4] == ("flavour", "spice", ["whirlpool", "secondary"], None)
    assert (float(spice[4].lower), float(spice[4].upper)) == (0.5, 1.0)
    assert spice[6] == {"purpose": "fixture-data-sheet", "category": "fixture-data-sheet",
                        "usages": "fixture-data-sheet", "dose_g_per_l": "fixture-data-sheet",
                        "description": "fixture-data-sheet"}
    assert row("Fixture No Dose")[4] is None and "dose_g_per_l" not in row("Fixture No Dose")[6]  # A15
    beans, brew = row("Fixture Coffee Beans"), row("Fixture Coffee Cold Brew")  # A14: two rows, own dose and time
    assert (beans[3], float(beans[4].lower)) == (2880, 3.0)
    assert (brew[3], float(brew[4].lower), brew[2]) == (960, 6.0, ["packaging"])
    # a process aid has no flavour descriptors; the fruit's sugar stays in raw.intake only
    assert row("Fixture Irish Moss")[:2] == ("process", "fining") and row("Fixture Enzyme")[:2] == ("process", "enzyme")
    assert row("Fixture Fruit")[1] == "fruit"
    sugar = rw.execute("select raw->'intake'->'fields'->>'sugar_pct' from ref.ingredient where name = 'Fixture Fruit'").fetchone()[0]
    assert sugar == "12" or sugar == "12.0"


@pytest.mark.stack
def test_liquid_extract_is_not_loaded(rw):
    ingredients, loaded = load_fixtures(rw)
    assert rw.execute("select count(*) from ref.ingredient where name = 'Fixture Vanilla Extract'").fetchone()[0] == 0
    assert all("vanilla-extract" not in path for path in loaded["ids"])


@pytest.mark.stack
def test_reload_clears_a_misc_dose(rw, work):
    def load_work():
        sources, ingredients = extra.read_folder(work)
        return extra.load(rw, sources, ingredients)

    load_work()
    q = ("select m.dose_g_per_l, m.field_source from ref.misc m join ref.ingredient i on i.id = m.ingredient_id "
         "where i.name = 'Fixture Spice'")
    assert rw.execute(q).fetchone()[0] is not None
    edit(work, "misc/fixture-spice.toml", "dose_g_per_l = [0.5, 1.0]", "dose_g_per_l = []")
    edit(work, "misc/fixture-spice.toml", 'dose_g_per_l_ref = "fixture sheet p. 5"', 'dose_g_per_l_ref = ""')
    load_work()
    dose, field_source = rw.execute(q).fetchone()
    assert dose is None and "dose_g_per_l" not in field_source
