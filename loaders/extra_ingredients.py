"""Ingredient intake (s8-ingredient-intake): add a fermentable, hop or yeast by filling a file.

Folder layout (default shared/ingredients/, one TOML file per ingredient, one per new source):

    fermentable/<name>.toml   hop/<name>.toml   yeast/<name>.toml   sources/<slug>.toml
    _templates/               the commented templates to copy (never read by this module)

The file format (keys, units, which are required) is in the templates and in the plan,
docs/work/s8-ingredient-intake/plan.md. "" or [] in a file means "not filled".

This part reads the folder and checks every file. check_files returns ALL problems, one text
each, in the form "<file>: <field>: <problem>"; an empty list means the set is good. It looks
only at the files, the tag vocabulary and the hopline product maps. The checks against the
database, the load and the command line follow in later tasks.
"""

from dataclasses import dataclass, field
from pathlib import Path
import tomllib

from loaders import adjunct_products, hop_products, malt_products, yeast_products
from loaders.common import name_key
from loaders.fermentable_facts import ENZYME, ROLES
from loaders.tags import descriptor_tag

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROOT = REPO_ROOT / "shared" / "ingredients"

KINDS = ("fermentable", "hop", "yeast")
FERMENTABILITY = {"full", "normal", "none"}
PURPOSES = {"aroma", "bittering", "dual"}
YEAST_TYPES = {"ale", "lager", "kveik", "brett", "lacto", "pedio"}
SOUR_TYPES = {"lacto", "pedio"}  # a souring culture's sheet usually states no attenuation
FLOCCULATION = {"very low", "low", "medium low", "medium", "medium high", "high", "very high"}
FORMS = {"dry", "liquid"}

# Every key of a kind's template, apart from the *_ref and *_source keys that follow from them.
COMMON_KEYS = ["kind", "name", "producer", "source", "description", "description_ref", "aliases", "descriptors"]
KIND_KEYS = {
    "fermentable": ["extract_dbfg_pct", "ebc", "role", "fermentability", "max_pct", "enzyme_activity", "min_boil_min"],
    "hop": ["alpha_pct", "purpose", "origins", "total_oil_ml_100g"],
    "yeast": ["type", "temp_c", "attenuation_pct", "flocculation", "form", "alcohol_tolerance_pct", "product_id"],
}
# Figures that need a page or URL (`<field>_ref`) when filled; description is checked for all kinds.
FIGURES = {
    "fermentable": ["extract_dbfg_pct", "ebc", "max_pct", "enzyme_activity", "min_boil_min"],
    "hop": ["alpha_pct", "total_oil_ml_100g"],
    "yeast": ["temp_c", "attenuation_pct", "alcohol_tolerance_pct"],
}
SOURCE_KEYS = ["slug", "title", "edition", "publisher", "url", "licence"]


@dataclass
class IntakeFile:
    """One file of the folder: where it is, what it says, and whether it could be read."""

    path: str  # as printed in messages: relative to the repo root when inside it
    stem: str  # the file name without .toml
    folder: str  # "fermentable", "hop", "yeast", "sources", or a folder that is not allowed
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
    db_rows: dict = field(default_factory=dict)  # (kind, producer_key, name_key) -> row info (from the DB)


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


KIND_CHECKS = {"fermentable": check_fermentable, "hop": check_hop, "yeast": check_yeast}


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
    if kind == "misc":
        p.add("kind", "misc arrives in s9")
        return p.errors
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
        if key in seen:
            errors.append(f"{item.path}: name: {label} is the same product as {seen[key]}")
        seen.setdefault(key, item.path)
    return errors
