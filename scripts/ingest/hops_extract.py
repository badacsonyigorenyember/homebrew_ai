import json
import re

from bs4 import BeautifulSoup
import requests
from dataclasses import dataclass, asdict, field
from pathlib import Path
import psycopg

env_path = Path(__file__).resolve().parents[2] / ".env"
env = dict(
    line.split("=", 1)
    for line in env_path.read_text().splitlines()
    if "=" in line and not line.lstrip().startswith("#")
)

conn_kwargs = dict(
    host="localhost",
    port=5432,
    dbname=env["POSTGRES_DB"].strip(),
    user=f"postgres.{env['POOLER_TENANT_ID'].strip()}",
    password=env["POSTGRES_PASSWORD"].strip(),
)

# A brewersfriend.com munkamenet-sutik a szkript melletti .env-ben (nincs verziokezelve).
local_env_path = Path(__file__).resolve().parent / ".env"
bf_cookie = ""
if local_env_path.exists():
    bf_cookie = dict(
        line.split("=", 1)
        for line in local_env_path.read_text().splitlines()
        if "=" in line and not line.lstrip().startswith("#")
    ).get("BF_COOKIE", "").strip()

@dataclass
class Hop:
    name: str
    alfa: float
    use: str
    recipes: int
    link: str
    description: str
    substitutes: str
    beer_styles: list = field(default_factory=list)

@dataclass
class BeerStyle:
    beer_style: dict

fetch_all_from_web_flag = False
fetch_detailed_from_web_flag = True
raw_file_name = "data/raw_hops_data.json"
file_name = "data/hops_data.json"

if fetch_all_from_web_flag:
    # 2. A cURL parancsból kimásolt URL és fejlécek (Headers)
    url = "https://www.brewersfriend.com/hops/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:156.0) Gecko/20100101 Firefox/156.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.brewersfriend.com/',
        'Alt-Used': 'www.brewersfriend.com',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Priority': 'u=0, i',
        'Cookie': bf_cookie
    }

    # 3. Kérés indítása stream=True használatával a socket eléréséhez
    response = requests.get(url, headers=headers, stream=True)

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': 'ui table striped browse-results'})  # vagy soup.find('table', class_='hops-table')

    hops = []

    if table:
        for row in table.find_all('tr'):
            # 3. Kinyerjük az adott soron belüli cellákat (td)
            cells = row.find_all('td')

            # Ha a sor nem üres (pl. a thead-ben nincs td, csak th), feldolgozzuk
            if cells:
                hop_name = cells[0].text.strip()

                hop_link = None
                a_tag = cells[0].find('a')
                if a_tag:
                    hop_link = a_tag['href']

                hop_alfa = float(cells[2].text.strip())
                hop_use = cells[3].text.strip()

                hops.append(Hop(hop_name, hop_alfa, hop_use, 0, hop_link, "", ""))

    # Kapcsolat lezárása
    response.close()


    serializable_data = [asdict(hop) for hop in hops]

    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(serializable_data, file, ensure_ascii=False, indent=4)

with open(file_name, "r", encoding="utf-8") as file:
    loaded_raw_data = json.load(file)

loaded_hops_array = [Hop(**item) for item in loaded_raw_data]

print(len(loaded_hops_array))

main_hops = sorted(loaded_hops_array[:141], key=lambda h: len(h.name), reverse=True)

print(len(main_hops))

# A with-blokk commitol kilépéskor (hiba esetén rollback) és lezárja a kapcsolatot.
with psycopg.connect(**conn_kwargs) as conn:
    with conn.cursor() as cur:

        cur.execute("SELECT raw_name FROM corpus.bf_hops")
        hops_in_db = [row[0] for row in cur.fetchall()]

        print("hops in db: " + str(len(hops_in_db)))
        for loaded_hop in main_hops:
            if loaded_hop.name in hops_in_db:
                loaded_hop.recipes += 1

        main_hops = [hop for hop in main_hops if hop.recipes >= 200]

        print("len")
        print(len(main_hops))

