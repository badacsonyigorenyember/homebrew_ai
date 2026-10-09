# Review: style-loader

Diff: main...style-loader at 3a30173  ·  Verdict: ready for testing

No brief; checked against the plan and its Source, [`docs/work/fill-ref/README.md`](../../work/fill-ref/README.md)
(global constraints, Review focus 1, 2, 4). Measured on 2026-10-09: suite 12 passed; in
`ref.beer_style` BA 169 rows / 144 with OG / 12 with open-ended SRM, BJCP 116 / 96; 15B is
`[1.036,1.044]|[25,45]|[25,40]`; every row's `source_id` is `ba-2026` or `bjcp-2021`; no
`empty` ranges; table owner `postgres`. Both source files are git-ignored (`.gitignore:21`) and
not in the diff. Source keys checked against the parser: every vitals key the files use is read,
no non-numeric vitals strings, and the only half-open pairs are the 12 BA SRM rows.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | note | loaders/styles.py:40 | Task 1 says "using `num` and `to_range`"; the code uses `to_range` plus a small local `text()` for blank-to-`None` on text fields, and does not import `num`. | Small helper, readable on its own; no plan change needed. |
| 2 | note | loaders/styles.py:108 | `source_id()` is looked up once per style (285 queries per run) instead of once per guide. | Harmless at this size; no measured need to change it. |
| 3 | note | ref.beer_style (BA) | `category_code` is `NULL` for all 169 BA rows, because `categorynumber` is `null` in every row of `ba_styles.json`. | Correct per "unknown stays NULL"; later steps should not expect a BA category code. |
| 4 | note | loaders/styles.py:82 | `load` has no automated test; idempotency rests on the plan's load-twice check (Review focus 4), which dev-verify repeats. | As planned; the upsert key matches the table's `unique (guide, edition, code)`. |
