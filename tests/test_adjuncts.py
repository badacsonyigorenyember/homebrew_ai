import copy
from decimal import Decimal as D

import pytest
from psycopg.types.range import Range

from loaders.adjunct_products import ALIASES, PACK_SIZES, PALMER, PALMER_ONLY, PRODUCTS, SKIPPED
from loaders.adjuncts import HOPLINE, PALMER_SLUG, build, extract_pct_from_ppg


def product(sku, name, text):
    return {"sku": sku, "url": f"https://www.hopline.hu/{sku}", "name": name, "text": text}


# Inline fixture: the 14 products fetch_hopline --adjuncts wrote on 2026-10-11, with each page
# text shortened but the quoted words kept.
HOPLINE_ADJUNCTS = {
    "fetched": "2026-10-11",
    "products": [
        product("400130", "Búzapehely 100g", "Főkategória Alapanyagok Maláták Búzapehely 100g"),
        product("400270", "Kukoricapehely 100g", "Főkategória Alapanyagok Maláták Kukoricapehely 100g"),
        product("400160", "Rizshéj 1 liter", "Főkategória Alapanyagok Maláták Rizshéj 1 liter"),
        product("400161-cs", "Rizshéj 5 liter", "Főkategória Alapanyagok Maláták Rizshéj 5 liter"),
        product("400150", "Zabpehely 100g", "Főkategória Alapanyagok Maláták Zabpehely 100g"),
        product("400110", "Árpa pehely 100g", "Főkategória Alapanyagok Maláták Árpa pehely 100g"),
        product("400290", "Chit Malt - 100g", "Főkategória Alapanyagok Maláták Chit Malt - 100g"),
        product(
            "400100",
            "Rizspehely 100g",
            "Főkategória Alapanyagok Maláták Rizspehely 100g A gyakorlatban akár 40%-ban is "
            "használhatunk rizspehelyt, azonban a legtöbb recept kb 20%-os tömegaránnyal számol.",
        ),
        product("400120", "Rozs pehely 100g", "Főkategória Alapanyagok Maláták Rozs pehely 100g"),
        product(
            "400091-cs",
            "Barna kandiscukor 500g",
            "Főkategória Alapanyagok Barna kandiscukor 500g A kandiscukor színértéke hasonló a "
            "malátákéhoz. Szín: 225 EBC Ajánlott sörtípus: belga sötét sörök",
        ),
        product("400081-cs", "Fehér kandiscukor 600g", "Főkategória Alapanyagok Fehér kandiscukor 600g"),
        product("400370", "Fruktóz 500g", "Főkategória Alapanyagok Fruktóz 500g"),
        product(
            "400031-cs",
            "Laktóz 1kg",
            "Főkategória Összes termék Laktóz 1kg A tejcukor a nem erjeszthető cukrok "
            "csoportjába tartozik, ezáltal az erjedés után is visszamarad.",
        ),
        product(
            "400030-cs",
            "Laktóz 250g",
            "Főkategória Összes termék Laktóz 250g A tejcukor a nem erjeszthető cukrok "
            "csoportjába tartozik, ezáltal az erjedés után is visszamarad.",
        ),
    ],
}


def by_name(items):
    return {item.name: item for item in items}


def test_extract_pct_from_ppg():
    assert extract_pct_from_ppg(D("46")) == D("100.0")
    assert extract_pct_from_ppg(D("38")) == D("82.6")


