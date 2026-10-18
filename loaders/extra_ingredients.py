"""Ingredient intake (s8-ingredient-intake, s9-misc-extras): add a fermentable, hop, yeast or misc by filling a file.

Folder layout (default shared/ingredients/, one TOML file per ingredient, one per new source):

    fermentable/<name>.toml   hop/<name>.toml   yeast/<name>.toml   misc/<name>.toml
    sources/<slug>.toml
    _templates/               the commented templates to copy (never read by this module)

The file format (keys, units, which are required) is in the templates and in the plan,
docs/work/s8-ingredient-intake/plan.md. "" or [] in a file means "not filled".

This module reads the folder, checks every file, and loads it. check_files returns ALL problems,
one text each, in the form "<file>: <field>: <problem>"; an empty list means the set is good. It
looks only at the files, the tag vocabulary and the hopline product maps. The checks against the
database are known_from_db, check_aliases and orphans. load writes the sources and each kind (one
row per ingredient, re-loading a file overwrites it, aliases included), checks that every alias
and name finds its product only, and main ties it together on the command line.

Usage (from the repo root):

    .venv/bin/python -m loaders.extra_ingredients --check [folder]
    .venv/bin/python -m loaders.extra_ingredients [folder]

--check runs every check, prints each problem (or "ok: ..."), and writes nothing: its connection is
read only and always rolled back. Without it, a clean set is loaded, tagged (loaders.tags) and
committed; any problem stops the run before anything is written. The folder defaults to
shared/ingredients.
"""

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
import tomllib

from loaders import adjunct_products, hop_products, malt_products, tags, yeast_products
from psycopg.types.json import Jsonb

from loaders.db import connect, source_id, upsert_ingredient
from loaders.common import name_key, num, to_range
from loaders.fermentable_facts import BOIL_SOURCE, ENZYME, ROLES
from loaders.tags import descriptor_tag

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROOT = REPO_ROOT / "shared" / "ingredients"

KINDS = ("fermentable", "hop", "yeast", "misc")
FERMENTABILITY = {"full", "normal", "none"}
PURPOSES = {"aroma", "bittering", "dual"}
YEAST_TYPES = {"ale", "lager", "kveik", "brett", "lacto", "pedio"}
SOUR_TYPES = {"lacto", "pedio"}  # a souring culture's sheet usually states no attenuation
FLOCCULATION = {"very low", "low", "medium low", "medium", "medium high", "high", "very high"}
FORMS = {"dry", "liquid"}
MISC_PURPOSES = {"flavour", "process"}
FLAVOUR_CATEGORIES = {"spice", "herb", "fruit", "wood", "coffee", "cacao", "vanilla", "smoke", "other"}
PROCESS_CATEGORIES = {"fining", "nutrient", "enzyme", "acid", "other-process"}
CHANGES_THE_NUMBERS = {"enzyme", "acid"}  # these alter gravity or pH, so they wait for the maths
MISC_USAGES = ["mash", "boil", "whirlpool", "ferment", "secondary", "packaging"]  # the order of a brew day

# Every key of a kind's template, apart from the *_ref and *_source keys that follow from them.
COMMON_KEYS = ["kind", "name", "producer", "source", "description", "description_ref", "aliases", "descriptors"]
KIND_KEYS = {
    "fermentable": ["extract_dbfg_pct", "ebc", "role", "fermentability", "max_pct", "enzyme_activity", "min_boil_min"],
    "hop": ["alpha_pct", "purpose", "origins", "total_oil_ml_100g"],
    "yeast": ["type", "temp_c", "attenuation_pct", "flocculation", "form", "alcohol_tolerance_pct", "product_id"],
    "misc": ["purpose", "category", "usages", "time_min", "dose_g_per_l", "dose_ml_per_l", "sugar_pct"],
}
# Figures that need a page or URL (`<field>_ref`) when filled; description is checked for all kinds.
FIGURES = {
    "fermentable": ["extract_dbfg_pct", "ebc", "max_pct", "enzyme_activity", "min_boil_min"],
    "hop": ["alpha_pct", "total_oil_ml_100g"],
    "yeast": ["temp_c", "attenuation_pct", "alcohol_tolerance_pct"],
    "misc": ["time_min", "dose_g_per_l", "dose_ml_per_l", "sugar_pct"],
}
SOURCE_KEYS = ["slug", "title", "edition", "publisher", "url", "licence"]


