-- Test data for the container only, never the stack: two recipes copied from the stack's
-- recipe 1155 (a session IPA). Foreign keys use subqueries by a natural key, because every id
-- is generated always as identity. Run with -v process=<the text of recipe-1155-process.json>.

-- Where the reference rows below come from.
insert into ref.source (slug)
values ('test');

-- Recipe 1155's style.
insert into ref.beer_style (source_id, guide, code, name, raw)
values ((select id from ref.source where slug = 'test'),
        'BA', 'session-india-pale-ale', 'Session India Pale Ale', '{}');

-- Recipe 1155's six ingredients: two malts, three hops, one yeast.
insert into ref.ingredient (source_id, kind, name, producer, name_key, producer_key, raw)
values ((select id from ref.source where slug = 'test'),
        'fermentable', 'Pale Ale Malt', 'Weyermann', 'palealemalt', 'weyermann', '{}'),
       ((select id from ref.source where slug = 'test'),
        'fermentable', 'Caramel 30 Malt', 'Viking Malt', 'caramel30malt', 'vikingmalt', '{}'),
       ((select id from ref.source where slug = 'test'),
        'hop', 'Columbus', '', 'columbus', '', '{}'),
       ((select id from ref.source where slug = 'test'),
        'hop', 'Citra', '', 'citra', '', '{}'),
       ((select id from ref.source where slug = 'test'),
        'hop', 'Cascade', '', 'cascade', '', '{}'),
       ((select id from ref.source where slug = 'test'),
        'yeast', 'SafAle US-05', 'Fermentis', 'safaleus05', 'fermentis', '{}');

-- The request both recipes answer.
insert into app.brief (request_text, brief)
values ('A session IPA at 4 %, hoppy but light enough to drink all afternoon.',
        '{"named": "session IPA", "stated": {"abv": 4}}');

-- Two recipes with 1155's numbers: the first with its saved process, the second without one.
insert into app.recipe (brief_id, style_id, batch_l, efficiency_pct, targets,
                        og, fg, abv, ibu, srm, calc_version, process)
values ((select id from app.brief where request_text like 'A session IPA%'),
        (select id from ref.beer_style where code = 'session-india-pale-ale'),
        20.0, 72.0, '{}', 1.0402, 1.0080, 4.1, 38.3, 5.6, 'maths-1', :'process'),
       ((select id from app.brief where request_text like 'A session IPA%'),
        (select id from ref.beer_style where code = 'session-india-pale-ale'),
        20.0, 72.0, '{}', 1.0402, 1.0080, 4.1, 38.3, 5.6, 'maths-1', null);

-- The first recipe's items, copied from 1155.
insert into app.recipe_item (recipe_id, ingredient_id, raw_name, usage, time_min, pct, amount, unit)
values ((select id from app.recipe where process is not null),
        (select id from ref.ingredient where name = 'Pale Ale Malt'),
        'Pale Ale Malt', 'mash', null, 90.54, 3.350, 'kg'),
       ((select id from app.recipe where process is not null),
        (select id from ref.ingredient where name = 'Caramel 30 Malt'),
        'Caramel 30 Malt', 'mash', null, 9.46, 0.350, 'kg'),
       ((select id from app.recipe where process is not null),
        (select id from ref.ingredient where name = 'Columbus'),
        'Columbus', 'boil', 60.0, 40.91, 18.000, 'g'),
       ((select id from app.recipe where process is not null),
        (select id from ref.ingredient where name = 'Citra'),
        'Citra', 'whirlpool', 0.0, 29.55, 13.000, 'g'),
       ((select id from app.recipe where process is not null),
        (select id from ref.ingredient where name = 'Cascade'),
        'Cascade', 'dry_hop', 0.0, 29.55, 13.000, 'g'),
       ((select id from app.recipe where process is not null),
        (select id from ref.ingredient where name = 'SafAle US-05'),
        'SafAle US-05', 'ferment', null, null, 16.000, 'g');

-- The second recipe's items: a shorter list, enough to have items.
insert into app.recipe_item (recipe_id, ingredient_id, raw_name, usage, time_min, pct, amount, unit)
values ((select id from app.recipe where process is null),
        (select id from ref.ingredient where name = 'Pale Ale Malt'),
        'Pale Ale Malt', 'mash', null, 100.00, 3.700, 'kg'),
       ((select id from app.recipe where process is null),
        (select id from ref.ingredient where name = 'Columbus'),
        'Columbus', 'boil', 60.0, 100.00, 18.000, 'g'),
       ((select id from app.recipe where process is null),
        (select id from ref.ingredient where name = 'SafAle US-05'),
        'SafAle US-05', 'ferment', null, null, 16.000, 'g');
