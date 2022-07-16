import functools
import os
import re
import urllib.request
from datetime import datetime
from logging import RootLogger
from typing import Tuple, Union, Dict
from urllib.error import URLError

from gevent import contextvars  # type: ignore
import asyncio

import pytesseract
from dateutil.parser import ParserError
from django.conf import settings

from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
application = get_wsgi_application()

from django.core.files import File
from django.db.models import Q, QuerySet
from requests import Session, Response
from requests.cookies import RequestsCookieJar
from django.core.exceptions import ValidationError
from bs4 import BeautifulSoup, SoupStrainer

from ForScrappy.utils import eval_simple_function
from data.models import LinkModel, ZippyLinks
from .dumper import FileDumper


class Download:

    def __init__(self, logger):
        self.logger = logger

    def save(self, file: ZippyLinks, music_type: str) -> None:
        """ Save object on hard drive """

        self.logger.info(f'Downloading: {file.name}')
        assert hasattr(file, 'published_date')

        if not hasattr(file, 'published_date'):
            self.logger.error(f'Error occurred. File dont have published date: {file.name}')
            raise AttributeError('File dont have published date')

        month, year = file.published_date.month, file.published_date.year
        folder_name = self.get_or_create((month, year), music_type)

        file_name = os.path.join(os.getcwd(), folder_name, file.name + '.mp3')

        if os.path.exists(file_name):
            self.logger.info(f'File {file.name} exists')
            file.downloaded = True
            file.save()
            return

        try:
            download_file = urllib.request.urlretrieve(file.download_link, file_name)
        except (URLError, ValueError) as e:

            self._error_message('Error occurred when downloading', e, file)
            return

        file_size = os.stat(download_file[0]).st_size / (1024 * 1024)

        if file_size <= 5:
            self._error_message(f'Something went wrong: file {file.id} has no size')
            raise Exception('File size is too small')

        try:
            file.downloaded = True
            file.downloaded_date = datetime.now()
            file.save()

            self.logger.info(f'Success downloading {file.name}')

        except Exception as e:

            self._error_message('Error occurred when saving to model', file, e)

    def get_or_create(self, date: Tuple, folder_name: str) -> str:
        """ get destination folder or create """

        month, year = date

        main_folder = os.path.join(settings.BASE_DIR, 'ForScrappy', 'downloaded', folder_name)
        year_fold = os.path.join(main_folder, str(year))
        month_fold = os.path.join(main_folder, str(year), str(month))

        folder_exists = [main_folder, year_fold, month_fold]

        for folder in folder_exists:
            if not os.path.exists(folder):

                try:
                    os.mkdir(folder)
                except FileNotFoundError as e:
                    self.logger.error(e)
                    raise e

        return month_fold

    def _error_message(
            self, message: str, file: Union[ZippyLinks, None] = None, error: Union[Exception, None] = None
    ) -> None:
        """ Log error messages """

        if error:
            self.logger.error(error)

        if file:
            file.error = True
            if file.error_message:
                file.error_message = file.error_message + ';' + message
            else:
                file.error_message = message

        if not file and not error:
            self.logger.error(message)