def test_build_values_per_adjunct():
    items = by_name(build(HOPLINE_ADJUNCTS))
    assert sorted(items) == [
        "Brown Candi Sugar",
        "Flaked Barley",
        "Flaked Corn",
        "Flaked Oats",
        "Flaked Rice",
        "Honey",
        "Lactose",
    ]

    for name, extract in [
        ("Flaked Oats", "70.0"),
        ("Flaked Corn", "84.0"),
        ("Flaked Rice", "82.0"),
        ("Flaked Barley", "70.0"),
    ]:
        flake = items[name]
        assert flake.extract_dbfg_pct == D(extract)
        assert flake.field_source["extract_dbfg_pct"] == PALMER_SLUG
        assert flake.fermentability == "normal"
        assert flake.source_slug == HOPLINE
    # colour: the producer's figure, written with its source (hopline prints none)
    assert items["Flaked Barley"].ebc == Range(D("0"), D("3.2"), "[]")
    assert items["Flaked Oats"].ebc == Range(D("0"), D("3.2"), "[]")
    assert items["Flaked Corn"].ebc == Range(D("1.576"), D("1.576"), "[]")
    assert items["Flaked Rice"].ebc == Range(D("1.97"), D("1.97"), "[]")
    for name in ["Flaked Barley", "Flaked Oats", "Flaked Corn", "Flaked Rice"]:
        assert items[name].field_source["ebc"] == items[name].raw["colour"]["source"]
    assert items["Flaked Rice"].max_pct == D("40")
    assert items["Flaked Rice"].field_source["max_pct"] == HOPLINE
    assert items["Flaked Oats"].max_pct is None

    candi = items["Brown Candi Sugar"]
    assert candi.extract_dbfg_pct == D("100.0")
    assert candi.field_source["extract_dbfg_pct"] == PALMER_SLUG
    assert candi.ebc == Range(D("225"), D("225"), "[]")
    assert candi.field_source["ebc"] == HOPLINE
    assert candi.fermentability == "full"
    assert candi.field_source["fermentability"] == PALMER_SLUG

    lactose = items["Lactose"]
    assert lactose.extract_dbfg_pct == D("100.0")
    assert lactose.field_source["extract_dbfg_pct"] == PALMER_SLUG
    assert lactose.fermentability == "none"
    assert lactose.field_source["fermentability"] == HOPLINE
    assert lactose.ebc is None
    assert [page["sku"] for page in lactose.raw["hopline-adjuncts pack sizes"]] == ["400031-cs"]

    honey = items["Honey"]
    assert honey.extract_dbfg_pct == D("82.6")
    assert honey.fermentability == "full"
    assert honey.field_source == {"extract_dbfg_pct": PALMER_SLUG, "fermentability": PALMER_SLUG}
    assert honey.source_slug == PALMER_SLUG
    assert HOPLINE not in honey.raw
    assert honey.raw[PALMER_SLUG] == PALMER["Honey"]


def test_every_filled_field_has_a_source():
    for item in build(HOPLINE_ADJUNCTS):
        filled = {
            field
            for field, value in [
                ("extract_dbfg_pct", item.extract_dbfg_pct),
                ("ebc", item.ebc),
                ("max_pct", item.max_pct),
            ]
            if value is not None
        }
        if item.fermentability != "normal":
            filled.add("fermentability")
        assert set(item.field_source) == filled, item.name


def test_unmapped_sku_raises():
    hopline = copy.deepcopy(HOPLINE_ADJUNCTS)
    hopline["products"].append(product("499999", "Új pehely 100g", "Főkategória Új pehely"))
    with pytest.raises(ValueError, match="499999"):
        build(hopline)


def test_hopline_figure_not_on_page_raises():
    hopline = copy.deepcopy(HOPLINE_ADJUNCTS)
    for item in hopline["products"]:
        if item["sku"] == "400100":
            item["text"] = "Főkategória Alapanyagok Maláták Rizspehely 100g"
    with pytest.raises(ValueError, match="400100"):
        build(hopline)


def test_maps_do_not_overlap():
    assert not set(PRODUCTS) & set(PACK_SIZES)
    assert not set(PRODUCTS) & set(SKIPPED)
    assert not set(PACK_SIZES) & set(SKIPPED)
    assert set(PACK_SIZES.values()) <= set(PRODUCTS)
    rows = [row for _, row, _ in PRODUCTS.values()] + list(PALMER_ONLY.values())
    assert all(row in PALMER for row in rows)


def test_aliases_name_mapped_products():
    product_names = {name for name, _, _ in PRODUCTS.values()}
    assert ALIASES and set(ALIASES) <= product_names


@pytest.fixture(scope="module")
def conn():
    from loaders.db import connect

    connection = connect()
    yield connection
    connection.close()


@pytest.mark.stack
def test_dark_candi_sugar_alias(conn):
    brown = conn.execute(
        "select id from ref.ingredient where kind = 'fermentable' and name = 'Brown Candi Sugar'"
    ).fetchone()[0]
    rows = conn.execute(
        "select ingredient_id, rule from app.resolve_ingredient('dark candi sugar')"
    ).fetchall()
    assert rows == [(brown, "alias")]
    by_name = conn.execute("select ingredient_id from app.resolve_ingredient('candi sugar')").fetchall()
    assert (brown,) in by_name
