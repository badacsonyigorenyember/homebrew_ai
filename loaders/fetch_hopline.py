"""Fetch hopline.hu's malt or hop list and product pages -> raw page facts as JSON.

No interpretation happens here: for each product it keeps the SKU, the URL, the name, the spec
text, the spec table, the data block and the long description as shown on the page.
loaders/malts.py, loaders/hops.py and loaders/yeasts.py read the figures out of them.

A listing is paged: osszes-malata, then osszes-malata,2, ,3 ... until a page adds no new SKU.
The two yeast pages render no product links; their list comes from the same page URL with
?action=cat_art_list&ajax=1&ajax_nodesign=1&filter=&page=N, as JSON (ajax_listing).
One request per second; /shop_ajax/ is never fetched (robots.txt disallows it).

Run: python -m loaders.fetch_hopline OUT.json          (malts)
     python -m loaders.fetch_hopline --hops OUT.json   (hops, with hopline's three hop categories)
     python -m loaders.fetch_hopline --yeasts OUT.json (dry and liquid yeasts, with the long description)
"""

import argparse
import html as htmllib
import json
import re
import time
import urllib.request
from datetime import date

LISTING_URL = "https://www.hopline.hu/alapanyagok/malatak/osszes-malata"
HOP_LISTING_URL = "https://www.hopline.hu/alapanyagok/komlok/osszes-komlo"
HOP_CATEGORIES = {
    "aroma": "https://www.hopline.hu/alapanyagok/komlok/aroma-komlok",
    "bittering": "https://www.hopline.hu/alapanyagok/komlok/keseru-komlo",
    "dual": "https://www.hopline.hu/alapanyagok/komlok/kettos-felhasznalasu-komlo",
}
YEAST_LISTINGS = {
    "dry": "https://www.hopline.hu/alapanyagok/elesztok/szaraz-eleszto",
    "liquid": "https://www.hopline.hu/alapanyagok/elesztok/folyekony-eleszto",
}
USER_AGENT = "AI-Homebrew-Assistant hopline loader (personal project; one request per second)"

LINK = re.compile(r'class="product__name-link[^"]*"\s+data-sku="([^"]+)"\s+href="([^"]+)"')
NAME = re.compile(r"<h1 class='artdet__name[^']*'>(.*?)</h1>", re.S)
SCRIPT_OR_STYLE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")

SHORT_DESCRIPTION = "artdet__short-descripton-content"  # hopline's spelling
LONG_DESCRIPTION = "long-description__content"
LABEL = re.compile(r"<strong\b[^>]*>(.*?)</strong>(.*?)(?=<br|</p>|<strong\b)", re.S | re.I)
DIV = re.compile(r"<(/?)div\b", re.I)
TABLE = re.compile(r"<table\b.*?</table>", re.S | re.I)
TH = re.compile(r"<th\b[^>]*>(.*?)</th>", re.S | re.I)
TD = re.compile(r"<td\b[^>]*>(.*?)</td>", re.S | re.I)
MOBILE_HEAD = re.compile(r'<span class="mobile-head">.*?</span>', re.S)
PARAM = re.compile(
    r'class="artdet__param-title"[^>]*>(.*?)</div>.*?class="artdet__param-value"[^>]*>(.*?)</div>',
    re.S,
)


def listing_links(html: str) -> list[tuple[str, str]]:
    """(sku, url) of every product link on a listing page, in page order, no repeats."""
    links = []
    seen = set()
    for sku, url in LINK.findall(html):
        if sku not in seen:
            seen.add(sku)
            links.append((sku, htmllib.unescape(url)))
    return links


def visible_text(html: str) -> str:
    """The page text: scripts and styles dropped, tags removed, entities unescaped, whitespace collapsed."""
    text = SCRIPT_OR_STYLE.sub(" ", html)
    text = TAG.sub(" ", text)
    text = htmllib.unescape(text)
    return " ".join(text.split())


def div_content(html: str, marker: str) -> str | None:
    """The HTML inside the first div whose class contains `marker`, or None when there is none.

    Starts after the opening tag's `>` and walks nested divs to the matching `</div>`.
    """
    start = html.find(marker)
    if start == -1:
        return None
    start = html.index(">", start) + 1
    depth = 0
    for m in DIV.finditer(html, start):
        if m.group(1):  # </div
            if depth == 0:
                return html[start:m.start()]
            depth -= 1
        else:
            depth += 1
    return html[start:]


def short_description(html: str) -> str | None:
    """The HTML inside the product's short-description div, or None when the page has none."""
    return div_content(html, SHORT_DESCRIPTION)


def table_dict(table: str) -> dict[str, str]:
    """A two-row table: header text -> cell text, in order.

    The `mobile-head` spans (a repeated label for narrow screens) are dropped first.
    ValueError when the header and cell counts differ.
    """
    body = MOBILE_HEAD.sub(" ", table)
    headers = [visible_text(th) for th in TH.findall(body)]
    cells = [visible_text(td) for td in TD.findall(body)]
    if len(headers) != len(cells):
        raise ValueError(f"spec table has {len(headers)} headers but {len(cells)} cells: {headers} {cells}")
    return dict(zip(headers, cells))


