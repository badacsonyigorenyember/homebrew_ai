# M8 · Step 16 and the chat: the recipe sheet you brew from

Status: draft
Slug: m8-recipe-sheet-chat · Branch: m8-recipe-sheet-chat
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) M8, checkpoint **G7** ·
[RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §3 step 16, §4, §8 P8 · PROJECT.md §4 (D5)
Needs: `m7-process`, `s4-books-kb` and `s7-kb-articles` shipped

## Why
Until now the pipeline's output is rows and JSON. The brewer needs one readable sheet: what to
buy, what to do, why each choice was made, what deviates from the style, and where the reasoning
comes from. The user talks to the assistant through n8n's chat trigger (D5), which also has to
handle the one question the pipeline may ask back (b05: "15B fits 4 % better. Keep 20C?").

## Goal
From the n8n chat, a request becomes a saved recipe and a recipe sheet written by the second LLM
call, from the saved rows only, with reasons, a Deviations box and book citations. You brew one
recipe from it.

## Scope
In:
- Step 16: the LLM writes the sheet from the saved recipe rows, step outputs (becauses) and
  retrieved `kb` chunks; code checks that every number on the sheet equals the saved one.
- The sheet content against the BJCP exam study guide's recipe checklist (RECIPE-ROADMAP §2).
- The chat trigger as the user entry point, sharing the pipeline the harness calls.
- One confirmation turn for a style mismatch, and setting the recipe `status` to `final` when
  you accept it.

Out:
- Recipe editing by chat ("make it less bitter"; Priority 2). Batch log. Brewing Q&A. A UI other
  than n8n's chat.

## Requirements
R1. Step 16 reads only the saved recipe, its deviations, the step becauses and retrieved chunks;
    it never computes or changes a number. A code check fails the step if any number on the
    sheet differs from the saved value.
R2. The sheet has: style and why, targets and results, fermentables (kg, %), hops (g, time,
    use), yeast, water, mash, boil, fermentation, packaging, a Deviations box (who asked for each),
    a "why" per main choice, and absent items with what to do about them.
R3. Each "why" that cites a book points to a `kb` chunk (source, page); a citation that does not
    resolve fails the check.
R4. The chat trigger starts the same pipeline as the harness; the run is logged the same way.
R5. On a style mismatch the chat asks once whether to keep the named style; the answer is
    applied, and the deviation is listed either way.
R6. LLM calls per recipe stay ≤ 2 plus tie-breaks (step 1 and step 16), counted from `run_step`.
R7. The sheet is stored with the recipe (in `app.recipe`, Open question 1).

## Constraints
- PROJECT.md §6.1: numbers come from SQL; the LLM writes prose.
- §6.2: one narrow writing call with a checkable output.
- n8n chat trigger (D5); n8n-skills rules for chat and LLM nodes.

## Assumptions
- n8n's chat trigger can hold a two-turn exchange in one session without an agent node
  *(unverified)*.

## Acceptance criteria
A1. For all validated briefs, the number check passes: every number on the sheet equals the saved
    one (R1).
A2. A sheet for b10 has every R2 section, and lists Special B (or what M5 decided) as absent with
    what to do (R2).
A3. Every citation on 5 sample sheets resolves to a `kb` chunk (R3).
A4. b05 asked through the chat asks about 20C once; answering "keep 20C" gives a 20C recipe with
    the ABV deviation listed (R5).
A5. LLM calls per recipe ≤ 2 plus tie-breaks on all 20 briefs (R6).
A6. You brew one recipe from its sheet and record the outcome in PROJECT.md §8 (G7).

## Open questions
1. Where does the sheet live? — options: a) a `sheet` text column on `app.recipe` (new `.sql`
   file); b) only in `run_step` 16 output — recommend a: the sheet belongs to the recipe.
2. Sheet format? — options: a) Markdown in the chat; b) Markdown plus a printable HTML/PDF —
   recommend a first.

## Deviations
- 2026-10-16 · Needs: `s7-kb-articles` added (dry-hop, souring, water and BJCP introduction
  articles for the sheet's citations, [SOURCES.md](../../SOURCES.md)).
