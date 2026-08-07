# ⏸ Deferred by D25 — do not build

**Parked 2026-08-02.** Architecture doc: §7.3 (the D25 callout), §13.2 (the open
decision), §11 Phase 2 (the scope change).

Everything in this folder was written for a two-tool Phase 2 and is **not to be
built**. It is kept intact, not deleted, because D25 is a discussion to have — and
when it happens, this is the concrete proposal to argue with rather than a blank page.

| File | What it is |
|---|---|
| [`find-batches-tool-draft.md`](find-batches-tool-draft.md) | full click-by-click for `tool-find-batches` — input schema, normalisation code, the `nlq.find_batches` call, output shaping, and all seven `$fromAI()` parameter descriptions |
| [`seed-batches.template.sql`](seed-batches.template.sql) | template for hand-entering 3–5 real batches, with duplicate guards and verification queries |

## What D25 actually defers

The **tool surface** that reads the user's own brewing records. Not the data model.

Still in place and untouched:

- `brew.*` — the truth schema (`db/init/20_brew.sql`)
- `nlq.find_batches` — the function itself (`db/init/40_nlq.sql`), verified executable by `n8n_agent`
- the `agent_ro` / `n8n_agent` grants (`db/init/50_roles.sql`)
- architecture §8.2 and §8.5 — the reference design and the end-to-end trace

## The questions to settle first

Listed in rough dependency order — the first one blocks the rest:

1. **How does batch data get into the system at all?** There is no entry path today:
   no WF3 import, no UI, no form. Hand-seeding by SQL was the original Phase 2 step
   and it is a stopgap, not a design. A query tool over a table nobody can fill is not
   a feature.
2. **Does §3.3's schema survive contact with real data?** It has never held any.
   `recipe_items` with no unique constraint, `measurements` with nothing reading it,
   and the `descriptors` array as the filter surface are all untested assumptions.
3. **One wide tool or several narrow ones?** `find_batches` takes seven optional
   filters. A 12B model may do better with `recent_batches` and
   `batches_by_descriptor` than with one tool it has to fill in correctly.
4. **Does the truth side need `get_batch_detail` and `get_inventory` to be coherent?**
   "Which of my IPAs were bitter" invites "tell me more about that one", and there is
   nothing to answer it with.

## What Phase 2 does in the meantime

Ships with one tool and tests the *harder* half of architecture rule 2: with no
truth tool at all, every question about the user's own brewing must be **refused**
rather than answered from the books. See [`../04-phase2-exit-gate.md`](../04-phase2-exit-gate.md) §2, group B.
