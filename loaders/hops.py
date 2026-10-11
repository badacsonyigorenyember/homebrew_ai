"""Hops sold on hopline.hu -> ref.ingredient + ref.hop.

One input: the hopline hop pages, fetched by `loaders.fetch_hopline --hops`. Each hop's figures
come from its main page's spec table; the data block's Alfasav is used only when the table has
no alpha. Origin is hopline's country, mapped to ISO codes; purpose comes from hopline's three
hop subcategories. Where hopline has no alpha, oil or purpose, the value entered from Beer
Maverick (BEERMAVERICK in loaders.hop_products) fills it. Unknown stays None (NULL), never 0.
field_source records the source of each filled field, and raw keeps every page of the hop whole,
plus the Beer Maverick entry when one is used.
"""

import argparse
import json
import re
from dataclasses import dataclass

import psycopg
from psycopg.types.json import Jsonb
from psycopg.types.range import Range

from loaders.common import to_range
from loaders.db import connect, source_id, upsert_ingredient
from loaders.hop_products import BEERMAVERICK, HOPS, NULL_FIGURES, PACK_SIZES

HOPLINE = "hopline-hops"
BEER_MAVERICK = "beermaverick"

NUMBER = r"(\d+(?:\.\d+)?)"

# A figure: "a" or "a-b" (hyphen or en dash, spaces optional), then "%" or "ml".
FIGURE = re.compile(NUMBER + r"(?:\s*[-–]\s*" + NUMBER + r")?\s*(?:%|ml)")

# Texts hopline uses for "no figure" (spaces removed before comparing).
NO_FIGURE = {"", "%", "?%", "-%"}

# hopline's country names -> ISO 3166 alpha-2. Every name on the pages on 2026-10-10.
ORIGIN_CODES = {
    "USA": "US",
    "Németország": "DE",
    "Új-Zéland": "NZ",
    "Anglia": "GB",
    "Csehország": "CZ",
    "Dél-Afrika": "ZA",
    "Szlovénia": "SI",
    "Ausztrália": "AU",
    "Franciaország": "FR",
    "Japán": "JP",
}


@dataclass
class Hop:
    name: str
    origins: list[str] | None
    purpose: str | None
    alpha_pct: Range | None
    total_oil_ml_100g: Range | None
    field_source: dict[str, str]
    raw: dict


def parse_figure(text: str | None) -> Range | None:
    """A hopline figure as a numrange: "10-15 %" -> [10,15], "0,85 %" -> [0.85,0.85],
    "~ 18.5 %" -> [18.5,18.5], "1.6-2.5 ml" -> [1.6,2.5].

    No figure ("? %", "%", "- %", "", None) -> None. Any other text -> ValueError, so a new
    format gets a decision instead of a silent NULL.
    """
    if text is None:
        return None
    cleaned = text.replace(",", ".").strip()
    if cleaned.startswith("~"):
        cleaned = cleaned[1:].strip()
    if re.sub(r"\s", "", cleaned) in NO_FIGURE:
        return None
    match = FIGURE.fullmatch(cleaned)
    if not match:
        raise ValueError(f"unknown hop figure format: {text!r}")
    low, high = match.group(1), match.group(2)
    return to_range(low, high if high is not None else low)


def origin_codes(country: str | None) -> list[str] | None:
    """hopline's country name as a list of ISO codes; None stays None; unknown -> ValueError."""
    if country is None:
        return None
    if country not in ORIGIN_CODES:
        raise ValueError(f"unknown hop country: {country!r}")
    return [ORIGIN_CODES[country]]


