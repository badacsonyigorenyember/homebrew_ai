# Review: ref-spotcheck

Diff: main...ref-spotcheck at 27a1bb3  ·  Verdict: ready for testing

No brief; checked against `plan.md` and its Source, the P1a index item 8 (moved from
`docs/work/fill-ref/README.md` to `docs/FILL-REF-README.md` on `main` in 941f102).
Checked on 2026-10-11: ran the pack read-only against the live DB (16 sources, 285 styles,
291 ingredients = 74 + 90 + 119 + 8, 0 without a source, the 8 style-fit tables 0; every column
it selects exists), `pytest` 51 passed, and every `field_source` slug in `fermentable`, `hop`
and `yeast` resolves to a `ref.source` row.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | docs/DATABASE.md:417 | The step-2 gap note says "the Beer Maverick alpha and oil of Delta, Lotus, Sterling and Mount Hood". Measured `field_source`: Mount Hood's alpha is from `hopline-hops` (only its oil is from `beermaverick`), and Enigma's `purpose` is from `beermaverick` but is not named. PROJECT.md §5's hop row states it correctly. | DATABASE.md is meant to hold measured facts; the note names one value too many and misses one. The wording came from the plan text, not from the DB. |
| 2 | should-fix | docs/DATABASE.md:417, PROJECT.md §5 hop row | The plan asked that the hand-entered Beer Maverick figures be checked against their source too. The docs record that only Sterling was in the random sample; Delta, Lotus, Mount Hood and Enigma's Beer Maverick values were not checked. | The docs state this honestly, so nothing is wrong now; the user decides whether those 7 values need a targeted check before P1a is called done. |
| 3 | note | docs/work/ref-spotcheck/plan.md:4 | `Source:` links `../fill-ref/README.md`, which no longer exists (moved to `docs/FILL-REF-README.md` on `main`). | Broken link only; dev-ship moves the folder anyway. |
| 4 | note | db/checks/ref_spotcheck.sql:33 | The "rows without a source" check cannot return anything but 0: `beer_style.source_id` and `ingredient.source_id` are `NOT NULL` with a foreign key to `ref.source`. The check is what the plan asked for and is harmless; the schema already guarantees it. | A reader should not take the 0 as evidence beyond the constraints. |
| 5 | note | PROJECT.md §5 hop row, §8 | "Sterling's Beer Maverick values among them" comes from the run output shown to the user; the sample is random (`order by random()`), so the claim cannot be re-checked from the code. | Recorded as given; no action. |

Plan: Task 1 done as written; the suite count change (40 → 51) is recorded under Deviations.
Scope: only the three files in the plan's Files table plus `plan.md`. Safety: the pack is
read-only (`default_transaction_read_only = on`), no secrets, no schema change. Records:
PROJECT.md §4, §5 and §8 updated; commits are one line, no trailer.
