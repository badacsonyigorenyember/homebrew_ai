"""Skips tests marked `stack` when Postgres or n8n can't be reached."""

import urllib.request
from functools import lru_cache

import psycopg
import pytest

from loaders.db import _read_env

N8N_HEALTH_URL = "http://localhost:5678/healthz"


@lru_cache(maxsize=1)
def stack_down_reason() -> str | None:
    """None when Postgres and n8n both answer, otherwise which part is down."""
    env = _read_env()
    try:
        psycopg.connect(
            host="localhost",
            port=env["POSTGRES_PORT"],
            dbname=env["POSTGRES_DB"],
            user=f"postgres.{env['POOLER_TENANT_ID']}",
            password=env["POSTGRES_PASSWORD"],
            connect_timeout=3,
        ).close()
    except psycopg.Error:
        return "Postgres"
    try:
        with urllib.request.urlopen(N8N_HEALTH_URL, timeout=3) as response:
            if response.status != 200:
                return "n8n"
    except OSError:
        return "n8n"
    return None


def pytest_collection_modifyitems(config, items):
    stack_items = [item for item in items if item.get_closest_marker("stack")]
    if not stack_items:
        return
    reason = stack_down_reason()
    if reason:
        skip = pytest.mark.skip(reason=f"stack not running: {reason}")
        for item in stack_items:
            item.add_marker(skip)
