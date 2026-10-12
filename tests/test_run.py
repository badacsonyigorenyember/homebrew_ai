"""The eval runner: summary of results (no stack) and a bad request through n8n (stack)."""

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
    assert totals["step1"] == {"passed": 0, "total": 1}
    assert totals["step2"] == {"passed": 0, "total": 1, "not_run": 1}
    assert totals["step3"] == {"passed": 0, "total": 1, "not_run": 1}
    assert totals["briefs"] == {"passed": 0, "total": 1}
    row = run.table(results).splitlines()[-1]
    assert "not run" in row and "wanted" in row


def test_failed_run_is_reported_failed():
    results = [_result("b01", run_ok=False, error="contract step1.input: bad")]
    assert results[0]["passed"] is False
    assert run.totals(results)["briefs"]["passed"] == 0
    assert "failed at step" in run.table(results) or "contract step1.input" in run.table(results)


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
