from decimal import Decimal as D

import pytest
from psycopg.types.range import Range

from loaders.common import name_key
from loaders.malt_products import IGNORE_HOPLINE_EXTRACT, PRODUCTS, SKIPPED
from loaders.malts import build, max_pct_from_text, merge, parse_hopline_spec, potential_sg

# Inline fixtures: spec text as fetch_hopline captures it (shortened, wording kept).
VIKING_PILSNER = {
    "sku": "100010",
    "url": "https://www.hopline.hu/viking-pilsner-malata",
    "name": "Viking Pilsner maláta",
    "spec": "Főkategória Alapanyagok Maláták Viking Pilsner maláta EBC: 3.0 - 4.2 "
    "Viking Pilsner kétsoros tavaszi árpából készül. Ajánlott sörtípusok: minden fajta sör "
    "Kihozatal: min 80% Felhasználás: 100% Származási hely: Finnország",
}

SIMPSONS_MARRIS_OTTER = {
    "sku": "101290",
    "url": "https://www.hopline.hu/simpsons-marris-otter",
    "name": "Simpsons Marris Otter",
    "spec": "Főkategória Alapanyagok Maláták Simpsons Marris Otter EBC: 5.5 - 7.5 "
    "A Crisp Marris Otter kiváló brit maláta. Kihozatal : min 79 % Felhasználás : 100 % "
    "Származási hely : Anglia",
}

SIMPSONS_CRYSTAL_T50 = {
    "sku": "101520",
    "url": "https://www.hopline.hu/simpsons-crystal-t50-malata",
    "name": "Simpsons Crystal T50 maláta",
    "spec": "Főkategória Feltöltött termékek Simpsons Crystal T50 maláta EBC: 139 - 154 "
    "A Simpsons Crystal T50 kiegyensúlyozott karamellás édességet ad. "
    "Kihozatal : min 70 % Felhasználás : 5-10 % Származási hely : Egyesült Királyság",
}

VIKING_SPRAU = {
    "sku": "101480",
    "url": "https://www.hopline.hu/viking-sprau-malt",
    "name": "Viking Sprau Malt",
    "spec": "Főkategória Alapanyagok Maláták Viking Sprau Malt EBC: 4.0 "
    "A Viking Sprau egy innovatív, malátázott mezei bab. "
    "Kihozatal : min 81% Felhasználás : max 15% Származási hely : Lengyelország",
}


def test_potential_sg():
    assert potential_sg(D("80.5")) == D("1.0372")
    assert potential_sg(D("79")) == D("1.0365")
    assert potential_sg(None) is None


def test_max_pct_from_text():
    assert max_pct_from_text("100%") == 100
    assert max_pct_from_text("100 %") == 100
    assert max_pct_from_text("max. 10%") == 10
    assert max_pct_from_text("max 15%") == 15
    assert max_pct_from_text("1-2%") == 2
    assert max_pct_from_text("10-15 %") == 15
    assert max_pct_from_text("50% (20%ban prémium lágerekben)") == 50
    assert max_pct_from_text("? %") is None
    assert max_pct_from_text("- %") is None
    assert max_pct_from_text("Recommended addition: up to 100%") == 100
    assert max_pct_from_text("Dosage rate up to 20% (30%.)") == 20
    assert max_pct_from_text("Use in small amounts (<10%).") == 10
    assert max_pct_from_text("Typical rate of usage is around 50% of the grist") is None
    assert max_pct_from_text(None) is None


def test_hopline_spec():
    spec = parse_hopline_spec(VIKING_PILSNER["spec"])
    assert spec["ebc"] == Range(D("3.0"), D("4.2"), "[]")
    assert spec["extract_pct"] == 80
    assert spec["max_pct"] == 100

    assert parse_hopline_spec("EBC: 4.0 A Viking")["ebc"] == Range(D("4.0"), D("4.0"), "[]")
    assert parse_hopline_spec("EBC: max 2.0 A Bestmalz")["ebc"] == Range(None, D("2.0"), "(]")
    assert parse_hopline_spec("EBC: - A Viking Enzim maláta")["ebc"] is None
    assert parse_hopline_spec("EBC: 2.5 - 12 Kihozatal : ? % Felhasználás : 1-5 %")["extract_pct"] is None
    assert parse_hopline_spec("Felhasználá s: 100 % Származási hely : Anglia")["max_pct"] == 100
    assert parse_hopline_spec(None) == {"ebc": None, "extract_pct": None, "max_pct": None}


