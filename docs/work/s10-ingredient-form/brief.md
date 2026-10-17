# S10 · Ingredient form: add an ingredient from an n8n form

Status: draft
Slug: s10-ingredient-form · Branch: s10-ingredient-form
Design: [INGREDIENT-INTAKE.md](../../INGREDIENT-INTAKE.md) §6 (phase 2), §12 Q1
Needs: `s8-ingredient-intake` and `s9-misc-extras` shipped. Planned after m8, so it doesn't hold
up the main line; until then the templates in `shared/ingredients/_templates/` are the form.

## Blocked by
Written 2026-10-17 as a draft, so the shape of the work is known. It can't be approved or planned
until these are cleared:

| # | Blocker | Blocks | Cleared when |
|---|---|---|---|
| B1 | **s8 and s9 are not built.** The form writes the intake files those two define (fields per kind, pick-lists, sources, aliases, misc purposes and categories). Until both ship, the file shape can still change. | approval, implementation | s9 is shipped |
| B2 | **n8n's form capabilities are unverified.** Not checked: a first page that picks the kind and then shows only that kind's page; pick-lists filled from Postgres at form time; writing a text file under `/data/shared/ingredients/` (n8n 2.23.4 is running, measured 2026-10-17; whether file access is restricted to some folders is unknown). The docs check through Context7 failed on 2026-10-17 with an invalid API key. | approval (scope may shrink), planning | a docs check (Context7 working again, or the n8n docs read directly) answers each point; the answers go into this brief |
| B3 | **Loading from n8n is not possible as the stack stands.** The n8n container mounts `shared/` but not the repo's `loaders/` or `.venv` (`docker-compose.yml`, checked 2026-10-17), so it can't run `python -m loaders.extra_ingredients`. | the scope of R7 | Open question 1 is answered |
| B4 | **Open questions 1–2 below.** | approval | you answer them |

## Why
s8 and s9 make adding an ingredient one file and one command, with the templates as the "form".
You asked for an actual form (2026-10-17): fill in fields, pick from lists, add the source, done.
n8n already runs locally and sees `shared/`, so it can host that form without a new component.

## Goal
You open a form in n8n, pick the kind, fill in the fields (pick-lists where the pipeline reads
the value), add or pick the source, and the form writes one intake file that passes the s8/s9
checker. Loading stays the one command, or a step decided in Open question 1.

## Scope
In:
- One n8n workflow with a Form Trigger: a first page for the kind (fermentable, hop, yeast, misc ·
  flavour, misc · process aid), then that kind's page, then an optional "new source" page.
- Pick-lists for kind, role, fermentability, purpose, origin, yeast type, flocculation, form, misc
  category, usages, and the source; descriptor words from `ref.tag` and `ref.tag_synonym`.
- Writing one TOML file per ingredient (and per new source) into `/data/shared/ingredients/`, in
  the templates' format.
- A last page showing the file written and the command to run.
- The workflow exported to `n8n/workflows/` (`python -m evals.workflows`).

Out:
- Editing or deleting an ingredient from the form (edit the file; delete the file).
- A second checker in n8n beyond required fields and pick-lists (the loader's `--check` stays the
  one checker; Open question 2).
- Adding an ingredient from the chat (lane B, Priority 2).
- Any LLM node.

## Requirements
R1. The form is reachable on `localhost:5678` and asks for the kind first; each kind's page shows
    only that kind's fields, required ones marked.
R2. Every field the pipeline reads as a fixed value is a pick-list; the source pick-list and the
    descriptor words come from `ref` at form time.
R3. A new source can be added in the same submission; it is written as its own file in
    `sources/`.
R4. The form writes one file per ingredient at `/data/shared/ingredients/<kind>/<name>.toml` in the
    template's format, and never overwrites an existing file (it says the name is taken).
R5. A file written from valid input passes `python -m loaders.extra_ingredients --check`
    unchanged.
R6. The last page shows the path written and the next step.
R7. Loading after the form works as decided in Open question 1.
R8. The workflow uses no LLM node and no secret in a text field (n8n-skills rules), and is
    exported to `n8n/workflows/`.

## Constraints
- PROJECT.md §4: n8n is the orchestration layer; workflows are built in n8n and exported to the
  repo. n8n-skills are read before any n8n action.
- The pipeline only reads `ref` (DATABASE.md §6); the form writes files, never `ref` rows.
- No LLM in the intake path (decided 2026-10-17).
- `docker-compose.yml` changes (Open question 1 b) follow OPERATIONS.md §3.

## Assumptions
- n8n forms can branch to a page per kind *(unverified, B2)*.
- n8n can fill a form's pick-list from a Postgres query *(unverified, B2)*.
- n8n can write a text file under `/data/shared/` *(unverified, B2; the mount exists, measured)*.

## Acceptance criteria
A1. Opening the form shows the kind choice first, and each kind shows only its fields (R1).
A2. The source pick-list and the descriptor words list match `ref.source` and the known tags (R2).
A3. A submission with a new source writes two files, the ingredient's and the source's (R3, R4).
A4. Submitting a name that already has a file writes nothing and says why (R4).
A5. One hop, one malt and one misc entered by you through the form each pass `--check` without
    an edit and load (R5, R7).
A6. The last page shows the written path and the next step (R6).
A7. The exported workflow has no LLM node and no secret in a text field (R8).

## Open questions
1. **How does the form's file get loaded?** — options: a) you run `python -m
   loaders.extra_ingredients` after submitting, and the last page shows the command; b) give n8n
   a way to run the loader (mount the repo and a Python into the container, or a small local
   service it calls) — recommend a: no change to the stack, and one command after a form is
   still effortless.
2. **How much checking in the form?** — options: a) only required fields and pick-lists, the
   loader's `--check` does the rest; b) the form also runs the loader's checks before writing
   (needs option 1 b) — recommend a: one checker, in one place, with tests.

## Deviations