@dataclass
class IntakeFile:
    """One file of the folder: where it is, what it says, and whether it could be read."""

    path: str  # as printed in messages: relative to the repo root when inside it
    stem: str  # the file name without .toml
    folder: str  # "fermentable", "hop", "yeast", "misc", "sources", or a folder that is not allowed
    text: str  # the file as written
    fields: dict = field(default_factory=dict)  # parsed; {} when the file has a syntax error
    syntax_error: str | None = None


@dataclass
class Known:
    """What the checks compare a file with."""

    source_notes: dict = field(default_factory=dict)  # slug in ref.source -> its notes (from the DB)
    origins: set = field(default_factory=set)  # origin tags of the vocabulary file
    characters: set = field(default_factory=set)  # character tag names
    synonyms: dict = field(default_factory=dict)  # name_key(word) -> character tag
    loader_keys: set = field(default_factory=set)  # (kind, producer_key, name_key) the hopline loaders write
    # (kind, producer_key, name_key) -> {"label", "intake" (bool), "path"} (from the DB)
    db_rows: dict = field(default_factory=dict)


def shown_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_folder(root: Path = DEFAULT_ROOT) -> tuple[list[IntakeFile], list[IntakeFile]]:
    """(source files, ingredient files) under root, each sorted by path. Nothing is checked yet."""
    root = Path(root)
    sources, ingredients = [], []
    for folder in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("_")):
        for path in sorted(folder.glob("*.toml")):
            text = path.read_text(encoding="utf-8")
            item = IntakeFile(shown_path(path), path.stem, folder.name, text)
            try:
                item.fields = tomllib.loads(text)
            except tomllib.TOMLDecodeError as e:
                item.syntax_error = str(e)
            (sources if folder.name == "sources" else ingredients).append(item)
    return sources, ingredients


def loader_keys() -> set:
    """The (kind, producer_key, name_key) of every ingredient the hopline loaders write."""
    keys = set()
    for producer, _, name in malt_products.PRODUCTS.values():
        keys.add(("fermentable", name_key(producer), name_key(name)))
    for name, _, _ in adjunct_products.PRODUCTS.values():
        keys.add(("fermentable", "", name_key(name)))
    for name in adjunct_products.PALMER_ONLY:
        keys.add(("fermentable", "", name_key(name)))
    for name in hop_products.HOPS.values():
        keys.add(("hop", "", name_key(name)))
    for producer, _, name in yeast_products.YEASTS.values():
        keys.add(("yeast", name_key(producer), name_key(name)))
    return keys


def known_from_files(vocab: dict) -> Known:
    """The vocabulary and product-map parts of Known (no database needed)."""
    return Known(
        origins={t["name"] for t in vocab["tag"] if t["facet"] == "origin"},
        characters={t["name"] for t in vocab["tag"] if t["facet"] == "character"},
        synonyms=dict(vocab["synonyms"]),
        loader_keys=loader_keys(),
    )


def known_from_db(conn, known: Known) -> Known:
    """Fill the database parts of Known: ref.source slugs with their notes, ref.ingredient rows."""
    known.source_notes = {slug: notes for slug, notes in conn.execute("select slug, notes from ref.source")}
    known.db_rows = {}
    rows = conn.execute(
        "select kind, producer_key, name_key, producer, name, raw ? 'intake', raw->'intake'->>'path' "
        "from ref.ingredient"
    )
    for kind, producer_key, key, producer, name, is_intake, path in rows:
        known.db_rows[(kind, producer_key, key)] = {
            "label": f"{producer} {name}".strip(),
            "intake": is_intake,
            "path": path,
        }
    return known


# ---------------------------------------------------------------- small checks on one value


class Problems:
    """The problems found in one file, as "<file>: <field>: <problem>" texts."""

    def __init__(self, path: str):
        self.path = path
        self.errors: list[str] = []

    def add(self, field_name: str, problem: str):
        self.errors.append(f"{self.path}: {field_name}: {problem}")


def is_blank(value) -> bool:
    return value is None or value == "" or value == []


def is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def need(p: Problems, f: dict, key: str) -> bool:
    """True when f[key] is filled; otherwise reports it as required."""
    if is_blank(f.get(key)):
        p.add(key, "required, missing or empty")
        return False
    return True


