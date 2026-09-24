// RecipeRun envelope: a runnable walk-through with dummy values.
// See RECIPE-WORKFLOW-BRAINSTORM.md §6. Run it with:  node docs/recipe-run.example.js
//
// Every step below is a stub that returns hard-coded dummy data. The part that is
// real is the SHAPE: steps take plain arguments and return one slot, and only
// runWorkflow() reads from or writes to `run`.

// ---------------------------------------------------------------------------
// 1. The envelope, empty. `null` = "this step has not run yet".
// ---------------------------------------------------------------------------
function newRecipeRun(question) {
  return {
    id: "run_0001",
    schema_version: 1,
    question,        // S0
    brief: null,     // S1 (S2 fills in the ref_ids)
    evidence: null,  // S3
    profile: null,   // S4
    pool: null,      // S5
    attempts: [],    // S6-S8, one entry per round
    recipe: null,    // S9
    trace: [],       // one entry per step
  };
}

// ---------------------------------------------------------------------------
// 2. The steps. Each one gets only what it needs and returns only its slot.
// ---------------------------------------------------------------------------

// S1 · LLM. Sees the question only. Real version: prompt + JSON schema, then validate.
async function understand(question) {
  return {
    style: { value: "American IPA", ref_id: null, source: "user" },
    must_include: [{ text: "Citra", ref_id: null, kind: "item" }],
    avoid: [{ text: "crystal malt", ref_id: null, kind: "category" }],
    concepts: ["tropical", "dank"],
    sensory: { aroma: ["tropical", "dank"], flavour: [], appearance: [], mouthfeel: [] },
    targets: { abv: { value: 6.5, source: "user" }, ibu: null, srm: null },
    batch: { volume_l: 20, efficiency: 0.72, source: "default" },
    unresolved: [],
    open_questions: [],
  };
}

// S2 · SQL + LLM. Returns a COPY of the brief with ids filled in (never edits in place).
async function resolveRefs(brief) {
  const b = structuredClone(brief);
  b.style.ref_id = 21;              // refs.styles: 21A American IPA
  b.must_include[0].ref_id = 7;     // refs.hops: Citra
  b.avoid[0].ref_id = 3;            // refs categories: "crystal malts"
  return b;
}

// S3 · SEARCH. Sees concepts, sensory words and unresolved names, not the whole brief.
async function searchKnowledge({ concepts, sensory, unresolved }) {
  return {
    findings: [
      { id: "ev1", claim: "Citra with Mosaic in the dry hop reads as tropical fruit with a dank edge",
        suggests_ref_id: 9, source: "library: hop book, p.112", confidence: 0.8 },
      { id: "ev2", claim: "Columbus adds resinous, dank character, also as a bittering hop",
        suggests_ref_id: 11, source: "library: hop book, p.87", confidence: 0.7 },
    ],
  };
}

// S4 · SQL. Sees the style id only.
async function loadStyleProfile(styleRefId) {
  return {
    style: { ref_id: styleRefId, code: "21A", name: "American IPA",
             description: "Hop-forward, bitter, moderately strong pale ale with a dry finish." },
    targets: {
      og:  { min: 1.056, max: 1.070, p10: 1.058, p50: 1.063, p90: 1.068 },
      fg:  { min: 1.008, max: 1.014, p10: 1.009, p50: 1.011, p90: 1.013 },
      ibu: { min: 40,    max: 70,    p10: 45,    p50: 58,    p90: 68 },
      srm: { min: 6,     max: 14,    p10: 6,     p50: 8,     p90: 11 },
      abv: { min: 5.5,   max: 7.5,   p10: 5.9,   p50: 6.6,   p90: 7.2 },
    },
    priors: {
      fermentables: [
        { ref_id: 12, name: "Pale 2-row",  role: "base",      pct: { p10: 70, p50: 85, p90: 95 }, n: 210 },
        { ref_id: 14, name: "Munich",      role: "specialty", pct: { p10: 5,  p50: 10, p90: 20 }, n: 90 },
        { ref_id: 13, name: "Crystal 40",  role: "specialty", pct: { p10: 3,  p50: 5,  p90: 10 }, n: 150 },
        { ref_id: 15, name: "Flaked oats", role: "adjunct",   pct: { p10: 3,  p50: 8,  p90: 15 }, n: 40 },
      ],
      hops: [
        { ref_id: 11, name: "Columbus",   use: "bittering", n: 80 },
        { ref_id: 10, name: "Centennial", use: "whirlpool", g_per_l: { p10: 1, p50: 3, p90: 5 },  n: 110 },
        { ref_id: 7,  name: "Citra",      use: "dry_hop",   g_per_l: { p10: 3, p50: 6, p90: 10 }, n: 140 },
        { ref_id: 9,  name: "Mosaic",     use: "dry_hop",   g_per_l: { p10: 2, p50: 4, p90: 8 },  n: 95 },
      ],
      yeast: [{ ref_id: 44, name: "US-05", share: 0.45, n: 210 }],
      process: { mash_temp_c: { p10: 65, p50: 66, p90: 68 } },
    },
    fallback: null,
  };
}

