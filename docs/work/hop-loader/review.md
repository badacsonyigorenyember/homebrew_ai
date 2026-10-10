# Review: hop-loader

Diff: main...hop-loader at 1f019fd  ·  Verdict: ready for testing

Checked: all five plan tasks against the diff, brief R1–R9 and A1–A9, scope, the parser and
loader code, the tests, `db/011_ref_sources.sql`, PROJECT.md and the fill-ref index, commit
messages. Re-run during review: suite 33 passed; `grep -nwiE "ollama|llm"` on both hop modules
found nothing; read-only queries gave `ref.hop` 90 rows, 3 with `NULL` alpha (Delta, Lotus,
Sterling), 90 hop ingredients, 10 `ref.source` rows with `hopline-hops` and without
`hops-json` / `hopslist`, and the Citra row as in A5. `report.md` lists Delta, Lotus, Sterling,
the Nectaron pack sizes and Amarillo and Mosaic LUPOMAX (A8). Commits are one line each, no
body or trailer. No secrets in the diff.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | PROJECT.md:106 | The Database row still says "11 `ref.source` rows" (malt-loader) and now also "10 `ref.source` rows" (hop-loader). The 11 is no longer true. | CLAUDE.md asks PROJECT.md to describe the current state with measured facts; a reader sees two counts for one table. |
| 2 | note | loaders/hops.py:130, loaders/hop_products.py:131 | Lotus's purpose (`dual`) comes from hopline's subcategory listings for SKU `200669`, whose page carries Taurus's tags and text. Origin `USA` fits Lotus, not Taurus (German). Delta's `dual` and `US` fit both Delta and Falconer's Flight. Loading purpose and origin for both is the user's decision (R7). `report.md` doesn't say the purpose may be the other hop's. | If the shop classified the SKU by its Taurus content, Lotus's purpose is Taurus's. No action needed unless the user wants that line in the report. |
| 3 | note | loaders/hops.py:175 | A `HOPS` SKU missing from the fetched file stops `build` with a bare `KeyError: '<sku>'`, not a message naming `hop_products`. | The load still stops, nothing loads silently. Only the error message is less clear than the unknown-SKU `ValueError`. |
| 4 | note | loaders/hops.py:28 | Oil figures written as `%` (most pages) and as `ml` (Nectaron `1.0-1.7 ml`) both go into `total_oil_ml_100g` unchanged. This is the brief's unverified assumption, applied as planned. | Still unverified. A check against a grower sheet would confirm it later. |
