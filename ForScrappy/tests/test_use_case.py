import random
from copy import deepcopy
from typing import Awaitable, Callable, List, Optional, Type
from unittest.mock import MagicMock

import pytest
from models import DownloadLinkPydantic
from models.entities import DownloadLinksPydantic, LinkModelPydantic, LinksModelPydantic
from pytest_mock import MockerFixture
from repos.db_repo import DownloadLinksRepo, LinkModelRepo
from repos.parser_repo import (
    ForClubbersParser,
    KrakenParser,
    ParserType,
    ZippyshareParser,
)
from requests import Response
from use_case.use_case import ForClubUseCase
from utils.utils import DBConnectionHandler


@pytest.mark.asyncio
async def test_choose_download_manager() -> None:
    """Test choose_download_manager method with different names"""
    res: Type[ParserType] = await ForClubUseCase.choose_download_manager(
        "https://examplekrakenfiles.com"
    )
    expected: Type[KrakenParser] = KrakenParser

    assert res == expected

    res2: Type[ParserType] = await ForClubUseCase.choose_download_manager(
        "https://examplezippyshare.com"
    )
    expected2: Type[ZippyshareParser] = ZippyshareParser

    assert res2 == expected2


@pytest.mark.asyncio
async def test_choose_download_manager_exception() -> None:
    """Test choose_download_manager method with a not existed manager name"""
    with pytest.raises(ValueError):
        await ForClubUseCase.choose_download_manager("https://example.com")


@pytest.mark.asyncio
async def test_get_links_with_errors(
    use_case: ForClubUseCase, download_link_model: Awaitable, clean_database: Callable
) -> None:
    """Test get_links_with_errors method. As a result we should get only links with error=True attribute"""

    repo: DownloadLinksRepo = DownloadLinksRepo()
    async with DBConnectionHandler():
        download_link: DownloadLinkPydantic = await download_link_model
        download_link.error = True

        second_link: DownloadLinkPydantic = deepcopy(download_link)
        second_link.link = "https://example2.com"
        second_link.error = False

        await repo.create(download_link)
        await repo.create(second_link)

        res: Optional[DownloadLinksPydantic] = await use_case.get_links_with_errors()

        assert isinstance(res, DownloadLinksPydantic)
        assert isinstance(res.__root__, List)
        assert len(res.__root__) == 1
        assert res.__root__[0].link == download_link.link


@pytest.mark.asyncio
async def test_get_links(
    use_case: ForClubUseCase, download_link_model: Awaitable, clean_database: Callable
) -> None:
    """Test get_links method. As a result we should get only links with downloaded=False attribute"""

    repo: DownloadLinksRepo = DownloadLinksRepo()
    async with DBConnectionHandler():
        download_link: DownloadLinkPydantic = await download_link_model
        download_link.downloaded = True

        second_link: DownloadLinkPydantic = deepcopy(download_link)
        second_link.link = "https://example2.com"
        second_link.downloaded = False

        await repo.create(download_link)
        await repo.create(second_link)

        res: Optional[DownloadLinksPydantic] = await use_case.get_links()

        assert isinstance(res, DownloadLinksPydantic)
        assert isinstance(res.__root__, List)
        assert len(res.__root__) == 1
        assert res.__root__[0].link == second_link.link


@pytest.mark.asyncio
async def test_get_files_link_from_forum(
    forum_response: Response,
    clean_database: Callable,
    mocker: "MockerFixture",
    use_case: ForClubUseCase,
    thread_response: Response,
    link_model: LinkModelPydantic,
    link_model_stub: Callable,
) -> None:
    """Test get links method from use case. Test if objects are saved in database."""

    async with DBConnectionHandler():
        mock_task: MagicMock = MagicMock()
        download_link_res: DownloadLinksPydantic
        download_link_res, _ = await ForClubbersParser.parse_download_links(
            thread_response, link_model.for_clubbers_url, "example_category"
        )
        result: LinksModelPydantic = await ForClubbersParser.parse_forum(
            forum_response, "example_category"
        )

        for element in result.__root__:
            element.for_clubbers_url = random.choice(
                download_link_res.__root__
            ).link_model.for_clubbers_url

        mocker.patch("tasks.tasks.update_thread_name", return_value=mock_task)
        mocker.patch(
            "repos.request_repo.ForClubbersScrapper.get_forum_urls", return_value=result
        )
        mocker.patch(
            "repos.request_repo.ForClubbersScrapper.get_download_links",
            return_value=download_link_res,
        )

        await use_case.get_files_link_from_forum("example_category", "example_link")

        download_link_filtered: DownloadLinksPydantic = await DownloadLinksRepo().all()
        link_models_filtered: LinksModelPydantic = await LinkModelRepo().all()

        assert len(data := link_models_filtered.__root__) == 1
        assert len(download_link_filtered.__root__) == len(download_link_res.__root__)
        assert data[0].for_clubbers_url == result.__root__[0].for_clubbers_url
