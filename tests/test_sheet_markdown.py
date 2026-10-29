"""Code writes the recipe sheet (Task 6 of docs/work/m8-recipe-sheet-chat, db/057_sheet_markdown.sql).

The facts are those of a saved case (tests.test_sheet_facts.logged), rolled back; the answer and the sources are
made up, because the sheet only places the prose. Some tests change the facts, which are plain JSON, to reach a
case no sample brief has (an absent item, a model deviation).
"""

import copy
import json
import re
from decimal import ROUND_HALF_UP, Decimal

import pytest

from loaders.db import connect
from tests.test_sheet_facts import facts_of, logged

pytestmark = pytest.mark.stack

BOOK = {"chunk_id": 101, "topic": "mash", "title": "How to Brew", "url": None, "section_path": "Mash", "page": 263,
        "text": "Mash at 66 C."}
ARTICLE = {"chunk_id": 102, "topic": "boil", "title": "A web article", "url": "https://example.org/a",
           "section_path": "Boil", "page": None, "text": "Boil it."}
UNCITED = {"chunk_id": 103, "topic": "water", "title": "Unused", "url": None, "section_path": "Water", "page": 1,
           "text": "x"}
SOURCES = [BOOK, ARTICLE, UNCITED]
HEADINGS = ["Style", "Targets and results", "Fermentables", "Hops", "Yeast", "Extras",
            "How the amounts were worked out", "Water", "Mash", "Boil", "Fermentation", "Packaging",
            "Deviations", "Absent and unused items", "Notes", "Sources"]


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


@pytest.fixture(autouse=True)
def rolled_back(conn):
    yield
    conn.rollback()


def facts_for(conn, bid):
    rid, run_id = logged(conn, bid)
    return rid, facts_of(conn, run_id)


def answer_for(facts, cite=(101,)):
    return {"style_description": "A strong dark abbey ale.",
            "why": [{"key": c["key"], "text": f"Because of {c['label']}.", "cite": list(cite)}
                    for c in facts["choices"]],
            "notes": [{"text": "Keep the yeast warm enough.", "cite": [102]}]}


def sheet(conn, facts, answer=None, sources=SOURCES):
    answer = answer or answer_for(facts)
    return conn.execute("select app.sheet_markdown(%s::jsonb, %s::jsonb, %s::jsonb)",
                        [json.dumps(facts), json.dumps(sources), json.dumps(answer)]).fetchone()[0]


def sections(text):
    """{heading: body} of the "## " sections."""
    parts = re.split(r"^## (.+)$", text, flags=re.M)
    return dict(zip(parts[1::2], parts[2::2]))


