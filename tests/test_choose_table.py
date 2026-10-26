"""The steps 6-9 candidate table and its prompt text (db/042_choose_table.sql).

Acceptance A2, A3, A5 (the facts code adds), A8 of docs/work/m5-choose-ingredients/brief.md.
"""

import copy
import json
import re

import pytest

from loaders.db import connect
from tests.test_step4 import BRIEFS, brief_of, sql, step4

pytestmark = pytest.mark.stack

BUILT: dict = {}


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def build(conn, b):
    """Step 1's expected brief through steps 2, 4, 5 and the table; returns (table, brief)."""
    brief = brief_of(b)
    style = sql(conn, "step2_best_style", brief, b["request"], None)
    targets = step4(conn, b)
    frame = sql(conn, "step5_frame", brief, sql(conn, "step0_profile", None), targets)
    return sql(conn, "choose_table", brief, style, targets, frame), brief


def table_of(conn, bid):
    if bid not in BUILT:
        BUILT[bid] = build(conn, BRIEFS[bid])
    return BUILT[bid][0]


def rows_of(tbl):
    return [r for key in ("fermentables", "hops", "yeasts", "misc") for r in tbl[key]]


def ids_of(tbl):
    return {r["ingredient_id"] for r in rows_of(tbl)}


def ids_named(conn, kind, *names):
    return {r[0] for r in conn.execute(
        "select id from ref.ingredient where kind = %s and name = any(%s)", (kind, list(names))).fetchall()}


def ids_of_word(conn, word):
    return {r[0] for r in conn.execute("select ingredient_id from app.resolve_ingredient(%s)", (word,)).fetchall()}


def test_b16_excludes_siblings(conn):
    """A2: no Citra, Citra LUPOMAX, Mosaic or Mosaic LUPOMAX in any row; the siblings are named."""
    tbl = table_of(conn, "b16")
    hops = ids_named(conn, "hop", "Citra", "Citra LUPOMAX", "Mosaic", "Mosaic LUPOMAX")
    assert len(hops) == 4
    assert not hops & ids_of(tbl)
    why = {e["name"]: e["why"] for e in tbl["excluded"]}
    assert why["Citra"] == "excluded in the request" and why["Mosaic"] == "excluded in the request"
    assert why["Citra LUPOMAX"] == "sibling of Citra" and why["Mosaic LUPOMAX"] == "sibling of Mosaic"
    assert {e["ingredient_id"] for e in tbl["excluded"]} == hops


def test_b08_has_no_saaz(conn):
    """A2: Saaz is not a row, and it is the only exclusion."""
    tbl = table_of(conn, "b08")
    saaz = ids_named(conn, "hop", "Saaz")
    assert len(saaz) == 1 and not saaz & ids_of(tbl)
    assert [e["name"] for e in tbl["excluded"]] == ["Saaz"]
    assert len(tbl["hops"]) > 0


def test_inventory_marked_and_fitting(conn):
    """A3: the inventory products carry their word and every inventory word fits."""
    b10 = table_of(conn, "b10")
    expected = {
        "dark candi sugar": ids_named(conn, "fermentable", "Brown Candi Sugar"),
        "Munich malt": ids_of_word(conn, "Munich malt"),
        "abbey yeast": ids_of_word(conn, "abbey yeast"),
    }
    assert [w["word"] for w in b10["inventory_words"]] == BRIEFS["b10"]["inventory"]
    for w in b10["inventory_words"]:
        assert w["fits"], w
        assert set(w["ids"]) == expected[w["word"]], w
    marked = {r["ingredient_id"]: r["inventory"] for r in rows_of(b10) if r["inventory"]}
    assert marked == {i: word for word, ids in expected.items() for i in ids}
    assert b10["unused_inventory"] == [] and b10["absent"] == []

    b15 = table_of(conn, "b15")
    expected = {w: ids_of_word(conn, w) for w in BRIEFS["b15"]["inventory"]}
    assert all(expected.values())
    for w in b15["inventory_words"]:
        assert w["fits"] and set(w["ids"]) == expected[w["word"]], w
    marked = {r["ingredient_id"] for r in rows_of(b15) if r["inventory"]}
    assert marked == set().union(*expected.values())


