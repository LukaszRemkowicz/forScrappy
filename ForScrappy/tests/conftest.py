import logging
import os
import warnings
from typing import List, Optional, Union
from unittest.mock import MagicMock

import pytest
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from dotenv import load_dotenv
from models.entities import DownloadLinkPydantic, LinkModelPydantic
from models.types import MyTortoise
from pytest_docker.plugin import Services
from pytest_mock import MockerFixture
from repos.db_repo import DownloadLinksRepo, LinkModelRepo
from repos.request_repo import ForClubbersScrapper
from settings import DB_CONFIG, PARENT_PATH, ROOT_PATH, settings
from tasks.celery import app
from tortoise import run_async
from use_case.use_case import ForClubUseCase
from utils.exceptions import TestDBWrongCredentialsError
from utils.utils import DBConnectionHandler

env_path: str = os.path.join(PARENT_PATH, ".env")
load_dotenv(env_path)
root_dir: str = ROOT_PATH


def pytest_configure(config):
    logging.getLogger("db_repo").setLevel(logging.CRITICAL)
    logging.getLogger("parser").setLevel(logging.CRITICAL),
    logging.getLogger("request_repo").setLevel(logging.CRITICAL),
    os.environ["TEST"] = "True"


@pytest.fixture(autouse=True)
def ignore_warnings():
    warnings.filterwarnings("ignore", message='Module "__main__" has no models')


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig) -> str:  # noqa
    docker_path: str = os.path.join(ROOT_PATH, "tests", "docker-compose-test.yml")
    return docker_path


@pytest.fixture(scope="session")
def test_db_credentials() -> dict:
    """Returns test database credentials"""

    test_credentials: dict = {
        "NAME": settings.test_db.name,
        "USER": settings.test_db.username,
        "PASSWORD": settings.test_db.password.get_secret_value(),
    }

    return test_credentials


@pytest.fixture(scope="session")
def db_connection(
    docker_services: "Services", docker_ip: str, test_db_credentials: dict
) -> dict:
    """
    :param test_db_credentials:
    :param docker_services: required -> pytest-docker plugin fixture
    :param docker_ip: required -> pytest-docker plugin fixture

    :return dict: db credentials
    """
    user: Optional[str] = test_db_credentials.get("USER")
    password: Optional[str] = test_db_credentials.get("PASSWORD")
    db_name: Optional[str] = test_db_credentials.get("NAME")

    if not user or not db_name or not password:
        raise TestDBWrongCredentialsError()

    port: int = docker_services.port_for("test_db", 5432) or 5450
    credentials: dict = {
        "host": docker_ip,
        "port": port,
        "user": user,
        "password": password,
        "database": db_name,
    }

    return credentials


@pytest.fixture(autouse=True)
def _mock_db_connection(mocker: "MockerFixture", db_connection: dict) -> bool:
    """
    This will alter application database connection settings, once and for all the tests
    in unit tests module.
    :param mocker: pytest-mock plugin fixture
    :param db_connection: connection class
    :return: True upon successful monkey-patching
    """
    mocker.patch("settings.get_db_credentials", db_connection)
    config = DB_CONFIG
    config["connections"]["default"]["credentials"] = db_connection
    mocker.patch("utils.utils.get_db_connections", return_value=config)
    return True


@pytest.fixture
def link_model() -> LinkModelPydantic:
    """Returns LinkModel instance"""
    return LinkModelPydantic(
        for_clubbers_url="https://www.google.com",
        name="123456789",
    )


@pytest.fixture
async def download_link_model() -> DownloadLinkPydantic:
    """Returns DownloadLinks instance"""

    link_model: LinkModelPydantic = LinkModelPydantic(
        for_clubbers_url="https://www.google.com",
        name="123456789",
    )

    # async def handle_db() -> LinkModel:
    async with DBConnectionHandler():
        repo: LinkModelRepo = LinkModelRepo()
        obj = await repo.create(link_model)
        # return obj
    # result: LinkModel = asyncio.get_event_loop().run_until_complete(handle_db())
    result = obj

    return DownloadLinkPydantic(
        link="https://www.google.com",
        link_model=result.__dict__,
        download_link="downloadlink",
        category="test",
    )


@pytest.fixture(scope="function", autouse=True)
def clean_database() -> None:
    """Clean database before each test"""

    async def _clean_database() -> None:
        async with DBConnectionHandler():
            query = 'DELETE FROM "4clubbers_links"'
            await MyTortoise.get_connection("default").execute_query(query)

            query = "DELETE FROM download_links"
            await MyTortoise.get_connection("default").execute_query(query)

    run_async(_clean_database())


