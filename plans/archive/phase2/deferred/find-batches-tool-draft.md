# ⏸ DEFERRED — `tool-find-batches`, drafted but NOT to be built

**Status:** ⏸ deferred 2026-08-02 by **D25** · **Do not build this yet.**

This is the click-by-click draft that was going to be Phase 2's second tool. It is
parked here intact rather than deleted, because D25 is a *discussion*, not a
rejection — when the truth-side surface is designed, this is the concrete proposal to
argue with.

**What D25 actually says** (architecture §7.3, §13.2): the tool surface that reads the
user's own brewing records is out of scope until its architecture is decided. The
blocking question is not the tool's shape — it is that **nothing populates
`brew.batches`**. There is no WF3, no UI, no entry path. A query tool over a table
nobody can fill is not a feature, and hand-seeding by SQL is a stopgap, not a design.

Nothing was torn down: `nlq.find_batches` still exists in `db/init/40_nlq.sql`, the
`n8n_agent` grants still hold, and architecture §8.2/§8.5 remain the reference for how
a truth tool should be built.

**Open questions to settle before any of this gets built:**

- Is the seven-filter shape below right, or do two narrow tools (`recent_batches`,
  `batches_by_descriptor`) route better on a 12B model than one wide one?
- Where does batch data come from — WF3 import, a form, a UI?
- Do `get_batch_detail` and `get_inventory` need to land together for the truth side
  to be coherent?
- How much of §3.3's schema is right? It has never held real data.

---

## 2. Workflow B — `tool-find-batches`

**New workflow, name it exactly `tool-find-batches`.** Four nodes.

| # | Node name | Add-Node search term |
|---|---|---|
| 1 | `When Executed by Another Workflow` | *Execute Workflow Trigger* |
| 2 | `Normalise input` | *Code* |
| 3 | `Find batches` | *Postgres* |
| 4 | `Shape for model` | *Code* |

### Node 1 — input schema

*Define using fields below*, **seven** fields:

| Name | Type |
|---|---|
| `style_name` | String |
| `descriptor` | String |
| `brewed_after` | String |
| `brewed_before` | String |
| `min_abv` | Number |
| `min_dry_hop_rate` | Number |
| `max_dry_hop_rate` | Number |

**Seven, not ten.** `nlq.find_batches` also accepts `p_style_code`, `p_max_abv` and
`p_limit`, but §7.3's tool signature doesn't expose the first two and `p_limit` is
pinned at 20 inside the SQL below. Every parameter you expose is another thing a 12B
model can hallucinate; the function keeps the extra arguments for Phase 3 when
`get_batch_detail` and friends arrive.

`brewed_after`/`brewed_before` are **String**, not Date — the model emits
`"2025-01-01"` and the cast happens in SQL. An n8n Date field would try to parse
whatever the model produced before you get a chance to `NULLIF` it.

### Node 2 — `Normalise input` (Code)

```javascript
const i = $input.first().json;

// $fromAI omits a parameter, sends null, or sends '' when it has nothing. All three
// must become '' so the SQL NULLIF turns them into a real SQL NULL. This is the
// single most common tool-parameter bug (§8.3 rule 2).
const s = (v) => {
  const t = String(v ?? '').trim();
  return t.toLowerCase() === 'null' || t.toLowerCase() === 'undefined' ? '' : t;
};
const n = (v) => {
  const x = Number(String(v ?? '').replace(/[^0-9.\-]/g, ''));  // "8 g/L" -> 8
  return Number.isFinite(x) ? String(x) : '';
};
const d = (v) => {
  const t = s(v);
  return /^\d{4}-\d{2}-\d{2}$/.test(t) ? t : '';   // anything else -> no filter
};

return [{ json: {
  style_name:       s(i.style_name),
  descriptor:       s(i.descriptor).toLowerCase(),
  brewed_after:     d(i.brewed_after),
  brewed_before:    d(i.brewed_before),
  min_abv:          n(i.min_abv),
  min_dry_hop_rate: n(i.min_dry_hop_rate),
  max_dry_hop_rate: n(i.max_dry_hop_rate),
}}];
```

`n()` strips units as a belt-and-braces backstop for `"8 g/L"` — the `$fromAI`
description in WF4 is supposed to prevent that (§8.3 rule 1), but a cast error here
would surface to the user as a broken tool rather than a slightly-off filter.

