"""The fit rule and the pass rule of the R13 fit test (evals/fit_test.py). No stack."""

from evals import fit_test


def test_fit_rule():
    assert fit_test.fits(4096, 8192, False)
    assert not fit_test.fits(4097, 8192, False)
    assert fit_test.fits(12288, 16384, False)


def test_truncation_line_means_no_fit():
    assert not fit_test.fits(100, 8192, True)
    assert fit_test.truncation_logged("time=1 level=WARN msg=\"truncating input prompt\" limit=8192")
    assert fit_test.truncation_logged("slot release: id 0 | task 3 | stop processing: n_tokens = 8192, truncated = 1")
    assert not fit_test.truncation_logged("time=1 level=INFO msg=\"loaded\"")
    assert not fit_test.truncation_logged("slot release: id 0 | task 3 | stop processing: n_tokens = 62, truncated = 0")


def try_(fits, errors):
    return {"fits": fits, "errors": errors}


def test_brief_passes_on_try_2():
    assert fit_test.brief_passes([try_(True, ["step 6: x"]), try_(True, [])])


def test_brief_fails_when_try_2_does_not_fit():
    assert not fit_test.brief_passes([try_(True, ["step 6: x"]), try_(False, [])])
    assert not fit_test.brief_passes([try_(True, ["step 6: x"]), try_(True, ["step 6: x"])])
    assert not fit_test.brief_passes([])


def test_ollama_refusal_counts_as_no_fit():
    body = '{"error":"{\\"error\\":{\\"code\\":400,\\"message\\":\\"request (19098 tokens) exceeds the available context size (8192 tokens)\\"}}"}'
    answer = fit_test.rejected_answer(body)
    assert answer["prompt_eval_count"] == 19098
    assert not fit_test.fits(answer["prompt_eval_count"], 8192, False)
