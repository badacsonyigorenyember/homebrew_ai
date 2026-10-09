"""Which malt each hopline.hu product is: the explicit, hand-checked map.

PRODUCTS: hopline SKU -> (producer, catalogue product or None, ingredient name).
The catalogue product is the "product" of an entry in malt_catalogue.json (None: the maltster's
catalogue does not list it, so only hopline's figures are used). The ingredient name is the
catalogue product, except where two SKUs share one catalogue product.

SKIPPED: hopline SKUs left out on purpose, with the reason.

An SKU in neither raises in loaders.malts.build, so a new hopline product never loads
without a decision here.
"""

PRODUCTS: dict[str, tuple[str, str | None, str]] = {
    # Weyermann (37), catalogue "Weyermann products, brewery (EN)", Crop 2026
    "101010": ("Weyermann", "Pilsner Malt", "Pilsner Malt"),  # Weyermann Pilsner maláta
    "101020": ("Weyermann", "Pale Ale Malt", "Pale Ale Malt"),  # Weyermann Pale Ale maláta
    "101030": ("Weyermann", "Vienna Malt", "Vienna Malt"),  # Weyermann Bécsi maláta
    "101040": ("Weyermann", "Munich Malt Type 1", "Munich Malt Type 1"),  # Weyermann munich I. maláta
    "101050": ("Weyermann", "Munich Malt Type 2", "Munich Malt Type 2"),  # Weyermann munich II. maláta
    "101060": ("Weyermann", "Beech Smoked Barley Malt", "Beech Smoked Barley Malt"),  # Weyermann bükk füstölt maláta
    "101070": ("Weyermann", "Oak Smoked Wheat Malt", "Oak Smoked Wheat Malt"),  # Weyermann tölgy füstölt búza maláta
    "101080": ("Weyermann", "Acidulated Malt", "Acidulated Malt"),  # Weyermann savas maláta
    "101090": ("Weyermann", "Melanoidin Malt", "Melanoidin Malt"),  # Weyermann Melanoidin maláta
    "101100": ("Weyermann", "Wheat Malt Pale", "Wheat Malt Pale"),  # Weyermann búzamaláta
    "101110": ("Weyermann", "Wheat Malt Dark", "Wheat Malt Dark"),  # Weyermann barna búza maláta
    "101120": ("Weyermann", "Carawheat", "Carawheat"),  # Weyermann Carawheat maláta
    "100130": ("Weyermann", "Chocolate Wheat Malt", "Chocolate Wheat Malt"),  # Weyermann Chocolate Wheat maláta
    "101130": ("Weyermann", "Carapils", "Carapils"),  # Weyermann Carapils maláta
    "101140": ("Weyermann", "Carahell", "Carahell"),  # Weyermann Carahell maláta
    "101150": ("Weyermann", "Carared", "Carared"),  # Weyermann Carared maláta
    "101160": ("Weyermann", "Caraamber", "Caraamber"),  # Weyermann Caraamber maláta
    "101170": ("Weyermann", "Caramunich Type 1", "Caramunich Type 1"),  # Weyermann Caramunich I. maláta
    "101180": ("Weyermann", "Caramunich Type 2", "Caramunich Type 2"),  # Weyermann Caramunich II. maláta
    "101190": ("Weyermann", "Caramunich Type 3", "Caramunich Type 3"),  # Weyermann Caramunich III. maláta
    "101200": ("Weyermann", "Caraaroma", "Caraaroma"),  # Weyermann Caraaroma maláta
    "101210": ("Weyermann", "Carabelge", "Carabelge"),  # Weyermann Carabelge maláta
    "101220": ("Weyermann", "Carabohemian", "Carabohemian"),  # Weyermann Carabohemian maláta
    "101240": ("Weyermann", "Bohemian Pilsner Malt", "Bohemian Pilsner Malt"),  # Weyermann Bohemian Pilsner maláta
    "101250": ("Weyermann", "Abbey Malt", "Abbey Malt"),  # Weyermann Abbey maláta
    "101260": ("Weyermann", "Special W", "Special W"),  # Weyermann Special W maláta
    "101270": ("Weyermann", "Roasted Barley", "Roasted Barley"),  # Weyermann Pörkölt árpa
    "101280": ("Weyermann", "Rye Malt Pale", "Rye Malt Pale"),  # Weyermann rozs maláta
    "101340": ("Weyermann", "Carafa Type 1", "Carafa Type 1"),  # Weyermann Carafa I.
    "101470": ("Weyermann", "Carafa Type 2", "Carafa Type 2"),  # Weyermann Carafa II.
    "101350": ("Weyermann", "Carafa Type 3", "Carafa Type 3"),  # Weyermann Carafa III.
    "101400": ("Weyermann", "Carafa Special Type 1", "Carafa Special Type 1"),  # Weyermann Carafa Spec I.
    "101410": ("Weyermann", "Carafa Special Type 2", "Carafa Special Type 2"),  # Weyermann Carafa Spec II.
    "101420": ("Weyermann", "Carafa Special Type 3", "Carafa Special Type 3"),  # Weyermann Carafa Spec III.
    "101430": ("Weyermann", "Extra Pale Premium Pilsner Malt", "Extra Pale Premium Pilsner Malt"),  # Weyermann Extra Pilsner maláta
    "101460": ("Weyermann", "Spelt Malt", "Spelt Malt"),  # Weyermann Spelt maláta
    "101490": ("Weyermann", "Eraclea Pilsner Malt", "Eraclea Pilsner Malt"),  # Weyermann Eraclea Pilsner maláta
    # Viking Malt (32), catalogue "Viking Malt Standard Product Portfolio", 2023
    "100010": ("Viking Malt", "Pilsner Malt", "Pilsner Malt"),  # Viking Pilsner maláta
    "100020": ("Viking Malt", "Pale Ale Malt", "Pale Ale Malt"),  # Viking Pale Ale maláta
    "100030": ("Viking Malt", "Vienna Malt", "Vienna Malt"),  # Viking Bécsi maláta
    "100050": ("Viking Malt", "Wheat Malt", "Wheat Malt"),  # Viking Búzamaláta
    "100070": ("Viking Malt", "CaraBody Malt", "CaraBody Malt"),  # Viking Carabody maláta
    "100080": ("Viking Malt", "Red Active Malt", "Red Active Malt"),  # Viking Red Active maláta
    "100090": ("Viking Malt", "Red Ale Malt", "Red Ale Malt"),  # Viking Red Ale maláta
    "100100": ("Viking Malt", "Dextrin Malt", "Dextrin Malt"),  # Viking Dextrin maláta
    "100110": ("Viking Malt", "Golden Ale Malt", "Golden Ale Malt"),  # Viking Golden Ale maláta
    "100120": ("Viking Malt", "Rye Malt", "Rye Malt"),  # Viking Rozs maláta
    "100140": ("Viking Malt", "Black Malt", "Black Malt"),  # Viking Black maláta
    "100150": ("Viking Malt", "Roasted Barley", "Roasted Barley"),  # Viking pörkölt árpa
    "100160": ("Viking Malt", "Chocolate Light Malt", "Chocolate Light Malt"),  # Viking Coffee maláta
    "100170": ("Viking Malt", "Chocolate Dark Malt", "Chocolate Dark Malt"),  # Viking Chocolate maláta
    "100180": ("Viking Malt", "Munich Light Malt", "Munich Light Malt"),  # Viking Munich Light maláta
    "100190": ("Viking Malt", "Munich Dark Malt", "Munich Dark Malt"),  # Viking Munich Dark maláta
    "100200": ("Viking Malt", "Caramel 30 Malt", "Caramel 30 Malt"),  # Viking Caramel 30 maláta
    "100210": ("Viking Malt", "Caramel 50 Malt", "Caramel 50 Malt"),  # Viking Caramel 50 maláta
    "100220": ("Viking Malt", "Caramel 100 Malt", "Caramel 100 Malt"),  # Viking Caramel 100 maláta
    "100230": ("Viking Malt", "Caramel 150 Malt", "Caramel 150 Malt"),  # Viking Caramel 150 maláta
    "100240": ("Viking Malt", "Caramel 200 Malt", "Caramel 200 Malt"),  # Viking Caramel 200 maláta
    "100250": ("Viking Malt", "Caramel 300 Malt", "Caramel 300 Malt"),  # Viking Caramel 300 maláta
    "100260": ("Viking Malt", "Caramel 400 Malt", "Caramel 400 Malt"),  # Viking Caramel 400 maláta
    "100270": ("Viking Malt", "Caramel 600 Malt", "Caramel 600 Malt"),  # Viking Caramel 600 maláta
    "100280": ("Viking Malt", "Caramel Pale Malt", "Caramel Pale Malt"),  # Viking Caramel Pale maláta
    "100290": ("Viking Malt", "Cookie Malt", "Cookie Malt"),  # Viking Keksz maláta
    "100370": ("Viking Malt", "Enzyme Malt", "Enzyme Malt"),  # Viking enzim maláta
    # Viking makes Smoked Malt with apple, beech, cherry, sweet cherry and pear wood; the
    # catalogue gives one set of figures for all of them.
    "100380": ("Viking Malt", "Smoked Malt", "Smoked Malt (cherry wood)"),  # Viking cseresznyefán füstölt pilsner maláta
    "100381": ("Viking Malt", "Smoked Malt", "Smoked Malt (pear wood)"),  # Viking körtefán füstölt pilsner maláta
    "100390": ("Viking Malt", "Smoked Wheat Malt", "Smoked Wheat Malt"),  # Viking füstölt búza maláta
    "100400": ("Viking Malt", "Lightly Peated Malt", "Lightly Peated Malt"),  # Viking lightly peated maláta
    "101480": ("Viking Malt", None, "Sprau Malt"),  # Viking Sprau Malt (not in the 2023 portfolio)
    # Simpsons Malt (5), catalogue "Simpsons Malt product range (NextHop)", November 2025
    "101290": ("Simpsons Malt", "Finest Pale Ale Maris Otter", "Finest Pale Ale Maris Otter"),  # Simpsons Marris Otter (bag label Simpsons Maris Otter)
    "101310": ("Simpsons Malt", "Finest Pale Ale Golden Promise", "Finest Pale Ale Golden Promise"),  # Simpsons Golden Promise maláta
    "101510": ("Simpsons Malt", "Crystal Extra Dark", "Crystal Extra Dark"),  # Simpsons Crystal Extra Dark maláta
    "101520": ("Simpsons Malt", "Crystal T50", "Crystal T50"),  # Simpsons Crystal T50 maláta
    "101530": ("Simpsons Malt", "DRC", "DRC"),  # Simpsons DRC maláta
}