def purpose_of(skus: list[str], categories: dict[str, list[str]]) -> str | None:
    """The purpose of one hop from hopline's subcategories, over all its SKUs.

    In "dual", or in both "aroma" and "bittering" -> "dual"; only "bittering" -> "bittering";
    only "aroma" -> "aroma"; in none -> None.
    """
    in_aroma = any(sku in categories["aroma"] for sku in skus)
    in_bittering = any(sku in categories["bittering"] for sku in skus)
    in_dual = any(sku in categories["dual"] for sku in skus)
    if in_dual or (in_aroma and in_bittering):
        return "dual"
    if in_bittering:
        return "bittering"
    if in_aroma:
        return "aroma"
    return None


def make_hop(
    name: str,
    main: dict,
    extras: list[dict],
    categories: dict,
    null_figures: bool = False,
    beermaverick: dict | None = None,
) -> Hop:
    """One hop from its main page and its extra pack-size pages.

    Figures come from the main page's table (alpha falls back to the data block's Alfasav);
    with null_figures hopline's figures are not used. A beermaverick entry then fills alpha,
    oil and purpose where hopline gave none. Origin from the main page, purpose over every page.
    """
    table = main["table"] or {}
    params = main["params"]

    if null_figures:
        alpha = oil = None
    else:
        alpha = parse_figure(table.get("Alfa-sav"))
        if alpha is None:
            alpha = parse_figure(params.get("Alfasav"))
        oil = parse_figure(table.get("Olaj tartalom"))

    pages = [main, *extras]
    origins = origin_codes(params.get("Ország"))
    purpose = purpose_of([page["sku"] for page in pages], categories)

    values = {
        "origins": origins,
        "purpose": purpose,
        "alpha_pct": alpha,
        "total_oil_ml_100g": oil,
    }
    field_source = {field: HOPLINE for field, value in values.items() if value is not None}
    raw = {HOPLINE: {page["sku"]: page for page in pages}}

    if beermaverick is not None:
        if alpha is None and "alpha_pct" in beermaverick:
            alpha = to_range(*beermaverick["alpha_pct"])
            field_source["alpha_pct"] = BEER_MAVERICK
        if oil is None and "total_oil_ml_100g" in beermaverick:
            oil = to_range(*beermaverick["total_oil_ml_100g"])
            field_source["total_oil_ml_100g"] = BEER_MAVERICK
        if purpose is None and "purpose" in beermaverick:
            purpose = beermaverick["purpose"]
            field_source["purpose"] = BEER_MAVERICK
        raw[BEER_MAVERICK] = beermaverick

    return Hop(
        name=name,
        origins=origins,
        purpose=purpose,
        alpha_pct=alpha,
        total_oil_ml_100g=oil,
        field_source=field_source,
        raw=raw,
    )


def build(hopline: dict) -> list[Hop]:
    """A Hop for every main SKU in HOPS, with its PACK_SIZES pages as extras.

    hopline is the file `loaders.fetch_hopline --hops` writes. An SKU in neither HOPS nor
    PACK_SIZES raises ValueError, so a new hopline product never loads without a decision in
    loaders.hop_products. Hops in NULL_FIGURES are built without hopline's figures, and
    BEERMAVERICK fills the alpha, oil and purpose hopline lacks.
    """
    products = {}
    for product in hopline["products"]:
        sku = product["sku"]
        if sku not in HOPS and sku not in PACK_SIZES:
            raise ValueError(
                f"hopline SKU {sku} ({product['name']}) is in neither HOPS nor PACK_SIZES"
            )
        products[sku] = product

    hops = []
    for sku, name in HOPS.items():
        extras = [products[extra] for extra, main in PACK_SIZES.items() if main == sku]
        hops.append(
            make_hop(
                name,
                products[sku],
                extras,
                hopline["categories"],
                null_figures=sku in NULL_FIGURES,
                beermaverick=BEERMAVERICK.get(sku),
            )
        )
    return hops


