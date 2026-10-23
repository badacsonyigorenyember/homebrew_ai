"""Yeasts sold on hopline.hu -> ref.ingredient + ref.yeast.

One input: the hopline dry and liquid yeast pages, fetched by `loaders.fetch_hopline --yeasts`.
Each yeast's figures come from its main page: the data block ("Adatok") first, because it has
one format on every page, and the long description's table where the data block has no value.
Form is the page that lists the SKU (dry or liquid). Unknown stays None (NULL), never 0, and a
format the parser doesn't know raises. field_source records the source of each filled field,
and raw keeps every page of the yeast whole.
"""

import argparse
import json
import re
from dataclasses import dataclass
from decimal import Decimal

import psycopg
from psycopg.types.json import Jsonb
from psycopg.types.range import Range

from loaders.common import to_range
from loaders.db import connect, source_id, upsert_ingredient
from loaders.yeast_products import ATTENUATION, BREWLINE_COPIES, LACTO, PACK_SIZES, SKIPPED, YEASTS

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
    attenuation: dict | None = None,
) -> Yeast:
    """One yeast from its main page and its extra pack-size pages.

    Figures come from the main page only; the extras are kept in raw. Attenuation is on no
    hopline page: it comes from `attenuation`, an ATTENUATION entry from the producer's source,
    which is recorded in field_source and kept whole in raw under that source's slug. Without
    an entry it stays None.
    """
    params = main["params"]
    details_table = (main.get("details") or {}).get("table")

    temp_c = parse_range(params.get("Hőmérséklet"), "°C")
    if temp_c is None:
        temp_c = to_range(params.get("Minimum hőmérséklet"), params.get("Maximum hőmérséklet"))

    if main["sku"] in LACTO:
        if LACTO[main["sku"]].lower() not in (main["details"] or {}).get("text", "").lower():
            raise ValueError(f"{main['sku']}: its text no longer says {LACTO[main['sku']]!r}")
        yeast_type = "lacto"
    else:
        yeast_type = type_of(params.get("Stílus"))

    values = {
        "temp_c": temp_c,
        "flocculation": flocculation(params, details_table),
        "alcohol_tolerance_pct": tolerance(params, details_table),
        "type": yeast_type,
        "form": form,
        "product_id": product_id,
    }
    field_source = {field: HOPLINE for field, value in values.items() if value is not None}
    raw = {HOPLINE: {page["sku"]: page for page in [main, *extras]}}

    attenuation_pct = None
    if attenuation is not None:
        attenuation_pct = to_range(*attenuation["attenuation_pct"])
        field_source["attenuation_pct"] = attenuation["source"]
        raw[attenuation["source"]] = attenuation

    return Yeast(
        name=name,
        producer=producer,
        product_id=product_id,
        type=values["type"],
        form=form,
        attenuation_pct=attenuation_pct,
        temp_c=temp_c,
        flocculation=values["flocculation"],
        alcohol_tolerance_pct=values["alcohol_tolerance_pct"],
        field_source=field_source,
        raw=raw,
    )


def build(hopline: dict) -> list[Yeast]:
    """A Yeast for every main SKU in YEASTS, with its PACK_SIZES pages as extras.

    hopline is the file `loaders.fetch_hopline --yeasts` writes. SKIPPED SKUs are left out. An
    SKU in none of YEASTS, PACK_SIZES and SKIPPED raises ValueError, so a new hopline product
    never loads without a decision in loaders.yeast_products.
    """
    products = {}
    for product in hopline["products"]:
        sku = product["sku"]
        if sku not in YEASTS and sku not in PACK_SIZES and sku not in SKIPPED:
            raise ValueError(
                f"hopline SKU {sku} ({product['name']}) is in none of YEASTS, PACK_SIZES, SKIPPED"
            )
        products[sku] = product

    form_of = {sku: form for form, skus in hopline["forms"].items() for sku in skus}
    yeasts = []
    for sku, (producer, product_id, name) in YEASTS.items():
        extras = [products[extra] for extra, main in PACK_SIZES.items() if main == sku]
        yeasts.append(
            make_yeast(
                producer,
                product_id,
                name,
                form_of[sku],
                products[sku],
                extras,
                ATTENUATION.get(sku),
            )
        )
    return yeasts


# Figures the report compares between two pages' data blocks: hopline's label -> English.
COMPARED_PARAMS = {
    "Stílus": "style family",
    "Hőmérséklet": "temperature",
    "Flokkuláció": "flocculation",
    "Alkoholtolarencia": "alcohol tolerance",
}

# Hungarian style families the report quotes from the pages -> English, printed beside the
# quote: 'Belga Ale' (Belgian ale). Flocculation words get theirs from FLOCCULATION.
STYLE_FAMILIES_EN = {
    "Belga Ale": "Belgian ale",
    "Belga Wit": "Belgian wit",
    "Bajor búza": "Bavarian wheat",
    "Amerikai búza": "American wheat",
}

