import os
import re
from pathlib import Path

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


class EmailSettings(BaseSettings):
    """Email settings"""

    host: str
    port: int
    username: str
    password: SecretStr
    use_tls: bool = True
    from_: str
    to_: str


class NginxSettings(BaseSettings):
    """Nginx settings"""

    base_url: str


class SentrySettings(BaseSettings):
    """Sentry settings"""

    dsn: str


class Settings(BaseSettings):
    """General settings for application"""

    celery: CelerySettings
    local: LocalRepoSettings
    db: DatabaseSettings
    test_db: TestDatabaseSettings
    download_path: str
    kraken_base_url: str
    email: EmailSettings
    nginx: NginxSettings
    sentry: SentrySettings
    environment: str = "local"

    class Config:
        env_file = os.path.join(PARENT_PATH, ".env")
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"

    @property
    def custom_download_path(self) -> str:
        if ROOT_PATH:
            path: Path = Path(ROOT_PATH) / self.download_path
            if not path.exists():
                path.mkdir()

            return str(path)
        else:
            return self.download_path


settings: Settings = Settings()

if os.environ.get("ENVIRONMENT") == "local":
    pattern = r"(?<=redis://)[^:]+(?=:)"
    replaced = re.sub(pattern, "localhost", settings.celery.broker_url)

    settings.celery.broker_url = replaced
    settings.celery.result_backend = replaced
    settings.db.host = "localhost"
    settings.db.port = 5432


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


MANAGERS = ["krakenfiles"]


CELERY_broker_url = settings.celery.broker_url
result_backend = settings.celery.result_backend
CELERY_TIMEZONE = "Europe/Warsaw"
