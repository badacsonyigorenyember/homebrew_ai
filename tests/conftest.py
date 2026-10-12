"""Skips tests marked `stack` when Postgres or n8n can't be reached."""

import urllib.request
from functools import lru_cache

import psycopg
import pytest

from loaders.db import connect

N8N_HEALTH_URL = "http://localhost:5678/healthz"


@lru_cache(maxsize=1)
def stack_down_reason() -> str | None:
    """None when Postgres and n8n both answer, otherwise which part is down."""
    try:
        connect(connect_timeout=3).close()
    except (psycopg.Error, OSError, KeyError):  # an unreadable env file or a missing key counts too
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
