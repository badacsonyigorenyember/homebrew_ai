import pytest

from loaders.fetch_hopline import listing_links, params, product_page, spec_table


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



def test_listing_links_any_sku():
    html = """
    <a class="product__name-link product_link_normal" data-sku="200020-cs"
       href="https://www.hopline.hu/african-queen-komlo-568">African Queen</a>
    <a class="product__name-link product_link_normal" data-sku="200712-masolata-1"
       href="https://www.hopline.hu/waimea-komlo-30g">Waimea</a>
    """
    assert listing_links(html) == [
        ("200020-cs", "https://www.hopline.hu/african-queen-komlo-568"),
        ("200712-masolata-1", "https://www.hopline.hu/waimea-komlo-30g"),
    ]


def test_spec_table_and_params():
    html = """
    <div class="artdet__short-descripton-content text-justify"><style>table {border: 0}</style>
    <table><tbody>
    <tr><th><span>Alfa-sav</span></th><th><span>B&eacute;ta-sav</span></th>
        <th><span>Co-Humolone</span></th><th><span>Olaj tartalom</span></th></tr>
    <tr><td>5-6 %</td>
        <td><span class="mobile-head">Béta-sav</span><span>2-3 %</span></td>
        <td><span class="mobile-head">Co-Humolone</span><span>29 %</span></td>
        <td><span class="mobile-head">Olaj tartalom</span><span>0,85 %</span></td></tr>
    </tbody></table>
    <p><strong>Felhasználás:</strong> Ale</p></div>
    <div id="artdet__long-description"><table><tr><th>Other</th></tr><tr><td>x</td></tr></table></div>
    <div class="artdet__param-title">
        Évjárat
    </div>
    <div class="data__item-value"><div class="artdet__param-value">
        2025
    </div></div>
    <div class="artdet__param-title">Ország</div>
    <div class="data__item-value"><div class="artdet__param-value"> USA </div></div>
    """
    assert spec_table(html) == {
        "Alfa-sav": "5-6 %",
        "Béta-sav": "2-3 %",
        "Co-Humolone": "29 %",
        "Olaj tartalom": "0,85 %",
    }
    assert params(html) == {"Évjárat": "2025", "Ország": "USA"}

    no_table = '<div class="artdet__short-descripton-content"><p>x</p></div><table><tr><th>A</th></tr></table>'
    assert spec_table(no_table) is None

    uneven = '<div class="artdet__short-descripton-content"><table><tr><th>A</th><th>B</th></tr><tr><td>1</td></tr></table></div>'
    with pytest.raises(ValueError):
        spec_table(uneven)
