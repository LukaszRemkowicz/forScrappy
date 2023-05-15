import json
from datetime import datetime
from typing import Optional
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup
from pytest_mock import MockerFixture
import requests_mock

from models.entities import LinksModelPydantic, DownloadLinksPydantic
from repos.parser_repo import ForClubbersParser, KrakenParser
from settings import settings
from utils.exceptions import LinkPostFailure


@pytest.mark.asyncio
async def test_forum_parser(forum_response, clean_database) -> None:
    """Test if forum parser is working properly and returns proper links"""

    expected_link: str = "https://example.com/example_category/example_title1.html"

    result: LinksModelPydantic = await ForClubbersParser.parse_forum(
        forum_response, "example_category"
    )
    assert isinstance(result, LinksModelPydantic)
    assert len(result.__root__) == 11
    assert result.__root__[0].for_clubbers_url == expected_link


@pytest.mark.asyncio
async def test_parse_date(forum_response, clean_database) -> None:
    """Test if parse_date is working properly"""

    expected_date: datetime = datetime.strptime("10-10-2020, 08:11", "%d-%m-%Y, %H:%M")
    result: Optional[datetime] = ForClubbersParser.parse_date(forum_response)

    assert isinstance(result, datetime)
    assert result == expected_date


@pytest.mark.asyncio
async def test_parse_date_today(forum_response_today, clean_database) -> None:
    """Test if parse_date is working properly for today's date if tag has no date, just day name"""

    expected_date: datetime = datetime.strptime(
        f"{datetime.now().strftime('%d-%m-%Y')}, 08:11", "%d-%m-%Y, %H:%M"
    )
    result: Optional[datetime] = ForClubbersParser.parse_date(forum_response_today)

    assert isinstance(result, datetime)
    assert result == expected_date


@pytest.mark.asyncio
async def test_parse_download_links(
    thread_response, link_model_stub, mocker: "MockerFixture", link_model
) -> None:
    """Test if download link parser works properly"""

    mock_task: MagicMock = MagicMock()
    mocker.patch("tasks.tasks.update_thread_name", return_value=mock_task)

    result: DownloadLinksPydantic = await ForClubbersParser.parse_download_links(
        thread_response, link_model.for_clubbers_url, "example_category"
    )

    assert isinstance(result, DownloadLinksPydantic)
    assert len(result.__root__) == 3
    assert result.__root__[0].category == "example_category"
    assert result.__root__[0].link_model.for_clubbers_url == "example_url_1"


@pytest.mark.asyncio
async def test_kraken_parse_date(get_list_of_tags) -> None:
    """Test if parse_date is working properly for kraken"""
    expected: str = "04.04.2023"
    result: Optional[datetime] = await KrakenParser.parse_date(get_list_of_tags)
    assert isinstance(result, datetime)
    assert result.strftime("%d.%m.%Y") == expected


@pytest.mark.asyncio
async def test_kraken_parse_name(file_name_response) -> None:
    """Test if parse_date is working properly for kraken"""
    expected: str = "Example Name"

    soup: BeautifulSoup = BeautifulSoup(file_name_response.text, "lxml")
    result: Optional[str] = await KrakenParser().parse_name(soup)
    assert isinstance(result, str)
    assert result == expected


@pytest.mark.asyncio
async def test_kraken_main_parser(kraken_response) -> None:
    """Test if main parser is working properly for kraken. Expected result is a dictionary"""

    kraken_post_response: str = json.dumps({"url": "example_url"})
    with requests_mock.Mocker() as mock_request:
        mock_request.get("https://example_url", text=kraken_response.text)
        mock_request.post(
            f"{settings.kraken_base_url}/download/example_hash",
            text=kraken_post_response,
        )

        response: Optional[dict] = await KrakenParser().get_download_link(
            "https://example_url"
        )

        assert isinstance(response, dict)
        assert response["dl_link"] == "example_url"


@pytest.mark.asyncio
async def test_kraken_main_parser_no_url(kraken_response) -> None:
    """Test kraken main parser. Expected LinkPostFailure exception"""

    kraken_post_response: str = json.dumps({"no_link": "example_url"})
    with requests_mock.Mocker() as mock_request:
        mock_request.get("https://example_url", text=kraken_response.text)
        mock_request.post(
            f"{settings.kraken_base_url}/download/example_hash",
            text=kraken_post_response,
        )

        with pytest.raises(LinkPostFailure):
            await KrakenParser().get_download_link("https://example_url")
