from typing import Optional

from models.models import LinkModel


class LinkModelHandler:
    @staticmethod
    async def get_obj(**kwargs):
        res: Optional[LinkModel] = await LinkModel.get(**kwargs)

        if res:
            return res
