from functools import lru_cache

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection
from psycopg.rows import dict_row

from app.core.config import get_settings


def _to_psycopg_conn_string(sqlalchemy_url: str) -> str:
    return (
    sqlalchemy_url
    .replace("postgresql+psycopg://", "postgresql://")
    .replace("postgresql+psycopg2://", "postgresql://")
)


@lru_cache
def get_checkpointer() -> PostgresSaver:
    conn_string = _to_psycopg_conn_string(get_settings().database_url)
    connection = Connection.connect(conn_string, autocommit=True, row_factory=dict_row)
    checkpointer = PostgresSaver(connection)
    checkpointer.setup()
    return checkpointer
