import re
from decimal import Decimal as D

import pytest
from psycopg.types.range import Range

from loaders.common import name_key
from loaders.yeast_products import ATTENUATION, PACK_SIZES, SKIPPED, YEASTS
from loaders.yeasts import (
    FLOCCULATION,
    TYPES,
    build,
    description_quote,
    flocculation,
    make_yeast,
    param_differences,
    parse_range,
    tolerance,
    type_of,
)


def r(lo, hi):
    return Range(D(lo), D(hi), "[]")


# Inline fixtures: product dicts as fetch_hopline --yeasts writes them (shortened, wording kept).
US05_TABLE = {
    "Stílus": "Ale",
    "Aroma": "semleges",
    "Flokkuláció": "közepes",
    "Alkoholtolerancia": "9-11 %",
}

US05 = {
    "sku": "301030",
    "url": "https://www.hopline.hu/fermentis-safale-us-05",
    "name": "Fermentis SafAle US-05",
    "spec": "Fermentis SafAle US-05 Stílus Aroma",
    "table": {"Stílus": "Ale", "Aroma": "Semleges"},
    "params": {
        "Stílus": "Ale",
        "Hőmérséklet": "18 – 28 °C",
        "Flokkuláció": "Közepes",
        "Alkoholtolarencia": "9 – 11 v/v%",
        "Aroma": "Semleges",
    },
    "details": {
        "table": US05_TABLE,
        "labels": {"Ideális hőmérséklet": "18 - 28 °C", "Adagolás": "5-8g/10l"},
        "text": "Ideális hőmérséklet: 18 - 28 °C Adagolás: 5-8g/10l",
    },
}


def west_coast(sku, size, temp):
    return {
        "sku": sku,
        "url": f"https://www.hopline.hu/brewline-us-west-coast-ale-{size}",
        "name": f"Brewline U.S West Coast Ale {size}",
        "spec": f"Brewline U.S West Coast Ale {size} Stílus Aroma",
        "table": {"Stílus": "Ale", "Aroma": "Semleges"},
        "params": {
            "Címkék": "ale,brewline,coast,west",
            "Stílus": "West Coast Ale",
            "Hőmérséklet": temp,
        },
        "details": {
            "table": {
                "Stílus": "Ale",
                "Aroma": "Semleges",
                "Flokkuláció": "közepes",
                "Alkoholtolerancia": "9-11 %",
            },
            "labels": {},
            "text": "",
        },
    }


REAL_SCOTLAND = {
    "sku": "301551",
    "url": "https://www.hopline.hu/gozdawa-real-scotland-yeast-10g",
    "name": "Gozdawa Real Scotland Yeast 10g",
    "spec": "Gozdawa Real Scotland Yeast 10g Stílus Aroma",
    "table": {"Stílus": "Ale", "Aroma": "semleges"},
    "params": {
        "Címkék": "10g,ale,gozdawa,scottish",
        "Stílus": "Ale",
        "Hőmérséklet": "15 – 22 °C",
    },
    "details": {
        "table": {
            "Stílus": "Ale",
            "Aroma": "semleges",
            "Flokkuláció": "magas",
            "Alkoholtolerancia": "5-5.5%",
        },
        "labels": {},
        "text": "",
    },
}

SUAVA = {
    "sku": "302410",
    "url": "https://www.hopline.hu/lallemand-suava-ale-eleszto-wlp079",
    "name": "Lallemand Suava Ale élesztő WLP079",
    "spec": "Lallemand Suava Ale élesztő WLP079 Stílus Aroma",
    "table": {"Stílus": "IPA", "Aroma": "ribizli, trópusi gyümölcsök"},
    "params": {
        "Flokkuláció": "Alacsony",
        "Aroma": "Trópusi gyümölcsös, Ribizli",
        "Minimum hőmérséklet": "24",
        "Maximum hőmérséklet": "30",
    },
    "details": {
        "table": {
            "Stílus": "IPA",
            "Aroma": "ribizli, trópusi gyümölcsök",
            "Flokkuláció": "alacsony",
            "Alkoholtolerancia": "12%",
        },
        "labels": {},
        "text": "",
    },
}


def test_parse_range():
    assert parse_range("18 – 28 °C", "°C") == r("18", "28")
    assert parse_range("17-22°C", "°C") == r("17", "22")
    assert parse_range("15,5 – 17,5 v/v%", "v/v%") == r("15.5", "17.5")
    assert parse_range("10 – 10 v/v%", "v/v%") == r("10", "10")
    assert parse_range("~12 %", "%") == r("12", "12")
    assert parse_range(None, "°C") is None
    assert parse_range("", "°C") is None
    assert parse_range("-", "°C") is None
    # The guard that nothing is ever stored un-converted.
    with pytest.raises(ValueError, match="64 – 82 °F"):
        parse_range("64 – 82 °F", "°C")
    with pytest.raises(ValueError, match="lots"):
        parse_range("lots", "°C")


