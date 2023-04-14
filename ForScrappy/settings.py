import os

from pydantic import BaseSettings, SecretStr

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
PARENT_PATH = os.path.dirname(ROOT_PATH)


class CelerySettings(BaseSettings):
    """Celery settings"""

    broker_url: str
    result_backend: str


class LocalRepoSettings(BaseSettings):
    """Local settings"""

    login_url: str
    username: str
    password: SecretStr
    base_url: str
    base_url_pattern: str


class DatabaseSettings(BaseSettings):
    """Database settings"""

    host: str = "localhost"
    port: int = 5432
    username: str = "postgres"
    password: SecretStr = SecretStr("postgres")
    name: str = "postgres"


class TestDatabaseSettings(BaseSettings):
    """Database settings"""

    username: str
    password: SecretStr
    name: str


class Settings(BaseSettings):
    """General settings for application"""

    celery: CelerySettings
    local: LocalRepoSettings
    db: DatabaseSettings
    test_db: TestDatabaseSettings

    class Config:
        env_file = os.path.join(PARENT_PATH, ".env")
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


settings = Settings()


def get_db_credentials() -> dict:
    return {
        "host": settings.db.host,
        "port": settings.db.port,
        "user": settings.db.username,
        "password": settings.db.password.get_secret_value(),
        "database": settings.db.name,
    }


DB_CONFIG: dict = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": get_db_credentials(),
        },
    },
    "apps": {
        "models": {
            "models": ["__main__", "models.models", "aerich.models"],
            "default_connection": "default",
        },
    },
    "default_connection": "default",
}


MANAGERS = ["krakenfiles.com"]


CELERY_broker_url = settings.celery.broker_url
result_backend = settings.celery.result_backend