# Hungarian phrases inside a quoted description line -> English, printed after the quote.
# The Norse Nectar note (KVEIK_NOTE) is explained in a paragraph of its own instead.
DESCRIPTION_PHRASES_EN = {
    "max tartomány": "max range",
}

# A figure at the start of a description line: "18 - 22 °C", "17-22°C", "16 - 32C", "30°C";
# what follows (a note in brackets) is ignored. Used only for the report's comparison.
LEADING_TEMPERATURE = re.compile(NUMBER + r"(?:\s*[-–]\s*" + NUMBER + r")?\s*°?C")

# Pages whose description is another strain's (user decision 2026-10-11: data block loaded).
ANOTHER_STRAINS_DESCRIPTION = {
    "302200-H": "the description is another strain's (it recommends Scottish heavy ales, "
    "American amber ales, sweet stouts); the data-block figures are loaded",
}

LACTOBACILLUS = "Lactobacillust tartalmaz!"  # "contains Lactobacillus!"

# The Norse Nectar temperature lines end with this note (in Hungarian); the report says in
# English what it means.
KVEIK_NOTE = "ezek a törzsek a magas hőmérséklethez alkalmazkodtak"

# Attenuation entries the report explains (user decisions 2026-10-11).
ATTENUATION_NOTES = {
    "302170": "Brewfather's \"german wheat\" (73), one of the figures the user gave for "
    "Brewline, is taken as this product (Bavarian Wheat).",
    "301242": "the YeastFlow page prints \"800-100\"; the user confirmed it means 80-100, so "
    "[80,100] is stored with source user-supplied and the printed text kept in raw.",
}

# Why a yeast has no ATTENUATION entry, for the report: by producer, else by SKU.
NO_ATTENUATION_BY_PRODUCER = {
    "Norse Nectar": "no attenuation source (user: \"we can skipp norse nectar\")",
    "YeasterBunny": "no attenuation source (user: \"leave out the yeasterbunny\")",
}
NO_ATTENUATION = {
    "301471": "no Brewfather figure among those the user gave",
    "301011": "no Brewfather figure among those the user gave (the Brewline catalogue PDF lists "
    "only other, 500 g strains)",
    "302310": "no Brewfather figure among those the user gave (the Brewline catalogue PDF lists "
    "only other, 500 g strains)",
    "300040": "the catalogue page prints \"n/a%\"; its data sheet says \"high attenuation\" only",
    "302190": "neither the fermentis.com page nor its data sheet gives a figure (a bottle "
    "refermentation Brett); hopline links the W-34/70 sheet",
    "301243": "the catalogue page's Attenuation box is empty",
    "301244": "the catalogue page's Attenuation box is empty",
    "301245": "the catalogue page's Attenuation box is empty",
}


def description_temperature(labels: dict) -> str | None:
    """The temperature line of a long description, as printed.

    Most pages say "Ideális hőmérséklet"; M84 says "Erjesztési hőmérséklet"; on M54 the bold
    label ends inside the figure ("Ideális hőmérséklet: 1" + "8 - 20 °C" = "18 - 20 °C").
    """
    if "Ideális hőmérséklet" in labels:
        return labels["Ideális hőmérséklet"]
    if "Erjesztési hőmérséklet" in labels:
        return labels["Erjesztési hőmérséklet"]
    if "Ideális hőmérséklet: 1" in labels:
        return "1" + labels["Ideális hőmérséklet: 1"]
    return None


def data_block_temperature(params: dict) -> Range | None:
    """temp_c as make_yeast reads it: Hőmérséklet, else Minimum/Maximum hőmérséklet."""
    temp_c = parse_range(params.get("Hőmérséklet"), "°C")
    if temp_c is None:
        temp_c = to_range(params.get("Minimum hőmérséklet"), params.get("Maximum hőmérséklet"))
    return temp_c


def value_quote(value: str | None) -> str:
    """A data-block value as printed, with its English beside it when it is a Hungarian style
    family or flocculation word: 'Belga Ale' (Belgian ale), 'Közepes' (medium)."""
    if value is None:
        return "None"
    english = STYLE_FAMILIES_EN.get(value) or FLOCCULATION.get(value.lower())
    if english is None or english == value.lower():
        return repr(value)
    return f"{value!r} ({english})"


def description_quote(printed: str) -> str:
    """A description line as printed, followed by the English of any Hungarian phrase in
    DESCRIPTION_PHRASES_EN: '22-26 °C (max tartomány: 16 - 32 °C)' ("max tartomány": max range)."""
    glosses = [
        f'"{phrase}": {english}'
        for phrase, english in DESCRIPTION_PHRASES_EN.items()
        if phrase in printed
    ]
    return repr(printed) + (f" ({'; '.join(glosses)})" if glosses else "")


