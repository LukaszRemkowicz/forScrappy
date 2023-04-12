import re
from typing import List, Optional

import validators
from bs4 import BeautifulSoup, SoupStrainer

from logger import ColoredLogger, get_module_logger
from models.entities import (
    LinkModelPydantic,
    Links,
    DownloadLinks,
    DownloadLinkPydantic,
)
from models.models import LinkModel
from repos.handlers import LinkModelHandler
from settings import MANAGERS

logger: ColoredLogger = get_module_logger("parser")


class ForClubbersParser:
    @staticmethod
    async def parse_object(obj, category) -> Links:
        soup = BeautifulSoup(obj.text, parse_only=SoupStrainer("td"), features="lxml")
        all_a_href_tags = soup.findAll("a")
        # regex = re.compile(rf'{category}/\d.?')

        if not isinstance(category, str):
            category = str(category)

        links_models: list = []

        posts_pattern = re.compile(r"#post\d+$")
        filtered_list = []
        for link in all_a_href_tags:
            if link.get("href") and posts_pattern.search(link.get("href")):
                filtered_list.append(link.get("href"))

        logger.info("parsing forum. Looking for zippy links...")
        for filtered_link in filtered_list:
            if category in filtered_link:
                html_regex = r"(.+)(html)(.+)"
                link = re.sub(html_regex, r"\1\2", filtered_link)

                assert validators.url(link) is True, "Not a valid url link"

                links_models.append(LinkModelPydantic(for_clubbers_url=link))

        return Links(__root__=links_models)

    @staticmethod
    async def parse_download_links(obj, url: str, category: str):
        #
        soupe = BeautifulSoup(
            obj.content, parse_only=SoupStrainer("div"), features="lxml"
        )

        # get_topic_name = BeautifulSoup(
        #     enter_topic.content, "html.parser"
        # ).find("meta", property="og:title").get('content')

        # TODO add to celery task
        # clubbers_link.name = get_topic_name
        # clubbers_link.save()

        a_href_tags = soupe.findAll("a")

        manager_links: List[str] = []
        for a_href_element in a_href_tags:
            if a_href_url := a_href_element.get("data-url"):  # noqa: E999
                for manager in MANAGERS:
                    if manager in a_href_url:
                        manager_links.append(a_href_url)

        result: list = []

        # 4clubbers date parser
        # date_parser: ResultSet[Tag] = BeautifulSoup(
        #     obj.content, features="lxml"
        # ).select('td:has(a[name^="post"])')
        # date_string: str = str(date_parser[0].text).replace("\n", "").replace("\t", "")

        # try:
        #     # parse_date = parser.parse(re.sub(regex_date, r'\3', soup.replace('\n', '')))
        #     date = datetime.strptime(date, '%d-%m-%Y %H:%M')
        #     return date
        # except (ValueError, ParserError) as e:
        #     # breakpoint()
        #     return ''

        link_instance: Optional[LinkModel] = await LinkModelHandler.get_obj(
            for_clubbers_url=url
        )
        if link_instance:
            link_model: LinkModelPydantic = LinkModelPydantic(**link_instance.__dict__)
        else:
            raise

        for link in set(manager_links):
            result.append(
                DownloadLinkPydantic(
                    link=link,
                    category=category,
                    link_model=link_model,
                )
            )

        return DownloadLinks(__root__=result)
