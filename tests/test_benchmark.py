"""The benchmark's summary, bar and best pick (no stack, no model)."""

from evals import benchmark, grade

PS = """NAME                  ID              SIZE     PROCESSOR          CONTEXT    UNTIL
gemma4:31b-it-qat     aaa111          22 GB    15%/85% CPU/GPU    8192       Forever
gemma4:12b            bbb222          9.0 GB   100% GPU           8192       Forever
"""


def _result(right=True, run_ok=True, ms=2000, tries=1):
    step1 = {"ok": right, **{f: right for f in grade.STEP1_FIELDS}}
    return {"run_ok": run_ok, "ran": {1: run_ok}, "step1": step1,
            "llm": {"llm_ms": ms, "tries": tries}}


def _runs(*right_counts, ms=2000):
    return [[_result(i < n, ms=ms) for i in range(20)] for n in right_counts]


def _config(*right_counts, ms=2000):
    return {"summary": benchmark.summarise(_runs(*right_counts, ms=ms))}


def test_bar_needs_every_run():
    assert not benchmark.meets_bar(_config(19, 19, 18)["summary"])
    assert benchmark.meets_bar(_config(20, 19, 19)["summary"])


def test_failed_run_counts_every_field_wrong():
    failed = {"run_ok": False, "ran": {1: False}, "step1": {"ok": False}, "llm": None}
    summary = benchmark.summarise([[failed, _result()]])
    assert summary["all_right"] == [1]
    assert all(v == 0.5 for v in summary["fields"].values())
    assert summary["failed_runs"] == 1


def test_best_is_quality_before_speed():
    configs = {"fast": _config(19, 19, 19, ms=1000), "slow": _config(20, 19, 19, ms=9000)}
    assert benchmark.pick_best(configs) == "slow"


def test_tie_broken_by_worst_run_then_speed():
    configs = {"uneven": _config(20, 20, 17), "even": _config(19, 19, 19, ms=9000),
               "even_fast": _config(19, 19, 19, ms=1000)}
    assert benchmark.pick_best(configs) == "even_fast"
    del configs["even_fast"]
    assert benchmark.pick_best(configs) == "even"


def test_processor_split_parses_ollama_ps():
    assert benchmark.processor_split(PS, "gemma4:31b-it-qat") == "15%/85% CPU/GPU"
    assert benchmark.processor_split(PS, "gemma4:12b") == "100% GPU"
    assert benchmark.processor_split(PS, "other") == "not loaded"


def test_percentile_nearest_rank():
    values = list(range(1, 11))
    assert benchmark.percentile(values, 90) == 9
    assert benchmark.percentile(values, 50) == 5
    assert benchmark.percentile([4], 90) == 4


def test_each_saved_config_keeps_its_own_hashes(tmp_path, monkeypatch):
    prompt, contract = tmp_path / "p.md", tmp_path / "c.json"
    monkeypatch.setattr(benchmark, "PROMPT_FILE", prompt)
    monkeypatch.setattr(benchmark, "CONTRACT_FILE", contract)
    doc = {"configs": {}}
    prompt.write_text("one"), contract.write_text("a")
    benchmark.add_config(doc, "m|no-think", {})
    prompt.write_text("two")
    benchmark.add_config(doc, "m|think", {})
    first, second = doc["configs"]["m|no-think"], doc["configs"]["m|think"]
    assert first["prompt_sha256"] != second["prompt_sha256"]
    assert first["contract_sha256"] == second["contract_sha256"] == benchmark.sha256(contract)
