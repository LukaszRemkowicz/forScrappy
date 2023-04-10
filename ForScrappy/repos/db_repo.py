from typing import List, Optional, Tuple

from models.entities import LinkModelPydantic, DownloadLinkPydantic
from models.models import LinkModel, DownloadLinks

from logger import ColoredLogger, get_module_logger

logger: ColoredLogger = get_module_logger("db_repo")


class BaseRepo:
    model = None

    async def filter(self, **kwargs) -> List[Optional[LinkModel | DownloadLinks]]:
        """Filter by given params."""
        return await self.model.filter(**kwargs)

    async def create(
        self, obj: DownloadLinkPydantic | LinkModelPydantic
    ) -> Optional[DownloadLinks | LinkModel]:
        """Save LinkModelPydantic instance to database"""
        res: DownloadLinks | LinkModel = await self.model.create(**obj.dict())  # noqa
        logger.info(f"Object with id {res.pk} created")

        return res

    async def save(self, **kwargs) -> LinkModel:
        """Save LinkModelPydantic instance to database"""

        model: DownloadLinks | LinkModel = self.model(**kwargs)
        res: DownloadLinks | LinkModel = await model.save()  # noqa
        logger.info(f"Object with id {res.pk} created")

        return res

    async def all(self) -> List[DownloadLinks | LinkModel]:
        """Get all model instances from DB"""
        return await self.model.all()

    async def get_or_create(
        self, obj: DownloadLinkPydantic | LinkModelPydantic
    ) -> Tuple[LinkModelPydantic | DownloadLinkPydantic, bool]:
        raise NotImplementedError


class LinkRepo(BaseRepo):
    model = LinkModel

    async def get_or_create(
        self, obj: LinkModelPydantic
    ) -> Tuple[LinkModelPydantic, bool]:
        exists = await self.filter(for_clubbers_url=obj.for_clubbers_url)

        if exists:
            return_object: LinkModelPydantic = LinkModelPydantic(**exists[0].__dict__)
            created: bool = False
        else:
            object_created: LinkModel = await self.create(obj)
            return_object: LinkModelPydantic = LinkModelPydantic(
                **object_created.__dict__
            )
            created: bool = True

        return return_object, created


class DownloadRepo(BaseRepo):
    model = DownloadLinks

    async def get_or_create(
        self, obj: DownloadLinkPydantic
    ) -> Tuple[DownloadLinkPydantic, bool]:
        exists = await self.filter(link=obj.link)

        if exists:

            instance = (
                await self.model.filter(link=obj.link)
                .prefetch_related("link_model")
                .first()
            )
            instance_dict = await instance.to_dict()
            return_object: DownloadLinkPydantic = DownloadLinkPydantic(**instance_dict)
            created: bool = False
        else:

            link_model_data = obj.dict().pop("link_model")
            link_model, _ = await LinkModel.get_or_create(**link_model_data)
            obj.link_model = link_model
            object_created = await self.create(obj)
            object_dict = await object_created.to_dict()

            return_object: DownloadLinkPydantic = DownloadLinkPydantic(**object_dict)
            created: bool = True

        return return_object, created
