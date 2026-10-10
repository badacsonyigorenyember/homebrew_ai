from decimal import Decimal as D

import pytest
from psycopg.types.range import Range

from loaders.hops import make_hop, origin_codes, parse_figure, purpose_of


def r(lo, hi):
    return Range(D(lo), D(hi), "[]")


# Inline fixtures: product dicts as fetch_hopline --hops writes them (shortened, wording kept).
CITRA = {
    "sku": "200750-cs",
    "url": "https://www.hopline.hu/citra-komlo-100g",
    "name": "Citra komló 100g",
    "spec": "Citra komló 100g Alfa-sav Béta-sav Co-Humolone Olaj tartalom",
    "table": {
        "Alfa-sav": "10-15 %",
        "Béta-sav": "3-4.5 %",
        "Co-Humolone": "20-35 %",
        "Olaj tartalom": "1.5-3 %",
    },
    "params": {"Ország": "USA", "Alfasav": "11 – 13 %"},
}

CITRA_CATEGORIES = {"aroma": ["200750-cs"], "bittering": ["200750-cs"], "dual": ["200750-cs"]}


def nectaron(sku, alpha):
    return {
        "sku": sku,
        "url": f"https://www.hopline.hu/nectaron-{sku}",
        "name": "Nectaron komló",
        "spec": "Nectaron komló",
        "table": {"Alfa-sav": alpha, "Béta-sav": "3.5-5.5 %", "Olaj tartalom": "1.5-2.4 %"},
        "params": {"Ország": "Új-Zéland"},
    }


DELTA = {
    "sku": "200269",
    "url": "https://www.hopline.hu/falconers-flight-komlo-1kg",
    "name": "Delta komló 1kg",
    "spec": "Delta komló 1kg",
    "table": {"Alfa-sav": "9.5-12 %", "Béta-sav": "4-5 %", "Olaj tartalom": "1.6-2.5 %"},
    "params": {"Ország": "USA"},
}


def test_parse_figure():
    assert parse_figure("10-15 %") == r("10", "15")
    assert parse_figure("9.5 - 11.5 %") == r("9.5", "11.5")
    assert parse_figure("5.8-6.3%") == r("5.8", "6.3")
    assert parse_figure("0,85 %") == r("0.85", "0.85")
    assert parse_figure("~ 18.5 %") == r("18.5", "18.5")
    assert parse_figure("16,5%") == r("16.5", "16.5")
    assert parse_figure("1.6-2.5 ml") == r("1.6", "2.5")
    assert parse_figure("2,5 – 5 %") == r("2.5", "5")
    for empty in ("? %", "%", "- %", "", None):
        assert parse_figure(empty) is None
    with pytest.raises(ValueError, match="lots"):
        parse_figure("lots")


def test_origin_codes():
    assert origin_codes("Anglia") == ["GB"]
    assert origin_codes("USA") == ["US"]
    assert origin_codes(None) is None
    with pytest.raises(ValueError, match="Mars"):
        origin_codes("Mars")


def test_purpose_of():
    assert purpose_of(["1"], {"aroma": [], "bittering": [], "dual": ["1"]}) == "dual"
    assert purpose_of(["1"], {"aroma": ["1"], "bittering": ["1"], "dual": []}) == "dual"
    assert purpose_of(["1"], {"aroma": [], "bittering": ["1"], "dual": []}) == "bittering"
    assert purpose_of(["1"], {"aroma": ["1"], "bittering": [], "dual": []}) == "aroma"
    assert purpose_of(["1"], {"aroma": ["2"], "bittering": [], "dual": []}) is None
    # The 100 g page only in aroma, its 1 kg page only in bittering: one hop, both uses.
    assert (
        purpose_of(["1-cs", "1"], {"aroma": ["1-cs"], "bittering": ["1"], "dual": []}) == "dual"
    )


def test_citra():
    hop = make_hop("Citra", CITRA, [], CITRA_CATEGORIES)
    assert hop.name == "Citra"
    assert hop.alpha_pct == r("10", "15")
    assert hop.beta_pct == r("3", "4.5")
    assert hop.total_oil_ml_100g == r("1.5", "3")
    assert hop.origins == ["US"]
    assert hop.purpose == "dual"
    assert hop.field_source == {
        "origins": "hopline-hops",
        "purpose": "hopline-hops",
        "alpha_pct": "hopline-hops",
        "beta_pct": "hopline-hops",
        "total_oil_ml_100g": "hopline-hops",
    }
    assert hop.raw == {"hopline-hops": {"200750-cs": CITRA}}


def test_alpha_falls_back_to_data_block():
    unknown = {**CITRA, "table": {**CITRA["table"], "Alfa-sav": "? %"}}
    hop = make_hop("Citra", unknown, [], CITRA_CATEGORIES)
    assert hop.alpha_pct == r("11", "13")
    assert hop.field_source["alpha_pct"] == "hopline-hops"

    no_block = {**unknown, "params": {"Ország": "USA"}}
    hop = make_hop("Citra", no_block, [], CITRA_CATEGORIES)
    assert hop.alpha_pct is None
    assert "alpha_pct" not in hop.field_source


def test_pack_sizes_and_null_figures():
    main = nectaron("200880-cs", "9.5 - 11.5 %")
    extras = [nectaron("200880", "9.5 - 13 %"), nectaron("200872", "9.5 - 13 %")]
    categories = {"aroma": ["200880"], "bittering": [], "dual": []}
    hop = make_hop("Nectaron", main, extras, categories)
    assert hop.alpha_pct == r("9.5", "11.5")
    assert hop.purpose == "aroma"
    assert set(hop.raw["hopline-hops"]) == {"200880-cs", "200880", "200872"}

    categories = {"aroma": ["200269"], "bittering": [], "dual": ["200269"]}
    hop = make_hop("Delta", DELTA, [], categories, null_figures=True)
    assert hop.alpha_pct is None
    assert hop.beta_pct is None
    assert hop.total_oil_ml_100g is None
    assert hop.origins == ["US"]
    assert hop.purpose == "dual"
    assert set(hop.field_source) == {"origins", "purpose"}
