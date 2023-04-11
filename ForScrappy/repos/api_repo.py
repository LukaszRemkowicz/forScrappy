from requests import Response

from logger import ColoredLogger, get_module_logger
from models.entities import Links
from models.types import SessionObject
from repos.parser_repo import ForClubbersParser

logger: ColoredLogger = get_module_logger("api_repo")


class ForClubbersScrapper:
    """Base repo responsible for handling requests"""

    def __init__(self, session_obj: SessionObject) -> None:
        self.session = session_obj.session
        self.session_headers = session_obj.headers
        self.session_cookies = session_obj.cookie
        self.parse: ForClubbersParser = ForClubbersParser()

    async def __fetch_data_get(self, url: str) -> Response:

        logger.info(f"Started parsing {url}")
        response: Response = self.session.get(
            url=url, cookies=self.session_cookies, headers=self.session_headers
        )
        response.raise_for_status()
        logger.info("Success")
        return response

    async def get_download_links(self, link: str, category: str):
        response = await self.__fetch_data_get(link)
        return await self.parse.parse_download_links(
            obj=response, url=link, category=category
        )

    async def get_forum_urls(self, link: str, category) -> Links:
        response = await self.__fetch_data_get(link)
        return await self.parse.parse_object(obj=response, category=category)

        # enter_topic = session.get(link, cookies=cookie, headers=header)
        # soupe = BeautifulSoup(enter_topic.content, parse_only=SoupStrainer("div"), features="lxml")
        #
        # get_topic_name = BeautifulSoup(
        #     enter_topic.content, "html.parser"
        # ).find("meta", property="og:title").get('content')
        #
        # clubbers_link.name = get_topic_name
        # clubbers_link.save()
        #
        # get_a_href_tags = soupe.findAll('a')
        #
        # get_all_zippy_links = set(
        #     [element.get('data-url') for element in get_a_href_tags
        #      if element.get('data-url') and 'zippyshare.com' in element.get('data-url')
        #      ])
        #
        # for link in get_all_zippy_links:
        #     ZippyLinks.objects.get_or_create(
        #         link=link,
        #         defaults={
        #             'link_model': clubbers_link,
        #             'category': category
        #         }
        #     )
