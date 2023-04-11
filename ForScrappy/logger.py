import logging
import os
from datetime import datetime
from typing import Optional

from settings import ROOT_PATH


class ColoredFormatter(logging.Formatter):
    default_msec_format: str = "%s"

    @staticmethod
    def message_formatter() -> str:
        """Custom message formatter"""

        return "%(asctime)s [%(name)s] - [%(levelname)s] - %(message)s (%(filename)s:%(lineno)d)"

    @property
    def colours(self) -> dict:
        """Custom logger level colour formatter"""

        return {
            "DEBUG": self.grey + self.message_formatter() + self.reset,
            "INFO": self.green + self.message_formatter() + self.reset,
            "WARNING": self.red + self.message_formatter() + self.reset,
            "ERROR": self.red + self.message_formatter() + self.reset,
            "CRITICAL": self.bold_red + self.message_formatter() + self.reset,
            "WELCOME_MSG": self.welcome
            + self.message_formatter().replace("(%(filename)s:%(lineno)d)", "")
            + self.reset,
        }

    def __init__(self, use_color=True):
        logging.Formatter.__init__(self)
        self.use_color = use_color
        self.grey: str = "\x1b[38;20m"
        self.blue: str = "\x1b[38;5;39m"
        self.yellow: str = "\x1b[33;20m"
        self.red: str = "\x1b[31;20m"
        self.bold_red: str = "\x1b[31;1m"
        self.green: str = "\x1b[38;5;190m"
        self.welcome: str = "\x1b[38;5;222m"

        self.reset: str = "\x1b[0m"

    def format(self, record) -> str:
        colour: Optional[str] = self.colours.get(record.levelname)
        formatter: logging.Formatter = logging.Formatter(colour)
        return formatter.format(record)


class ColoredLogger(logging.Logger):
    """Custom logger with extra levels"""

    def __init__(self, name):
        logging.Logger.__init__(self, name, logging.DEBUG)
        logging.addLevelName(90, "WELCOME_MSG")

        color_formatter: ColoredFormatter = ColoredFormatter()

        console: logging.StreamHandler = logging.StreamHandler()
        console.setFormatter(color_formatter)

        log_dir: str = os.path.join(ROOT_PATH, "logs")

        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        file_handler: logging = logging.FileHandler(
            f"{log_dir}/{datetime.now().date()}.log"
        )

        formatter: logging.Formatter = logging.Formatter(
            "%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s"
        )
        file_handler.setFormatter(formatter)

        self.addHandler(console)
        self.addHandler(file_handler)
        self.addHandler(logging.FileHandler(f"{log_dir}/{datetime.now().date()}.log"))
        self.setLevel(logging.INFO)
        return

    def welcome_msg(self, msg, *args, **kw) -> None:
        """Custom logger level"""

        self.log(90, msg, *args, **kw)


def get_module_logger(mod_name: str) -> ColoredLogger:
    """
    returns logger. Example usage:
    logger = get_module_logger('name')
    """
    logging.setLoggerClass(ColoredLogger)
    return logging.getLogger(mod_name)  # type: ignore


# get_module_logger("TESTING_LOGGER").welcome_msg("Welcome")
