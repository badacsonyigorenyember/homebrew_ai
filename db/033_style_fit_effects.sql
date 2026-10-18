-- Style fit, part 1 (docs/work/s3-style-fit, Task 7): what each use of an ingredient drives,
-- the cut points that turn a dose into a 0-7 level, and the helpers that compute a dose.
-- Every cut point carries its basis: a book and page, or "set by the user, <date>"
-- (docs/work/s3-style-fit/cut-points.md has the arithmetic). No corpus is read (A7).
-- Needs db/032_formulation_check.sql (app.ebc_mid).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/033_style_fit_effects.sql
-- Idempotent: safe to re-run.

-- STYLE-FIT.md §3. For a misc, applies_to is its category and the dimension is the one
-- sensation it adds (docs/work/s9-misc-extras); a misc never carries its tags into the match.
-- applies_to is a role, a family or a tag name, as kind says: a hop (any),
-- a fermentable role, a yeast (any, or a family), or any ingredient with a tag. A null usage
-- means any usage; min_minutes / max_minutes bound a hop's boil time. carries_character says
-- whether the use shows the ingredient's character tags (hop bitterness does not).
create or replace function app.usage_effects()
returns table (kind text, applies_to text, usage text, min_minutes int, max_minutes int,
               dimension text, carries_character boolean)
language sql
immutable
as $$
    select * from (values
        ('hop',         'hop',     'boil',      30,   null::int, 'bitterness',  false),
        ('hop',         'hop',     'boil',      5,    29,        'bitterness',  false),
        ('hop',         'hop',     'boil',      5,    29,        'hop_flavour', true),
        ('hop',         'hop',     'boil',      0,    4,         'hop_flavour', true),
        ('hop',         'hop',     'boil',      0,    4,         'hop_aroma',   true),
        ('hop',         'hop',     'whirlpool', null, null,      'hop_flavour', true),
        ('hop',         'hop',     'whirlpool', null, null,      'hop_aroma',   true),
        ('hop',         'hop',     'dry_hop',   null, null,      'hop_aroma',   true),
        ('fermentable', 'roast',   'mash',      null, null,      'roast',       true),
        ('fermentable', 'roast',   'mash',      null, null,      'colour',      false),
        ('fermentable', 'roast',   'boil',      null, null,      'roast',       true),
        ('fermentable', 'roast',   'boil',      null, null,      'colour',      false),
        ('fermentable', 'crystal', 'mash',      null, null,      'caramel',     true),
        ('fermentable', 'crystal', 'mash',      null, null,      'sweetness',   false),
        ('fermentable', 'crystal', 'mash',      null, null,      'colour',      false),
        ('fermentable', 'crystal', 'mash',      null, null,      'body',        false),
        ('fermentable', 'crystal', 'boil',      null, null,      'caramel',     true),
        ('fermentable', 'crystal', 'boil',      null, null,      'sweetness',   false),
        ('fermentable', 'crystal', 'boil',      null, null,      'colour',      false),
        ('fermentable', 'crystal', 'boil',      null, null,      'body',        false),
        ('yeast',       'yeast',   'ferment',   null, null,      'esters',      true),
        ('yeast',       'yeast',   'ferment',   null, null,      'phenols',     true),
        ('yeast',       'brett',   'ferment',   null, null,      'brett_funk',  false),
        ('yeast',       'sour',    'ferment',   null, null,      'sourness',    false),
        ('any',         'smoke',   null,        null, null,      'smoke',       false),
        ('misc',        'spice',   null,        null, null,      'spice',       false),
        ('misc',        'herb',    null,        null, null,      'spice',       false),
        ('misc',        'coffee',  null,        null, null,      'spice',       false),
        ('misc',        'cacao',   null,        null, null,      'spice',       false),
        ('misc',        'vanilla', null,        null, null,      'spice',       false),
        ('misc',        'fruit',   null,        null, null,      'fruit',       false),
        ('misc',        'wood',    null,        null, null,      'wood',        false),
        ('misc',        'smoke',   null,        null, null,      'smoke',       false)
    ) as t(kind, applies_to, usage, min_minutes, max_minutes, dimension, carries_character)
$$;

