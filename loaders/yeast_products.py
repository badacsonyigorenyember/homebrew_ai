"""Which yeast each hopline.hu product is: the explicit, hand-checked map.

YEASTS: main SKU -> (producer, product id, name). The producer is the brand in hopline's name
(SafAle/SafLager -> Fermentis, Lalbrew -> Lallemand, Mangrove's Jack -> Mangrove Jack's). The
product id is set only where hopline's name prints one, written in the maker's form (US-05,
M20, YF-101), else None. The name is the strain as the maker sells it, product id included,
without the producer word, "élesztő", "Yeast", "kveik" and the pack size, with hopline's
spelling fixed. Names are English: a Hungarian product name is translated (Brewline
"Bajor Búza" -> Bavarian Wheat; user request 2026-10-11). Brewline, hopline's own repack brand, has its own rows and no codes; each
Brewline comment names the strain its page says it copies (user decision 2026-10-11).

PACK_SIZES: 2 g SKU -> the 12 g SKU of the same Brewline product. Its page is kept in raw only.

SKIPPED: SKU -> why it is not loaded (non-beer yeasts, user decision 2026-10-11).

BREWLINE_COPIES: Brewline SKU -> the SKUs of the strains its page says it copies (report only).

ATTENUATION: main SKU -> attenuation copied from the producer's own source (no hopline page
states one), with that source's slug, the URL read and the text as printed.

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
    "302170": ("Brewline", None, "Bavarian Wheat"),  # Brewline Bajor Búza 12g (copies WB-06)
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
    "302170": ["301060"],  # Bavarian Wheat -> SafAle WB-06
    "301650": ["302010"],  # Belgian Wit -> SafAle T-58
    "301021": ["301020"],  # British Ale -> SafAle S-04
    "301601": ["301030", "300030"],  # U.S. West Coast Ale -> SafAle US-05 and BRY-97
}

# The day the maker sources below were read.
DATE = "2026-10-11"

# Main SKU -> attenuation copied as printed by the producer's source the user named (2026-10-11).
# attenuation_pct is (low, high) as printed, one figure -> (a, a); "printed" is the text as it
# stands in the source; url is the page or PDF it was read from. A source with a word only or no
# figure gives no entry (listed in the report). Norse Nectar and YeasterBunny have no source.
ATTENUATION: dict[str, dict] = {
    # YeastFlow: strain pages under https://yeastflow.com/our-strains/ ("Attenuation" box, no unit
    # printed). YF-107 has a page there though the index lists YF-118 Mrs. McGyver instead.
    "301230": {  # YF 101 – Queen of hearts
        "attenuation_pct": ("72", "76"), "source": "yeastflow-catalogue", "printed": "72-76",
        "url": "https://yeastflow.com/our-strains/yf-101-queen-of-hearts/", "date": DATE,
    },
    "301240": {  # YF 102 – British bulldog
        "attenuation_pct": ("72", "76"), "source": "yeastflow-catalogue", "printed": "72-76",
        "url": "https://yeastflow.com/our-strains/yf-102-british-bulldog/", "date": DATE,
    },
    "301250": {  # YF 103 – Steamprunk
        "attenuation_pct": ("71", "75"), "source": "yeastflow-catalogue", "printed": "71-75",
        "url": "https://yeastflow.com/our-strains/yf-103-steamprunk/", "date": DATE,
    },
    "301260": {  # YF-104 – Terrier
        "attenuation_pct": ("67", "71"), "source": "yeastflow-catalogue", "printed": "67-71",
        "url": "https://yeastflow.com/our-strains/yf-104-terrier/", "date": DATE,
    },
    "301270": {  # YF-105 – Haggis
        "attenuation_pct": ("69", "73"), "source": "yeastflow-catalogue", "printed": "69-73",
        "url": "https://yeastflow.com/our-strains/yf-105-haggis/", "date": DATE,
    },
    "301280": {  # YF-106 – Redshamrock
        "attenuation_pct": ("71", "75"), "source": "yeastflow-catalogue", "printed": "71-75",
        "url": "https://yeastflow.com/our-strains/yf-106-redshamrock/", "date": DATE,
    },
    "301290": {  # YF-107 – McGyver
        "attenuation_pct": ("73", "77"), "source": "yeastflow-catalogue", "printed": "73-77",
        "url": "https://yeastflow.com/our-strains/yf-107-mcgyver/", "date": DATE,
    },
    "301300": {  # YF-108 – Jawohl!
        "attenuation_pct": ("65", "72"), "source": "yeastflow-catalogue", "printed": "65-72",
        "url": "https://yeastflow.com/our-strains/yf-108-jawohl/", "date": DATE,
    },
    "301310": {  # YF-109 – Caskaway
        "attenuation_pct": ("67", "71"), "source": "yeastflow-catalogue", "printed": "67-71",
        "url": "https://yeastflow.com/our-strains/yf-109-caskaway/", "date": DATE,
    },
    "301460": {  # YF-110 – Kölschermeister
        "attenuation_pct": ("72", "78"), "source": "yeastflow-catalogue", "printed": "72-78",
        "url": "https://yeastflow.com/our-strains/yf-110-kolschermeister/", "date": DATE,
    },
    "301231": {  # YF-111 – Pacification
        "attenuation_pct": ("65", "70"), "source": "yeastflow-catalogue", "printed": "65-70",
        "url": "https://yeastflow.com/our-strains/yf-111-pacification/", "date": DATE,
    },
    "301232": {  # YF-112 – Vermonter
        "attenuation_pct": ("78", "82"), "source": "yeastflow-catalogue", "printed": "78-82",
        "url": "https://yeastflow.com/our-strains/yf-112-vermonter/", "date": DATE,
    },
    "301233": {  # YF-114 – Crazy Hazy
        "attenuation_pct": ("75", "80"), "source": "yeastflow-catalogue", "printed": "75-80",
        "url": "https://yeastflow.com/our-strains/yf-114-crazy-hazy/", "date": DATE,
    },
    "302340": {  # YF-116 – St. Hedwig
        "attenuation_pct": ("75", "80"), "source": "yeastflow-catalogue", "printed": "75-80",
        "url": "https://yeastflow.com/our-strains/yf-116-st-hedwig/", "date": DATE,
    },
    "301320": {  # YF-201 – St. Cölibate
        "attenuation_pct": ("78", "85"), "source": "yeastflow-catalogue", "printed": "78-85",
        "url": "https://yeastflow.com/our-strains/yf-201-st-colibate/", "date": DATE,
    },
    "301330": {  # YF-202 – Priest D’vel
        "attenuation_pct": ("74", "82"), "source": "yeastflow-catalogue", "printed": "74-82",
        "url": "https://yeastflow.com/our-strains/yf-202-priest-dvel/", "date": DATE,
    },
    "301340": {  # YF-203 – Father Tibi
        "attenuation_pct": ("78", "85"), "source": "yeastflow-catalogue", "printed": "78-85",
        "url": "https://yeastflow.com/our-strains/yf-203-father-tibi/", "date": DATE,
    },
    "301350": {  # YF-204 – Priest D’vill
        "attenuation_pct": ("75", "80"), "source": "yeastflow-catalogue", "printed": "75-80",
        "url": "https://yeastflow.com/our-strains/yf-204-priest-dvill/", "date": DATE,
    },
    "301360": {  # YF-205 – Holy Cölibate
        "attenuation_pct": ("75", "80"), "source": "yeastflow-catalogue", "printed": "75-80",
        "url": "https://yeastflow.com/our-strains/yf-205-holy-colibate/", "date": DATE,
    },
    "301370": {  # YF-206 – Double Agent
        "attenuation_pct": ("80", "85"), "source": "yeastflow-catalogue", "printed": "80-85",
        "url": "https://yeastflow.com/our-strains/yf-206-double-agent/", "date": DATE,
    },
    "301380": {  # YF-207 – Wit’n a minute
        "attenuation_pct": ("74", "78"), "source": "yeastflow-catalogue", "printed": "74-78",
        "url": "https://yeastflow.com/our-strains/yf-207-witn-a-minute/", "date": DATE,
    },
    "301390": {  # YF-208 – Priest Passion
        "attenuation_pct": ("76", "80"), "source": "yeastflow-catalogue", "printed": "76-80",
        "url": "https://yeastflow.com/our-strains/yf-208-priest-passion/", "date": DATE,
    },
    "301400": {  # YF-301 – Pils’ing them softly
        "attenuation_pct": ("80", "84"), "source": "yeastflow-catalogue", "printed": "80-84",
        "url": "https://yeastflow.com/our-strains/yf-301-pilsing-them-softly/", "date": DATE,
    },
    "301410": {  # YF-302 – Californithologist
        "attenuation_pct": ("67", "71"), "source": "yeastflow-catalogue", "printed": "67-71",
        "url": "https://yeastflow.com/our-strains/yf-302-californithologist/", "date": DATE,
    },
    "301420": {  # YF-303 – Yeastoberfest
        "attenuation_pct": ("65", "73"), "source": "yeastflow-catalogue", "printed": "65-73",
        "url": "https://yeastflow.com/our-strains/yf-303-yeastoberfest/", "date": DATE,
    },
    "301430": {  # YF-304 – Bockster
        "attenuation_pct": ("70", "74"), "source": "yeastflow-catalogue", "printed": "70-74",
        "url": "https://yeastflow.com/our-strains/yf-304-bockster/", "date": DATE,
    },
    "301234": {  # YF-305 – Mistr Pilsner
        "attenuation_pct": ("72", "77"), "source": "yeastflow-catalogue", "printed": "72-77",
        "url": "https://yeastflow.com/our-strains/yf-305-mistr-pilsner/", "date": DATE,
    },
    "301235": {  # YF-306 – Herr Schnellager
        "attenuation_pct": ("73", "82"), "source": "yeastflow-catalogue", "printed": "73-82",
        "url": "https://yeastflow.com/our-strains/yf-306-herr-schnellager/", "date": DATE,
    },
    "301440": {  # YF-401 – Mr. Weizen
        "attenuation_pct": ("74", "79"), "source": "yeastflow-catalogue", "printed": "74-79",
        "url": "https://yeastflow.com/our-strains/yf-401-mr-weizen/", "date": DATE,
    },
    "301450": {  # YF-402 – Herr Weizen
        "attenuation_pct": ("73", "77"), "source": "yeastflow-catalogue", "printed": "73-77",
        "url": "https://yeastflow.com/our-strains/yf-402-herr-weizen/", "date": DATE,
    },
    "302390": {  # YF-403 – Frau Weizen
        "attenuation_pct": ("73", "80"), "source": "yeastflow-catalogue", "printed": "73-80",
        "url": "https://yeastflow.com/our-strains/yf-403-frau-weizen/", "date": DATE,
    },
    "301237": {  # YF-501 – Kingster
        "attenuation_pct": ("77", "83"), "source": "yeastflow-catalogue", "printed": "77-83",
        "url": "https://yeastflow.com/our-strains/yf-501-kingster/", "date": DATE,
    },
    "301238": {  # YF-502 – Farmster
        "attenuation_pct": ("74", "79"), "source": "yeastflow-catalogue", "printed": "74-79",
        "url": "https://yeastflow.com/our-strains/yf-502-farmster/", "date": DATE,
    },
    "301239": {  # YF-503 – Hotspur Viking
        "attenuation_pct": ("78", "83"), "source": "yeastflow-catalogue", "printed": "78-83",
        "url": "https://yeastflow.com/our-strains/yf-503-hotspur-viking/", "date": DATE,
    },
    # YF-666: the page prints "800-100"; the user confirmed it means 80-100 (2026-10-11), so the
    # figure is user-supplied and the printed text is kept.
    "301242": {  # YF-666 – Yeastman
        "attenuation_pct": ("80", "100"), "source": "user-supplied", "printed": "800-100",
        "url": "https://yeastflow.com/our-strains/yf-666-yeastman/", "date": DATE,
        "user": "Use 80–100",
    },
    # Lallemand: product pages of the catalogue (spec table "Attenuation"); Suava has no figure
    # there, so its technical data sheet linked from that page is used.
    "300010": {  # LalBrew Abbaye™
        "attenuation_pct": ("77", "83"), "source": "lallemand-catalogue", "printed": "77-83%",
        "url": "https://www.lallemandbrewing.com/en/continental-europe/products/abbaye-belgian-ale-yeast/", "date": DATE,
    },
    "300020": {  # LalBrew Belle Saison™
        "attenuation_pct": ("86", "94"), "source": "lallemand-catalogue", "printed": "86-94%",
        "url": "https://www.lallemandbrewing.com/en/continental-europe/products/belle-saison-beer-yeast/", "date": DATE,
    },
    "300030": {  # LalBrew BRY-97™
        "attenuation_pct": ("78", "84"), "source": "lallemand-catalogue", "printed": "78-84%",
        "url": "https://www.lallemandbrewing.com/en/continental-europe/products/bry-97-west-coast-ale-yeast/", "date": DATE,
    },
    "300050": {  # LalBrew Diamond™
        "attenuation_pct": ("77", "83"), "source": "lallemand-catalogue", "printed": "77-83%",
        "url": "https://www.lallemandbrewing.com/en/continental-europe/products/diamond-lager-yeast/", "date": DATE,
    },
    "300160": {  # LalBrew Farmhouse™
        "attenuation_pct": ("78", "84"), "source": "lallemand-catalogue", "printed": "78-84%",
        "url": "https://www.lallemandbrewing.com/en/continental-europe/products/lalbrew-farmhouse/", "date": DATE,
    },
    "302400": {  # LalBrew® House Ale
        "attenuation_pct": ("78", "86"), "source": "lallemand-catalogue", "printed": "78-86%",
        "url": "https://www.lallemandbrewing.com/en/continental-europe/products/lalbrew-house-ale/", "date": DATE,
    },
    "300080": {  # LalBrew Munich Classic™
        "attenuation_pct": ("76", "83"), "source": "lallemand-catalogue", "printed": "76-83%",
        "url": "https://www.lallemandbrewing.com/en/continental-europe/products/munich-classic-wheat-beer-yeast/", "date": DATE,
    },
    "300110": {  # LalBrew New England™
        "attenuation_pct": ("78", "83"), "source": "lallemand-catalogue", "printed": "78-83%",
        "url": "https://www.lallemandbrewing.com/en/continental-europe/products/lalbrew-new-england/", "date": DATE,
    },
    "300090": {  # LalBrew Nottingham™
        "attenuation_pct": ("78", "84"), "source": "lallemand-catalogue", "printed": "78-84%",
        "url": "https://www.lallemandbrewing.com/en/continental-europe/products/nottingham-high-performance-ale-yeast/", "date": DATE,
    },
    "302180": {  # LalBrew NovaLager™
        "attenuation_pct": ("78", "84"), "source": "lallemand-catalogue", "printed": "78-84%",
        "url": "https://www.lallemandbrewing.com/en/continental-europe/products/lalbrew-novalager/", "date": DATE,
    },
    "300150": {  # WildBrew Philly Sour™
        "attenuation_pct": ("74", "82"), "source": "lallemand-catalogue", "printed": "74-82%",
        "url": "https://www.lallemandbrewing.com/en/continental-europe/products/wildbrew-philly-sour/", "date": DATE,
    },
    "302330": {  # LalBrew Pomona™
        "attenuation_pct": ("75", "84"), "source": "lallemand-catalogue", "printed": "75-84%",
        "url": "https://www.lallemandbrewing.com/en/continental-europe/products/lalbrew-pomona/", "date": DATE,
    },
    "300140": {  # LalBrew Verdant IPA™
        "attenuation_pct": ("75", "82"), "source": "lallemand-catalogue", "printed": "75-82%",
        "url": "https://www.lallemandbrewing.com/en/continental-europe/products/lalbrew-verdant-ipa/", "date": DATE,
    },
    "300130": {  # LalBrew Voss™
        "attenuation_pct": ("76", "82"), "source": "lallemand-catalogue", "printed": "76-82%",
        "url": "https://www.lallemandbrewing.com/en/continental-europe/products/lalbrew-voss-kveik-ale-yeast/", "date": DATE,
    },
    "300100": {  # LalBrew Windsor™
        "attenuation_pct": ("65", "72"), "source": "lallemand-catalogue", "printed": "65-72%",
        "url": "https://www.lallemandbrewing.com/en/continental-europe/products/windsor-british-style-beer-yeast/", "date": DATE,
    },
    "300070": {  # LalBrew Wit™
        "attenuation_pct": ("75", "82"), "source": "lallemand-catalogue", "printed": "75-82%",
        "url": "https://www.lallemandbrewing.com/en/continental-europe/products/belgian-wit-style-ale-yeast/", "date": DATE,
    },
    "302410": {  # WLP079 Suava Ale Yeast (technical data sheet linked from the catalogue page)
        "attenuation_pct": ("72", "82"), "source": "lallemand-catalogue", "printed": "72% - 82%",
        "url": "https://admin.lallemandbrewing.com/wp-content/uploads/2026/08/WL-Dry-Yeast-Tech-Sheets-2026-Suava_041426-4-2-1.pdf", "date": DATE,
    },
    # Fermentis: data sheets linked from hopline (box "Apparent attenuation"); fermentis.com product
    # pages where hopline links none (T-58, URL from the user) or another strain's sheet (BE-256,
    # S-33).
    "301000": {  # SafAle BE-134
        "attenuation_pct": ("89", "93"), "source": "fermentis-datasheets", "printed": "89-93%",
        "url": "https://distributors.fermentis.com/download/135/english/166/safale-be-134-en.pdf", "date": DATE,
    },
    "301020": {  # SafAle S-04
        "attenuation_pct": ("74", "82"), "source": "fermentis-datasheets", "printed": "74-82%",
        "url": "https://distributors.fermentis.com/download/135/english/167/safale-s-04-en.pdf", "date": DATE,
    },
    "301030": {  # SafAle US-05
        "attenuation_pct": ("78", "82"), "source": "fermentis-datasheets", "printed": "78-82%",
        "url": "https://distributors.fermentis.com/download/135/english/171/safale-us-05-en.pdf", "date": DATE,
    },
    "301060": {  # SafAle WB-06
        "attenuation_pct": ("86", "90"), "source": "fermentis-datasheets", "printed": "86-90%",
        "url": "https://distributors.fermentis.com/download/135/english/173/safale-wb-06-en.pdf", "date": DATE,
    },
    "301090": {  # SafLager S-189
        "attenuation_pct": ("80", "84"), "source": "fermentis-datasheets", "printed": "80-84%",
        "url": "https://distributors.fermentis.com/download/135/english/175/saflager-s-189-en.pdf", "date": DATE,
    },
    "301080": {  # SafLager S-23
        "attenuation_pct": ("80", "84"), "source": "fermentis-datasheets", "printed": "80-84%",
        "url": "https://distributors.fermentis.com/download/135/english/172/saflager-s-23-en.pdf", "date": DATE,
    },
    "301100": {  # SafLager W-34/70
        "attenuation_pct": ("80", "84"), "source": "fermentis-datasheets", "printed": "80-84%",
        "url": "https://distributors.fermentis.com/download/135/english/177/saflager-w34-70-en.pdf", "date": DATE,
    },
    "301010": {  # SafAle BE-256
        "attenuation_pct": ("82", "86"), "source": "fermentis-datasheets", "printed": "82-86%",
        "url": "https://fermentis.com/en/product/safale-be-256/", "date": DATE,
    },
    "301070": {  # SafAle K-97
        "attenuation_pct": ("80", "84"), "source": "fermentis-datasheets", "printed": "80-84%",
        "url": "https://fermentis.com/en/product/safale-k-97/", "date": DATE,
    },
    "301050": {  # SafAle S-33
        "attenuation_pct": ("68", "72"), "source": "fermentis-datasheets", "printed": "68-72%",
        "url": "https://fermentis.com/en/product/safale-s-33/", "date": DATE,
    },
    "302010": {  # SafAle T-58
        "attenuation_pct": ("72", "78"), "source": "fermentis-datasheets", "printed": "72-78%",
        "url": "https://fermentis.com/en/product/safale-t%e2%80%9158/", "date": DATE,
    },
    "301110": {  # SafAle W-68
        "attenuation_pct": ("78", "84"), "source": "fermentis-datasheets", "printed": "78-84%",
        "url": "https://fermentis.com/en/product/safale-w-68/", "date": DATE,
    },
    # Mangrove Jack's: product pages linked from hopline; the Yeast Range booklet (linked from
    # hopline's M84 page) where hopline links none or another strain's page (M20, M47 404, M84).
    "300200": {  # M44 US West Coast
        "attenuation_pct": ("77", "85"), "source": "mangrovejacks-datasheets", "printed": "High (77 - 85%)",
        "url": "https://mangrovejacks.com/collections/craft-series-yeasts/products/m44-us-west-coast-yeast-10g", "date": DATE,
    },
    "300210": {  # M29 French Saison
        "attenuation_pct": ("85", "95"), "source": "mangrovejacks-datasheets", "printed": "Very High (85 - 95%)",
        "url": "https://mangrovejacks.com/collections/craft-series-yeasts/products/m29-french-sasion-yeast-10-g", "date": DATE,
    },
    "300220": {  # M21 Belgian Wit
        "attenuation_pct": ("70", "75"), "source": "mangrovejacks-datasheets", "printed": "Medium (70 - 75%)",
        "url": "https://mangrovejacks.com/collections/craft-series-yeasts/products/belgian-wit-m21-yeast-10g", "date": DATE,
    },
    "300240": {  # M66 Hophead Ale
        "attenuation_pct": ("74", "82"), "source": "mangrovejacks-datasheets", "printed": "Medium (74-82 %)",
        "url": "https://mangrovejacks.com/collections/craft-series-yeasts/products/m66-hophead-ale-yeast-10g", "date": DATE,
    },
    "302270-H": {  # M15 Empire Ale
        "attenuation_pct": ("70", "75"), "source": "mangrovejacks-datasheets", "printed": "Low-Medium (70 - 75%)",
        "url": "https://mangrovejacks.com/collections/craft-series-yeasts/products/m15-empire-ale-yeast-10-g", "date": DATE,
    },
    "302220-H": {  # M54 Californian Lager
        "attenuation_pct": ("77", "82"), "source": "mangrovejacks-datasheets", "printed": "High (77 - 82%)",
        "url": "https://mangrovejacks.com/collections/craft-series-yeasts/products/californian-lager-m54-yeast-10g", "date": DATE,
    },
    "302230-H": {  # M41 Belgian Ale
        "attenuation_pct": ("82", "92"), "source": "mangrovejacks-datasheets", "printed": "Very High (82 - 92%)",
        "url": "https://mangrovejacks.com/collections/craft-series-yeasts/products/belgian-ale-yeast-10g", "date": DATE,
    },
    "302240-H": {  # M31 Belgian Tripel
        "attenuation_pct": ("82", "92"), "source": "mangrovejacks-datasheets", "printed": "Very High (82 - 92%)",
        "url": "https://mangrovejacks.com/collections/craft-series-yeasts/products/belgian-tripel-m31-yeast-10g", "date": DATE,
    },
    "302260-H": {  # M36 Liberty Bell Ale
        "attenuation_pct": ("74", "78"), "source": "mangrovejacks-datasheets", "printed": "High (74 - 78%)",
        "url": "https://mangrovejacks.com/collections/craft-series-yeasts/products/liberty-bell-ale-m36-yeast-10g", "date": DATE,
    },
    "302280-H": {  # M42 New World Strong Ale
        "attenuation_pct": ("77", "82"), "source": "mangrovejacks-datasheets", "printed": "High (77 - 82%)",
        "url": "https://mangrovejacks.com/collections/craft-series-yeasts/products/new-world-strong-ale-m42-yeast-10g", "date": DATE,
    },
    "302200-H": {  # M20 Bavarian Wheat (Yeast Range booklet)
        "attenuation_pct": ("70", "75"), "source": "mangrovejacks-datasheets", "printed": "70 - 75%",
        "url": "https://help.mangrovejacks.com/hc/en-us/article_attachments/13551379984785/Mangrove_Jack_s_Yeast_Range.pdf", "date": DATE,
    },
    "302210-H": {  # M47 Belgian Abbey (Yeast Range booklet)
        "attenuation_pct": ("73", "77"), "source": "mangrovejacks-datasheets", "printed": "73 - 77%",
        "url": "https://help.mangrovejacks.com/hc/en-us/article_attachments/13551379984785/Mangrove_Jack_s_Yeast_Range.pdf", "date": DATE,
    },
    "302250-H": {  # M84 Bohemian Lager (Yeast Range booklet)
        "attenuation_pct": ("72", "76"), "source": "mangrovejacks-datasheets", "printed": "72 - 76%",
        "url": "https://help.mangrovejacks.com/hc/en-us/article_attachments/13551379984785/Mangrove_Jack_s_Yeast_Range.pdf", "date": DATE,
    },
    # Gozdawa and Brewline: Brewfather figures as the user gave them on 2026-10-11 (no URL); one
    # figure is stored as [a,a]. Brewline Abbey Monk Ale and Pure Hornindal got none.
    "301491": {  # Czech Pilsner 18
        "attenuation_pct": ("76", "76"), "source": "brewfather", "printed": "76",
        "url": None, "date": DATE,
    },
    "301571": {  # Old German Altbier
        "attenuation_pct": ("78", "78"), "source": "brewfather", "printed": "78%",
        "url": None, "date": DATE,
    },
    "301531": {  # Porter&Kvass
        "attenuation_pct": ("72", "72"), "source": "brewfather", "printed": "72",
        "url": None, "date": DATE,
    },
    "301541": {  # Pure Ale
        "attenuation_pct": ("75", "75"), "source": "brewfather", "printed": "75",
        "url": None, "date": DATE,
    },
    "301561": {  # "Rochefort" Trappist Ale
        "attenuation_pct": ("77", "77"), "source": "brewfather", "printed": "77",
        "url": None, "date": DATE,
    },
    "301482": {  # Conan "New England"
        "attenuation_pct": ("76", "76"), "source": "brewfather", "printed": "76",
        "url": None, "date": DATE,
    },
    "301540": {  # Noble Saison
        "attenuation_pct": ("83", "83"), "source": "brewfather", "printed": "83",
        "url": None, "date": DATE,
    },
    "301551": {  # Real Scotland
        "attenuation_pct": ("71", "71"), "source": "brewfather", "printed": "71",
        "url": None, "date": DATE,
    },
    "301650": {  # Brewline Belgian Wit
        "attenuation_pct": ("78", "78"), "source": "brewfather", "printed": "Belgian wit 78",
        "url": None, "date": DATE,
    },
    "302170": {  # Brewline Bavarian Wheat (Brewfather: "german wheat")
        "attenuation_pct": ("73", "73"), "source": "brewfather", "printed": "german wheat 73",
        "url": None, "date": DATE,
    },
    "301021": {  # Brewline British Ale
        "attenuation_pct": ("75", "75"), "source": "brewfather", "printed": "british ale 75",
        "url": None, "date": DATE,
    },
    "301492": {  # Brewline Czech Lager
        "attenuation_pct": ("76", "76"), "source": "brewfather", "printed": "czech lager 76",
        "url": None, "date": DATE,
    },
    "301101": {  # Brewline German Lager
        "attenuation_pct": ("81", "81"), "source": "brewfather", "printed": "german lager 81",
        "url": None, "date": DATE,
    },
    "300091": {  # Brewline High Performance Ale
        "attenuation_pct": ("81", "81"), "source": "brewfather", "printed": "high performance ale 81",
        "url": None, "date": DATE,
    },
    "300121": {  # Brewline Köln
        "attenuation_pct": ("78", "78"), "source": "brewfather", "printed": "köln 78",
        "url": None, "date": DATE,
    },
    "301601": {  # Brewline U.S. West Coast Ale
        "attenuation_pct": ("80", "80"), "source": "brewfather", "printed": "us west coast 80",
        "url": None, "date": DATE,
    },
}
