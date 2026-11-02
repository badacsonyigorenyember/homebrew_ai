"""Step 16 checks the model's prose (Task 5 of docs/work/m8-recipe-sheet-chat, db/056_sheet_check.sql).

The facts are those of a saved b10 case (tests.test_sheet_facts.logged), rolled back. The sources are made up:
the check only reads their chunk ids.
"""

import json

import pytest

from loaders.db import connect
from tests.test_contracts import CONTRACTS
from tests.test_sheet_facts import facts_of, logged

pytestmark = pytest.mark.stack

CONTRACT = (CONTRACTS / "sheet.answer.schema.json").read_text()
SOURCES = [{"chunk_id": 11, "topic": "mash"}, {"chunk_id": 12, "topic": "boil"}]


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


@pytest.fixture(autouse=True)
def rolled_back(conn):
    yield
    conn.rollback()


@pytest.fixture
def facts(conn):
    _, run_id = logged(conn, "b10")
    return facts_of(conn, run_id)


def good(facts):
    return {"style_description": "A strong dark abbey ale.",
            "why": [{"key": c["key"], "text": f"It suits the beer ({c['label']}).", "cite": [11]}
                    for c in facts["choices"]],
            "notes": [{"text": "Keep the yeast warm enough.", "cite": [12]}]}


def check(conn, facts, answer, sources=SOURCES):
    content = answer if isinstance(answer, str) else json.dumps(answer)
    return conn.execute("select errors from app.sheet_read_answer(%s, %s::jsonb, %s::jsonb, %s::json)",
                        [content, json.dumps(facts), json.dumps(sources), CONTRACT]).fetchone()[0]


def test_prose_numbers(conn):
    def tokens(t):
        return conn.execute("select app.prose_numbers(%s)", [t]).fetchone()[0]
    assert tokens("Style 15B with US-05 and S-04 at 66.5 C for 60 min.") == ["66.5", "60"]
    assert tokens("1st of 2nd; 3.") == ["3"]
    assert tokens("no numbers") == []


def test_good_answer_passes(conn, facts):
    assert check(conn, facts, good(facts)) == []


def test_wrong_number_fails(conn, facts):
    mash_c = facts["process"]["mash"]["mash_c"]
    wrong = int(float(mash_c))  # 66 for a 66.5 mash, or the integer part of whatever the mash is
    if float(mash_c) == wrong:
        wrong += 1
    answer = good(facts)
    answer["why"][[c["key"] for c in facts["choices"]].index("mash")]["text"] = f"Mash at {wrong} C."
    assert check(conn, facts, answer) == [
        f"number {wrong} in why[mash] is not a saved value or a style range value"]


def test_number_in_style_description_fails(conn, facts):
    answer = good(facts)
    answer["style_description"] = "Brewed since 1856."
    assert check(conn, facts, answer) == [
        "number 1856 in style_description is not a saved value or a style range value"]


def test_rounded_saved_number_and_names_pass(conn, facts):
    og = float(facts["recipe"]["og"])
    answer = good(facts)
    answer["style_description"] = f"Style 26B, yeast US-05, OG {og:.3f}."
    answer["notes"][0]["text"] = "Aim at S-04 or similar."
    assert check(conn, facts, answer) == []


def test_unknown_chunk_fails(conn, facts):
    answer = good(facts)
    answer["notes"][0]["cite"] = [9999]
    assert check(conn, facts, answer) == ["chunk 9999 in notes[0] was not retrieved"]


def test_no_citation_at_all_fails(conn, facts):
    answer = good(facts)
    for line in answer["why"] + answer["notes"]:
        line["cite"] = []
    assert check(conn, facts, answer) == ["the sheet cites no source"]


def test_empty_cite_on_one_line_passes(conn, facts):
    answer = good(facts)
    answer["why"][0]["cite"] = []
    assert check(conn, facts, answer) == []


def test_missing_and_unknown_keys_fail(conn, facts):
    answer = good(facts)
    dropped = answer["why"].pop()["key"]
    answer["why"].append({"key": "colour", "text": "Dark.", "cite": []})
    assert check(conn, facts, answer) == [
        "why has key colour, which is not in the list of keys to write", f"why is missing key {dropped}"]


def test_repeated_key_fails(conn, facts):
    answer = good(facts)
    answer["why"].append(dict(answer["why"][0]))
    assert check(conn, facts, answer) == [f"why has key {answer['why'][0]['key']} more than once"]


def test_contract_and_json_errors(conn, facts):
    assert check(conn, facts, "not json")[0].startswith("answer is not JSON")
    answer = good(facts)
    del answer["notes"]
    assert check(conn, facts, answer)


def test_retry_text_lists_failures(conn):
    text = conn.execute("select app.sheet_retry_text(%s)", [["one problem", "another"]]).fetchone()[0]
    assert "- one problem" in text and "- another" in text


def test_prompt_lists_keys_and_sources(conn, facts):
    sources = [{"chunk_id": 11, "title": "How to Brew", "section_path": "Mash", "text": "Mash at 66 C."}]
    prompt = conn.execute("select app.sheet_prompt(%s::jsonb, %s::jsonb)",
                          [json.dumps(facts), json.dumps(sources)]).fetchone()[0]
    for choice in facts["choices"]:
        assert f"- {choice['key']} |" in prompt
    assert "[11] How to Brew - Mash: Mash at 66 C." in prompt
    assert str(facts["recipe"]["og"]) in prompt
