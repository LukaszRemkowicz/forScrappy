import pytest
from tortoise import Tortoise

from models.models import DownloadLinks
from repos.db_repo import LinkModelRepo, DownloadLinksRepo
from settings import settings
from utils.utils import DBConnectionHandler


@pytest.mark.asyncio
async def test_db_handler() -> None:
    """Test if handler is handling connection to DB"""

    expected: str = settings.test_db.name

    assert not Tortoise.is_connected  # type: ignore

    async with DBConnectionHandler():
        assert Tortoise.is_connected  # type: ignore
        assert Tortoise.get_connection("default").database == expected  # type: ignore


@pytest.mark.asyncio
async def test_get_or_create_link_model_repo_success(link_model) -> None:
    """Test if get_or_create method is working properly. This case should return True for created flag"""

    repo: LinkModelRepo = LinkModelRepo()
    async with DBConnectionHandler():
        obj, created = await repo.get_or_create(link_model)
        assert obj.for_clubbers_url == link_model.for_clubbers_url
        assert created is True


@pytest.mark.asyncio
async def test_get_or_create_link_model_repo_row_exists(
    link_model, clean_database
) -> None:
    """This case should return False for created flag"""

    repo: LinkModelRepo = LinkModelRepo()
    async with DBConnectionHandler():
        await repo.create(link_model)
        obj, created = await repo.get_or_create(link_model)
        assert obj.for_clubbers_url == link_model.for_clubbers_url
        assert created is False


@pytest.mark.asyncio
async def test_get_or_create_download_links_repo_row_success(
    download_link_model, clean_database
) -> None:
    """This case should return True for created flag"""

    download_link = await download_link_model

    repo: DownloadLinksRepo = DownloadLinksRepo()
    async with DBConnectionHandler():
        obj, created = await repo.get_or_create(download_link)
        assert obj
        assert obj.link == download_link.link
        assert created is True


@pytest.mark.asyncio
async def test_get_or_create_download_links_repo_row_exists(
    download_link_model, clean_database
) -> None:
    """This case should return False for created flag"""
    download_link = await download_link_model

    repo: DownloadLinksRepo = DownloadLinksRepo()
    async with DBConnectionHandler():
        await repo.create(download_link)
        obj, created = await repo.get_or_create(download_link)
        assert obj
        assert obj.link == download_link.link
        assert created is False


@pytest.mark.asyncio
async def test_download_links_create_method(
    download_link_model, clean_database
) -> None:
    """This case should return False for created flag"""

    download_link = await download_link_model
    repo: DownloadLinksRepo = DownloadLinksRepo()

    async with DBConnectionHandler():
        res: DownloadLinks = await repo.create(download_link)
        assert res.link == download_link.link
        assert (
            res.link_model.for_clubbers_url == download_link.link_model.for_clubbers_url
        )
