from logging import Logger
from typing import Optional, Type, Dict

from requests import Response, Session
from requests.cookies import RequestsCookieJar

from logger import get_module_logger
from models.entities import DownloadLinksPydantic, LinksModelPydantic
from models.types import SessionObject
from repos.parser_repo import ForClubbersParser, ParserType
from tasks.tasks import download_file

logger: Logger = get_module_logger("request_repo")


class ForClubbersScrapper:
    """Base repo responsible for handling requests"""

    def __init__(self, session_obj: Optional[SessionObject] = None) -> None:
        self.session: Session = Session() if not session_obj else session_obj.session
        self.session_headers: dict[str, str] = {}
        self.session_cookies: RequestsCookieJar = RequestsCookieJar()

        if session_obj:
            self.session_headers = session_obj.headers
            self.session_cookies = session_obj.cookie

        self.forum_parser: ForClubbersParser = ForClubbersParser()

    async def __fetch_data_get(self, url: str) -> Response:
        """
        Main method for fetching data
        :param url: str: url to parse
        :return: Response
        """

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
        """
        Get download links from specific forum thread. Parse them from html responses
        :param link: str: url to parse
        :param category: str: category name
        :return: DownloadLinksPydantic
        """
        response: Response = await self.__fetch_data_get(link)
        return await self.forum_parser.parse_download_links(
            obj=response, url=link, category=category
        )

    async def get_forum_urls(self, link: str, category) -> LinksModelPydantic:
        """
        Get forum urls from specific forum category. Parse them from html responses
        :param link: str: url to parse
        :param category: str: category name
        :return: LinksModelPydantic
        """
        response = await self.__fetch_data_get(link)
        return await self.forum_parser.parse_forum(obj=response, category=category)

    @staticmethod
    async def download_file(
        dl_link: str,
        headers: Dict[str, str],
        object_id: Optional[int],
        file_path: str,
    ) -> None:
        """
        Download file from url as a celery task
        :param dl_link: file download link
        :param headers: headers as dict
        :param object_id: id of DownloadLinksPydantic object
        :param file_path: path to save file
        return: None
        """

        if not object_id:
            return

        download_file.delay(  # type: ignore
            object_id=object_id, dl_link=dl_link, headers=headers, file_path=file_path
        )

    async def parse_download_link(self, url: str, parser: Type[ParserType]) -> Dict:
        """
        Parse download link from Response object
        :param url: str: url to parse
        :param parser: Type[ParserType]: parser object: KrakenParser | ZippyShareParser
        :return: Dict: parsed download link with additional information
        """

        parser_obj: ParserType = parser(session=self.session)
        response: dict = await parser_obj.get_download_link(url)  # type: ignore
        return response