def check_text(p: Problems, f: dict, key: str):
    if key in f and not is_blank(f[key]) and not isinstance(f[key], str):
        p.add(key, "must be text")


def check_choice(p: Problems, f: dict, key: str, allowed: set):
    value = f.get(key)
    if not is_blank(value) and value not in allowed:
        p.add(key, f"{value!r} is not one of {sorted(allowed)}")


def check_number(p: Problems, f: dict, key: str, low: float, high: float):
    value = f.get(key)
    if is_blank(value):
        return
    if not is_number(value):
        p.add(key, "must be a number")
    elif not low <= value <= high:
        p.add(key, f"{value} is outside {low} to {high}")


def check_range(p: Problems, f: dict, key: str, low: float, high: float):
    """A [low, high] pair of numbers within low..high, low not above high."""
    value = f.get(key)
    if is_blank(value):
        return
    if not (isinstance(value, list) and len(value) == 2 and all(is_number(v) for v in value)):
        p.add(key, "must be a range [low, high] of two numbers")
    elif value[0] > value[1]:
        p.add(key, f"range low {value[0]} is greater than high {value[1]}")
    elif value[0] < low or value[1] > high:
        p.add(key, f"{value} is outside {low} to {high}")


def check_ref(p: Problems, f: dict, key: str, why: str = "is filled"):
    """A filled figure needs a page or URL in `<key>_ref`."""
    if is_blank(f.get(f"{key}_ref")):
        p.add(f"{key}_ref", f"needed, because {key} {why}")


# ---------------------------------------------------------------- one function per kind


def check_fermentable(p: Problems, f: dict):
    need(p, f, "producer")
    need(p, f, "extract_dbfg_pct")
    need(p, f, "role")
    check_number(p, f, "extract_dbfg_pct", 0, 100)
    check_range(p, f, "ebc", 0, 2000)
    check_choice(p, f, "role", ROLES)
    check_choice(p, f, "fermentability", FERMENTABILITY)
    check_number(p, f, "max_pct", 0, 100)
    check_choice(p, f, "enzyme_activity", ENZYME)
    if not is_blank(f.get("min_boil_min")) and not (is_number(f["min_boil_min"]) and 60 <= f["min_boil_min"] <= 120):
        p.add("min_boil_min", "must be a number of minutes from 60 to 120")
    if f.get("fermentability") not in (None, "", "normal"):
        check_ref(p, f, "fermentability", f"is {f['fermentability']!r}, not 'normal'")


def check_hop(p: Problems, f: dict):
    need(p, f, "alpha_pct")
    need(p, f, "purpose")
    need(p, f, "origins")
    need(p, f, "descriptors")
    check_range(p, f, "alpha_pct", 0, 100)
    check_choice(p, f, "purpose", PURPOSES)
    check_range(p, f, "total_oil_ml_100g", 0, 100)


def check_yeast(p: Problems, f: dict):
    need(p, f, "producer")
    need(p, f, "type")
    need(p, f, "temp_c")
    need(p, f, "descriptors")
    if f.get("type") not in SOUR_TYPES:
        need(p, f, "attenuation_pct")
    check_choice(p, f, "type", YEAST_TYPES)
    check_range(p, f, "temp_c", -20, 100)
    check_range(p, f, "attenuation_pct", 0, 100)
    check_choice(p, f, "flocculation", FLOCCULATION)
    check_choice(p, f, "form", FORMS)
    check_number(p, f, "alcohol_tolerance_pct", 0, 100)
    check_text(p, f, "product_id")


