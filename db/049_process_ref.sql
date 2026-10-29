-- Water rows and CO2 volumes as reference data (docs/work/m7-process, Task 2):
--   ref.water_profile  Water (Palmer and Kaminski) Tables 18a/b and 19a/b (16 rows) plus one web-sourced
--                      row for 23A Berliner Weisse (doc-calc.md §3, §4b)
--   ref.beer_style     water_profile / water_basis (doc-calc.md §4), co2_family / co2_vol / co2_basis
--                      (doc-calc.md §14, How to Brew p. 159)
-- Needs db/010_ref_schema.sql (ref.source, ref.beer_style), db/011_ref_sources.sql (the
-- palmer-kaminski-water source).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/049_process_ref.sql
-- Idempotent: safe to re-run.
-- A style not in doc-calc §4 / §14 keeps null water_profile and co2_vol: no salts and 2.5 volumes
-- (plan decision Q1). The alkalinity and RA columns are references only, never dosing targets.

-- The source of the one web row (URLs in docs/SOURCES.md).
insert into ref.source (slug, title, edition, url, notes)
values ('web-berliner-weisse-water', 'Berliner Weisse water profile (web sources)', 'fetched 2026-10-28',
        'https://brewersfriend.com/homebrew/recipe/print/1109903',
        'Brewer''s Friend recipe, HomebrewersAssociation forum thread, Learning to Homebrew guide; Ca from How to Brew Table 8.1. Unverified against any brewery source (doc-calc.md §4b)')
on conflict (slug) do nothing;

create table if not exists ref.water_profile (
    code       text primary key,
    table_no   text not null check (table_no in ('18', '19', 'web')),
    beer_type  text not null check (beer_type in ('lager', 'ale')),
    strength   text not null,
    colour     text not null,
    bitterness text not null,
    ca         numrange not null,
    alkalinity numrange not null,
    so4        numrange not null,
    cl         numrange not null,
    ra         numrange not null,
    acidify    text not null check (acidify in ('yes', 'maybe', 'no')),
    styles     text not null,
    source_id  bigint not null references ref.source (id),
    page       text not null
);

