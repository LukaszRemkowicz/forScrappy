from dataclasses import dataclass

from requests import Session
from requests.cookies import RequestsCookieJar


@dataclass
class SessionObject:
    session: Session
    cookie: RequestsCookieJar
    headers: dict
