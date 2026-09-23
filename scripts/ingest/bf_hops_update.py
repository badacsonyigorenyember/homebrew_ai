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

with psycopg.connect(**conn_kwargs) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT recipe_id, position, raw_name FROM corpus.bf_hops;")
        bf_hops = cur.fetchall()

        print(len(bf_hops))

        cur.execute("SELECT recipe_id, position, raw_name FROM corpus.bf_hops;")
        ref_hops = cur.fetchall()

        print(len(bf_hops))

