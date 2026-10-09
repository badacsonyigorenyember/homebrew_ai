"""Style guidelines (BJCP 2021, BA 2026) -> ref.beer_style.

Both source files are a JSON list of style dicts with the same keys: number, name, category,
categorynumber, the prose fields, and the vitals ogmin/ogmax ... abvmin/abvmax.
BJCP gives every value as a string; BA gives numbers as floats and its number is a slug.
"""

from dataclasses import dataclass

from psycopg.types.range import Range

from loaders.common import to_range


@dataclass
class Style:
    guide: str
    edition: str
    code: str
    name: str | None
    category: str | None
    category_code: str | None
    og: Range | None
    fg: Range | None
    ibu: Range | None
    srm: Range | None
    abv: Range | None
    characteristic_ingredients: str | None
    raw: dict


def text(x) -> str | None:
    """A source text value, or None when it is missing or blank."""
    if x is None:
        return None
    s = str(x).strip()
    return s or None


def parse_style(row: dict, guide: str, edition: str) -> Style:
    """One source style dict as a Style; missing vitals become None ranges."""
    return Style(
        guide=guide,
        edition=edition,
        code=row["number"].strip(),
        name=text(row.get("name")),
        category=text(row.get("category")),
        category_code=text(row.get("categorynumber")),
        og=to_range(row.get("ogmin"), row.get("ogmax")),
        fg=to_range(row.get("fgmin"), row.get("fgmax")),
        ibu=to_range(row.get("ibumin"), row.get("ibumax")),
        srm=to_range(row.get("srmmin"), row.get("srmmax")),
        abv=to_range(row.get("abvmin"), row.get("abvmax")),
        characteristic_ingredients=text(row.get("characteristicingredients")),
        raw=row,
    )


def parse_bjcp(rows: list[dict]) -> list[Style]:
    """BJCP 2021 styles from styles.json; the code is the style number, e.g. "21A"."""
    return [parse_style(row, "BJCP", "2021") for row in rows]


def parse_ba(rows: list[dict]) -> list[Style]:
    """BA 2026 styles from ba_styles.json; the code is the number slug, e.g. "ordinary-bitter"."""
    return [parse_style(row, "BA", "2026") for row in rows]
