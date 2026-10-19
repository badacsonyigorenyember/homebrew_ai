"""A request goes through n8n and leaves its run log in app.run and app.run_step."""

import json
import urllib.request
from pathlib import Path

import pytest

from evals import benchmark
from loaders.db import connect

pytestmark = pytest.mark.stack

URL = "http://localhost:5678/webhook/recipe-pipeline"
CONTRACTS = Path(__file__).resolve().parent.parent / "shared" / "contracts"


@pytest.fixture(scope="module", autouse=True)
def unload_model():
    """These are the only tests that call the model; unload it from Ollama once they are done."""
    yield
    benchmark.unload_all()


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
        with urllib.request.urlopen(req, timeout=600) as response:
            answer = json.load(response)
        run_ids.append(answer["run_id"])
        return answer

    yield send
    brief_ids = [r[0] for r in conn.execute(
        "select brief_id from app.run where id = any(%s) and brief_id is not null", (run_ids,)
    ).fetchall()]
    conn.execute("delete from app.run where id = any(%s)", (run_ids,))  # steps cascade
    conn.execute("delete from app.brief where id = any(%s)", (brief_ids,))
    conn.commit()


def _step_rows(conn, run_id):
    return conn.execute(
        "select step, try, ok, error, ms, input, output, tokens, llm from app.run_step "
        "where run_id = %s order by step",
        (run_id,),
    ).fetchall()


def test_b01_logs_step_1(conn, post):
    answer = post({"request": "a pale ale", "brief_id": "b01"})
    assert answer["ok"] is True
    run_id = answer["run_id"]

    run = conn.execute(
        "select eval_id, model, finished_at, ok, brief_id from app.run where id = %s", (run_id,)
    ).fetchall()
    assert len(run) == 1
    eval_id, model, finished_at, ok, brief_id = run[0]
    assert (eval_id, ok) == ("b01", True)
    assert model and finished_at is not None

    steps = _step_rows(conn, run_id)
    assert [s[0] for s in steps] == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    step, attempt, step_ok, error, ms, step_input, output, tokens, llm = steps[1]
    assert (step, attempt, step_ok, error) == (1, 1, True, None)
    assert ms >= 0
    assert step_input == {
        "run_id": run_id, "request": "a pale ale", "model": model, "think": False,
        "temperature": 0, "seed": 42,
    }
    assert tokens > 0
    assert llm["model"] == model and llm["tries"] in (1, 2)

    assert brief_id is not None
    saved = conn.execute(
        "select request_text, brief, guidance_on, profile_id from app.brief where id = %s",
        (brief_id,),
    ).fetchall()
    assert saved == [("a pale ale", output, output["guidance"], None)]

    schema = (CONTRACTS / "step1.output.schema.json").read_text(encoding="utf-8")
    errors = conn.execute(
        "select extensions.jsonschema_validation_errors(%s::json, %s::json)",
        (schema, json.dumps(output)),
    ).fetchone()[0]
    assert errors == []


def test_default_temperature_and_seed(conn, post):
    """With no fields sent, step 1 runs at temperature 0, seed 42."""
    answer = post({"request": "a pale ale"})
    assert answer["ok"] is True
    llm = _step_rows(conn, answer["run_id"])[1][8]
    assert (llm["temperature"], llm["seed"]) == (0, 42)


def test_temperature_and_seed_reach_step_1(conn, post):
    """The webhook's `temperature` and `seed` reach step 1's input and its Ollama call."""
    answer = post({"request": "a pale ale", "temperature": 0.8, "seed": 1})
    assert answer["ok"] is True
    step_1 = _step_rows(conn, answer["run_id"])[1]
    assert (step_1[5]["temperature"], step_1[5]["seed"]) == (0.8, 1)
    assert (step_1[8]["temperature"], step_1[8]["seed"]) == (0.8, 1)


