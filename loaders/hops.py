"""Hops sold on hopline.hu -> ref.ingredient + ref.hop.

One input: the hopline hop pages, fetched by `loaders.fetch_hopline --hops`. Each hop's figures
come from its main page's spec table; the data block's Alfasav is used only when the table has
no alpha. Origin is hopline's country, mapped to ISO codes; purpose comes from hopline's three
hop subcategories. Unknown stays None (NULL), never 0. field_source records the source of each
filled field, and raw keeps every page of the hop whole.
"""

import re
from dataclasses import dataclass

from psycopg.types.range import Range

from loaders.common import to_range

HOPLINE = "hopline-hops"

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
    beta_pct: Range | None
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
    name: str, main: dict, extras: list[dict], categories: dict, null_figures: bool = False
) -> Hop:
    """One hop from its main page and its extra pack-size pages.

    Figures come from the main page's table (alpha falls back to the data block's Alfasav);
    with null_figures they all stay None. Origin from the main page, purpose over every page.
    """
    table = main["table"] or {}
    params = main["params"]

    if null_figures:
        alpha = beta = oil = None
    else:
        alpha = parse_figure(table.get("Alfa-sav"))
        if alpha is None:
            alpha = parse_figure(params.get("Alfasav"))
        beta = parse_figure(table.get("Béta-sav"))
        oil = parse_figure(table.get("Olaj tartalom"))

    pages = [main, *extras]
    origins = origin_codes(params.get("Ország"))
    purpose = purpose_of([page["sku"] for page in pages], categories)

    values = {
        "origins": origins,
        "purpose": purpose,
        "alpha_pct": alpha,
        "beta_pct": beta,
        "total_oil_ml_100g": oil,
    }
    field_source = {field: HOPLINE for field, value in values.items() if value is not None}

    return Hop(
        name=name,
        origins=origins,
        purpose=purpose,
        alpha_pct=alpha,
        beta_pct=beta,
        total_oil_ml_100g=oil,
        field_source=field_source,
        raw={HOPLINE: {page["sku"]: page for page in pages}},
    )