def param_differences(a: dict, b: dict) -> list[str]:
    """The COMPARED_PARAMS on which two data blocks differ, as "label: a vs b" (the label in
    English, the values as printed with an English gloss where they are Hungarian)."""
    return [
        f"{label}: {value_quote(a.get(key))} vs {value_quote(b.get(key))}"
        for key, label in COMPARED_PARAMS.items()
        if a.get(key) != b.get(key)
    ]


def report(hopline: dict) -> str:
    """Markdown for the user to check: pages whose data block and description disagree, the
    Brewline rows and the strains they copy, pack sizes whose data block differs, the yeasts
    without attenuation and why, the attenuation count per source, and the kveiks whose page
    says they contain Lactobacillus."""
    products = {product["sku"]: product for product in hopline["products"]}

    def title(sku: str) -> str:
        """The yeast's English name from YEASTS (a 2 g pack: its 12 g product's), else
        hopline's page name (skipped products)."""
        if sku in YEASTS:
            name = f"{YEASTS[sku][0]} {YEASTS[sku][2]}"
        elif sku in PACK_SIZES:
            name = f"{YEASTS[PACK_SIZES[sku]][0]} {YEASTS[PACK_SIZES[sku]][2]} 2 g"
        else:
            name = products[sku]["name"]
        note = ANOTHER_STRAINS_DESCRIPTION.get(sku)
        return f"{name} (`{sku}`)" + (f"; {note}" if note else "")

    temperature, flocc, alcohol = [], [], []
    for sku, product in products.items():
        params = product["params"]
        details = product["details"] or {}
        table = details.get("table")

        block = data_block_temperature(params)
        printed = description_temperature(details.get("labels") or {})
        if block is not None and printed is not None:
            match = LEADING_TEMPERATURE.match(printed.replace(",", "."))
            figure = to_range(match.group(1), match.group(2) or match.group(1)) if match else None
            if figure != block:
                temperature.append(
                    f"- {title(sku)}: data block {params.get('Hőmérséklet', block)!r}, "
                    f"description {description_quote(printed)}"
                )

        if params.get("Flokkuláció") and table and table.get("Flokkuláció"):
            if flocculation(params, None) != flocculation({}, table):
                flocc.append(
                    f"- {title(sku)}: data block {params['Flokkuláció']!r} "
                    f"({flocculation(params, None)}), description {table['Flokkuláció']!r} "
                    f"({flocculation({}, table)})"
                )

        described = (table or {}).get("Alkoholtolerancia", (table or {}).get("Alkohol tolerancia"))
        if params.get("Alkoholtolarencia") and described:
            if tolerance(params, None) != tolerance({}, table):
                alcohol.append(
                    f"- {title(sku)}: data block {params['Alkoholtolarencia']!r}, "
                    f"description {described!r}"
                )

    yeasts = build(hopline)
    lines = [
        "# Yeast loader report",
        "",
        f"Input: hopline yeast pages fetched {hopline['fetched']}, {len(products)} products: "
        f"{len(YEASTS)} yeasts loaded, {len(PACK_SIZES)} pack-size pages kept in raw, "
        f"{len(SKIPPED)} skipped (non-beer). The data block's figures are loaded; the "
        "description fills only what the data block lacks.",
        "",
        f"## Data block and description disagree: temperature ({len(temperature)})",
        "",
        "Values are quoted as the pages print them.",
        "",
        *temperature,
        *(
            [
                "",
                f'The bracketed note on the Norse Nectar lines ("{KVEIK_NOTE}, ...") says the '
                "strains are adapted to high temperatures, are best used above the figure it "
                "gives and work slowly below it.",
            ]
            if any(KVEIK_NOTE in line for line in temperature)
            else []
        ),
        "",
        f"## Data block and description disagree: flocculation ({len(flocc)})",
        "",
        *flocc,
        "",
        f"## Data block and description disagree: alcohol tolerance ({len(alcohol)})",
        "",
        *alcohol,
        "",
        "## Brewline rows and the strains their pages say they copy",
        "",
    ]
    for sku, (producer, _, name) in YEASTS.items():
        if producer != "Brewline":
            continue
        copies = BREWLINE_COPIES.get(sku)
        if not copies:
            lines.append(f"- {name} (`{sku}`): its page names no strain.")
            continue
        for copied in copies:
            differences = param_differences(products[sku]["params"], products[copied]["params"])
            verdict = "; ".join(differences) if differences else "same data block figures"
            lines.append(f"- {name} (`{sku}`) copies {YEASTS[copied][2]} (`{copied}`): {verdict}.")

    lines += ["", "## Pack sizes whose data block differs from the 12 g page's", ""]
    pack_lines = []
    for extra, main in PACK_SIZES.items():
        differences = param_differences(products[extra]["params"], products[main]["params"])
        if differences:
            pack_lines.append(
                f"- {YEASTS[main][2]}: `{extra}` vs `{main}`: {'; '.join(differences)}; "
                "the 12 g page's figures are loaded."
            )
    lines += pack_lines or ["- none"]

    missing = [yeast for yeast in yeasts if yeast.attenuation_pct is None]
    lines += ["", f"## Yeasts without attenuation ({len(missing)})", ""]
    by_reason: dict[tuple[str, str], list[str]] = {}
    for sku, (producer, _, name) in YEASTS.items():
        if sku in ATTENUATION:
            continue
        reason = NO_ATTENUATION.get(sku, NO_ATTENUATION_BY_PRODUCER.get(producer))
        if reason is None:
            raise ValueError(f"yeast {sku} ({name}) has no attenuation and no reason why")
        by_reason.setdefault((producer, reason), []).append(f"{name} (`{sku}`)")
    for (producer, reason), names in sorted(by_reason.items()):
        lines.append(f"- {producer} ({len(names)}): {', '.join(names)}: {reason}.")

    lines += ["", "## Attenuation notes", ""]
    for sku, note in ATTENUATION_NOTES.items():
        lines.append(f"- {YEASTS[sku][0]} {YEASTS[sku][2]} (`{sku}`): {note}")

    lines += ["", f"## Attenuation by source ({len(ATTENUATION)})", ""]
    by_source: dict[str, int] = {}
    for entry in ATTENUATION.values():
        by_source[entry["source"]] = by_source.get(entry["source"], 0) + 1
    for source, count in sorted(by_source.items()):
        lines.append(f"- {source}: {count}")

    lines += ["", f"## Pages that say the culture contains Lactobacillus (\"{LACTOBACILLUS}\")", ""]
    for sku, product in products.items():
        if LACTOBACILLUS in ((product["details"] or {}).get("text") or ""):
            lines.append(f"- {title(sku)}")

    lines += ["", "## Loaded as type lacto (LACTO in yeast_products.py)", ""]
    for sku, quote in LACTO.items():
        lines.append(f"- {title(sku)}: \"{quote}\"")

    return "\n".join(lines) + "\n"


