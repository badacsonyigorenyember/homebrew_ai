"""Helpers shared by the ref loaders: numbers, ranges, units, name keys, BeerJSON files."""

import json
import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP

from psycopg.types.range import Range


def num(x: str | float | int | None) -> Decimal | None:
    """A source value as a Decimal, or None when it is missing or blank.

    The Decimal is built from str(x), so 5.0 becomes Decimal("5.0"), not a binary float.
    """
    if x is None:
        return None
    text = str(x).strip()
    if text == "":
        return None
    return Decimal(text)


def to_range(lo, hi) -> Range | None:
    """A numrange from a low and a high value; a missing side stays open.

    Both missing -> None (stored as NULL). Only lo -> [lo,). Only hi -> (,hi].
    lo greater than hi -> ValueError, since the source data is then wrong.
    """
    lo = num(lo)
    hi = num(hi)
    if lo is None and hi is None:
        return None
    if lo is None:
        return Range(None, hi, "(]")
    if hi is None:
        return Range(lo, None, "[)")
    if lo > hi:
        raise ValueError(f"range low {lo} is greater than high {hi}")
    return Range(lo, hi, "[]")


def f_to_c(f: Decimal | float) -> Decimal:
    """Degrees Fahrenheit to Celsius, rounded to 0.1."""
    celsius = (num(f) - 32) * 5 / 9
    return celsius.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def name_key(s: str) -> str:
    """A matching key for a name: no accents or ®™©, lowercase, only a-z and 0-9.

    Text inside parentheses is kept, so "Saaz (US)" -> "saazus" stays apart from "Saaz".
    """
    # Drop the marks first: NFKD would turn ™ into "TM".
    for mark in "®™©":
        s = s.replace(mark, "")
    folded = unicodedata.normalize("NFKD", s)
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]", "", folded.lower())


def read_beerjson(path) -> dict:
    """The "beerjson" object of a BeerJSON file, skipping its // comment header lines."""
    with open(path, encoding="utf-8") as f:
        lines = [line for line in f if not line.strip().startswith("//")]
    return json.loads("".join(lines))["beerjson"]
