from typing import Optional

from requests import Response, Session
from requests.cookies import RequestsCookieJar

from logger import ColoredLogger, get_module_logger
from models.entities import DownloadLinksPydantic, LinksModelPydantic
from models.types import SessionObject
from repos.parser_repo import ForClubbersParser

logger: ColoredLogger = get_module_logger("api_repo")


class ForClubbersScrapper:
    """Base repo responsible for handling requests"""

    def __init__(self, session_obj: Optional[SessionObject] = None) -> None:
        self.session: Session = Session() if not session_obj else session_obj.session
        self.session_headers: dict[str, str] = {}
        self.session_cookies: RequestsCookieJar = RequestsCookieJar()

        if session_obj:
            self.session_headers = session_obj.headers
            self.session_cookies = session_obj.cookie

        self.parse: ForClubbersParser = ForClubbersParser()

    async def __fetch_data_get(self, url: str) -> Response:
        """Main method for fetching data"""

        logger.info(f"Started parsing {url}")
        response: Response = self.session.get(
            url=url, cookies=self.session_cookies, headers=self.session_headers
        )
        response.raise_for_status()
        logger.info("Success")
        return response

    async def get_download_links(
        self, link: str, category: str
    ) -> DownloadLinksPydantic:
        """Get download links from specific forum thread. Parse them from html response"""
        response = await self.__fetch_data_get(link)
        return await self.parse.parse_download_links(
            obj=response, url=link, category=category
        )

    async def get_forum_urls(self, link: str, category) -> LinksModelPydantic:
        """Get forum urls from specific forum category. Parse them from html response"""
        response = await self.__fetch_data_get(link)
        return await self.parse.parse_forum(obj=response, category=category)
