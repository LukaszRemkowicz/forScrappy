import re
from abc import ABC
from datetime import datetime
from typing import List, Optional, Pattern, Dict

import requests
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
from settings import MANAGERS, settings
from tasks.tasks import update_thread_name
from utils.exceptions import HashNotFoundException, LinkPostFailure

logger: ColoredLogger = get_module_logger("parser")


class BaseParser:
    _kraken_headers: Dict[str, str] = {
        "content-type": "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
        "cache-control": "no-cache",
    }

    def __init__(self, session: requests.Session = requests.session()):
        self.session: requests.Session = session

    async def get_download_link(self, page_link: str) -> Optional[Dict]:
        raise NotImplementedError

    async def parse_date(self, tag_element: List[Tag]) -> Optional[datetime]:
        raise NotImplementedError

    async def parse_name(self, soup: BeautifulSoup) -> Optional[str]:
        raise NotImplementedError

    async def printify_name(self, name: str) -> str:
        raise NotImplementedError

    @property
    def printify_regexes(self) -> List[Pattern]:
        """
        Regexes responsible for removing unnecessary parts of the song name
        :return: List of regexes
        """
        return [
            re.compile(r"\.[a-zA-Z\d]{3,4}$"),
            re.compile(r"\b4clubbers(\.com)?\.pl\b", re.IGNORECASE),
        ]


class ForClubbersParser:
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

    @staticmethod
    async def parse_download_links(
        obj: Response, url: str, category: str
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


class KrakenParser(BaseParser):
    async def printify_name(self, name: str) -> str:
        new_name: str = name
        for regex in self.printify_regexes:
            new_name = re.sub(regex, "", name).strip()

        # name: str = name.strip()
        # regex1: Pattern = re.compile(r'\.[a-zA-Z\d]{3,4}$')
        # name = re.sub(regex1, "", name)
        # name = name.strip()
        # regex2: Pattern = re.compile(r'\b4clubbers(\.com)?\.pl\b', re.IGNORECASE)
        # name = re.sub(regex2, "", name)
        return new_name.title()

    async def parse_date(self, tag_elements: List[Tag]) -> Optional[datetime]:
        """
        Parse date from given tag elements
        :param tag_elements: List of tag elements
        :return: Dictionary with date
        """
        for li_tag in tag_elements:
            element_type = li_tag.find("div", {"class": "sub-text"})

            if element_type and element_type.text == "Upload date":
                date = li_tag.find("div", {"class": "lead-text"})

                if date:
                    date_str: str = date.text
                    return datetime.strptime(date_str, "%d.%m.%Y")
        return None

    async def parse_name(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Parse name from given soup
        :param soup: BeautifulSoup object
        :return: Name
        """
        regex: Pattern = re.compile(".*file-title.*")
        name_div: Tag | NavigableString | None | int = soup.find(
            "div", {"class": regex}
        )
        if name_div and isinstance(name_div, Tag):
            name_span: Tag | NavigableString | None | int = name_div.find(
                "span", {"class": "coin-name"}
            )

            if name_div and isinstance(name_span, Tag):
                name_str: str = name_span.text
                minified: str = await self.printify_name(name_str)
                return minified

        return None

    async def get_download_link(self, page_link: str) -> Optional[Dict]:
        """
        Return dictionary link with dl_link and headers.
        """
        page_resp: Response = self.session.get(page_link)
        soup: BeautifulSoup = BeautifulSoup(page_resp.text, "lxml")

        # parse token
        token: str = soup.find("input", id="dl-token")["value"]  # type: ignore
        breakpoint()
        # attempt to find hash
        hashes: List[str] = [
            item["data-file-hash"]
            for item in soup.find_all("div", attrs={"data-file-hash": True})
        ]
        if len(hashes) < 1:
            raise HashNotFoundException(f"Hash not found for page_link: {page_link}")

        dl_hash: str = hashes[0]

        payload: str = (
            f'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name="token"'
            f"\r\n\r\n{token}\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW--"
        )
        headers: Dict[str, str] = {
            **self._kraken_headers,
            "hash": dl_hash,
        }

        dl_link_resp: Response = self.session.post(
            f"{settings.kraken_base_url}/download/{dl_hash}",
            data=payload,
            headers=headers,
        )

        regex: Pattern = re.compile(".*nk-iv-wg4-overview.*")
        date_li_elements: List[Tag] = soup.find_all("ul", {"class": regex})[0].find_all(
            "li"
        )

        date: datetime | None = await self.parse_date(date_li_elements)
        name: str | None = await self.parse_name(soup)

        if dl_link_resp.status_code != 200:
            raise LinkPostFailure(
                f"Failed to get content. Status code: {dl_link_resp.status_code}"
            )

        dl_link_json: dict = dl_link_resp.json()
        if "url" in dl_link_json:
            return {
                "dl_link": dl_link_json["url"],
                "headers": self._kraken_headers,
                "published_date": date,
                "name": name,
            }
        else:
            raise LinkPostFailure(
                f"Failed to acquire download URL from kraken for page_link: {page_link}"
            )


class ZippyshareParser(BaseParser, ABC):
    async def get_download_link(self, page_link: str) -> Optional[Dict]:
        return {page_link: ""}

    @staticmethod
    async def download_file(page_link: str, path: str) -> Dict[str, str]:
        return {page_link: path}


# ParserType = TypeVar("ParserType", KrakenParser, ZippyshareParser)
ParserType = ZippyshareParser | KrakenParser
