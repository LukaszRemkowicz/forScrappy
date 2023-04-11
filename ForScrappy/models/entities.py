from datetime import datetime
from random import choice
from typing import Optional, Dict, List

from pydantic.main import BaseModel

from utils.consts import USER_AGENTS


class LinkModelPydantic(BaseModel):
    name: Optional[str]
    for_clubbers_url: str
    error: bool = False
    error_message: Optional[str]


class Links(BaseModel):
    __root__: List[LinkModelPydantic]


class DownloadLinkPydantic(BaseModel):
    name: Optional[str]
    link: str
    link_model: LinkModelPydantic
    download_link: Optional[str]
    downloaded: bool = False
    downloaded_date: Optional[datetime]
    error: bool = False
    error_message: Optional[str]
    not_exists: bool = False
    published_date: Optional[datetime]
    category: str
    invalid_download_link: bool = False


class DownloadLinks(BaseModel):
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
