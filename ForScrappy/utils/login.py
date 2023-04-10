import hashlib

import requests

from models.entities import RequestHeaders
from models.types import SessionObject
from settings import USERNAME, LOGIN_URL, PASSWORD


class User:
    @staticmethod
    def login() -> SessionObject:
        base_url: str = LOGIN_URL
        headers: RequestHeaders = RequestHeaders()

        payload = {
            "vb_login_username": USERNAME,
            "vb_login_password": "",
            "s": "",
            "securitytoken": "guest",
            "do": "login",
            "vb_login_md5password": (hashlib.md5(PASSWORD)).hexdigest(),
            "vb_login_md5password_utf": (hashlib.md5(PASSWORD)).hexdigest(),
        }

        session = requests.Session()
        headers_choice: dict = headers()

        session.post(base_url, data=payload, headers=headers_choice)
        cookie = session.cookies

        return SessionObject(session=session, cookie=cookie, headers=headers_choice)
