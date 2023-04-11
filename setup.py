from os import path

from distutils.core import setup

here = path.abspath(path.dirname(__file__))

setup(
    name="for_scrappy",
    version="1.1.0",
    author="l.remkowicz",
    author_email="l.remkowicz@gmail.com",
    setup_requires=["setuptools>=38.6.0", "pytest"],
    install_requires=[
        "aerich==0.7.1",
        "aiosqlite==0.17.0; python_version >= '3.6'",
        "amqp==5.1.1; python_version >= '3.6'",
        "async-timeout==4.0.2; python_full_version <= '3.11.2'",
        "asyncpg==0.27.0",
        "beautifulsoup4==4.12.2",
        "billiard==3.6.4.0",
        "celery==5.2.7",
        "certifi==2022.12.7; python_version >= '3.6'",
        "charset-normalizer==3.1.0; python_version >= '3.7'",
        "click==8.1.3; python_version >= '3.7'",
        "click-didyoumean==0.3.0; python_version < '4.0' and python_full_version >= '3.6.2'",
        "click-plugins==1.1.1",
        "click-repl==0.2.0",
        "colorama==0.4.6; platform_system == 'Windows'",
        "decorator==5.1.1; python_version >= '3.5'",
        "dictdiffer==0.9.0",
        "flower==1.2.0",
        "greenlet==2.0.2; platform_machine == 'aarch64' or (platform_machine == 'ppc64le' "
        "or (platform_machine == 'x86_64' or (platform_machine == 'amd64' "
        "or (platform_machine == 'AMD64' or (platform_machine == 'win32' or platform_machine == 'WIN32')))))",
        "humanize==4.6.0; python_version >= '3.7'",
        "idna==3.4; python_version >= '3.5'",
        "iso8601==1.1.0; python_version < '4.0' and python_full_version >= '3.6.2'",
        "kombu==5.2.4; python_version >= '3.7'",
        "lxml==4.9.2",
        "prometheus-client==0.16.0; python_version >= '3.6'",
        "prompt-toolkit==3.0.38; python_version >= '3.7'",
        "psycopg2==2.9.6",
        "pydantic==1.10.7",
        "pypika-tortoise==0.1.6; python_version >= '3.7' and python_version < '4.0'",
        "python-dateutil==2.8.2",
        "python-dotenv==1.1.0",
        "pytz==2023.3",
        "redis==4.5.4",
        "requests==2.28.2",
        "six==1.16.0; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
        "soupsieve==2.4; python_version >= '3.7'",
        "sqlalchemy==2.0.9",
        "tomlkit==0.11.7; python_version >= '3.7'",
        "tornado==6.2; python_version >= '3.7'",
        "tortoise-orm==0.19.3",
        "typer==0.7.0",
        "typing-extensions==4.5.0; python_version >= '3.7'",
        "urllib3==1.26.15; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4, 3.5'",
        "validators==0.20.0",
        "vine==5.0.0; python_version >= '3.6'",
        "wcwidth==0.2.6",
    ],
)
