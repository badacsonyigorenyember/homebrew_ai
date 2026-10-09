from loaders.fetch_hopline import listing_links, product_page


def test_listing_links():
    html = """
    <a class="product__name-link product_link_normal" data-sku="100160"
       href="https://www.hopline.hu/viking-coffee-malata-1kg">Viking Coffee</a>
    <a class="product__name-link product_link_normal" data-sku="101290"
       href="https://www.hopline.hu/simpsons-marris-otter">Simpsons Marris Otter</a>
    <a class="product__name-link product_link_normal" data-sku="100160"
       href="https://www.hopline.hu/viking-coffee-malata-1kg">Viking Coffee</a>
    """
    assert listing_links(html) == [
        ("100160", "https://www.hopline.hu/viking-coffee-malata-1kg"),
        ("101290", "https://www.hopline.hu/simpsons-marris-otter"),
    ]


def test_product_page():
    html = """
    <html><head><style>.x { color: red }</style></head><body>
    <h1 class='artdet__name x'>Simpsons Crystal T50 maláta</h1>
    <script>var spec = "EBC: 1";</script>
    <div>F&#337;kategória</div> <a>Feltöltött termékek</a>
    <p>Simpsons Crystal T50 maláta</p>
    <p>EBC: 139 - 154</p><script>var x = "EBC: 1";</script>
    <p>Ízjegyek: karamell</p>
    <span>Bővebben</span><p>Bővebben más</p>
    </body></html>
    """
    page = product_page(html)
    assert page["name"] == "Simpsons Crystal T50 maláta"
    assert page["spec"].startswith("Főkategória")
    assert "EBC: 139 - 154" in page["spec"]
    assert "EBC: 1\"" not in page["spec"]
    assert "var " not in page["spec"]
    assert "Bővebben" not in page["spec"]

