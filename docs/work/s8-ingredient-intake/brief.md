# S8 · Ingredient intake: add fermentables, hops and yeasts by hand

Status: approved
Slug: s8-ingredient-intake · Branch: s8-ingredient-intake
Design: [INGREDIENT-INTAKE.md](../../INGREDIENT-INTAKE.md) §5–§8, §11 (rows marked s8), §13
Needs: nothing shipped beyond `main`. Build order (INGREDIENT-INTAKE discussion, 2026-10-17):
s5 → **s8** → s9 → m4 → m5. `s9-misc-extras` (misc) and `s10-ingredient-form` (the n8n form) build
on this.

## Why
Every ingredient in `ref` came in through a loader written for one shop (hopline SKU maps), and a
fermentable needs two loaders plus `fermentable_facts.toml`, in a fixed order. A product hopline
does not sell has no way in: Special B (b10) and Lactobacillus (b14) were left out for exactly that
reason (`docs/finished/adjunct-fermentables/report.md`), and M5 needs both. You want to add a new
hop, malt or yeast yourself, with its source, without Claude (decided 2026-10-17, INGREDIENT-INTAKE
§12 Q1).

## Goal
You add a fermentable, hop or yeast by filling one template file in `shared/ingredients/` and
running one command. The command checks the file, loads it into `ref` with its source, and the
tagger tags it, so the ingredient is as usable in steps 3, 10 and 11 as a hopline one. No LLM is
involved anywhere.

## Scope
In:
- The intake folder `shared/ingredients/` (git-tracked; n8n already mounts `shared/` as
  `/data/shared`): a folder per kind (`fermentable/`, `hop/`, `yeast/`), `sources/` for new
  `ref.source` rows, `_templates/` with one commented template per kind and one for a source, and a
  `README.md` with the "add an ingredient" checklist (INGREDIENT-INTAKE §13). One file per
  ingredient: `shared/ingredients/<kind>/<name>.toml`.
- `loaders/extra_ingredients.py`: `--check` (validate only) and load, one plain function per kind,
  sources first. The fields a fermentable needs from `fermentable_facts.toml` (role, description,
  max %, enzyme activity, minimum boil) are in its own intake file.
- Aliases: the words a brewer types for a product, listed in its intake file, loaded into a new
  `ref.ingredient_alias` table that `app.resolve_ingredient` reads. `app.ingredient_synonym()`
  stays for spelling rules (abbaye → abbey).
- `loaders/tags.py` reads an intake row's descriptor words, origin, role and yeast type, so it is
  tagged like a hopline row.
- Souring cultures as yeasts: `ref.yeast` with `type = 'lacto'` or `'pedio'`, family tag `sour`.
- The tests that pin catalogue sizes (INGREDIENT-INTAKE G10) changed so an added row doesn't fail
  them, while they still pin what the hopline loaders load.
- The spot-check pack lists the intake rows.
- First real entries: Special B and one souring culture hopline sells, from data sheets you
  name.
- DATABASE.md (fill order, `ref.source`, the intake loader) and PROJECT.md updated.

Out:
- Misc of any kind, flavour or process aid: `s9-misc-extras`. A misc file is refused with
  "misc arrives in s9".
- The n8n form: `s10-ingredient-form`. This work's templates are the form for now.
- Lane B (an ingredient added from the chat), Priority 2.
- Fruit as a fermentable (INGREDIENT-INTAKE Q3, s9).
- New tags or sensory dimensions beyond the words the first entries need.
- Pipeline steps (resolver class matching, step 9, recipe checks): M5 and later.
- Changing the hopline loaders, apart from the tests in G10.

## Requirements
R1. `shared/ingredients/` holds `fermentable/`, `hop/`, `yeast/`, `sources/`, `_templates/` (one
    commented template per kind and one for a source, each field saying what it is, its unit and
    whether it is required) and `README.md` with the checklist.
R2. `python -m loaders.extra_ingredients --check` writes nothing and refuses the whole set, naming
    file and field, when: a required field for the kind is missing (INGREDIENT-INTAKE §3); a value
    is not one of the allowed values (role, fermentability, purpose, flocculation, type, form); a
    range has low > high; a filled figure has no source reference (page or URL); a `source` slug is
    in neither `ref.source` nor `sources/`; a source has no edition or version; `fermentability`
    other than `normal` has no source; a descriptor word is neither a tag nor a synonym in
    `ref.tag_synonym`; a file's `(kind, producer, name)` matches a row another loader owns; two
    files name the same product; a file is a misc file.
R3. `python -m loaders.extra_ingredients` runs the checks, then writes the sources, then each
    ingredient into `ref.ingredient` and its kind table, with `field_source` for every filled
    field and `raw` holding the file as written plus its path. A fermentable gets its role,
    description and the other facts from its file and needs no `fermentable_facts.toml` entry.
    Running it twice gives the same rows.
