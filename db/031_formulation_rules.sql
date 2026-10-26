-- Formulation rules (docs/work/s2-formulation-rules): every threshold in one place, and the rule
-- text built from those thresholds with format(), so the sentence and the check cannot disagree.
-- Rules name only ingredient roles, style numbers and ingredient-table fields, never an
-- ingredient or a style. The check itself is db/032_formulation_check.sql and reads the same limits.
-- Needs db/015_app.sql (schema app).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/031_formulation_rules.sql
-- Idempotent: safe to re-run.

-- Every threshold the rules use. midpoint_tolerance is rule 9's rounding tolerance, equal to s1's
-- test tolerances (OG 0.001, FG 0.002, ABV 0.1, IBU 1, SRM 1). pct_sum_tolerance is how far the
-- fermentable percentages may be from 100 before the check raises.
create or replace function app.formulation_limits()
returns jsonb
language sql
immutable
as $$
    -- mash_ref_c, mash_knee_c, mash_slope_pct_per_c: docs/work/s5-mash-attenuation/doc-calc.md
    select '{
        "max_fermentables": 5,
        "max_specialty": 3,
        "max_hop_varieties": 3,
        "crystal_dark_ebc": 60,
        "crystal_very_dark_ebc": 160,
        "dark_total_pct": 15,
        "crystal_total_pct": 25,
        "crystal_dark_pct": 10,
        "crystal_very_dark_pct": 5,
        "adjunct_sugar_pct": 40,
        "late_hop_max_min": 15,
        "mash_min_c": 64,
        "mash_max_c": 69,
        "mash_ref_c": 66.5,
        "mash_knee_c": 68.3,
        "mash_slope_pct_per_c": 4.15,
        "min_boil_min": 60,
        "pct_sum_tolerance": 0.1,
        "midpoint_tolerance": {"og": 0.001, "fg": 0.002, "abv": 0.1, "ibu": 1, "srm": 1}
    }'::jsonb
$$;

-- One row per rule: its number (or "definitions" / "pending"), whether the check enforces it, and
-- the sentence. Rule 7 is enforced by the colour solver (step 10), not by the check.
create or replace function app.formulation_rules()
returns table (rule text, checked boolean, sentence text)
language sql
stable
as $$
    with l as (select app.formulation_limits() as j),
    t as (select j, j -> 'midpoint_tolerance' as tol from l)
    select v.rule, v.checked, v.sentence
    from t, lateral (values
        ('definitions', true, 'A share is a percentage of the total fermentable mass, sugars included. '
            || 'A fermentable''s colour is the midpoint of its ebc range, or its one bound when the range '
            || 'is open. Role, max_pct, min_boil_min, fermentability, attenuation_pct, temp_c and '
            || 'alcohol_tolerance_pct are ingredient-table fields.'),
        ('1', true, format('A recipe has at most %s fermentables, and at most %s of them have the role '
            || 'kilned, crystal or roast; fermentables with the role adjunct or sugar do not count '
            || 'toward the %s.',
            j->>'max_fermentables', j->>'max_specialty', j->>'max_specialty')),
        ('2', true, format('A recipe uses at most %s hop varieties.', j->>'max_hop_varieties')),
        ('3', true, format('Fermentables with the role crystal and a colour above %s EBC, plus '
            || 'fermentables with the role roast, are at most %s %% of the grist together.',
            j->>'crystal_dark_ebc', j->>'dark_total_pct')),
        ('4', true, format('Fermentables with the role crystal are at most %s %% of the grist together; '
            || 'those with a colour above %s EBC at most %s %%; those with a colour above %s EBC at '
            || 'most %s %%. Those at or below %s EBC are limited only by rule 6.',
            j->>'crystal_total_pct', j->>'crystal_dark_ebc', j->>'crystal_dark_pct',
            j->>'crystal_very_dark_ebc', j->>'crystal_very_dark_pct', j->>'crystal_dark_ebc')),
        ('5', true, format('Fermentables with the role adjunct or sugar are at most %s %% of the grist '
            || 'together.', j->>'adjunct_sugar_pct')),
        ('6', true, 'Each fermentable is at most its max_pct share of the grist.'),
        ('7', false, 'The colour adjustment changes the share of the darkest fermentable that is not a '
            || 'crystal and, when that share reaches a limit, of the next-darkest one; base malts take up '
            || 'the difference; the share of a crystal never changes. Enforced by the colour solver in '
            || 'step 10, not by this check.'),
        ('8', true, format('A recipe has exactly one bittering addition: a boil addition whose time '
            || 'equals the boil time. Every other hop addition is a boil addition of at most %s min, '
            || 'a whirlpool addition or a dry hop.', j->>'late_hop_max_min')),
        ('9', true, format('When style guidance is on, a target OG, FG, IBU or SRM that the user did not '
            || 'state is the style''s midpoint, moved by the request''s hints to 87.5 %% (up) or 12.5 %% '
            || '(down) of the style''s range, with the OG moved inside its range as far as needed for the '
            || 'ABV from the OG and FG to reach the style''s ABV range; within %s for OG, %s for FG, %s IBU '
            || 'and %s SRM. OG and FG count as stated when the user stated the ABV. The ABV target is '
            || 'app.abv of the OG and FG targets, within %s %%. A target is outside the style''s range '
            || 'only when the user stated it or style guidance is off.',
            tol->>'og', tol->>'fg', tol->>'ibu', tol->>'srm', tol->>'abv')),
        ('10', true, format('The mash temperature is between %s and %s °C, and the FG predicted from the '
            || 'yeast''s attenuation_pct, each fermentable''s fermentability and the mash temperature '
            || 'is inside the target FG range: the style''s FG range, or the target FG ± %s when the '
            || 'user stated the FG or the ABV. Up to %s °C the attenuation is the middle of the '
            || 'yeast''s attenuation_pct range, which applies at %s °C; above %s °C it is %s points '
            || 'lower per °C, never outside that range (Troester 2009, limit of attenuation against '
            || 'mash temperature).',
            j->>'mash_min_c', j->>'mash_max_c', tol->>'fg', j->>'mash_knee_c', j->>'mash_ref_c',
            j->>'mash_knee_c', j->>'mash_slope_pct_per_c')),
        ('11', true, 'The planned ABV is at most the yeast''s alcohol_tolerance_pct, and the '
            || 'fermentation temperature is inside the yeast''s temp_c range.'),
        ('12', true, 'Every fermentable, hop and yeast in the recipe has a purpose that is not empty.'),
        ('13', true, format('The boil time is at least the largest min_boil_min of the recipe''s '
            || 'fermentables, and at least %s min.', j->>'min_boil_min')),
        ('pending', false, 'A recipe uses only processes the brewer profile allows. Pending: needs the '
            || 'brewer profile (step 0); not checked.')
    ) as v (rule, checked, sentence)
$$;
