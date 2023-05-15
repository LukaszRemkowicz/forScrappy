from pathlib import Path
from typing import Dict, Awaitable, Optional
from unittest.mock import MagicMock

import pytest
from celery import Celery

from models.entities import (
    DownloadLinkPydantic,
    LinkModelPydantic,
)

from repos.db_repo import LinkModelRepo, DownloadLinksRepo
from tasks.tasks import update_thread_name_task, download_file_task
from utils.utils import DBConnectionHandler


@pytest.mark.asyncio
async def test_update_thread_name_no_obj(celery_app: Celery) -> None:
    """Test celery task update_thread_name with no obj"""

    expected: Dict[str, str] = {"status": "No object with url example"}
    res: Dict = await update_thread_name_task("example", "example")

    assert res == expected


@pytest.mark.asyncio
async def test_update_thread_name(
    celery_app: Celery, link_model: LinkModelPydantic
) -> None:
    """Test celery task update_thread_name with no obj"""

    repo: LinkModelRepo = LinkModelRepo()

    async with DBConnectionHandler():
        res_object: LinkModelPydantic | None = await repo.create(link_model)
        if not res_object:
            assert False
        res_object.name = ""
        await repo.update_fields(res_object, name="")

    expected: Dict = {
        "status": "object name updated",
        "object pk": res_object.pk,
    }
    res: Dict = await update_thread_name_task("example", res_object.for_clubbers_url)

    assert res == expected


@pytest.mark.asyncio
async def test_update_thread_name_set(
    celery_app: Celery, link_model: LinkModelPydantic
) -> None:
    """Test celery task update_thread_name with name already set"""

    repo: LinkModelRepo = LinkModelRepo()

    async with DBConnectionHandler():
        res_object: LinkModelPydantic = await repo.create(link_model)
        if not res_object:
            assert False

    expected: Dict[str, str] = {
        "status": "object name not updated. Name is already set"
    }
    res: Dict[str, str] = await update_thread_name_task(
        thread_name="example", url=res_object.for_clubbers_url
    )

    assert res == expected


@pytest.mark.asyncio
async def test_download_file_no_obj(
    celery_app: Celery, mock_download_file_task: MagicMock
) -> None:
    """Test celery task download_file. No object case"""

    expected_response: Dict = {
        "status": "Error. No object with this id",
        "object pk": 1,
        "model": "DownloadLinks",
    }
    session_mock: MagicMock = mock_download_file_task

    res: Optional[Dict] = await download_file_task(
        object_id=1,
        dl_link="https://example.com/file.zip",
        headers={},
        file_path=Path("/path/to/save"),
        session=session_mock,
    )
    assert res == expected_response


@pytest.mark.asyncio
async def test_download_file(
    celery_app: Celery,
    mock_download_file_task: MagicMock,
    download_link_model: Awaitable,
) -> None:
    """Test celery task download_file. Object exists case"""

    session_mock: MagicMock = mock_download_file_task
    download_link: DownloadLinkPydantic = await download_link_model
    repo: DownloadLinksRepo = DownloadLinksRepo()

    async with DBConnectionHandler():
        res_object: DownloadLinkPydantic = await repo.create(download_link)

    expected_response: Dict = {
        "status": "success",
        "object pk": res_object.pk,
    }

    res: Optional[Dict[str, str]] = await download_file_task(
        object_id=1,
        dl_link="https://example.com/file.zip",
        headers={},
        file_path=Path("/path/to/save"),
        session=session_mock,
    )
    assert res == expected_response
