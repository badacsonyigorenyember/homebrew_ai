# Review: m2-adjunct-role

Diff: main...m2-adjunct-role at 213c7b7  ·  Verdict: ready for testing

Checked: all 9 tasks against the plan, R1–R10 and A1–A10 of the brief, the full diff (db, shared,
evals, n8n exports, tests, docs), the result files, and the database. Re-run during review:
`pytest` 252 passed (stack included); the A9 grep finds only the two `drop function` lines in
`db/023_drop_adjunct_rule.sql`; `pg_proc` has no `app.adjunct%` function. Recomputed from
`evals/results/2026-10-14-m2-role-gate.json`: gated clear 21/21 (63/63 runs), held-out 10/10,
0 inconsistent, ambiguous r22–r24 `feature`; hot clear 61/63, held-out 29/30, flips r05, r20, h03;
word rule 28/31 (misses r21, h05, h09); median `llm_ms` 12.82 s gated, 12.41 s hot. The gate
file's prompt sha256 equals the committed prompt (frozen at af64d2b, unchanged since). G2 run
`2026-10-14-m2-role.json` read back from `app.run_step`: b05 15B with mismatch named 20C, b12 31B
(alt 18A, reason cites `"feature"`), b19 17C, b17 8B. The 34 wordings in `evals/role_wordings.toml`
match the plan table field for field.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | docs/work/m2-adjunct-role/brief.md (Deviations) | The 2026-10-14 retune changed two step 1 rules outside the brief's scope (role only): a remark about how much the user will drink is dropped (no hint, no `unknown`), and a wish that asks for an ingredient goes to `wanted` instead of `unknown`. The user allowed it, and plan.md records it, but brief.md has no Deviations line. | Conventions: a scope change is recorded in brief.md too. A reader of the brief would not know step 1's `hints`/`unknown` behaviour changed in this work. |
| 2 | should-fix | PROJECT.md:171 | "When step 1 gives a wanted adjunct the role `feature` (and `background` otherwise), the specialty code is picked" — the parenthetical reads as if `background` also picks the specialty code. | PROJECT.md is the single source of truth; the sentence states the rule ambiguously. |
| 3 | note | shared/prompts/step1.system.md:22-24, 34-36 | The retune stays general in form (placeholder `X`, no 5-word run from any brief or wording; `test_prompt_quotes_no_role_wording` passes), but its examples come straight from the tuning data: "X forward" / "X-forward" is the cue of clear wordings r04, r07–r09, r12, and the drinking rule fits b05 ("something I can drink a few pints of"). So clear 21/21 and G1 step 1 22/22 are scores on wordings the prompt was tuned on; held-out 10/10 is the only independent number. The retune was also made after the first full gate run (2026-10-13), whose saved result shows held-out answers, though no held-out wording was run during the tuning iterations. | Context for how much the 21/21 and 22/22 say; the user approved this retune. |
| 4 | note | shared/prompts/step1.system.md:22-24 | Drinking remarks are now left out of the brief entirely, not kept in `unknown`. | A "drink a few pints" wish no longer reaches step 2 in any form. Approved as the b05 fix; recorded here so it is a known behaviour. |
| 5 | note | evals/results/2026-10-13-m2-fix3.json vs 2026-10-14-m2-role*.json | Step 1 median on the 22 briefs went from 12.72 s (m2-fix3) to 13.18 s (m2-role) and 13.40 s (m2-role-g1), about +4–5%; the wordings' gated median is 12.82 s against the 12.5 s benchmark figure. | The brief assumed "not far above 12.5 s" (unverified); it is now measured and modest. No requirement covers it. |
| 6 | note | docs/work/m2-adjunct-role/plan.md:117-129 | Task 2 still names the MCP `update_workflow` and MCP publish route; the n8n CLI import actually used is recorded under Deviations, but the task text was not edited to match. | Conventions ask for both; the record is complete, the task text is out of date. |
| 7 | note | n8n/workflows/step-1-read-request.json (`Build model request` notes) | The node note still says "Fixed options for a repeatable answer (R5)"; the options now come from the input with defaults 0 and 42. The sticky note was updated. | A reader of the workflow sees a stale statement. |
| 8 | note | PROJECT.md:230 | The re-measured Task 6 entry (2026-10-14 work) sits under the `### 2026-10-13` heading, and it replaced the first, NOT MET Task 6 entry rather than adding one (the NOT MET result survives as one sentence in it). | Log order and dates are slightly off; no information lost that the plan and result files do not hold. |
| 9 | note | docs/work/m2-adjunct-role/plan.md | Checked the orchestrator's concern: compared to the approved plan (f75ee38), the current plan differs only in ticks, `Stage`, the new `## Gate result` and Deviations; Tasks 7–9, the tests table and Approved exceptions are intact. The gate verdict (MET) was in plan.md at af8f36d, before the first step 2 change (20f0a2c) and the deletion (c501c3e), so A6 holds. | Plan is complete and accurate. |
| 10 | note | tests/test_contracts.py, tests/test_step1_check.py, tests/test_prompt.py | Task 4's tests were not seen failing first. Checked by reading: with the old `items: string` schema, the plain-string bad case would be accepted and the good `BRIEF` (object item) rejected, so `test_bad_examples`, the good-example test and `test_plain_string_item_fails` would fail if the contract change were reverted; `test_prompt_names_every_role` fails if either role leaves the prompt. | The tests do guard the critical behaviour. |
