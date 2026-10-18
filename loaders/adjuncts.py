"""Flakes and sugars -> ref.ingredient + ref.fermentable.

Two inputs: the hopline flake and sugar product pages (fetched by
`loaders.fetch_hopline --adjuncts`) and the rows of Palmer's How to Brew Tables 18.5 and 24.1
(typed in loaders.adjunct_products, as printed).

Hopline wins: its few printed figures (rice max %, candi colour, lactose "non-fermentable")
come first. Palmer fills each field still empty: the extract (Table 18.5's FGDB yield, or
Table 24.1's PPG as extract %; that one is as sold, water included, not dry basis, so P2
must not moisture-correct it) and a sugar's fermentability. Fermentability "normal" (follows
the yeast's attenuation, like every malt) needs no source; "full" and "none" do.
field_source records which source each filled field came from, and raw keeps every source
record whole. Honey is Palmer only: hopline sells none.
"""

import argparse
import json
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

import psycopg
from psycopg.types.json import Jsonb
from psycopg.types.range import Range

from loaders.adjunct_products import ALIASES, COLOUR, PACK_SIZES, PALMER, PALMER_ONLY, PRODUCTS, SKIPPED
from loaders.common import num, to_range
from loaders.db import connect, source_id, upsert_ingredient

HOPLINE = "hopline-adjuncts"
PALMER_SLUG = "palmer-how-to-brew"
PACK_PAGES = "hopline-adjuncts pack sizes"

# Palmer Table 24.1's note: "the reference standard for sucrose, which is 46 PPG".
PPG_OF_SUCROSE = Decimal("46")


@dataclass
class Adjunct:
    name: str
    source_slug: str
    extract_dbfg_pct: Decimal | None
    ebc: Range | None
    max_pct: Decimal | None
    fermentability: str
    field_source: dict[str, str]
    raw: dict


