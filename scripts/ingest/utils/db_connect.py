from pathlib import Path
import psycopg

def load_env_dict(levels_up: int = 2) -> dict:
    env_path = Path(__file__).resolve().parents[levels_up] / ".env"

    if not env_path.exists():
        raise FileNotFoundError(f"A keresett .env fájl nem található itt: {env_path}")

    return dict(
        line.split("=", 1)
        for line in env_path.read_text().splitlines()
        if "=" in line and not line.lstrip().startswith("#")
    )


def get_db_connection() -> psycopg.Connection:
    env = load_env_dict()

    conn_kwargs = dict(
        host="localhost",
        port=5432,
        dbname=env["POSTGRES_DB"].strip(),
        user=f"postgres.{env['POOLER_TENANT_ID'].strip()}",
        password=env["POSTGRES_PASSWORD"].strip(),
    )

    return psycopg.connect(**conn_kwargs)
