-- ref.source rows: one per data source the P1a loaders read. Needs 010_ref_schema.sql.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/011_ref_sources.sql
-- Idempotent: an existing slug is left as it is, except for the corrections at the end.
-- A NULL licence means it has not been checked yet.

insert into ref.source (slug, title, edition, publisher, licence, url, notes) values
    ('bjcp-2021',
     'BJCP Beer Style Guidelines', '2021',
     'Beer Judge Certification Program', null,
     'https://www.bjcp.org/style/2021/beer/',
     'Loaded from styles.json'),
    ('ba-2026',
     'Brewers Association Beer Style Guidelines', '2026',
     'Brewers Association', null,
     'https://www.brewersassociation.org/edu/brewers-association-beer-style-guidelines/',
     'Loaded from ba_styles.json'),
    ('hopline-malts',
     'Hopline malt product pages', 'website, fetched 2026-10-09',
     'Hopline', null,
     'https://www.hopline.hu/alapanyagok/malatak/osszes-malata',
     null),
    ('weyermann-2026',
     'Weyermann products, brewery (EN)', 'Crop 2026',
     'Weyermann Specialty Malts', null,
     'https://www.weyermannmalt.com/',
     null),
    ('viking-malt-2023',
     'Viking Malt Standard Product Portfolio', '2023',
     'Viking Malt', null,
     'https://www.vikingmalt.com/',
     null),
    ('simpsons-malt-2025',
     'Simpsons Malt product range (NextHop)', 'November 2025',
     'Simpsons Malt', null,
     'https://www.simpsonsmalt.co.uk/',
     null),
    ('hops-json',
     'Hop data (hops.json)', 'hops.json copy of 2026-10-08',
     null, 'unknown', null,
     'provenance unverified'),
    ('hopslist',
     'Hop data (hops.hopslist.json)', 'hops.hopslist.json copy of 2026-10-08',
     null, 'unknown', null,
     'provenance unverified'),
    ('brewtarget-default-data',
     'Brewtarget default ingredient data', 'DefaultContent003 and DefaultContent004',
     'Brewtarget project', 'GPL-3.0',
     'https://github.com/Brewtarget/brewtarget',
     'BeerJSON files DefaultContent003-Ingredients-Hops-Yeasts.json and DefaultContent004-MoreYeasts.json'),
    ('water-chemistry',
     'Standard atomic masses', 'IUPAC standard atomic weights 2021',
     'IUPAC', null, null,
     'Molar masses and ion contributions of brewing water salts, computed from standard atomic masses')
on conflict (slug) do nothing;

-- Corrections to rows inserted by an earlier version of this file.
update ref.source set edition = 'IUPAC standard atomic weights 2021'
 where slug = 'water-chemistry'
   and edition is distinct from 'IUPAC standard atomic weights 2021';

-- The two malts.json sources were replaced by the malt sources above; remove them while
-- nothing references them.
delete from ref.source s
 where s.slug in ('weyermann-specs', 'viking-malt-2020')
   and not exists (select 1 from ref.ingredient i where i.source_id = s.id);