def test_tolerance():
    assert tolerance({"Alkoholtolarencia": "9 – 11 v/v%"}, None) == D("11")
    assert tolerance({}, {"Alkoholtolerancia": "12 %+"}) == D("12")
    assert tolerance({}, {"Alkoholtolerancia": "5-5.5%"}) == D("5.5")
    assert tolerance({}, {"Alkoholtolerancia": "17,5 %"}) == D("17.5")
    assert tolerance({}, {"Alkohol tolerancia": "12%"}) == D("12")
    assert tolerance({}, None) is None
    assert tolerance({}, {"Stílus": "Ale"}) is None


def test_flocculation():
    assert flocculation({"Flokkuláció": "Magas"}, None) == "high"
    assert flocculation({"Flokkuláció": "Közepes"}, None) == "medium"
    assert flocculation({"Flokkuláció": "Alacsony"}, None) == "low"
    assert flocculation({}, {"Flokkuláció": "nagyon magas"}) == "very high"
    assert flocculation({}, {"Flokkuláció": "közepes - magas"}) == "medium high"
    assert flocculation({}, {"Flokkuláció": "közepes-alacsony"}) == "medium low"
    assert flocculation({}, {"Flokkuláció": "-"}) is None
    assert flocculation({}, None) is None
    with pytest.raises(ValueError, match="sticky"):
        flocculation({"Flokkuláció": "sticky"}, None)


def test_type_of():
    assert type_of("kveik") == "kveik"
    assert type_of("Pilsner") == "lager"
    assert type_of("Brett") == "brett"
    assert type_of("Belga Wit") == "ale"
    assert type_of("sour") is None
    assert type_of(None) is None
    with pytest.raises(ValueError, match="Wine"):
        type_of("Wine")


def test_us05():
    yeast = make_yeast("Fermentis", "US-05", "SafAle US-05", "dry", US05, [])
    assert yeast.name == "SafAle US-05"
    assert yeast.producer == "Fermentis"
    assert yeast.product_id == "US-05"
    assert yeast.form == "dry"
    assert yeast.temp_c == r("18", "28")
    assert yeast.flocculation == "medium"
    assert yeast.alcohol_tolerance_pct == D("11")
    assert yeast.type == "ale"
    assert yeast.attenuation_pct is None
    assert yeast.field_source == {
        field: "hopline-yeasts"
        for field in (
            "temp_c",
            "flocculation",
            "alcohol_tolerance_pct",
            "type",
            "form",
            "product_id",
        )
    }
    assert yeast.raw == {"hopline-yeasts": {"301030": US05}}


def test_brewline_pack_size():
    main = west_coast("301601", "12g", "18 – 28 °C")
    extra = west_coast("301600", "2g", "18 – 30 °C")
    yeast = make_yeast("Brewline", None, "U.S. West Coast Ale", "dry", main, [extra])
    assert yeast.temp_c == r("18", "28")
    assert yeast.flocculation == "medium"
    assert yeast.alcohol_tolerance_pct == D("11")
    assert yeast.type == "ale"
    assert yeast.product_id is None
    assert "product_id" not in yeast.field_source
    assert set(yeast.raw["hopline-yeasts"]) == {"301601", "301600"}


def test_description_fills_gaps():
    scotland = make_yeast("Gozdawa", None, "Real Scotland", "dry", REAL_SCOTLAND, [])
    assert scotland.flocculation == "high"
    assert scotland.alcohol_tolerance_pct == D("5.5")

    suava = make_yeast("Lallemand", None, "Suava", "dry", SUAVA, [])
    assert suava.temp_c == r("24", "30")
    assert suava.type is None
    assert "type" not in suava.field_source


def test_yeast_map():
    assert len(YEASTS) == 119
    assert sum(producer == "Brewline" for producer, _, _ in YEASTS.values()) == 10
    assert len(PACK_SIZES) == 2
    assert len(SKIPPED) == 8
    assert not set(YEASTS) & set(PACK_SIZES)
    assert not set(YEASTS) & set(SKIPPED)
    assert not set(PACK_SIZES) & set(SKIPPED)
    assert set(PACK_SIZES.values()) <= set(YEASTS)
    # Two yeasts with the same key would make the upsert overwrite one with the other.
    keys = [(name_key(producer), name_key(name)) for producer, _, name in YEASTS.values()]
    assert len(set(keys)) == len(keys)
    # Attenuation only for loaded yeasts, only from the named sources, none for the producers
    # the user said to skip.
    assert set(ATTENUATION) <= set(YEASTS)
    assert {entry["source"] for entry in ATTENUATION.values()} <= ATTENUATION_SOURCES
    assert not [
        sku for sku in ATTENUATION if YEASTS[sku][0] in ("Norse Nectar", "YeasterBunny")
    ]
    # User decisions 2026-10-11: Brewfather's "german wheat" is Brewline Bavarian Wheat; YF-666's
    # printed "800-100" is 80-100, recorded as user-supplied with the printed text kept.
    assert ATTENUATION["302170"]["source"] == "brewfather"
    assert ATTENUATION["302170"]["attenuation_pct"] == ("73", "73")
    assert ATTENUATION["301242"]["source"] == "user-supplied"
    assert ATTENUATION["301242"]["attenuation_pct"] == ("80", "100")
    assert ATTENUATION["301242"]["printed"] == "800-100"


