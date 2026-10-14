# Review: s1-maths

Diff: main...s1-maths at b77ab3c  ·  Verdict: ready for testing

Checked: all 10 commits (0b863b9..b77ab3c), `db/030_maths.sql`, `tests/test_maths.py`, `doc-calc.md`,
the PROJECT.md / RECIPE-ROADMAP / WORKFLOW-ROADMAP edits. `pytest tests/test_maths.py`: 79 passed
(0.10 s). `pg_proc`: all 19 functions in `app`, owned by `postgres`. Every plan task is done as
written or covered by a Deviations line, every brief requirement (R1–R10) and acceptance criterion
(A1–A8) has its test or recorded check, and nothing outside the plan's Files table changed. No
secrets in the diff; commits are one line, no body.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | db/030_maths.sql:113-124, doc-calc.md:69-73 | `boil_gravity(og, batch_l, preboil_l)` uses the batch volume, but HTB p. 291 (quoted in doc-calc) says the **post-boil** volume. With `app.brewer_profile`, `losses_l` is "kettle + fermenter", so post-boil = batch + losses = pre-boil − boil-off, not batch. `test_solve_hops_round_trip` passes `batch` (20 L) too. | No caller yet, so nothing is wrong today. When m6 passes `batch_l` as the name suggests, 20 L / 2 L losses / 25 L pre-boil / OG 1.060 gives Gb 1.048 instead of 1.0528. Measured: IBU per gram goes from 1.125 to 1.174 (+4.4 %), so a 50 IBU recipe reads ~52 IBU, which is outside the ± 1 bar, and `solve_hops` doses ~4 % too few hops. Renaming the argument to `postboil_l` (and saying which volume the caller passes) would fix it without changing the maths. |
| 2 | should-fix | db/030_maths.sql:80-86, 150-157, 350-369, 401-425 | The "missing field raises" checks use `g->'key' is null`, which is false for a JSON `null` value. So `{"mashed": null}` silently counts as **not mashed** (full yield): measured 1 kg at 80 %, 50 % efficiency, 10 L gives OG 1.0307 instead of 1.0154. `{"pct": null}` in `solve_grist` and `{"share_pct": null}` in `solve_hops` return items with `kg` / `g` = null instead of raising. A null `grist` / `hops` argument gives OG 1.000 and IBU 0 (no rows from `jsonb_array_elements`). | The plan says bad input raises and never becomes 0. A caller that builds `mashed` from `usage = 'mash'` with a null `usage` would get a wrong OG with no error. Harmless until a caller exists. |
| 3 | note | tests/test_maths.py:99-102 | `test_boil_gravity_joe_ale` calls `app.og` (extract in the 23 L boil volume), not `app.boil_gravity`. This is what plan Task 2 specifies; `boil_gravity` itself is covered by `test_boil_gravity_book_example` (deviation line). | None; the name only reads as if it tests `boil_gravity`. |
