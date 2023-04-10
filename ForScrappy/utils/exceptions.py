from asyncpg import CannotConnectNowError


class CustomBaseException(Exception):
    default_message: str = ""

    def __init__(self, custom_msg: str):
        super().__init__(self.default_message or custom_msg)


class DBConnectionError(ConnectionError, CannotConnectNowError):
    default_message = str(CannotConnectNowError)


class URLNotValidFormat(Exception):
    def __init__(self, url: str):
        message = f"url `{url}` is in wrong format. Expected '/' at the end of url"
        super().__init__(message)
