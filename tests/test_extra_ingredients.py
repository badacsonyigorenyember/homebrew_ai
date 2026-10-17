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
    assert len(ingredients) == 4
    assert "fixture-data-sheet" not in known.source_notes  # it comes from sources/, not from ref


@pytest.mark.parametrize("kind, fixture", [
    ("fermentable", "fermentable/fixture-crystal.toml"),
    ("hop", "hop/fixture-hop.toml"),
    ("yeast", "yeast/fixture-ale.toml"),
    ("yeast", "yeast/fixture-lacto.toml"),
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


def test_misc_file_refused(known, work):
    (work / "misc").mkdir()
    misc = work / "misc" / "honey.toml"
    misc.write_text(toml_text({"kind": "misc", "name": "Honey"}))
    errors = check_folder(work, known)
    assert any(e.startswith(f"{shown(misc)}: kind") and "misc arrives in s9" in e for e in errors), errors


def test_all_errors_reported(known, work):
    one = edit(work, "hop/fixture-hop.toml", 'purpose = "dual"', 'purpose = "both"')
    two = edit(work, "yeast/fixture-ale.toml", 'type = "ale"', 'type = "wine"')
    errors = check_folder(work, known)
    assert any(e.startswith(shown(one)) for e in errors)
    assert any(e.startswith(shown(two)) for e in errors)