def check_misc(p: Problems, f: dict):
    need(p, f, "purpose")
    need(p, f, "category")
    need(p, f, "usages")
    check_choice(p, f, "purpose", MISC_PURPOSES)
    purpose, category = f.get("purpose"), f.get("category")
    categories = {"flavour": FLAVOUR_CATEGORIES, "process": PROCESS_CATEGORIES}
    if purpose in categories and not is_blank(category) and category not in categories[purpose]:
        p.add("category", f"{category!r} is not a {purpose} category; use one of {sorted(categories[purpose])}")
    elif purpose not in categories and not is_blank(category) and category not in FLAVOUR_CATEGORIES | PROCESS_CATEGORIES:
        p.add("category", f"{category!r} is not one of {sorted(FLAVOUR_CATEGORIES | PROCESS_CATEGORIES)}")
    usages = f.get("usages")
    if isinstance(usages, list):
        for usage in usages:
            if usage not in MISC_USAGES:
                p.add("usages", f"{usage!r} is not one of {MISC_USAGES}")
    elif not is_blank(usages):
        p.add("usages", "must be a list of usages")
    minutes = f.get("time_min")
    if not is_blank(minutes) and not (isinstance(minutes, int) and not isinstance(minutes, bool) and minutes >= 0):
        p.add("time_min", "must be a whole number of minutes, 0 or more")
    check_range(p, f, "dose_g_per_l", 0, 1000)
    check_range(p, f, "dose_ml_per_l", 0, 1000)
    if not is_blank(f.get("dose_g_per_l")) and not is_blank(f.get("dose_ml_per_l")):
        p.add("dose_ml_per_l", "fill dose_g_per_l or dose_ml_per_l, not both")
    if not is_blank(f.get("sugar_pct")):
        if category != "fruit":
            p.add("sugar_pct", "only a fruit has a sugar_pct")
        check_number(p, f, "sugar_pct", 0, 100)
    if purpose == "flavour":
        need(p, f, "descriptors")
    elif purpose == "process" and not is_blank(f.get("descriptors")):
        p.add("descriptors", "a process aid has no flavour; leave descriptors empty")


def misc_waits(item: IntakeFile) -> str | None:
    """Why a misc file that passes the checks is not (fully) used yet, or None."""
    f = item.fields
    if item.folder != "misc" or item.syntax_error:
        return None
    if not is_blank(f.get("dose_ml_per_l")):
        return "liquid extract dosed in mL/L, not loaded until a later work item adds mL/L"
    if f.get("category") in CHANGES_THE_NUMBERS:
        return f"changes the numbers ({f['category']}): waits for maths"
    if f.get("category") == "fruit" and not is_blank(f.get("sugar_pct")):
        return "fruit sugar: waits for maths; TODO: fruit as a fermentable is decided with M6"
    return None


KIND_CHECKS = {"fermentable": check_fermentable, "hop": check_hop, "yeast": check_yeast, "misc": check_misc}


def check_source(item: IntakeFile) -> list[str]:
    p = Problems(item.path)
    f = item.fields
    if item.syntax_error:
        p.add("toml", item.syntax_error)
        return p.errors
    for key in f:
        if key not in SOURCE_KEYS:
            p.add(key, "not a key of the source template")
    for key in ("slug", "title", "edition"):
        need(p, f, key)
    for key in SOURCE_KEYS:
        check_text(p, f, key)
    if f.get("slug") and f["slug"] != item.stem:
        p.add("slug", f"{f['slug']!r} must equal the file name {item.stem!r}")
    return p.errors


def check_ingredient(item: IntakeFile, known: Known, source_slugs: set) -> list[str]:
    """Every problem in one ingredient file that needs no other file."""
    p = Problems(item.path)
    f = item.fields
    if item.syntax_error:
        p.add("toml", item.syntax_error)
        return p.errors
    kind = item.folder
    if kind not in KINDS:
        p.add("kind", f"folder {kind!r} is not one of {list(KINDS)}")
        return p.errors
    if f.get("kind") != kind:
        p.add("kind", f"must be {kind!r}, the name of the folder (it is {f.get('kind')!r})")

    figure_keys = KIND_KEYS[kind] + ["description"]
    allowed = set(COMMON_KEYS + KIND_KEYS[kind]) | {f"{k}_ref" for k in figure_keys}
    for key in f:
        if key not in allowed and not (key.endswith("_source") and key[: -len("_source")] in figure_keys):
            p.add(key, f"not a key of the {kind} template")

    for key in ("name", "source", "description", "description_ref"):
        need(p, f, key)
    for key in ("name", "producer", "source", "description", "description_ref"):
        check_text(p, f, key)
    for key in [k for k in f if k.endswith("_ref")]:
        check_text(p, f, key)

    for key in ("aliases", "descriptors", "origins"):
        value = f.get(key, [])
        if not isinstance(value, list) or not all(isinstance(w, str) and w.strip() for w in value):
            p.add(key, "must be a list of words")
    KIND_CHECKS[kind](p, f)

    for key in FIGURES[kind]:
        if not is_blank(f.get(key)):
            check_ref(p, f, key)

    for word in f.get("descriptors", []) if isinstance(f.get("descriptors"), list) else []:
        if isinstance(word, str) and descriptor_tag(word, known.synonyms, known.characters) is None:
            p.add("descriptors", f"{word!r} is neither a character tag nor a word of the vocabulary file")
    for origin in f.get("origins", []) if isinstance(f.get("origins"), list) else []:
        if origin not in known.origins:
            p.add("origins", f"{origin!r} is not an origin tag of the vocabulary file")

    slugs = [("source", f.get("source"))] + [(k, v) for k, v in f.items() if k.endswith("_source")]
    for key, slug in slugs:
        if isinstance(slug, str) and slug and slug not in source_slugs:
            p.add(key, f"{slug!r} is in neither ref.source nor sources/")
    return p.errors