def test_guidance_filters_rows(conn):
    """With guidance on a row has a good choice or a mark; with guidance off every product is listed."""
    good = {"required", "typical", "allowed"}
    for r in rows_of(table_of(conn, "b01")):
        marked = r["inventory"] or r["wanted"]
        assert marked or good & {c["level"] for c in r["levels"]}, r["name"]
    assert len(table_of(conn, "b01")["fermentables"]) < conn.execute(
        "select count(*) from ref.ingredient where kind = 'fermentable'").fetchone()[0]

    b18 = table_of(conn, "b18")
    assert b18["guidance"] is False
    excluded = {e["ingredient_id"] for e in b18["excluded"]}
    for key, kind in (("fermentables", "fermentable"), ("hops", "hop"), ("yeasts", "yeast")):
        total = conn.execute("select count(*) from ref.ingredient where kind = %s and id <> all(%s)",
                             (kind, list(excluded))).fetchone()[0]
        assert len(b18[key]) == total, key
    assert b18["yeast_rules"]["lager"] is False and b18["yeast_rules"]["families"] == []


def test_wanted_rows_keep_best(conn):
    """R4: a wanted row's keeps_best is rated in step 2's style (30A), not in the style used (20B)."""
    tbl = table_of(conn, "b23")
    assert tbl["style_used"] == "20B" and tbl["wanted_style"] == "30A"
    coffee = [r for r in tbl["misc"] if r["wanted"] and r["wanted"]["item"] == "coffee"]
    assert coffee and all(r["keeps_best"] for r in coffee)
    for r in coffee:
        for choice in r["levels"]:
            assert choice["level"] == "out_of_style"  # the style used has no coffee
            if choice["choice"] in r["keeps_best"]:
                level = conn.execute("select app.style_level('30A', %s, %s, '{}'::jsonb) ->> 'level'",
                                     (r["ingredient_id"], choice["usage"])).fetchone()[0]
                assert level in ("typical", "allowed"), (r["name"], choice, level)
    assert all(r["wanted"] is None and "keeps_best" not in r for r in tbl["fermentables"])

    # a product with choices that differ between the two styles: Citra reaches its best level at
    # "boil 30 min" in 30A, but not in 20B
    b = copy.deepcopy(BRIEFS["b23"])
    b["wanted"] = b["wanted"] + [{"item": "Citra", "role": "background"}]
    citra = next(r for r in rows_of(build(conn, b)[0]) if r["name"] == "Citra")
    assert citra["wanted"] == {"item": "Citra", "role": "background"}
    assert "boil 30 min" in citra["keeps_best"] and "dry hop" in citra["keeps_best"]


def test_yeast_rules(conn):
    for bid in ("b06", "b08", "b09", "b17", "b22"):
        assert table_of(conn, bid)["yeast_rules"]["lager"] is True, bid
    for bid in ("b01", "b10", "b13", "b14", "b11"):
        assert table_of(conn, bid)["yeast_rules"]["lager"] is False, bid
    assert table_of(conn, "b13")["yeast_rules"]["families"] == ["wheat"]
    b14 = table_of(conn, "b14")
    assert b14["yeast_rules"]["souring"] is True
    lacto = {r[0] for r in conn.execute("select ingredient_id from ref.yeast where type = 'lacto'").fetchall()}
    assert len(lacto) == 2 and lacto <= {r["ingredient_id"] for r in b14["yeasts"]}
    assert table_of(conn, "b11")["yeast_rules"]["souring"] is False
    wheat = [r for r in table_of(conn, "b13")["yeasts"] if "wheat" in r["family"]]
    assert wheat and all("belgian" in r["family"] and "ale" in r["family"] for r in wheat)


