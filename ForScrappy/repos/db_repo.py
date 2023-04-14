from typing import List, Optional, Tuple, Type

from models.entities import LinkModelPydantic, DownloadLinkPydantic
from models.models import LinkModel, DownloadLinks

from logger import ColoredLogger, get_module_logger

logger: ColoredLogger = get_module_logger("db_repo")


class BaseRepo:
    model: Optional[Type[LinkModel | DownloadLinks]] = None

    async def filter(self, **kwargs) -> List[Optional[LinkModel | DownloadLinks]]:
        """Filter by given params."""
        if self.model:
            return await self.model.filter(**kwargs)  # type: ignore
        return list()

    async def create(
        self, obj: DownloadLinkPydantic | LinkModelPydantic
    ) -> Optional[DownloadLinks | LinkModel]:
        """Save LinkModelPydantic instance to database"""
        if self.model:
            res: DownloadLinks | LinkModel = await self.model.create(**obj.dict())
            logger.info(f"Object with id {res.pk} created")

            return res
        return None

    async def save(self, **kwargs) -> Optional[LinkModel | DownloadLinks]:
        """Save LinkModelPydantic instance to database"""
        if self.model:
            res: DownloadLinks | LinkModel = await self.model.create(**kwargs)
            logger.info(f"Object with id {res.pk} created")
            return res
        return None

    async def all(self) -> List[DownloadLinks | LinkModel]:
        """Get all model instances from DB"""
        if self.model:
            return await self.model.all()  # type: ignore
        return list()

    async def get_or_create(
        self, obj: DownloadLinkPydantic | LinkModelPydantic
    ) -> Tuple[LinkModelPydantic | DownloadLinkPydantic, bool]:
        raise NotImplementedError


class LinkRepo(BaseRepo):
    model = LinkModel

    async def get_or_create(self, obj) -> Tuple[LinkModelPydantic, bool]:
        exists = await self.filter(for_clubbers_url=obj.for_clubbers_url)
        created: bool
        return_object: LinkModelPydantic

        if exists:
            return_object = LinkModelPydantic(**exists[0].__dict__)
            created = False
        else:
            object_created: LinkModel = await self.create(obj)  # type: ignore
            return_object = LinkModelPydantic(**object_created.__dict__)
            created = True

        return return_object, created


class DownloadRepo(BaseRepo):
    model = DownloadLinks

    async def get_or_create(self, obj) -> Tuple[Optional[DownloadLinkPydantic], bool]:  # type: ignore
        exists = await self.filter(link=obj.link)
        created: bool = False
        return_object: Optional[DownloadLinkPydantic] = None

        if exists:
            instance = (
                await self.model.filter(link=obj.link)
                .prefetch_related("link_model")
                .first()
            )
            if instance:
                instance_dict = await instance.to_dict()
                return_object = DownloadLinkPydantic(**instance_dict)
                created = False
        else:
            link_model_data = obj.dict().pop("link_model")
            link_model, _ = await LinkModel.get_or_create(**link_model_data)
            obj.link_model = link_model
            object_created = await self.create(obj)

            if object_created:
                object_dict = await object_created.to_dict()

                return_object = DownloadLinkPydantic(**object_dict)
                created = True

        return return_object, created
