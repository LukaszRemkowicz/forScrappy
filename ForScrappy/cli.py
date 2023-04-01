from time import sleep

import typer
from requests import Session

from models.types import SessionObject
from repos.api_repo import ForClubbersScrapper
from repos.db_repo import LinkRepo
from use_case.use_case import ForClubUseCase
from utils.decorators import be_async
from utils.login import User
from utils.utils import DBConnectionHandler

from logger import ColoredLogger, get_module_logger
logger: ColoredLogger = get_module_logger("db_repo")


app = typer.Typer()


@app.command()
@be_async
async def fetch(
    category: str = typer.Option('trance', "-cat", help="category name"),
    link: str = typer.Option(..., "-link", help="Link to forum"),
) -> None:

    # async with DBConnectionHandler():

    session_obj: SessionObject = User.login()
    sleep(3)
    forum_use_case: ForClubUseCase = ForClubUseCase(
        repo_db=LinkRepo,
        repo_scrapper=ForClubbersScrapper,
        session_obj=session_obj
    )
    await forum_use_case.walk_thru_forum(category=category, link=link)

    logger.info("Command get_tfs_data finished with success")


@app.command()
@be_async
async def fetch_2(
    category: str = typer.Option('trance', "-cat", help="category name"),
    link: str = typer.Option(..., "-link", help="Link to forum"),
) -> None:

   ...

if __name__ == "__main__":
    app()
