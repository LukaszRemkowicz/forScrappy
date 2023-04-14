import re
from time import sleep

from asyncpg import CannotConnectNowError
from tortoise import Tortoise
import validators

from logger import ColoredLogger, get_module_logger
from settings import DB_CONFIG, settings
from utils.exceptions import DBConnectionError, URLNotValidFormat


logger: ColoredLogger = get_module_logger("utils")


def get_db_connections():
    return DB_CONFIG


setattr(Tortoise, "is_connected", False)


class DBConnectionHandler:
    """Handler responsible for connection and disconnection to database"""

    async def __aenter__(self) -> None:
        """Open database connection"""
        await Tortoise.init(config=get_db_connections())

        retry: int = 0

        while True:
            try:
                await Tortoise.generate_schemas()
                setattr(Tortoise, "is_connected", True)
                break
            except (ConnectionError, CannotConnectNowError):
                retry += 1
                logger.critical(f"Cannot connect to database. Retrying...{retry}")
                sleep(1)
                if retry >= 5:
                    raise DBConnectionError()
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

        pattern = rf"{settings.local.base_url_pattern}"
        match = re.match(pattern, self.link)

        if not match:
            raise URLNotValidFormat(
                custom_msg=f"Wrong url format. Expected: {settings.local.base_url}/category/"
            )

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
