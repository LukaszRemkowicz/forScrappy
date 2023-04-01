from typing import Type

from requests import Session

from models.types import SessionObject
from repos.api_repo import ForClubbersScrapper
from repos.db_repo import LinkRepo


class ForClubUseCase:
    def __init__(
        self,
        repo_db: Type["LinkRepo"],
        repo_scrapper: Type["ForClubbersScrapper"],
        session_obj: ["SessionObject"]
    ) -> None:
        self.db_repo = repo_db()
        self.scrapper_repo = repo_scrapper(session_obj)

    async def walk_thru_forum(self, category: str, link: str):
        res = await self.scrapper_repo.get_forum_urls(link=link, category=category)
        res_2 = await self.scrapper_repo.get_download_links(link=link, category=category)
        breakpoint()