main_hops.sort(key=lambda x: x.name)

if fetch_detailed_from_web_flag:
    for hop in main_hops:
        url = 'https://www.brewersfriend.com' + hop.link
        print(url)

        # A curl parancsból kimásolt fejlécek (Headers)
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:156.0) Gecko/20100101 Firefox/156.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Alt-Used': 'www.brewersfriend.com',
            'Connection': 'keep-alive',
            'Referer': 'https://www.brewersfriend.com/hops/',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=0, i',
            'Cookie': bf_cookie
        }

        # A kérés elküldése
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            print("Sikeres lekérés!")
            html_content = response.text

            soup = BeautifulSoup(html_content, 'html.parser')
            table = soup.find('table', {'class': 'ui table striped browse-results'})

            # Description
            desc_label = soup.find('b', string=re.compile("Description:", re.IGNORECASE))
            description = ""

            if desc_label:
                # A szöveg közvetlenül a <b> tag UTÁN van (next_sibling)
                raw_desc = desc_label.next_sibling
                if raw_desc:
                    # Eltávolítjuk a felesleges idézőjeleket és szóközöket\
                    cleaned_desc = raw_desc.strip().strip('"').strip()
                    description = " ".join(cleaned_desc.split())

            # Substitutes
            sub_label = soup.find('b', string=re.compile("Substitutes:", re.IGNORECASE))
            substitutes_list = []

            if sub_label:
                current_node = sub_label.next_sibling
                while current_node and current_node.name != 'h2' and current_node.name != 'br':
                    if current_node.name == 'a':
                        substitutes_list.append(current_node.text.strip())
                    current_node = current_node.next_sibling

            substitutes = ", ".join(substitutes_list)

            # Most used in
            beer_styles = []
            all_recipe_count = 0
            if table:
                for row in table.find_all('tr'):
                    cells = row.find_all('td')
                    if cells:
                        style_name = cells[0].text.strip()
                        usage_pct = float(cells[2].text.strip().replace('%', ''))
                        recipe_count = float(cells[1].text.strip())

                        all_recipe_count += recipe_count

                        beer_style = {
                            "beer_style": style_name,
                            "usage_pct": usage_pct,
                            "popularity": recipe_count,
                        }

                        beer_styles.append(beer_style)

            filtered_beer_styles = []
            for beer_style in beer_styles:
                beer_style["popularity"] = round(beer_style["popularity"] / all_recipe_count, 2)
                if beer_style["popularity"] > 0.1:
                    filtered_beer_styles.append(beer_style)

            hop.description = description
            hop.substitutes = substitutes
            hop.beer_styles = filtered_beer_styles

        else:
            print(f"Hiba történt: {response.status_code}")
        print(hop)
        response.close()

main_hops.sort(key=lambda x: x.name)
serializable_data = [asdict(hop) for hop in main_hops]

with open(file_name, "w", encoding="utf-8") as file:
    json.dump(serializable_data, file, ensure_ascii=False, indent=4)

with psycopg.connect(**conn_kwargs) as conn:
    with conn.cursor() as cur:
        # cur.execute("TRUNCATE ref.hops RESTART IDENTITY CASCADE;")

        # A `use` (Boil / Dry Hop / Whirlpool / First Wort) hasznalati fazis, nem
        # hop_type (Aroma / Bitter / Dual purpose) -- ezert nem megy a hop_type-ba.
        # Az `alfa` egyetlen ertek, sajat maga also es felso hatara.
        cur.executemany(
            "INSERT INTO ref.hops (name, alpha_acid_pct, description, substitutes, beer_styles) "
            "VALUES (%s, %s, %s, %s, %s)",
            [
                (
                    hop.name,
                    hop.alfa,
                    hop.description or None,
                    [s.strip() for s in hop.substitutes.split(",") if s.strip()],
                    json.dumps(hop.beer_styles)
                )
                for hop in main_hops
            ],
        )

        cur.execute("SELECT count(*) FROM ref.hops")
        print(f"ref.hops: {cur.fetchone()[0]} sor")