def product_key(item: IntakeFile):
    """(kind, producer_key, name_key) of a readable ingredient file, else None."""
    f = item.fields
    if item.folder not in KINDS or item.syntax_error or not isinstance(f.get("name"), str):
        return None
    producer = f.get("producer") if isinstance(f.get("producer"), str) else ""
    return (item.folder, name_key(producer), name_key(f["name"]))


def check_files(sources: list[IntakeFile], ingredients: list[IntakeFile], known: Known) -> list[str]:
    """All problems of the whole set, file by file, then the checks that compare files."""
    errors = []
    source_slugs = set(known.source_notes) | {s.stem for s in sources}
    for item in sources:
        errors += check_source(item)
        slug = item.fields.get("slug") or item.stem
        if slug in known.source_notes and not (known.source_notes[slug] or "").startswith("intake:"):
            errors.append(f"{item.path}: slug: {slug!r} is already a source in ref.source (not from the intake); "
                          "use it as `source` in the ingredient file instead")
    for item in ingredients:
        errors += check_ingredient(item, known, source_slugs)

    seen = {}
    for item in ingredients:
        key = product_key(item)
        if key is None:
            continue
        label = f"{item.fields.get('producer') or ''} {item.fields['name']}".strip()
        if key in known.loader_keys:
            errors.append(f"{item.path}: name: {label} is loaded by another loader")
        row = known.db_rows.get(key)
        if row and not row["intake"]:
            errors.append(f"{item.path}: name: clashes with {row['label']} loaded by another loader")
        if key in seen:
            errors.append(f"{item.path}: name: {label} is the same product as {seen[key]}")
        seen.setdefault(key, item.path)
    return errors


# ---------------------------------------------------------------- checks that need the database


def alias_words(conn, text: str) -> tuple:
    """The words of a text as the resolver compares them: sorted."""
    return tuple(sorted(conn.execute("select app.ingredient_words(%s)", (text,)).fetchone()[0]))


def alias_matches(conn, query: tuple, alias: tuple, kind: str) -> bool:
    """Does a query with these (sorted) words find an alias of a product of this kind? The same
    rule as app.resolve_ingredient: equal words, or equal once the kind's word is removed."""
    kind_words = {w for (w,) in conn.execute("select word from app.ingredient_kind_word() where kind = %s", (kind,))}
    return query == alias or tuple(w for w in query if w not in kind_words) == alias


