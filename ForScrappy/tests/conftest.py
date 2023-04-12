import os

import pytest
from pytest_docker.plugin import Services
from pytest_mock import MockerFixture

from settings import ROOT_PATH, DB_CONFIG
from utils.exceptions import TestDBWrongCredentialsError


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):  # noqa
    docker_path: str = os.path.join(
        ROOT_PATH, "tests", "docker-compose-test.yml"
    )
    return docker_path


@pytest.fixture(scope="session")
def test_db_credentials():
    """Returns test database credentials"""

    test_credentials: dict = {
        "NAME": os.getenv("POSTGRES_TEST_DB_NAME", "test_db"),
        "USER": os.getenv("POSTGRES_TEST_USER", "postgres"),
        "PASSWORD": os.getenv("POSTGRES_TEST_PASSWORD", "postgres")
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
    user: str = test_db_credentials.get("USER")
    password: str = test_db_credentials.get("PASSWORD")
    db_name: str = test_db_credentials.get("NAME")

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
