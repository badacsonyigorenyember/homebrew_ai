"""Hand-checked facts for ref.fermentable: role, max %, enzyme activity, minimum boil, substitutes.

The facts are typed into loaders/fermentable_facts.toml (one [[fermentable]] per row of the 81,
keyed by producer and name as in ref.ingredient; [[substitute]] for the pairs). This module reads
the file, checks it, and loads it. It writes only its own columns and tables:
  ref.fermentable: role, enzyme_activity, min_boil_min, description, description_ref,
                   max_pct (only the rows the file gives one)
  ref.fermentable_substitute
  ref.fermentable_style
and merges its keys into field_source (`field_source || new`), so it can run again.

LOAD ORDER: run it AFTER loaders.malts and loaders.adjuncts. They rewrite max_pct and
field_source wholesale on every run and would drop what this loader wrote.

Every fermentable gets min_boil_min: 60 unless the file says more. A value above 60 is accepted
only when propose_min_boil proposes it for that row's role and colour, and the user confirmed it
(it is then in the file). Source: palmer-how-to-brew.

Usage:
  python -m loaders.fermentable_facts                     check and load
  python -m loaders.fermentable_facts --propose-min-boil  print the rows the proposal sets above 60
"""

import argparse
import tomllib
from pathlib import Path

from psycopg.types.json import Jsonb

from loaders.db import connect

TOML_PATH = Path(__file__).with_name("fermentable_facts.toml")
ROLES = {"base", "kilned", "crystal", "roast", "adjunct", "sugar"}
ENZYME = {"none", "low", "normal", "high"}
BOIL_SOURCE = "palmer-how-to-brew"  # How to Brew p. 59 and p. 177 (see propose_min_boil)
USER = "user-supplied"
UNPLACED = "unplaced"


def read(path: Path = TOML_PATH) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def propose_min_boil(role: str | None, ebc: tuple | None) -> int:
    """90 for a base malt with a colour midpoint below 5 EBC, else 60.

    How to Brew p. 177: "A 90-min. boil is recommended for pale lagers that use a majority of
    Pilsner malt"; p. 59: "60-90 minutes is considered the norm". ebc is (lower, upper); an open
    side is None and the other bound is used. No colour gives 60.
    """
    if role != "base" or ebc is None:
        return 60
    lower, upper = ebc
    if lower is None and upper is None:
        return 60
    midpoint = lower if upper is None else upper if lower is None else (lower + upper) / 2
    return 90 if midpoint < 5 else 60


def fetch_rows(conn) -> dict:
    """(producer, name) -> {"ebc": (lower, upper) or None, "max_pct": ..., "max_pct_source": ...}."""
    rows = {}
    for producer, name, ebc, max_pct, max_pct_source in conn.execute(
        """
        select i.producer, i.name, f.ebc, f.max_pct, f.field_source->>'max_pct'
        from ref.fermentable f join ref.ingredient i on i.id = f.ingredient_id
        """
    ):
        rows[(producer, name)] = {
            "ebc": None if ebc is None else (ebc.lower, ebc.upper),
            "max_pct": max_pct,
            "max_pct_source": max_pct_source,
        }
    return rows


def fetch_sources(conn) -> set[str]:
    return {slug for (slug,) in conn.execute("select slug from ref.source")}


def fetch_style_codes(conn) -> set[str]:
    return {code for (code,) in conn.execute("select code from ref.beer_style")}


def check(
    data: dict, rows: dict, sources: set[str], allow_unplaced: bool = False, style_codes: set[str] | None = None
) -> None:
    """Raise ValueError on the first thing wrong with the file.

    style_codes (the codes of ref.beer_style) turns on the check that every code in the
    [style_names] table exists.

    allow_unplaced lets the tests read a file whose max_pct bases the user has not placed yet;
    loading never allows it.
    """
    seen = set()
    for f in data.get("fermentable", []):
        key = (f["producer"], f["name"])
        label = f"{key[0]} {key[1]}".strip()
        if key not in rows:
            raise ValueError(f"{label}: not in ref.ingredient")
        if key in seen:
            raise ValueError(f"{label}: listed twice")
        seen.add(key)
        if "role" in f:
            if f["role"] not in ROLES:
                raise ValueError(f"{label}: role {f['role']!r} is not one of {sorted(ROLES)}")
            _need(f, "role", ("role_source", "role_note"), label, sources)
        if "enzyme_activity" in f:
            if f["enzyme_activity"] not in ENZYME:
                raise ValueError(f"{label}: enzyme_activity {f['enzyme_activity']!r} is not one of {sorted(ENZYME)}")
            _need(f, "enzyme_activity", ("enzyme_source", "enzyme_ref"), label, sources)
        if "max_pct" in f:
            existing = rows[key]
            if existing["max_pct"] is not None and existing["max_pct_source"] != USER:
                raise ValueError(f"{label}: max_pct is not one of the missing 18 (already from {existing['max_pct_source']})")
            _need(f, "max_pct", ("max_pct_source", "max_pct_basis"), label, sources)
            if f["max_pct_basis"] == UNPLACED and not allow_unplaced:
                raise ValueError(f"{label}: max_pct_basis is still 'unplaced'")
        if "description" in f:
            _need(f, "description", ("description_source", "description_ref"), label, sources)
        if "style_names" in f:
            _need(f, "style_names", ("styles_source",), label, sources)
            for printed in f["style_names"]:
                if printed.lower() not in data.get("style_names", {}):
                    raise ValueError(f"{label}: style name {printed!r} is not in the [style_names] table")
        if "min_boil_min" in f and f["min_boil_min"] > 60:
            proposed = propose_min_boil(f.get("role"), rows[key]["ebc"])
            if f["min_boil_min"] != proposed:
                raise ValueError(f"{label}: min_boil_min {f['min_boil_min']} was not proposed (proposal: {proposed})")
    if style_codes is not None:
        for printed, code in data.get("style_names", {}).items():
            if code != "" and code not in style_codes:
                raise ValueError(f"style name {printed!r}: code {code!r} is not in ref.beer_style")
    pairs = set()
    for s in data.get("substitute", []):
        a, b = tuple(s["a"]), tuple(s["b"])
        for key in (a, b):
            if key not in rows:
                raise ValueError(f"substitute {key}: not in ref.ingredient")
        if a == b:
            raise ValueError(f"substitute {a}: paired with itself")
        if frozenset((a, b)) in pairs:
            raise ValueError(f"substitute {a} / {b}: listed twice")
        pairs.add(frozenset((a, b)))
        if s["source"] not in sources:
            raise ValueError(f"substitute {a} / {b}: source {s['source']!r} is not in ref.source")
        if not s["note"]:
            raise ValueError(f"substitute {a} / {b}: no note")


