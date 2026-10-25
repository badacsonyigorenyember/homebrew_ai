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


def _recipe(**numbers):
    """A saved recipe as read_recipe returns it."""
    return {"batch_l": 20.0, "og": 1.065, "fg": 1.012, "abv": 6.5, "ibu": 60.0, "srm": 6.0,
            "items": [{"ingredient_id": 1, "raw_name": "Pale"}], "deviations": [], **numbers}


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
    brief = next(b for b in BRIEFS if b["id"] == "b01")
    good = run.grade_result(brief, {"run_id": 1, "ok": True}, {}, recipe=_recipe())
    bad = run.grade_result(brief, {"run_id": 1, "ok": False, "error": "boom"}, {}, recipe=_recipe())
    assert run.grade_result(brief, {"run_id": 1, "ok": True}, {})["passed"] is False  # not validated
    assert good["passed"] is True
    assert bad["passed"] is False


def test_unfinished_run_is_not_passed(monkeypatch):
    """The HTTP answer says ok, but the stored run never finished: the runner trusts the database."""
    _all_pass(monkeypatch)
    brief = next(b for b in BRIEFS if b["id"] == "b01")
    monkeypatch.setattr(run, "send", lambda *a, **k: {"ok": True, "run_id": 7})
    monkeypatch.setattr(run, "read_facts", lambda conn, steps, inputs=None: {})
    monkeypatch.setattr(run, "read_recipe", lambda conn, run_id: _recipe())
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


# --- recipes in the harness (docs/work/m6-compute-validate, Task 9) ---------------------------
class FakeConn:
    """Answers read_run's two queries from lists: the app.run row and the app.run_step rows
    (step, try, ok, llm, input, output)."""

    def __init__(self, run_row, step_rows):
        self.run_row, self.step_rows = run_row, step_rows

    def execute(self, sql, params=None):
        rows = self.step_rows if "app.run_step" in sql else [self.run_row]
        return type("Cursor", (), {"fetchone": lambda s: rows[0], "fetchall": lambda s: rows})()

    def commit(self):
        pass


def _row(step, try_, llm_tries=None, ok=True):
    llm = None if llm_tries is None else {"tries": llm_tries}
    return (step, try_, ok, llm, {}, {"step": step})


def test_read_run_counts_calls_over_three_tries():
    """Three tries: step 1 once, steps 6-9 on each try (a failed row counts too), step 11 has no llm."""
    rows = [_row(1, 1, 1), _row(6, 1, 1), _row(10, 1), _row(11, 1, ok=False),
            _row(6, 2, 1), _row(10, 2), _row(11, 2, ok=False),
            _row(6, 3, 2, ok=False), _row(6, 3, 1), _row(10, 3), _row(11, 3)]
    stored = run.read_run(FakeConn((1, True), rows), 5)
    assert stored["calls"] == 1 + 1 + 1 + 2 + 1
    assert stored["first_try_calls"] == 2 and stored["retry_calls"] == 4
    assert stored["tries"] == 3
    assert stored["steps"][6] == {"step": 6} and stored["llms"][6] == {"tries": 1}


def test_first_try_calls_ignore_contract_retries():
    """A step 6 contract retry on try 1 raises llm.tries to 2 but is one first-try call."""
    stored = run.read_run(FakeConn((1, True), [_row(1, 1, 1), _row(6, 1, 2), _row(10, 1), _row(11, 1)]), 5)
    assert stored["calls"] == 3
    assert stored["first_try_calls"] == 2 and stored["retry_calls"] == 1 and stored["tries"] == 1


def test_read_run_without_step_11_has_zero_tries():
    stored = run.read_run(FakeConn((None, None), [_row(1, 1, 1)]), 5)
    assert stored["tries"] == 0 and stored["finished"] is False


def _graded(brief_id, recipe, stats=None):
    brief = next(b for b in BRIEFS if b["id"] == brief_id)
    return run.grade_result(brief, {"run_id": 1, "ok": True}, {}, recipe=recipe,
                            stats=stats or {"calls": 2, "first_try_calls": 2, "retry_calls": 0, "tries": 1})


def test_table_and_totals_report_recipes():
    good = _graded("b01", _recipe(abv=6.6))
    miss = _graded("b08", _recipe(batch_l=10.0, ibu=40.0), {"calls": 5, "first_try_calls": 2, "retry_calls": 3, "tries": 3})
    none = _graded("b21", None, {"calls": 6, "first_try_calls": 2, "retry_calls": 4, "tries": 3})
    for r in (good, miss, none):
        r["id"] = r["id"]
    lines = run.table([good, miss, none]).splitlines()
    assert "valid" in lines[0] and "tries" in lines[0] and "stated" in lines[0]
    assert "2+0" in lines[1] and "2+3" in lines[2] and "2+4" in lines[3]
    assert "ibu MISS" in lines[2] and "abv ok" in lines[1]
    t = run.totals([good, miss, none])
    assert t["validated"] == {"b01_b20": 2, "all": 2}
    assert t["invented"] == 0
    assert t["stated_met"] == {"met": 3, "total": 5}  # b01: batch, abv; b08: batch, ibu; b21: abv (no recipe)
    assert t["first_try_calls_max"] == 2 and t["retry_calls"] == 7
    assert t["calls"]["total"] == 13
    text = run.format_totals(t)
    assert "validated 2/3" in text and "stated 3/5" in text and "retry calls 7" in text


