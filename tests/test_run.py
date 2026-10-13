"""The eval runner: summary of results (no stack) and a bad request through n8n (stack)."""

import json
import tomllib
from pathlib import Path

import pytest

from evals import run
from loaders.db import connect

BRIEFS = tomllib.loads(
    (Path(__file__).resolve().parent.parent / "evals" / "recipe_briefs.toml").read_text("utf-8")
)["brief"]


def _result(brief_id, run_ok=True, error=None, steps=None):
    """A made-up run: only the pieces table() and totals() read."""
    brief = next(b for b in BRIEFS if b["id"] == brief_id)
    return run.grade_result(brief, {"run_id": 1, "ok": run_ok, "error": error}, steps or {})


def test_not_run_steps_count_as_failed():
    results = [_result("b01", steps={1: {"stated": {}, "hints": [], "wanted": ["x"],
                                         "excluded": [], "inventory": [], "guidance": True}})]
    totals = run.totals(results)
    assert totals["step1"] == {"passed": 0, "total": 1, "not_run": 0}
    assert totals["step2"] == {"passed": 0, "total": 1, "not_run": 1}
    assert totals["step3"] == {"passed": 0, "total": 1, "not_run": 1}
    assert totals["briefs"] == {"passed": 0, "total": 1}
    row = run.table(results).splitlines()[-1]
    assert "not run" in row and "wanted" in row


def test_failed_run_is_reported_failed():
    results = [_result("b01", run_ok=False, error="contract step1.input: bad")]
    assert results[0]["passed"] is False
    assert run.totals(results)["briefs"]["passed"] == 0
    row = run.table(results).splitlines()[-1]
    assert "failed at step" in row and "contract step1.input" in row


def _all_pass(monkeypatch):
    """Make grading give a pass, so only the run's own state decides `passed`."""
    ok = {"ok": True}
    monkeypatch.setattr(
        run.grade, "grade_run",
        lambda brief, steps: {"step1": ok, "step2": True, "step3": True, "passed": True},
    )


def test_failed_run_with_good_steps_is_not_passed(monkeypatch):
    _all_pass(monkeypatch)
    good = _result("b01", run_ok=True)
    bad = _result("b01", run_ok=False, error="boom")
    assert good["passed"] is True
    assert bad["passed"] is False


def test_unfinished_run_is_not_passed(monkeypatch):
    """The HTTP answer says ok, but the stored run never finished: the runner trusts the database."""
    _all_pass(monkeypatch)
    brief = next(b for b in BRIEFS if b["id"] == "b01")
    monkeypatch.setattr(run, "send", lambda *a, **k: {"ok": True, "run_id": 7})
    monkeypatch.setattr(
        run, "read_run", lambda conn, run_id: {"finished": False, "ok": False, "steps": {1: {}}}
    )
    result = run.run_brief(None, brief)
    assert result["run_ok"] is False
    assert result["passed"] is False
    assert result["error"] == "run not finished ok"


def test_send_puts_think_in_body(monkeypatch):
    seen = {}

    class Reply:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"ok": true}'

    def fake_urlopen(req, timeout):
        seen["body"] = json.loads(req.data)
        return Reply()

    monkeypatch.setattr(run.urllib.request, "urlopen", fake_urlopen)
    run.send("a pale ale", "b01", "m", think=True)
    assert seen["body"]["think"] is True and seen["body"]["model"] == "m"

    run.send("a pale ale", "b01")
    assert "temperature" not in seen["body"] and "seed" not in seen["body"]
    run.send("a pale ale", "b01", temperature=0.8, seed=1)
    assert (seen["body"]["temperature"], seen["body"]["seed"]) == (0.8, 1)


@pytest.mark.stack
def test_runner_reports_bad_request_as_failed():
    brief = {**next(b for b in BRIEFS if b["id"] == "b01"), "request": ""}
    conn = connect()
    try:
        result = run.run_brief(conn, brief)
        conn.execute("delete from app.run where id = %s", (result["run_id"],))
        conn.commit()
    finally:
        conn.close()
    assert result["passed"] is False
    assert "step1.input" in result["error"]