def _need(f: dict, field: str, companions: tuple, label: str, sources: set[str]) -> None:
    """The companion keys of a value must be present, and the one ending in _source a real source."""
    for companion in companions:
        if not f.get(companion):
            raise ValueError(f"{label}: {field} has no {companion}")
        if companion.endswith("_source") and f[companion] not in sources:
            raise ValueError(f"{label}: {companion} {f[companion]!r} is not in ref.source")


def load(conn, data: dict) -> dict:
    """Write the file's facts. The caller commits. Returns counts."""
    ids = {
        (producer, name): ingredient_id
        for ingredient_id, producer, name in conn.execute(
            "select f.ingredient_id, i.producer, i.name from ref.fermentable f "
            "join ref.ingredient i on i.id = f.ingredient_id"
        )
    }
    source_ids = dict(conn.execute("select slug, id from ref.source"))
    for f in data["fermentable"]:
        ingredient_id = ids[(f["producer"], f["name"])]
        new_sources = {"min_boil_min": BOIL_SOURCE}
        if "description" in f:
            new_sources["description"] = f["description_source"]
        if "role" in f:
            new_sources["role"] = f["role_source"]
        if "enzyme_activity" in f:
            new_sources["enzyme_activity"] = f["enzyme_source"]
        max_pct = None
        if "max_pct" in f:
            max_pct = f["max_pct"]
            new_sources["max_pct"] = f["max_pct_source"]
        conn.execute(
            """
            update ref.fermentable
               set role = %s,
                   enzyme_activity = %s,
                   min_boil_min = %s,
                   description = %s,
                   description_ref = %s,
                   max_pct = coalesce(%s, max_pct),
                   field_source = (field_source - 'role' - 'enzyme_activity' - 'min_boil_min' - 'description') || %s
             where ingredient_id = %s
            """,
            (
                f.get("role"), f.get("enzyme_activity"), f.get("min_boil_min", 60),
                f.get("description"), f.get("description_ref"), max_pct, Jsonb(new_sources), ingredient_id,
            ),
        )
    style_ids = dict(conn.execute("select code, id from ref.beer_style"))
    conn.execute("delete from ref.fermentable_style")
    styles = 0
    for f in data["fermentable"]:
        codes = {data["style_names"][name.lower()] for name in f.get("style_names", [])} - {""}
        for code in sorted(codes):
            conn.execute(
                "insert into ref.fermentable_style (ingredient_id, style_id, source_id) values (%s, %s, %s)",
                (ids[(f["producer"], f["name"])], style_ids[code], source_ids[f["styles_source"]]),
            )
            styles += 1
    conn.execute("delete from ref.fermentable_substitute")
    for s in data["substitute"]:
        first, second = sorted((ids[tuple(s["a"])], ids[tuple(s["b"])]))
        conn.execute(
            "insert into ref.fermentable_substitute (fermentable_id, substitute_id, source_id, note) "
            "values (%s, %s, %s, %s)",
            (first, second, source_ids[s["source"]], s["note"]),
        )
    return {"fermentables": len(data["fermentable"]), "substitutes": len(data["substitute"]), "styles": styles}


def proposed_long_boils(data: dict, rows: dict) -> list[tuple[str, int]]:
    """The rows whose proposal is above 60, as (label, minutes)."""
    out = []
    for f in data["fermentable"]:
        minutes = propose_min_boil(f.get("role"), rows[(f["producer"], f["name"])]["ebc"])
        if minutes > 60:
            out.append((f"{f['producer']} {f['name']}".strip(), minutes))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Load the hand-checked fermentable facts into ref.")
    parser.add_argument("--propose-min-boil", action="store_true", help="print the proposed long boils; load nothing")
    args = parser.parse_args()

    data = read()
    with connect() as conn:
        rows = fetch_rows(conn)
        if args.propose_min_boil:
            check(data, rows, fetch_sources(conn), allow_unplaced=True, style_codes=fetch_style_codes(conn))
            for label, minutes in proposed_long_boils(data, rows):
                print(f"{minutes} min  {label}")
            return
        check(data, rows, fetch_sources(conn), style_codes=fetch_style_codes(conn))
        counts = load(conn, data)
    print(
        f"loaded: {counts['fermentables']} fermentables, {counts['substitutes']} substitute pairs, "
        f"{counts['styles']} malt-style rows"
    )


if __name__ == "__main__":
    main()