ATTENUATION_SOURCES = {
    "yeastflow-catalogue",
    "lallemand-catalogue",
    "fermentis-datasheets",
    "mangrovejacks-datasheets",
    "brewfather",
    "user-supplied",
}

US05_ATTENUATION = {
    "attenuation_pct": ("78", "82"),
    "source": "fermentis-datasheets",
    "url": "https://distributors.fermentis.com/download/135/english/171/safale-us-05-en.pdf",
    "printed": "78-82%",
    "date": "2026-10-11",
}

CZECH_PILSNER_ATTENUATION = {
    "attenuation_pct": ("76", "76"),
    "source": "brewfather",
    "url": None,
    "printed": "76",
    "date": "2026-10-11",
}


def test_attenuation_fill():
    us05 = make_yeast("Fermentis", "US-05", "SafAle US-05", "dry", US05, [], US05_ATTENUATION)
    assert us05.attenuation_pct == r("78", "82")
    assert us05.field_source["attenuation_pct"] == "fermentis-datasheets"
    assert us05.field_source["temp_c"] == "hopline-yeasts"
    assert us05.raw["fermentis-datasheets"] == US05_ATTENUATION
    assert us05.raw["hopline-yeasts"] == {"301030": US05}

    # One printed figure is stored as the point range [a,a], not widened.
    pilsner = make_yeast(
        "Gozdawa", None, "Czech Pilsner 18", "dry", REAL_SCOTLAND, [], CZECH_PILSNER_ATTENUATION
    )
    assert pilsner.attenuation_pct == r("76", "76")
    assert pilsner.field_source["attenuation_pct"] == "brewfather"

    without = make_yeast("Fermentis", "US-05", "SafAle US-05", "dry", US05, [], None)
    assert without.attenuation_pct is None
    assert "attenuation_pct" not in without.field_source
    assert set(without.raw) == {"hopline-yeasts"}


def test_unknown_sku_raises():
    unknown = {**US05, "sku": "999999", "name": "Brand New Yeast"}
    hopline = {"forms": {"dry": ["999999"], "liquid": []}, "products": [unknown]}
    with pytest.raises(ValueError, match="999999"):
        build(hopline)


# Letters Hungarian uses and English, German and the makers' brand names don't (ö and ü are
# left out: Köln, Kölschermeister and St. Cölibate are German or the maker's own spelling).
HUNGARIAN_LETTERS = set("áéíóőúű")
# Hungarian words hopline's yeast pages use, which would show a value copied untranslated.
HUNGARIAN_WORDS = {
    "élesztő", "eleszto", "bajor", "búza", "buza", "belga", "amerikai", "sör", "száraz",
    "folyékony", "alacsony", "közepes", "magas", "nagyon", "semleges", "gyümölcsös",
}


def hungarian(text: str) -> bool:
    lower = text.lower()
    words = set(re.findall(r"\w+", lower))
    return bool(HUNGARIAN_LETTERS & set(lower)) or bool(HUNGARIAN_WORDS & words)


def test_no_hungarian_outside_raw():
    # User request 2026-10-11: every value written outside raw is English. raw keeps the
    # hopline pages and the attenuation entries' printed text as they are (provenance).
    assert hungarian("Bajor Búza") and hungarian("Közepes") and not hungarian("Köln")
    written = [text for entry in YEASTS.values() for text in entry if text is not None]
    written += [value for value in TYPES.values() if value is not None]
    written += list(FLOCCULATION.values())
    us05 = make_yeast("Fermentis", "US-05", "SafAle US-05", "dry", US05, [], US05_ATTENUATION)
    written += [us05.name, us05.producer, us05.product_id, us05.type, us05.form, us05.flocculation]
    written += [*us05.field_source, *us05.field_source.values()]
    assert [text for text in written if hungarian(text)] == []


def test_report_glosses_hungarian_quotes():
    # Re-review note 2026-10-11: a Hungarian value the report quotes keeps its printed text and
    # gets its English beside it; English values are quoted alone.
    abbey = {"Stílus": "Belga Ale", "Flokkuláció": "Közepes"}
    be256 = {"Stílus": "Saison", "Flokkuláció": "Közepes"}
    assert param_differences(abbey, be256) == ["style family: 'Belga Ale' (Belgian ale) vs 'Saison'"]
    wheat = {"Stílus": "Bajor búza"}
    wb06 = {"Stílus": "Bajor búza", "Flokkuláció": "Alacsony"}
    assert param_differences(wheat, wb06) == ["flocculation: None vs 'Alacsony' (low)"]
    assert param_differences({"Flokkuláció": "low"}, {}) == ["flocculation: 'low' vs None"]
    assert (
        description_quote("22-26 °C (max tartomány: 16 - 32 °C)")
        == "'22-26 °C (max tartomány: 16 - 32 °C)' (\"max tartomány\": max range)"
    )
    assert description_quote("17-22°C") == "'17-22°C'"