def check_aliases(conn, ingredients: list[IntakeFile]) -> list[str]:
    """An alias must name this product only: not another file's alias, not another product's name
    (as the resolver reads names), not an alias already stored for another ingredient."""
    errors = []
    seen = []  # (words, kind, file) of every alias met so far
    names = []  # (sorted words of a product's name, file): an alias must not take it over
    for item in ingredients:
        if product_key(item) is not None:
            names.append((alias_words(conn, item.fields["name"]), item))
    for item in ingredients:
        own = product_key(item)
        aliases = item.fields.get("aliases")
        if own is None or not isinstance(aliases, list):
            continue
        for alias in aliases:
            if not isinstance(alias, str) or not alias.strip():
                continue
            words = alias_words(conn, alias)
            if not words:
                errors.append(f"{item.path}: aliases: {alias!r} has no words")
                continue
            others = {path for w, kind, path in seen if path != item.path
                      and (alias_matches(conn, words, w, kind) or alias_matches(conn, w, words, item.folder))}
            for other in sorted(others):
                errors.append(f"{item.path}: aliases: {alias!r} is also an alias in {other}")
            seen.append((words, item.folder, item.path))
            for w, named in names:
                if named is not item and (alias_matches(conn, words, w, named.folder)
                                          or alias_matches(conn, w, words, named.folder)):
                    errors.append(f"{item.path}: aliases: {alias!r} is the name of {named.path}")
            found = conn.execute(
                "select i.kind, i.producer_key, i.name_key, i.producer, i.name "
                "from app.resolve_ingredient_by_name(%s) r join ref.ingredient i on i.id = r.ingredient_id",
                (alias,),
            ).fetchall()
            for kind, producer_key, key, producer, name in found:
                if (kind, producer_key, key) != own:
                    errors.append(f"{item.path}: aliases: {alias!r} already finds {f'{producer} {name}'.strip()}")
            stored = set()
            for kind, producer_key, key, producer, name, stored_alias in conn.execute(
                "select i.kind, i.producer_key, i.name_key, i.producer, i.name, a.alias from ref.ingredient_alias a "
                "join ref.ingredient i on i.id = a.ingredient_id"
            ).fetchall():
                if alias_matches(conn, words, alias_words(conn, stored_alias), kind):
                    stored.add((kind, producer_key, key, producer, name))
            for kind, producer_key, key, producer, name in stored:
                if (kind, producer_key, key) != own:
                    errors.append(f"{item.path}: aliases: {alias!r} is already an alias of {f'{producer} {name}'.strip()}")
    return errors


def orphans(known: Known, ingredients: list[IntakeFile]) -> list[str]:
    """Intake rows in the database that no file backs any more (reported, never deleted)."""
    keys = {product_key(item) for item in ingredients}
    return [
        f"{row['label']} ({row['path']})"
        for key, row in sorted(known.db_rows.items())
        if row["intake"] and key not in keys
    ]


# ---------------------------------------------------------------- command line


def run_checks(conn, root: Path):
    """(errors, sources, ingredients, orphan list) for a folder; reads the database only."""
    sources, ingredients = read_folder(root)
    known = known_from_db(conn, known_from_files(tags.read_vocab()))
    errors = check_files(sources, ingredients, known) + check_aliases(conn, ingredients)
    return errors, sources, ingredients, orphans(known, ingredients)


# ---------------------------------------------------------------- the load


def load_source(conn, item: IntakeFile) -> int:
    """Upsert a ref.source row on its slug; notes says which file it came from."""
    f = item.fields
    return conn.execute(
        """
        insert into ref.source (slug, title, edition, publisher, licence, url, notes)
        values (%s, %s, %s, %s, %s, %s, %s)
        on conflict (slug) do update
           set title = excluded.title, edition = excluded.edition, publisher = excluded.publisher,
               licence = excluded.licence, url = excluded.url, notes = excluded.notes
        returning id
        """,
        (f["slug"], f["title"], f["edition"], f.get("publisher") or None, f.get("licence") or None,
         f.get("url") or None, f"intake: {item.path}"),
    ).fetchone()[0]


def write_kind_row(conn, table: str, ingredient_id: int, values: dict, field_source: dict):
    """Insert or update the one row of ref.fermentable / ref.hop / ref.yeast for an ingredient."""
    columns = list(values) + ["field_source"]
    params = [ingredient_id] + list(values.values()) + [Jsonb(field_source)]
    conn.execute(
        f"insert into {table} (ingredient_id, {', '.join(columns)}) "
        f"values ({', '.join(['%s'] * (len(columns) + 1))}) "
        f"on conflict (ingredient_id) do update set {', '.join(f'{c} = excluded.{c}' for c in columns)}",
        params,
    )


def rng(value):
    """A [low, high] list from a file as a numrange; "" or [] as None."""
    return to_range(*value) if value else None


def field_sources(f: dict, values: dict, skip=()) -> dict:
    """{column: slug} for every filled column: its `<column>_source` if the file has one, else `source`.
    Columns ending in _ref hold a page, not a figure, and are left out, as are the ones in skip."""
    return {
        column: f.get(f"{column}_source") or f["source"]
        for column, value in values.items()
        if value is not None and not column.endswith("_ref") and column not in skip
    }


