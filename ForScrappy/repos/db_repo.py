from typing import List

from models.models import LinkModel

from logger import ColoredLogger, get_module_logger

logger: ColoredLogger = get_module_logger("db_repo")


class LinkRepo:
    model = LinkModel

    async def filter(self, **kwargs) -> List[LinkModel]:
        """Filter by given params."""
        return await self.model.filter(**kwargs)

    async def create(self, **kwargs) -> LinkModel:
        """Save LinkModel instance to database"""
        res: LinkModel = await self.model.create(**kwargs)  # noqa
        logger.info(f"Object with id {res.pk} created")

        return res

    async def save(self, **kwargs) -> LinkModel:
        """Save LinkModel instance to database"""
        model: LinkModel = self.model(**kwargs)
        res: LinkModel = await model.save()  # noqa
        logger.info(f"Object with id {res.pk} created")

        return res

    async def all(self) -> List[LinkModel]:
        """Get all LinkModel instances from DB"""
        return await self.model.all()

    async def get_or_create(self, **kwargs):
        """
        structure
        link=link,
                defaults={
                    'link_model': clubbers_link,
                    'category': category
                }

        :param kwargs:
        :return:
        """
