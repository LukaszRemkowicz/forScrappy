import asyncio
import cgi
import datetime
import shutil
from pathlib import Path
from typing import Optional, Dict

from celery import shared_task
from requests import Session

from models.models import LinkModel, DownloadLinks
from settings import settings
from utils.utils import DBConnectionHandler


@shared_task
def update_thread_name(thread_name: str, url: str) -> dict:
    """Update object name in database"""

    async def do_save_topic_name() -> dict:
        async with DBConnectionHandler():
            obj: Optional[LinkModel] = await LinkModel.filter(
                for_clubbers_url=url
            ).first()
            if obj and not obj.name:
                obj.name = thread_name
                await obj.save()
                await obj.refresh_from_db()
                return {"status": "object name updated", "object pk": obj.pk}
            return {"status": "object name not updated. Name is already set"}

    result: dict = asyncio.get_event_loop().run_until_complete(do_save_topic_name())
    return result


@shared_task
def download_file(
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

    async def handle_response() -> Optional[dict]:
        """Handle DB connection and update object in database"""

        async with DBConnectionHandler():
            obj: Optional[DownloadLinks] = await DownloadLinks.filter(
                pk=object_id
            ).first()

            if obj:
                obj.downloaded = True
                obj.downloaded_date = datetime.datetime.now()

                await obj.save()
                await obj.refresh_from_db()

                response: dict = {"status": "success", "object pk": obj.pk}
                return response
            return None

    result: Optional[dict] = asyncio.get_event_loop().run_until_complete(
        handle_response()
    )
    return result
