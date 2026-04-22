from functools import lru_cache
from os import getenv


class Settings:
    app_name = "AI Commerce API"
    api_version = "v1"
    schema_version = "1.0"
    mysql_host = getenv("MYSQL_HOST", "127.0.0.1")
    mysql_port = int(getenv("MYSQL_PORT", "3306"))
    mysql_database = getenv("MYSQL_DATABASE", "ai_commerce")
    mysql_user = getenv("MYSQL_USER", "querymart")
    mysql_password = getenv("MYSQL_PASSWORD", "querymartpass")


@lru_cache
def get_settings() -> Settings:
    return Settings()