def report(hopline: dict) -> str:
    """Markdown listing the pages whose figures were not used or disagree:
    hops loaded without figures, pack sizes whose table differs from the main page's, and
    LUPOMAX pages whose table equals the pellet's."""
    products = {product["sku"]: product for product in hopline["products"]}
    sku_of = {name: sku for sku, name in HOPS.items()}

    lines = [
        "# Hop loader report",
        "",
        f"Input: hopline hop pages fetched {hopline['fetched']}, {len(products)} products, "
        f"{len(HOPS)} hops.",
        "",
        "## Hops without hopline figures",
        "",
    ]
    hops = build(hopline)
    for sku, reason in NULL_FIGURES.items():
        lines.append(f"- {HOPS[sku]} (`{sku}`): hopline's figures not used, {reason}.")
    for hop in hops:
        sku = sku_of[hop.name]
        if hop.field_source.get("alpha_pct") != HOPLINE and sku not in NULL_FIGURES:
            table = products[sku]["table"]
            lines.append(f"- {hop.name} (`{sku}`): no alpha on the page (table: {table}).")

    lines += ["", "## Figures filled from Beer Maverick", ""]
    for hop in hops:
        filled = [field for field, source in hop.field_source.items() if source == BEER_MAVERICK]
        if filled:
            lines.append(f"- {hop.name} (`{sku_of[hop.name]}`): {', '.join(filled)}.")

    lines += ["", "## Pack sizes whose table differs from the main page's", ""]
    for extra, main in PACK_SIZES.items():
        if products[extra]["table"] != products[main]["table"]:
            lines.append(
                f"- {HOPS[main]}: `{extra}` {products[extra]['table']} vs "
                f"main `{main}` {products[main]['table']}; the main page's figures are loaded."
            )

    lines += ["", "## LUPOMAX pages whose table equals the pellet's", ""]
    for sku, name in HOPS.items():
        if not name.endswith(" LUPOMAX"):
            continue
        pellet = sku_of[name.removesuffix(" LUPOMAX")]
        if products[sku]["table"] == products[pellet]["table"]:
            lines.append(
                f"- {name} (`{sku}`) repeats {HOPS[pellet]} (`{pellet}`): "
                f"{products[sku]['table']}. Loaded as the page shows."
            )

    return "\n".join(lines) + "\n"


def load(conn: psycopg.Connection, hops: list[Hop]) -> int:
    """Insert or update each hop in ref.ingredient and ref.hop; returns how many.

    Re-running updates the same rows instead of adding duplicates. All rows are written in
    one transaction (the connection commits on leaving its with-block).
    """
    hopline_id = source_id(conn, HOPLINE)
    for hop in hops:
        ingredient_id = upsert_ingredient(conn, "hop", hop.name, "", hopline_id, hop.raw)
        conn.execute(
            """
            insert into ref.hop
                (ingredient_id, origins, purpose, alpha_pct, total_oil_ml_100g, field_source)
            values (%s, %s, %s, %s, %s, %s)
            on conflict (ingredient_id) do update
               set origins = excluded.origins,
                   purpose = excluded.purpose,
                   alpha_pct = excluded.alpha_pct,
                   total_oil_ml_100g = excluded.total_oil_ml_100g,
                   field_source = excluded.field_source
            """,
            (
                ingredient_id,
                hop.origins,
                hop.purpose,
                hop.alpha_pct,
                hop.total_oil_ml_100g,
                Jsonb(hop.field_source),
            ),
        )
    return len(hops)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load the hops sold on hopline.hu into ref.hop.")
    parser.add_argument(
        "--hopline", required=True, help="path to hopline_hops.json (loaders.fetch_hopline --hops)"
    )
    parser.add_argument("--report", required=True, help="path of the Markdown report to write")
    args = parser.parse_args()

    with open(args.hopline, encoding="utf-8") as f:
        hopline = json.load(f)
    hops = build(hopline)
    with connect() as conn:
        print(f"loaded: {load(conn, hops)} hops")
    with open(args.report, "w", encoding="utf-8") as f:
        f.write(report(hopline))
    print(f"report: {args.report}")


if __name__ == "__main__":
    main()