// S5 · CODE. Trend top-N + evidence hits + must_include, minus avoid.
function buildPool({ evidence, priors, mustInclude, avoid }) {
  return {
    fermentables: [
      { ref_id: 12, reasons: ["trend"], stats: { p50: 85, n: 210 } },
      { ref_id: 14, reasons: ["trend"], stats: { p50: 10, n: 90 } },
      { ref_id: 15, reasons: ["trend"], stats: { p50: 8,  n: 40 } },
    ],
    hops: [
      { ref_id: 7,  reasons: ["user", "trend"],     stats: { p50: 6, n: 140 } },
      { ref_id: 9,  reasons: ["trend", "evidence"], stats: { p50: 4, n: 95 } },
      { ref_id: 10, reasons: ["trend"],             stats: { p50: 3, n: 110 } },
      { ref_id: 11, reasons: ["trend", "evidence"], stats: { n: 80 } },
    ],
    yeast: [{ ref_id: 44, reasons: ["trend"], stats: { share: 0.45, n: 210 } }],
    misc: [],
    excluded: [{ ref_id: 13, why: "avoid: category 3 (crystal malts)" }],
  };
}

// S6 · LLM. Proportions only, no grams. `feedback` is null on the first round.
async function select({ brief, pool, profile, evidence, feedback }) {
  const grist = feedback
    ? [{ ref_id: 12, role: "base", pct: 72 }, { ref_id: 14, role: "specialty", pct: 20 },
       { ref_id: 15, role: "adjunct", pct: 8 }]              // round 2: Munich added for colour
    : [{ ref_id: 12, role: "base", pct: 92 }, { ref_id: 15, role: "adjunct", pct: 8 }];
  return {
    fermentables: grist,
    hops: [
      { ref_id: 11, use: "bittering" },                        // grams solved by S7
      { ref_id: 10, use: "whirlpool", g_per_l: 3 },
      { ref_id: 7,  use: "dry_hop",   g_per_l: 6 },
      { ref_id: 9,  use: "dry_hop",   g_per_l: 4 },
    ],
    yeast: { ref_id: 44 },
    misc: [],
    mash_temp_c: 66,
    targets: { og: 1.062, ibu: 50 },
    rationale: [
      { ref_id: 7,  why: "user asked for Citra; tropical aroma", evidence: ["ev1", "trend:hop:7"] },
      { ref_id: 9,  why: "pairs with Citra for the dank side",   evidence: ["ev1"] },
      { ref_id: 11, why: "clean bittering with a resinous edge", evidence: ["ev2"] },
    ],
  };
}

// S7 · CODE. Dummy numbers; the real one solves base malt kg (OG) and bittering g (IBU).
function calculate(selection, targets, batch) {
  const hasMunich = selection.fermentables.some(f => f.ref_id === 14);
  const bitteringG = selection.adjusted?.bittering_g ?? 20;
  return {
    amounts: [
      ...selection.fermentables.map(f => ({ ref_id: f.ref_id, kg: +(5.6 * f.pct / 100).toFixed(2) })),
      { ref_id: 11, g: bitteringG, time_min: 60 },
      { ref_id: 10, g: 60, time_min: 0, note: "whirlpool 80 °C" },
      { ref_id: 7,  g: 120, day: 3 },
      { ref_id: 9,  g: 80,  day: 3 },
    ],
    specs: { og: 1.062, fg: 1.012, abv: 6.6, ibu: bitteringG === 20 ? 52.8 : 49.6,
             srm: hasMunich ? 6.3 : 4.0 },
    estimates: ["fg"],
  };
}