def test_made_up_word_is_absent(conn):
    """A8: a wanted word no product fills is one absent row, and the rest of the table is unchanged."""
    base = table_of(conn, "b01")
    b = copy.deepcopy(BRIEFS["b01"])
    b["wanted"] = b["wanted"] + [{"item": "unobtainium", "role": "background"}]
    got, _ = build(conn, b)
    assert got["absent"] == [{"word": "unobtainium", "kind": None,
                              "reason": 'no product in the catalogue matches "unobtainium"'}]
    assert got["slots"][-1] == {"item": "unobtainium", "role": "background", "kind": None, "ids": []}
    assert got["slots"][:-1] == base["slots"]
    rest = {k: v for k, v in got.items() if k not in ("slots", "absent")}
    assert rest == {k: v for k, v in base.items() if k not in ("slots", "absent")}


def numbers(text):
    return {float(n) for n in re.findall(r"\d+(?:\.\d+)?", text)}


def test_prompt_uses_table_numbers(conn):
    """Every number in the prompt text is a number of the table JSON or the brief."""
    for bid in ("b01", "b10", "b14", "b18", "b23"):
        tbl = table_of(conn, bid)
        brief = BUILT[bid][1]
        prompt = sql(conn, "choose_prompt", tbl, brief)
        assert numbers(prompt) <= numbers(json.dumps(tbl) + json.dumps(brief)), bid
        assert "{" not in prompt and '":' not in prompt, bid
        for r in rows_of(tbl):
            assert f"\n{r['ingredient_id']} | {r['name']}" in prompt, (bid, r["name"])
        for e in tbl["excluded"]:
            assert f"\n{e['ingredient_id']} | " not in prompt


def unrated_lager_table(conn):
    """b01's brief with 4A Munich Helles (a lager style with no reviewed envelope) as the style used."""
    b = BRIEFS["b01"]
    brief = brief_of(b)
    style = sql(conn, "step2_best_style", brief, b["request"], None)
    targets = copy.deepcopy(step4(conn, b))
    targets["style"]["code"] = "4A"
    frame = sql(conn, "step5_frame", brief, sql(conn, "step0_profile", None), targets)
    return sql(conn, "choose_table", brief, style, targets, frame)


def test_unrated_lager_style_keeps_the_yeast_rules(conn):
    """The lager rule reads style tags, not levels: an unrated lager style still needs a lager yeast."""
    tbl = unrated_lager_table(conn)
    assert tbl["style_rated"] is False and tbl["guidance"] is False
    assert tbl["yeast_rules"]["lager"] is True
    assert tbl["yeasts"]


def test_unrated_style_lists_every_product(conn):
    """A style with no reviewed envelope has no levels: the table is built as with guidance off."""
    b = BRIEFS["b01"]
    brief = brief_of(b)
    style = sql(conn, "step2_best_style", brief, b["request"], None)
    targets = copy.deepcopy(step4(conn, b))
    targets["style"]["code"] = "24B"  # Belgian Pale Ale: "not rated: has no reviewed envelope"
    frame = sql(conn, "step5_frame", brief, sql(conn, "step0_profile", None), targets)
    tbl = sql(conn, "choose_table", brief, style, targets, frame)
    assert tbl["style_rated"] is False and tbl["guidance"] is False
    assert all(len(tbl[k]) > 0 for k in ("fermentables", "hops", "yeasts"))
    assert "no reviewed ingredient guidance" in sql(conn, "choose_prompt", tbl, brief)
    assert table_of(conn, "b01")["style_rated"] is True


# --- Task 7 of docs/work/m6-compute-validate: a retry's table and prompt (R4) ---

