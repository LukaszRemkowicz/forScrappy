from asyncpg import CannotConnectNowError
from tortoise import Tortoise
import validators

from settings import DB_CONFIG
from utils.exceptions import DBConnectionError, URLNotValidFormat


def get_db_connections():
    return DB_CONFIG


class DBConnectionHandler:
    """Handler responsible for connection and disconnection to database"""

    async def __aenter__(self) -> None:
        """Open database connection"""
        await Tortoise.init(config=get_db_connections())
        while True:
            retry: int = 0
            try:
                if retry >= 5:
                    raise DBConnectionError()
                await Tortoise.generate_schemas()
                setattr(Tortoise, "is_connected", True)
                break
            except (ConnectionError, CannotConnectNowError):
                retry += 1
                pass

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close database connection"""
        await Tortoise.close_connections()
        setattr(Tortoise, "is_connected", False)


class LinkValidator:
    """Validate if link has valid url format"""

    def __init__(self, link: str):
        self.link: str = link

    async def __aenter__(self) -> None:
        if validators.url(self.link) is not True or not self.link.endswith("/"):
            raise URLNotValidFormat(url=self.link)

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        ...


def validate_category(category: str) -> str:
    """Validate if category is valid"""

    if category not in ("trance", "house", "techno"):
        raise ValueError(f"Category `{category}` is not valid")
    return category