def test_passed_needs_a_validated_recipe(monkeypatch):
    _all_pass(monkeypatch)
    assert _graded("b01", _recipe())["passed"] is True
    assert _graded("b01", None)["passed"] is False


def test_needs_skipped_for_another_briefs_file():
    brief = {**next(b for b in BRIEFS if b["id"] == "b01"), "id": "h01"}
    graded = run.grade_result(brief, {"run_id": 1, "ok": True}, {}, recipe=_recipe(), grade_needs=False)
    assert graded["needs"] == {} and graded["needs_ok"] is True


def test_briefs_option_default_and_override(tmp_path):
    assert run.load_briefs()[0]["id"] == "b01"
    assert [b["id"] for b in run.load_briefs(run.HELDOUT_FILE)][0] == "h01"


@pytest.mark.stack
def test_harness_tolerances_match_sql():
    from evals import grade
    conn = connect()
    try:
        sql = conn.execute("select app.recipe_tolerances()").fetchone()[0]
        conn.commit()
    finally:
        conn.close()
    assert {k: float(v) for k, v in sql.items()} == {k: float(v) for k, v in grade.RECIPE_TOLERANCES.items()}


@pytest.mark.stack
def test_read_recipe_reads_the_saved_rows():
    conn = connect()
    brief = run_id = rid = None
    try:
        assert run.read_recipe(conn, -1) is None
        style = conn.execute("select id from ref.beer_style order by id limit 1").fetchone()[0]
        brief = conn.execute("insert into app.brief (request_text, brief) values ('t', '{}') returning id").fetchone()[0]
        rid = conn.execute(
            "insert into app.recipe (brief_id, style_id, batch_l, efficiency_pct, targets, og, fg, abv, ibu, srm, calc_version) "
            "values (%s, %s, 20, 72, '{}', 1.0650, 1.0120, 6.9, 40, 8, 'x') returning id", (brief, style)).fetchone()[0]
        conn.execute("insert into app.recipe_item (recipe_id, ingredient_id, raw_name, usage, amount, unit) "
                     "values (%s, null, 'mystery', 'boil', 5, 'g')", (rid,))
        conn.execute("insert into app.recipe_deviation (recipe_id, kind, subject, level, requested_by, note) "
                     "values (%s, 'ingredient', 'mystery', 'out_of_style', 'model', 'why')", (rid,))
        run_id = conn.execute("insert into app.run (brief_id, recipe_id, model) values (%s, %s, 'm') returning id",
                              (brief, rid)).fetchone()[0]
        recipe = run.read_recipe(conn, run_id)
        assert recipe["abv"] == 6.9 and recipe["batch_l"] == 20.0 and recipe["og"] == 1.065
        assert recipe["items"][0]["ingredient_id"] is None and recipe["items"][0]["amount"] == 5.0
        assert recipe["deviations"][0]["subject"] == "mystery"
        from evals import grade
        assert grade.grade_recipe({"stated": {"abv": 7}}, recipe)["invented"] == 1
    finally:
        conn.rollback()  # read_recipe commits, so the rows are removed by hand
        if run_id:
            conn.execute("delete from app.run where id = %s", (run_id,))
        if rid:
            conn.execute("delete from app.recipe where id = %s", (rid,))
        if brief:
            conn.execute("delete from app.brief where id = %s", (brief,))
        conn.commit()
        conn.close()


def test_show_recipe_prints_the_saved_recipe():
    from evals import show_recipe
    steps = {4: {"style": {"code": "21A", "name": "West Coast IPA"},
                 "targets": {"og": {"value": 1.065}, "fg": {"value": 1.012}, "abv": {"value": 6.5},
                             "ibu": {"value": 60}, "srm": {"value": 6}}},
             6: {"yeast": {"ingredient_id": 3, "because": "clean ale yeast"}},
             7: {"fermentables": [{"ingredient_id": 1, "because": "base malt"}]},
             8: {"hops": [{"ingredient_id": 2, "because": "bittering"}]}, 9: {"extras": []}}
    recipe = _recipe(items=[
        {"ingredient_id": 1, "raw_name": "Pale Ale Malt", "usage": "mash", "time_min": None, "pct": 100.0, "amount": 5.2, "unit": "kg"},
        {"ingredient_id": 2, "raw_name": "Columbus", "usage": "boil", "time_min": 60.0, "pct": 100.0, "amount": 40.0, "unit": "g"},
        {"ingredient_id": 3, "raw_name": "US-05", "usage": "ferment", "time_min": None, "pct": None, "amount": 1.0, "unit": "pack"},
        {"ingredient_id": 4, "raw_name": "Orange peel", "usage": "boil", "time_min": 5.0, "pct": None, "amount": 10.0, "unit": "g"}],
        deviations=[{"kind": "ingredient", "subject": "orange peel", "level": "out_of_style", "requested_by": "user", "note": "asked"}])
    text = show_recipe.format_recipe("a pale ale", steps, recipe)
    assert "West Coast IPA (21A)" in text and "5.2 kg  100 %  Pale Ale Malt" in text
    assert "40 g  Columbus  boil 60 min" in text and "because: bittering" in text
    assert "1 pack  US-05" in text and "10 g  Orange peel  boil 5 min" in text
    assert "ABV  6.5 %   (target 6.5)" in text and "orange peel: out_of_style (asked by user) asked" in text
