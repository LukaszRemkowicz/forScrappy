import os
from typing import Optional

import pytest
from pytest_docker.plugin import Services
from pytest_mock import MockerFixture

from settings import ROOT_PATH, DB_CONFIG, settings, PARENT_PATH
from utils.exceptions import TestDBWrongCredentialsError


from dotenv import load_dotenv

env_path: str = os.path.join(PARENT_PATH, ".env")

load_dotenv(env_path)


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
