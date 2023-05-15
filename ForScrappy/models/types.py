from dataclasses import dataclass
from typing import TypeVar, Dict, Any

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
