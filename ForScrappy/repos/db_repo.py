import abc
from logging import Logger
from typing import Generic, List, Optional, Tuple, Type, TypeVar

from logger import get_module_logger
from models.entities import (
    DownloadLinkPydantic,
    DownloadLinksPydantic,
    LinkModelPydantic,
    LinksModelPydantic,
)
from models.models import DownloadLinks, LinkModel
from mypy.checkstrformat import Union
from tortoise.exceptions import DoesNotExist
from tortoise.queryset import QuerySet

logger: Logger = get_module_logger("db_repo")


# ModelType = TypeVar("ModelType", bound=models.Model)

ModelType = Union[LinkModel, DownloadLinks]

PydanticTypeVar = TypeVar(
    "PydanticTypeVar",
    bound=Union[
        LinksModelPydantic,
        DownloadLinksPydantic,
        DownloadLinkPydantic,
        LinkModelPydantic,
    ],
)

b = DownloadLinksPydantic | LinksModelPydantic | DownloadLinkPydantic | LinkModelPydantic

# TODO klasy generyczne/template, interfejsy

T = TypeVar("T", bound=b)


class BaseRepo(abc.ABC, Generic[PydanticTypeVar]):
    model: Type[ModelType]

    @abc.abstractmethod
    async def filter(self, **kwargs) -> Optional[PydanticTypeVar]:
        raise NotImplementedError

    @abc.abstractmethod
    async def create(self, obj: PydanticTypeVar) -> PydanticTypeVar:
        """Save LinkModelPydantic instance to database"""
        raise NotImplementedError

    @abc.abstractmethod
    async def save(self, obj: PydanticTypeVar) -> PydanticTypeVar:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_or_create(
        self, obj: PydanticTypeVar
    ) -> Tuple[Optional[PydanticTypeVar], bool]:
        raise NotImplementedError

    @abc.abstractmethod
    async def update_fields(self, obj: PydanticTypeVar, **kwargs) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def all(self) -> PydanticTypeVar:
        """Get all model instances from DB"""
        raise NotImplementedError


class LinkModelRepo(BaseRepo):
    model = LinkModel

    async def filter(self, **kwargs) -> Optional[PydanticTypeVar]:  # type: ignore
        result = await self.model.filter(**kwargs)
        pydantic_list = []
        if result:
            for element in result:
                pydantic_list.append(LinkModelPydantic(**element.__dict__))

            return LinksModelPydantic(__root__=pydantic_list)  # type: ignore
        return None

    async def save(self, obj: PydanticTypeVar) -> PydanticTypeVar:
        instance: LinkModel = self.model(**obj.dict())
        await instance.save()
        return LinkModelPydantic(**instance.__dict__)  # type: ignore

    async def create(self, obj: PydanticTypeVar) -> PydanticTypeVar:
        """Save LinkModelPydantic instance to database"""
        res: ModelType = await self.model.create(**obj.dict())
        logger.info(f"Object {self.model.__name__} with id {res.pk} created")
        return LinkModelPydantic(**res.__dict__)  # type: ignore

    async def get_or_create(self, obj: b) -> Tuple[b, bool]:
        """Get or create LinkModelPydantic instance in database"""

        assert isinstance(obj, LinkModelPydantic)

        exists: Optional[List[LinkModel]] = await self.model.filter(
            for_clubbers_url=obj.for_clubbers_url
        )
        created: bool
        return_object: LinkModelPydantic

        if exists:
            return_object = LinkModelPydantic(**exists[0].__dict__)
            created = False
        else:
            return_object = await self.create(obj)  # type: ignore
            created = True

        return return_object, created

    async def all(self) -> PydanticTypeVar:
        """Get all model instances from DB"""
        res: List[LinkModel] = await self.model.all()
        return LinksModelPydantic(__root__=res)  # type: ignore

    async def update_fields(self, obj: PydanticTypeVar, **kwargs) -> None:
        assert isinstance(obj, LinkModelPydantic)
        try:
            model_instance: ModelType = await self.model.get(pk=obj.pk)
        except DoesNotExist as e:
            logger.error(f"Object with id {obj.pk} doesn't exist")
            raise e

        for key, value in kwargs.items():
            try:
                setattr(model_instance, key, value)
            except AttributeError:
                logger.error(f"Attribute {key} doesn't exist")

        await model_instance.save()
        logger.info(f"Object updated: {obj.pk}")


