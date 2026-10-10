"""Which hop each hopline.hu product is: the explicit, hand-checked map.

HOPS: main SKU -> hop name. The main SKU is the 100 g ("-cs") page where the variety has one,
else its only page; that page's figures are loaded. The name is hopline's without "komló", the
pack size, an alpha in the name and ™, with hopline's misspellings fixed. LUPOMAX products are
their own hops, never merged with the pellet.

PACK_SIZES: extra pack-size SKU -> the main SKU of its hop. Its page is kept in raw only.

NULL_FIGURES: main SKUs whose page shows another hop's content, with the reason. These hops are
loaded with name, origin and purpose, but no acid or oil figures (user decision 2026-10-10).

An SKU in neither HOPS nor PACK_SIZES raises in loaders.hops.build, so a new hopline product
never loads without a decision here. Comments are hopline's product names (2026-10-10).
"""

HOPS: dict[str, str] = {
    "200020-cs": "African Queen",  # African Queen komló 100g
    "200040-cs": "Amarillo",  # Amarillo komló 100g
    "200044": "Amarillo LUPOMAX",  # Amarillo LUPOMAX 50g
    "200050-cs": "Ariana",  # Ariana komló 100g
    "200780-cs": "Aurora",  # Aurora komló 100g
    "200060-cs": "Azacca",  # Azacca komló 100g
    "200064": "Azacca LUPOMAX",  # Azacca komló LUPOMAX 50g
    "200840-cs": "Barbe Rouge",  # Barbe Rouge komló 100g
    "200070-cs": "Bramling Cross",  # Bramling Cross komló 100g
    "200080-cs": "Brewer's Gold",  # Brewer&#039;s Gold komló 100g
    "200800-cs": "BRU-1",  # BRU-1 komló 100g
    "200110-cs": "Cascade",  # Cascade komló 100g
    "200100-cs": "Cashmere",  # Cashmere komló 100g
    "200120-cs": "Centennial",  # Centennial komló 100g
    "201341": "Ceres",  # Ceres komló 50g
    "200130-cs": "Challenger",  # Challenger komló 100g
    "200150-cs": "Chinook",  # Chinook komló 100g
    "200750-cs": "Citra",  # Citra komló 100g
    "200830": "Citra LUPOMAX",  # Citra komló LUPOMAX 50g
    "200170-cs": "Columbus",  # Colombus komló 100g
    "201360-cs": "Dolcita",  # Dolcita komló 100g
    "200210-cs": "East Kent Golding",  # East Kent Golding komló 100g
    "200220-cs": "Ekuanot",  # Ekuanot komló 100g
    "200250-cs": "El Dorado",  # El Dorado komló 100g
    "200280-cs": "Fuggle",  # Fuggle komló 100g
    "200294-cs": "Galaxy",  # Galaxy komló 100g
    "200310-cs": "Hallertau Blanc",  # Hallertau Blanc komló 100g
    "200320-cs": "Hallertau Hersbrücker",  # Hallertau Hersbrücker 100g
    "200340-cs": "Hallertau Tradition",  # Hallertau Tradition 100g
    "200350-cs": "Herkules",  # Herkules komló 100g
    "200370-cs": "Huell Melon",  # Huell Melon komló 100g
    "200380-cs": "Idaho 7",  # Idaho 7 komló 100g
    "200390-cs": "Kazbek",  # Kazbek komló 100g
    "200420-cs": "Magnum",  # Magnum komló 100g
    "200430-cs": "Mandarina Bavaria",  # Mandarina Bavaria 100g
    "200440-cs": "Mosaic",  # Mosaic komló 100g
    "200444": "Mosaic LUPOMAX",  # Mosaic LUPOMAX 50g
    "200460-cs": "Motueka",  # Motueka komló 100g
    "200870-cs": "Nectaron",  # Nectaron komló 100g
    "200470-cs": "Nelson Sauvin",  # Nelson Sauvin komló 100g
    "200480-cs": "Northern Brewer",  # Northern Brewer 100g
    "200490-cs": "Perle",  # Perle komló 100g
    "200520-cs": "Polaris",  # Polaris komló 100g
    "200890-cs": "Riwaka",  # Riwaka komló 100g
    "200530-cs": "Saaz",  # Saaz komló 100g
    "200540-cs": "Sabro",  # Sabro komló 100g
    "200570-cs": "Simcoe",  # Simcoe komló 100g
    "200580-cs": "Sorachi Ace",  # Sorachi Ace komló 100g
    "200610-cs": "Spalt Select",  # Spalt Select komló 100g
    "200860-cs": "Strata",  # Strata komló 100g
    "200630-cs": "Styrian Golding",  # Styrian Golding 100g
    "201001-cs": "Superdelic",  # Superdelic komló 100g
    "200650-cs": "Target",  # Target komló 100g
    "200670-cs": "Tettnanger",  # Tettnanger komló 100g
    "200760-cs": "Uran",  # Uran komló 100g
    "200700-cs": "Wai-Iti",  # Wai-Iti komló 100g
    "200710-cs": "Waimea",  # Waimea komló 100g
    "200720-cs": "Wakatu",  # Wakatu komló 100g
    "200730-cs": "Warrior",  # Warrior komló 100g
    "200740-cs": "Willamette",  # Willamette komló 100g
    "200030-cs": "Ahtanum",  # Ahtanum komló 100g
    "200160-cs": "Comet",  # Comet koml? 100g
    "200180-cs": "Crystal",  # Crystal komló 100g
    "200269": "Delta",  # Delta komló 1kg (URL says Falconer's Flight; see NULL_FIGURES)
    "200190-cs": "Denali",  # Denali komló 100g
    "200240-cs": "Ella",  # Ella komló 100g
    "201081": "Enigma",  # Enigma komló 50g
    "200270-cs": "First Gold",  # First Gold komló 100g
    "200990-cs": "Hallertau Callista",  # Hallertau Callista komló 100g
    "200330-cs": "Hallertau Mittelfrüh",  # Hallertau Mittelfrüh 100g
    "200980-cs": "Hallertau Opal",  # Hallertau Opal komló 100g
    "200810": "Huell Melon LUPOMAX",  # Huell Melon LUPOMAX 50g (URL says mandarina-bavaria)
    "200400-cs": "Lemondrop",  # Lemondrop komló 100g
    "200410-cs": "Loral",  # Loral koml? 100g
    "200669": "Lotus",  # Lotus komló 1kg (URL says Taurus; see NULL_FIGURES)
    "200790-cs": "Monroe",  # Monroe komló 100g
    "200450-cs": "Mount Hood",  # Mount Hood komló 100g
    "200500-cs": "Pacific Jade",  # Pacific Jade komló 100g
    "200811": "Pacifica",  # Pacifica komló 50g 3.9%
    "200850-cs": "Pekko",  # Pekko komló 100g
    "200510-cs": "Pilgrim",  # Pilgrim komló 100g
    "200550-cs": "Saphir",  # Saphir komló 100g (URL says sabro)
    "200560-cs": "Sladek",  # Sladek komló 100g
    "200600-cs": "Southern Star",  # Southern Star 100g
    "200929": "Sterling",  # Sterling komló 1kg
    "201320-cs": "Styrian Wolf",  # Styrian Wolf komló 100g - 9.80%
    "200680-cs": "Tomahawk",  # Tomahawk komló 100g
    "200821": "Trident",  # Trident komló 50g
    "200690-cs": "Vic Secret",  # Vic Secret komló 100g
    "200770-cs": "Zappa",  # Zappa komló100g
}

