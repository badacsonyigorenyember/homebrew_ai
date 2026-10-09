"""Malts sold on hopline.hu -> ref.ingredient + ref.fermentable.

Two inputs per malt: the hopline product page (fetched by loaders.fetch_hopline) and, when the
maltster's catalogue lists the product, its catalogue entry (hand-built malt_catalogue.json).
The catalogue wins; hopline only fills a field the catalogue lacks. field_source records which
source each filled field came from, and raw keeps both source records whole.
"""

import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from psycopg.types.range import Range

from loaders.common import num, to_range

HOPLINE = "hopline-malts"

# The source slug of each maltster's catalogue (rows in db/011_ref_sources.sql).
CATALOGUE_SLUG = {
    "Weyermann": "weyermann-2026",
    "Viking Malt": "viking-malt-2023",
    "Simpsons Malt": "simpsons-malt-2025",
}

# Points per pound per gallon of 100% extract (sucrose).
PPG_OF_PURE_EXTRACT = Decimal("46.214")

NUMBER = r"(\d+(?:\.\d+)?)"


@dataclass
class Fermentable:
    name: str
    producer: str
    source_slug: str
    potential_sg: Decimal | None
    extract_dbfg_pct: Decimal | None
    ebc: Range | None
    max_pct: Decimal | None
    field_source: dict[str, str]
    raw: dict


def potential_sg(extract_pct: Decimal | None) -> Decimal | None:
    """Potential SG from the dry-basis fine-grind extract %: ppg = extract/100 x 46.214,
    SG = 1 + ppg/1000, rounded half-up to 4 places. None stays None."""
    if extract_pct is None:
        return None
    ppg = extract_pct / 100 * PPG_OF_PURE_EXTRACT
    return (1 + ppg / 1000).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def max_pct_from_text(text: str | None) -> Decimal | None:
    """The stated upper usage limit in a usage text, or None if it states none.

    In order: "up to N%", "max N%", "max. N%" or "<N%" -> N; else a range "A-B%" -> B;
    else text starting with "N%" -> N. A vague figure ("around 50%") is not a limit.
    """
    if text is None:
        return None
    limit = re.search(r"(?:up to|max\.?|<)\s*" + NUMBER + r"\s*%", text, re.IGNORECASE)
    if limit:
        return num(limit.group(1))
    span = re.search(NUMBER + r"\s*[-–]\s*" + NUMBER + r"\s*%", text)
    if span:
        return num(span.group(2))
    start = re.match(r"\s*" + NUMBER + r"\s*%", text)
    if start:
        return num(start.group(1))
    return None


def parse_hopline_spec(spec: str | None) -> dict:
    """EBC range, extract % and max % from a hopline spec text; each None when not stated.

    The page text has stray spaces inside words where the HTML had tags
    ("Felhasználá s:", "F elhasználás", "S zármazási"), so the markers allow one.
    """
    result = {"ebc": None, "extract_pct": None, "max_pct": None}
    if spec is None:
        return result

    # Colour: the first "EBC:" is the spec line; the prose may mention "°EBC" later.
    ebc = re.search(r"EBC\s*:\s*(max\s*)?" + NUMBER + r"(?:\s*-\s*" + NUMBER + r")?", spec)
    if ebc and spec.index("EBC") == ebc.start():
        upto, lo, hi = ebc.groups()
        if upto:
            result["ebc"] = to_range(None, lo)
        else:
            result["ebc"] = to_range(lo, hi or lo)

    # Extract: "Kihozatal : min 79 %"; "? %" or "- %" means not stated.
    extract = re.search(r"Kihozatal\s*:\s*min\.?\s*" + NUMBER, spec)
    if extract:
        result["extract_pct"] = num(extract.group(1))

    # Usage: the text after "Felhasználás:" up to "Származási hely".
    usage = re.search(r"F ?elhaszn\w* ?\w?\s*:(.*?)(?:S ?zármazási|$)", spec)
    if usage:
        result["max_pct"] = max_pct_from_text(usage.group(1))

    return result


def merge(
    item: dict,
    producer: str,
    catalogue: dict | None,
    name: str,
    *,
    ignore_hopline_extract: bool = False,
) -> Fermentable:
    """One hopline product and its catalogue entry (or None) as a Fermentable.

    Each of ebc, extract_dbfg_pct and max_pct comes from the catalogue when it has a value,
    else from hopline. potential_sg follows extract_dbfg_pct. field_source names the source
    of every field that has a value.

    ignore_hopline_extract: leave the extract NULL rather than take hopline's figure. The user
    decided this on 2026-10-09 for Simpsons Crystal T50, DRC and Crystal Extra Dark, where the
    catalogue prints no extract and hopline lists a flat "min 70%".
    """
    catalogue_slug = CATALOGUE_SLUG[producer]
    hopline = parse_hopline_spec(item["spec"])
    if ignore_hopline_extract:
        hopline["extract_pct"] = None

    from_catalogue = {"ebc": None, "extract_pct": None, "max_pct": None}
    if catalogue is not None:
        from_catalogue = {
            "ebc": to_range(catalogue["ebc_min"], catalogue["ebc_max"]),
            "extract_pct": num(catalogue["extract_pct"]),
            "max_pct": max_pct_from_text(catalogue["usage"]),
        }

    values = {}
    field_source = {}
    for field, key in [("ebc", "ebc"), ("extract_dbfg_pct", "extract_pct"), ("max_pct", "max_pct")]:
        if from_catalogue[key] is not None:
            values[field] = from_catalogue[key]
            field_source[field] = catalogue_slug
        elif hopline[key] is not None:
            values[field] = hopline[key]
            field_source[field] = HOPLINE
        else:
            values[field] = None
    if "extract_dbfg_pct" in field_source:
        field_source["potential_sg"] = field_source["extract_dbfg_pct"]

    raw = {HOPLINE: item}
    if catalogue is not None:
        raw[catalogue_slug] = catalogue

    return Fermentable(
        name=name,
        producer=producer,
        source_slug=catalogue_slug if catalogue is not None else HOPLINE,
        potential_sg=potential_sg(values["extract_dbfg_pct"]),
        extract_dbfg_pct=values["extract_dbfg_pct"],
        ebc=values["ebc"],
        max_pct=values["max_pct"],
        field_source=field_source,
        raw=raw,
    )
