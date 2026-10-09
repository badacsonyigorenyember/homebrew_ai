from decimal import Decimal as D
from psycopg.types.range import Range
from loaders.styles import parse_bjcp, parse_ba

# Inline fixtures, copied from the measured styles.json / ba_styles.json shapes.
BJCP_21A = {
    "name": "American IPA", "number": "21A", "category": "IPA", "categorynumber": "21",
    "overallimpression": "A decidedly hoppy and bitter, moderately strong American pale ale.",
    "aroma": "A prominent to intense hop aroma.",
    "characteristicingredients": "Pale ale or 2-row brewers malt as the base.",
    "ogmin": "1.056", "ogmax": "1.070", "fgmin": "1.008", "fgmax": "1.014",
    "ibumin": "40", "ibumax": "70", "srmmin": "6", "srmmax": "14",
    "abvmin": "5.5", "abvmax": "7.5",
}

BJCP_27A = {
    "name": "Historical Beer", "number": "27A", "category": "Historical Beer",
    "categorynumber": "27", "aroma": "", "characteristicingredients": "",
    "ogmin": "", "ogmax": "", "fgmin": "", "fgmax": "",
    "ibumin": "", "ibumax": "", "srmmin": "", "srmmax": "", "abvmin": "", "abvmax": "",
}

BA_OPEN_SRM = {
    "name": "Open SRM Style", "number": "x", "category": "Test",
    "ogmin": 1.040, "ogmax": 1.050, "srmmin": 5.0, "srmmax": None,
}

BA_ORDINARY_BITTER = {
    "name": "Ordinary Bitter", "number": "ordinary-bitter", "category": "British Origin Ale Styles",
    "ogmin": 1.033, "ogmax": 1.038, "fgmin": 1.006, "fgmax": 1.012,
    "ibumin": 20.0, "ibumax": 35.0, "srmmin": 5.0, "srmmax": 12.0,
    "abvmin": 3.0, "abvmax": 4.1,
}


def test_bjcp_21a():
    [style] = parse_bjcp([BJCP_21A])
    assert style.guide == "BJCP" and style.edition == "2021" and style.code == "21A"
    assert style.og == Range(D("1.056"), D("1.070"), "[]")
    assert style.ibu == Range(D("40"), D("70"), "[]")
    assert style.category == "IPA" and style.category_code == "21"
    assert style.characteristic_ingredients == "Pale ale or 2-row brewers malt as the base."
    assert "aroma" in style.raw


def test_bjcp_specialty_no_vitals():     # Review focus 2
    styles = parse_bjcp([BJCP_27A])
    assert len(styles) == 1
    style = styles[0]
    assert style.code == "27A"
    assert (style.og, style.fg, style.ibu, style.srm, style.abv) == (None, None, None, None, None)
    assert style.characteristic_ingredients is None


def test_ba_open_srm():                  # Review focus 1
    [style] = parse_ba([BA_OPEN_SRM])
    assert style.srm == Range(D("5.0"), None, "[)")


def test_ba_code_is_slug():
    [style] = parse_ba([BA_ORDINARY_BITTER])
    assert style.guide == "BA" and style.edition == "2026"
    assert style.code == "ordinary-bitter"