PACK_SIZES: dict[str, str] = {
    "200259": "200250-cs",  # El Dorado komló 1kg
    "200329": "200320-cs",  # Hallertau Hersbrücker 1kg
    "200349": "200340-cs",  # Hallertau Tradition 1kg
    "200429": "200420-cs",  # Magnum komló 1kg
    "200439": "200430-cs",  # Mandarina Bavaria 1kg
    "200880": "200870-cs",  # Nectaron komló 50g
    "200872": "200870-cs",  # Nectaron komló 30g
    "200483": "200480-cs",  # Northern Brewer 1kg
    "200899": "200890-cs",  # Riwaka komló 1kg
    "200639": "200630-cs",  # Styrian Golding 1kg
    "200712-masolata-1": "200710-cs",  # Waimea™ komló 30g
    "200749": "200740-cs",  # Willamette komló 1kg
    "200999": "200990-cs",  # Hallertau Callista komló 1kg
    "200989": "200980-cs",  # Hallertau Opal komló 1kg 9.00%
    "200609": "200600-cs",  # Southern Star 1kg 12.00%
    "200779": "200770-cs",  # Zappa komló 1kg
}

NULL_FIGURES: dict[str, str] = {
    "200269": "page shows Falconer's Flight (tags, text and figures)",  # Delta komló 1kg
    "200669": "page shows Taurus (tags and text)",  # Lotus komló 1kg
}
