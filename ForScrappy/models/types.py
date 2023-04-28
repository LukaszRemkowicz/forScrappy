from dataclasses import dataclass
from typing import TypeVar, Dict, Any

from requests import Session
from requests.cookies import RequestsCookieJar


@dataclass
class SessionObject:
    session: Session
    cookie: RequestsCookieJar
    headers: dict


NestedDict = TypeVar("NestedDict", bound=Dict[str, Any])
