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
    ('hopline-hops',
     'Hopline hop product pages', 'website, fetched 2026-10-10',
     'Hopline', null,
     'https://www.hopline.hu/alapanyagok/komlok/osszes-komlo',
     null),
    ('beermaverick',
     'Beer Maverick', 'website, fetched 2026-10-11',
     null, null,
     'https://beermaverick.com',
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
    ('user-supplied',
     'Figures supplied by the user', null,
     null, null, null,
     'Hand-entered figures where no source states one; the user''s wording is kept in raw'),
    ('hopline-yeasts',
     'Hopline yeast product pages', 'website, fetched 2026-10-11',
     'Hopline', null,
     'https://www.hopline.hu/alapanyagok/elesztok/szaraz-eleszto',
     'Dry yeast page (this URL) and liquid yeast page (https://www.hopline.hu/alapanyagok/elesztok/folyekony-eleszto)'),
    ('yeastflow-catalogue',
     'YeastFlow strain catalogue', 'website, fetched 2026-10-11',
     'YeastFlow', null,
     'https://yeastflow.com/our-strains/',
     'Yeast attenuation; each strain page under this URL'),
    ('lallemand-catalogue',
     'Lallemand brewing yeast catalogue', 'website, fetched 2026-10-11',
     'Lallemand Brewing', null,
     'https://www.lallemandbrewing.com/en/continental-europe/products/brewing-yeast?page=1',
     'Yeast attenuation; the product pages of the catalogue'),
    ('fermentis-datasheets',
     'Fermentis technical data sheets', 'website, fetched 2026-10-11',
     'Fermentis', null,
     'https://fermentis.com/',
     'Yeast attenuation; data sheets linked from hopline, else fermentis.com product pages'),
    ('mangrovejacks-datasheets',
     'Mangrove Jack''s yeast data sheets', 'website, fetched 2026-10-11',
     'Mangrove Jack''s', null,
     'https://mangrovejacks.com/',
     'Yeast attenuation; product pages and the Yeast Range booklet linked from hopline'),
    ('brewfather',
     'Brewfather yeast database', 'website, figures given by the user 2026-10-11',
     'Brewfather', null,
     'https://brewfather.app/',
     'Yeast attenuation for Gozdawa and Brewline strains, as the user read them'),
    ('water-chemistry',
     'Standard atomic masses', 'IUPAC standard atomic weights 2021',
     'IUPAC', null, null,
     'Molar masses and ion contributions of brewing water salts, computed from standard atomic masses'),
    ('palmer-how-to-brew',
     'How to Brew', 'Fourth edition 2017',
     'Brewers Publications', null, null,
     'Table 18.5 (p. 289) and Table 24.1 (p. 436) only; file shared/rag-files/pending/how_to_brew.pdf')
on conflict (slug) do nothing;

-- Corrections to rows inserted by an earlier version of this file.
update ref.source set edition = 'IUPAC standard atomic weights 2021'
 where slug = 'water-chemistry'
   and edition is distinct from 'IUPAC standard atomic weights 2021';

update ref.source set notes = 'Yeast attenuation for Gozdawa and Brewline strains, as the user read them'
 where slug = 'brewfather'
   and notes is distinct from 'Yeast attenuation for Gozdawa and Brewline strains, as the user read them';

update ref.source set notes = 'Dry yeast page (this URL) and liquid yeast page (https://www.hopline.hu/alapanyagok/elesztok/folyekony-eleszto)'
 where slug = 'hopline-yeasts'
   and notes is distinct from 'Dry yeast page (this URL) and liquid yeast page (https://www.hopline.hu/alapanyagok/elesztok/folyekony-eleszto)';

-- Brewline "Bajor Búza" is named in English (user request 2026-10-11). Renaming the row keeps
-- its id, so the yeast loader's upsert updates it instead of adding a second row.
update ref.ingredient
   set name = 'Bavarian Wheat', name_key = 'bavarianwheat'
 where kind = 'yeast' and producer_key = 'brewline' and name_key = 'bajorbuza'
   and not exists (select 1 from ref.ingredient
                    where kind = 'yeast' and producer_key = 'brewline' and name_key = 'bavarianwheat');

-- The two malts.json sources were replaced by the malt sources above; remove them while
-- nothing references them.
delete from ref.source s
 where s.slug in ('weyermann-specs', 'viking-malt-2020')
   and not exists (select 1 from ref.ingredient i where i.source_id = s.id);

-- The hops.json and hops.hopslist.json sources were replaced by hopline-hops; remove them
-- while nothing references them.
delete from ref.source s
 where s.slug in ('hops-json', 'hopslist')
   and not exists (select 1 from ref.ingredient i where i.source_id = s.id);

-- The Brewtarget yeast files were replaced by hopline-yeasts; remove the source while nothing
-- references it.
delete from ref.source s
 where s.slug = 'brewtarget-default-data'
   and not exists (select 1 from ref.ingredient i where i.source_id = s.id);

-- The Brewline catalogue PDF lists none of hopline's Brewline products (their attenuation comes
-- from Brewfather instead); remove the source while nothing references it.
delete from ref.source s
 where s.slug = 'brewline-catalogue'
   and not exists (select 1 from ref.ingredient i where i.source_id = s.id);
