"""app.step1_read_answer: the SQL check of a model's step 1 answer (R2, R3)."""

import json
import tomllib
from pathlib import Path

import pytest

from loaders.db import connect

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = (ROOT / "shared" / "contracts" / "step1.output.schema.json").read_text()
B01 = tomllib.loads((ROOT / "evals" / "recipe_briefs.toml").read_text())["brief"][0]
REQUEST = B01["request"]
GOOD = {
    "named": B01["named"], "stated": B01["stated"], "hints": B01["hints"],
    "wanted": B01["wanted"], "excluded": B01["excluded"], "inventory": B01["inventory"],
    "unknown": [], "guidance": B01["guidance"],
}


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def check(conn, content, request=REQUEST):
    text = content if isinstance(content, str) else json.dumps(content)
    brief, errors = conn.execute(
        "select brief, errors from app.step1_read_answer(%s, %s, %s::json)",
        (request, text, CONTRACT),
    ).fetchone()
    return brief, errors


@pytest.mark.stack
def test_good_answer_passes(conn):
    brief, errors = check(conn, GOOD)
    assert errors == []
    assert brief == GOOD


@pytest.mark.stack
def test_made_up_number_fails(conn):
    _, errors = check(conn, {**GOOD, "stated": {"abv": 7}})
    assert len(errors) == 1
    assert "stated.abv" in errors[0]


@pytest.mark.stack
def test_written_forms_of_a_number_match(conn):
    _, errors = check(
        conn, {**GOOD, "stated": {"og": 1.06, "abv": 6.5}}, "OG 1.060 and 6,5 % please"
    )
    assert errors == []


@pytest.mark.stack
def test_not_json_fails(conn):
    brief, errors = check(conn, '{"named": ')
    assert brief is None
    assert "answer is not JSON" in errors[0]


@pytest.mark.stack
def test_repeated_words_dropped(conn):
    brief, errors = check(conn, {**GOOD, "hints": ["bitter", "bitter"]})
    assert brief["hints"] == ["bitter"]
    assert errors == []


@pytest.mark.stack
def test_contract_errors_reported(conn):
    _, errors = check(conn, {**GOOD, "hints": ["funky"]})
    assert len(errors) >= 1
