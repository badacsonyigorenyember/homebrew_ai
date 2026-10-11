"""Which yeast each hopline.hu product is: the explicit, hand-checked map.

YEASTS: main SKU -> (producer, product id, name). The producer is the brand in hopline's name
(SafAle/SafLager -> Fermentis, Lalbrew -> Lallemand, Mangrove's Jack -> Mangrove Jack's). The
product id is set only where hopline's name prints one, written in the maker's form (US-05,
M20, YF-101), else None. The name is the strain as the maker sells it, product id included,
without the producer word, "élesztő", "Yeast", "kveik" and the pack size, with hopline's
spelling fixed. Brewline, hopline's own repack brand, has its own rows and no codes; each
Brewline comment names the strain its page says it copies (user decision 2026-10-11).

PACK_SIZES: 2 g SKU -> the 12 g SKU of the same Brewline product. Its page is kept in raw only.

SKIPPED: SKU -> why it is not loaded (non-beer yeasts, user decision 2026-10-11).

BREWLINE_COPIES: Brewline SKU -> the SKUs of the strains its page says it copies (report only).

An SKU in none of the three raises in loaders.yeasts.build, so a new hopline product never
loads without a decision here. Comments are hopline's product names (2026-10-11).
"""

YEASTS: dict[str, tuple[str, str | None, str]] = {
    # Brewline (no codes; the comment's "copies" is what its page says)
    "301101": ("Brewline", None, "German Lager"),  # Brewline German Lager - W34/70 - 12g (copies W-34/70)
    "301492": ("Brewline", None, "Czech Lager"),  # Brewline Czech Lager 12g (copies Gozdawa CP18 "Czech Pilsner")
    "300091": ("Brewline", None, "High Performance Ale"),  # Brewline High Performance Ale / Nottingham (copies Nottingham)
    "300121": ("Brewline", None, "Köln"),  # Brewline Köln élesztő 12g (names no strain)
    "301011": ("Brewline", None, "Abbey Monk Ale"),  # Brewline Abbey Monk Ale élesztő - 12g (copies BE-256)
    "302310": ("Brewline", None, "Pure Hornindal"),  # Brewline Pure Hornindal kveik (names no strain)
    "302170": ("Brewline", None, "Bajor Búza"),  # Brewline Bajor Búza 12g (copies WB-06)
    "301650": ("Brewline", None, "Belgian Wit"),  # Brewline Belgian Wit 12g (copies T-58)
    "301021": ("Brewline", None, "British Ale"),  # Brewline British Ale 12g (copies S-04)
    "301601": ("Brewline", None, "U.S. West Coast Ale"),  # Brewline U.S West Coast Ale 12g (copies US-05 and BRY-97)
    # Fermentis
    "302190": ("Fermentis", "BR-8", "SafBrew BR-8"),  # Fermentis BR-8 Brettanomyces élesztő
    "301000": ("Fermentis", "BE-134", "SafAle BE-134"),  # Fermentis SafAle BE-134
    "301010": ("Fermentis", "BE-256", "SafAle BE-256"),  # Fermentis SafAle BE-256
    "301070": ("Fermentis", "K-97", "SafAle K-97"),  # Fermentis SafAle K-97
    "301020": ("Fermentis", "S-04", "SafAle S-04"),  # Fermentis SafAle S-04
    "301050": ("Fermentis", "S-33", "SafAle S-33"),  # Fermentis SafAle S-33
    "302010": ("Fermentis", "T-58", "SafAle T-58"),  # Fermentis SafAle T-58
    "301030": ("Fermentis", "US-05", "SafAle US-05"),  # Fermentis SafAle US-05
    "301110": ("Fermentis", "W-68", "SafAle W-68"),  # Fermentis SafAle W-68
    "301060": ("Fermentis", "WB-06", "SafAle WB-06"),  # Fermentis SafAle WB-06
    "301090": ("Fermentis", "S-189", "SafLager S-189"),  # SafLager S-189
    "301080": ("Fermentis", "S-23", "SafLager S-23"),  # SafLager S-23
    "301100": ("Fermentis", "W-34/70", "SafLager W-34/70"),  # SafLager W-34/70
    # Gozdawa
    "301491": ("Gozdawa", None, "Czech Pilsner 18"),  # Gozdawa Czech Pilsner 18 10g
    "301571": ("Gozdawa", None, "Old German Altbier"),  # Gozdawa Old German Altbier 10g
    "301531": ("Gozdawa", None, "Porter&Kvass"),  # Gozdawa Porter&Kvass 10g
    "301541": ("Gozdawa", None, "Pure Ale"),  # Gozdawa Pure Ale 10g
    "301471": ("Gozdawa", "W-34/70", "W-34/70"),  # Gozdawa W-34/70 10g
    "301561": ("Gozdawa", None, '"Rochefort" Trappist Ale'),  # Gozdawa "Rochefort" Trappist Ale 10g
    "301482": ("Gozdawa", None, 'Conan "New England"'),  # Gozdawa Conan "New England" 10 g
    "301540": ("Gozdawa", None, "Noble Saison"),  # Gozdawa Noble Saison 10 g
    "301551": ("Gozdawa", None, "Real Scotland"),  # Gozdawa Real Scotland Yeast 10g
    # Lallemand (names as on lallemandbrewing.com: LalBrew Diamond, WLP079 Suava Ale Yeast)
    "300010": ("Lallemand", None, "Abbaye"),  # Lalbrew Abbaye élesztő
    "300020": ("Lallemand", None, "Belle Saison"),  # Lalbrew Belle Saison élesztő
    "300030": ("Lallemand", "BRY-97", "BRY-97"),  # Lallemand BRY-97 élesztő
    "300040": ("Lallemand", "CBC-1", "CBC-1"),  # Lallemand CBC-1 élesztő
    "300050": ("Lallemand", None, "Diamond"),  # Lallemand Diamond Lager élesztő
    "300160": ("Lallemand", None, "Farmhouse"),  # Lallemand Farmhouse
    "302400": ("Lallemand", None, "House Ale"),  # Lallemand House Ale élesztő
    "300080": ("Lallemand", None, "Munich Classic"),  # Lallemand Munich Classic élesztő
    "300110": ("Lallemand", None, "New England"),  # Lallemand New England élesztő
    "300090": ("Lallemand", None, "Nottingham"),  # Lallemand Nottingham élesztő
    "302180": ("Lallemand", None, "NovaLager"),  # Lallemand Novalager élesztő
    "300150": ("Lallemand", None, "Philly Sour"),  # Lallemand Philly Sour
    "302330": ("Lallemand", None, "Pomona"),  # Lallemand Pomona élesztő
    "302410": ("Lallemand", None, "Suava Ale"),  # Lallemand Suava Ale élesztő WLP079 (WLP079 is White Labs' code)
    "300140": ("Lallemand", None, "Verdant IPA"),  # Lallemand Verdant IPA élesztő
    "300130": ("Lallemand", None, "Voss"),  # Lallemand Voss élesztő
    "300100": ("Lallemand", None, "Windsor"),  # Lallemand Windsor élesztő
    "300070": ("Lallemand", None, "Wit"),  # Lallemand Wit élesztő
    # Mangrove Jack's (hopline writes some as "Mangrove's Jack")
    "302270-H": ("Mangrove Jack's", "M15", "M15 Empire Ale"),  # Mangrove's Jack M15 - Empire Ale yeast
    "302200-H": ("Mangrove Jack's", "M20", "M20 Bavarian Wheat"),  # Mangrove Jack's Bavarian Wheat Yeast M20
    "300220": ("Mangrove Jack's", "M21", "M21 Belgian Wit"),  # Mangrove Jack's M21 Belgian Wit élesztő
    "300210": ("Mangrove Jack's", "M29", "M29 French Saison"),  # Mangrove Jack's M29 French Saison élesztő
    "302240-H": ("Mangrove Jack's", "M31", "M31 Belgian Tripel"),  # Mangrove's Jack Belgian Tripel yeast Yeast M31
    "302260-H": ("Mangrove Jack's", "M36", "M36 Liberty Bell Ale"),  # Mangrove's Jack Liberty Bell Yeast (M36)
    "302230-H": ("Mangrove Jack's", "M41", "M41 Belgian Ale"),  # Mangrove's Jack Belgian Ale Yeast M41
    "302280-H": ("Mangrove Jack's", "M42", "M42 New World Strong Ale"),  # Mangrove's Jack New World Strong Ale Yeast M42
    "300200": ("Mangrove Jack's", "M44", "M44 US West Coast"),  # Mangrove Jack's M44 US West Coast élesztő
    "302210-H": ("Mangrove Jack's", "M47", "M47 Belgian Abbey"),  # Mangrove Jack's Belgian Abbey Yeast M47
    "302220-H": ("Mangrove Jack's", "M54", "M54 Californian Lager"),  # Mangrove Jack's Californian Lager Yeast M54
    "300240": ("Mangrove Jack's", "M66", "M66 Hophead Ale"),  # Mangrove Jack's M66 Hophead Ale élesztő
    "302250-H": ("Mangrove Jack's", "M84", "M84 Bohemian Lager"),  # Mangrove's Jack Bohemian Lager Yeast M84
    # Norse Nectar
    "302360": ("Norse Nectar", None, "Aurland"),  # Norse Nectar Aurland kveik
    "301170": ("Norse Nectar", None, "Ebbergarden"),  # Norse Nectar Ebbergarden kveik
    "301180": ("Norse Nectar", None, "Espe"),  # Norse Nectar Espe kveik
    "302140": ("Norse Nectar", None, "Framgarden"),  # Norse Nectar Framgarden kveik
    "301150": ("Norse Nectar", None, "Hornindal"),  # Norse Nectar Hornindal kveik
    "302380": ("Norse Nectar", None, "Jordal"),  # Norse Nectar Jordal kveik
    "301190": ("Norse Nectar", None, "Jovaru"),  # Norse Nectar Jovaru kveik
    "302160": ("Norse Nectar", None, "Lida"),  # Norse Nectar Lida kveik
    "302320": ("Norse Nectar", None, "Nystein"),  # Norse Nectar Nystein kveik
    "301210": ("Norse Nectar", None, "Opshaug"),  # Norse Nectar Opshaug kveik
    "301220": ("Norse Nectar", None, "Rivenes"),  # Norse Nectar Rivenes kveik
    "301221": ("Norse Nectar", None, "Simonaitis"),  # Norse Nectar Simonaitis kveik
    "301200": ("Norse Nectar", None, "Skare"),  # Norse Nectar Skare kveik
    "301120": ("Norse Nectar", None, "Spro"),  # Norse Nectar Spro kveik
    "301140": ("Norse Nectar", None, "Stranda"),  # Norse Nectar Stranda kveik
    "301130": ("Norse Nectar", None, "Voss"),  # Norse Nectar Voss kveik
    "302370": ("Norse Nectar", None, "Wollsaeter"),  # Norse Nectar Wollsaeter kveik
    # YeasterBunny
    "301160": ("YeasterBunny", "YB-208", "YB-208 Tormodgarden"),  # YeasterBunny YB-208 Tormodgarden kveik
    # YeastFlow (names as on yeastflow.com/our-strains)
    "301230": ("YeastFlow", "YF-101", "YF-101 Queen of Hearts"),  # YF-101 Yeastflow Queen of hearts élesztő
    "301240": ("YeastFlow", "YF-102", "YF-102 British Bulldog"),  # YF-102 Yeastflow British Bulldog élesztő
    "301250": ("YeastFlow", "YF-103", "YF-103 Steamprunk"),  # YF-103 Yeastflow Steamprunk élesztő
    "301260": ("YeastFlow", "YF-104", "YF-104 Terrier"),  # YF-104 Yeastflow Terrier élesztő
    "301270": ("YeastFlow", "YF-105", "YF-105 Haggis"),  # YF-105 Yeastflow Haggis élesztő
    "301280": ("YeastFlow", "YF-106", "YF-106 Redshamrock"),  # YF-106 Yeastflow Redshamrock élesztő
    "301290": ("YeastFlow", "YF-107", "YF-107 McGyver"),  # YF-107 Yeastflow McGyver élesztő
    "301300": ("YeastFlow", "YF-108", "YF-108 Jawohl!"),  # YF-108 Yeastflow Jawohl! élesztő
    "301310": ("YeastFlow", "YF-109", "YF-109 Caskaway"),  # YF-109 Yeastflow Caskaway élesztő
    "301460": ("YeastFlow", "YF-110", "YF-110 Kölschermeister"),  # YF-110 Yeastflow Kölscher Meister élesztő
    "301231": ("YeastFlow", "YF-111", "YF-111 Pacification"),  # YF-111 Yeastflow Pacification élesztő
    "301232": ("YeastFlow", "YF-112", "YF-112 Vermonter"),  # YF-112 Yeastflow Vermonter élesztő
    "301233": ("YeastFlow", "YF-114", "YF-114 Crazy Hazy"),  # YF-114 Yeastflow Crazy Hazy élesztő
    "302340": ("YeastFlow", "YF-116", "YF-116 St. Hedwig"),  # YF-116 Yeastflow St. Hedwig élesztő
    "301320": ("YeastFlow", "YF-201", "YF-201 St. Cölibate"),  # YF-201 Yeastflow St. Cölibate élesztő
    "301330": ("YeastFlow", "YF-202", "YF-202 Priest D'vel"),  # YF-202 Yeastflow Priest D'vel élesztő
    "301340": ("YeastFlow", "YF-203", "YF-203 Father Tibi"),  # YF-203 Yeastflow Father Tibi élesztő
    "301350": ("YeastFlow", "YF-204", "YF-204 Priest D'vill"),  # YF-204 Yeastflow Priest D'vill élesztő
    "301360": ("YeastFlow", "YF-205", "YF-205 Holy Cölibate"),  # YF-205 Yeastflow Holly Cölibate élesztő
    "301370": ("YeastFlow", "YF-206", "YF-206 Double Agent"),  # YF-206 Yeastflow Double Agent élesztő
    "301380": ("YeastFlow", "YF-207", "YF-207 Wit'n a minute"),  # YF-207 Yeastflow Wit'n a minute élesztő
    "301390": ("YeastFlow", "YF-208", "YF-208 Priest Passion"),  # YF-208 Yeastflow Priest Passion élesztő
    "301400": ("YeastFlow", "YF-301", "YF-301 Pils'ing them softly"),  # YF-301 Yeastflow Pils'ing them softly élesztő
    "301410": ("YeastFlow", "YF-302", "YF-302 Californithologist"),  # YF-302 Yeastflow Californithologist élesztő
    "301420": ("YeastFlow", "YF-303", "YF-303 Yeastoberfest"),  # YF-303 Yeastflow Yeastoberfest élesztő
    "301430": ("YeastFlow", "YF-304", "YF-304 Bockster"),  # YF-304 Yeastflow Bockster élesztő
    "301234": ("YeastFlow", "YF-305", "YF-305 Mistr Pilsner"),  # YF-305 Yeastflow Mistr Pilsner élesztő
    "301235": ("YeastFlow", "YF-306", "YF-306 Herr Schnellager"),  # YF-306 Yeastflow Herr Schnellager élesztő
    "301440": ("YeastFlow", "YF-401", "YF-401 Mr. Weizen"),  # YF-401 Yeastflow Mr.Weizen élesztő
    "301450": ("YeastFlow", "YF-402", "YF-402 Herr Weizen"),  # YF-402 Yeastflow Herr Weizen élesztő
    "302390": ("YeastFlow", "YF-403", "YF-403 Frau Weizen"),  # YF-403 Yeastflow Frau Weizen élesztő
    "301237": ("YeastFlow", "YF-501", "YF-501 Kingster"),  # YF-501 Yeastflow Kingster élesztő
    "301238": ("YeastFlow", "YF-502", "YF-502 Farmster"),  # YF-502 Yeastflow Farmster élesztő
    "301239": ("YeastFlow", "YF-503", "YF-503 Hotspur Viking"),  # YF-503 Yeastflow Hotspur Viking élesztő
    "301242": ("YeastFlow", "YF-666", "YF-666 Yeastman"),  # YF-666 Yeastflow Yeastman élesztő
    "301243": ("YeastFlow", "YF-801", "YF-801 Brett Pid"),  # YF-801 Yeastflow Brett Pid élesztő
    "301244": ("YeastFlow", "YF-998", "YF-998 Sour, yes sour!"),  # YF-998 Yeastflow Sour, yes sour élesztő
    "301245": ("YeastFlow", "YF-999", "YF-999 Sourprise"),  # YF-999 Yeastflow Sourprise élesztő
}

