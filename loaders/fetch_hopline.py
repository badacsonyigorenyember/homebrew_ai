"""Fetch hopline.hu's malt list and product pages -> raw page facts as JSON.

No interpretation happens here: for each product it keeps the SKU, the URL, the name and the
spec text as shown on the page. loaders/malts.py reads the figures out of the spec text.

The listing is paged: osszes-malata, then osszes-malata,2, ,3 ... until a page adds no new SKU.
One request per second; /shop_ajax/ is never fetched (robots.txt disallows it).

Run: python -m loaders.fetch_hopline OUT.json
"""

import argparse
import html as htmllib
import json
import re
import time
import urllib.request
from datetime import date

LISTING_URL = "https://www.hopline.hu/alapanyagok/malatak/osszes-malata"
USER_AGENT = "AI-Homebrew-Assistant malt loader (personal project; one request per second)"

LINK = re.compile(r'class="product__name-link[^"]*"\s+data-sku="(\d+)"\s+href="([^"]+)"')
NAME = re.compile(r"<h1 class='artdet__name[^']*'>(.*?)</h1>", re.S)
SCRIPT_OR_STYLE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")


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


def product_page(html: str) -> dict:
    """The product's name and its spec text, from the first "Főkategória" up to the next "Bővebben".

    spec is None when either marker is missing.
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
    return {"name": name, "spec": spec}


def fetch(url: str) -> str:
    """One GET as this project, then a one-second pause."""
    if "/shop_ajax/" in url:
        raise ValueError(f"refusing to fetch {url}: /shop_ajax/ is disallowed by robots.txt")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
    time.sleep(1)
    return body


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out", help="JSON file to write")
    args = parser.parse_args()

    links: list[tuple[str, str]] = []
    seen: set[str] = set()
    page = 1
    while True:
        url = LISTING_URL if page == 1 else f"{LISTING_URL},{page}"
        new = [(sku, link) for sku, link in listing_links(fetch(url)) if sku not in seen]
        if not new:
            break
        links += new
        seen.update(sku for sku, _ in new)
        page += 1
    print(f"listing: {len(links)} products on {page - 1} pages")

    products = []
    for sku, url in links:
        facts = product_page(fetch(url))
        products.append({"sku": sku, "url": url, "name": facts["name"], "spec": facts["spec"]})

    result = {"fetched": date.today().isoformat(), "listing": LISTING_URL, "products": products}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(products)} products to {args.out}")


if __name__ == "__main__":
    main()
