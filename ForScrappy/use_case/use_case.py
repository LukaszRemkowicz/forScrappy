from typing import Dict, List, Optional, Type

from models.entities import (
    DownloadLinkPydantic,
    DownloadLinksPydantic,
    LinkModelPydantic,
    LinksModelPydantic,
)
from models.types import ParserData, SessionObject
from repos.db_repo import DownloadLinksRepo, LinkModelRepo
from repos.parser_repo import KrakenParser, ParserType, ZippyshareParser
from repos.request_repo import ForClubbersScrapper
from utils.exceptions import HashNotFoundException, LinkPostFailure
from utils.utils import get_folder_name_from_date


class ForClubUseCase:
    def __init__(
        self,
        link_repo: Type["LinkModelRepo"],
        download_repo: Type["DownloadLinksRepo"],
        repo_scrapper: Type["ForClubbersScrapper"],
        session_obj: Optional[SessionObject] = None,
    ) -> None:
        self.link_model_repo: LinkModelRepo = link_repo()
        self.download_links_repo: DownloadLinksRepo = download_repo()
        self.scrapper_repo: ForClubbersScrapper = repo_scrapper(session_obj)

    @staticmethod
    async def choose_download_manager(url: str) -> Type[ParserType]:
        managers: Dict[str, Type[ParserType]] = {
            "krakenfiles": KrakenParser,
            "zippyshare": ZippyshareParser,
        }

        for manager in managers:
            if manager in url:
                try:
                    res: Type[ParserType] = managers[manager]
                    return res
                except KeyError:
                    #  TODO add information to model, that manager is not found. Add new field for manager type
                    ...
        raise ValueError(f"Manager not found for {url}")

    async def download_file(self, link_obj: DownloadLinkPydantic) -> None:
        """
        Download file from link. This method as an argument takes existing
        DownloadLinks object, that's why there is no need to check if object is in db
        :param link_obj: DownloadLinkPydantic: pydantic representation of DownloadLinks model
        :return: None : This method ends with saving file to disk as a celery task
        """

        url: str = link_obj.link
        parser: Type[ParserType] = await self.choose_download_manager(url)

        dl_link: str
        headers: Dict[str, str]

        try:
            response: Dict = await self.scrapper_repo.parse_download_link(
                url=url, parser=parser
            )
            await self.download_links_repo.update_fields(
                obj=link_obj,
                download_link=url,
                published_date=response.get("published_date"),
                name=response.get("name"),
            )
        except (LinkPostFailure, HashNotFoundException) as e:
            await self.download_links_repo.update_fields(
                obj=link_obj,
                download_link=url,
                error=True,
                error_message=f"{link_obj.error_message}; {str(e)}",
            )
            return

        dl_link = response["dl_link"]
        headers = response["headers"]
        file_path = get_folder_name_from_date(response["published_date"])

        await self.scrapper_repo.download_file(
            dl_link=dl_link,
            headers=headers,
            file_path=file_path,
            object_id=link_obj.pk,
        )

    async def get_links_with_errors(self) -> Optional[DownloadLinksPydantic]:
        """Return links with errors"""
        res: Optional[DownloadLinksPydantic] = await self.download_links_repo.filter(  # type: ignore
            error=True
        )
        if not res or not res.__root__:
            return None
        return res

    async def get_links(self) -> Optional[DownloadLinksPydantic]:
        """Return links from DB which are not downloaded yet"""
        res: Optional[DownloadLinksPydantic] = await self.download_links_repo.filter(  # type: ignore
            downloaded=False
        )
        if not res or not res.__root__:
            return None
        return res

    async def get_files_link_from_forum(self, category: str, link: str) -> ParserData:
        """Walk through forum, and get the links"""

        forum_threads: int = 0
        download_links_counter: int = 0
        errors: List[str] = []

        forum_links: LinksModelPydantic = await self.scrapper_repo.get_forum_urls(
            link=link, category=category
        )

        if not isinstance(forum_links, LinksModelPydantic):
            errors.append("No thread links found")
            return ParserData(forum_threads, download_links_counter, errors)

        forum_threads += len(forum_links.__root__)

        for element in forum_links.__root__:
            try:
                obj, _ = await self.link_model_repo.get_or_create(element)
                assert isinstance(obj, LinkModelPydantic)
            except Exception as e:
                errors.append(f"error for {element.for_clubbers_url}: {str(e)}")
                return ParserData(forum_threads, download_links_counter, errors)

            download_links: DownloadLinksPydantic
            not_known_managers: List[dict]

            (
                download_links,
                not_known_managers,
            ) = await self.scrapper_repo.get_download_links(
                link=obj.for_clubbers_url, category=category
            )

            if not_known_managers:
                errors.append(f"Not know managers: {not_known_managers}")

            if not isinstance(download_links, DownloadLinksPydantic):
                errors.append(f"No download links found for {obj.for_clubbers_url}")
                return ParserData(forum_threads, download_links_counter, errors)

            if download_links and (
                download_links_list := download_links.__root__  # noqa: E999
            ):
                download_links_counter += len(download_links_list)
                for download_link_obj in download_links_list:
                    await self.download_links_repo.get_or_create(download_link_obj)

        return ParserData(forum_threads, download_links_counter, errors)
