from asyncpg import CannotConnectNowError


class CustomBaseException(Exception):
    default_message: str = ""

    def __init__(self, custom_msg: str = ""):
        super().__init__(self.default_message or custom_msg)


class DBConnectionError(ConnectionError, CannotConnectNowError):
    default_message = str(CannotConnectNowError)


class URLNotValidFormat(Exception):
    def __init__(self, custom_msg: str = "", url: str = ""):
        message: str

        if custom_msg:
            message = custom_msg
        else:
            message = f"url `{url}` is in wrong format. Expected '/' at the end of url"

        super().__init__(message)


class TestDBWrongCredentialsError(CustomBaseException):
    default_message = (
        "Credentials for test DB are wrong. "
        "Please be sure that you have valid variables in .env file in root directory"
    )


class HashNotFoundException(CustomBaseException):
    pass


class LinkPostFailure(CustomBaseException):
    pass


class LinkModelDoesNotExist(CustomBaseException):
    custom_message = "Link model does not exist"


class DownloadLinkPydanticException(CustomBaseException):
    custom_message = "Object is not valid DownloadLinkPydantic instance"


class TokenNotFoundException(CustomBaseException):
    custom_message = "Token not found"


class TokenIsNotStrException(CustomBaseException):
    custom_message = "Token is not a valid string"
