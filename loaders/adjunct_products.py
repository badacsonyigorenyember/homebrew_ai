"""Which adjunct each hopline.hu flake or sugar product is: the explicit, hand-checked map.

PALMER: the rows of Palmer's How to Brew (Fourth edition 2017) that this map uses, as printed.
Table 18.5 (p. 289) prints the fine-grind dry-basis yield (FGDB) of flaked grains; Table 24.1
(p. 436) prints each sugar's PPG and fermentability. For a sugar, "fermentability" is the
category the printed figure means: "full" (yeast ferments all of it) or "none" (none of it).

PRODUCTS: hopline SKU -> (ingredient name, Palmer row, hopline figures). The hopline pages
print almost no figures, so each one is typed here by hand as field -> (value, the page's own
words). loaders.adjuncts.build checks that those words are on the fetched page.

PACK_SIZES: hopline SKU of another pack of a product -> the SKU in PRODUCTS. Its page is kept
in raw only.

PALMER_ONLY: ingredient name -> Palmer row, for an adjunct hopline does not sell.

SKIPPED: hopline SKUs left out on purpose, with the reason.

An SKU in none of PRODUCTS, PACK_SIZES and SKIPPED raises in loaders.adjuncts.build, so a new
hopline product never loads without a decision here.
"""

PALMER: dict[str, dict] = {
    # Table 18.5 "Typical malt yields in PPG and PKL", p. 289
    "Oatmeal (flaked)": {"table": "18.5", "page": "289", "fgdb": "70%"},
    "Corn (flaked)": {"table": "18.5", "page": "289", "fgdb": "84%"},
    "Rice (flaked)": {"table": "18.5", "page": "289", "fgdb": "82%"},
    "Barley (flaked)": {"table": "18.5", "page": "289", "fgdb": "70%"},
    # Table 24.1 "Common brewing sugars", p. 436
    "Table sugar": {
        "table": "24.1",
        "page": "436",
        "ppg": "46",
        "fermentability_printed": "100%",
        "fermentability": "full",
    },
    "Lactose": {
        "table": "24.1",
        "page": "436",
        "ppg": "46",
        "fermentability_printed": "…",
        "fermentability": "none",
        "comment": "Lactose is an unfermentable sugar",
    },
    "Honey": {
        "table": "24.1",
        "page": "436",
        "ppg": "38",
        "fermentability_printed": "95%",
        "fermentability": "full",
    },
}

PRODUCTS: dict[str, tuple[str, str, dict[str, tuple[str, str]]]] = {
    "400150": ("Flaked Oats", "Oatmeal (flaked)", {}),  # Zabpehely 100g
    "400270": ("Flaked Corn", "Corn (flaked)", {}),  # Kukoricapehely 100g
    "400100": (  # Rizspehely 100g
        "Flaked Rice",
        "Rice (flaked)",
        {"max_pct": ("40", "akár 40%-ban is használhatunk rizspehelyt")},
    ),
    "400110": ("Flaked Barley", "Barley (flaked)", {}),  # Árpa pehely 100g
    # Hopline sells crystals (sucrose), so Palmer's "Table sugar" row, not "Belgian candi syrup".
    "400091-cs": ("Brown Candi Sugar", "Table sugar", {"ebc": ("225", "Szín: 225 EBC")}),  # Barna kandiscukor 500g
    "400030-cs": (  # Laktóz 250g
        "Lactose",
        "Lactose",
        {"fermentability": ("none", "a nem erjeszthető cukrok csoportjába tartozik")},
    ),
}

# COLOUR: ingredient name -> (EBC low, EBC high, source slug, what the source prints). Hopline
# prints no colour for the flakes, so they take the producer's own figure. Honey, Lactose and
# Enzyme Malt have no sourced colour and stay NULL (user decision 2026-10-15): s3's colour
# check then counts only the fermentables that have one, and says so.
COLOUR: dict[str, tuple[str, str, str, str]] = {
    "Flaked Barley": ("0", "3.2", "simpsons-malt-nov25", "Simpsons nexthop product range Nov 2025, p. 2, Unmalted Adjuncts: Flaked Barley <3.2 EBC"),
    "Flaked Oats": ("0", "3.2", "simpsons-malt-nov25", "Simpsons nexthop product range Nov 2025, p. 2, Unmalted Adjuncts: Flaked Oats <3.2 EBC"),
    # 0.8 SRM x 1.97 (app.ebc_from_srm) = 1.576 EBC
    "Flaked Corn": ("1.576", "1.576", "briess-flakes-web", "https://brewingwithbriess.com/craft-distilling/flakes/ Brewers Yellow Corn Flakes Non-GMO: 0.8 SRM, x 1.97"),
    # 1 SRM x 1.97 = 1.97 EBC (Briess's product is brown rice flakes)
    "Flaked Rice": ("1.97", "1.97", "briess-flakes-web", "https://brewingwithbriess.com/craft-distilling/flakes/ Brewers Brown Rice Flakes: 1 SRM, x 1.97"),
}

PACK_SIZES: dict[str, str] = {
    "400031-cs": "400030-cs",  # Laktóz 1kg
}

# Hopline sells no honey (user decision 2026-10-11): Palmer's row only.
PALMER_ONLY: dict[str, str] = {
    "Honey": "Honey",
}

SKIPPED: dict[str, str] = {
    "400120": "Rozs pehely 100g: rye flakes, another adjunct no test brief needs",
    "400130": "Búzapehely 100g: wheat flakes, another adjunct no test brief needs",
    "400290": "Chit Malt - 100g: chit malt flakes, another adjunct no test brief needs",
    "400081-cs": "Fehér kandiscukor 600g: white candi sugar, another adjunct no test brief needs",
    "400370": "Fruktóz 500g: fructose, another adjunct no test brief needs",
    "400160": "Rizshéj 1 liter: rice hulls, a process aid, not a fermentable",
    "400161-cs": "Rizshéj 5 liter: rice hulls, a process aid, not a fermentable",
}
