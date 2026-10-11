# Review: water-salts

Diff: main...water-salts at 0d09ea4  ·  Verdict: ready for testing

No brief; checked against `plan.md` and its source, `docs/work/fill-ref/README.md` item 7.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | note | loaders/water_salts.py:48-58 | All 8 salts computed and checked by hand against standard tables: epsom Mg 98.6 / SO4 389.7, MgCl2·6H2O Mg 119.6 / Cl 348.8, NaCl Na 393.4 / Cl 606.6, chalk Ca 400.4 / CO3 599.6, slaked lime Ca 540.9 / OH 459.1, plus the 3 tested salts. Only the 3 salts named in the plan have tests. | The untested 5 share the same code path (`ion_mg_per_l_per_g`) as the tested 3, so a wrong composition entry is the only way they could break unseen. No action. |
| 2 | note | loaders/water_salts.py:32-45 | `PARTS` / `WATER` is the recorded Task 1 deviation (counting parts instead of parsing formulas). It reads plainly: each salt lists its ions and waters, each part lists its atoms. | Readability check (§6.8) passes; no generic machinery. |
| 3 | note | ref.water_salt (DB) | Queried read-only: 8 `ref.water_salt` rows, 8 `ref.ingredient` rows of kind `water_salt`, all with source `water-chemistry`; stored ion values match the code output. | Confirms the Task 2 load-twice check and the PROJECT.md claim. |

Checks:
- Plan: both tasks done as written; the two differences are under Deviations.
- Scope: only the 3 files in the Files table plus `plan.md` changed.
- Correctness: molar mass includes water of hydration, ions exclude it; rounding is `ROUND_HALF_UP` to 0.1 in `Decimal`; the loader upserts on `ingredient_id` and `upsert_ingredient`'s natural key, so it is idempotent.
- Tests: `.venv/bin/python -m pytest -q` → 51 passed. The 3 tests compare exact `Decimal` values, so a wrong atomic mass, composition or rounding fails them.
- Safety: no secrets; no schema change (table and `water-chemistry` source already exist in `db/010`, `db/011`).
- Records: PROJECT.md §8 has entries for both tasks and the Database status names the 8 rows; commits are single lines with no trailer.
