from typing import List, Optional, Tuple, Type, TypeVar, Generic

from tortoise import models

from models.entities import LinkModelPydantic, DownloadLinkPydantic
from models.models import LinkModel, DownloadLinks
from logger import ColoredLogger, get_module_logger

logger: ColoredLogger = get_module_logger("db_repo")


ModelType = TypeVar("ModelType", bound=models.Model)
PydanticTypeVar = TypeVar("PydanticTypeVar", DownloadLinkPydantic, LinkModelPydantic)


class BaseRepo(Generic[ModelType]):
    model: Type[ModelType]

    async def filter(self, **kwargs) -> List[Optional[ModelType]]:
        """Filter by given params."""
        return await self.model.filter(**kwargs)  # type: ignore

    async def create(self, obj: PydanticTypeVar) -> Optional[ModelType]:
        """Save LinkModelPydantic instance to database"""
        res: ModelType = await self.model.create(**obj.dict())
        logger.info(f"Object {self.model.__name__} with id {res.pk} created")

        return res

    async def save(self, **kwargs) -> None:
        obj: ModelType = self.model(**kwargs)
        await obj.save(**kwargs)

    async def all(self) -> List[Optional[ModelType]]:
        """Get all model instances from DB"""
        return await self.model.all()  # type: ignore

    async def get_or_create(self, obj: PydanticTypeVar) -> Tuple[PydanticTypeVar, bool]:
        raise NotImplementedError

    @staticmethod
    async def update_fields(obj: ModelType, **kwargs):
        for key, value in kwargs.items():
            setattr(obj, key, value)
        await obj.save()
        logger.info(f"Object updated: {obj.pk}")


class LinkModelRepo(BaseRepo[LinkModel]):
    model = LinkModel

    async def get_or_create(self, obj: LinkModelPydantic) -> Tuple[LinkModelPydantic, bool]:  # type: ignore
        exists: List[Optional[LinkModel]] = await self.filter(
            for_clubbers_url=obj.for_clubbers_url
        )
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


class DownloadLinksRepo(BaseRepo[DownloadLinks]):
    model: Type[DownloadLinks] = DownloadLinks
    link_model: Type[LinkModel] = LinkModel

    async def get_or_create(self, obj: DownloadLinkPydantic) -> Tuple[Optional[DownloadLinkPydantic], bool]:  # type: ignore
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
            link_model: Optional[LinkModel] = await self.link_model.filter(
                for_clubbers_url=obj.link_model.for_clubbers_url
            ).first()

            if not link_model:
                raise ValueError("LinkModel with given url doesn't exist")

            obj.link_model = LinkModelPydantic(**link_model.__dict__)
            object_created: DownloadLinks = await self.create(obj)

            if object_created:
                object_dict = await object_created.to_dict()

                return_object = DownloadLinkPydantic(**object_dict)
                created = True

        return return_object, created

    async def create(self, obj: DownloadLinkPydantic) -> DownloadLinks:  # type: ignore
        """Override create method to create link_model if it doesn't exist."""
        link_model: LinkModel
        link_model, _ = await self.link_model.get_or_create(**obj.link_model.dict())

        new_object_data: dict = {**obj.dict(), "link_model": link_model}
        # obj.link_model = link_model
        # res: ModelType = await self.model.create(**obj.dict())
        res: DownloadLinks = await self.model.create(**new_object_data)
        logger.info(f"Object {self.model.__name__} with id {res.pk} created")

        return res
