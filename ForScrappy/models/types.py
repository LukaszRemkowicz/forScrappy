from collections import namedtuple
from dataclasses import dataclass
from typing import Any, Dict, TypeVar

from requests import Session
from requests.cookies import RequestsCookieJar
from tortoise import Tortoise


@dataclass
class SessionObject:
    session: Session
    cookie: RequestsCookieJar
    headers: dict


NestedDict = TypeVar("NestedDict", bound=Dict[str, Any])


class MyTortoise(Tortoise):
    is_connected: bool = False


ParserData = namedtuple("ParserData", "thread_num download_links_num errors")
