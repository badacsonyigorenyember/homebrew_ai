"""Step 16 gathers its facts and finds its sources (Task 4 of docs/work/m8-recipe-sheet-chat,
db/055_sheet_facts.sql).

A saved case gets the run_step rows 2 and 6-11 the pipeline would have logged (steps 12-15 are in the saved
process). Every insert is rolled back. test_htb_first embeds with Ollama's bge-m3, like the pipeline does.
"""

import json

import pytest

from loaders.books import embed
from loaders.db import connect
from tests.test_save_process import save, steps_of
from tests.test_save_recipe import new_run
from tests.test_step4 import BRIEFS, sql

pytestmark = pytest.mark.stack


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


@pytest.fixture(autouse=True)
def rolled_back(conn):
    yield
    conn.rollback()


def logged(conn, bid):
    """Save brief `bid` and log the step rows the facts read. Returns (recipe id, run id)."""
    rid, _ = save(conn, bid)
    run_id = conn.execute("select id from app.run where recipe_id = %s", [rid]).fetchone()[0]
    inp, out, _, _, _, _, v = steps_of(conn, bid)
    step2 = sql(conn, "step2_best_style", inp["brief"], BRIEFS[bid]["request"], None)
    for step, output in ((2, step2), (6, inp["step6"]), (7, inp["step7"]), (8, inp["step8"]),
                         (9, inp["step9"]), (10, out), (11, v)):
        conn.execute("insert into app.run_step (run_id, step, try, input, output, ok, ms) "
                     "values (%s, %s, 1, '{}'::jsonb, %s::jsonb, true, 0)", [run_id, step, json.dumps(output)])
    return rid, run_id


def facts_of(conn, run_id):
    return sql(conn, "sheet_facts", run_id)


def test_choices_list_every_item_once_with_inventory(conn):
    rid, run_id = logged(conn, "b10")
    facts = facts_of(conn, run_id)
    keys = [c["key"] for c in facts["choices"]]
    assert len(keys) == len(set(keys))
    ids = {r[0] for r in conn.execute("select ingredient_id from app.recipe_item where recipe_id = %s", [rid])}
    listed = {int(k.split(":")[1]) for k in keys if k.split(":")[0] in ("fermentable", "hop", "yeast", "extra")}
    assert listed == ids
    assert {"style", "water", "mash", "boil", "fermentation", "packaging"} <= set(keys)
    by_key = {c["key"]: c for c in facts["choices"]}
    flagged = [c for c in facts["choices"] if c.get("inventory")]
    # b10 states three inventory items (candi sugar, Munich malt, abbey yeast): each is flagged on a choice
    assert len(flagged) == 3
    assert any(c["key"].startswith("yeast:") for c in flagged)
    assert all(c["label"] for c in by_key.values())
    # the facts hold the saved recipe, its process and the passed try's step outputs
    assert facts["recipe"]["id"] == rid and facts["process"]["mash"] and len(facts["items"]) == len(ids)
    assert facts["style"]["code"] == "26B" and facts["style"]["ranges"]["abv"]["low"] is not None
    assert facts["step2"]["reason"] and "absent" in facts["step6"] and "values_used" in facts["step10"]
    assert facts["try"] == 1


def test_allowed_numbers_hold_saved_values(conn):
    rid, run_id = logged(conn, "b10")
    facts = facts_of(conn, run_id)
    allowed = {float(n) for n in facts["allowed_numbers"]}
    og = float(conn.execute("select og from app.recipe where id = %s", [rid]).fetchone()[0])
    assert og in allowed
    salts = facts["process"]["water"]["salts"]
    assert salts and all(float(s["total_g"]) in allowed for s in salts)
    lo, hi = conn.execute("select lower(abv), upper(abv) from ref.beer_style where code = '26B' and guide = 'BJCP'"
                          ).fetchone()
    assert float(lo) in allowed and float(hi) in allowed
    assert float(facts["recipe"]["batch_l"]) in allowed
    # the function agrees with the list in the facts, and numbers inside names count ("15B", "S-04")
    assert {float(n) for n in sql(conn, "sheet_allowed_numbers", facts)} == allowed
    assert 26.0 in allowed


def test_allowed_numbers_hold_named_style_ranges(conn):
    """b05's step 2 names 20C Imperial Stout and chooses 15B: both styles' range bounds are allowed."""
    rid, run_id = logged(conn, "b05")
    facts = facts_of(conn, run_id)
    assert facts["step2"]["mismatch"]["named"].startswith("20C")
    allowed = {float(n) for n in facts["allowed_numbers"]}
    lo, hi = conn.execute("select lower(abv), upper(abv) from ref.beer_style where code = '20C' and guide = 'BJCP'"
                          ).fetchone()
    assert float(lo) in allowed and float(hi) in allowed


def test_run_without_recipe_raises(conn):
    _, run_id = new_run(conn)
    with pytest.raises(Exception, match="no saved recipe"):
        facts_of(conn, run_id)


QUERIES = [{"topic": "mash", "text": "mash temperature saccharification rest"},
           {"topic": "boil", "text": "boil time hop additions bitterness"}]


def vec_text(vector):
    return "[" + ",".join(str(x) for x in vector) + "]"


def sources(conn, queries, per_query):
    embeddings = [embed(q["text"])[0] for q in queries]
    return sql(conn, "sheet_sources", queries, embeddings, per_query)


def test_htb_first(conn):
    """Every kept chunk of a query is How to Brew when the top 10 hold at least per_query of them."""
    kept = sources(conn, QUERIES[:1], 3)
    assert len(kept) == 3
    top = conn.execute("select source_slug from app.kb_search(%s, %s::extensions.vector, 10)",
                       [QUERIES[0]["text"], vec_text(embed(QUERIES[0]["text"])[0])]).fetchall()
    if sum(1 for (slug,) in top if slug == "palmer-how-to-brew") >= 3:
        assert {c["source_slug"] for c in kept} == {"palmer-how-to-brew"}
    # the shape: each item carries what the sheet cites
    for c in kept:
        assert set(c) >= {"chunk_id", "topic", "source_slug", "title", "url", "section_path", "page", "text"}
        assert c["topic"] == "mash"


def test_each_chunk_once_first_topic_wins(conn):
    twice = [{"topic": "mash", "text": QUERIES[0]["text"]}, {"topic": "boil", "text": QUERIES[0]["text"]}]
    kept = sources(conn, twice, 3)
    ids = [c["chunk_id"] for c in kept]
    assert len(ids) == len(set(ids)) == 6
    assert [c["topic"] for c in kept] == ["mash"] * 3 + ["boil"] * 3


def test_zero_per_query_gives_no_sources(conn):
    assert sources(conn, QUERIES, 0) == []


def test_queries_name_the_recipe(conn):
    rid, run_id = logged(conn, "b10")
    facts = facts_of(conn, run_id)
    queries = sql(conn, "sheet_queries", facts)
    assert [q["topic"] for q in queries] == ["style", "grist", "hops", "yeast", "water", "mash", "boil",
                                             "fermentation", "packaging"]
    by = {q["topic"]: q["text"] for q in queries}
    assert facts["style"]["name"] in by["style"]
    assert all(q["text"].strip() for q in queries)
