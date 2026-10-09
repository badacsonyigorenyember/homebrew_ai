"""Database helpers shared by the ref loaders: the connection, source lookup, ingredient upsert."""

from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from loaders.common import name_key

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
NEEDED = ("POSTGRES_DB", "POSTGRES_PASSWORD", "POOLER_TENANT_ID", "POSTGRES_PORT")


def _read_env() -> dict[str, str]:
    """The four connection variables from the root .env; nothing else is read or kept."""
    values = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        key = key.strip()
        if sep and key in NEEDED:
            values[key] = value.strip().strip("'\"")
    missing = [key for key in NEEDED if key not in values]
    if missing:
        raise KeyError(f"missing in {ENV_FILE}: {', '.join(missing)}")
    return values


def connect() -> psycopg.Connection:
    """A connection as postgres.<POOLER_TENANT_ID> through the pooler on localhost."""
    env = _read_env()
    return psycopg.connect(
        host="localhost",
        port=env["POSTGRES_PORT"],
        dbname=env["POSTGRES_DB"],
        user=f"postgres.{env['POOLER_TENANT_ID']}",
        password=env["POSTGRES_PASSWORD"],
        autocommit=False,
    )


def source_id(conn: psycopg.Connection, slug: str) -> int:
    """The ref.source id for a slug; LookupError if there is no such row."""
    row = conn.execute("select id from ref.source where slug = %s", (slug,)).fetchone()
    if row is None:
        raise LookupError(f"no ref.source row with slug {slug!r}")
    return row[0]


def upsert_ingredient(
    conn: psycopg.Connection, kind: str, name: str, producer: str, source_id: int, raw: dict
) -> int:
    """Insert or update a ref.ingredient row on (kind, producer_key, name_key); returns its id.

    Re-running a loader updates the same row instead of adding a duplicate.
    """
    producer = producer or ""
    row = conn.execute(
        """
        insert into ref.ingredient (kind, name, name_key, producer, producer_key, source_id, raw)
        values (%s, %s, %s, %s, %s, %s, %s)
        on conflict (kind, producer_key, name_key) do update
           set name = excluded.name,
               producer = excluded.producer,
               source_id = excluded.source_id,
               raw = excluded.raw
        returning id
        """,
        (kind, name, name_key(name), producer, name_key(producer), source_id, Jsonb(raw)),
    ).fetchone()
    return row[0]
