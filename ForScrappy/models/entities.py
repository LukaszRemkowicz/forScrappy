from datetime import datetime
from random import choice
from typing import Optional, Dict, List

from pydantic.main import BaseModel

from utils.consts import USER_AGENTS


class LinkModel(BaseModel):
    name: Optional[str]
    for_clubbers_url: str
    error: bool = False
    error_message: Optional[str]


class Links(BaseModel):
    __root__: List[LinkModel]


class DownloadLink(BaseModel):

    name: str
    link: str
    link_model: LinkModel
    download_link: str
    downloaded: bool
    downloaded_date: datetime
    error: bool
    error_message: str
    not_exists: bool
    published_date: datetime
    category: str
    invalid_download_link: bool


class DownloadLinks:
    __root__: List[DownloadLink]


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
