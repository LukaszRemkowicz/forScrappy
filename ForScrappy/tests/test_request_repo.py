import pytest
import requests_mock
from repos.request_repo import ForClubbersScrapper
from requests import Response


@pytest.mark.asyncio
async def test__fetch_data_get() -> None:
    content: dict = {"data": {"name": "city_name"}}
    with requests_mock.Mocker() as mock_request:
        mock_request.get("https://example_url", json=content)
        response = await ForClubbersScrapper()._ForClubbersScrapper__fetch_data_get(  # type: ignore
            "https://example_url"
        )

    assert response.json() == content
    assert isinstance(response, Response)