def load(conn: psycopg.Connection, yeasts: list[Yeast]) -> int:
    """Insert or update each yeast in ref.ingredient and ref.yeast; returns how many.

    Re-running updates the same rows instead of adding duplicates. All rows are written in
    one transaction (the connection commits on leaving its with-block).
    """
    hopline_id = source_id(conn, HOPLINE)
    for yeast in yeasts:
        ingredient_id = upsert_ingredient(
            conn, "yeast", yeast.name, yeast.producer, hopline_id, yeast.raw
        )
        conn.execute(
            """
            insert into ref.yeast
                (ingredient_id, product_id, type, form, attenuation_pct, temp_c, flocculation,
                 alcohol_tolerance_pct, field_source)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            on conflict (ingredient_id) do update
               set product_id = excluded.product_id,
                   type = excluded.type,
                   form = excluded.form,
                   attenuation_pct = excluded.attenuation_pct,
                   temp_c = excluded.temp_c,
                   flocculation = excluded.flocculation,
                   alcohol_tolerance_pct = excluded.alcohol_tolerance_pct,
                   field_source = excluded.field_source
            """,
            (
                ingredient_id,
                yeast.product_id,
                yeast.type,
                yeast.form,
                yeast.attenuation_pct,
                yeast.temp_c,
                yeast.flocculation,
                yeast.alcohol_tolerance_pct,
                Jsonb(yeast.field_source),
            ),
        )
    return len(yeasts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load the yeasts sold on hopline.hu into ref.yeast."
    )
    parser.add_argument(
        "--hopline",
        required=True,
        help="path to hopline_yeasts.json (loaders.fetch_hopline --yeasts)",
    )
    parser.add_argument("--report", required=True, help="path of the Markdown report to write")
    args = parser.parse_args()

    with open(args.hopline, encoding="utf-8") as f:
        hopline = json.load(f)
    yeasts = build(hopline)
    with connect() as conn:
        print(f"loaded: {load(conn, yeasts)} yeasts")
    skipped = [sku for sku in hopline["forms"]["dry"] + hopline["forms"]["liquid"] if sku in SKIPPED]
    print(f"skipped: {len(skipped)} non-beer yeasts")
    with open(args.report, "w", encoding="utf-8") as f:
        f.write(report(hopline))
    print(f"report: {args.report}")


if __name__ == "__main__":
    main()
