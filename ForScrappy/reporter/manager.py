import calendar
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional, Tuple

import jinja2
from jinja2 import Template
from settings import ROOT_PATH, settings


class BaseManagerMixin:
    """Base mailer manager, responsible for sending emails"""

    subject: str
    template_path: str

    def render_template(self, **kwargs) -> str:
        raise NotImplementedError

    def prepare_context(self, **kwargs) -> Tuple[str, List[str], MIMEMultipart]:
        """Prepares context for the email"""

        html: str = self.render_template(**kwargs)

        msg: MIMEMultipart = MIMEMultipart("alternative")
        from_: str = settings.email.from_

        msg["From"] = settings.email.from_
        msg["Subject"] = self.subject
        msg["To"] = settings.email.to_

        msg.attach(MIMEText(html, "html"))

        return from_, [settings.email.to_], msg

    def send_email(self, **kwargs) -> None:
        """sends email main method"""

        context: ssl.SSLContext = ssl.create_default_context()

        with smtplib.SMTP_SSL(
            settings.email.host, settings.email.port, context=context
        ) as server:
            server.login(
                settings.email.username, settings.email.password.get_secret_value()
            )
            _from, to_list, msg = self.prepare_context(**kwargs)
            server.sendmail(_from, to_list, msg.as_string())


class ReportMailer(BaseManagerMixin):
    """Report mailer manager, responsible for sending emails (reports)"""

    def __init__(self, command: str, template_name: Optional[str] = None) -> None:
        self.command = command
        self.subject = (
            f'Hello there. You got a mail. Here is a command "{self.command}" report'
        )
        self.templates_path = Path(ROOT_PATH) / "reporter/templates"
        self.template_name = template_name or "report.html"

    @staticmethod
    def add_static_files(**kwargs) -> dict:
        """adds static files url to the context"""

        base_url: str = settings.nginx.base_url
        kwargs["ico02"] = f"{base_url}ICON-02.png"
        kwargs["ico03"] = f"{base_url}ICON-03.png"
        kwargs["ico05"] = f"{base_url}ICON-05.png"
        kwargs["calendar_check"] = f"{base_url}CalendarCheck.png"
        kwargs["header_bg"] = f"{base_url}Header-bg.png"

        return kwargs

    @staticmethod
    def __postfix(n: int) -> str:
        """adds postfix to the day: th, st, nd, rd"""

        postfix: str = (
            "th" if 4 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        )
        return str(n) + postfix

    def prepare_datatime_elements(self, **kwargs) -> dict:
        """
        prepares datetime elements for the jinja template. Template needs to be formatted
         a month, day, year, hour. Expected example:
          {
            "month_short": "Jan",
            "day": "1st",
            "year": 2021,
            "hour": "12:00PM",
          }
        """

        kwargs["month_short"] = calendar.month_abbr[kwargs["datetime"].month]
        kwargs["day"] = self.__postfix(kwargs["datetime"].day)
        kwargs["year"] = datetime.now().year
        kwargs["hour"] = kwargs["datetime"].strftime("%I:%M%p")

        return kwargs

    def render_template(self, **kwargs) -> str:
        """renders a Jinja template into HTML"""

        if not (Path(self.templates_path) / self.template_name).exists():
            raise Exception(f"Template {self.template_name} not found")

        template_loader: jinja2.FileSystemLoader = jinja2.FileSystemLoader(
            searchpath=str(self.templates_path)
        )
        template_env: jinja2.Environment = jinja2.Environment(loader=template_loader)
        templ: Template = template_env.get_template(self.template_name)
        kwargs = self.add_static_files(**kwargs)
        kwargs = self.prepare_datatime_elements(**kwargs)
        kwargs["command_name"] = self.command

        return templ.render(**kwargs)


#
# ReportMailer("test").send_email(
#     template_name="report.html",
#     forum_threads_num=10,
#     links_num=9,
#     errors=[],
#     datetime=datetime.now(),
# )
