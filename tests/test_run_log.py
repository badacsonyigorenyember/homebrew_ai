"""The run log: a run can start before its brief, and every failed step says why."""

import psycopg
import pytest

from loaders.db import connect

pytestmark = pytest.mark.stack


@pytest.fixture
def conn():
    """A connection whose work is always rolled back."""
    connection = connect()
    yield connection
    connection.rollback()
    connection.close()


def _new_run(conn) -> int:
    return conn.execute(
        "insert into app.run (model, eval_id) values ('m', 'b01') returning id"
    ).fetchone()[0]


def test_run_starts_without_brief(conn):
    assert _new_run(conn) > 0


def test_failed_step_needs_error(conn):
    run_id = _new_run(conn)
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            "insert into app.run_step (run_id, step, input, ok, ms) values (%s, 1, '{}', false, 0)",
            (run_id,),
        )


def test_passed_step_has_no_error(conn):
    run_id = _new_run(conn)
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            "insert into app.run_step (run_id, step, input, ok, ms, error)"
            " values (%s, 1, '{}', true, 0, 'boom')",
            (run_id,),
        )


def test_jsonschema_errors_available(conn):
    errors = conn.execute(
        "select extensions.jsonschema_validation_errors('{\"type\":\"object\"}', '1')"
    ).fetchone()[0]
    assert len(errors) == 1
