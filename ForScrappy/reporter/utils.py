import smtplib
import ssl
from contextlib import contextmanager

from settings import settings


@contextmanager
def setup_email():
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(
        settings.email.host, settings.email.port, context=context
    ) as server:
        server.starttls()
        server.login(settings.email.username, settings.email.password.get_secret_value())
        yield
