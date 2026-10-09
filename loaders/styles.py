"""Style guidelines (BJCP 2021, BA 2026) -> ref.beer_style.

Both source files are a JSON list of style dicts with the same keys: number, name, category,
categorynumber, the prose fields, and the vitals ogmin/ogmax ... abvmin/abvmax.
BJCP gives every value as a string; BA gives numbers as floats and its number is a slug.

Run: python -m loaders.styles --bjcp styles.json --ba ba_styles.json
"""

import argparse
import json
from dataclasses import dataclass

import psycopg
from psycopg.types.json import Jsonb
from psycopg.types.range import Range

from loaders.common import to_range
from loaders.db import connect, source_id


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


# The ref.source slug for each guide.
SOURCE_SLUG = {"BJCP": "bjcp-2021", "BA": "ba-2026"}


def load(conn: psycopg.Connection, styles: list[Style]) -> int:
    """Insert or update each style on (guide, edition, code); returns how many were written.

    Re-running updates the same rows instead of adding duplicates.
    """
    for style in styles:
        conn.execute(
            """
            insert into ref.beer_style
                (source_id, guide, edition, code, name, category, category_code,
                 og, fg, ibu, srm, abv, characteristic_ingredients, raw)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            on conflict (guide, edition, code) do update
               set source_id = excluded.source_id,
                   name = excluded.name,
                   category = excluded.category,
                   category_code = excluded.category_code,
                   og = excluded.og,
                   fg = excluded.fg,
                   ibu = excluded.ibu,
                   srm = excluded.srm,
                   abv = excluded.abv,
                   characteristic_ingredients = excluded.characteristic_ingredients,
                   raw = excluded.raw
            """,
            (
                source_id(conn, SOURCE_SLUG[style.guide]),
                style.guide,
                style.edition,
                style.code,
                style.name,
                style.category,
                style.category_code,
                style.og,
                style.fg,
                style.ibu,
                style.srm,
                style.abv,
                style.characteristic_ingredients,
                Jsonb(style.raw),
            ),
        )
    return len(styles)


def read_json(path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load BJCP 2021 and BA 2026 styles into ref.beer_style.")
    parser.add_argument("--bjcp", required=True, help="path to styles.json (BJCP 2021)")
    parser.add_argument("--ba", required=True, help="path to ba_styles.json (BA 2026)")
    args = parser.parse_args()

    bjcp = parse_bjcp(read_json(args.bjcp))
    ba = parse_ba(read_json(args.ba))
    with connect() as conn:
        print(f"BJCP 2021: {load(conn, bjcp)} styles")
        print(f"BA 2026: {load(conn, ba)} styles")


if __name__ == "__main__":
    main()
