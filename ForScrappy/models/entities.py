from datetime import datetime
from random import choice
from typing import Dict, List, Optional

from pydantic import BaseModel
from utils.consts import USER_AGENTS


class LinkModelPydantic(BaseModel):
    pk: Optional[int] = None
    name: Optional[str] = None
    for_clubbers_url: str
    error: bool = False
    error_message: Optional[str] = None


class LinksModelPydantic(BaseModel):
    __root__: List[LinkModelPydantic]


class DownloadLinkPydantic(BaseModel):
    pk: Optional[int] = None
    name: Optional[str] = None
    link: str
    link_model: LinkModelPydantic
    download_link: Optional[str] = None
    downloaded: bool = False
    downloaded_date: Optional[datetime] = None
    error: bool = False
    error_message: Optional[str] = None
    not_exists: bool = False
    published_date: Optional[datetime] = None
    category: str
    invalid_download_link: bool = False


class DownloadLinksPydantic(BaseModel):
    __root__: List[DownloadLinkPydantic]


class RequestHeaders(BaseModel):
    """Headers params"""

    user_agent: Optional[str] = None

    def __call__(self) -> Dict:
        """call different user agent on every object call"""
        self.set_user_agent()
        return self.dict()

    def set_user_agent(self) -> None:
        """shuffle user agent"""
        self.user_agent = choice(USER_AGENTS)

    def dict(self, **kwargs):
        """serialize headers"""
        serialized = super().dict()
        serialized["User-agent"] = serialized.pop("user_agent")
        return serialized
