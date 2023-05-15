import re
from datetime import datetime
from logging import Logger
from time import sleep
from typing import Dict

from asyncpg import CannotConnectNowError

# from tortoise import Tortoise
import validators

from logger import get_module_logger
from models.types import MyTortoise
from settings import DB_CONFIG, settings
from utils.exceptions import DBConnectionError, URLNotValidFormat
from utils.schemas import DB_CONFIG_SCHEMA

logger: Logger = get_module_logger("utils")


def get_db_connections():
    return DB_CONFIG


# setattr(Tortoise, "is_connected", False)


def validate_credentials(config: dict) -> None:
    DB_CONFIG_SCHEMA.validate_schema(config)


class DBConnectionHandler:
    """Handler responsible for connection and disconnection to database"""

    async def __aenter__(self) -> None:
        """Open database connection"""

        config: Dict = get_db_connections()

        await MyTortoise.init(config=config)

        retry: int = 0

        while True:
            try:
                validate_credentials(DB_CONFIG)
                await MyTortoise.generate_schemas()
                # setattr(Tortoise, "is_connected", True)
                MyTortoise.is_connected = True
                break
            except (ConnectionError, CannotConnectNowError):
                retry += 1
                logger.critical(f"Cannot connect to database. Retrying...{retry}")
                sleep(1)
                if retry >= 5:
                    raise DBConnectionError(
                        f"Cannot connect to database. Tried {retry} times. Closing..."
                        f"Check out your credentials in .env file. Actual credentials: "
                        f"{config['connections']['default']['credentials']}"
                    )
                pass

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close database connection"""
        # await Tortoise.close_connections()
        # setattr(Tortoise, "is_connected", False)
        await MyTortoise.close_connections()
        MyTortoise.is_connected = False


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


def get_folder_name_from_date(date: datetime) -> str:
    """Get folder name from date"""
    return f"{date.year}/{date.month}/"