class Mainparser:

    def __init__(self, logger: RootLogger):

        self.logger = logger
        self.error = 'File has expired and does not exist anymore on this server'
        self.fileDoesNotExist = 'File does not exist on this server'
        self.dumper = FileDumper(self.logger)

    def parse_forum(
            self,
            session: Session,
            cookie: RequestsCookieJar,
            header: dict, topic: Response,
            category: str
    ) -> None:
        """ Parse zippyshare links from threads """

        assert isinstance(category, str), "Category is not a string!"
        assert isinstance(topic, Response), "Topic body is not a response object"

        if not isinstance(topic, Response):
            self.logger.error('Critical error. Topic object is not Response object')
            return

        soup = BeautifulSoup(topic.text, parse_only=SoupStrainer("td"), features="lxml")
        all_a_href_tags = soup.findAll("a")
        regex = re.compile(rf'{category}/\d.?')

        if not isinstance(category, str):
            category = str(category)

        for tr in all_a_href_tags:

            self.logger.info(f'parsing forum. Looking for zippy links...')
            links = tr.get('href')

            if links and category in links and regex.search(links) and links[-5::].isdigit():

                html_regex = r'(.+)(html)(.+)'
                link = re.sub(html_regex, r'\1\2', links)

                assert isinstance(self.validate_url(link), str), "Not a valid url link"

                if not self.validate_url(link):
                    self.logger.error(f'Url is not valid {link}')
                    return

                clubbers_link, created = LinkModel.objects.get_or_create(
                    for_clubbers_url=link
                )

                enter_topic = session.get(link, cookies=cookie, headers=header)
                soupe = BeautifulSoup(enter_topic.content, parse_only=SoupStrainer("div"), features="lxml")

                get_topic_name = BeautifulSoup(
                    enter_topic.content, "html.parser"
                ).find("meta", property="og:title").get('content')

                clubbers_link.name = get_topic_name
                clubbers_link.save()

                get_a_href_tags = soupe.findAll('a')

                get_all_zippy_links = set(
                    [element.get('data-url') for element in get_a_href_tags
                     if element.get('data-url') and 'zippyshare.com' in element.get('data-url')
                     ])

                for link in get_all_zippy_links:
                    ZippyLinks.objects.get_or_create(
                        link=link,
                        defaults={
                            'link_model': clubbers_link,
                            'category': category
                        }
                    )

    def parse_zippy(
            self,
            session: Session,
            cookie: RequestsCookieJar,
            header: dict,
            links: QuerySet,
            update_all: bool = False
    ) -> ZippyLinks:
        """ parse zippyshare download links from links """

        counter = 0

        for link in links:

            # Can't use it, because zippy links control numbers are changing a lot.
            """
            counter += 1
            
            html_dump_file_path = f'zippy/{link.link_model.for_clubbers_url.split("/")[-1]}'

            if self.dumper.file_exists(html_dump_file_path) and not update_all:

                if not update_all:

                    if counter % 300 == 0:
                        print('Link dumped.. looping')
                    continue

                start_session = self.dumper.load(html_dump_file_path)
                self.logger.info(f'Parsing html file... {html_dump_file_path}')

            else:
            
                page = requests.get(link.link)
                self.dumper.dump(html_dump_file_path, page.content)
            """

            start_session = session.get(link.link, cookies=cookie, headers=header).text
            self.logger.info(f'Parsing link... {link.link}')

            parse_lrbox = BeautifulSoup(start_session, parse_only=SoupStrainer("div", id='lrbox'), features="lxml")

            hostname = self.parse_hostname(link.link)
            name = self.parse_name(parse_lrbox.text)

            if name == 'error':
                self._error(f'{link.link} - {self.error}', link)
                continue

            date = self.parse_date(parse_lrbox.text)
            script_tag_result = self.parse_script_tag(parse_lrbox)

            if script_tag_result == 'error':
                self._error(f'{self.error} - {link.link}', link)
                continue

            string_one, numbers, string_two = script_tag_result
            link_to_file = hostname + string_one + str(numbers) + string_two

            if not name and name != 'error':

                link.error = True
                link.error_message = 'NO FILE NAME'

                path_to_file, file_name = self.get_img_with_name(parse_lrbox, link)

                if path_to_file and file_name:

                    link.img_name.save(file_name + '.jpg', File(open(path_to_file, "rb")))
                    name = self.get_name_from_img(path_to_file)
                    link.error_message = 'NO FILE NAME - PARSED FROM IMG'
                else:
                    name = 'NO FILE NAME'

            link.download_link = link_to_file
            link.published_date = date or ''
            link.name = self.printify_name(name)
            link.save()

    @staticmethod
    def validate_url(url: str) -> Union[str, None]:

        from django import forms
        f = forms.URLField()

        try:
            f.clean(url)
        except ValidationError:
            return None

        return f.clean(url)

    def _error(self, message: str, model: ZippyLinks) -> None:

        self.logger.error(message)
        model.not_exists = True
        model.error_message = self.error
        model.save()

    def parse_date(self, soup: str) -> Union[datetime, str]:

        from dateutil import parser  # not working when date is 12/06/2022. Returns december
        regex_date = r'(.+)(Uploaded: )(.+)(Last)(.+)'
        date = re.sub(regex_date, r'\3', soup.replace('\n', ''))

        assert datetime.strptime(date, '%d-%m-%Y %H:%M')

        try:
            # parse_date = parser.parse(re.sub(regex_date, r'\3', soup.replace('\n', '')))
            date = datetime.strptime(date, '%d-%m-%Y %H:%M')
            return date
        except (ValueError, ParserError) as e:
            self.logger.error(e)
            return ''

    def parse_name(self, soup: str) -> str:

        regex = r'(.+)(Name: )(.+)(Size)(.+)'
        name = re.sub(regex, r'\3', soup.replace('\n', ''))

        if not name.replace(' ', ''):
            name = name.replace(' ', '')

        if self.error in name or self.fileDoesNotExist in name:
            return 'error'

        return name

    @staticmethod
    def parse_hostname(link: str) -> str:

        parse_hostname = re.compile(r'(.+)(www)(.+)(com)(.+?)(.+)')
        return re.sub(parse_hostname, r'\1\2\3\4', link)

    def parse_script_tag(self, soup: BeautifulSoup) -> Union[Tuple[str, str, str], str]:

        if self.error in soup or self.fileDoesNotExist in soup:
            return 'error'

        parse_js_scripts = soup.findAll('script')
        script_tag = [str(zips) for zips in parse_js_scripts if 'mp3' in str(zips) or 'wav' in str(zips)]

        assert len(script_tag) >= 1, "Script tag list is empty"

        if script_tag:
            script_tag_splitted = [element.split(';') for element in script_tag]
        else:
            return 'error'

        if len(script_tag_splitted) >= 1:
            script_tag_splitted = script_tag_splitted[0]

            regex = re.compile(r'(.+)(href = )(.+)')
            su = re.sub(regex, r'\3', str(script_tag_splitted[0].split('\n')[1]))

            assert su is not None

            if su:

                regex = r'(\")(.+)(\")(.+)(\")(.+)(\")'
                string_one = re.sub(regex, r'\2', su)
                numbers = eval_simple_function(re.sub(regex, r'\4', su)[2:-3].replace(' ', ''))
                string_two = re.sub(regex, r'\6', su)

                if not string_one and not numbers and not string_two:
                    return 'error'
            else:
                return 'error'
        else:
            return 'error'

        return string_one, numbers, string_two

    async def to_thread(self, func, /, *args, **kwargs):
        """ Create asyncio to_thread func """

        loop = asyncio.get_running_loop()
        ctx = contextvars.copy_context()
        func_call = functools.partial(ctx.run, func, *args, **kwargs)
        return await loop.run_in_executor(None, func_call)

    def _find_words(self, name: str) -> Union[str, None]:
        """ Recursive removing unnecessary characters """

        new_name = ''

        assert len(settings.REMOVE_FROM_NAME) >= 1, "Settings list REMOVE_FROM_NAME is empty"

        if not settings.REMOVE_FROM_NAME:
            return

        for element in settings.REMOVE_FROM_NAME:

            if element.lower() in name:
                if element == '_':
                    new_name = name.replace(element.lower(), ' ')
                    break

                else:
                    new_name = name.replace(element.lower(), '')
                    break

        for element in settings.REMOVE_FROM_NAME:
            if element.lower() in new_name and element != '':
                new_name = self._find_words(new_name)

        if new_name == '':
            new_name = name

        return new_name

    def printify_name(self, name: str) -> Union[str, None]:

        name = name.strip().lower()

        assert len(name) >= 1, "Name is empty"

        if not name:
            return

        try:
            new_name = self._find_words(name)
        except RecursionError as e:
            self.logger.error(f'maximum recursion depth exceeded in {name}. \n {e}')
            new_name = name

        starts_with = re.compile(r'^\d\d-')
        if re.match(starts_with, new_name):
            new_name = re.sub(starts_with, '', new_name)

        starts_with = re.compile(r'^\d\d ')
        if re.match(starts_with, new_name):
            new_name = re.sub(starts_with, '', new_name)

        starts_with = re.compile(r'^\d\d\.')
        if re.match(starts_with, new_name):
            new_name = re.sub(starts_with, '', new_name)

        ends_with = re.compile(r'\.$')
        if len(re.findall(ends_with, new_name)) >= 1:
            new_name = re.sub(ends_with, '', new_name)

        new_name = new_name.lower().replace('.mp3', '')
        new_name = new_name.lower().replace('|', '')
        new_name = new_name.lower().replace('_', '')
        new_name = new_name.lower().replace('M_O_R_P_H', 'M.O.R.P.H')
        new_name = new_name.lower().replace('?', '')

        return new_name.title()

    def get_img_with_name(
            self, soup_obj: BeautifulSoup, link_obj: LinkModel) -> Union[Tuple[str, str], Tuple[None, None]]:
        """ Try to get image from website. Img usually include song name """

        find_img_tag = [
            element.get('src') for element in soup_obj.findAll('img') if 'fileName' in element.get('src')
        ]

        if len(find_img_tag) >= 1:

            get_https = link_obj.link.split('//')[0]
            get_host_name = ''.join(link_obj.link.split('//')[1]).split('/')[0]

            link_to_file = get_https + '//' + get_host_name + find_img_tag[0]
            file_name_by_date = datetime.now().strftime('%m.%Y.%d-%H%M%S')

            create_file_path = os.path.join(os.getcwd(), 'link_names_imgs', file_name_by_date + '.jpg')
            urllib.request.urlretrieve(link_to_file, create_file_path)

            return create_file_path, file_name_by_date

        else:
            return None, None

    def get_name_from_img(self, img_path: str) -> str:
        return self.printify_name(pytesseract.image_to_string(img_path, config='--psm 10 --oem 3'))


