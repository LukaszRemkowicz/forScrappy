from typing import Union, Type

from .entities import DownloadLinkPydantic, LinkModelPydantic


PydanticType = Union[Type[LinkModelPydantic], Type[DownloadLinkPydantic]]
