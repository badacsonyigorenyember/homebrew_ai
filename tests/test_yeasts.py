from decimal import Decimal as D

import pytest
from psycopg.types.range import Range

from loaders.common import name_key
from loaders.yeast_products import PACK_SIZES, SKIPPED, YEASTS
from loaders.yeasts import flocculation, make_yeast, parse_range, tolerance, type_of


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