PACK_SIZES: dict[str, str] = {
    "301610": "301021",  # Brewline British Ale 2g -> Brewline British Ale 12g
    "301600": "301601",  # Brewline U.S West Coast Ale 2g -> Brewline U.S West Coast Ale 12g
}

SKIPPED: dict[str, str] = {
    "301580": "whiskey yeast",  # Gozdawa American Bourbon Whiskey élesztő 10g
    "301560": "whiskey yeast",  # Gozdawa Irish Whiskey élesztő 10g
    "301570": "whiskey yeast",  # Gozdawa Scotch Whiskey élesztő 10g
    "301581": "cider yeast",  # Gozdawa French Cider G1 10g
    "300250": "cider yeast",  # Mangrove Jack's M02 Cider élesztő
    "301591": "mead yeast",  # Gozdawa Mead 10g
    "300230": "mead yeast",  # Mangrove Jack's M05 Mead élesztő
    "301241": "sake yeast",  # YF-601 Yeastflow For the SAKE of brewing élesztő
}

# Brewline SKU -> the SKUs of the strains its page says it copies (Köln and Pure Hornindal name
# none). Used only by the report, to show whether the data blocks agree.
BREWLINE_COPIES: dict[str, list[str]] = {
    "301101": ["301100"],  # German Lager -> SafLager W-34/70
    "301492": ["301491"],  # Czech Lager -> Gozdawa Czech Pilsner 18 (CP18)
    "300091": ["300090"],  # High Performance Ale -> Nottingham
    "301011": ["301010"],  # Abbey Monk Ale -> SafAle BE-256
    "302170": ["301060"],  # Bajor Búza -> SafAle WB-06
    "301650": ["302010"],  # Belgian Wit -> SafAle T-58
    "301021": ["301020"],  # British Ale -> SafAle S-04
    "301601": ["301030", "300030"],  # U.S. West Coast Ale -> SafAle US-05 and BRY-97
}
