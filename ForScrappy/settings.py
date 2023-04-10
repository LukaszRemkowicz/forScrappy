import os
from dotenv import load_dotenv


ROOT_PATH: str = os.path.dirname(os.path.abspath(__file__))
env_path: str = os.path.join(ROOT_PATH, ".env")
load_dotenv(env_path)


def get_db_credentials() -> dict:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", 5432),
        "user": os.getenv("DB_USERNAME", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres"),
        "database": os.getenv("DB_NAME", "postgres"),
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

LOGIN_URL: str = ""
USERNAME: str = ""
PASSWORD: str = ""


CELERY_broker_url = "redis://redis:6379"
result_backend = "redis://redis:6379"

MANAGERS = ["krakenfiles.com"]

try:
    from local_settings import *  # noqa

    print(">> Loading local local_settings.py file")
except Exception as e:
    print(f">> No local_settings.py file found ~ `{e}`")
