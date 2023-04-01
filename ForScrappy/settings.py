import os

ROOT_PATH: str = os.path.dirname(os.path.abspath(__file__))


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

LOGIN_URL: str = ''
USERNAME: str = ''
PASSWORD: str = ''


try:
    from local_settings import *  # noqa
    print('>> Loading local local_settings.py file')
except Exception as e:
    print(f'>> No local_settings.py file found ~ `{e}`')