def response(string: str) -> requests.Response:
    """Create Response object from given string"""

    mock_response: requests.Response = requests.models.Response()
    mock_response._content = string.encode("iso-8859-2")
    mock_response._text = string  # type: ignore
    mock_response.status_code = 200
    res: requests.Response = requests.Response()
    res.__dict__.update(mock_response.__dict__)

    return res


@pytest.fixture
def forum_response() -> requests.Response:
    """
    Get html content from file and return it as a Response object. File contains links to forum threads
    """

    with open(
        f"{root_dir}/tests/fixtures/responses/forclubbers.html",
        "r",
        encoding="iso-8859-2",
    ) as f:
        file = f.read()

    return response(file)


@pytest.fixture
def forum_response_today() -> requests.Response:
    """
    Get html content from file and return it as a Response object. File contains date with date name
    """

    with open(
        f"{root_dir}/tests/fixtures/responses/forum_date_name.html",
        "r",
        encoding="iso-8859-2",
    ) as f:
        file = f.read()

    return response(file)


@pytest.fixture
def thread_response() -> requests.Response:
    """
    Get html content from file and return it as a Response object. File contains files download links
    """

    with open(
        f"{root_dir}/tests/fixtures/responses/forum_thread.html",
        "r",
        encoding="iso-8859-2",
    ) as f:
        file = f.read()

    return response(file)


@pytest.fixture
def file_name_response() -> requests.Response:
    """
    Get html content from file and return it as a Response object. File contains files download links
    """

    with open(
        f"{root_dir}/tests/fixtures/responses/file_name.html",
        "r",
        encoding="iso-8859-2",
    ) as f:
        file = f.read()

    return response(file)


@pytest.fixture
def kraken_response() -> requests.Response:
    """
    Get html content from file and return it as a Response object.
    """

    with open(
        f"{root_dir}/tests/fixtures/responses/kraken.html", "r", encoding="iso-8859-2"
    ) as f:
        file = f.read()

    return response(file)


@pytest.fixture
def link_model_stub(monkeypatch) -> None:
    class LinkModel:
        def __init__(self, for_clubbers_url):
            self.for_clubbers_url = for_clubbers_url

    async def _mock_get(*args, **kwargs):
        if kwargs.get("for_clubbers_url") == "https://www.google.com":
            return LinkModel("example_url_1")

    monkeypatch.setattr("models.models.LinkModel.get", _mock_get)


def create_tag_element(string: str) -> Union[Tag, NavigableString, None]:
    """Create tag element"""

    soup: BeautifulSoup = BeautifulSoup(string, "html.parser")
    li_tag: Union[Tag, NavigableString, None] = soup.find("li")
    return li_tag


@pytest.fixture
def get_list_of_tags() -> List[Tag]:
    """Return list of tags"""

    tags: list = []

    html_tags: List[str] = [
        '<li><div class="sub-text">Last download date</div><div class="lead-text">30.04.2023</div></li>',
        '<li><div class="sub-text">File size</div><div class="lead-text">13.77 MB</div></li>',
        '<li><div class="sub-text">Upload date</div><div class="lead-text">4.04.2023</div></li>',
    ]

    for element in html_tags:
        tags.append(create_tag_element(element))
    return tags


@pytest.fixture(scope="module")
def celery_app():
    app.conf.update(CELERY_ALWAYS_EAGER=True)
    return app


@pytest.fixture
def mock_download_file_task(mocker: "MockerFixture") -> MagicMock:
    """Mock download_file task properties like cgi, Session or shutil"""
    session_mock = mocker.MagicMock()
    mocker.patch("requests.Session", return_value=session_mock)
    mocker.patch(
        "shutil.copyfileobj", autospec=True, side_effect=lambda fsrc, fdst: None
    )

    response_mock = mocker.MagicMock()
    response_mock.headers = {"content-disposition": 'attachment; filename="file.zip"'}
    response_mock.raw = mocker.MagicMock()

    parse_header_mock = mocker.patch("cgi.parse_header", autospec=True)
    parse_header_mock.return_value = ("attachment", {"filename": "file.zip"})

    mocker.patch("builtins.open", mocker.MagicMock())
    mocker.patch("pathlib.Path.mkdir", mocker.MagicMock())

    session_mock.get.return_value = response_mock

    return session_mock


@pytest.fixture
def use_case() -> ForClubUseCase:
    return ForClubUseCase(
        link_repo=LinkModelRepo,
        download_repo=DownloadLinksRepo,
        repo_scrapper=ForClubbersScrapper,
    )
