from datetime import datetime

from pydantic.main import Model


class LinkModel(Model):
    name: str
    for_clubbers_url: str
    error: bool
    error_message: str


class DownloadLinks(Model):

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