def spec_table(html: str) -> dict[str, str] | None:
    """The first table of the short description, read with table_dict; None when there is no table."""
    description = short_description(html)
    table = TABLE.search(description) if description else None
    if not table:
        return None
    return table_dict(table.group(0))


def long_description(html: str) -> dict | None:
    """The "Részletek" description: its first table, its `<strong>Label:</strong> value` lines and its text.

    labels maps the strong text without the trailing colon to the text after it, up to the next
    `<br`, `</p>` or `<strong`; labels with no text after them (a bold sentence) are left out.
    None when the page has no long description.
    """
    content = div_content(html, LONG_DESCRIPTION)
    if content is None:
        return None
    table = TABLE.search(content)
    labels = {}
    for label, value in LABEL.findall(content):
        label = visible_text(label).rstrip(":").strip()
        value = visible_text(value).lstrip(":").strip()
        if label and value and label not in labels:
            labels[label] = value
    return {
        "table": table_dict(table.group(0)) if table else None,
        "labels": labels,
        "text": visible_text(content),
    }


def params(html: str) -> dict[str, str]:
    """The data block: every artdet__param-title -> the artdet__param-value after it."""
    return {visible_text(title): visible_text(value) for title, value in PARAM.findall(html)}


def product_page(html: str) -> dict:
    """The product's name, spec text, spec table and data block.

    spec is the text from the first "Főkategória" up to the next "Bővebben"; None when either
    marker is missing.
    """
    m = NAME.search(html)
    name = visible_text(m.group(1)) if m else None

    text = visible_text(html)
    spec = None
    start = text.find("Főkategória")
    if start != -1:
        end = text.find("Bővebben", start)
        if end != -1:
            spec = text[start:end].strip()
    return {"name": name, "spec": spec, "table": spec_table(html), "params": params(html)}


def fetch(url: str) -> str:
    """One GET as this project, then a one-second pause."""
    if "/shop_ajax/" in url:
        raise ValueError(f"refusing to fetch {url}: /shop_ajax/ is disallowed by robots.txt")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
    time.sleep(1)
    return body


def listing(first_url: str) -> list[tuple[str, str]]:
    """(sku, url) of every product on a paged listing: first_url, first_url,2, ,3 ... until a page adds no new SKU."""
    links: list[tuple[str, str]] = []
    seen: set[str] = set()
    page = 1
    while True:
        url = first_url if page == 1 else f"{first_url},{page}"
        new = [(sku, link) for sku, link in listing_links(fetch(url)) if sku not in seen]
        if not new:
            break
        links += new
        seen.update(sku for sku, _ in new)
        page += 1
    print(f"listing {first_url}: {len(links)} products on {page - 1} pages")
    return links


def ajax_links(body: str) -> list[tuple[str, str]]:
    """(sku, url) of every product in one JSON page of a script-loaded listing."""
    return listing_links(json.loads(body)["product_list_content"])


def ajax_listing(category_url: str) -> list[tuple[str, str]]:
    """(sku, url) of every product on a listing whose page loads its products by script.

    GETs category_url?action=cat_art_list&ajax=1&ajax_nodesign=1&filter=&page=N for N = 1, 2 ...
    until a page adds no new SKU (a page past the end repeats the last one).
    """
    links: list[tuple[str, str]] = []
    seen: set[str] = set()
    page = 1
    while True:
        url = category_url + "?action=cat_art_list&ajax=1&ajax_nodesign=1&filter=&page=" + str(page)
        new = [(sku, link) for sku, link in ajax_links(fetch(url)) if sku not in seen]
        if not new:
            break
        links += new
        seen.update(sku for sku, _ in new)
        page += 1
    print(f"listing {category_url}: {len(links)} products on {page - 1} pages")
    return links


def fetch_yeasts(out: str) -> None:
    """Both yeast listings and every product page on them -> out."""
    forms = {form: ajax_listing(url) for form, url in YEAST_LISTINGS.items()}
    products = []
    seen: set[str] = set()
    for links in forms.values():
        for sku, url in links:
            if sku not in seen:
                seen.add(sku)
                html = fetch(url)
                products.append({"sku": sku, "url": url, **product_page(html), "details": long_description(html)})
    result = {
        "fetched": date.today().isoformat(),
        "listings": YEAST_LISTINGS,
        "forms": {form: [sku for sku, _ in links] for form, links in forms.items()},
        "products": products,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(products)} products to {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out", help="JSON file to write")
    kind = parser.add_mutually_exclusive_group()
    kind.add_argument("--hops", action="store_true", help="fetch the hop list instead of the malt list")
    kind.add_argument("--yeasts", action="store_true", help="fetch the dry and liquid yeast lists instead")
    args = parser.parse_args()

    if args.yeasts:
        fetch_yeasts(args.out)
        return

    listing_url = HOP_LISTING_URL if args.hops else LISTING_URL
    links = listing(listing_url)

    products = []
    for sku, url in links:
        products.append({"sku": sku, "url": url, **product_page(fetch(url))})

    result = {"fetched": date.today().isoformat(), "listing": listing_url}
    if args.hops:
        result["categories"] = {purpose: [sku for sku, _ in listing(url)] for purpose, url in HOP_CATEGORIES.items()}
    result["products"] = products
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(products)} products to {args.out}")


if __name__ == "__main__":
    main()
