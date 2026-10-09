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

## Re-review 2026-10-09

Diff: main...malt-loader at d6d0a07  ·  Verdict: ready for testing

Checked: fix commit d6d0a07 (`IGNORE_HOPLINE_EXTRACT` removed; `user-supplied` source,
`USER_SUPPLIED` and `merge(..., user=...)`), the whole branch diff against plan.md (changed files
match the Files table; no other paths), the suite (23 passed), and the loaded rows. `merge` takes
the user's figure only in the last `elif`, after catalogue and hopline, and only `extract_pct` is
read from the entry; `potential_sg` follows the extract and its source. No code path still refers
to the removed flag. DB: 11 `ref.source` rows with `user-supplied` last; 74 fermentables, 73 EBC,
74 potential, 62 `max_pct`; potential sourced Weyermann 36 / Viking 31 / hopline 6 / user-supplied 1;
Crystal T50, DRC and Crystal Extra Dark extract 70.0, potential 1.0323 from `hopline-malts`;
Acidulated Malt extract 64.9, potential 1.0300 from `user-supplied`, with the user's wording in
`raw["user-supplied"]` (the only row carrying that key); every `potential_sg` equals
`round(1 + extract/100 × 46.214/1000, 4)` and shares the extract's `field_source`. Arithmetic:
30 / 46.214 = 64.9%, and 64.9 × 0.46214 = 29.993 → 1.0300. The plan (two dated Deviations,
Task 3/4/5 text, test table) and PROJECT.md §4, §5, §8 describe the new state; the fix commit is
one line with no trailer.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 5 | note | docs/work/malt-loader/verification.md | Written at 0257ccf, before the fix: it still reports 10 sources, 70 with potential and 22 tests. | The verify step has to rerun it; nothing else depends on it. |
| 6 | note | tests/test_malts.py:436 | The "user does not replace hopline" case merges Maris Otter (Simpsons) with the Weyermann Acidulated catalogue fixture. The assertion holds because that fixture has no extract. | Test still fails if the order of precedence broke; only the fixture pairing is odd. |

No must-fix or should-fix findings. Earlier findings 1–4 stand as recorded (1 left as is by the
user); finding 2's and 3's situations are unchanged by the fix.
