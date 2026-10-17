# Review: s5-mash-attenuation

Diff: main...s5-mash-attenuation at 7d630ca  ·  Verdict: ready for testing

Checked:
- Plan Tasks 1–3 against the diff, and brief R1–R7 / A1–A6.
- The 11 transcribed rows against Troester's PDF p. 22, rendered at 200 dpi: all 11 match the image.
- The knee formula, the SQL body and the clamps.
- Affected tests: 72 passed (`test_mash_attenuation`, `test_formulation_check`, `test_formulation_rules`, `test_reference_recipes`).
- Function owners in the DB: `postgres` for all three.
- Commits: one line each, no body.

Not re-checked here (left to verify): both SQL files applying twice, and the full `pytest` run.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | docs/RECIPE-ROADMAP.md:257 | The hint table still maps `dry / crisp` to "mash 64–65 °C". Under the new model, every mash from 64 to 68.3 °C gives the same attenuation (the middle of the yeast's range). The only part of 64–69 °C that changes the FG is 68.3–69 °C, which lowers it. The brief's Why section expects M4 to set the mash from these hints "and expect the FG to follow". Neither the doc-calc nor the roadmap records that the `dry` mash hint no longer changes the predicted FG. | M4 will be planned against a hint that has no effect in rule 10's maths. The consequence follows from the approved model a; only recording it is missing. The user decides whether to note it now or in the M4 brief. |
| 2 | should-fix | docs/work/s5-mash-attenuation/doc-calc.md:27-28 | §2 still says "**Approval needed: check each row against the image.**", although the file is approved. Line 28 also states as fact that the table's attenuation is "apparent attenuation, the same measure as `ref.yeast.attenuation_pct`". The same section then shows that (OE − AE) / OE does not give that column for 10 of 11 rows, and that the paper does not say which readings OE and AE are. | The slope is applied in points of `attenuation_pct`. Its unit therefore rests on a claim the file's own data leaves unverified, and CLAUDE.md asks for unverified facts to be marked as such. The stale approval line misleads a later reader. |
| 3 | note | docs/work/s5-mash-attenuation/doc-calc.md:31 (sample 2) | In the source image, sample 2's average temperature (70.5) equals its starting temperature, and its end temperature is 68.6. Every other row's average sits between its start and end, close to their mean. The transcription is faithful. If the true average were about 69.5 °C, the fit would give a slope of 3.97 and a knee of 67.84, which falls outside the 0.01 and 0.1 tolerances. | This is a possible error in the source, not in the transcription. It may be worth one line under doc-calc §7 known limits. |
| 4 | note | db/032_formulation_check.sql:31-32 | The function comment hard-codes 68.3 C and 4.15, while the function reads both from `app.formulation_limits()`. | The plan asked the comment to give the R4 sentence, so this is as planned. If the limits change, the comment goes stale, but rule 10's sentence will not, because it is built from the limits. |
| 5 | note | tests/test_mash_attenuation.py:68-74 | `test_function_follows_the_curve` checks differences (`att(T) − att(ref)`), so it cannot see a wrong absolute level. | `test_mash_mapping` pins the absolute ends and the middle (80 / 78 / 77.095), so between them the critical behaviour is covered. |
