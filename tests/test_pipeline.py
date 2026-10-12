"""A request goes through n8n and leaves its run log in app.run and app.run_step."""

import json
import urllib.request
from pathlib import Path

import pytest

from loaders.db import connect

pytestmark = pytest.mark.stack

URL = "http://localhost:5678/webhook/recipe-pipeline"
CONTRACTS = Path(__file__).resolve().parent.parent / "shared" / "contracts"


@pytest.fixture
def conn():
    connection = connect()
    yield connection
    connection.close()


@pytest.fixture
def post(conn):
    """POST a body to the pipeline; the runs it creates are deleted afterwards."""
    run_ids = []

    def send(body: dict) -> dict:
        req = urllib.request.Request(
            URL,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            answer = json.load(response)
        run_ids.append(answer["run_id"])
        return answer

    yield send
    conn.execute("delete from app.run where id = any(%s)", (run_ids,))  # steps cascade
    conn.commit()


def _step_rows(conn, run_id):
    return conn.execute(
        "select step, try, ok, error, ms, input, output from app.run_step where run_id = %s",
        (run_id,),
    ).fetchall()


def test_b01_logs_step_1(conn, post):
    answer = post({"request": "a pale ale", "brief_id": "b01"})
    assert answer["ok"] is True
    run_id = answer["run_id"]

    run = conn.execute(
        "select eval_id, model, finished_at, ok from app.run where id = %s", (run_id,)
    ).fetchall()
    assert len(run) == 1
    eval_id, model, finished_at, ok = run[0]
    assert (eval_id, ok) == ("b01", True)
    assert model and finished_at is not None

    steps = _step_rows(conn, run_id)
    assert len(steps) == 1
    step, attempt, step_ok, error, ms, step_input, output = steps[0]
    assert (step, attempt, step_ok, error) == (1, 1, True, None)
    assert ms >= 0
    assert step_input == {"run_id": run_id, "request": "a pale ale"}

    schema = (CONTRACTS / "step1.output.schema.json").read_text(encoding="utf-8")
    errors = conn.execute(
        "select extensions.jsonschema_validation_errors(%s::json, %s::json)",
        (schema, json.dumps(output)),
    ).fetchone()[0]
    assert errors == []


def test_bad_input_logs_failure(conn, post):
    answer = post({"request": ""})
    assert answer["ok"] is False
    assert answer["failed_step"] == 1
    run_id = answer["run_id"]

    assert conn.execute("select ok from app.run where id = %s", (run_id,)).fetchone() == (False,)
    steps = _step_rows(conn, run_id)
    assert len(steps) == 1
    _, _, step_ok, error, _, _, output = steps[0]
    assert step_ok is False
    assert "step1.input" in error
    assert output is None


def test_request_kept_verbatim(conn, post):
    request = 'a "pale", ale; 50% off $1\nsecond line'
    answer = post({"request": request})
    assert answer["ok"] is True
    steps = _step_rows(conn, answer["run_id"])
    assert steps[0][5]["request"] == request
    assert steps[0][6]["wanted"][0] == request
