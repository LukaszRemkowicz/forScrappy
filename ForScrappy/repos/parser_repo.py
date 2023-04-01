import re

import validators
from bs4 import BeautifulSoup, SoupStrainer
from requests import Session

from logger import ColoredLogger, get_module_logger
from models.entities import LinkModel, Links, DownloadLinks, DownloadLink

logger: ColoredLogger = get_module_logger("parser")


class MainParser:
    @staticmethod
    async def parse_object(obj, category) -> Links:
        soup = BeautifulSoup(obj.text, parse_only=SoupStrainer("td"), features="lxml")
        all_a_href_tags = soup.findAll("a")
        regex = re.compile(rf'{category}/\d.?')

        if not isinstance(category, str):
            category = str(category)

        links_models: list = []

        posts_pattern = re.compile(r'#post\d+$')
        filtered_list = []
        for link in all_a_href_tags:
            if link.get('href') and posts_pattern.search(link.get('href')):
                filtered_list.append(link.get('href'))

        logger.info(f'parsing forum. Looking for zippy links...')
        for filtered_link in filtered_list:

            if category in filtered_link:

                html_regex = r'(.+)(html)(.+)'
                link = re.sub(html_regex, r'\1\2', filtered_link)

                assert validators.url(link), "Not a valid url link"

                links_models.append(LinkModel(for_clubbers_url=link))

        return Links(__root__=links_models)

    @staticmethod
    async def parse_download_links(obj, url: str, category: str):

        #
        soupe = BeautifulSoup(
            obj.content,
            parse_only=SoupStrainer("div"),
            features="lxml"
        )

        # get_topic_name = BeautifulSoup(
        #     enter_topic.content, "html.parser"
        # ).find("meta", property="og:title").get('content')

        # TODO add to celery task
        # clubbers_link.name = get_topic_name
        # clubbers_link.save()

        get_a_href_tags = soupe.findAll('a')
        breakpoint()

        get_all_zippy_links = set(
            [element.get('data-url') for element in get_a_href_tags
             if element.get('data-url') and 'zippyshare.com' in element.get('data-url')
             ])

        result: list = []

        for link in get_all_zippy_links:
            result.append(
                DownloadLink(
                    link=link,
                    link_model=url,
                    category=category)
            )

        return DownloadLinks(__root__=result)
