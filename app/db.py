from collections.abc import Iterator
from contextlib import contextmanager
import json
from typing import Any

import mysql.connector
from mysql.connector import MySQLConnection

from app.config import get_settings


@contextmanager
def get_connection() -> Iterator[MySQLConnection]:
    settings = get_settings()
    conn = mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        database=settings.mysql_database,
        user=settings.mysql_user,
        password=settings.mysql_password,
        autocommit=False,
    )
    try:
        yield conn
    finally:
        conn.close()


def decode_json_field(value: Any, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode()
    if isinstance(value, str):
        return json.loads(value)
    return value
