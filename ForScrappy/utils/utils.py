import re

from asyncpg import CannotConnectNowError
from tortoise import Tortoise
import validators

from settings import DB_CONFIG, BASE_URL, BASE_URL_PATTERN
from utils.exceptions import DBConnectionError, URLNotValidFormat


def get_db_connections():
    return DB_CONFIG


setattr(Tortoise, "is_connected", False)


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
        """Validate if link has valid url format"""
        if validators.url(self.link) is not True or not self.link.endswith("/"):
            raise URLNotValidFormat(url=self.link)

        pattern = rf'{BASE_URL_PATTERN}'
        match = re.match(pattern, self.link)

        if not match:
            raise URLNotValidFormat(custom_msg=f"Wrong url format. Expected: {BASE_URL}/category/")

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        ...


def validate_category(link: str) -> str:
    """Validate if category is valid"""

    try:
        category = link.split("/")[-2]
    except IndexError:
        raise ValueError("Category not in link")

    if category not in ("trance", "house", "techno"):
        raise ValueError(f"Category `{category}` is not valid")
    return category
