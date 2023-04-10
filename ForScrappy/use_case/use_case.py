from typing import Type, Optional, List

from models.entities import Links
from models.models import DownloadLinks
from models.types import SessionObject
from repos.api_repo import ForClubbersScrapper
from repos.db_repo import LinkRepo, DownloadRepo


class ForClubUseCase:
    def __init__(
        self,
        link_repo: Type["LinkRepo"],
        download_repo: Type["DownloadRepo"],
        repo_scrapper: Type["ForClubbersScrapper"],
        session_obj: Optional[SessionObject] = None,
    ) -> None:
        self.link_repo: LinkRepo = link_repo()
        self.download_repo: DownloadRepo = download_repo()
        self.scrapper_repo: ForClubbersScrapper = repo_scrapper(session_obj)

    async def choose_download_manager(self):
        ...

    async def download_file(self, link: DownloadLinks) -> None:
        ...

    async def get_links(self) -> List[DownloadLinks]:
        res: List[DownloadLinks] = await self.download_repo.filter(downloaded=False)

        return res

    async def get_files_link_from_forum(self, category: str, link: str) -> None:
        """Walk through forum, and get the links"""

        forum_links: Links = await self.scrapper_repo.get_forum_urls(
            link=link, category=category
        )

        for element in forum_links.__root__:
            obj, _ = await self.link_repo.get_or_create(element)

            download_links = await self.scrapper_repo.get_download_links(
                link=obj.for_clubbers_url, category=category
            )

            if download_links and (download_links_list := download_links.__root__):  # noqa: E999
                for link in download_links_list:
                    await self.download_repo.get_or_create(link)