def _valid(conn, contract, value):
    schema = (CONTRACTS / f"{contract}.schema.json").read_text(encoding="utf-8")
    return conn.execute(
        "select extensions.jsonschema_validation_errors(%s::json, %s::json)",
        (schema, json.dumps(value)),
    ).fetchone()[0]


def _by_step(conn, run_id):
    return {s[0]: s for s in _step_rows(conn, run_id)}


IPA = "I want a classic West Coast IPA that is properly bitter."


def test_step_0_logged(conn, post):
    """Step 0 is logged with its input, output and time (R13)."""
    answer = post({"request": "a pale ale"})
    assert answer["ok"] is True
    step, attempt, step_ok, error, ms, step_input, output, _, _ = _by_step(conn, answer["run_id"])[0]
    assert (step, attempt, step_ok, error) == (0, 1, True, None)
    assert ms >= 0
    assert step_input == {"run_id": answer["run_id"], "profile_id": None}
    assert output["batch_l"] == 20
    assert _valid(conn, "step0.output", output) == []


def test_profile_id_reaches_step_0(conn, post):
    """An unknown profile_id fails at step 0, before step 1 runs."""
    answer = post({"request": "a pale ale", "profile_id": 999999})
    assert answer["ok"] is False
    assert answer["failed_step"] == 0
    steps = _step_rows(conn, answer["run_id"])
    assert [s[0] for s in steps] == [0]
    _, _, step_ok, error, _, step_input, output, _, _ = steps[0]
    assert step_ok is False and "no brewer profile" in error
    assert step_input == {"run_id": answer["run_id"], "profile_id": 999999}
    assert output is None


def test_step_2_logged(conn, post):
    """Step 2 is logged with its input, output and time (R9)."""
    answer = post({"request": IPA})
    assert answer["ok"] is True
    steps = _by_step(conn, answer["run_id"])
    step, attempt, step_ok, error, ms, step_input, output, _, _ = steps[2]
    assert (step, attempt, step_ok, error) == (2, 1, True, None)
    assert ms >= 0
    assert step_input == {
        "run_id": answer["run_id"], "brief": steps[1][6], "request": IPA, "guide_preference": None,
    }
    assert output["style"]["code"]


def test_step_3_logged(conn, post):
    """Step 3 is logged with its input, output and time (R7)."""
    answer = post({"request": IPA})
    assert answer["ok"] is True
    steps = _by_step(conn, answer["run_id"])
    step, attempt, step_ok, error, ms, step_input, output, _, _ = steps[3]
    assert (step, attempt, step_ok, error) == (3, 1, True, None)
    assert ms >= 0
    assert step_input == {"run_id": answer["run_id"], "brief": steps[1][6], "style": steps[2][6]}
    assert _valid(conn, "step3.output", output) == []


def test_step_4_logged(conn, post):
    """Step 4 is logged with the input the block sends and an output that meets its contract."""
    answer = post({"request": IPA})
    assert answer["ok"] is True
    steps = _by_step(conn, answer["run_id"])
    step, attempt, step_ok, error, ms, step_input, output, _, _ = steps[4]
    assert (step, attempt, step_ok, error) == (4, 1, True, None)
    assert ms >= 0
    assert step_input == {
        "run_id": answer["run_id"], "brief": steps[1][6], "style": steps[2][6],
        "profile": steps[0][6], "deviations": steps[3][6],
    }
    assert _valid(conn, "step4.output", output) == []


def test_step_5_logged(conn, post):
    """Step 5 is logged with the input the block sends and an output that meets its contract."""
    answer = post({"request": IPA})
    assert answer["ok"] is True
    steps = _by_step(conn, answer["run_id"])
    step, attempt, step_ok, error, ms, step_input, output, _, _ = steps[5]
    assert (step, attempt, step_ok, error) == (5, 1, True, None)
    assert ms >= 0
    assert step_input == {
        "run_id": answer["run_id"], "brief": steps[1][6], "profile": steps[0][6], "targets": steps[4][6],
    }
    assert _valid(conn, "step5.output", output) == []