class TranceParser(Mainparser):

    def __init__(self, logger):

        super().__init__(logger)
        self.link = 'http://www.4clubbers.com.pl/trance/'
        self.download_manager = Download(logger)
        self.category = 'Trance'

    def page_range(
            self,
            session: Session,
            cookie: RequestsCookieJar,
            header: dict,
            category: str,
            pages: Union[list, None] = None,
            update_all: bool = False,
            id_obj: Union[int, None] = None,
    ) -> None:

        session_options = {
            'session': session,
            'cookie': cookie,
            'header': header
        }

        if id_obj:
            assert isinstance(id_obj, list), "Id obj is not a list"
            assert len(id_obj) >= 1, "id list is empty"
            assert isinstance(id_obj[0], int), "Element is not integer"

            if len(id_obj) >= 1 and isinstance(id_obj[0], int):
                zippy = ZippyLinks.objects.filter(id=id_obj[0])

                if zippy.exists():
                    self.parse_zippy(**session_options, links=zippy)
                    self.download_manager.save(zippy[0], category)
            return

        if pages:
            assert isinstance(pages, list), "Pages are not a list"
            assert len(pages) >= 1, "Pages list is empty"
            assert isinstance(pages[0], int), "Page is not integer"

            if len(pages) >= 1 and isinstance(pages[0], int):
                ranger = range(1, pages[0])
            else:
                ranger = range(1, 2)
        else:
            ranger = range(1, 2)

        for page in ranger:
            topic = session.get(f"{self.link}/{page}", cookies=cookie, headers=header)

            assert topic.status_code == 200, f"Response is not ok. Actual: {topic.status_code}"

            if topic.status_code == 200:
                self.parse_forum(topic=topic, category=category, **session_options)

                not_downloaded = ZippyLinks.objects.filter(downloaded=False, not_exists=False, category=category)
                self.parse_zippy(links=not_downloaded, update_all=update_all, **session_options)

        self.update_links(**session_options)

        not_downloaded = ZippyLinks.objects.filter(downloaded=False, not_exists=False)

        for file in not_downloaded:
            try:
                self.download_manager.save(file, category)
            except (AttributeError, Exception):
                continue

    def update_links_partial(self, session: Session, cookie: RequestsCookieJar, header: Dict) -> None:
        """ Update links partially (without name and download link """

        not_downloaded = ZippyLinks.objects.filter(Q(name=None) | Q(name='') | Q(download_link=None))
        self.parse_zippy(session, cookie, header, not_downloaded, update_all=True)

    def update_links(self, session: Session, cookie: RequestsCookieJar, header: Dict) -> None:
        """ Update all objects in dB """

        not_downloaded = ZippyLinks.objects.all()
        self.parse_zippy(session, cookie, header, not_downloaded, update_all=True)

    def download_all(self, session: Session, cookie: RequestsCookieJar, header: Dict, music_type: str) -> None:
        """
        Download all objects where downloaded=False and name not empty.
        Not working because of zippyshare valid digits which are changing a lot.
        """

        for file in ZippyLinks.objects.filter(Q(downloaded=False) & ~Q(name='') & ~Q(name=None) & ~Q(name='-')):
            link = ZippyLinks.objects.filter(id=file.id)
            self.parse_zippy(session, cookie, header, link, update_all=True)
            try:
                self.download_manager.save(file, music_type)
            except (AttributeError, Exception):
                continue


class HouseParser(TranceParser):

    def __init__(self, logger: RootLogger):
        super().__init__(logger)
        self.link = 'http://www.4clubbers.com.pl/house/'
        self.category = 'House'