def write_ingredient(conn, item: IntakeFile, kind: str, table: str, values: dict, sources: dict) -> int:
    """The ref.ingredient row, its kind row (every column, so a cleared field becomes NULL again) and its aliases."""
    f = item.fields
    raw = {"intake": {"path": item.path, "text": item.text, "fields": f}}
    ingredient_id = upsert_ingredient(conn, kind, f["name"], f.get("producer") or "", source_id(conn, f["source"]), raw)
    write_kind_row(conn, table, ingredient_id, values, sources)
    conn.execute("delete from ref.ingredient_alias where ingredient_id = %s", (ingredient_id,))
    for alias in f.get("aliases", []):
        conn.execute(
            "insert into ref.ingredient_alias (ingredient_id, alias) values (%s, %s) on conflict do nothing",
            (ingredient_id, alias),
        )
    return ingredient_id


def load_fermentable(conn, item: IntakeFile) -> int:
    f = item.fields
    values = {
        "extract_dbfg_pct": num(f["extract_dbfg_pct"]),
        "ebc": rng(f.get("ebc")),
        "role": f["role"],
        "fermentability": f.get("fermentability") or "normal",
        "max_pct": num(f.get("max_pct")),
        "enzyme_activity": f.get("enzyme_activity") or None,
        "min_boil_min": f.get("min_boil_min") or 60,
        "description": f["description"],
        "description_ref": f["description_ref"],
    }
    # fermentability has a column default, so it counts as a filled field only when the file sets it
    sources = field_sources(f, values, skip=() if f.get("fermentability") else ("fermentability",))
    if not f.get("min_boil_min"):
        sources["min_boil_min"] = BOIL_SOURCE  # the rule fermentable_facts applies to every fermentable
    return write_ingredient(conn, item, "fermentable", "ref.fermentable", values, sources)


def load_hop(conn, item: IntakeFile) -> int:
    f = item.fields
    values = {
        "alpha_pct": rng(f["alpha_pct"]),
        "purpose": f["purpose"],
        "origins": f["origins"],
        "total_oil_ml_100g": rng(f.get("total_oil_ml_100g")),
    }
    return write_ingredient(conn, item, "hop", "ref.hop", values, field_sources(f, values))


def load_yeast(conn, item: IntakeFile) -> int:
    f = item.fields
    values = {
        "product_id": f.get("product_id") or None,
        "type": f["type"],
        "form": f.get("form") or None,
        "attenuation_pct": rng(f.get("attenuation_pct")),
        "temp_c": rng(f["temp_c"]),
        "flocculation": f.get("flocculation") or None,
        "alcohol_tolerance_pct": num(f.get("alcohol_tolerance_pct")),
    }
    return write_ingredient(conn, item, "yeast", "ref.yeast", values, field_sources(f, values))


LOADERS = {"fermentable": load_fermentable, "hop": load_hop, "yeast": load_yeast}


def load(conn, sources: list[IntakeFile], ingredients: list[IntakeFile]) -> dict:
    """Write the sources, then each kind; then check that every alias finds its product only.

    Returns {"counts": {kind: files loaded}, "new_sources": [slug], "aliases": n, "ids": {path: id}}.
    Raises (so the caller rolls back) when an alias finds anything else.
    """
    existing = {slug for (slug,) in conn.execute("select slug from ref.source")}
    new_sources = [s.fields["slug"] for s in sources if s.fields["slug"] not in existing]
    for item in sources:
        load_source(conn, item)
    counts = {kind: 0 for kind in LOADERS}
    ids = {}
    ingredients = [i for i in ingredients if i.folder in LOADERS]  # misc has no loader yet
    for kind in LOADERS:
        for item in ingredients:
            if item.folder == kind:
                ids[item.path] = LOADERS[kind](conn, item)
                counts[kind] += 1
    aliases = 0
    for item in ingredients:
        for alias in item.fields.get("aliases", []):
            found = [row[0] for row in conn.execute("select ingredient_id from app.resolve_ingredient(%s)", (alias,))]
            if found != [ids[item.path]]:
                raise RuntimeError(f"{item.path}: aliases: {alias!r} finds ingredient ids {found}, not only {ids[item.path]}")
            aliases += 1
    for item in ingredients:  # an alias must not take over another product's name either
        for ingredient_id, rule in conn.execute("select ingredient_id, rule from app.resolve_ingredient(%s)", (item.fields["name"],)):
            if rule == "alias" and ingredient_id != ids[item.path]:
                raise RuntimeError(f"{item.path}: name: {item.fields['name']!r} finds ingredient id {ingredient_id} by an alias")
    return {"counts": counts, "new_sources": new_sources, "aliases": aliases, "ids": ids}