class DownloadLinksRepo(BaseRepo):
    model: Type[DownloadLinks] = DownloadLinks
    link_model: Type[LinkModel] = LinkModel

    async def update_fields(self, obj: PydanticTypeVar, **kwargs) -> None:
        assert isinstance(obj, DownloadLinkPydantic)

        try:
            model_instance: DownloadLinks = await self.model.get(pk=obj.pk)
        except DoesNotExist as e:
            logger.error(f"Object with id {obj.pk} doesn't exist")
            raise e

        for key, value in kwargs.items():
            if key != "link_model":
                try:
                    setattr(model_instance, key, value)
                except AttributeError:
                    logger.error(f"Attribute {key} doesn't exist")

        await model_instance.save()
        logger.info(f"Object updated: {obj.pk}")

    @staticmethod
    async def get_link_model_pydantic(link_model_id: int) -> dict:
        link_model: Optional[LinksModelPydantic] = await LinkModelRepo().filter(  # type: ignore
            pk=link_model_id
        )
        if not link_model:
            raise ValueError("LinkModel with given id doesn't exist")
        link_object: dict = link_model.__root__[0].dict()
        return link_object

    async def save(self, obj: PydanticTypeVar) -> PydanticTypeVar:
        assert isinstance(obj, DownloadLinkPydantic)

        obj_instance: Optional[DownloadLinks] = await self.model.filter(
            link=obj.link
        ).first()
        if obj_instance:
            for key, val in obj.dict().items():
                if not isinstance(
                    getattr(obj_instance, key), QuerySet
                ) and val != getattr(obj_instance, key):
                    setattr(obj_instance, key, val)
            await obj_instance.save()
            await obj_instance.refresh_from_db()

        link_model_id: Optional[int] = obj_instance.__dict__.get("link_model_id")

        if not link_model_id:
            raise ValueError("LinkModel id is not provided")

        link_object: dict = await self.get_link_model_pydantic(link_model_id)
        element_dict: dict = {**obj_instance.__dict__, "link_model": link_object}

        return DownloadLinkPydantic(**element_dict)  # type: ignore

    async def get_or_create(
        self, obj: PydanticTypeVar
    ) -> Tuple[Optional[PydanticTypeVar], bool]:
        assert isinstance(obj, DownloadLinkPydantic)

        exists = await self.filter(link=obj.link)  # type: ignore
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
            object_created: DownloadLinkPydantic = await self.create(obj)

            if object_created:
                object_dict = object_created.dict()

                return_object = DownloadLinkPydantic(**object_dict)
                created = True

        return return_object, created  # type: ignore

    async def all(self) -> PydanticTypeVar:
        """Get all model instances from DB"""
        res: List[DownloadLinks] = await self.model.all()

        result: List[dict] = []
        for element in res:
            element_dict = await element.to_dict()
            result.append(element_dict)

        return DownloadLinksPydantic(__root__=result)  # type: ignore

    async def create(self, obj: PydanticTypeVar) -> PydanticTypeVar:
        """Override create method to create link_model if it doesn't exist."""

        link_model: LinkModel
        assert isinstance(obj, DownloadLinkPydantic)

        link_model4create: dict = obj.link_model.dict()
        link_model4create.pop("pk")
        link_model, _ = await self.link_model.get_or_create(**link_model4create)

        new_object_data: dict = {**obj.dict(), "link_model": link_model}
        new_object_data.pop("pk")
        res: DownloadLinks = await self.model.create(**new_object_data)

        logger.info(f"Object {self.model.__name__} with id {res.pk} created")
        res_dict: dict = await res.to_dict()

        return DownloadLinkPydantic(**res_dict)  # type: ignore

    async def filter(self, **kwargs) -> Optional[PydanticTypeVar]:  # type: ignore
        result: List[DownloadLinks] = await self.model.filter(**kwargs)
        pydantic_list: list[DownloadLinkPydantic] = []
        if result:
            for element in result:
                link_object: dict = await self.get_link_model_pydantic(
                    element.__dict__.get("link_model_id")
                )
                element_dict: dict = {**element.__dict__, "link_model": link_object}
                pydantic_list.append(DownloadLinkPydantic(**element_dict))
            if pydantic_list:
                return DownloadLinksPydantic(__root__=pydantic_list)  # type: ignore
        return None
