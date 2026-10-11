"""Yeasts sold on hopline.hu -> ref.ingredient + ref.yeast.

One input: the hopline dry and liquid yeast pages, fetched by `loaders.fetch_hopline --yeasts`.
Each yeast's figures come from its main page: the data block ("Adatok") first, because it has
one format on every page, and the long description's table where the data block has no value.
Form is the page that lists the SKU (dry or liquid). Unknown stays None (NULL), never 0, and a
format the parser doesn't know raises. field_source records the source of each filled field,
and raw keeps every page of the yeast whole.
"""

import re
from dataclasses import dataclass
from decimal import Decimal

from psycopg.types.range import Range

from loaders.common import to_range

HOPLINE = "hopline-yeasts"

NUMBER = r"(\d+(?:\.\d+)?)"

# Texts hopline uses for "no figure".
NO_FIGURE = {"", "-"}

# hopline's flocculation words (lowercase) -> the schema's values.
FLOCCULATION = {
    "alacsony": "low",
    "low": "low",
    "közepes-alacsony": "medium low",
    "közepes": "medium",
    "közepes-magas": "medium high",
    "közepes - magas": "medium high",
    "magas": "high",
    "nagyon magas": "very high",
}

# hopline's style family (data block "Stílus") -> the yeast type. None: the page doesn't say
# what culture it is.
TYPES = {
    "kveik": "kveik",
    "Lager": "lager",
    "Pilsner": "lager",
    "Brett": "brett",
    "Ale": "ale",
    "English Ale": "ale",
    "London Ale": "ale",
    "West Coast Ale": "ale",
    "East Coast Ale": "ale",
    "Belga Ale": "ale",
    "Belga Wit": "ale",
    "Saison": "ale",
    "Farmhouse": "ale",
    "Bajor búza": "ale",
    "Amerikai búza": "ale",
    "Kölsch": "ale",
    "Barleywine": "ale",
    "sour": None,
    "conditioning": None,
}


@dataclass
class Yeast:
    name: str
    producer: str
    product_id: str | None
    type: str | None
    form: str
    attenuation_pct: Range | None
    temp_c: Range | None
    flocculation: str | None
    alcohol_tolerance_pct: Decimal | None
    field_source: dict[str, str]
    raw: dict


def parse_range(text: str | None, unit: str) -> Range | None:
    """A hopline figure in unit as a numrange: "18 – 28 °C" -> [18,28],
    "15,5 – 17,5 v/v%" -> [15.5,17.5], "~12 %" -> [12,12].

    No figure (None, "", "-") -> None. Any other text, another unit included -> ValueError,
    so nothing is ever stored un-converted and a new format gets a decision.
    """
    if text is None:
        return None
    cleaned = text.replace(",", ".").strip()
    if cleaned in NO_FIGURE:
        return None
    if cleaned.startswith("~"):
        cleaned = cleaned[1:].strip()
    pattern = NUMBER + r"(?:\s*[-–]\s*" + NUMBER + r")?\s*" + re.escape(unit)
    match = re.fullmatch(pattern, cleaned)
    if not match:
        raise ValueError(f"unknown yeast figure format for unit {unit}: {text!r}")
    low, high = match.group(1), match.group(2)
    return to_range(low, high if high is not None else low)


def tolerance(params: dict, details_table: dict | None) -> Decimal | None:
    """Alcohol tolerance, %: the top of the data block's range, else the top of the
    description table's figure (a trailing "+" dropped), else None."""
    figure = parse_range(params.get("Alkoholtolarencia"), "v/v%")
    if figure is None and details_table:
        text = details_table.get("Alkoholtolerancia", details_table.get("Alkohol tolerancia"))
        if text is not None:
            figure = parse_range(text.strip().removesuffix("+"), "%")
    return figure.upper if figure is not None else None


def flocculation(params: dict, details_table: dict | None) -> str | None:
    """Flocculation from the data block, else the description table, as a schema value.

    "-" or no value -> None; an unknown word -> ValueError.
    """
    word = params.get("Flokkuláció")
    if word is None and details_table:
        word = details_table.get("Flokkuláció")
    if word is None:
        return None
    word = word.strip().lower()
    if word == "-":
        return None
    if word not in FLOCCULATION:
        raise ValueError(f"unknown yeast flocculation: {word!r}")
    return FLOCCULATION[word]


def type_of(stilus: str | None) -> str | None:
    """The yeast type from the data block's Stílus; None stays None; unknown -> ValueError."""
    if stilus is None:
        return None
    if stilus not in TYPES:
        raise ValueError(f"unknown yeast style family: {stilus!r}")
    return TYPES[stilus]


def make_yeast(
    producer: str,
    product_id: str | None,
    name: str,
    form: str,
    main: dict,
    extras: list[dict],
) -> Yeast:
    """One yeast from its main page and its extra pack-size pages.

    Figures come from the main page only; the extras are kept in raw. Attenuation is on no
    hopline page and stays None.
    """
    params = main["params"]
    details_table = (main.get("details") or {}).get("table")

    temp_c = parse_range(params.get("Hőmérséklet"), "°C")
    if temp_c is None:
        temp_c = to_range(params.get("Minimum hőmérséklet"), params.get("Maximum hőmérséklet"))

    values = {
        "temp_c": temp_c,
        "flocculation": flocculation(params, details_table),
        "alcohol_tolerance_pct": tolerance(params, details_table),
        "type": type_of(params.get("Stílus")),
        "form": form,
        "product_id": product_id,
    }
    field_source = {field: HOPLINE for field, value in values.items() if value is not None}
    raw = {HOPLINE: {page["sku"]: page for page in [main, *extras]}}

    return Yeast(
        name=name,
        producer=producer,
        product_id=product_id,
        type=values["type"],
        form=form,
        attenuation_pct=None,
        temp_c=temp_c,
        flocculation=values["flocculation"],
        alcohol_tolerance_pct=values["alcohol_tolerance_pct"],
        field_source=field_source,
        raw=raw,
    )
