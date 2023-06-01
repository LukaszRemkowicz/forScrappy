import datetime as datetime
from logging import Logger
from typing import List, Type

from logger import get_module_logger
from reporter.manager import ReportMailer

logger: Logger = get_module_logger("db_repo")


class ReporterUseCase:
    reporter: Type[ReportMailer] = ReportMailer

    @classmethod
    async def send_report(
        cls,
        command: str,
        forum_threads_num: int,
        links_num: int,
        errors: List[str],
        date_time: datetime.date,
    ) -> None:
        """Sends report email"""

        cls.reporter(command).send_email(
            forum_threads_num=forum_threads_num,
            links_num=links_num,
            errors=errors,
            datetime=date_time,
        )
        logger.info("Report has been sent")