-- Water Tables 18a/b (lager) and 19a/b (ale), doc-calc.md §3. mg/L; alkalinity and RA as CaCO3.
-- A single number (light lager Ca 50) is a minimum [50,); bracketed outliers are left out.
with src as (select id from ref.source where slug = 'palmer-kaminski-water'),
rows(code, table_no, beer_type, strength, colour, bitterness, ca, alkalinity, so4, cl, ra, acidify, styles, page) as (values
 ('lager-light-pale', '18', 'lager', 'light', 'pale', 'soft', '[50,)', '[0,40]', '[0,50]', '[50,100]', '[-60,0]', 'yes', 'Lite American Lager, Standard American Lager, Munich Helles, (Bohemian Pils)', 'p. 121'),
 ('lager-medium-pale', '18', 'lager', 'medium', 'pale', 'moderate, assertive', '[50,75]', '[0,40]', '[50,150]', '[50,100]', '[-60,0]', 'yes', 'American Premium Lager, German Pils, Classic American Pils, (Dortmunder Export)', 'p. 121'),
 ('lager-medium-amber', '18', 'lager', 'medium', 'amber', 'soft, moderate', '[50,75]', '[40,120]', '[0,100]', '[50,150]', '[0,60]', 'maybe', 'Vienna, Oktoberfest', 'p. 121'),
 ('lager-medium-brown-black', '18', 'lager', 'medium', 'brown/black', 'soft, moderate', '[50,75]', '[80,120]', '[0,50]', '[50,150]', '[40,80]', 'no', 'American Dark, Munich Dunkel, Schwarzbier', 'p. 121'),
 ('lager-strong-amber', '18', 'lager', 'strong', 'amber', 'soft, moderate', '[50,75]', '[40,80]', '[0,100]', '[50,150]', '[0,60]', 'maybe', 'Helles/Maibock, Traditional Bock, Doppelbock', 'p. 121'),
 ('lager-strong-brown-black', '18', 'lager', 'strong', 'brown/black', 'soft, moderate', '[50,100]', '[80,150]', '[0,100]', '[50,100]', '[60,120]', 'no', 'Traditional Bock, Doppelbock, Eisbock, Baltic Porter', 'p. 121'),
 ('ale-light-pale', '19', 'ale', 'light', 'pale', 'moderate', '[50,100]', '[0,80]', '[100,200]', '[50,100]', '[-60,0]', 'yes', 'Blonde Ale, American Wheat, Standard Bitter, Best Bitter', 'p. 122-123'),
 ('ale-light-amber', '19', 'ale', 'light', 'amber', 'soft, moderate', '[50,150]', '[40,120]', '[100,200]', '[50,100]', '[0,60]', 'maybe', 'English Mild, Scottish 60/70/80, Standard Bitter, Best Bitter', 'p. 122-123'),
 ('ale-light-brown-black', '19', 'ale', 'light', 'brown/black', 'moderate', '[50,75]', '[80,150]', '[50,150]', '[50,100]', '[30,90]', 'maybe', 'English Brown, Brown Porter, Dry Stout', 'p. 122-123'),
 ('ale-medium-pale-soft', '19', 'ale', 'medium', 'pale', 'soft, moderate', '[50,100]', '[0,80]', '[0,50]', '[0,100]', '[-30,0]', 'yes', 'Weizen, Witbier, Cream Ale, Blonde Ale, Kölsch', 'p. 122-123'),
 ('ale-medium-pale-assertive', '19', 'ale', 'medium', 'pale', 'moderate, assertive', '[50,150]', '[40,120]', '[100,400]', '[0,100]', '[-30,30]', 'maybe', 'American Pale Ale, American XPA, Saison, American IPA, Double IPA', 'p. 122-123'),
 ('ale-medium-amber', '19', 'ale', 'medium', 'amber', 'moderate, assertive', '[50,150]', '[40,120]', '[100,300]', '[50,100]', '[0,60]', 'no', 'Altbier, California Common, ESB, Irish Red, American Amber, English IPA, Roggenbier, Belgian Pale, Saison', 'p. 122-123'),
 ('ale-medium-brown-black', '19', 'ale', 'medium', 'brown/black', 'moderate, assertive', '[50,75]', '[80,160]', '[50,150]', '[50,150]', '[60,120]', 'no', 'American Brown, English Brown, Brown Porter, Robust Porter, Dry Stout, Sweet Stout, Oatmeal Stout, Foreign Extra Stout, American Stout, Dunkelweizen', 'p. 122-123'),
 ('ale-strong-pale', '19', 'ale', 'strong', 'pale', 'moderate', '[50,100]', '[0,40]', '[50,100]', '[50,100]', '[-30,0]', 'maybe', 'Belgian Blonde, Golden Strong, Tripel', 'p. 122-123'),
 ('ale-strong-amber', '19', 'ale', 'strong', 'amber', 'moderate, assertive', '[50,100]', '[40,120]', '[50,100]', '[50,150]', '[0,60]', 'no', 'Strong Scotch Ale, Bière de Garde, Dubbel, Old Ale, Barleywine', 'p. 122-123'),
 ('ale-strong-brown-black', '19', 'ale', 'strong', 'brown/black', 'moderate-assertive', '[50,75]', '[120,200]', '[50,150]', '[50,150]', '[120,200]', 'no', 'Baltic Porter, Foreign Extra Stout, American Stout, Russian Imperial Stout, Weizenbock, Belgian Dark Strong, Old Ale', 'p. 122-123')
)
insert into ref.water_profile (code, table_no, beer_type, strength, colour, bitterness, ca, alkalinity, so4, cl, ra, acidify, styles, source_id, page)
select r.code, r.table_no, r.beer_type, r.strength, r.colour, r.bitterness, r.ca::numrange, r.alkalinity::numrange,
       r.so4::numrange, r.cl::numrange, r.ra::numrange, r.acidify, r.styles, src.id, r.page
  from rows r, src
on conflict (code) do update set
    table_no = excluded.table_no, beer_type = excluded.beer_type, strength = excluded.strength,
    colour = excluded.colour, bitterness = excluded.bitterness, ca = excluded.ca,
    alkalinity = excluded.alkalinity, so4 = excluded.so4, cl = excluded.cl, ra = excluded.ra,
    acidify = excluded.acidify, styles = excluded.styles, source_id = excluded.source_id, page = excluded.page;

-- The web-sourced row for 23A Berliner Weisse (doc-calc.md §4b): not a Table 18/19 row.
insert into ref.water_profile (code, table_no, beer_type, strength, colour, bitterness, ca, alkalinity, so4, cl, ra, acidify, styles, source_id, page)
select 'web-berliner-weisse', 'web', 'ale', 'light', 'pale', 'soft (3-8 IBU)', '[50,100]', '[0,40]', '[20,60]', '[40,60]', '[-60,0]', 'yes',
       'Berliner Weisse', s.id, 'web'
  from ref.source s where s.slug = 'web-berliner-weisse-water'
on conflict (code) do update set
    table_no = excluded.table_no, beer_type = excluded.beer_type, strength = excluded.strength,
    colour = excluded.colour, bitterness = excluded.bitterness, ca = excluded.ca,
    alkalinity = excluded.alkalinity, so4 = excluded.so4, cl = excluded.cl, ra = excluded.ra,
    acidify = excluded.acidify, styles = excluded.styles, source_id = excluded.source_id, page = excluded.page;

alter table ref.beer_style add column if not exists water_profile text references ref.water_profile (code);
alter table ref.beer_style add column if not exists water_basis text
    check (water_basis in ('listed', 'inferred', 'judgement', 'web'));
alter table ref.beer_style add column if not exists co2_family text;
alter table ref.beer_style add column if not exists co2_vol numrange;
alter table ref.beer_style add column if not exists co2_basis text
    check (co2_basis in ('listed', 'inferred', 'judgement', 'web'));