-- The cut points of cut-points.md, each with its basis. A scale is an ascending list: the level
-- is how many of its values the dose reaches. The esters / phenols entries are base levels.
create or replace function app.style_fit_cut_points()
returns jsonb
language sql
immutable
as $$
    select '{
        "oil_ml_per_l": [
            {"id": "O1", "level": 1, "value": 0.003, "basis": "HTB p. 71 (derived)"},
            {"id": "O2", "level": 2, "value": 0.008, "basis": "HTB p. 71 (derived)"},
            {"id": "O3", "level": 3, "value": 0.012, "basis": "HTB p. 72 (derived)"},
            {"id": "O4", "level": 4, "value": 0.025, "basis": "HTB pp. 71-72 (derived)"},
            {"id": "O5", "level": 5, "value": 0.05,  "basis": "HTB p. 71, pp. 399-400 (derived)"},
            {"id": "O6", "level": 6, "value": 0.08,  "basis": "HTB p. 72, pp. 401-402 (derived)"},
            {"id": "O7", "level": 7, "value": 0.15,  "basis": "HTB p. 72 range; value set by the user, 2026-10-15"}
        ],
        "roast_index": [
            {"id": "R1", "level": 1, "value": 700,   "basis": "HTB p. 231 (derived)"},
            {"id": "R2", "level": 2, "value": 1500,  "basis": "HTB p. 231 (derived)"},
            {"id": "R3", "level": 3, "value": 4000,  "basis": "HTB p. 230 (derived)"},
            {"id": "R4", "level": 4, "value": 5500,  "basis": "HTB pp. 230, 404 (derived)"},
            {"id": "R5", "level": 5, "value": 12000, "basis": "HTB pp. 231, 410-413 (derived)"},
            {"id": "R6", "level": 6, "value": 16000, "basis": "set by the user, 2026-10-15"},
            {"id": "R7", "level": 7, "value": 22000, "basis": "set by the user, 2026-10-15"}
        ],
        "esters": {
            "lager_family":       {"id": "E1", "level": 0, "basis": "OBC p. 6 (qualitative); value set by the user, 2026-10-15"},
            "no_ester_character": {"id": "E2", "level": 1, "basis": "set by the user, 2026-10-15"},
            "ester_character":    {"id": "E3", "level": 3, "basis": "set by the user, 2026-10-15"},
            "warm_step":          {"id": "E4", "step": 1, "above_c": 21, "basis": "HTB p. 443 (21 C); step size set by the user, 2026-10-15"}
        },
        "phenols": {
            "phenolic_character": {"id": "P1", "level": 4, "basis": "set by the user, 2026-10-15"},
            "phenolic_tags":      {"id": "P2", "tags": ["clove", "pepper", "phenolic", "spicy"], "basis": "set by the user, 2026-10-15"},
            "warm_step":          {"id": "P3", "step": 1, "above_c": 21, "basis": "HTB p. 443; step set by the user, 2026-10-15"}
        },
        "misc_dose": {
            "subtle_below":     {"id": "M1", "ratio": 0.5, "basis": "set by the user, 2026-10-18 (docs/work/s9-misc-extras/doc-calc.md D): below this share of the lower sourced dose of the entry"},
            "aggressive_above": {"id": "M2", "ratio": 2.0, "basis": "set by the user, 2026-10-18 (doc-calc.md D): above this multiple of the upper sourced dose of the entry; HTB p. 225 top coffee dose is 1.98 x the Janish cold brew dose"},
            "levels":           {"id": "M3", "subtle": 2, "noticeable": 4, "aggressive": 6, "basis": "set by the user, 2026-10-18 (doc-calc.md D): low, medium, high on the 0-7 scale"}
        },
        "min_tolerance": {"levels": 1, "basis": "set by the user, 2026-10-15"},
        "character_match": {"typical": 0.8, "allowed": 0.3, "basis": "decided, STYLE-FIT.md §5"}
    }'::jsonb
$$;

-- How many of a scale's cut points the value reaches (0-7). Null value gives null.
create or replace function app.intensity_level(scale text, value numeric)
returns smallint
language plpgsql
immutable
as $$
declare
    points jsonb := app.style_fit_cut_points() -> scale;
begin
    if jsonb_typeof(points) is distinct from 'array' then
        raise exception 'unknown intensity scale: %', scale;
    end if;
    if value is null then
        return null;
    end if;
    return (select count(*) from jsonb_array_elements(points) as p(item)
            where intensity_level.value >= (p.item ->> 'value')::numeric)::smallint;
end
$$;

-- mL of hop oil per litre of beer from one late addition (g/L of a hop whose total oil is a
-- range in mL/100 g).
create or replace function app.oil_dose(g_per_l numeric, total_oil numrange)
returns numeric
language sql
immutable
as $$
    select g_per_l * app.ebc_mid(total_oil) / 100
$$;

-- One roast malt's share of the roast index: % of grist x the midpoint of its EBC range.
create or replace function app.roast_index(pct numeric, ebc numrange)
returns numeric
language sql
immutable
as $$
    select pct * app.ebc_mid(ebc)
$$;