`d()` discards anything that isn't a bare ISO date. A model that emits `"last year"`
gets *no date filter* instead of a Postgres cast error — the answer is then too broad
rather than an error, which is the better failure.

### Node 3 — `Find batches` (Postgres)

- **Credential:** `Postgres — n8n_agent (read-only)`
- **Operation:** Execute Query
- **Settings tab → Always Output Data: ON** (same reason as above — and here the
  empty case is *load-bearing*, it's how the agent learns to say "I have no record")

```sql
SELECT batch_no, recipe_name, style_code, style_name, brewed_on,
       og, fg, abv, dry_hop_rate_g_per_l, descriptors, avg_score
FROM nlq.find_batches(
  p_style_name       => NULLIF($1::text, ''),
  p_descriptor       => NULLIF($2::text, ''),
  p_brewed_after     => NULLIF($3::text, '')::date,
  p_brewed_before    => NULLIF($4::text, '')::date,
  p_min_abv          => NULLIF($5::text, '')::numeric,
  p_min_dry_hop_rate => NULLIF($6::text, '')::numeric,
  p_max_dry_hop_rate => NULLIF($7::text, '')::numeric,
  p_limit            => 20
);
```

Options → **Query Parameters**:

```
={{ [$json.style_name, $json.descriptor, $json.brewed_after, $json.brewed_before, $json.min_abv, $json.min_dry_hop_rate, $json.max_dry_hop_rate] }}
```

Named-argument call syntax (`=>`) is used on purpose: positional would silently shift
every filter by one if you ever add a parameter, and that bug returns *plausible wrong
rows* rather than an error.

Nothing here composes SQL from model output — the model picks the function and the
arguments, never the statement (§8.4 Layer 3).

### Node 4 — `Shape for model` (Code)

Reproduces the §8.5 step-6 output format exactly.

```javascript
const rows = $input.all().map(i => i.json).filter(r => r.batch_no);
const f = $('Normalise input').first().json;

const filters = Object.entries({
  style: f.style_name,
  descriptor: f.descriptor,
  brewed_after: f.brewed_after,
  brewed_before: f.brewed_before,
  min_abv: f.min_abv,
  'min_dry_hop_g/L': f.min_dry_hop_rate,
  'max_dry_hop_g/L': f.max_dry_hop_rate,
}).filter(([, v]) => v !== '' && v != null)
  .map(([k, v]) => `${k}=${v}`)
  .join(', ') || 'no filters';

if (!rows.length) {
  return [{ json: {
    response: `No batches in the user's records match (${filters}). `
            + `The user has no such batch on record. Say so — do not substitute book knowledge.`,
  }}];
}

const body = rows.map((r, n) => {
  const desc = Array.isArray(r.descriptors) && r.descriptors.length
    ? r.descriptors.join(', ') : '—';
  const dh = r.dry_hop_rate_g_per_l != null ? `${r.dry_hop_rate_g_per_l} g/L` : 'none';
  return `[S${n + 1}] ${r.batch_no} "${r.recipe_name ?? 'unnamed'}" | `
       + `${r.style_code ?? '?'} ${r.style_name ?? ''} | ${r.brewed_on} | `
       + `OG ${r.og} FG ${r.fg} | ${r.abv}% | dry hop ${dh} | ${desc} | `
       + `avg ${r.avg_score ?? '—'}/10`;
}).join('\n');

return [{ json: {
  response: `${rows.length} batch(es) matched (${filters}):\n${body}`,
}}];
```

**The empty-result string is a guardrail, not a message.** It restates the law from
the system prompt at the moment the model is most tempted to break it — it has just
asked about the user's beer and got nothing back. Hallucinated inventory is the worst
failure this system can produce (§7.4); saying so twice is cheap.

Echoing the filters back also means a wrong `$fromAI` extraction shows up in the
answer (*"no batches match style=IPA, descriptor=bitter and harsh"*) instead of
vanishing silently.

### Test it standalone

Until `brew.batches` is seeded this returns the empty-case string — which is itself
worth confirming. Pin:

```json
{ "style_name": "IPA", "descriptor": "bitter", "brewed_after": "", "brewed_before": "", "min_abv": "", "min_dry_hop_rate": 8, "max_dry_hop_rate": "" }
```

Expect: `No batches in the user's records match (style=IPA, descriptor=bitter,
min_dry_hop_g/L=8). …`. Re-run this same pin after seeding — it's the §8.5 trace, and
it should return two rows.

---
