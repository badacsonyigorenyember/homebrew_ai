# S8 · Ingredient intake: add fermentables, hops and yeasts by hand — implementation plan

Stage: implementing
Brief: [brief.md](brief.md)
Branch: s8-ingredient-intake

## Approach
One TOML file per ingredient in `shared/ingredients/<kind>/`, one per new source in
`shared/ingredients/sources/`. `loaders/extra_ingredients.py` reads the folder, runs every check
and prints **all** problems as `<file>: <field>: <problem>`; `--check` stops there and writes
nothing. Without `--check` it then writes, in one transaction: sources, each ingredient (one
plain function per kind: `load_fermentable`, `load_hop`, `load_yeast`), its aliases, then checks
that each alias resolves to its product only, then re-runs the tagger (`tags.load_vocab` +
`tags.derive_tags`) and prints the R9 summary. Any failure rolls the whole run back.

No real ingredient is added in this work (R11, user 2026-10-17): `shared/ingredients/` ships
with templates and empty kind folders, and the path is proven by the fixture set in
`tests/fixtures/ingredients/`, which tests load only inside transactions they roll back. **Never
run the load command (without `--check`) on `tests/fixtures/`**: it would commit fixture rows into
the live `ref`.

How intake rows stay apart from loader rows (R4): an intake row is any `ref.ingredient` row with
`raw ? 'intake'`; `raw = {"intake": {"path", "text", "fields"}}` (path relative to the repo
root, the file text as written, the parsed fields). A clash is caught both ways round: against
the keys the hopline loaders would write (from their product maps: `malt_products.PRODUCTS`,
`adjunct_products.PRODUCTS` + `PALMER_ONLY`, `hop_products.HOPS`, `yeast_products.YEASTS`) and
against any `ref.ingredient` row without the `intake` key. The loaders themselves are not
changed; they never delete and only upsert their own keys, so they leave intake rows alone.

Aliases (R6): a new `ref.ingredient_alias` table. The current resolver body becomes
`app.resolve_ingredient_by_name(word)` unchanged; `app.resolve_ingredient(word)` first tries the
aliases and falls back to it. `--check` refuses an alias that `resolve_ingredient_by_name` maps to
any other product, or whose words equal another product's alias.

Descriptor words are checked against `loaders/style_fit_vocab.toml` (the file `ref.tag_synonym`
is loaded from), so a word you just added there passes `--check` before the tagger has run; the
load re-runs `load_vocab` first, so check and tags always agree. Origins are checked against the
`origin` tags of the same file.

## Intake file format
This is the contract the templates, the checks, the tests and later the s10 form share. Every
key is present in the template; `""` or `[]` means "not filled". Ranges are `[low, high]` (one
value: `[x, x]`). Units: %, EBC, °C, mL/100 g, minutes.

