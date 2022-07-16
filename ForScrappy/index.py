import argparse
import re
import datetime
import hashlib
import json
import pathlib
import sys
from contextlib import contextmanager
from logging import RootLogger
from timeit import default_timer
from typing import Tuple, Dict

import requests
from django.conf import settings
from fake_useragent import UserAgent
from requests import Session as SessionObj
from requests.cookies import RequestsCookieJar

from ForScrappy.parsers import TranceParser, HouseParser
from ForScrappy.logger import SetupLogger
from django.core.mail import send_mail


def create_parser():

    parser = argparse.ArgumentParser(description="Command line interface for 4clubbers.")

    parser.add_argument(
        '-lf',
        '--log-filename',
        dest='log_filename',
        help='custom file log name'
    )

    parser.add_argument('-tr', '--trance', dest='trance', action='store_true', help='Parse trance topic')
    parser.add_argument('-hs', '--house', dest='house', action='store_true', help='Parse house topic')
    parser.add_argument(
        '-p',
        '--pages',
        dest='pages',
        metavar='pages number',
        nargs='+',
        type=int,
        help='Choose pages number'
    )

    parser.add_argument(
        '-ufl',
        '--update-forum-links',
        dest='update_all',
        action='store_true',
        help='Parse forum link again'
    )

    parser.add_argument(
        '-ula', '--update-links-all',
        dest='update',
        action='store_true',
        help='Update all links if not name set'
    )

    parser.add_argument(
        '-ul', '--update-links-without-name',
        dest='update_partial',
        action='store_true',
        help='Update all links if not name set'
    )

    parser.add_argument(
        '-dl', '--download_all',
        dest='download',
        action='store_true',
        help='Download all mp3 with status False'
    )

    parser.add_argument(
        '-dl-one', '--download_one',
        dest='download_one',
        action='store_true',
        help='Download one mp3'
    )

    parser.add_argument(
        '-id',
        '--id',
        dest='id',
        metavar='Object id',
        nargs='+',
        type=int,
        help='Write object id'
    )

    return parser


class CmdLineInterface:

    def __init__(self):

        parser = create_parser()
        self.args = parser.parse_args()
        self.used_command = " ".join(sys.argv)
        custom_log_name = self.args.log_filename or None
        self.session = Session(filename=custom_log_name)
        self.logger = self.session.logger
        self.logged = self._login()

    def _login(self) -> Tuple[SessionObj, RequestsCookieJar, Dict]:

        base_url = settings.LOGIN_URL

        payload = {
            'vb_login_username': settings.USERNAME,
            'vb_login_password': '',
            's': '',
            'securitytoken': 'guest',
            'do': 'login',
            'vb_login_md5password': (hashlib.md5(settings.PASSWORD)).hexdigest(),
            'vb_login_md5password_utf': (hashlib.md5(settings.PASSWORD)).hexdigest()
        }

        user_agent = UserAgent()
        header = {'User-Agent': str(user_agent.chrome)}
        session = requests.Session()
        session.post(base_url, data=payload, headers=header)
        cookie = session.cookies

        return session, cookie, header

    def _close_connection(self, session: SessionObj) -> None:
        session.close()
        self.logger.info('Session closed')

    def parse(self) -> None:

        options = self.get_options()

        self.logger.debug(f'Session parameters: {options}')
        self.logger.debug(f'Session invoked with following parameters: {self.used_command}')
        self.logger.info(f'Session logs will be stored under name: {self.session.logfile}')
        session, cookie, header = self._login()

        session_obj = {
            'session': session,
            'cookie': cookie,
            'header': header
        }

        try:
            with self.elapsed_timer() as elapsed:
                elapsed()

                if self.args.trance and self.args.update_partial:

                    new_obj = TranceParser(self.logger)
                    new_obj.update_links_partial(**session_obj)

                elif self.args.trance and self.args.download_one:

                    new_obj = TranceParser(self.logger)
                    new_obj.page_range(**session_obj, category='trance', **options)

                elif self.args.trance and not self.args.update and not self.args.download:

                    new_obj = TranceParser(self.logger)
                    new_obj.page_range(**session_obj, category='trance', **options)

                elif self.args.trance and self.args.download:

                    new_obj = TranceParser(self.logger)
                    new_obj.download_all(**session_obj, music_type='trance')

                elif self.args.trance and self.args.update:

                    new_obj = TranceParser(self.logger)
                    new_obj.update_links(**session_obj)

                elif self.args.house and self.args.update_partial:

                    new_obj = HouseParser(self.logger)
                    new_obj.update_links_partial(**session_obj)

                elif self.args.house and self.args.download_one:

                    new_obj = HouseParser(self.logger)
                    new_obj.page_range(**session_obj, category='house', **options)

                elif self.args.house and self.args.download:

                    new_obj = HouseParser(self.logger)
                    new_obj.download_all(**session_obj, music_type='house')

                elif self.args.house and self.args.update:

                    new_obj = HouseParser(self.logger)
                    new_obj.update_links(**session_obj)

                elif self.args.house and self.args.update_partial:

                    new_obj = HouseParser(self.logger)
                    new_obj.update_links_partial(**session_obj)

                elif self.args.house and not self.args.update and not self.args.download:

                    new_obj = HouseParser(self.logger)
                    new_obj.page_range(**session_obj, category='house', **options)

            self._close_connection(session)
            time_elapsed = elapsed()

            if time_elapsed > 60:
                result = f'{int(time_elapsed // 60)} min and {time_elapsed % 60} s.'
            else:
                result = f'{time_elapsed} s'

            result = re.sub(r'([^\n].*)\.([^\n].*)', r'\1', result)
            self.logger.info(f'Finished in {result} s')

            title = f'[4scrappy] Sukces {self.session.id}'
            message = f'Wykonywanie komendy {self.used_command} zakonczylo sukcesem.' \
                      f'\n\n Więcej szczegółów znjdziesz: {self.session.logfile} \n\n v{settings.VERSION}'

            send_mail(title, message, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL])

        except Exception as e:

            title = f'[ForScrappy] Nie powodzenie. {self.session.id}'
            message = f'Wykonywanie komendy {self.used_command} zakonczylo sie bledem  ' \
                      f'"{e}" -------------- \n\n  Więcej szczegółów znjdziesz: ' \
                      f'{self.session.logfile} v{settings.VERSION}'
            self.logger.exception(f'error during command execution {self.used_command}:')

            send_mail(title, message, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL])

    @contextmanager
    def elapsed_timer(self):

        start = default_timer()
        elapser = lambda: default_timer() - start
        yield lambda: elapser()
        end = default_timer()
        elapser = lambda: end - start

    def get_options(self) -> Dict:
        return {
            'pages': self.args.pages,
            'update_all': self.args.update_all,
            'id_obj': self.args.id
        }