-- Style -> water row, doc-calc.md §4 (reviewed by the user 2026-10-28). Basis: listed = the book's
-- row names the style, inferred = read from the bands, judgement = a tie or call, web = 23A.
update ref.beer_style b
   set water_profile = m.row_code, water_basis = m.basis
  from (values
    ('21A', 'ale-medium-pale-assertive', 'listed'),
    ('21C', 'ale-medium-pale-assertive', 'judgement'),
    ('session-india-pale-ale', 'ale-medium-pale-assertive', 'judgement'),
    ('18B', 'ale-medium-pale-assertive', 'listed'),
    ('16B', 'ale-medium-brown-black', 'listed'),
    ('16A', 'ale-medium-brown-black', 'listed'),
    ('20B', 'ale-medium-brown-black', 'listed'),
    ('15B', 'ale-light-brown-black', 'judgement'),
    ('20C', 'ale-strong-brown-black', 'listed'),
    ('13C', 'ale-medium-brown-black', 'judgement'),
    ('19C', 'ale-medium-brown-black', 'listed'),
    ('10A', 'ale-medium-pale-soft', 'listed'),
    ('1C', 'ale-medium-pale-soft', 'listed'),
    ('5B', 'ale-medium-pale-soft', 'listed'),
    ('18A', 'ale-medium-pale-soft', 'judgement'),
    ('11B', 'ale-light-amber', 'listed'),
    ('14B', 'ale-light-amber', 'listed'),
    ('15A', 'ale-medium-amber', 'judgement'),
    ('25B', 'ale-medium-amber', 'judgement'),
    ('26B', 'ale-strong-amber', 'listed'),
    ('25A', 'ale-strong-pale', 'listed'),
    ('17C', 'ale-strong-amber', 'listed'),
    ('17D', 'ale-strong-amber', 'listed'),
    ('22C', 'ale-strong-amber', 'listed'),
    ('1B', 'lager-light-pale', 'listed'),
    ('3B', 'lager-light-pale', 'listed'),
    ('5D', 'lager-medium-pale', 'listed'),
    ('6A', 'lager-medium-amber', 'listed'),
    ('mexican-style-amber-lager', 'lager-medium-amber', 'inferred'),
    ('8B', 'lager-medium-brown-black', 'listed'),
    ('23A', 'web-berliner-weisse', 'web')
  ) as m(style_code, row_code, basis)
 where b.code = m.style_code;

-- Style -> CO2 family and volumes, doc-calc.md §14 (How to Brew p. 159). co2_vol is the family's
-- range; step 15 uses its middle.
update ref.beer_style b
   set co2_family = m.family, co2_vol = f.vol::numrange, co2_basis = m.basis
  from (values
    ('21A', 'american-ales', 'inferred'),
    ('21C', 'american-ales', 'inferred'),
    ('session-india-pale-ale', 'american-ales', 'inferred'),
    ('18B', 'american-ales', 'inferred'),
    ('18A', 'american-ales', 'inferred'),
    ('19C', 'american-ales', 'inferred'),
    ('1C', 'american-ales', 'inferred'),
    ('22C', 'american-ales', 'inferred'),
    ('16B', 'porter-stout', 'listed'),
    ('16A', 'porter-stout', 'listed'),
    ('20B', 'porter-stout', 'listed'),
    ('15B', 'porter-stout', 'listed'),
    ('20C', 'porter-stout', 'listed'),
    ('13C', 'porter-stout', 'listed'),
    ('11B', 'british-ales', 'inferred'),
    ('14B', 'british-ales', 'inferred'),
    ('15A', 'british-ales', 'judgement'),
    ('17C', 'british-ales', 'inferred'),
    ('17D', 'british-ales', 'inferred'),
    ('26B', 'belgian-ales', 'inferred'),
    ('25A', 'belgian-ales', 'inferred'),
    ('25B', 'belgian-ales', 'judgement'),
    ('5D', 'european-lagers', 'inferred'),
    ('3B', 'european-lagers', 'inferred'),
    ('6A', 'european-lagers', 'inferred'),
    ('8B', 'european-lagers', 'inferred'),
    ('1B', 'european-lagers', 'judgement'),
    ('mexican-style-amber-lager', 'european-lagers', 'judgement'),
    ('5B', 'european-lagers', 'judgement'),
    ('10A', 'german-wheat', 'listed'),
    ('23A', 'german-wheat', 'judgement')
  ) as m(style_code, family, basis)
  join (values
    ('british-ales', '[1.5,2.0]'),
    ('porter-stout', '[1.7,2.3]'),
    ('belgian-ales', '[1.9,2.4]'),
    ('american-ales', '[2.2,2.7]'),
    ('european-lagers', '[2.2,2.7]'),
    ('belgian-lambic', '[2.4,2.8]'),
    ('american-wheat', '[2.7,3.3]'),
    ('german-wheat', '[3.3,4.5]')
  ) as f(family, vol) on f.family = m.family
 where b.code = m.style_code;
