from typing import Type, Union

from .entities import DownloadLinkPydantic, LinkModelPydantic

PydanticType = Union[Type[LinkModelPydantic], Type[DownloadLinkPydantic]]