def extract_pct_from_ppg(ppg: Decimal) -> Decimal:
    """A Table 24.1 PPG as extract %: ppg / 46 x 100, rounded half-up to 0.1.

    46 PPG is sucrose, the reference standard Palmer's note under Table 24.1 gives, so
    46 -> 100.0 and 38 (honey) -> 82.6.
    """
    return (ppg / PPG_OF_SUCROSE * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def make_adjunct(
    name: str,
    palmer_row: str,
    page: dict | None = None,
    hopline_figures: dict[str, tuple[str, str]] | None = None,
    extra_pages: list[dict] | None = None,
) -> Adjunct:
    """One adjunct from its hopline page (None for a Palmer-only one), the figures typed from
    that page, and its Palmer row. Hopline first, then Palmer for each field still empty."""
    hopline_figures = hopline_figures or {}
    palmer = PALMER[palmer_row]
    values = {"extract_dbfg_pct": None, "ebc": None, "max_pct": None, "fermentability": None}
    field_source = {}

    for field, (value, _words) in hopline_figures.items():
        if field == "ebc":
            values["ebc"] = to_range(value, value)
        elif field == "max_pct":
            values["max_pct"] = num(value)
        elif field == "fermentability":
            values["fermentability"] = value
        else:
            raise ValueError(f"{name}: no rule for hopline figure {field!r}")
        field_source[field] = HOPLINE

    # Producer colour for the flakes (hopline prints none); a hopline figure above wins.
    if name in COLOUR and values["ebc"] is None:
        low, high, slug, printed = COLOUR[name]
        values["ebc"] = to_range(low, high)
        field_source["ebc"] = slug
        extra_raw = {"colour": {"source": slug, "printed": printed}}
    else:
        extra_raw = {}

    # Palmer prints no colour and no max %, only the extract and a sugar's fermentability.
    if values["extract_dbfg_pct"] is None:
        if "fgdb" in palmer:
            values["extract_dbfg_pct"] = num(palmer["fgdb"].rstrip("%"))
        else:
            values["extract_dbfg_pct"] = extract_pct_from_ppg(num(palmer["ppg"]))
        field_source["extract_dbfg_pct"] = PALMER_SLUG
    if values["fermentability"] is None:
        category = palmer.get("fermentability", "normal")
        values["fermentability"] = category
        if category != "normal":
            field_source["fermentability"] = PALMER_SLUG

    raw = {}
    if page is not None:
        raw[HOPLINE] = page
    if extra_pages:
        raw[PACK_PAGES] = extra_pages
    raw[PALMER_SLUG] = palmer
    raw.update(extra_raw)

    return Adjunct(
        name=name,
        source_slug=HOPLINE if page is not None else PALMER_SLUG,
        extract_dbfg_pct=values["extract_dbfg_pct"],
        ebc=values["ebc"],
        max_pct=values["max_pct"],
        fermentability=values["fermentability"],
        field_source=field_source,
        raw=raw,
    )


def build(hopline: dict) -> list[Adjunct]:
    """An Adjunct for every hopline product mapped in PRODUCTS, then each PALMER_ONLY one.

    hopline is the file `loaders.fetch_hopline --adjuncts` writes. A product in none of
    PRODUCTS, PACK_SIZES and SKIPPED raises ValueError, so a new hopline product never loads
    without a decision in loaders.adjunct_products. A hopline figure whose words are not on
    its page raises ValueError too.
    """
    pack_pages: dict[str, list[dict]] = {}
    for item in hopline["products"]:
        sku = item["sku"]
        if sku in PACK_SIZES:
            pack_pages.setdefault(PACK_SIZES[sku], []).append(item)
        elif sku not in PRODUCTS and sku not in SKIPPED:
            raise ValueError(
                f"hopline SKU {sku} ({item['name']}) is in none of PRODUCTS, PACK_SIZES and SKIPPED"
            )

    items = []
    for item in hopline["products"]:
        sku = item["sku"]
        if sku not in PRODUCTS:
            continue
        name, palmer_row, figures = PRODUCTS[sku]
        for field, (_value, words) in figures.items():
            if words not in (item["text"] or ""):
                raise ValueError(f"SKU {sku} ({item['name']}): {field} words {words!r} are not on the page")
        items.append(make_adjunct(name, palmer_row, item, figures, pack_pages.get(sku)))

    for name, palmer_row in PALMER_ONLY.items():
        items.append(make_adjunct(name, palmer_row))
    return items


def load(conn: psycopg.Connection, items: list[Adjunct]) -> int:
    """Insert or update each adjunct in ref.ingredient and ref.fermentable; returns how many.

    Re-running updates the same rows instead of adding duplicates. All rows are written in
    one transaction (the connection commits on leaving its with-block).
    Hopline names no maker, so producer is "".
    """
    for a in items:
        ingredient_id = upsert_ingredient(
            conn, "fermentable", a.name, "", source_id(conn, a.source_slug), a.raw
        )
        conn.execute(
            """
            insert into ref.fermentable
                (ingredient_id, extract_dbfg_pct, ebc, max_pct, fermentability, field_source)
            values (%s, %s, %s, %s, %s, %s)
            on conflict (ingredient_id) do update
               set extract_dbfg_pct = excluded.extract_dbfg_pct,
                   ebc = excluded.ebc,
                   max_pct = excluded.max_pct,
                   fermentability = excluded.fermentability,
                   field_source = excluded.field_source
            """,
            (
                ingredient_id,
                a.extract_dbfg_pct,
                a.ebc,
                a.max_pct,
                a.fermentability,
                Jsonb(a.field_source),
            ),
        )
        conn.execute("delete from ref.ingredient_alias where ingredient_id = %s", (ingredient_id,))
        for alias in ALIASES.get(a.name, ()):
            conn.execute(
                "insert into ref.ingredient_alias (ingredient_id, alias) values (%s, %s) on conflict do nothing",
                (ingredient_id, alias),
            )
    for name, aliases in ALIASES.items():
        for alias in aliases:
            ids = [r[0] for r in conn.execute("select ingredient_id from app.resolve_ingredient(%s)", (alias,))]
            own = conn.execute(
                "select id from ref.ingredient where kind = 'fermentable' and name = %s", (name,)
            ).fetchone()
            if own is None or ids != [own[0]]:
                raise ValueError(f"alias {alias!r} must resolve to {name!r} only, got ids {ids}")
    return len(items)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load hopline's flakes and sugars, and honey, into ref.fermentable.")
    parser.add_argument("--hopline", required=True, help="path to hopline_adjuncts.json (loaders.fetch_hopline --adjuncts)")
    args = parser.parse_args()

    with open(args.hopline, encoding="utf-8") as f:
        hopline = json.load(f)
    items = build(hopline)
    skipped = sum(1 for item in hopline["products"] if item["sku"] in SKIPPED)
    with connect() as conn:
        print(f"loaded: {load(conn, items)} adjuncts")
    print(f"skipped: {skipped} hopline products (see SKIPPED in loaders/adjunct_products.py)")


if __name__ == "__main__":
    main()
