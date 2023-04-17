import asyncio
from typing import Optional

from celery import shared_task

from models.models import LinkModel
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
