"""Style envelopes: the extraction job's checks (s3-style-fit Task 4). No LLM is called here;
the checks run on canned answers. Stack tests only read ref."""

import json
import tomllib
from pathlib import Path

import pytest

from loaders import style_envelopes as se
from loaders.db import connect

ROOT = Path(__file__).resolve().parent.parent

PROSE = (
    "Overall impression: A dark, roasty beer.\n\n"
    "Aroma: Moderate to strong roast aroma, often with a coffee\nquality. Low hop aroma, citrusy."
)

LOOKUPS = {
    "characters": {"coffee": "coffee", "citrusy": "citrus", "citrus": "citrus"},
    "tags": {"us": "US", "belgian": "belgian"},
    "ingredients": {"flakedrice": ["|Flaked Rice"], "roastedbarley": ["Viking Malt|Roasted Barley", "Weyermann|Roasted Barley"]},
}


def entry(**kw):
    base = {"dimension": "roast", "min": "medium", "max": "high", "characters": ["coffee"],
            "quote": "Moderate to strong roast aroma"}
    return {**base, **kw}


def check(sensory=(), ingredients=()):
    return se.check_answer(LOOKUPS, PROSE, {"sensory": list(sensory), "ingredients": list(ingredients)})


def test_quote_must_be_in_prose():
    _, problems = check([entry()])
    assert problems == []
    # a quote may span the line break in the prose (whitespace is folded)
    _, problems = check([entry(quote="often with a coffee quality.")])
    assert problems == []
    # a quote that is not there, or whose words were changed, is a problem
    _, problems = check([entry(quote="Strong roast aroma")])
    assert len(problems) == 1 and "verbatim" in problems[0]
    _, problems = check([entry(quote="")])
    assert len(problems) == 1
    # the same holds for an ingredient quote
    ing = {"role": "adjunct", "ingredient": None, "tag": None, "required": False, "min_pct": None, "quote": "made up"}
    _, problems = check(ingredients=[ing])
    assert len(problems) == 1 and "verbatim" in problems[0]


def test_scale_words_to_numbers():
    assert [se.SCALE[w] for w in
            ("none", "very low", "low", "medium-low", "medium", "medium-high", "high", "very high")] == list(range(8))
    _, problems = check([entry(min="moderate")])
    assert len(problems) == 1 and "not on the scale" in problems[0]


def test_unknown_character_kept():
    draft, problems = check([entry(characters=["coffee", "coffee", "burnt toast"])])
    assert problems == []  # an unresolved word is for the reviewer, not a problem
    assert draft["sensory"][0]["characters"] == ["coffee"]
    assert draft["sensory"][0]["unknown"] == ["burnt toast"]
    # ingredient names: resolved, unresolved and ambiguous
    def ing(**kw):
        return {"role": None, "ingredient": None, "tag": None, "required": False, "min_pct": None,
                "quote": "Low hop aroma", **kw}
    draft, problems = check(ingredients=[ing(ingredient="flaked rice"), ing(ingredient="Mystery Sugar"),
                                         ing(ingredient="Roasted Barley"), ing(tag="us"), ing(tag="mars"),
                                         ing(role="roast")])
    assert problems == []
    items = draft["ingredients"]
    assert items[0]["ingredient"] == "|Flaked Rice" and items[0]["unknown"] == []
    assert items[1]["unknown"] == ["Mystery Sugar"]
    assert items[2]["unknown"] == ["Roasted Barley"]  # two producers: the reviewer picks
    assert items[3]["tag"] == "US" and items[4]["unknown"] == ["mars"]
    assert items[5]["role"] == "roast"


def test_min_above_max_is_a_problem():
    _, problems = check([entry(min="high", max="low")])
    assert len(problems) == 1 and "above max" in problems[0]
    # a dimension given twice, and an ingredient with two kinds set
    _, problems = check([entry(), entry()])
    assert any("more than once" in p for p in problems)
    two = {"role": "adjunct", "ingredient": "flaked rice", "tag": None, "required": False, "min_pct": None,
           "quote": "Low hop aroma"}
    _, problems = check(ingredients=[two])
    assert len(problems) == 1 and "exactly one" in problems[0]