def test_catalogue_wins_hopline_fills():
    catalogue = {"ebc_min": 4.4, "ebc_max": 6.6, "extract_pct": None, "usage": None}
    f = merge(SIMPSONS_MARRIS_OTTER, "Simpsons Malt", catalogue, "Finest Pale Ale Maris Otter")
    assert f.name == "Finest Pale Ale Maris Otter"
    assert f.producer == "Simpsons Malt"
    assert f.ebc == Range(D("4.4"), D("6.6"), "[]")
    assert f.extract_dbfg_pct == 79
    assert f.potential_sg == D("1.0365")
    assert f.max_pct == 100
    assert f.field_source == {
        "ebc": "simpsons-malt-2025",
        "extract_dbfg_pct": "hopline-malts",
        "potential_sg": "hopline-malts",
        "max_pct": "hopline-malts",
    }
    assert set(f.raw) == {"hopline-malts", "simpsons-malt-2025"}
    assert f.raw["simpsons-malt-2025"] is catalogue
    assert f.source_slug == "simpsons-malt-2025"


def test_no_extract_stays_null():
    catalogue = {"ebc_min": 139, "ebc_max": 154, "extract_pct": None, "usage": None}

    # No extract in either source.
    no_kihozatal = dict(SIMPSONS_CRYSTAL_T50, spec="EBC: 139 - 154 Felhasználás : 5-10 %")
    f = merge(no_kihozatal, "Simpsons Malt", catalogue, "Crystal T50")
    assert f.extract_dbfg_pct is None
    assert f.potential_sg is None
    assert "extract_dbfg_pct" not in f.field_source
    assert "potential_sg" not in f.field_source

    # Hopline's "min 70 %" is ignored when asked (user decision for 3 Simpsons crystals).
    f = merge(SIMPSONS_CRYSTAL_T50, "Simpsons Malt", catalogue, "Crystal T50",
              ignore_hopline_extract=True)
    assert f.extract_dbfg_pct is None
    assert f.potential_sg is None
    assert "extract_dbfg_pct" not in f.field_source
    assert "potential_sg" not in f.field_source
    assert f.ebc == Range(D("139"), D("154"), "[]")
    assert f.max_pct == 10
    assert f.field_source == {"ebc": "simpsons-malt-2025", "max_pct": "hopline-malts"}


def test_hopline_only():
    f = merge(VIKING_SPRAU, "Viking Malt", None, "Sprau Malt")
    assert f.source_slug == "hopline-malts"
    assert f.ebc == Range(D("4.0"), D("4.0"), "[]")
    assert f.extract_dbfg_pct == 81
    assert f.max_pct == 15
    assert set(f.field_source) == {"ebc", "extract_dbfg_pct", "potential_sg", "max_pct"}
    assert set(f.field_source.values()) == {"hopline-malts"}
    assert set(f.raw) == {"hopline-malts"}


def test_product_map():
    producers = [producer for producer, _, _ in PRODUCTS.values()]
    assert len(PRODUCTS) == 74
    assert producers.count("Weyermann") == 37
    assert producers.count("Viking Malt") == 32
    assert producers.count("Simpsons Malt") == 5
    assert len(SKIPPED) == 8
    assert not set(PRODUCTS) & set(SKIPPED)
    assert IGNORE_HOPLINE_EXTRACT <= set(PRODUCTS)

    # Two names with one key would make the upsert overwrite one malt with another.
    keys = [(producer, name_key(name)) for producer, _, name in PRODUCTS.values()]
    assert len(keys) == len(set(keys))


def test_unknown_sku_raises():
    unknown = dict(VIKING_SPRAU, sku="999999", name="Új maláta")
    with pytest.raises(ValueError, match="999999"):
        build({"products": [unknown]}, [])
