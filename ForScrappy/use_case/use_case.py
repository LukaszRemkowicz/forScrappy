from typing import Type, Optional, List, Dict

from models.entities import DownloadLinksPydantic, LinksModelPydantic
from models.models import DownloadLinks
from models.types import SessionObject
from repos.parser_repo import KrakenParser
from repos.request_repo import ForClubbersScrapper
from repos.db_repo import LinkModelRepo, DownloadLinksRepo
from settings import MANAGERS
from use_case.managers.kraken import Kraken, ManagerType
from utils.exceptions import LinkPostFailure, HashNotFoundException
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
    async def choose_download_manager(url: str) -> Type[ManagerType]:

        managers = {
            "krakenfiles": KrakenParser,
        }

        for manager in MANAGERS:
            if manager in url:
                try:
                    res: Type[ManagerType] = managers[manager]
                    return res
                except KeyError:
                    raise ValueError(f"Manager not found for {url}")

    async def download_file(self, link_obj: DownloadLinks) -> None:
        url: str = link_obj.link
        manager: Type[ManagerType] = await self.choose_download_manager(url)

        dl_link: str
        headers: Dict[str, str]

        obj: Optional[DownloadLinks] = await DownloadLinks.filter(
            link=url
        ).first()

        try:
            response: Dict = await self.scrapper_repo.parse_download_link(
                url=url, parser=manager
            )
            await self.download_links_repo.update_fields(
                obj=obj,
                download_link=url,
                published_date=response.get("published_date"),
                name=response.get("name"),
            )
        except (LinkPostFailure, HashNotFoundException) as e:
            await self.download_links_repo.update_fields(
                obj=obj,
                download_link=url,
                error=True,
                error_message=f'{obj.error_message}; {str(e)}'
            )
            return

        dl_link = response['dl_link']
        headers = response['headers']
        file_path = get_folder_name_from_date(response['published_date'])

        await self.scrapper_repo.download_file(
            dl_link=dl_link, headers=headers, file_path=file_path, object_id=obj.pk
        )

    async def get_links_with_errors(self) -> List[DownloadLinks]:
        """Return links with errors"""
        res: List[DownloadLinks] = await self.download_links_repo.filter(error=True)
        return res

    async def get_links(self) -> List[DownloadLinks]:
        res: List[DownloadLinks] = await self.download_links_repo.filter(downloaded=False)  # type: ignore

        return res

    async def get_files_link_from_forum(self, category: str, link: str) -> None:
        """Walk through forum, and get the links"""

        forum_links: LinksModelPydantic = await self.scrapper_repo.get_forum_urls(
            link=link, category=category
        )

        for element in forum_links.__root__:
            obj, _ = await self.link_model_repo.get_or_create(element)

            download_links: DownloadLinksPydantic = (
                await self.scrapper_repo.get_download_links(
                    link=obj.for_clubbers_url, category=category
                )
            )

            if download_links and (
                download_links_list := download_links.__root__  # noqa: E999
            ):
                for download_link_obj in download_links_list:
                    await self.download_links_repo.get_or_create(download_link_obj)
