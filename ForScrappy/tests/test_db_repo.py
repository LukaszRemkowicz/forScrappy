import os

import pytest
from tortoise import Tortoise

from utils.utils import DBConnectionHandler


@pytest.mark.asyncio
async def test_db_handler():
    """Test if handler is handling connection to DB"""

    assert not Tortoise.is_connected  # noqa

    async with DBConnectionHandler():
        assert Tortoise.is_connected  # noqa
        assert Tortoise.get_connection("default").database == os.getenv("POSTGRES_TEST_DB_NAME")  # noqa
