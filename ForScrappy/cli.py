import datetime
from logging import Logger
from time import sleep
from typing import List, Optional

import sentry_sdk
import typer
from logger import get_module_logger
from models.entities import DownloadLinksPydantic
from models.types import ParserData, SessionObject
from reporter.use_case import ReporterUseCase
from repos.db_repo import DownloadLinksRepo, LinkModelRepo
from repos.request_repo import ForClubbersScrapper
from settings import settings
from use_case.use_case import ForClubUseCase
from utils.decorators import be_async
from utils.login import User
from utils.utils import DBConnectionHandler, LinkValidator, validate_category

logger: Logger = get_module_logger("db_repo")


app = typer.Typer()
reporter: ReporterUseCase = ReporterUseCase()


sentry_sdk.init(
    dsn=settings.sentry.dsn,
    traces_sample_rate=1.0,
    environment=settings.environment,
)


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

        thread_num: int = 0
        download_links_num: int = 0
        errors: List[str] = []

        for link in links:
            res: ParserData = await forum_use_case.get_files_link_from_forum(
                category=category, link=link
            )
            thread_num += res.thread_num
            download_links_num += res.download_links_num
            errors.extend(res.errors)

        await reporter.send_report(
            command="get-forum-links",
            forum_threads_num=thread_num,
            links_num=download_links_num,
            errors=errors,
            date_time=datetime.datetime.now(),
        )
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
    app()