class Session:
    """  Class to take control over session. Keep logs, data in sync. one logger, one session """

    session_filename = 'linkssesion.json'
    session_path = '..'

    def __init__(self, session_id=None, filename=None):
        self.session_id = session_id or self.get_new_session_id()
        self._current_session_logfile = filename or f'session_{self.session_id}'
        self.logger = self._setup_session_logger()

        self.content = self.get_or_create_content()

        self.logger.info(f'session ID: {self.session_id}')

    @property
    def id(self):
        return self.session_id

    def set_id(self, id_):
        self.session_id = id_

    @property
    def logfile(self):
        return self._current_session_logfile

    def _setup_session_logger(self) -> RootLogger:
        logging_settings = {'console_handler': True}

        self.logger = SetupLogger(
            logfile=self._current_session_logfile,
            settings=logging_settings,
            root_path=settings.LOGGING_ROOT_PATH
        ).get_logger()

        print(f'session logs: {self._current_session_logfile}')
        return self.logger

    def get_new_session_id(self) -> str:
        return datetime.datetime.now().strftime('%y%m%d-%H%M%S')

    def create_session_cookie(self) -> Dict:
        return {'id': self.get_new_session_id(), 'data': {}}

    def set_session_content(self):
        pass

    def get_or_create_content(self) -> Dict:
        session_file = pathlib.Path(self.session_path, self.session_filename)

        if session_file.exists():
            with open(session_file, 'r') as sessionFile:
                data = json.load(sessionFile)
                if data.get(self.session_id):
                    self.logger.info(f'Session cookie exists with id:{self.session_id}')
                    return data.get(self.session_id)
                else:
                    self.logger.info(f'Creating new session cookie for id:{self.session_id}')
                    data[self.session_id] = self.create_session_cookie()
        else:
            with open(session_file, 'w') as sessionFile:
                data = {self.session_id: self.create_session_cookie()}
                json.dump(data, sessionFile, indent=4, ensure_ascii=False)

        with open(session_file, 'w') as sessionFile:
            json.dump(data, sessionFile, indent=4, ensure_ascii=False)

        return data[self.session_id]


if __name__ == '__main__':
    CmdLineInterface().parse()
