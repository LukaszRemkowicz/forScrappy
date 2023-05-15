from logging import Logger
from time import sleep
from typing import List, Optional

import typer

from models.entities import DownloadLinksPydantic
from models.types import SessionObject
from repos.request_repo import ForClubbersScrapper
from repos.db_repo import LinkModelRepo, DownloadLinksRepo
from use_case.use_case import ForClubUseCase
from utils.decorators import be_async
from utils.login import User
from utils.utils import DBConnectionHandler, LinkValidator, validate_category

from logger import get_module_logger

logger: Logger = get_module_logger("db_repo")


app = typer.Typer()


@app.command()
@be_async
async def get_forum_links(
    link: str = typer.Option(..., "-link", help="Link to forum"),
    page: int = typer.Option(0, "-p", help="Forum page number to fetch"),
) -> None:
    async with DBConnectionHandler():
        async with LinkValidator(link):
            ...

        category: str = validate_category(link=link)

        session_obj: SessionObject = User.login()
        sleep(3)
        forum_use_case: ForClubUseCase = ForClubUseCase(
            link_repo=LinkModelRepo,
            download_repo=DownloadLinksRepo,
            repo_scrapper=ForClubbersScrapper,
            session_obj=session_obj,
        )

        links: List[str] = []

        if page >= 2:
            for page_no in range(1, page):
                new_link = f"{link}{page_no}"
                links.append(new_link)

        links.append(link)

        for link in links:
            await forum_use_case.get_files_link_from_forum(category=category, link=link)

        logger.info("Command get-forum-links finished with success")


@app.command()
@be_async
async def download_fetched() -> None:
    forum_use_case: ForClubUseCase = ForClubUseCase(
        link_repo=LinkModelRepo,
        download_repo=DownloadLinksRepo,
        repo_scrapper=ForClubbersScrapper,
    )
    async with DBConnectionHandler():
        res: Optional[DownloadLinksPydantic] = await forum_use_case.get_links()
        if res and res.__root__:
            for link_obj in res.__root__:
                await forum_use_case.download_file(link_obj=link_obj)

    logger.info("Command download-fetched with success")


@app.command(help="Get links with errors. Make sure celery tasks are completed")
@be_async
async def files_with_errors() -> None:
    forum_use_case: ForClubUseCase = ForClubUseCase(
        link_repo=LinkModelRepo,
        download_repo=DownloadLinksRepo,
        repo_scrapper=ForClubbersScrapper,
    )
    async with DBConnectionHandler():
        res: Optional[
            DownloadLinksPydantic
        ] = await forum_use_case.get_links_with_errors()

        if res:
            logger.info("LinksModelPydantic with errors:")
            for link in res.__root__:
                if link is not None:
                    logger.info(f"{link.link} - {link.error}")
        else:
            logger.info("No links with errors found")


if __name__ == "__main__":
    # os.environ['PYTHONASYNCIODEBUG'] = '1'
    app()