def style(**kw):
    return {"code": "20B", "reviewed": True, "problems": [], "sensory": [], "ingredient": [], **kw}


def test_reviewed_style_with_unknown_refused():
    se.refuse_unfinished(style())  # nothing open: fine
    for open_item in (
        style(sensory=[{"unknown": ["burnt toast"]}]),
        style(ingredient=[{"unknown": ["Mystery Sugar"]}]),
        style(problems=["roast: the quote is not a verbatim piece"]),
    ):
        with pytest.raises(ValueError, match="open items"):
            se.refuse_unfinished(open_item)


def test_prose_labels_present_fields_only():
    prose = se.style_prose({"aroma": "Fruity.", "flavor": "  ", "comments": None, "name": "X",
                            "characteristicingredients": "Pilsner malt."})
    assert prose == "Aroma: Fruity.\n\nCharacteristic ingredients: Pilsner malt."


def test_draft_toml_round_trips():
    draft = {"tries": 1, "problems": ["a \"quoted\" problem"], "sensory": [
                {"dimension": "roast", "min": "low", "max": "high", "characters": ["coffee"],
                 "unknown": ["burnt"], "quote": 'it said "roast"\nand more'}],
             "ingredients": [{"role": "roast", "required": True, "min_pct": 2.5, "unknown": [], "quote": "q"},
                             {"ingredient": "|Flaked Rice", "required": False, "min_pct": None, "unknown": [], "quote": "q"}]}
    text = se.draft_toml([("20B", "American Stout", draft)], "m", "2026-10-15")
    back = tomllib.loads(text)["style"][0]
    assert back["reviewed"] is False and back["extracted"]["tries"] == 1
    assert back["problems"] == draft["problems"]
    assert back["sensory"][0]["quote"] == 'it said "roast"\nand more'
    assert back["ingredient"][0]["min_pct"] == 2.5 and back["ingredient"][1]["ingredient"] == "|Flaked Rice"


def test_schema_dimensions_are_the_vocabulary_minus_colour_and_bitterness():
    from loaders import tags
    schema = json.loads(se.SCHEMA_PATH.read_text(encoding="utf-8"))
    enum = schema["properties"]["sensory"]["items"]["properties"]["dimension"]["enum"]
    vocab = {d["name"] for d in tags.read_vocab()["dimension"]}
    assert set(enum) == vocab - {"colour", "bitterness"}
    assert schema["properties"]["sensory"]["items"]["properties"]["min"]["enum"] == list(se.SCALE)


@pytest.mark.stack
def test_s3_styles_are_the_26():
    with open(ROOT / "evals" / "recipe_briefs.toml", "rb") as f:
        briefs = {b["style"] for b in tomllib.load(f)["brief"]}
    assert len(briefs) == 22
    expected = briefs | {"20C", "18A", "specialty-honey-beer", "20B"}
    assert len(expected) == 26
    assert set(se.S3_STYLES) == expected and len(se.S3_STYLES) == 26
    with connect() as conn:
        found = {c for (c,) in conn.execute("select code from ref.beer_style where code = any(%s)", (se.S3_STYLES,))}
        assert found == expected
        assert conn.execute("select count(*) from ref.beer_style where code = any(%s) and guide = 'BA'",
                            (se.S3_STYLES,)).fetchone()[0] == 3


def test_extraction_not_in_pipeline():
    """R4: the LLM extraction runs offline only; nothing in the workflows or prompts uses it."""
    for folder in ("n8n/workflows", "shared/prompts"):
        for path in (ROOT / folder).rglob("*"):
            if path.is_file():
                assert "style_envelope" not in path.read_text(encoding="utf-8", errors="ignore"), path
