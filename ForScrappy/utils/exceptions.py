from asyncpg import CannotConnectNowError


class CustomBaseException(Exception):
    default_message: str = ""

    def __init__(self, custom_msg: str):
        super().__init__(self.default_message or custom_msg)


class DBConnectionError(ConnectionError, CannotConnectNowError):
    default_message = str(CannotConnectNowError)
