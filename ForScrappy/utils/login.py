import hashlib

import requests

from models.entities import RequestHeaders
from models.types import SessionObject
from settings import settings


class User:
    @staticmethod
    def login() -> SessionObject:
        base_url: str = settings.local.login_url
        headers: RequestHeaders = RequestHeaders()

        payload = {
            "vb_login_username": settings.local.username,
            "vb_login_password": "",
            "s": "",
            "securitytoken": "guest",
            "do": "login",
            "vb_login_md5password": (
                hashlib.md5(bytes(settings.local.password.get_secret_value(), "utf-8"))
            ).hexdigest(),
            "vb_login_md5password_utf": (
                hashlib.md5(bytes(settings.local.password.get_secret_value(), "utf-8"))
            ).hexdigest(),
        }

        session = requests.Session()
        headers_choice: dict = headers()

        session.post(base_url, data=payload, headers=headers_choice)
        cookie = session.cookies

        return SessionObject(session=session, cookie=cookie, headers=headers_choice)