def summary(conn, ingredients: list[IntakeFile], loaded: dict, orphan_list: list[str] | None = None) -> dict:
    """What the run did, for the printout (R9). Call after the tagger has run."""
    ids = loaded["ids"]
    by_id = {ids[i.path]: i for i in ingredients if i.path in ids}
    tagged, flagged = [], []
    for ingredient_id, item in by_id.items():
        label = f"{item.fields.get('producer') or ''} {item.fields['name']}".strip()
        reasons = [r for (r,) in conn.execute("select reason from ref.ingredient_review where ingredient_id = %s", (ingredient_id,))]
        n_tags = conn.execute("select count(*) from ref.ingredient_tag where ingredient_id = %s", (ingredient_id,)).fetchone()[0]
        if reasons:
            flagged.append((label, reasons))
        elif n_tags:
            tagged.append(label)
        else:
            flagged.append((label, ["no tags derived"]))
    waits = [
        f"{i.fields.get('producer') or ''} {i.fields['name']}".strip()
        for i in ingredients
        if i.folder == "yeast" and i.fields.get("type") in SOUR_TYPES
    ]
    return {
        "loaded": loaded["counts"],
        "new_sources": loaded["new_sources"],
        "tagged": tagged,
        "flagged": flagged,
        "orphans": orphan_list or [],
        "aliases_checked": loaded["aliases"],
        "waits_for_maths": waits,
        "ref_counts": dict(conn.execute("select kind, count(*) from ref.ingredient group by kind order by kind")),
    }


def print_summary(s: dict):
    loaded = s["loaded"]
    print(f"loaded: fermentable {loaded['fermentable']}, hop {loaded['hop']}, yeast {loaded['yeast']}")
    print(f"sources added: {', '.join(s['new_sources']) or 'none'}")
    print(f"tagged: {len(s['tagged'])}; flagged for review: {len(s['flagged'])}")
    for label, reasons in s["flagged"]:
        print(f"  flagged {label}: {'; '.join(reasons)}")
    for line in s["orphans"]:
        print(f"no file backs this intake row: {line}")
    print(f"aliases checked: {s['aliases_checked']}")
    for label in s["waits_for_maths"]:
        print(f"waits for maths (souring culture, no model yet): {label}")
    print("ref.ingredient per kind: " + ", ".join(f"{k} {n}" for k, n in s["ref_counts"].items()))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m loaders.extra_ingredients", description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true", help="check the files and write nothing")
    parser.add_argument("path", nargs="?", default=str(DEFAULT_ROOT), help="intake folder (default shared/ingredients)")
    args = parser.parse_args(argv)

    conn = connect()
    try:
        conn.read_only = args.check
        errors, sources, ingredients, orphan_list = run_checks(conn, Path(args.path))
        if errors:
            for error in errors:
                print(error)
            print(f"{len(errors)} problem(s); nothing was written")
            return 1
        count = {kind: sum(1 for i in ingredients if i.folder == kind) for kind in KINDS}
        if args.check:
            print(f"ok: {len(sources) + len(ingredients)} files (fermentable {count['fermentable']}, "
                  f"hop {count['hop']}, yeast {count['yeast']}, misc {count['misc']}, sources {len(sources)})")
            for item in ingredients:
                reason = misc_waits(item)
                if reason:
                    print(f"waits: {item.path}: {reason}")
            for line in orphan_list:
                print(f"no file backs this intake row: {line}")
            return 0
        loaded = load(conn, sources, ingredients)
        vocab = tags.read_vocab()
        tags.load_vocab(conn, vocab)
        tags.derive_tags(conn, vocab)
        print_summary(summary(conn, ingredients, loaded, orphan_list))
        conn.commit()
        return 0
    finally:
        conn.rollback()
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