R4. Intake rows and loader rows stay apart: re-running `loaders.malts`, `loaders.adjuncts`,
    `loaders.fermentable_facts`, `loaders.hops` and `loaders.yeasts` leaves intake rows unchanged,
    and `--check` reports a clash with a loader row whichever loaded first. A `ref` row the
    intake loader wrote whose file is gone is reported, not deleted.
R5. `loaders.tags` tags an intake row from its file: hop origin from `origins`, family from a
    fermentable's role and a yeast's type, character tags from `descriptors`. An intake row with
    known words gets no `ingredient_review` row.
R6. Each alias in a file finds its product through `app.resolve_ingredient`, and only that
    product; `--check` refuses an alias that finds another product.
R7. The tests listed in INGREDIENT-INTAKE G10 pass with intake rows in `ref` and still pin the
    number of rows each hopline loader writes.
R8. `db/checks/ref_spotcheck.sql` prints the number of intake rows per kind and every intake row
    with its source.
R9. After loading, the command prints: rows loaded per kind, sources added, rows tagged, rows
    flagged for review, rows its file no longer backs, and the `ref.ingredient` count per kind (the
    numbers for PROJECT.md and DATABASE.md).
R10. A souring culture loads into `ref.yeast` with `type` `lacto` or `pedio` and is tagged with the
     `sour` family.
R11. Special B and one souring culture hopline sells are loaded through intake files, each figure
     from a data sheet you name.

## Constraints
- CLAUDE.md: readable over optimal, one plain function per kind, no config-driven machinery
  (PROJECT.md §6.8). Schema changes (the alias table) as a `.sql` file in
  `db/` applied as `postgres` (OPERATIONS.md §4), never through MCP.
- `ref` rules (DATABASE.md §2): every row sourced, every source has an edition, units SI (°C, EBC,
  %), unknown stays `NULL`, nothing guessed, `raw` keeps the original.
- Every loader is idempotent and takes its input path as an argument (default
  `shared/ingredients/`).
- No LLM in the intake path (decided 2026-10-17). No brewing maths changes.
- Intake files are committed (curated data, like `fermentable_facts.toml`); source PDFs stay in
  `shared/rag-files/`, git-ignored.
- Plain branch, no worktree; the guard hook stays as it is.

## Assumptions
- `ref.yeast.type` has no check constraint (values today: ale, brett, kveik, lager, NULL; measured
  2026-10-17), so a new type needs no schema change *(verified)*.
- The tag vocabulary already has the words the first entries need *(unverified)*.
- Data sheets with the needed figures exist for Special B and for the culture you choose
  *(unverified; hopline sells LP-582, LP-652 and Helveticus Pitch, adjunct-fermentables report)*.

## Acceptance criteria
A1. The folder, the four templates and the README exist; a template copied and filled from a test
    fixture passes `--check` (R1).
A2. For each refusal in R2 a test fixture fails `--check` with a message naming its file and
    field, and `ref` row counts are unchanged afterwards (R2).
A3. Loading twice leaves the same counts in `ref.source`, `ref.ingredient` and each kind table; a
    loaded row has a `field_source` key for every filled field (R3).
A4. An intake fermentable without a `fermentable_facts.toml` entry has `role` and `description`,
    and `app.style_level` returns a level for it in mash use (R3).
A5. After the intake loader, re-running the five loaders of R4 leaves every intake row's columns
    and `raw` unchanged; a fixture with a hopline product's name is refused (R4).
A6. An intake hop and yeast loaded from fixtures get their origin, family and character tags and
    no `ingredient_review` row (R5, R10).
A7. Every alias of every loaded file resolves to its product only (R6).
A8. Full `pytest` passes with the first entries loaded, and the G10 tests still assert the hopline
    loaders' row counts (R7).
A9. The spot-check pack prints the intake rows with their sources (R8).
A10. The load prints the R9 summary, and its counts match `select kind, count(*) from
     ref.ingredient group by kind` (R9).
A11. `app.resolve_ingredient('Special B')` and the culture's name each return the new product
     (R11).
A12. You add one ingredient yourself from a template, using only the README checklist, and it
     loads and tags without help (R1, Goal).

## Open questions
None open. Decided by you on 2026-10-17 (INGREDIENT-INTAKE §12):
- Souring cultures (Q4): `ref.yeast` with `type = 'lacto'` / `'pedio'`, family tag `sour`. *Why: no
  new table; the yeast steps already read temperature and attenuation.*
- Aliases (Q6): per product in its intake file, in a new `ref.ingredient_alias` table the resolver
  reads; `app.ingredient_synonym()` stays for spelling rules. *Why: adding an alias needs no SQL edit.*
- One file per ingredient (Q9): `shared/ingredients/<kind>/<name>.toml`. *Why: the later n8n form only
  creates files; diffs and deletes are per ingredient.*
- First real entries: Special B and one souring culture hopline sells. *Why: proves the path on real
  data and fills M5's gaps for b10 and b14.* The data sheets are named by you when the plan is written.

## Deviations
