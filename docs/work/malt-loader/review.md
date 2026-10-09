# Review: malt-loader

Diff: main...malt-loader at a2c0c38  ·  Verdict: ready for testing

Checked: the branch diff against plan.md (no brief; the plan is the spec), the suite (22 passed),
the real source files (`hopline_malts.json`, `malt_catalogue.json`) run through the parsers,
spot checks of `malt_catalogue.json` against the PDF text (Acidulated, Viking Smoked Malt,
Simpsons crystals, Maris Otter), and the loaded rows: 10 `ref.source` rows without the two old
slugs, `field_source jsonb not null`, 74 fermentables (Weyermann 37, Viking 32, Simpsons 5),
sources 37 / 31 / 5 / 1, counts 73 EBC / 70 potential / 62 `max_pct` with the 36 / 8 / 1 / 17
split, the Maris Otter row as tested, and every `potential_sg` equal to
`round(1 + extract/100 × 46.214/1000, 4)` recomputed in SQL. All match the plan and PROJECT.md.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | loaders/malts.py:492 (`max_pct_from_text`) | Some catalogue usage texts state a limit in wording the parser does not know: Weyermann Acidulated "Maximum addition 5%", Viking Chocolate Dark "under 10%", Cookie "under 20%", Rye "under 7%". They parse to `None`, so `max_pct` falls back to hopline. Hopline gives the same numbers today (5, 10, 20, 7), so the values are right, but `field_source.max_pct` says `hopline-malts` for 4 rows where the catalogue states the limit. The plan's rule list does not include these wordings, so this is plan-conformant. | Provenance is off for 4 rows, and if hopline's figure changes or is missing these malts would get the wrong or no limit although the catalogue states one. |
| 2 | note | loaders/malts.py:484 | Viking Wheat Malt: the catalogue's "around 50%" is correctly not taken as a limit, but hopline's "50% (20%ban …)" then gives `max_pct` 50 from hopline. Follows the plan as written. | A vague catalogue figure still ends up as a stated maximum through hopline. |
| 3 | note | db/011_ref_sources.sql:128 | The `hopline-malts` edition hard-codes "website, fetched 2026-10-09" and the insert is `on conflict do nothing`, so a later re-fetch keeps the old date. As the plan specifies. | Only matters when hopline is fetched again. |
| 4 | note | git log eaaa59e | The plan commit `Add plan: malt-loader` carries a `Co-Authored-By` trailer; conventions ask for one line with no trailer. The five task commits are one line each. | Records only; rewriting it is not worth it. |

No must-fix findings. Plan tasks 1–5 are done as written, with every difference recorded under
Deviations; scope matches the Files table; the maths is in tested code; no secrets; DB changes
are `.sql` files applied as `postgres`; source files stay git-ignored; PROJECT.md §4, §5 and §8
are updated.
