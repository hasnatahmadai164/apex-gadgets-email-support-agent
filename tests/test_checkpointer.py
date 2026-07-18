from app.core.checkpointer import _to_psycopg_conn_string


def test_to_psycopg_conn_string_strips_driver_suffix():
    result = _to_psycopg_conn_string("postgresql+psycopg2://user:pass@localhost:5432/db")
    assert result == "postgresql://user:pass@localhost:5432/db"