def q(value, places):
    """A saved number at the display precision, as the sheet shows it."""
    return str(Decimal(str(value)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def lines(body):
    return [ln.strip() for ln in body.splitlines()]


def cells(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]


@pytest.mark.parametrize("bid", ["b01", "b10"])
def test_quantities_equal_saved_rows(conn, bid):
    rid, facts = facts_for(conn, bid)
    secs = sections(sheet(conn, facts))
    rec = conn.execute("select batch_l, efficiency_pct, og, fg, abv, ibu, srm from app.recipe where id = %s",
                       [rid]).fetchone()
    rows = {cells(r)[0]: cells(r) for r in secs["Targets and results"].splitlines() if r.startswith("| ")}
    for name, value, places in (("Batch (L)", rec[0], 1), ("Efficiency (%)", rec[1], 1), ("OG", rec[2], 3),
                                ("FG", rec[3], 3), ("ABV (%)", rec[4], 1), ("IBU", rec[5], 1), ("SRM", rec[6], 1)):
        assert rows[name][2] == q(value, places), name
    low, high = facts["style"]["ranges"]["og"]["low"], facts["style"]["ranges"]["og"]["high"]
    assert rows["OG"][3] == f"{q(low, 3)}–{q(high, 3)}"
    items = conn.execute("select raw_name, usage, time_min, pct, amount, unit, ingredient_id from app.recipe_item "
                         "where recipe_id = %s order by id", [rid]).fetchall()
    kinds = {i["ingredient_id"]: i["kind"] for i in facts["items"]}
    for name, usage, time_min, pct, amount, unit, ing in items:
        kind = kinds[ing]
        if kind == "fermentable":
            assert any(ln.startswith(f"- {q(amount, 2)} kg {name}, {q(pct, 1)} %") for ln in lines(secs["Fermentables"]))
        elif kind == "hop":
            assert any(ln.startswith(f"- {q(amount, 0)} g {name}, {usage.replace('_', ' ')} {q(time_min, 0)} min")
                       for ln in lines(secs["Hops"]))
        elif kind == "yeast":
            assert any(ln.startswith(f"- {q(amount, 0)} {unit} {name}") for ln in lines(secs["Yeast"]))
    for salt in facts["process"]["water"]["salts"]:
        assert any(ln.startswith(f"- {salt['name']} {q(salt['total_g'], 1)} g") for ln in lines(secs["Water"]))
    mash = facts["process"]["mash"]
    assert any(f"{q(mash['strike_c'], 1)} °C" in ln and f"{q(mash['volumes']['strike_l'], 1)} L" in ln
               for ln in lines(secs["Mash"]))
    pack = facts["process"]["packaging"]
    assert any(f"{q(pack['co2']['volumes'], 2)} volumes" in ln for ln in lines(secs["Packaging"]))
    assert any(ln.startswith(f"- Priming: {q(pack['priming']['g'], 0)} g") for ln in lines(secs["Packaging"]))


def test_section_order(conn):
    _, facts = facts_for(conn, "b10")
    text = sheet(conn, facts)
    assert re.findall(r"^## (.+)$", text, flags=re.M) == HEADINGS
    assert text.startswith("# ")


def test_labels_shown(conn):
    _, facts = facts_for(conn, "b10")
    secs = sections(sheet(conn, facts))
    assert "estimate" in secs["Yeast"]
    water = secs["Water"]
    assert "basis listed" in water and "from style" in water and "fallback" not in water
    assert facts["process"]["water"]["acid"]["text"] in water
    assert "estimate, unverified against Bru'n Water" in water
    assert "basis inferred" in secs["Packaging"] and "from style" in secs["Packaging"]
    # b05's water row is a fallback, and the sheet says so
    _, facts5 = facts_for(conn, "b05")
    assert facts5["process"]["water"]["target"]["fallback"] is True
    assert "fallback row" in sections(sheet(conn, facts5))["Water"]


def test_how_amounts_were_worked_out(conn):
    _, facts = facts_for(conn, "b10")
    body = sections(sheet(conn, facts))["How the amounts were worked out"]
    assert "the pitch rate is set (M7)" not in body  # the yeast placeholder line is replaced by step 14's
    assert facts["step10"]["values_used"][0]["because"] in body
    assert facts["step10"]["colour_because"] in body
    assert facts["step10"]["og_used"]["because"] in body
    assert facts["step10"]["rounding"]["because"] in body
    assert facts["process"]["fermentation"]["pitch"][0]["because"] in body


def test_deviations_box(conn):
    _, facts = facts_for(conn, "b05")
    facts["deviations"].append({"subject": "hop stand", "kind": "conflict", "level": None,
                                "requested_by": "model", "note": "the model added it"})
    body = sections(sheet(conn, facts))["Deviations"]
    mismatch = next(ln for ln in lines(body) if "mismatch" in ln)
    assert cells(mismatch)[0] == "20C Imperial Stout with ABV 4" and cells(mismatch)[3] == "you asked"
    model = next(ln for ln in lines(body) if ln.startswith("| hop stand"))
    assert cells(model)[3] == "the pipeline chose" and cells(model)[4] == "the model added it"
    # none
    facts["deviations"] = []
    assert "No deviations" in sections(sheet(conn, facts))["Deviations"]
    # the style section names the mismatch and the alternatives
    _, facts5 = facts_for(conn, "b05")
    style = sections(sheet(conn, facts5))["Style"]
    assert "20C Imperial Stout" in style and "15B Irish Stout" in style and "16A" in style


def test_inventory_named(conn):
    _, facts = facts_for(conn, "b10")
    secs = sections(sheet(conn, facts))
    def line(sec, name):
        return next(ln for ln in lines(secs[sec]) if name in ln and ln.startswith("- "))
    assert 'from your inventory ("dark candi sugar")' in line("Fermentables", "Brown Candi Sugar")
    assert 'from your inventory ("Munich malt")' in line("Fermentables", "Munich Dark Malt")
    assert 'from your inventory ("abbey yeast")' in line("Yeast", "Abbaye")
    assert "inventory" not in line("Fermentables", "Bohemian Pilsner Malt")


def test_absent_special_b(conn):
    _, facts = facts_for(conn, "b10")
    facts["step9"]["absent"] = [{"word": "Special B", "kind": None,
                                 "reason": 'no product in the catalogue matches "Special B"'}]
    facts["step8"]["absent"] = [{"word": "Saaz", "kind": "hop", "reason": 'every product that "Saaz" names is excluded'}]
    facts["step7"]["unused_inventory"] = [{"word": "rye malt", "reason": "it conflicts with the style"}]
    body = sections(sheet(conn, facts))["Absent and unused items"]
    special = next(ln for ln in lines(body) if "Special B" in ln)
    assert "not in the catalogue" in special and "shared/ingredients/" in special and "ask again" in special
    assert "drop the exclusion" in next(ln for ln in lines(body) if "Saaz" in ln)
    rye = next(ln for ln in lines(body) if "rye malt" in ln)
    assert "it conflicts with the style" in rye and "keep it for another brew" in rye
    # nothing absent: the section says so
    _, plain = facts_for(conn, "b10")
    assert "None" in sections(sheet(conn, plain))["Absent and unused items"]


def test_citation_format(conn):
    _, facts = facts_for(conn, "b10")
    answer = answer_for(facts, cite=())
    by_key = {w["key"]: w for w in answer["why"]}
    by_key["style"]["cite"] = [102]
    by_key["mash"]["cite"] = [101, 102]
    answer["notes"][0]["cite"] = [101]
    secs = sections(sheet(conn, facts, answer))
    # numbers follow first use on the sheet: the style line cites 102 first
    assert "Because of 26B Belgian Dubbel. [1]" in secs["Style"]
    assert "Because of Mash. [1, 2]" in secs["Mash"]
    assert "Keep the yeast warm enough. [2]" in secs["Notes"]
    src = lines(secs["Sources"])
    assert "1. A web article — Boil — https://example.org/a" in src
    assert "2. How to Brew, PDF p. 263 — Mash" in src
    assert not any("Unused" in ln for ln in src)
