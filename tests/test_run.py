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
    results = [_result("b01", steps={1: {"stated": {}, "hints": [], "wanted": [{"item": "x", "role": "background"}],
                                         "excluded": [], "inventory": [], "guidance": True}})]
    totals = run.totals(results)
    assert totals["step1"] == {"passed": 0, "total": 1, "not_run": 0}
    assert totals["step2"] == {"passed": 0, "total": 1, "not_run": 1}
    assert totals["step3"] == {"passed": 0, "total": 1, "not_run": 1}
    assert totals["step4"] == {"passed": 0, "total": 1, "not_run": 1}
    assert totals["step5"] == {"passed": 0, "total": 1, "not_run": 1}
    assert totals["briefs"] == {"passed": 0, "total": 1}
    row = run.table(results).splitlines()[-1]
    assert "not run" in row and "wanted" in row
    assert "step 4" in run.table(results).splitlines()[0] and "step 5" in run.table(results).splitlines()[0]
    assert "step 4 0/1 (1 not run)" in run.format_totals(totals)
    for n in (6, 7, 8, 9):
        assert totals[f"step{n}"] == {"passed": 0, "total": 1, "not_run": 1}
        assert f"step {n}" in run.table(results).splitlines()[0]
    assert "step 9 0/1 (1 not run)" in run.format_totals(totals)
    assert totals["needs"] == {"passed": 0, "total": 1, "gaps": 6}  # b01: 6 non-water needs words, step 6-9 not run
    assert "needs 0/1 (6 gaps)" in run.format_totals(totals)


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
        lambda brief, steps, facts=None, classes=None: {
            "step1": ok, **{f"step{n}": True for n in range(2, 10)},
            "needs": {}, "needs_ok": True, "problems": {}, "passed": True},
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
    monkeypatch.setattr(run, "read_facts", lambda conn, steps, inputs=None: {})
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


def test_calls_adds_up_tries_of_every_step():
    brief = next(b for b in BRIEFS if b["id"] == "b01")
    llms = {1: {"tries": 1}, 6: {"tries": 2}}
    result = run.grade_result(brief, {"run_id": 1, "ok": True}, {}, llms[1], None, llms)
    assert result["calls"] == 3
    assert run.totals([result])["calls"] == {"total": 3, "runs": 1}
    assert "LLM calls 3 in 1 runs" in run.format_totals(run.totals([result]))
    assert run.grade_result(brief, {"run_id": 1, "ok": True}, {}, {"tries": 1})["calls"] == 1
    assert run.grade_result(brief, {"run_id": 1, "ok": True}, {})["calls"] == 0


def test_table_prints_needs_coverage():
    result = _result("b10")
    result["needs"] = {"fermentables": {"Special B": "gap", "candi sugar": "covered"},
                       "yeast": {"Lactobacillus": "absent: no product of the class is in the candidate table"}}
    row = run.table([result]).splitlines()[-1]
    assert "1/3" in row and "absent: Lactobacillus" in row and "GAP: Special B" in row


@pytest.mark.stack
def test_class_names_are_catalogue_products():
    """Every product name in the class map is a ref product of the right kind."""
    conn = connect()
    try:
        have = {(kind, name) for kind, name in conn.execute("select kind, name from ref.ingredient").fetchall()}
        kinds = {"fermentables": "fermentable", "hops": "hop", "yeast": "yeast", "misc": "misc"}
        for c in run.load_classes():
            for name in c.get("names", []):
                assert (kinds[c["kind"]], name) in have, (c["word"], name)
    finally:
        conn.close()


@pytest.mark.stack
def test_choose_facts_from_ref():
    """read_choose_facts: b16's excluded ids include the LUPOMAX siblings; b08 is a lager style."""
    from tests.test_choose_check import good
    from tests.test_choose_outputs import outputs, step_inputs
    from tests.test_choose_table import BRIEFS as TBRIEFS, brief_of, table_of
    from tests.test_step4 import sql, step4
    conn = connect()
    try:
        facts = {}
        for bid in ("b16", "b08"):
            b = TBRIEFS[bid]
            tbl, targets = table_of(conn, bid), step4(conn, b)
            frame = sql(conn, "step5_frame", brief_of(b), sql(conn, "step0_profile", None), targets)
            out = outputs(conn, tbl, good(conn, bid))
            steps = {4: targets, 5: frame, 6: out["step6"], 7: out["step7"], 8: out["step8"], 9: out["step9"]}
            facts[bid] = run.read_choose_facts(conn, steps, step_inputs(tbl))
        names = {r[0] for r in conn.execute("select name from ref.ingredient where id = any(%s)",
                                            (sorted(facts["b16"]["excluded_ids"]),)).fetchall()}
        assert {"Citra", "Citra LUPOMAX", "Mosaic", "Mosaic LUPOMAX"} <= names
        assert facts["b08"]["style"] == {"lager": True, "families": ["lager"], "souring": False}
        assert facts["b08"]["excluded_ids"] and all(r["kind"] for r in facts["b08"]["refs"].values())
    finally:
        conn.close()


@pytest.mark.stack
def test_choose_facts_keep_lager_rule_for_an_unrated_style():
    """4A has no reviewed envelope (the table's guidance is off) but the brief's guidance is on: it is a lager style."""
    import copy
    from tests.test_choose_check import good
    from tests.test_choose_outputs import outputs, step_inputs
    from tests.test_choose_table import BRIEFS as TBRIEFS, table_of
    from tests.test_choose_table import brief_of
    from tests.test_step4 import sql, step4
    conn = connect()
    try:
        tbl, targets = table_of(conn, "b01"), copy.deepcopy(step4(conn, TBRIEFS["b01"]))
        frame = sql(conn, "step5_frame", brief_of(TBRIEFS["b01"]), sql(conn, "step0_profile", None), targets)
        targets["style"]["code"] = "4A"
        out = outputs(conn, tbl, good(conn, "b01"))
        inputs = step_inputs(tbl)
        inputs[6] = {**inputs[6], "guidance": False}  # what an unrated style logs
        steps = {1: {"guidance": True}, 4: targets, 5: frame, 6: out["step6"], 7: out["step7"], 8: out["step8"], 9: out["step9"]}
        assert run.read_choose_facts(conn, steps, inputs)["style"]["lager"] is True
        steps[1] = {"guidance": False}
        assert run.read_choose_facts(conn, steps, inputs)["style"]["lager"] is False
    finally:
        conn.close()
