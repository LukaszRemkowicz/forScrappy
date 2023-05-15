import cgi
import datetime
import shutil
from pathlib import Path
from typing import Optional, Dict

from asgiref.sync import async_to_sync
from celery import shared_task
from requests import Session

from models.entities import DownloadLinksPydantic, DownloadLinkPydantic
from models.models import LinkModel
from repos.db_repo import DownloadLinksRepo
from settings import settings
from utils.utils import DBConnectionHandler


async def update_thread_name_task(thread_name: str, url: str) -> dict:
    """Update object name in database"""

    async with DBConnectionHandler():
        obj: Optional[LinkModel] = await LinkModel.filter(for_clubbers_url=url).first()
        if obj and not obj.name:
            obj.name = thread_name
            await obj.save()
            await obj.refresh_from_db()
            return {"status": "object name updated", "object pk": obj.pk}
        if not obj:
            return {"status": f"No object with url {url}"}
        return {"status": "object name not updated. Name is already set"}


async def download_file_task(
    object_id: int,
    dl_link: str,
    headers: Dict[str, str],
    file_path: Path,
    session: Session = Session(),
) -> Optional[dict]:
    """download file and update object in database"""

    path = Path(settings.custom_download_path) / file_path

    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    new_file_path: Optional[Path]

    with session.get(dl_link, headers=headers, stream=True) as r:
        _, params = cgi.parse_header(r.headers["content-disposition"])
        file_name = params["filename"]
        new_file_path = Path(path) / file_name
        with open(new_file_path, "wb") as f:
            shutil.copyfileobj(r.raw, f)

    async with DBConnectionHandler():
        obj: Optional[DownloadLinksPydantic] = await DownloadLinksRepo().filter(  # type: ignore
            pk=object_id
        )

        if obj and (object_pydantic := obj.__root__):
            object_pydantic[0].downloaded = True
            object_pydantic[0].downloaded_date = datetime.datetime.now()

            object_returned: DownloadLinkPydantic = await DownloadLinksRepo().save(
                object_pydantic[0]
            )
            return {"status": "success", "object pk": object_returned.pk}

        return {
            "status": "Error. No object with this id",
            "object pk": object_id,
            "model": "DownloadLinks",
        }


download_file_async = async_to_sync(download_file_task)
update_thread_name_async = async_to_sync(update_thread_name_task)


@shared_task
def download_file(*args, **kwargs):
    return download_file_async(*args, **kwargs)


@shared_task
def update_thread_name(*args, **kwargs):
    return update_thread_name_async(*args, **kwargs)
