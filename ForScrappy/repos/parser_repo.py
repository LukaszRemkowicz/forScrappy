import re
from datetime import datetime
from typing import List, Optional, Pattern

import validators
from bs4 import BeautifulSoup, SoupStrainer, Tag, NavigableString
from bs4.element import ResultSet
from dateutil.parser import ParserError
from requests import Response

from logger import ColoredLogger, get_module_logger
from models.entities import (
    LinkModelPydantic,
    DownloadLinkPydantic,
    DownloadLinksPydantic,
    LinksModelPydantic,
)
from models.models import LinkModel
from repos.handlers import LinkModelHandler
from settings import MANAGERS
from tasks.tasks import update_thread_name

logger: ColoredLogger = get_module_logger("parser")


class ForClubbersParser:
    """Base repo for specific forum responsible for parsing data"""

    @staticmethod
    async def parse_forum(obj: Response, category: str) -> LinksModelPydantic:
        """
        Parse forum and return list of links.
        Basically parse main forum page and get all links to topics
            :param obj: Response object
            :param category: Category name (string)
            :return: List of links to topics
        """

        soup = BeautifulSoup(obj.text, parse_only=SoupStrainer("td"), features="lxml")
        all_a_href_tags: ResultSet = soup.findAll("a")

        links_models: List[LinkModelPydantic] = []
        posts_pattern: Pattern = re.compile(r"#post\d+$")
        filtered_list: List[str] = []

        for link in all_a_href_tags:
            if link.get("href") and posts_pattern.search(link.get("href")):
                filtered_list.append(link.get("href"))

        logger.info("Parsing forum. Looking for download links...")

        for filtered_link in filtered_list:
            if category in filtered_link:
                html_regex: Pattern = re.compile(r"(.+)(html)(.+)")
                new_link: str = re.sub(html_regex, r"\1\2", filtered_link)

                assert validators.url(new_link) is True, "Not a valid url link"

                links_models.append(LinkModelPydantic(for_clubbers_url=new_link))

        return LinksModelPydantic(__root__=links_models)

    @staticmethod
    def parse_date(obj: Response) -> Optional[datetime]:
        """
        Parse date from given Response object
            :param obj: Response object
            :return: datetime object
        """
        date_parser: ResultSet[Tag] = BeautifulSoup(
            obj.content, features="lxml"
        ).select('td:has(a[name^="post"])')

        date_string: str = str(date_parser[0].text)

        for element in ["\n", "\t", "\r", ","]:
            date_string = date_string.replace(element, "")

        try:
            date = datetime.strptime(date_string, "%d-%m-%Y %H:%M")
            return date
        except (ValueError, ParserError):
            return None

    async def parse_download_links(
        self, obj: Response, url: str, category: str
    ) -> DownloadLinksPydantic:
        """
        Parse given topic and return list of download links
            :param obj: Response object
            :param url: Url to topic
            :param category: Category name (string)
            :return: List of download links
        """

        soup: BeautifulSoup = BeautifulSoup(
            obj.content, parse_only=SoupStrainer("div"), features="lxml"
        )

        thread_name: str | List[str] | None = ""
        thread_obj: BeautifulSoup = BeautifulSoup(obj.content, "html.parser")
        if thread_obj:
            thread_meta: Optional[Tag | NavigableString] = thread_obj.find(
                "meta", property="og:title"
            )
            if thread_meta and isinstance(thread_meta, Tag):
                thread_name = thread_meta.get("content")

        if thread_name:
            update_thread_name.delay(thread_name=thread_name, url=url)  # type: ignore

        a_href_tags: ResultSet = soup.findAll("a")
        manager_links: List[str] = []

        # gather all links to download managers
        for a_href_element in a_href_tags:
            if a_href_url := a_href_element.get("data-url"):  # noqa: E999
                for manager in MANAGERS:
                    if manager in a_href_url:
                        manager_links.append(a_href_url)

        # TODO date not used right now
        # date_obj: Optional[datetime] = self.parse_date(obj)

        # Get the LinkModel instance from db
        link_instance: Optional[LinkModel] = await LinkModelHandler.get_obj(
            for_clubbers_url=url
        )
        if link_instance:
            link_model: LinkModelPydantic = LinkModelPydantic(**link_instance.__dict__)
        else:
            raise

        result: List[DownloadLinkPydantic] = []

        for link in set(manager_links):
            result.append(
                DownloadLinkPydantic(
                    link=link,
                    category=category,
                    link_model=link_model,
                )
            )

        return DownloadLinksPydantic(__root__=result)
