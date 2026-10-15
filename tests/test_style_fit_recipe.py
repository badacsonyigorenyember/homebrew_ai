"""app.style_fit_recipe on whole recipes (Task 9 of s3-style-fit): the required check, the
recipe-total min check, and the 22 reference recipes. Needs the stack."""

import copy
import json

import pytest

from loaders.db import connect
from tests.test_reference_recipes import RECIPES, build_input, ingredient_id

pytestmark = pytest.mark.stack

# Lines the user has decided to accept: (brief id, ingredient name) -> (decision, date).
# The briefs ask for numbers outside the style range (b08 about 50 IBU, b18 20 SRM).
_B08 = "the brief asks for about 50 IBU, above 5D's range; user, 2026-10-15"
_B18 = "the brief asks for 20 SRM, above 15A's range; user, 2026-10-15"
ACCEPTED_LINES: dict[tuple[str, str], tuple[str, str]] = {
    ("b08", "Magnum"): (_B08, "2026-10-15"),
    ("b08", "Hallertau Mittelfrüh"): (_B08, "2026-10-15"),
    ("b18", "Caramel 100 Malt"): (_B18, "2026-10-15"),
    ("b18", "Roasted Barley"): (_B18, "2026-10-15"),
    ("b18", "Carafa Special Type 1"): (_B18, "2026-10-15"),
}

# Recipe totals the user has decided to accept: (brief id, dimension) -> (decision, date).
ACCEPTED_TOTALS: dict[tuple[str, str], tuple[str, str]] = {}

# The briefs' own deviations (b16 rice, b19 honey, b20 lactose): out of style by design.
DEVIATIONS = {("b16", "Flaked Rice"), ("b19", "Honey"), ("b20", "Lactose")}


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def fit(conn, recipe_input):
    return conn.execute(
        "select app.style_fit_recipe(%s::jsonb)", (json.dumps(recipe_input),)).fetchone()[0]


def recipe(brief):
    return next(r for r in RECIPES if r["brief"] == brief)


def test_15b_needs_roast(conn):
    with_roast = fit(conn, build_input(conn, recipe("b05")))
    roast = [r for r in with_roast["required"] if "roast" in r["requirement"]]
    assert roast and all(r["met"] for r in roast)

    swapped = copy.deepcopy(recipe("b05"))
    for f in swapped["fermentable"]:
        if f["name"] == "Roasted Barley":
            f["producer"], f["name"] = "Weyermann", "Pale Ale Malt"
    without = fit(conn, build_input(conn, swapped))
    roast = [r for r in without["required"] if "roast" in r["requirement"]]
    assert roast and not any(r["met"] for r in roast)


def test_reference_recipe_lines(conn):
    failures = []
    for rec in RECIPES:
        result = fit(conn, build_input(conn, rec))
        for line in result["lines"]:
            if line["level"] is None:
                failures.append((rec["brief"], line["name"], "no level", line["because"]))
            elif (line["level"] in ("out_of_style", "changes_style")
                  and (rec["brief"], line["name"]) not in DEVIATIONS
                  and (rec["brief"], line["name"]) not in ACCEPTED_LINES):
                failures.append((rec["brief"], line["name"], line["level"], line["because"]))
    assert not failures, "\n".join(map(str, failures))


def test_deviation_lines_are_flagged(conn):
    for brief, name in sorted(DEVIATIONS):
        result = fit(conn, build_input(conn, recipe(brief)))
        line = next(l for l in result["lines"] if l["name"] == name)
        assert line["level"] == "out_of_style", (brief, name, line)


def test_recipe_too_little(conn):
    # an 18B recipe with only a 60-minute bittering hop has no hop aroma or flavour
    bittering_only = copy.deepcopy(recipe("b16"))
    bittering_only["hop"] = [h for h in bittering_only["hop"] if h["minutes"] == 60]
    result = fit(conn, build_input(conn, bittering_only))
    assert "hop_aroma" in [t["dimension"] for t in result["too_little"]]
    # b16's own recipe is within one level of the style's minimum
    assert fit(conn, build_input(conn, recipe("b16")))["too_little"] == []


def test_reference_recipe_totals(conn):
    found = []
    for rec in RECIPES:
        result = fit(conn, build_input(conn, rec))
        for t in result["too_little"]:
            if (rec["brief"], t["dimension"]) not in ACCEPTED_TOTALS:
                found.append((rec["brief"], rec["style_code"], t["dimension"], t["level"], t["min"]))
    assert not found, "\n".join(map(str, found))


def test_colour_lower_bound(conn):
    """A fermentable without colour (Honey) counts as 0 EBC: the SRM is a lower bound, said in the
    because, and 'too much colour' needs even the lower bound above the style maximum."""
    ok = fit(conn, build_input(conn, recipe("b19")))
    caramunich = next(x for x in ok["lines"] if x["name"] == "Caramunich Type 2")
    assert caramunich["level"] != "out_of_style"
    assert "lower bound, no colour for Honey" in caramunich["because"]

    dark = copy.deepcopy(recipe("b19"))
    for f in dark["fermentable"]:
        if f["name"] == "Caramunich Type 2":
            f["pct"] = 8
        if f["name"] == "Roasted Barley":
            f["pct"] = 2
        if f["name"] == "Finest Pale Ale Maris Otter":
            f["pct"] = 80
    lines = {x["name"]: x for x in fit(conn, build_input(conn, dark))["lines"]}
    for name in ("Caramunich Type 2", "Roasted Barley"):
        assert lines[name]["level"] == "out_of_style"
        assert "too much colour: at least" in lines[name]["because"]
        assert "no colour for Honey" in lines[name]["because"]