# Hopline lists "Kihozatal: min 70%" for these three Simpsons crystals, while the Simpsons
# sheet prints no extract. The user decided on 2026-10-09 to keep their extract and potential
# NULL rather than take hopline's flat figure.
IGNORE_HOPLINE_EXTRACT: set[str] = {
    "101510",  # Simpsons Crystal Extra Dark maláta
    "101520",  # Simpsons Crystal T50 maláta
    "101530",  # Simpsons DRC maláta
}

SKIPPED: dict[str, str] = {
    "101000": "BestMalz Heidelberg Extra Pilsner: BestMalz is left out (user decision)",
    "101440": "Sladovna Bohemian Pilsner maláta: Sladovna is left out (user decision)",
    "101450": "Sladovna Whisky maláta: Sladovna is left out (user decision)",
    "101300": "Száraz malátakivonat (DME) 400g: malt extract, left out (user decision)",
    "101330": "Folyékony malátakivonat - világos 1,7kg: malt extract, left out (user decision)",
    "101332": "Folyékony malátakivonat - festő 1,7kg: malt extract, left out (user decision)",
    "101333": "Folyékony malátakivonat - Pale Ale 1,7kg: malt extract, left out (user decision)",
    "101334": "Folyékony malátakivonat - Búza 1,7kg: malt extract, left out (user decision)",
}