// S8 · CODE.
function validate(calc, profile, brief, selection) {
  if (calc.specs.srm < profile.targets.srm.min) {
    return { outcome: "structural", reasons: [
      { check: "srm_in_style", value: calc.specs.srm, range: [6, 14], severity: "fail",
        hint: "grist too pale; crystal is excluded, so colour must come from another malt" }] };
  }
  if (Math.abs(calc.specs.ibu - selection.targets.ibu) > 1) {
    return { outcome: "fixable", reasons: [
      { check: "ibu_on_target", value: calc.specs.ibu, target: selection.targets.ibu, severity: "fix" }] };
  }
  return { outcome: "pass", reasons: [] };
}

// Fixable → nudge the balancing variable, keep every choice.
function autoAdjust(selection, validation) {
  return { ...selection, adjusted: { bittering_g: 18 } };
}

// S9 · LLM. Gets the chosen attempt and the cited evidence only.
async function writeRecipe(attemptIndex, attempt, evidence) {
  return {
    attempt: attemptIndex,
    text: "Tropical Dank IPA · 20 L · OG 1.062 · FG ≈1.012 · 6.6% ABV · 50 IBU · 6.3 SRM …",
    citations: ["ev1", "ev2"],
    warnings: ["FG is an estimate.",
               "Colour sits at the pale edge of the style because crystal malt was excluded."],
  };
}

// ---------------------------------------------------------------------------
// 3. The orchestrator: the only code that touches `run`. Reads like the diagram.
// ---------------------------------------------------------------------------
const MAX_RESELECT = 3;
const MAX_ADJUST = 5;

async function runWorkflow(question) {
  const run = newRecipeRun(question);                                        // S0
  show(run, "S0");

  run.brief = await understand(run.question);                                // S1
  show(run, "S1");
  run.brief = await resolveRefs(run.brief);                                  // S2
  show(run, "S2");
  if (run.brief.style.ref_id === null) return run;                           // G1 (E1 later)

  [run.evidence, run.profile] = await Promise.all([                          // S3 ‖ S4
    searchKnowledge({ concepts: run.brief.concepts, sensory: run.brief.sensory,
                      unresolved: run.brief.unresolved }),
    loadStyleProfile(run.brief.style.ref_id),
  ]);
  show(run, "S3 ‖ S4");

  run.pool = buildPool({ evidence: run.evidence, priors: run.profile.priors,  // S5
                         mustInclude: run.brief.must_include, avoid: run.brief.avoid });
  show(run, "S5");

  let feedback = null, kind = "initial", validation;
  for (let r = 0; r < MAX_RESELECT; r++) {
    let selection = await select({ brief: run.brief, pool: run.pool,         // S6
                                   profile: run.profile, evidence: run.evidence, feedback });
    for (let a = 0; a < MAX_ADJUST; a++) {
      const calc = calculate(selection, run.profile.targets, run.brief.batch); // S7
      validation = validate(calc, run.profile, run.brief, selection);         // S8
      run.attempts.push({ kind, selection, calc, validation });
      show(run, `S6–S8 attempt ${run.attempts.length - 1} (${kind}) → ${validation.outcome}`);
      if (validation.outcome !== "fixable") break;
      selection = autoAdjust(selection, validation);
      kind = "auto_adjust";
    }
    if (validation.outcome === "pass") break;
    feedback = validation.reasons;
    kind = "reselect";
  }

  const chosen = run.attempts.length - 1;              // real one: best attempt if none passed
  const cited = { findings: run.evidence.findings.filter(f =>
    run.attempts[chosen].selection.rationale.some(x => x.evidence.includes(f.id))) };
  run.recipe = await writeRecipe(chosen, run.attempts[chosen], cited);        // S9
  show(run, "S9");

  // S10: save(run) → one JSON column holds the whole run.
  return run;
}

// Print which slots are filled after each step.
function show(run, label) {
  const slots = ["brief", "evidence", "profile", "pool", "attempts", "recipe"];
  const state = slots.map(s => {
    const v = run[s];
    const filled = Array.isArray(v) ? v.length > 0 : v !== null;
    return filled ? `■ ${s}${Array.isArray(v) ? `[${v.length}]` : ""}` : `□ ${s}`;
  }).join("  ");
  console.log(`${label.padEnd(44)} ${state}`);
  run.trace.push({ step: label.split(" ")[0], at: new Date().toISOString() });
}

runWorkflow("A tropical, dank American IPA with Citra, around 6.5%, no crystal malt.")
  .then(run => {
    console.log("\nFinal RecipeRun:\n");
    console.log(JSON.stringify(run, null, 2));
  });