def feedback_of(banned, lines=None):
    """A try 2 feedback: three failure lines, the failed picks, the banned products."""
    return {
        "try": 2,
        "lines": lines or ["Rule 3: roast malt is 20 % of the grist, the limit is 10 %.",
                           "SRM 31.2 misses the target 14 by more than 1.",
                           "Black Malt (mash) is out of style (banned for the next try)"],
        "banned": banned,
        "last": {
            "fermentables": [{"name": "Pale Ale Malt", "pct": 80.5, "usage": "mash"}],
            "hops": [{"name": "Magnum", "share_pct": 100.0, "usage": "boil", "minutes": 60}],
            "yeast": [{"name": "Safale US-05"}],
            "extras": [],
        },
    }


def test_ban_removes_and_excludes(conn):
    """R4: a banned pick leaves every list and is excluded with its why, so the check refuses it."""
    from tests.test_choose_check import good_proposal
    tbl = table_of(conn, "b01")
    banned = next(r for r in tbl["fermentables"] if r["role"] != "base")
    fb = feedback_of([{"ingredient_id": banned["ingredient_id"], "name": banned["name"], "why": "out of style"}])
    after = sql(conn, "choose_ban", tbl, fb)
    assert banned["ingredient_id"] not in ids_of(after)
    assert all(banned["ingredient_id"] not in s["ids"] for s in after["slots"] + after["inventory_words"])
    ex = next(e for e in after["excluded"] if e["ingredient_id"] == banned["ingredient_id"])
    assert ex["why"] == "failed step 11 on try 2: out of style" and ex["name"] == banned["name"]
    assert len(after["excluded"]) == len(tbl["excluded"]) + 1
    p = copy.deepcopy(good_proposal(tbl))
    p["fermentables"][-1]["ingredient_id"] = banned["ingredient_id"]
    errs = sql(conn, "choose_check", after, p)
    assert any("is excluded: failed step 11 on try 2: out of style" in e for e in errs)


def test_ban_removes_from_slots_and_inventory(conn):
    """A banned id is also taken out of the slots and inventory words that listed it."""
    tbl = copy.deepcopy(table_of(conn, "b01"))
    victim = tbl["fermentables"][0]["ingredient_id"]
    tbl["slots"] = [{"item": "x", "role": None, "kind": "fermentable", "ids": [victim]}]
    tbl["inventory_words"] = [{"word": "y", "kind": "fermentable", "ids": [victim], "fits": True}]
    after = sql(conn, "choose_ban", tbl, feedback_of([{"ingredient_id": victim, "name": "n", "why": "w"}]))
    assert after["slots"][0]["ids"] == [] and after["inventory_words"][0]["ids"] == []


def test_no_feedback_same_table(conn):
    """No feedback (try 1): the same table and the same prompt, the prompt block is empty."""
    tbl, brief = built(conn, "b01")
    assert sql(conn, "choose_ban", tbl, None) == tbl
    assert (conn.execute("select app.choose_feedback_prompt(null)").fetchone()[0] or "") == ""


def built(conn, bid):
    table_of(conn, bid)
    return BUILT[bid]


def test_feedback_prompt_lines(conn):
    """Every failure line, pick and banned name is in the block; every number in it is the feedback's."""
    fb = feedback_of([{"ingredient_id": 1, "name": "Black Malt", "why": "out of style"}])
    text = conn.execute("select app.choose_feedback_prompt(%s::jsonb)", (json.dumps(fb),)).fetchone()[0]
    assert "Try 2: the last recipe failed step 11. Fix these and change as little else as you can. Where a line says To fix, do that:" in text
    for line in fb["lines"]:
        assert line in text
    assert "Where a line says To fix, do that" in text
    for name in ("Pale Ale Malt", "Magnum", "Safale US-05", "Black Malt"):
        assert name in text
    allowed = set(re.findall(r"\d+(?:\.\d+)?", json.dumps({k: v for k, v in fb.items() if k != "banned"})))
    allowed |= {"2", "11"}
    found = set(re.findall(r"\d+(?:\.\d+)?", text))
    assert found <= allowed | {"80.5", "100", "60"} and found, found - allowed