| Key | Kinds | Required | Allowed / unit |
|---|---|---|---|
| `kind` | all | yes | must equal the folder: `fermentable`, `hop`, `yeast` (`misc` → "misc arrives in s9") |
| `name` | all | yes | as the maker prints it |
| `producer` | all | fermentable, yeast | hop may be `""` (as hopline hops are) |
| `source` | all | yes | a slug in `ref.source` or in `sources/` |
| `description`, `description_ref` | all | yes | one to three English sentences from the source; page or URL. Fermentable → `ref.fermentable.description`; hop, yeast → `raw` only (no column) |
| `aliases` | all | no | words a brewer types for this product |
| `descriptors` | all | hop, yeast (≥ 1) | each a `character` tag name or a `[synonyms]` key (compared as `name_key`) |
| `extract_dbfg_pct` | fermentable | yes | % dry basis |
| `ebc` | fermentable | no | range, EBC |
| `role` | fermentable | yes | `base kilned crystal roast adjunct sugar` (`fermentable_facts.ROLES`) |
| `fermentability` | fermentable | no | `full normal none`; absent = column default `normal`; not `normal` needs `fermentability_ref` |
| `max_pct` | fermentable | no | % of grist |
| `enzyme_activity` | fermentable | no | `none low normal high` |
| `min_boil_min` | fermentable | no | 60–120; absent → 60 with source `palmer-how-to-brew` (`fermentable_facts.BOIL_SOURCE`), the rule `fermentable_facts` applies to every fermentable |
| `alpha_pct` | hop | yes | range, % |
| `purpose` | hop | yes | `aroma bittering dual` |
| `origins` | hop | yes | list of `origin` tags in the vocab file (US DE CZ GB SI NZ AU JP FR ZA today) |
| `total_oil_ml_100g` | hop | no | range, mL/100 g |
| `type` | yeast | yes | `ale lager kveik brett lacto pedio` |
| `temp_c` | yeast | yes | range, °C |
| `attenuation_pct` | yeast | yes, except `lacto`/`pedio` | range, % (a souring culture's sheet usually states none; it stays NULL) |
| `flocculation` | yeast | no | the 7 values of the `ref.yeast` check constraint |
| `form` | yeast | no | `dry liquid` |
| `alcohol_tolerance_pct` | yeast | no | % |
| `product_id` | yeast | no | text, the maker's code |
| `<field>_ref` | all | for every filled figure | page or URL. Figures: every number and range above, plus `description`, `enzyme_activity`, `fermentability` ≠ `normal` |
| `<field>_source` | all | no | another slug for that one field (e.g. `user-supplied`); otherwise the field's source is `source` |

A key outside this table is refused (a typo would otherwise drop a value silently).
Source files `sources/<slug>.toml`: `slug` (= file name), `title`, `edition` required;
`publisher`, `url`, `licence` optional. The loader writes `notes = 'intake: <path>'`; a source file
whose slug is already in `ref.source` without that note (a `db/011` row) is refused: use the slug
as `source` instead.

## Files
| Path | New / changed | Purpose |
|---|---|---|
| `db/010_ref_schema.sql` | changed | `ref.ingredient_alias` table (appended) |
| `db/036_ingredient_resolver.sql` | changed | `app.resolve_ingredient_by_name` (today's rules 1–2) and the alias rule first in `app.resolve_ingredient` |
| `tests/test_ingredient_resolver.py` | changed | alias tests |
| `shared/ingredients/README.md` | new | the "add an ingredient" checklist (INGREDIENT-INTAKE §13, as built) |
| `shared/ingredients/_templates/fermentable.toml`, `hop.toml`, `yeast.toml`, `source.toml` | new | commented templates: each key with what it is, unit, required or not |
| `shared/ingredients/fermentable/`, `hop/`, `yeast/`, `sources/` (`.gitkeep` while empty) | new | intake folders |
| `loaders/extra_ingredients.py` | new | reader, checks, per-kind loaders, summary, CLI |
| `loaders/tags.py` | changed | `descriptor_tag` helper; intake rows read `raw.intake.fields`; `lacto`/`pedio` → family `sour` |
| `tests/test_extra_ingredients.py` | new | checks, load, tags, summary, spot-check queries, all on the fixtures |
| `tests/fixtures/ingredients/` | new | the valid fixture set that proves the intake (R11): `sources/fixture-data-sheet.toml`, `fermentable/fixture-crystal.toml`, `hop/fixture-hop.toml`, `yeast/fixture-ale.toml`, `yeast/fixture-lacto.toml` |
| `tests/test_tags.py` | changed | intake unit tests; G10 hop count |
| `tests/test_fermentable_facts.py` | changed | G10: DB counts over non-intake rows |
| `db/checks/ref_spotcheck.sql` | changed | intake rows per kind and with their source; `ingredient_alias` in the row counts |
| `docs/DATABASE.md`, `PROJECT.md` | changed | fill order, tables, counts, log |

## Tasks

### Task 1: The resolver reads aliases
Why: R6, A7 need a place for aliases and a resolver that reads them (Q6).
- [x] Append to `db/010_ref_schema.sql`:
  `create table if not exists ref.ingredient_alias (ingredient_id bigint not null references ref.ingredient (id) on delete cascade, alias text not null, primary key (ingredient_id, alias));`
  with a comment: written by `loaders/extra_ingredients.py`, read by `app.resolve_ingredient`.
- [x] In `db/036_ingredient_resolver.sql`: rename today's `app.resolve_ingredient` body to
  `app.resolve_ingredient_by_name(word text)` (same columns, rules 1–2 unchanged). New
  `app.resolve_ingredient(word text)`, same return columns: rule `alias` first — every product
  with an alias whose `app.ingredient_words` (sorted) equal the query's words, or equal the query's
  words with kind words removed when the product is of that kind (alias "fixture crystal": "fixture crystal malt" → that
  product; "fixture crystal yeast" finds no alias); `distinct`, ordered by name, id. Only when that finds nothing,
  return `app.resolve_ingredient_by_name(word)`. Update the header comment.
- [x] Apply as `postgres`, table first:
  `docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/010_ref_schema.sql`, then the same for `db/036_ingredient_resolver.sql`.
  Check the owner: `select tableowner from pg_tables where tablename = 'ingredient_alias'` → `postgres`.
- [x] Write tests in `tests/test_ingredient_resolver.py` (stack; insert a temporary alias for an
  existing product, roll back in `finally`):
  `test_alias_finds_only_its_product` (alias `"zz test alias"` on Citra → `[Citra]`, rule `alias`),
  `test_alias_with_kind_word` (`"zz test alias hop"` → Citra; `"zz test alias malt"` → not via the alias),
  `test_by_name_ignores_aliases` (`resolve_ingredient_by_name("zz test alias")` → `[]`).
- [x] Run `.venv/bin/pytest tests/test_ingredient_resolver.py tests/test_step3.py`, expect all pass (existing tests unchanged).
Done when: the table exists owned by `postgres`, both functions exist, all resolver and step 3 tests pass.
Commit: `Add ingredient aliases to the resolver`

### Task 2: Intake folder, templates and file checks
Why: R1, R2 (the checks that need only the files, the vocab and the maps), A1, A2.
- [x] Create `shared/ingredients/` with `fermentable/`, `hop/`, `yeast/`, `sources/` (`.gitkeep`),
  `_templates/` with `fermentable.toml`, `hop.toml`, `yeast.toml`, `source.toml` per the format
  table (every key present, empty, with a comment line: what, unit, required). No `misc/`.
- [x] Add `descriptor_tag(word, synonyms, character_tags) -> str | None` to `loaders/tags.py`:
  `synonyms.get(name_key(word))`, else `word` when it is a character tag name, else None. Unit test
  in `tests/test_tags.py`.
- [x] `loaders/extra_ingredients.py`, first part: a module docstring (what, folder layout, load
  order, usage); `read_folder(root) -> (sources, ingredients)` where each item keeps its relative
  path, text and parsed fields (a TOML syntax error is a check error naming the file);
  `Known` (a dataclass: source slugs and their notes, origin tags, character tags, synonyms,
  loader-owned keys, DB rows by key) with `known_from_files(vocab)` filling the vocab and map
  parts; `check_files(sources, ingredients, known) -> list[str]` calling one function per kind
  (`check_fermentable`, `check_hop`, `check_yeast`, `check_source`) plus the cross-file checks:
  folder vs `kind`, misc refused, unknown keys, required fields, allowed values, low > high,
  figure without `_ref`, `source` / `<field>_source` not in `known` or `sources/`, source without
  edition, `fermentability` ≠ `normal` without ref, unknown descriptor word, unknown origin,
  `(kind, name_key(producer), name_key(name))` in the loader maps, two files with the same key.
  Keys compare with `loaders.common.name_key`.
- [x] Fixtures: `tests/fixtures/ingredients/` as in the Files table. Invented values, clearly
  fake names (producer `Fixture Maltings`, `Fixture Yeasts`), source slug `fixture-data-sheet`,
  edition `test fixture`; known descriptors only (`caramel`, `dried-fruit`, `citrus`, `pine`,
  `fruity`, `sour`); `fixture-lacto` has `type = "lacto"` and no attenuation. These are only ever
  loaded inside rolled-back test transactions.
- [x] Write tests in `tests/test_extra_ingredients.py` (no stack):
  `test_fixtures_pass` (no errors, with `fixture-data-sheet` coming from `sources/`);
  `test_template_filled_from_fixture_passes` (A1: each template's keys ⊇ the fixture's keys of that
  kind; template fields updated with the fixture's values pass);
  `test_refusal[...]` parametrized, one case per R2 refusal (a mutated copy of the fixtures in
  `tmp_path`): each returns an error starting with that file's path and naming the field —
  missing required field per kind, bad `role`/`fermentability`/`purpose`/`flocculation`/`type`/`form`,
  `ebc` low > high, `alpha_pct` without `alpha_pct_ref`, unknown `source`, source file without
  `edition`, `fermentability = "none"` without ref, unknown descriptor, a hop named `Citra`
  (loader map), two files with one product, a file in `misc/`, an unknown key;
  `test_all_errors_reported` (two broken files → both named).
- [x] Run `.venv/bin/pytest -m "not stack" tests/test_extra_ingredients.py tests/test_tags.py`, expect all pass.
Done when: the folder and templates exist; every R2 refusal that needs no DB has a passing test.
Commit: `Add ingredient intake folder, templates and checks`

### Task 3: Database checks and `--check`
Why: R2 (source in DB, clash with a loaded row, aliases), R4 (clash either order, orphans), A2, A5.
- [x] `known_from_db(conn)`: `ref.source` slugs with notes; `ref.ingredient` keys with whether
  `raw ? 'intake'` and the stored path. Add to `check_files`: a file key that matches a DB row
  without `intake` → "clashes with <producer name> loaded by another loader"; a source file whose
  slug is a non-intake `ref.source` row → refused.
- [x] `check_aliases(conn, ingredients) -> list[str]`: per alias, `app.ingredient_words` for each;
  refuse equal words on two files; refuse when `app.resolve_ingredient_by_name(alias)` returns any
  row that is not this file's own row (by key); refuse when `ref.ingredient_alias` holds the same
  words for another ingredient.
- [x] `orphans(known, ingredients)`: intake rows in the DB whose key no file has (reported, never
  deleted).
- [x] CLI `python -m loaders.extra_ingredients [--check] [path]` (default `shared/ingredients`,
  resolved from the repo root). `--check`: connection with `read_only = True`, run all checks,
  print each error and exit 1, or print `ok: N files (fermentable a, hop b, yeast c, sources d)`
  plus the orphan list; always roll back. `main(argv=None)` so tests can call it.
- [x] Write tests (stack): `test_check_writes_nothing` (row counts of `ref.source`,
  `ref.ingredient`, the three kind tables and `ref.ingredient_alias` equal before and after
  `main(["--check", bad])` exits 1 and after `main(["--check", fixtures])` passes);
  `test_clash_with_db_row` (a fixture yeast renamed to `SafAle US-05`, producer `Fermentis`, checked
  with `Known.loader_keys` emptied, so only the DB row can catch it → refused); `test_alias_finding_another_product_refused` (fixture hop alias `citra`
  → refused naming Citra); `test_source_slug_of_db011_refused` (a source file with slug
  `bjcp-2021`).
- [x] Run `.venv/bin/pytest tests/test_extra_ingredients.py`, expect all pass.
Done when: `--check` on the fixtures prints ok, on each bad case names file and field, and writes nothing.
Commit: `Check intake files against the database`

### Task 4: The tagger reads intake rows
Why: R5, R10; G3 (the tagger reads hopline page shapes only).
- [ ] In `loaders/tags.py` `derive_tags`: an intake row (`'intake' in raw`) takes its words from
  `raw["intake"]["fields"]["descriptors"]`, resolved with `descriptor_tag`; a word it cannot
  resolve goes to `ingredient_review` as "unknown words: …". Hop: origins from `ref.hop.origins` as
  today; empty descriptors → "no descriptor text". Fermentable: family from `role` as today,
  characters from the descriptors instead of the name/description scan (the fermentable query also
  selects `i.raw`). Yeast: family from `INTAKE_YEAST_FAMILY = {"ale": "ale", "lager": "lager",
  "kveik": "kveik", "brett": "brett", "lacto": "sour", "pedio": "sour"}` by `ref.yeast.type`.
  Hopline rows keep today's path untouched. Update the module docstring's "Where the words come from".
- [ ] Write tests in `tests/test_tags.py` (no stack): `test_intake_words` (the descriptors of an
  intake raw; a hopline raw unchanged); `test_intake_yeast_family` (lacto and pedio → sour).
  The existing `test_retag_is_identical` still passes.
- [ ] Run `.venv/bin/pytest tests/test_tags.py`, expect all pass.
Done when: tagging is unchanged for every existing row (retag test) and intake raws resolve as above.
Commit: `Tag intake rows from their descriptor words`

### Task 5: Load intake files
Why: R3, R4, R5, R6, R9, R10; A3–A7, A10.
- [ ] `load_source`: upsert on `slug` with `notes = 'intake: <path>'`. `load_fermentable`,
  `load_hop`, `load_yeast`: `upsert_ingredient(conn, kind, name, producer, source_id, raw)`, then
  insert-or-update the kind row (all columns of the format table, `common.num` / `common.to_range`),
  `field_source` = `{field: <field>_source or source}` for every filled field (fermentable also
  `min_boil_min`, defaulted or not; `fermentability` only when the file sets it). Aliases: delete
  this ingredient's rows in `ref.ingredient_alias`, insert the file's. No `fermentable_style`
  rows (`fermentable_facts` deletes and rebuilds that table).
- [ ] `load(conn, sources, ingredients) -> dict` writes sources first, then each kind, then
  checks every alias: `app.resolve_ingredient(alias)` must return exactly this row, else raise.
  `main` without `--check`: checks (exit 1 on errors), `load`, `tags.load_vocab` +
  `tags.derive_tags`, summary, commit (the `with connect()` block); any exception rolls back.
- [ ] `summary(conn, ingredients, counts) -> dict` and its printout (R9): rows loaded per kind;
  sources added (slugs new in this run); intake rows tagged / flagged for review (with names and
  reasons); rows no file backs; aliases checked; "waits for maths" for `lacto`/`pedio` yeasts
  (INGREDIENT-INTAKE §13 step 5); `ref.ingredient` count per kind.
- [ ] Write tests (stack, every one in a transaction rolled back in `finally`, loading the
  fixtures): `test_load_twice_same_rows` (A3: same counts in `ref.source`, `ref.ingredient`, kind
  tables, aliases and the same row values); `test_field_source_covers_filled_fields` (A3: keys ==
  filled columns; `raw.intake` has path, text, fields); `test_intake_fermentable_usable` (A4: role
  and description set without a `fermentable_facts.toml` entry; `app.style_level('21A', id, 'mash')`
  has a non-null `level` — pick another s3 style if 21A gives none); `test_hopline_loaders_leave_intake_rows`
  (A5: snapshot intake rows incl. kind row, `raw`, aliases; run `malts.load(build(...))`,
  `adjuncts.load`, `fermentable_facts.load(conn, read())`, `hops.load`, `yeasts.load` on the files in
  `shared/rag-files/` (skip if absent); snapshot equal); `test_intake_rows_tagged` (A6, R10:
  fixture hop has origin `US` and its character tags, ale yeast family `ale`, lacto family `sour`,
  none in `ingredient_review`); `test_every_alias_resolves` (A7, A11: every fixture alias and
  every fixture name, the lacto culture included, resolves to that product only); `test_summary_counts` (A10:
  summary per-kind counts == `select kind, count(*) from ref.ingredient group by kind`).
- [ ] Run `.venv/bin/pytest tests/test_extra_ingredients.py tests/test_tags.py tests/test_ingredient_resolver.py`, expect all pass; `ref` row counts unchanged afterwards (fixtures rolled back).
Done when: all of the above pass and the live DB has no fixture rows (`select count(*) from ref.ingredient where raw ? 'intake'` → 0).
Commit: `Load intake files into ref`

### Task 6: Size-free tests and the spot-check pack
Why: R7, R8; A8 (G10), A9.
- [ ] `tests/test_tags.py::test_every_hop_tagged_or_flagged`: `count of hops where not raw ? 'intake'`
  == 89; every hop (intake too) tagged or flagged.
- [ ] `tests/test_fermentable_facts.py`: restrict DB reads to `not i.raw ? 'intake'` in
  `test_file_matches_the_database` (the 81 vs `fetch_rows`), the `db_rows` helper (used by
  `test_db_roles`, `test_db_enzyme_and_boil`), the role counts in `test_db_roles`, the null
  `max_pct` count in `test_db_max_pct`, and the description count in `test_db_descriptions`.
  The map-size tests (`test_hops.py:169`, `test_yeasts.py:229`, `test_malts.py:170`) stay: they
  pin what the hopline loaders load.
- [ ] Prove it: in a rolled-back transaction with the fixtures loaded, these assertions hold — add
  `test_g10_counts_ignore_intake_rows` to `tests/test_extra_ingredients.py` that loads the fixtures
  and re-runs the same filtered queries (89 hops, 81 fermentables).
- [ ] `db/checks/ref_spotcheck.sql`: `ingredient_alias` in the row counts (fix the table count in
  the header); new sections "Intake rows per kind" (`where raw ? 'intake'`) and "Intake rows with
  their source" (kind, producer, name, source slug, edition, `raw->'intake'->>'path'`, aliases).
- [ ] Write test `tests/test_extra_ingredients.py::test_spotcheck_lists_intake_rows` (stack, A9):
  load the fixtures in a transaction, read the statements under the two "Intake" `\echo` headings
  of `db/checks/ref_spotcheck.sql`, run them on the same connection, expect the five fixture rows
  with slug `fixture-data-sheet` and its edition; roll back.
- [ ] Run `.venv/bin/pytest tests/test_tags.py tests/test_fermentable_facts.py tests/test_extra_ingredients.py`, expect all pass; run the pack (`docker exec -i supabase-db psql -U postgres -d postgres < db/checks/ref_spotcheck.sql`), expect the new sections with 0 intake rows (none are real).
- [ ] Run `.venv/bin/python -m loaders.extra_ingredients --check` on the real (empty) folder, expect `ok: 0 files`.
- [ ] Run `.venv/bin/pytest` (full, stack up), expect all pass (A8). A failure caused by intake rows
  outside the G10 list: stop and report it, do not widen this task.
Done when: the G10 tests pass with fixture rows present and still pin 89 hops and 81 fermentables; full pytest passes; `select count(*) from ref.ingredient where raw ? 'intake'` → 0.
Commit: `Make catalogue-size tests ignore intake rows`

### Task 7: Docs and counts
Why: brief scope (DATABASE.md, PROJECT.md); CLAUDE.md "PROJECT.md is the single source of truth".
- [ ] `shared/ingredients/README.md` final check against what was built (one command loads and tags).
- [ ] `docs/DATABASE.md`: `source` row ("also `shared/ingredients/sources/`"); new
  `ingredient_alias` row (0 rows, measured); `ingredient` row "filled from … and
  `shared/ingredients/` (0 intake rows)"; counts stay as measured (no real item added); §7 fill order step 2 adds `loaders.extra_ingredients`
  and the load order `malts → adjuncts → fermentable_facts → hops → yeasts → extra_ingredients →
  tags → style_envelopes`; the `fermentable` row's "loaded by fermentable_facts" note says intake
  fermentables carry their own facts.
- [ ] `PROJECT.md`: §4 Scripts row (the intake loader, its command and test count), §8 dated entry
  linking `docs/work/s8-ingredient-intake/`, with the pytest result, and that no real ingredient
  was added (proven by fixtures; Special B and a souring culture wait for M5).
- [ ] Run `.venv/bin/pytest -m "not stack"`, expect pass.
Done when: the docs state measured numbers only.
Commit: `Document ingredient intake`

## Critical behaviour and its tests
| Behaviour | Test | Task |
|---|---|---|
| An alias finds its product and only it; kind words respected | `test_ingredient_resolver.py::test_alias_finds_only_its_product`, `test_alias_with_kind_word` | 1 |
| The resolver without aliases is unchanged | existing `test_ingredient_resolver.py`, `test_step3.py` | 1 |
| Each R2 refusal names file and field | `test_extra_ingredients.py::test_refusal[...]`, `test_clash_with_db_row`, `test_alias_finding_another_product_refused`, `test_source_slug_of_db011_refused` | 2, 3 |
| `--check` writes nothing | `test_check_writes_nothing` | 3 |
| Tags for existing rows unchanged; intake words and lacto → sour | `test_tags.py::test_retag_is_identical`, `test_intake_words`, `test_intake_yeast_family` | 4 |
| Load is idempotent; every filled field sourced; raw keeps file and path | `test_load_twice_same_rows`, `test_field_source_covers_filled_fields` | 5 |
| An intake fermentable works without `fermentable_facts.toml` | `test_intake_fermentable_usable` | 5 |
| Hopline loaders leave intake rows unchanged | `test_hopline_loaders_leave_intake_rows` | 5 |
| Intake rows tagged, not flagged | `test_intake_rows_tagged` | 5 |
| Summary counts match `ref` | `test_summary_counts` | 5 |
| G10 tests still pin hopline sizes with intake rows present | `test_g10_counts_ignore_intake_rows` + edited `test_tags.py`, `test_fermentable_facts.py` | 6 |
| Fixture products, the lacto culture included, resolve by name and alias | `test_every_alias_resolves` | 5 |
| The spot-check pack lists intake rows with their source | `test_spotcheck_lists_intake_rows` | 6 |

A12 (you fill one template yourself, README only, and it passes `--check`) is a manual step for
dev-verify; the filled file is not loaded and not committed.

## Approved exceptions

## Deviations
- 2026-10-17 · Task 7 (first real entries, Special B and a souring culture) removed; old Task 8 is
  now Task 7. The intake is proven by the fixture set only (source, fermentable, hop, ale yeast,
  lacto culture), loaded in rolled-back test transactions; Task 6 gains the full pytest run, the
  spot-check test (A9) and `--check` on the empty folder; Task 5's alias test also covers A11. —
  user decision during planning: a working intake for later, no new items yet (brief.md R11).