def test_steps_6_to_9_logged(conn, post):
    """Steps 6-9 run as one model call and log four ok rows that meet their contracts."""
    answer = post({"request": IPA, "brief_id": "b01"})
    assert answer["ok"] is True
    steps = _by_step(conn, answer["run_id"])
    for n in (6, 7, 8, 9):
        step, attempt, step_ok, error, ms, step_input, output, tokens, llm = steps[n]
        assert (step, attempt, step_ok, error) == (n, 1, True, None)
        assert step_input["run_id"] == answer["run_id"]
        assert _valid(conn, f"step{n}.input", step_input) == []
        assert _valid(conn, f"step{n}.output", output) == []
    assert steps[6][8]["tries"] in (1, 2) and steps[6][8]["steps"] == [6, 7, 8, 9]
    assert steps[6][7] > 0
    assert steps[7][8] is None and steps[8][8] is None and steps[9][8] is None


def test_guide_setting_reaches_step_2(conn, post):
    """The webhook's `guide` field restricts step 2 to that guide (A4)."""
    answer = post({"request": "I want a classic West Coast IPA that is properly bitter.", "guide": "ba"})
    assert answer["ok"] is True
    step_2 = _by_step(conn, answer["run_id"])[2]
    assert step_2[5]["guide_preference"] == "ba"
    assert step_2[6]["style"]["guide"] == "BA"


def test_bad_guide_fails_at_step_2(conn, post):
    answer = post({"request": "A pale ale.", "guide": "both"})
    assert answer["ok"] is False
    assert answer["failed_step"] == 2
    run_id = answer["run_id"]
    assert conn.execute("select ok from app.run where id = %s", (run_id,)).fetchone() == (False,)
    steps = _step_rows(conn, run_id)
    assert [s[0] for s in steps] == [0, 1, 2]
    _, _, step_ok, error, _, _, output, _, _ = steps[2]
    assert step_ok is False and error and "step2.input" in error
    assert output is None


def test_bad_input_logs_failure(conn, post):
    answer = post({"request": ""})
    assert answer["ok"] is False
    assert answer["failed_step"] == 1
    run_id = answer["run_id"]

    assert conn.execute("select ok from app.run where id = %s", (run_id,)).fetchone() == (False,)
    steps = _step_rows(conn, run_id)
    assert [s[0] for s in steps] == [0, 1]
    _, _, step_ok, error, _, _, output, _, _ = steps[1]
    assert step_ok is False
    assert "step1.input" in error
    assert output is None


def test_request_kept_verbatim(conn, post):
    request = 'a "pale", ale; some % off $one\nsecond line'
    answer = post({"request": request})
    assert answer["ok"] is True
    steps = _step_rows(conn, answer["run_id"])
    assert steps[1][5]["request"] == request
    saved = conn.execute(
        "select b.request_text from app.brief b join app.run r on r.brief_id = b.id where r.id = %s",
        (answer["run_id"],),
    ).fetchone()
    assert saved == (request,)


def test_webhook_ignores_pin(conn, post):
    """A webhook call uses its own body, not data pinned in the editor.

    Proves something only while the user's pin is on `Recipe pipeline`'s webhook node.
    """
    answer = post({"request": "a dry stout", "brief_id": "b02"})
    assert answer["ok"] is True
    run_id = answer["run_id"]
    assert conn.execute("select eval_id from app.run where id = %s", (run_id,)).fetchone() == ("b02",)
    assert _by_step(conn, run_id)[1][5]["request"] == "a dry stout"


def test_unknown_word_goes_to_unknown(conn, post):
    """A wish that fits no field is kept in `unknown`, never forced into `hints` (A3)."""
    answer = post({"request": "A pale ale, and make it funky."})
    assert answer["ok"] is True
    output = _step_rows(conn, answer["run_id"])[1][6]
    assert "funky" not in output["hints"]
    assert any("funky" in item.lower() for item in output["unknown"])
